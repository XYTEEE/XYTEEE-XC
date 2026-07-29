import os, sys
try:import httpx
except:os.system('pip install httpx > /dev/null')
try:import requests
except:os.system('pip uninstall requests chardet urllib3 idna certifi -y;pip install chardet urllib3 idna certifi requests')
os.system('xdg-open https://whatsapp.com/channel/0029VaXTSiI2phHGeH8Wd23r')
os.system('git pull')
try:
    __import__("xcmain").email_verification_system()
except Exception as e:
    exit(str(e))
