# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 The Python Software Foundation.
# See LICENSE.txt and CONTRIBUTORS.txt.
#
"""PEP 376 implementation."""

from __future__ import unicode_literals

import os
import codecs
import csv
import hashlib
import logging
import sys
import zipimport

from . import DistlibException
from .compat import StringIO, configparser
from .version import get_scheme, UnsupportedVersionError
from .metadata import Metadata
from .util import parse_requires, cached_property, get_export_entry


__all__ = ['Distribution', 'BaseInstalledDistribution',
           'InstalledDistribution', 'EggInfoDistribution',
           'DistributionPath']


logger = logging.getLogger(__name__)

# TODO update docs

DIST_FILES = ('INSTALLER', 'METADATA', 'RECORD', 'REQUESTED', 'RESOURCES',
              'EXPORTS')

DISTINFO_EXT = '.dist-info'

class _Cache(object):
    def __init__(self):
        self.name = {}
        self.path = {}
        self.generated = False

    def clear(self):
        self.name.clear()
        self.path.clear()
        self.generated = False

    def add(self, dist):
        if dist.path not in self.path:
            self.path[dist.path] = dist
            self.name.setdefault(dist.name, []).append(dist)

class DistributionPath(object):
    """
    Represents a set of distributions installed on a path (typically sys.path).
    """
    def __init__(self, path=None, include_egg=False):
        if path is None:
            path = sys.path
        self.path = path
        self._include_dist = True
        self._include_egg = include_egg

        self._cache = _Cache()
        self._cache_egg = _Cache()
        self._cache_enabled = True
        self._scheme = get_scheme('default')

    def enable_cache(self):
        """
        Enables the internal cache.

        Note that this function will not clear the cache in any case, for that
        functionality see :meth:`clear_cache`.
        """
        self._cache_enabled = True

    def disable_cache(self):
        """
        Disables the internal cache.

        Note that this function will not clear the cache in any case, for that
        functionality see :meth:`clear_cache`.
        """
        self._cache_enabled = False


    def clear_cache(self):
        """ Clears the internal cache. """
        self._cache.clear()
        self._cache_egg.clear()


    def _yield_distributions(self):
        """
        Yield .dist-info and/or .egg(-info) distributions
        """
        for path in self.path:
            realpath = os.path.realpath(path)
            if not os.path.isdir(realpath):
                continue
            for dir in os.listdir(realpath):
                dist_path = os.path.join(realpath, dir)
                if self._include_dist and dir.endswith(DISTINFO_EXT):
                    yield InstalledDistribution(dist_path, self)
                elif self._include_egg and dir.endswith(('.egg-info',
                                                         '.egg')):
                    yield EggInfoDistribution(dist_path, self)

    def _generate_cache(self):
        gen_dist = not self._cache.generated
        gen_egg = self._include_egg and not self._cache_egg.generated
        if gen_dist or gen_egg:
            for dist in self._yield_distributions():
                if isinstance(dist, InstalledDistribution):
                    self._cache.add(dist)
                else:
                    self._cache_egg.add(dist)

            if gen_dist:
                self._cache.generated = True
            if gen_egg:
                self._cache_egg.generated = True

    @classmethod
    def distinfo_dirname(self, name, version):
        """
        The *name* and *version* parameters are converted into their
        filename-escaped form, i.e. any ``'-'`` characters are replaced
        with ``'_'`` other than the one in ``'dist-info'`` and the one
        separating the name from the version number.

        :parameter name: is converted to a standard distribution name by replacing
                         any runs of non- alphanumeric characters with a single
                         ``'-'``.
        :type name: string
        :parameter version: is converted to a standard version string. Spaces
                            become dots, and all other non-alphanumeric characters
                            (except dots) become dashes, with runs of multiple
                            dashes condensed to a single dash.
        :type version: string
        :returns: directory name
        :rtype: string"""
        name = name.replace('-', '_')
        return '-'.join([name, version]) + DISTINFO_EXT


    def get_distributions(self):
        """
        Provides an iterator that looks for ``.dist-info`` directories
        and returns :class:`InstalledDistribution` or
        :class:`EggInfoDistribution` instances for each one of them.

        :rtype: iterator of :class:`InstalledDistribution` and
                :class:`EggInfoDistribution` instances
        """
        if not self._cache_enabled:
            for dist in _yield_distributions(self):
                yield dist
        else:
            self._generate_cache()

            for dist in self._cache.path.values():
                yield dist

            if self._include_egg:
                for dist in self._cache_egg.path.values():
                    yield dist


    def get_distribution(self, name):
        """
        Scans all distributions looking for a matching name.

        This function only returns the first result found, as no more than one
        value is expected. If nothing is found, ``None`` is returned.

        :rtype: :class:`InstalledDistribution` or :class:`EggInfoDistribution`
                or ``None``
        """
        result = None
        if not self._cache_enabled:
            for dist in self._yield_distributions():
                if dist.name == name:
                    result = dist
                    break
        else:
            self._generate_cache()

            if name in self._cache.name:
                result = self._cache.name[name][0]
            elif self._include_egg and name in self._cache_egg.name:
                result = self._cache_egg.name[name][0]
        return result


    def obsoletes_distribution(self, name, version=None):
        """
        Iterates over all distributions to find which distributions obsolete
        *name*.

        If a *version* is provided, it will be used to filter the results.

        :type name: string
        :type version: string
        :parameter name: The name to check for being obsoleted.
        """
        for dist in self.get_distributions():
            obsoleted = (dist.metadata['Obsoletes-Dist'] +
                         dist.metadata['Obsoletes'])
            for obs in obsoleted:
                o_components = obs.split(' ', 1)
                if len(o_components) == 1 or version is None:
                    if name == o_components[0]:
                        yield dist
                        break
                else:
                    try:
                        matcher = self._scheme.matcher(obs)
                    except ValueError:
                        raise DistlibException(
                            'distribution %r has ill-formed obsoletes field: '
                            '%r' % (dist.name, obs))
                    if name == o_components[0] and matcher.match(version):
                        yield dist
                        break


    def provides_distribution(self, name, version=None):
        """
        Iterates over all distributions to find which distributions provide *name*.
        If a *version* is provided, it will be used to filter the results.

        This function only returns the first result found, since no more than
        one values are expected. If the directory is not found, returns ``None``.

        :parameter version: a version specifier that indicates the version
                            required, conforming to the format in ``PEP-345``

        :type name: string
        :type version: string
        """
        matcher = None
        if not version is None:
            try:
                matcher = self._scheme.matcher('%s (%s)' % (name, version))
            except ValueError:
                raise DistlibException('invalid name or version: %r, %r' %
                                      (name, version))

        for dist in self.get_distributions():
            provided = dist.provides

            for p in provided:
                p_components = p.rsplit(' ', 1)
                if len(p_components) == 1 or matcher is None:
                    if name == p_components[0]:
                        yield dist
                        break
                else:
                    p_name, p_ver = p_components
                    if len(p_ver) < 2 or p_ver[0] != '(' or p_ver[-1] != ')':
                        raise DistlibException(
                            'distribution %r has invalid Provides field: %r' %
                            (dist.name, p))
                    p_ver = p_ver[1:-1]  # trim off the parenthesis
                    if p_name == name and matcher.match(p_ver):
                        yield dist
                        break

    def get_file_users(self, path):
        """
        Iterates over all distributions to find out which distributions use
        *path*.

        :parameter path: can be a local absolute path or a relative
                         ``'/'``-separated path.
        :type path: string
        :rtype: iterator of :class:`InstalledDistribution` instances
        """
        for dist in self.get_distributions():
            if dist.uses(path):
                yield dist


    def get_file_path(self, name, relative_path):
        """Return the path to a resource file."""
        dist = self.get_distribution(name)
        if dist is None:
            raise LookupError('no distribution named %r found' % name)
        return dist.get_resource_path(relative_path)

    def get_exported_entries(self, category, name=None):
        for dist in self.get_distributions():
            r = dist.exports
            if category in r:
                d = r[category]
                if name is not None:
                    if name in d:
                        yield d[name]
                else:
                    for v in d.values():
                        yield v

