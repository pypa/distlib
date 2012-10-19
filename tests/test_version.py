# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 The Python Software Foundation.
# See LICENSE.txt and CONTRIBUTORS.txt.
#
"""Tests for distlib.version."""
import doctest

from compat import unittest

from distlib.version import NormalizedVersion as V
from distlib.version import HugeMajorVersionNumError, IrrationalVersionError
from distlib.version import suggest_normalized_version as suggest
from distlib.version import VersionPredicate
from distlib.version import legacy_version_key
from distlib.version import is_semver, semver_key


class VersionTestCase(unittest.TestCase):

    versions = ((V('1.0'), '1.0'),
                (V('1.1'), '1.1'),
                (V('1.2.3'), '1.2.3'),
                (V('1.2'), '1.2'),
                (V('1.2.3a4'), '1.2.3a4'),
                (V('1.2c4'), '1.2c4'),
                (V('4.17rc2'), '4.17rc2'),
                (V('1.2.3.4'), '1.2.3.4'),
                (V('1.2.3.4.0b3', drop_trailing_zeros=True), '1.2.3.4b3'),
                (V('1.2.0.0.0', drop_trailing_zeros=True), '1.2'),
                (V('1.0.dev345'), '1.0.dev345'),
                (V('1.0.post456.dev623'), '1.0.post456.dev623'))

    def test_repr(self):
        self.assertEqual(repr(V('1.0')), "NormalizedVersion('1.0')")

    def test_basic_versions(self):
        for v, s in self.versions:
            self.assertEqual(str(v), s)

    def test_hash(self):
        for v, s in self.versions:
            self.assertEqual(hash(v), hash(V(s)))

        versions = set([v for v, s in self.versions])
        for v, s in self.versions:
            self.assertIn(v, versions)

        self.assertEqual(set([V('1.0')]), set([V('1.0'), V('1.0')]))

    def test_from_parts(self):
        for v, s in self.versions:
            v2 = V.from_parts(*v.parts)
            self.assertEqual(v, v2)
            self.assertEqual(str(v), str(v2))

    def test_irrational_versions(self):
        irrational = ('1', '1.2a', '1.2.3b',
                      #'1.02', '1.2a03', '1.2a3.04',
                      '1.2.dev.2', '1.2dev', '1.2.dev',
                      '1.2.dev2.post2', '1.2.post2.dev3.post4')

        for s in irrational:
            self.assertRaises(IrrationalVersionError, V, s)

    def test_huge_version(self):
        self.assertEqual(str(V('1980.0')), '1980.0')
        self.assertRaises(HugeMajorVersionNumError, V, '1981.0')
        self.assertEqual(str(V('1981.0', error_on_huge_major_num=False)),
                         '1981.0')

    def test_comparison(self):
        comparison_doctest_string = r"""
        >>> V('1.2.0') == '1.2'
        Traceback (most recent call last):
        ...
        TypeError: cannot compare NormalizedVersion and str

        >>> V('1.2') < '1.3'
        Traceback (most recent call last):
        ...
        TypeError: cannot compare NormalizedVersion and str

        >>> V('1.2.0') == V('1.2')
        True
        >>> V('1.2.0') == V('1.2.3')
        False
        >>> V('1.2.0') != V('1.2.3')
        True
        >>> V('1.2.0') < V('1.2.3')
        True
        >>> V('1.2.0') < V('1.2.0')
        False
        >>> V('1.2.0') <= V('1.2.0')
        True
        >>> V('1.2.0') <= V('1.2.3')
        True
        >>> V('1.2.3') <= V('1.2.0')
        False
        >>> V('1.2.0') >= V('1.2.0')
        True
        >>> V('1.2.3') >= V('1.2.0')
        True
        >>> V('1.2.0') >= V('1.2.3')
        False
        >>> V('1.2.0rc1') >= V('1.2.0')
        False
        >>> V('1.0') > V('1.0b2')
        True
        >>> V('1.0') > V('1.0c2')
        True
        >>> V('1.0') > V('1.0rc2')
        True
        >>> V('1.0rc2') > V('1.0rc1')
        True
        >>> V('1.0c4') > V('1.0c1')
        True
        >>> (V('1.0') > V('1.0c2') > V('1.0c1') > V('1.0b2') > V('1.0b1')
        ...  > V('1.0a2') > V('1.0a1'))
        True
        >>> (V('1.0.0') > V('1.0.0c2') > V('1.0.0c1') > V('1.0.0b2') > V('1.0.0b1')
        ...  > V('1.0.0a2') > V('1.0.0a1'))
        True

        >>> V('1.0') < V('1.0.post456.dev623')
        True

        >>> V('1.0.post456.dev623') < V('1.0.post456')  < V('1.0.post1234')
        True

        >>> (V('1.0a1')
        ...  < V('1.0a2.dev456')
        ...  < V('1.0a2')
        ...  < V('1.0a2.1.dev456')  # e.g. need to do a quick post release on 1.0a2
        ...  < V('1.0a2.1')
        ...  < V('1.0b1.dev456')
        ...  < V('1.0b2')
        ...  < V('1.0c1.dev456')
        ...  < V('1.0c1')
        ...  < V('1.0.dev7')
        ...  < V('1.0.dev18')
        ...  < V('1.0.dev456')
        ...  < V('1.0.dev1234')
        ...  < V('1.0rc1')
        ...  < V('1.0rc2')
        ...  < V('1.0')
        ...  < V('1.0.post456.dev623')  # development version of a post release
        ...  < V('1.0.post456'))
        True
        """
        doctest.script_from_examples(comparison_doctest_string)

        # the doctest above is never run, so temporarily add real unit
        # tests until the doctest is rewritten
        self.assertLessEqual(V('1.2.0rc1'), V('1.2.0'))
        self.assertGreater(V('1.0'), V('1.0c2'))
        self.assertGreater(V('1.0'), V('1.0rc2'))
        self.assertGreater(V('1.0rc2'), V('1.0rc1'))
        self.assertGreater(V('1.0c4'), V('1.0c1'))

    def test_suggest_normalized_version(self):
        self.assertEqual(suggest('1.0'), '1.0')
        self.assertEqual(suggest('1.0-alpha1'), '1.0a1')
        self.assertEqual(suggest('1.0c2'), '1.0c2')
        self.assertEqual(suggest('walla walla washington'), None)
        self.assertEqual(suggest('2.4c1'), '2.4c1')
        self.assertEqual(suggest('v1.0'), '1.0')

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
        self.assertEqual(suggest('9.0.0+r2363'), '9.0.0.post2363')

        # pre-releases are using markers like "pre1"
        self.assertEqual(suggest('9.0.0pre1'), '9.0.0c1')

        # we want to be able to parse Tcl-TK
        # they us "p1" "p2" for post releases
        self.assertEqual(suggest('1.4p1'), '1.4.post1')

    def test_predicate(self):
        # VersionPredicate knows how to parse stuff like:
        #
        #   Project (>=version, ver2)

        predicates = ('zope.interface (>3.5.0)',
                      'AnotherProject (3.4)',
                      'OtherProject (<3.0)',
                      'NoVersion',
                      'Hey (>=2.5,<2.7)')

        for predicate in predicates:
            VersionPredicate(predicate)

        self.assertTrue(VersionPredicate('Hey (>=2.5,<2.7)').match('2.6'))
        self.assertTrue(VersionPredicate('Ho').match('2.6'))
        self.assertFalse(VersionPredicate('Hey (>=2.5,!=2.6,<2.7)').match('2.6'))
        self.assertTrue(VersionPredicate('Ho (<3.0)').match('2.6'))
        self.assertTrue(VersionPredicate('Ho (<3.0,!=2.5)').match('2.6.0'))
        self.assertFalse(VersionPredicate('Ho (<3.0,!=2.6)').match('2.6.0'))
        self.assertTrue(VersionPredicate('Ho (2.5)').match('2.5.4'))
        self.assertFalse(VersionPredicate('Ho (!=2.5)').match('2.5.2'))
        self.assertTrue(VersionPredicate('Hey (<=2.5)').match('2.5.9'))
        self.assertFalse(VersionPredicate('Hey (<=2.5)').match('2.6.0'))
        self.assertTrue(VersionPredicate('Hey (>=2.5)').match('2.5.1'))

        self.assertRaises(ValueError, VersionPredicate, '')

        self.assertTrue(VersionPredicate('Hey 2.5').match('2.5.1'))

        # XXX need to silent the micro version in this case
        self.assertFalse(VersionPredicate('Ho (<3.0,!=2.6)').match('2.6.3'))

        # Make sure a predicate that ends with a number works
        self.assertTrue(VersionPredicate('virtualenv5 (1.0)').match('1.0'))
        self.assertTrue(VersionPredicate('virtualenv5').match('1.0'))
        self.assertTrue(VersionPredicate('vi5two').match('1.0'))
        self.assertTrue(VersionPredicate('5two').match('1.0'))
        self.assertTrue(VersionPredicate('vi5two 1.0').match('1.0'))
        self.assertTrue(VersionPredicate('5two 1.0').match('1.0'))

        # test repr
        for predicate in predicates:
            self.assertEqual(str(VersionPredicate(predicate)), predicate)

    def test_predicate_name(self):
        # Test that names are parsed the right way

        self.assertEqual('Hey', VersionPredicate('Hey (<1.1)').name)
        self.assertEqual('Foo-Bar', VersionPredicate('Foo-Bar (1.1)').name)
        self.assertEqual('Foo Bar', VersionPredicate('Foo Bar (1.1)').name)

    def test_is_final(self):
        # VersionPredicate knows is a distribution is a final one or not.
        final_versions = ('1.0', '1.0.post456')
        other_versions = ('1.0.dev1', '1.0a2', '1.0c3')

        for version in final_versions:
            self.assertTrue(V(version).is_final)
        for version in other_versions:
            self.assertFalse(V(version).is_final)

    def test_micro_predicate(self):
        self.assertNotEqual(V('3.4.0'), V('3.4'))
        predicate = VersionPredicate('zope.event (3.4.0)')
        self.assertTrue(predicate.match('3.4.0'))
        self.assertFalse(predicate.match('3.4.1'))


