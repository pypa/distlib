from __future__ import annotations
from _csv import _reader as _csv_reader, _writer as _csv_writer
from .database import InstalledDistribution
from .index import PackageIndex
from .metadata import Metadata
from .resources import Resource, ResourceContainer
from .wheel import Wheel
from codecs import StreamReader, StreamWriter
from collections import deque
from collections.abc import (
    Callable,
    Collection,
    Iterable,
    Iterator,
    Mapping,
    Sequence,
)
from io import (
    BufferedReader,
    BufferedWriter,
    BytesIO,
    IOBase,
    TextIOBase,
    TextIOWrapper,
)
from logging import Logger
from logging.config import (  # type: ignore[attr-defined]
    BaseConfigurator,
    ConvertingDict,
    ConvertingList,
)
from re import Pattern
from socket import socket
from ssl import SSLContext
from subprocess import Popen
from types import ModuleType, TracebackType
from types import SimpleNamespace as Container
from typing import IO
from typing_extensions import (
    Any,
    Final,
    Literal,
    NoReturn,
    overload,
    Self,
    TypeAlias,
    TypedDict,
    TypeVar,
    Unpack,
)
from urllib.request import (
    HTTPHandler,
    Request,
    HTTPSHandler as BaseHTTPSHandler,
)
from xmlrpc.client import (
    SafeTransport as BaseSafeTransport,
    ServerProxy as BaseServerProxy,
    Transport as BaseTransport,
)
from zipfile import ZipExtFile
import contextlib
import http.client as httplib
import sys

# START STUB ONLY

class _defaults_td(TypedDict, total=False):
    delimiter: Literal[","]
    quotechar: Literal['"']
    lineterminator: Literal["\n"]

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
_T0: TypeAlias = str | int | None
_RecursiveDictInt: TypeAlias = dict[str, _T0
    | list[_T0 | list[_T0 | "_RecursiveDictInt"]
         | dict[str, _T0 | list[_T0 | "_RecursiveDictInt"] | "_RecursiveDictInt"]
      ]
    | dict[str, _T0
         | list[_T0 | list[_T0 | "_RecursiveDictInt"]
              | dict[str, _T0 | list[_T0 | "_RecursiveDictInt"] | "_RecursiveDictInt"]
           ],
      ],
]
# fmt: on
_ReversedVar = TypeVar("_ReversedVar", bound=str)
# Adapted from:
# https://github.com/python/typeshed/blob/main/stdlib/subprocess.pyi
if sys.platform == "win32":
    _ENV: TypeAlias = Mapping[str, str]
else:
    _ENV: TypeAlias = Mapping[bytes, str | bytes] | Mapping[str, str | bytes]

# Not all of these keywords exist on all Python versions.
# The only way I would know to annotate this is with many
# TypedDicts, which (at this length) seems overly verbose.
class _Popen_td(TypedDict, total=False):
    # args is already in params, re-named cmd
    # args: str | bytes | Sequence[str | bytes]
    bufsize: int
    executable: str | bytes | None
    stdin: int | IO[Any] | None
    # stdout: int | IO[Any] | None;  already in params
    # stderr: int | IO[Any] | None; already in params
    preexec_fn: Callable[[], Any] | None
    close_fds: bool
    shell: bool
    cwd: str | bytes | None
    env: _ENV | None
    universal_newlines: bool | None
    startupinfo: Any | None
    creationflags: int
    restore_signals: bool
    start_new_session: bool
    pass_fds: Collection[int]
    # * end of positionals
    user: str | int | None
    group: str | int | None
    extra_groups: Iterable[str | int] | None  # >=3.9
    encoding: str | None
    errors: str | None
    text: bool | None
    umask: int
    pipesize: int  # >=3.10
    process_group: int | None  # >=3.11

# Adapted from:
# https://github.com/python/typeshed/blob/main/stdlib/builtins.pyi
class _Open_td(TypedDict, total=False):
    # file: int | str | bytes; re-named again as fn, already in params
    # mode: str; already in params
    buffering: int
    encoding: str | None
    errors: str | None
    newline: str | None
    closefd: bool
    opener: Callable[[str, int], int] | None

class _CSVReader_td(TypedDict, total=False):
    # Technically accepts all of open()'s keywords, but only these two
    # are passed on.
    # 'file' re-named again from fn to path.
    path: int | str | bytes
    stream: str

