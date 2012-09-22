import contextlib
import logging
import os
import re

from distlib.compat import string_types
from distlib.glob import iglob

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