class VersionWhiteBoxTestCase(unittest.TestCase):

    def test_parse_numdots(self):
        # For code coverage completeness, as pad_zeros_length can't be set or
        # influenced from the public interface
        self.assertEqual(
            V('1.0')._parse_numdots('1.0', '1.0', pad_zeros_length=3),
            [1, 0, 0])


class LegacyVersionTestCase(unittest.TestCase):
    # These tests are the same as distribute's
    def test_equality(self):
        def compare(a, b):
            ka, kb = legacy_version_key(a), legacy_version_key(b)
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
            ka, kb = legacy_version_key(a), legacy_version_key(b)
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
        compare('2.1.0','2.1.0-rc0')
        compare('2.1.0','2.1.0-a')
        compare('2.1.0','2.1.0-alpha')
        compare('2.1.0','2.1.0-foo')
        compare('1.0','1.0-1')
        compare('1.0-1','1.0.1')
        compare('1.0a','1.0b')
        compare('1.0dev','1.0rc1')
        compare('1.0pre','1.0')
        compare('1.0pre','1.0')
        compare('1.0a','1.0-a')
        compare('1.0rc1','1.0-rc1')

        versions = """
        0.80.1-3 0.80.1-2 0.80.1-1 0.79.9999+0.80.0pre4-1
        0.79.9999+0.80.0pre2-3 0.79.9999+0.80.0pre2-2
        0.77.2-1 0.77.1-1 0.77.0-1
        """.split()

        for i, v1 in enumerate(versions):
            for v2 in versions[i+1:]:
                compare(v2, v1)


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
            self.assertRaises(ValueError, semver_key, s)

        for s in good:
            self.assertTrue(is_semver(s))

    def test_ordering(self):
        def compare(a, b):
            ka, kb = semver_key(a), semver_key(b)
            self.assertLess(ka, kb)

        # From the semver.org home page
        versions = [
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
        ]

        for i, v1 in enumerate(versions):
            for v2 in versions[i+1:]:
                compare(v1, v2)

def test_suite():
    #README = os.path.join(os.path.dirname(__file__), 'README.txt')
    #suite = [doctest.DocFileSuite(README), unittest.makeSuite(VersionTestCase)]
    suite = [unittest.makeSuite(VersionTestCase),
             unittest.makeSuite(VersionWhiteBoxTestCase),
             unittest.makeSuite(LegacyVersionTestCase),
             unittest.makeSuite(SemanticVersionTestCase)]
    return unittest.TestSuite(suite)

if __name__ == "__main__":
    unittest.main(defaultTest="test_suite")
