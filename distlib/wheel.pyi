from __future__ import annotations
from .database import InstalledDistribution
from .metadata import Metadata
from .scripts import ScriptMaker
from .util import Cache, cached_property
from collections.abc import Callable, Iterator
from logging import Logger
from re import Pattern
from types import ModuleType
from typing_extensions import (
    Any,
    Literal,
    overload,
    Required,
    Self,
    TypeAlias,
    TypedDict,
)
from zipfile import ZipFile

# START STUB ONLY

# bytecode_hashed_invalidation is documented in source, but not in docs.
# The warner callable spec does not specify a return type.
# Warner's arguments are not well defined or created. Documentation dictates that
# warner will be passed two tuples of (major_ver, minor_ver).
# wv = message['Wheel-Version'].split('.', 1)
# file_version = tuple([int(i) for i in wv])
# warner(self.wheel_version, file_version)
# The split('.' max) command implies that there may only be one str to turn into int
# (which conflicts with the documentation wantig 2 ints). Secondly, if passed something
# like "1.2.3", this split command will return ["1", "2.3"]. This means int(i) raises a
# ValueError because 2.3 is not 10 (it is interpreted as int(literal float of 2.3)).
_warnerArg: TypeAlias = tuple[int] | tuple[int, int]
class _install_False_td(TypedDict, total=False):
    warner: Callable[[_warnerArg, _warnerArg], Any]
    lib_only: Literal[False]
    bytecode_hashed_invalidation: bool

# None of these are technically required, but "Required[]" here just clarifies that
# the overloaded case only happens when lib_only is expliitly set to True.
class _install_True_td(TypedDict, total=False):
    warner: Callable[[_warnerArg, _warnerArg], Any]
    lib_only: Required[Literal[True]]
    bytecode_hashed_invalidation: bool

class _paths_platlib_td(TypedDict):
    prefix: str
    scripts: str
    headers: str
    data: str
    platlib: str

class _paths_purelib_td(TypedDict):
    prefix: str
    scripts: str
    headers: str
    data: str
    purelib: str

class _tags_td(TypedDict):
    pyver: list[str]
    abi: list[str]
    arch: list[str]

_paths_td: TypeAlias = _paths_platlib_td | _paths_purelib_td

# END STUB ONLY

ABI: str
ARCH: str
cache: Cache | None  # documented
COMPATIBLE_TAGS: set[tuple[str | None, str, str]]  # documented
FILENAME_RE: Pattern[str]
IMP_PREFIX: str
IMPVER: str
imp: ModuleType | None
LEGACY_METADATA_FILENAME: str
logger: Logger
METADATA_FILENAME: str
NAME_VERSION_RE: Pattern[str]
PYVER: str
SHEBANG_PYTHON: bytes
SHEBANG_PYTHONW: bytes
SHEBANG_RE: Pattern[bytes]
SHEBANG_DETAIL_RE: Pattern[bytes]
VER_SUFFIX: str | None
WHEEL_METADATA_FILENAME: str

def _derive_abi() -> str: ...
def _get_glibc_version() -> list[int] | tuple[int, ...] | None: ...
def _get_suffixes() -> list[str] | None: ...
def _load_dynamic(name: str, path: str | bytes) -> ModuleType | None: ...
def is_compatible(  # documented
    wheel: str | Wheel, tags: set[list[tuple[str | None, str, str]]] | None = ...
) -> bool: ...
@overload
def to_posix(o: str) -> str: ...
@overload
def to_posix(o: bytes) -> bytes: ...

class Mounter():
    impure_wheels: dict[str | bytes, list[tuple[str, str]]]
    libs: dict[str, str]
    def __init__(self) -> None: ...
    def add(self, pathname: str | bytes, extensions: list[tuple[str, str]]) -> None: ...
    # path in find_module is unused. Assuming it exists for backwards compatibility.
    def find_module(self, fullname: str, path: Any = ...) -> Self | None: ...
    def load_module(self, fullname: str) -> ModuleType | None: ...
    def remove(self, pathname: str | bytes) -> None: ...

class Wheel():  # documented
    _filename: str | None
    abi: list[str]  # documented
    arch: list[str]  # documented
    buildver: str  # documented
    dirname: str  # documented
    hash_kind: str
    name: str  # documented
    pyver: list[str]  # documented
    should_verify: bool
    sign: bool
    version: str  # documented
    wheel_version: tuple[int, int]
    def __init__(  # documented as only accepting the parameter "spec: str"
        self, filename: str | None = ..., sign: bool = ..., verify: bool = ...
    ) -> None: ...
    def _get_dylib_cache(self) -> Cache: ...
    def _get_extensions(self) -> list[tuple[str, str]] | None: ...
    def build(  # documented
        self,
        paths: _paths_td,
        tags: _tags_td | None = ...,
        wheel_version: tuple[int, int] | None = ...,
    ) -> str | None: ...
    def build_zip(
        self, pathname: str, archive_paths: list[tuple[str, str]]
    ) -> None: ...
    @property
    def exists(self) -> bool: ...  # documented as a normal attribute
    @property
    def filename(self) -> str | None: ...  # documented as a normal attribute
    def get_hash(
        self, data: bytes, hash_kind: str | None = ...
    ) -> tuple[str, str] | None: ...
    def get_wheel_metadata(self, zf: ZipFile) -> dict[str, str] | None: ...
    # info() is documented as a normal attribute
    @cached_property
    def info(self) -> dict[str, str] | None: ...
    # Kwarg bytecode_hashed_invalidation for install is documented in source, but
    # it is not in docs.
    @overload
    def install(
        self,
        paths: _paths_td,
        maker: ScriptMaker,
        **kwargs: _install_False_td
    ) -> InstalledDistribution: ...
    @overload
    def install(
        self,
        paths: _paths_td,
        maker: ScriptMaker,
        **kwargs: _install_True_td
    ) -> None: ...
    def is_compatible(self) -> bool: ...  # documented
    def is_mountable(self) -> bool: ...  # documented
    @cached_property
    def metadata(self) -> Metadata | None: ...  # documented as a normal variable
    def mount(self, append: bool = ...) -> None: ...  # documented
    def process_shebang(self, data: bytes) -> bytes | None: ...
    def skip_entry(self, arcname: str) -> bool: ...
    @property
    def tags(self) -> Iterator[tuple[str, str, str]] | None: ...
    def unmount(self) -> None: ...  # documented
    def update(  # documented
        self,
        modifier: Callable[[dict[str, str]], bool],
        dest_dir: str | None = ...,
        **kwargs: Any,
    ) -> bool: ...
    def verify(self) -> None: ...  # documented
    def write_record(
        self,
        records: list[tuple[str, str, int]],
        record_path: str,
        archive_record_path: str,
    ) -> None: ...
    def write_records(
        self, info: tuple[str, str], libdir: str, archive_paths: list[tuple[str, str]]
    ) -> None: ...
