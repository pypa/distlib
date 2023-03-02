from __future__ import annotations
from .version import NormalizedVersion
from collections.abc import Callable
from re import Pattern
from typing_extensions import Final, NotRequired, Self, TypedDict

# START STUB ONLY

class _Context_td(TypedDict):
    extra: NotRequired[str | None] 
    implementation_name: str
    implementation_version: str
    os_name: str
    platform_in_venv: str
    platform_machine: str
    platform_python_implementation: str
    platform_release: str | None
    platform_system: str
    platform_version: str | None
    python_full_version: str | None
    python_version: str | None
    sys_platform: str

# END STUB ONLY

__all__ = ["interpret"]

_DIGITS: Final[Pattern[str]]
_VERSION_MARKERS: Final[set[str]]
_VERSION_PATTERN: Final[Pattern[str]]
DEFAULT_CONTEXT: _Context_td
evaluator: Evaluator

def _get_versions(s: str) -> set[NormalizedVersion]: ...
def _is_literal(o: str | dict[str, str | dict[str, str]]) -> bool: ...
def _is_version_marker(s: str | dict[str, str | dict[str, str]]) -> bool: ...

# def default_context() -> dict[str, str]: ... deleted, stored to DEFAULT_CONTEXT
def interpret(  # documented
    marker: str, execution_context: dict[str, str] | None = ...
) -> bool: ...

class Evaluator():
    operations: dict[str, Callable[[Self, Self], bool]]
    def evaluate(
        self,
        expr: str | dict[str, str | dict[str, str | dict[str, str]]],
        context: _Context_td,
    ) -> str | bool: ...
