#!pythonw
import sys
with open(sys.argv[1], 'wb') as f:
    f.write(sys.argv[2].encode('ascii'))
