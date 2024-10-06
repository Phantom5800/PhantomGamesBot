@echo off

if not defined PYVER set PYVER=3.11
echo Initializing bot for Python version %PYVER%

pip install pipenv
pipenv --python %PYVER%
pipenv install twitchio
pipenv install srcomapi
pipenv install py-cord==2.4.1
pipenv install AnilistPython==0.1.3
pipenv install markovify
pipenv install tweepy
pipenv install google-api-python-client
pipenv install google-auth-oauthlib google-auth-httplib2
