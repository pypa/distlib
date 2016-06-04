#!python
import sys
import os
input = repr(sys.stdin.read())
print(os.path.basename(sys.argv[0]))
print(sys.argv[1:])
print(input)
if __debug__:
    print('non-optimized')