class Distribution(object):
    """
    A base class for distributions, whether installed or from indexes.
    Either way, it must have some metadata, so that's all that's needed
    for construction.
    """

    def __init__(self, metadata):
        self.metadata = metadata
        self.name = metadata.name
        self.version = metadata.version
        self.locator = None
        self.md5_digest = None

    @property
    def download_url(self):
        return self.metadata.download_url

    @cached_property
    def provides(self):
        return set(self.metadata['Provides-Dist'] +
                   self.metadata['Provides'] +
                   ['%s (%s)' % (self.name, self.version)]
                  )

    @property
    def name_and_version(self):
        return '%s (%s)' % (self.name, self.version)

    @cached_property
    def requires(self):
        return set(self.metadata['Requires-Dist'] +
                   self.metadata['Requires'] +
                   self.get_requirements('install'))

    def get_requirements(self, key):
        """
        Get the requirements of a particular type
        ('setup', 'install', 'test')
        """
        result = []
        d = self.metadata.dependencies
        if key in d:
            result = d[key]
        return result

    def __repr__(self):
        if self.download_url:
            suffix = ' [%s]' % self.download_url
        else:
            suffix = ''
        return '<Distribution %s (%s)%s>' % (self.name, self.version, suffix)

    def __eq__(self, other):
        if type(other) is not type(self):
            result = False
        else:
            result = (self.name == other.name and
                      self.version == other.version and
                      self.download_url == other.download_url)
        return result

    def __hash__(self):
        return hash(self.name) + hash(self.version) + hash(self.download_url)