# Adapted from:
# https://github.com/python/typeshed/blob/main/stdlib/http/client.pyi
# change to total=False when/if overloads for _conn_maker are removed
class _HTTPSConnection_td(TypedDict, total=True):
    host: str
    port: int | None
    key_file: str | None
    cert_file: str | None
    timeout: float | None
    source_address: tuple[str, int] | None
    # *  end of positional
    context: SSLContext | None
    check_hostname: bool | None
    blocksize: int

class _HTTPSConnection_kwd_td(TypedDict, total=False):
    context: SSLContext | None
    check_hostname: bool | None
    blocksize: int

# Adapted from:
# https://github.com/python/typeshed/blob/main/stdlib/xmlrpc/client.pyi
class _ServerProxy_td(TypedDict, total=False):
    # uri: str; already in params
    transport: SafeTransport | Transport | None
    encoding: str | None
    verbose: bool
    allow_none: bool
    use_datetime: bool
    use_builtin_types: bool
    # *  end of positional
    headers: Iterable[tuple[str, str]] # >=3.8
    context: Any | None

# END STUB ONLY

_CHECK_MISMATCH_SET: Final[Pattern[str]]
_CHECK_RECURSIVE_GLOB: Final[Pattern[str]]
_external_data_base_url: Final[str]
_TARGET_TO_PLAT: Final[dict[str, str]]
AND: Pattern[str]
# fmt: off
ARCHIVE_EXTENSIONS: tuple[
    Literal[".tar.gz"], Literal[".tar.bz2"], Literal[".tar"], Literal[".zip"],
    Literal[".tgz"], Literal[".tbz"], Literal[".whl"],
]
# fmt: on
COMPARE_OP: Pattern[str]
ENTRY_RE: Pattern[str]
IDENTIFIER: Pattern[str]
logger: Logger
MARKER_OP: Pattern[str]
NAME_VERSION_RE: Pattern[str]
NON_SPACE: Pattern[str]
OR: Pattern[str]
PROJECT_NAME_AND_VERSION: Pattern[str]
PYTHON_VERSION: Pattern[str]
RICH_GLOB: Pattern[str]
ssl: ModuleType | None
STRING_CHUNK: Pattern[str]
UNITS: tuple[(
    Literal[""], Literal["K"], Literal["M"],
    Literal["G"], Literal["T"], Literal["P"],
)]
VERSION_IDENTIFIER: Pattern[str]

def _csv_open(fn: str, mode: str, **kwargs: Unpack[_Open_td]) -> TextIOWrapper: ...
def _get_external_data(url: str) -> dict[str, str | list[Any] | dict[str, Any]]: ...
def _iglob(path_glob: str) -> Iterator[str]: ...
def _load_pypirc(index: PackageIndex) -> dict[str, str]: ...
def _store_pypirc(index: PackageIndex) -> None: ...
@contextlib.contextmanager
def chdir(d: str | bytes) -> Iterator[None]: ...
def convert_path(pathname: str) -> str: ...
def ensure_slash(s: str) -> str: ...
def extract_by_key(
    d: _RecursiveDict,
    keys: str,
) -> dict[str, str | list[str | dict[str, str | list[str]]]]: ...
def get_cache_base(suffix: str | None = ...) -> str: ...  # documented
def get_executable() -> str: ...
def get_export_entry(specification: str) -> ExportEntry | None: ...  # documented
def get_extras(
    requested: str | list[str] | set[str], available: str | list[str] | set[str]
) -> set[str]: ...
def get_host_platform() -> str: ...
def get_package_data(name: str, version: str) -> _RecursiveDictInt: ...
def get_platform() -> str: ...
def get_process_umask() -> int: ...
def get_project_data(
    name: str,
) -> _RecursiveDictInt: ...
def get_resources_dests(
    resources_root: str, rules: list[tuple[str, str, str] | tuple[str, str, None]]
) -> dict[str, str]: ...
def iglob(path_glob: str) -> Iterator[str]: ...
def in_venv() -> bool: ...
def is_string_sequence(seq: Any) -> bool: ...
def normalize_name(name: str) -> str: ...
def parse_credentials(netloc: str) -> tuple[str | None, str | None, str]: ...
def parse_marker(
    marker_string: str,
) -> tuple[str, str | dict[str, str | dict[str, str | dict[str, str]]]]: ...
def parse_name_and_version(p: str) -> tuple[str, str]: ...
def parse_requirement(req: str) -> Container | None: ...
def path_to_cache_dir(path: str) -> str: ...  # documented
# proceed(...) is dead code?
def proceed(
    prompt: str,
    allowed_chars: str,
    error_prompt: str | None = ...,
    default: str | None = ...,
) -> str: ...
def read_exports(
    stream: BufferedReader | StreamReader | BytesIO,
) -> dict[str, dict[str, ExportEntry]]: ...
def resolve(module_name: str, dotted_path: str | None) -> ModuleType: ...  # documented
@contextlib.contextmanager
def socket_timeout(timeout: int = ...) -> Iterator[None]: ...
def split_filename(
    filename: str, project_name: str | None = ...
) -> tuple[str, str, str | None] | None: ...
@contextlib.contextmanager
def tempdir() -> Iterator[str]: ...
def unarchive(
    archive_filename: str | bytes,
    dest_dir: str | bytes,
    format: str | None = ...,
    check: bool = ...,
) -> None: ...
def write_exports(
    exports: dict[str, dict[str, ExportEntry]], stream: BufferedWriter | StreamWriter
) -> None: ...
def zip_dir(directory: str | bytes) -> BytesIO: ...

