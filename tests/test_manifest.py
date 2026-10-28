# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Vinay Sajip.
# Licensed to the Python Software Foundation under a contributor agreement.
# See LICENSE.txt and CONTRIBUTORS.txt.
#
import logging
import logging.handlers
import os
import re

from compat import unittest
from support import DistlibTestCase, TempdirManager, skip_unless_symlink

from distlib import DistlibException
from distlib.manifest import Manifest

logger = logging.getLogger(__name__)

HERE = os.path.abspath(os.path.dirname(__file__))


class ManifestTestCase(DistlibTestCase):

    def setUp(self):
        self.base = os.path.join(HERE, 'testsrc')
        self.manifest = Manifest(self.base)

    def get_files(self, files):
        return set([os.path.relpath(p, self.base) for p in files])

    def test_findall(self):
        mf = self.manifest
        mf.findall()
        actual = self.get_files(mf.allfiles)
        expected = set([
            '.hidden',
            'README.txt',
            'LICENSE',
            os.path.join('subdir', 'somedata.txt'),
            os.path.join('subdir', 'lose', 'lose.txt'),
            os.path.join('subdir', 'subsubdir', 'somedata.bin'),
            os.path.join('keep', 'keep.txt'),
        ])
        self.assertEqual(actual, expected)

    def test_add(self):
        mf = self.manifest
        mf.add('README.txt')
        actual = self.get_files(mf.files)
        expected = set(['README.txt'])
        self.assertEqual(actual, expected)

    def test_add_many(self):
        mf = self.manifest
        mf.add_many(['README.txt', 'LICENSE'])
        actual = self.get_files(mf.files)
        expected = set(['README.txt', 'LICENSE'])
        self.assertEqual(actual, expected)

    def test_clear(self):
        mf = self.manifest
        mf.findall()
        mf.add('abc')
        self.assertTrue(mf.files)
        mf.clear()
        self.assertFalse(mf.files)
        self.assertFalse(mf.allfiles)

    def test_invalid(self):
        mf = self.manifest
        self.assertRaises(DistlibException, mf.process_directive, 'random abc')
        for directive in ('', ' ', '\t\r\n'):
            self.assertRaises(DistlibException, mf.process_directive, directive)
        for cmd in ('include', 'exclude', 'global-include', 'global-exclude'):
            self.assertRaises(DistlibException, mf.process_directive, cmd)
        for cmd in ('recursive-include', 'recursive-exclude'):
            s = '%s dir' % cmd
            self.assertRaises(DistlibException, mf.process_directive, s)
        for cmd in ('prune', 'graft'):
            self.assertRaises(DistlibException, mf.process_directive, cmd)
            s = '%s abc def' % cmd
            self.assertRaises(DistlibException, mf.process_directive, s)

    def test_default_action(self):
        mf = self.manifest
        mf.process_directive('*')
        actual = self.get_files(mf.files)
        expected = set(['.hidden', 'README.txt', 'LICENSE'])
        self.assertEqual(actual, expected)

    def test_include(self):
        mf = self.manifest
        mf.process_directive('include README.txt LICENSE')
        actual = self.get_files(mf.files)
        expected = set(['README.txt', 'LICENSE'])
        self.assertEqual(actual, expected)

    def test_exclude(self):
        mf = self.manifest
        mf.process_directive('global-include *.txt')
        mf.process_directive('exclude README.txt')
        actual = self.get_files(mf.files)
        expected = set([
            os.path.join('keep', 'keep.txt'),
            os.path.join('subdir', 'somedata.txt'),
            os.path.join('subdir', 'lose', 'lose.txt'),
        ])
        self.assertEqual(actual, expected)

    def test_exclude_regex_str(self):
        mf = self.manifest
        mf.process_directive('global-include *.txt')
        mf._exclude_pattern(r'R.*\.txt', is_regex=True)
        actual = self.get_files(mf.files)
        expected = set([
            os.path.join('keep', 'keep.txt'),
            os.path.join('subdir', 'somedata.txt'),
            os.path.join('subdir', 'lose', 'lose.txt'),
        ])
        self.assertEqual(actual, expected)

    def test_exclude_regex_re(self):
        mf = self.manifest
        mf.process_directive('global-include *.txt')
        mf._exclude_pattern(re.compile(r'R.*\.txt'), is_regex=True)
        actual = self.get_files(mf.files)
        expected = set([
            os.path.join('keep', 'keep.txt'),
            os.path.join('subdir', 'somedata.txt'),
            os.path.join('subdir', 'lose', 'lose.txt'),
        ])
        self.assertEqual(actual, expected)

    def test_global_include(self):
        mf = self.manifest
        mf.process_directive('global-include *.txt')
        actual = self.get_files(mf.files)
        expected = set([
            'README.txt',
            os.path.join('keep', 'keep.txt'),
            os.path.join('subdir', 'somedata.txt'),
            os.path.join('subdir', 'lose', 'lose.txt'),
        ])
        self.assertEqual(actual, expected)

    def test_global_exclude(self):
        mf = self.manifest
        mf.process_directive('global-include *.txt')
        mf.process_directive('global-exclude *d*.txt')
        actual = self.get_files(mf.files)
        expected = set([
            'README.txt',
            os.path.join('keep', 'keep.txt'),
            os.path.join('subdir', 'lose', 'lose.txt'),
        ])
        self.assertEqual(actual, expected)

    def test_recursive_include(self):
        mf = self.manifest
        mf.process_directive('recursive-include subdir *.txt')
        actual = self.get_files(mf.files)
        expected = set([
            os.path.join('subdir', 'somedata.txt'),
            os.path.join('subdir', 'lose', 'lose.txt'),
        ])
        self.assertEqual(actual, expected)

    def test_recursive_exclude(self):
        mf = self.manifest
        mf.process_directive('global-include *.txt')
        mf.process_directive('recursive-exclude subdir *d*.txt')
        actual = self.get_files(mf.files)
        expected = set([
            'README.txt',
            os.path.join('keep', 'keep.txt'),
            os.path.join('subdir', 'lose', 'lose.txt'),
        ])
        self.assertEqual(actual, expected)

    def test_graft(self):
        mf = self.manifest
        mf.process_directive('graft keep')
        actual = self.get_files(mf.files)
        expected = set([
            os.path.join('keep', 'keep.txt'),
        ])
        self.assertEqual(actual, expected)

    def test_prune(self):
        mf = self.manifest
        mf.process_directive('graft subdir')
        mf.process_directive('prune subdir/lose')
        actual = self.get_files(mf.files)
        expected = set([
            os.path.join('subdir', 'somedata.txt'),
            os.path.join('subdir', 'subsubdir', 'somedata.bin'),
        ])
        self.assertEqual(actual, expected)

    def test_sorting(self):
        mf = self.manifest
        mf.process_directive('global-include *')
        actual = self.get_files(mf.sorted())
        expected = set([
            '.hidden',
            'LICENSE',
            'README.txt',
            os.path.join('subdir', 'somedata.txt'),
            os.path.join('subdir', 'lose', 'lose.txt'),
            os.path.join('subdir', 'subsubdir', 'somedata.bin'),
            os.path.join('keep', 'keep.txt'),
        ])
        self.assertEqual(actual, expected)

    def test_find_warnings(self):
        mf = self.manifest
        lines = (
            'include nonexistent',
            'exclude nonexistent',
            'global-include nonexistent',
            'global-exclude nonexistent',
            'recursive-include subdir nonexistent',
            'recursive-exclude subdir nonexistent',
            'graft nonexistent',
            'prune nonexistent',
        )
        h = logging.handlers.MemoryHandler(len(lines))
        dl_logger = logging.getLogger('distlib.manifest')
        dl_logger.addHandler(h)
        try:
            for line in lines:
                mf.process_directive(line)
        finally:
            dl_logger.removeHandler(h)
        h.close()
        actual = [r.getMessage() for r in h.buffer]
        expected = [
            "no files found matching 'nonexistent'",
            # "no previously-included files found matching 'nonexistent'",
            "no files found matching 'nonexistent' anywhere in distribution",
            # "no previously-included files matching 'nonexistent' found "
            #    "anywhere in distribution",
            "no files found matching 'nonexistent' under directory 'subdir'",
            # "no previously-included files matching 'nonexistent' found under "
            #    "directory 'subdir'",
            "no directories found matching 'nonexistent'",
            "no previously-included directories found matching 'nonexistent'",
        ]
        self.assertEqual(actual, expected)


