import os
import re
import requests
import json
from bs4 import BeautifulSoup

import argparse
import uuid
import csv
import logging
import sys
import pandas as pd
import time
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Configuração de logging
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)


client = OpenAI()

from datetime import datetime, timedelta
from pinecone import Pinecone, ServerlessSpec
from pinecone.exceptions import PineconeApiException
from sentence_transformers import SentenceTransformer
import unicodedata

def sanitize_string_for_pinecone(text):
    """
    Sanitiza uma string para ser usada como nome de namespace no Pinecone,
    removendo caracteres não-ASCII e substituindo espaços por underscores.
    """
    text = str(text)
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    text = text.lower().replace(' ', '_')
    # Remove caracteres que não são alfanuméricos ou underscores
    text = ''.join(c for c in text if c.isalnum() or c == '_')
    return text

def load_additional_metadata(file_path):
    """Carrega metadados adicionais de um arquivo JSON."""
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def upload_categories_file(file_path):
    """Faz o upload do arquivo de categorias para a OpenAI e retorna o file_id."""
    try:
        with open(file_path, "rb") as f:
            response = client.files.create(file=f, purpose="assistants")
        logging.info(f"Arquivo {file_path} enviado com sucesso. File ID: {response.id}")
        return response.id
    except Exception as e:
        logging.error(f"Erro ao fazer upload do arquivo {file_path}: {e}")
        return None

def abreviar_categoria(texto):
    """Abrevia o texto para criar um código de categoria."""
    texto = re.sub(r'[^a-zA-Z0-9\s]', '', texto) # Remove caracteres especiais
    palavras = texto.upper().split()
    abreviacao = "".join(word[0] for word in palavras if word)
    return abreviacao[:10] # Limita a 10 caracteres para o código

def load_valid_categories(file_path):
    """Carrega as categorias válidas do arquivo CSV."""
    valid_categories = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=',')
            for row in reader:
                valid_categories[row['categoria']] = row['desc_categoria']
    except FileNotFoundError:
        logging.error(f"Arquivo de categorias não encontrado: {file_path}")
    except Exception as e:
        logging.error(f"Erro ao carregar categorias do CSV: {e}")
    return valid_categories

def get_category_description(category_id, valid_categories):
    """Retorna a descrição de uma categoria a partir das categorias válidas."""
    return valid_categories.get(category_id, "Categoria não encontrada ou inválida.")

def get_log_file_path():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return os.path.join(log_dir, f"log_{timestamp}.log")

# Determine if help is requested early to suppress logs
if any(arg in sys.argv for arg in ['--help', '-h']):
    log_level = logging.CRITICAL
else:
    log_level = logging.DEBUG

# Removendo a configuração básica e adicionando handlers
log_file_path = get_log_file_path()
logging.getLogger().handlers = [] # Clear any existing handlers

# File handler
file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
file_handler.setLevel(log_level) # Set level based on help request
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(file_handler)

# Stream handler for console output
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(log_level) # Set level based on help request
stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(stream_handler)



load_dotenv()
CATEGORIES_FILE_PATH = os.getenv('CATEGORIES_CSV_PATH', r"./docs/categorias.csv")
categories_file_id = upload_categories_file(CATEGORIES_FILE_PATH)

if not categories_file_id:
    logging.error("Não foi possível obter o File ID para categorias.csv. Encerrando o script.")
    sys.exit(1)

logging.getLogger().setLevel(log_level) # Set root logger level based on help request

model = SentenceTransformer('intfloat/multilingual-e5-large')

def generate_vetor(texto):
    """Gera um vetor (embedding) para o texto fornecido usando o modelo SentenceTransformer."""
    try:
        embedding = model.encode(texto, convert_to_tensor=False).tolist()
        return embedding
    except Exception as e:
        logging.error(f"Erro ao gerar vetor para o texto: {e}")
        return None

