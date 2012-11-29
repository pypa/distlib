# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 The Python Software Foundation.
# See LICENSE.txt and CONTRIBUTORS.txt.
#
import codecs
from collections import deque
import contextlib
import json
import logging
import os
import re
import socket
import sys

from . import DistlibException
from .compat import string_types, shutil, urlopen
from .glob import iglob

logger = logging.getLogger(__name__)


def parse_requires(req_path):
    """Create a list of dependencies from a requires.txt file.

    *req_path* must be the path to a setuptools-produced requires.txt file.
    """

    # reused from Distribute's pkg_resources
    def yield_lines(strs):
        """Yield non-empty/non-comment lines of a string or sequence"""
        if isinstance(strs, string_types):
            for s in strs.splitlines():
                s = s.strip()
                # skip blank lines/comments
                if s and not s.startswith('#'):
                    yield s
        else:
            for ss in strs:
                for s in yield_lines(ss):
                    yield s

    _REQUIREMENT = re.compile(
        r'(?P<name>[-A-Za-z0-9_.]+)\s*'
        r'(?P<first>(?:<|<=|!=|==|>=|>)[-A-Za-z0-9_.]+)?\s*'
        r'(?P<rest>(?:\s*,\s*(?:<|<=|!=|==|>=|>)[-A-Za-z0-9_.]+)*)\s*'
        r'(?P<extras>\[.*\])?')

    reqs = []
    try:
        with open(req_path, 'r') as fp:
            requires = fp.read()
    except IOError:
        return None

    for line in yield_lines(requires):
        if line.startswith('['):
            logger.warning('extensions in requires.txt are not supported')
            break
        else:
            match = _REQUIREMENT.match(line.strip())
            if not match:
                # this happens when we encounter extras; since they
                # are written at the end of the file we just exit
                break
            else:
                if match.group('extras'):
                    # msg = ('extra requirements are not supported '
                    # '(used by %r %s)', self.name, self.version)
                    msg = 'extra requirements are not supported'
                    logger.warning(msg)
                name = match.group('name')
                version = None
                if match.group('first'):
                    version = match.group('first')
                    if match.group('rest'):
                        version += match.group('rest')
                    version = version.replace(' ', '')  # trim spaces
                if version is None:
                    reqs.append(name)
                else:
                    reqs.append('%s (%s)' % (name, version))
    return reqs


def _rel_path(base, path):
    # normalizes and returns a lstripped-/-separated path
    base = base.replace(os.path.sep, '/')
    path = path.replace(os.path.sep, '/')
    assert path.startswith(base)
    return path[len(base):].lstrip('/')


def get_resources_dests(resources_root, rules):
    """Find destinations for resources files"""
    destinations = {}
    for base, suffix, dest in rules:
        prefix = os.path.join(resources_root, base)
        for abs_base in iglob(prefix):
            abs_glob = os.path.join(abs_base, suffix)
            for abs_path in iglob(abs_glob):
                resource_file = _rel_path(resources_root, abs_path)
                if dest is None:  # remove the entry if it was here
                    destinations.pop(resource_file, None)
                else:
                    rel_path = _rel_path(abs_base, abs_path)
                    rel_dest = dest.replace(os.path.sep, '/').rstrip('/')
                    destinations[resource_file] = rel_dest + '/' + rel_path
    return destinations


@contextlib.contextmanager
def chdir(d):
    cwd = os.getcwd()
    try:
        os.chdir(d)
        yield
    finally:
        os.chdir(cwd)


@contextlib.contextmanager
def socket_timeout(seconds=15):
    cto = socket.getdefaulttimeout()
    try:
        socket.setdefaulttimeout(seconds)
        yield
    finally:
        socket.setdefaulttimeout(cto)


class cached_property(object):
    def __init__(self, func):
        self.func = func
        #for attr in ('__name__', '__module__', '__doc__'):
        #    setattr(self, attr, getattr(func, attr, None))

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        value = self.func(obj)
        object.__setattr__(obj, self.func.__name__, value)
        #obj.__dict__[self.func.__name__] = value = self.func(obj)
        return value


