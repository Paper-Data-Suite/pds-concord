from __future__ import annotations

from pathlib import Path

from scripts import benchmark_storage_performance_issue93 as benchmark


def test_storage_benchmark_formats_improvement_without_thresholds() -> None:
    assert benchmark._format_change(2.0, 1.0) == "50.0% faster"
    assert benchmark._format_change(0.0, 1.0) == "n/a"


def test_storage_benchmark_source_keeps_comparisons_diagnostic_only() -> None:
    source = Path(benchmark.__file__).read_text(encoding="utf-8")

    assert "time.perf_counter()" in source
    assert "statistics.median" in source
    assert "_legacy_list_work_snapshots" in source
    assert "_legacy_load_current_record_graph" in source
    assert "_legacy_record_history_pass" in source
    assert "pytest" not in source
    assert "pass/fail" not in source.casefold()
