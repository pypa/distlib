# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2013 Vinay Sajip.
# Licensed to the Python Software Foundation under a contributor agreement.
# See LICENSE.txt and CONTRIBUTORS.txt.
#
import os
import shutil
import subprocess
import sys
import tempfile

from compat import unittest

from distlib import DistlibException
from distlib.compat import fsencode, sysconfig
from distlib.scripts import ScriptMaker, _enquote_executable
from distlib.util import get_executable

HERE = os.path.abspath(os.path.dirname(__file__))

COPIED_SCRIPT = '''#!python
# This is a copied script
'''

MADE_SCRIPT = 'made = dummy.module:main'


class ScriptTestCase(unittest.TestCase):

    def setUp(self):
        source_dir = os.path.join(HERE, 'scripts')
        target_dir = tempfile.mkdtemp()
        self.maker = ScriptMaker(source_dir, target_dir, add_launchers=False)

    def tearDown(self):
        shutil.rmtree(self.maker.target_dir)

    @unittest.skipIf(sysconfig.is_python_build(), 'Test not appropriate for '
                     'Python source builds')
    def test_shebangs(self):
        executable = fsencode(get_executable())
        for fn in ('foo.py', 'script1.py', 'script2.py', 'script3.py',
                   'shell.sh'):
            files = self.maker.make(fn)
            self.assertEqual(len(files), 1)
            d, f = os.path.split(files[0])
            self.assertEqual(f, fn)
            self.assertEqual(d, self.maker.target_dir)
            if fn.endswith('.py') and fn != 'foo.py':   # no shebang in foo.py
                with open(files[0], 'rb') as f:
                    first_line = f.readline()
                self.assertIn(executable, first_line)

    def test_shebangs_custom_executable(self):
        srcdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, srcdir)
        dstdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, dstdir)
        maker = ScriptMaker(srcdir, dstdir, add_launchers=False)
        maker.executable = 'this_should_appear_in_the_shebang_line'
        #let's create the script to be copied. It has a vanilla shebang line.
        fn = os.path.join(srcdir, 'copied')
        with open(fn, 'w') as f:
            f.write(COPIED_SCRIPT)
        # Let's ask the maker to copy the script, and see what the shebang is
        # in the copy.
        filenames = maker.make('copied')
        with open(filenames[0], 'r') as f:
            actual = f.readline()
        self.assertIn(maker.executable, actual)
        # Now let's make a script from a callable
        filenames = maker.make(MADE_SCRIPT)
        with open(filenames[0], 'r') as f:
            actual = f.readline()
        self.assertIn(maker.executable, actual)

    def test_multiple(self):
        specs = ('foo.py', 'script1.py', 'script2.py', 'script3.py',
                 'shell.sh')
        files = self.maker.make_multiple(specs)
        self.assertEqual(len(specs), len(files))
        expected = set(specs)
        self.assertEqual(expected, set([os.path.basename(f) for f in files]))
        ofiles = os.listdir(self.maker.target_dir)
        self.assertEqual(expected, set(ofiles))

    def test_generation(self):
        self.maker.clobber = True
        for name in ('main', 'other_main'):
            for options in (None, {}, {'gui': False}, {'gui': True}):
                gui = options and options.get('gui', False)
                spec = 'foo = foo:' + name
                files = self.maker.make(spec, options)
                self.assertEqual(len(files), 2)
                actual = set()
                for f in files:
                    d, f = os.path.split(f)
                    actual.add(f)
                if os.name == 'nt':  # pragma: no cover
                    if gui:
                        ext = 'pyw'
                    else:
                        ext = 'py'
                    expected = set(['foo.%s' % ext,
                                    'foo-%s.%s' % (sys.version[:3], ext)])
                else:
                    expected = set(['foo', 'foo-%s' % sys.version[:3]])
                self.assertEqual(actual, expected)
                self.assertEqual(d, self.maker.target_dir)
                for fn in files:
                    with open(fn, 'r') as f:
                        text = f.read()
                    self.assertIn("_resolve('foo', '%s')" % name, text)
                    if options and options['gui'] and os.name == 'nt':  # pragma: no cover
                        first_line, rest = text.split('\n', 1)
                        self.assertIn('pythonw', first_line)

    def test_clobber(self):
        files = self.maker.make('foo = foo:main')
        saved_files = files
        self.assertGreaterEqual(len(files), 2)  # foo, foo-X.Y
        files = self.maker.make('foo = foo:main')
        self.assertFalse(files)
        self.maker.clobber = True
        files = self.maker.make('foo = foo:main')
        self.assertEqual(files, saved_files)

    @unittest.skipIf(os.name != 'nt', 'Test is Windows-specific')
    def test_launchers(self):  # pragma: no cover
        tlauncher = self.maker._get_launcher('t')
        self.maker.add_launchers = True
        specs = ('foo.py', 'script1.py', 'script2.py', 'script3.py',
                 'shell.sh')
        files = self.maker.make_multiple(specs)
        self.assertEqual(len(specs), len(files))
        filenames = set([os.path.basename(f) for f in files])
        self.assertEqual(filenames, set(('foo.py', 'script1.exe',
                                         'script2.exe', 'script3.exe',
                                         'shell.sh')))
        for fn in files:
            if not fn.endswith('.exe'):
                continue
            with open(fn, 'rb') as f:
                data = f.read()
            self.assertTrue(data.startswith(tlauncher))

    @unittest.skipIf(os.name != 'nt', 'Test is Windows-specific')
    def test_windows(self):  # pragma: no cover
        wlauncher = self.maker._get_launcher('w')
        tlauncher = self.maker._get_launcher('t')
        self.maker.add_launchers = True
        executable = os.path.normcase(sys.executable).encode('utf-8')
        wexecutable = executable.replace(b'python.exe', b'pythonw.exe')
        files = self.maker.make('script4.py')
        self.assertEqual(len(files), 1)
        filenames = set([os.path.basename(f) for f in files])
        self.assertEqual(filenames, set(['script4.exe']))
        for fn in files:
            with open(fn, 'rb') as f:
                data = f.read()
            self.assertTrue(data.startswith(wlauncher))
            self.assertIn(executable, data)
        # Now test making scripts gui and console
        files = self.maker.make('foo = foo:main', {'gui': True})
        self.assertEqual(len(files), 2)
        filenames = set([os.path.basename(f) for f in files])
        specific = sys.version[:3]
        self.assertEqual(filenames, set(('foo.exe', 'foo-%s.exe' % specific)))
        for fn in files:
            with open(fn, 'rb') as f:
                data = f.read()
            self.assertTrue(data.startswith(wlauncher))
            self.assertIn(wexecutable, data)

        files = self.maker.make('foo = foo:main')
        self.assertEqual(len(files), 2)
        filenames = set([os.path.basename(f) for f in files])
        self.assertEqual(filenames, set(('foo.exe', 'foo-%s.exe' % specific)))
        for fn in files:
            with open(fn, 'rb') as f:
                data = f.read()
            self.assertTrue(data.startswith(tlauncher))
            self.assertIn(executable, data)

    def test_dry_run(self):
        self.maker.dry_run = True
        self.maker.variants = set([''])
        specs = ('foo.py', 'bar = foo:main')
        files = self.maker.make_multiple(specs)
        self.assertEqual(len(specs), len(files))
        if os.name == 'nt':  # pragma: no cover
            bar = 'bar.py'
        else:
            bar = 'bar'
        self.assertEqual(set(('foo.py', bar)),
                         set([os.path.basename(f) for f in files]))
        ofiles = os.listdir(self.maker.target_dir)
        self.assertFalse(ofiles)

    def test_script_run(self):
        files = self.maker.make('test = cgi:print_directory')
        self.assertEqual(len(files), 2)
        p = subprocess.Popen([sys.executable, files[0]],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        self.assertIn(b'<H3>Current Working Directory:</H3>', stdout)
        self.assertIn(os.getcwd().encode('utf-8'), stdout)

    @unittest.skipUnless(os.name == 'posix', 'Test only valid for POSIX')
    def test_mode(self):
        self.maker.set_mode = False
        files = self.maker.make('foo = foo:main')
        self.assertEqual(len(files), 2)
        for f in files:
            self.assertIn(os.stat(f).st_mode & 0o7777, (0o644, 0o664))
        self.maker.set_mode = True
        files = self.maker.make('bar = bar:main')
        self.assertEqual(len(files), 2)
        for f in files:
            self.assertIn(os.stat(f).st_mode & 0o7777, (0o755, 0o775))

    def test_interpreter_args(self):
        executable = fsencode(get_executable())
        options = {
            'interpreter_args': ['-E', '"foo bar"', 'baz frobozz']
        }
        self.maker.variants = set([''])
        files = self.maker.make('foo = bar:baz', options=options)
        self.assertEqual(len(files), 1)
        with open(files[0], 'rb') as f:
            shebang_line = f.readline()
        self.assertIn(executable, shebang_line)
        self.assertIn(b' -E "foo bar" baz frobozz', shebang_line)

    def test_args_on_copy(self):
        self.maker.variants = set([''])
        self.maker.executable = 'mypython'
        files = self.maker.make('script5.py')
        with open(files[0]) as f:
            actual = f.readline().strip()
        self.assertEqual(actual, '#!mypython -mzippy.activate')
        self.maker.executable = None
        os.remove(files[0])
        files = self.maker.make('script5.py')
        with open(files[0]) as f:
            actual = f.readline().strip()
        expected = '#!%s -mzippy.activate' % get_executable()
        self.assertEqual(actual, expected)

    def test_enquote_executable(self):
        for executable, expected in (
                ('/no/spaces', '/no/spaces'),
                ('/i have/space', '"/i have/space"'),
                ('"/space prequoted"', '"/space prequoted"'),
                ('/usr/bin/env nospaces', '/usr/bin/env nospaces'),
                ('/usr/bin/env with spaces', '/usr/bin/env "with spaces"'),
                ('/usr/bin/env "pre spaced"', '/usr/bin/env "pre spaced"')
                ):
            self.assertEqual(_enquote_executable(executable),
                             expected)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
