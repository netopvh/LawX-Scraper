import pytest
import requests_mock
from scrap import fetch_content_from_url, processar_com_ia, load_valid_categories
import os

# Mock para a variável de ambiente OPENAI_API_KEY
@pytest.fixture(autouse=True)
def mock_openai_api_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "dummy_api_key")

def test_fetch_content_from_url_success():
    """
    Verifica se a função extrai corretamente o conteúdo HTML de uma URL válida.
    """
    with requests_mock.Mocker() as m:
        mock_url = "http://example.com/document"
        mock_html_content = """
        <html>
            <body>
                <p>Este é um parágrafo de teste.</p>
                <div>Outro conteúdo.</div>
            </body>
        </html>
        """
        m.get(mock_url, text=mock_html_content, headers={'Content-Type': 'text/html'})

        extracted_text = fetch_content_from_url(mock_url)
        assert "Este é um parágrafo de teste." in extracted_text
        assert "Outro conteúdo." in extracted_text

def test_fetch_content_from_url_failure():
    """Verifica se a função retorna None ao tentar extrair conteúdo de uma URL inexistente ou com erro."""
    with requests_mock.Mocker() as m:
        mock_url = "http://example.com/nonexistent"
        m.get(mock_url, status_code=404)

        extracted_text = fetch_content_from_url(mock_url)
        assert extracted_text is None

def test_fetch_content_from_url_empty_content():
    """Verifica se a função lida corretamente com URLs que retornam conteúdo HTML vazio."""
    with requests_mock.Mocker() as m:
        mock_url = "http://example.com/empty"
        m.get(mock_url, text="", headers={'Content-Type': 'text/html'})

        extracted_text = fetch_content_from_url(mock_url)
        assert extracted_text == ""

def test_processar_com_ia_classificacao_sucesso():
    """
    Verifica se a função processar_com_ia classifica corretamente um texto simples.
    """
    with requests_mock.Mocker() as m:
        # Mock para a criação da Thread
        m.post("https://api.openai.com/v1/threads", json={"id": "thread_dummy_id"})
        # Mock para adicionar mensagem à Thread
        m.post("https://api.openai.com/v1/threads/thread_dummy_id/messages", json={"id": "msg_dummy_id", "thread_id": "thread_dummy_id"})
        # Mock para a criação do Run
        m.post("https://api.openai.com/v1/threads/thread_dummy_id/runs", json={"id": "run_dummy_id", "thread_id": "thread_dummy_id", "assistant_id": "asst_dummy_id"})
        # Mock para verificar o status do Run
        m.get("https://api.openai.com/v1/threads/thread_dummy_id/runs/run_dummy_id", json={"status": "completed"})
        # Mock para obter as mensagens da Thread (resposta final da IA)
        m.get("https://api.openai.com/v1/threads/thread_dummy_id/messages", json={
            "data": [
                {
                    "content": [
                        {
                            "text": {
                                "value": "{\"categoria_id\": \"Direito Constitucional\", \"desc_categoria\": \"Ramo do direito que estuda a Constituição, a organização do Estado e os direitos fundamentais.\"}"
                            },
                            "type": "text"
                        }
                    ],
                    "role": "assistant"
                }
            ]
        })

        test_text = "Processo 5014490-04.2023.4.02.5121 distribuido para PRESIDÊNCIA - TURMA NACIONAL DE UNIFORMIZAÇÃO na data de 22/09/2025."
        dummy_item = {}
        dummy_api_key = "dummy_api_key"
        dummy_categories_file_id = "file-dummy_id"
        dummy_payload_uri = "http://dummy.uri"

        # Carregar categorias válidas para o teste
        categorias_csv_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'categorias.csv')
        valid_categories = load_valid_categories(categorias_csv_path)

        resultado = processar_com_ia(test_text, dummy_categories_file_id, dummy_payload_uri)

        print(f"Resultado da IA: {resultado}")

        assert resultado["categoria_id"] == "Direito Constitucional"
        assert resultado["desc_categoria"] == "Ramo do direito que estuda a Constituição, a organização do Estado e os direitos fundamentais."
        assert resultado["categories_file_id"] == dummy_categories_file_id

        # Verificar se a categoria retornada está nas categorias válidas
        assert "Direito Constitucional" in valid_categories
        assert valid_categories["Direito Constitucional"] == "Ramo do direito que estuda a Constituição, a organização do Estado e os direitos fundamentais."