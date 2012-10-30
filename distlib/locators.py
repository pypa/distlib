# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 The Python Software Foundation.
# See LICENSE.txt and CONTRIBUTORS.txt.
#
import gzip
from io import BytesIO
import json
import logging
import os
import posixpath
import re
import threading
import zlib

from .compat import (xmlrpclib, urljoin, urlopen, urlparse, urlunparse,
                     url2pathname, pathname2url, queue, quote,
                     unescape,
                     Request, HTTPError, URLError)
from .database import Distribution
from .metadata import Metadata
from .util import (cached_property, parse_credentials, ensure_slash,
                   split_filename)
from .version import get_scheme

logger = logging.getLogger(__name__)

MD5_HASH = re.compile('^md5=([a-f0-9]+)$')
CHARSET = re.compile(r';\s*charset\s*=\s*(.*)\s*$', re.I)
HTML_CONTENT_TYPE = re.compile('text/html|application/x(ht)?ml')

def get_all_distribution_names(url=None):
    if url is None:
        url = 'http://python.org/pypi'
    client = xmlrpclib.ServerProxy(url)
    return client.list_packages()

class Locator(object):
    source_extensions = ('.tar.gz', '.tar.bz2', '.tar', '.zip', '.tgz')
    binary_extensions = ('.egg', '.exe', '.whl')
    excluded_extensions = ('.pdf',)

    # Leave out binaries from downloadables, for now.
    downloadable_extensions = source_extensions

    def __init__(self):
        self._cache = {}

    def _get_project(self, name):
        """
        For a given project, get a dictionary mapping available versions to Distribution
        instances.

        This should be implemented in subclasses.
        """
        raise NotImplementedError('Please implement in the subclass')

    def get_distribution_names(self):
        """
        Return all the distribution names known to this locator.
        """
        raise NotImplementedError('Please implement in the subclass')

    def get_project(self, name):
        """
        For a given project, get a dictionary mapping available versions to Distribution
        instances.

        This calls _get_project to do all the work, and just implements a caching layer on top.
        """
        if self._cache is None:
            result = self._get_project(name)
        elif name in self._cache:
            result = self._cache[name]
        else:
            result = self._get_project(name)
            self._cache[name] = result
        return result

    def prefer_url(self, url1, url2):
        """
        Choose one of two URLs where both are candidates for distribution
        archives for the same version of a distribution (for example,
        .tar.gz vs. zip).

        The current implement favours http:// URLs over https://, archives
        from PyPI over those from other locations and then the archive name.
        """
        def score(url):
            t = urlparse(url)
            return (t.scheme != 'https', 'pypi.python.org' in t.netloc,
                    posixpath.basename(t.path))

        if url1 == 'UNKNOWN':
            result = url2
        else:
            result = url2
            s1 = score(url1)
            s2 = score(url2)
            if s1 > s2:
                result = url1
            if result != url2:
                logger.debug('Not replacing %r with %r', url1, url2)
            else:
                logger.debug('Replacing %r with %r', url1, url2)
        return result

    def split_filename(self, filename, project_name):
        """
        Attempt to split a filename in project name, version and Python version.
        """
        return split_filename(filename, project_name)

    def convert_url_to_download_info(self, url, project_name):
        """
        See if a URL is a candidate for a download URL for a project (the URL
        has typically been scraped from an HTML page).

        If it is, a dictionary is returned with keys "name", "version",
        "filename" and "url"; otherwise, None is returned.
        """
        def same_project(name1, name2):
            name1, name2 = name1.lower(), name2.lower()
            if name1 == name2:
                result = True
            else:
                # distribute replaces '-' by '_' in project names, so it
                # can tell where the version starts in a filename.
                result = name1.replace('_', '-') == name2.replace('_', '-')
            return result

        result = None
        scheme, netloc, path, params, query, frag = urlparse(url)
        if frag.lower().startswith('egg='):
            logger.debug('%s: version hint in fragment: %r',
                         project_name, frag)
        origpath = path
        if path and path[-1] == '/':
            path = path[:-1]
        if path.endswith(self.downloadable_extensions):
            path = filename = posixpath.basename(path)
            for ext in self.downloadable_extensions:
                if path.endswith(ext):
                    path = path[:-len(ext)]
                    t = self.split_filename(path, project_name)
                    if not t:
                        logger.debug('No match for project/version: %s', path)
                    else:
                        name, version, pyver = t
                        if not project_name or same_project(project_name, name):
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
        """
        Update a result dictionary (the final result from _get_project) with a dictionary for a
        specific version, whih typically holds information gleaned from a filename or URL for an
        archive for the distribution.
        """
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
            md['Download-URL'] = self.prefer_url(md['Download-URL'],
                                                 info['url'])
        dist.locator = self
        result[version] = dist

