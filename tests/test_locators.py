# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2013 Vinay Sajip.
# Licensed to the Python Software Foundation under a contributor agreement.
# See LICENSE.txt and CONTRIBUTORS.txt.
#
from __future__ import unicode_literals
import os
import posixpath
try:
    import ssl
except ImportError:
    ssl = None
import sys

from compat import unittest

from distlib.compat import url2pathname, urlparse, urljoin
from distlib.database import (Distribution, DistributionPath, make_graph,
                              make_dist)
from distlib.locators import (SimpleScrapingLocator, PyPIRPCLocator,
                              PyPIJSONLocator, DirectoryLocator,
                              DistPathLocator, AggregatingLocator,
                              JSONLocator, DistPathLocator,
                              DependencyFinder, locate,
                              get_all_distribution_names, default_locator)

HERE = os.path.abspath(os.path.dirname(__file__))

PYPI_RPC_HOST = 'http://python.org/pypi'

PYPI_WEB_HOST = os.environ.get('PYPI_WEB_HOST', 'https://pypi.org/simple/')

class LocatorTestCase(unittest.TestCase):

    @unittest.skipIf('SKIP_ONLINE' in os.environ, 'Skipping online test')
    @unittest.skipUnless(ssl, 'SSL required for this test.')
    def test_xmlrpc(self):
        locator = PyPIRPCLocator(PYPI_RPC_HOST)
        try:
            try:
                result = locator.get_project('sarge')
            except Exception:     # pragma: no cover
                raise unittest.SkipTest('PyPI XML-RPC not available')
            self.assertIn('0.1', result)
            dist = result['0.1']
            self.assertEqual(dist.name, 'sarge')
            self.assertEqual(dist.version, '0.1')
            possible = ('https://pypi.org/packages/source/s/sarge/'
                        'sarge-0.1.tar.gz',
                        'http://pypi.org/packages/source/s/sarge/'
                        'sarge-0.1.tar.gz')
            self.assertIn(dist.source_url, possible)
            self.assertEqual(dist.digest,
                             ('md5', '961ddd9bc085fdd8b248c6dd96ceb1c8'))
            try:
                names = locator.get_distribution_names()
            except Exception:   # pragma: no cover
                raise unittest.SkipTest('PyPI XML-RPC not available')
            self.assertGreater(len(names), 25000)
        finally:
            locator.client('close')()

    @unittest.skipIf('SKIP_ONLINE' in os.environ, 'Skipping online test')
    @unittest.skipUnless(ssl, 'SSL required for this test.')
    def test_json(self):
        locator = PyPIJSONLocator(PYPI_RPC_HOST)
        result = locator.get_project('sarge')
        LATEST_SARGE_VERSION = '0.1.4'
        LATEST_SARGE_HASHES = (
            ('md5', '285013875aa908ef1417055d3e74a00a'),
            ('sha256', '59f93216723ddd9062d17cbbb90ed9e69267b84825cf0bde0b7f8d934c424823'),
        )
        self.assertIn(LATEST_SARGE_VERSION, result)
        dist = result[LATEST_SARGE_VERSION]
        self.assertEqual(dist.name, 'sarge')
        self.assertEqual(dist.version, LATEST_SARGE_VERSION)
        path = '/sarge-%s.tar.gz' % LATEST_SARGE_VERSION
        for url in dist.download_urls:
            self.assertTrue(url.endswith(path))
        self.assertIn(dist.digests[url], LATEST_SARGE_HASHES)
        self.assertRaises(NotImplementedError, locator.get_distribution_names)

    @unittest.skipIf('SKIP_ONLINE' in os.environ, 'Skipping online test')
    @unittest.skipUnless(ssl, 'SSL required for this test.')
    def test_scraper(self):
        locator = SimpleScrapingLocator('https://pypi.org/simple/')
        for name in ('sarge', 'Sarge'):
            result = locator.get_project(name)
            self.assertIn('0.1', result)
            dist = result['0.1']
            self.assertEqual(dist.name, 'sarge')
            self.assertEqual(dist.version, '0.1')
            self.assertTrue(dist.source_url.endswith('/sarge-0.1.tar.gz'))
            SARGE_HASHES = (
                ('md5', '961ddd9bc085fdd8b248c6dd96ceb1c8'),
                ('sha256', 'ec2ec0b1c9ed9a77f9b4322c16e4954c93aa00d974a1af931b18eb751e377dfe'),
            )
            self.assertIn(dist.digest, SARGE_HASHES)
        # Test to check issue #112 fix.
        locator.wheel_tags = [('cp27', 'cp27m', 'win_amd64'),
                              ('cp35', 'cp35m', 'win32')]
        result = locator.get_project('simplejson')
        urls = result['urls'].get('3.16.0')
        self.assertTrue(urls)
        self.assertEqual(3, len(urls))
        expected = set(['simplejson-3.16.0-cp27-cp27m-win_amd64.whl',
                        'simplejson-3.16.0-cp35-cp35m-win32.whl',
                        'simplejson-3.16.0.tar.gz'])
        for u in urls:
            p = posixpath.split(urlparse(u).path)[-1]
            self.assertIn(p, expected)
        return
        # The following is too slow
        names = locator.get_distribution_names()
        self.assertGreater(len(names), 25000)

    @unittest.skipIf('SKIP_ONLINE' in os.environ, 'Skipping online test')
    @unittest.skipUnless(ssl, 'SSL required for this test.')
    def test_unicode_project_name(self):
        # Just checking to see that no exceptions are raised.
        NAME = '\u2603'
        locator = SimpleScrapingLocator('https://pypi.org/simple/')
        result = locator.get_project(NAME)
        expected = {'urls': {}, 'digests': {}}
        self.assertEqual(result, expected)
        locator = PyPIJSONLocator('https://pypi.org/pypi/')
        result = locator.get_project(NAME)
        self.assertEqual(result, expected)

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
            self.assertEqual(os.path.normcase(get_path(dist.source_url)),
                             os.path.normcase(expected))
        names = locator.get_distribution_names()
        expected = set(['Flask', 'python-gnupg', 'coverage', 'Django'])
        if sys.version_info[:2] == (2, 7):
            expected.add('config')
        self.assertEqual(names, expected)

    def test_dir_nonrecursive(self):
        d = os.path.join(HERE, 'fake_archives')
        locator = DirectoryLocator(d, recursive=False)
        expected = os.path.join(HERE, 'fake_archives', 'subdir',
                                'subsubdir', 'Flask-0.9.tar.gz')
        def get_path(url):
            t = urlparse(url)
            return url2pathname(t.path)

        for name in ('flask', 'Flask'):
            result = locator.get_project(name)
            self.assertEqual(result, {'urls': {}, 'digests': {}})
        names = locator.get_distribution_names()
        expected = set(['coverage'])
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
                d = locator.locate(name, True)
                self.assertIsNotNone(d)
                r = locator.get_project(name)
                expected = {
                    d.version: d,
                    'urls': {d.version: set([d.source_url])},
                    'digests': {d.version: set([None])}
                }
                self.assertEqual(r, expected)
            d = locator.locate('nonexistent')
            self.assertIsNone(d)
            r = locator.get_project('nonexistent')
            self.assertTrue(len(r) == 2)

        finally:
            sys.path.pop(0)

    @unittest.skipIf('SKIP_ONLINE' in os.environ, 'Skipping online test')
    @unittest.skipUnless(ssl, 'SSL required for this test.')
    def test_aggregation(self):
        d = os.path.join(HERE, 'fake_archives')
        loc1 = DirectoryLocator(d)
        loc2 = SimpleScrapingLocator('https://pypi.org/simple/',
                                     timeout=5.0)
        locator = AggregatingLocator(loc1, loc2)
        exp1 = os.path.join(HERE, 'fake_archives', 'subdir',
                            'subsubdir', 'Flask-0.9.tar.gz')
        exp2 = '/Flask-0.9.tar.gz'
        result = locator.get_project('flask')
        self.assertEqual(len(result), 3)
        self.assertIn('0.9', result)
        dist = result['0.9']
        self.assertEqual(dist.name, 'Flask')
        self.assertEqual(dist.version, '0.9')
        scheme, _, path, _, _, _ = urlparse(dist.source_url)
        self.assertEqual(scheme, 'file')
        self.assertEqual(os.path.normcase(url2pathname(path)),
                         os.path.normcase(exp1))
        locator.merge = True
        locator._cache.clear()
        result = locator.get_project('flask')
        self.assertGreater(len(result), 3)
        self.assertIn('0.9', result)
        dist = result['0.9']
        self.assertEqual(dist.name, 'Flask')
        self.assertEqual(dist.version, '0.9')
        self.assertTrue(dist.source_url.endswith(exp2))
        return
        # The following code is slow because it has
        # to get all the dist names by scraping :-(
        n1 = loc1.get_distribution_names()
        n2 = loc2.get_distribution_names()
        self.assertEqual(locator.get_distribution_names(), n1 | n2)

    @unittest.skipIf('SKIP_ONLINE' in os.environ, 'Skipping online test')
    @unittest.skipUnless(ssl, 'SSL required for this test.')
    def test_dependency_finder(self):
        locator = AggregatingLocator(
            JSONLocator(),
            SimpleScrapingLocator('https://pypi.org/simple/',
                                  timeout=3.0),
            scheme='legacy')
        finder = DependencyFinder(locator)
        dists, problems = finder.find('irc (== 5.0.1)')
        self.assertFalse(problems)
        actual = sorted([d.name for d in dists])
        self.assertEqual(actual, ['hgtools', 'irc',
                                  'pytest-runner', 'setuptools_scm'])
        dists, problems = finder.find('irc (== 5.0.1)',
                                      meta_extras=[':test:'])
        self.assertFalse(problems)
        actual = sorted([d.name for d in dists])
        self.assertEqual(actual, ['hgtools', 'irc', 'py',
                                  'pytest', 'pytest-runner', 'setuptools',
                                  'setuptools_scm'])

        g = make_graph(dists)
        slist, cycle = g.topological_sort()
        self.assertFalse(cycle)
        names = [d.name for d in slist]
        expected = set([
            # ('setuptools_scm', 'hgtools', 'py', 'pytest-runner', 'pytest', 'irc'),
            # ('setuptools_scm', 'hgtools', 'py', 'pytest', 'pytest-runner', 'irc'),
            # ('setuptools_scm', 'py', 'hgtools', 'pytest-runner', 'pytest', 'irc'),
            # ('hgtools', 'setuptools_scm', 'py', 'pytest', 'pytest-runner', 'irc'),
            # ('py', 'hgtools', 'setuptools_scm', 'pytest', 'pytest-runner', 'irc'),
            # ('hgtools', 'setuptools_scm', 'py', 'pytest-runner', 'pytest', 'irc'),
            # ('py', 'hgtools', 'setuptools_scm', 'pytest-runner', 'pytest', 'irc'),
            # ('py', 'setuptools_scm', 'hgtools', 'pytest', 'pytest-runner', 'irc'),
            # ('pytest', 'setuptools_scm', 'hgtools', 'pytest-runner', 'irc'),
            # ('hgtools', 'setuptools_scm', 'pytest', 'pytest-runner', 'irc'),
            # ('py', 'setuptools_scm', 'hgtools', 'pytest-runner', 'pytest', 'irc'),
            # ('py', 'setuptools_scm', 'pytest', 'pytest-runner', 'hgtools', 'irc'),
            # ('py', 'setuptools_scm', 'pytest-runner', 'pytest', 'hgtools', 'irc'),
            # ('py', 'setuptools_scm', 'pytest', 'hgtools', 'pytest-runner', 'irc'),
            # ('setuptools_scm', 'py', 'pytest', 'hgtools', 'pytest-runner', 'irc'),
            # ('setuptools_scm', 'py', 'pytest-runner', 'hgtools', 'pytest', 'irc'),
            # ('py', 'setuptools_scm', 'pytest-runner', 'hgtools', 'pytest', 'irc'),
            # ('setuptools_scm', 'py', 'pytest', 'pytest-runner', 'hgtools', 'irc'),
            ('setuptools_scm', 'py', 'setuptools', 'pytest-runner', 'pytest',
             'hgtools', 'irc'),
            ('py', 'setuptools', 'setuptools_scm', 'pytest-runner', 'hgtools',
             'pytest', 'irc'),
            ('setuptools_scm', 'setuptools', 'py', 'pytest', 'pytest-runner',
             'hgtools', 'irc'),
            ('py', 'setuptools_scm', 'setuptools', 'pytest-runner', 'hgtools',
             'pytest', 'irc'),
            ('setuptools', 'py', 'setuptools_scm', 'hgtools', 'pytest-runner',
             'pytest', 'irc'),
            ('setuptools', 'py', 'setuptools_scm', 'pytest', 'pytest-runner',
             'hgtools', 'irc'),
            ('py', 'setuptools', 'setuptools_scm', 'hgtools', 'pytest-runner',
             'pytest', 'irc'),
        ])
        self.assertIn(tuple(names), expected)

        # Test with extras
        dists, problems = finder.find('Jinja2 (== 2.6)')
        self.assertFalse(problems)
        actual = sorted([d.name_and_version for d in dists])
        self.assertEqual(actual, ['Jinja2 (2.6)'])
        dists, problems = finder.find('Jinja2 [i18n] (== 2.6)')
        self.assertFalse(problems)
        actual = sorted([d.name_and_version for d in dists])
        self.assertEqual(actual[-2], 'Jinja2 (2.6)')
        self.assertTrue(actual[-1].startswith('pytz ('))
        self.assertTrue(actual[0].startswith('Babel ('))
        actual = [d.build_time_dependency for d in dists]
        self.assertEqual(actual, [False, False, False])

        # Now test with extra in dependency
        locator.clear_cache()
        dummy = make_dist('dummy', '0.1')
        dummy.metadata.run_requires = [{'requires': ['Jinja2 [i18n] (<2.8)']}]
        dists, problems = finder.find(dummy)
        self.assertFalse(problems)
        actual = sorted([d.name_and_version for d in dists])
        self.assertTrue(actual[0].startswith('Babel ('))
        locator.clear_cache()
        dummy.metadata.run_requires = [{'requires': ['Jinja2']}]
        dists, problems = finder.find(dummy)
        self.assertFalse(problems)
        actual = sorted([d.name_and_version for d in dists])
        self.assertTrue(actual[0].startswith('Jinja2 ('))

    @unittest.skipIf('SKIP_ONLINE' in os.environ, 'Skipping online test')
    @unittest.skipUnless(ssl, 'SSL required for this test.')
    def test_get_all_dist_names(self):
        for url in (None, PYPI_RPC_HOST):
            try:
                all_dists = get_all_distribution_names(url)
            except Exception:     # pragma: no cover
                raise unittest.SkipTest('PyPI XML-RPC not available')
            self.assertGreater(len(all_dists), 0)

    def test_url_preference(self):
        cases = (('https://netloc/path', 'http://netloc/path'),
                 ('http://pypi.org/path', 'http://netloc/path'),
                 ('http://netloc/B', 'http://netloc/A'))
        for url1, url2 in cases:
            self.assertEqual(default_locator.prefer_url(url1, url2), url1)

    @unittest.skipIf('SKIP_ONLINE' in os.environ, 'Skipping online test')
    @unittest.skipUnless(ssl, 'SSL required for this test.')
    def test_prereleases(self):
        locator = AggregatingLocator(
            JSONLocator(),
            SimpleScrapingLocator('https://pypi.org/simple/',
                                  timeout=3.0),
            scheme='legacy')
        REQT = 'SQLAlchemy (>0.5.8, < 0.6)'
        finder = DependencyFinder(locator)
        d = locator.locate(REQT)
        self.assertIsNone(d)
        d = locator.locate(REQT, True)
        self.assertIsNotNone(d)
        self.assertEqual(d.name_and_version, 'SQLAlchemy (0.6beta3)')
        dist = make_dist('dummy', '0.1')
        dist.metadata.run_requires = [{'requires': [REQT]}]
        dists, problems = finder.find(dist, prereleases=True)
        self.assertFalse(problems)
        actual = sorted(dists, key=lambda o: o.name_and_version)
        self.assertEqual(actual[0].name_and_version, 'SQLAlchemy (0.6beta3)')
        dists, problems = finder.find(dist)
        # Test changed since now prereleases as found as a last resort.
        #self.assertEqual(dists, set([dist]))
        #self.assertEqual(len(problems), 1)
        #problem = problems.pop()
        #self.assertEqual(problem, ('unsatisfied', REQT))
        self.assertEqual(dists, set([actual[0], dist]))
        self.assertFalse(problems)

    @unittest.skipIf('SKIP_ONLINE' in os.environ, 'Skipping online test')
    @unittest.skipUnless(ssl, 'SSL required for this test.')
    def test_dist_reqts(self):
        r = 'config <=0.3.5'
        dist = default_locator.locate(r)
        self.assertIsNotNone(dist)
        self.assertIsNone(dist.extras)
        self.assertTrue(dist.matches_requirement(r))
        self.assertFalse(dist.matches_requirement('config == 0.3.6'))

    @unittest.skipIf('SKIP_ONLINE' in os.environ, 'Skipping online test')
    @unittest.skipUnless(ssl, 'SSL required for this test.')
    def test_dist_reqts_extras(self):
        r = 'config[doc,test](<=0.3.5)'
        dist = default_locator.locate(r)
        self.assertIsNotNone(dist)
        self.assertTrue(dist.matches_requirement(r))
        self.assertEqual(dist.extras, ['doc', 'test'])

    @unittest.skipIf('SKIP_ONLINE' in os.environ, 'Skipping online test')
    @unittest.skipUnless(ssl, 'SSL required for this test.')
    def test_all(self):
        d = default_locator.get_project('setuptools')
        self.assertTrue('urls' in d)
        d = d['urls']
        expected = set([
            'setuptools-0.6b1.zip',
            'setuptools-0.6b2.zip',
            'setuptools-0.6b3.zip',
            'setuptools-0.6b4.zip',
            'setuptools-0.6c10.tar.gz',
            'setuptools-0.6c11.tar.gz',
            #'setuptools-0.6c12dev-r88997.tar.gz',
            #'setuptools-0.6c12dev-r88998.tar.gz',
            #'setuptools-0.6c12dev-r89000.tar.gz',
            'setuptools-0.6c1.zip',
            'setuptools-0.6c2.zip',
            'setuptools-0.6c3.tar.gz',
            'setuptools-0.6c4.tar.gz',
            'setuptools-0.6c5.tar.gz',
            'setuptools-0.6c6.tar.gz',
            'setuptools-0.6c7.tar.gz',
            'setuptools-0.6c8.tar.gz',
            'setuptools-0.6c9.tar.gz',
            'setuptools-0.7.2.tar.gz',
            'setuptools-0.7.3.tar.gz',
            'setuptools-0.7.4.tar.gz',
            'setuptools-0.7.5.tar.gz',
            'setuptools-0.7.6.tar.gz',
            'setuptools-0.7.7.tar.gz',
            'setuptools-0.7.8.tar.gz',
            'setuptools-0.8.tar.gz',
            'setuptools-0.9.1.tar.gz',
            'setuptools-0.9.2.tar.gz',
            'setuptools-0.9.3.tar.gz',
            'setuptools-0.9.4.tar.gz',
            'setuptools-0.9.5.tar.gz',
            'setuptools-0.9.6.tar.gz',
            'setuptools-0.9.7.tar.gz',
            'setuptools-0.9.8.tar.gz',
            'setuptools-0.9.tar.gz',
            'setuptools-1.0.tar.gz',
            'setuptools-1.1.1.tar.gz',
            'setuptools-1.1.2.tar.gz',
            'setuptools-1.1.3.tar.gz',
            'setuptools-1.1.4.tar.gz',
            'setuptools-1.1.5.tar.gz',
            'setuptools-1.1.6.tar.gz',
            'setuptools-1.1.7.tar.gz',
            'setuptools-1.1.tar.gz',
            'setuptools-1.2.tar.gz',
            'setuptools-1.3.1.tar.gz',
            'setuptools-1.3.2.tar.gz',
            'setuptools-1.3.tar.gz',
            'setuptools-1.4.1.tar.gz',
            'setuptools-1.4.2.tar.gz',
            'setuptools-1.4.tar.gz',
            'setuptools-2.0.1.tar.gz',
            'setuptools-2.0.2.tar.gz',
            'setuptools-2.0.tar.gz',
            'setuptools-2.1.1.tar.gz',
            'setuptools-2.1.2.tar.gz',
            'setuptools-2.1.tar.gz',
            'setuptools-2.2.tar.gz',
            'setuptools-3.0.1.tar.gz',
            'setuptools-3.0.1.zip',
            'setuptools-3.0.2.tar.gz',
            'setuptools-3.0.2.zip',
            'setuptools-3.0.tar.gz',
            'setuptools-3.0.zip',
            'setuptools-3.1.tar.gz',
            'setuptools-3.1.zip',
            'setuptools-3.2.tar.gz',
            'setuptools-3.2.zip',
            'setuptools-3.3.tar.gz',
            'setuptools-3.3.zip',
            'setuptools-3.4.1.tar.gz',
            'setuptools-3.4.1.zip',
            'setuptools-3.4.2.tar.gz',
            'setuptools-3.4.2.zip',
            'setuptools-3.4.3.tar.gz',
            'setuptools-3.4.3.zip',
            'setuptools-3.4.4.tar.gz',
            'setuptools-3.4.4.zip',
            'setuptools-3.4.tar.gz',
            'setuptools-3.4.zip',
            'setuptools-3.5.1.tar.gz',
            'setuptools-3.5.1.zip',
            'setuptools-3.5.2.tar.gz',
            'setuptools-3.5.2.zip',
            'setuptools-3.5.tar.gz',
            'setuptools-3.5.zip',
            'setuptools-3.6.tar.gz',
            'setuptools-3.6.zip',
            'setuptools-3.7.1.tar.gz',
            'setuptools-3.7.1.zip',
            'setuptools-3.7.tar.gz',
            'setuptools-3.7.zip',
            'setuptools-3.8.1.tar.gz',
            'setuptools-3.8.1.zip',
            'setuptools-3.8.tar.gz',
            'setuptools-3.8.zip',
            'setuptools-4.0.1.tar.gz',
            'setuptools-4.0.1.zip',
            'setuptools-4.0.tar.gz',
            'setuptools-4.0.zip',
            'setuptools-5.0.1.tar.gz',
            'setuptools-5.0.1.zip',
            'setuptools-5.0.2.tar.gz',
            'setuptools-5.0.2.zip',
            'setuptools-5.0.tar.gz',
            'setuptools-5.0.zip',
            'setuptools-5.1.tar.gz',
            'setuptools-5.1.zip',
            'setuptools-5.2.tar.gz',
            'setuptools-5.2.zip',
            'setuptools-5.3.tar.gz',
            'setuptools-5.3.zip',
            'setuptools-5.4.1.tar.gz',
            'setuptools-5.4.1.zip',
            'setuptools-5.4.2.tar.gz',
            'setuptools-5.4.2.zip',
            'setuptools-5.4.tar.gz',
            'setuptools-5.4.zip',
            'setuptools-5.5.1.tar.gz',
            'setuptools-5.5.1.zip',
            'setuptools-5.5.tar.gz',
            'setuptools-5.5.zip',
            'setuptools-5.6.tar.gz',
            'setuptools-5.6.zip',
            'setuptools-5.7.tar.gz',
            'setuptools-5.7.zip',
            'setuptools-5.8.tar.gz',
            'setuptools-5.8.zip',
            'setuptools-6.0.1.tar.gz',
            'setuptools-6.0.1.zip',
            'setuptools-6.0.2.tar.gz',
            'setuptools-6.0.2.zip',
            # 'setuptools-6.0.tar.gz',
            'setuptools-6.0.zip',
        ])
        actual = set()
        for k, v in d.items():
            for url in v:
                _, _, path, _, _, _ = urlparse(url)
                filename = path.rsplit('/', 1)[-1]
                actual.add(filename)
        self.assertEqual(actual & expected, expected)

    @unittest.skipIf('SKIP_ONLINE' in os.environ, 'Skipping online test')
    @unittest.skipUnless(ssl, 'SSL required for this test.')
    def test_nonexistent(self):
        # See Issue #58
        d = locate('foobarbazbishboshboo')
        self.assertTrue(d is None or isinstance(d, Distribution))

if __name__ == '__main__':  # pragma: no cover
    import logging
    logging.basicConfig(level=logging.DEBUG, filename='test_locators.log',
                        filemode='w', format='%(message)s')
    unittest.main()