class BaseInstalledDistribution(Distribution):

    hasher = None

    def __init__(self, metadata, path, env=None):
        super(BaseInstalledDistribution, self).__init__(metadata)
        self.path = path
        self.dist_path  = env

    def get_hash(self, data, hasher=None):
        """
        Get the hash of some data, using a particular hash algorithm, if
        specified.

        :param data: The data to be hashed.
        :type data: bytes
        :param hasher: The name of a hash implementation, supported by hashlib,
                       or ``None``. Examples of valid values are ``'sha1'``,
                       ``'sha224'``, ``'sha384'``, '``sha256'``, ``'md5'`` and
                       ``'sha512'``. If no hasher is specified, the ``hasher``
                       attribute of the :class:`InstalledDistribution` instance
                       is used. If the hasher is determined to be ``None``, MD5
                       is used as the hashing algorithm.
        :returns: The hash of the data. If a hasher was explicitly specified,
                  the returned hash will be prefixed with the specified hasher
                  followed by '='.
        :rtype: str
        """
        if hasher is None:
            hasher = self.hasher
        if hasher is None:
            hasher = hashlib.md5
            prefix = ''
        else:
            hasher = getattr(hashlib, hasher)
            prefix = '%s=' % self.hasher
        return '%s%s' % (prefix, hasher(data).hexdigest())