class CSVBase():
    defaults: _defaults_td
    def __enter__(self) -> Self: ...
    @overload
    def __exit__(self, *exc_info: tuple[None, None, None]) -> None: ...
    @overload
    def __exit__(
        self, *exc_info: tuple[type[BaseException], BaseException, TracebackType]
    ) -> None: ...

class CSVReader(CSVBase):
    reader: _csv_reader
    stream: StreamReader | TextIOBase
    def __init__(self, **kwargs: Unpack[_CSVReader_td]) -> None: ...
    def __iter__(self) -> Self: ...
    def next(self) -> list[str]: ...
    __next__ = next

class CSVWriter(CSVBase):
    stream: TextIOBase
    writer: _csv_writer
    # kwargs is dead code?
    def __init__(self, fn: str, **kwargs: Any) -> None: ...
    def writerow(self, row: tuple[str, str, str | int]) -> None: ...

class Cache():  # documented
    base: str | bytes
    def __init__(self, base: str | bytes) -> None: ...
    def clear(self) -> list[str]: ...
    def prefix_to_dir(self, prefix: str) -> str: ...

# Typeshed is missing stubs for BaseConfigurator
class Configurator(BaseConfigurator):  # type: ignore[misc]
    base: str
    value_converters: dict[str, str]
    def __getitem__(
        self, key: str
    ) -> (
        ConvertingDict
        | ConvertingList
        | TextIOWrapper
        | dict[str, str]
        | float
        | int
        | str
    ): ...
    def __init__(
        self, config: ConvertingDict | dict[str, Any], base: str | None = ...
    ) -> None: ...
    def configure_custom(
        self,
        config: ConvertingDict | dict[str, Any],
    ) -> Container: ...
    def inc_convert(self, value: str | bytes) -> dict[str, str]: ...

class EventMixin():
    # Callables, *args, **kwargs, and the subscriber parameters were inferred
    # to be Any (from the "test_events" test in test_util); they are mostly
    # undocumented and appear to allow arbitrary arguments.
    _subscribers: Final[dict[str, deque[Callable[..., Any]]]]
    def __init__(self) -> None: ...
    def add(
        self, event: str, subscriber: Callable[..., Any], append: bool = ...
    ) -> None: ...
    def get_subscribers(self, event: str) -> Iterator[deque[Callable[..., Any]]]: ...
    def publish(
        self, event: str, *args: Any, **kwargs: Any
    ) -> list[tuple[tuple[int, int], dict[str, str]] | None]: ...
    def remove(self, event: str, subscriber: Callable[..., Any]) -> None: ...

