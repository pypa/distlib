#
# Copyright (C) 2012-2013 The Python Software Foundation.
# See LICENSE.txt and CONTRIBUTORS.txt.
#
"""Tests for distlib.version."""
import doctest

from compat import unittest

from distlib.version import (NormalizedVersion as NV, NormalizedMatcher as NM,
                             UnsupportedVersionError,
                             _suggest_normalized_version,
                             _suggest_semantic_version,
                             LegacyVersion as LV, LegacyMatcher as LM,
                             SemanticVersion as SV, SemanticMatcher as SM,
                             is_semver, get_scheme,
                             _normalized_key, _legacy_key, _semantic_key)


class VersionTestCase(unittest.TestCase):

    versions = ((NV('1.0'), '1.0'),
                (NV('1.1'), '1.1'),
                (NV('1.2.3'), '1.2.3'),
                (NV('1.2'), '1.2'),
                (NV('1.2.3a4'), '1.2.3a4'),
                (NV('1.2c4'), '1.2c4'),
                (NV('4.17rc2'), '4.17rc2'),
                (NV('1.2.3.4'), '1.2.3.4'),
                #(NV('1.2.3.4.0b3', drop_trailing_zeros=True), '1.2.3.4b3'),
                #(NV('1.2.0.0.0', drop_trailing_zeros=True), '1.2'),
                (NV('1.0.dev345'), '1.0.dev345'),
                (NV('1.0.post456.dev623'), '1.0.post456.dev623'),
                (NV('1.2.3+1.2'), '1.2.3+1.2'),
                (NV('1.2.3+a1.b2'), '1.2.3+a1.b2'),
               )

    def test_repr(self):
        self.assertEqual(repr(NV('1.0')), "NormalizedVersion('1.0')")

    def test_basic_versions(self):
        for v, s in self.versions:
            self.assertEqual(str(v), s)

    def test_hash(self):
        for v, s in self.versions:
            self.assertEqual(hash(v), hash(NV(s)))

        versions = set([v for v, s in self.versions])
        for v, s in self.versions:
            self.assertIn(v, versions)

        self.assertEqual(set([NV('1.0')]), set([NV('1.0'), NV('1.0')]))

    def test_unsupported_versions(self):
        unsupported = ('1.2a', '1.2.3b',
                      #'1.02', '1.2a03', '1.2a3.04',
                      '1.2.dev.2', '1.2dev', '1.2.dev',
                      '1.2-', '1.2-a',
                      '1.2.dev2.post2', '1.2.post2.dev3.post4')

        for s in unsupported:
            self.assertRaises(UnsupportedVersionError, NV, s)

    def test_huge_version(self):
        self.assertEqual(str(NV('1980.0')), '1980.0')

    def test_comparison(self):
        comparison_doctest_string = r"""
        >>> NV('1.2.0') == '1.2'
        Traceback (most recent call last):
        ...
        TypeError: cannot compare NormalizedVersion and str

        >>> NV('1.2') < '1.3'
        Traceback (most recent call last):
        ...
        TypeError: cannot compare NormalizedVersion and str

        >>> NV('1.2.0') == NV('1.2')
        True
        >>> NV('1.2.0') == NV('1.2.3')
        False
        >>> NV('1.2.0') != NV('1.2.3')
        True
        >>> NV('1.2.0') < NV('1.2.3')
        True
        >>> NV('1.2.0') < NV('1.2.0')
        False
        >>> NV('1.2.0') <= NV('1.2.0')
        True
        >>> NV('1.2.0') <= NV('1.2.3')
        True
        >>> NV('1.2.3') <= NV('1.2.0')
        False
        >>> NV('1.2.0') >= NV('1.2.0')
        True
        >>> NV('1.2.3') >= NV('1.2.0')
        True
        >>> NV('1.2.0') >= NV('1.2.3')
        False
        >>> NV('1.2.0rc1') >= NV('1.2.0')
        False
        >>> NV('1.0') > NV('1.0b2')
        True
        >>> NV('1.0') > NV('1.0c2')
        True
        >>> NV('1.0') > NV('1.0rc2')
        True
        >>> NV('1.0rc2') > NV('1.0rc1')
        True
        >>> NV('1.0c4') > NV('1.0c1')
        True
        >>> (NV('1.0') > NV('1.0c2') > NV('1.0c1') > NV('1.0b2') > NV('1.0b1')
        ...  > NV('1.0a2') > NV('1.0a1'))
        True
        >>> (NV('1.0.0') > NV('1.0.0c2') > NV('1.0.0c1') > NV('1.0.0b2') > NV('1.0.0b1')
        ...  > NV('1.0.0a2') > NV('1.0.0a1'))
        True

        >>> NV('1.0') < NV('1.0.post456.dev623')
        True

        >>> NV('1.0.post456.dev623') < NV('1.0.post456')  < NV('1.0.post1234')
        True

        >>> (NV('1.0a1')
        ...  < NV('1.0a2.dev456')
        ...  < NV('1.0a2')
        ...  < NV('1.0a2.1.dev456')  # e.g. need to do a quick post release on 1.0a2
        ...  < NV('1.0a2.1')
        ...  < NV('1.0b1.dev456')
        ...  < NV('1.0b2')
        ...  < NV('1.0c1.dev456')
        ...  < NV('1.0c1')
        ...  < NV('1.0c1-1')
        ...  < NV('1.0c1-1.1')
        ...  < NV('1.0.dev7')
        ...  < NV('1.0.dev18')
        ...  < NV('1.0.dev456')
        ...  < NV('1.0.dev1234')
        ...  < NV('1.0rc1')
        ...  < NV('1.0rc2')
        ...  < NV('1.0')
        ...  < NV('1.0-1')
        ...  < NV('1.0-1.1')
        ...  < NV('1.0.post456.dev623')  # development version of a post release
        ...  < NV('1.0.post456.dev623-1')
        ...  < NV('1.0.post456.dev623-1.1')
        ...  < NV('1.0.post456')
             < NV('1.0.post456-1')
             < NV('1.0.post456-1.1'))
        True
        """
        doctest.script_from_examples(comparison_doctest_string)

        # the doctest above is never run, so temporarily add real unit
        # tests until the doctest is rewritten
        self.assertLessEqual(NV('1.2.0rc1'), NV('1.2.0'))
        self.assertGreater(NV('1.0'), NV('1.0c2'))
        self.assertGreater(NV('1.0'), NV('1.0rc2'))
        self.assertGreater(NV('1.0rc2'), NV('1.0rc1'))
        self.assertGreater(NV('1.0c4'), NV('1.0c1'))

    def test_suggest_normalized_version(self):
        suggest = _suggest_normalized_version
        self.assertEqual(suggest('1.0'), '1.0')
        self.assertEqual(suggest('1.0-alpha1'), '1.0a1')
        self.assertEqual(suggest('1.0c2'), '1.0c2')
        self.assertEqual(suggest('walla walla washington'), None)
        self.assertEqual(suggest('2.4c1'), '2.4c1')
        self.assertEqual(suggest('v1.0'), 'v1.0')

        # from setuptools
        self.assertEqual(suggest('0.4a1.r10'), '0.4a1.post10')
        self.assertEqual(suggest('0.7a1dev-r66608'), '0.7a1.dev66608')
        self.assertEqual(suggest('0.6a9.dev-r41475'), '0.6a9.dev41475')
        self.assertEqual(suggest('2.4preview1'), '2.4c1')
        self.assertEqual(suggest('2.4pre1'), '2.4c1')
        self.assertEqual(suggest('2.1-rc2'), '2.1c2')

        # from pypi
        self.assertEqual(suggest('0.1dev'), '0.1.dev0')
        self.assertEqual(suggest('0.1.dev'), '0.1.dev0')

        # we want to be able to parse Twisted
        # development versions are like post releases in Twisted
        #self.assertEqual(suggest('9.0.0+r2363'), '9.0.0.post2363')

        # pre-releases are using markers like "pre1"
        self.assertEqual(suggest('9.0.0pre1'), '9.0.0c1')

        # we want to be able to parse Tcl-TK
        # they us "p1" "p2" for post releases
        self.assertEqual(suggest('1.4p1'), '1.4.post1')

    def test_suggestions_other(self):
        suggest = _suggest_semantic_version
        self.assertEqual(suggest(''), '0.0.0')
        self.assertEqual(suggest('1'), '1.0.0')
        self.assertEqual(suggest('1.2'), '1.2.0')

    def test_matcher(self):
        # NormalizedMatcher knows how to parse stuff like:
        #
        #   Project (>=version, ver2)

        constraints = ('zope.interface (>3.5.0)',
                       'AnotherProject (3.4)',
                       'OtherProject (<3.0)',
                       'NoVersion',
                       'Hey (>=2.5,<2.7)')

        for constraint in constraints:
            NM(constraint)

        self.assertTrue(NM('Hey (>=2.5,<2.7)').match('2.6'))
        self.assertTrue(NM('Ho').match('2.6'))
        self.assertFalse(NM('Hey (>=2.5,!=2.6,<2.7)').match('2.6'))
        self.assertTrue(NM('Ho (<3.0)').match('2.6'))
        self.assertTrue(NM('Ho (<3.0,!=2.5)').match('2.6.0'))
        self.assertFalse(NM('Ho (<3.0,!=2.6)').match('2.6.0'))
        self.assertTrue(NM('Ho (2.5)').match('2.5.4'))
        self.assertFalse(NM('Ho (==2.5)').match('2.50'))
        self.assertTrue(NM('Ho (!=2.5)').match('2.5.2'))
        self.assertFalse(NM('Hey (<=2.5)').match('2.5.9'))
        self.assertFalse(NM('Hey (<=2.5)').match('2.6.0'))
        self.assertTrue(NM('Hey (>=2.5)').match('2.5.1'))

        self.assertRaises(ValueError, NM, '')

        # We don't allow
        #self.assertTrue(NM('Hey 2.5').match('2.5.1'))
        #self.assertTrue(NM('vi5two 1.0').match('1.0'))
        #self.assertTrue(NM('5two 1.0').match('1.0'))

        self.assertTrue(NM('Ho (<3.0,!=2.6)').match('2.6.3'))

        # Make sure a constraint that ends with a number works
        self.assertTrue(NM('virtualenv5 (1.0)').match('1.0'))
        self.assertTrue(NM('virtualenv5').match('1.0'))
        self.assertTrue(NM('vi5two').match('1.0'))
        self.assertTrue(NM('5two').match('1.0'))

        # test repr
        for constraint in constraints:
            self.assertEqual(str(NM(constraint)), constraint)

        #Test exact_version
        cases = (
            ('Dummy', False),
            ('Dummy (1.0)', False),
            ('Dummy (<1.0)', False),
            ('Dummy (<=1.0)', False),
            ('Dummy (>1.0)', False),
            ('Dummy (>=1.0)', False),
            ('Dummy (==1.0)', True),
            ('Dummy (===1.0)', True),
            ('Dummy (!=1.0)', False),
        )

        for s, b in cases:
            m = NM(s)
            self.assertEqual(m.exact_version is not None, b)

    def test_matcher_name(self):
        # Test that names are parsed the right way

        self.assertEqual('Hey', NM('Hey (<1.1)').name)
        self.assertEqual('9Hey', NM('9Hey (1.1)').name)
        self.assertEqual('Foo-Bar', NM('Foo-Bar (1.1)').name)
        self.assertEqual('Foo_Bar', NM('Foo_Bar (1.1)').name)
        self.assertEqual('Foo.Bar', NM('Foo.Bar (1.1)').name)

    def test_matcher_local(self):
        self.assertTrue(NM('Foo (>=2.5+1.2)').match('2.6.0+1.3'))
        self.assertFalse(NM('Foo (>=2.6+1.4)').match('2.6.0+1.3'))
        self.assertTrue(NM('Foo (>=2.6)').match('2.6+1.3'))
        # numeric > lexicographic in local versions
        self.assertTrue(NM('Foo (>2.6+a1.4)').match('2.6+1.4'))

    def test_schemes(self):
        cases = (
            ('normalized', (_normalized_key, NV, NM)),
            ('legacy', (_legacy_key, LV, LM)),
            ('semantic', (_semantic_key, SV, SM)),
        )

        for name, values in cases:
            scheme = get_scheme(name)
            key, version, matcher = values
            self.assertIs(key, scheme.key)
            self.assertIs(matcher, scheme.matcher)
            self.assertIs(version, scheme.matcher.version_class)

        self.assertIs(get_scheme('default'), get_scheme('normalized'))

        self.assertRaises(ValueError, get_scheme, 'random')

    def test_prereleases(self):
        pre_releases = (
            '1.0.dev456',
            '1.0a1',
            '1.0a2.dev456',
            '1.0a12.dev456',
            '1.0a12',
            '1.0b1.dev456',
            '1.0b2',
            '1.0b2.post345.dev456',
            '1.0b2.post345',
            '1.0c1.dev456',
            '1.0c1',
            '1.0rc1',
            '1.0.post345.dev456',
            '1.1.dev1',
            '1.1.dev1+1.2',
        )
        final_releases = (
            '1.0',
            '1.0.post345',
            '1.0.post345+2.3',
        )
        for s in pre_releases:
            self.assertTrue(NV(s).is_prerelease)
        for s in final_releases:
            self.assertFalse(NV(s).is_prerelease)

    def test_comparison_pep426(self):
        versions = (
            '1.0.dev456',
            '1.0a1',
            '1.0a2.dev456',
            '1.0a12.dev456',
            '1.0a12',
            '1.0b1.dev456',
            '1.0b2',
            '1.0b2.post345.dev456',
            '1.0b2.post345',
            '1.0c1.dev456',
            '1.0c1',
            '1.0rc1',
            '1.0',
            '1.0.post345.dev456',
            '1.0.post345',
            '1.1.dev1',
        )

        n = len(versions)
        for i in range(n - 1):
            v1 = versions[i]
            v2 = versions[i + 1]
            self.assertLess(NV(v1), NV(v2))

    def test_440(self):
        # compatible release matching
        for s in ('foo (1.2)', 'foo (~= 1.2)'):
            m = NM(s)
            for should_match in ('1.2', '1.3', '1.2.post0'):
                msg = 'Failed for %s' % should_match
                self.assertTrue(m.match(should_match), msg)
            for should_not_match in ('1.0', '1.1', '1.2.dev0', '2.0'):
                msg = 'Failed for %s' % should_not_match
                self.assertFalse(m.match(should_not_match), msg)
        for s in ('foo (1.4.5)', 'foo (~= 1.4.5)', 'foo (1.4.5a4)'):
            m = NM(s)
            for should_match in ('1.4.5', '1.4.6', '1.4.7.dev0'):
                msg = 'Failed for %s' % should_match
                self.assertTrue(m.match(should_match), msg)
            for should_not_match in ('1.5', '1.6', '1.4.5.dev0', '2.4.5'):
                msg = 'Failed for %s' % should_not_match
                self.assertFalse(m.match(should_not_match), msg)
        m = NM('foo (1.4.5.0)')
        for should_match in ('1.4.5.0', '1.4.5.1', '1.4.5.9.post1'):
            msg = 'Failed for %s' % should_match
            self.assertTrue(m.match(should_match), msg)
        for should_not_match in ('1.4.6', '1.5', '2.0'):
            msg = 'Failed for %s' % should_not_match
            self.assertFalse(m.match(should_not_match), msg)

        # prefix matching
        v = '1.1.post1'
        cases = (('(== 1.1)', False),
                 ('(== 1.1.post1)', True),
                 ('(== 1.1.*)', True),
                 ('(!= 1.1)', True),
                 ('(!= 1.1.post1)', False),
                 ('(!= 1.1.*)', False))
        for s, expected in cases:
            m = NM('foo %s' % s)
            actual = m.match(v)
            self.assertEqual(expected, actual, 'Failed for %s' % s)

        # inclusive ordered
        m = NM('foo (<= 1.5)')
        for should_match in ('0.1', '1.4', '1.4.9.post1', '1.5.dev0',
                             '1.5', '1.5.0', '1.5.0.0'):
            msg = 'Failed for %s' % should_match
            self.assertTrue(m.match(should_match), msg)
        for should_not_match in ('1.5.post1', '1.5.post0.dev0', '1.6', '2.0'):
            msg = 'Failed for %s' % should_not_match
            self.assertFalse(m.match(should_not_match), msg)
        m = NM('foo (>= 1.5)')
        for should_match in ('1.5.post1', '1.5.post0.dev0', '1.6', '2.0',
                             '1.5', '1.5.0', '1.5.0.0'):
            msg = 'Failed for %s' % should_match
            self.assertTrue(m.match(should_match), msg)
        for should_not_match in ('0.1', '1.4', '1.4.9.post1', '1.5.dev0'):
            msg = 'Failed for %s' % should_not_match
            self.assertFalse(m.match(should_not_match), msg)

        # exclusive ordered
        m = NM('foo (< 1.5)')
        for should_match in ('0.1', '1.4', '1.4.9.post1'):
            msg = 'Failed for %s' % should_match
            self.assertTrue(m.match(should_match), msg)
        for should_not_match in ('1.5.post1', '1.5.post0.dev0', '1.5.dev0',
                                 '1.5', '1.5.0', '1.5.0.1', '1.6', '2.0'):
            msg = 'Failed for %s' % should_not_match
            self.assertFalse(m.match(should_not_match), msg)
        m = NM('foo (> 1.5)')
        for should_match in ('1.6', '2.0'):
            msg = 'Failed for %s' % should_match
            self.assertTrue(m.match(should_match), msg)
        for should_not_match in ('0.1', '1.4', '1.4.9.post1', '1.5.dev0',
                                 '1.5', '1.5.0', '1.5.post0','1.5.post0.dev0',
                                 '1.5.0.1'):
            msg = 'Failed for %s' % should_not_match
            self.assertFalse(m.match(should_not_match), msg)

        #unusual prefix matching
        m = NM('foo (== 1.2.post0.*)')
        for should_match in ('1.2.post0', '1.2.post0.dev0'):
            msg = 'Failed for %s' % should_match
            self.assertTrue(m.match(should_match), msg)
        for should_not_match in ('1.2', '1.2.dev0'):
            msg = 'Failed for %s' % should_not_match
            self.assertFalse(m.match(should_not_match), msg)

        # invalid
        for op in ('<', '<=', '>', '>=', '~='):
            s = 'foo (%s 1.*)' % op
            self.assertRaises(ValueError, NM, s)
        for v in ('', '1.*.*'):
            s = 'foo (== %s)' % v
            self.assertRaises((SyntaxError, ValueError), NM, s)


