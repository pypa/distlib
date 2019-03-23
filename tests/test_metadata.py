# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2013 The Python Software Foundation.
# See LICENSE.txt and CONTRIBUTORS.txt.
#
"""Tests for distlib.metadata."""
from __future__ import unicode_literals

import codecs
import json
import os
import sys
from textwrap import dedent

from compat import unittest

from distlib import __version__
from distlib.compat import StringIO
from distlib.metadata import (LegacyMetadata, Metadata, METADATA_FILENAME,
                              PKG_INFO_PREFERRED_VERSION,
                              MetadataConflictError, MetadataMissingError,
                              MetadataUnrecognizedVersionError,
                              MetadataInvalidError, _ATTR2FIELD)

from support import (LoggingCatcher, TempdirManager)


HERE = os.path.abspath(os.path.dirname(__file__))

class LegacyMetadataTestCase(LoggingCatcher, TempdirManager,
                             unittest.TestCase):

    maxDiff = None
    restore_environ = ['HOME']

    def setUp(self):
        super(LegacyMetadataTestCase, self).setUp()
        self.argv = sys.argv, sys.argv[:]

    def tearDown(self):
        sys.argv = self.argv[0]
        sys.argv[:] = self.argv[1]
        super(LegacyMetadataTestCase, self).tearDown()

    ####  Test various methods of the LegacyMetadata class

    def get_file_contents(self, name):
        name = os.path.join(HERE, name)
        f = codecs.open(name, 'r', encoding='utf-8')
        try:
            contents = f.read() % sys.platform
        finally:
            f.close()
        return contents

    def test_instantiation(self):
        PKG_INFO = os.path.join(HERE, 'PKG-INFO')
        f = codecs.open(PKG_INFO, 'r', encoding='utf-8')
        try:
            contents = f.read()
        finally:
            f.close()

        fp = StringIO(contents)

        m = LegacyMetadata()
        self.assertRaises(MetadataUnrecognizedVersionError, m.items)

        m = LegacyMetadata(PKG_INFO)
        self.assertEqual(len(m.items()), 22)

        m = LegacyMetadata(fileobj=fp)
        self.assertEqual(len(m.items()), 22)

        m = LegacyMetadata(mapping=dict(name='Test', version='1.0'))
        self.assertEqual(len(m.items()), 17)

        d = dict(m.items())
        self.assertRaises(TypeError, LegacyMetadata,
                          PKG_INFO, fileobj=fp)
        self.assertRaises(TypeError, LegacyMetadata,
                          PKG_INFO, mapping=d)
        self.assertRaises(TypeError, LegacyMetadata,
                          fileobj=fp, mapping=d)
        self.assertRaises(TypeError, LegacyMetadata,
                          PKG_INFO, mapping=m, fileobj=fp)

    def test_mapping_api(self):
        content = self.get_file_contents('PKG-INFO')
        metadata = LegacyMetadata(fileobj=StringIO(content))
        self.assertIn('Version', metadata.keys())
        self.assertIn('0.5', metadata.values())
        self.assertIn(('Version', '0.5'), metadata.items())

        metadata.update({'version': '0.6'})
        self.assertEqual(metadata['Version'], '0.6')
        metadata.update([('version', '0.7')])
        self.assertEqual(metadata['Version'], '0.7')
        # use a kwarg to update
        metadata.update(version='0.6')
        self.assertEqual(metadata['Version'], '0.6')

        # make sure update method checks values like the set method does
        metadata.update({'version': '1--2'})
        self.assertEqual(len(self.get_logs()), 1)

        self.assertEqual(list(metadata), metadata.keys())

    def test_attribute_access(self):
        content = self.get_file_contents('PKG-INFO')
        metadata = LegacyMetadata(fileobj=StringIO(content))
        for attr in _ATTR2FIELD:
            self.assertEqual(getattr(metadata, attr), metadata[attr])

    def test_read_metadata(self):
        fields = {'name': 'project',
                  'version': '1.0',
                  'description': 'desc',
                  'summary': 'xxx',
                  'download_url': 'http://example.com',
                  'keywords': ['one', 'two'],
                  'requires_dist': ['foo']}

        metadata = LegacyMetadata(mapping=fields)
        PKG_INFO = StringIO()
        metadata.write_file(PKG_INFO)
        PKG_INFO.seek(0)

        metadata = LegacyMetadata(fileobj=PKG_INFO)

        self.assertEqual(metadata['name'], 'project')
        self.assertEqual(metadata['version'], '1.0')
        self.assertEqual(metadata['summary'], 'xxx')
        self.assertEqual(metadata['download_url'], 'http://example.com')
        self.assertEqual(metadata['keywords'], ['one', 'two'])
        self.assertEqual(metadata['platform'], [])
        self.assertEqual(metadata['obsoletes'], [])
        self.assertEqual(metadata['requires-dist'], ['foo'])

    def test_write_metadata(self):
        # check support of non-ASCII values
        tmp_dir = self.mkdtemp()
        my_file = os.path.join(tmp_dir, 'f')

        metadata = LegacyMetadata(mapping={
                                     'name': 'my.project',
                                     'author': 'Café Junior',
                                     'summary': 'Café torréfié',
                                     'description': 'Héhéhé',
                                     'keywords': ['café', 'coffee']
                                  })
        metadata.write(my_file)

        # the file should use UTF-8
        metadata2 = LegacyMetadata()
        fp = codecs.open(my_file, encoding='utf-8')
        try:
            metadata2.read_file(fp)
        finally:
            fp.close()

        # XXX when keywords are not defined, metadata will have
        # 'Keywords': [] but metadata2 will have 'Keywords': ['']
        # because of a value.split(',') in LegacyMetadata.get
        self.assertEqual(metadata.items(), metadata2.items())

        # ASCII also works, it's a subset of UTF-8
        metadata = LegacyMetadata(mapping={'author': 'Mister Cafe',
                                     'name': 'my.project',
                                     'author': 'Cafe Junior',
                                     'summary': 'Cafe torrefie',
                                     'description': 'Hehehe'
                                  })
        metadata.write(my_file)

        metadata2 = LegacyMetadata()
        fp = codecs.open(my_file, encoding='utf-8')
        try:
            metadata2.read_file(fp)
        finally:
            fp.close()

    def test_metadata_read_write(self):
        PKG_INFO = os.path.join(HERE, 'PKG-INFO')
        metadata = LegacyMetadata(PKG_INFO)
        out = StringIO()
        metadata.write_file(out)

        out.seek(0)
        res = LegacyMetadata()
        res.read_file(out)
        self.assertEqual(metadata.values(), res.values())

    ####  Test checks

    def test_check_version(self):
        metadata = LegacyMetadata()
        metadata['Name'] = 'vimpdb'
        metadata['Home-page'] = 'http://pypi.org'
        metadata['Author'] = 'Monty Python'
        missing, warnings = metadata.check()
        self.assertEqual(missing, ['Version'])

    def test_check_version_strict(self):
        metadata = LegacyMetadata()
        metadata['Name'] = 'vimpdb'
        metadata['Home-page'] = 'http://pypi.org'
        metadata['Author'] = 'Monty Python'
        self.assertRaises(MetadataMissingError, metadata.check, strict=True)

    def test_check_name(self):
        metadata = LegacyMetadata()
        metadata['Version'] = '1.0'
        metadata['Home-page'] = 'http://pypi.org'
        metadata['Author'] = 'Monty Python'
        missing, warnings = metadata.check()
        self.assertEqual(missing, ['Name'])

    def test_check_name_strict(self):
        metadata = LegacyMetadata()
        metadata['Version'] = '1.0'
        metadata['Home-page'] = 'http://pypi.org'
        metadata['Author'] = 'Monty Python'
        self.assertRaises(MetadataMissingError, metadata.check, strict=True)

    def test_check_author(self):
        metadata = LegacyMetadata()
        metadata['Version'] = '1.0'
        metadata['Name'] = 'vimpdb'
        metadata['Home-page'] = 'http://pypi.org'
        missing, warnings = metadata.check()
        self.assertEqual(missing, ['Author'])

    def test_check_homepage(self):
        metadata = LegacyMetadata()
        metadata['Version'] = '1.0'
        metadata['Name'] = 'vimpdb'
        metadata['Author'] = 'Monty Python'
        missing, warnings = metadata.check()
        self.assertEqual(missing, ['Home-page'])

    def test_check_matchers(self):
        metadata = LegacyMetadata()
        metadata['Version'] = 'rr'
        metadata['Name'] = 'vimpdb'
        metadata['Home-page'] = 'http://pypi.org'
        metadata['Author'] = 'Monty Python'
        metadata['Requires-dist'] = ['Foo (a)']
        metadata['Obsoletes-dist'] = ['Foo (a)']
        metadata['Provides-dist'] = ['Foo (a)']
        missing, warnings = metadata.check()
        self.assertEqual(len(warnings), 4)

    ####  Test fields and metadata versions

    def test_metadata_versions(self):
        metadata = LegacyMetadata(mapping={'name': 'project',
                                           'version': '1.0'})
        self.assertEqual(metadata['Metadata-Version'],
                         PKG_INFO_PREFERRED_VERSION)
        self.assertNotIn('Provides', metadata)
        self.assertNotIn('Requires', metadata)
        self.assertNotIn('Obsoletes', metadata)

        metadata['Classifier'] = ['ok']
        metadata.set_metadata_version()
        self.assertEqual(metadata['Metadata-Version'], '1.1')

        metadata = LegacyMetadata()
        metadata['Download-URL'] = 'ok'
        metadata.set_metadata_version()
        self.assertEqual(metadata['Metadata-Version'], '1.1')

        metadata = LegacyMetadata()
        metadata['Obsoletes'] = 'ok'
        metadata.set_metadata_version()
        self.assertEqual(metadata['Metadata-Version'], '1.1')

        del metadata['Obsoletes']
        metadata['Obsoletes-Dist'] = 'ok'
        metadata.set_metadata_version()
        self.assertEqual(metadata['Metadata-Version'], '1.2')
        metadata.set('Obsoletes', 'ok')
        self.assertRaises(MetadataConflictError,
                          metadata.set_metadata_version)

        del metadata['Obsoletes']
        del metadata['Obsoletes-Dist']
        metadata.set_metadata_version()
        metadata['Version'] = '1'
        self.assertEqual(metadata['Metadata-Version'], '1.1')

        # make sure the _best_version function works okay with
        # non-conflicting fields from 1.1 and 1.2 (i.e. we want only the
        # requires/requires-dist and co. pairs to cause a conflict, not all
        # fields in _314_MARKERS)
        metadata = LegacyMetadata()
        metadata['Requires-Python'] = '3'
        metadata['Classifier'] = ['Programming language :: Python :: 3']
        metadata.set_metadata_version()
        self.assertEqual(metadata['Metadata-Version'], '1.2')

        PKG_INFO = os.path.join(HERE, 'SETUPTOOLS-PKG-INFO')
        metadata = LegacyMetadata(PKG_INFO)
        self.assertEqual(metadata['Metadata-Version'], '1.0')

        PKG_INFO = os.path.join(HERE, 'SETUPTOOLS-PKG-INFO2')
        metadata = LegacyMetadata(PKG_INFO)
        self.assertEqual(metadata['Metadata-Version'], '1.1')

        # make sure an empty list for Obsoletes and Requires-dist gets ignored
        metadata['Obsoletes'] = []
        metadata['Requires-dist'] = []
        metadata.set_metadata_version()
        self.assertEqual(metadata['Metadata-Version'], '1.1')

        # Update the _fields dict directly to prevent 'Metadata-Version'
        # from being updated by the _set_best_version() method.
        metadata._fields['Metadata-Version'] = '1.618'
        self.assertRaises(MetadataUnrecognizedVersionError, metadata.keys)

        # add a test for 2.1
        metadata = LegacyMetadata()
        metadata['Description-Content-Type'] = 'text/markdown; charset=UTF-8; variant=CommonMark'
        metadata.set_metadata_version()
        self.assertEqual(metadata['Metadata-Version'], '2.1')

    def test_version(self):
        LegacyMetadata(mapping={'author': 'xxx',
                          'name': 'xxx',
                          'version': 'xxx',
                          'home_page': 'xxxx'
                       })
        logs = self.get_logs()
        self.assertEqual(1, len(logs))
        self.assertIn('not a valid version', logs[0])

    def test_description(self):
        content = self.get_file_contents('PKG-INFO')
        metadata = LegacyMetadata()
        metadata.read_file(StringIO(content))

        # see if we can read the description now
        DESC = os.path.join(HERE, 'LONG_DESC.txt')
        f = open(DESC)
        try:
            wanted = f.read()
        finally:
            f.close()
        self.assertEqual(wanted, metadata['Description'])

        # save the file somewhere and make sure we can read it back
        out = StringIO()
        metadata.write_file(out)
        out.seek(0)

        out.seek(0)
        metadata = LegacyMetadata()
        metadata.read_file(out)
        self.assertEqual(wanted, metadata['Description'])

    def test_description_folding(self):
        # make sure the indentation is preserved
        out = StringIO()
        desc = dedent("""\
        example::
              We start here
            and continue here
          and end here.
        """)

        metadata = LegacyMetadata()
        metadata['description'] = desc
        metadata.write_file(out)

        # folded_desc = desc.replace('\n', '\n' + (7 * ' ') + '|')
        folded_desc = desc.replace('\n', '\n' + (8 * ' '))
        self.assertIn(folded_desc, out.getvalue())

    def test_project_url(self):
        metadata = LegacyMetadata()
        metadata['Project-URL'] = [('one', 'http://ok')]
        self.assertEqual(metadata['Project-URL'], [('one', 'http://ok')])
        metadata.set_metadata_version()
        self.assertEqual(metadata['Metadata-Version'], '1.2')

        # make sure this particular field is handled properly when written
        fp = StringIO()
        metadata.write_file(fp)
        self.assertIn('Project-URL: one,http://ok', fp.getvalue().split('\n'))

        fp.seek(0)
        metadata = LegacyMetadata()
        metadata.read_file(fp)
        self.assertEqual(metadata['Project-Url'], [('one', 'http://ok')])

    # TODO copy tests for v1.1 requires, obsoletes and provides from distutils
    # (they're useless but we support them so we should test them anyway)

    def test_provides_dist(self):
        fields = {'name': 'project',
                  'version': '1.0',
                  'provides_dist': ['project', 'my.project']}
        metadata = LegacyMetadata(mapping=fields)
        self.assertEqual(metadata['Provides-Dist'],
                         ['project', 'my.project'])
        self.assertEqual(metadata['Metadata-Version'], '1.2', metadata)
        self.assertNotIn('Requires', metadata)
        self.assertNotIn('Obsoletes', metadata)

    def test_requires_dist(self):
        fields = {'name': 'project',
                  'version': '1.0',
                  'requires_dist': ['other', 'another (==1.0)']}
        metadata = LegacyMetadata(mapping=fields)
        self.assertEqual(metadata['Requires-Dist'],
                         ['other', 'another (==1.0)'])
        self.assertEqual(metadata['Metadata-Version'], '1.2')
        self.assertNotIn('Provides', metadata)
        self.assertEqual(metadata['Requires-Dist'],
                         ['other', 'another (==1.0)'])
        self.assertNotIn('Obsoletes', metadata)

        # make sure write_file uses one RFC 822 header per item
        fp = StringIO()
        metadata.write_file(fp)
        lines = fp.getvalue().split('\n')
        self.assertIn('Requires-Dist: other', lines)
        self.assertIn('Requires-Dist: another (==1.0)', lines)

        # test warnings for invalid version constraints
        # XXX this would cause no warnings if we used update (or the mapping
        # argument of the constructor), see comment in LegacyMetadata.update
        metadata = LegacyMetadata()
        metadata['Requires-Dist'] = 'Funky (Groovie)'
        metadata['Requires-Python'] = '1a-4'
        self.assertEqual(len(self.get_logs()), 2)

        # test multiple version matches
        metadata = LegacyMetadata()

        # XXX check PEP and see if 3 == 3.0
        metadata['Requires-Python'] = '>=2.6, <3.0'
        metadata['Requires-Dist'] = ['Foo (>=2.6, <3.0)']
        self.assertEqual(self.get_logs(), [])

    def test_obsoletes_dist(self):
        fields = {'name': 'project',
                  'version': '1.0',
                  'obsoletes_dist': ['other', 'another (<1.0)']}
        metadata = LegacyMetadata(mapping=fields)
        self.assertEqual(metadata['Obsoletes-Dist'],
                         ['other', 'another (<1.0)'])
        self.assertEqual(metadata['Metadata-Version'], '1.2')
        self.assertNotIn('Provides', metadata)
        self.assertNotIn('Requires', metadata)
        self.assertEqual(metadata['Obsoletes-Dist'],
                         ['other', 'another (<1.0)'])

    def test_fullname(self):
        md = LegacyMetadata()
        md['Name'] = 'a b c'
        md['Version'] = '1 0 0'
        s = md.get_fullname()
        self.assertEqual(s, 'a b c-1 0 0')
        s = md.get_fullname(True)
        self.assertEqual(s, 'a-b-c-1.0.0')

    def test_fields(self):
        md = LegacyMetadata()
        self.assertTrue(md.is_multi_field('Requires-Dist'))
        self.assertFalse(md.is_multi_field('Name'))
        self.assertTrue(md.is_field('Obsoleted-By'))
        self.assertFalse(md.is_field('Frobozz'))