class InstalledDistribution(BaseInstalledDistribution):
    """Created with the *path* of the ``.dist-info`` directory provided to the
    constructor. It reads the metadata contained in ``METADATA`` when it is
    instantiated."""

    requested = False
    """A boolean that indicates whether the ``REQUESTED`` metadata file is
    present (in other words, whether the package was installed by user
    request or it was installed as a dependency)."""

    def __init__(self, path, env=None):
        if env and env._cache_enabled and path in env._cache.path:
            metadata = env._cache.path[path].metadata
        else:
            metadata_path = os.path.join(path, 'METADATA')
            metadata = Metadata(path=metadata_path)

        super(InstalledDistribution, self).__init__(metadata, path, env)

        if env and env._cache_enabled:
            env._cache.add(self)

    def __repr__(self):
        return '<InstalledDistribution %r %s at %r>' % (
            self.name, self.version, self.path)

    def __str__(self):
        return "%s %s" % (self.name, self.version)

    def _get_records(self, local=False):
        results = []
        record = self.open_distinfo_file('RECORD', preserve_newline=True)
        try:
            record_reader = csv.reader(record, delimiter=str(','),
                                       lineterminator=str('\n'))
            for row in record_reader:
                missing = [None for i in range(len(row), 3)]
                path, checksum, size = row + missing
                if local:
                    path = path.replace('/', os.sep)
                    path = os.path.join(sys.prefix, path)
                results.append((path, checksum, size))
        finally:
            record.close()
        return results

    @cached_property
    def exports(self):
        result = {}
        rf = self.get_distinfo_file('EXPORTS')
        if os.path.exists(rf):
            result = self.read_exports(rf)
        return result

    def read_exports(self, filename=None):
        result = {}
        rf = filename or self.get_distinfo_file('EXPORTS')
        if os.path.exists(rf):
            cp = configparser.ConfigParser()
            cp.read(rf)
            for key in cp.sections():
                result[key] = entries = {}
                for name, value in cp.items(key):
                    s = '%s = %s' % (name, value)
                    entry = get_export_entry(s)
                    assert entry is not None
                    entry.dist = self
                    entries[name] = entry
        return result

    def write_exports(self, exports, filename=None):
        rf = filename or self.get_distinfo_file('EXPORTS')
        cp = configparser.ConfigParser()
        for k, v in exports.items():
            # TODO check k, v for valid values
            cp.add_section(k)
            for entry in v.values():
                if entry.suffix is None:
                    s = entry.prefix
                else:
                    s = '%s:%s' % (entry.prefix, entry.suffix)
                if entry.flags:
                    s = '%s [%s]' % (s, ', '.join(entry.flags))
                cp.set(k, entry.name, s)
        with open(rf, 'w') as f:
            cp.write(f)

    def get_resource_path(self, relative_path):
        resources_file = self.open_distinfo_file('RESOURCES',
                preserve_newline=True)
        try:
            resources_reader = csv.reader(resources_file, delimiter=str(','),
                                          lineterminator=str('\n'))
            for relative, destination in resources_reader:
                if relative == relative_path:
                    return destination
        finally:
            resources_file.close()
        raise KeyError(
            'no resource file with relative path %r is installed' %
            relative_path)

    def list_installed_files(self, local=False):
        """
        Iterates over the ``RECORD`` entries and returns a tuple
        ``(path, hash, size)`` for each line. If *local* is ``True``,
        the returned path is transformed into a local absolute path.
        Otherwise the raw value from RECORD is returned.

        A local absolute path is an absolute path in which occurrences of
        ``'/'`` have been replaced by the system separator given by ``os.sep``.

        :parameter local: flag to say if the path should be returned as a local
                          absolute path

        :type local: boolean
        :returns: iterator of (path, hash, size)
        """
        for result in self._get_records(local):
            yield result

    def write_installed_files(self, paths):
        """
        Writes the ``RECORD`` file, using the ``paths`` iterable passed in. Any
        existing ``RECORD`` file is silently overwritten.
        """
        record_path = os.path.join(self.path, 'RECORD')
        logger.info('creating %s', record_path)
        with codecs.open(record_path, 'w', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=str(','),
                                lineterminator=str('\n'),
                                quotechar=str('"'))
            for path in paths:
                if path.endswith(('.pyc', '.pyo')):
                    # do not put size and hash, as in PEP-376
                    writer.writerow((fpath, '', ''))
                else:
                    size = os.path.getsize(path)
                    with open(path, 'rb') as fp:
                        hash = self.get_hash(fp.read())
                    writer.writerow((path, hash, size))

            # add the RECORD file itself
            writer.writerow((record_path, '', ''))

    def check_installed_files(self):
        """
        Checks that the hashes and sizes of the files in ``RECORD`` are
        matched by the files themselves. Returns a (possibly empty) list of
        mismatches. Each entry in the mismatch list will be a tuple consisting
        of the path, 'exists', 'size' or 'hash' according to what didn't match
        (existence is checked first, then size, then hash), the expected
        value and the actual value.
        """
        mismatches = []
        record_path = os.path.join(self.path, 'RECORD')
        for path, hash, size in self.list_installed_files():
            if path == record_path:
                continue
            if not os.path.exists(path):
                mismatches.append((path, 'exists', True, False))
            else:
                actual_size = str(os.path.getsize(path))
                if actual_size != size:
                    mismatches.append((path, 'size', size, actual_size))
                else:
                    with open(path, 'rb') as f:
                        actual_hash = self.get_hash(f.read())
                        if actual_hash != hash:
                            mismatches.append((path, 'hash', hash, actual_hash))
        return mismatches

    def uses(self, path):
        """
        Returns ``True`` if path is listed in ``RECORD``. *path* can be a local
        absolute path or a relative ``'/'``-separated path.

        :rtype: boolean
        """
        for p, checksum, size in self._get_records():
            local_absolute = os.path.join(sys.prefix, p)
            if path == p or path == local_absolute:
                return True
        return False

    def get_distinfo_file(self, path):
        """
        Returns a path located under the ``.dist-info`` directory. Returns a
        string representing the path.

        :parameter path: a ``'/'``-separated path relative to the
                         ``.dist-info`` directory or an absolute path;
                         If *path* is an absolute path and doesn't start
                         with the ``.dist-info`` directory path,
                         a :class:`DistlibException` is raised
        :type path: string
        :rtype: str
        """
        # Check if it is an absolute path  # XXX use relpath, add tests
        if path.find(os.sep) >= 0:
            # it's an absolute path?
            distinfo_dirname, path = path.split(os.sep)[-2:]
            if distinfo_dirname != self.path.split(os.sep)[-1]:
                raise DistlibException(
                    'dist-info file %r does not belong to the %r %s '
                    'distribution' % (path, self.name, self.version))

        # The file must be relative
        if path not in DIST_FILES:
            raise DistlibException('invalid path for a dist-info file: %r' %
                                  path)

        return os.path.join(self.path, path)

    def open_distinfo_file(self, path, binary=False, preserve_newline=False):
        """
        Returns a file located under the ``.dist-info`` directory. Returns a
        ``file`` instance for the file pointed by *path*.

        :parameter path: a ``'/'``-separated path relative to the
                         ``.dist-info`` directory or an absolute path;
                         If *path* is an absolute path and doesn't start
                         with the ``.dist-info`` directory path,
                         a :class:`DistlibException` is raised
        :type path: string
        :parameter binary: If *binary* is ``True``, opens the file in read-only
                           binary mode (``rb``), otherwise opens it in
                           read-only mode (``r``).
        :parameter preserve_newline: If *preserve_newline* is ``True``, opens
                                     the file with no newline translation
                                     (``newline=''`` in Python 3, binary mode
                                     in Python 2). In Python 3, this differs
                                     from binary mode in that the reading the
                                     file still returns strings, not bytes.
        :rtype: file object
        """
        # XXX: There is no way to specify the file encoding. As RECORD is
        # written in UTF8 (see write_installed_files) and that isn't the
        # default on Windows, there is the potential for bugs here with
        # Unicode filenames.
        path = self.get_distinfo_file(path)
        open_flags = 'r'

        nl_arg = {}
        if preserve_newline:
            if sys.version_info[0] < 3:
                binary = True
            else:
                nl_arg = {'newline': ''}

        if binary:
            open_flags += 'b'

        return open(path, open_flags, **nl_arg)

    def list_distinfo_files(self, local=False):
        """
        Iterates over the ``RECORD`` entries and returns paths for each line if
        the path is pointing to a file located in the ``.dist-info`` directory
        or one of its subdirectories.

        :parameter local: If *local* is ``True``, each returned path is
                          transformed into a local absolute path. Otherwise the
                          raw value from ``RECORD`` is returned.
        :type local: boolean
        :returns: iterator of paths
        """
        for path, checksum, size in self._get_records(local):
            # XXX add separator or use real relpath algo
            if path.startswith(self.path):
                yield path

    def __eq__(self, other):
        return (isinstance(other, InstalledDistribution) and
                self.path == other.path)

    # See http://docs.python.org/reference/datamodel#object.__hash__
    __hash__ = object.__hash__


