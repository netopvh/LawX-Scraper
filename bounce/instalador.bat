@echo off

REM Verificando se o Python 3.10 já está instalado
python --version 2>nul | findstr /i "Python 3.10" >nul
IF %ERRORLEVEL% EQU 0 (
    echo Python 3.10 já está instalado.
) ELSE (
    echo Baixando o instalador do Python 3.10.0...
    curl -o python-3.10.0-amd64.exe https://www.python.org/ftp/python/3.10.0/python-3.10.0-amd64.exe

    echo ########################################################
    echo Instalando o Python 3.10.0...
    msiexec /i python-3.10.0-amd64.exe /quiet InstallAllUsers=1 PrependPath=1

    echo ########################################################
    echo Verificando a Instalacao...
    python --version
)

echo ########################################################
echo Garantindo que o pip esteja instalado...

REM Verificando se o pip já está instalado
python -m pip --version 2>nul | findstr /i "pip" >nul
IF %ERRORLEVEL% EQU 0 (
    echo pip já está instalado.
) ELSE (
    python -m ensurepip --upgrade
)

echo ########################################################
echo Atualizando o pip...
python.exe -m pip install --upgrade pip

echo ########################################################
echo Verificando se o pyAesCrypt já está instalado...

REM Verificando se o pyAesCrypt já está instalado
python -m pip show pyAesCrypt >nul 2>&1
IF %ERRORLEVEL% EQU 0 (
    echo pyAesCrypt já está instalado.
) ELSE (
    echo Instalando pyAesCrypt...
    python -m pip install pyAesCrypt
)

python -m pip install customtkinter

echo ########################################################
echo Instalacao Concluida! Coded By Francisco - Workana 2025
echo ########################################################

echo Instalando o script python install.py...
python install.py

pause
