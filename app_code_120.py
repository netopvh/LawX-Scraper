
import customtkinter as ctk
import sys
import os
import warnings
import logging
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
warnings.filterwarnings("ignore", category=DeprecationWarning, module="tensorflow")
import tensorflow as tf
tf.get_logger().setLevel('ERROR')
logging.getLogger('tensorflow').setLevel(logging.ERROR)
import json
import time
import textwrap
import requests
import json
import time
import pandas as pd
from datetime import datetime, timedelta
import threading
import unicodedata
import re
#-----------------------------------------------------------------------
pasta_script = os.path.dirname(os.path.abspath(__file__))
pasta_downloads_os = os.path.join(pasta_script, 'downloads')
pasta_configs = os.path.join(pasta_script, 'configurações')
arquivo_configs = os.path.join(pasta_configs, 'configs.json')   
arquivo_categorias = os.path.join(pasta_configs, 'categorias.json')
arquivo_status = os.path.join(pasta_configs, 'status.txt')  
arquivo_tribunais = os.path.join(pasta_configs, 'tribunais.json')   
arquivo_cache = os.path.join(pasta_configs, 'cache.json')       
pasta_relatorios = os.path.join(pasta_downloads_os, 'pasta_relatorios')
pasta_json = os.path.join(pasta_downloads_os, 'pasta_json')     
arquivo_salmple_relatorios = os.path.join(pasta_relatorios, 'sample.csv')
arquivo_salmple_json = os.path.join(pasta_json, 'sample.json')      
pasta_backup = os.path.join(pasta_script, 'pasta_backup') 
pasta_cache = os.path.join(pasta_script, 'pasta_cache') 
dados_para_salvar_geral = []
dados_para_salvar_filtrado = []
#--
# le o arquivo cache.json
# altera o valor de     "tribunal": para "TODOS"
# salva o arquivo cache.json
#--
arquivo_cache = os.path.join(pasta_configs, 'cache.json')
with open(arquivo_cache, 'r', encoding='utf-8') as file:
    cache_data = json.load(file)
    cache_data['tribunal'] = 'TODOS'
with open(arquivo_cache, 'w', encoding='utf-8') as file:
    json.dump(cache_data, file, ensure_ascii=False, indent=4)
    
#----------------------------------------------------------------------
def clean():
    #------------------------------------------------------------------
    def limpar_pasta_relatorios():
        if os.path.exists(pasta_relatorios):
            for arquivo in os.listdir(pasta_relatorios):
                caminho_arquivo = os.path.join(pasta_relatorios, arquivo)
                try:
                    if os.path.isfile(caminho_arquivo):
                        os.unlink(caminho_arquivo)
                        print(f"Arquivo {caminho_arquivo} apagado com sucesso.")
                except Exception as e:
                    print(f"Erro ao apagar o arquivo {caminho_arquivo}: {e}")
    limpar_pasta_relatorios()
    #------------------------------------------------------------------
    def limpar_pasta_backup():
        pasta_backup = os.path.join(pasta_script, 'pasta_backup') 
        pasta_backup_normalizado = os.path.join(pasta_backup, 'backup_normalizado') 
        pasta_backup_filtrado = os.path.join(pasta_backup_normalizado, 'backup_filtrado')
        pasta_backup_geral = os.path.join(pasta_backup_normalizado, 'backup_geral')

        for pasta in [pasta_backup_filtrado, pasta_backup_geral]:
            if os.path.exists(pasta):
                for arquivo in os.listdir(pasta):
                    caminho_arquivo = os.path.join(pasta, arquivo)
                    try:
                        if os.path.isfile(caminho_arquivo):
                            os.unlink(caminho_arquivo)
                            print(f"Arquivo {caminho_arquivo} apagado com sucesso.")
                    except Exception as e:
                        print(f"Erro ao apagar o arquivo {caminho_arquivo}: {e}")
    limpar_pasta_backup()
    #------------------------------------------------------------------
    def limpar_pasta_cache():
        if os.path.exists(pasta_cache):
            for arquivo in os.listdir(pasta_cache):
                caminho_arquivo = os.path.join(pasta_cache, arquivo)
                try:
                    if os.path.isfile(caminho_arquivo):
                        os.unlink(caminho_arquivo)
                        print(f"Arquivo {caminho_arquivo} apagado com sucesso.")
                except Exception as e:
                    print(f"Erro ao apagar o arquivo {caminho_arquivo}: {e}")
    limpar_pasta_cache()
    #------------------------------------------------------------------
    def limpar_pasta_buffer():
        pasta_buffer = os.path.join(pasta_script, 'pasta_buffer')
        if os.path.exists(pasta_buffer):
            for arquivo in os.listdir(pasta_buffer):
                caminho_arquivo = os.path.join(pasta_buffer, arquivo)
                try:
                    if os.path.isfile(caminho_arquivo):
                        os.unlink(caminho_arquivo)
                        print(f"Arquivo {caminho_arquivo} apagado com sucesso.")
                except Exception as e:
                    print(f"Erro ao apagar o arquivo {caminho_arquivo}: {e}")
    limpar_pasta_buffer()
    #------------------------------------------------------------------
#----------------------------------------------------------------------
dados_padrao = {
    "pasta_padrao": True,
    "pasta_downloads": "",
    "preencher_data": True,
    "nomenclatura": "data_tribunal",
    "arquitetura": "xlsx",
    "busca_multipla": "não",
    "data-type": "dia-hoje",
}
#----------------------------------------------------------------------
if os.path.exists(arquivo_configs) and os.path.getsize(arquivo_configs) > 0:
    try:
        with open(arquivo_configs, 'r+', encoding='utf-8') as f:
            configs = json.load(f)  
            configs["pasta_downloads"] = pasta_downloads_os  
            f.seek(0)  
            json.dump(configs, f, indent=4, ensure_ascii=False)
            f.truncate()  
    except json.JSONDecodeError:
        with open(arquivo_configs, 'w', encoding='utf-8') as f:
            json.dump(dados_padrao, f, indent=4, ensure_ascii=False)
else:
    with open(arquivo_configs, 'w', encoding='utf-8') as f:
        json.dump(dados_padrao, f, indent=4, ensure_ascii=False)
#----------------------------------------------------------------------
if os.path.exists(arquivo_configs) and os.path.getsize(arquivo_configs) > 0:
    with open(arquivo_configs, 'r+', encoding='utf-8') as f:
        configs = json.load(f)  
        configs["pasta_downloads"] = pasta_downloads_os
        f.seek(0) 
        json.dump(configs, f, indent=4, ensure_ascii=False)
        f.truncate() 
else:
    configs = {"pasta_downloads": pasta_downloads_os}
    with open(arquivo_configs, 'w', encoding='utf-8') as f:
        json.dump(configs, f, indent=4, ensure_ascii=False)
#---------------------------------------------------------------------
if not os.path.exists(pasta_downloads_os):
    os.makedirs(pasta_downloads_os)
if not os.path.exists(pasta_configs):
    os.makedirs(pasta_configs)
if not os.path.exists(arquivo_configs):
    with open(arquivo_configs, 'w') as f:
        f.write('{}')  # Criando um arquivo JSON vazio
if not os.path.exists(arquivo_status):
    with open(arquivo_status, 'w') as f:
        f.write('')  # Criando um arquivo de texto vazio
if not os.path.exists(arquivo_tribunais):
    with open(arquivo_tribunais, 'w') as f:
        f.write('{}')  # Criando um arquivo JSON vazio
if not os.path.exists(arquivo_cache):
    with open(arquivo_cache, 'w') as f:
        f.write('{}')  # Criando um arquivo JSON vazio
if not os.path.exists(pasta_relatorios):
    os.makedirs(pasta_relatorios)
if not os.path.exists(pasta_json):
    os.makedirs(pasta_json)
if not os.path.exists(arquivo_salmple_relatorios):
    with open(arquivo_salmple_relatorios, 'w') as f:
        f.write('')  # Criando um arquivo JSON vazio
if not os.path.exists(arquivo_salmple_json):
    with open(arquivo_salmple_json, 'w') as f:
        f.write('')  # Criando um arquivo JSON vazio
#----------------------------------------------------------------------     
print(f"Pasta do script: {pasta_script}")
print(f"Pasta de downloads: {pasta_downloads_os}")
print(f"Pasta de configurações: {pasta_configs}")
print(f"Arquivo de configurações: {arquivo_configs}")
print(f"Arquivo de status: {arquivo_status}")
print(f"Arquivo de tribunais: {arquivo_tribunais}")
print(f"Arquivo de cache: {arquivo_cache}")
print(f"Pasta de relatórios: {pasta_relatorios}")
print(f"Pasta de JSONs: {pasta_json}")
print(f"Arquivo de exemplo de relatórios: {arquivo_salmple_relatorios}")
print(f"Arquivo de exemplo de JSON: {arquivo_salmple_json}")
print("\nStatus das pastas e arquivos:")
print(f"A pasta 'downloads' existe? {'Sim' if os.path.exists(pasta_downloads_os) else 'Não'}")
print(f"A pasta 'configurações' existe? {'Sim' if os.path.exists(pasta_configs) else 'Não'}")
#----------------------------------------------------------------------  
print(f"O arquivo 'configs.json' existe? {'Sim' if os.path.exists(arquivo_configs) else 'Não'}")
print(f"O arquivo 'status.txt' existe? {'Sim' if os.path.exists(arquivo_status) else 'Não'}")
print(f"O arquivo 'tribunais.json' existe? {'Sim' if os.path.exists(arquivo_tribunais) else 'Não'}")
print(f"O arquivo 'cache.json' existe? {'Sim' if os.path.exists(arquivo_cache) else 'Não'}")    
print(f"A pasta 'pasta_relatorios' existe? {'Sim' if os.path.exists(pasta_relatorios) else 'Não'}")
print(f"A pasta 'pasta_json' existe? {'Sim' if os.path.exists(pasta_json) else 'Não'}")
print(f"O arquivo de exemplo 'sample.csv' existe? {'Sim' if os.path.exists(arquivo_salmple_relatorios) else 'Não'}")
print(f"O arquivo de exemplo 'sample.json' existe? {'Sim' if os.path.exists(arquivo_salmple_json) else 'Não'}")
#----------------------------------------------------------------------
def verificar_estrutura_configs():
    estrutura_esperada = {
        "pasta_padrao": bool,
        "pasta_downloads": str,
        "preencher_data": bool,
        "nomenclatura": str,
        "arquitetura": str,
        "data-type": str,
        "lista_modelos": list,
        "api_key": str,
        "modelo_atual": str
    }
    
    with open(arquivo_configs, 'r', encoding='utf-8') as file:
        configs = json.load(file)
        print("Verificando estrutura do arquivo configs.json...")
        print(configs)
        for chave, tipo in estrutura_esperada.items():
            if chave not in configs or not isinstance(configs[chave], tipo):
                print(f"Erro na estrutura do arquivo configs.json: chave '{chave}' ausente ou tipo incorreto.")
                return False
        print("Arquivo configs.json está estruturado corretamente.")
verificar_estrutura_configs()
#----------------------------------------------------------------------
def request_singular(resume=False):
    pass
#_-----------------
def request_tribunal():
    pass
root = ctk.CTk()
pause_event = threading.Event()
is_paused = False
is_running = False  
leitura_anterior = False
frame_coluna1 = ctk.CTkFrame(root, width=350, height=850, fg_color='#D9D9D9')
entry_tribunais = None
dropdown_tribunais = None
method_request = ''
entry_tribunais = ctk.CTkEntry(frame_coluna1, width=300, height=40, font=('Arial', 12), text_color='white', placeholder_text="Digite os tribunais separados por vírgula")
#----------------------------------------------------------------------
with open(arquivo_tribunais, 'r', encoding='utf-8') as file:
    tribunais_data = json.load(file)
    lista_tribunais = tribunais_data.get('lista_tribunais', [])
    if isinstance(lista_tribunais, str):
        lista_tribunais = lista_tribunais.split(',')
#----------------------------------------------------------------------
dropdown_tribunais = ctk.CTkComboBox(frame_coluna1, width=300, height=40, font=('Arial', 12), text_color='white', values=lista_tribunais)
#----------------------------------------------------------------------     
arquivo_docs = os.path.join(pasta_configs, 'docs.json') 
if not os.path.exists(arquivo_docs):
    with open(arquivo_docs, 'w', encoding='utf-8') as f:
        json.dump({"lista_docs": []}, f, ensure_ascii=False, indent=4)
with open(arquivo_docs, 'r', encoding='utf-8') as file:
    tipodoc_data = json.load(file)
    lista_tipodoc = tipodoc_data.get('lista_docs', [])
    if isinstance(lista_tipodoc, str):
        lista_tipodoc = lista_tipodoc.split(',')
valor_selecionado = ctk.StringVar()
dropdwon_tipodocumento = ctk.CTkComboBox(
    frame_coluna1,
    width=300,
    height=40,
    font=('Arial', 12),
    text_color='white',
    values=lista_tipodoc,  # Passa a lista de valores
    variable=valor_selecionado  # Define a variável para o valor selecionado
)
#----------------------------------------------------------------------
global contador_buffer
limitador_ui = 25  
limiter_buffer = 10 
#----------------------------------------------------------------------
pasta_downloads_final = ctk.StringVar()
pasta_padrao_var = ctk.StringVar()
preencher_data_var = ctk.StringVar()
nomenclatura_var = ctk.StringVar()
formato_saida_var = ctk.StringVar()
data_entrada_var = ctk.StringVar()
data_saida_var = ctk.StringVar()
busca_multipla_var = ctk.StringVar()
entry_multiplas_buscas_var = ctk.StringVar()    
dropdown_tribunais_var = ctk.StringVar()
status_atual_var = ctk.StringVar()
pag_atual_var = ctk.StringVar()
tt_txt_acordao_var = ctk.StringVar()
tt_txt_ementa_var = ctk.StringVar()
tt_doc_ementa_var = ctk.StringVar()
tt_doc_acordao_var = ctk.StringVar()
contador_txt_acordao_var= ctk.StringVar()
contador_txt_ementa_var = ctk.StringVar()
contador_doc_ementa_var = ctk.StringVar()
contador_doc_acordao_var= ctk.StringVar()
data_type_var = ctk.StringVar()
api_atual = ctk.StringVar() 
api_pinecone = ctk.StringVar()
lista_modelos_var = ctk.StringVar()
tribunal = ''
#----------------------------------------------------------------------
with open(arquivo_status, 'w', encoding='utf-8') as file:
    file.write("Em repouso...")
#----------------------------------------------------------------------
def limpar_pasta_json():
    pasta_json = os.path.join(pasta_downloads_os, 'pasta_json')
    if os.path.exists(pasta_json):
        for arquivo in os.listdir(pasta_json):
            caminho_arquivo = os.path.join(pasta_json, arquivo)
            try:
                if os.path.isfile(caminho_arquivo):
                    os.unlink(caminho_arquivo)
                    print(f"Arquivo {caminho_arquivo} apagado com sucesso.")
            except Exception as e:
                print(f"Erro ao apagar o arquivo {caminho_arquivo}: {e}")
limpar_pasta_json()
#----------------------------------------------------------------------
def api_request(): 
    global entry_tribunais, dropdown_tribunais, tribunal
    print('- sequenciador api_request() -----------')    
    # ------------------------------------------------------------------
    print('----------------------------------------')
    with open (arquivo_configs, 'r', encoding='utf-8') as file:
        configs = json.load(file)
        nomenclatura = configs['nomenclatura']
        arquitetura = configs['arquitetura']
        local_saida = configs['pasta_downloads']
        busca_multipla = configs['busca_multipla']
        lista_modelos = configs['lista_modelos']
        api_key = configs['api_key']
        modelo_atual = configs['modelo_atual']
    print(' - nomenclatura_var ==', nomenclatura)
    print(' - pasta_downloads_final ==', local_saida)   
    print(' - busca_multipla ==', busca_multipla)
    print(' - arquitetura ==', arquitetura)  
    # ------------------------------------------------------------------
    if busca_multipla == 'sim':
        tribunais = entry_multiplas_buscas_var.get().split(',')
        print(' - tribunais ==', tribunais) 
    if busca_multipla == 'não':
        tribunais = dropdown_tribunais_var.get()
        print(' - tribunal_alvo ==', tribunais)
    print(' - tribunais ==', tribunais) 
    with open(arquivo_tribunais, 'r', encoding='utf-8') as file:
        tribunais_data = json.load(file)
        lista_tribunais = tribunais_data['lista_tribunais']
    tribunais_nao_encontrados = [tribunal for tribunal in tribunais if tribunal not in lista_tribunais]
    print('----------------------------------------')
    #------------------------------------------------------------------
    if tribunais == 'TODOS':
        print('request_todos_null')
        request_todos()
    # ------------------------------------------------------------------
    if busca_multipla == 'sim':
        for tribunal in tribunais:
            print(' - tribunal ==', tribunal)
            print (' request_null')
            # request_tribunal(tribunal)
    # ------------------------------------------------------------------
    if busca_multipla == 'não' and tribunais != 'TODOS':
        tribunal = tribunais.split()[0]
        print(' - tribunal ==', tribunal)
        request_singular()
    # ------------------------------------------------------------------
#----------------------------------------------------------------------
def request_api(): 
    global frame_coluna1, dropdown_tribunais, entry_tribunais
    import threading
    threading.Thread(target=api_request).start()
#----------------------------------------------------------------------
def pesquisar():    
    global method_request
    method_request = 'new'
    global frame_coluna1, dropdown_tribunais, entry_tribunais, entry_artigo_procurado, tipo_busca_var
    data_inicio = entry_data_entrada.get()
    data_fim = entry_data_saida.get()
    artigo_procurado = entry_artigo_procurado.get()
    tipo_busca = tipo_busca_var.get()   
    pasta_final = pasta_downloads_final.get()
    print('##################################################')
    print('### NOVA REQUEST #################################')
    print(' - data_inicio ==', data_inicio)
    print(' - data_fim == ', data_fim)
    print(' - tipo_busca ==', tipo_busca)       
    #--------------------------------------------------
    if os.path.exists(arquivo_configs):
        with open(arquivo_configs, 'r', encoding='utf-8') as file:
            configs = json.load(file)
            nomenclaturaf = ''
            arquiteturaf = ''
            nomenclatura = configs.get('nomenclatura', nomenclaturaf)
            arquitetura = configs.get('arquitetura', arquiteturaf)
    else:
        nomenclatura = 'data_tribunal'
        arquitetura = 'csv' 
    print(' - nomenclatura ==', nomenclatura)
    print(' - arquitetura ==', arquitetura)
    #--------------------------------------------------
    if tipo_busca == 'Artigo':
        artigo_procurado = [f'art. {artigo_procurado}', f'artigo {artigo_procurado}', f'art {artigo_procurado}']
    #--------------------------------------------------
    print(f' - {tipo_busca}_procurado ==', artigo_procurado)
    print('----------------------------------------')
    print(' - efetuando request api ')  
    print('----------------------------------------')
    global is_paused
    is_paused = False
    global btn_pause
    btn_pause.configure(text="Pausar")
    pause_event.clear() 
    request_api()
