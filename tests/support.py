import codecs
import os
import logging
import logging.handlers
import shutil
import tempfile
import unittest
import weakref

from distlib import logger

class _TestHandler(logging.handlers.BufferingHandler, object):
    # stolen and adapted from test.support

    def __init__(self):
        super(_TestHandler, self).__init__(0)
        self.setLevel(logging.DEBUG)

    def shouldFlush(self):
        return False

    def emit(self, record):
        self.buffer.append(record)

class LoggingCatcher(object):
    """TestCase-compatible mixin to receive logging calls.

    Upon setUp, instances of this classes get a BufferingHandler that's
    configured to record all messages logged to the 'distutils2' logger.

    Use get_logs to retrieve messages and self.loghandler.flush to discard
    them.  get_logs automatically flushes the logs, unless you pass
    *flush=False*, for example to make multiple calls to the method with
    different level arguments.  If your test calls some code that generates
    logging message and then you don't call get_logs, you will need to flush
    manually before testing other code in the same test_* method, otherwise
    get_logs in the next lines will see messages from the previous lines.
    See example in test_command_check.
    """

    def setUp(self):
        super(LoggingCatcher, self).setUp()
        self.loghandler = handler = _TestHandler()
        self._old_level = logger.level
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)  # we want all messages

    def tearDown(self):
        handler = self.loghandler
        # All this is necessary to properly shut down the logging system and
        # avoid a regrtest complaint.  Thanks to Vinay Sajip for the help.
        handler.close()
        logger.removeHandler(handler)
        for ref in weakref.getweakrefs(handler):
            logging._removeHandlerRef(ref)
        del self.loghandler
        logger.setLevel(self._old_level)
        super(LoggingCatcher, self).tearDown()

    def get_logs(self, level=logging.WARNING, flush=True):
        """Return all log messages with given level.

        *level* defaults to logging.WARNING.

        For log calls with arguments (i.e.  logger.info('bla bla %r', arg)),
        the messages will be formatted before being returned (e.g. "bla bla
        'thing'").

        Returns a list.  Automatically flushes the loghandler after being
        called, unless *flush* is False (this is useful to get e.g. all
        warnings then all info messages).
        """
        messages = [log.getMessage() for log in self.loghandler.buffer
                    if log.levelno == level]
        if flush:
            self.loghandler.flush()
        return messages


class TempdirManager(object):
    """TestCase-compatible mixin to create temporary directories and files.

    Directories and files created in a test_* method will be removed after it
    has run.
    """

    def setUp(self):
        super(TempdirManager, self).setUp()
        self._olddir = os.getcwd()
        self._basetempdir = tempfile.mkdtemp()
        self._files = []

    def tearDown(self):
        for handle, name in self._files:
            handle.close()
            unlink(name)

        os.chdir(self._olddir)
        shutil.rmtree(self._basetempdir)
        super(TempdirManager, self).tearDown()

    def mktempfile(self):
        """Create a read-write temporary file and return it."""
        fd, fn = tempfile.mkstemp(dir=self._basetempdir)
        os.close(fd)
        fp = open(fn, 'w+')
        self._files.append((fp, fn))
        return fp

    def mkdtemp(self):
        """Create a temporary directory and return its path."""
        d = tempfile.mkdtemp(dir=self._basetempdir)
        return d

    def write_file(self, path, content='xxx', encoding=None):
        """Write a file at the given path.

        path can be a string, a tuple or a list; if it's a tuple or list,
        os.path.join will be used to produce a path.
        """
        if isinstance(path, (list, tuple)):
            path = os.path.join(*path)
        f = codecs.open(path, 'w', encoding=encoding)
        try:
            f.write(content)
        finally:
            f.close()

    def create_dist(self, **kw):
        """Create a stub distribution object and files.

        This function creates a Distribution instance (use keyword arguments
        to customize it) and a temporary directory with a project structure
        (currently an empty directory).

        It returns the path to the directory and the Distribution instance.
        You can use self.write_file to write any file in that
        directory, e.g. setup scripts or Python modules.
        """
        if 'name' not in kw:
            kw['name'] = 'foo'
        tmp_dir = self.mkdtemp()
        project_dir = os.path.join(tmp_dir, kw['name'])
        os.mkdir(project_dir)
        dist = Distribution(attrs=kw)
        return project_dir, dist

    def assertIsFile(self, *args):
        path = os.path.join(*args)
        dirname = os.path.dirname(path)
        file = os.path.basename(path)
        if os.path.isdir(dirname):
            files = os.listdir(dirname)
            msg = "%s not found in %s: %s" % (file, dirname, files)
            assert os.path.isfile(path), msg
        else:
            raise AssertionError(
                    '%s not found. %s does not exist' % (file, dirname))

    def assertIsNotFile(self, *args):
        path = os.path.join(*args)
        self.assertFalse(os.path.isfile(path), "%r exists" % path)


class EnvironRestorer(object):
    """TestCase-compatible mixin to restore or delete environment variables.

    The variables to restore (or delete if they were not originally present)
    must be explicitly listed in self.restore_environ.  It's better to be
    aware of what we're modifying instead of saving and restoring the whole
    environment.
    """

    def setUp(self):
        super(EnvironRestorer, self).setUp()
        self._saved = []
        self._added = []
        for key in self.restore_environ:
            if key in os.environ:
                self._saved.append((key, os.environ[key]))
            else:
                self._added.append(key)

    def tearDown(self):
        for key, value in self._saved:
            os.environ[key] = value
        for key in self._added:
            os.environ.pop(key, None)
        super(EnvironRestorer, self).tearDown()

try:
    import docutils
except ImportError:
    docutils = None

requires_docutils = unittest.skipUnless(docutils, 'requires docutils')

try:
    import zlib
except ImportError:
    zlib = None

requires_zlib = unittest.skipUnless(docutils, 'requires zlib')

