from __future__ import annotations
from .locators import Locator
from .metadata import Metadata
from .resources import Resource, ResourceContainer, ResourceFinder
from .util import cached_property, ExportEntry
from .version import VersionScheme
from codecs import StreamReader
from collections.abc import Iterator
from io import BufferedReader, StringIO
from logging import Logger
from typing_extensions import (
    Literal,
    Self,
    TypedDict,
    TypeVar,
    Unpack,
)

# START STUB ONLY

class _dist_td(TypedDict, total=False):
    path: str | None
    fileobj: BufferedReader | StreamReader | StringIO | None
    mapping: dict[str, str] | None
    scheme: str

class _locations_td(TypedDict, total=False):
    prefix: str
    purelib: str
    platlib: str
    scripts: str
    headers: str
    data: str
    namespace: list[str]
    lib: str  # used internally

_PathVar = TypeVar("_PathVar", bound=list[str])

# END STUB ONLY

__all__ = [
    "Distribution",
    "BaseInstalledDistribution",
    "InstalledDistribution",
    "EggInfoDistribution",
    "DistributionPath",
]

COMMANDS_FILENAME: str
DIST_FILES: tuple[str, str, str, str, str, str, str]
DISTINFO_EXT: str
EXPORTS_FILENAME: str
logger: Logger
new_dist_class: type[InstalledDistribution]
old_dist_class: type[EggInfoDistribution]

def get_dependent_dists(  # documented
    dists: list[Distribution], dist: Distribution
) -> list[Distribution]: ...
def get_required_dists(  # documented to return a list, implementation returns a set
    dists: list[Distribution], dist: Distribution
) -> set[Distribution]: ...
def make_dist(name: str, version: str, **kwargs: Unpack[_dist_td]) -> Distribution: ...
def make_graph(  # improperly documented or implemented; test_dependency_finder passes
                 # in a set from finder.find
    dists: set[Distribution] | list[Distribution], scheme: str = ...
) -> DependencyGraph: ...

class Distribution():  # documented
    build_time_dependency: bool
    # Not obvious from source, but it appears 'context' is the
    # execution_context parameter to distlib.markers.interpet.
    context: dict[str, str] | None
    digest: tuple[str, str] | None  # documented as a property
    digests: dict[str, str]  # documented as a property
    download_urls: set[str]
    extras: list[str] | set[str] | None
    key: str
    locator: Locator | None  # documented as a property
    metadata: Metadata  # documented as a property
    name: str  # documented as a property
    requested: bool
    version: str  # documented as a property
    def __eq__(self, other: object) -> bool: ...
    def __hash__(self) -> int: ...
    def __init__(self, metadata: Metadata) -> None: ...
    def _get_requirements(self, req_attr: str) -> set[str]: ...
    @property
    def build_requires(self) -> set[str]: ...
    @property
    def dev_requires(self) -> set[str]: ...
    @property
    def download_url(self) -> str: ...  # documented
    def matches_requirement(self, req: str) -> bool: ...
    @property
    def meta_requires(self) -> set[str]: ...
    @property
    def name_and_version(self) -> str: ...
    @property
    def provides(self) -> list[str]: ...
    @property
    def run_requires(self) -> set[str]: ...
    @property
    def source_url(self) -> str | None: ...
    @property
    def test_requires(self) -> set[str]: ...

class BaseInstalledDistribution(Distribution):
    dist_path: DistributionPath | None
    hasher: str | None
    path: str
    def __init__(
        self, metadata: Metadata, path: str, env: DistributionPath | None = ...
    ) -> None: ...
    def get_hash(self, data: bytes, hasher: str | None = ...) -> str: ...

class DependencyGraph():
    adjacency_list: dict[  # documented
        Distribution, list[tuple[Distribution, str | None]]
    ]
    missing: dict[Distribution, list[str]]  # documented
    reverse_list: dict[Distribution, list[str]]  # documented
    def __init__(self) -> None: ...
    def _repr_dist(self, dist: Distribution) -> str: ...
    def add_distribution(self, distribution: Distribution) -> None: ...  # documented
    def add_edge(  # documented
        self, x: Distribution, y: Distribution, label: str | None = ...
    ) -> None: ...
    def add_missing(  # documented
        self,
        distribution: Distribution,
        requirement: str
    ) -> None: ...
    def repr_node(self, dist: Distribution, level: int = ...) -> str: ...  # documented
    def to_dot(self, f: StringIO, skip_disconnected: bool = ...) -> None: ...
    def topological_sort(self) -> tuple[list[Distribution], list[Distribution]]: ...

