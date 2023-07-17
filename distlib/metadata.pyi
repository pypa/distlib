from __future__ import annotations
from . import DistlibException
from codecs import StreamReaderWriter
from collections.abc import Callable, Iterator
from encodings.utf_8 import StreamReader
from io import BufferedReader, StringIO
from logging import Logger
from re import Pattern
from typing_extensions import Any, Final, Self, TypeAlias

# START STUB ONLY

# Using TypeAliases for recursive type hints.
_RecursiveType: TypeAlias = str | list["_RecursiveType"] | dict[str, "_RecursiveType"]
# fmt: off
_RecursiveDict: TypeAlias = dict[str, str
    | list[str | list[str | "_RecursiveDict"]
         | dict[str, str | list[str | "_RecursiveDict"] | "_RecursiveDict"]
      ]
    | dict[str, str
         | list[str | list[str | "_RecursiveDict"]
              | dict[str, str | list[str | "_RecursiveDict"] | "_RecursiveDict"]
           ],
      ],
]

# END STUB ONLY

__all__ = ["Metadata", "PKG_INFO_ENCODING", "PKG_INFO_PREFERRED_VERSION"]

_241_FIELDS: Final[tuple[str, str, str, str, str, str, str, str, str, str, str]]
_314_FIELDS: Final[tuple[str, str, str, str, str, str, str, str, str, str, str,
    str, str, str, str, str, str]]
_314_MARKERS: Final[tuple[str, str, str, str, str]]
_345_FIELDS: Final[tuple[str, str, str, str, str, str, str, str, str, str, str,
    str, str, str, str, str, str, str, str, str, str, str]]
_345_MARKERS: Final[tuple[str, str, str, str, str, str, str, str]]
_426_FIELDS: Final[tuple[str, str, str, str, str, str, str, str, str, str, str,
    str, str, str, str, str, str,str, str, str, str,str, str, str, str, str, str]]
_426_MARKERS: Final[tuple[str, str, str, str, str]]
_566_FIELDS: Final[tuple[str, str, str, str, str, str, str, str, str, str, str,
    str, str, str, str, str, str, str, str, str, str, str, str, str, str, str,
    str, str, str, str, str]]
_566_MARKERS: Final[tuple[str]]
_643_FIELDS: Final[tuple[str, str, str, str, str, str, str, str, str, str, str,
    str, str, str, str, str, str, str, str, str, str, str, str, str,str, str,
    str, str, str, str, str, str, str]]
_643_MARKERS: Final[tuple[str, str]]
_ALL_FIELDS: Final[set[str]]
_ATTR2FIELD: Final[dict[str, str]]
_ELEMENTSFIELD: Final[tuple[str]]
_FIELD2ATTR: Final[dict[str, str]]
_FILESAFE: Final[Pattern[str]]
_LINE_PREFIX_1_2: Final[Pattern[str]]
_LINE_PREFIX_PRE_1_2: Final[Pattern[str]]
_LISTFIELDS: Final[tuple[str, str, str, str, str, str, str, str, str, str, str,
    str, str, str, str]]
# fmt: on
_LISTTUPLEFIELDS: Final[tuple[str]]
_MISSING: Final[object]
_PREDICATE_FIELDS: Final[tuple[str, str, str]]
_UNICODEFIELDS: Final[tuple[str, str, str, str]]
_VERSIONS_FIELDS: Final[tuple[str]]
_VERSION_FIELDS: Final[tuple[str]]
EXTRA_RE: Pattern[str]
LEGACY_METADATA_FILENAME: str
logger: Logger
METADATA_FILENAME: str
PKG_INFO_ENCODING: str
PKG_INFO_PREFERRED_VERSION: str
WHEEL_METADATA_FILENAME: str

# There should probably be a series of nested TypedDicts for
# the metadata, but I am not sure of all possible keys and
# valid types for each.

def _best_version(fields: dict[str, str | list[str | tuple[str, str]]]) -> str: ...
def _get_name_and_version(
    name: str | list[str | tuple[str, str]],
    version: str | list[str | tuple[str, str]],
    for_filename: bool = ...,
) -> str: ...
def _version2fieldlist(
    version: str | list[str | tuple[str, ...]]
) -> tuple[str, ...]: ...

class MetadataMissingError(DistlibException): ...
class MetadataConflictError(DistlibException): ...
class MetadataUnrecognizedVersionError(DistlibException): ...
class MetadataInvalidError(DistlibException): ...

