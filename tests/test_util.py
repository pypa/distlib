# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2013 Vinay Sajip.
# Licensed to the Python Software Foundation under a contributor agreement.
# See LICENSE.txt and CONTRIBUTORS.txt.
#
from io import BytesIO
from itertools import islice
import os
import re
import shutil
try:
    import ssl
except ImportError:
    ssl = None
import sys
import tempfile
import textwrap
import time

from compat import unittest

from support import TempdirManager

from distlib import DistlibException
from distlib.compat import cache_from_source,  Container
from distlib.util import (get_export_entry, ExportEntry, resolve,
                          get_cache_base, path_to_cache_dir, zip_dir,
                          parse_credentials, ensure_slash, split_filename,
                          EventMixin, Sequencer, unarchive, Progress,
                          iglob, RICH_GLOB, parse_requirement, get_extras,
                          Configurator, read_exports, write_exports,
                          FileOperator, is_string_sequence, get_package_data,
                          convert_path)


HERE = os.path.dirname(os.path.abspath(__file__))


class TestContainer(object):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


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
        self.check_entry(get_export_entry('smc++ = smcpp.frontend:console'), 'smc++',
                                          'smcpp.frontend', 'console', [])
        self.assertRaises(DistlibException, get_export_entry, 'foo=foo.bar:x:y')
        self.assertRaises(DistlibException, get_export_entry, 'foo=foo.bar:x [')
        self.assertRaises(DistlibException, get_export_entry, 'foo=foo.bar:x ]')
        self.assertRaises(DistlibException, get_export_entry, 'foo=foo.bar:x []')
        self.assertRaises(DistlibException, get_export_entry, 'foo=foo.bar:x [\\]')
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
        cases = (
            ('example.com', (None, None, 'example.com')),
            ('user@example.com',  ('user', None, 'example.com')),
            ('user:pwd@example.com', ('user', 'pwd', 'example.com')),
            ('user:@example.com', ('user', '', 'example.com')),
            ('user:pass@word@example.com', ('user', 'pass@word', 'example.com')),
            ('user:pass:word@example.com', ('user', 'pass:word', 'example.com')),
            ('user%3Aname:%23%5E%40@example.com', ('user:name', '#^@', 'example.com')),
        )

        for s, expected in cases:
            self.assertEqual(parse_credentials(s), expected)

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
        self.assertEqual(split_filename('greenlet-0.4.0-py27-win32'),
                         ('greenlet', '0.4.0', '27'))
        self.assertEqual(split_filename('greenlet-0.4.0-py27-linux_x86_64'),
                         ('greenlet', '0.4.0', '27'))
        self.assertEqual(split_filename('django-altuser-v0.6.8'),
                         ('django-altuser', 'v0.6.8', None))
        self.assertEqual(split_filename('youtube_dl_server-alpha.1'),
                         ('youtube_dl_server', 'alpha.1', None))
        self.assertEqual(split_filename('pytest-xdist-dev'),
                         ('pytest-xdist', 'dev', None))
        self.assertEqual(split_filename('pytest_xdist-0.1_myfork', None),
                         ('pytest_xdist', '0.1_myfork', None))
        self.assertEqual(split_filename('pytest_xdist-0.1_myfork',
                                        'pytest-xdist'),
                         ('pytest_xdist', '0.1_myfork', None))
        self.assertEqual(split_filename('pytest_xdist-0.1_myfork',
                                        'pytest_dist'),
                         ('pytest_xdist', '0.1_myfork', None))

    def test_convert_path(self):
        CP = convert_path
        if os.sep == '/':
            d = os.path.dirname(__file__)
            self.assertEqual(CP(d), d)
        else:
            self.assertEqual(CP(''), '')
            self.assertRaises(ValueError, CP, '/foo')
            self.assertRaises(ValueError, CP, 'foo/')

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

    def test_sequencer_basic(self):
        seq = Sequencer()

        steps = (
            ('check', 'sdist'),
            ('check', 'register'),
            ('check', 'sdist'),
            ('check', 'register'),
            ('register', 'upload_sdist'),
            ('sdist', 'upload_sdist'),
            ('check', 'build_clibs'),
            ('build_clibs', 'build_ext'),
            ('build_ext', 'build_py'),
            ('build_py', 'build_scripts'),
            ('build_scripts', 'build'),
            ('build', 'test'),
            ('register', 'upload_bdist'),
            ('build', 'upload_bdist'),
            ('build', 'install_headers'),
            ('install_headers', 'install_lib'),
            ('install_lib', 'install_scripts'),
            ('install_scripts', 'install_data'),
            ('install_data', 'install_distinfo'),
            ('install_distinfo', 'install')
        )

        for pred, succ in steps:
            seq.add(pred, succ)

        # Note: these tests are sensitive to dictionary ordering
        # but work under Python 2.6, 2.7, 3.2, 3.3, 3.4 and PyPy 2.5
        cases = (
            ('check', ['check']),
            ('register', ['check', 'register']),
            ('sdist', ['check', 'sdist']),
            ('build_clibs', ['check', 'build_clibs']),
            ('build_ext', ['check', 'build_clibs', 'build_ext']),
            ('build_py', ['check', 'build_clibs', 'build_ext', 'build_py']),
            ('build_scripts', ['check', 'build_clibs', 'build_ext', 'build_py',
                               'build_scripts']),
            ('build', ['check', 'build_clibs', 'build_ext', 'build_py',
                       'build_scripts', 'build']),
            ('test', ['check', 'build_clibs', 'build_ext', 'build_py',
                      'build_scripts', 'build', 'test']),
            ('install_headers', ['check', 'build_clibs', 'build_ext',
                                 'build_py', 'build_scripts', 'build',
                                 'install_headers']),
            ('install_lib', ['check', 'build_clibs', 'build_ext', 'build_py',
                             'build_scripts', 'build', 'install_headers',
                             'install_lib']),
            ('install_scripts', ['check', 'build_clibs', 'build_ext',
                                 'build_py', 'build_scripts', 'build',
                                 'install_headers', 'install_lib',
                                 'install_scripts']),
            ('install_data', ['check', 'build_clibs', 'build_ext', 'build_py',
                              'build_scripts', 'build', 'install_headers',
                              'install_lib', 'install_scripts',
                              'install_data']),
            ('install_distinfo', ['check', 'build_clibs', 'build_ext',
                                  'build_py', 'build_scripts', 'build',
                                  'install_headers', 'install_lib',
                                  'install_scripts', 'install_data',
                                  'install_distinfo']),
            ('install', ['check', 'build_clibs', 'build_ext', 'build_py',
                         'build_scripts', 'build', 'install_headers',
                         'install_lib', 'install_scripts', 'install_data',
                         'install_distinfo', 'install']),
            ('upload_sdist', (['check', 'register', 'sdist', 'upload_sdist'],
                              ['check', 'sdist', 'register', 'upload_sdist'])),
            ('upload_bdist', (['check', 'build_clibs', 'build_ext', 'build_py',
                               'build_scripts', 'build', 'register',
                               'upload_bdist'],
                              ['check', 'build_clibs', 'build_ext', 'build_py',
                               'build_scripts', 'register', 'build',
                               'upload_bdist'])),
        )

        for final, expected in cases:
            actual = list(seq.get_steps(final))
            if isinstance(expected, tuple):
                self.assertIn(actual, expected)
            else:
                self.assertEqual(actual, expected)

        dot = seq.dot
        expected = '''
        digraph G {
          check -> build_clibs;
          install_lib -> install_scripts;
          register -> upload_bdist;
          build -> upload_bdist;
          build_ext -> build_py;
          install_scripts -> install_data;
          check -> sdist;
          check -> register;
          build -> install_headers;
          install_data -> install_distinfo;
          sdist -> upload_sdist;
          register -> upload_sdist;
          install_distinfo -> install;
          build -> test;
          install_headers -> install_lib;
          build_py -> build_scripts;
          build_clibs -> build_ext;
          build_scripts -> build;
        }
        '''
        expected = textwrap.dedent(expected).strip().splitlines()
        actual = dot.splitlines()
        self.assertEqual(expected[0], actual[0])
        self.assertEqual(expected[-1], actual[-1])
        self.assertEqual(set(expected[1:-1]), set(actual[1:-1]))
        actual = seq.strong_connections
        expected = (
            [
                ('test',), ('upload_bdist',), ('install',),
                ('install_distinfo',), ('install_data',), ('install_scripts',),
                ('install_lib',), ('install_headers',), ('build',),
                ('build_scripts',), ('build_py',), ('build_ext',),
                ('build_clibs',), ('upload_sdist',), ('sdist',), ('register',),
                ('check',)
            ],
            [
                ('install',), ('install_distinfo',), ('install_data',),
                ('install_scripts',), ('install_lib',), ('install_headers',),
                ('test',), ('upload_bdist',), ('build',), ('build_scripts',),
                ('build_py',), ('build_ext',), ('build_clibs',),
                ('upload_sdist',), ('sdist',), ('register',), ('check',)
            ],
            [
                ('upload_sdist',), ('sdist',), ('install',),
                ('install_distinfo',), ('install_data',), ('upload_bdist',),
                ('register',), ('install_scripts',), ('install_lib',),
                ('install_headers',), ('test',), ('build',),
                ('build_scripts',), ('build_py',), ('build_ext',),
                ('build_clibs',), ('check',)
            ],
            # Next case added for PyPy
            [
                ('upload_sdist',), ('sdist',), ('upload_bdist',), ('register',),
                ('test',), ('install',), ('install_distinfo',),
                ('install_data',), ('install_scripts',), ('install_lib',),
                ('install_headers',), ('build',), ('build_scripts',),
                ('build_py',), ('build_ext',), ('build_clibs',), ('check',)
            ],
            # Next case added for Python 3.6
            [
                ('upload_sdist',), ('sdist',), ('upload_bdist',), ('register',),
                ('install',), ('install_distinfo',), ('install_data',),
                ('install_scripts',), ('install_lib',), ('install_headers',),
                ('test',), ('build',), ('build_scripts',), ('build_py',),
                ('build_ext',), ('build_clibs',), ('check',)
            ]
        )
        self.assertIn(actual, expected)

    def test_sequencer_cycle(self):
        seq = Sequencer()
        seq.add('A', 'B')
        seq.add('B', 'C')
        seq.add('C', 'D')
        self.assertEqual(list(seq.get_steps('D')), ['A', 'B', 'C', 'D'])
        seq.add('C', 'A')
        self.assertEqual(list(seq.get_steps('D')), ['C', 'A', 'B', 'D'])
        self.assertFalse(seq.is_step('E'))
        self.assertRaises(ValueError, seq.get_steps, 'E')
        seq.add_node('E')
        self.assertTrue(seq.is_step('E'))
        self.assertEqual(list(seq.get_steps('E')), ['E'])
        seq.remove_node('E')
        self.assertFalse(seq.is_step('E'))
        self.assertRaises(ValueError, seq.get_steps, 'E')
        seq.remove('C', 'A')
        self.assertEqual(list(seq.get_steps('D')), ['A', 'B', 'C', 'D'])

    def test_sequencer_removal(self):
        seq = Sequencer()
        seq.add('A', 'B')
        seq.add('B', 'C')
        seq.add('C', 'D')
        preds = {
            'B': set(['A']),
            'C': set(['B']),
            'D': set(['C'])
        }
        succs =  {
            'A': set(['B']),
            'B': set(['C']),
            'C': set(['D'])
        }
        self.assertEqual(seq._preds, preds)
        self.assertEqual(seq._succs, succs)
        seq.remove_node('C')
        self.assertEqual(seq._preds, preds)
        self.assertEqual(seq._succs, succs)
        seq.remove_node('C', True)
        self.assertEqual(seq._preds, {'B': set(['A'])})
        self.assertEqual(seq._succs, {'A': set(['B'])})

    def test_unarchive(self):
        import zipfile, tarfile

        good_archives = (
            ('good.zip', zipfile.ZipFile, 'r', 'namelist'),
            ('good.tar', tarfile.open, 'r', 'getnames'),
            ('good.tar.gz', tarfile.open, 'r:gz', 'getnames'),
            ('good.tar.bz2', tarfile.open, 'r:bz2', 'getnames'),
        )
        bad_archives = ('bad.zip', 'bad.tar', 'bad.tar.gz', 'bad.tar.bz2')

        for name, cls, mode, lister in good_archives:
            td = tempfile.mkdtemp()
            archive = None
            try:
                name = os.path.join(HERE, name)
                unarchive(name, td)
                archive = cls(name, mode)
                names = getattr(archive, lister)()
                for name in names:
                    p = os.path.join(td, name)
                    self.assertTrue(os.path.exists(p))
            finally:
                shutil.rmtree(td)
                if archive:
                    archive.close()

        for name in bad_archives:
            name = os.path.join(HERE, name)
            td = tempfile.mkdtemp()
            try:
                self.assertRaises(ValueError, unarchive, name, td)
            finally:
                shutil.rmtree(td)

    def test_string_sequence(self):
        self.assertTrue(is_string_sequence(['a']))
        self.assertTrue(is_string_sequence(['a', 'b']))
        self.assertFalse(is_string_sequence(['a', 'b', None]))
        self.assertRaises(AssertionError, is_string_sequence, [])

    @unittest.skipIf('SKIP_ONLINE' in os.environ, 'Skipping online test')
    @unittest.skipUnless(ssl, 'SSL required for this test.')
    def test_package_data(self):
        data = get_package_data(name='config', version='0.3.6')
        self.assertTrue(data)
        self.assertTrue('index-metadata' in data)
        metadata = data['index-metadata']
        self.assertEqual(metadata['name'], 'config')
        self.assertEqual(metadata['version'], '0.3.6')
        data = get_package_data(name='config', version='0.3.5')
        self.assertFalse(data)

    def test_zip_dir(self):
        d = os.path.join(HERE, 'foofoo')
        data = zip_dir(d)
        self.assertIsInstance(data, BytesIO)

    def test_configurator(self):
        d = {
            'a': 1,
            'b': 2.0,
            'c': 'xyz',
            'd': 'inc://' + os.path.join(HERE, 'included.json'),
            'e': 'inc://' + 'included.json',
            'stderr': 'ext://sys.stderr',
            'list_o_stuff': [
                'cfg://stderr',
                'ext://sys.stdout',
                'ext://logging.NOTSET',
            ],
            'dict_o_stuff': {
                'k1': 'cfg://list_o_stuff[1]',
                'k2': 'abc',
                'k3': 'cfg://list_o_stuff',
            },
            'another_dict_o_stuff': {
                'k1': 'cfg://dict_o_stuff[k2]',
                'k2': 'ext://re.I',
                'k3': 'cfg://dict_o_stuff[k3][0]',
            },
            'custom': {
                '()': __name__ + '.TestContainer',
                '[]': [1, 'a', 2.0, ('b', 'c', 'd')],
                '.': {
                    'p1': 'a',
                    'p2': 'b',
                    'p3': {
                        '()' : __name__ + '.TestContainer',
                        '[]': [1, 2],
                        '.': {
                            'p1': 'c',
                        },
                    },
                },
                'k1': 'v1',
                'k2': 'v2',
            }
        }

        cfg = Configurator(d, HERE)
        self.assertEqual(cfg['a'], 1)
        self.assertEqual(cfg['b'], 2.0)
        self.assertEqual(cfg['c'], 'xyz')
        self.assertIs(cfg['stderr'], sys.stderr)
        self.assertIs(cfg['list_o_stuff'][0], sys.stderr)
        self.assertIs(cfg['list_o_stuff'][1], sys.stdout)
        self.assertIs(cfg['list_o_stuff'][-1], 0)   # logging.NOTSET == 0
        self.assertIs(cfg['dict_o_stuff']['k1'], sys.stdout)
        self.assertIs(cfg['another_dict_o_stuff']['k1'], 'abc')
        self.assertIs(cfg['another_dict_o_stuff']['k2'], re.I)
        self.assertIs(cfg['another_dict_o_stuff']['k3'], sys.stderr)
        custom = cfg['custom']
        self.assertIsInstance(custom, TestContainer)
        self.assertEqual(custom.args, (1, 'a', 2.0, ('b', 'c', 'd')))
        self.assertEqual(custom.kwargs, {'k1': 'v1', 'k2': 'v2'})
        self.assertEqual(custom.p1, 'a')
        self.assertEqual(custom.p2, 'b')
        self.assertIsInstance(custom.p3, TestContainer)
        self.assertEqual(custom.p3.args, (1, 2))
        self.assertEqual(custom.p3.kwargs, {})
        self.assertEqual(custom.p3.p1, 'c')
        self.assertEqual(cfg['d'], {'foo': 'bar', 'bar': 'baz'})
        self.assertEqual(cfg['e'], {'foo': 'bar', 'bar': 'baz'})


