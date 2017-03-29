# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2013 Vinay Sajip.
# Licensed to the Python Software Foundation under a contributor agreement.
# See LICENSE.txt and CONTRIBUTORS.txt.
#
import logging
import os
import shutil
import sys

from compat import unittest

# Always find our sources first
sys.path.insert(0, '..')
import distlib_tests
sys.path.pop(0)

def main():
    verbosity = 1
    if '-v' in sys.argv:
        verbosity = 2
    loader = unittest.TestLoader()
    failfast = 'FAILFAST' in os.environ
    runner = unittest.TextTestRunner(verbosity=verbosity, failfast=failfast)
    results = runner.run(loader.loadTestsFromModule(distlib_tests))
    return not results.wasSuccessful()

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
    sys.exit(main())
