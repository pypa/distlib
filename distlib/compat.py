# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 The Python Software Foundation.
# See LICENSE.txt and CONTRIBUTORS.txt.
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
    from ._backport import shutil
    from urlparse import urlparse, urlunparse, urljoin, urlsplit, urlunsplit
    from urllib import urlretrieve, unquote, url2pathname, pathname2url
    import urllib2
    from urllib2 import Request, urlopen, URLError, HTTPError
    import httplib
    import xmlrpclib
    import Queue as queue

    _userprog = None
    def splituser(host):
        """splituser('user[:passwd]@host[:port]') --> 'user[:passwd]', 'host[:port]'."""
        global _userprog
        if _userprog is None:
            import re
            _userprog = re.compile('^(.*)@(.*)$')

        match = _userprog.match(host)
        if match: return match.group(1, 2)
        return None, host

else:
    from io import StringIO
    string_types = str,
    text_type = str
    from io import TextIOWrapper as file_type
    import builtins
    import configparser
    import shutil
    from urllib.parse import (urlparse, urlunparse, urljoin, splituser, unquote,
                              urlsplit, urlunsplit)
    from urllib.request import (urlopen, urlretrieve, Request, url2pathname,
                                pathname2url)
    from urllib.error import HTTPError, URLError
    import http.client as httplib
    import urllib.request as urllib2
    import xmlrpc.client as xmlrpclib
    import queue
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

try:
    import sysconfig
except ImportError:
    from ._backport import sysconfig

try:
    callable = callable
except NameError:
    from collections import Callable

    def callable(obj):
        return isinstance(obj, Callable)


try:
    fsencode = os.fsencode
except AttributeError:
    def fsencode(filename):
        if isinstance(filename, bytes):
            return filename
        elif isinstance(filename, str):
            return filename.encode(sys.getfilesystemencoding())
        else:
            raise TypeError("expect bytes or str, not %s" %
                            type(filename).__name__)

try:
    from tokenize import detect_encoding
except ImportError:
    from codecs import BOM_UTF8
    import re

    cookie_re = re.compile("coding[:=]\s*([-\w.]+)")

    def detect_encoding(readline):
        """
        The detect_encoding() function is used to detect the encoding that should
        be used to decode a Python source file.  It requires one argment, readline,
        in the same way as the tokenize() generator.

        It will call readline a maximum of twice, and return the encoding used
        (as a string) and a list of any lines (left as bytes) it has read in.

        It detects the encoding from the presence of a utf-8 bom or an encoding
        cookie as specified in pep-0263.  If both a bom and a cookie are present,
        but disagree, a SyntaxError will be raised.  If the encoding cookie is an
        invalid charset, raise a SyntaxError.  Note that if a utf-8 bom is found,
        'utf-8-sig' is returned.

        If no encoding is specified, then the default of 'utf-8' will be returned.
        """
        try:
            filename = readline.__self__.name
        except AttributeError:
            filename = None
        bom_found = False
        encoding = None
        default = 'utf-8'
        def read_or_stop():
            try:
                return readline()
            except StopIteration:
                return b''

        def find_cookie(line):
            try:
                # Decode as UTF-8. Either the line is an encoding declaration,
                # in which case it should be pure ASCII, or it must be UTF-8
                # per default encoding.
                line_string = line.decode('utf-8')
            except UnicodeDecodeError:
                msg = "invalid or missing encoding declaration"
                if filename is not None:
                    msg = '{} for {!r}'.format(msg, filename)
                raise SyntaxError(msg)

            matches = cookie_re.findall(line_string)
            if not matches:
                return None
            encoding = _get_normal_name(matches[0])
            try:
                codec = lookup(encoding)
            except LookupError:
                # This behaviour mimics the Python interpreter
                if filename is None:
                    msg = "unknown encoding: " + encoding
                else:
                    msg = "unknown encoding for {!r}: {}".format(filename,
                            encoding)
                raise SyntaxError(msg)

            if bom_found:
                if codec.name != 'utf-8':
                    # This behaviour mimics the Python interpreter
                    if filename is None:
                        msg = 'encoding problem: utf-8'
                    else:
                        msg = 'encoding problem for {!r}: utf-8'.format(filename)
                    raise SyntaxError(msg)
                encoding += '-sig'
            return encoding

        first = read_or_stop()
        if first.startswith(BOM_UTF8):
            bom_found = True
            first = first[3:]
            default = 'utf-8-sig'
        if not first:
            return default, []

        encoding = find_cookie(first)
        if encoding:
            return encoding, [first]

        second = read_or_stop()
        if not second:
            return default, [first]

        encoding = find_cookie(second)
        if encoding:
            return encoding, [first, second]

        return default, [first, second]
