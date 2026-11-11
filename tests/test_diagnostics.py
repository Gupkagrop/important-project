"""Модульные тесты для модуля сбора системной диагностики (diagnostics)."""

import json

from pocket_toolkit.system.diagnostics import (
    DiagnosticCollector,
    DiagnosticReport,
    collect_diagnostics,
)


def test_collect_diagnostics_structure() -> None:
    """Проверка сбора метрик окружения и процесса."""
    report = collect_diagnostics()

    assert isinstance(report, DiagnosticReport)

    # Проверка параметров окружения
    env = report.environment
    assert env.os_name != ""
    assert env.python_version != ""
    assert env.architecture != ""
    assert "T" in env.timestamp_utc  # ISO формат времени

    # Проверка метрик процесса
    proc = report.process
    assert proc.pid > 0
    assert proc.threads_count >= 1
    assert proc.uptime_seconds >= 0.0


def test_diagnostic_report_serialization() -> None:
    """Проверка сериализации отчета в словарь и JSON."""
    report = collect_diagnostics()

    data_dict = report.to_dict()
    assert "environment" in data_dict
    assert "process" in data_dict
    assert data_dict["process"]["pid"] == report.process.pid

    json_str = report.to_json()
    parsed = json.loads(json_str)
    assert parsed["environment"]["python_version"] == report.environment.python_version


def test_diagnostic_collector_measure_time() -> None:
    """Проверка измерения времени выполнения функции."""
    def sample_task() -> int:
        total = 0
        for i in range(1000):
            total += i
        return total

    result, duration = DiagnosticCollector.measure_time(sample_task)
    assert result == 499500
    assert duration >= 0.0
