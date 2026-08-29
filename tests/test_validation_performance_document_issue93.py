from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "development" / "validation-performance.md"
INDEX = ROOT / "docs" / "README.md"


def test_validation_performance_document_records_issue93_contract() -> None:
    text = DOC.read_text(encoding="utf-8")

    required = (
        "faster validation != weaker validation",
        "487.916 s",
        "336.195 s",
        "322.901 s",
        "-33.8%",
        "197.694 s",
        "1,330",
        "PDS_CONCORD_TEST_WHEEL",
        "--reuse-static-caches",
        "PDS_CONCORD_VALIDATION_CACHE_ROOT",
        "55.1% faster",
        "42.7% faster",
        "49.1% faster",
        "Ubuntu / Python 3.11",
        "Windows / Python 3.14",
        "pytest-xdist",
        "post-pointer",
        "predecessor SHA-256",
        "scripts/benchmark_storage_performance_issue93.py",
    )
    for phrase in required:
        assert phrase in text


def test_validation_performance_document_is_indexed() -> None:
    text = INDEX.read_text(encoding="utf-8")

    assert (
        "[`development/validation-performance.md`]"
        "(development/validation-performance.md)"
        in text
    )
