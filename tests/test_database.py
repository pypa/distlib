# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2013 The Python Software Foundation.
# See LICENSE.txt and CONTRIBUTORS.txt.
#
from __future__ import unicode_literals

import base64
import io
import os
import hashlib
import logging
import random
import re
import shutil
import sys
import tempfile
from textwrap import dedent

from compat import unittest

from distlib import DistlibException
from distlib.compat import text_type, file_type, StringIO
import distlib.database
from distlib.metadata import Metadata, METADATA_FILENAME
from distlib.database import (InstalledDistribution, EggInfoDistribution,
                              BaseInstalledDistribution, EXPORTS_FILENAME,
                              DistributionPath, make_graph,
                              get_required_dists, get_dependent_dists)
from distlib.util import (get_resources_dests, ExportEntry, CSVReader,
                          read_exports, write_exports)

from test_util import GlobTestCaseBase
from support import LoggingCatcher, requires_zlib

logger = logging.getLogger(__name__)

# TODO Add a test for getting a distribution provided by another distribution
# TODO Add a test for absolute path RECORD items (e.g. /etc/myapp/config.ini)
# TODO Add tests from the former pep376 project (zipped site-packages, etc.)


class FakeDistsMixin(object):

    def setUp(self):
        super(FakeDistsMixin, self).setUp()

        # make a copy that we can write into for our fake installed
        # distributions
        tmpdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmpdir)
        self.fake_dists_path = os.path.realpath(
            os.path.join(tmpdir, 'fake_dists'))
        fake_dists_src = os.path.abspath(
            os.path.join(os.path.dirname(__file__), 'fake_dists'))
        shutil.copytree(fake_dists_src, self.fake_dists_path)
        # XXX ugly workaround: revert copystat calls done by shutil behind our
        # back (to avoid getting a read-only copy of a read-only file).  we
        # could pass a custom copy_function to change the mode of files, but
        # shutil gives no control over the mode of directories :(
        # see http://bugs.python.org/issue1666318
        for root, dirs, files in os.walk(self.fake_dists_path):
            os.chmod(root, 0o755)
            for f in files:
                os.chmod(os.path.join(root, f), 0o644)
            for d in dirs:
                os.chmod(os.path.join(root, d), 0o755)


class CommonDistributionTests(FakeDistsMixin):
    """Mixin used to test the interface common to InstalledDistribution
    and EggInfoDistribution classes.

    Derived classes define cls, sample_dist, dirs and records.  These
    attributes are used in test methods.  See source code for details.
    """

    def _get_dist_path(self, distdir):
        here = os.path.abspath(os.path.dirname(__file__))
        return os.path.join(here, 'fake_dists', distdir)

    def test_instantiation(self):
        # check that useful attributes are here
        name, version, distdir = self.sample_dist
        dist_path = self._get_dist_path(distdir)
        dist = self.dist = self.cls(dist_path)
        self.assertEqual(dist.path, dist_path)
        self.assertEqual(dist.name, name)
        self.assertEqual(dist.metadata.name, name)
        self.assertIsInstance(dist.metadata, Metadata)
        self.assertEqual(dist.version, version)
        self.assertEqual(dist.metadata.version, version)

    @requires_zlib
    def test_repr(self):
        dist = self.cls(self.dirs[0])
        # just check that the class name is in the repr
        self.assertIn(self.cls.__name__, repr(dist))

    @requires_zlib
    def test_str(self):
        name, version, distdir = self.sample_dist
        dist = self.cls(self._get_dist_path(distdir))
        self.assertEqual(name, dist.name)
        # Sanity test: dist.name is unicode,
        # but str output contains no u prefix.
        self.assertIsInstance(dist.name, text_type)
        self.assertEqual(version, dist.version)
        self.assertEqual(str(dist), self.expected_str_output)

    @requires_zlib
    def test_comparison(self):
        # tests for __eq__ and __hash__
        dist = self.cls(self.dirs[0])
        dist2 = self.cls(self.dirs[0])
        dist3 = self.cls(self.dirs[1])
        self.assertIn(dist, {dist: True})
        self.assertEqual(dist, dist)

        self.assertIsNot(dist, dist2)
        self.assertEqual(dist, dist2)
        self.assertNotEqual(dist, dist3)
        self.assertNotEqual(dist, ())

    def test_list_installed_files(self):
        for dir_ in self.dirs:
            dist = self.cls(dir_)
            for path, hash, size in dist.list_installed_files():
                record_data = self.records[dist.path]
                self.assertIn(path, record_data)
                self.assertEqual(hash, record_data[path][0])
                self.assertEqual(size, record_data[path][1])

    def test_hash(self):
        datalen = random.randrange(0, 500)
        data = os.urandom(datalen)
        for dir_ in self.dirs:
            dist = self.cls(dir_)
            for hasher in ('sha1', 'sha224', 'sha384',
                           'sha256', 'sha512', None):
                dist.hasher = hasher
                actual = dist.get_hash(data)
                if hasher is None:
                    digester = hashlib.md5(data)
                else:
                    digester = getattr(hashlib, hasher)(data)
                digest = digester.digest()
                digest = base64.urlsafe_b64encode(digest).rstrip(b'=')
                digest = digest.decode('ascii')
                if hasher is None:
                    expected = digest
                else:
                    expected = '%s=%s' % (hasher, digest)
                self.assertEqual(actual, expected)

