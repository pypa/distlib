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
    from urllib import (urlretrieve, quote as _quote, unquote, url2pathname,
                        pathname2url)

    def quote(s):
        if isinstance(s, unicode):
            s = s.encode('utf-8')
        return _quote(s)

    import urllib2
    from urllib2 import Request, urlopen, URLError, HTTPError
    import httplib
    import xmlrpclib
    import Queue as queue
    from HTMLParser import HTMLParser
    import htmlentitydefs

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
    from urllib.parse import (urlparse, urlunparse, urljoin, splituser, quote,
                              unquote, urlsplit, urlunsplit)
    from urllib.request import (urlopen, urlretrieve, Request, url2pathname,
                                pathname2url)
    from urllib.error import HTTPError, URLError
    import http.client as httplib
    import urllib.request as urllib2
    import xmlrpc.client as xmlrpclib
    import queue
    from html.parser import HTMLParser
    import html.entities as htmlentitydefs

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

# For converting & <-> &amp; etc.
from cgi import escape
unescape = HTMLParser().unescape

try:
    from collections import ChainMap
except ImportError:
    from collections import MutableMapping

    try:
        from reprlib import recursive_repr as _recursive_repr
    except ImportError:
        def _recursive_repr(fillvalue='...'):
            '''
            Decorator to make a repr function return fillvalue for a recursive
            call
            '''

            def decorating_function(user_function):
                repr_running = set()

                def wrapper(self):
                    key = id(self), get_ident()
                    if key in repr_running:
                        return fillvalue
                    repr_running.add(key)
                    try:
                        result = user_function(self)
                    finally:
                        repr_running.discard(key)
                    return result

                # Can't use functools.wraps() here because of bootstrap issues
                wrapper.__module__ = getattr(user_function, '__module__')
                wrapper.__doc__ = getattr(user_function, '__doc__')
                wrapper.__name__ = getattr(user_function, '__name__')
                wrapper.__annotations__ = getattr(user_function, '__annotations__', {})
                return wrapper

            return decorating_function

    class ChainMap(MutableMapping):
        ''' A ChainMap groups multiple dicts (or other mappings) together
        to create a single, updateable view.

        The underlying mappings are stored in a list.  That list is public and can
        accessed or updated using the *maps* attribute.  There is no other state.

        Lookups search the underlying mappings successively until a key is found.
        In contrast, writes, updates, and deletions only operate on the first
        mapping.

        '''

        def __init__(self, *maps):
            '''Initialize a ChainMap by setting *maps* to the given mappings.
            If no mappings are provided, a single empty dictionary is used.

            '''
            self.maps = list(maps) or [{}]          # always at least one map

        def __missing__(self, key):
            raise KeyError(key)

        def __getitem__(self, key):
            for mapping in self.maps:
                try:
                    return mapping[key]             # can't use 'key in mapping' with defaultdict
                except KeyError:
                    pass
            return self.__missing__(key)            # support subclasses that define __missing__

        def get(self, key, default=None):
            return self[key] if key in self else default

        def __len__(self):
            return len(set().union(*self.maps))     # reuses stored hash values if possible

        def __iter__(self):
            return iter(set().union(*self.maps))

        def __contains__(self, key):
            return any(key in m for m in self.maps)

        def __bool__(self):
            return any(self.maps)

        @_recursive_repr()
        def __repr__(self):
            return '{0.__class__.__name__}({1})'.format(
                self, ', '.join(map(repr, self.maps)))

        @classmethod
        def fromkeys(cls, iterable, *args):
            'Create a ChainMap with a single dict created from the iterable.'
            return cls(dict.fromkeys(iterable, *args))

        def copy(self):
            'New ChainMap or subclass with a new copy of maps[0] and refs to maps[1:]'
            return self.__class__(self.maps[0].copy(), *self.maps[1:])

        __copy__ = copy

        def new_child(self):                        # like Django's Context.push()
            'New ChainMap with a new dict followed by all previous maps.'
            return self.__class__({}, *self.maps)

        @property
        def parents(self):                          # like Django's Context.pop()
            'New ChainMap from maps[1:].'
            return self.__class__(*self.maps[1:])

        def __setitem__(self, key, value):
            self.maps[0][key] = value

        def __delitem__(self, key):
            try:
                del self.maps[0][key]
            except KeyError:
                raise KeyError('Key not found in the first mapping: {!r}'.format(key))

        def popitem(self):
            'Remove and return an item pair from maps[0]. Raise KeyError is maps[0] is empty.'
            try:
                return self.maps[0].popitem()
            except KeyError:
                raise KeyError('No keys found in the first mapping.')

        def pop(self, key, *args):
            'Remove *key* from maps[0] and return its value. Raise KeyError if *key* not in maps[0].'
            try:
                return self.maps[0].pop(key, *args)
            except KeyError:
                raise KeyError('Key not found in the first mapping: {!r}'.format(key))

        def clear(self):
            'Clear maps[0], leaving maps[1:] intact.'
            self.maps[0].clear()

try:
    from imp import cache_from_source
except ImportError:
    def cache_from_source(path, debug_override=None):
        assert path.endswith('.py')
        if debug_override is None:
            debug_override = __debug__
        if debug_override:
            suffix = 'c'
        else:
            suffix = 'o'
        return path + suffix