def _speed_range(min_speed, max_speed):
    return tuple(['%d KB/s' % v for v in range(min_speed,
                                               max_speed + 1)])

def _eta_range(min_eta, max_eta, prefix='ETA '):
    msg = prefix + ': 00:00:%02d'
    return tuple([msg % v for v in range(min_eta, max_eta + 1)])

class ProgressTestCase(unittest.TestCase):
    def test_basic(self):

        # These ranges may need tweaking to cater for especially slow
        # machines
        if os.name == 'nt':
            speed1 = _speed_range(18, 20)
            speed2 = _speed_range(20, 22)
        else:
            speed1 = _speed_range(16, 19)
            speed2 = _speed_range(20, 22)
        expected = (
            (' 10 %', _eta_range(4, 7), speed1),
            (' 20 %', _eta_range(4, 7), speed1),
            (' 30 %', _eta_range(3, 4), speed1),
            (' 40 %', _eta_range(3, 3), speed1),
            (' 50 %', _eta_range(2, 2), speed1),
            (' 60 %', _eta_range(2, 2), speed1),
            (' 70 %', _eta_range(1, 1), speed1),
            (' 80 %', _eta_range(1, 1), speed1),
            (' 90 %', _eta_range(0, 0), speed1),
            ('100 %', _eta_range(4, 5, 'Done'), speed2),
        )
        bar = Progress(maxval=100000).start()
        for i, v in enumerate(range(10000, 100000, 10000)):
            time.sleep(0.5)
            bar.update(v)
            p, e, s = expected[i]
            self.assertEqual(bar.percentage, p)
            self.assertIn(bar.ETA, e, p)
            self.assertIn(bar.speed, s)
        bar.stop()
        p, e, s = expected[i + 1]
        self.assertEqual(bar.percentage, p)
        self.assertIn(bar.ETA, e, p)
        self.assertIn(bar.speed, s)

    def test_unknown(self):
        if os.name == 'nt':
            speed = _speed_range(17, 20)
        else:
            speed = _speed_range(17, 19)
        expected = (
            (' ?? %', 'ETA : ??:??:??', speed),
            (' ?? %', 'ETA : ??:??:??', speed),
            (' ?? %', 'ETA : ??:??:??', speed),
            (' ?? %', 'ETA : ??:??:??', speed),
            (' ?? %', 'ETA : ??:??:??', speed),
            (' ?? %', 'ETA : ??:??:??', speed),
            (' ?? %', 'ETA : ??:??:??', speed),
            (' ?? %', 'ETA : ??:??:??', speed),
            (' ?? %', 'ETA : ??:??:??', speed),
            ('100 %', 'Done: 00:00:04', speed),
        )
        bar = Progress(maxval=None).start()
        for i, v in enumerate(range(10000, 100000, 10000)):
            time.sleep(0.5)
            bar.update(v)
            p, e, s = expected[i]
            self.assertEqual(bar.percentage, p)
            self.assertEqual(bar.ETA, e)
            self.assertIn(bar.speed, s)
        bar.stop()
        p, e, s = expected[i + 1]
        self.assertEqual(bar.percentage, p)
        self.assertEqual(bar.ETA, e)
        self.assertIn(bar.speed, s)

