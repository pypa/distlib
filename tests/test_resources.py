# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2026 Vinay Sajip.
# Licensed to the Python Software Foundation under a contributor agreement.
# See LICENSE.txt and CONTRIBUTORS.txt.
#
from __future__ import unicode_literals

from operator import attrgetter
import os
import shutil
import sys
import tempfile
import zipfile

from compat import unittest
from support import DistlibTestCase, in_github_workflow

from distlib import DistlibException
from distlib.resources import finder, finder_for_path, ResourceCache
from distlib.util import get_cache_base

HERE = os.path.abspath(os.path.dirname(__file__))
IN_GITHUB_WORKFLOW = in_github_workflow()


class ZipResourceTestCase(DistlibTestCase):

    def setUp(self):
        sys.path.insert(0, os.path.join(HERE, 'foo.zip'))

    def tearDown(self):
        sys.path.pop(0)

    def test_existing_resource(self):
        f = finder('foo')
        r = f.find('foo_resource.bin')
        self.assertTrue(r)
        self.assertEqual(r.bytes, b'more_data\n')
        self.assertEqual(r.size, 10)
        stream = r.as_stream()
        self.assertEqual(stream.read(), b'more_data\n')
        stream.close()
        # can access subpackage bar's resources using subdir path ...
        r = f.find('bar/bar_resource.bin')
        self.assertTrue(r)
        self.assertFalse(r.is_container)
        self.assertEqual(r.bytes, b'data\n')
        self.assertEqual(r.size, 5)
        stream = r.as_stream()
        self.assertEqual(stream.read(), b'data\n')
        stream.close()

        r = f.find('bar')
        self.assertTrue(r)
        self.assertTrue(r.is_container)
        self.assertRaises(AttributeError, attrgetter('bytes'), r)
        self.assertRaises(AttributeError, attrgetter('size'), r)
        self.assertRaises(AttributeError, attrgetter('file_path'), r)
        f = finder('foo.bar')
        r = f.find('bar_resource.bin')
        self.assertTrue(r)
        self.assertEqual(r.bytes, b'data\n')
        self.assertEqual(r.size, 5)
        stream = r.as_stream()
        self.assertEqual(stream.read(), b'data\n')
        stream.close()

    def test_nonexistent_resource(self):
        f = finder('foo')
        r = f.find('no_such_resource.bin')
        self.assertIsNone(r)

    def test_non_package(self):
        self.assertRaises(DistlibException, finder, 'foo.bar.baz')

    def test_contents(self):
        f = finder('foo')
        r = f.find('foo_resource.bin')
        self.assertTrue(r)
        self.assertRaises(AttributeError, attrgetter('resources'), r)
        r = f.find('bar')
        self.assertTrue(r)
        expected = set(('bar_resource.bin', 'baz.py', '__init__.py'))
        self.assertEqual(r.resources, expected)

    def test_root_resources(self):
        f = finder('foo')
        r = f.find('')
        self.assertTrue(r)
        self.assertTrue(r.is_container)
        expected = set(('foo_resource.bin', 'bar', '__init__.py'))
        self.assertEqual(r.resources, expected)

    def test_dir_in_zip(self):
        sys.path[0] = '%s/lib' % os.path.join(HERE, 'bar.zip')
        f = finder('barbar')
        self.assertIsNone(f.find('readme.txt'))
        r = f.find('bar_resource.bin')
        self.assertTrue(r)
        self.assertFalse(r.is_container)
        f = finder('barbar.baz')
        r = f.find('baz_resource.bin')
        self.assertTrue(r)
        self.assertFalse(r.is_container)

    def test_finder_for_path(self):
        f = finder_for_path(sys.path[0])
        r = f.find('')
        self.assertIsNotNone(r)
        self.assertTrue(r.is_container)
        p = os.path.join(sys.path[0], 'foo')
        f = finder_for_path(p)
        r = f.find('')
        self.assertIsNotNone(r)
        self.assertTrue(r.is_container)

    def test_iterator(self):
        f = finder('foo')
        iterator = f.iterator('')
        actual = set([(r.name, r.is_container) for r in iterator])
        expected = set([('', True), ('foo_resource.bin', False), ('bar/bar_resource.bin', False), ('bar/baz.py', False),
                        ('__init__.py', False), ('bar', True), ('bar/__init__.py', False)])
        self.assertEqual(actual, expected)
        iterator = f.iterator('bar')
        actual = set([(r.name, r.is_container) for r in iterator])
        expected = set([('bar/baz.py', False), ('bar', True), ('bar/bar_resource.bin', False),
                        ('bar/__init__.py', False)])
        self.assertEqual(actual, expected)
        iterator = f.iterator('bar/bar_resource.bin')
        actual = set([(r.name, r.is_container) for r in iterator])
        self.assertEqual(actual, set([('bar/bar_resource.bin', False)]))

    def _make_directory_zip(self):
        directory = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, directory)
        archive = os.path.join(directory, 'resources.zip')
        with zipfile.ZipFile(archive, 'w') as zf:
            for name in ('empty/', 'empty-sibling.txt', 'implicit/data.txt',
                         'nested/empty/', 'populated/', 'populated/data.txt', 'zempty/'):
                zf.writestr(name, b'')
        return archive

    def test_empty_directories(self):
        f = finder_for_path(self._make_directory_zip())
        for name in ('empty', 'nested/empty', 'zempty'):
            r = f.find(name)
            self.assertIsNotNone(r)
            self.assertTrue(r.is_container)
            self.assertEqual(r.resources, set())

    def test_empty_directories_with_separator(self):
        f = finder_for_path(self._make_directory_zip())
        for name in ('empty/', 'nested/empty/', 'zempty/'):
            r = f.find(name)
            self.assertIsNotNone(r)
            self.assertTrue(r.is_container)
            self.assertEqual(r.resources, set())

    def test_directory_prefix(self):
        archive = self._make_directory_zip()
        for prefix, expected in (('empty', set()), ('nested', set(['empty']))):
            f = finder_for_path(os.path.join(archive, prefix))
            r = f.find('')
            self.assertIsNotNone(r)
            self.assertTrue(r.is_container)
            self.assertEqual(r.resources, expected)
        r = f.find('empty')
        self.assertIsNotNone(r)
        self.assertTrue(r.is_container)
        self.assertEqual(r.resources, set())

    def test_directory_boundaries(self):
        f = finder_for_path(self._make_directory_zip())
        for name in ('implicit', 'populated'):
            for suffix in ('', '/'):
                r = f.find(name + suffix)
                self.assertIsNotNone(r)
                self.assertTrue(r.is_container)
                self.assertEqual(r.resources, set(['data.txt']))
        for name in ('empty-sibling.txt', 'implicit/data.txt', 'populated/data.txt'):
            self.assertFalse(f.find(name).is_container)
        for name in ('missing', 'empty-sibling', 'empty/missing', 'nested/missing', 'zempty/missing'):
            self.assertIsNone(f.find(name))
            self.assertIsNone(f.find(name + '/'))

    def test_iterator_with_empty_directories(self):
        f = finder_for_path(self._make_directory_zip())
        actual = set((r.name, r.is_container) for r in f.iterator(''))
        expected = set([('', True), ('empty', True), ('empty-sibling.txt', False),
                        ('implicit', True), ('implicit/data.txt', False), ('nested', True),
                        ('nested/empty', True), ('populated', True), ('populated/data.txt', False),
                        ('zempty', True)])
        self.assertEqual(actual, expected)