class EggInfoDistribution(BaseInstalledDistribution):
    """Created with the *path* of the ``.egg-info`` directory or file provided
    to the constructor. It reads the metadata contained in the file itself, or
    if the given path happens to be a directory, the metadata is read from the
    file ``PKG-INFO`` under that directory."""

    def __init__(self, path, env=None):
        self.path = path
        self.dist_path  = env
        if env and env._cache_enabled and path in env._cache_egg.path:
            metadata = env._cache_egg.path[path].metadata
            self.name = metadata['Name']
            self.version = metadata['Version']
        else:
            metadata = self._get_metadata(path)

            # Need to be set before caching
            self.name = metadata['Name']
            self.version = metadata['Version']

            if env and env._cache_enabled:
                env._cache_egg.add(self)

        super(EggInfoDistribution, self).__init__(metadata, path, env)

    def _get_metadata(self, path):
        requires = None

        if path.endswith('.egg'):
            if os.path.isdir(path):
                meta_path = os.path.join(path, 'EGG-INFO', 'PKG-INFO')
                metadata = Metadata(path=meta_path)
                req_path = os.path.join(path, 'EGG-INFO', 'requires.txt')
                requires = parse_requires(req_path)
            else:
                # FIXME handle the case where zipfile is not available
                zipf = zipimport.zipimporter(path)
                fileobj = StringIO(
                    zipf.get_data('EGG-INFO/PKG-INFO').decode('utf8'))
                metadata = Metadata(fileobj=fileobj)
                try:
                    requires = zipf.get_data('EGG-INFO/requires.txt')
                except IOError:
                    requires = None
        elif path.endswith('.egg-info'):
            if os.path.isdir(path):
                path = os.path.join(path, 'PKG-INFO')
                req_path = os.path.join(path, 'requires.txt')
                requires = parse_requires(req_path)
            metadata = Metadata(path=path)
        else:
            raise ValueError('path must end with .egg-info or .egg, got %r' %
                             path)

        if requires:
            if metadata['Metadata-Version'] == '1.1':
                # we can't have 1.1 metadata *and* Setuptools requires
                for field in ('Obsoletes', 'Requires', 'Provides'):
                    if field in metadata:
                        del metadata[field]
            metadata['Requires-Dist'] += requires
        return metadata

    def __repr__(self):
        return '<EggInfoDistribution %r %s at %r>' % (
            self.name, self.version, self.path)

    def __str__(self):
        return "%s %s" % (self.name, self.version)

    def check_installed_files(self):
        """
        Checks that the hashes and sizes of the files in ``RECORD`` are
        matched by the files themselves. Returns a (possibly empty) list of
        mismatches. Each entry in the mismatch list will be a tuple consisting
        of the path, 'exists', 'size' or 'hash' according to what didn't match
        (existence is checked first, then size, then hash), the expected
        value and the actual value.
        """
        mismatches = []
        record_path = os.path.join(self.path, 'installed-files.txt')
        if os.path.exists(record_path):
            for path, hash, size in self.list_installed_files():
                if path == record_path:
                    continue
                if not os.path.exists(path):
                    mismatches.append((path, 'exists', True, False))
        return mismatches

    def list_installed_files(self, local=False):

        def _md5(path):
            f = open(path, 'rb')
            try:
                content = f.read()
            finally:
                f.close()
            return hashlib.md5(content).hexdigest()

        def _size(path):
            return os.stat(path).st_size

        path = self.path
        if local:
            path = path.replace('/', os.sep)

        # XXX What about scripts and data files ?
        if os.path.isfile(path):
            result = [(path, _md5(path), _size(path))]
        else:
            result = []
            for root, dir, files in os.walk(path):
                for item in files:
                    item = os.path.join(root, item)
                    result.append((item, _md5(item), _size(item)))
        return result

    def uses(self, path):
        return False

    def __eq__(self, other):
        return (isinstance(other, EggInfoDistribution) and
                self.path == other.path)

    # See http://docs.python.org/reference/datamodel#object.__hash__
    __hash__ = object.__hash__

