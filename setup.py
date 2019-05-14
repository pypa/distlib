# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Vinay Sajip.
# Licensed to the Python Software Foundation under a contributor agreement.
# See LICENSE.txt and CONTRIBUTORS.txt.
#

import distutils.core
from distutils.sysconfig import get_python_lib
from os.path import join, dirname, abspath
import re
import sys

import distlib


class TestCommand(distutils.core.Command):
    user_options = []

    def run(self):
        import sys
        import unittest

        sys.path.append(join(dirname(__file__), 'tests'))
        import test_all
        sys.exit(test_all.main())

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

distutils.core.setup(
    name='distlib',
    version=distlib.__version__,
    author='Vinay Sajip',
    author_email='vinay_sajip@red-dove.com',
    url='https://bitbucket.org/pypa/distlib',
    download_url=('https://bitbucket.org/pypa/distlib/downloads/'
                  'distlib-' + distlib.__version__ + '.zip'),
    description='Distribution utilities',
    long_description = ('Low-level components of distutils2/packaging, '
                        'augmented with higher-level APIs for making '
                        'packaging easier.'),
    license='Python license',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Python Software Foundation License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development',
    ],
    platforms='any',
    packages=[
        'distlib',
        'distlib._backport',
    ],
    package_data={
        'distlib._backport': ['sysconfig.cfg'],
        'distlib': ['t32.exe', 't64.exe', 'w32.exe', 'w64.exe'],
    },
    cmdclass={
        'test': TestCommand,
    },
)
