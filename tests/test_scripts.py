import os
import shutil
import sys
import tempfile
import unittest

from distlib.scripts import ScriptMaker

HERE = os.path.abspath(os.path.dirname(__file__))

class ScriptTestCase(unittest.TestCase):

    def setUp(self):
        source_dir = os.path.join(HERE, 'scripts')
        target_dir = tempfile.mkdtemp()
        self.maker = ScriptMaker(source_dir, target_dir)

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
        cases = (('main', '.'), ('main', ':'),
                 ('other_main', '.'), ('other_main', ':'))
        for name, sep in cases:
            spec = 'foo = foo%s%s' % (sep, name)
            files = self.maker.make(spec)
            self.assertEqual(len(files), 1)
            d, f = os.path.split(files[0])
            self.assertEqual(f, 'foo')
            self.assertEqual(d, self.maker.target_dir)
            with open(files[0], 'r') as f:
                text = f.read()
            self.assertIn('from foo import %s' % name, text)

