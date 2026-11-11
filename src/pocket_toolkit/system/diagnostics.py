"""Модуль сбора диагностических метрик системы и процесса (System Diagnostic Collector).

Предоставляет функции collect_diagnostics, класс DiagnosticCollector и отчет DiagnosticReport
для сбора параметров окружения (ОС, архитектура, версия Python, время, память процесса)
исключительно средствами стандартной библиотеки без внешних зависимостей.
"""

import json
import os
import platform
import sys
import threading
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import TypeVar

T = TypeVar("T")

_PROCESS_START_TIME: float = time.monotonic()


@dataclass(frozen=True, slots=True)
class ProcessMetrics:
    """Метрики текущего процесса."""

    pid: int
    threads_count: int
    uptime_seconds: float
    memory_rss_bytes: int | None


@dataclass(frozen=True, slots=True)
class EnvironmentInfo:
    """Информация об операционной системе и среде Python."""

    os_name: str
    os_release: str
    os_version: str
    architecture: str
    cpu_count: int | None
    python_version: str
    python_implementation: str
    timestamp_utc: str


@dataclass(frozen=True, slots=True)
class DiagnosticReport:
    """Сводный диагностический отчет окружения и процесса."""

    environment: EnvironmentInfo
    process: ProcessMetrics

    def to_dict(self) -> dict[str, object]:
        """Преобразует отчет в словарь."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Сериализует отчет в JSON-строку."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


def _get_process_memory() -> int | None:
    """Определяет объем выделенной памяти процесса (RSS) кроссплатформенно."""
    # Попытка через resource (Linux/macOS)
    try:
        import resource
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # В Linux ru_maxrss измеряется в килобайтах, в macOS в байтах
        multiplier = 1 if sys.platform == "darwin" else 1024
        return int(usage.ru_maxrss * multiplier)
    except (ImportError, AttributeError, ValueError):
        pass

    # Попытка через ctypes на Windows (K32GetProcessMemoryInfo)
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes

            class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
                _fields_ = [
                    ("cb", wintypes.DWORD),
                    ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t),
                ]

            counters = PROCESS_MEMORY_COUNTERS()
            counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
            handle = ctypes.windll.kernel32.GetCurrentProcess()
            if ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
                return int(counters.WorkingSetSize)
        except (AttributeError, OSError, ValueError):
            return None

    return None


def collect_diagnostics() -> DiagnosticReport:
    """Собирает системные метрики и параметры текущего процесса.

    :return: Сводный объект DiagnosticReport.
    """
    now_utc = datetime.now(UTC).isoformat()
    uptime = max(0.0, time.monotonic() - _PROCESS_START_TIME)

    env_info = EnvironmentInfo(
        os_name=platform.system(),
        os_release=platform.release(),
        os_version=platform.version(),
        architecture=platform.machine(),
        cpu_count=os.cpu_count(),
        python_version=platform.python_version(),
        python_implementation=platform.python_implementation(),
        timestamp_utc=now_utc,
    )

    proc_info = ProcessMetrics(
        pid=os.getpid(),
        threads_count=threading.active_count(),
        uptime_seconds=uptime,
        memory_rss_bytes=_get_process_memory(),
    )

    return DiagnosticReport(environment=env_info, process=proc_info)


class DiagnosticCollector:
    """Удобный коллектор для снятия метрик и профилирования функций."""

    @staticmethod
    def collect() -> DiagnosticReport:
        """Снимает моментальный диагностический снимок."""
        return collect_diagnostics()

    @staticmethod
    def measure_time(func: Callable[[], T]) -> tuple[T, float]:
        """Измеряет время выполнения функции в секундах.

        :param func: Вызываемая функция без аргументов.
        :return: Кортеж (результат_функции, затраченное_время_в_секундах).
        """
        start = time.perf_counter()
        result = func()
        duration = time.perf_counter() - start
        return result, duration
