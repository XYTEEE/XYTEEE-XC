import os, sys
try:
    __import__("xcmain").security()
except Exception as e:
    exit(str(e))
