import hashlib
import itertools
import logging
import os
import shutil
import socket
from string import ascii_lowercase
import subprocess
import tempfile
from threading import Thread

from distlib.compat import (xmlrpclib, configparser, HTTPBasicAuthHandler,
                            Request, HTTPPasswordMgr, urlparse, build_opener)
from distlib.metadata import Metadata
from distlib.util import cached_property, zip_dir

logger = logging.getLogger(__name__)

DEFAULT_MIRROR_HOST = 'last.pypi.python.org'
DEFAULT_INDEX = 'http://pypi.python.org/pypi'
DEFAULT_REALM = 'pypi'

class Index(object):

    boundary = b'----------ThIs_Is_tHe_distlib_index_bouNdaRY_$'

    def __init__(self, url=None, mirror_host=None):
        self.url = url or DEFAULT_INDEX
        self.mirror_host = mirror_host or DEFAULT_MIRROR_HOST
        self.read_configuration()
        scheme, netloc, path, params, query, frag = urlparse(self.url)
        if params or query or frag or scheme not in ('http', 'https'):
            raise ValueError('invalid repository: %s' % self.url)
        self.password_manager = None
        self.gpg = None
        self.gpg_home = None
        with open(os.devnull, 'w') as sink:
            for s in ('gpg2', 'gpg'):
                try:
                    rc = subprocess.check_call([s, '--version'], stdout=sink,
                                               stderr=sink)
                    if rc == 0:
                        self.gpg = s
                        break
                except OSError:
                    pass

    def _get_pypirc_command(self):
        from distutils.core import Distribution
        from distutils.config import PyPIRCCommand
        d = Distribution()
        return PyPIRCCommand(d)

    def read_configuration(self):
        # get distutils to do the work
        c = self._get_pypirc_command()
        c.repository = self.url
        cfg = c._read_pypirc()
        self.username = cfg.get('username')
        self.password = cfg.get('password')
        self.realm = cfg.get('realm', 'pypi')
        self.url = cfg.get('repository', self.url)

    def save_configuration(self):
        self.check_credentials()
        # get distutils to do the work
        c = self._get_pypirc_command()
        c._store_pypirc(self.username, self.password)

    def check_credentials(self):
        if self.username is None or self.password is None:
            raise ValueError('username and password must be set')
        if self.password_manager is None:
            self.password_manager = pm = HTTPPasswordMgr()
            _, netloc, _, _, _, _ = urlparse(self.url)
            pm.add_password(self.realm, netloc, self.username, self.password)

    def register(self, metadata):
        self.check_credentials()
        missing, warnings = metadata.check(True)    # strict check
        logger.debug('result of check: missing: %s, warnings: %s',
                     missing, warnings)
        d = metadata.todict(True)
        d[':action'] = 'verify'
        request = self.encode_request(d.items(), [])
        response = self.send_request(request, self.password_manager)
        d[':action'] = 'submit'
        request = self.encode_request(d.items(), [])
        return self.send_request(request, self.password_manager)

    def reader(self, name, stream, outbuf):
        while True:
            s = stream.readline()
            if not s:
                break
            s = s.decode('utf-8').rstrip()
            outbuf.append(s)
            logger.debug('%s: %s' % (name, s))
        stream.close()

    def get_sign_command(self, filename, signer, sign_password):
        cmd = [self.gpg, '--status-fd', '2', '--no-tty']
        if self.gpg_home:
            cmd.extend(['--homedir', self.gpg_home])
        if sign_password is not None:
            cmd.extend(['--batch', '--passphrase-fd', '0'])
        td = tempfile.mkdtemp()
        sf = os.path.join(td, os.path.basename(filename) + '.asc')
        cmd.extend(['--detach-sign', '--armor', '--local-user',
                    signer, '--output', sf, filename])
        logger.debug('invoking: %s', ' '.join(cmd))
        return cmd, sf

    def run_command(self, cmd, input_data=None):
        kwargs = {
            'stdout': subprocess.PIPE,
            'stderr': subprocess.PIPE,
        }
        if input_data is not None:
            kwargs['stdin'] = subprocess.PIPE
        stdout = []
        stderr = []
        p = subprocess.Popen(cmd, **kwargs)
        # We don't use communicate() here because we may need to
        # get clever with interacting with the command
        t1 = Thread(target=self.reader, args=('stdout', p.stdout, stdout))
        t1.start()
        t2 = Thread(target=self.reader, args=('stderr', p.stderr, stderr))
        t2.start()
        if input_data is not None:
            p.stdin.write(input_data)
            p.stdin.close()

        p.wait()
        t1.join()
        t2.join()
        return p.returncode, stdout, stderr

    def sign_file(self, filename, signer, sign_password):
        cmd, sig_file = self.get_sign_command(filename, signer, sign_password)
        rc, stdout, stderr = self.run_command(cmd,
                                              sign_password.encode('utf-8'))
        if rc != 0:
            raise ValueError('sign command failed with error '
                             'code %s' % rc)
        return sig_file

    def upload_file(self, metadata, filename, signer=None, sign_password=None,
                    filetype='sdist', pyversion='source'):
        self.check_credentials()
        if not os.path.exists(filename):
            raise ValueError('not found: %s' % filename)
        missing, warnings = metadata.check(True)    # strict check
        logger.debug('result of check: missing: %s, warnings: %s',
                     missing, warnings)
        d = metadata.todict(True)
        sig_file = None
        if signer:
            if not self.gpg:
                logger.warning('no signing program available - not signed')
            else:
                sig_file = self.sign_file(filename, signer, sign_password)
        with open(filename, 'rb') as f:
            file_data = f.read()
        digest = hashlib.md5(file_data).hexdigest()
        d.update({
            ':action': 'file_upload',
            'protcol_version': '1',
            'filetype': filetype,
            'pyversion': pyversion,
            'md5_digest': digest,
        })
        files = [('content', os.path.basename(filename), file_data)]
        if sig_file:
            with open(sig_file, 'rb') as f:
                sig_data = f.read()
            files.append(('gpg_signature', os.path.basename(sig_file),
                         sig_data))
            shutil.rmtree(os.path.dirname(sig_file))
        logger.debug('files: %s', files)
        request = self.encode_request(d.items(), files)
        return self.send_request(request, self.password_manager)

    def upload_documentation(self, metadata, doc_dir):
        self.check_credentials()
        if not os.path.isdir(doc_dir):
            raise ValueError('not a directory: %r' % doc_dir)
        fn = os.path.join(doc_dir, 'index.html')
        if not os.path.exists(fn):
            raise ValueError('not found: %r' % fn)
        missing, warnings = metadata.check(True)    # strict check
        logger.debug('result of check: missing: %s, warnings: %s',
                     missing, warnings)
        name, version = metadata.name, metadata.version
        zip_data = zip_dir(doc_dir).getvalue()
        fields = [(':action', 'doc_upload'),
                  ('name', name), ('version', version)]
        files = [('content', name, zip_data)]
        request = self.encode_request(fields, files)
        return self.send_request(request, self.password_manager)

    def get_verify_command(self, signature_filename, data_filename):
        cmd = [self.gpg, '--status-fd', '2', '--no-tty']
        if self.gpg_home:
            cmd.extend(['--homedir', self.gpg_home])
        cmd.extend(['--verify', signature_filename, data_filename])
        logger.debug('invoking: %s', ' '.join(cmd))
        return cmd

    def verify_signature(self, signature_filename, data_filename):
        cmd = self.get_verify_command(signature_filename, data_filename)
        rc, stdout, stderr = self.run_command(cmd)
        if rc not in (0, 1):
            raise ValueError('verify command failed with error '
                             'code %s' % rc)
        return rc == 0

    def send_request(self, req, password_manager):
        opener = build_opener(HTTPBasicAuthHandler(password_manager))
        return opener.open(req)

    def encode_request(self, fields, files):
        """
        Encode fields and files for posting to an HTTP server.
        """
        # Adapted from packaging, which in turn was adapted from
        # http://code.activestate.com/recipes/146306

        parts = []
        boundary = self.boundary
        for k, values in fields:
            if not isinstance(values, (list, tuple)):
                values = [values]

            for v in values:
                parts.extend((
                    b'--' + boundary,
                    ('Content-Disposition: form-data; name="%s"' %
                     k).encode('utf-8'),
                    b'',
                    v.encode('utf-8')))
        for key, filename, value in files:
            parts.extend((
                b'--' + boundary,
                ('Content-Disposition: form-data; name="%s"; filename="%s"' %
                 (key, filename)).encode('utf-8'),
                b'',
                value))

        parts.extend((b'--' + boundary + b'--', b''))

        body = b'\r\n'.join(parts)
        ct = b'multipart/form-data; boundary=' + boundary
        headers = {
            'Content-type': ct,
            'Content-length': str(len(body))
        }
        return Request(self.url, body, headers)

    @cached_property
    def mirrors(self):
        result = []
        try:
            host = socket.gethostbyname_ex(self.mirror_host)[0]
        except socket.gaierror:
            host = None
        if host:
            last, rest = host.split('.', 1)
            n = len(last)
            hostlist = (''.join(w) for w in itertools.chain.from_iterable(
                        itertools.product(ascii_lowercase, repeat=i)
                        for i in range(1, n + 1)))
            for s in hostlist:
                result.append('.'.join((s, rest)))
                if s == last:
                    break
        return result
