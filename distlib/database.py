# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 The Python Software Foundation.
# See LICENSE.txt and CONTRIBUTORS.txt.
#
"""PEP 376 implementation."""

import os
import codecs
import csv
import hashlib
import logging
import sys
import zipimport

from . import DistlibException
from .compat import StringIO
from .version import suggest_normalized_version, VersionPredicate
from .metadata import Metadata
from .util import parse_requires


__all__ = ['Distribution', 'EggInfoDistribution', 'DistributionSet']


logger = logging.getLogger(__name__)

# TODO update docs

DIST_FILES = ('INSTALLER', 'METADATA', 'RECORD', 'REQUESTED', 'RESOURCES')

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

class DistributionSet(object):
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
                    yield Distribution(dist_path, self)
                elif self._include_egg and dir.endswith(('.egg-info',
                                                         '.egg')):
                    yield EggInfoDistribution(dist_path, self)

    def _generate_cache(self):
        gen_dist = not self._cache.generated
        gen_egg = self._include_egg and not self._cache_egg.generated
        if gen_dist or gen_egg:
            for dist in self._yield_distributions():
                if isinstance(dist, Distribution):
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
        normalized_version = suggest_normalized_version(version)
        # Because this is a lookup procedure, something will be returned even if
        #   it is a version that cannot be normalized
        if normalized_version is None:
            # Unable to achieve normality?
            normalized_version = version
        return '-'.join([name, normalized_version]) + DISTINFO_EXT


    def get_distributions(self):
        """
        Provides an iterator that looks for ``.dist-info`` directories
        and returns :class:`Distribution` or :class:`EggInfoDistribution`
        instances for each one of them.

        :rtype: iterator of :class:`Distribution` and :class:`EggInfoDistribution`
                instances
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

        :rtype: :class:`Distribution` or :class:`EggInfoDistribution` or None
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
                        predicate = VersionPredicate(obs)
                    except ValueError:
                        raise DistlibException(
                            'distribution %r has ill-formed obsoletes field: '
                            '%r' % (dist.name, obs))
                    if name == o_components[0] and predicate.match(version):
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
        predicate = None
        if not version is None:
            try:
                predicate = VersionPredicate(name + ' (' + version + ')')
            except ValueError:
                raise DistlibException('invalid name or version: %r, %r' %
                                      (name, version))

        for dist in self.get_distributions():
            provided = dist.metadata['Provides-Dist'] + dist.metadata['Provides']

            for p in provided:
                p_components = p.rsplit(' ', 1)
                if len(p_components) == 1 or predicate is None:
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
                    if p_name == name and predicate.match(p_ver):
                        yield dist
                        break

    def get_file_users(self, path):
        """
        Iterates over all distributions to find out which distributions use
        *path*.

        :parameter path: can be a local absolute path or a relative
                         ``'/'``-separated path.
        :type path: string
        :rtype: iterator of :class:`Distribution` instances
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