class PyPIRPCLocator(Locator):
    def __init__(self, url):
        super(PyPIRPCLocator, self).__init__()
        self.base_url = url
        self.client = xmlrpclib.ServerProxy(url)

    def get_distribution_names(self):
        """
        Return all the distribution names known to this locator.
        """
        return set(self.client.list_packages())

    def _get_project(self, name):
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
                dist.locator = self
                result[v] = dist
        return result

class PyPIJSONLocator(Locator):
    def __init__(self, url):
        super(PyPIJSONLocator, self).__init__()
        self.base_url = ensure_slash(url)

    def get_distribution_names(self):
        """
        Return all the distribution names known to this locator.
        """
        raise NotImplementedError('Not available from this locator')

    def _get_project(self, name):
        result = {}
        url = urljoin(self.base_url, '%s/json' % quote(name))
        try:
            resp = urlopen(url)
            data = resp.read().decode() # for now
            d = json.loads(data)
            md = Metadata()
            md.update(d['info'])
            dist = Distribution(md)
            urls = d['urls']
            if urls:
                info = urls[0]
                md['Download-URL'] = info['url']
                if 'md5_digest' in info:
                    dist.md5_digest = info['md5_digest']
                dist.locator = self
                result[md.version] = dist
        except Exception as e:
            logger.exception('JSON fetch failed: %s', e)
        return result

class Page(object):
    "This class represents a scraped HTML page."
    # The following slightly hairy-looking regex just looks for the contents of
    # an anchor link, which has an attribute "href" either immediately preceded
    # or immediately followed by a "rel" attribute. The attribute values can be
    # declared with double quotes, single quotes or no quotes - which leads to
    # the length of the expression.
    _href = re.compile("""
(rel\s*=\s*(?:"(?P<rel1>[^"]*)"|'(?P<rel2>[^']*)'|(?P<rel3>[^>\s\n]*))\s+)?
href\s*=\s*(?:"(?P<url1>[^"]*)"|'(?P<url2>[^']*)'|(?P<url3>[^>\s\n]*))
(\s+rel\s*=\s*(?:"(?P<rel4>[^"]*)"|'(?P<rel5>[^']*)'|(?P<rel6>[^>\s\n]*)))?
""", re.I | re.S | re.X)
    _base = re.compile(r"""<base\s+href\s*=\s*['"]?([^'">]+)""", re.I | re.S)

    def __init__(self, data, url):
        """
        Initialise an instance with the Unicode page contents and the URL they
        came from.
        """
        self.data = data
        self.base_url = self.url = url
        m = self._base.search(self.data)
        if m:
            self.base_url = m.group(1)

    _clean_re = re.compile(r'[^a-z0-9$&+,/:;=?@.#%_\\|-]', re.I)

    @cached_property
    def links(self):
        """
        Return the URLs of all the links on a page together with information
        about their "rel" attribute, for determining which ones to treat as
        downloads and which ones to queue for further scraping.
        """
        def clean(url):
            "Tidy up an URL."
            scheme, netloc, path, params, query, frag = urlparse(url)
            return urlunparse((scheme, netloc, quote(path),
                               params, query, frag))

        result = set()
        for match in self._href.finditer(self.data):
            d = match.groupdict('')
            rel = (d['rel1'] or d['rel2'] or d['rel3'] or
                   d['rel4'] or d['rel5'] or d['rel6'])
            url = d['url1'] or d['url2'] or d['url3']
            url = urljoin(self.base_url, url)
            url = unescape(url)
            url = self._clean_re.sub(lambda m: '%%%2x' % ord(m.group(0)), url)
            result.add((url, rel))
        # We sort the result, hoping to bring the most recent versions
        # to the front
        result = sorted(result, key=lambda t: t[0], reverse=True)
        return result


