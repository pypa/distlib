import gzip
from io import BytesIO
import logging
import os
import posixpath
import re
import threading
import zlib

from .compat import (xmlrpclib, urljoin, urlopen, urlparse, urlunparse,
                     url2pathname, pathname2url, queue,
                     Request, HTTPError, URLError)
from .database import Distribution
from .metadata import Metadata
from .util import cached_property, parse_credentials, ensure_slash

logger = logging.getLogger(__name__)

EXTENSIONS = tuple(".tar.gz .tar.bz2 .tar .zip .tgz .egg".split())
MD5_HASH = re.compile('^md5=([a-f0-9]+)$')
CHARSET = re.compile(r';\s*charset\s*=\s*(.*)\s*$', re.I)
HTML_CONTENT_TYPE = re.compile('text/html|application/xhtml')
PROJECT_NAME_AND_VERSION = re.compile('([a-z0-9_.-]+)-([0-9][0-9_.-]*)', re.I)
PYTHON_VERSION = re.compile(r'-py(\d\.?\d?)$')

class Locator(object):
    def get_project(self, name):
        raise NotImplementedError('Please implement in the subclass')

    def convert_url_to_download_info(self, url, project_name):
        scheme, netloc, path, params, query, frag = urlparse(url)
        result = None
        if path.endswith(EXTENSIONS):
            origpath = path
            path = filename = posixpath.basename(path)
            for ext in EXTENSIONS:
                if ext == '.egg':
                    continue    # for now, at least
                if path.endswith(ext):
                    path = path[:-len(ext)]
                    pyver = None
                    m = PYTHON_VERSION.search(path)
                    if m:
                        pyver = m.group(1)
                        path = path[:m.start()]
                    m = PROJECT_NAME_AND_VERSION.match(path)
                    if not m:
                        logger.debug('No match: %s', path)
                    else:
                        name, version = m.group(1), m.group(2)
                        if (not project_name or
                            project_name.lower() == name.lower()):
                            result = {
                                'name': name,
                                'version': version,
                                'filename': filename,
                                'url': urlunparse((scheme, netloc, origpath,
                                                   params, query, '')),
                                #'packagetype': 'sdist',
                            }
                            if pyver:
                                result['python-version'] = pyver
                            m = MD5_HASH.match(frag)
                            if m:
                                result['md5_digest'] = m.group(1)
                    break
        return result

    def _update_version_data(self, result, info):
        name = info.pop('name')
        version = info.pop('version')
        if version in result:
            dist = result[version]
            md = dist.metadata
        else:
            md = Metadata()
            md['Name'] = name
            md['Version'] = version
            dist = Distribution(md)
        if 'md5_digest' in info:
            dist.md5_digest = info['md5_digest']
        if 'python-version' in info:
            md['Requires-Python'] = info['python-version']
        if md['Download-URL'] != info['url']:
            md['Download-URL'] = info['url']
        dist.locator = self
        result[version] = dist

class PyPIRPCLocator(Locator):
    def __init__(self, url):
        self.base_url = url
        self.client = xmlrpclib.ServerProxy(url)

    def get_project(self, name):
        result = {}
        versions = self.client.package_releases(name, True)
        for v in versions:
            urls = self.client.release_urls(name, v)
            data = self.client.release_data(name, v)
            metadata = Metadata()
            metadata.update(data)
            dist = Distribution(metadata)
            if urls:
                info = urls[0]
                metadata['Download-URL'] = info['url']
                if 'md5_digest' in info:
                    dist.md5_digest = info['md5_digest']
            result[v] = dist
        return result

class Page(object):

    _href = re.compile('href\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|([^>\\s\\n]*))', re.I|re.S)
    _base = re.compile(r"""<base\s+href\s*=\s*['"]?([^'">]+)""", re.I|re.S)

    def __init__(self, data, url):
        self.data = data
        self.base_url = self.url = url
        m = self._base.search(self.data)
        if m:
            self.base_url = m.group(1)

    @cached_property
    def links(self):
        result = set()
        for match in self._href.finditer(self.data):
            url = match.group(1) or match.group(2) or match.group(3)
            url = urljoin(self.base_url, url)
            # do any required cleanup of URL here (e.g. converting spaces)
            result.add(url)
        return result