class TestDistribution(CommonDistributionTests, unittest.TestCase):

    cls = InstalledDistribution
    sample_dist = 'choxie', '2.0.0.9', 'choxie-2.0.0.9.dist-info'
    expected_str_output = 'choxie 2.0.0.9'

    def setUp(self):
        def get_files(location):
            for path in ('REQUESTED', 'INSTALLER', 'METADATA',
                         METADATA_FILENAME, EXPORTS_FILENAME):
                p = os.path.join(location + '.dist-info', path)
                if os.path.exists(p):
                    yield p
            for path, dirs, files in os.walk(location):
                for f in files:
                    yield os.path.join(path, f)

        super(TestDistribution, self).setUp()
        self.dirs = [os.path.join(self.fake_dists_path, f)
                     for f in os.listdir(self.fake_dists_path)
                     if f.endswith('.dist-info')]

        self.records = {}
        for distinfo_dir in self.dirs:
            dist_location = distinfo_dir.replace('.dist-info', '')
            record_file = os.path.join(distinfo_dir, 'RECORD')

            # Write the files using write_installed_files.
            # list_installed_files should read and match.
            dist = self.cls(distinfo_dir)
            prefix = os.path.dirname(dist_location)
            dist.write_installed_files(get_files(dist_location), prefix)

            with CSVReader(path=record_file) as record_reader:
                record_data = {}
                for row in record_reader:
                    if row == []:
                        continue
                    path, hash, size = (row[:] +
                                        [None for i in range(len(row), 3)])
                    record_data[path] = hash, size
            self.records[distinfo_dir] = record_data

    def test_instantiation(self):
        super(TestDistribution, self).test_instantiation()
        self.assertIsInstance(self.dist.requested, bool)

    def test_get_distinfo_file(self):
        # Test the retrieval of dist-info file objects.
        distinfo_name = 'choxie-2.0.0.9'
        other_distinfo_name = 'grammar-1.0a4'
        distinfo_dir = os.path.join(self.fake_dists_path,
                                    distinfo_name + '.dist-info')
        dist = InstalledDistribution(distinfo_dir)
        # Test for known good file matches
        distinfo_files = [
            # Relative paths
            'INSTALLER', METADATA_FILENAME,
            # Absolute paths
            os.path.join(distinfo_dir, 'RECORD'),
            os.path.join(distinfo_dir, 'REQUESTED'),
        ]

        for distfile in distinfo_files:
            value = dist.get_distinfo_file(distfile)
            self.assertTrue(os.path.isfile(value))
            self.assertEqual(value,
                             os.path.join(distinfo_dir, distfile))

        # Test an absolute path that is part of another distributions dist-info
        other_distinfo_file = os.path.join(
            self.fake_dists_path, other_distinfo_name + '.dist-info',
            'REQUESTED')
        self.assertRaises(DistlibException, dist.get_distinfo_file,
                          other_distinfo_file)
        # Test for a file that should not exist
        self.assertRaises(DistlibException, dist.get_distinfo_file,
                          'MAGICFILE')

    def test_list_distinfo_files(self):
        distinfo_name = 'towel_stuff-0.1'
        distinfo_dir = os.path.join(self.fake_dists_path,
                                    distinfo_name + '.dist-info')
        dist = InstalledDistribution(distinfo_dir)
        # Test for the iteration of the raw path
        distinfo_files = [os.path.join(distinfo_dir, filename) for filename in
                          os.listdir(distinfo_dir)]
        found = list(dist.list_distinfo_files())
        base = self.fake_dists_path
        for i, p in enumerate(found):
            if not os.path.isabs(p):
                found[i] = os.path.join(base, p)
        self.assertEqual(sorted(found), sorted(distinfo_files))
        # Test for the iteration of local absolute paths
        distinfo_files = [os.path.join(sys.prefix, distinfo_dir, path) for
                          path in distinfo_files]
        found = sorted(dist.list_distinfo_files())
        if os.sep != '/':
            self.assertNotIn('/', found[0])
            self.assertIn(os.sep, found[0])
        self.assertEqual(found, sorted(distinfo_files))

    def test_get_resources_path(self):
        distinfo_name = 'babar-0.1'
        distinfo_dir = os.path.join(self.fake_dists_path,
                                    distinfo_name + '.dist-info')
        dist = InstalledDistribution(distinfo_dir)
        resource_path = dist.get_resource_path('babar.png')
        self.assertEqual(resource_path, 'babar.png')
        self.assertRaises(KeyError, dist.get_resource_path, 'notexist')

    def test_check_installed_files(self):
        for dir_ in self.dirs:
            dist = self.cls(dir_)
            mismatches = dist.check_installed_files()
            self.assertEqual(mismatches, [])
            # pick a non-empty file at random and change its contents
            # but not its size. Check the failure returned,
            # then restore the file.
            files = [f for f in dist.list_installed_files() if f[-1] not in ('', '0')]
            bad_file = random.choice(files)
            bad_file_name = bad_file[0]
            if not os.path.isabs(bad_file_name):
                base = os.path.dirname(dir_)
                bad_file_name = os.path.join(base, bad_file_name)
            with open(bad_file_name, 'rb') as f:
                data = f.read()
            bad_data = bytes(bytearray(reversed(data)))
            bad_hash = dist.get_hash(bad_data)
            with open(bad_file_name, 'wb') as f:
                f.write(bad_data)
            mismatches = dist.check_installed_files()
            self.assertEqual(mismatches, [(bad_file_name, 'hash', bad_file[1],
                                           bad_hash)])
            # now truncate the file by one byte and see what's returned
            with open(bad_file_name, 'wb') as f:
                f.write(bad_data[:-1])
            bad_size = str(len(bad_data) - 1)
            mismatches = dist.check_installed_files()
            self.assertEqual(mismatches, [(bad_file_name, 'size', bad_file[2],
                                           bad_size)])

            # now remove the file and see what's returned
            os.remove(bad_file_name)
            mismatches = dist.check_installed_files()
            self.assertEqual(mismatches, [(bad_file_name, 'exists',
                                           True, False)])

            # restore the file
            with open(bad_file_name, 'wb') as f:
                f.write(data)


