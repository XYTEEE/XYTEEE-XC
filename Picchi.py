os.system('xdg-open https://t.me/xyteeetools')
import os, sys
try:
    __import__("xcmain").main()
except Exception as e:
    exit(str(e))
