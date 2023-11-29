import os, sys
try:
    __import__("xcmain").main()
except Exception as e:
    exit(str(e))
