#
# Copyright (C) 2012 Vinay Sajip. All rights reserved.
#
import os
import shutil
import subprocess
import sys
import tempfile

from compat import unittest

from distlib import DistlibException
from distlib.scripts import ScriptMaker

HERE = os.path.abspath(os.path.dirname(__file__))

class ScriptTestCase(unittest.TestCase):

    def setUp(self):
        source_dir = os.path.join(HERE, 'scripts')
        target_dir = tempfile.mkdtemp()
        self.maker = ScriptMaker(source_dir, target_dir, add_launchers=False)

    def tearDown(self):
        shutil.rmtree(self.maker.target_dir)

    def test_shebangs(self):
        if sys.platform == 'darwin' and ('__VENV_LAUNCHER__'
                                         in os.environ):
            executable =  os.environ['__VENV_LAUNCHER__']
        else:
            executable = sys.executable
        executable = executable.encode('utf-8')
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

    def test_multiple(self):
        specs = ('foo.py', 'script1.py', 'script2.py', 'script3.py',
                 'shell.sh')
        files = self.maker.make_multiple(specs)
        self.assertEqual(len(specs), len(files))
        self.assertEqual(set(specs), set([os.path.basename(f) for f in files]))
        ofiles = os.listdir(self.maker.target_dir)
        self.assertEqual(set(specs), set(ofiles))

    def test_callable(self):
        for name in ('main', 'other_main'):
            spec = 'foo = foo:' + name
            files = self.maker.make(spec)
            self.assertEqual(len(files), 1)
            d, f = os.path.split(files[0])
            self.assertEqual(f, 'foo')
            self.assertEqual(d, self.maker.target_dir)
            with open(files[0], 'r') as f:
                text = f.read()
            self.assertIn("_resolve('foo', '%s')" % name, text)

    @unittest.skipIf(os.name != 'nt', 'Test is Windows-specific')
    def test_launchers(self):
        tlauncher = self.maker._get_launcher('t')
        self.maker.add_launchers = True
        specs = ('foo.py', 'script1.py', 'script2.py', 'script3.py',
                 'shell.sh')
        files = self.maker.make_multiple(specs)
        self.assertEqual(len(specs), len(files) - 3)
        filenames = set([os.path.basename(f) for f in files])
        self.assertEqual(filenames, set(('foo.py', 'script1-script.py',
                                         'script1.exe', 'script2-script.py',
                                         'script2.exe', 'script3-script.py',
                                         'script3.exe', 'shell.sh')))
        for fn in files:
            if fn.endswith('.exe'):
                with open(fn, 'rb') as f:
                    data = f.read()
                self.assertEqual(data, tlauncher)

    @unittest.skipIf(os.name != 'nt', 'Test is Windows-specific')
    def test_windows(self):
        wlauncher = self.maker._get_launcher('w')
        self.maker.add_launchers = True
        executable = sys.executable.encode('utf-8')
        files = self.maker.make('script4.py')
        self.assertEqual(len(files), 2)
        filenames = set([os.path.basename(f) for f in files])
        self.assertEqual(filenames, set(('script4-script.pyw', 'script4.exe')))
        for fn in files:
            if fn.endswith('.exe'):
                with open(fn, 'rb') as f:
                    data = f.read()
                self.assertEqual(data, wlauncher)
            elif fn.endswith(('.py', '.pyw')):
                with open(fn, 'rb') as f:
                    data = f.readline()
                    self.assertIn(executable, data)

    def test_dry_run(self):
        self.maker.dry_run = True
        specs = ('foo.py', 'foo = foo:main')
        files = self.maker.make_multiple(specs)
        self.assertEqual(len(specs), len(files))
        self.assertEqual(set(('foo.py', 'foo')),
                         set([os.path.basename(f) for f in files]))
        ofiles = os.listdir(self.maker.target_dir)
        self.assertFalse(ofiles)

    def test_script_run(self):
        files = self.maker.make('test = cgi:print_directory')
        self.assertEqual(len(files), 1)
        p = subprocess.Popen([sys.executable, files[0]],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        self.assertIn(b'<H3>Current Working Directory:</H3>', stdout)
        self.assertIn(os.getcwd().encode('utf-8'), stdout)

    def test_mode(self):
        files = self.maker.make('foo = foo:main')
        self.assertEqual(len(files), 1)
        f = files[0]
        self.assertIn(os.stat(f).st_mode & 0o7777, (0o644, 0o664))
        self.maker.set_mode = True
        files = self.maker.make('bar = bar:main')
        self.assertEqual(len(files), 1)
        f = files[0]
        self.assertIn(os.stat(f).st_mode & 0o7777, (0o755, 0o775))

    def test_callable_format(self):
        get_callable = self.maker.get_callable
        self.assertIsNone(get_callable('foo.py'))
        self.assertIsNone(get_callable('foo.py='))
        self.assertIsNone(get_callable('foo.py=abc'))
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
        self.assertRaises(DistlibException, get_callable, 'foo=foo.bar:x:y')
        self.assertRaises(DistlibException, get_callable, 'foo=foo.bar:x [')
        self.assertRaises(DistlibException, get_callable, 'foo=foo.bar:x ]')
        self.assertRaises(DistlibException, get_callable, 'foo=foo.bar:x []')
        self.assertRaises(DistlibException, get_callable, 'foo=foo.bar:x [\]')
        self.assertRaises(DistlibException, get_callable, 'foo=foo.bar:x [a=]')
        self.assertRaises(DistlibException, get_callable, 'foo=foo.bar:x [a,]')
        self.assertRaises(DistlibException, get_callable, 'foo=foo.bar:x [a,,b]')
        self.assertRaises(DistlibException, get_callable, 'foo=foo.bar:x [a b]')

