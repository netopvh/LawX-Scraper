import os
import argparse
import json
from dotenv import load_dotenv
from openai import OpenAI
import pandas as pd

# Carregar variáveis de ambiente do .env
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL")
CATEGORIES_CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "docs", "categorias.csv")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY não encontrada no arquivo .env")
if not OPENAI_MODEL:
    raise ValueError("OPENAI_MODEL não encontrada no arquivo .env")
if not CATEGORIES_CSV_PATH:
    raise ValueError("CATEGORIES_CSV_PATH não encontrada no arquivo .env")

client = OpenAI(api_key=OPENAI_API_KEY)

def test_openai_api_key(api_key):
    try:
        test_client = OpenAI(api_key=api_key)
        models = test_client.models.list()
        print("Modelos OpenAI disponíveis:")
        for model in models.data:
            print(f"- {model.id}")
        return True
    except Exception as e:
        print(f"Erro ao conectar com a OpenAI: {e}")
        return False

def get_categories(csv_path):
    try:
        df = pd.read_csv(csv_path)
        return df["categoria"].tolist()
    except FileNotFoundError:
        raise FileNotFoundError(f"Arquivo de categorias não encontrado: {csv_path}")

def classify_text(text, categories, model):
    category_list = ", ".join(categories)
    prompt = f"""
    Você é um assistente de IA especializado em classificar textos jurídicos.
    Classifique o seguinte texto em uma das categorias fornecidas:
    Categorias disponíveis: {category_list}

    Texto a ser classificado: "{text}"

    Retorne apenas o nome da categoria mais relevante.
    """
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Você é um assistente de IA."}, 
            {"role": "user", "content": prompt}
        ],
        max_tokens=50
    )
    return response.choices[0].message.content.strip()

def generate_response(text, classified_category, model):
    prompt = f"""
    Com base no texto original e na categoria classificada, gere uma resposta concisa e relevante.
    Texto original: "{text}"
    Categoria classificada: "{classified_category}"

    Resposta:
    """
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Você é um assistente de IA."}, 
            {"role": "user", "content": prompt}
        ],
        max_tokens=200
    )
    return response.choices[0].message.content.strip()
def main():
    parser = argparse.ArgumentParser(description="Comunica-se com a OpenAI para classificar e gerar respostas para um texto.")
    parser.add_argument("--texto", required=True, help="O texto a ser enviado para a OpenAI.")
    args = parser.parse_args()

    if not test_openai_api_key(OPENAI_API_KEY):
        print("Chave OpenAI inválida. Verifique sua API Key no arquivo .env")
        return

    categories = get_categories(CATEGORIES_CSV_PATH)
    
    classified_category = classify_text(args.texto, categories, OPENAI_MODEL)
    ai_response = generate_response(args.texto, classified_category, OPENAI_MODEL)

    output = {
        "texto_original": args.texto,
        "categoria_classificada": classified_category,
        "resposta_ia": ai_response
    }
    
    output_file_path = os.path.join(os.path.dirname(__file__), "resposta.json")
    with open(output_file_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=4, ensure_ascii=False)
    print(f"Saída JSON salva em: {output_file_path}")

if __name__ == "__main__":
    main()
