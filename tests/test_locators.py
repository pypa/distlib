# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 The Python Software Foundation.
# See LICENSE.txt and CONTRIBUTORS.txt.
#
from __future__ import unicode_literals
import os
import sys

from compat import unittest

from distlib.compat import url2pathname, urlparse, urljoin
from distlib.database import DistributionPath, make_graph
from distlib.locators import (SimpleScrapingLocator, PyPIRPCLocator,
                              PyPIJSONLocator, DirectoryLocator,
                              DistPathLocator, AggregatingLocator,
                              JSONLocator, DistPathLocator,
                              DependencyFinder,
                              get_all_distribution_names, default_locator)

HERE = os.path.abspath(os.path.dirname(__file__))

PYPI_RPC_HOST = 'http://python.org/pypi'
PYPI_WEB_HOST = os.environ.get('PYPI_WEB_HOST', 'http://pypi.python.org')

class LocatorTestCase(unittest.TestCase):

    @unittest.skipIf('SKIP_SLOW' in os.environ, 'Skipping slow test')
    def test_xmlrpc(self):
        locator = PyPIRPCLocator(PYPI_RPC_HOST)
        result = locator.get_project('sarge')
        self.assertIn('0.1', result)
        dist = result['0.1']
        self.assertEqual(dist.name, 'sarge')
        self.assertEqual(dist.version, '0.1')
        self.assertEqual(dist.download_url,
                         'http://pypi.python.org/packages/source/s/sarge/'
                         'sarge-0.1.tar.gz')
        self.assertEqual(dist.md5_digest,
                         '961ddd9bc085fdd8b248c6dd96ceb1c8')
        names = locator.get_distribution_names()
        self.assertGreater(len(names), 25000)

    @unittest.skipIf('SKIP_SLOW' in os.environ, 'Skipping slow test')
    def test_json(self):
        locator = PyPIJSONLocator(PYPI_RPC_HOST)
        result = locator.get_project('sarge')
        self.assertIn('0.1', result)
        dist = result['0.1']
        self.assertEqual(dist.name, 'sarge')
        self.assertEqual(dist.version, '0.1')
        self.assertEqual(dist.download_url,
                         'http://pypi.python.org/packages/source/s/sarge/'
                         'sarge-0.1.tar.gz')
        self.assertEqual(dist.md5_digest,
                         '961ddd9bc085fdd8b248c6dd96ceb1c8')
        self.assertRaises(NotImplementedError, locator.get_distribution_names)

    @unittest.skipIf('SKIP_SLOW' in os.environ, 'Skipping slow test')
    def test_scraper(self):
        locator = SimpleScrapingLocator('http://pypi.python.org/simple/')
        for name in ('sarge', 'Sarge'):
            result = locator.get_project(name)
            self.assertIn('0.1', result)
            dist = result['0.1']
            self.assertEqual(dist.name, 'sarge')
            self.assertEqual(dist.version, '0.1')
            self.assertEqual(dist.download_url,
                             'http://pypi.python.org/packages/source/s/sarge/'
                             'sarge-0.1.tar.gz')
            self.assertEqual(dist.md5_digest,
                             '961ddd9bc085fdd8b248c6dd96ceb1c8')
        names = locator.get_distribution_names()
        self.assertGreater(len(names), 25000)

    @unittest.skipIf('SKIP_SLOW' in os.environ, 'Skipping slow test')
    def test_unicode_project_name(self):
        # Just checking to see that no exceptions are raised.
        NAME = '\u2603'
        locator = SimpleScrapingLocator('http://pypi.python.org/simple/')
        result = locator.get_project(NAME)
        self.assertFalse(result)
        locator = PyPIJSONLocator('http://pypi.python.org/pypi/')
        result = locator.get_project(NAME)
        self.assertFalse(result)

    def test_dir(self):
        d = os.path.join(HERE, 'fake_archives')
        locator = DirectoryLocator(d)
        expected = os.path.join(HERE, 'fake_archives', 'subdir',
                                'subsubdir', 'Flask-0.9.tar.gz')
        def get_path(url):
            t = urlparse(url)
            return url2pathname(t.path)

        for name in ('flask', 'Flask'):
            result = locator.get_project(name)
            self.assertIn('0.9', result)
            dist = result['0.9']
            self.assertEqual(dist.name, 'Flask')
            self.assertEqual(dist.version, '0.9')
            self.assertEqual(get_path(dist.download_url), expected)
        names = locator.get_distribution_names()
        expected = set(['Flask', 'python-gnupg', 'coverage', 'Django'])
        self.assertEqual(names, expected)

    def test_path(self):
        fakes = os.path.join(HERE, 'fake_dists')
        sys.path.insert(0, fakes)
        try:
            edp = DistributionPath(include_egg=True)
            locator = DistPathLocator(edp)
            cases = ('babar', 'choxie', 'strawberry', 'towel-stuff',
                     'coconuts-aster', 'bacon', 'grammar', 'truffles',
                     'banana', 'cheese')
            for name in cases:
                d = locator.locate(name)
                r = locator.get_project(name)
                self.assertIsNotNone(d)
                self.assertEqual(r, { d.version: d })
            d = locator.locate('nonexistent')
            r = locator.get_project('nonexistent')
            self.assertIsNone(d)
            self.assertFalse(r)

        finally:
            sys.path.pop(0)

    @unittest.skipIf('SKIP_SLOW' in os.environ, 'Skipping slow test')
    def test_aggregation(self):
        d = os.path.join(HERE, 'fake_archives')
        loc1 = DirectoryLocator(d)
        loc2 = SimpleScrapingLocator('http://pypi.python.org/simple/',
                                     timeout=1.0)
        locator = AggregatingLocator(loc1, loc2)
        exp1 = os.path.join(HERE, 'fake_archives', 'subdir',
                            'subsubdir', 'Flask-0.9.tar.gz')
        exp2 = 'http://pypi.python.org/packages/source/F/Flask/Flask-0.9.tar.gz'
        result = locator.get_project('flask')
        self.assertEqual(len(result), 1)
        self.assertIn('0.9', result)
        dist = result['0.9']
        self.assertEqual(dist.name, 'Flask')
        self.assertEqual(dist.version, '0.9')
        scheme, _, path, _, _, _ = urlparse(dist.download_url)
        self.assertEqual(scheme, 'file')
        self.assertEqual(url2pathname(path), exp1)
        locator.merge = True
        locator._cache.clear()
        result = locator.get_project('flask')
        self.assertGreater(len(result), 1)
        self.assertIn('0.9', result)
        dist = result['0.9']
        self.assertEqual(dist.name, 'Flask')
        self.assertEqual(dist.version, '0.9')
        self.assertEqual(dist.download_url, exp2)
        n1 = loc1.get_distribution_names()
        n2 = loc2.get_distribution_names()
        self.assertEqual(locator.get_distribution_names(), n1 | n2)

    def test_dependency_finder(self):
        locator = AggregatingLocator(
            JSONLocator(),
            SimpleScrapingLocator('http://pypi.python.org/simple/',
                                  timeout=3.0),
            scheme='legacy')
        finder = DependencyFinder(locator)
        dists, problems = finder.find('irc (5.0.1)')
        self.assertFalse(problems)
        actual = sorted([d.name_and_version for d in dists])
        self.assertEqual(actual, ['hgtools (2.0.2)', 'irc (5.0.1)',
                                  'pytest-runner (1.2)'])
        dists, problems = finder.find('irc (5.0.1)', True)  # include tests
        self.assertFalse(problems)
        actual = sorted([d.name_and_version for d in dists])
        self.assertEqual(actual, ['hgtools (2.0.2)', 'irc (5.0.1)',
                                  'py (1.4.12)', 'pytest (2.3.4)',
                                  'pytest-runner (1.2)'])

        g = make_graph(dists)
        slist, cycle = g.topological_sort()
        self.assertFalse(cycle)
        names = [d.name for d in slist]
        self.assertEqual(names, ['py', 'hgtools', 'pytest',
                                 'pytest-runner', 'irc'])

        # Test with extras
        dists, problems = finder.find('Jinja2 (2.6)')
        self.assertFalse(problems)
        actual = sorted([d.name_and_version for d in dists])
        self.assertEqual(actual, ['Jinja2 (2.6)'])
        dists, problems = finder.find('Jinja2 [i18n] (2.6)')
        self.assertFalse(problems)
        actual = sorted([d.name_and_version for d in dists])
        self.assertEqual(actual[-1], 'Jinja2 (2.6)')
        self.assertTrue(actual[0].startswith('Babel ('))
        actual = [d.build_time_dependency for d in dists]
        self.assertEqual(actual, [False, False])

    def test_get_all_dist_names(self):
        for url in (None, PYPI_RPC_HOST):
            all_dists = get_all_distribution_names(url)
            self.assertGreater(len(all_dists), 0)

    def test_url_preference(self):
        cases = (('http://netloc/path', 'https://netloc/path'),
                 ('http://pypi.python.org/path', 'http://netloc/path'),
                 ('http://netloc/B', 'http://netloc/A'))
        for url1, url2 in cases:
            self.assertEqual(default_locator.prefer_url(url1, url2), url1)


    def test_dist_reqts(self):
        r = 'config (<=0.3.5)'
        dist = default_locator.locate(r)
        self.assertIsNotNone(dist)
        self.assertIsNone(dist.extras)
        self.assertTrue(dist.matches_requirement(r))
        self.assertFalse(dist.matches_requirement('config (0.3.6)'))

    def test_dist_reqts_extras(self):
        r = 'config[doc,test](<=0.3.5)'
        dist = default_locator.locate(r)
        self.assertIsNotNone(dist)
        self.assertTrue(dist.matches_requirement(r))
        self.assertEqual(dist.extras, ['doc', 'test'])
