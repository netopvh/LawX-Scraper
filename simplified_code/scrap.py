import re
import requests
import json

import argparse
import uuid
import csv
import os
import logging
import sys
import pandas as pd
import time
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

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

# Configuração de logging
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

def get_log_file_path():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return os.path.join(log_dir, f"log_{timestamp}.log")

# Removendo a configuração básica e adicionando handlers
log_file_path = get_log_file_path()
logging.getLogger().handlers = [] # Clear any existing handlers

# File handler
file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(file_handler)

# Stream handler for console output
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(stream_handler)



def update_ignored_categories_json(category_name):
    ignored_categories_json_path = os.path.join(os.path.dirname(__file__), 'docs', "ignored_categories_count.json")
    ignored_categories_data = {}
    if os.path.exists(ignored_categories_json_path):
        try:
            with open(ignored_categories_json_path, 'r', encoding='utf-8') as f:
                ignored_categories_data = json.load(f)
        except json.JSONDecodeError:
            logging.error(f"Erro ao decodificar {ignored_categories_json_path}. Criando um novo arquivo.")
            ignored_categories_data = {}

    ignored_categories_data[category_name] = ignored_categories_data.get(category_name, 0) + 1

    with open(ignored_categories_json_path, 'w', encoding='utf-8') as f:
        json.dump(ignored_categories_data, f, ensure_ascii=False, indent=4)
    logging.info(f"Contagem de categorias ignoradas atualizada para '{category_name}'.")

CATEGORIES_FILE_PATH = r"d:\Workspace\LawX-Scraper\simplified_code\docs\categorias.csv"
categories_file_id = upload_categories_file(CATEGORIES_FILE_PATH)

if not categories_file_id:
    logging.error("Não foi possível obter o File ID para categorias.csv. Encerrando o script.")
    sys.exit(1)