class LegacyVersionTestCase(unittest.TestCase):
    # These tests are the same as distribute's
    def test_equality(self):
        def compare(a, b):
            ka, kb = _legacy_key(a), _legacy_key(b)
            self.assertEqual(ka, kb)

        compare('0.4', '0.4.0')
        compare('0.4.0.0', '0.4.0')
        compare('0.4.0-0', '0.4-0')
        compare('0pl1', '0.0pl1')
        compare('0pre1', '0.0c1')
        compare('0.0.0preview1', '0c1')
        compare('0.0c1', '0rc1')
        compare('1.2a1', '1.2.a.1')
        compare('1.2...a', '1.2a')

    def test_ordering(self):
        def compare(a, b):
            ka, kb = _legacy_key(a), _legacy_key(b)
            self.assertLess(ka, kb)

        compare('2.1','2.1.1')
        compare('2.1.0','2.10')
        compare('2a1','2b0')
        compare('2b1','2c0')
        compare('2a1','2.1')
        compare('2.3a1', '2.3')
        compare('2.1-1', '2.1-2')
        compare('2.1-1', '2.1.1')
        compare('2.1', '2.1.1-1')
        compare('2.1', '2.1pl4')
        compare('2.1a0-20040501', '2.1')
        compare('1.1', '02.1')
        compare('A56','B27')
        compare('3.2', '3.2.pl0')
        compare('3.2-1', '3.2pl1')
        compare('3.2pl1', '3.2pl1-1')
        compare('0.4', '4.0')
        compare('0.0.4', '0.4.0')
        compare('0pl1', '0.4pl1')
        compare('2.1dev','2.1a0')
        compare('2.1.0rc1','2.1.0')
        compare('2.1.0-rc0','2.1.0')
        compare('2.1.0-a','2.1.0')
        compare('2.1.0-alpha','2.1.0')
        compare('2.1.0','2.1.0-foo')
        compare('1.0','1.0-1')
        compare('1.0-1','1.0.1')
        compare('1.0a','1.0b')
        compare('1.0dev','1.0rc1')
        compare('1.0pre','1.0')
        compare('1.0pre','1.0')

        versions = """
        0.80.1-3 0.80.1-2 0.80.1-1 0.79.9999+0.80.0pre4-1
        0.79.9999+0.80.0pre2-3 0.79.9999+0.80.0pre2-2
        0.77.2-1 0.77.1-1 0.77.0-1
        """.split()

        for i, v1 in enumerate(versions):
            for v2 in versions[i+1:]:
                compare(v2, v1)

    def test_absolute(self):
        cases = (
            ('1.0-beta6', ('00000001', '*beta', '00000006', '*final')),
        )
        for k, v in cases:
            self.assertEqual(_legacy_key(k), v)

    def test_prereleases(self):
        pre_releases = (
            '2.1.0-alpha',
            '0.79.9999+0.80.0pre4-1',
            '1.0dev',
            '2.1a0',
            '1.0rc1',
            'A56',
            '1.0b',
            '0.79.9999+0.80.0',
            '2013b',
            '2013f',
        )
        final_releases = (
            '0.80.1-3',
            '2.1.0',
            '3.2pl1-1',
        )
        for s in pre_releases:
            self.assertTrue(LV(s).is_prerelease, s)
        for s in final_releases:
            self.assertFalse(LV(s).is_prerelease, s)


