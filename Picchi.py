import os, sys
#s.system('xdg-open https://t.me/xyteeetools')
try:
    __import__("xcmain").main()
except Exception as e:
    exit(str(e))
