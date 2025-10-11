import os, sys
try:
    __import__("xcmain").email_verification_system()
except Exception as e:
    exit(str(e))