def save_backup_vetorizado(file_path, data):
    """Salva um backup do arquivo vetorizado com um timestamp."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_path = f"{file_path}.{timestamp}.bak"
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info(f"Backup do arquivo vetorizado salvo em: {backup_path}")
    except Exception as e:
        logging.error(f"Erro ao salvar backup do arquivo vetorizado: {e}")

def _initialize_pinecone_client(dimension=None):
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    pinecone_environment = os.getenv("PINECONE_ENVIRONMENT")
    pinecone_cloud = os.getenv("PINECONE_CLOUD")
    pinecone_index_name = os.getenv("PINECONE_INDEX_NAME")

    if not all([pinecone_api_key, pinecone_environment, pinecone_cloud, pinecone_index_name]):
        logging.error("Erro: Variáveis de ambiente do Pinecone não configuradas corretamente.")
        return None, None

    pc = Pinecone(api_key=pinecone_api_key)

    try:
        if pinecone_index_name not in pc.list_indexes():
            if dimension is None:
                logging.error("Erro: Dimensão do índice não fornecida para criação do índice Pinecone.")
                return None, None
            pc.create_index(
                name=pinecone_index_name,
                dimension=dimension,
                metric='cosine',
                spec=ServerlessSpec(cloud=pinecone_cloud, region=pinecone_environment)
            )
            logging.info(f"Índice Pinecone '{pinecone_index_name}' criado.")
        else:
            logging.info(f"Índice Pinecone '{pinecone_index_name}' já existe. Conectando-se a ele.")
    except PineconeApiException as e:
        if e.status == 409 and "ALREADY_EXISTS" in e.body:
            logging.warning(f"Índice Pinecone '{pinecone_index_name}' já existe. Conectando-se a ele.")
        else:
            logging.error(f"Erro ao criar/conectar ao índice Pinecone: {e}")
            return None, None
    except Exception as e:
        logging.error(f"Erro inesperado ao inicializar Pinecone: {e}")
        return None, None

    return pc, pinecone_index_name

def deploy(namespace=None, ids=None, vectors=None, metadata=None):
    """Realiza o upsert dos embeddings no Pinecone."""
    try:
        pc, pinecone_index_name = _initialize_pinecone_client(dimension=1024)
        index = pc.Index(pinecone_index_name)
        index.upsert(vectors=zip(ids, vectors, metadata), namespace=namespace)
        logging.info(f"Embeddings inseridos no Pinecone para o namespace '{namespace}'.")
        return True
    except Exception as e:
        logging.error(f"Erro ao fazer deploy no Pinecone: {e}")
        return False

def get_dates_between(start_date, end_date):
    start_dt = datetime.strptime(start_date, "%d/%m/%Y")
    end_dt = datetime.strptime(end_date, "%d/%m/%Y")
    delta = end_dt - start_dt
    return [(start_dt + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(delta.days + 1)]

def request_singular(data_inicio, data_fim, jurisprudencia_procurada, tribunais_selecionados, categorias_disponiveis, only_csv, categories_file_id, test=False):
    processed_items_count = 0
    # TODO: Implementar leitura de configs.json

    # Configuração do Pinecone
    if not only_csv:
        pc, pinecone_index_name = _initialize_pinecone_client(dimension=1024)
        if pc is None or pinecone_index_name is None:
            return

        index = pc.Index(pinecone_index_name)

        lista_datas = get_dates_between(data_inicio, data_fim)

    # Lógica de filtragem de tribunais
    tribunais_para_pesquisar = []
    if tribunais_selecionados.lower() == "todos":
        # Se 'Todos' for selecionado, carregar todos os tribunais disponíveis
        tribunais_disponiveis = load_tribunais()
        tribunais_para_pesquisar = [t for t in tribunais_disponiveis if t != "TODOS"]
    else:
        # Caso contrário, usar os tribunais fornecidos pelo usuário
        tribunais_disponiveis_lista = load_tribunais()
        for t in tribunais_selecionados.split(','):
            tribunal_limpo = t.strip()
            if load_tribunais(tribunal_a_validar=tribunal_limpo):
                tribunais_para_pesquisar.append(tribunal_limpo)
            else:
                logging.warning(f"Tribunal '{tribunal_limpo}' não suportado ou não existe e será ignorado.")

    logging.info(f"Tribunais a serem pesquisados: {tribunais_para_pesquisar}")

    for data in lista_datas:
        for tribunal_sigla in tribunais_para_pesquisar:
            page = 1
            while True:
                base_url = os.getenv('SCRAP_BASE_URL')
                params = {
                    "pagina": page,
                    "itensPorPagina": 5,
                    "dataDisponibilizacaoInicio": data,
                    "dataDisponibilizacaoFim": data,
                    "tribunal": tribunal_sigla,  # Adiciona o filtro de tribunal
                }
                if jurisprudencia_procurada:
                    params["query"] = jurisprudencia_procurada

                logging.info(f"Parâmetros da requisição: {params}")

                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                response = requests.get(base_url, params=params, headers=headers)
                logging.info(f"Request URL: {base_url}?{params}")
                payload_uri = f"{base_url}?{requests.compat.urlencode(params)}"

                if response.status_code == 200:
                    try:
                        resultado_atual = response.json()
                        logging.debug(f"Tipo de resultado_atual: {type(resultado_atual)}")
                        logging.debug(f"Conteúdo de resultado_atual (primeiros 1000 caracteres): {str(resultado_atual)[:1000]}")
                        if not resultado_atual or not resultado_atual.get('items'):
                            logging.info(f"Nenhum item encontrado para a página {page} na data {data} e tribunal {tribunal_sigla}. Quebrando o loop.")
                            break
                        
                        # Processar resultados e enviar para o Pinecone

                        for item in resultado_atual['items']:
                            if test and processed_items_count >= 3:
                                logging.info("Limite de 3 itens atingido no modo de teste. Parando o processamento.")
                                break
                            logging.debug(f"Conteúdo do item: {item}")
                            vector_id = str(item.get('id', uuid.uuid4()))
                            
                            # Initialize default values for categorization and description
                            item['categoria_id'] = 'sem_categoria'
                            item['desc_categoria'] = 'sem_categoria'
                            item['descricao_ia'] = 'sem_descricao'
                            
                            # Processar categorização com IA
                            logging.debug(f"Conteúdo de 'texto' antes de extrair_ementa: {item.get('texto', '')}")
                            ementa_extraida = extrair_ementa(item.get('texto', ''))
                            texto_para_categorizar = ementa_extraida if ementa_extraida else item.get('texto', '')

                            # Se o texto for o placeholder, tenta extrair do link
                            if "Não foi possível extrair conteúdo do documento" in texto_para_categorizar and item.get('link'):
                                logging.info(f"Placeholder detectado. Tentando extrair conteúdo de: {item['link']}")
                                extracted_text = fetch_content_from_url(item['link'])
                                if extracted_text:
                                    item['texto'] = extracted_text  # Atualiza o item['texto'] com o conteúdo real
                                    texto_para_categorizar = extracted_text # Atualiza para categorização
                                    logging.info("Conteúdo extraído com sucesso do link.")
                                else:
                                    logging.warning("Não foi possível extrair conteúdo do link. Mantendo placeholder.")

                            # Ignorar documentos com conteúdo indesejado
                            if "Não foi possível extrair conteúdo do documento" in texto_para_categorizar:
                                logging.info(f"Documento ignorado devido ao conteúdo indesejado: {vector_id}")
                                continue # Pula para o próximo item
                            
                            if texto_para_categorizar:
                                openai_api_key = os.getenv("OPENAI_API_KEY")
                                if openai_api_key:
                                    resultado_categorizacao = processar_com_ia(texto_para_categorizar, categories_file_id, payload_uri)
                                    if resultado_categorizacao:
                                        ia_categoria_id = resultado_categorizacao.get('categoria_id', 'sem_categoria')
                                        ia_desc_categoria = resultado_categorizacao.get('desc_categoria', 'sem_categoria')
                                        categories_file_id = resultado_categorizacao.get('categories_file_id', categories_file_id) # Atualiza o file_id
                                        logging.debug(f"IA retornou: categoria_id='{ia_categoria_id}', desc_categoria='{ia_desc_categoria}'")

                                        item['categoria_id'] = ia_categoria_id
                                        item['desc_categoria'] = ia_desc_categoria
                                        logging.info(f"Categoria identificada e validada pela IA: ID={item['categoria_id']}, Descrição={item['desc_categoria']}")
                                
                                    # Gerar descrição com IA
                                    descricao_gerada = gerar_descricao_com_ia(texto_para_categorizar)
                                    if descricao_gerada:
                                        item['descricao_ia'] = descricao_gerada
                                        logging.info(f"Descrição gerada pela IA: {descricao_gerada}")
                                else:
                                    logging.error("Erro: Variável de ambiente OPENAI_API_KEY não configurada. Categorização e descrição IA serão ignoradas.")
                                

                            
                            # Lógica de upsert no Pinecone após categorização (condicional a not only_csv)
                            if not only_csv:
                                namespace_raw = item.get('categoria_id', 'geral')
                                namespace = sanitize_string_for_pinecone(namespace_raw)
                                logging.info(f"Namespace para upsert no Pinecone: '{namespace}' (categoria_id: {item.get('categoria_id')})")
                                # TODO: Substituir 'dummy_vector' por embeddings reais gerados pelo modelo SentenceTransformer.
                                embeddings = model.encode(texto_para_categorizar).tolist()
                                additional_metadata_template = load_additional_metadata(r"d:\Workspace\LawX-Scraper\docs\metadata.json")
                                
                                # Filter item metadata based on additional_metadata_template keys
                                filtered_item_metadata = {k: (str(v) if v is not None else "") for k, v in item.items() if k in additional_metadata_template}
                                
                                # Start with filtered item metadata
                                cleaned_metadata = filtered_item_metadata
                                
                                # Update with additional_metadata_template, giving precedence to its values
                                cleaned_metadata.update(additional_metadata_template)
                                index.upsert(vectors=[{"id": vector_id, "values": embeddings, "metadata": cleaned_metadata}], namespace=namespace)
                                logging.info(f"Item {vector_id} enviado para o Pinecone no namespace '{namespace}'.")

                            processed_items_count += 1 # Increment count once per item

                            # Manter geração de CSV e logs
                            output_base_dir = os.path.join(os.path.dirname(__file__), 'output')
                            categoria_dir = os.path.join(output_base_dir, item.get('categoria_id', 'geral').replace(' ', '_').replace('/', '_').lower())
                            os.makedirs(categoria_dir, exist_ok=True)
                        
                            data_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
                            csv_file_path = os.path.join(categoria_dir, f"relatorio_{data_hora}.csv")
                            
                            # Escrever cabeçalho se o arquivo não existir
                            if not os.path.exists(csv_file_path):
                                with open(csv_file_path, 'w', newline='', encoding='utf-8') as f:
                                    writer = csv.DictWriter(f, fieldnames=item.keys())
                                    writer.writeheader()
                            
                            # Anexar dados
                            with open(csv_file_path, 'a', newline='', encoding='utf-8') as f:
                                writer = csv.DictWriter(f, fieldnames=item.keys())
                                writer.writerow(item)
                            logging.info(f"Dados salvos em {csv_file_path}")

                        if test and processed_items_count >= 3:
                            break

                        page += 1
                    except json.JSONDecodeError:
                        logging.error("Erro ao decodificar JSON da resposta.")
                        break
                else:
                    logging.error(f"Erro na requisição: {response.status_code} - {response.text}")
                    break
                page += 1
            if test and processed_items_count >= 3:
                break
    logging.info("request_singular finalizado.")
    
def log_ai_interaction(input_text, raw_ai_response, categoria_id, desc_categoria, payload_uri):
    """
    Registra a interação da IA em um arquivo JSON na pasta interations_ai.
    """
    log_dir = os.path.join(os.path.dirname(__file__), 'logs', 'interations_ai')
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    log_file_path = os.path.join(log_dir, f"ai_interaction_{timestamp}.json")

    interaction_data = {
        "timestamp": datetime.now().isoformat(),
        "input_text": input_text,
        "raw_ai_response": raw_ai_response,
        "categoria_id": categoria_id,
        "desc_categoria": desc_categoria,
        "payload_uri": payload_uri
    }

    try:
        with open(log_file_path, 'w', encoding='utf-8') as f:
            json.dump(interaction_data, f, ensure_ascii=False, indent=4)
        logging.info(f"Interação da IA registrada em: {log_file_path}")
    except Exception as e:
        logging.error(f"Erro ao registrar interação da IA: {e}")

def load_tribunais(tribunal_a_validar=None):
    """
    Carrega a lista de tribunais do arquivo JSON.
    Se tribunal_a_validar for None, retorna todos os tribunais (incluindo 'TODOS').
    Se tribunal_a_validar for fornecido, verifica se o tribunal existe na lista.
    """
    tribunais_file = os.path.join(os.path.dirname(__file__), 'config', 'tribunais.json')
    try:
        with open(tribunais_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Extrai a lista de tribunais, suportando diferentes estruturas
        if isinstance(data, dict) and 'lista_tribunais' in data:
            lista_tribunais = data['lista_tribunais']
        elif isinstance(data, list):
            lista_tribunais = data
        else:
            logging.error(f"Erro: Formato inesperado no arquivo de tribunais em {tribunais_file}")
            return lista_tribunais if tribunal_a_validar is None else False

        if tribunal_a_validar is not None:
            return tribunal_a_validar in lista_tribunais
        else:
            return lista_tribunais

    except FileNotFoundError:
        logging.error(f"Erro: Arquivo de tribunais não encontrado em {tribunais_file}")
        sys.exit(1)
    except json.JSONDecodeError:
        logging.error(f"Erro: Não foi possível decodificar o arquivo JSON de tribunais em {tribunais_file}")
        sys.exit(1)

def load_categorias():
    """Carrega a lista de categorias do arquivo CSV."""
    categorias_path = os.path.join(os.path.dirname(__file__), 'docs', 'categorias.csv')
    try:
        df_categorias = pd.read_csv(categorias_path, delimiter=';')
        # Converte o DataFrame para uma lista de dicionários
        categorias = df_categorias.to_dict(orient='records')
        return categorias
    except FileNotFoundError:
        logging.error(f"Erro: Arquivo de categorias não encontrado em {categorias_path}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Erro ao carregar categorias do arquivo {categorias_path}: {e}")
        sys.exit(1)

def extrair_ementa(texto):
    """Extrai a ementa de um texto, se presente."""
    # Padrão para encontrar a ementa (exemplo: EMENTA: ...)
    match = re.search(r'EMENTA:\s*(.*?)(?=\n\n|\Z)', texto, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""

def fetch_content_from_url(url):
    """Faz uma requisição HTTP para a URL e extrai o conteúdo de texto."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Levanta um erro para códigos de status HTTP ruins (4xx ou 5xx)
        soup = BeautifulSoup(response.text, 'html.parser')
        # Remove scripts e estilos para obter apenas o texto visível
        for script in soup(["script", "style"]):
            script.extract()
        text = soup.get_text()
        # Quebra linhas e remove espaços em branco extras
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for phrase in ' '.join(lines).split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        return text
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro ao acessar a URL {url}: {e}")
        return "Não foi possível extrair conteúdo do documento"
    except Exception as e:
        logging.error(f"Erro inesperado ao extrair conteúdo da URL {url}: {e}")
        return "Não foi possível extrair conteúdo do documento"



