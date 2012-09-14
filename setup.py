# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Vinay Sajip. All Rights Reserved.
#

import distutils.core
from distutils.sysconfig import get_python_lib
from os.path import join, dirname, abspath
import re
import distlib


class TestCommand(distutils.core.Command):
    user_options = []

    def run(self):
        import sys
        import unittest

        sys.path.append(join(dirname(__file__), 'tests'))
        import distlib_tests
        loader = unittest.TestLoader()
        runner = unittest.TextTestRunner()
        runner.run(loader.loadTestsFromModule(distlib_tests))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

distutils.core.setup(
    name='distlib',
    version=distlib.__version__,
    author='Vinay Sajip',
    author_email='vinay_sajip@red-dove.com',
    url='https://bitbucket.org/vinay.sajip/distlib',
    description='Distribution utilities',
    long_description = 'Low-level components of distutils2/packaging',
    license='BSD',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development',
    ],
    platforms='any',
    packages=['distlib'],
    cmdclass={
        'test': TestCommand,
    },
)