class SemanticVersionTestCase(unittest.TestCase):
    def test_basic(self):
        bad = [
            'a', '1', '1.', '1.2' , '1.2.',
            '1.2.a', '1.2.3.a',
        ]
        good = [
            '1.2.3', '1.2.3-pre.1.abc.2.def',
            '1.2.3+post.1.abc.2.def',
            '1.2.3-pre.1.abc.2.def+post.1.abc.2.def',
        ]
        for s in bad:
            self.assertFalse(is_semver(s))
            self.assertRaises(UnsupportedVersionError, _semantic_key, s)

        for s in good:
            self.assertTrue(is_semver(s))

    def test_ordering(self):
        def compare(a, b):
            ka, kb = _semantic_key(a), _semantic_key(b)
            self.assertLess(ka, kb)

        # From the semver.org home page
        versions = (
            '1.0.0-alpha',
            '1.0.0-alpha.1',
            '1.0.0-beta.2',
            '1.0.0-beta.11',
            '1.0.0-rc.1',
            '1.0.0-rc.1+build.1',
            '1.0.0',
            '1.0.0+0.3.7',
            '1.3.7+build',
            '1.3.7+build.2.b8f12d7',
            '1.3.7+build.11.e0f985a',
        )

        for i, v1 in enumerate(versions):
            for v2 in versions[i+1:]:
                compare(v1, v2)

    def test_prereleases(self):
        pre_releases = (
            '1.0.0-alpha',
            '1.0.0-alpha.1',
            '1.0.0-beta.2',
            '1.0.0-beta.11',
            '1.0.0-rc.1',
            '1.0.0-rc.1+build.1',
        )
        final_releases = (
            '1.0.0',
            '1.0.0+0.3.7',
            '1.3.7+build',
            '1.3.7+build.2.b8f12d7',
            '1.3.7+build.11.e0f985a',
        )
        for s in pre_releases:
            self.assertTrue(SV(s).is_prerelease)
        for s in final_releases:
            self.assertFalse(SV(s).is_prerelease)