class SimpleScrapingLocator(Locator):
    """
    A locator which scrapes HTML pages to locate downloads for a distribution.
    This runs multiple threads to do the I/O; performance is at least as good
    as pip's PackageFinder, which works in an analogous fashion.
    """

    # These are used to deal with various Content-Encoding schemes.
    decoders = {
        'deflate': zlib.decompress,
        'gzip': lambda b: gzip.GzipFile(fileobj=BytesIO(d)).read(),
        'none': lambda b: b,
    }

    def __init__(self, url, timeout=None, num_workers=10):
        super(SimpleScrapingLocator, self).__init__()
        self.base_url = ensure_slash(url)
        self.timeout = timeout
        self._page_cache = {}
        self._seen = set()
        self._to_fetch = queue.Queue()
        self._bad_hosts = set()
        self.skip_externals = False
        self.num_workers = num_workers
        self._lock = threading.RLock()

    def _prepare_threads(self):
        """
        Threads are created only when get_project is called, and terminate
        before it returns. They are there primarily to parallelise I/O (i.e.
        fetching web pages).
        """
        self._threads = []
        for i in range(self.num_workers):
            t = threading.Thread(target=self._fetch)
            t.setDaemon(True)
            t.start()
            self._threads.append(t)

    def _wait_threads(self):
        """
        Tell all the threads to terminate (by sending a sentinel value) and
        wait for them to do so.
        """
        # Note that you need two loops, since you can't say which
        # thread will get each sentinel
        for t in self._threads:
            self._to_fetch.put(None)    # sentinel
        for t in self._threads:
            t.join()
        self._threads = []

    def _get_project(self, name):
        self.result = result = {}
        self.project_name = name
        url = urljoin(self.base_url, '%s/' % quote(name))
        self._seen.clear()
        self._page_cache.clear()
        self._prepare_threads()
        try:
            logger.debug('Queueing %s', url)
            self._to_fetch.put(url)
            self._to_fetch.join()
        finally:
            self._wait_threads()
        del self.result
        return result

    platform_dependent = re.compile(r'\b(linux-(i\d86|x86_64|arm\w+)|'
                                    r'win(32|-amd64)|macosx-?\d+)\b', re.I)

    def _is_platform_dependent(self, url):
        """
        Does an URL refer to a platform-specific download?
        """
        return self.platform_dependent.search(url)

    def _process_download(self, url):
        """
        See if an URL is a suitable download for a project.

        If it is, register information in the result dictionary (for
        _get_project) about the specific version it's for.

        Note that the return value isn't actually used other than as a boolean
        value.
        """
        if self._is_platform_dependent(url):
            info = None
        else:
            info = self.convert_url_to_download_info(url, self.project_name)
        logger.debug('process_download: %s -> %s', url, info)
        if info:
            with self._lock:    # needed because self.result is shared
                self._update_version_data(self.result, info)
        return info

    def _should_queue(self, link, referrer, rel):
        """
        Determine whether a link URL from a referring page and with a
        particular "rel" attribute should be queued for scraping.
        """
        scheme, netloc, path, _, _, _ = urlparse(link)
        if path.endswith(self.source_extensions + self.binary_extensions +
                         self.excluded_extensions):
            result = False
        elif self.skip_externals and not link.startswith(self.base_url):
            result = False
        elif not referrer.startswith(self.base_url):
            result = False
        elif rel not in ('homepage', 'download'):
            result = False
        elif scheme not in ('http', 'https', 'ftp'):
            result = False
        elif self._is_platform_dependent(link):
            result = False
        else:
            host = netloc.split(':', 1)[0]
            if host.lower() == 'localhost':
                result = False
            else:
                result = True
        logger.debug('should_queue: %s (%s) from %s -> %s', link, rel,
                     referrer, result)
        return result

    def _fetch(self):
        """
        Get a URL to fetch from the work queue, get the HTML page, examine its
        links for download candidates and candidates for further scraping.

        This is a handy method to run in a thread.
        """
        while True:
            url = self._to_fetch.get()
            try:
                if url:
                    page = self.get_page(url)
                    if page is None:    # e.g. after an error
                        continue
                    for link, rel in page.links:
                        if link not in self._seen:
                            self._seen.add(link)
                            if (not self._process_download(link) and
                                self._should_queue(link, url, rel)):
                                logger.debug('Queueing %s from %s', link, url)
                                self._to_fetch.put(link)
            finally:
                # always do this, to avoid hangs :-)
                self._to_fetch.task_done()
            if not url:
                #logger.debug('Sentinel seen, quitting.')
                break

    def get_page(self, url):
        """
        Get the HTML for an URL, possibly from an in-memory cache.

        XXX TODO Note: this cache is never actually cleared. It's assumed that
        the data won't get stale over the lifetime of a locator instance (not
        necessarily true for the default_locator).
        """
        # http://peak.telecommunity.com/DevCenter/EasyInstall#package-index-api
        scheme, netloc, path, _, _, _ = urlparse(url)
        if scheme == 'file' and os.path.isdir(url2pathname(path)):
            url = urljoin(ensure_slash(url), 'index.html')

        if url in self._page_cache:
            result = self._page_cache[url]
            logger.debug('Returning %s from cache: %s', url, result)
        else:
            host = netloc.split(':', 1)[0]
            result = None
            if host in self._bad_hosts:
                logger.debug('Skipping %s due to bad host %s', url, host)
            else:
                req = Request(url, headers={'Accept-encoding': 'identity'})
                try:
                    logger.debug('Fetching %s', url)
                    resp = urlopen(req, timeout=self.timeout)
                    logger.debug('Fetched %s', url)
                    headers = resp.info()
                    content_type = headers.get('Content-Type', '')
                    if HTML_CONTENT_TYPE.match(content_type):
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
                        try:
                            data = data.decode(encoding)
                        except UnicodeError:
                            data = data.decode('latin-1')    # fallback
                        result = Page(data, final_url)
                        self._page_cache[final_url] = result
                except HTTPError as e:
                    if e.code != 404:
                        logger.exception('Fetch failed: %s: %s', url, e)
                except URLError as e:
                    logger.exception('Fetch failed: %s: %s', url, e)
                    with self._lock:
                        self._bad_hosts.add(host)
                except Exception as e:
                    logger.exception('Fetch failed: %s: %s', url, e)
                finally:
                    self._page_cache[url] = result   # even if None (failure)
        return result

    _distname_re = re.compile('<a href=[^>]*>([^<]+)<')

    def get_distribution_names(self):
        """
        Return all the distribution names known to this locator.
        """
        result = set()
        page = self.get_page(self.base_url)
        for match in self._distname_re.finditer(page.data):
            result.add(match.group(1))
        return result