class FileResourceTestCase(DistlibTestCase):

    def setUp(self):
        sys.path.insert(0, HERE)

    def tearDown(self):
        sys.path.pop(0)

    @unittest.skipIf(IN_GITHUB_WORKFLOW, 'This test is end-of-line dependent')
    def test_existing_resource(self):
        f = finder('foofoo')
        r = f.find('foo_resource.bin')
        self.assertTrue(r)
        self.assertFalse(r.is_container)
        self.assertEqual(r.bytes, b'more_data\n')
        self.assertEqual(r.size, 10)
        stream = r.as_stream()
        self.assertEqual(stream.read(), b'more_data\n')
        stream.close()
        r = f.find('bar')
        self.assertTrue(r)
        self.assertTrue(r.is_container)
        self.assertRaises(AttributeError, attrgetter('bytes'), r)
        self.assertRaises(AttributeError, attrgetter('size'), r)
        f = finder('foofoo.bar')
        r = f.find('bar_resource.bin')
        self.assertTrue(r)
        self.assertFalse(r.is_container)
        self.assertEqual(r.bytes, b'data\n')
        self.assertEqual(r.size, 5)
        stream = r.as_stream()
        self.assertEqual(stream.read(), b'data\n')
        stream.close()

    def test_nonexistent_resource(self):
        f = finder('foofoo')
        r = f.find('no_such_resource.bin')
        self.assertIsNone(r)

    # def test_escaping_resource(self):
        # f = finder('foofoo')
        # escapes = (
            # '../included.json',
            # '../../tests/included.json',
            # 'bar/../../included.json',
        # )
        # for path in escapes:
            # with self.assertRaises(DistlibException) as ctx:
                # r = f.find(path)
            # self.assertIn('Resource name escapes package:', str(ctx.exception))
        # # Allow a non-escaping resource which happens to have .. in it
        # r = f.find('bar/../bar/bar_resource.bin')
        # self.assertTrue(r)

    def test_contents(self):
        f = finder('foofoo')
        r = f.find('foo_resource.bin')
        self.assertTrue(r)
        self.assertRaises(AttributeError, attrgetter('resources'), r)
        r = f.find('bar')
        self.assertTrue(r)
        expected = set(('bar_resource.bin', 'baz.py', '__init__.py'))
        self.assertEqual(r.resources, expected)

    def test_root_resources(self):
        f = finder('foofoo')
        r = f.find('')
        self.assertTrue(r)
        self.assertTrue(r.is_container)
        expected = set(('foo_resource.bin', 'bar', '__init__.py', 'nested'))
        self.assertEqual(r.resources, expected)

    @unittest.skipIf(IN_GITHUB_WORKFLOW, 'This test is end-of-line dependent')
    def test_nested(self):
        f = finder('foofoo')
        r = f.find('nested/nested_resource.bin')
        self.assertTrue(r)
        self.assertFalse(r.is_container)
        self.assertEqual(r.bytes, b'nested data\n')
        stream = r.as_stream()
        self.assertEqual(stream.read(), b'nested data\n')
        stream.close()
        r = f.find('nested')
        self.assertTrue(r)
        self.assertTrue(r.is_container)
        self.assertTrue(r)
        self.assertEqual(r.resources, set(['nested_resource.bin']))

    @unittest.skipIf(sys.version_info[0] != 2, 'This test on Python 2 only')
    def test_bytes_path(self):
        f = finder('foofoo')
        for path in 'foo/b\xe7r', b'foo/b\xe7r':
            self.assertEqual(type(f._make_path(path)), type(path))

    def test_iterator(self):
        f = finder('foofoo')
        iterator = f.iterator('')
        actual = set([(r.name, r.is_container) for r in iterator])
        expected = set([
            ('', True),
            ('nested/nested_resource.bin', False),
            ('bar', True),
            ('__init__.py', False),
            ('nested', True),
            ('bar/bar_resource.bin', False),
            ('bar/__init__.py', False),
            ('bar/baz.py', False),
            ('foo_resource.bin', False),
        ])
        self.assertEqual(actual, expected)
        iterator = f.iterator('bar')
        actual = set([(r.name, r.is_container) for r in iterator])
        expected = set([('bar/baz.py', False), ('bar', True), ('bar/bar_resource.bin', False),
                        ('bar/__init__.py', False)])
        self.assertEqual(actual, expected)
        iterator = f.iterator('bar/bar_resource.bin')
        actual = set([(r.name, r.is_container) for r in iterator])
        self.assertEqual(actual, set([('bar/bar_resource.bin', False)]))


