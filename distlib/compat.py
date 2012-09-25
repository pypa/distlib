#
# Copyright (C) 2012 Vinay Sajip. All rights reserved.
#
from __future__ import absolute_import

import os
import sys

if sys.version_info[0] < 3:
    from StringIO import StringIO
    string_types = basestring,
    text_type = unicode
    from types import FileType as file_type
    import __builtin__ as builtins
    import ConfigParser as configparser
else:
    from io import StringIO
    string_types = str,
    text_type = str
    from io import TextIOWrapper as file_type
    import builtins
    import configparser

try:
    from platform import python_implementation
except ImportError:
    def python_implementation():
        """Return a string identifying the Python implementation."""
        if 'PyPy' in sys.version:
            return 'PyPy'
        if os.name == 'java':
            return 'Jython'
        if sys.version.startswith('IronPython'):
            return 'IronPython'
        return 'CPython'

