import os, sys, platform
try:os.system('pip uninstall requests chardet urllib3 idna certifi -y;pip install chardet urllib3 idna certifi requests')
except:pass
try:os.system('git pull')
except:pass
try:os.system('am start https://t.me/xyteeetools')
except:pass
bit = platform.architecture()[0]
if bit == '64bit':
    import xcmain
    xcmain.Rand()
elif bit == '32bit':
    os.system("exit")
 
