# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 The Python Software Foundation.
# See LICENSE.txt and CONTRIBUTORS.txt.
#
"""Implementation of the Metadata for Python packages PEPs.

Supports all metadata formats (1.0, 1.1, 1.2, and 2.0 experimental).
"""
from __future__ import unicode_literals

import codecs
from email import message_from_file
import json
import logging
import re


from . import DistlibException
from .compat import StringIO, string_types
from .markers import interpret
from .util import extract_by_key
from .version import get_scheme

logger = logging.getLogger(__name__)


class MetadataMissingError(DistlibException):
    """A required metadata is missing"""


class MetadataConflictError(DistlibException):
    """Attempt to read or write metadata fields that are conflictual."""


class MetadataUnrecognizedVersionError(DistlibException):
    """Unknown metadata version number."""


try:
    # docutils is installed
    from docutils.utils import Reporter
    from docutils.parsers.rst import Parser
    from docutils import frontend
    from docutils import nodes

    class SilentReporter(Reporter, object):

        def __init__(self, source, report_level, halt_level, stream=None,
                     debug=0, encoding='ascii', error_handler='replace'):
            self.messages = []
            super(SilentReporter, self).__init__(
                source, report_level, halt_level, stream,
                debug, encoding, error_handler)

        def system_message(self, level, message, *children, **kwargs):
            self.messages.append((level, message, children, kwargs))
            return nodes.system_message(message, level=level, type=self.
                                        levels[level], *children, **kwargs)

    _HAS_DOCUTILS = True
except ImportError:
    # docutils is not installed
    _HAS_DOCUTILS = False

# public API of this module
__all__ = ['Metadata', 'PKG_INFO_ENCODING', 'PKG_INFO_PREFERRED_VERSION']

# Encoding used for the PKG-INFO files
PKG_INFO_ENCODING = 'utf-8'

# preferred version. Hopefully will be changed
# to 1.2 once PEP 345 is supported everywhere
PKG_INFO_PREFERRED_VERSION = '1.1'

_LINE_PREFIX = re.compile('\n       \|')
_241_FIELDS = ('Metadata-Version', 'Name', 'Version', 'Platform',
               'Summary', 'Description',
               'Keywords', 'Home-page', 'Author', 'Author-email',
               'License')

_314_FIELDS = ('Metadata-Version', 'Name', 'Version', 'Platform',
               'Supported-Platform', 'Summary', 'Description',
               'Keywords', 'Home-page', 'Author', 'Author-email',
               'License', 'Classifier', 'Download-URL', 'Obsoletes',
               'Provides', 'Requires')

_314_MARKERS = ('Obsoletes', 'Provides', 'Requires', 'Classifier',
                'Download-URL')

_345_FIELDS = ('Metadata-Version', 'Name', 'Version', 'Platform',
               'Supported-Platform', 'Summary', 'Description',
               'Keywords', 'Home-page', 'Author', 'Author-email',
               'Maintainer', 'Maintainer-email', 'License',
               'Classifier', 'Download-URL', 'Obsoletes-Dist',
               'Project-URL', 'Provides-Dist', 'Requires-Dist',
               'Requires-Python', 'Requires-External')

_345_MARKERS = ('Provides-Dist', 'Requires-Dist', 'Requires-Python',
                'Obsoletes-Dist', 'Requires-External', 'Maintainer',
                'Maintainer-email', 'Project-URL')

_426_FIELDS = ('Metadata-Version', 'Name', 'Version', 'Platform',
               'Supported-Platform', 'Summary', 'Description',
               'Keywords', 'Home-page', 'Author', 'Author-email',
               'Maintainer', 'Maintainer-email', 'License',
               'Classifier', 'Download-URL', 'Obsoletes-Dist',
               'Project-URL', 'Provides-Dist', 'Requires-Dist',
               'Requires-Python', 'Requires-External', 'Private-Version',
               'Obsoleted-By', 'Setup-Requires-Dist', 'Extension',
               'Provides-Extra')

_426_MARKERS = ('Private-Version', 'Provides-Extra', 'Obsoleted-By',
                'Setup-Requires-Dist', 'Extension')