class TestEggInfoDistribution(CommonDistributionTests,
                              LoggingCatcher,
                              unittest.TestCase):

    cls = EggInfoDistribution
    sample_dist = 'bacon', '0.1', 'bacon-0.1.egg-info'
    expected_str_output = 'bacon 0.1'

    def setUp(self):
        super(TestEggInfoDistribution, self).setUp()

        self.dirs = [os.path.join(self.fake_dists_path, f)
                     for f in os.listdir(self.fake_dists_path)
                     if f.endswith('.egg') or f.endswith('.egg-info')]

        self.records = {}
        for egginfo_dir in self.dirs:
            dist_location = egginfo_dir.replace('.egg-info', '')
            record_file = os.path.join(egginfo_dir, 'installed-files.txt')

            dist = self.cls(egginfo_dir)
            #prefix = os.path.dirname(dist_location)
            #dist.write_installed_files(get_files(dist_location), prefix)

            record_data = {}
            if os.path.exists(record_file):
                with open(record_file) as fp:
                    for line in fp:
                        line = line.strip()
                        if line == './':
                            break
                        record_data[line] = None, None
            self.records[egginfo_dir] = record_data

    @unittest.skip('not implemented yet')
    def test_list_installed_files(self):
        # EggInfoDistribution defines list_installed_files but there is no
        # test for it yet; someone needs to add a file with the list of
        # installed files for one of the egg fake dists and write the support
        # code to populate self.records (and then delete this method)
        pass


