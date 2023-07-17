from __future__ import annotations
from collections.abc import Callable
from logging import Logger
from re import Match, Pattern
from types import FunctionType, SimpleNamespace as Container
from typing_extensions import Any, Final, Literal, TypeAlias, TypeVar
from typing_extensions import Protocol

# START STUB ONLY

_LegacyKeyType: TypeAlias = tuple[str, ...]
_KeyCallableType: TypeAlias = Callable[
    [str], _NormKeyType | _LegacyKeyType | _SemanticKeyType
]
_NormVerVar0 = TypeVar("_NormVerVar0", bound=NormalizedVersion)
_NormVerVar1 = TypeVar("_NormVerVar1", bound=NormalizedVersion)
_NormKeyType: TypeAlias = tuple[int | str | tuple[()] | "_NormKeyType", ...]
_SemanticKeyType: TypeAlias = (
    tuple[tuple[int, int, int], tuple[str], tuple[str, str, str]]
    | tuple[tuple[int, int, int], tuple[str, str], tuple[str, str]]
    | tuple[tuple[int, int, int], tuple[str, str], tuple[str]]
    | tuple[tuple[int, int, int], tuple[str], tuple[str]]
)
# Using these to indicate that the input itself may be returned, rather than
# a different string.
_SuggestVar = TypeVar("_SuggestVar", bound=str)
class _SuggestProtocol(Protocol):
    def __call__(self, __Any: _SuggestVar) -> _SuggestVar | str | None:
        ...

# END STUB ONLY

__all__ = [
    "NormalizedVersion",
    "NormalizedMatcher",
    "LegacyVersion",
    "LegacyMatcher",
    "SemanticVersion",
    "SemanticMatcher",
    "UnsupportedVersionError",
    "get_scheme",
]

_NUMERIC_PREFIX: Final[Pattern[str]]
_REPLACEMENTS: Final[tuple[tuple[Pattern[str], str], ...]]
_SCHEMES: Final[dict[str, VersionScheme]]
_SEMVER_RE: Final[Pattern[str]]
_SUFFIX_REPLACEMENTS: Final[tuple[tuple[Pattern[str], str], ...]]
_VERSION_PART: Final[Pattern[str]]
_VERSION_REPLACE: Final[dict[str, str | None]]
logger: Logger
PEP440_VERSION_RE: Pattern[str]

def _legacy_key(s: str) -> _LegacyKeyType: ...
def _match_prefix(x: NormalizedVersion, y: str) -> bool: ...
def _pep_440_key(s: str) -> _NormKeyType: ...
_normalized_key = _pep_440_key

def _semantic_key(s: str) -> _SemanticKeyType: ...
def _suggest_normalized_version(s: _SuggestVar) -> _SuggestVar | str | None: ...
def _suggest_semantic_version(s: str) -> str | None: ...
def get_scheme(name: str) -> VersionScheme: ...  # documented
def is_semver(s: str) -> Match[str] | None: ...

class UnsupportedVersionError(ValueError): ...

class Version():  # documented
    _parts: Final[tuple[str | int, ...]]
    _string: Final[str]
    def __eq__(self, other: object) -> bool: ...
    def __ge__(self, other: object) -> bool: ...
    def __gt__(self, other: object) -> bool: ...
    def __hash__(self) -> int: ...
    def __init__(self, s: str) -> None: ...
    def __le__(self, other: object) -> bool: ...
    def __lt__(self, other: object) -> bool: ...
    def __ne__(self, other: object) -> bool: ...
    def _check_compatible(self, other: object) -> None: ...
    @property
    # @abstractmethod
    def is_prerelease(self) -> Any: ...
    # @abstractmethod
    def parse(self, s: Any) -> Any: ...  # Intentionally not implemented

class LegacyVersion(Version):
    @property
    def is_prerelease(self) -> bool: ...
    def parse(self, s: str) -> tuple[str, ...]: ...

class Matcher():  # documented
    _operators: dict[str, Callable[..., bool | FunctionType] | str]
    _parts: Final[tuple[str | int, ...]]
    _string: Final[str]
    key: str
    name: str
    # @abstractmethod?
    version_class: type[Version] | None
    def __eq__(self, other: object) -> bool: ...
    def __init__(self, s: str) -> None: ...
    def _check_compatible(self, other: object) -> None: ...
    @property
    def exact_version(self) -> NormalizedVersion | None: ...
    def match(self, version: str) -> bool: ...
    def parse_requirement(self, s: str) -> Container | None: ...

class LegacyMatcher(Matcher):
    _operators: dict[str, Callable[..., bool | FunctionType] | str]
    numeric_re: Pattern[str]
    version_class: type[LegacyVersion]
    def _match_compatible(
        self, version: NormalizedVersion, constraint: NormalizedVersion, prefix: bool
    ) -> bool: ...

# This entire class might be able to be made less verbose with a ParamSpec. Not sure.
class NormalizedMatcher(Matcher):  # documented
    _operators: dict[str, Callable[..., bool | FunctionType] | str]
    version_class: type[NormalizedVersion]
    def _adjust_local(
        self, version: _NormVerVar0, constraint: _NormVerVar1, prefix: bool
    ) -> tuple[NormalizedVersion | _NormVerVar0, _NormVerVar1]: ...
    def _match_arbitrary(
        self,
        version: NormalizedVersion,
        constraint: NormalizedVersion,
        prefix: Any,
    ) -> bool: ...
    def _match_compatible(
        self, version: NormalizedVersion, constraint: NormalizedVersion, prefix: bool
    ) -> bool: ...
    def _match_eq(
        self, version: NormalizedVersion, constraint: NormalizedVersion, prefix: bool
    ) -> bool: ...
    def _match_ge(
        self, version: NormalizedVersion, constraint: NormalizedVersion, prefix: bool
    ) -> bool: ...
    def _match_gt(
        self, version: NormalizedVersion, constraint: NormalizedVersion, prefix: bool
    ) -> bool: ...
    def _match_le(
        self, version: NormalizedVersion, constraint: NormalizedVersion, prefix: bool
    ) -> bool: ...
    def _match_lt(
        self, version: NormalizedVersion, constraint: NormalizedVersion, prefix: bool
    ) -> bool: ...
    def _match_ne(
        self, version: NormalizedVersion, constraint: NormalizedVersion, prefix: bool
    ) -> bool: ...

class NormalizedVersion(Version):  # documented
    _release_clause: Final[tuple[int, ...]]
    PREREL_TAGS: set[Literal["a", "b", "c", "rc", "dev"]]

    @property
    def is_prerelease(self) -> bool: ...
    def parse(self, s: str) -> _NormKeyType: ...

class SemanticVersion(Version):
    @property
    def is_prerelease(self) -> bool: ...
    def parse(self, s: str) -> _SemanticKeyType: ...

class SemanticMatcher(Matcher):
    version_class: type[SemanticVersion]

class VersionScheme():  # documented
    key: _KeyCallableType
    matcher: Matcher
    suggester: _SuggestProtocol
    def __init__(
        self,
        key: _KeyCallableType,
        matcher: Matcher,
        suggester: _SuggestProtocol | None = ...,
    ) -> None: ...
    def is_valid_constraint_list(self, s: str) -> bool: ...
    def is_valid_matcher(self, s: str) -> bool: ...
    def is_valid_version(self, s: str) -> bool: ...
    def suggest(self, s: _SuggestVar) -> _SuggestVar | str | None: ...
