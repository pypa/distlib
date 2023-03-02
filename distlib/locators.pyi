from __future__ import annotations
from .database import Distribution, DistributionPath
from .util import cached_property, ServerProxy
from .version import Matcher, VersionScheme
from collections.abc import Callable
from http.client import HTTPMessage, HTTPResponse
from logging import Logger
from queue import Queue
from re import Match, Pattern
from threading import RLock, Thread
from typing import IO
from typing_extensions import (
    Any,
    Literal,
    NoReturn,
    NotRequired,
    overload,
    TypedDict,
    TypeVar,
    Unpack,
)
from urllib.request import (
    HTTPRedirectHandler as BaseRedirectHandler,
    OpenerDirector,
    Request,
)

# START STUB ONLY

_Provider = TypeVar("_Provider", bound=Distribution)
_Other = TypeVar("_Other", bound=Distribution)

class _AggregatingLocator_td(TypedDict, total=False):
    scheme: str
    merge: bool

class _convert_url_td(TypedDict):
    url: str
    filename: str
    md5_digest: NotRequired[str]
    sha256_digest: NotRequired[str]

class _DirectoryLocator_td(TypedDict, total=False):
    scheme: str
    recursive: bool

class _Locator_td(TypedDict, total=False):
    scheme: str

# END STUB ONLY

CHARSET: Pattern[str]
default_locator: AggregatingLocator  # documented
DEFAULT_INDEX: str
HASHER_HASH: Pattern[str]
HTML_CONTENT_TYPE: Pattern[str]
# locate is documented as a function, but is technically an alias to a method
locate: Callable[[str, str], Distribution | None]  # default_locator.locate
logger: Logger


def get_all_distribution_names(url: str | None = ...) -> list[str]: ...  # documented

class Locator():
    _cache: dict[
        str,
        dict[str, Distribution | dict[str, set[str | None] | tuple[str, str] | None]],
    ]
    _scheme: str
    binary_extensions: tuple[Literal[".egg"], Literal[".exe"], Literal[".whl"]]
    source_extensions: tuple[
        Literal[".tar.gz"],
        Literal[".tar.bz2"],
        Literal[".tar"],
        Literal[".zip"],
        Literal[".tgz"],
        Literal[".tbz"],
    ]
    downloadable_extensions: tuple[
        Literal[".tar.gz"],
        Literal[".tar.bz2"],
        Literal[".tar"],
        Literal[".zip"],
        Literal[".tgz"],
        Literal[".tbz"],
        Literal[".whl"],
    ]
    errors: Queue[str]
    excluded_extensions: tuple[Literal[".pdf"]]
    matcher: Matcher | None  # documented with non-existent "VersionMatcher"
    opener: OpenerDirector
    wheel_tags: set[list[tuple[str | None, str, str]]] | None
    def __init__(self, scheme: str = ...) -> None: ...  # documented
    # scheme and its getter/setter do not use decorators in implementation
    def _get_digest(
        self, info: dict[str, str | dict[str, str] | None]
    ) -> tuple[str, str] | None: ...
    # @abstractmethod
    def _get_project(  # documented
        self,
        name: Any
    ) -> NoReturn | dict[str, Any]: ...
    def _get_scheme(self) -> str: ...
    def _set_scheme(self, value: str) -> None: ...
    def _update_version_data(
        self,
        result: dict[
            str, Distribution | dict[str, set[str | None] | tuple[str, str] | None]
        ],
        info: dict[str, str],
    ) -> None: ...
    def clear_cache(self) -> None: ...
    def clear_errors(self) -> None: ...
    def convert_url_to_download_info(  # documented
        self, url: str, project_name: str | None
    ) -> _convert_url_td | None: ...
    # @abstractmethod
    def get_distribution_names(self) -> NoReturn | set[str]: ...  # documented
    def get_errors(self) -> list[str]: ...  # documented
    def get_project(  # documented as only returning dict[str, Distribution]
        self, name: str
    ) -> dict[
        str,
        Distribution | dict[str, set[str | None] | tuple[str, str] | None],
    ]: ...
    def locate(  # documented
        self, requirement: str, prereleases: bool = ...
    ) -> Distribution | None: ...
    @overload
    def prefer_url(self, url1: str | None, url2: str) -> str: ...
    @overload
    def prefer_url(self, url1: str | None, url2: None) -> None: ...
    def score_url(self, url: str) -> tuple[bool, bool, bool, bool, bool, str]: ...
    # @property not used in source
    scheme = property(_get_scheme, _set_scheme)
    def split_filename(
        self, filename: str, project_name: str | None
    ) -> tuple[str, str, str | None] | None: ...

