from scrap import request_singular

def main():
    # Exemplo de uso com dados de teste
    data_inicio = "01/01/2023"
    data_fim = "01/01/2023"
    jurisprudencia_procurada = "teste"
    tribunais_selecionados = "Todos"
    request_singular(data_inicio, data_fim, jurisprudencia_procurada, tribunais_selecionados)

if __name__ == "__main__":
    main()
