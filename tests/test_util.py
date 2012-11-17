from itertools import islice
import os

from compat import unittest

from distlib import DistlibException
from distlib.util import (get_export_entry, ExportEntry, resolve,
                          get_cache_base, path_to_cache_dir,
                          parse_credentials, ensure_slash, split_filename,
                          EventMixin)

class UtilTestCase(unittest.TestCase):
    def check_entry(self, entry, name, prefix, suffix, flags):
        self.assertEqual(entry.name, name)
        self.assertEqual(entry.prefix, prefix)
        self.assertEqual(entry.suffix, suffix)
        self.assertEqual(entry.flags, flags)

    def test_export_entry(self):
        self.assertIsNone(get_export_entry('foo.py'))
        self.assertIsNone(get_export_entry('foo.py='))
        for spec in ('foo=foo:main', 'foo =foo:main', 'foo= foo:main',
                     'foo = foo:main'):
            self.check_entry(get_export_entry(spec),
                             'foo', 'foo', 'main', [])
        self.check_entry(get_export_entry('foo=foo.bar:main'),
                         'foo', 'foo.bar', 'main', [])
        self.check_entry(get_export_entry('foo=foo.bar:main [a]'),
                         'foo', 'foo.bar', 'main', ['a'])
        self.check_entry(get_export_entry('foo=foo.bar:main [ a ]'),
                         'foo', 'foo.bar', 'main', ['a'])
        self.check_entry(get_export_entry('foo=foo.bar:main [a=b, c=d,e, f=g]'),
                         'foo', 'foo.bar', 'main', ['a=b', 'c=d', 'e', 'f=g'])
        self.check_entry(get_export_entry('foo=foo.bar:main [a=9, 9=8,e, f9=g8]'),
                         'foo', 'foo.bar', 'main', ['a=9', '9=8', 'e', 'f9=g8'])
        self.check_entry(get_export_entry('foo=foo.bar:main[x]'),
                         'foo', 'foo.bar', 'main', ['x'])
        self.check_entry(get_export_entry('foo=abc'), 'foo', 'abc', None, [])
        self.assertRaises(DistlibException, get_export_entry, 'foo=foo.bar:x:y')
        self.assertRaises(DistlibException, get_export_entry, 'foo=foo.bar:x [')
        self.assertRaises(DistlibException, get_export_entry, 'foo=foo.bar:x ]')
        self.assertRaises(DistlibException, get_export_entry, 'foo=foo.bar:x []')
        self.assertRaises(DistlibException, get_export_entry, 'foo=foo.bar:x [\]')
        self.assertRaises(DistlibException, get_export_entry, 'foo=foo.bar:x [a=]')
        self.assertRaises(DistlibException, get_export_entry, 'foo=foo.bar:x [a,]')
        self.assertRaises(DistlibException, get_export_entry, 'foo=foo.bar:x [a,,b]')
        self.assertRaises(DistlibException, get_export_entry, 'foo=foo.bar:x [a b]')

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

    def test_ensure_slash(self):
        self.assertEqual(ensure_slash(''), '/')
        self.assertEqual(ensure_slash('/'), '/')
        self.assertEqual(ensure_slash('abc'), 'abc/')
        self.assertEqual(ensure_slash('def/'), 'def/')

    def test_split_filename(self):
        self.assertIsNone(split_filename('abl.jquery'))
        self.assertEqual(split_filename('abl.jquery-1.4.2-2'),
                         ('abl.jquery', '1.4.2-2', None))
        self.assertEqual(split_filename('python-gnupg-0.1'),
                         ('python-gnupg', '0.1', None))
        self.assertEqual(split_filename('baklabel-1.0.3-2729-py3.2'),
                         ('baklabel', '1.0.3-2729', '3.2'))
        self.assertEqual(split_filename('baklabel-1.0.3-2729-py27'),
                         ('baklabel', '1.0.3-2729', '27'))
        self.assertEqual(split_filename('advpy-0.99b'),
                         ('advpy', '0.99b', None))
        self.assertEqual(split_filename('asv_files-dev-20120501-01', 'asv_files'),
                         ('asv_files', 'dev-20120501-01', None))
        #import pdb; pdb.set_trace()
        #self.assertEqual(split_filename('asv_files-test-dev-20120501-01', 'asv_files'),
        #                 ('asv_files-test', 'dev-20120501-01', None))

    def test_events(self):
        collected = []

        def handler1(e, *args, **kwargs):
            collected.append((1, e, args, kwargs))

        def handler2(e, *args, **kwargs):
            collected.append((2, e, args, kwargs))

        def handler3(e, *args, **kwargs):
            if not args:
                raise NotImplementedError('surprise!')
            collected.append((3, e, args, kwargs))
            return (args, kwargs)

        e = EventMixin()
        e.add('A', handler1)
        self.assertRaises(ValueError, e.remove, 'B', handler1)

        cases = (
            ((1, 2), {'buckle': 'my shoe'}),
            ((3, 4), {'shut': 'the door'}),
        )

        for case in cases:
            e.publish('A', *case[0], **case[1])
            e.publish('B', *case[0], **case[1])

        for actual, source in zip(collected, cases):
            self.assertEqual(actual, (1, 'A') + source[:1] + source[1:])

        collected = []
        e.add('B', handler2)

        self.assertEqual(tuple(e.get_subscribers('A')), (handler1,))
        self.assertEqual(tuple(e.get_subscribers('B')), (handler2,))
        self.assertEqual(tuple(e.get_subscribers('C')), ())

        for case in cases:
            e.publish('A', *case[0], **case[1])
            e.publish('B', *case[0], **case[1])

        actuals = islice(collected, 0, None, 2)
        for actual, source in zip(actuals, cases):
            self.assertEqual(actual, (1, 'A') + source[:1] + source[1:])

        actuals = islice(collected, 1, None, 2)
        for actual, source in zip(actuals, cases):
            self.assertEqual(actual, (2, 'B') + source[:1] + source[1:])

        e.remove('B', handler2)

        collected = []

        for case in cases:
            e.publish('A', *case[0], **case[1])
            e.publish('B', *case[0], **case[1])

        for actual, source in zip(collected, cases):
            self.assertEqual(actual, (1, 'A') + source[:1] + source[1:])

        e.add('C', handler3)

        collected = []
        returned = []

        for case in cases:
            returned.extend(e.publish('C', *case[0], **case[1]))
            returned.extend(e.publish('C'))

        for actual, source in zip(collected, cases):
            self.assertEqual(actual, (3, 'C') + source[:1] + source[1:])

        self.assertEqual(tuple(islice(returned, 1, None, 2)), (None, None))
        actuals = islice(returned, 0, None, 2)
        for actual, expected in zip(actuals, cases):
            self.assertEqual(actual, expected)