class AggregatingLocator(Locator):  # documented
    _scheme: str
    errors: Queue[str]
    locators: tuple[Locator, ...]
    matcher: Matcher | None
    merge: bool
    opener: OpenerDirector
    def __init__(  # documented
        self, *locators: Locator, **kwargs: Unpack[_AggregatingLocator_td]
    ) -> None: ...
    def _get_project(
        self, name: str
    ) -> dict[str, Distribution | dict[str, set[str] | tuple[str, str] | None]]: ...
    def _set_scheme(self, value: str) -> None: ...
    def clear_cache(self) -> None: ...
    def get_distribution_names(self) -> set[str]: ...
    # @property not used in source
    scheme = property(Locator.scheme.fget, _set_scheme)

class DependencyFinder():  # documented
    dists: dict[tuple[str, str], Distribution]
    dists_by_name: dict[str, Distribution]
    locator: Locator
    provided: dict[str, set[tuple[str, Distribution]]]
    reqts: dict[Distribution, set[str]]
    scheme: VersionScheme
    def __init__(self, locator: Locator | None = ...) -> None: ...  # documented
    def add_distribution(self, dist: Distribution) -> None: ...
    def find(  # documented
        self,
        requirement: str | Distribution,
        meta_extras: list[str] | None = ...,
        prereleases: bool = ...,
    ) -> tuple[
        set[Distribution], set[tuple[Literal["unsatisfied"], Distribution | str] | None]
    ]: ...
    def find_providers(self, reqt: str) -> set[Distribution]: ...
    def get_matcher(self, reqt: str) -> Matcher: ...
    # Using TypeVars to indicate 'problems' may mutate to contain the
    # passed-in variables
    def remove_distribution(self, dist: Distribution) -> None: ...
    # Using TypeVars to indicate 'problems' may mutate to contain the
    # passed-in variables
    def try_to_replace(
        self,
        provider: _Provider,
        other: _Other,
        problems: None
        | set[
            tuple[
                Literal["cantreplace"],
                _Provider | None,
                _Other | None,
                set[Distribution | str],
            ]
        ],
    ) -> bool: ...

class DirectoryLocator(Locator):  # documented
    base_dir: str
    errors: Queue[str]
    matcher: Matcher | None
    opener: OpenerDirector
    recursive: bool
    def __init__(  # documented
        self,
        path: str,  # documented as "base_dir: str"
        **kwargs: Unpack[_DirectoryLocator_td]
    ) -> None: ...
    def _get_project(
        self, name: str
    ) -> dict[str, Distribution | dict[str, set[str] | None]]: ...
    def get_distribution_names(self) -> set[str]: ...
    def should_include(self, filename: str, parent: str) -> bool: ...

class DistPathLocator(Locator):  # documented
    distpath: DistributionPath
    errors: Queue[str]
    matcher: Matcher | None
    opener: OpenerDirector
    def __init__(  # documented, self misnamed url
        self, distpath: DistributionPath, **kwargs: Unpack[_Locator_td]
    ) -> None: ...
    def _get_project(
        self, name: str
    ) -> dict[str, Distribution | dict[str, set[str | None]]]: ...

class JSONLocator(Locator):
    errors: Queue[str]
    matcher: Matcher | None
    opener: OpenerDirector
    def _get_project(
        self, name: str
    ) -> dict[str, Distribution | dict[str, set[str]]]: ...
    # @abstractmethod
    def get_distribution_names(self) -> NoReturn: ...  # Intentionally NotImplemented

