# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 The Python Software Foundation.
# See LICENSE.txt and CONTRIBUTORS.txt.
#
import contextlib
import logging
import os
import re
import sys

from . import DistlibException
from .compat import string_types, shutil
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

class cached_property(object):
    def __init__(self, func):
        self.func = func
        #for attr in ('__name__', '__module__', '__doc__'):
        #    setattr(self, attr, getattr(func, attr, None))

    def __get__(self, obj, type=None):
        if obj is None: return self
        obj.__dict__[self.func.__name__] = value = self.func(obj)
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

        Note that this test is not very accurate: files created in the same second
        will have the same "age".
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


class RegistryEntry(object):
    def __init__(self, name, prefix, suffix, flags):
        self.name = name
        self.prefix = prefix
        self.suffix = suffix
        self.flags = flags

    @cached_property
    def value(self):
        return resolve(self.prefix, self.suffix)

    def __repr__(self):
        return '<RegistryEntry %s = %s:%s %s>' % (self.name, self.prefix,
                                                  self.suffix, self.flags)

    def __eq__(self, other):
        if not isinstance(other, RegistryEntry):
            result = False
        else:
            result = (self.name == other.name and
                      self.prefix == other.prefix and
                      self.suffix == other.suffix and
                      self.flags == other.flags)
        return result

    __hash__ = object.__hash__


class Distribution(object):
    """
    A base class for distributions, whether installed or from indexes.
    Either way, it must have some metadata, so that's all that's needed
    for construction.
    """

    def __init__(self, metadata):
        self.metadata = metadata

    @cached_property
    def name(self):
        return self.metadata.name

    @cached_property
    def version(self):
        return self.metadata.version


ENTRY_RE = re.compile(r'''(?P<name>(\w|[-.])+)
                      \s*=\s*(?P<callable>(\w+)([:\.]\w+)*)
                      \s*(\[\s*(?P<flags>\w+(=\w+)?(,\s*\w+(=\w+)?)*)\s*\])?''',
                      re.VERBOSE)

def get_registry_entry(specification):
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
        result = RegistryEntry(name, prefix, suffix, flags)
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
    else:   #assume posix, or old Windows
        result = os.path.expanduser('~')
    result = os.path.join(result, '.distlib')
    # we use 'isdir' instead of 'exists', because we want to
    # fail if there's a file with that name
    if not os.path.isdir(result):
        os.makedirs(result)
    return result
