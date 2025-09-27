import os
import pytest
from dotenv import load_dotenv

# Adicione o caminho para o diretório 'simplified_code' ao PYTHONPATH
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'simplified_code', 'logic_test'))

from ask import test_openai_api_key, get_categories, classify_text, generate_response, OPENAI_API_KEY, OPENAI_MODEL, CATEGORIES_CSV_PATH

# Carregar variáveis de ambiente do .env
load_dotenv()

class TestIntegrationAsk:
    @pytest.fixture(scope="class", autouse=True)
    def setup_class(self):
        # Verifica se as variáveis de ambiente estão carregadas
        assert OPENAI_API_KEY is not None, "OPENAI_API_KEY não está configurada."
        assert OPENAI_MODEL is not None, "OPENAI_MODEL não está configurada."
        assert CATEGORIES_CSV_PATH is not None, "CATEGORIES_CSV_PATH não está configurada."
        
        # Valida a chave da API OpenAI
        assert test_openai_api_key(OPENAI_API_KEY), "Chave OpenAI inválida."

    def test_classify_and_generate_response(self):
        # Dados de teste reais
        test_text = "Este é um texto de teste sobre direito civil e contratos."
        
        # Obter categorias
        categories = get_categories(CATEGORIES_CSV_PATH)
        assert len(categories) > 0, "Nenhuma categoria encontrada."

        # Classificar o texto
        classified_category = classify_text(test_text, categories, OPENAI_MODEL)
        print(f"Categoria classificada: {classified_category}")
        assert classified_category is not None and classified_category != "", "A classificação da categoria retornou vazia."

        # Gerar resposta
        ai_response = generate_response(test_text, classified_category, OPENAI_MODEL)
        print(f"Resposta da IA: {ai_response}")
        assert ai_response is not None and ai_response != "", "A resposta da IA retornou vazia."

        # Opcional: Adicionar mais asserções baseadas no conteúdo esperado
        # Por exemplo, verificar se a categoria classificada está na lista de categorias
        assert classified_category in categories, f"Categoria '{classified_category}' não está na lista de categorias válidas."