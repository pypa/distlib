import codecs
import json
import logging
import os
import shutil
import socket
import ssl
import subprocess
import sys
import tempfile
import threading

from compat import unittest, Request
from support import HTTPSServerThread

from distlib import DistlibException
from distlib.compat import urlopen, HTTPError, URLError
from distlib.index import PackageIndex, DEFAULT_MIRROR_HOST
from distlib.metadata import Metadata, MetadataMissingError
from distlib.util import zip_dir, HTTPSHandler

logger = logging.getLogger(__name__)

HERE = os.path.abspath(os.path.dirname(__file__))

class PackageIndexTestCase(unittest.TestCase):
    run_test_server = True
    test_server_url = 'http://localhost:8080/'

    @classmethod
    def setUpClass(cls):
        if cls.run_test_server:
            cls.server = None
            server_script = os.path.join(HERE, 'pypi-server-standalone.py')
            if not os.path.exists(server_script):
                logger.debug('test server not available - some tests '
                             'will be skipped.')
                return
            pwdfn = os.path.join(HERE, 'passwords')
            if not os.path.exists(pwdfn):   # pragma: no cover
                with open(pwdfn, 'w') as f:
                    f.write('test:secret\n')
            pkgdir = os.path.join(HERE, 'packages')
            if not os.path.isdir(pkgdir):   # pragma: no cover
                os.mkdir(pkgdir)
            cls.sink = sink = open(os.devnull, 'w')
            cmd = [sys.executable, 'pypi-server-standalone.py',
                   '-P', 'passwords', 'packages']
            cls.server = subprocess.Popen(cmd, stdout=sink, stderr=sink,
                                          cwd=HERE)
            # wait for the server to start up
            response = None
            while response is None:
                try:
                    response = urlopen(cls.test_server_url)
                except URLError:
                    pass

    @classmethod
    def tearDownClass(cls):
        if cls.run_test_server:
            if cls.server and cls.server.returncode is None:
                cls.server.kill()
                cls.sink.close()

    def setUp(self):
        if not self.run_test_server:
            self.index = PackageIndex()
        else:
            self.index = PackageIndex(self.test_server_url)
            self.index.username = 'test'
            self.index.password = 'secret'

    def test_mirrors(self):
        "Test list of mirrors"
        actual = self.index.mirrors
        if actual:
            host = socket.gethostbyname_ex(DEFAULT_MIRROR_HOST)[0]
            self.assertEqual(actual[-1], host)
            prefix, suffix = host.split('.', 1)
            self.assertEqual(actual[0], '.'.join(('a', suffix)))

    def load_package_metadata(self, path):
        fn = os.path.join(path, 'package.json')
        if not os.path.exists(fn):
            raise ValueError('not found: %s' % fn)
        with codecs.open(fn, 'r', 'utf-8') as jf:
            result = json.load(jf)
        if result.get('version') != '1' or 'metadata' not in result:
            raise ValueError('Not a valid file: %s' % fn)
        return result

    def get_index_metadata(self, data):
        result = dict(data['metadata'])
        for key in ('home-page', 'author-email', 'maintainer-email'):
            if key in result:
                new_key = key.replace('-', '_')
            result[new_key] = result.pop(key)
        return result

    def check_pypi_server_available(self):
        if self.run_test_server and not self.server:
            raise unittest.SkipTest('test server not available')

    def check_testdist_available(self):
        self.index.check_credentials()
        self.username = self.index.username.replace('-', '_')
        self.dist_project = '%s_testdist' % self.username
        self.dist_version = '0.1'
        self.testdir = '%s-%s' % (self.dist_project, self.dist_version)
        destdir = os.path.join(HERE, self.testdir)
        if not os.path.isdir(destdir):  # pragma : no cover
            srcdir = os.path.join(HERE, 'testdist-0.1')
            shutil.copytree(srcdir, destdir)
            for fn in os.listdir(destdir):
                fn = os.path.join(destdir, fn)
                if os.path.isfile(fn):
                    with codecs.open(fn, 'r', 'utf-8') as f:
                        data = f.read()
                    data = data.format(username=self.username)
                    with codecs.open(fn, 'w', 'utf-8') as f:
                        f.write(data)
            zip_data = zip_dir(destdir).getvalue()
            zip_name = destdir + '.zip'
            with open(zip_name, 'wb') as f:
                f.write(zip_data)

    def test_register(self):
        "Test registration"
        self.check_pypi_server_available()
        self.check_testdist_available()
        d = os.path.join(HERE, self.testdir)
        data = self.load_package_metadata(d)
        md = Metadata()
        self.assertRaises(MetadataMissingError, self.index.register, md)
        md['Name'] = self.dist_project
        self.assertRaises(MetadataMissingError, self.index.register, md)
        md.update(self.get_index_metadata(data))
        response = self.index.register(md)
        self.assertEqual(response.code, 200)

    def remove_package(self, name, version):
        """
        Remove package. Only works with test server; PyPI would require
        some scraping to get CSRF tokens into the request.
        """
        d = {
            ':action': 'remove_pkg',
            'name': name,
            'version': version,
            'submit_remove': 'Remove',
            'submit_ok': 'OK',
        }
        self.index.check_credentials()
        request = self.index.encode_request(d.items(), [])
        try:
            response = self.index.send_request(request)
        except HTTPError as e:
            if e.getcode() != 404:
                raise

    def test_upload(self):
        "Test upload"
        self.check_pypi_server_available()
        self.check_testdist_available()
        if self.run_test_server:
            self.remove_package(self.dist_project, self.dist_version)
        d = os.path.join(HERE, self.testdir)
        data = self.load_package_metadata(d)
        md = Metadata()
        md.update(self.get_index_metadata(data))
        #import pdb; pdb.set_trace()
        self.index.gpg_home = os.path.join(HERE, 'keys')
        try:
            zip_name = os.path.join(HERE, '%s.zip' % self.testdir)
            response = self.index.upload_file(md, zip_name,
                                              'Test User', 'tuser')
            self.assertEqual(response.code, 200)
            if self.run_test_server:
                fn = os.path.join(HERE, 'packages', os.path.basename(zip_name))
                self.assertTrue(os.path.exists(fn))
        except HTTPError as e:
            # Treat as success if it already exists
            if e.getcode() != 400 or 'already exists' not in e.msg:
                raise

    def test_upload_documentation(self):
        "Test upload of documentation"
        self.check_pypi_server_available()
        self.check_testdist_available()
        d = os.path.join(HERE, self.testdir)
        data = self.load_package_metadata(d)
        md = Metadata()
        md.update(self.get_index_metadata(data))
        d = os.path.join(d, 'doc')
        response = self.index.upload_documentation(md, d)
        self.assertEqual(response.code, 200)
        if not self.run_test_server:
            url = 'http://packages.python.org/%s/' % self.dist_project
            response = urlopen(url)
            self.assertEqual(response.code, 200)
            data = response.read()
            expected = b'This is dummy documentation'
            self.assertIn(expected, data)

    def test_verify_signature(self):
        if not self.index.gpg:
            raise unittest.SkipTest('gpg not available')
        self.index.gpg_home = os.path.join(HERE, 'keys')
        sig_file = os.path.join(HERE, 'good.bin.asc')
        good_file = os.path.join(HERE, 'good.bin')
        bad_file = os.path.join(HERE, 'bad.bin')
        self.assertTrue(self.index.verify_signature(sig_file, good_file))
        self.assertFalse(self.index.verify_signature(sig_file, bad_file))

    def test_invalid(self):
        self.assertRaises(DistlibException, PackageIndex,
                          'ftp://ftp.python.org/')

    def make_https_server(self, certfile):
        server = HTTPSServerThread(certfile)
        flag = threading.Event()
        server.start(flag)
        flag.wait()
        def cleanup():
            server.stop()
            server.join()
        self.addCleanup(cleanup)
        return server

    def test_ssl_verification(self):
        certfile = os.path.join(HERE, 'keycert.pem')
        server = self.make_https_server(certfile)
        url = 'https://localhost:%d/' % server.port
        req = Request(url)
        self.index.ssl_verifier = HTTPSHandler(certfile)
        response = self.index.send_request(req)
        self.assertEqual(response.code, 200)

    def test_download(self):
        digest = '913093474942c5a564c011f232868517' # for testsrc/README.txt
        certfile = os.path.join(HERE, 'keycert.pem')
        server = self.make_https_server(certfile)
        url = 'https://localhost:%d/README.txt' % server.port
        fd, fn = tempfile.mkstemp()
        os.close(fd)
        self.addCleanup(os.remove, fn)
        with open(os.path.join(HERE, 'testsrc', 'README.txt'), 'rb') as f:
            data = f.read()
        self.index.download_file(url, fn)   # no digest
        with open(fn, 'rb') as f:
            self.assertEqual(data, f.read())
        self.index.download_file(url, fn, digest)
        with open(fn, 'rb') as f:
            self.assertEqual(data, f.read())
        reporthook = lambda *args: None
        self.index.download_file(url, fn, ('md5', digest), reporthook)
        with open(fn, 'rb') as f:
            self.assertEqual(data, f.read())
        # bad digest
        self.assertRaises(DistlibException, self.index.download_file, url, fn,
                          digest[:-1] + '8')

if __name__ == '__main__':
    unittest.main()
