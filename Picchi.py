import os,time
os.system('clear')
os.system('xdg-open https://t.me/xyteeetools')
from platform import uname
arch=uname().machine.lower()
if 'aarch' in arch:
    print(' \n\033[1;37m Congratulations! Your Device Support This Tools');time.sleep(2)
    import xcmain
    main()
else:
    print(' \033[1;31m Sorry system or device not support this tools');exit()
 