#----------------------------------------------------------------------
def popup_configs():
    global api_pinecone
    global frame_coluna1, dropdown_tribunais, entry_tribunais
    global busca_multipla_var, dropdown_tribunais, lista_modelos_var
    global root, pasta_downloads_final, pasta_padrao_var, preencher_data_var, nomenclatura_var, formato_saida_var, data_type_var
    from tkinter import filedialog
    popup = ctk.CTkToplevel(root)
    popup.title("Configurações")
    popup.geometry("700x700")
    popup.resizable(False, False)
    popup.transient(root) #filiacao_root
    popup.grab_set() #bloqueia_root
    popup.focus() #foca_top
    #----------------------------------------------------------
    pasta_downloadsf = ''
    def selecionar_pasta():
        nova_pasta = filedialog.askdirectory(initialdir=pasta_downloads_os, title="Selecione a pasta de downloads")
        if nova_pasta:
            print(nova_pasta)
            pasta_downloads_final.set(nova_pasta)
            pasta_padrao_var.set("Não")
    if os.path.exists(arquivo_configs):
        with open(arquivo_configs, 'r', encoding='utf-8') as file:
            configs = json.load(file)
            pasta_downloadsf = configs.get('pasta_downloads', pasta_downloadsf)
    print('pasta_dl (direto)', pasta_downloadsf)
    pasta_downloads_final.set(pasta_downloadsf)
    print('pasta_dl (StringVar)', pasta_downloads_final.get())
    #-----------------------------------------------------------
    if os.path.exists(arquivo_configs):
        with open(arquivo_configs, 'r', encoding='utf-8') as file:
            configs = json.load(file)
            if configs.get('pasta_padrao', True):
                pasta_padrao_var.set("Sim")
            else:
                pasta_padrao_var.set("Não")
    label_configuracoes = ctk.CTkLabel(popup, text="Configurações", font=('Arial', 12, 'bold'))
    label_configuracoes.place(x=50, y=10)
    label_pasta_padrao = ctk.CTkLabel(popup, text="Pasta Padrão:", font=('Arial', 12))
    label_pasta_padrao.place(x=50, y=50)
    #-----------------------------------------------------------
    def update_pasta_downloads(*args):
        if pasta_padrao_var.get() == "Sim":
            pasta_downloads_final.set(pasta_downloads_os)
    #-----------------------------------------------------------
    pasta_padrao_var.trace_add("write", update_pasta_downloads)
    radio_sim = ctk.CTkRadioButton(popup, text="Sim", variable=pasta_padrao_var, value="Sim")
    radio_sim.place(x=200, y=50)
    radio_nao = ctk.CTkRadioButton(popup, text="Não", variable=pasta_padrao_var, value="Não")
    radio_nao.place(x=325, y=50)
    label_pasta_dl = ctk.CTkLabel(popup, text="Pasta de Downloads:", font=('Arial', 12))
    label_pasta_dl.place(x=50, y=100)
    pasta_downloads_label = ctk.CTkLabel(popup, textvariable=pasta_downloads_final, font=('Arial', 12), width=600, anchor="w")
    pasta_downloads_label.place(x=200, y=100)
    #-----------------------------------------------------------
    label_alterar_pasta = ctk.CTkLabel(popup, text="Alterar Pasta:", font=('Arial', 12))    
    label_alterar_pasta.place(x=50,y=150)
    botao_alterar_pasta = ctk.CTkButton(popup, text="Selecionar Pasta", command=selecionar_pasta)
    botao_alterar_pasta.place(x=200, y=150)
    #--------------------------------------------------------
    if os.path.exists(arquivo_configs):
        with open(arquivo_configs, 'r', encoding='utf-8') as file:
            configs = json.load(file)
            if configs.get('preencher_data', True):
                preencher_data_var.set("Sim")
            else:
                preencher_data_var.set("Não")
    #--------------------------------------------------------
    label_preencher_data = ctk.CTkLabel(popup, text="Auto Preencher Data:", font=('Arial', 12))
    label_preencher_data.place(x=50, y=200)
    radio_preencher_sim = ctk.CTkRadioButton(popup, text="Sim", variable=preencher_data_var, value="Sim")
    radio_preencher_sim.place(x=200, y=200)
    radio_preencher_nao = ctk.CTkRadioButton(popup, text="Não", variable=preencher_data_var, value="Não")
    radio_preencher_nao.place(x=325, y=200)
    #--------------------------------------------------------
    if os.path.exists(arquivo_configs):
        with open(arquivo_configs, 'r', encoding='utf-8') as file:
            configs = json.load(file)
            nomenclatura_var.set(configs.get('nomenclatura', 'data_tribunal'))
            
    if os.path.exists(arquivo_configs):
        with open(arquivo_configs, 'r', encoding='utf-8') as file:
            print('loading_data')
            configs = json.load(file)
            busca_multipla = ''
            formato_saida = ''
            data_type = ''
            api_key = ''
            modelo_atual = ''
            api_pinecone = ''
            busca_multipla_var.set(configs.get('busca_multipla', busca_multipla))
            print(' - busca_multipla_var ==', busca_multipla_var.get())
            formato_saida_var.set(configs.get('arquitetura', formato_saida))
            print(' - formato_saida_var ==', formato_saida_var.get())
            data_type_var.set(configs.get('data-type', data_type))
            api_atual.set(configs.get('api_key', api_key))  
            api_pinecone = configs.get('api_pinecone', api_pinecone)
            print(' - api_pinecone ==', api_pinecone)
            
            print(' - api_atual ==', api_atual.get())

            # Obtenha o modelo atual e a lista de modelos
            modelo_atual = configs.get('modelo_atual', '')
            lista_modelos_list = configs.get('lista_modelos', [])  # Garante que seja uma lista
            print(' - lista_modelos_list ==', lista_modelos_list)
    else:
        lista_modelos_list = []
        modelo_atual = ""

    # Crie um StringVar para armazenar o valor selecionado (se necessário)
    modelo_selecionado_var = ctk.StringVar(value=modelo_atual)

    # Cria o ComboBox usando a lista de modelos e vinculando o valor selecionado
    modelo_utilizado_dropdown = ctk.CTkComboBox(
        popup, 
        width=300, 
        height=40, 
        font=('Arial', 12), 
        text_color='white', 
        values=lista_modelos_list,  # Aqui passamos uma lista!
        variable=modelo_selecionado_var  # Vincula o valor selecionado ao StringVar
    )

    modelo_utilizado_dropdown.place(x=200, y=500)
            
    label_nomenclatura = ctk.CTkLabel(popup, text="Nomenclatura:", font=('Arial', 12))
    label_nomenclatura.place(x=50, y=250)
    radio_data_tribunal = ctk.CTkRadioButton(popup, text="Data-Tribunal", variable=nomenclatura_var, value="data_tribunal")
    radio_data_tribunal.place(x=200, y=250)
    radio_tribunal_data = ctk.CTkRadioButton(popup, text="Tribunal-Data", variable=nomenclatura_var, value="tribunal_data")
    radio_tribunal_data.place(x=325, y=250)
    #--------------------------------------------------------
    label_formato_saida = ctk.CTkLabel(popup, text="Formato de Saída:", font=('Arial', 12))
    label_formato_saida.place(x=50, y=300)
    radio_csv = ctk.CTkRadioButton(popup, text="CSV", variable=formato_saida_var, value="csv")
    radio_csv.place(x=200, y=300)
    radio_xlsx = ctk.CTkRadioButton(popup, text="XLSX", variable=formato_saida_var, value="xlsx")
    radio_xlsx.place(x=325, y=300)
    #--------------------------------------------------------   
    # label_busca_multipla = ctk.CTkLabel(popup, text="Busca Múltipla:", font=('Arial', 12))
    # label_busca_multipla.place(x=50, y=350)
    # radio_sim = ctk.CTkRadioButton(popup, text="Sim", variable=busca_multipla_var, value="sim")
    # radio_sim.place(x=200, y=350)
    # radio_nao = ctk.CTkRadioButton(popup, text="Não", variable=busca_multipla_var, value="não")
    # radio_nao.place(x=325, y=350)   

    label_data_var_ou_dia = ctk.CTkLabel(popup, text="Salvar data como:", font=('Arial', 12))
    label_data_var_ou_dia.place(x=50, y=400)

    radio_data_var_sim = ctk.CTkRadioButton(popup, text="dia-hoje", variable=data_type_var, value="dia-hoje")
    radio_data_var_sim.place(x=200, y=400)
    radio_data_var_nao = ctk.CTkRadioButton(popup, text="dia-variavel", variable=data_type_var, value="dia-variavel")
    radio_data_var_nao.place(x=325, y=400)


    label_api_key = ctk.CTkLabel(popup, text="API Key: (GPT)", font=('Arial', 12))
    label_api_key.place(x=50, y=450)
    entry_api_key = ctk.CTkEntry(popup, width=300, height=40, textvariable = api_atual ,font=('Arial', 12), text_color='white')
    entry_api_key.place(x=200, y=450)
    
    label_modelos = ctk.CTkLabel(popup, text="Modelos Utilizados:", font=('Arial', 12))
    label_modelos.place(x=50, y=500)    
    
    
    pasta_configurações = os.path.join(pasta_configs, 'configs.json')
    with open(pasta_configurações, 'r', encoding='utf-8') as file:
        configs = json.load(file)
        api_key_pinecone = configs.get('api_pinecone', '')
    print(' - api_key_pinecone ==', api_key_pinecone)

    api_pinecone_var = ctk.StringVar(value=api_key_pinecone)

    label_api_pinecone = ctk.CTkLabel(popup, text="API Key: (Pinecone)", font=('Arial', 12))
    label_api_pinecone.place(x=50, y=550)

    entry_api_pinecone = ctk.CTkEntry(popup, width=300, height=40, textvariable=api_pinecone_var, font=('Arial', 12), text_color='white')
    entry_api_pinecone.place(x=200, y=550)
    #--------------------------------------------------------
    def salvar():
        settings = {
            'pasta_padrao': pasta_padrao_var.get() == "Sim",
            'pasta_downloads': pasta_downloads_final.get(),
            'preencher_data': preencher_data_var.get() == "Sim",
            'nomenclatura': nomenclatura_var.get() , 
            'arquitetura': formato_saida_var.get()  ,
            'busca_multipla': busca_multipla_var.get(),
            'data-type': data_type_var.get(),
            'api_key': entry_api_key.get(),
            'api_pinecone': entry_api_pinecone.get(),
            'modelo_atual': modelo_utilizado_dropdown.get(),
            'lista_modelos': modelo_utilizado_dropdown.cget('values')
            
        }
        with open(arquivo_configs, 'w', encoding='utf-8') as file:
            json.dump(settings, file, ensure_ascii=False, indent=4)
        #----------------------------------------
        if busca_multipla_var.get() == "sim":
            entry_tribunais = ctk.CTkEntry(frame_coluna1, width=300, height=40, font=('Arial', 12), text_color='white', textvariable=entry_multiplas_buscas_var)
            entry_tribunais.place(x=20, y=50)  
            try:
                dropdown_tribunais.destroy()
            except:
                print("O widget não está presente na UI.")
            #----------------------------------------------------------------------
        if busca_multipla_var.get() == "não":   
            with open(arquivo_tribunais, 'r', encoding='utf-8') as file:
                tribunais_data = json.load(file)
                lista_tribunais = tribunais_data.get('lista_tribunais', [])
                if isinstance(lista_tribunais, str):
                    lista_tribunais = lista_tribunais.split(',')
            dropdown_tribunais = ctk.CTkComboBox(frame_coluna1, width=300, height=40, font=('Arial', 12), text_color='white', values=lista_tribunais)
            dropdown_tribunais.place(x=20, y=50)
            try:
                entry_tribunais.destroy()
            except:
                print("O widget não está presente na UI.")
        popup.destroy()
    #--------------------------------------------------------
    botao_salvar = ctk.CTkButton(popup, text="Salvar", command=salvar, width=200)
    botao_salvar.place(x=50,y=650)  
    botao_cancelar = ctk.CTkButton(popup, text="Cancelar", command=popup.destroy, width=200)
    botao_cancelar.place(x=300,y=650)
    #--------------------------------------------------------
    def center_popup(popup):
        popup.update_idletasks()
        popup_width = popup.winfo_width()
        popup_height = popup.winfo_height()
        root_x = root.winfo_x()
        root_y = root.winfo_y()
        root_width = root.winfo_width()
        root_height = root.winfo_height()
        popup_x = root_x + (root_width - popup_width) // 2
        popup_y = root_y + (root_height - popup_height) // 2
        popup.geometry(f"{popup_width}x{popup_height}+{popup_x}+{popup_y}")
    popup.after(10, lambda: center_popup(popup))
#---------------------------------------------------------------------- 
def reload_cache():
    print('-thread iniciada')
    global leitura_anterior
    global method_request
    leitura_anterior = True  # 🔴 Marca que a execução foi retomada pelo cache
    method_request = 'update'
    if os.path.exists(arquivo_cache):
        with open(arquivo_cache, 'r', encoding='utf-8') as f:
            cache = json.load(f)
        if 'current_page' in cache and 'current_date_index' in cache:
            data_inicio = datetime.strptime(cache['data_inicio'], "%d/%m/%Y").strftime("%Y-%m-%d")
            data_fim = datetime.strptime(cache['data_fim'], "%d/%m/%Y").strftime("%Y-%m-%d")
            current_date_index = cache['current_date_index']
            page = cache['current_page']
            tribunal = cache['tribunal']
            base_url = 'https://comunicaapi.pje.jus.br/api/v1/comunicacao'
            with open(arquivo_configs, 'r', encoding='utf-8') as file:
                configs = json.load(file)
                busca_multipla = configs['busca_multipla']
                lista_modelos = configs['lista_modelos']
                api_key = configs['api_key']
                modelo_atual = configs['modelo_atual']
            print(' - busca_multipla ==', busca_multipla)       
            print(' - tribunal ==', tribunal)
            #------------------------------------------------------------------
            if tribunal == "TODOS": 
                print('reiniciando TODOS')
                tribunal == ''  
                current_date_index = 1  
                request_todos(resume=True)
            #------------------------------------------------------------------
            if busca_multipla == 'não' and tribunal != "TODOS":     
                print(f'reiniciando SINGULAR {tribunal}')
                params = {
                    "pagina": page,
                    "itensPorPagina": 100,
                    "siglaTribunal": tribunal,
                    "dataDisponibilizacaoInicio": data_inicio,
                    "dataDisponibilizacaoFim": data_fim,
                }
                current_date_index = 1
                request_singular(resume=True)
            #------------------------------------------------------------------     
            if busca_multipla  == 'sim':
                tribunal = cache['tribunal']    
                print(f'reiniciando busca multipla {tribunal}')
                request_todos(resume=True)
                
            else:
                request_singular(resume=True)
                print(f"🔄 Retomando da página {page}, índice {current_date_index}")
        else:
            print("❌ Cache inválido, reiniciando do zero...")
            request_singular(resume=False)
    else:
        print("Nenhum cache encontrado!")    
#----------------------------------------------------------------------
def return_from_cache():  
    print('-iniciando thread reload')
    global frame_coluna1, dropdown_tribunais, entry_tribunais
    import threading
    threading.Thread(target=reload_cache).start()
#----------------------------------------------------------------------
def janela_principal():         
    global login_ok
    login_ok = False
    def login_popup():
        global login_ok
        login_ok = False
        popup = ctk.CTkToplevel(root)
        popup.title("Login")
        popup.geometry("300x200")
        popup.resizable(False, False)
        window_width = 600
        window_height = 400
        screen_width = popup.winfo_screenwidth()
        screen_height = popup.winfo_screenheight()
        position_top = int((screen_height - window_height) / 2)
        position_right = int((screen_width - window_width) / 2)
        popup.geometry(f'{window_width}x{window_height}+{position_right}+{position_top}')
        ctk.CTkLabel(popup, text="Login:").pack(pady=10)
        login_entry = ctk.CTkEntry(popup)
        login_entry.pack(pady=5)
        ctk.CTkLabel(popup, text="Senha:").pack(pady=10)
        senha_entry = ctk.CTkEntry(popup, show="*")
        senha_entry.pack(pady=5)
        error_label = ctk.CTkLabel(popup, text="", text_color="red")
        error_label.pack(pady=5)
        def validate_login():
            global login_ok
            if login_entry.get() == "fhfdiniz" and senha_entry.get() == "#Atirador33":   
                login_ok = True 
                popup.geometry("1570x760") 
                time.sleep(1)
                popup.destroy()
                iframe_esquerda()
                iframe_tabela() 
                center_window(root)
            else:
                error_label.configure(text="Login ou senha incorretos")
        popup.bind('<Return>', lambda event: validate_login())
        ctk.CTkButton(popup, text="Login", command=validate_login).pack(pady=20)
        popup.protocol("WM_DELETE_WINDOW", sys.exit)  
        popup.transient(root)  # Make the popup a child of root
        popup.grab_set()  # Ensure all events are sent to the popup
        popup.focus()  # Focus on the popup