class ManifestSymlinkTestCase(TempdirManager, DistlibTestCase):

    def setUp(self):
        super(ManifestSymlinkTestCase, self).setUp()
        self.base = self.mkdtemp()
        self.manifest = Manifest(self.base)

    @skip_unless_symlink
    def test_findall_file_symlinks(self):
        target = os.path.join(self.base, 'actual.txt')
        self.write_file(target)
        os.symlink('actual.txt', os.path.join(self.base, 'relative.txt'))
        os.symlink(target, os.path.join(self.base, 'absolute.txt'))
        os.symlink('relative.txt', os.path.join(self.base, 'chained.txt'))
        self.manifest.findall()
        expected = set(os.path.join(self.base, name) for name in
                       ('actual.txt', 'relative.txt', 'absolute.txt', 'chained.txt'))
        self.assertEqual(set(self.manifest.allfiles), expected)

    @skip_unless_symlink
    def test_include_file_symlink(self):
        self.write_file(os.path.join(self.base, 'actual.txt'))
        link = os.path.join(self.base, 'LICENSE')
        os.symlink('actual.txt', link)
        self.manifest.process_directive('include LICENSE')
        self.assertEqual(self.manifest.sorted(), [link])

    @skip_unless_symlink
    def test_findall_skips_directory_and_broken_symlinks(self):
        directory = self.mkdtemp()
        self.write_file(os.path.join(directory, 'outside.txt'))
        os.symlink(directory, os.path.join(self.base, 'directory'))
        os.symlink('.', os.path.join(self.base, 'loop'))
        os.symlink('missing.txt', os.path.join(self.base, 'broken.txt'))
        self.manifest.findall()
        self.assertEqual(self.manifest.allfiles, [])


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