class CompatibilityTestCase(unittest.TestCase):
    def test_basic(self):
        def are_equal(v1, v2):
            return v1 == v2

        def is_less(v1, v2):
            return v1 < v2

        self.assertRaises(TypeError, are_equal, NV('3.3.0'),
                          SV('3.3.0'))
        self.assertRaises(TypeError, are_equal, NV('3.3.0'),
                          LV('3.3.0'))
        self.assertRaises(TypeError, are_equal, LV('3.3.0'),
                          SV('3.3.0'))
        self.assertRaises(TypeError, are_equal, NM('foo'),
                          LV('foo'))
        self.assertRaises(TypeError, are_equal, NM('foo'),
                          NM('bar'))



def test_suite():
    #README = os.path.join(os.path.dirname(__file__), 'README.txt')
    #suite = [doctest.DocFileSuite(README), unittest.makeSuite(VersionTestCase)]
    suite = [unittest.makeSuite(VersionTestCase),
             unittest.makeSuite(CompatibilityTestCase),
             unittest.makeSuite(LegacyVersionTestCase),
             unittest.makeSuite(SemanticVersionTestCase)]
    return unittest.TestSuite(suite)

if __name__ == "__main__":  # pragma: no cover
    import logging
    import os
    import sys

    here = os.path.dirname(os.path.abspath(__file__))
    rundir = os.path.join(here, 'run')
    if not os.path.exists(rundir):
        os.mkdir(rundir)
    elif not os.path.isdir(rundir):
        raise ValueError('Not a directory: %r' % rundir)
    fn = os.path.join(rundir, 'test_version_%d.%d.log' % sys.version_info[:2])
    logging.basicConfig(level=logging.DEBUG, filename=fn, filemode='w',
                        format='%(name)s %(funcName)s %(message)s')
    unittest.main(defaultTest="test_suite")