class DistributionPath():  # documented
    _cache: _Cache
    _cache_egg: _Cache
    _cache_enabled: bool
    _include_dist: bool
    _include_egg: bool
    _scheme: VersionScheme
    path: list[str]
    def __init__(  # documented
        self, path: list[str] | None = ..., include_egg: bool = ...
    ) -> None: ...
    def _generate_cache(self) -> None: ...
    def _get_cache_enabled(self) -> bool: ...
    def _set_cache_enabled(self, value: bool) -> None: ...
    def _yield_distributions(self) -> Iterator[Distribution]: ...
    @property
    def cache_enabled(self) -> bool: ...
    def clear_cache(self) -> None: ...  # documented
    @classmethod
    def distinfo_dirname(cls, name: str, version: str) -> str: ...
    def get_distribution(self, name: str) -> Distribution | None: ...  # documented
    def get_distributions(self) -> Iterator[Distribution]: ...  # documented
    def get_exported_entries(  # documented
        self, category: str, name: str | None = ...
    ) -> Iterator[ExportEntry]: ...
    def get_file_path(self, name: str, relative_path: str) -> str: ...
    def provides_distribution(
        self, name: str, version: str | None = ...
    ) -> Iterator[Distribution]: ...

class EggInfoDistribution(BaseInstalledDistribution):
    modules: list[str]
    path: str
    requested: bool
    shared_locations: dict[str, str]
    def __eq__(self, other: Self | None | object) -> bool: ...
    def __init__(self, path: str, env: DistributionPath | None = ...) -> None: ...
    def _get_metadata(self, path: str | bytes) -> Metadata: ...
    def check_installed_files(self) -> list[tuple[str, str, bool, bool]]: ...
    def list_distinfo_files(self, absolute: bool = ...) -> Iterator[str]: ...
    def list_installed_files(  # documented
        self
    ) -> list[tuple[str, str | None, int | None]]: ...

class InstalledDistribution(BaseInstalledDistribution):
    finder: ResourceFinder | None
    hasher: str
    locator: None
    modules: list[str]
    requested: bool  # documented as a property
    def __eq__(self, other: object) -> bool: ...
    def __init__(
        self,
        path: str,
        metadata: Metadata | None = ...,
        env: DistributionPath | None = ...,
    ) -> None: ...
    def _get_records(self) -> list[tuple[str, str | None, str | None]]: ...
    def check_installed_files(  # documented
        self,
    ) -> list[None | tuple[
        str,
        Literal["exists", "size", "hash"],
        str | bool,
        str | bool]]: ...
    @cached_property
    def exports(self) -> dict[str, dict[str, ExportEntry]]: ...  # documented
    def get_distinfo_file(self, path: str) -> str: ...
    def get_distinfo_resource(
        self, path: str
    ) -> Resource | ResourceContainer | None: ...
    def get_resource_path(self, relative_path: str) -> str: ...
    def list_distinfo_files(self) -> Iterator[str]: ...  # documented
    def list_installed_files(  # documented
        self
    ) -> Iterator[tuple[str, str, str] | None]: ...
    def read_exports(  # improperly documented to take a filename parameter
        self
    ) -> dict[str, dict[str, ExportEntry]]: ...
    @cached_property
    def shared_locations(self) -> _locations_td: ...
    def write_exports(  # improperly documented to take a filename parameter
        self,
        exports: dict[str, dict[str, ExportEntry]]
    ) -> None: ...
    def write_installed_files(
        self, paths: list[str], prefix: str, dry_run: bool = ...
    ) -> str | None: ...
    def write_shared_locations(
        self, paths: _locations_td, dry_run: bool = ...
    ) -> str | None: ...

class _Cache():
    generated: bool
    name: dict[str, list[Distribution]]
    path: dict[str, Distribution]
    def __init__(self) -> None: ...
    def add(self, dist: Distribution) -> None: ...
    def clear(self) -> None: ...
