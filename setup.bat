@echo off

if not defined PYVER set PYVER=3.9
echo Initializing bot for Python version %PYVER%

pip install pipenv
pipenv --python %PYVER%
pipenv install twitchio
pipenv install srcomapi
pipenv install discord
