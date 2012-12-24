# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 The Python Software Foundation.
# See LICENSE.txt and CONTRIBUTORS.txt.
#
import logging

__version__ = '0.1dev'

class DistlibException(Exception):
    pass

try:
    from logging import NullHandler
except ImportError: # pragma: no cover
    class NullHandler(logging.Handler):
        def handle(self, record): pass
        def emit(self, record): pass

logger = logging.getLogger(__name__)
logger.addHandler(NullHandler())
