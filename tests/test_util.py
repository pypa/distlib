import os

from compat import unittest

from distlib import DistlibException
from distlib.util import (get_registry_entry, RegistryEntry, resolve,
                          get_cache_base, path_to_cache_dir,
                          parse_credentials)

class UtilTestCase(unittest.TestCase):
    def check_entry(self, entry, name, prefix, suffix, flags):
        self.assertEqual(entry.name, name)
        self.assertEqual(entry.prefix, prefix)
        self.assertEqual(entry.suffix, suffix)
        self.assertEqual(entry.flags, flags)

    def test_registry_entry(self):
        self.assertIsNone(get_registry_entry('foo.py'))
        self.assertIsNone(get_registry_entry('foo.py='))
        for spec in ('foo=foo:main', 'foo =foo:main', 'foo= foo:main',
                     'foo = foo:main'):
            self.check_entry(get_registry_entry(spec),
                             'foo', 'foo', 'main', [])
        self.check_entry(get_registry_entry('foo=foo.bar:main'),
                         'foo', 'foo.bar', 'main', [])
        self.check_entry(get_registry_entry('foo=foo.bar:main [a]'),
                         'foo', 'foo.bar', 'main', ['a'])
        self.check_entry(get_registry_entry('foo=foo.bar:main [ a ]'),
                         'foo', 'foo.bar', 'main', ['a'])
        self.check_entry(get_registry_entry('foo=foo.bar:main [a=b, c=d,e, f=g]'),
                         'foo', 'foo.bar', 'main', ['a=b', 'c=d', 'e', 'f=g'])
        self.check_entry(get_registry_entry('foo=foo.bar:main [a=9, 9=8,e, f9=g8]'),
                         'foo', 'foo.bar', 'main', ['a=9', '9=8', 'e', 'f9=g8'])
        self.check_entry(get_registry_entry('foo=foo.bar:main[x]'),
                         'foo', 'foo.bar', 'main', ['x'])
        self.check_entry(get_registry_entry('foo=abc'), 'foo', 'abc', None, [])
        self.assertRaises(DistlibException, get_registry_entry, 'foo=foo.bar:x:y')
        self.assertRaises(DistlibException, get_registry_entry, 'foo=foo.bar:x [')
        self.assertRaises(DistlibException, get_registry_entry, 'foo=foo.bar:x ]')
        self.assertRaises(DistlibException, get_registry_entry, 'foo=foo.bar:x []')
        self.assertRaises(DistlibException, get_registry_entry, 'foo=foo.bar:x [\]')
        self.assertRaises(DistlibException, get_registry_entry, 'foo=foo.bar:x [a=]')
        self.assertRaises(DistlibException, get_registry_entry, 'foo=foo.bar:x [a,]')
        self.assertRaises(DistlibException, get_registry_entry, 'foo=foo.bar:x [a,,b]')
        self.assertRaises(DistlibException, get_registry_entry, 'foo=foo.bar:x [a b]')

    def test_resolve(self):
        import logging
        import logging.handlers
        self.assertIs(resolve('logging', None), logging)
        self.assertIs(resolve('logging.handlers', None), logging.handlers)
        self.assertIs(resolve('logging', 'root'), logging.root)
        self.assertEqual(resolve('logging', 'root.debug'), logging.root.debug)

    def test_cache_base(self):
        actual = get_cache_base()
        if os.name == 'nt' and 'LOCALAPPDATA' in os.environ:
            expected = os.path.expandvars('$localappdata')
        else:
            expected = os.path.expanduser('~')
        expected = os.path.join(expected, '.distlib')
        self.assertEqual(expected, actual)
        self.assertTrue(os.path.isdir(expected))

    @unittest.skipIf(os.name != 'posix', 'Test is only valid for POSIX')
    def test_path_to_cache_dir_posix(self):
        self.assertEqual(path_to_cache_dir('/home/user/some-file.zip'),
                        '--home--user--some-file.zip.cache')

    @unittest.skipIf(os.name != 'nt', 'Test is only valid for Windows')
    def test_path_to_cache_dir_nt(self):
        self.assertEqual(path_to_cache_dir(r'c:\Users\User\Some-File.zip'),
                        'c-----Users--User--Some-File.zip.cache')

    def test_parse_credentials(self):
        self.assertEqual(parse_credentials('example.com', ),
                         (None, None, 'example.com'))
        self.assertEqual(parse_credentials('user@example.com', ),
                         ('user', None, 'example.com'))
        self.assertEqual(parse_credentials('user:pwd@example.com', ),
                         ('user', 'pwd', 'example.com'))
