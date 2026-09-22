from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "development" / "validation-performance.md"
CHANGELOG = ROOT / "CHANGELOG.md"


def test_issue104_runtime_performance_evidence_is_recorded() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = (
        "Teacher-runtime opened-Activity performance (issue #104)",
        "#93\nstorage / validation / CI optimization",
        "#104\nteacher-runtime opened-Activity projection optimization",
        "faster Activity projection != weaker canonical validation",
        "01dc76b4b0859b1cc78fa48840b0de9ed59a8b45",
        "88f03f52c3fb694ee570b9c926b942899046cb7d",
        "0.188104 s",
        "0.016246 s",
        "15 / 12 / 12",
        "1 / 1 / 1",
        "21 snapshots / 20 Artifacts",
        "scripts/benchmark_open_activity_performance_issue104.py",
        "no persistent canonical-state cache",
        "task-oriented-menu installed acceptance",
        "paper_data_suite.module_operations",
    )
    for phrase in required:
        assert phrase in text


def test_issue104_changelog_records_runtime_optimization() -> None:
    text = CHANGELOG.read_text(encoding="utf-8")
    assert "Issue #104 makes ordinary opened-Activity rendering reuse one exact" in text
    assert "0, 1, and 20 Artifacts" in text
    assert "registered Share retains" in text
