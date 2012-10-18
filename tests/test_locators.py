# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 The Python Software Foundation.
# See LICENSE.txt and CONTRIBUTORS.txt.
#
from __future__ import unicode_literals
import os

from compat import unittest

from distlib.compat import url2pathname
from distlib.locators import (SimpleScrapingLocator, PyPIRPCLocator,
                              PyPIJSONLocator, DirectoryLocator,
                              AggregatingLocator)

HERE = os.path.abspath(os.path.dirname(__file__))

class LocatorTestCase(unittest.TestCase):
    def test_xmlrpc(self):
        locator = PyPIRPCLocator('http://python.org/pypi')
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

    def test_json(self):
        locator = PyPIJSONLocator('http://python.org/pypi')
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
        for name in ('flask', 'Flask'):
            result = locator.get_project(name)
            self.assertIn('0.9', result)
            dist = result['0.9']
            self.assertEqual(dist.name, 'Flask')
            self.assertEqual(dist.version, '0.9')
            self.assertEqual(url2pathname(dist.download_url), expected)

    def test_aggregation(self):
        d = os.path.join(HERE, 'fake_archives')
        loc1 = DirectoryLocator(d)
        loc2 = SimpleScrapingLocator('http://pypi.python.org/simple/')
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
        self.assertEqual(url2pathname(dist.download_url), exp1)
        locator.merge = True
        result = locator.get_project('flask')
        self.assertGreater(len(result), 1)
        self.assertIn('0.9', result)
        dist = result['0.9']
        self.assertEqual(dist.name, 'Flask')
        self.assertEqual(dist.version, '0.9')
        self.assertEqual(dist.download_url, exp2)
