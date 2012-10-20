"""Spider using the XML-RPC PyPI API.

This module contains the class Client, a spider that can be used to find
and retrieve distributions from a project index (like the Python Package
Index), using its XML-RPC API (see documentation of the reference
implementation at http://wiki.python.org/moin/PyPiXmlRpc).
"""

import logging

from ..compat import xmlrpclib
from ..version import get_matcher, UnsupportedVersionError
from .base import BaseClient
from .errors import ProjectNotFound, InvalidSearchField, ReleaseNotFound
from .dist import ReleaseInfo

__all__ = ['Client', 'DEFAULT_XMLRPC_INDEX_URL']

logger = logging.getLogger(__name__)

DEFAULT_XMLRPC_INDEX_URL = 'http://python.org/pypi'

_SEARCH_FIELDS = ['name', 'version', 'author', 'author_email', 'maintainer',
                  'maintainer_email', 'home_page', 'license', 'summary',
                  'description', 'keywords', 'platform', 'download_url']


class Client(BaseClient):
    """Client to query indexes using XML-RPC method calls.

    If no server_url is specified, use the default PyPI XML-RPC URL,
    defined in the DEFAULT_XMLRPC_INDEX_URL constant::

        >>> client = Client()
        >>> client.server_url == DEFAULT_XMLRPC_INDEX_URL
        True

        >>> client = Client("http://someurl/")
        >>> client.server_url
        'http://someurl/'
    """

    def __init__(self, server_url=DEFAULT_XMLRPC_INDEX_URL,
                 prefer_source=True):
        super(Client, self).__init__(prefer_source)
        self.server_url = server_url
        self._projects = {}

    def get_release(self, requirements):
        """Return a release with all complete metadata and distribution
        related informations.
        """
        predicate = get_matcher(requirements)
        releases = self.get_releases(predicate.name)
        release = releases.get_last(predicate)
        self.get_metadata(release.name, str(release.version))
        self.get_distributions(release.name, str(release.version))
        return release

    def get_releases(self, requirements, show_hidden=True, force_update=False):
        """Return the list of existing releases for a specific project.

        Cache the results from one call to another.

        If show_hidden is True, return the hidden releases too.
        If force_update is True, reprocess the index to update the
        informations (eg. make a new XML-RPC call).
        ::

            >>> client = Client()
            >>> client.get_releases('Foo')
            ['1.1', '1.2', '1.3']

        If no such project exists, raise a ProjectNotFound exception::

            >>> client.get_project_versions('UnexistingProject')
            ProjectNotFound: UnexistingProject

        """
        def get_versions(project_name, show_hidden):
            return self.proxy.package_releases(project_name, show_hidden)

        predicate = get_matcher(requirements)
        project_name = predicate.name
        if not force_update and (project_name.lower() in self._projects):
            project = self._projects[project_name.lower()]
            if not project.contains_hidden and show_hidden:
                # if hidden releases are requested, and have an existing
                # list of releases that does not contains hidden ones
                all_versions = get_versions(project_name, show_hidden)
                existing_versions = project.get_versions()
                hidden_versions = set(all_versions) - set(existing_versions)
                for version in hidden_versions:
                    project.add_release(release=ReleaseInfo(project_name,
                                            version, index=self._index))
        else:
            versions = get_versions(project_name, show_hidden)
            if not versions:
                raise ProjectNotFound(project_name)
            project = self._get_project(project_name)
            project.add_releases([ReleaseInfo(project_name, version,
                                              index=self._index)
                                  for version in versions])
        project = project.filter(predicate)
        if len(project) == 0:
            raise ReleaseNotFound("%s" % predicate)
        project.sort_releases()
        return project


    def get_distributions(self, project_name, version):
        """Grab informations about distributions from XML-RPC.

        Return a ReleaseInfo object, with distribution-related informations
        filled in.
        """
        url_infos = self.proxy.release_urls(project_name, version)
        project = self._get_project(project_name)
        if version not in project.get_versions():
            project.add_release(release=ReleaseInfo(project_name, version,
                                                    index=self._index))
        release = project.get_release(version)
        for info in url_infos:
            packagetype = info['packagetype']
            dist_infos = {'url': info['url'],
                          'hashval': info['md5_digest'],
                          'hashname': 'md5',
                          'is_external': False,
                          'python_version': info['python_version']}
            release.add_distribution(packagetype, **dist_infos)
        return release

    def get_metadata(self, project_name, version):
        """Retrieve project metadata.

        Return a ReleaseInfo object, with metadata informations filled in.
        """
        # to be case-insensitive, get the informations from the XMLRPC API
        projects = [d['name'] for d in
                    self.proxy.search({'name': project_name})
                    if d['name'].lower() == project_name]
        if len(projects) > 0:
            project_name = projects[0]

        metadata = self.proxy.release_data(project_name, version)
        project = self._get_project(project_name)
        if version not in project.get_versions():
            project.add_release(release=ReleaseInfo(project_name, version,
                                                    index=self._index))
        release = project.get_release(version)
        release.set_metadata(metadata)
        return release

    def search_projects(self, name=None, operator="or", **kwargs):
        """Find using the keys provided in kwargs.

        You can set operator to "and" or "or".
        """
        for key in kwargs:
            if key not in _SEARCH_FIELDS:
                raise InvalidSearchField(key)
        if name:
            kwargs["name"] = name
        projects = self.proxy.search(kwargs, operator)
        for p in projects:
            project = self._get_project(p['name'])
            try:
                project.add_release(release=ReleaseInfo(p['name'],
                    p['version'], metadata={'summary': p['summary']},
                    index=self._index))
            except UnsupportedVersionError as e:
                logger.warning("Irrational version error found: %s", e)
        return [self._projects[p['name'].lower()] for p in projects]

    def get_all_projects(self):
        """Return the list of all projects registered in the package index"""
        projects = self.proxy.list_packages()
        for name in projects:
            self.get_releases(name, show_hidden=True)

        return [self._projects[name.lower()] for name in set(projects)]

    @property
    def proxy(self):
        """Property used to return the XMLRPC server proxy.

        If no server proxy is defined yet, creates a new one::

            >>> client = Client()
            >>> client.proxy()
            <ServerProxy for python.org/pypi>

        """
        if not hasattr(self, '_server_proxy'):
            self._server_proxy = xmlrpclib.ServerProxy(self.server_url)

        return self._server_proxy
