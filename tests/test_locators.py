import os

from compat import unittest

from distlib.locators import (SimpleScrapingLocator, PyPIRPCLocator,
                              DirectoryLocator)

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

    def test_dir(self):
        d = os.path.join(HERE, 'fake_archives')
        locator = DirectoryLocator(d)
        for name in ('flask', 'Flask'):
            result = locator.get_project(name)
            self.assertIn('0.9', result)
            dist = result['0.9']
            self.assertEqual(dist.name, 'Flask')
            self.assertEqual(dist.version, '0.9')
            expected = os.path.join(HERE, 'fake_archives', 'subdir',
                                    'subsubdir', 'Flask-0.9.tar.gz')
            self.assertEqual(dist.download_url, expected)