def validate_assistant_id(client, assistant_id):
    """Valida se o assistant_id existe na OpenAI."""
    if not assistant_id:
        return False
    try:
        client.beta.assistants.retrieve(assistant_id)
        return True
    except NotFound:
        logging.warning(f"Assistant ID '{assistant_id}' não encontrado na OpenAI. Usando fallback para Chat Completions.")
        return False
    except Exception as e:
        logging.error(f"Erro ao validar Assistant ID '{assistant_id}': {e}. Usando fallback para Chat Completions.")
        return False

def processar_com_ia(texto, categories_file_id, payload_uri):
    """Processa o texto usando a API da OpenAI para categorizar, com fallback para Chat Completions."""
    pasta_configs = os.path.join(os.path.dirname(__file__), 'prompts')
    prompt_categoria_path = os.path.join(pasta_configs, 'prompt_categoria.txt')
    
    # Carregar categorias válidas do CSV
    categorias_csv_path = os.path.join(os.path.dirname(__file__), 'docs', 'categorias.csv')
    valid_categories = load_valid_categories(categorias_csv_path)

    try:
        # Carrega o prompt do arquivo
        with open(prompt_categoria_path, 'r', encoding='utf-8') as file:
            prompt_base = file.read()

        # Format valid categories for the prompt
        valid_categories_list = ", ".join(f"'{cat}'" for cat in valid_categories.keys())
        prompt_base = prompt_base.format(valid_categories_list=valid_categories_list)

        prompt_final = f"""{prompt_base}

------------------------------------
Este é o texto a ser analisado:
{texto}
------------------------------------"""
        logging.info(f"Prompt final enviado para a IA: {prompt_final}")
        
        # Usando sempre Chat Completions API
        response = client.chat.completions.create(
            model="gpt-4o-mini", # Ou outro modelo de sua preferência para completions
            messages=[
                {"role": "user", "content": prompt_final}
            ],
            temperature=0.7,
        )
        value = response.choices[0].message.content

        if value:
            logging.info(f"Categoria identificada pela IA (valor bruto): {value}")
            ia_categoria_id = value.strip() # A IA deve retornar apenas o nome da categoria
            ia_desc_categoria = valid_categories.get(ia_categoria_id, "Documento não classificado por categoria específica.")

            # Validação da categoria retornada pela IA
            if ia_categoria_id not in valid_categories:
                logging.warning(f"IA retornou categoria inválida: {ia_categoria_id}. Usando 'sem_categoria'.")
                ia_categoria_id = "sem_categoria"
                ia_desc_categoria = "Documento não classificado por categoria específica."

            log_ai_interaction(texto, value, ia_categoria_id, ia_desc_categoria, payload_uri)
            return {"categoria_id": ia_categoria_id, "desc_categoria": ia_desc_categoria, "categories_file_id": categories_file_id}
        else:
            logging.warning("A IA não retornou um valor de categoria válido.")
            log_ai_interaction(texto, "N/A", "sem_categoria", "IA não retornou valor válido", payload_uri)
            return None

    except Exception as e:
        logging.error(f"Erro inesperado ao processar com IA: {e}")
        log_ai_interaction(texto, "N/A", "erro_geral", str(e), payload_uri)
        return None

