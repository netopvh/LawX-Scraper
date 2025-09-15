#!/usr/bin/env python3
"""
Script para carregar variáveis de ambiente do arquivo .env
Este script pode ser importado no início do app_code_120.py para carregar as variáveis de ambiente.
"""

import os
from pathlib import Path

def load_env():
    """Carrega as variáveis de ambiente do arquivo .env"""
    env_path = Path(__file__).parent / '.env'
    
    if not env_path.exists():
        print("Arquivo .env não encontrado. Criando arquivo com valores padrão...")
        return False
    
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        
        print("Variáveis de ambiente carregadas com sucesso!")
        return True
        
    except Exception as e:
        print(f"Erro ao carregar .env: {e}")
        return False

def update_configs_from_env():
    """Atualiza configs.json com valores do .env se disponíveis"""
    import json
    
    config_path = Path(__file__).parent / 'configurações' / 'configs.json'
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            configs = json.load(f)
        
        # Atualiza com valores do ambiente se disponíveis
        if os.getenv('OPENAI_API_KEY'):
            configs['api_key'] = os.getenv('OPENAI_API_KEY')
        
        if os.getenv('PINECONE_API_KEY'):
            configs['api_pinecone'] = os.getenv('PINECONE_API_KEY')
            
        if os.getenv('OPENAI_MODEL'):
            configs['modelo_atual'] = os.getenv('OPENAI_MODEL')
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(configs, f, indent=4, ensure_ascii=False)
            
        print("Arquivo configs.json atualizado com variáveis de ambiente!")
        
    except Exception as e:
        print(f"Erro ao atualizar configs.json: {e}")

if __name__ == "__main__":
    if load_env():
        update_configs_from_env()
        print("Configuração de ambiente concluída!")
    else:
        print("Execute este script para configurar as variáveis de ambiente.")