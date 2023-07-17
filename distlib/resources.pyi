from __future__ import annotations
from .util import Cache, cached_property
# Anything that uses _frozen_importlib_external directly (rather than the 
# importlib.abc equivalents) will fail certain checks.
# Because distlib directly uses _frozen_importlib_external, 
# importlib.
from importlib.abc import (
    Finder,
    Loader,
    MetaPathFinder,
    PathEntryFinder,
)
from io import BufferedReader, BytesIO
from collections.abc import Callable, Iterator
from logging import Logger
from types import ModuleType
from typing import IO
from typing_extensions import Final, Literal, TypeAlias
from zipimport import zipimporter
import sys

# NamespaceLoader wasn't publicly accessible until 3.11; before that,
# it did not inherit from Loader, so it is named explicitly for compatibility.
if sys.version_info[:2] >= (3, 11):
    from importlib.machinery import NamespaceLoader
else:
    from _frozen_importlib_external import (  # type: ignore[import]
        _NamespaceLoader as NamespaceLoader
    )

# START STUB ONLY

# MetaPathFinder and PathEntryFinder no longer subclass Finder in >= 3.10.
_FinderTypes: TypeAlias = Finder | MetaPathFinder | PathEntryFinder
_LoaderTypes: TypeAlias = NamespaceLoader | Loader
_ResourceInstance: TypeAlias = Resource | ResourceContainer
if sys.platform.startswith("java"):
    _skipped_extensions: TypeAlias = tuple[
        Literal[".pyc"], Literal[".pyo"], Literal[".class"]
    ]
else:
    _skipped_extensions: TypeAlias = tuple[Literal[".pyc"], Literal[".pyo"]]

# END STUB ONLY

_dummy_module: Final[ModuleType]
_finder_cache: Final[dict[str, ResourceFinder]]
_finder_registry: Final[dict[type[_LoaderTypes], ResourceFinder]]
cache: ResourceCache | None  # documented
logger: Logger

def finder(package: str) -> ResourceFinder: ...
def finder_for_path(path: str) -> ResourceFinder: ...
def register_finder(  # documented
    loader: _LoaderTypes,
    finder_maker: ResourceFinder | Callable[[ModuleType], _FinderTypes],
) -> None: ...

class ResourceBase():
    finder: ResourceFinder
    name: str
    def __init__(self, finder: ResourceFinder, name: str) -> None: ...

# The below class is improperly documented, being ascribed methods that are
# uniquely present in only some subclasses.
class Resource(ResourceBase):
    is_container: bool  # documented as a property
    # @abstractmethod
    def as_stream(self) -> IO[bytes]: ...  # documented
    @cached_property
    def bytes(self) -> bytes: ...  # documented
    @cached_property
    def file_path(self) -> str: ...  # documented
    @cached_property
    def size(self) -> int: ...  # documented

class ResourceCache(Cache):  # documented
    def __init__(self, base: str | None = ...) -> None: ...  # documented
    def get(self, resource: _ResourceInstance) -> str: ...  # documented
    # @abstractmethod
    def is_stale(  # documented
        self,
        resource: _ResourceInstance,
        path: str
    ) -> Literal[True]: ...

class ResourceContainer(ResourceBase):
    is_container: bool

    @cached_property
    def resources(self) -> set[str]: ...

class ResourceFinder():  # documented
    base: str
    loader: _LoaderTypes
    module: ModuleType
    skipped_extensions: _skipped_extensions
    def __init__(self, module: ModuleType) -> None: ...  # documented
    def _adjust_path(self, path: str) -> str: ...
    def _find(self, path: str) -> bool: ...
    # FIXME: Either this implementation or the one in ZipResourceFinder needs to be
    # changed. This supertype is not compatible with ZipResourceFinder._is_directory.
    @staticmethod
    def _is_directory(s: str) -> bool: ...
    def _make_path(self, resource_name: str) -> str: ...
    def find(self, resource_name: str) -> _ResourceInstance | None: ...  # documented
    def get_bytes(self, resource: _ResourceInstance) -> bytes: ...  # documented
    # FIXME: documented, but could be considered an LSP violation.
    # One possible fix is using an empty string rather than None, since it is falsey.
    def get_cache_info(
        self,
        resource: _ResourceInstance
    ) -> tuple[str | None, str]: ...
    def get_resources(self, resource: _ResourceInstance) -> set[str]: ...
    def get_size(self, resource: _ResourceInstance) -> int: ...  # documented
    # FIXME: Possible LSP violation; it is documented to return a generic binary
    # stream, but return is always BufferedReader. One possible fix is creating 
    # an abstractmethod.
    def get_stream(self, resource: _ResourceInstance) -> BufferedReader | IO[bytes]: ...
    def is_container(self, resource: _ResourceInstance) -> bool: ...
    # documented as returning a generator, despite its name and return type.
    # Generator subclasses Iterator, and this is simply an Iterator.
    def iterator(self, resource_name: str) -> Iterator[_ResourceInstance] | None: ...

class ZipResourceFinder(ResourceFinder):  # documented
    _files: Final[dict[str, tuple[str, int, int, int, int, int, int, int]]]
    archive: str
    index: list[str]
    loader: zipimporter  # inherits from _LoaderBasics, so this type-checks fine
    prefix_len: int
    def __init__(self, module: ModuleType) -> None: ...
    def _adjust_path(self, path: str) -> str: ...
    def _find(self, path: str) -> bool: ...
    # FIXME: see supertype
    def _is_directory(self, path: str) -> bool: ...  # type: ignore
    def get_bytes(self, resource: _ResourceInstance) -> bytes: ...
    def get_cache_info(self, resource: _ResourceInstance) -> tuple[str, str]: ...
    def get_resources(self, resource: _ResourceInstance) -> set[str]: ...
    def get_size(self, resource: _ResourceInstance) -> int: ...
    def get_stream(self, resource: _ResourceInstance) -> BytesIO: ...