class TestDatabase(LoggingCatcher,
                   FakeDistsMixin,
                   unittest.TestCase):

    def setUp(self):
        super(TestDatabase, self).setUp()
        sys.path.insert(0, self.fake_dists_path)
        self.addCleanup(sys.path.remove, self.fake_dists_path)

    def test_caches(self):
        # sanity check for internal caches
        d = DistributionPath()
        for name in ('_cache', '_cache_egg'):
            self.assertEqual(getattr(d, name).name, {})
            self.assertEqual(getattr(d, name).path, {})

    def test_distinfo_dirname(self):
        # Given a name and a version, we expect the distinfo_dirname function
        # to return a standard distribution information directory name.

        items = [
            # (name, version, standard_dirname)
            # Test for a very simple single word name and decimal version
            # number
            ('docutils', '0.5', 'docutils-0.5.dist-info'),
            # Test for another except this time with a '-' in the name, which
            # needs to be transformed during the name lookup
            ('python-ldap', '2.5', 'python_ldap-2.5.dist-info'),
            # Test for both '-' in the name and a funky version number
            ('python-ldap', '2.5 a---5', 'python_ldap-2.5 a---5.dist-info'),
            ]

        # Loop through the items to validate the results
        for name, version, standard_dirname in items:
            dirname = DistributionPath.distinfo_dirname(name, version)
            self.assertEqual(dirname, standard_dirname)

    @requires_zlib
    def test_get_distributions(self):
        # Lookup all distributions found in the ``sys.path``.
        # This test could potentially pick up other installed distributions
        non_egg_dists = [('grammar', '1.0a4'), ('choxie', '2.0.0.9'),
                         ('towel-stuff', '0.1'), ('babar', '0.1')]
        egg_dists = [('bacon', '0.1'), ('cheese', '2.0.2'),
                     ('coconuts-aster', '10.3'),
                     ('banana', '0.4'), ('strawberry', '0.6'),
                     ('truffles', '5.0'), ('nut', 'funkyversion')]

        all_dists = non_egg_dists + egg_dists

        d = DistributionPath()
        ed = DistributionPath(include_egg=True)

        cases = ((d, non_egg_dists, InstalledDistribution),
                 (ed, all_dists, BaseInstalledDistribution))

        fake_dists_path = self.fake_dists_path
        for enabled in (True, False):
            if not enabled:
                d.cache_enabled = False
                ed.cache_enabled = False
                d.clear_cache()
                ed.clear_cache()

            for distset, fake_dists, allowed_class in cases:
                found_dists = []

                # Verify the fake dists have been found.
                dists = list(distset.get_distributions())
                for dist in dists:
                    self.assertIsInstance(dist, allowed_class)
                    if (dist.name in dict(fake_dists) and
                        dist.path.startswith(fake_dists_path)):
                        found_dists.append((dist.name, dist.version))
                    else:
                        # check that it doesn't find anything more than this
                        self.assertFalse(dist.path.startswith(fake_dists_path))
                    # otherwise we don't care what other dists are found

                # Finally, test that we found all that we were looking for
                self.assertEqual(sorted(found_dists), sorted(fake_dists))

    @requires_zlib
    def test_get_distribution(self):
        # Test for looking up a distribution by name.
        # Test the lookup of the towel-stuff distribution
        name = 'towel-stuff'  # Note: This is different from the directory name

        d = DistributionPath()
        ed = DistributionPath(include_egg=True)

        # Lookup the distribution
        dist = d.get_distribution(name)
        self.assertIsInstance(dist, InstalledDistribution)
        self.assertEqual(dist.name, name)

        # Verify that an unknown distribution returns None
        self.assertIsNone(d.get_distribution('bogus'))

        # Verify partial name matching doesn't work
        self.assertIsNone(d.get_distribution('towel'))

        # Verify that it does not find egg-info distributions, when not
        # instructed to
        self.assertIsNone(d.get_distribution('bacon'))
        self.assertIsNone(d.get_distribution('cheese'))
        self.assertIsNone(d.get_distribution('strawberry'))
        self.assertIsNone(d.get_distribution('banana'))

        # Now check that it works well in both situations, when egg-info
        # is a file and directory respectively.

        for name in ('cheese', 'bacon', 'banana', 'strawberry'):
            dist = ed.get_distribution(name)
            self.assertIsInstance(dist, EggInfoDistribution)
            self.assertEqual(dist.name, name)

    @requires_zlib
    def test_provides(self):
        # Test for looking up distributions by what they provide
        checkLists = lambda x, y: self.assertEqual(sorted(x), sorted(y))

        d = DistributionPath()
        ed = DistributionPath(include_egg=True)

        l = [dist.name for dist in d.provides_distribution('truffles')]
        checkLists(l, ['choxie', 'towel-stuff'])

        l = [dist.name for dist in d.provides_distribution('truffles', '1.0')]
        checkLists(l, ['choxie', 'towel-stuff'])

        l = [dist.name for dist in ed.provides_distribution('truffles', '1.0')]
        checkLists(l, ['choxie', 'cheese', 'towel-stuff'])

        l = [dist.name for dist in d.provides_distribution('truffles', '1.1.2')]
        checkLists(l, ['towel-stuff'])

        l = [dist.name for dist in d.provides_distribution('truffles', '1.1')]
        checkLists(l, ['towel-stuff'])

        l = [dist.name for dist in d.provides_distribution('truffles',
                                                           '!=1.1,<=2.0')]
        checkLists(l, ['choxie', 'towel-stuff'])

        l = [dist.name for dist in ed.provides_distribution('truffles',
                                                            '!=1.1,<=2.0')]
        checkLists(l, ['choxie', 'bacon', 'cheese', 'towel-stuff'])

        l = [dist.name for dist in d.provides_distribution('truffles', '>1.0')]
        checkLists(l, ['towel-stuff'])

        l = [dist.name for dist in d.provides_distribution('truffles', '>1.5')]
        checkLists(l, [])

        l = [dist.name for dist in ed.provides_distribution('truffles', '>1.5')]
        checkLists(l, ['bacon', 'truffles'])

        l = [dist.name for dist in d.provides_distribution('truffles', '>=1.0')]
        checkLists(l, ['choxie', 'towel-stuff'])

        l = [dist.name for dist in ed.provides_distribution('strawberry', '0.6')]
        checkLists(l, ['coconuts-aster', 'strawberry'])

        l = [dist.name for dist in ed.provides_distribution('strawberry', '>=0.5')]
        checkLists(l, ['coconuts-aster', 'strawberry'])

        l = [dist.name for dist in ed.provides_distribution('strawberry', '>0.6')]
        checkLists(l, [])

        l = [dist.name for dist in ed.provides_distribution('banana', '0.4')]
        checkLists(l, ['banana', 'coconuts-aster'])

        l = [dist.name for dist in ed.provides_distribution('banana', '>=0.3')]
        checkLists(l, ['banana', 'coconuts-aster'])

        l = [dist.name for dist in ed.provides_distribution('banana', '!=0.4')]
        checkLists(l, [])

    @requires_zlib
    def test_yield_distribution(self):
        # tests the internal function _yield_distributions
        checkLists = lambda x, y: self.assertEqual(sorted(x), sorted(y))

        eggs = [('bacon', '0.1'), ('banana', '0.4'), ('strawberry', '0.6'),
                ('truffles', '5.0'), ('cheese', '2.0.2'),
                ('coconuts-aster', '10.3'), ('nut', 'funkyversion')]
        dists = [('choxie', '2.0.0.9'), ('grammar', '1.0a4'),
                 ('towel-stuff', '0.1'), ('babar', '0.1')]

        d = DistributionPath(include_egg=False)
        d._include_dist = False
        checkLists([], d._yield_distributions())

        d = DistributionPath(include_egg=True)
        d._include_dist = False
        found = [(dist.name, dist.version)
                 for dist in d._yield_distributions()
                 if dist.path.startswith(self.fake_dists_path)]
        checkLists(eggs, found)

        d = DistributionPath()
        found = [(dist.name, dist.version)
                 for dist in d._yield_distributions()
                 if dist.path.startswith(self.fake_dists_path)]
        checkLists(dists, found)

        d = DistributionPath(include_egg=True)
        found = [(dist.name, dist.version)
                 for dist in d._yield_distributions()
                 if dist.path.startswith(self.fake_dists_path)]
        checkLists(dists + eggs, found)

    def check_entry(self, entry, name, prefix, suffix, flags):
        self.assertEqual(entry.name, name)
        self.assertEqual(entry.prefix, prefix)
        self.assertEqual(entry.suffix, suffix)
        self.assertEqual(entry.flags, flags)

    def test_read_exports(self):
        d = DistributionPath().get_distribution('babar')
        r = d.exports
        self.assertIn('foo', r)
        d = r['foo']
        self.assertIn('bar', d)
        self.check_entry(d['bar'], 'bar', 'baz', 'barbaz', ['a=10', 'b'])
        self.assertIn('bar.baz', r)
        d = r['bar.baz']
        self.assertIn('foofoo', d)
        self.check_entry(d['foofoo'], 'foofoo', 'baz.foo', 'bazbar', [])
        self.assertIn('real', d)
        e = d['real']
        self.check_entry(e, 'real', 'cgi', 'print_directory', [])
        import cgi
        self.assertIs(e.value, cgi.print_directory)

        # See issue #78. Test reading an entry_points.txt with leading spaces

        TEST_EXPORTS = b"""
        [paste.server_runner]
        main = waitress:serve_paste
        [console_scripts]
        waitress-serve = waitress.runner:run
        """
        with io.BytesIO(TEST_EXPORTS) as f:
            exports = read_exports(f)
        self.assertEqual(set(exports.keys()),
                         set(['paste.server_runner', 'console_scripts']))

    def test_exports_iteration(self):
        d = DistributionPath()
        expected = set((
            ('bar', 'baz', 'barbaz', ('a=10', 'b')),
            ('bar', 'crunchie', None, ()),
            ('bar', 'towel', 'towel', ()),
            ('baz', 'towel', 'beach_towel', ()),
        ))
        entries = list(d.get_exported_entries('foo'))
        for e in entries:
            t = e.name, e.prefix, e.suffix, tuple(e.flags)
            self.assertIn(t, expected)
            expected.remove(t)
        self.assertFalse(expected)   # nothing left
        expected = set((
            ('bar', 'baz', 'barbaz', ('a=10', 'b')),
            ('bar', 'crunchie', None, ()),
            ('bar', 'towel', 'towel', ()),
        ))
        entries = list(d.get_exported_entries('foo', 'bar'))
        for e in entries:
            t = e.name, e.prefix, e.suffix, tuple(e.flags)
            self.assertIn(t, expected)
            expected.remove(t)
        self.assertFalse(expected)   # nothing left

        expected = set((
            ('foofoo', 'baz.foo', 'bazbar', ()),
            ('real', 'cgi', 'print_directory', ()),
            ('foofoo', 'ferrero', 'rocher', ()),
            ('foobar', 'hoopy', 'frood', ('dent',)),
        ))
        entries = list(d.get_exported_entries('bar.baz'))
        for e in entries:
            t = e.name, e.prefix, e.suffix, tuple(e.flags)
            self.assertIn(t, expected)
            expected.remove(t)
        self.assertFalse(expected)   # nothing left

    def test_modules(self):
        dp = DistributionPath(include_egg=True)
        dist = dp.get_distribution('banana')
        self.assertIsInstance(dist, EggInfoDistribution)
        self.assertEqual(dist.modules, ['banana', 'cavendish'])