_ALL_FIELDS = set()
_ALL_FIELDS.update(_241_FIELDS)
_ALL_FIELDS.update(_314_FIELDS)
_ALL_FIELDS.update(_345_FIELDS)
_ALL_FIELDS.update(_426_FIELDS)

EXTRA_RE = re.compile(r'''extra\s*==\s*("([^"]+)"|'([^']+)')''')


def _version2fieldlist(version):
    if version == '1.0':
        return _241_FIELDS
    elif version == '1.1':
        return _314_FIELDS
    elif version == '1.2':
        return _345_FIELDS
    elif version == '2.0':
        return _426_FIELDS
    raise MetadataUnrecognizedVersionError(version)


def _best_version(fields):
    """Detect the best version depending on the fields used."""
    def _has_marker(keys, markers):
        for marker in markers:
            if marker in keys:
                return True
        return False

    keys = []
    for key, value in fields.items():
        if value in ([], 'UNKNOWN', None):
            continue
        keys.append(key)

    possible_versions = ['1.0', '1.1', '1.2', '2.0']

    # first let's try to see if a field is not part of one of the version
    for key in keys:
        if key not in _241_FIELDS and '1.0' in possible_versions:
            possible_versions.remove('1.0')
        if key not in _314_FIELDS and '1.1' in possible_versions:
            possible_versions.remove('1.1')
        if key not in _345_FIELDS and '1.2' in possible_versions:
            possible_versions.remove('1.2')
        if key not in _426_FIELDS and '2.0' in possible_versions:
            possible_versions.remove('2.0')

    # possible_version contains qualified versions
    if len(possible_versions) == 1:
        return possible_versions[0]   # found !
    elif len(possible_versions) == 0:
        raise MetadataConflictError('Unknown metadata set')

    # let's see if one unique marker is found
    is_1_1 = '1.1' in possible_versions and _has_marker(keys, _314_MARKERS)
    is_1_2 = '1.2' in possible_versions and _has_marker(keys, _345_MARKERS)
    is_2_0 = '2.0' in possible_versions and _has_marker(keys, _426_MARKERS)
    if int(is_1_1) + int(is_1_2) + int(is_2_0) > 1:
        raise MetadataConflictError('You used incompatible 1.1/1.2/2.0 fields')

    # we have the choice, 1.0, or 1.2, or 2.0
    #   - 1.0 has a broken Summary field but works with all tools
    #   - 1.1 is to avoid
    #   - 1.2 fixes Summary but has little adoption
    #   - 2.0 adds more features and is very new
    if not is_1_1 and not is_1_2 and not is_2_0:
        # we couldn't find any specific marker
        if PKG_INFO_PREFERRED_VERSION in possible_versions:
            return PKG_INFO_PREFERRED_VERSION
    if is_1_1:
        return '1.1'
    if is_1_2:
        return '1.2'

    return '2.0'

_ATTR2FIELD = {
    'metadata_version': 'Metadata-Version',
    'name': 'Name',
    'version': 'Version',
    'platform': 'Platform',
    'supported_platform': 'Supported-Platform',
    'summary': 'Summary',
    'description': 'Description',
    'keywords': 'Keywords',
    'home_page': 'Home-page',
    'author': 'Author',
    'author_email': 'Author-email',
    'maintainer': 'Maintainer',
    'maintainer_email': 'Maintainer-email',
    'license': 'License',
    'classifier': 'Classifier',
    'download_url': 'Download-URL',
    'obsoletes_dist': 'Obsoletes-Dist',
    'provides_dist': 'Provides-Dist',
    'requires_dist': 'Requires-Dist',
    'setup_requires_dist': 'Setup-Requires-Dist',
    'requires_python': 'Requires-Python',
    'requires_external': 'Requires-External',
    'requires': 'Requires',
    'provides': 'Provides',
    'obsoletes': 'Obsoletes',
    'project_url': 'Project-URL',
    'private_version': 'Private-Version',
    'obsoleted_by': 'Obsoleted-By',
    'extension': 'Extension',
    'provides_extra': 'Provides-Extra',
}