class FileOpsTestCase(unittest.TestCase):

    def setUp(self):
        self.fileop = FileOperator()
        self.workdir = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.isdir(self.workdir):
            shutil.rmtree(self.workdir)

    def test_ensure_dir(self):
        td = self.workdir
        os.rmdir(td)
        self.fileop.ensure_dir(td)
        self.assertTrue(os.path.exists(td))
        self.fileop.dry_run = True
        os.rmdir(td)
        self.fileop.ensure_dir(td)
        self.assertFalse(os.path.exists(td))

    def test_ensure_removed(self):
        td = self.workdir
        self.assertTrue(os.path.exists(td))
        self.fileop.dry_run = True
        self.fileop.ensure_removed(td)
        self.assertTrue(os.path.exists(td))
        self.fileop.dry_run = False
        self.fileop.ensure_removed(td)
        self.assertFalse(os.path.exists(td))

    def test_is_writable(self):
        sd = 'subdir'
        ssd = 'subsubdir'
        path = os.path.join(self.workdir, sd, ssd)
        os.makedirs(path)
        path = os.path.join(path, 'test')
        self.assertTrue(self.fileop.is_writable(path))
        if os.name == 'posix':
            self.assertFalse(self.fileop.is_writable('/etc'))

    def test_byte_compile(self):
        path = os.path.join(self.workdir, 'hello.py')
        dpath = cache_from_source(path, True)
        self.fileop.write_text_file(path, 'print("Hello, world!")', 'utf-8')
        self.fileop.byte_compile(path, optimize=False)
        self.assertTrue(os.path.exists(dpath))

    def write_some_files(self):
        path = os.path.join(self.workdir, 'file1')
        written = []
        self.fileop.write_text_file(path, 'test', 'utf-8')
        written.append(path)
        path = os.path.join(self.workdir, 'file2')
        self.fileop.copy_file(written[0], path)
        written.append(path)
        path = os.path.join(self.workdir, 'dir1')
        self.fileop.ensure_dir(path)
        return set(written), set([path])

    def test_copy_check(self):
        srcpath = os.path.join(self.workdir, 'file1')
        self.fileop.write_text_file(srcpath, 'test', 'utf-8')
        dstpath = os.path.join(self.workdir, 'file2')
        os.mkdir(dstpath)
        self.assertRaises(ValueError, self.fileop.copy_file, srcpath,
                          dstpath)
        os.rmdir(dstpath)
        if os.name == 'posix':      # symlinks available
            linkpath = os.path.join(self.workdir, 'file3')
            self.fileop.write_text_file(linkpath, 'linkdest', 'utf-8')
            os.symlink(linkpath, dstpath)
            self.assertRaises(ValueError, self.fileop.copy_file, srcpath,
                              dstpath)

    def test_commit(self):
        # will assert if record isn't set
        self.assertRaises(AssertionError, self.fileop.commit)
        self.fileop.record = True
        expected = self.write_some_files()
        actual = self.fileop.commit()
        self.assertEqual(actual, expected)
        self.assertFalse(self.fileop.record)

    def test_rollback(self):
        # will assert if record isn't set
        self.assertRaises(AssertionError, self.fileop.commit)
        self.fileop.record = True
        expected = self.write_some_files()
        actual = self.fileop.rollback()
        self.assertEqual(os.listdir(self.workdir), [])
        self.assertFalse(self.fileop.record)


