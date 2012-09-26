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
    loader = unittest.TestLoader()
    runner = unittest.TextTestRunner()
    runner.run(loader.loadTestsFromModule(distlib_tests))

if __name__ == '__main__':
    #if os.path.exists('run'):
    #    shutil.rmtree('run')
    #os.mkdir('run')
    fn = os.path.join('run', 'test_all_%d.%d.log' % sys.version_info[:2])
    logging.basicConfig(level=logging.DEBUG, filename=fn, filemode='w',
                        format='%(levelname)-8s %(name)-20s %(message)s')
    main()

