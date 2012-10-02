"""Exceptions raised by packaging.pypi code."""

from .. import DistlibException

class PyPIError(DistlibException):
    pass

class ProjectNotFound(PyPIError):
    """Project has not been found"""


class DistributionNotFound(PyPIError):
    """The release has not been found"""


class ReleaseNotFound(PyPIError):
    """The release has not been found"""


class CantParseArchiveName(PyPIError):
    """An archive name can't be parsed to find distribution name and version"""


class DownloadError(PyPIError):
    """An error has occurs while downloading"""


class HashDoesNotMatch(DownloadError):
    """Compared hashes does not match"""


class UnsupportedHashName(PyPIError):
    """A unsupported hashname has been used"""


class UnableToDownload(PyPIError):
    """All mirrors have been tried, without success"""


class InvalidSearchField(PyPIError):
    """An invalid search field has been used"""