def gerar_descricao_com_ia(texto):
    """Gera uma descrição para o texto fornecido usando a API da OpenAI."""
    pasta_configs = os.path.join(os.path.dirname(__file__), 'prompts')
    prompt_descricao_path = os.path.join(pasta_configs, 'prompt_descricao.txt')

    try:
        with open(prompt_descricao_path, 'r', encoding='utf-8') as file:
            prompt_base = file.read()

        prompt_final = f"""{prompt_base}

------------------------------------
Este é o texto a ser analisado:
{texto}
------------------------------------"""
        logging.info(f"Prompt final enviado para a IA para descrição: {prompt_final}")

        assistant_id = os.getenv("OPENAI_ASSISTANT_ID")
        if validate_assistant_id(client, assistant_id):
            logging.info(f"Usando Assistants API para descrição com ID: {assistant_id}")
            thread = client.beta.threads.create()
            thread_id = thread.id
            logging.info(f"Thread criada com ID: {thread_id}")

            client.beta.threads.messages.create(
                thread_id=thread_id, role="user", content=prompt_final
            )
            logging.info("Mensagem adicionada ao thread.")

            run = client.beta.threads.runs.create(
                thread_id=thread_id, assistant_id=assistant_id
            )
            run_id = run.id
            logging.info(f"Run criado com ID: {run_id}")

            while run.status in ['queued', 'in_progress', 'cancelling']:
                time.sleep(1)
                run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)

            if run.status == 'completed':
                messages = client.beta.threads.messages.list(thread_id=thread_id)
                resposta_ia = ""
                for msg in messages.data:
                    if msg.role == "assistant":
                        for content in msg.content:
                            if content.type == 'text':
                                resposta_ia = content.text.value
                                break
                        if resposta_ia:
                            break
                logging.info(f"Resposta da IA para descrição: {resposta_ia}")
                return resposta_ia
            else:
                logging.error(f"Run para descrição falhou com status: {run.status}")
                return ""
        else:
            logging.warning("OPENAI_ASSISTANT_ID inválido ou não configurado para descrição. Usando Chat Completions API.")
            response = client.chat.completions.create(
                model="gpt-4o-mini", # Ou outro modelo de sua preferência para completions
                messages=[
                    {"role": "user", "content": prompt_final}
                ],
                temperature=0.7,
            )
            return response.choices[0].message.content

    except FileNotFoundError:
        logging.error(f"Arquivo de prompt de descrição não encontrado: {prompt_descricao_path}")
        return ""
    except Exception as e:
        logging.error(f"Erro geral em gerar_descricao_com_ia: {e}")
        return ""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script de scraping de jurisprudência.")
    parser.add_argument("--data-inicio", help="Data de início no formato DD/MM/AAAA", required=True)
    parser.add_argument("--data-fim", default=None, help="Data de fim no formato DD/MM/AAAA. Se não fornecida, será igual à data de início.")
    parser.add_argument("--jurisprudencia", default="", help="Termo de jurisprudência a ser procurado (opcional). Use --jurisprudencia \"Ementa\" para uma tag, ou --jurisprudencia \"Ementa, Acórdão\" para múltiplas tags. Documentos possíveis em ./config/docs.json")
    parser.add_argument("--tribunal", default="Todos", help="Tribunais a serem pesquisados, separados por vírgula. Ex: 'TJSP,TJMG' ou 'Todos'")
    parser.add_argument("--only-csv", action="store_true", help="Se presente, o script gerará apenas CSVs e não usará o Pinecone.")
    parser.add_argument("--test", action="store_true", help="Se presente, o script limitará o scraping a 10 escritas para testes.")

    args = parser.parse_args()

    # Adiciona a lógica para exibir ajuda e sair se --help ou -h for fornecido
    if any(arg in sys.argv for arg in ['--help', '-h']):
        parser.print_help()
        sys.exit(0)

    if args.data_fim is None:
        args.data_fim = args.data_inicio

    tribunais_disponiveis = load_tribunais()

    categorias_disponiveis = load_categorias()

    request_singular(args.data_inicio, args.data_fim, args.jurisprudencia, args.tribunal, categorias_disponiveis, args.only_csv, categories_file_id, args.test)


def fetch_content_from_url(url):
    """Baixa o conteúdo de uma URL e tenta extrair texto.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Levanta um erro para códigos de status HTTP ruins (4xx ou 5xx)
        
        # Tenta extrair texto de HTML
        if 'text/html' in response.headers.get('Content-Type', ''):
            soup = BeautifulSoup(response.content.decode('utf-8'), 'html.parser')
            # Remove scripts e estilos
            for script_or_style in soup(['script', 'style']):
                script_or_style.extract()
            text = soup.get_text()
            # Quebra linhas e remove espaços extras
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            return text
        else:
            logging.warning(f"Tipo de conteúdo não suportado para extração de texto: {response.headers.get('Content-Type', '')}")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro ao baixar conteúdo da URL {url}: {e}")
        return None
    except Exception as e:
        logging.error(f"Erro inesperado ao processar URL {url}: {e}")