import os

from compat import unittest

from distlib.locators import (SimpleScrapingLocator, PyPIRPCLocator,
                              DirectoryLocator)

HERE = os.path.abspath(os.path.dirname(__file__))

class LocatorTestCase(unittest.TestCase):
    def test_xmlrpc(self):
        locator = PyPIRPCLocator('http://python.org/pypi')
        result = locator.get_project('Flask')
        self.assertIn('0.9', result)
        metadata, urls = result['0.9']
        self.assertEqual(metadata.name, 'Flask')
        self.assertEqual(metadata.version, '0.9')
        self.assertTrue(urls)
        url_data = urls[0]
        self.assertEqual(url_data['url'],
                         'http://pypi.python.org/packages/source/F/Flask/'
                         'Flask-0.9.tar.gz')
        self.assertEqual(url_data['filename'], 'Flask-0.9.tar.gz')
        self.assertEqual(url_data['md5_digest'],
                         '4a89ef2b3ab0f151f781182bd0cc8933')

    def test_scraper(self):
        locator = SimpleScrapingLocator('http://pypi.python.org/simple/')
        for name in ('flask', 'Flask'):
            result = locator.get_project(name)
            self.assertIn('0.9', result)
            metadata, urls = result['0.9']
            self.assertEqual(metadata.name, 'Flask')
            self.assertEqual(metadata.version, '0.9')
            self.assertTrue(urls)
            url_data = urls[0]
            self.assertEqual(url_data['url'],
                             'http://pypi.python.org/packages/source/F/Flask/'
                             'Flask-0.9.tar.gz')
            self.assertEqual(url_data['filename'], 'Flask-0.9.tar.gz')
            self.assertEqual(url_data['md5_digest'],
                             '4a89ef2b3ab0f151f781182bd0cc8933')

    def test_dir(self):
        d = os.path.join(HERE, 'fake_archives')
        locator = DirectoryLocator(d)
        for name in ('flask', 'Flask'):
            result = locator.get_project(name)
            self.assertIn('0.9', result)
            metadata, urls = result['0.9']
            self.assertEqual(metadata.name, 'Flask')
            self.assertEqual(metadata.version, '0.9')
            self.assertTrue(urls)
            url_data = urls[0]
            expected = os.path.join(HERE, 'fake_archives', 'subdir',
                                    'subsubdir', 'Flask-0.9.tar.gz')
            self.assertEqual(url_data['url'], expected)
            self.assertEqual(url_data['filename'], 'Flask-0.9.tar.gz')
