from __future__ import annotations
from logging import Logger
from re import Pattern
from typing_extensions import Final

__all__ = ["Manifest"]

_COLLAPSE_PATTERN: Final[Pattern[str]]
_COMMENTED_LINE: Final[Pattern[str]]
_PYTHON_VERSION: Final[tuple[int, int]]
logger: Logger

class Manifest():  # documented
    allfiles: list[str] | None  # documented
    base: str  # documented
    files: set[str]  # documented
    prefix: str
    def __init__(self, base: str | None = ...) -> None: ...
    def _exclude_pattern(
        self,
        pattern: Pattern[str] | str | None,
        anchor: bool = ...,
        prefix: str | None = ...,
        is_regex: bool = ...,
    ) -> bool: ...
    def _glob_to_re(self, pattern: str) -> str: ...
    def _include_pattern(
        self,
        pattern: str | None,
        anchor: bool = ...,
        prefix: str | None = ...,
        is_regex: bool = ...,
    ) -> bool: ...
    def _parse_directive(
        self, directive: str
    ) -> tuple[str, list[str] | None, str | None, list[str] | None]: ...
    def _translate_pattern(
        self,
        pattern: Pattern[str] | str | None,
        anchor: bool = ...,
        prefix: str | None = ...,
        is_regex: bool = ...,
    ) -> Pattern[str]: ...
    def add(self, item: str) -> None: ...
    def add_many(self, items: list[str]) -> None: ...
    def clear(self) -> None: ...
    def findall(self) -> None: ...
    def process_directive(self, directive: str) -> None: ...  # documented
    def sorted(self, wantdirs: bool = ...) -> list[str]: ...