class cached_property():
    func: Callable[..., Any]

    @overload
    def __get__(
        self,
        obj: None,
        cls: type[InstalledDistribution]
        | type[Resource]
        | type[ResourceContainer]
        | type[Wheel]
        | type[ExportEntry]
        | None = ...,
    ) -> Self: ...
    @overload
    def __get__(
        self,
        obj: Wheel | ExportEntry | ResourceContainer | Resource | InstalledDistribution,
        cls: type[InstalledDistribution]
        | type[Resource]
        | type[ResourceContainer]
        | type[Wheel]
        | type[ExportEntry]
        | None = ...,
    ) -> (
        int
        | bytes
        | str
        | set[str]
        | dict[str, str | dict[str, ExportEntry]]
        | Callable[..., Any]
        | Metadata
    ): ...
    def __init__(self, func: Callable[..., Any]) -> None: ...

# ExportEntry is documented as having non-existent attribute 'dist'
class ExportEntry():
    flags: str | list[str] | None  # documented
    name: str  # documented
    prefix: str  # documented
    suffix: str | None  # documented
    def __eq__(self, other: ExportEntry | object) -> bool: ...
    def __init__(
        self, name: str, prefix: str, suffix: str | None, flags: str | list[str] | None
    ) -> None: ...
    @cached_property
    def value(self, prefix: str, suffix: str | None) -> ModuleType: ...  # documented

class FileOperator():
    dirs_created: set[str | None]
    dry_run: bool
    ensured: set[str | None]
    files_written: set[str | None]
    record: bool
    def __init__(self, dry_run: bool = ...) -> None: ...
    def _init_record(self) -> None: ...
    def byte_compile(
        self,
        path: str,
        optimize: bool = ...,
        force: bool = ...,
        prefix: str | tuple[str, ...] | None = ...,
        hashed_invalidation: bool = ...,
    ) -> str: ...
    def commit(self) -> tuple[set[str], set[str]]: ...
    def copy_file(
        self,
        infile: str,
        outfile: str | bytes,
        check: bool = ...,
    ) -> None: ...
    def copy_stream(
        self,
        instream: ZipExtFile,
        outfile: str | bytes,
        encoding: str | None = ...,
    ) -> None: ...
    def ensure_dir(self, path: str | bytes) -> None: ...
    def ensure_removed(self, path: str | bytes) -> None: ...
    def is_writable(self, path: str | bytes) -> bool: ...
    def newer(
        self,
        source: str | bytes,
        target: str | bytes,
    ) -> bool: ...
    def record_as_written(self, path: str) -> None: ...
    def rollback(self) -> None: ...
    def set_executable_mode(s: Self, f: str | list[str]) -> None: ...  # from a lambda
    def set_mode(self, bits: int, mask: int, files: str | list[str] | None) -> None: ...
    def write_binary_file(self, path: str, data: bytes) -> None: ...
    def write_text_file(self, path: str, data: str, encoding: str) -> None: ...

class HTTPSConnection(httplib.HTTPSConnection):
    ca_certs: str | None
    check_domain: bool
    sock: socket
    def connect(self) -> None: ...

class HTTPSHandler(BaseHTTPSHandler):  # documented
    ca_certs: str
    check_domain: bool
    def __init__(self, ca_certs: str, check_domain: bool = ...) -> None: ...
    # I am unaware of a way to Unpack *args and **kwargs s.t. mypy does not complain
    # about incorrect argument count. Hopefully this sickening series of overloads
    # can be removed.
    @overload
    def _conn_maker(self, **kwargs: Unpack[_HTTPSConnection_td]) -> HTTPSConnection: ...
    @overload
    def _conn_maker(
        self, host: str,
        **kwargs: Unpack[_HTTPSConnection_kwd_td]
    ) -> HTTPSConnection: ...
    @overload
    def _conn_maker(
        self, host: str, port: int | None, **kwargs: Unpack[_HTTPSConnection_kwd_td]
    ) -> HTTPSConnection: ...
    @overload
    def _conn_maker(
        self, host: str, port: int | None, key_file: str | None,
        **kwargs: Unpack[_HTTPSConnection_kwd_td]
    ) -> HTTPSConnection: ...
    @overload
    def _conn_maker(
        self, host: str, port: int | None, key_file: str | None, cert_file: str | None,
        **kwargs: Unpack[_HTTPSConnection_kwd_td]
    ) -> HTTPSConnection: ...
    @overload
    def _conn_maker(
        self, host: str, port: int | None, key_file: str | None, cert_file: str | None,
        timeout: float | None, **kwargs: Unpack[_HTTPSConnection_kwd_td]
    ) -> HTTPSConnection: ...
    @overload
    def _conn_maker(
        self, host: str, port: int | None, key_file: str | None, cert_file: str | None,
        timeout: float | None, source_address: tuple[str, int] | None,
        **kwargs: Unpack[_HTTPSConnection_kwd_td]
    ) -> HTTPSConnection: ...
    def https_open(self, req: Request) -> httplib.HTTPResponse: ...

