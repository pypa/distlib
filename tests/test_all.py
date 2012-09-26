#
# Copyright (C) 2012 Vinay Sajip. All rights reserved.
#
import logging
import os
import shutil
import sys
import unittest

# Always find our sources first
sys.path.insert(0, '..')
import distlib_tests

def main():
    verbosity = 1
    if '-v' in sys.argv:
        verbosity = 2
    loader = unittest.TestLoader()
    runner = unittest.TextTestRunner(verbosity=verbosity)
    runner.run(loader.loadTestsFromModule(distlib_tests))

if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(__file__))
    rundir = os.path.join(here, 'run')
    if not os.path.exists(rundir):
        os.mkdir(rundir)
    elif not os.path.isdir(rundir):
        raise ValueError('Not a directory: %r' % rundir)
    fn = os.path.join(rundir, 'test_all_%d.%d.log' % sys.version_info[:2])
    logging.basicConfig(level=logging.DEBUG, filename=fn, filemode='w',
                        format='%(levelname)-8s %(name)-20s %(message)s')
    main()

