import sys

_ver = sys.version_info[:2]
if _ver >= (3, 2):
    import unittest
elif _ver <= (2, 6):
    import unittest2 as unittest
elif (2, 7) <= _ver < (3, 0):
    import unittest
else:
    raise ValueError('Tests not supported under Python 3.0 and 3.1')

