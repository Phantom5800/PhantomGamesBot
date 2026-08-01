@echo off

if not defined PYVER set PYVER=3.11
echo Initializing bot for Python version %PYVER%

pip install pipenv
pipenv --python %PYVER%
pipenv install -r requirements.txt
