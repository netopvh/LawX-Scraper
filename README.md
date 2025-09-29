# LawX Scraper

Um web scraper construído com UV Python para extrair dados legais de sites jurídicos.

## Visão Geral

O LawX Scraper é uma ferramenta de web scraping de alto desempenho que utiliza as capacidades assíncronas do UV Python para coletar informações jurídicas de várias fontes de forma eficiente. O scraper foi projetado para lidar com múltiplas requisições simultaneamente, respeitando limites de taxa e políticas dos sites.

## Funcionalidades

- Web scraping assíncrono usando UV Python
- Gerenciamento eficiente de requisições concorrentes
- Limitação de taxa e scraping respeitoso
- Extração e análise de dados
- Exportação para formatos estruturados (JSON, CSV)

## Requisitos

- Python 3.7+
- UV Python
- aiohttp
- beautifulsoup4
- pandas

## Instalação

### Instalação via UV (Recomendado)

```bash
# Clone o repositório
git clone [url-do-repositorio]
cd lawx-scraper

# Instale o UV (modo simplificado com Python pré instalado)
pip install uv (não aconselho instalar esse dentro da venv)

# Instale o UV (mesmo sem ter o Python)
link para a documentação: https://docs.astral.sh/uv/getting-started/installation/#standalone-installer

# Instale o Python com o UV
link para a documentação: https://docs.astral.sh/uv/guides/install-python/

# Instale com UV (recomendado com gestão de dependencia)
uv sync --active --link-mode=copy

# Instale com PIP (Python caso não queira usar o UV)
pip install -r requirements.txt

# Executar a aplicação (usando UV)
uv run main.py #inicialização curta (menos linhas para chamar)
uv run app_code_120.py #inicialização direta (inica o projeto sem intermediario)
```

# Executar a aplicação (usando Python)

python scrap.py --data-inicio "28/09/2025" --data-fim "28/09/2025" --jurisprudencia "Ementa, Acórdão" --tribunal "TODOS" --test (para rodar teste de 3 escritas)

## Configuração

1. **Configuração inicial**: Execute o aplicativo e configure:

   - Chave de API OpenAI (para análise com IA)
   - Diretório de downloads
   - Tribunais alvo
   - Período de busca
2. **Arquivos de configuração**:

   - `config/tribunais.json`: Lista de tribunais disponíveis
   - `config/docs.json`: Tipos de documentos aceitos

## Uso


### Parâmetros de Busca

- **Tribunais**: Selecione tribunais específicos ou "TODOS"
- **Período**: Defina data inicial e final
- **Tipo de Busca**: Jurisprudência ou Artigo específico
- **Filtros**: Documentos tipo "acórdão" ou "ementa"

## Estrutura do Projeto

```
LawX-Scraper/
├── app_code_120.py          # Aplicação principal GUI
├── main.py                  # Script CLI principal
├── configurações/           # Arquivos de configuração
│   ├── configs.json         # Configurações do sistema
│   ├── tribunais.json       # Lista de tribunais
│   ├── docs.json           # Tipos de documentos
│   └── prompts/            # Prompts para IA
├── downloads/              # Saída dos dados
│   └── pasta_relatorios/   # Relatórios CSV/Excel
├── pasta_cache/            # Cache de processos
├── pasta_backup/           # Backups de dados
├── buffer_vetorizado/      # Dados vetorizados para IA
└── ia_settings/           # Configurações de IA
```

## Funcionalidades Avançadas

### Análise com IA

- **Categorização automática**: Classifica documentos jurídicos
- **Sumarização**: Gera descrições concisas de jurisprudências
- **Privacidade**: Remove nomes de pessoas (substitui por "polo ativo/passivo")

### Sistema de Cache

- **Retomada de processos**: Continua de onde parou
- **Evita duplicatas**: Verifica processos já extraídos
- **Backup automático**: Salva progresso a cada intervalo

### Formatos de Saída

- **CSV**: Dados tabulares completos
- **Excel**: Planilhas formatadas
- **JSON**: Dados estruturados para integração

## Exemplos de Uso

### Busca por Jurisprudência

1. Abra a aplicação
2. Selecione "Jurisprudência" no tipo de busca
3. Escolha o tribunal ou "TODOS"
4. Defina o período (ex: 01/01/2024 a 31/12/2024)
5. Clique em "Iniciar Busca"

### Busca por Artigo Específico

1. Selecione "Artigo" no tipo de busca
2. Digite o número do artigo (ex: 121)
3. Configure filtros adicionais
4. Execute a busca

### Exportação de Dados

- Arquivos são salvos em: `downloads/pasta_relatorios/`
- Nomenclatura: `[TRIBUNAL]_[DATA]_[TIPO].csv`
- Exemplo: `TODOS_2024-12-31_geral.csv`

## Limites e Respeito às Fontes

- **Rate limiting**: Respeita limites de requisição
- **Backoff exponencial**: Tratamento de erros 429
- **User-Agent**: Identificação adequada nas requisições
- **Intervalos**: Pausas entre requisições para evitar sobrecarga

## Solução de Problemas

### Erros Comuns

1. **"API Key inválida"**: Configure a chave OpenAI em configs.json
2. **"Tribunal não encontrado"**: Verifique a lista em tribunais.json
3. **"Sem resultados"**: Ajuste o período ou filtros

### Logs e Debug

- Verifique o console para mensagens de erro
- Arquivos de log são criados automaticamente
- Cache pode ser limpo via interface

## Contribuindo

1. Fork o projeto
2. Crie uma branch `feature/nova-funcionalidade`
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para detalhes.

## Suporte

Para dúvidas ou problemas:

- Crie uma issue no GitHub
- Consulte a documentação em `/docs`
- Verifique os logs em `pasta_cache/`

---

## Testes

Para executar os testes e gerar um relatório HTML, utilize o seguinte comando:

```bash
uv run pytest --html=tests_report/report.html --self-contained-html
```

O relatório `report.html` será gerado na pasta `tests_report/`.

Para visualizar o relatório, você pode iniciar um servidor HTTP simples na pasta `tests_report`:

```bash
cd tests_report
python -m http.server 8000
```

Em seguida, abra seu navegador e acesse `http://localhost:8000/report.html`.

---

# Exibindo dados na tabela

Atualmente conseguimos exibir os dados do scriping via relatório depois da pesquisa e pelo botão recuperar anterior que vai buscar destes relatórios e vai renderiza-los na tabela da aplicação.
analises atuais ficam salvos como relatório mas ainda não exibidos depois do processo na tabela o que sera resolvido em breve.

**Desenvolvido com ❤️ para a LawX e comunidade jurídica brasileira**