class DataFilesTestCase(GlobTestCaseBase):

    def assertRulesMatch(self, rules, spec):
        tempdir = self.build_files_tree(spec)
        expected = self.clean_tree(spec)
        result = get_resources_dests(tempdir, rules)
        self.assertEqual(expected, result)

    def clean_tree(self, spec):
        files = {}
        for path, value in spec.items():
            if value is not None:
                files[path] = value
        return files

    def test_simple_glob(self):
        rules = [('', '*.tpl', '{data}')]
        spec = {'coucou.tpl': '{data}/coucou.tpl',
                'Donotwant': None}
        self.assertRulesMatch(rules, spec)

    def test_multiple_match(self):
        rules = [('scripts', '*.bin', '{appdata}'),
                 ('scripts', '*', '{appscript}')]
        spec = {'scripts/script.bin': '{appscript}/script.bin',
                'Babarlikestrawberry': None}
        self.assertRulesMatch(rules, spec)

    def test_set_match(self):
        rules = [('scripts', '*.{bin,sh}', '{appscript}')]
        spec = {'scripts/script.bin': '{appscript}/script.bin',
                'scripts/babar.sh':  '{appscript}/babar.sh',
                'Babarlikestrawberry': None}
        self.assertRulesMatch(rules, spec)

    def test_set_match_multiple(self):
        rules = [('scripts', 'script{s,}.{bin,sh}', '{appscript}')]
        spec = {'scripts/scripts.bin': '{appscript}/scripts.bin',
                'scripts/script.sh':  '{appscript}/script.sh',
                'Babarlikestrawberry': None}
        self.assertRulesMatch(rules, spec)

    def test_set_match_exclude(self):
        rules = [('scripts', '*', '{appscript}'),
                 ('', os.path.join('**', '*.sh'), None)]
        spec = {'scripts/scripts.bin': '{appscript}/scripts.bin',
                'scripts/script.sh':  None,
                'Babarlikestrawberry': None}
        self.assertRulesMatch(rules, spec)

    def test_glob_in_base(self):
        rules = [('scrip*', '*.bin', '{appscript}')]
        spec = {'scripts/scripts.bin': '{appscript}/scripts.bin',
                'scripouille/babar.bin': '{appscript}/babar.bin',
                'scriptortu/lotus.bin': '{appscript}/lotus.bin',
                'Babarlikestrawberry': None}
        self.assertRulesMatch(rules, spec)

    def test_recursive_glob(self):
        rules = [('', os.path.join('**', '*.bin'), '{binary}')]
        spec = {'binary0.bin': '{binary}/binary0.bin',
                'scripts/binary1.bin': '{binary}/scripts/binary1.bin',
                'scripts/bin/binary2.bin': '{binary}/scripts/bin/binary2.bin',
                'you/kill/pandabear.guy': None}
        self.assertRulesMatch(rules, spec)

    def test_final_example_glob(self):
        rules = [
            ('mailman/database/schemas/', '*', '{appdata}/schemas'),
            ('', os.path.join('**', '*.tpl'), '{appdata}/templates'),
            ('', os.path.join('developer-docs', '**', '*.txt'), '{doc}'),
            ('', 'README', '{doc}'),
            ('mailman/etc/', '*', '{config}'),
            ('mailman/foo/', os.path.join('**', 'bar', '*.cfg'),
             '{config}/baz'),
            ('mailman/foo/', os.path.join('**', '*.cfg'), '{config}/hmm'),
            ('', 'some-new-semantic.sns', '{funky-crazy-category}'),
        ]
        spec = {
            'README': '{doc}/README',
            'some.tpl': '{appdata}/templates/some.tpl',
            'some-new-semantic.sns':
                '{funky-crazy-category}/some-new-semantic.sns',
            'mailman/database/mailman.db': None,
            'mailman/database/schemas/blah.schema':
                '{appdata}/schemas/blah.schema',
            'mailman/etc/my.cnf': '{config}/my.cnf',
            'mailman/foo/some/path/bar/my.cfg':
                '{config}/hmm/some/path/bar/my.cfg',
            'mailman/foo/some/path/other.cfg':
                '{config}/hmm/some/path/other.cfg',
            'developer-docs/index.txt': '{doc}/developer-docs/index.txt',
            'developer-docs/api/toc.txt': '{doc}/developer-docs/api/toc.txt',
        }
        self.maxDiff = None
        self.assertRulesMatch(rules, spec)

    def test_get_file(self):
        # Create a fake dist
        temp_site_packages = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp_site_packages)

        dist_name = 'test'
        dist_info = os.path.join(temp_site_packages, 'test-0.1.dist-info')
        os.mkdir(dist_info)

        metadata_path = os.path.join(dist_info, 'pydist.json')
        resources_path = os.path.join(dist_info, 'RESOURCES')
        md = Metadata()
        md.name = 'test'
        md.version = '0.1'
        md.summary = 'test'
        md.write(path=metadata_path)
        test_path = 'test.cfg'

        fd, test_resource_path = tempfile.mkstemp()
        os.close(fd)
        self.addCleanup(os.remove, test_resource_path)

        fp = open(test_resource_path, 'w')
        try:
            fp.write('Config')
        finally:
            fp.close()

        fp = open(resources_path, 'w')
        try:
            fp.write('%s,%s' % (test_path, test_resource_path))
        finally:
            fp.close()

        # Add fake site-packages to sys.path to retrieve fake dist
        self.addCleanup(sys.path.remove, temp_site_packages)
        sys.path.insert(0, temp_site_packages)

        # Try to retrieve resources paths and files
        d = DistributionPath()
        self.assertEqual(d.get_file_path(dist_name, test_path),
                         test_resource_path)
        self.assertRaises(KeyError, d.get_file_path, dist_name,
                          'i-dont-exist')