#----------------------------------------------------------------------
    global frame_coluna1, dropdown_tribunais, entry_tribunais, entry_artigo_procurado, tipo_busca_var
    global root, arquivo_status, entry_data_entrada, entry_artigo_procurado
    #------------------------------------------------------------------
    window_width = 1570
    window_height = 760 
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    position_top = int((screen_height - window_height) / 2 - 40)
    position_right = int((screen_width - window_width) / 2)
    root.geometry(f'{window_width}x{window_height}+{position_right}+{position_top}')
    ctk.CTkLabel(root, text="Valide o acesso para concluir o carregamento").pack(pady=20)
    #------------------------------------------------------------------
    def iframe_esquerda():
        global frame_coluna1, dropdown_tribunais, entry_tribunais
        global entry_data_entrada, entry_data_saida, entry_artigo_procurado, tipo_busca_var
        from datetime import datetime
        if os.path.exists(arquivo_configs):
            with open(arquivo_configs, 'r', encoding='utf-8') as file:
                configs = json.load(file)
            if configs.get('preencher_data', True):
                data_hoje = datetime.now().strftime("%d/%m/%Y")
            else:
                data_hoje = " "
        else:
            data_hoje = " "
        print(' - data_hoje ==', data_hoje)
        data_entrada_var = ctk.StringVar(value=data_hoje)
        data_saida_var = ctk.StringVar(value=data_hoje)
        #---------------------------------------------------
        frame_coluna1.place(x=20,y=5)
        #---------------------------------------------------
        label_tribunais = ctk.CTkLabel(frame_coluna1, text='Tribunais', font=('Arial', 12), text_color='black')  
        label_tribunais.place(x=20, y=10)
        #---------------------------------------------------
        with open(arquivo_configs, 'r', encoding='utf-8') as file:
            configs = json.load(file)
            busca_multipla = configs['busca_multipla']
            lista_modelos = configs['lista_modelos']
            api_key = configs['api_key']
            modelo_atual = configs['modelo_atual']
        if busca_multipla == 'não':    
            print(' - busca_multipla ==', configs.get('busca_multipla', 'não')) 
            with open(arquivo_tribunais, 'r', encoding='utf-8') as file:
                tribunais_data = json.load(file)
                lista_tribunais = tribunais_data['lista_tribunais']
            dropdown_tribunais = ctk.CTkComboBox(frame_coluna1, width=300, height=40, font=('Arial', 12), text_color='white', values=lista_tribunais, variable=dropdown_tribunais_var)
            dropdown_tribunais.place(x=20, y=50)
            dropdown_tribunais.set('TODOS')
            print('-------tribunais dropdown')
        if busca_multipla == 'sim':
            entry_tribunais = ctk.CTkEntry(frame_coluna1, width=300, height=40, font=('Arial', 12), text_color='white', textvariable=entry_multiplas_buscas_var)
            entry_tribunais.place(x=20, y=50)   
            print('-------tribunais entry')
        #---------------------------------------------------
        label_data_entrada = ctk.CTkLabel(frame_coluna1, text='Data início ( dd / mm / aaaa )', font=('Arial', 12), text_color='black')
        label_data_entrada.place(x=20, y=100)
        #---------------------------------------------------
        def mascara_data_inicio(event):
            data_inicio = entry_data_entrada.get()
            data_inicio = ''.join(filter(str.isdigit, data_inicio))
            if len(data_inicio) > 8:
                data_inicio = data_inicio[:8]
            data_formatada_inicio = ""
            if len(data_inicio) >= 2:
                data_formatada_inicio = data_inicio[:2]  # Adiciona o dia
                entry_data_entrada.delete(0, ctk.END)
                entry_data_entrada.insert(0, data_formatada_inicio)
            if len(data_inicio) > 2:
                data_formatada_inicio += "/" + data_inicio[2:4]  # Adiciona o mês
                entry_data_entrada.delete(0, ctk.END)
                entry_data_entrada.insert(0, data_formatada_inicio)
            if len(data_inicio) > 4:
                data_formatada_inicio += "/" + data_inicio[4:8]  # Adiciona o ano
                entry_data_entrada.delete(0, ctk.END)
                entry_data_entrada.insert(0, data_formatada_inicio)
        #---------------------------------------------------
        entry_data_entrada = ctk.CTkEntry(frame_coluna1, width=300, height=40, font=('Arial', 12), textvariable=data_entrada_var, text_color='white', placeholder_text="DD / MM / AAAA")
        entry_data_entrada.place(x=20, y=140)
        entry_data_entrada.bind("<KeyRelease>", mascara_data_inicio)
        #---------------------------------------------------
        label_data_saida = ctk.CTkLabel(frame_coluna1, text='Data fim ( dd / mm / aaaa )', font=('Arial', 12), text_color='black')
        label_data_saida.place(x=20, y=190)
        #---------------------------------------------------
        def mascara_data_fim(event):
            data_saida = ''.join(filter(str.isdigit, entry_data_saida.get()))  # Filtra apenas números
            data_saida_formatada = ""
            if len(data_saida) >= 2:
                data_saida_formatada += data_saida[:2]  # Dia
                entry_data_saida.delete(0, ctk.END)
                entry_data_saida.insert(0, data_saida_formatada)
            if len(data_saida) > 2:
                data_saida_formatada += "/" + data_saida[2:4]  # Mês
                entry_data_saida.delete(0, ctk.END)
                entry_data_saida.insert(0, data_saida_formatada)
            if len(data_saida) > 4:
                data_saida_formatada += "/" + data_saida[4:8]  # Ano
                entry_data_saida.delete(0, ctk.END)
                entry_data_saida.insert(0, data_saida_formatada)
        #---------------------------------------------------
        entry_data_saida = ctk.CTkEntry(frame_coluna1, width=300, height=40, font=('Arial', 12),textvariable=data_saida_var, text_color='white', placeholder_text="DD / MM / AAAA")
        entry_data_saida.place(x=20, y=230)
        entry_data_saida.bind("<KeyRelease>", mascara_data_fim)
        #---------------------------------------------------
        def atualizar_label_tipo_busca(*args):
            texto_label_busca_var.set(f"{tipo_busca_var.get()} procurado:")
        #---------------------------------------------------
        label_tipo_busca = ctk.CTkLabel(frame_coluna1, text="Tipo de Busca", font=("Arial", 12), text_color="black")
        label_tipo_busca.place(x=20, y=280)
        tipo_busca_var = ctk.StringVar(value="Jurisprudencia")
        tipo_busca_var.trace_add("write", atualizar_label_tipo_busca)
        # radio_artigo = ctk.CTkRadioButton(frame_coluna1, text="Artigo", variable=tipo_busca_var, value="Artigo", text_color="black")
        # radio_artigo.place(x=20, y=320)
        # radio_palavra = ctk.CTkRadioButton(frame_coluna1, text="Texto", variable=tipo_busca_var, value="Texto", text_color="black")
        # radio_palavra.place(x=120, y=320)   
        radio_geral = ctk.CTkRadioButton(frame_coluna1, text="Jurisprudencia (Otimizado)", variable=tipo_busca_var, value="Jurisprudencia", text_color="black")
        radio_geral.place(x=20, y=320)
        #---------------------------------------------------
        texto_label_busca_var = ctk.StringVar()
        texto_label_busca_var.set(f"{tipo_busca_var.get()} procurado")
        label_artigo_procurado = ctk.CTkLabel(frame_coluna1, textvariable=texto_label_busca_var, font=("Arial", 12), text_color="black")
        label_artigo_procurado.place(x=20, y=360)
        entry_artigo_procurado = ctk.CTkEntry(frame_coluna1, width=300, height=40, font=('Arial', 12), text_color='white')
        entry_artigo_procurado.insert(0, "Ementa,Ácordão")
        entry_artigo_procurado.place(x=20, y=400)
        #---------------------------------------------------
        botao_configuracoes = ctk.CTkButton(frame_coluna1, text='Configurações',  width=300,height=40, font=('Arial', 12), text_color='white', command=popup_configs)
        botao_configuracoes.place(x=20, y=460)
        #---------------------------------------------------
        botao_efetuar_pesquisa = ctk.CTkButton(frame_coluna1, text='Pesquisar', width=300, height=40, font=('Arial', 12), text_color='white', command=pesquisar)
        botao_efetuar_pesquisa.place(x=20, y=560)
        #---------------------------------------------------
        def start_request(resume=False):
            global request_thread
            with open(arquivo_configs, 'r', encoding='utf-8') as file:
                configs = json.load(file)
                busca_multipla = configs['busca_multipla'] 
                lista_modelos = configs['lista_modelos']
                api_key = configs['api_key']
                modelo_atual = configs['modelo_atual']
            if busca_multipla == 'sim':
                request_thread = threading.Thread(target=request_todos, kwargs={'resume': resume})
            if busca_multipla == 'não':
                tribunal_selecionado = dropdown_tribunais.get()
                print(f"Tribunal selecionado: {tribunal_selecionado}")  
                if tribunal_selecionado == "TODOS":
                    request_thread = threading.Thread(target=request_todos, kwargs={'resume': resume})
            if resume:
                request_thread = threading.Thread(target=request_singular, kwargs={'resume': True})
            else:
                request_thread = threading.Thread(target=request_singular)
            request_thread.start()
        #---------------------------------------------------
        def toggle_pause():
            global is_paused
            is_paused = not is_paused
            if is_paused:
                print("🔴 Pausando requisição...")
                btn_pause.configure(text="Continuar")
                pause_event.set()  # Marca o evento para pausar
            else:
                print("🟢 Continuando requisição...")
                btn_pause.configure(text="Pausar")
                pause_event.clear()  # Libera para continuar
        #---------------------------------------------------
        def resume_from_cache():
            global leitura_anterior
            global method_request
            leitura_anterior = True  # 🔴 Marca que a execução foi retomada pelo cache
            method_request = 'update'
            if os.path.exists(arquivo_cache):
                with open(arquivo_cache, 'r', encoding='utf-8') as f:
                    cache = json.load(f)

                if 'current_page' in cache and 'current_date_index' in cache:
                    data_inicio = datetime.strptime(cache['data_inicio'], "%d/%m/%Y").strftime("%Y-%m-%d")
                    data_fim = datetime.strptime(cache['data_fim'], "%d/%m/%Y").strftime("%Y-%m-%d")
                    current_date_index = cache['current_date_index']
                    page = cache['current_page']
                    tribunal = cache['tribunal']
                    base_url = 'https://comunicaapi.pje.jus.br/api/v1/comunicacao'
                    with open(arquivo_configs, 'r', encoding='utf-8') as file:
                        configs = json.load(file)
                        busca_multipla = configs['busca_multipla']
                        lista_modelos = configs['lista_modelos']
                        api_key = configs['api_key']
                        modelo_atual = configs['modelo_atual']
                    print(' - busca_multipla ==', busca_multipla)   
                    #------------------------------------------------------------------
                    if tribunal == "TODOS":
                        tribunal == ''  
                        current_date_index = 1  
                        
                        def executar(): 
                            resume = True
                            request_thread = threading.Thread(target=request_todos, kwargs={'resume': resume})
                            request_thread.start()
                            # request_todos(resume=True)
                        executar()
                    #------------------------------------------------------------------
                    if busca_multipla == 'não' and tribunal != "TODOS": 
                        params = {
                            "pagina": page,
                            "itensPorPagina": 100,
                            "siglaTribunal": tribunal,
                            "dataDisponibilizacaoInicio": data_inicio,
                            "dataDisponibilizacaoFim": data_fim,
                        }
                        current_date_index = 1
                        resume = True
                        request_thread = threading.Thread(target=request_todos, kwargs={'resume': resume})
                        request_thread.start()
                        # request_singular(resume=True)
                    #------------------------------------------------------------------     
                    if busca_multipla  == 'sim':
                        resume = True   
                        tribunal = cache['tribunal']
                        request_thread = threading.Thread(target=request_tribunal, kwargs={'tribunal': tribunal, 'resume': resume})
                        request_thread.start()
                        # request_todos(resume=True)
                        
                    else:
                        request_singular(resume=True)
                        print(f"🔄 Retomando da página {page}, índice {current_date_index}")
                else:
                    print("❌ Cache inválido, reiniciando do zero...")
                    request_singular(resume=False)
            else:
                print("Nenhum cache encontrado!")
        #---------------------------------------------------
        global btn_pause
        btn_pause = ctk.CTkButton(frame_coluna1, text="Pausar", command=toggle_pause, width=140, height=40, font=('Arial', 12), text_color='white')
        btn_pause.place(x=20, y=610)
        #---------------------------------------------------
        btn_resume = ctk.CTkButton(frame_coluna1, text="Recuperar Ant.", command=return_from_cache, width=140, height=40, font=('Arial', 12), text_color='white')
        btn_resume.place(x=175, y=610)
        #---------------------------------------------------
        def abrir_pasta_relatorios():   
            pasta_script = os.path.dirname(os.path.abspath(__file__))
            pasta_dl = os.path.join(pasta_script, 'downloads')
            pasta_relatorios = os.path.join(pasta_dl, 'pasta_relatorios')   
            if not os.path.exists(pasta_relatorios):
                os.makedirs(pasta_relatorios)
            os.startfile(pasta_relatorios)
        #---------------------------------------------------   
        botao_ver_relatorio = ctk.CTkButton(frame_coluna1, text='Relatórios',  width=300,height=40, font=('Arial', 12), text_color='white', command=abrir_pasta_relatorios)
        botao_ver_relatorio.place(x=20, y=510)
        #---------------------------------------------------
        def ler_status():
            if os.path.exists(arquivo_status):
                with open(arquivo_status, 'r', encoding='utf-8') as file:
                    status_atual_var.set(f"Status atual = {file.read().strip()}")
            else:
                status_atual_var.set("Status atual = Status não encontrado.")
        ler_status()
        #---------------------------------------------------
        label_status_atual = ctk.CTkLabel(frame_coluna1, textvariable=status_atual_var, font=('Arial', 12), text_color='black', bg_color='#D3D3D3', width=300, height=30, corner_radius=5) 
        label_status_atual.place(x=23, y=666)   
        label_pag_atual = ctk.CTkLabel(frame_coluna1, textvariable=pag_atual_var, font=('Arial', 12), text_color='black', bg_color='#D3D3D3', width=300, height=30, corner_radius=5)
        label_pag_atual.place(x=23, y=700)
        global contador_txt_acordao, contador_txt_ementa, contador_doc_ementa, contador_doc_acordao 
        global contador_txt_acordao_var, contador_txt_ementa_var, contador_doc_ementa_var, contador_doc_acordao_var
        
        label_tt_doc_acordao = ctk.CTkLabel(frame_coluna1,  textvariable=contador_doc_acordao_var, font=('Arial', 10), text_color='black', bg_color='#D3D3D3', width=300, height=20, corner_radius=5) 
        label_tt_doc_acordao.place(x=23, y=735)     
            
        label_tt_doc_ementa = ctk.CTkLabel(frame_coluna1, textvariable=contador_doc_ementa_var, font=('Arial', 10), text_color='black', bg_color='#D3D3D3', width=300, height=20, corner_radius=5)
        label_tt_doc_ementa.place(x=23, y=765)
        
        label_tt_txt_ementa = ctk.CTkLabel(frame_coluna1, textvariable=contador_txt_ementa_var, font=('Arial', 10), text_color='black', bg_color='#D3D3D3', width=300, height=20, corner_radius=5)
        label_tt_txt_ementa.place(x=23, y=795)
        
        label_tt_txt_acordao = ctk.CTkLabel(frame_coluna1, textvariable=contador_txt_acordao_var, font=('Arial', 10), text_color='black', bg_color='#D3D3D3', width=300, height=20, corner_radius=5)
        label_tt_txt_acordao.place(x=23, y=825)
    #------------------------------------------------------------------
    def iframe_tabela():
        frame_coluna2 = ctk.CTkFrame(root, width=1180, height=800, fg_color='#D9D9D9')
        frame_coluna2.place(x=365, y=5)
        #---------------------------------------------------
        global tabela_frame
        global canvas
        global colunas
        global largura_celula
        global altura_celula
        
        colunas = ["codigo_categoria", "categoria", "desc_categoria", "desc_jurisprudencia", "data_disponibilizacao", "tribunal", "nome_orgao", 
        "numero_processo", "tipo_documento", "txt_encontrado", "texto"]  
        limitador_ui = 25
        dados = [["", "", "", "", "", "",  "", "","",  "", "",""] for _ in range(limitador_ui)]
        #---------------------------------------------------
        canvas = ctk.CTkCanvas(frame_coluna2, width=1180, height=850, bg="#d9d9d9", bd=0, highlightthickness=0)
        canvas.pack(side=ctk.LEFT, fill=ctk.BOTH, expand=True)
        #---------------------------------------------------
        scrollbar = ctk.CTkScrollbar(frame_coluna2, command=canvas.yview)
        scrollbar.pack(side=ctk.RIGHT, fill=ctk.Y)
        canvas.configure(yscrollcommand=scrollbar.set)
        #---------------------------------------------------
        tabela_frame = ctk.CTkFrame(canvas, fg_color="#d9d9d9", width=1180, height=850)
        canvas.create_window((0, 0), window=tabela_frame, anchor="nw")
        #---------------------------------------------------
        largura_celula = 120  # Largura fixa para cada célula
        altura_celula = 30    # Altura fixa para cada linha
        #---------------------------------------------------
        for idx, coluna in enumerate(colunas): #cabeçalho
            label = ctk.CTkLabel(
            tabela_frame, text=coluna, width=largura_celula, height=altura_celula, 
            anchor="w", fg_color="#1F6AA5", text_color="white"
            )
            label.grid(row=0, column=idx, sticky="nsew", padx=1, pady=1)
        #---------------------------------------------------
        for i, linha in enumerate(dados): # Dados da tabela
            for j, valor in enumerate(linha):
                label = ctk.CTkLabel(
                    tabela_frame, text=valor, width=largura_celula, height=altura_celula, 
                    anchor="w", fg_color="white", text_color="black"
                )
                label.grid(row=i+1, column=j, sticky="nsew", padx=1, pady=1)
        #---------------------------------------------------
        tabela_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        #---------------------------------------------------
        largura_celula = 1180 // len(colunas)  # Largura de cada célula
        altura_celula = 30                     # Altura fixa para cada linha
        #---------------------------------------------------
        for idx, coluna in enumerate(colunas): #cabeçalho
            label = ctk.CTkLabel(
                tabela_frame, text=coluna, width=largura_celula, height=altura_celula, 
                anchor="w", fg_color="#1F6AA5", text_color="white"
            )
            label.grid(row=0, column=idx, sticky="nsew", padx=1, pady=1)
        #---------------------------------------------------
        for i, linha in enumerate(dados): # Dados da tabela
            for j, valor in enumerate(linha):
                label = ctk.CTkLabel(
                    tabela_frame, text=valor, width=largura_celula, height=altura_celula, 
                    anchor="w", fg_color="white", text_color="black"
                )
                label.grid(row=i+1, column=j, sticky="nsew", padx=1, pady=1)
        #---------------------------------------------------
        tabela_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
    #------------------------------------------------------------------
    def center_window(root):
        global login_ok 
        window_width = 1570
        window_height = 860 
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        position_top = int((screen_height - window_height) / 2 - 40)
        position_right = int((screen_width - window_width) / 2)
        root.geometry(f'{window_width}x{window_height}+{position_right}+{position_top}')
    #------------------------------------------------------------------
    def start():
        iframe_esquerda()
        iframe_tabela() 
        center_window(root)
    start()
    #------------------------------------------------------------------
    center_window(root)

    def on_combobox_change(choice):
        # Se a opção selecionada não for "TODOS", redefine para "TODOS"
        if choice != "TODOS":
            dropdown_tribunais.set("TODOS")


    dropdown_tribunais = ctk.CTkComboBox(
        frame_coluna1,
        width=300,
        height=40,
        font=("Arial", 12),
        text_color="white",
        values=lista_tribunais,
        command=on_combobox_change  # Callback para cada mudança de seleção
    )
    dropdown_tribunais.place(x=20, y=50)

    # Define o valor inicial como "TODOS"
    dropdown_tribunais.set("TODOS")
    
    root.mainloop()