class HTTPSOnlyHandler(HTTPSHandler, HTTPHandler):  # documented
    ca_certs: str
    check_domain: bool
    def http_open(self, req: Request | str) -> NoReturn: ...

class Progress():
    cur: int | None
    done: bool
    # elapsed is only annotated with int because it defaults to 0.
    # Its default should probably be '0.0' since time.now()
    # returns a float.
    elapsed: int | float
    max: int | None
    min: int
    started: float | None
    unknown: str
    def __init__(self, minval: int = ..., maxval: int | None = ...) -> None: ...
    @property
    def ETA(self) -> str: ...
    def format_duration(self, duration: int | float | None) -> str: ...
    def increment(self, incr: int) -> None: ...
    @property
    def maximum(self) -> str | int: ...
    @property
    def percentage(self) -> str: ...
    @property
    def speed(self) -> str: ...
    def start(self) -> Self: ...
    def stop(self) -> None: ...
    def update(self, curval: int) -> None: ...

class PyPIRCFile():
    DEFAULT_REALM: str
    DEFAULT_REPOSITORY: str
    filename: str
    url: str | None
    def __init__(self, fn: str | None = ..., url: str | None = ...) -> None: ...
    def read(self) -> dict[str, str]: ...
    def update(self, username: str, password: str) -> None: ...

class SafeTransport(BaseSafeTransport):
    _connection: tuple[str, httplib.HTTPSConnection]
    _extra_headers: list[tuple[str, str]]
    timeout: float
    def __init__(self, timeout: float, use_datetime: int = ...) -> None: ...
    def make_connection(
        self, host: str | tuple[str, dict[str, str]]
    ) -> httplib.HTTPSConnection: ...

class Sequencer():
    _nodes: Final[set[str]]
    _preds: Final[dict[str, set[str]]]
    _succs: Final[dict[str, set[str]]]
    def __init__(self) -> None: ...
    def add(self, pred: str, succ: str) -> None: ...
    def add_node(self, node: str) -> None: ...
    @property
    def dot(self) -> str: ...
    def get_steps(self, final: _ReversedVar) -> Iterator[list[_ReversedVar]]: ...
    def is_step(self, step: str) -> bool: ...
    def remove(self, pred: str, succ: str) -> None: ...
    def remove_node(self, node: str, edges: bool = ...) -> None: ...
    @property
    def strong_connections(self) -> list[tuple[str]]: ...

class SubprocessMixin():
    # As it is not documented anywhere, I inferred the type of progress's args
    # from run_commmand calling it with two strings; the return type is assumed
    # to be None since its result is not used.
    # reader's parameter 'context' inferred from the above as it is used as
    # an argument to progress().
    progress: Callable[[str, str], None]
    verbose: bool
    def __init__(
        self,
        verbose: bool = ...,
        progress: Callable[[str, str], None] | None = ...,
    ) -> None: ...
    def reader(self, stream: IOBase, context: str) -> None: ...
    def run_command(
        self, cmd: str | bytes | Sequence[str | bytes], **kwargs: Unpack[_Popen_td]
    ) -> Popen[str]: ...

class ServerProxy(BaseServerProxy):
    timeout: float | None
    transport: SafeTransport | Transport = ...
    def __init__(self, uri: str, **kwargs: Unpack[_ServerProxy_td]) -> None: ...

class Transport(BaseTransport):
    _connection: tuple[str, httplib.HTTPConnection]
    _extra_headers: list[tuple[str, str]]
    timeout: float
    def __init__(self, timeout: float, use_datetime: int = ...) -> None: ...
    def make_connection(
        self, host: str | tuple[str, dict[str, str]]
    ) -> httplib.HTTPConnection: ...
