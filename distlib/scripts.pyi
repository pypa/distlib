from __future__ import annotations
from .util import ExportEntry, FileOperator
from collections.abc import Iterable
from logging import Logger
from re import Pattern
from sys import _version_info
from typing_extensions import (
    Final,
    Literal,
    TypeAlias,
    TypedDict,
)
import sys

# START STUB ONLY

if sys.platform == "win32":
    __is_nt: TypeAlias = Literal[True]
else:
    __is_nt: TypeAlias = Literal[False]

class _script_td(TypedDict, total=False):
    gui: bool
    interpreter_args: list[str]

# END STUB ONLY

_DEFAULT_MANIFEST: Final[str]
FIRST_LINE_RE: Pattern[bytes]
logger: Logger
SCRIPT_TEMPLATE: str

def enquote_executable(executable: str) -> str: ...  # documented

_enquote_executable = enquote_executable

# source_dir and target_dir parameters to __init__ may be None
# when called from distlib.wheel Wheel.install(), but this is
# documented only in distlib.wheel, not in distlib.scripts.
# The attributes of the same name should never be None.
class ScriptMaker():  # documented
    _fileop: Final[FileOperator]
    _is_nt: Final[__is_nt]
    add_launchers: bool  # documented
    clobber: bool  # documented
    executable: str | None  # documented
    force: bool  # documented
    manifest: str
    script_template: str  # documented
    set_mode: bool  # documented
    source_dir: str  # documented
    target_dir: str # documented
    variant_separator: str  # documented
    variants: set[str]
    version_info: _version_info  # documented
    if sys.platform.startswith("java"):
        def _fix_jython_executable(self, executable: str | None) -> str | None: ...
        def _is_shell(self, executable: str) -> bool: ...
    if sys.platform == "win32":
        def _get_launcher(self, kind: str) -> str: ...
    def __init__(  # documented
        self,
        source_dir: str | None,
        target_dir: str | None,
        add_launchers: bool = ...,
        dry_run: bool = ...,
        fileop: None = ...,
    ) -> None: ...
    def _build_shebang(self, executable: bytes, post_interp: bytes) -> bytes: ...
    def _copy_script(self, script: str, filenames: list[str]) -> None: ...
    def _get_alternate_executable(
        self, executable: str, options: _script_td
    ) -> str: ...
    def _get_script_text(self, entry: ExportEntry) -> str: ...
    def _get_shebang(
        self,
        encoding: str,
        post_interp: bytes = ...,
        options: _script_td | None = ...,
    ) -> bytes: ...
    def _make_script(
        self,
        entry: ExportEntry,
        filenames: list[str],
        options: _script_td | None = ...,
    ) -> None: ...
    def _write_script(
        self,
        names: list[str] | set[str],
        shebang: bytes,
        script_bytes: bytes,
        filenames: list[str],
        ext: str,
    ) -> None: ...
    @property
    def dry_run(self) -> bool: ...
    @dry_run.setter
    def dry_run(self, value: bool) -> bool: ...
    def get_manifest(self, exename: str) -> str: ...
    def get_script_filenames(self, name: str) -> set[str]: ...  # documented
    def make(  # documented
        self,
        specification: str,
        options: _script_td | None = ...,
    ) -> list[str]: ...
    # make_multiple is incorrectly documented in source, correctly in docs.
    # docs specifies taking any Iterable, source says a list.
    def make_multiple(
        self,
        specifications: Iterable[str],
        options: _script_td | None = ...,
    ) -> list[str]: ...
