import requests
import json
import os
import argparse
import uuid
import csv
import logging
import sys
import pandas as pd
import time
from dotenv import load_dotenv

load_dotenv()

from datetime import datetime, timedelta
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer

# Configuração do logging
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

def get_log_file_path():
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H-%M-%S")
    return os.path.join(log_dir, f"log_{today}_{current_time}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(get_log_file_path()),
        logging.StreamHandler(sys.stdout)
    ]
)

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

def deploy(index_name, namespace, ids, vectors, metadata):
    """Realiza o upsert dos embeddings no Pinecone."""
    try:
        pinecone_api_key = os.getenv("PINECONE_API_KEY")
        pinecone_environment = os.getenv("PINECONE_ENVIRONMENT")

        if not all([pinecone_api_key, pinecone_environment]):
            logging.error("Erro: Variáveis de ambiente do Pinecone não configuradas corretamente para deploy.")
            return False

        pc = Pinecone(api_key=pinecone_api_key)

        if index_name not in pc.list_indexes():
            pc.create_index(
                name=index_name,
                dimension=len(vectors[0]),
                metric='cosine',
                spec=ServerlessSpec(cloud='aws', region=pinecone_environment)
            )
            logging.info(f"Índice Pinecone '{index_name}' criado.")

        index = pc.Index(index_name)
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

def request_singular(data_inicio, data_fim, jurisprudencia_procurada, tribunais_selecionados, categorias_disponiveis, only_csv=False):
    # TODO: Implementar leitura de configs.json

    # Configuração do Pinecone
    if not only_csv:
        pinecone_api_key = os.getenv("PINECONE_API_KEY")
        pinecone_environment = os.getenv("PINECONE_ENVIRONMENT")
        pinecone_index_name = os.getenv("PINECONE_INDEX_NAME")

        if not all([pinecone_api_key, pinecone_environment, pinecone_index_name]):
            logging.error("Erro: Variáveis de ambiente do Pinecone não configuradas corretamente.")
            return

        pc = Pinecone(api_key=pinecone_api_key)
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

                if response.status_code == 200:
                    try:
                        resultado_atual = response.json()
                        logging.debug(f"Tipo de resultado_atual: {type(resultado_atual)}")
                        logging.debug(f"Conteúdo de resultado_atual (primeiros 1000 caracteres): {str(resultado_atual)[:1000]}")
                        if not resultado_atual or not resultado_atual.get('items'):
                            logging.info(f"Nenhum item encontrado para a página {page} na data {data} e tribunal {tribunal_sigla}. Quebrando o loop.")
                            break
                        
                        # Processar resultados e enviar para o Pinecone
                        all_results = []
                        for item in resultado_atual['items']:
                            vector_id = str(item.get('id', uuid.uuid4()))
                            if not only_csv:
                                dummy_vector = [0.1] * 1536
                                # Limpar metadados: converter None para string vazia
                                cleaned_metadata = {k: (str(v) if v is not None else "") for k, v in item.items()}
                                index.upsert(vectors=[{"id": vector_id, "values": dummy_vector, "metadata": cleaned_metadata}])
                                logging.info(f"Item {vector_id} enviado para o Pinecone.")
                            all_results.append(item)
                        
                            # Processar categorização com IA
                            texto_para_categorizar = item.get('texto', '')
                            if texto_para_categorizar and not only_csv:
                                openai_api_key = os.getenv("OPENAI_API_KEY")
                                if openai_api_key:
                                    resultado_categorizacao = processar_com_ia(texto_para_categorizar, openai_api_key, categorias_disponiveis)
                                    if resultado_categorizacao:
                                        item['categoria_id'] = resultado_categorizacao.get('categoria_id')
                                        item['desc_categoria'] = resultado_categorizacao.get('desc_categoria')
                                        logging.info(f"Categoria identificada: {resultado_categorizacao}")

                                    # Gerar descrição com IA
                                    descricao_gerada = gerar_descricao_com_ia(texto_para_categorizar, openai_api_key)
                                    if descricao_gerada:
                                        item['descricao_ia'] = descricao_gerada
                                        logging.info(f"Descrição gerada pela IA: {descricao_gerada}")
                                else:
                                    logging.error("Erro: Variável de ambiente OPENAI_API_KEY não configurada.")
                        
                        # Manter geração de CSV e logs
                        if all_results:
                            output_dir = "output"
                            os.makedirs(output_dir, exist_ok=True)
                            csv_file_path = os.path.join(output_dir, f"jurisprudencia_{data.replace('-', '')}.csv")
                            
                            # Escrever cabeçalho se o arquivo não existir
                            if not os.path.exists(csv_file_path):
                                with open(csv_file_path, 'w', newline='', encoding='utf-8') as f:
                                    writer = csv.DictWriter(f, fieldnames=all_results[0].keys())
                                    writer.writeheader()
                            
                            # Anexar dados
                            with open(csv_file_path, 'a', newline='', encoding='utf-8') as f:
                                writer = csv.DictWriter(f, fieldnames=all_results[0].keys())
                                writer.writerows(all_results)
                            logging.info(f"Dados salvos em {csv_file_path}")

                        page += 1
                    except json.JSONDecodeError:
                        logging.error("Erro ao decodificar JSON da resposta.")
                        break
                else:
                    logging.error(f"Erro na requisição: {response.status_code} - {response.text}")
                    break

    logging.info("request_singular finalizado.")
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

def processar_com_ia(texto, api_key, categorias_disponiveis):
    """Processa o texto usando a API da OpenAI para categorizar."""
    pasta_configs = os.path.join(os.path.dirname(__file__), 'prompts')
    prompt_categoria_path = os.path.join(pasta_configs, 'prompt_categoria.txt')

    try:
        with open(prompt_categoria_path, 'r', encoding='utf-8') as file:
            prompt_base = file.read()

        # Formatar as categorias disponíveis para o prompt
        categorias_formatadas = "\n".join([f"- {cat['codigo_categoria']}: {cat['desc_categoria']}" for cat in categorias_disponiveis])
        prompt_final = f"""{prompt_base}

Categorias disponíveis:
{categorias_formatadas}

------------------------------------
Este é o texto a ser analisado:
{texto}
------------------------------------"""

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

        value = None
        if messages_data.get("data"):
            first_message = messages_data["data"][0]
            if first_message.get("content"):
                first_content = first_message["content"][0]
                if first_content.get("type") == "text":
                    value = first_content.get("text", {}).get("value")

        if value:
            logging.info(f"Categoria identificada pela IA: {value}")
            # Tentar parsear o JSON retornado pela IA
            try:
                categoria_ia = json.loads(value)
                # Garantir que as chaves esperadas existam
                return {
                    "categoria_id": categoria_ia.get("categoria_id"),
                    "desc_categoria": categoria_ia.get("desc_categoria")
                }
            except json.JSONDecodeError:
                logging.error(f"Erro ao decodificar JSON da categoria da IA: {value}")
                return {"categoria_id": None, "desc_categoria": None}
        else:
            logging.warning("Nenhuma categoria de valor da IA.")
            return {"categoria_id": None, "desc_categoria": None}

    except Exception as e:
        logging.error(f"Erro geral na categorização por IA: {e}")
        return {"categoria_id": None, "desc_categoria": None}

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

    args = parser.parse_args()

    if args.data_fim is None:
        args.data_fim = args.data_inicio

    tribunais_disponiveis = load_tribunais()

    categorias_disponiveis = load_categorias()

    request_singular(args.data_inicio, args.data_fim, args.jurisprudencia, args.tribunais, categorias_disponiveis, args.only_csv)