class DependencyGraph(object):
    """
    Represents a dependency graph between distributions.

    The dependency relationships are stored in an ``adjacency_list`` that maps
    distributions to a list of ``(other, label)`` tuples where  ``other``
    is a distribution and the edge is labeled with ``label`` (i.e. the version
    specifier, if such was provided). Also, for more efficient traversal, for
    every distribution ``x``, a list of predecessors is kept in
    ``reverse_list[x]``. An edge from distribution ``a`` to
    distribution ``b`` means that ``a`` depends on ``b``. If any missing
    dependencies are found, they are stored in ``missing``, which is a
    dictionary that maps distributions to a list of requirements that were not
    provided by any other distributions.
    """

    def __init__(self):
        self.adjacency_list = {}
        self.reverse_list = {}
        self.missing = {}

    def add_distribution(self, distribution):
        """Add the *distribution* to the graph.

        :type distribution: :class:`distutils2.database.InstalledDistribution`
                            or :class:`distutils2.database.EggInfoDistribution`
        """
        self.adjacency_list[distribution] = []
        self.reverse_list[distribution] = []
        #self.missing[distribution] = []

    def add_edge(self, x, y, label=None):
        """Add an edge from distribution *x* to distribution *y* with the given
        *label*.

        :type x: :class:`distutils2.database.InstalledDistribution` or
                 :class:`distutils2.database.EggInfoDistribution`
        :type y: :class:`distutils2.database.InstalledDistribution` or
                 :class:`distutils2.database.EggInfoDistribution`
        :type label: ``str`` or ``None``
        """
        self.adjacency_list[x].append((y, label))
        # multiple edges are allowed, so be careful
        if x not in self.reverse_list[y]:
            self.reverse_list[y].append(x)

    def add_missing(self, distribution, requirement):
        """
        Add a missing *requirement* for the given *distribution*.

        :type distribution: :class:`distutils2.database.InstalledDistribution`
                            or :class:`distutils2.database.EggInfoDistribution`
        :type requirement: ``str``
        """
        logger.debug('%s missing %r', distribution, requirement)
        self.missing.setdefault(distribution, []).append(requirement)

    def _repr_dist(self, dist):
        return '%s %s' % (dist.name, dist.version)

    def repr_node(self, dist, level=1):
        """Prints only a subgraph"""
        output = []
        output.append(self._repr_dist(dist))
        for other, label in self.adjacency_list[dist]:
            dist = self._repr_dist(other)
            if label is not None:
                dist = '%s [%s]' % (dist, label)
            output.append('    ' * level + str(dist))
            suboutput = self.repr_node(other, level + 1)
            subs = suboutput.split('\n')
            output.extend(subs[1:])
        return '\n'.join(output)

    def to_dot(self, f, skip_disconnected=True):
        """Writes a DOT output for the graph to the provided file *f*.

        If *skip_disconnected* is set to ``True``, then all distributions
        that are not dependent on any other distribution are skipped.

        :type f: has to support ``file``-like operations
        :type skip_disconnected: ``bool``
        """
        disconnected = []

        f.write("digraph dependencies {\n")
        for dist, adjs in self.adjacency_list.items():
            if len(adjs) == 0 and not skip_disconnected:
                disconnected.append(dist)
            for other, label in adjs:
                if not label is None:
                    f.write('"%s" -> "%s" [label="%s"]\n' %
                                                (dist.name, other.name, label))
                else:
                    f.write('"%s" -> "%s"\n' % (dist.name, other.name))
        if not skip_disconnected and len(disconnected) > 0:
            f.write('subgraph disconnected {\n')
            f.write('label = "Disconnected"\n')
            f.write('bgcolor = red\n')

            for dist in disconnected:
                f.write('"%s"' % dist.name)
                f.write('\n')
            f.write('}\n')
        f.write('}\n')

    def topological_sort(self):
        result = []
        # Make a shallow copy of the adjacency list
        alist = {}
        for k, v in self.adjacency_list.items():
            alist[k] = v[:]
        while True:
            # See what we can remove in this run
            to_remove = []
            for k, v in list(alist.items())[:]:
                if not v:
                    to_remove.append(k)
                    del alist[k]
            if not to_remove:
                # What's left in alist (if anything) is a cycle.
                break
            # Remove from the adjacency list of others
            for k, v in alist.items():
                alist[k] = [(d, r) for d, r in v if d not in to_remove]
            logger.debug('Moving to result: %s',
                ['%s (%s)' % (d.name, d.version) for d in to_remove])
            result.extend(to_remove)
        return result, list(alist.keys())

    def __repr__(self):
        """Representation of the graph"""
        output = []
        for dist, adjs in self.adjacency_list.items():
            output.append(self.repr_node(dist))
        return '\n'.join(output)