_PREDICATE_FIELDS = ('Requires-Dist', 'Obsoletes-Dist', 'Provides-Dist')
_VERSIONS_FIELDS = ('Requires-Python',)
_VERSION_FIELDS = ('Version',)
_LISTFIELDS = ('Platform', 'Classifier', 'Obsoletes',
               'Requires', 'Provides', 'Obsoletes-Dist',
               'Provides-Dist', 'Requires-Dist', 'Requires-External',
               'Project-URL', 'Supported-Platform', 'Setup-Requires-Dist',
               'Provides-Extra', 'Extension')
_LISTTUPLEFIELDS = ('Project-URL',)

_ELEMENTSFIELD = ('Keywords',)

_UNICODEFIELDS = ('Author', 'Maintainer', 'Summary', 'Description')

_MISSING = object()

_FILESAFE = re.compile('[^A-Za-z0-9.]+')


def _get_name_and_version(name, version, for_filename=False):
    """Return the distribution name with version.

    If for_filename is true, return a filename-escaped form."""
    if for_filename:
        # For both name and version any runs of non-alphanumeric or '.'
        # characters are replaced with a single '-'.  Additionally any
        # spaces in the version string become '.'
        name = _FILESAFE.sub('-', name)
        version = _FILESAFE.sub('-', version.replace(' ', '.'))
    return '%s-%s' % (name, version)

