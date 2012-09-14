import logging

__version__ = '0.1'

class DistlibException(Exception):
    pass

try:
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def handle(self, record): pass
        def emit(self, record): pass

logger = logging.getLogger(__name__)
logger.addHandler(NullHandler())
