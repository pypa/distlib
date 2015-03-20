# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2013 Vinay Sajip.
# Licensed to the Python Software Foundation under a contributor agreement.
# See LICENSE.txt and CONTRIBUTORS.txt.
#
from __future__ import unicode_literals

from operator import attrgetter
import os
import sys

from compat import unittest

from distlib import DistlibException
from distlib.resources import finder, finder_for_path, ResourceCache
from distlib.util import get_cache_base

HERE = os.path.abspath(os.path.dirname(__file__))

class ZipResourceTestCase(unittest.TestCase):
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
        expected = set([
                        ('', True),
                        ('foo_resource.bin', False),
                        ('bar/bar_resource.bin', False),
                        ('bar/baz.py', False),
                        ('__init__.py', False),
                        ('bar', True),
                        ('bar/__init__.py', False)
                       ])
        self.assertEqual(actual, expected)
        iterator = f.iterator('bar')
        actual = set([(r.name, r.is_container) for r in iterator])
        expected = set([
                        ('bar/baz.py', False),
                        ('bar', True),
                        ('bar/bar_resource.bin', False),
                        ('bar/__init__.py', False)
                       ])
        self.assertEqual(actual, expected)
        iterator = f.iterator('bar/bar_resource.bin')
        actual = set([(r.name, r.is_container) for r in iterator])
        self.assertEqual(actual, set([('bar/bar_resource.bin', False)]))


class FileResourceTestCase(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, HERE)

    def tearDown(self):
        sys.path.pop(0)

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
        expected = set([('', True),
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
        expected = set([
                        ('bar/baz.py', False),
                        ('bar', True),
                        ('bar/bar_resource.bin', False),
                        ('bar/__init__.py', False)
                       ])
        self.assertEqual(actual, expected)
        iterator = f.iterator('bar/bar_resource.bin')
        actual = set([(r.name, r.is_container) for r in iterator])
        self.assertEqual(actual, set([('bar/bar_resource.bin', False)]))


class CacheTestCase(unittest.TestCase):
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

        cases = (
            ('foo', 'foo_resource.bin'),
            ('foo', 'bar/bar_resource.bin'),
            ('foofoo', 'bar/bar_resource.bin'),
            ('barbar', 'bar_resource.bin'),
            ('barbar.baz', 'baz_resource.bin')
        )

        for pkg, path in cases:
            f = finder(pkg)
            r = f.find(path)
            fp = r.file_path
            with open(fp, 'rb') as df:
                data = df.read()
            self.assertEqual(data, r.bytes)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