class MetadataTestCase(LoggingCatcher, TempdirManager,
                       unittest.TestCase):
    def test_init(self):
        "Test initialisation"
        md = Metadata()
        self.assertIsNone(md._legacy)
        self.assertRaises(MetadataMissingError, md.validate)
        md.name = 'dummy'
        self.assertRaises(MetadataMissingError, md.validate)
        md.version = '0.1'
        self.assertRaises(MetadataMissingError, md.validate)
        md.summary = 'Summary'
        md.validate()
        self.assertEqual(md.name, 'dummy')
        self.assertEqual(md.version, '0.1')

        # Initialise from mapping
        md = Metadata(mapping={
                        'metadata_version': '2.0',
                        'name': 'foo',
                        'version': '0.3.4',
                        'summary': 'Summary',
                      })
        md.validate()
        self.assertEqual(md.name, 'foo')
        self.assertEqual(md.version, '0.3.4')
        self.assertEqual(md.run_requires, [])
        self.assertEqual(md.meta_requires, [])
        self.assertEqual(md.provides, ['foo (0.3.4)'])

        # Initialise from legacy metadata
        fn = os.path.join(HERE, 'fake_dists', 'choxie-2.0.0.9.dist-info',
                          'METADATA')
        md = Metadata(path=fn)
        md.validate()
        self.assertIsNotNone(md._legacy)
        self.assertEqual(set(md.run_requires), set(['towel-stuff (0.1)', 'nut']))
        self.assertEqual(md.metadata_version, '1.2')
        self.assertEqual(md.version, '2.0.0.9')
        self.assertEqual(md.meta_requires, [])
        self.assertEqual(set(md.provides),
                         set(['choxie (2.0.0.9)', 'truffles (1.0)']))

        # Initialise from new metadata
        fn = os.path.join(HERE, METADATA_FILENAME)
        md = Metadata(path=fn)
        md.validate()
        self.assertIsNone(md._legacy)
        self.assertEqual(md.metadata_version, '2.0')
        self.assertEqual(md.name, 'foobar')
        self.assertEqual(md.version, '0.1')
        self.assertEqual(md.provides, ['foobar (0.1)'])

    def test_add_requirements(self):
        md = Metadata()
        md.name = 'bar'
        md.version = '0.5'
        md.add_requirements(['foo (0.1.2)'])
        self.assertEqual(md.run_requires, [{ 'requires': ['foo (0.1.2)']}])

        fn = os.path.join(HERE, 'fake_dists', 'choxie-2.0.0.9.dist-info',
                          'METADATA')
        md = Metadata(path=fn)
        md.add_requirements(['foo (0.1.2)'])
        self.assertEqual(set(md.run_requires),
                         set(['towel-stuff (0.1)', 'nut', 'foo (0.1.2)']))

    def test_requirements(self):
        fn = os.path.join(HERE, METADATA_FILENAME)
        md = Metadata(path=fn)
        self.assertEqual(md.meta_requires, [{'requires': ['bar (1.0)']}])
        r = md.get_requirements(md.run_requires)
        self.assertEqual(r, ['foo'])
        r = md.get_requirements(md.run_requires, extras=['certs'])
        self.assertEqual(r, ['foo', 'certifi (0.0.8)'])
        r = md.get_requirements(md.run_requires, extras=['certs', 'ssl'])
        if sys.platform != 'win32':
            self.assertEqual(r, ['foo', 'certifi (0.0.8)'])
        else:
            self.assertEqual(set(r), set(['foo', 'certifi (0.0.8)',
                                          'wincertstore (0.1)']))
        for ver in ('2.5', '2.4'):
            env = {'python_version': ver}
            r = md.get_requirements(md.run_requires,
                                    extras=['certs', 'ssl'], env=env)
            if sys.platform != 'win32':
                self.assertEqual(set(r), set(['foo', 'certifi (0.0.8)',
                                              'ssl (1.16)']))
            elif ver == '2.4':
                self.assertEqual(set(r), set(['certifi (0.0.8)', 'ssl (1.16)',
                                              'wincertstore (0.1)', 'foo',
                                              'ctypes (1.0.2)']))
            else:
                self.assertEqual(set(r), set(['certifi (0.0.8)', 'ssl (1.16)',
                                              'wincertstore (0.1)', 'foo']))
        env['sys_platform'] = 'win32'
        r = md.get_requirements(md.run_requires,
                                extras=['certs', 'ssl'], env=env)
        self.assertEqual(set(r), set(['foo', 'certifi (0.0.8)', 'ssl (1.16)',
                                      'ctypes (1.0.2)', 'wincertstore (0.1)']))
        env['python_version'] = '2.5'
        r = md.get_requirements(md.run_requires,
                                extras=['certs', 'ssl'], env=env)
        self.assertEqual(set(r), set(['foo', 'certifi (0.0.8)', 'ssl (1.16)',
                                      'wincertstore (0.1)']))
        r = md.get_requirements(md.run_requires, extras=[':test:'])
        self.assertEqual(r, ['foo', 'nose'])
        r = md.get_requirements(md.run_requires, extras=[':test:', 'udp'])
        self.assertEqual(set(r), set(['foo', 'nose', 'nose-udp']))
        self.assertEqual(md.dependencies, {
            'provides': ['foobar (0.1)'],
            'meta_requires': [
                {
                    'requires': ['bar (1.0)']
                }
            ],
            'extras': ['ssl', 'certs'],
            'build_requires': [],
            'test_requires': [
                {
                    'requires': ['nose'],
                },
                {
                    'requires': ['nose-udp'],
                    'extra': 'udp',
                }
            ],
            'run_requires': [
                {
                    'requires': ['foo']
                },
                {
                    'requires': ['certifi (0.0.8)'],
                    'extra': 'certs',
                },
                {
                    'requires': ['wincertstore (0.1)'],
                    'extra': 'ssl',
                    'environment': "sys_platform=='win32'",
                },
                {
                    'requires': ['ctypes (1.0.2)'],
                    'extra': 'ssl',
                    'environment': "sys_platform=='win32' and "
                                   "python_version=='2.4'",
                },
                {
                    'requires': ['ssl (1.16)'],
                    'extra': 'ssl',
                    'environment': "python_version in '2.4, 2.5'",
                }
            ]
        })

    def test_write(self):
        dfn = self.temp_filename()
        # Read legacy, write new
        sfn = os.path.join(HERE, 'fake_dists', 'choxie-2.0.0.9.dist-info',
                           'METADATA')
        md = Metadata(path=sfn)
        md.write(path=dfn)
        with codecs.open(dfn, 'r', 'utf-8') as f:
            data = json.load(f)
        self.assertEqual(data, {
            'metadata_version': '2.0',
            'generator': 'distlib (%s)' % __version__,
            'name': 'choxie',
            'version': '2.0.0.9',
            'license': 'BSD',
            'summary': 'Chocolate with a kick!',
            'description': 'Chocolate with a longer kick!',
            'provides': ['truffles (1.0)', 'choxie (2.0.0.9)'],
            'run_requires': [{'requires': ['towel-stuff (0.1)', 'nut']}],
            'keywords': [],
        })
        # Write legacy, compare with original
        md.write(path=dfn, legacy=True)
        nmd = Metadata(path=dfn)
        d1 = md.todict()
        d2 = nmd.todict()
        self.assertEqual(d1, d2)

    def test_valid(self):
        """
        Tests to check that missing and invalid metadata is caught.
        """
        md = Metadata()
        self.assertRaises(MetadataMissingError, md.validate)
        try:
            md.name = 'Foo Bar'
        except MetadataInvalidError:
            pass
        md.name = 'foo_bar'
        # Name now OK, but version and summary to be checked
        self.assertRaises(MetadataMissingError, md.validate)
        try:
            md.version = '1.0a'
        except MetadataInvalidError:
            pass
        md.version = '1.0'
        # Name and version now OK, but summary to be checked
        self.assertRaises(MetadataMissingError, md.validate)
        try:
            md.summary = ''
        except MetadataInvalidError:
            pass
        try:
            md.summary = ' ' * 2048
        except MetadataInvalidError:
            pass
        md.summary = ' ' * 2047
        md.validate()
        md.summary = ' '
        md.validate()


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
