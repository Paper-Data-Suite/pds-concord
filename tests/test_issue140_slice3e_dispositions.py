"""#140 Slice 3E: exact classification ledger and evidence-reference regression."""

from __future__ import annotations

import csv
import importlib.util
import io
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/issue140_slice3e_dispositions.py"


def _module() -> Any:
    spec = importlib.util.spec_from_file_location(
        "issue140_slice3e_dispositions", SCRIPT
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_exact_18_scoped_source_families_have_evidence_or_explicit_open_gate() -> None:
    audit = _module()
    candidate = (ROOT / audit.SOURCE).read_text(encoding="utf-8")
    originals = audit.read_candidates(candidate)
    generated = audit.build(ROOT)
    records = list(csv.DictReader(io.StringIO(generated.decode("utf-8"))))
    assert len(originals) == len(records) == 18
    assert (ROOT / audit.OUTPUT).read_bytes() == generated
    assert [row["service_name"] for row in originals] == [
        row["service_name"] for row in records
    ]
    assert sum(item["slice3e_evidence_status"] == audit.GUARD for item in records) == 13
    assert sum(item["slice3e_evidence_status"] == audit.LABEL for item in records) == 2
    assert (
        sum(item["slice3e_evidence_status"] == audit.UNTESTED for item in records) == 3
    )
    assert all(item["slice3a_source_status"] == audit.UNTESTED for item in records)
    assert all(item["finding_scope"] and item["owner"] for item in records)
    assert all(
        item["evidence_test"]
        for item in records
        if item["slice3e_evidence_status"] != audit.UNTESTED
    )


def test_unreturned_score_and_review_do_not_claim_success_or_a_fixed_regression() -> (
    None
):
    audit = _module()
    assert audit.CLAIMS["record_prepared_routine_score"].status == audit.UNTESTED
    assert audit.CLAIMS["record_routine_artifact_review"].status == audit.UNTESTED
    assert audit.CLAIMS["show_criterion_set"].status == audit.UNTESTED
    assert (
        "planned Artifact refused"
        in audit.CLAIMS["record_prepared_routine_score"].scope
    )
    assert audit.CLAIMS["record_prepared_routine_score"].disposition == "HUMAN_GATE"


def test_candidate_matrix_rejects_an_unknown_or_duplicate_family() -> None:
    audit = _module()
    source = (ROOT / audit.SOURCE).read_text(encoding="utf-8")
    rows = audit.read_candidates(source)
    unknown = [dict(row) for row in rows]
    unknown[0]["service_name"] = "invented_service"
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=audit.SOURCE_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(unknown)
    with pytest.raises(audit.AuditError, match="Candidate coverage drift"):
        audit.read_candidates(stream.getvalue())
    duplicate = [dict(row) for row in rows]
    duplicate[0]["service_name"] = duplicate[1]["service_name"]
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=audit.SOURCE_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(duplicate)
    with pytest.raises(audit.AuditError, match="18 distinct"):
        audit.read_candidates(stream.getvalue())


def test_reference_check_rejects_nonexistent_pytest_function() -> None:
    audit = _module()
    claim = audit.Claim(
        audit.GUARD,
        "tests/test_issue140_slice3b_menu_guard.py::test_not_in_repository",
        "author",
        "not real",
        "FIX_142",
        "#142",
    )
    with pytest.raises(
        audit.AuditError, match="Referenced witness function is missing"
    ):
        audit._check_test_reference(ROOT, claim)