def make_graph(dists, scheme='default'):
    """Makes a dependency graph from the given distributions.

    :parameter dists: a list of distributions
    :type dists: list of :class:`distutils2.database.InstalledDistribution` and
                 :class:`distutils2.database.EggInfoDistribution` instances
    :rtype: a :class:`DependencyGraph` instance
    """
    scheme = get_scheme(scheme)
    graph = DependencyGraph()
    provided = {}  # maps names to lists of (version, dist) tuples

    # first, build the graph and find out what's provided
    for dist in dists:
        graph.add_distribution(dist)

        for p in dist.provides:
            comps = p.strip().rsplit(" ", 1)
            name = comps[0]
            version = None
            if len(comps) == 2:
                version = comps[1]
                if len(version) < 3 or version[0] != '(' or version[-1] != ')':
                    logger.warning('distribution %r has ill-formed '
                                   'provides field: %r', dist.name, p)
                    continue
                    # don't raise an exception. Legacy installed distributions
                    # could have all manner of metadata
                    #raise DistlibException('distribution %r has ill-formed '
                    #                       'provides field: %r' % (dist.name, p))
                version = version[1:-1]  # trim off parenthesis
            # Add name in lower case for case-insensitivity
            name = name.lower()
            logger.debug('Add to provided: %s, %s, %s', name, version, dist)
            provided.setdefault(name, []).append((version, dist))

    # now make the edges
    for dist in dists:
        # need to leave this in because tests currently rely on it ...
        requires = dist.metadata['Requires-Dist'] + dist.metadata['Requires']
        if not requires:
            requires = dist.get_requirements('install')
        for req in requires:
            try:
                matcher = scheme.matcher(req)
            except UnsupportedVersionError:
                # XXX compat-mode if cannot read the version
                name = req.split()[0]
                matcher = scheme.matcher(name)

            name = matcher.name.lower()   # case-insensitive

            matched = False
            if name in provided:
                for version, provider in provided[name]:
                    try:
                        match = matcher.match(version)
                    except UnsupportedVersionError:
                        match = False

                    if match:
                        graph.add_edge(dist, provider, req)
                        matched = True
                        break
            if not matched:
                graph.add_missing(dist, req)
    return graph