class Distribution(object):
    """Created with the *path* of the ``.dist-info`` directory provided to the
    constructor. It reads the metadata contained in ``METADATA`` when it is
    instantiated."""

    name = ''
    """The name of the distribution."""

    version = ''
    """The version of the distribution."""

    metadata = None
    """A :class:`distutils2.metadata.Metadata` instance loaded with
    the distribution's ``METADATA`` file."""

    requested = False
    """A boolean that indicates whether the ``REQUESTED`` metadata file is
    present (in other words, whether the package was installed by user
    request or it was installed as a dependency)."""

    hasher = None

    def __init__(self, path, env=None):
        if env and env._cache_enabled and path in env._cache.path:
            self.metadata = env._cache.path[path].metadata
        else:
            metadata_path = os.path.join(path, 'METADATA')
            self.metadata = Metadata(path=metadata_path)

        self.name = self.metadata['Name']
        self.version = self.metadata['Version']
        self.path = path

        if env and env._cache_enabled:
            env._cache.add(self)

    def __repr__(self):
        return '<Distribution %r %s at %r>' % (
            self.name, self.version, self.path)

    def __str__(self):
        return "%s %s" % (self.name, self.version)

    def _get_records(self, local=False):
        results = []
        record = self.get_distinfo_file('RECORD', preserve_newline=True)
        try:
            record_reader = csv.reader(record, delimiter=',',
                                       lineterminator='\n')
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

    def get_resource_path(self, relative_path):
        resources_file = self.get_distinfo_file('RESOURCES',
                preserve_newline=True)
        try:
            resources_reader = csv.reader(resources_file, delimiter=',',
                                          lineterminator='\n')
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
                       attribute of the :class:`Distribution` instance is used.
                       If the hasher is determined to be ``None``, MD5 is used
                       as the hashing algorithm.
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

    def write_installed_files(self, paths):
        """
        Writes the ``RECORD`` file, using the ``paths`` iterable passed in. Any
        existing ``RECORD`` file is silently overwritten.
        """
        record_path = os.path.join(self.path, 'RECORD')
        logger.info('creating %s', record_path)
        with codecs.open(record_path, 'w', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=',',
                                lineterminator='\n',
                                quotechar='"')
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

    def get_distinfo_file(self, path, binary=False, preserve_newline=False):
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
        open_flags = 'r'

        nl_arg = {}
        if preserve_newline:
            if sys.version_info[0] < 3:
                binary = True
            else:
                nl_arg = {'newline': ''}

        if binary:
            open_flags += 'b'

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

        path = os.path.join(self.path, path)
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
        return isinstance(other, Distribution) and self.path == other.path

    # See http://docs.python.org/reference/datamodel#object.__hash__
    __hash__ = object.__hash__


class EggInfoDistribution(object):
    """Created with the *path* of the ``.egg-info`` directory or file provided
    to the constructor. It reads the metadata contained in the file itself, or
    if the given path happens to be a directory, the metadata is read from the
    file ``PKG-INFO`` under that directory."""

    name = ''
    """The name of the distribution."""

    version = ''
    """The version of the distribution."""

    metadata = None
    """A :class:`distutils2.metadata.Metadata` instance loaded with
    the distribution's ``METADATA`` file."""

    def __init__(self, path, env=None):
        self.path = path
        if env._cache_enabled and path in env._cache_egg.path:
            self.metadata = env._cache_egg.path[path].metadata
            self.name = self.metadata['Name']
            self.version = self.metadata['Version']
            return

        requires = None

        if path.endswith('.egg'):
            if os.path.isdir(path):
                meta_path = os.path.join(path, 'EGG-INFO', 'PKG-INFO')
                self.metadata = Metadata(path=meta_path)
                req_path = os.path.join(path, 'EGG-INFO', 'requires.txt')
                requires = parse_requires(req_path)
            else:
                # FIXME handle the case where zipfile is not available
                zipf = zipimport.zipimporter(path)
                fileobj = StringIO(
                    zipf.get_data('EGG-INFO/PKG-INFO').decode('utf8'))
                self.metadata = Metadata(fileobj=fileobj)
                try:
                    requires = zipf.get_data('EGG-INFO/requires.txt')
                except IOError:
                    requires = None
            self.name = self.metadata['Name']
            self.version = self.metadata['Version']

        elif path.endswith('.egg-info'):
            if os.path.isdir(path):
                path = os.path.join(path, 'PKG-INFO')
                req_path = os.path.join(path, 'requires.txt')
                requires = parse_requires(req_path)
            self.metadata = Metadata(path=path)
            self.name = self.metadata['Name']
            self.version = self.metadata['Version']

        else:
            raise ValueError('path must end with .egg-info or .egg, got %r' %
                             path)

        if requires:
            if self.metadata['Metadata-Version'] == '1.1':
                # we can't have 1.1 metadata *and* Setuptools requires
                for field in ('Obsoletes', 'Requires', 'Provides'):
                    if field in self.metadata:
                        del self.metadata[field]
            self.metadata['Requires-Dist'] += requires

        if env and env._cache_enabled:
            env._cache_egg.add(self)

    def __repr__(self):
        return '<EggInfoDistribution %r %s at %r>' % (
            self.name, self.version, self.path)

    def __str__(self):
        return "%s %s" % (self.name, self.version)

    def list_installed_files(self, local=False):

        def _md5(path):
            f = open(path, 'rb')
            try:
                content = f.read()
            finally:
                f.close()
            return md5(content).hexdigest()

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