class FileOperator(object):
    def __init__(self, dry_run=False):
        self.dry_run = dry_run

    def convert_path(self, pathname):
        """Return 'pathname' as a name that will work on the native filesystem.

        The path is split on '/' and put back together again using the current
        directory separator.  Needed because filenames in the setup script are
        always supplied in Unix style, and have to be converted to the local
        convention before we can actually use them in the filesystem.  Raises
        ValueError on non-Unix-ish systems if 'pathname' either starts or
        ends with a slash.
        """
        if os.sep == '/':
            return pathname
        if not pathname:
            return pathname
        if pathname[0] == '/':
            raise ValueError("path '%s' cannot be absolute" % pathname)
        if pathname[-1] == '/':
            raise ValueError("path '%s' cannot end with '/'" % pathname)

        paths = pathname.split('/')
        while os.curdir in paths:
            paths.remove(os.curdir)
        if not paths:
            return os.curdir
        return os.path.join(*paths)

    def newer(self, source, target):
        """Tell if the target is newer than the source.

        Returns true if 'source' exists and is more recently modified than
        'target', or if 'source' exists and 'target' doesn't.

        Returns false if both exist and 'target' is the same age or younger
        than 'source'. Raise PackagingFileError if 'source' does not exist.

        Note that this test is not very accurate: files created in the same
        second will have the same "age".
        """
        if not os.path.exists(source):
            raise DistlibException("file '%r' does not exist" %
                                   os.path.abspath(source))
        if not os.path.exists(target):
            return True

        return os.stat(source).st_mtime > os.stat(target).st_mtime

    def copy_file(self, infile, outfile):
        """Copy a file respecting dry-run and force flags.
        """
        if not self.dry_run:
            if os.path.isdir(outfile):
                outfile = os.path.join(outfile, os.path.split(infile)[-1])
            shutil.copyfile(infile, outfile)

    def write_binary_file(self, path, data):
        if not self.dry_run:
            with open(path, 'wb') as f:
                f.write(data)

    def write_text_file(self, path, data, encoding):
        if not self.dry_run:
            with open(path, 'wb') as f:
                f.write(data.encode(encoding))

    def set_mode(self, bits, mask, files):
        if os.name == 'posix':
            # Set the executable bits (owner, group, and world) on
            # all the files specified.
            for f in files:
                if self.dry_run:
                    logger.info("changing mode of %s", f)
                else:
                    mode = (os.stat(f).st_mode | bits) & mask
                    logger.info("changing mode of %s to %o", f, mode)
                    os.chmod(f, mode)

    set_executable_mode = lambda s, f: s.set_mode(0o555, 0o7777, f)


def resolve(module_name, dotted_path):
    if module_name in sys.modules:
        mod = sys.modules[module_name]
    else:
        mod = __import__(module_name)
    if dotted_path is None:
        result = mod
    else:
        parts = dotted_path.split('.')
        result = getattr(mod, parts.pop(0))
        for p in parts:
            result = getattr(result, p)
    return result


class ExportEntry(object):
    def __init__(self, name, prefix, suffix, flags):
        self.name = name
        self.prefix = prefix
        self.suffix = suffix
        self.flags = flags

    @cached_property
    def value(self):
        return resolve(self.prefix, self.suffix)

    def __repr__(self):
        return '<ExportEntry %s = %s:%s %s>' % (self.name, self.prefix,
                                                self.suffix, self.flags)

    def __eq__(self, other):
        if not isinstance(other, ExportEntry):
            result = False
        else:
            result = (self.name == other.name and
                      self.prefix == other.prefix and
                      self.suffix == other.suffix and
                      self.flags == other.flags)
        return result

    __hash__ = object.__hash__


ENTRY_RE = re.compile(r'''(?P<name>(\w|[-.])+)
                      \s*=\s*(?P<callable>(\w+)([:\.]\w+)*)
                      \s*(\[\s*(?P<flags>\w+(=\w+)?(,\s*\w+(=\w+)?)*)\s*\])?
                      ''', re.VERBOSE)


def get_export_entry(specification):
    m = ENTRY_RE.search(specification)
    if not m:
        result = None
        if '[' in specification or ']' in specification:
            raise DistlibException('Invalid specification '
                                   '%r' % specification)
    else:
        d = m.groupdict()
        name = d['name']
        path = d['callable']
        colons = path.count(':')
        if colons == 0:
            prefix, suffix = path, None
        else:
            if colons != 1:
                raise DistlibException('Invalid specification '
                                       '%r' % specification)
            prefix, suffix = path.split(':')
        flags = d['flags']
        if flags is None:
            if '[' in specification or ']' in specification:
                raise DistlibException('Invalid specification '
                                       '%r' % specification)
            flags = []
        else:
            flags = [f.strip() for f in flags.split(',')]
        result = ExportEntry(name, prefix, suffix, flags)
    return result