class LegacyMetadata(object):
    """The legacy metadata of a release.

    Supports versions 1.0, 1.1 and 1.2 (auto-detected). You can
    instantiate the class with one of these arguments (or none):
    - *path*, the path to a metadata file
    - *fileobj* give a file-like object with metadata as content
    - *mapping* is a dict-like object
    - *scheme* is a version scheme name
    """
    # TODO document the mapping API and UNKNOWN default key

    def __init__(self, path=None, fileobj=None, mapping=None,
                 scheme='default'):
        if [path, fileobj, mapping].count(None) < 2:
            raise TypeError('path, fileobj and mapping are exclusive')
        self._fields = {}
        self.requires_files = []
        self.docutils_support = _HAS_DOCUTILS
        self._dependencies = None
        self.scheme = scheme
        if path is not None:
            self.read(path)
        elif fileobj is not None:
            self.read_file(fileobj)
        elif mapping is not None:
            self.update(mapping)
            self.set_metadata_version()

    def set_metadata_version(self):
        self._fields['Metadata-Version'] = _best_version(self._fields)

    def _write_field(self, fileobj, name, value):
        fileobj.write('%s: %s\n' % (name, value))

    def __getitem__(self, name):
        return self.get(name)

    def __setitem__(self, name, value):
        return self.set(name, value)

    def __delitem__(self, name):
        field_name = self._convert_name(name)
        try:
            del self._fields[field_name]
        except KeyError:
            raise KeyError(name)

    def __contains__(self, name):
        return (name in self._fields or
                self._convert_name(name) in self._fields)

    def _convert_name(self, name):
        if name in _ALL_FIELDS:
            return name
        name = name.replace('-', '_').lower()
        return _ATTR2FIELD.get(name, name)

    def _default_value(self, name):
        if name in _LISTFIELDS or name in _ELEMENTSFIELD:
            return []
        return 'UNKNOWN'

    def _check_rst_data(self, data):
        """Return warnings when the provided data has syntax errors."""
        source_path = StringIO()
        parser = Parser()
        settings = frontend.OptionParser().get_default_values()
        settings.tab_width = 4
        settings.pep_references = None
        settings.rfc_references = None
        reporter = SilentReporter(source_path,
                          settings.report_level,
                          settings.halt_level,
                          stream=settings.warning_stream,
                          debug=settings.debug,
                          encoding=settings.error_encoding,
                          error_handler=settings.error_encoding_error_handler)

        document = nodes.document(settings, reporter, source=source_path)
        document.note_source(source_path, -1)
        try:
            parser.parse(data, document)
        except AttributeError:
            reporter.messages.append((-1, 'Could not finish the parsing.',
                                      '', {}))

        return reporter.messages

    def _remove_line_prefix(self, value):
        return _LINE_PREFIX.sub('\n', value)

    def __getattr__(self, name):
        if name in _ATTR2FIELD:
            return self[name]
        raise AttributeError(name)

    def _get_dependencies(self):
        def handle_req(req, rlist, extras):
            if ';' not in req:
                rlist.append(req)
            else:
                r, marker = req.split(';')
                m = EXTRA_RE.search(marker)
                if m:
                    extra = m.groups()[0][1:-1]
                    extras.setdefault(extra, []).append(r)

        result = self._dependencies
        if result is None:
            self._dependencies = result = {}
            extras = {}
            setup_reqs = self['Setup-Requires-Dist']
            if setup_reqs:
                result['setup'] = setup_reqs
            install_reqs = []
            for req in self['Requires-Dist']:
                handle_req(req, install_reqs, extras)
            if install_reqs:
                result['install'] = install_reqs
            if extras:
                result['extras'] = extras
        return result

    def _set_dependencies(self, value):
        if 'test' in value:
            value = dict(value)     # don't change value passed in
            value.setdefault('extras', {})['test'] = value.pop('test')
        self._dependencies = value
        setup_reqs = value.get('setup', [])
        install_reqs = value.get('install', [])
        klist = []
        for k, rlist in value.get('extras', {}).items():
            klist.append(k)
            for r in rlist:
                install_reqs.append('%s; extra == "%s"' % (r, k))
        if setup_reqs:
            self['Setup-Requires-Dist'] = setup_reqs
        if install_reqs:
            self['Requires-Dist'] = install_reqs
        if klist:
            self['Provides-Extra'] = klist
    #
    # Public API
    #

    dependencies = property(_get_dependencies, _set_dependencies)

    def get_fullname(self, filesafe=False):
        """Return the distribution name with version.

        If filesafe is true, return a filename-escaped form."""
        return _get_name_and_version(self['Name'], self['Version'], filesafe)

    def is_field(self, name):
        """return True if name is a valid metadata key"""
        name = self._convert_name(name)
        return name in _ALL_FIELDS

    def is_multi_field(self, name):
        name = self._convert_name(name)
        return name in _LISTFIELDS

    def read(self, filepath):
        """Read the metadata values from a file path."""
        fp = codecs.open(filepath, 'r', encoding='utf-8')
        try:
            self.read_file(fp)
        finally:
            fp.close()

    def read_file(self, fileob):
        """Read the metadata values from a file object."""
        msg = message_from_file(fileob)
        self._fields['Metadata-Version'] = msg['metadata-version']

        # When reading, get all the fields we can
        for field in _ALL_FIELDS:
            if field not in msg:
                continue
            if field in _LISTFIELDS:
                # we can have multiple lines
                values = msg.get_all(field)
                if field in _LISTTUPLEFIELDS and values is not None:
                    values = [tuple(value.split(',')) for value in values]
                self.set(field, values)
            else:
                # single line
                value = msg[field]
                if value is not None and value != 'UNKNOWN':
                    self.set(field, value)
        self.set_metadata_version()

    def write(self, filepath, skip_unknown=False):
        """Write the metadata fields to filepath."""
        fp = codecs.open(filepath, 'w', encoding='utf-8')
        try:
            self.write_file(fp, skip_unknown)
        finally:
            fp.close()

    def write_file(self, fileobject, skip_unknown=False):
        """Write the PKG-INFO format data to a file object."""
        self.set_metadata_version()

        for field in _version2fieldlist(self['Metadata-Version']):
            values = self.get(field)
            if skip_unknown and values in ('UNKNOWN', [], ['UNKNOWN']):
                continue
            if field in _ELEMENTSFIELD:
                self._write_field(fileobject, field, ','.join(values))
                continue
            if field not in _LISTFIELDS:
                if field == 'Description':
                    values = values.replace('\n', '\n       |')
                values = [values]

            if field in _LISTTUPLEFIELDS:
                values = [','.join(value) for value in values]

            for value in values:
                self._write_field(fileobject, field, value)

    def update(self, other=None, **kwargs):
        """Set metadata values from the given iterable `other` and kwargs.

        Behavior is like `dict.update`: If `other` has a ``keys`` method,
        they are looped over and ``self[key]`` is assigned ``other[key]``.
        Else, ``other`` is an iterable of ``(key, value)`` iterables.

        Keys that don't match a metadata field or that have an empty value are
        dropped.
        """
        def _set(key, value):
            if key in _ATTR2FIELD and value:
                self.set(self._convert_name(key), value)

        if not other:
            # other is None or empty container
            pass
        elif hasattr(other, 'keys'):
            for k in other.keys():
                _set(k, other[k])
        else:
            for k, v in other:
                _set(k, v)

        if kwargs:
            for k, v in kwargs.items():
                _set(k, v)

    def set(self, name, value):
        """Control then set a metadata field."""
        name = self._convert_name(name)

        if ((name in _ELEMENTSFIELD or name == 'Platform') and
            not isinstance(value, (list, tuple))):
            if isinstance(value, string_types):
                value = [v.strip() for v in value.split(',')]
            else:
                value = []
        elif (name in _LISTFIELDS and
              not isinstance(value, (list, tuple))):
            if isinstance(value, string_types):
                value = [value]
            else:
                value = []

        if logger.isEnabledFor(logging.WARNING):
            project_name = self['Name']

            scheme = get_scheme(self.scheme)
            if name in _PREDICATE_FIELDS and value is not None:
                for v in value:
                    # check that the values are valid
                    if not scheme.is_valid_matcher(v.split(';')[0]):
                        logger.warning(
                            '%r: %r is not valid (field %r)',
                            project_name, v, name)
            # FIXME this rejects UNKNOWN, is that right?
            elif name in _VERSIONS_FIELDS and value is not None:
                if not scheme.is_valid_constraint_list(value):
                    logger.warning('%r: %r is not a valid version (field %r)',
                                   project_name, value, name)
            elif name in _VERSION_FIELDS and value is not None:
                if not scheme.is_valid_version(value):
                    logger.warning('%r: %r is not a valid version (field %r)',
                                   project_name, value, name)

        if name in _UNICODEFIELDS:
            if name == 'Description':
                value = self._remove_line_prefix(value)

        self._fields[name] = value

    def get(self, name, default=_MISSING):
        """Get a metadata field."""
        name = self._convert_name(name)
        if name not in self._fields:
            if default is _MISSING:
                default = self._default_value(name)
            return default
        if name in _UNICODEFIELDS:
            value = self._fields[name]
            return value
        elif name in _LISTFIELDS:
            value = self._fields[name]
            if value is None:
                return []
            res = []
            for val in value:
                if name not in _LISTTUPLEFIELDS:
                    res.append(val)
                else:
                    # That's for Project-URL
                    res.append((val[0], val[1]))
            return res

        elif name in _ELEMENTSFIELD:
            value = self._fields[name]
            if isinstance(value, string_types):
                return value.split(',')
        return self._fields[name]

    def check(self, strict=False, restructuredtext=False):
        """Check if the metadata is compliant. If strict is True then raise if
        no Name or Version are provided"""
        self.set_metadata_version()

        # XXX should check the versions (if the file was loaded)
        missing, warnings = [], []

        for attr in ('Name', 'Version'):  # required by PEP 345
            if attr not in self:
                missing.append(attr)

        if strict and missing != []:
            msg = 'missing required metadata: %s' % ', '.join(missing)
            raise MetadataMissingError(msg)

        for attr in ('Home-page', 'Author'):
            if attr not in self:
                missing.append(attr)

        if _HAS_DOCUTILS and restructuredtext:
            warnings.extend(self._check_rst_data(self['Description']))

        # checking metadata 1.2 (XXX needs to check 1.1, 1.0)
        if self['Metadata-Version'] != '1.2':
            return missing, warnings

        scheme = get_scheme(self.scheme)

        def are_valid_constraints(value):
            for v in value:
                if not scheme.is_valid_matcher(v.split(';')[0]):
                    return False
            return True

        for fields, controller in ((_PREDICATE_FIELDS, are_valid_constraints),
                                   (_VERSIONS_FIELDS,
                                    scheme.is_valid_constraint_list),
                                   (_VERSION_FIELDS,
                                    scheme.is_valid_version)):
            for field in fields:
                value = self.get(field, None)
                if value is not None and not controller(value):
                    warnings.append('Wrong value for %r: %s' % (field, value))

        return missing, warnings

    def todict(self, skip_missing=False):
        """Return fields as a dict.

        Field names will be converted to use the underscore-lowercase style
        instead of hyphen-mixed case (i.e. home_page instead of Home-page).
        """
        self.set_metadata_version()

        mapping_1_0 = (
            ('metadata_version', 'Metadata-Version'),
            ('name', 'Name'),
            ('version', 'Version'),
            ('summary', 'Summary'),
            ('home_page', 'Home-page'),
            ('author', 'Author'),
            ('author_email', 'Author-email'),
            ('license', 'License'),
            ('description', 'Description'),
            ('keywords', 'Keywords'),
            ('platform', 'Platform'),
            ('classifier', 'Classifier'),
            ('download_url', 'Download-URL'),
        )

        data = {}
        for key, field_name in mapping_1_0:
            if not skip_missing or field_name in self._fields:
                data[key] = self[field_name]

        if self['Metadata-Version'] == '1.2':
            mapping_1_2 = (
                ('requires_dist', 'Requires-Dist'),
                ('requires_python', 'Requires-Python'),
                ('requires_external', 'Requires-External'),
                ('provides_dist', 'Provides-Dist'),
                ('obsoletes_dist', 'Obsoletes-Dist'),
                ('project_url', 'Project-URL'),
            )
            for key, field_name in mapping_1_2:
                if not skip_missing or field_name in self._fields:
                    if key != 'project_url':
                        data[key] = self[field_name]
                    else:
                        data[key] = [','.join(u) for u in self[field_name]]

        elif self['Metadata-Version'] == '1.1':
            mapping_1_1 = (
                ('provides', 'Provides'),
                ('requires', 'Requires'),
                ('obsoletes', 'Obsoletes'),
            )
            for key, field_name in mapping_1_1:
                if not skip_missing or field_name in self._fields:
                    data[key] = self[field_name]

        return data

    def add_requirements(self, requirements):
        if self['Metadata-Version'] == '1.1':
            # we can't have 1.1 metadata *and* Setuptools requires
            for field in ('Obsoletes', 'Requires', 'Provides'):
                if field in self:
                    del self[field]
        self['Requires-Dist'] += requirements

    # Mapping API
    # TODO could add iter* variants

    def keys(self):
        return list(_version2fieldlist(self['Metadata-Version']))

    def __iter__(self):
        for key in self.keys():
            yield key

    def values(self):
        return [self[key] for key in self.keys()]

    def items(self):
        return [(key, self[key]) for key in self.keys()]

    def __repr__(self):
        return '<%s %s %s>' % (self.__class__.__name__, self.name,
                               self.version)

