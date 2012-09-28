"""Tests for distlib.glob."""
import os

from compat import unittest

from support import TempdirManager

from distlib.glob import iglob, RICH_GLOB

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

if __name__ == '__main__':
    unittest.main()
