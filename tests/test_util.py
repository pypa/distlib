from compat import unittest

from distlib import DistlibException
from distlib.util import get_callable

class UtilTestCase(unittest.TestCase):
    def test_callable_format(self):
        self.assertIsNone(get_callable('foo.py'))
        self.assertIsNone(get_callable('foo.py='))
        for spec in ('foo=foo:main', 'foo =foo:main', 'foo= foo:main',
                     'foo = foo:main'):
            self.assertEqual(get_callable(spec),
                             ('foo', 'foo', 'main', []))
        self.assertEqual(get_callable('foo=foo.bar:main'),
                             ('foo', 'foo.bar', 'main', []))
        self.assertEqual(get_callable('foo=foo.bar:main [a]'),
                             ('foo', 'foo.bar', 'main', ['a']))
        self.assertEqual(get_callable('foo=foo.bar:main [a=b, c=d,e, f=g]'),
                             ('foo', 'foo.bar', 'main', ['a=b', 'c=d',
                                                         'e', 'f=g']))
        self.assertEqual(get_callable('foo=foo.bar:main [a=9, 9=8,e, f9=g8]'),
                             ('foo', 'foo.bar', 'main', ['a=9', '9=8',
                                                         'e', 'f9=g8']))
        self.assertEqual(get_callable('foo=foo.bar:main[x]'),
                             ('foo', 'foo.bar', 'main', ['x']))
        self.assertEqual(get_callable('foo=abc'), ('foo', 'abc', None, []))
        self.assertRaises(DistlibException, get_callable, 'foo=foo.bar:x:y')
        self.assertRaises(DistlibException, get_callable, 'foo=foo.bar:x [')
        self.assertRaises(DistlibException, get_callable, 'foo=foo.bar:x ]')
        self.assertRaises(DistlibException, get_callable, 'foo=foo.bar:x []')
        self.assertRaises(DistlibException, get_callable, 'foo=foo.bar:x [\]')
        self.assertRaises(DistlibException, get_callable, 'foo=foo.bar:x [a=]')
        self.assertRaises(DistlibException, get_callable, 'foo=foo.bar:x [a,]')
        self.assertRaises(DistlibException, get_callable, 'foo=foo.bar:x [a,,b]')
        self.assertRaises(DistlibException, get_callable, 'foo=foo.bar:x [a b]')