class GlobTestCaseBase(TempdirManager, unittest.TestCase):

    def build_files_tree(self, files):
        tempdir = self.mkdtemp()
        for filepath in files:
            is_dir = filepath.endswith('/')
            filepath = os.path.join(tempdir, *filepath.split('/'))
            if is_dir:
                dirname = filepath
            else:
                dirname = os.path.dirname(filepath)
            if dirname and not os.path.exists(dirname):
                os.makedirs(dirname)
            if not is_dir:
                self.write_file(filepath, 'babar')
        return tempdir

    @staticmethod
    def os_dependent_path(path):
        path = path.rstrip('/').split('/')
        return os.path.join(*path)

    def clean_tree(self, spec):
        files = []
        for path, includes in spec.items():
            if includes:
                files.append(self.os_dependent_path(path))
        return sorted(files)


class GlobTestCase(GlobTestCaseBase):

    def assertGlobMatch(self, glob, spec):
        tempdir = self.build_files_tree(spec)
        expected = self.clean_tree(spec)
        os.chdir(tempdir)
        result = sorted(iglob(glob))
        self.assertEqual(expected, result)

    def test_regex_rich_glob(self):
        matches = RICH_GLOB.findall(
                                r"babar aime les {fraises} est les {huitres}")
        self.assertEqual(["fraises", "huitres"], matches)

    def test_simple_glob(self):
        glob = '*.tp?'
        spec = {'coucou.tpl': True,
                 'coucou.tpj': True,
                 'Donotwant': False}
        self.assertGlobMatch(glob, spec)

    def test_simple_glob_in_dir(self):
        glob = os.path.join('babar', '*.tp?')
        spec = {'babar/coucou.tpl': True,
                 'babar/coucou.tpj': True,
                 'babar/toto.bin': False,
                 'Donotwant': False}
        self.assertGlobMatch(glob, spec)

    def test_recursive_glob_head(self):
        glob = os.path.join('**', 'tip', '*.t?l')
        spec = {'babar/zaza/zuzu/tip/coucou.tpl': True,
                 'babar/z/tip/coucou.tpl': True,
                 'babar/tip/coucou.tpl': True,
                 'babar/zeop/tip/babar/babar.tpl': False,
                 'babar/z/tip/coucou.bin': False,
                 'babar/toto.bin': False,
                 'zozo/zuzu/tip/babar.tpl': True,
                 'zozo/tip/babar.tpl': True,
                 'Donotwant': False}
        self.assertGlobMatch(glob, spec)

    def test_recursive_glob_tail(self):
        glob = os.path.join('babar', '**')
        spec = {'babar/zaza/': True,
                'babar/zaza/zuzu/': True,
                'babar/zaza/zuzu/babar.xml': True,
                'babar/zaza/zuzu/toto.xml': True,
                'babar/zaza/zuzu/toto.csv': True,
                'babar/zaza/coucou.tpl': True,
                'babar/bubu.tpl': True,
                'zozo/zuzu/tip/babar.tpl': False,
                'zozo/tip/babar.tpl': False,
                'Donotwant': False}
        self.assertGlobMatch(glob, spec)

    def test_recursive_glob_middle(self):
        glob = os.path.join('babar', '**', 'tip', '*.t?l')
        spec = {'babar/zaza/zuzu/tip/coucou.tpl': True,
                 'babar/z/tip/coucou.tpl': True,
                 'babar/tip/coucou.tpl': True,
                 'babar/zeop/tip/babar/babar.tpl': False,
                 'babar/z/tip/coucou.bin': False,
                 'babar/toto.bin': False,
                 'zozo/zuzu/tip/babar.tpl': False,
                 'zozo/tip/babar.tpl': False,
                 'Donotwant': False}
        self.assertGlobMatch(glob, spec)

    def test_glob_set_tail(self):
        glob = os.path.join('bin', '*.{bin,sh,exe}')
        spec = {'bin/babar.bin': True,
                 'bin/zephir.sh': True,
                 'bin/celestine.exe': True,
                 'bin/cornelius.bat': False,
                 'bin/cornelius.xml': False,
                 'toto/yurg': False,
                 'Donotwant': False}
        self.assertGlobMatch(glob, spec)

    def test_glob_set_middle(self):
        glob = os.path.join('xml', '{babar,toto}.xml')
        spec = {'xml/babar.xml': True,
                 'xml/toto.xml': True,
                 'xml/babar.xslt': False,
                 'xml/cornelius.sgml': False,
                 'xml/zephir.xml': False,
                 'toto/yurg.xml': False,
                 'Donotwant': False}
        self.assertGlobMatch(glob, spec)

    def test_glob_set_head(self):
        glob = os.path.join('{xml,xslt}', 'babar.*')
        spec = {'xml/babar.xml': True,
                 'xml/toto.xml': False,
                 'xslt/babar.xslt': True,
                 'xslt/toto.xslt': False,
                 'toto/yurg.xml': False,
                 'Donotwant': False}
        self.assertGlobMatch(glob, spec)

    def test_glob_all(self):
        dirs = '{%s,%s}' % (os.path.join('xml', '*'),
                            os.path.join('xslt', '**'))
        glob = os.path.join(dirs, 'babar.xml')
        spec = {'xml/a/babar.xml': True,
                 'xml/b/babar.xml': True,
                 'xml/a/c/babar.xml': False,
                 'xslt/a/babar.xml': True,
                 'xslt/b/babar.xml': True,
                 'xslt/a/c/babar.xml': True,
                 'toto/yurg.xml': False,
                 'Donotwant': False}
        self.assertGlobMatch(glob, spec)

    def test_invalid_glob_pattern(self):
        invalids = [
            'ppooa**',
            'azzaeaz4**/',
            '/**ddsfs',
            '**##1e"&e',
            'DSFb**c009',
            '{',
            '{aaQSDFa',
            '}',
            'aQSDFSaa}',
            '{**a,',
            ',**a}',
            '{a**,',
            ',b**}',
            '{a**a,babar}',
            '{bob,b**z}',
        ]
        for pattern in invalids:
            self.assertRaises(ValueError, iglob, pattern)

    def test_parse_requirement(self):
        # Empty requirements
        for empty in ('', '#this should be ignored'):
            self.assertIsNone(parse_requirement(empty))

        # Invalid requirements
        for invalid in ('a (', 'a/', 'a$', 'a [', 'a () [],', 'a 1.2'):
            self.assertRaises(SyntaxError, parse_requirement, invalid)

        # Valid requirements
        def validate(r, values):
            self.assertEqual(r.name, values[0])
            self.assertEqual(r.constraints, values[1])
            self.assertEqual(r.extras, values[2])
            self.assertEqual(r.requirement, values[3])
            self.assertEqual(r.url, values[4])

        r = parse_requirement('a')
        validate(r, ('a', None, None, 'a', None))
        r = parse_requirement('a >= 1.2, <2.0,!=1.7')
        validate(r, ('a', [('>=', '1.2'), ('<', '2.0'), ('!=', '1.7')], None,
                     'a >= 1.2, < 2.0, != 1.7', None))
        r = parse_requirement('a [ab,cd , ef] >= 1.2, <2.0')
        validate(r, ('a', [('>=', '1.2'), ('<', '2.0')], ['ab', 'cd', 'ef'],
                     'a >= 1.2, < 2.0', None))
        r = parse_requirement('a[]')
        validate(r, ('a', None, None, 'a', None))
        r = parse_requirement('a (== 1.2.*, != 1.2.1.*)')
        validate(r, ('a', [('==', '1.2.*'), ('!=', '1.2.1.*')], None,
                 'a == 1.2.*, != 1.2.1.*', None))
        r = parse_requirement('a @ http://domain.com/path#abc=def')
        validate(r, ('a', None, None, 'a', 'http://domain.com/path#abc=def'))
        if False: # TODO re-enable
            for e in ('*', ':*:', ':meta:', '-', '-abc'):
                r = parse_requirement('a [%s]' % e)
                validate(r, ('a', None, [e], 'a', None))

    def test_write_exports(self):
        exports = {
            'foo': {
                'v1': ExportEntry('v1', 'p1', 's1', []),
                'v2': ExportEntry('v2', 'p2', 's2', ['f2=a', 'g2']),
            },
            'bar': {
                'v3': ExportEntry('v3', 'p3', 's3', ['f3', 'g3=h']),
                'v4': ExportEntry('v4', 'p4', 's4', ['f4', 'g4']),
            },
        }

        fd, fn = tempfile.mkstemp()
        try:
            os.close(fd)
            with open(fn, 'wb') as f:
                write_exports(exports, f)
            with open(fn, 'rb') as f:
                actual = read_exports(f)
            self.assertEqual(actual, exports)
        finally:
            os.remove(fn)

    def test_get_extras(self):
        cases = (
            (['*'], ['i18n'], set(['i18n'])),
            (['*', '-bar'], ['foo', 'bar'], set(['foo'])),
        )
        for requested, available, expected in cases:
            actual = get_extras(requested, available)
            self.assertEqual(actual, expected)
if __name__ == '__main__':  # pragma: no cover
    unittest.main()