class SimpleScrapingLocator(Locator):

    decoders = {
        'deflate': zlib.decompress,
        'gzip': lambda b: gzip.GZipFile(fileobj=BytesIO(d)).read(),
    }

    def __init__(self, url, timeout=None, num_workers=1):
        self.base_url = ensure_slash(url)
        self.timeout = timeout
        self._cache = {}
        self._seen = set()
        self._to_fetch = queue.Queue()
        self.num_workers = num_workers

    def _prepare_threads(self):
        self._threads = []
        for i in range(self.num_workers):
            t = threading.Thread(target=self._fetch)
            t.setDaemon(True)
            t.start()
            self._threads.append(t)

    def _wait_threads(self):
        for t in self._threads:
            self._to_fetch.put(None)    # sentinel
            t.join()

    def get_project(self, name):
        self.result = result = {}
        self.project_name = name
        url = urljoin(self.base_url, '%s/' % name)
        self._seen.clear()
        self._prepare_threads()
        logger.debug('Queueing %s', url)
        self._to_fetch.put(url)
        self._to_fetch.join()
        self._wait_threads()
        del self.result
        return result

    def _process_download(self, url):
        info = self.convert_url_to_download_info(url, self.project_name)
        if info:
            self._update_version_data(self.result, info)
        return info

    def _fetch(self):
        while True:
            url = self._to_fetch.get()
            try:
                if url:
                    page = self.get_page(url)
                    if page is None:    # e.g. after an error
                        continue
                    for link in page.links:
                        if link not in self._seen:
                            self._seen.add(link)
                            if (not self._process_download(link) and
                                url.startswith(self.base_url)):
                                logger.debug('Queueing %s from %s', link, url)
                                self._to_fetch.put(link)
            finally:
                self._to_fetch.task_done()
            if not url:
                logger.debug('Sentinel seen, quitting.')
                break

    def get_page(self, url):
        # http://peak.telecommunity.com/DevCenter/EasyInstall#package-index-api
        scheme, _, path, _, _, _ = urlparse(url)
        if scheme == 'file' and os.path.isdir(url2pathname(path)):
            url = urljoin(ensure_slash(url), 'index.html')

        if url in self._cache:
            result = self._cache[url]
        else:
            result = None
            req = Request(url, headers={'Accept-encoding': 'identity'})
            try:
                logger.debug('Fetching %s', url)
                resp = urlopen(req, timeout=self.timeout)
                logger.debug('Fetched %s', url)
                headers = resp.info()
                content_type = headers.get('Content-Type', '')
                if not HTML_CONTENT_TYPE.match(content_type):
                    result = None
                else:
                    final_url = resp.geturl()
                    data = resp.read()
                    encoding = headers.get('Content-Encoding')
                    if encoding:
                        decoder = self.decoders[encoding]   # fail if not found
                        data = decoder(data)
                    encoding = 'utf-8'
                    m = CHARSET.search(content_type)
                    if m:
                        encoding = m.group(1)
                    data = data.decode(encoding)
                    result = Page(data, final_url)
                    self._cache[url] = self._cache[final_url] = result
            except HTTPError as e:
                if e.code != 404:
                    raise
            except URLError as e:
                logger.exception('Fetch failed: %s: %s', url, e)
            except Exception:
                logger.exception('Fetch failed: %s: %s', url, e)
        return result


class DirectoryLocator(Locator):
    def __init__(self, path):
        path = os.path.abspath(path)
        if not os.path.isdir(path):
            raise ValueError('Not a directory: %r' % path)
        self.base_dir = path

    def get_project(self, name):
        result = {}
        for root, dirs, files in os.walk(self.base_dir):
            for fn in files:
                if fn.endswith(EXTENSIONS):
                    fn = os.path.join(root, fn)
                    url = pathname2url(os.path.abspath(fn))
                    info = self.convert_url_to_download_info(url, name)
                    if info:
                        self._update_version_data(result, info)
        return result

class AggregatingLocator(Locator):
    def __init__(self, *locators, **kwargs):
        self.locators = locators
        self.merge = kwargs.get('merge', False)

    def get_project(self, name):
        result = {}
        for locator in self.locators:
            r = locator.get_project(name)
            if r:
                if self.merge:
                    result.update(r)
                else:
                    result = r
                    break
        return result