def get_cache_base():
    """
    Return the default base location for distlib caches. If the directory does
    not exist, it is created.

    On Windows, if LOCALAPPDATA is defined in the environment, then it is
    assumed to be a directory, and will be the parent directory of the result.
    On POSIX, and on Windows if LOCALAPPDATA is not defined, the user's home
    directory - using os.expanduser('~') - will be the parent directory of
    the result.

    The result is just the directory '.distlib' in the parent directory as
    determined above.
    """
    if os.name == 'nt' and 'LOCALAPPDATA' in os.environ:
        result = os.path.expandvars('$localappdata')
    else:
        # Assume posix, or old Windows
        result = os.path.expanduser('~')
    result = os.path.join(result, '.distlib')
    # we use 'isdir' instead of 'exists', because we want to
    # fail if there's a file with that name
    if not os.path.isdir(result):
        os.makedirs(result)
    return result


def path_to_cache_dir(path):
    """
    Convert an absolute path to a directory name for use in a cache.

    The algorithm used is:

    #. On Windows, any ``':'`` in the drive is replaced with ``'---'``.
    #. Any occurrence of ``os.sep`` is replaced with ``'--'``.
    #. ``'.cache'`` is appended.
    """
    d, p = os.path.splitdrive(os.path.abspath(path))
    if d:
        d = d.replace(':', '---')
    p = p.replace(os.sep, '--')
    return d + p + '.cache'


def ensure_slash(s):
    if not s.endswith('/'):
        return s + '/'
    return s


def parse_credentials(netloc):
    username = password = None
    if '@' in netloc:
        prefix, netloc = netloc.split('@', 1)
        if ':' not in prefix:
            username = prefix
        else:
            username, password = prefix.split(':', 1)
    return username, password, netloc


def get_process_umask():
    result = os.umask(0o22)
    os.umask(result)
    return result

PROJECT_NAME_AND_VERSION = re.compile('([a-z0-9_]+([.-][a-z_][a-z0-9_]*)*)-'
                                      '([0-9][a-z0-9_.+-]*)', re.I)
PYTHON_VERSION = re.compile(r'-py(\d\.?\d?)$')


def split_filename(filename, project_name=None):
    """
    Extract name, version, python version from a filename (no extension)

    Return name, version, pyver or None
    """
    result = None
    pyver = None
    m = PYTHON_VERSION.search(filename)
    if m:
        pyver = m.group(1)
        filename = filename[:m.start()]
    if project_name and len(filename) > len(project_name) + 1:
        m = re.match(re.escape(project_name) + r'\b', filename)
        if m:
            n = m.end()
            result = filename[:n], filename[n + 1:], pyver
    if result is None:
        m = PROJECT_NAME_AND_VERSION.match(filename)
        if m:
            result = m.group(1), m.group(3), pyver
    return result


def _get_external_data(url):
    result = {}
    try:
        resp = urlopen(url)
        headers = resp.info()
        if headers.get('Content-Type') != 'application/json':
            logger.debug('Unexpected response for JSON request')
        else:
            reader = codecs.getreader('utf-8')(resp)
            #data = reader.read().decode('utf-8')
            #result = json.loads(data)
            result = json.load(reader)
    except Exception as e:
        logger.exception('Failed to get external data for %s: %s', url, e)
    return result


def get_project_data(name):
    url = ('http://www.red-dove.com/pypi/projects/'
           '%s/%s/project.json' % (name[0].upper(), name))
    result = _get_external_data(url)
    return result

def get_package_data(name, version):
    url = ('http://www.red-dove.com/pypi/projects/'
           '%s/%s/package-%s.json' % (name[0].upper(), name, version))
    result = _get_external_data(url)
    return result

#
# Simple event pub/sub
#