logging.getLogger().setLevel(logging.DEBUG)

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
                base_url = 'https://comunicaapi.pje.jus.br/api/v1/comunicacao'
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

                            # Ignorar documentos com conteúdo indesejado
                            if "Não foi possível extrair conteúdo do documento" in texto_para_categorizar:
                                logging.info(f"Documento ignorado devido ao conteúdo indesejado: {vector_id}")
                                continue # Pula para o próximo item
                            
                            if texto_para_categorizar:
                                openai_api_key = os.getenv("OPENAI_API_KEY")
                                if openai_api_key:
                                    categorias_csv_path = os.path.join(os.path.dirname(__file__), 'docs', 'categorias.csv')
                                    resultado_categorizacao = processar_com_ia(item, texto_para_categorizar, openai_api_key, categories_file_id, payload_uri)
                                    if resultado_categorizacao:
                                        ia_categoria_id = resultado_categorizacao.get('categoria_id', 'sem_categoria')
                                        ia_desc_categoria = resultado_categorizacao.get('desc_categoria', 'sem_categoria')
                                        categories_file_id = resultado_categorizacao.get('categories_file_id', categories_file_id) # Atualiza o file_id
                                        logging.debug(f"IA retornou: categoria_id='{ia_categoria_id}', desc_categoria='{ia_desc_categoria}'")

                                        item['categoria_id'] = ia_categoria_id
                                        item['desc_categoria'] = ia_desc_categoria
                                        logging.info(f"Categoria identificada e validada pela IA: ID={item['categoria_id']}, Descrição={item['desc_categoria']}")
                                
                                    # Gerar descrição com IA
                                    descricao_gerada = gerar_descricao_com_ia(texto_para_categorizar, openai_api_key)
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
                                cleaned_metadata = {k: (str(v) if v is not None else "") for k, v in item.items()}
                                additional_metadata = load_additional_metadata(r"d:\Workspace\LawX-Scraper\simplified_code\docs\metadata.json")
                                cleaned_metadata.update(additional_metadata)
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
    """Extrai a seção 'EMENTA' de um texto, se presente."""
    match = re.search(r'EMENTA:\s*(.*?)(?:\n\n|\Z)', texto, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""

def processar_com_ia(item, texto, api_key, categories_file_id, payload_uri):
    """Processa o texto usando a API da OpenAI para categorizar."""
    pasta_configs = os.path.join(os.path.dirname(__file__), 'prompts')
    prompt_categoria_path = os.path.join(pasta_configs, 'prompt_categoria.txt')

    try:
        with open(prompt_categoria_path, 'r', encoding='utf-8') as file:
            prompt_base = file.read()

        prompt_final = f"""{prompt_base}

------------------------------------
Este é o texto a ser analisado:
{texto}
------------------------------------"""
        logging.info(f"Prompt final enviado para a IA: {prompt_final}")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "OpenAI-Beta": "assistants=v2"
        }
        assistant_id = 'asst_7HnwPIVsEXEtiFNU68ri2TRs' # ID do assistente, pode ser configurável

        # Criação da Thread
        thread_start = False
        thread_id = None
        while not thread_start:
            try:
                thread_url = "https://api.openai.com/v1/threads"
                thread_response = requests.post(thread_url, headers=headers)
                thread_data = thread_response.json()
                logging.info(f"Dados brutos da thread da IA: {thread_data}")
                thread_id = thread_data.get("id")
                if not thread_id:
                    logging.error(f"Erro ao criar a Thread para categorização: {thread_data}")
                    time.sleep(5) # Espera antes de tentar novamente
                else:
                    logging.info(f"Thread para categorização criada com sucesso. ID: {thread_id}")
                    thread_start = True
            except Exception as e:
                logging.error(f"Erro ao criar a Thread para categorização: {e}")
                time.sleep(5) # Espera antes de tentar novamente

        # Adicionar mensagem à Thread
        message_ok = False
        while not message_ok:
            try:
                message_url = f"https://api.openai.com/v1/threads/{thread_id}/messages"
                message_data = {
                    "role": "user",
                    "content": prompt_final
                }
                message_response = requests.post(message_url, headers=headers, json=message_data)
                if message_response.status_code != 200:
                    logging.error(f"Erro ao adicionar mensagem à Thread para categorização: {message_response.json()}")
                    time.sleep(5) # Espera antes de tentar novamente
                else:
                    logging.info("Mensagem para categorização adicionada ao Thread com sucesso.")
                    message_ok = True
            except Exception as e:
                logging.error(f"Erro ao adicionar mensagem à Thread para categorização: {e}")
                time.sleep(5) # Espera antes de tentar novamente

        # Iniciar o Run
        run_start = False
        run_id = None
        while not run_start:
            try:
                run_url = f"https://api.openai.com/v1/threads/{thread_id}/runs"
                run_data = {"assistant_id": assistant_id}
                run_response = requests.post(run_url, headers=headers, json=run_data)
                run_data = run_response.json()
                run_id = run_data.get("id")
                if not run_id:
                    logging.error(f"Erro ao iniciar o Run para categorização: {run_data}")
                    time.sleep(5) # Espera antes de tentar novamente
                else:
                    logging.info(f"Run para categorização iniciado. ID: {run_id}")
                    run_start = True
            except Exception as e:
                logging.error(f"Erro ao iniciar o Run para categorização: {e}")
                time.sleep(5) # Espera antes de tentar novamente

        # Verificar status do Run
        run_ok = False
        while not run_ok:
            try:
                run_status_response = requests.get(f"https://api.openai.com/v1/threads/{thread_id}/runs/{run_id}", headers=headers)
                run_status = run_status_response.json().get("status")
                if run_status == "completed":
                    logging.info("Run para categorização concluído com sucesso.")
                    run_ok = True
                else:
                    logging.info(f"Aguardando conclusão do processamento da categorização... Status: {run_status}")
                    time.sleep(5) # Espera antes de verificar novamente
            except Exception as e:
                logging.error(f"Erro ao verificar status do Run para categorização: {e}")
                time.sleep(5) # Espera antes de tentar novamente

        # Obter mensagens da Thread
        messages_url = f"https://api.openai.com/v1/threads/{thread_id}/messages"
        messages_response = requests.get(messages_url, headers=headers)
        messages_data = messages_response.json()
        logging.debug(f"Resposta completa da API da IA: {messages_data}")

        value = None
        if messages_data.get("data"):
            first_message = messages_data["data"][0]
            if first_message.get("content"):
                first_content = first_message["content"][0]
                if first_content.get("type") == "text":
                    value = first_content.get("text", {}).get("value")

        if value:
            logging.info(f"Categoria identificada pela IA (valor bruto): {value}")
            ia_categoria_id = "N/A"
            ia_desc_categoria = "N/A"
            try:
                ai_response_json = json.loads(value)
                ia_categoria_id = ai_response_json.get("categoria_id", "N/A")
                ia_desc_categoria = ai_response_json.get("desc_categoria", "N/A")

                if ia_categoria_id == "NAO_CLASSIFICADO":
                    logging.warning(f"IA não classificou o item: {item} - Motivo: {ia_desc_categoria}")
                    log_ai_interaction(texto, value, ia_categoria_id, ia_desc_categoria, payload_uri)
                    return {
                        "categoria_id": "NAO_CLASSIFICADO",
                        "desc_categoria": ia_desc_categoria,
                        "categories_file_id": categories_file_id
                    }
                elif ia_categoria_id and ia_categoria_id.startswith("[SUGESTAO_DE_NOVA_CATEGORIA]"):
                    suggested_category = ia_desc_categoria if ia_desc_categoria else ia_categoria_id.replace("[SUGESTAO_DE_NOVA_CATEGORIA]", "").strip()
                    
                    update_ignored_categories_json(suggested_category)
                    log_ai_interaction(texto, value, "NAO_CLASSIFICADO", suggested_category, payload_uri)
                    return {
                        "categoria_id": "NAO_CLASSIFICADO", # Retorna como NAO_CLASSIFICADO para processamento posterior
                        "desc_categoria": suggested_category,
                        "categories_file_id": categories_file_id
                    }
                elif ia_categoria_id and ia_desc_categoria:
                    logging.info(f"IA retornou categoria: {ia_categoria_id} - {ia_desc_categoria}")
                    log_ai_interaction(texto, value, ia_categoria_id, ia_desc_categoria, payload_uri)
                    return {
                        "categoria_id": ia_categoria_id,
                        "desc_categoria": ia_desc_categoria,
                        "categories_file_id": categories_file_id
                    }
                else:
                    logging.warning(f"Resposta da IA em formato inesperado ou incompleto: {value}")
                    log_ai_interaction(texto, value, "NAO_CLASSIFICADO", "Não Classificado")
                    return {
                        "categoria_id": "NAO_CLASSIFICADO",
                        "desc_categoria": "Não Classificado",
                        "categories_file_id": categories_file_id
                    }
            except json.JSONDecodeError:
                logging.error(f"Erro ao decodificar JSON da resposta da IA: {value}")
                log_ai_interaction(texto, value, "NAO_CLASSIFICADO", "Não Classificado")
                return {
                    "categoria_id": "NAO_CLASSIFICADO",
                    "desc_categoria": "Não Classificado",
                    "categories_file_id": categories_file_id
                }
        else:
            logging.warning("IA não retornou nenhum valor para categorização.")
            log_ai_interaction(texto, value, "NAO_CLASSIFICADO", "Não Classificado")
            return {
                "categoria_id": "NAO_CLASSIFICADO",
                "desc_categoria": "Não Classificado",
                "categories_file_id": categories_file_id
            }

    except Exception as e:
        logging.error(f"Erro geral na categorização por IA: {e}")
        return {"categoria_id": None, "desc_categoria": None, "categories_file_id": categories_file_id}

