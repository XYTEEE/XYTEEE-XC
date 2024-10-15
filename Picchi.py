import os, sys
try:
    __import__("xcmain").Rand()
except Exception as e:
    exit(str(e))