class Page():
    _base: Pattern[str]
    _clean_re: Pattern[str]
    _href: Pattern[str]
    base_url: str
    data: str
    url: str
    def __init__(self, data: str, url: str) -> None: ...
    @cached_property
    def links(self) -> list[set[tuple[str, str]]]: ...

class PyPIJSONLocator(Locator):
    base_url: str
    errors: Queue[str]
    matcher: Matcher | None
    opener: OpenerDirector
    def __init__(  # documented
        self,
        url: str,
        **kwargs: Unpack[_Locator_td]
    ) -> None: ...
    def _get_project(
        self, name: str
    ) -> dict[str, Distribution | dict[str, set[str] | tuple[str, str]]]: ...
    # @abstractmethod
    def get_distribution_names(self) -> NoReturn: ...

class PyPIRPCLocator(Locator):  # documented
    base_url: str
    client: ServerProxy
    errors: Queue[str]
    matcher: Matcher | None
    opener: OpenerDirector
    def __init__(  # documented
        self,
        url: str,
        **kwargs: Unpack[_Locator_td]
    ) -> None: ...
    def _get_project(
        self, name: str
    ) -> dict[str, Distribution | dict[str, set[str] | tuple[str, str]]]: ...
    # set of `str` inferred from:
    # https://warehouse.pypa.io/api-reference/xml-rpc.html#list-packages
    def get_distribution_names(self) -> set[str]: ...

class RedirectHandler(BaseRedirectHandler):
    def http_error_301(
        self,
        req: Request,
        fp: IO[bytes] | HTTPResponse,
        code: int,
        msg: str,
        headers: HTTPMessage,
    ) -> HTTPResponse: ...
    def http_error_302(
        self,
        req: Request,
        fp: IO[bytes] | HTTPResponse,
        code: int,
        msg: str,
        headers: HTTPMessage,
    ) -> HTTPResponse: ...
    def http_error_303(
        self,
        req: Request,
        fp: IO[bytes] | HTTPResponse,
        code: int,
        msg: str,
        headers: HTTPMessage,
    ) -> HTTPResponse: ...
    def http_error_307(
        self,
        req: Request,
        fp: IO[bytes] | HTTPResponse,
        code: int,
        msg: str,
        headers: HTTPMessage,
    ) -> HTTPResponse: ...

class SimpleScrapingLocator(Locator):  # documented
    _bad_hosts: set[str]
    _distname_re: Pattern[str]
    _gplock: RLock
    _lock: RLock
    _page_cache: dict[str, Page | None]
    _seen: set[str]
    _threads: list[Thread]
    _to_fetch: Queue[str | None]
    base_url: str
    # This could probably be improved with TypedDicts/Callback Protocols
    decoders: dict[str, Callable[..., bytes] | Callable[..., bytes] | None]
    errors: Queue[str]
    matcher: Matcher | None
    num_workers: int
    opener: OpenerDirector
    platform_check: bool
    platform_dependent: Pattern[str]
    project_name: str
    skip_externals: bool
    timeout: float | None
    def __init__(  # documented
        self,
        url: str,
        timeout: float | None = ...,
        num_workers: int = ...,
        **kwargs: Unpack[_Locator_td],
    ) -> None: ...
    def _fetch(self) -> None: ...
    def _get_project(
        self, name: str
    ) -> dict[str, Distribution | dict[str, set[str] | tuple[str, str]]]: ...
    def _is_platform_dependent(self, url: str) -> None | Match[str]: ...
    def _process_download(self, url: str) -> dict[str, str] | None: ...
    def _prepare_threads(self) -> None: ...
    def _should_queue(self, link: str, referrer: str, rel: str) -> bool: ...
    def _wait_threads(self) -> None: ...
    def get_distribution_names(self) -> set[str]: ...
    def get_page(self, url: str) -> Page | None: ...