def gerar_descricao_com_ia(texto, api_key):
    """Processa o texto usando a API da OpenAI para gerar uma descrição."""
    pasta_prompts = os.path.join(os.path.dirname(__file__), 'prompts')
    prompt_descricao_path = os.path.join(pasta_prompts, 'prompt_descricao.txt')

    try:
        with open(prompt_descricao_path, 'r', encoding='utf-8') as file:
            prompt_descricao = file.read()

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "OpenAI-Beta": "assistants=v2"
        }
        assistant_id = 'asst_7HnwPIVsEXEtiFNU68ri2TRs' # ID do assistente, pode ser configurável

        # Criação da Thread
        thread_start = False
        thread_id = None
        while not thread_start:
            try:
                thread_url = "https://api.openai.com/v1/threads"
                thread_response = requests.post(thread_url, headers=headers)
                thread_data = thread_response.json()
                thread_id = thread_data.get("id")
                if not thread_id:
                    logging.error(f"Erro ao criar a Thread para descrição: {thread_data}")
                    time.sleep(5) # Espera antes de tentar novamente
                else:
                    logging.info(f"Thread para descrição criada com sucesso. ID: {thread_id}")
                    thread_start = True
            except Exception as e:
                logging.error(f"Erro ao criar a Thread para descrição: {e}")
                time.sleep(5) # Espera antes de tentar novamente

        # Adicionar mensagem à Thread
        message_ok = False
        while not message_ok:
            try:
                message_url = f"https://api.openai.com/v1/threads/{thread_id}/messages"
                message_data = {
                    "role": "user",
                    "content": f"""{prompt_descricao}
------------------------------------
Este é o texto a ser analisado:
{texto}
------------------------------------"""
                }
                message_response = requests.post(message_url, headers=headers, json=message_data)
                if message_response.status_code != 200:
                    logging.error(f"Erro ao adicionar mensagem à Thread para descrição: {message_response.json()}")
                    time.sleep(5) # Espera antes de tentar novamente
                else:
                    logging.info("Mensagem para descrição adicionada ao Thread com sucesso.")
                    message_ok = True
            except Exception as e:
                logging.error(f"Erro ao adicionar mensagem à Thread para descrição: {e}")
                time.sleep(5) # Espera antes de tentar novamente

        # Iniciar o Run
        run_start = False
        run_id = None
        while not run_start:
            try:
                run_url = f"https://api.openai.com/v1/threads/{thread_id}/runs"
                run_data = {"assistant_id": assistant_id}
                run_response = requests.post(run_url, headers=headers, json=run_data)
                run_data = run_response.json()
                run_id = run_data.get("id")
                if not run_id:
                    logging.error(f"Erro ao iniciar o Run para descrição: {run_data}")
                    time.sleep(5) # Espera antes de tentar novamente
                else:
                    logging.info(f"Run para descrição iniciado. ID: {run_id}")
                    run_start = True
            except Exception as e:
                logging.error(f"Erro ao iniciar o Run para descrição: {e}")
                time.sleep(5) # Espera antes de tentar novamente

        # Verificar status do Run
        run_ok = False
        while not run_ok:
            try:
                run_status_response = requests.get(f"https://api.openai.com/v1/threads/{thread_id}/runs/{run_id}", headers=headers)
                run_status = run_status_response.json().get("status")
                if run_status == "completed":
                    logging.info("Run para descrição concluído com sucesso.")
                    run_ok = True
                else:
                    logging.info(f"Aguardando conclusão do processamento da descrição... Status: {run_status}")
                    time.sleep(5) # Espera antes de verificar novamente
            except Exception as e:
                logging.error(f"Erro ao verificar status do Run para descrição: {e}")
                time.sleep(5) # Espera antes de tentar novamente

        # Obter mensagens da Thread
        messages_url = f"https://api.openai.com/v1/threads/{thread_id}/messages"
        messages_response = requests.get(messages_url, headers=headers)
        messages_data = messages_response.json()

        value = None
        if messages_data.get("data"):
            first_message = messages_data["data"][0]
            if first_message.get("content"):
                first_content = first_message["content"][0]
                if first_content.get("type") == "text":
                    value = first_content.get("text", {}).get("value")

        if value:
            logging.info(f"Descrição gerada pela IA: {value}")
            return value.strip()
        else:
            logging.warning("Nenhuma descrição de valor da IA.")
            return ""

    except Exception as e:
        logging.error(f"Erro geral na geração de descrição por IA: {e}")
        return ""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script de scraping de jurisprudência.")
    parser.add_argument("--data-inicio", help="Data de início no formato DD/MM/AAAA", required=True)
    parser.add_argument("--data-fim", help="Data de fim no formato DD/MM/AAAA. Se não fornecida, será igual à data de início.", default=None)
    parser.add_argument("--jurisprudencia", help="Termo de jurisprudência a ser procurado", required=True)
    parser.add_argument("--tribunais", default="Todos", help="Tribunais a serem pesquisados, separados por vírgula. Ex: 'TJSP,TJMG' ou 'Todos'")
    parser.add_argument("--only-csv", action="store_true", help="Se presente, o script gerará apenas CSVs e não usará o Pinecone.")
    parser.add_argument("--test", action="store_true", help="Se presente, o script limitará o scraping a 10 escritas para testes.")

    args = parser.parse_args()

    if args.data_fim is None:
        args.data_fim = args.data_inicio

    tribunais_disponiveis = load_tribunais()

    categorias_disponiveis = load_categorias()

    request_singular(args.data_inicio, args.data_fim, args.jurisprudencia, args.tribunais, categorias_disponiveis, args.only_csv, categories_file_id, args.test)