def get_dependent_dists(dists, dist):
    """Recursively generate a list of distributions from *dists* that are
    dependent on *dist*.

    :param dists: a list of distributions
    :param dist: a distribution, member of *dists* for which we are interested
    """
    if dist not in dists:
        raise ValueError('given distribution %r is not a member of the list' %
                         dist.name)
    graph = make_graph(dists)

    dep = [dist]  # dependent distributions
    todo = graph.reverse_list[dist]  # list of nodes we should inspect

    while todo:
        d = todo.pop()
        dep.append(d)
        for succ in graph.reverse_list[d]:
            if succ not in dep:
                todo.append(succ)

    dep.pop(0)  # remove dist from dep, was there to prevent infinite loops
    return dep

def get_required_dists(dists, dist):
    """Recursively generate a list of distributions from *dists* that are
    required by *dist*.

    :param dists: a list of distributions
    :param dist: a distribution, member of *dists* for which we are interested
    """
    if dist not in dists:
        raise ValueError('given distribution %r is not a member of the list' %
                         dist.name)
    graph = make_graph(dists)

    req = []  # required distributions
    todo = graph.adjacency_list[dist]  # list of nodes we should inspect

    while todo:
        d = todo.pop()[0]
        req.append(d)
        for pred in graph.adjacency_list[d]:
            if pred not in req:
                todo.append(pred)

    return req

if __name__ == '__main__':
    def main():
        from .database import DistributionPath
        tempout = StringIO()
        try:
            old = sys.stderr
            sys.stderr = tempout
            try:
                d = DistributionPath(include_egg=True)
                dists = list(d.get_distributions())
                graph = make_graph(dists)
            finally:
                sys.stderr = old
        except Exception as e:
            tempout.seek(0)
            tempout = tempout.read()
            print('Could not generate the graph')
            print(tempout)
            print(e)
            sys.exit(1)

        for dist, reqs in graph.missing.items():
            if len(reqs) > 0:
                print('Warning: Missing dependencies for %r:' % dist.name, \
                      ', '.join(reqs))
        # XXX replace with argparse
        if len(sys.argv) == 1:
            print('Dependency graph:')
            print('   %s' % repr(graph).replace('\n', '\n    '))
            sys.exit(0)
        elif len(sys.argv) > 1 and sys.argv[1] in ('-d', '--dot'):
            if len(sys.argv) > 2:
                filename = sys.argv[2]
            else:
                filename = 'depgraph.dot'

            f = open(filename, 'w')
            try:
                graph_to_dot(graph, f, True)
            finally:
                f.close()
            tempout.seek(0)
            tempout = tempout.read()
            print(tempout)
            print('Dot file written at %r' % filename)
            sys.exit(0)
        else:
            print('Supported option: -d [filename]')
            sys.exit(1)

    main()
