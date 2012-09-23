from operator import attrgetter
import os
import sys
import unittest

from distlib import DistlibException
from distlib.resources import finder

HERE = os.path.abspath(os.path.dirname(__file__))

class ZipResourceTestCase(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, os.path.join(HERE, 'foo.zip'))

    def tearDown(self):
        sys.path.pop(0)

    def test_existing_resource(self):
        f = finder('foo')
        r = f.get_resource('foo_resource.bin')
        self.assertTrue(r)
        self.assertEqual(r.bytes, b'more_data\n')
        r = f.get_resource('bar')
        self.assertTrue(r)
        self.assertTrue(r.is_container)
        self.assertRaises(DistlibException, attrgetter('bytes'), r)
        f = finder('foo.bar')
        r = f.get_resource('bar_resource.bin')
        self.assertTrue(r)
        self.assertEqual(r.bytes, b'data\n')

    def test_nonexistent_resource(self):
        f = finder('foo')
        r = f.get_resource('no_such_resource.bin')
        self.assertEqual(r, None)

    def test_non_package(self):
        self.assertRaises(DistlibException, finder, 'foo.bar.baz')

    def test_contents(self):
        f = finder('foo')
        r = f.get_resource('foo_resource.bin')
        self.assertRaises(DistlibException, attrgetter('resources'), r)
        r = f.get_resource('bar')
        expected = set(('bar_resource.bin', 'baz.py', '__init__.py'))
        self.assertEqual(r.resources, expected)

class FileResourceTestCase(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, HERE)
        
    def tearDown(self):
        sys.path.pop(0)

    def test_existing_resource(self):
        f = finder('foofoo')
        r = f.get_resource('foo_resource.bin')
        self.assertTrue(r)
        self.assertFalse(r.is_container)
        self.assertEqual(r.bytes, b'more_data\n')
        r = f.get_resource('bar')
        self.assertTrue(r)
        self.assertTrue(r.is_container)
        self.assertRaises(DistlibException, attrgetter('bytes'), r)
        f = finder('foofoo.bar')
        r = f.get_resource('bar_resource.bin')
        self.assertTrue(r)
        self.assertFalse(r.is_container)
        self.assertEqual(r.bytes, b'data\n')

    def test_nonexistent_resource(self):
        f = finder('foofoo')
        r = f.get_resource('no_such_resource.bin')
        self.assertEqual(r, None)

    def test_contents(self):
        f = finder('foofoo')
        r = f.get_resource('foo_resource.bin')
        self.assertRaises(DistlibException, attrgetter('resources'), r)
        r = f.get_resource('bar')
        expected = set(('bar_resource.bin', 'baz.py', '__init__.py'))
        self.assertEqual(r.resources, expected)

    def test_nested(self):
        f = finder('foofoo')
        r = f.get_resource('nested/nested_resource.bin')
        self.assertTrue(r)
        self.assertEqual(r.bytes, b'nested data\n')