class FileResourceIterationTestCase(DistlibTestCase):

    def setUp(self):
        self.workdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.workdir)
        with open(os.path.join(self.workdir, 'keep.txt'), 'wb') as stream:
            stream.write(b'keep')

    @unittest.skipIf(os.name != 'posix', 'Test requires symbolic links')
    def test_iterator_dangling_symlink(self):
        os.symlink(os.path.join(self.workdir, 'missing'), os.path.join(self.workdir, 'link'))
        f = finder_for_path(self.workdir)
        self.assertEqual(set(r.name for r in f.iterator('')), set(['', 'keep.txt']))

    def test_iterator_disappearing_child(self):
        path = os.path.join(self.workdir, 'removed.txt')
        with open(path, 'wb') as stream:
            stream.write(b'removed')
        f = finder_for_path(self.workdir)
        get_resources = f.get_resources

        def disappearing_resources(resource):
            names = get_resources(resource)
            os.remove(path)
            return names

        f.get_resources = disappearing_resources
        self.assertEqual(set(r.name for r in f.iterator('')), set(['', 'keep.txt']))


class CacheTestCase(DistlibTestCase):

    def test_base(self):
        cache = ResourceCache()
        expected = os.path.join(get_cache_base(), str('resource-cache'))
        self.assertEqual(expected, cache.base)
        self.assertTrue(os.path.isdir(expected))

    def test_filepath(self):
        path = os.path.join(HERE, 'foo.zip')
        sys.path.insert(0, path)
        self.addCleanup(sys.path.remove, path)
        sys.path.insert(0, HERE)
        self.addCleanup(sys.path.remove, HERE)
        path = '%s/lib' % os.path.join(HERE, 'bar.zip')
        sys.path.insert(0, path)
        self.addCleanup(sys.path.remove, path)

        cases = (('foo', 'foo_resource.bin'), ('foo', 'bar/bar_resource.bin'), ('foofoo', 'bar/bar_resource.bin'),
                 ('barbar', 'bar_resource.bin'), ('barbar.baz', 'baz_resource.bin'))

        for pkg, path in cases:
            f = finder(pkg)
            r = f.find(path)
            fp = r.file_path
            with open(fp, 'rb') as df:
                data = df.read()
            self.assertEqual(data, r.bytes)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
