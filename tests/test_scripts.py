import os
import shutil
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

    def test_basic(self):
        files = self.maker.make('foo.py')
        self.assertEqual(len(files), 1)
        d, f = os.path.split(files[0])
        self.assertEqual(f, 'foo.py')
        self.assertEqual(d, self.maker.target_dir)

