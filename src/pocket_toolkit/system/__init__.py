"""Пакет системных утилит и файловых операций Pocket Toolkit."""

from pocket_toolkit.system.atomic import (
    AtomicFileWriter,
    atomic_open,
    atomic_write,
)
from pocket_toolkit.system.buffer import (
    BufferOverflowError,
    MemoryFileBuffer,
)
from pocket_toolkit.system.diagnostics import (
    DiagnosticCollector,
    DiagnosticReport,
    EnvironmentInfo,
    ProcessMetrics,
    collect_diagnostics,
)
from pocket_toolkit.system.env import (
    EnvConfig,
    EnvParseError,
    load_env,
    parse_env,
)
from pocket_toolkit.system.event_bus import (
    EventBus,
    EventHandler,
)
from pocket_toolkit.system.glob_matcher import (
    GlobPattern,
    glob_filter,
    glob_match,
    glob_to_regex,
)
from pocket_toolkit.system.logger import (
    LogLevel,
    StructuredLogger,
)
from pocket_toolkit.system.temp import (
    TempWorkspace,
    temp_dir,
    temp_file,
)

__all__: list[str] = [
    "AtomicFileWriter",
    "BufferOverflowError",
    "DiagnosticCollector",
    "DiagnosticReport",
    "EnvConfig",
    "EnvParseError",
    "EnvironmentInfo",
    "EventBus",
    "EventHandler",
    "GlobPattern",
    "LogLevel",
    "MemoryFileBuffer",
    "ProcessMetrics",
    "StructuredLogger",
    "TempWorkspace",
    "atomic_open",
    "atomic_write",
    "collect_diagnostics",
    "glob_filter",
    "glob_match",
    "glob_to_regex",
    "load_env",
    "parse_env",
    "temp_dir",
    "temp_file",
]
