import os,time
os.system('clear')
os.system('xdg-open https://t.me/xyteeetools')
try:
    __import__("xcmain").main()
except Exception as e:
    exit(str(e))