class Metadata(object):
    """
    The metadata of a release. This implementation uses 2.0 (JSON)
    metadata where possible. If not possible, it wraps a LegacyMetadata
    instance which handles the key-value metadata format.
    """

    METADATA_VERSION = '2.0'

    MANDATORY_KEYS = ('name', 'version')

    INDEX_KEYS = 'name version license summary description'

    DEPENDENCY_KEYS = ('extras requires may_require test_requires '
                       'test_may_require build_requires build_may_require '
                       'dev_requires dev_may_require distributes provides '
                       'obsoleted_by supports_environments')

    __slots__ = ('legacy', 'data', 'scheme')

    def __init__(self, path=None, fileobj=None, mapping=None,
                 scheme='default'):
        if [path, fileobj, mapping].count(None) < 2:
            raise TypeError('path, fileobj and mapping are exclusive')
        self.legacy = None
        self.data = None
        #import pdb; pdb.set_trace()
        if mapping is not None:
            try:
                self.validate_mapping(mapping)
                self.data = mapping
            except MetadataUnrecognizedVersionError:
                self.legacy = LegacyMetadata(mapping=mapping, scheme=scheme)
        else:
            self.scheme = scheme
            data = None
            if path:
                with codecs.open(path, 'r', 'utf-8') as f:
                    data = f.read()
            elif fileobj:
                data = fileobj.read()
            if data is None:
                # Initialised with no args - to be added
                self.data = {'metadata_version': self.METADATA_VERSION}
            else:
                try:
                    self.data = json.loads(data)
                    self.validate_mapping(self.data)
                except ValueError:
                    # Note: MetadataUnrecognizedVersionError does not
                    # inherit from ValueError (it's a DistlibException,
                    # which should not inherit from ValueError).
                    # The ValueError comes from the json.load - if that
                    # succeeds and we get a validation error, we want
                    # that to propagate
                    self.legacy = LegacyMetadata(fileobj=StringIO(data),
                                                 scheme=scheme)

    common_keys = set(('name', 'version', 'license', 'keywords', 'summary'))

    mapped_keys = {
        'requires': ('Requires-Dist', list),
        'may_require': (None, list),
        'build_requires': ('Setup-Requires-Dist', list),
        'build_may_require': (None, list),
        'dev_requires': (None, list),
        'dev_may_require': (None, list),
        'test_requires': (None, list),
        'test_may_require': (None, list),
        'classifiers': ('Classifier', list),
    }

    def __getattribute__(self, key):
        common = object.__getattribute__(self, 'common_keys')
        mapped = object.__getattribute__(self, 'mapped_keys')
        if key in mapped:
            lk, maker = mapped[key]
            if self.legacy:
                if lk is None:
                    result = maker()
                else:
                    result = self.legacy[lk]
            else:
                result = self.data.setdefault(key, maker())
        elif key not in common:
            result = object.__getattribute__(self, key)
        elif self.legacy:
            result = self.legacy[key]
        else:
            result = self.data[key]
        return result

    def __setattr__(self, key, value):
        common = object.__getattribute__(self, 'common_keys')
        mapped = object.__getattribute__(self, 'mapped_keys')
        if key in mapped:
            lk, maker = mapped[key]
            if self.legacy:
                if lk is None:
                    raise NotImplementedError
                self.legacy[lk] = value
            else:
                self.data[key] = value
        elif key not in common:
            object.__setattr__(self, key, value)
        else:
            if key == 'keywords':
                if isinstance(value, string_types):
                    value = value.split()
            if self.legacy:
                self.legacy[key] = value
            else:
                self.data[key] = value

    @property
    def metadata_version(self):
        if self.legacy:
            return self.legacy['Metadata-Version']
        return self.data['metadata_version']

    @metadata_version.setter
    def metadata_version(self, value):
        if self.legacy:
            self.legacy['Metadata-Version'] = value
        else:
            assert value == METADATA_VERSION
            self.data['metadata_version'] = value

    @property
    def name_and_version(self):
        return _get_name_and_version(self.name, self.version, True)

    @property
    def provides(self):
        if self.legacy:
            result = self.legacy['Provides-Dist']
        else:
            result = self.data.setdefault('provides', [])
        s = '%s (%s)' % (self.name, self.version)
        if s not in result:
            result.append(s)
        return result

    @provides.setter
    def provides(self, value):
        if self.legacy:
            self.legacy['Provides-Dist'] = value
        else:
            self.data['provides'] = value

    def get_requirements(self, always, sometimes, extras=None,
                          environment=None):
        """
        Base method to get dependencies, given a set of extras
        to satisfy and an optional environment context.
        :param always: A list of always-wanted dependencies.
        :param sometimes: A list of sometimes-wanted dependencies,
                          dependent on extras and environment.
        :param extras: A list of optional components being requested.
        :param environment: An optional environment for marker evaluation.
        """
        if self.legacy:
            if sometimes:
                raise NotImplementedError
            result = always
        else:
            result = list(always)   # make a copy, as we may add to it
            extras = set(extras or [])
            for d in sometimes:
                if d.get('extra') in extras:
                    include = True
                else:
                    marker = d.get('environment')
                    include = marker and interpret(marker, environment)
                if include:
                    result.extend(d['dependencies'])
            if 'test' in extras:
                extras.remove('test')
                always = self.data.get('test_requires', [])
                sometimes = self.data.get('test_may_require', [])
                # A recursive call, but it should terminate since 'test'
                # has been removed from the extras
                result.extend(self._get_requirements(always, sometimes,
                              extras=extras, environment=environment))
        return result

    @property
    def source_url(self):
        if self.legacy:
            return self.legacy['Download-URL']
        return self.data.get('source_url')

    @source_url.setter
    def source_url(self, value):
        if self.legacy:
            self.legacy['Download-URL'] = value
        else:
            self.data['source_url'] = value

    @property
    def dependencies(self):
        if self.legacy:
            raise NotImplementedError
        else:
            return extract_by_key(self.data, self.DEPENDENCY_KEYS)

    @dependencies.setter
    def dependencies(self, value):
        if self.legacy:
            raise NotImplementedError
        else:
            self.data.update(value)

    def validate_name(self, name):
        return name

    def validate_version(self, version):
        return version

    def validate_mapping(self, mapping):
        if mapping.get('metadata_version') != self.METADATA_VERSION:
            raise MetadataUnrecognizedVersionError()
        missing = []
        for key in self.MANDATORY_KEYS:
            if key not in mapping:
                missing.append(key)
        if missing:
            msg = 'Missing metadata items: %s' % ', '.join(missing)
            raise MetadataMissingError(msg)

    def validate(self):
        if self.legacy:
            missing, warnings = self.legacy.check(True)
            if missing or warnings:
                msg = 'Bad metadata: missing: %s, warnings: %s' % (missing,
                                                                   warnings)
                raise MetadataMissingError(msg)
        else:
            self.validate_mapping(self.data)

    def todict(self):
        if self.legacy:
            return self.legacy.todict(True)
        else:
            result = extract_by_key(self.data, self.INDEX_KEYS)
            return result

    LEGACY_MAPPING = {
        'name': 'Name',
        'version': 'Version',
        'license': 'License',
        'summary': 'Summary',
        'description': 'Description',
        'keywords': 'Keywords',
        'classifiers': 'Classifier',
    }

    def _from_legacy(self):
        assert self.legacy and not self.data
        result = { 'metadata_version': self.METADATA_VERSION }
        lmd = self.legacy
        for nk, ok in self.LEGACY_MAPPING.items():
            result[nk] = lmd[ok]
        result['requires'] = lmd['Requires-Dist']
        result['build_requires'] = lmd['Setup-Requires-Dist']
        result['provides'] = self.provides
        # TODO: other fields such as contacts
        return result

    def _to_legacy(self):
        assert self.data and not self.legacy
        result = LegacyMetadata()
        nmd = self.data
        for nk, ok in self.LEGACY_MAPPING.items():
            result[ok] = nmd[nk]
        result['Requires-Dist'] = self.requires + self.distributes
        result['Setup-Requires-Dist'] = self.build_requires + self.dev_requires
        # TODO: other fields such as contacts
        return result

    def write(self, path=None, fileobj=None, legacy=False, skip_unknown=False):
        if [path, fileobj].count(None) != 1:
            raise ValueError('Exactly one of path and fileobj is needed')
        self.validate()
        if legacy:
            if self.legacy:
                legacy_md = self.legacy
            else:
                legacy_md = self._to_legacy()
            if path:
                self.legacy.write(path, skip_unknown=skip_unknown)
            else:
                self.legacy.write_file(fileobj, skip_unknown=skip_unknown)
        else:
            if self.legacy:
                d = self._from_legacy()
            else:
                d = self.data
            if fileobj:
                json.dump(d, fileobj, ensure_ascii=True, indent=2)
            else:
                with codecs.open(path, 'w', 'utf-8') as f:
                    json.dump(d, f, ensure_ascii=True, indent=2)

    def add_requirements(self, requirements):
        if self.legacy:
            self.legacy.add_requirements(requirements)
        else:
            self.data.setdefault('requires', []).extend(requirements)
