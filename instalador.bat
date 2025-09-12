@echo off
setlocal EnableDelayedExpansion

:: Tenta obter a versão do Python instalada (se houver)
for /f "tokens=2 delims= " %%a in ('python --version 2^>nul') do (
    set PY_VER=%%a
)

:: Verifica se o Python está instalado e se a versão começa com "3.10"
if defined PY_VER (
    if "!PY_VER:~0,4!"=="3.10" (
        echo Python 3.10 ja esta instalado (versao: %PY_VER%).
        goto Fim
    )
)

echo Python 3.10 nao encontrado. Iniciando o download e instalacao...
echo ########################################################
echo Baixando o instalador do Python 3.10.0...
curl -o python-3.10.0-amd64.exe https://www.python.org/ftp/python/3.10.0/python-3.10.0-amd64.exe

echo ########################################################
echo Instalando o Python 3.10.0...
msiexec /i python-3.10.0-amd64.exe /quiet InstallAllUsers=1 PrependPath=1

echo ########################################################
echo Atualizando o pip...
python.exe -m pip install --upgrade pip

echo Verificando a instalacao...
python --version
echo ########################################################
python -m pip install pinecone-client
python -m pip install customtkinter
python -m pip install textwrap
python -m pip install requests
python -m pip install pandas
python -m pip install unicodedata
python -m pip install tensorflow
python -m pip install sentence-transformers
python -m pip install unidecode
echo ########################################################
echo Instalacao Concluida! Coded By Francisco - Workana 2025
echo ########################################################
python appcode.py
pause
