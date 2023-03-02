from __future__ import annotations
from .metadata import Metadata
from collections.abc import Callable
from http.client import HTTPResponse
from logging import Logger
from urllib.request import HTTPBasicAuthHandler, HTTPSHandler, Request
from typing import IO
from typing_extensions import Any, Literal, TypedDict

# START STUB ONLY

class _search_terms_td(TypedDict, total=False):
    name: str
    version: str
    stable_version: str
    author: str
    author_email: str
    maintainer: str
    maintainer_email: str
    home_page: str
    license: str
    summary: str
    description: str
    keywords: str
    platform: str
    download_url: str
    classifiers: list[str]
    project_url: str
    docs_url: str

class _search_return_td(TypedDict):
    _pypi_ordering: int
    name: str
    version: str
    summary: str

# END STUB ONLY

DEFAULT_INDEX: str
DEFAULT_REALM: str
logger: Logger

class PackageIndex():  # documented, no attribute named "mirrors"
    boundary: bytes  # documented
    gpg: str | None  # documented
    gpg_home: str | None  # documented
    password: dict[str, str] | str | None  # documented
    password_handler: HTTPBasicAuthHandler | None
    realm: dict[str, str] | str | None
    ssl_verifier: HTTPSHandler | None
    url: str | None
    username: dict[str, str] | str | None  # documented
    # __init__ is improperly documented as having second parameter "mirror_host=None"
    def __init__(self, url: str | None = ...) -> None: ...
    # This imports a function of the same name from .util, but that function
    # is commented out. So, I do not really know what to do with this.
    # As is, it will cause an unhandled ImportError.
    def _get_pypirc_command(self) -> None: ...
    def _reader(self, name: str, stream: IO[Any], outbuf: list[str]) -> None: ...
    def check_credentials(self) -> None: ...
    def download_file(
        self,
        url: str,
        destfile: str,
        digest: str | tuple[str, str] | None = ...,
        reporthook: Callable[[int, int, int], object] | None = ...,
    ) -> None: ...
    def encode_request(
        self,
        # Source indicates field's list of tuples may also contain a list or
        # a tuple. I see no example of this case, so contents of those are
        # presumed to be str from 'v in values ... v.encode'.
        # I could not determine if the inner tuple had a fixed length, so it
        # is typed variadically.
        fields: list[tuple[str, str | list[str] | tuple[str, ...]]],
        # There is no way to explicitly annotate an empty-list being returned,
        # but empty lists should pass type-check against any subscripted list.
        files: list[tuple[str, str | bytes, str | bytes]],
    ) -> Request: ...
    def get_sign_command(
        self,
        filename: str,
        signer: str | None,
        sign_password: str | None,
        keystore: str | None = ...,
    ) -> tuple[list[str], str]: ...
    def get_verify_command(
        self, signature_filename: str, data_filename: str, keystore: str | None = ...
    ) -> list[str]: ...
    def read_configuration(self) -> None: ...  # documented
    def register(self, metadata: Metadata) -> HTTPResponse: ...  # documented
    def run_command(
        self, cmd: list[str], input_data: bytes | None = ...
    ) -> tuple[int, list[str], list[str]]: ...
    def save_configuration(self) -> None: ...  # documented
    def search(  # documented
        self,
        terms: _search_terms_td | str,
        operator: Literal["and"] | Literal["or"] | None = ...
    ) -> list[_search_return_td]: ...
    def send_request(self, req: Request) -> HTTPResponse: ...
    def sign_file(
        self,
        filename: str,
        signer: str | None,
        sign_password: str | None,
        keystore: str | None = ...,
    ) -> str: ...
    def upload_documentation(  # documented
        self, metadata: Metadata, doc_dir: str
    ) -> HTTPResponse: ...
    def upload_file(  # documented
        self,
        metadata: Metadata,
        filename: str,
        signer: str | None = ...,
        sign_password: str | None = ...,
        filetype: str = ...,
        pyversion: str = ...,
        keystore: str | None = ...,
    ) -> HTTPResponse: ...
    def verify_signature(  # documented
        self, signature_filename: str, data_filename: str, keystore: str | None = ...
    ) -> bool: ...