class DirectoryLocator(Locator):
    def __init__(self, path):
        super(DirectoryLocator, self).__init__()
        path = os.path.abspath(path)
        if not os.path.isdir(path):
            raise ValueError('Not a directory: %r' % path)
        self.base_dir = path

    def should_include(self, filename, parent):
        """
        Should a filename be considered as a candidate for a distribution
        archive? As well as the filename, the directory which contains it
        is provided, though not used by the current implementation.
        """
        return filename.endswith(self.downloadable_extensions)

    def _get_project(self, name):
        result = {}
        for root, dirs, files in os.walk(self.base_dir):
            for fn in files:
                if self.should_include(fn, root):
                    fn = os.path.join(root, fn)
                    url = urlunparse(('file', '',
                                      pathname2url(os.path.abspath(fn)),
                                      '', '', ''))
                    info = self.convert_url_to_download_info(url, name)
                    if info:
                        self._update_version_data(result, info)
        return result

    def get_distribution_names(self):
        """
        Return all the distribution names known to this locator.
        """
        result = set()
        for root, dirs, files in os.walk(self.base_dir):
            for fn in files:
                if self.should_include(fn, root):
                    fn = os.path.join(root, fn)
                    url = urlunparse(('file', '',
                                      pathname2url(os.path.abspath(fn)),
                                      '', '', ''))
                    info = self.convert_url_to_download_info(url, None)
                    if info:
                        result.add(info['name'])
        return result


class AggregatingLocator(Locator):
    """
    Chain and/or merge a list of locators.
    """
    def __init__(self, *locators, **kwargs):
        super(AggregatingLocator, self).__init__()
        self.locators = locators
        self.merge = kwargs.get('merge', False)

    def _get_project(self, name):
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

    def get_distribution_names(self):
        """
        Return all the distribution names known to this locator.
        """
        result = set()
        for locator in self.locators:
            try:
                result |= locator.get_distribution_names()
            except NotImplementedError:
                pass
        return result


default_locator = AggregatingLocator(
                    #PyPIJSONLocator('http://pypi.python.org/pypi'),
                    SimpleScrapingLocator('http://pypi.python.org/simple/',
                                          timeout=3.0))

def locate(requirement, scheme='default'):
    """
    Locate a downloadable distribution, given a requirement (project name and
    version constraints, if any).
    """
    logger.debug('locate %r starting', requirement)
    result = None
    scheme = get_scheme(scheme)
    matcher = scheme.matcher(requirement)
    versions = default_locator.get_project(matcher.name)
    if versions:
        # sometimes, versions are invalid
        slist = []
        for k in versions:
            try:
                if matcher.match(k):
                    slist.append(k)
            except Exception:
                pass # slist.append(k)
        if len(slist) > 1:
            slist = sorted(slist, key=scheme.key)
        if slist:
            result = versions[slist[-1]]
    logger.debug('locate %r -> %s', requirement, result)
    return result
