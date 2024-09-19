# Copyright (C) 2024 Stewart Miles
# Licensed to the Python Software Foundation under a contributor agreement.
# See LICENSE.txt and CONTRIBUTORS.txt.
import codecs
import os
import json
from setuptools import Extension, setup
from setuptools.command import egg_info
import sys


EMBED_EXTENSIONS_METADATA = (
    int(os.getenv('MINIMEXT_EMBED_EXTENSIONS_METADATA', '0')))


class EggInfo(egg_info.egg_info):
    """egg_info command that optionally writes extensions metadata.

    distlib.wheel.Wheel attempts to read the list of extensions from the
    undocumented JSON EXTENSIONS metadata file.

    This command will add the special file JSON EXTENSIONS metadata file to the
    *.dist-info directory in the wheel if the
    MINIMEXT_EMBED_EXTENSIONS_METADATA environment variable is set to 1.
    """

    def run(self):
        egg_info.egg_info.run(self)
        if EMBED_EXTENSIONS_METADATA:
            build_ext = self.get_finalized_command('build_ext')
            extensions_dict = {
                ext_module.name: build_ext.get_ext_filename(ext_module.name)
                for ext_module in self.distribution.ext_modules
            }
            with open(os.path.join(self.egg_info, 'EXTENSIONS'), 'wb') as (
                    extensions_file):
                json.dump(extensions_dict,
                          codecs.getwriter('utf-8')(extensions_file),
                          indent=2)


setup(
    name='minimext' + ('_metadata' if EMBED_EXTENSIONS_METADATA else ''),
    version='0.1',
    description='Calculates Fibonacci numbers.',
    long_description=(
        'Distribution that provides calculate.fib() and calculate_py.fib() '
        'which calculate Fibonacci numbers. minimext.calculate is implemented '
        'as a C extension to test distlib.wheel.Wheel.mount().'),
    packages=['minimext'],
    ext_modules=[
        Extension(name='minimext.calculate',
                  sources=['calculate.c'],
                  py_limited_api=True,
                  define_macros=[
                      ('Py_LIMITED_API', str(sys.version_info.major)),
                  ]),
    ],
    # The extension uses the limited API so tag the wheel as compatible with
    # Python 3.2 and later.
    #
    # Unfortunately the py_limited_api argument to Extension does not mark the
    # wheel as supporting the limited API, so set the see compatibility
    # manually.
    options={'bdist_wheel': {'py_limited_api': 'cp32'}},
    cmdclass={'egg_info': EggInfo},
)
