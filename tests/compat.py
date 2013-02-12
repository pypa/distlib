# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 The Python Software Foundation.
# See LICENSE.txt and CONTRIBUTORS.txt.
#
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

if _ver[0] < 3:
    import Queue as queue
    from SimpleXMLRPCServer import SimpleXMLRPCServer
    from SimpleHTTPServer import SimpleHTTPRequestHandler
    from BaseHTTPServer import HTTPServer
    text_type = unicode
    from urllib import unquote
    from urllib2 import Request
    from urlparse import urlparse
else:
    import queue
    from xmlrpc.server import SimpleXMLRPCServer
    from http.server import HTTPServer, SimpleHTTPRequestHandler
    text_type = str
    from urllib.parse import urlparse, unquote
    from urllib.request import Request