class LegacyMetadata():
    _dependencies: None  # dead code?
    _fields: Final[dict[str, str | list[str | tuple[str, str]]]]
    requires_files: list[Any]  # dead code?
    scheme: str
    def __contains__(self, name: str) -> bool: ...
    def __delitem__(self, name: str) -> None: ...
    def __getattr__(self, name: str) -> list[str] | str: ...
    def __getitem__(self, name: str) -> str | list[str | tuple[str, str]]: ...
    def __init__(
        self,
        path: str | None = ...,
        fileobj: StringIO | None = ...,
        mapping: dict[str, str | list[str]] | Self | None = ...,
        scheme: str = ...,
    ) -> None: ...
    def __iter__(self) -> Iterator[str]: ...
    def __setitem__(
        self, name: str, value: str | list[str | tuple[str, str]]
    ) -> None: ...
    def _convert_name(self, name: str) -> str: ...
    def _default_value(self, name: str) -> str: ...
    def _remove_line_prefix(self, value: str | list[str | tuple[str, str]]) -> str: ...
    def _write_field(
        self,
        fileobj: StreamReaderWriter | StringIO,
        name: str,
        value: str | list[str | tuple[str, str]],
    ) -> None: ...
    def add_requirements(self, requirements: list[str]) -> None: ...
    def check(self, strict: bool = ...) -> tuple[list[str], list[str]]: ...
    def get(
        self, name: str, default: object = ...
    ) -> str | list[str | tuple[str, str]]: ...
    def get_fullname(self, filesafe: bool = ...) -> str: ...
    def is_field(self, name: str) -> bool: ...
    def is_multi_field(self, name: str) -> bool: ...
    def items(self) -> list[tuple[str, str | list[str]]]: ...
    def keys(self) -> list[str]: ...
    def read(self, filepath: str) -> None: ...
    def read_file(self, fileob: StreamReaderWriter | StringIO) -> None: ...
    def set(self, name: str, value: str | list[str | tuple[str, str]]) -> None: ...
    def set_metadata_version(self) -> None: ...
    def todict(self, skip_missing: bool = ...) -> dict[str, str | list[str]]: ...
    def update(
        self,
        other: dict[str, str | list[str]] | list[tuple[str, str]] | None = ...,
        **kwargs: Any,
    ) -> None: ...
    def values(self) -> list[str | list[str]]: ...
    def write(self, filepath: str, skip_unknown: bool = ...) -> None: ...
    def write_file(
        self, fileobject: StreamReaderWriter | StringIO | None, skip_unknown: bool = ...
    ) -> None: ...

class Metadata():  # documented
    __slots__ = ("_data", "_legacy", "scheme")
    DEPENDENCY_KEYS: str
    FIELDNAME_MATCHER: Pattern[str]
    GENERATOR: str
    INDEX_KEYS: str
    LEGACY_MAPPING: dict[str | tuple[int | str, ...], str]
    MANDATORY_KEYS: dict[str, tuple[str, ...]]
    METADATA_VERSION: str
    METADATA_VERSION_MATCHER: Pattern[str]
    NAME_MATCHER: Pattern[str]
    SUMMARY_MATCHER: Pattern[str]
    SYNTAX_VALIDATORS: dict[str, tuple[Pattern[str] | tuple[str | tuple[()], ...]]]
    VERSION_MATCHER: Pattern[str]
    _data: None | dict[
        str,
        tuple[None, dict[str, Any]]
        | tuple[None, list[Any]]
        | tuple[str, list[str | set[str]] | None],
    ]
    _legacy: LegacyMetadata | None
    common_keys: set[str]
    mapped_keys: dict[
        str,
        tuple[None, dict[str, Any]]
        | tuple[None, list[Any]]
        | tuple[str, list[str | set[str]] | None],
    ]
    scheme: str
    # A tracer showed a Callable here, but it could be a false result
    def __getattribute__(
        self, key: str
    ) -> (
        _RecursiveType
        | Callable[..., Any]
        | Metadata
        | dict[str, tuple[Pattern[str], tuple[()] | tuple[str]]]
        | dict[str, tuple[()] | tuple[str]]
        | None
    ): ...
    def __init__(
        self,
        path: str | None = ...,
        fileobj: BufferedReader | StreamReader | StringIO | None = ...,
        mapping: dict[str, str] | None = ...,
        scheme: str = ...,
    ) -> None: ...
    def __setattr__(
        self, key: str, value: _RecursiveType | Metadata | None
    ) -> None: ...
    def _from_legacy(self) -> dict[str, str | list[str | dict[str, list[str]]]]: ...
    def _to_legacy(self) -> LegacyMetadata: ...
    def _validate_mapping(
        self, mapping: _RecursiveDict, scheme: str | None
    ) -> None: ...
    def _validate_value(
        self,
        key: str,
        value: _RecursiveType | Metadata | None,
        scheme: str | None = ...,
    ) -> None: ...
    def add_requirements(self, requirements: list[str]) -> None: ...
    @property
    def dependencies(
        self,
    ) -> dict[str, str | list[str | dict[str, str | list[str]]]]: ...
    @dependencies.setter
    def dependencies(
        self, value: dict[str, str | list[str | dict[str, str | list[str]]]]
    ) -> None: ...
    @property
    def dictionary(self) -> dict[str, str | list[str | dict[str, str | list[str]]]]: ...
    def get_requirements(
        self,
        reqts: str | list[dict[str, str | list[str]] | str | None],
        extras: list[str] | set[str] | None = ...,
        env: dict[str, str] | None = ...,
    ) -> str | list[dict[str, str | list[str]] | str | None]: ...
    @property
    def name_and_version(self) -> str: ...
    @property
    def provides(self) -> str | list[str]: ...
    @provides.setter
    def provides(self, value: str | list[str]) -> None: ...
    def todict(self) -> dict[str,  # documented
        str | list[str | dict[str, str | list[str]]]
    ]: ...
    def validate(self) -> None: ...
    def write(
        self,
        path: str | None = ...,
        fileobj: StreamReaderWriter | StringIO | None = ...,
        legacy: bool = ...,
        skip_unknown: bool = ...,
    ) -> None: ...