#---------------------------------------------------------------------- 
def request_todos(resume=False):        
    global tt_txt_acordao_var, tt_txt_ementa_var, tt_doc_ementa_var, tt_doc_acordao_var, api_atual, api_pinecone
    global indice_atual, lista_modelos_var
    indice_atual = 0
    current_date_index = 1      
    #------------------------------------------------------------------
    global contador_txt_acordao, contador_txt_ementa, contador_doc_ementa, contador_doc_acordao
    contador_txt_acordao = 0
    contador_txt_ementa = 0
    contador_doc_ementa = 0
    contador_doc_acordao = 0
    def limpar_tabela():
        global tabela_frame, canvas, dados_front, dados_para_salvar, colunas 
        dados_front = []
        dados_para_salvar = []  
        colunas = ["codigo_categoria", "categoria", "desc_categoria", "desc_jurisprudencia", "data_disponibilizacao", "tribunal", "nome_orgao", 
        "numero_processo", "num_processo_masc", "tipo_documento", "txt_encontrado", "texto"]
        for widget in tabela_frame.winfo_children():
            if isinstance(widget, ctk.CTkLabel) and widget.cget("text") not in colunas:
                widget.configure(text="")
        tabela_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
    limpar_tabela()
    #------------------------------------------------------------------
    global method_request                 
    print('method_request', method_request) 
    with open(arquivo_configs, 'r', encoding='utf-8') as file:
        configs = json.load(file)
        pasta_downloads = configs['pasta_downloads']
        print(f"Local de saída obtido: {pasta_downloads}")
    tribunal = 'TODOS'
    #------------------------------------------------------------------
    pasta_relatorios = os.path.join(pasta_downloads, 'pasta_relatorios')    
    data = datetime.now().strftime("%Y-%m-%d")
    #------------------------------------------------------------------
    global caminho_geral, caminho_filtrado
    caminho_geral = ''
    caminho_filtrado = ''
    #------------------------------------------------------------------
    estado_atual = "RUNNING"
    is_running = True
    global  is_paused, page, leitura_anterior, dados_front, limiter_buffer, contador_buffer
    lista_datas = []    
    contador_request = 0    
    contador_buffer = 0
    global contador_append, contador_pagina
    contador_append = 0 
    contador_pagina = 0
    dados_front = []
    miss = 0
    lista_datas = []
    # ------------------------------------------------------------------
    print(' - request_singular() iniciada')
    print('----------------------------------------')
    print(f"🔍 leitura_anterior: {leitura_anterior}")  # 🔴 Depuração
    # ------------------------------------------------------------------
    data_inicio = entry_data_entrada.get()
    data_fim = entry_data_saida.get()
    print(' - data_inicio ==', data_inicio)
    print(' - data_fim ==', data_fim)
    # ------------------------------------------------------------------
    if resume:
        try:
            with open(arquivo_cache, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            # ------------------------------------------------------------------
            data_inicio = cache['data_inicio']
            data_fim = cache['data_fim']
            tribunal = cache['tribunal']
            current_date_index = cache['current_date_index']
            page = cache['current_page']
            configs = cache['configs']
            nomenclatura = configs['nomenclatura']
            arquitetura = configs['arquitetura']
            local_saida = configs['pasta_downloads']
            busca_multipla = configs['busca_multipla']
            lista_modelos = configs['lista_modelos']
            api_key = configs['api_key']
            modelo_atual = configs['modelo_atual']
            print(f"✅ Resumindo a partir de {data_inicio} até {data_fim}, página {page}")
            # ------------------------------------------------------------------
            # 🔴 Recriar lista de datas para continuar de onde parou
            def gerar_datas(data_inicio, data_fim):
                data_inicio_dt = datetime.strptime(data_inicio, "%d/%m/%Y")
                data_fim_dt = datetime.strptime(data_fim, "%d/%m/%Y")
                delta = data_fim_dt - data_inicio_dt
                return [(data_inicio_dt + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(delta.days + 1)]
            lista_datas = gerar_datas(data_inicio, data_fim)
            # ------------------------------------------------------------------
        except Exception as e:
            print("❌ Erro ao carregar cache:", e)
            return
    # ------------------------------------------------------------------
    else:
        with open(arquivo_configs, 'r', encoding='utf-8') as file:
            configs = json.load(file)
            nomenclatura = configs['nomenclatura']
            arquitetura = configs['arquitetura']
            local_saida = configs['pasta_downloads']
            busca_multipla = configs['busca_multipla']
            lista_modelos = configs['lista_modelos']
            api_key = configs['api_key']
            modelo_atual = configs['modelo_atual']
        page = 1
        def gerar_datas(data_inicio, data_fim):
            data_inicio_dt = datetime.strptime(data_inicio, "%d/%m/%Y")
            data_fim_dt = datetime.strptime(data_fim, "%d/%m/%Y")
            delta = data_fim_dt - data_inicio_dt
            return [(data_inicio_dt + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(delta.days + 1)]
        lista_datas = gerar_datas(data_inicio, data_fim)
    # ------------------------------------------------------------------
    start_idx = current_date_index if resume else 0
    dados_para_salvar = []    
    dados_front = []
    # ------------------------------------------------------------------
    print('lista_datas', lista_datas)
    # ------------------------------------------------------------------
    for idx in range(start_idx, len(lista_datas)):
        data = lista_datas[idx] 
        data_cache = data
        data_hoje = datetime.now().strftime("%Y-%m-%d")
        # ------------------------------------------------------------------
        print('method_request', method_request) 
        with open(arquivo_configs, 'r', encoding='utf-8') as file:
            configs = json.load(file)
            pasta_downloads = configs['pasta_downloads']    
            data_type = configs['data-type']
            print(f"Local de saída obtido: {pasta_downloads}")
        tribunal = dropdown_tribunais_var.get() 
        data_hoje = datetime.now().strftime("%Y-%m-%d")
        print('data-type ==', data_type)
        if data_type == 'dia-hoje': 
            data = data_hoje
        #------------------------------------------------------------------
        if data_type == 'dia-variavel':
            data = data_cache
        #------------------------------------------------------------------
        pasta_relatorios = os.path.join(pasta_downloads, 'pasta_relatorios')    
        #------------------------------------------------------------------
        nomenclatura = configs['nomenclatura']
        if nomenclatura == 'data_tribunal': 
            nome_arquivo = f"{tribunal}_{data}"
        if nomenclatura == 'tribunal_data':
            nome_arquivo = f"{data}_{tribunal}"
        #------------------------------------------------------------------ 
        if method_request == 'update':
            pasta_relatorios = os.path.join(pasta_downloads, 'pasta_relatorios')    
            import glob
            arquivos_existentes = glob.glob(os.path.join(pasta_relatorios, '*'))
            if arquivos_existentes:
                nome_arquivo = os.path.basename(max(arquivos_existentes, key=os.path.getctime)).replace('.csv', '').replace('.xlsx', '')
            else:
                nome_arquivo = f"{tribunal}_{data}"
        #------------------------------------------------------------------
        caminho_arquivo_csv = os.path.join(pasta_relatorios, f"{nome_arquivo}.csv")
        caminho_arquivo_xlsx = os.path.join(pasta_relatorios, f"{nome_arquivo}.xlsx")
        #------------------------------------------------------------------
        nomenclatura = configs['nomenclatura']
        arquitetura = configs['arquitetura']
        #------------------------------------------------------------------
        print('nomenclatura', nomenclatura)
        print('arquitetura', arquitetura)
        #------------------------------------------------------------------
        if arquitetura == 'csv':
            caminho_arquivo_final = caminho_arquivo_csv
        if arquitetura == 'xlsx':
            caminho_arquivo_final = caminho_arquivo_xlsx
        if method_request == 'new':
            colunas = ["codigo_categoria", "categoria", "desc_categoria", "desc_jurisprudencia", "data_disponibilizacao", "tribunal", "nome_orgao", 
                    "numero_processo", "num_processo_masc", "tipo_documento", "txt_encontrado", "texto", "categoria", "desc_categoria", "desc_jurisprudencia"]
            
            base_path, ext = os.path.splitext(caminho_arquivo_final)
            caminho_geral = f"{base_path}_geral{ext}"
            caminho_filtrado = f"{base_path}_filtrado{ext}"

            i = 1
            while os.path.exists(caminho_geral) or os.path.exists(caminho_filtrado):
                caminho_geral = f"{base_path}_geral_{i}{ext}"
                caminho_filtrado = f"{base_path}_filtrado_{i}{ext}"
                i += 1

            arquivo_last_update = os.path.join(pasta_configs, 'last_update.txt')
            with open(arquivo_last_update, 'w', encoding='utf-8') as file:
                file.write(f"{caminho_geral}\n{caminho_filtrado}")

            if arquitetura == 'csv':
                pd.DataFrame(columns=colunas).astype(str).to_csv(caminho_geral, index=False, sep=";")
                pd.DataFrame(columns=colunas).astype(str).to_csv(caminho_filtrado, index=False, sep=";")
            elif arquitetura == 'xlsx':
                pd.DataFrame(columns=colunas).astype(str).to_excel(caminho_geral, index=False)
                pd.DataFrame(columns=colunas).astype(str).to_excel(caminho_filtrado, index=False)
        #------------------------------------------------------------------
        print('Arquivos criados:')
        print(' -', caminho_geral)
        print(' -', caminho_filtrado)
        #------------------------------------------------------------------
        while True:
            if is_paused and is_running:
                estado_atual = "PAUSED"
                global status_atual_var
                estado_atual = 'Status atual : PAUSADO'
                status_atual_var.set(estado_atual)
                print('-------------------------------------------')
                print(f"⏸️ [{estado_atual}] Execução pausada! Aguardando...")    
                print('------------------------------------------')
            while is_paused and is_running:
                time.sleep(0.5)
            # ------------------------------------------------------------------
            estado_atual = "RUNNING"
            data_print = datetime.strptime(data, "%Y-%m-%d").strftime("%d/%m")
            status_atual = f'Status atual : EFETUANDO SCRAPPING '
            status_atual_var.set(status_atual)
            pag_atual_var.set(f'Página Atual : {page}, Tribunal : {tribunal}, data : {data_print}')
            base_url = 'https://comunicaapi.pje.jus.br/api/v1/comunicacao'
            # ------------------------------------------------------------------
            params = {
                "pagina": page,
                "itensPorPagina": 100,
                "dataDisponibilizacaoInicio": data,
                "dataDisponibilizacaoFim": data,
            }
            # ------------------------------------------------------------------
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = requests.get(base_url, params=params, headers=headers)
            print(f" [33] [{estado_atual}] Request URL: {base_url}?{params}")       
            link_final = f"{base_url}?pagina={page}&itensPorPagina=100&dataDisponibilizacaoInicio={data}&dataDisponibilizacaoFim={data}"
            print(f" [!!] [{estado_atual}] Request URL: {link_final}")
            print(f" [55] lista_datas", lista_datas)    
            print(f" [77] Data_atual =", data)
            #--------------------------------------------------
            if response.status_code == 200:
                try:
                    resultado_atual = response.json()       
                    #------------------------------------------------------------------------   
                    # print(' [👁️] - numero_processo ==', n_processo)
                    # print(' [👁️] - data_disponibilizacao ==', deta_disponibilizacao)
                    print(' - - - - - - - - - - -')
                    pasta_cache = os.path.join(pasta_downloads, 'pasta_cache')
                    if not os.path.exists(pasta_cache):
                        os.makedirs(pasta_cache)
                    #------------------------------------------------------------------------
                    # le todos os csvs da pasta de cache, le a coluna numero_processo e data_disponibilizacao, 
                    # se o numero_processo e data_disponibilizacao estiverem no csv, pula para o proximo caso sim
                    # se não, continua a execução
                    #------------------------------------------------------------------------
                    # lista os arquivos da pasta
                    arquivos_cache = os.listdir(pasta_cache)
                    dados_existem = False
                    for arquivo in arquivos_cache:
                        caminho_arquivo = os.path.join(pasta_cache, arquivo)
                        df = pd.read_csv(caminho_arquivo, sep=";")
                        filtro = (df['numero_processo'] == num_processo) & (df['data_disponibilizacao'] == data_disponibilizacao)
                        if filtro.any():
                            print(' - [99] - [🟥] - Dados já existem no cache')
                            dados_existem = True
                        else:
                            print(' -  [🟩] -  Dados não encontrados')
                    #------------------------------------------------------------------------
                    if dados_existem: 
                        continue  
                    #------------------------------------------------------------------------
                    nome_arquivo = f"{tribunal}_{data}_{page}.json"     
                    pasta_json = os.path.join(local_saida, 'pasta_json')
                    if not os.path.exists(pasta_json):
                        os.makedirs(pasta_json)
                    caminho_arquivo = os.path.join(pasta_json, nome_arquivo)       
                    print('nome_arquivo', nome_arquivo)
                    print('caminho_arquivo', caminho_arquivo)
                    #--------------------------------------------------
                    with open(caminho_arquivo, 'a', encoding='utf-8') as f:
                        json.dump(resultado_atual, f, ensure_ascii=False, indent=4)
                    print(f"✅ [{estado_atual}] Dados salvos em {caminho_arquivo}")
                    #--------------------------------------------------
                    pasta_relatorios = os.path.join(local_saida, 'pasta_relatorios')
                    if not os.path.exists(pasta_relatorios):
                        os.makedirs(pasta_relatorios)
                    #--------------------------------------------------
                    if resultado_atual:
                        print('----------------------------------')
                        print("Argumentos possíveis no JSON:")
                        print('----------------------------------')
                        for key, value in resultado_atual.items():
                            if isinstance(value, list):
                                print(f"- {key} (lista com {len(value)} itens)")
                                if key == "items":  # Se a chave for "items", iterar sobre os itens da lista
                                    if value:  # Verifica se a lista não está vazia
                                        print("  Argumentos dentro de 'items':")
                                        for sub_key in value[0].keys():  # Pega as chaves do primeiro item
                                            print(f"  - {sub_key}")
                            else:
                                print(f"- {key}")
                    #------------------------------------------------------
                    for item in resultado_atual.get("items", []):   
                        print('----------------------------------') 
                        contador_request += 1
                        print(f' - Efetuando busca de dados {contador_request}')
                        tipo_busca = tipo_busca_var.get()  
                        print (' - tipo_busca ==', tipo_busca)
                        #--------------------------------------------------
                        if tipo_busca == 'Jurisprudencia':
                            #start_aqui
                            texto = item.get("texto")
                            if texto is None:
                                continue
                            texto = texto.replace(";", "")
                            tribunal = item.get("siglaTribunal", "")
                            tribunal = tribunal.replace(";", "")
                            #---------------------------------------
                            data_disponibilizacao = item.get("data_disponibilizacao", "") #1
                            tribunal_atual = item.get("siglaTribunal", "") #3
                            nomeOrgao = item.get("nomeOrgao", "") #4
                            num_processo = item.get("numero_processo", "") #5 
                            numeroprocessocommascara = item.get("numeroprocessocommascara", "") #6                       
                            tipo_documento = item.get("tipoDocumento", "") #7
                            texto = item.get("texto", "") #8   
                            texto = texto.replace(";", ".")     
                            global dados_para_salvar_filtrado, dados_para_salvar_geral
                            dados_para_salvar_filtrado = []
                            dados_para_salvar_geral = []
                            global var_save
                            var_save = ''
                            print(' [👁️] - Resultado Atual' )   
                            print(' [👁️] - numero_processo  ==', num_processo)
                            print(' [👁️] - data_disponibilizacao ==', data_disponibilizacao)  
                            print(' [👁️] - Verificando pasta_cache' )   
                            pasta_cache = os.path.join(pasta_script, 'pasta_cache')
                            arquivos = os.listdir(pasta_cache)
                            print(' [👁️] - Arquivos encontrados na pasta_cache')
                            print(arquivos)
                            dados_existem = False
                            for arquivo in arquivos:
                                caminho_arquivo = os.path.join(pasta_cache, arquivo)
                                print(f"Lendo o arquivo: {caminho_arquivo}")
                                df = pd.read_csv(caminho_arquivo, sep=";", encoding="utf-8")
                                filtro = (df['numero_processo'] == num_processo) & (df['data_disponibilizacao'] == data_disponibilizacao)
                                if filtro.any():
                                    print(' [👁️] - [🟥] - Dados já existem no cache')
                                    print(' [👁️] - [🟥] - FIM DA VERIFICAÇÂO')
                                    print(' [👁️] - [🟥] - reiniciando')
                                    dados_existem = True    
                                    time.sleep(1)
                                else:
                                    print(' [👁️] - [🟩] -  Dados não encontrados')
                                    print(' [👁️] - [🟩] -  FIM DA VERIFICAÇÃO')
                                    print(' [👁️] - [🟩] -  seguindo')
                            if dados_existem:
                                continue
                            print(' - - - - - - - - - - -')
                
                            #-----------------------------------------------------------------------------------------
                            def generate_vetor():
                                print('iniciando_geracao_vetor')
                                from sentence_transformers import SentenceTransformer
                                """
                                Lê o CSV, gera embeddings a partir da coluna 'texto' e preserva todas as colunas
                                como metadados. O resultado é salvo como um arquivo JSON na pasta 'buffer_vetorizado'.
                                """
                                pasta_script = os.path.dirname(os.path.abspath(__file__))
                                pasta_buffer = os.path.join(pasta_script, 'pasta_buffer')
                                arquivo_buffer_entrada = os.path.join(pasta_buffer, 'buffer_normalizado.csv')
                                df = pd.read_csv(arquivo_buffer_entrada, sep=";", dtype=str)
                                # Inicializa o modelo para gerar embeddings
                                model = SentenceTransformer("all-MiniLM-L6-v2")
                                print('vetor_gerado')
                                
                                vetor_list = []
                                for idx, row in df.iterrows():
                                    texto = row["texto"]
                                    embedding = model.encode(texto).tolist()  # Converter para lista para ser serializável em JSON
                                    codigo_categoria = row["codigo_categoria"]
                                    # Gera um id único para o vetor
                                    vector_id = f"{codigo_categoria.lower().replace(' ', '-')}-{idx}"
                                    
                                    item = {
                                        "id": vector_id,
                                        "embedding": embedding,
                                        "metadata": row.to_dict()
                                    }
                                    vetor_list.append(item)
                                
                                pasta_buffer_vetorizado = os.path.join(pasta_script, 'buffer_vetorizado')
                                
                                output_path = os.path.join(pasta_buffer_vetorizado, "buffer_vetorizado.json")
                                with open(output_path, "w", encoding="utf-8") as f:
                                    json.dump(vetor_list, f, ensure_ascii=False, indent=4)
                                print(f"Arquivo de vetores gerado e salvo em: {output_path}")
                                save_backup_vetorizado()
                                deploy()
                            #-----------------------------------------------------------------------------------------
                            def save_backup_vetorizado():
                                """
                                Copia o arquivo de vetores (da pasta 'vetor_atual') para a pasta 'backup_vetorizado',
                                acrescentando um timestamp ao nome do arquivo para manter histórico.
                                """
                                pasta_script = os.path.dirname(os.path.abspath(__file__))
                                pasta_backup = os.path.join(pasta_script, 'pasta_backup')   
                                pasta_backup_vetorizado = os.path.join(pasta_backup, 'backup_vetor')
                                
                                pasta_buffer_vetorizado = os.path.join(pasta_script, 'buffer_vetorizado')
                                arquivo_vetor = os.path.join(pasta_buffer_vetorizado, 'buffer_vetorizado.json')
                                source_path = os.path.join(pasta_backup_vetorizado, arquivo_vetor)
                                
                                total_arquivos = len(os.listdir(pasta_backup_vetorizado))
                                i = total_arquivos
                                backup_file = f"vetorizado_backup_{i+1}.json"
                                backup_path = os.path.join(pasta_backup_vetorizado, backup_file)
                                import shutil
                                shutil.copy(source_path, backup_path)
                                print(f"Backup realizado: {backup_path}")
                            #-----------------------------------------------------------------------------------------     
                            def deploy():
                                deploy_final = False
                                while deploy_final == False:
                                    try:
                                        global api_key_master
                                        api_key_master = ""
                                        pasta_buffer_vetorizado = os.path.join(pasta_script, 'buffer_vetorizado')
                                        input_file = "buffer_vetorizado.json"
                                        input_path = os.path.join(pasta_buffer_vetorizado, input_file)
                                        
                                        pasta_configs = os.path.join(pasta_script, 'configurações')
                                        arquivo_configs_json = os.path.join(pasta_configs, 'configs.json')
                                        with open(arquivo_configs_json, 'r', encoding='utf-8') as file:
                                            configs = json.load(file)
                                            api_key_master = configs['api_pinecone']
                                        if not os.path.exists(input_path):
                                            print(f"Arquivo {input_path} não encontrado. Execute 'generate_vetor()' primeiro.")
                                            return
                                        with open(input_path, "r", encoding="utf-8") as f:
                                            vetor_list = json.load(f)
                                        from pinecone import Pinecone, ServerlessSpec
                                        grupos = {}
                                        for item in vetor_list:
                                            codigo_categoria = item["metadata"]["codigo_categoria"]
                                            grupos.setdefault(codigo_categoria, []).append(item)
                                        # Cria a instância do cliente Pinecone
                                        pc = Pinecone(api_key=api_key_master)
                                        # Para cada codigo_categoria, realiza o upsert no índice correspondente
                                        for codigo_categoria, items in grupos.items():
                                            # Define o nome do índice: converte para minúsculas, substitui espaços e underscores por hífens e remove hífens finais
                                            index_name = codigo_categoria.lower().replace(" ", "-").replace("_", "-").rstrip("-")
                                            # Se o nome exceder 45 caracteres, trunca e remove hífens finais
                                            if len(index_name) > 45:
                                                index_name = index_name[:45].rstrip("-")
                                            
                                            # Verifica se o índice já existe; se não, cria-o
                                            if index_name not in pc.list_indexes().names():
                                                dimension = len(items[0]["embedding"])  # Assume que todos os vetores têm a mesma dimensão
                                                spec = ServerlessSpec(cloud='aws', region='us-west-2')
                                                pc.create_index(index_name, dimension=dimension, spec=spec)
                                                print(f"Índice '{index_name}' criado.")
                                            else:
                                                print(f"Índice '{index_name}' já existe.")
                                            
                                            # Conecta ao índice usando o cliente pc
                                            index = pc.Index(index_name)
                                            
                                            # Prepara a lista de vetores para o upsert
                                            upsert_data = []
                                            for item in items:
                                                upsert_data.append((item["id"], item["embedding"], item["metadata"]))
                                            
                                            # Realiza o upsert dos vetores no índice
                                            index.upsert(vectors=upsert_data)
                                            print(f"Deploy concluído para a codigo_categoria '{codigo_categoria}' no índice '{index_name}'.")
                                        # limpa o arquivo de cache buffer_normalizado.csv
                                        pasta_buffer = os.path.join(pasta_script, 'pasta_buffer')
                                        arquivo_buffer_entrada = os.path.join(pasta_buffer, 'buffer_normalizado.csv')
                                        # apagar os dados ,nao é para apagar o arquivo, deverá manter o header 
                                        df = pd.read_csv(arquivo_buffer_entrada, sep=";", encoding="utf-8")
                                        df = df.iloc[0:0]
                                        df.to_csv(arquivo_buffer_entrada, sep=";", index=False)
                                        #-----------------------------------------------------------
                                        # apaga o arquivo buffer vetorizado da pasta buffer_vetorizado
                                        pasta_buffer_vetorizado = os.path.join(pasta_script, 'buffer_vetorizado')
                                        arquivo_buffer_vetorizado = os.path.join(pasta_buffer_vetorizado, 'buffer_vetorizado.json')
                                        os.remove(arquivo_buffer_vetorizado)
                                        deploy_final = True
                                        #-----------------------------------------------------------
                                        print("Deploy finalizado para todos os vetores.")
                                    except Exception as e:
                                        print('Erro ao fazer deploy:', e)
                                        deploy_final = False
                                        time.sleep(30)
                            #-----------------------------------------------------------------------------------------
                            def request_api():
                                global dados_para_salvar_filtrado, dados_para_salvar_geral
                                global desc_jurisprudencia, desc_categoria, categoria_final, texto
                                desc_jurisprudencia = ''
                                desc_categoria = ''
                                categoria_final = ''
                                texto = item.get("texto", "")
                                texto = texto.replace(";", ".")
                                texto = re.sub(r' {2,}', ' ', texto)
                                with open(arquivo_configs, 'r', encoding='utf-8') as file:
                                    configs = json.load(file)
                                    pasta_downloads = configs['pasta_downloads']    
                                    api_key = configs['api_key']
                                    modelo_atual = configs['modelo_atual']
                                #--------------------------------------------------------------------
                                arquivo_prompt_categoria = os.path.join(pasta_configs, 'prompt_categoria.txt')
                                with open(arquivo_prompt_categoria, 'r', encoding='utf-8') as file:
                                    prompt_categoria = file.read()
                                arquivo_prompt_descricao = os.path.join(pasta_configs, 'prompt_descricao.txt')
                                with open(arquivo_prompt_descricao, 'r', encoding='utf-8') as file:
                                    prompt_descricao = file.read()
                                #--------------------------------------------------------------------
                                arquivo_categorias = os.path.join(pasta_configs, 'categorias.csv')
                                df = pd.read_csv(arquivo_categorias, sep=";")
                                df = df.dropna(subset=['indice'])
                                df.to_csv(arquivo_categorias, sep=";", index=False)
                                arquivo_categorias = os.path.join(pasta_configs, 'categorias.csv')  
                                df = pd.read_csv(arquivo_categorias, sep=";")
                                if 'indice' in df.columns and df['indice'].notna().any():
                                    df['indice'] = df['indice'].astype(int)
                                    total_de_categorias_atual = df['indice'].max()
                                #--------------------------------------------------------------------   
                                print(' - [🤖] ')
                                print(' - [IA] - GERANDO DADOS COM IA ')   
                                print(' - [IA] - EFETUANDO NOVA REQUEST ')
                                print(' - [IA] - 1. total_de_categorias_atual ==', total_de_categorias_atual)
                                print(' - [IA] - 2. modelo_atual', modelo_atual)
                                #--------------------------------------------------------------------
                                csv_categorias = os.path.join(pasta_configs, 'categorias.csv')
                                arquivo_categorias = os.path.join(pasta_configs, 'categorias.csv')
                                #------------
                                upload_file = False 
                                while upload_file == False:
                                    try:
                                        upload_url = "https://api.openai.com/v1/files"
                                        upload_headers = {"Authorization": f"Bearer {api_key}"}
                                        upload_data = {"purpose": "assistants"}
                                        with open(csv_categorias, "rb") as f:
                                            upload_files = {"file": f}
                                            upload_response = requests.post(upload_url, headers=upload_headers, data=upload_data, files=upload_files)
                                        upload_result = upload_response.json()
                                        file_id = upload_result.get("id")
                                        if not file_id:
                                            print("Erro ao fazer upload do arquivo:", upload_result)
                                            upload_file = False
                                        if file_id == None:
                                            upload_file = False
                                        else:
                                            print(f" - [IA] - 3. Arquivo enviado com sucesso. ID: {file_id}")
                                            upload_file = True
                                    except Exception as e:
                                        print('Erro ao fazer upload do arquivo:', e)
                                        upload_file = False
                                #-----------------------------------------------------------------------
                                with open(csv_categorias, "r", encoding="utf-8") as f:
                                    lista_categorias = f.read()
                                headers = {
                                    "Authorization": f"Bearer {api_key}",
                                    "Content-Type": "application/json",
                                    "OpenAI-Beta": "assistants=v2"
                                }
                                assistant_id = 'asst_7HnwPIVsEXEtiFNU68ri2TRs'
                                #-----------------------------------------------------------------
                                thread_start = False
                                while thread_start == False:
                                    try:
                                        thread_url = "https://api.openai.com/v1/threads"
                                        thread_response = requests.post(thread_url, headers=headers)
                                        thread_data = thread_response.json()
                                        thread_id = thread_data.get("id")
                                        if not thread_id:
                                            print("Erro ao criar a Thread:", thread_data)
                                            thread_start = False
                                        print(f" - [IA] - 5. Thread criada com sucesso. ID: {thread_id}")   
                                        thread_start = True
                                    except Exception as e:
                                        print('Erro ao criar a Thread:', e)
                                        thread_start = False
                                #---------------------------------------------------------------------
                                message_ok = False
                                while message_ok == False: 
                                    try:
                                        message_url = f"https://api.openai.com/v1/threads/{thread_id}/messages"
                                        #-----------------------------------------------------------------
                                        message_data = {
                                            "role": "user",
                                            "content": f"""{prompt_categoria}
                                        ------------------------------------
                                        Esta é a lista de categorias atuais:
                                        {lista_categorias}
                                        ------------------------------------
                                        Este é o texto a ser analisado:
                                        {texto}
                                        ------------------------------------"""
                                        }
                                        #-----------------------------------------------------------------
                                        message_response = requests.post(message_url, headers=headers, json=message_data)
                                        if message_response.status_code != 200:
                                            print("Erro ao adicionar mensagem à Thread:", message_response.json())
                                            message_ok = False
                                        else:
                                            message_ok = True
                                            print(" - [IA] - 6. Mensagem adicionada ao Thread com sucesso.")
                                    except Exception as e:
                                        print('Erro ao adicionar mensagem à Thread:', e)
                                        message_ok = False
                                #-----------------------------------------------------------------  
                                run_start = False
                                while run_start == False: 
                                    try:
                                        run_url = f"https://api.openai.com/v1/threads/{thread_id}/runs"
                                        run_data = {"assistant_id": assistant_id}
                                        run_response = requests.post(run_url, headers=headers, json=run_data)
                                        run_data = run_response.json()
                                        run_id = run_data.get("id")
                                        if not run_id:
                                            print("Erro ao iniciar o Run:", run_data)   
                                            run_start = False
                                        else:
                                            print(f" - [IA] - 7. Run iniciado. ID: {run_id}")
                                            run_start = True    
                                    except Exception as e:
                                        print('Erro ao iniciar o Run:', e)
                                        run_start = False
                                #-----------------------------------------------------------------  
                                run_ok = False
                                while run_ok == False:
                                    try:
                                        run_status_response = requests.get(f"https://api.openai.com/v1/threads/{thread_id}/runs/{run_id}", headers=headers)
                                        run_status = run_status_response.json().get("status")
                                        if run_status == "completed":
                                            print(" - [IA] - 9. Run concluído com sucesso.")
                                            run_ok = True
                                            print(" - [IA] - 8. Aguardando conclusão do processamento...")
                                        time.sleep(1)   
                                    except Exception as e:
                                        print(' - [IA] - 9. Erro ao verificar status do Run:', e)
                                        run_ok = False
                                #-----------------------------------------------------------------
                                messages_url = f"https://api.openai.com/v1/threads/{thread_id}/messages"
                                messages_response = requests.get(messages_url, headers=headers)
                                messages_data = messages_response.json()
                                #-----------------------------------------------------------------
                                value = None
                                type_release = ''
                                if messages_data.get("data"):  
                                    first_message = messages_data["data"][0]  
                                    if first_message.get("content"): 
                                        first_content = first_message["content"][0] 
                                        if first_content.get("type") == "text": 
                                            value = first_content.get("text", {}).get("value") 
                                #-----------------------------------------------------------------
                                if value:
                                    print(f" - [IA] - 10. [✅] [R]: {value}")
                                #--------------------------------------------------------------------
                                if '[categoria_antiga]' in value:
                                    categoria_final = value.split('[categoria_antiga]')[1].strip()
                                    print(' - [IA] - 11. [✅] - ', categoria_final)
                                    match = re.search(r'\d+', categoria_final)
                                    if match:
                                        categoria_final = match.group(0)
                                    print(categoria_final)  # Isso imprimirá: 16
                                    type_release = 'categoria_antiga'
                                    df = pd.read_csv(csv_categorias, encoding="utf-8", sep=";")
                                    df.columns = df.columns.str.strip()
                                    df['categoria'] = df['categoria'].str.replace('\n', ' ').str.strip()
                                    categoria_final = categoria_final.replace('\n', ' ').strip()
                                    categoria_final = categoria_final.lstrip()
                                    categoria_final = categoria_final.rstrip()  
                                    categoria_final = categoria_final.replace(";",".")
                                    categoria_final = int(categoria_final)
                                    with open (arquivo_categorias, 'r', encoding='utf-8') as file:
                                        df = pd.read_csv(arquivo_categorias, sep=";")
                                        desc_categoria = df.loc[df['indice'] == categoria_final, 'desc_categoria'].values[0]
                                        desc_categoria = desc_categoria.replace(";",".")
                                        print(' - [IA] - 12. [✅] - desc_categoria', desc_categoria)
                                #--------------------------------------------------------------------
                                if '[categoria_nova]' in value:
                                    categoria_final = value.split('[categoria_nova]')[1].strip()
                                    categoria_final = categoria_final.replace(";",".")
                                    categoria_final = categoria_final.replace('\n', ' ').strip()
                                    categoria_final = categoria_final.replace('"', '')  
                                    categoria_final = categoria_final.lstrip()
                                    categoria_final = categoria_final.rstrip()
                                    categoria_final = value.split('[categoria_nova]')[1].split('[descricao_categoria]')[0].strip()
                                    categoria_final = categoria_final.replace(";", ".")
                                    categoria_final = categoria_final.replace('\n', ' ')
                                    categoria_final = categoria_final.replace('"', '')
                                    categoria_final = categoria_final.strip()

                                    print(' - ')
                                    print(' - [IA] - 11. [✅] - categoria_nova', categoria_final) 
                                    type_release = 'categoria_nova'  
                                    
                                    #le o arquivo categorias.csv e printa quantas linhas existem (excluindo o header)
                                    df = pd.read_csv(csv_categorias, sep=";")
                                    total_de_categorias_atual = len(df)
                                    print(' - [IA] - 12. Total de categorias atual ==', total_de_categorias_atual)
                                    
                                    
                                    
                                    #-------------------------------
                                    # novo_codigo_gen
                                    #-----------------------------------
                                    from unidecode import unidecode
                                    pasta_script = os.path.dirname(os.path.abspath(__file__))
                                    pasta_config = os.path.join(pasta_script, "configurações")
                                    csv_categorias = os.path.join(pasta_config, "categorias.csv")

                                    def abreviar_categoria(indice, categoria, target=40):
                                        """
                                        Gera uma abreviação legível de tamanho fixo (target) para a string da categoria.
                                        O código terá o formato: NN-<abreviação>, onde NN é o índice com 2 dígitos.
                                        A abreviação é formada com as letras dos termos significativos (removendo palavras comuns)
                                        distribuídas de forma round‑robin para preencher exatamente os caracteres disponíveis.
                                        """
                                        categoria_ascii = unidecode(categoria)
                                        stopwords = {"de", "da", "do", "em", "e", "a", "o", "para", "por"}
                                        palavras = [pal for pal in categoria_ascii.split() if pal.lower() not in stopwords]
                                        prefixo = f"{int(indice):02d}-"
                                        disponivel = target - len(prefixo)
                                        n = len(palavras) if palavras else 1
                                        disponivel_letras = disponivel - (n - 1)
                                        partes = ["" for _ in range(n)]
                                        ponteiros = [0] * n  
                                        letras_adicionadas = 0
                                        while letras_adicionadas < disponivel_letras:
                                            progresso = False
                                            for i, pal in enumerate(palavras):
                                                if ponteiros[i] < len(pal):
                                                    partes[i] += pal[ponteiros[i]]
                                                    ponteiros[i] += 1
                                                    letras_adicionadas += 1
                                                    progresso = True
                                                    if letras_adicionadas >= disponivel_letras:
                                                        break
                                            if not progresso:
                                                break
                                        abrev = "-".join(partes)
                                        codigo = prefixo + abrev
                                        if len(codigo) < target:
                                            codigo += "-" * (target - len(codigo))
                                        else:
                                            codigo = codigo[:target]
                                        return codigo
                                    df = pd.read_csv(csv_categorias, sep=";")
                                    total_de_categorias_atual = len(df)
                                    print(' - [IA] - 12. Total de categorias atual ==', total_de_categorias_atual)
                                    novo_indice = total_de_categorias_atual + 1
                                    codigo_categoria = abreviar_categoria(novo_indice, categoria_final, target=40)
                                    print(f" - [IA] - {novo_indice}. [✅] - categoria_nova", codigo_categoria)
                                    #-------------------------------------------------------------------- 
                                    if '[descricao_categoria]' in value:
                                        print(' - ')
                                        desc_categoria = value.split('[descricao_categoria]')[1].strip()
                                        desc_categoria = desc_categoria.replace(";",".")    
                                        desc_categoria = desc_categoria.replace('\n', ' ').strip()
                                        desc_categoria = desc_categoria.replace("[descricao_categoria]", "")
                                        desc_categoria = desc_categoria.replace("[descriçao_categoria]", "")
                                        desc_categoria = desc_categoria.replace("[descrição_categoria]", "")
                                        desc_categoria = desc_categoria.replace("[descricão_categoria]", "")
                                        desc_categoria = desc_categoria.lstrip()
                                        desc_categoria = desc_categoria.rstrip()
                                        desc_categoria = desc_categoria.replace("[Descricao_Categoria]", "")
                                        desc_categoria = desc_categoria.replace("[DESCRICAO_CATEGORIA]", "")
                                        desc_categoria = desc_categoria.replace("[Descricao_categoria]", "")
                                        desc_categoria = desc_categoria.replace("descricao_categoria", "")
                                        desc_categoria = desc_categoria.replace("descricao da categoria", "")
                                        desc_categoria = desc_categoria.replace("descrição da categoria", "")
                                        desc_categoria = desc_categoria.replace("Descrição da categoria", "")   
                                        desc_categoria = desc_categoria.replace("[descricao_categoria]", "")  
                                        desc_categoria = desc_categoria.replace("[categoria_antiga]", "")
                                        desc_categoria = desc_categoria.replace("[Categoria_antiga]", "")
                                        desc_categoria = desc_categoria.replace("[Categoria_Antiga]", "")
                                        desc_categoria = desc_categoria.replace("[CATEGORIA_ANTIGA]", "")
                                        desc_categoria = desc_categoria.replace("[categoria_nova]", "") 
                                        desc_categoria = desc_categoria.replace("[Categoria_nova]", "") 
                                        desc_categoria = desc_categoria.replace("[Categoria_Nova]", "")     
                                        desc_categoria = desc_categoria.replace("[CATEGORIA_NOVA]", "")
                                        print(' - [IA] - 12. [✅] - descricao_categoria', desc_categoria)   
                                        #--------------------------------------
                                        df = pd.read_csv(csv_categorias, sep=";")
                                        if 'indice' in df.columns and df['indice'].notna().any():
                                            df['indice'] = df['indice'].astype(int)
                                            novo_indice = df['indice'].max() + 1
                                        else:
                                            # breakpoint()
                                            novo_indice = 1  
                                    #-------------------------------------- 
                                        nova_linha = pd.DataFrame({
                                            'indice': novo_indice,
                                            'categoria': categoria_final,
                                            'desc_categoria': desc_categoria,
                                            'codigo_categoria': codigo_categoria
                                        }, index=[0])
                                        df = pd.concat([df, nova_linha], ignore_index=True)
                                        df.to_csv(arquivo_categorias, sep=";", index=False, encoding='utf-8')
                                        print(f' - [IA] - 13. ✅ Categoria "{categoria_final}" adicionada com sucesso!')
                                else:
                                    print(" - [IA] - 13. 🚫 Nenhuma nova categoria válida encontrada.")
                                df = pd.read_csv(arquivo_categorias, sep=";")
                                total_de_categorias_atual = len(df)
                                print(' - [IA] - 14. Total de categorias atual ==', total_de_categorias_atual)
                                #-------------------------------------------------------------------- 
                                df = pd.read_csv(arquivo_categorias, sep=";")
                                df = df.dropna(subset=['indice'])
                                df.to_csv(arquivo_categorias, sep=";", index=False)
                                #-----------------------------------------------------------------------------
                                #  REQUEST PARA GERAR O TEXTO DE DESCIRÇÃO SOBRE A JURISPRUDENCIA.
                                #--------------------------------------------------------------------
                                headers = {
                                    "Authorization": f"Bearer {api_key}",
                                    "Content-Type": "application/json",
                                    "OpenAI-Beta": "assistants=v2"
                                }
                                assistant_id = 'asst_lrXcTebu7kYq6uKihyfnBmjG'
                                #-----------------------------------------------------------------
                                def start_tread():
                                    thread_start2 = False
                                    while thread_start2 == False:
                                        try:
                                            thread_url = "https://api.openai.com/v1/threads"
                                            thread_response = requests.post(thread_url, headers=headers)
                                            thread_data = thread_response.json()
                                            thread_id = thread_data.get("id")
                                            if not thread_id:
                                                print("Erro ao criar a Thread:", thread_data)
                                            print(f" - [IA] - 15. Thread criada com sucesso. ID: {thread_id}")   
                                            thread_start2 = True
                                        except Exception as e:
                                            print('Erro ao criar a Thread:', e)
                                            thread_start2 = False
                                            time.sleep(1)
                                start_tread()
                                #---------------------------------------------------------------------
                                message_ok2 = False  
                                arquivo_descricao = os.path.join(pasta_configs, 'prompt_descricao.txt')
                                with open(arquivo_descricao, 'r', encoding='utf-8') as file:
                                    prompt_descricao = file.read()
                                while message_ok2 == False: 
                                    try: 
                                        message_url = f"https://api.openai.com/v1/threads/{thread_id}/messages"
                                        #-----------------------------------------------------------------
                                        message_data = {
                                            "role": "user",
                                            "content": f"""
                                                prompt = {prompt_descricao}
                                                ------------------------------------
                                                Esse é o texto à ser analisado = {texto}
                                                ------------------------------------
                                                Responda exatamente como solicitado, trazendo uma descrição sobre a jurisprudência.
                                                """
                                        }
                                        #-----------------------------------------------------------------
                                        message_response = requests.post(message_url, headers=headers, json=message_data)
                                        if message_response.status_code != 200:
                                            print("Erro ao adicionar mensagem à Thread:", message_response.json())
                                            message_ok2 = False
                                        else:
                                            message_ok2 = True
                                            print(" - [IA] - 16. Mensagem adicionada ao Thread com sucesso.")
                                    except Exception as e:
                                        print('Erro ao adicionar mensagem à Thread:', e)
                                        message_ok2 = False
                                #-----------------------------------------------------------------  
                                run_start2 = False
                                while run_start2 == False: 
                                    try:
                                        run_url = f"https://api.openai.com/v1/threads/{thread_id}/runs"
                                        run_data = {"assistant_id": assistant_id}
                                        run_response = requests.post(run_url, headers=headers, json=run_data)
                                        run_data = run_response.json()
                                        run_id = run_data.get("id")
                                        if not run_id:
                                            print("Erro ao iniciar o Run:", run_data)
                                            run_start2 = False
                                        else:
                                            print(f" - [IA] - 17. Run iniciado. ID: {run_id}")
                                            run_start2 = True
                                    except Exception as e:
                                        print('Erro ao iniciar o Run:', e)
                                        run_start2 = False
                                #-----------------------------------------------------------------  
                                run_ok2 = False
                                while run_ok2 == False:
                                    try:
                                        run_status_response = requests.get(f"https://api.openai.com/v1/threads/{thread_id}/runs/{run_id}", headers=headers)
                                        run_status = run_status_response.json().get("status")
                                        if run_status == "completed":
                                            print(" - [IA] - 19. Run concluído com sucesso.")
                                            run_ok2 = True
                                        elif run_status in ["failed", "cancelled"]:
                                            print(" - [IA] - 19. Erro: O Run falhou ou foi cancelado.")
                                            run_ok2 = False
                                        print(" - [IA] - 18. Aguardando conclusão do processamento...")
                                        time.sleep(1)
                                    except Exception as e:
                                        print(' - [IA] - 19. Erro ao verificar status do Run:', e)
                                        run_ok2 = False
                                #-----------------------------------------------------------------
                                messages_url = f"https://api.openai.com/v1/threads/{thread_id}/messages"
                                messages_response = requests.get(messages_url, headers=headers)
                                messages_data = messages_response.json()
                                #-----------------------------------------------------------------
                                if messages_data.get("data"):  
                                    first_message = messages_data["data"][0]  
                                    if first_message.get("content"): 
                                        first_content = first_message["content"][0] 
                                        if first_content.get("type") == "text": 
                                            desc_jurisprudencia = first_content.get("text", {}).get("value") 
                                #-----------------------------------------------------------------
                                if desc_jurisprudencia:
                                    print(f" - [IA] - 20. [✅] [R]: {desc_jurisprudencia }")
                                desc_jurisprudencia = desc_jurisprudencia.replace('\n', ' ').strip()
                                desc_jurisprudencia = desc_jurisprudencia.replace("[descricao_jurisprudencia]", "")
                                desc_jurisprudencia = desc_jurisprudencia.replace("[DESCRICAO_JURISPRUDENCIA]", "")
                                desc_jurisprudencia = desc_jurisprudencia.replace("[Descricao_Jurisprudencia]", "")
                                desc_jurisprudencia = desc_jurisprudencia.replace("descricao_jurisprudencia", "")
                                desc_jurisprudencia = desc_jurisprudencia.replace("descricao da jurisprudencia", "")
                                desc_jurisprudencia = desc_jurisprudencia.replace("descrição da jurisprudencia", "")
                                desc_jurisprudencia = desc_jurisprudencia.replace("Descrição da jurisprudencia", "")
                                #--------------------------------------------------------------------
                                print( ' - [SAVE] - ')
                                #--------------------------------------------------------------------
                                if type_release == 'categoria_antiga':
                                    df = pd.read_csv(csv_categorias, encoding="utf-8", sep=";")
                                    df.columns = df.columns.str.strip()
                                    df['categoria'] = df['categoria'].str.replace('\n', ' ').str.strip()
                                    cat_int = int(categoria_final)
                                    with open (arquivo_categorias, 'r', encoding='utf-8') as file:
                                        df = pd.read_csv(arquivo_categorias, sep=";")
                                        desc_categoria = df.loc[df['indice'] == cat_int, 'desc_categoria'].values[0]
                                        categoria_final = df.loc[df['indice'] == cat_int, 'categoria'].values[0]
                                        codigo_categoria = df.loc[df['indice'] == cat_int, 'codigo_categoria'].values[0]
                                #--------------------------------------------------------------------
                                if var_save == 'filtrado':
                                    # limita o texto a 30.000 caracteres
                                    texto = texto[:35000]
                                    if palavra_encontrada == '':
                                        if tipo_documento == 'acordao':
                                            txt_encontrado = 'acordao'
                                        if tipo_documento == 'ementa':
                                            txt_encontrado = 'ementa'
                                    dados_para_salvar_filtrado.append({
                                        "codigo_categoria": codigo_categoria.replace('"', '').replace("\n", "").replace(";", ""),
                                        "categoria": categoria_final.replace('"', '').replace("\n", "").replace(";", ""),
                                        "desc_categoria": desc_categoria.replace('"', '').replace("\n", "").replace(";", ""),
                                        "desc_jurisprudencia": desc_jurisprudencia.replace('"', '').replace("\n", "").replace(";", ""),
                                        "data_disponibilizacao": data_disponibilizacao.replace('"', '').replace("\n", "").replace(";", ""),
                                        "tribunal": tribunal_atual.replace('"', '').replace("\n", "").replace(";", ""),
                                        "nome_orgao": nomeOrgao.replace('"', '').replace("\n", "").replace(";", ""),
                                        "numero_processo": num_processo.replace('"', '').replace("\n", "").replace(";", ""),
                                        "tipo_documento": tipo_documento_final.replace('"', '').replace("\n", "").replace(";", ""),
                                        "txt_encontrado": palavra_encontrada.replace('"', '').replace("\n", "").replace(";", ""),
                                        "texto": texto.replace('"', '').replace("\n", "").replace(";", "")
                                    })
                                    print(' - [IA] - 21. [✅] Dados salvos em dados_para_salvar_filtrado')
                                if var_save == 'geral': 
                                    codigo_categoria = 'gnp'
                                    categoria_final = 'gnp'
                                    desc_categoria = 'gnp'
                                    desc_jurisprudencia = 'gnp'
                                    dados_para_salvar_geral.append({
                                        "codigo_categoria": codigo_categoria,
                                        "categoria": categoria_final,
                                        "desc_categoria": desc_categoria,
                                        "desc_jurisprudencia": desc_jurisprudencia,
                                        "data_disponibilizacao": data_disponibilizacao.replace(";", ""),
                                        "tribunal": tribunal_atual.replace('"', '').replace("\n", "").replace(";", ""),
                                        "nome_orgao": nomeOrgao.replace('"', '').replace("\n", "").replace(";", ""),
                                        "numero_processo": num_processo.replace('"', '').replace("\n", "").replace(";", ""),
                                        "num_processo_masc": numeroprocessocommascara.replace('"', '').replace("\n", "").replace(";", ""),
                                        "tipo_documento": tipo_documento_final.replace('"', '').replace("\n", "").replace(";", ""),
                                        "txt_encontrado": palavra_encontrada.replace('"', '').replace("\n", "").replace(";", ""),
                                        "texto": texto.replace('"', '').replace("\n", "").replace(";", "")
                                    })
                            ##########################################################################################
                            def save_processo_extraido():
                                global dados_para_salvar_filtrado, dados_para_salvar_geral
                                print('salvando processo extraido')
                                pasta_cache = os.path.join(pasta_script, 'pasta_cache')
                                #-------------------------------------------------------------------------------------
                                pasta_ia_settings = os.path.join(pasta_script, 'ia_settings')       
                                json_ia_settings = os.path.join(pasta_ia_settings, 'ia_settings.json')
                                with open(json_ia_settings, 'r', encoding='utf-8') as f:
                                    ia_settings = json.load(f)
                                batchsize_cache_processos = ia_settings["batchsize_cache_processos"]
                                print(batchsize_cache_processos)
                                #-------------------------------------------------------------------------------------
                                print(' [C] - Salvando cache na pasta =' , pasta_cache) 
                                if not os.path.exists(pasta_cache):
                                    os.makedirs(pasta_cache)
                                num_arquivos = len(os.listdir(pasta_cache))
                                print(f" [C] - A pasta contém {num_arquivos} arquivos antes da operação.")
                                #--------------------------------------------------------------------------------------
                                arquivo_cache = os.path.join(pasta_cache, f'lista_extraidos_1.csv')
                                if not os.path.exists(arquivo_cache):
                                    df = pd.DataFrame(
                                        [["sample", "sample", "sample", "sample"]],
                                        columns=["data_disponibilizacao", "numero_processo", "tribunal", "tipo_extracao"]
                                    )
                                    with open(arquivo_cache, 'w', encoding='utf-8') as f:
                                        df.to_csv(f, index=False, sep=";")
                                    print(' [C] - CACHE INICIAL GERADO')
                                #--------------------------------------------------------------------------------------
                                arquivos = [os.path.join(pasta_cache, f) for f in os.listdir(pasta_cache) if os.path.isfile(os.path.join(pasta_cache, f))]
                                if arquivos:
                                    arquivo_mais_recente = max(arquivos, key=os.path.getmtime)
                                    print(f" [C] - Arquivo mais recente: {arquivo_mais_recente}")
                                    df = pd.read_csv(arquivo_mais_recente,  sep=";")
                                    #-------------------------------------------------------------------
                                    # CHECK BATCH SIZE PARA SALVAR CACHE
                                    num_linhas = len(df)
                                    if num_linhas >= batchsize_cache_processos:
                                        print(" [C] - Salvando cache em novo arquivo.")
                                        novo_arquivo = os.path.join(pasta_cache, f"lista_extraidos_{num_arquivos+1}.csv")
                                        df = pd.DataFrame({
                                            "data_disponibilizacao": [data_disponibilizacao],
                                            "numero_processo": [num_processo],
                                            "tribunal": [tribunal_atual],
                                            "tipo_extracao": var_save
                                        })
                                        columns = ["data_disponibilizacao", "numero_processo", "tribunal", "tipo_extracao"]
                                        header_value = not os.path.exists(novo_arquivo)
                                        df.to_csv(novo_arquivo, mode='a', header=header_value, index=False, sep=";", columns=columns)
                                        print(f" [C] - Cache salvo em {novo_arquivo}")
                                    #----------------------------------------------------------------------
                                    # SALVA OS DADOS NO ARQUIVO EXISTENTE
                                    arquivo_mais_recente = max(arquivos, key=os.path.getmtime)
                                    df = pd.DataFrame({
                                        "data_disponibilizacao": [data_disponibilizacao],
                                        "numero_processo": [num_processo],
                                        "tribunal": [tribunal_atual],
                                        "tipo_extracao": var_save
                                    })
                                    columns = ["data_disponibilizacao", "numero_processo", "tribunal", "tipo_extracao"]
                                    df.to_csv(arquivo_mais_recente, mode='a', header=False, index=False, sep=";", columns=columns)
                                    #----------------------------------------------------------------------
                                else:
                                    print(" [C] - Nenhum arquivo encontrado na pasta.")
                                #------------------------------------------------------------------------------------
                                def clean_cache_files():
                                    pasta_cache = os.path.join(pasta_script, 'pasta_cache')
                                    for arquivo in os.listdir(pasta_cache):
                                        caminho_arquivo = os.path.join(pasta_cache, arquivo)
                                        if os.path.isfile(caminho_arquivo):
                                            df = pd.read_csv(caminho_arquivo, sep=";")
                                            df = df.dropna(how='all')  # Remove linhas completamente vazias
                                            df = df[~df.apply(lambda row: row.astype(str).str.contains('sample').any(), axis=1)]  # Remove linhas com 'sample'
                                            df.to_csv(caminho_arquivo, sep=";", index=False)
                                clean_cache_files()
                            #-----------------------------------------------------------------------------------------
                            def save_backup_geral():
                                print('iniciando_salvamento_back_geral')
                                global dados_para_salvar_filtrado, dados_para_salvar_geral
                                global categoria_final, desc_categoria, desc_jurisprudencia, dados_para_salvar_geral
                                # print(dados_para_salvar_geral)
                                # breakpoint()
                                pasta_backup = os.path.join(pasta_script, 'pasta_backup') 
                                print(' - [BACK_GERAL] - iniciando_salvamento_backup')
                                print(' - [BACK_GERAL] - pasta_backup ==', pasta_backup)
                                pasta_normalizada = os.path.join(pasta_backup, 'backup_normalizado')
                                pasta_backup_geral = os.path.join(pasta_normalizada, 'backup_geral')
                                #----------------------------------------------------------------
                                pasta_ia_settings = os.path.join(pasta_script, 'ia_settings')       
                                json_ia_settings = os.path.join(pasta_ia_settings, 'ia_settings.json')
                                with open(json_ia_settings, 'r', encoding='utf-8') as f:
                                    ia_settings = json.load(f)
                                batchsize_backupcsv_geral_normalizado = ia_settings["batchsize_backupcsv_geral_normalizado"]
                                print(batchsize_backupcsv_geral_normalizado)
                                #-----------------------------------------------------------------  
                                print(' [BACK_GERAL] - Salvando backup na pasta =' , pasta_backup_geral)     
                                if not os.path.exists(pasta_backup_geral):
                                    os.makedirs(pasta_backup_geral)
                                num_arquivos = len(os.listdir(pasta_backup_geral))
                                print(f" [BACK_GERAL] - A pasta contém {num_arquivos} arquivos antes da operação.") 
                                arquivo_backup_1 = os.path.join(pasta_backup_geral, 'backup_geral_1.csv')
                                if not os.path.exists(arquivo_backup_1):
                                    df = pd.DataFrame(
                                        [[ "sample", "sample", "sample", "sample", "sample", "sample", "sample", "sample", "sample", "sample", "sample"]],
                                        columns=["codigo_categoria", "categoria", "desc_categoria", "desc_jurisprudencia", "data_disponibilizacao", 
                                                "tribunal", "nome_orgao", "numero_processo",
                                                "tipo_documento", "txt_encontrado", "texto"]
                                    )
                                    df.to_csv(arquivo_backup_1, index=False, sep=";")
                                    print(' [BACK_GERAL] - backup_geral_1 GERADO com linha sample.')
                                else:
                                    print(' [BACK_GERAL] - O arquivo backup_geral_1 já existe.')
                                #-----------------------------------------------------------------  
                                arquivos = [os.path.join(pasta_backup_geral, f) for f in os.listdir(pasta_backup_geral) if os.path.isfile(os.path.join(pasta_backup_geral, f))]
                                if arquivos:
                                    arquivo_mais_recente = max(arquivos, key=os.path.getmtime)
                                    print(f" [BACK_GERAL] - Arquivo mais recente: {arquivo_mais_recente}")
                                    print(' [BACK] -D1 ')
                                    df = pd.read_csv(arquivo_mais_recente, sep=";")
                                    if df.columns[0] != "categoria":
                                        print(' [BACK] -D2 ')
                                        df.columns = ["codigo_categoria", "categoria", "desc_categoria", "desc_jurisprudencia", "data_disponibilizacao", "tribunal", "nome_orgao", "numero_processo","tipo_documento", "txt_encontrado", "texto"]
                                        df.to_csv(arquivo_mais_recente, index=False, sep=";")
                                        print(' [BACK] -D3 ')
                                    df = pd.read_csv(arquivo_mais_recente, sep=";")
                                    print(' [BACK] -D4 ')
                                    df = pd.DataFrame(dados_para_salvar_geral)
                                    df.to_csv(arquivo_mais_recente, mode='a', header=False, index=False, sep=";")
                                    #----------------------------sss---------------------------------------
                                    # CHECK BATCH SIZE PARA SALVAR CACHE
                                    df = pd.read_csv(arquivo_mais_recente, sep=";")
                                    df = df.drop_duplicates()
                                    num_linhas = len(df)
                                    print(' - [D5]')
                                    print(' - [D5]', num_linhas)
                                    df.to_csv(arquivo_mais_recente, index=False, sep=";")
                                    if num_linhas >= batchsize_backupcsv_geral_normalizado:
                                        print(" [BACK_GERAL] -----------------------------------------------")
                                        print(" [BACK_GERAL] - NUMERO de linhas atingiu o limite. Salvando em novo arquivo.")
                                        print(" [BACK_GERAL] - Salvando backup em novo arquivo.")
                                        novo_arquivo = os.path.join(pasta_backup_geral, f"backup_geral_{num_arquivos+1}.csv")
                                        df.to_csv(novo_arquivo, index=False, sep=";")
                                        print(f" [BACK_GERAL] - Backup salvo em {novo_arquivo}")
                                    #----------------------------------------------------------------------
                                    # SALVA OS DADOS NO ARQUIVO MAIS RECENTE
                                    arquivo_mais_recente = max(arquivos, key=os.path.getmtime)
                                    print(' [BACK] -D5 ')
                                    df = pd.DataFrame(dados_para_salvar_geral)
                                    print(' [BACK] -D6 ')
                                    df.to_csv(arquivo_mais_recente, mode='a', header=False, index=False, sep =";")
                                    #----------------------------------------------------------------------

                                else:
                                    print(" [BACK_GERAL] - Nenhum arquivo encontrado na pasta.")
                                #------------------------------------------------------------------------------------
                                # BASEADO NA NOMENCLATURA 
                            #-----------------------------------------------------------------------------------------
                            def save_backup_filtrado():
                                print('iniciando_salvamento_back_filtrado')
                                global dados_para_salvar_filtrado, dados_para_salvar_geral
                                global categoria_final, desc_categoria, desc_jurisprudencia
                                pasta_backup = os.path.join(pasta_script, 'pasta_backup') 
                                print(' - [BACK_FILTRADO] - iniciando_salvamento_backup')
                                print(' - [BACK_FILTRADO] - pasta_backup ==', pasta_backup)
                                pasta_normalizada = os.path.join(pasta_backup, 'backup_normalizado')
                                pasta_backup_filtrado = os.path.join(pasta_normalizada, 'backup_filtrado')
                                #----------------------------------------------------------------
                                pasta_ia_settings = os.path.join(pasta_script, 'ia_settings')       
                                json_ia_settings = os.path.join(pasta_ia_settings, 'ia_settings.json')
                                with open(json_ia_settings, 'r', encoding='utf-8') as f:
                                    ia_settings = json.load(f)
                                batchsize_backupcsv_filtrado_normalizado = ia_settings["batchsize_backupcsv_filtrado_normalizado"]
                                print(batchsize_backupcsv_filtrado_normalizado)
                                #-----------------------------------------------------------------
                                print(' [BACK_FILTRADO] - Salvando backup na pasta =' , pasta_backup_filtrado)
                                if not os.path.exists(pasta_backup_filtrado):
                                    os.makedirs(pasta_backup_filtrado)
                                num_arquivos = len(os.listdir(pasta_backup_filtrado))
                                print(f" [BACK_FILTRADO] - A pasta contém {num_arquivos} arquivos antes da operação.")
                                arquivo_filtrado_1 = os.path.join(pasta_backup_filtrado, f'backup_filtrado_1.csv')
                                if not os.path.exists(arquivo_filtrado_1):
                                    df = pd.DataFrame(
                                        [["sample", "sample", "sample", "sample", "sample", "sample", "sample", "sample", "sample", "sample", "sample"]],
                                        columns = ["codigo_categoria", "categoria", "desc_categoria", "desc_jurisprudencia", "data_disponibilizacao", "tribunal", "nome_orgao", 
                                        "numero_processo",  "tipo_documento", "txt_encontrado", "texto"]
                                    )
                                    with open(arquivo_filtrado_1, 'w', encoding='utf-8') as f:
                                        df.to_csv(f, index=False, sep=";")
                                    print(' [BACK_FILTRADO] - backup_filtrado_1 GERADO')
                                #-----------------------------------------------------------------
                                arquivos_filtrados = [os.path.join(pasta_backup_filtrado, f) for f in os.listdir(pasta_backup_filtrado) if os.path.isfile(os.path.join(pasta_backup_filtrado, f))]
                                if arquivos_filtrados:
                                    arquivo_mais_recente_filtrado = max(arquivos_filtrados, key=os.path.getmtime)
                                    print(f" [BACK_FILTRADO] - Arquivo mais recente: {arquivo_mais_recente_filtrado}")
                                    df = pd.read_csv(arquivo_mais_recente_filtrado, sep =";")
                                    df = df.drop_duplicates()
                                    df.to_csv(arquivo_mais_recente_filtrado, index=False, sep=";")
                                    df = pd.read_csv(arquivo_mais_recente_filtrado, sep=";")
                                    #-------------------------------------------------------------------
                                    # CHECK BATCH SIZE PARA SALVAR CACHE
                                    num_linhas = len(df)
                                    if num_linhas >= batchsize_backupcsv_filtrado_normalizado:
                                        print(" [BACK_FILTRADO] - Salvando backup em novo arquivo.")
                                        novo_arquivo = os.path.join(pasta_backup_filtrado, f"backup_filtrado_{num_arquivos+1}.csv")
                                        df.to_csv(novo_arquivo, index=False, sep=";")
                                        print(f" [BACK_FILTRADO] - Backup salvo em {novo_arquivo}")
                                    #----------------------------------------------------------------------
                                    # SALVA OS DADOS NO ARQUIVO MAIS RECENTE
                                    arquivo_mais_recente_filtrado = max(arquivos_filtrados, key=os.path.getmtime)
                                    df = pd.DataFrame(dados_para_salvar_filtrado)
                                    df.to_csv(arquivo_mais_recente_filtrado, mode='a', header=False, index=False, sep =";")
                                    #----------------------------------------------------------------------
                                    # verifica se existe linhas com conteudo sample, se sim remove, apaga linhas onde todo conteudo está vazio
                                    df = pd.read_csv(arquivo_mais_recente_filtrado, sep=";")
                                    df = df.dropna(how='all')  # Remove linhas completamente vazias
                                    df = df[~df.apply(lambda row: row.astype(str).str.contains('sample').any(), axis=1)]  # Remove linhas com 'sample'
                                    df.to_csv(arquivo_mais_recente_filtrado, sep=";", index=False)
                                else:
                                    print(" [BACK_FILTRADO] - Nenhum arquivo encontrado na pasta.")
                            #------------------------------------------------------------------------------------                   
                            def save_geral():
                                global dados_para_salvar_filtrado, dados_para_salvar_geral
                                global categoria_final, desc_categoria, desc_jurisprudencia
                                global contador_buffer, caminho_geral, dados_para_salvar_geral
                                categoria_final = 'geral_nao_processado'
                                desc_categoria = 'geral_nao_processado'
                                desc_jurisprudencia = 'geral_nao_processado'
                                save_processo_extraido() # SALVAR PROCESSO EXTRAIDO
                                save_backup_geral() # SALVAR BACKUP
                                # SALVAR RELATORIO
                                # request_api()
                                #------------------------------------------------------------------------------
                                print(' - [SAVE_geral] - categoria_final:', categoria_final)
                                print(' - [SAVE_geral] - desc_categoria:', desc_categoria)
                                print(' - [SAVE_geral] - descricao_jurisprudencia:', desc_jurisprudencia)
                                print(' - [SAVE_geral] - texto:', dados_para_salvar_geral)
                                if arquitetura == 'csv':
                                    df_novo = pd.DataFrame(dados_para_salvar_geral).astype(str).dropna(how='all')  
                                    if not df_novo.empty: 
                                        pasta_script = os.path.dirname(os.path.abspath(__file__))
                                        pasta_backup = os.path.join(pasta_script, 'pasta_backup')
                                        pasta_normalizada = os.path.join(pasta_backup, 'backup_normalizado')
                                        pasta_geral = os.path.join(pasta_normalizada, 'backup_geral')
                                        total_arquivos_backup_geral = len(os.listdir(pasta_geral))
                                        i = total_arquivos_backup_geral
                                        caminho_geral = os.path.join(pasta_geral, f'backup_geral_{i}.csv')
                                        if os.path.exists(caminho_geral):
                                            df_existente = pd.read_csv(caminho_geral, sep=";", dtype=str).astype(str)
                                            df_final = pd.concat([df_existente, df_novo], ignore_index=True).dropna(how='all')
                                        else:
                                            df_final = df_novo
                                        df_final.to_csv(caminho_geral, sep=";", index=False, encoding='utf-8-sig')
                                        print(f"✅ [{estado_atual}] Dados salvos em {caminho_geral} (GERAL)")
                                    else:
                                        print(f"⚠️ [{estado_atual}] Nenhum dado válido para salvar (GERAL)")
                            #------------------------------------------------------------------------------------------
                            def save_buffer(): # normalizado
                                global dados_para_salvar_filtrado, dados_para_salvar_geral
                                global categoria_final, desc_categoria, desc_jurisprudencia
                                global contador_buffer, caminho_filtrado, dados_para_salvar_filtrado
                                print(' - [BUFFER] - iniciando_salvamento_buffer')
                                pasta_buffer = os.path.join(pasta_script, 'pasta_buffer')
                                print(' - [BUFFER] - pasta_buffer ==', pasta_buffer)
                                if not os.path.exists(pasta_buffer):
                                    os.makedirs(pasta_buffer)

                                arquivo_buffer = os.path.join(pasta_buffer, 'buffer_normalizado.csv')
                                print('buffer_carregado')
                                expected_header = [
                                    "codigo_categoria",
                                    "categoria", "desc_categoria", "desc_jurisprudencia", "data_disponibilizacao",
                                    "tribunal", "nome_orgao", "numero_processo", 
                                    "tipo_documento", "txt_encontrado", "texto"
                                ]
                                df = pd.DataFrame(dados_para_salvar_filtrado, columns=expected_header)
                                print('df_gerado')
                                if not os.path.exists(arquivo_buffer):
                                    df.to_csv(arquivo_buffer, mode='w', header=True, index=False, sep=";")
                                else:
                                    df.to_csv(arquivo_buffer, mode='a', header=False, index=False, sep=";")
                                #--------------------------------------------------
                                df = pd.read_csv(arquivo_buffer, sep=";")
                                qtt_linhas_buffer = len(df)
                                print(f"✅ [{estado_atual}] Dados salvos em {arquivo_buffer} (BUFFER)")
                                
                                pasta_ia_settings = os.path.join(pasta_script, 'ia_settings')
                                json_ia_settings = os.path.join(pasta_ia_settings, 'ia_settings.json')
                                with open(json_ia_settings, 'r', encoding='utf-8') as f:
                                    ia_settings = json.load(f)
                                    batchsize_deploy_vetor = ia_settings["batchsize_deploy_vetor"]
                                print('dados_ia_carregados')
                                print('qtt_linhas_buffer', qtt_linhas_buffer)
                                print('batchsize_deploy_vetor', batchsize_deploy_vetor)
                                
                                if qtt_linhas_buffer >= batchsize_deploy_vetor:
                                    print(' - efetuando_deploy_geracao_vetor ')
                                    print(f" - [BUFFER] - ⚠️ - {qtt_linhas_buffer} linhas. ")
                                    print(f" - [BUFFER] - ⚠️ - INICIANDO ENCODER VETORIZADO ")
                                    print(' - bufffer_join_vetor')
                                    generate_vetor()
                                print('-buffer_finalizado')
                            #-----------------------------------------------------------------------------------------
                            def save_filtrado():
                                global dados_para_salvar_filtrado, dados_para_salvar_geral
                                global categoria_final, desc_categoria, desc_jurisprudencia
                                global contador_buffer, caminho_filtrado, dados_para_salvar_filtrado
                                request_api() 
                                print(' - [SAVE_filtrado] - categoria_final:', categoria_final)
                                print(' - [SAVE_filtrado] - desc_categoria:', desc_categoria)
                                print(' - [SAVE_filtrado] - descricao_jurisprudencia:', desc_jurisprudencia)
                                print(' - [SAVE_filtrado] - texto:', dados_para_salvar_filtrado)
                                desc_categoria = desc_categoria.replace("[descricao_categoria]", "")
                                desc_categoria = desc_categoria.replace("[DESCRICAO_CATEGORIA]", "")
                                desc_categoria = desc_categoria.replace("[Descricao_categoria]", "")
                                desc_categoria = desc_categoria.replace("[Descricao_Categoria]", "")
                                save_processo_extraido() # SALVAR PROCESSO EXTRAIDO 
                                save_backup_filtrado() # SALsAR BACKUP 
                                save_buffer()   
                                print('save_buffer_finalizado')
                                pasta_script = os.path.dirname(os.path.abspath(__file__))
                                pasta_backup = os.path.join(pasta_script, 'pasta_backup')
                                pasta_normalizada = os.path.join(pasta_backup, 'backup_normalizado')
                                pasta_backup_filtrado = os.path.join(pasta_normalizada, 'backup_filtrado')
                                total_arquivos = len(os.listdir(pasta_backup_filtrado))
                                arquivo_mais_recente = max([os.path.join(pasta_backup_filtrado, f) for f in os.listdir(pasta_backup_filtrado)], key=os.path.getmtime)
                                print(f" - [SAVE_filtrado] - Arquivo mais recente: {arquivo_mais_recente}")
                                caminho_filtrado = arquivo_mais_recente  
                                print('efetuando_save_final')
                                if arquitetura == 'csv':
                                    df_novo = pd.DataFrame(dados_para_salvar_filtrado).astype(str).dropna(how='all')    
                                    print ('sf1')
                                    if not df_novo.empty:
                                        if os.path.exists(caminho_filtrado):
                                            print ('sf2')
                                            df_existente = pd.read_csv(caminho_filtrado, sep=";", dtype=str).astype(str)
                                            df_final = pd.concat([df_existente, df_novo], ignore_index=True).dropna(how='all')
                                            df_final = df_final.drop_duplicates(subset='numero_processo')  # Remove duplicatas
                                            print('sf3')
                                        else:
                                            print('sf2____')
                                            df_final = df_novo.drop_duplicates(subset='numero_processo')
                                        df_final.to_csv(caminho_filtrado, sep=";", index=False, encoding='utf-8-sig')
                                        print('sf4')
                                        print(f"✅ [{estado_atual}] Dados salvos em {caminho_filtrado} (FILTRADO)")
                                    else:
                                        print(f"⚠️ [{estado_atual}] Nenhum dado válido para salvar (FILTRADO)")
                            #-----------------------------------------------------------------------------------------
                            def atualizar_tabela(): 
                                print('-atualizando_tabela')
                                global contador_append, contador_buffer, dados_front, tabela_frame, canvas, colunas, largura_celula, altura_celula
                                print('contador_buffer', contador_buffer)
                                print('contador_append', contador_append)
                                if contador_buffer > 100:
                                    pass
                                else:
                                    if contador_append == 10:
                                        limitador_ui = 25
                                        colunas = ["codigo_categoria", "categoria", "desc_categoria", "desc_jurisprudencia", "data_disponibilizacao", "tribunal", "nome_orgao", 
                                        "numero_processo", "tipo_documento", "txt_encontrado", "texto"]
                                        dados_front = dados_front[:limitador_ui]  # Limita os dados exibidos
                                        if not hasattr(atualizar_tabela, "labels"):
                                            atualizar_tabela.labels = []
                                        if not hasattr(atualizar_tabela, "header_labels"):
                                            atualizar_tabela.header_labels = []
                                            for idx, coluna in enumerate(colunas):
                                                label = ctk.CTkLabel(
                                                    tabela_frame, text=coluna, width=largura_celula, height=altura_celula,
                                                    anchor="w", fg_color="#4CAF50", text_color="white"
                                                )
                                                label.grid(row=0, column=idx, sticky="nsew", padx=1, pady=1)
                                                atualizar_tabela.header_labels.append(label)
                                        for i, linha in enumerate(dados_front):
                                            while len(atualizar_tabela.labels) <= i * len(colunas):  
                                                for j in range(len(colunas)):  
                                                    label = ctk.CTkLabel(
                                                        tabela_frame, text="", width=largura_celula, height=altura_celula,
                                                        anchor="w", fg_color="white", text_color="black", wraplength=largura_celula - 10
                                                    )
                                                    label.grid(row=i+1, column=j, sticky="nsew", padx=1, pady=1)
                                                    atualizar_tabela.labels.append(label)
                                            for j, valor in enumerate(linha.values()):
                                                texto_formatado = textwrap.shorten(str(valor), width=30, placeholder="...")
                                                atualizar_tabela.labels[i * len(colunas) + j].configure(text=texto_formatado)
                                        tabela_frame.update_idletasks()
                                        canvas.configure(scrollregion=canvas.bbox("all"))
                                        contador_append = 0
                            #-----------------------------------------------------------------------------------------
                            # with open(json_ia_settings, 'r', encoding='utf-8') as f:
                            #     ia_settings = json.load(f)
                            # batchsize_backupcsv_geral_normalizado = ia_settings["batchsize_backupcsv_geral_normalizado"]
                            # batchsize_backupcsv_filtrado_normalizado = ia_settings["batchsize_backupcsv_filtrado_normalizado"]
                            # batchsize_backupcsv_filtrado_vetorizado = ia_settings["batchsize_backupcsv_filtrado_vetorizado"]
                            # batchsize_deploy_vetor = ia_settings["batchsize_deploy_vetor"]
                            # batchsize_cache_processos = ia_settings["batchsize_cache_processos"]
                            # print(batchsize_backupcsv_geral_normalizado)
                            # print(batchsize_backupcsv_filtrado_normalizado)
                            # print(batchsize_backupcsv_filtrado_vetorizado)
                            # print(batchsize_deploy_vetor)
                            # print(batchsize_cache_processos)
                            print(" - 1 - data_disponibilizacao:", data_disponibilizacao)     
                            print(" - 3 - Tribunal:", tribunal_atual)
                            print(" - 4 - Nome do Órgão:", nomeOrgao)   
                            print(" - 5 - Número do Processo:", num_processo)
                            print(" - 6 - Número do Processo com Máscara:", numeroprocessocommascara)   
                            print(" - 7 - Tipo de Documento:", tipo_documento)      
                            print(" - 8 - texto = texto")
                            #------------------------------------------------------------------------------------------
                            try:
                                texto_sem_acentos = texto.lower()
                                texto_sem_acentos = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
                                palavras_chave = ["ementa", "acordao"]
                                tipo_documento_final = tipo_documento.lower()
                                tipo_documento_final = ''.join(c for c in unicodedata.normalize('NFD', tipo_documento_final) if unicodedata.category(c) != 'Mn')
                            except:
                                pass
                            palavra_encontrada = None
                            #-----------------------------------------------------------------------------------------
                            for palavra in palavras_chave:
                                if re.search(rf"\b{palavra}\b", texto_sem_acentos, re.IGNORECASE):
                                    palavra_encontrada = palavra
                                    break  
                            #-----------------------------------------------------------------------------------------
                            # FILTRO POR TEXTO - (GERAL)
                            #-----------------------------------------------------------------------------------------
                            var_save = ''
                            if palavra_encontrada: 
                                print(" - ✅ - ementa ou acórdão encontrado no texto ") 
                                print(f' - ✅ - variável encontrada no texto == {palavra_encontrada}')  
                                #------------------------------------------------------------------------------     
                                if palavra_encontrada == 'acordao': #GERAL 
                                    contador_txt_acordao += 1   
                                    texto_acordao_final = f"Total de textos c. 'acordao' = {contador_txt_acordao} "
                                    contador_txt_acordao_var.set(texto_acordao_final)
                                if palavra_encontrada == 'ementa':  #GERAL 
                                    contador_txt_ementa += 1    
                                    texto_ementa_final = f"Total de textos c. 'ementa' = {contador_txt_ementa}" 
                                    contador_txt_ementa_var.set(texto_ementa_final)
                                colunas = ["categoria", "desc_categoria", "desc_jurisprudencia", "data_disponibilizacao", "tribunal", "nome_orgao", 
                                "numero_processo", "tipo_documento", "txt_encontrado", "texto"]
                                #------------------------------------------------------------------------------
                                if tipo_documento_final == 'acordao': # FILTRADO
                                    print(" - ✅ - acórdão encontrado - no documento")
                                    print( " - ✅ - APPEND_FILTRADO " ) 
                                    contador_doc_acordao += 1
                                    txt_doc_acc = f"Total de docs 'acordao' = {contador_doc_acordao}"
                                    contador_doc_acordao_var.set(txt_doc_acc)
                                    contador_append += 1 
                                    contador_buffer += 1   
                                    var_save = 'filtrado' 
                                    save_filtrado()
                                    print('33_salvamento_efetuado_doc_acordao_filtrado')
                                #------------------------------------------------------------------------------
                                elif tipo_documento_final == 'ementa': # FILTRADO
                                    print(" - ✅ - ementa encontrada - no documento")
                                    print( " - ✅ - APPEND_FILTRADO " )
                                    contador_append += 1 
                                    contador_buffer += 1    
                                    contador_doc_ementa += 1
                                    txt_doc_ementa = f"Total de docs 'ementa' = {contador_doc_ementa}"
                                    contador_doc_ementa_var.set(txt_doc_ementa) 
                                    var_save = 'filtrado'
                                    save_filtrado()
                                    print('33_salvamento_efetuado_doc_ementa_filtrado')
                                #------------------------------------------------------------------------------
                                elif tipo_documento_final is not None and tipo_documento_final not in ['acordao', 'ementa']:  #GERAL 
                                    print(" - 🟨 - documento diferente ")
                                    print(f' - 🟨 - documento = {tipo_documento_final}')    
                                    print( " - ✅ - APPEND_GERAL " )
                                    categoria_final = 'gnp'
                                    desc_categoria = 'gnp'
                                    desc_jurisprudencia = 'gnp'
                                    if texto == '':
                                        texto = ''
                                    texto = texto.replace("\n", " ")
                                    dados_front.append({
                                            "categoria": categoria_final,
                                            "desc_categoria": desc_categoria,
                                            "desc_jurisprudencia": desc_jurisprudencia,
                                            "data_disponibilizacao": data_disponibilizacao, # 1 
                                            "tribunal": tribunal_atual, # 3
                                            "nome_orgao": nomeOrgao, #4 
                                            "numero_processo": num_processo,     #5
                                            "num_processo_masc": numeroprocessocommascara,      #6
                                            "tipo_documento": tipo_documento_final, #7  
                                            "txt_encontrado": palavra_encontrada, #8
                                            "texto": texto, #8
                                        }) 
                                    desc_categoria = desc_categoria.replace("[descricao_categoria]", "")
                                    desc_categoria = desc_categoria.replace("[DESCRICAO_CATEGORIA]", "")
                                    desc_categoria = desc_categoria.replace("[Descricao_categoria]", "")
                                    desc_categoria = desc_categoria.replace("[Descricao_Categoria]", "")
                                    desc_categoria = desc_categoria.replace("[categoria_antiga]", "")   
                                    desc_categoria = desc_categoria.replace("[Categoria_Antiga]", "")
                                    desc_categoria = desc_categoria.replace("[Categoria_antiga]", "")
                                    desc_categoria = desc_categoria.replace("[categoria_Antiga]", "")   
                                    desc_categoria = desc_categoria.replace("[CATEGORIA_ANTIGA]", "")   
                                    #-----------------------------------------------------------------------------------------
                                    # if txt_encontrado == '':
                                    #     if tipo_documento == 'acordao':
                                    #         txt_encontrado = 'acordao'
                                    #     if tipo_documento == 'ementa':
                                    #         txt_encontrado = 'ementa'
                                    #-----------------------------------------------------------------------------------------
                                    dados_para_salvar_geral.append({
                                        "categoria": categoria_final.replace('"', '').replace("\n", "").replace(";", ""),
                                        "desc_categoria": desc_categoria.replace('"', '').replace("\n", "").replace(";", ""),
                                        "desc_jurisprudencia": desc_jurisprudencia.replace('"', '').replace("\n", "").replace(";", ""),
                                        "data_disponibilizacao": data_disponibilizacao.replace('"', '').replace("\n", "").replace(";", ""),
                                        "tribunal": tribunal_atual.replace('"', '').replace("\n", "").replace(";", ""),
                                        "nome_orgao": nomeOrgao.replace('"', '').replace("\n", "").replace(";", ""),
                                        "numero_processo": num_processo.replace('"', '').replace("\n", "").replace(";", ""),
                                        "tipo_documento": tipo_documento_final.replace('"', '').replace("\n", "").replace(";", ""),
                                        "txt_encontrado": palavra_encontrada.replace('"', '').replace("\n", "").replace(";", ""),
                                        "texto": texto.replace('"', '').replace("\n", "").replace(";", "")
                                    })

                                    contador_append += 1 
                                    contador_buffer += 1  
                                    var_save = 'geral'  
                                    save_geral()
                            #-----------------------------------------------------------------------------------------
                            # FILTRO POR DOCUMENTO - (FILTRADO)
                            #-----------------------------------------------------------------------------------------
                            else:
                                print(" - 🟨 - texto não encontrado ['acordao, 'ementa'] ")     
                                print(" - 🟨 - verificando documento...")     
                                #------------------------------------------------------------------------------
                                if tipo_documento_final == 'acordao': # FILTRO POR TIPODOCUMENTO , FILTRADO
                                    print(" - ✅ - acórdão encontrado - no documento")  
                                    print(" - ✅ - APPEND_FILTRADO")
                                    palavra_encontrada = f'txt_miss_mas_tipo_documento_{tipo_documento_final}'
                                    contador_append += 1 
                                    contador_buffer += 1    
                                    contador_doc_acordao += 1       
                                    txt_doc_ac = f"Total de docs 'acordao' = {contador_doc_acordao}"
                                    contador_doc_acordao_var.set(txt_doc_ac)
                                    var_save = 'filtrado'
                                    save_filtrado() 
                                    print('33_salvamento_efetuado_doc_acordao_filtrado')
                                #------------------------------------------------------------------------------
                                if tipo_documento_final == 'ementa':    
                                    print(" - ✅ - ementa encontrada - no documento")  
                                    print(" - ✅ - APPEND_FILTRADO")
                                    contador_append += 1 
                                    contador_buffer += 1        
                                    contador_doc_ementa += 1    
                                    txt_doc_ementa = f"Total de docs 'ementa' = {contador_doc_ementa}"
                                    contador_doc_ementa_var.set(txt_doc_ementa)
                                    var_save = 'filtrado'
                                    save_filtrado()
                                    print('33_salvamento_efetuado_doc_ementa_filtrado')
                                #-------------------------------------------------------------------------
                                else:
                                    print(" - 🟥 - documento não encontrado")
                                    print(f' - 🟥 - documento = {tipo_documento_final}')
                            #-----------------------------------------------------------------------------------------     
                            print('caminho_arquivo_filtrado', caminho_filtrado)
                            print('caminho_arquivo_final', caminho_geral)
                            #-----------------------------------------------------------------------------------------            
                            print(' - - - - - - - - - - - - - - - - - - - ')
                            #-----------------------------------------------------------------------------------------
                            arquivo_docs = os.path.join(pasta_configs, 'docs.json') 
                            if not os.path.exists(arquivo_docs):
                                with open(arquivo_docs, 'w', encoding='utf-8') as f:
                                    json.dump({"lista_docs": []}, f, ensure_ascii=False, indent=4)
                            with open(arquivo_docs, 'r', encoding='utf-8') as file:
                                docs = json.load(file)
                                lista_docs = docs.get('lista_docs', [])
                                if not isinstance(lista_docs, list):
                                    lista_docs = lista_docs.split(',')
                                if tipo_documento not in lista_docs:
                                    lista_docs.append(tipo_documento)
                                    docs['lista_docs'] = lista_docs
                                    with open(arquivo_docs, 'w', encoding='utf-8') as file:
                                        json.dump(docs, file, ensure_ascii=False, indent=4)
                            #-----------------------------------------------------------------------------------------
                            print(' - quantidade_obtida', len(dados_para_salvar))
                            print('caminho_arquivo_final', caminho_arquivo_final)
                            #-----------------------------------------------------------------------------------------    
                            print('-call_tabela')
                            atualizar_tabela()
                            contador_pagina += 1    
                            print('----------------------------------')
                            print('-debug_lista')
                            #-----------------------------------------------------------------------------------------
                    miss = 0
                    #--------------------------------------------------
                except Exception as e:
                    print(e)
                    status_atual = f'ERRO: {e}'
                    status_atual_var.set(status_atual)
                    resultado_atual = None
                    resultado_atual = None
            else:
                print(f"Erro {response.status_code}: {response.text}")
                resultado_atual = None
            #---------------------------------------------------------------------
            # 🔴 Se leitura_anterior=True, aplica lógica alternativa
            if leitura_anterior:
                if not resultado_atual or not resultado_atual.get("items"):
                    print(f"⚠️ Nenhum item encontrado na página {page}. Continuando de onde parou.")
                    page += 1   
                    miss += 1
                    print('total_de_miss', miss)
                    limiter_miss = 10
                    print('limiter_de_miss', limiter_miss)
                    if miss > limiter_miss:
                        miss = 0
                        print('miss_igual_maior_a_10')
                        print('miss_resetado')
                        if 'ERRO' in status_atual:
                            # print(' - Erro encontrado, encerrando') 
                            # print(status_atual)
                            # status_atual_var.set(status_atual)  
                            return
                        else:
                            print(' - DEBUG_MASTER_1 ')
                            print(f" [33_S] [{estado_atual}] Request URL: {base_url}?{params}")
                            print(f" [55_S] lista_datas", lista_datas)    
                            print(f" [77_S] Data_atual =", data)
                            status_atual = 'Status atual : Scrapping Concluído'
                            status_atual_var.set(status_atual)
                            print(status_atual)
                            breakpoint()
                            return
                    continue
            else:
                if not resultado_atual or not resultado_atual.get("items"):
                    print(' - DEBUG_MASTER_0 ')
                    print(f" [33_S] [{estado_atual}] Request URL: {base_url}?{params}")
                    print(f" [55_S] lista_datas", lista_datas)    
                    print(f" [77_S] Data_atual =", data)
                    data = lista_datas[indice_atual]  # Obtém a data correspondente ao índice atual
                    print(f"[55_S] lista_datas {lista_datas}")    
                    print(f"[77_S] Data_atual = {data}")
                    indice_atual += 1
                    page = 1
                    status_atual = 'EFETUANDO SCRAPPING'
                    status_atual_var.set(status_atual)
                    pag_atual_var.set(f'Página Atual : {page}, Tribunal : {tribunal}, data : {data}')
                    continue
            page += 1
            #---------------------------------------------------------------------
            # Atualiza o cache
            tribunal = 'TODOS'
            cache = {
                'data_inicio': data_inicio,
                'data_fim': data_fim,
                'tribunal': tribunal,
                'current_date_index': idx,
                'current_page': page,
                'configs': configs
            }
            with open(arquivo_cache, 'w', encoding='utf-8') as f:
                json.dump(cache, f, ensure_ascii=False, indent=4)
                print(f"Cache salvo em {arquivo_cache}")
            #---------------------------------------------------------------------
            limpar_pasta_json()
            #---------------------------------------------------------------------
    estado_atual = "INACTIVE"
    print(f"✅ [{estado_atual}] Requisições finalizadas para todas as datas!")
#----------------------------------------------------------------------
janela_principal()