class EventMixin(object):
    """
    A very simple publish/subscribe system.
    """
    def __init__(self):
        self._subscribers = {}

    def add(self, event, subscriber, append=True):
        """
        Add a subscriber for an event.

        :param event: The name of an event.
        :param subscriber: The subscriber to be added (and called when the
                           event is published).
        :param append: Whether to append or prepend the subscriber to an
                       existing subscriber list for the event.
        """
        subs = self._subscribers
        if event not in subs:
            subs[event] = deque([subscriber])
        else:
            sq = subs[event]
            if append:
                sq.append(subscriber)
            else:
                sq.appendleft(subscriber)

    def remove(self, event, subscriber):
        """
        Remove a subscriber for an event.

        :param event: The name of an event.
        :param subscriber: The subscriber to be removed.
        """
        subs = self._subscribers
        if event not in subs:
            raise ValueError('No subscribers: %r' % event)
        subs[event].remove(subscriber)

    def get_subscribers(self, event):
        """
        Return an iterator for the subscribers for an event.
        :param event: The event to return subscribers for.
        """
        return iter(self._subscribers.get(event, ()))

    def publish(self, event, *args, **kwargs):
        """
        Publish a event and return a list of values returned by its
        subscribers.

        :param event: The event to publish.
        :param args: The positional arguments to pass to the event's
                     subscribers.
        :param kwargs: The keyword arguments to pass to the event's
                       subscribers.
        """
        result = []
        for subscriber in self.get_subscribers(event):
            try:
                value = subscriber(event, *args, **kwargs)
            except Exception:
                logger.exception('Exception during event publication')
                value = None
            result.append(value)
        logger.debug('%s: args = %s, kwargs = %s, result = %s',
                     event, args, kwargs, result)
        return result

#
# Simple sequencing
#
class Sequencer(object):
    def __init__(self):
        self._preds = {}
        self._succs = {}

    def add(self, pred, succ):
        assert pred != succ
        self._preds.setdefault(succ, set()).add(pred)
        self._succs.setdefault(pred, set()).add(succ)

    def remove(self, pred, succ):
        assert pred != succ
        try:
            preds = self._preds[succ]
            succs = self._succs[pred]
        except KeyError:
            raise ValueError('%r not a successor of anything' % succ)
        try:
            preds.remove(pred)
            succs.remove(succ)
        except KeyError:
            raise ValueError('%r not a successor of %r' % (succ, pred))

    def get_steps(self, final):
        if final not in self._preds and final not in self._succs:
            raise ValueError('Unknown: %r' % final)
        result = []
        todo = []
        seen = set()
        todo.append(final)
        while todo:
            step = todo.pop(0)
            if step in seen:
                # if a step was already seen,
                # move it to the end (so it will appear earlier
                # when reversed on return) ... but not for the
                # final step, as that would be confusing for
                # users
                if step != final:
                    result.remove(step)
                    result.append(step)
            else:
                seen.add(step)
                result.append(step)
                preds = self._preds.get(step, ())
                todo.extend(preds)
        return reversed(result)

    def strong_connections(self):
        #http://en.wikipedia.org/wiki/Tarjan%27s_strongly_connected_components_algorithm
        index_counter = [0]
        stack = []
        lowlinks = {}
        index = {}
        result = []

        graph = self._succs

        def strongconnect(node):
            # set the depth index for this node to the smallest unused index
            index[node] = index_counter[0]
            lowlinks[node] = index_counter[0]
            index_counter[0] += 1
            stack.append(node)

            # Consider successors
            try:
                successors = graph[node]
            except:
                successors = []
            for successor in successors:
                if successor not in lowlinks:
                    # Successor has not yet been visited
                    strongconnect(successor)
                    lowlinks[node] = min(lowlinks[node],lowlinks[successor])
                elif successor in stack:
                    # the successor is in the stack and hence in the current
                    # strongly connected component (SCC)
                    lowlinks[node] = min(lowlinks[node],index[successor])

            # If `node` is a root node, pop the stack and generate an SCC
            if lowlinks[node] == index[node]:
                connected_component = []

                while True:
                    successor = stack.pop()
                    connected_component.append(successor)
                    if successor == node: break
                component = tuple(connected_component)
                # storing the result
                result.append(component)

        for node in graph:
            if node not in lowlinks:
                strongconnect(node)

        return result

    @property
    def dot(self):
        result = ['digraph G {']
        for succ in self._preds:
            preds = self._preds[succ]
            for pred in preds:
                result.append('  %s -> %s;' % (pred, succ))
        result.append('}')
        return '\n'.join(result)
