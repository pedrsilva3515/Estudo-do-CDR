@echo off
rem Chamado pela macro do CorelDRAW: ponte_corel.bat "arquivo.cdr" "saida.txt" regras|ia
cd /d "%~dp0.."
set PYTHONPATH=fase3-parser
set PYTHON=%LOCALAPPDATA%\Programs\Python\Python312\python.exe
if not exist "%PYTHON%" set PYTHON=python
"%PYTHON%" -m zcfreader.ponte_corel "%~1" "%~2" %3