class DepGraphTestCase(LoggingCatcher,
                       unittest.TestCase):

    DISTROS_DIST = ('choxie', 'grammar', 'towel-stuff')
    DISTROS_EGG = ('bacon', 'banana', 'strawberry', 'cheese')
    BAD_EGGS = ('nut',)

    EDGE = re.compile(
           r'"(?P<from>.*)" -> "(?P<to>.*)" \[label="(?P<label>.*)"\]')

    def checkLists(self, l1, l2):
        """ Compare two lists without taking the order into consideration """
        self.assertListEqual(sorted(l1), sorted(l2))

    def setUp(self):
        super(DepGraphTestCase, self).setUp()
        path = os.path.join(os.path.dirname(__file__), 'fake_dists')
        path = os.path.abspath(path)
        sys.path.insert(0, path)
        self.addCleanup(sys.path.remove, path)

    def get_dists(self, names, include_egg=False):
        dists = []
        d = DistributionPath(include_egg=include_egg)
        for name in names:
            dist = d.get_distribution(name)
            self.assertNotEqual(dist, None)
            dists.append(dist)
        return dists

    def test_make_graph(self):
        dists = self.get_dists(self.DISTROS_DIST)

        choxie, grammar, towel = dists

        graph = make_graph(dists)

        deps = [(x.name, y) for x, y in graph.adjacency_list[choxie]]
        self.checkLists([('towel-stuff', 'towel-stuff (0.1)')], deps)
        self.assertIn(choxie, graph.reverse_list[towel])
        self.checkLists(graph.missing[choxie], ['nut'])

        deps = [(x.name, y) for x, y in graph.adjacency_list[grammar]]
        self.checkLists([], deps)
        self.checkLists(graph.missing[grammar], ['truffles (>=1.2)'])

        deps = [(x.name, y) for x, y in graph.adjacency_list[towel]]
        self.checkLists([], deps)
        self.checkLists(graph.missing[towel], ['bacon (<=0.2)'])

    @requires_zlib
    def test_make_graph_egg(self):
        dists = self.get_dists(self.DISTROS_DIST + self.DISTROS_EGG, True)

        choxie, grammar, towel, bacon, banana, strawberry, cheese = dists

        graph = make_graph(dists)

        deps = [(x.name, y) for x, y in graph.adjacency_list[choxie]]
        self.checkLists([('towel-stuff', 'towel-stuff (0.1)')], deps)
        self.assertIn(choxie, graph.reverse_list[towel])
        self.checkLists(graph.missing[choxie], ['nut'])

        deps = [(x.name, y) for x, y in graph.adjacency_list[grammar]]
        self.checkLists([('bacon', 'truffles (>=1.2)')], deps)
        self.checkLists(graph.missing.get(grammar, []), [])
        self.assertIn(grammar, graph.reverse_list[bacon])

        deps = [(x.name, y) for x, y in graph.adjacency_list[towel]]
        self.checkLists([('bacon', 'bacon (<=0.2)')], deps)
        self.checkLists(graph.missing.get(towel, []), [])
        self.assertIn(towel, graph.reverse_list[bacon])

        deps = [(x.name, y) for x, y in graph.adjacency_list[bacon]]
        self.checkLists([], deps)
        self.checkLists(graph.missing.get(bacon, []), [])

        deps = [(x.name, y) for x, y in graph.adjacency_list[banana]]
        self.checkLists([('strawberry', 'strawberry (>=0.5)')], deps)
        self.checkLists(graph.missing.get(banana, []), [])
        self.assertIn(banana, graph.reverse_list[strawberry])

        deps = [(x.name, y) for x, y in graph.adjacency_list[strawberry]]
        self.checkLists([], deps)
        self.checkLists(graph.missing.get(strawberry, []), [])

        deps = [(x.name, y) for x, y in graph.adjacency_list[cheese]]
        self.checkLists([], deps)
        self.checkLists(graph.missing.get(cheese, []), [])

    def test_dependent_dists(self):
        # import pdb; pdb.set_trace()
        dists = self.get_dists(self.DISTROS_DIST)

        choxie, grammar, towel = dists

        deps = [d.name for d in get_dependent_dists(dists, choxie)]
        self.checkLists([], deps)

        deps = [d.name for d in get_dependent_dists(dists, grammar)]
        self.checkLists([], deps)

        deps = [d.name for d in get_dependent_dists(dists, towel)]
        self.checkLists(['choxie'], deps)

    def test_required_dists(self):
        dists = self.get_dists(self.DISTROS_DIST +
                               ('truffles', 'bacon', 'banana',
                                'coconuts-aster'), True)

        choxie, grammar, towel, truffles, bacon, banana, coco = dists

        reqs = [d.name for d in get_required_dists(dists, choxie)]
        self.checkLists(['bacon', 'towel-stuff'], reqs)

        reqs = [d.name for d in get_required_dists(dists, grammar)]
        self.checkLists(['truffles'], reqs)

        reqs = [d.name for d in get_required_dists(dists, banana)]
        self.checkLists(['coconuts-aster'], reqs)

        reqs = [d.name for d in get_required_dists(dists, towel)]
        self.checkLists(['bacon'], reqs)

        # Check the invalid case: pass a dist not in the list
        dists = dists[:-1]
        self.assertRaises(DistlibException, get_required_dists, dists, coco)

    @requires_zlib
    def test_dependent_dists_egg(self):
        dists = self.get_dists(self.DISTROS_DIST + self.DISTROS_EGG, True)

        choxie, grammar, towel, bacon, banana, strawberry, cheese = dists

        deps = [d.name for d in get_dependent_dists(dists, choxie)]
        self.checkLists([], deps)

        deps = [d.name for d in get_dependent_dists(dists, grammar)]
        self.checkLists([], deps)

        deps = [d.name for d in get_dependent_dists(dists, towel)]
        self.checkLists(['choxie'], deps)

        deps = [d.name for d in get_dependent_dists(dists, bacon)]
        self.checkLists(['choxie', 'towel-stuff', 'grammar'], deps)

        deps = [d.name for d in get_dependent_dists(dists, strawberry)]
        self.checkLists(['banana'], deps)

        deps = [d.name for d in get_dependent_dists(dists, cheese)]
        self.checkLists([], deps)

        # Check the invalid case: pass a dist not in the list
        dists = dists[:-1]
        self.assertRaises(DistlibException, get_dependent_dists, dists, cheese)

    @requires_zlib
    def test_graph_to_dot(self):
        expected = (
            ('towel-stuff', 'bacon', 'bacon (<=0.2)'),
            ('grammar', 'bacon', 'truffles (>=1.2)'),
            ('choxie', 'towel-stuff', 'towel-stuff (0.1)'),
            ('banana', 'strawberry', 'strawberry (>=0.5)'),
        )

        dists = self.get_dists(self.DISTROS_DIST + self.DISTROS_EGG, True)

        graph = make_graph(dists)
        buf = StringIO()
        graph.to_dot(buf)
        buf.seek(0)
        matches = []
        lines = buf.readlines()
        for line in lines[1:-1]:  # skip the first and the last lines
            if line[-1] == '\n':
                line = line[:-1]
            match = self.EDGE.match(line.strip())
            self.assertIsNot(match, None)
            matches.append(match.groups())

        self.checkLists(matches, expected)

    @requires_zlib
    def test_graph_disconnected_to_dot(self):
        dependencies_expected = (
            ('towel-stuff', 'bacon', 'bacon (<=0.2)'),
            ('grammar', 'bacon', 'truffles (>=1.2)'),
            ('choxie', 'towel-stuff', 'towel-stuff (0.1)'),
            ('banana', 'strawberry', 'strawberry (>=0.5)'),
        )
        disconnected_expected = ('cheese', 'bacon', 'strawberry')

        dists = self.get_dists(self.DISTROS_DIST + self.DISTROS_EGG, True)

        graph = make_graph(dists)
        buf = StringIO()
        graph.to_dot(buf, skip_disconnected=False)
        buf.seek(0)
        lines = buf.readlines()

        dependencies_lines = []
        disconnected_lines = []

        # First sort output lines into dependencies and disconnected lines.
        # We also skip the attribute lines, and don't include the "{" and "}"
        # lines.
        disconnected_active = False
        for line in lines[1:-1]:  # Skip first and last line
            if line.startswith('subgraph disconnected'):
                disconnected_active = True
                continue
            if line.startswith('}') and disconnected_active:
                disconnected_active = False
                continue

            if disconnected_active:
                # Skip the 'label = "Disconnected"', etc. attribute lines.
                if ' = ' not in line:
                    disconnected_lines.append(line)
            else:
                dependencies_lines.append(line)

        dependencies_matches = []
        for line in dependencies_lines:
            if line[-1] == '\n':
                line = line[:-1]
            match = self.EDGE.match(line.strip())
            self.assertIsNot(match, None)
            dependencies_matches.append(match.groups())

        disconnected_matches = []
        for line in disconnected_lines:
            if line[-1] == '\n':
                line = line[:-1]
            line = line.strip('"')
            disconnected_matches.append(line)

        self.checkLists(dependencies_matches, dependencies_expected)
        self.checkLists(disconnected_matches, disconnected_expected)

    @requires_zlib
    def test_graph_bad_version_to_dot(self):
        expected = (
            ('towel-stuff', 'bacon', 'bacon (<=0.2)'),
            ('grammar', 'bacon', 'truffles (>=1.2)'),
            ('choxie', 'towel-stuff', 'towel-stuff (0.1)'),
            ('banana', 'strawberry', 'strawberry (>=0.5)'),
        )

        dists = self.get_dists(self.DISTROS_DIST + self.DISTROS_EGG +
                               self.BAD_EGGS, True)

        graph = make_graph(dists)
        buf = StringIO()
        graph.to_dot(buf)
        buf.seek(0)
        matches = []
        lines = buf.readlines()
        for line in lines[1:-1]:  # skip the first and the last lines
            if line[-1] == '\n':
                line = line[:-1]
            match = self.EDGE.match(line.strip())
            self.assertIsNot(match, None)
            matches.append(match.groups())

        self.checkLists(matches, expected)

    @requires_zlib
    def test_repr(self):
        dists = self.get_dists(self.DISTROS_DIST + self.DISTROS_EGG +
                               self.BAD_EGGS, True)

        graph = make_graph(dists)
        self.assertTrue(repr(graph))


def test_suite():
    suite = unittest.TestSuite()
    load = unittest.defaultTestLoader.loadTestsFromTestCase
    suite.addTest(load(TestDistribution))
    suite.addTest(load(TestEggInfoDistribution))
    suite.addTest(load(TestDatabase))
    suite.addTest(load(DataFilesTestCase))
    suite.addTest(load(DepGraphTestCase))
    return suite


if __name__ == "__main__":  # pragma: no cover
    unittest.main(defaultTest='test_suite')
