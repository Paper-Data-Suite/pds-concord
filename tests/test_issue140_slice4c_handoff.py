"""#140 Slice 4C: handoff crosswalk, evidence boundaries and create-only output."""

from __future__ import annotations

import csv
import importlib.util
import io
import json
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/issue140_slice4c_handoff.py"


def _module() -> Any:
    spec = importlib.util.spec_from_file_location("issue140_slice4c_handoff", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    path.write_text(stream.getvalue(), encoding="utf-8")


def _fixture(root: Path, audit: Any) -> Path:
    base = root / audit.BASE
    base.mkdir(parents=True)
    baseline = {
        "git": {
            "head": audit.RELEASE_COMMIT,
            "tag_peeled_commit": audit.RELEASE_COMMIT,
            "tag": "v0.3.4",
            "origin_repository": "Paper-Data-Suite/pds-concord",
        },
        "source": {
            "version": "0.3.4",
            "dependencies": ["pds-core>=0.6.6,<0.7"],
        },
        "published_artifacts": {
            "core_v0_6_6_wheel": {
                "status": "verified_published_bytes_and_metadata",
                "sha256": "a" * 64,
            },
            "concord_v0_3_4_wheel": {"status": "not_provided"},
        },
        "environment": {
            "installed_distributions": {
                "concord": {"version": "0.3.2", "editable": True},
                "core": {"version": "0.6.6"},
            },
            "system": "Windows",
            "machine_architecture": "AMD64",
            "python": "3.11.9",
        },
    }
    (base / "baseline.json").write_text(json.dumps(baseline), encoding="utf-8")
    source_a = "concord/menu_artifact.py"
    source_b = "concord/cli.py"
    summary = {
        "schema": "concord_issue140_slice1_census_v1",
        "source_surfaces": [source_a, source_b],
        "matrix_row_count": 4,
        "all_calls": 6,
    }
    (base / "surface_inventory.json").write_text(json.dumps(summary), encoding="utf-8")
    matrix = [
        {"operation_id": f"operation_{i}", "source_file": source_a} for i in range(3)
    ] + [{"operation_id": "operation_3", "source_file": source_b}]
    _write_csv(base / "teacher_operation_matrix.csv", matrix)
    statuses = [audit.GUARD] * 13 + [audit.DEGRADED] * 2 + [audit.UNTESTED] * 3
    ledger = [
        {
            "source_file": source_a,
            "service_name": f"service_{index}",
            "slice3e_evidence_status": status,
            "finding_scope": "Context first" if status == audit.GUARD else "Pending",
            "evidence_test": "test_synthetic" if status != audit.UNTESTED else "",
            "evidence_case": "synthetic" if status != audit.UNTESTED else "",
            "disposition": ("INVESTIGATE" if status == audit.UNTESTED else "FIX_142"),
            "owner": "#142",
        }
        for index, status in enumerate(statuses)
    ]
    _write_csv(base / "slice3e_scoped_dispositions.csv", ledger)
    queue = [
        {
            "source_file": source_a,
            "review_status": "REVIEW_REQUIRED",
            "human_reviewer": "UNASSIGNED",
            "review_date": "",
            "matrix_operations": "3",
            "workflow_calls": "1",
            "menu_delegations": "1",
            "other_calls_unclassified": "3",
            "context_fields_pending": "3",
            "p02_reproduced": "13",
            "p02_display_degraded": "2",
            "p02_unqualified": "3",
        },
        {
            "source_file": source_b,
            "review_status": "REVIEW_REQUIRED",
            "human_reviewer": "UNASSIGNED",
            "review_date": "",
            "matrix_operations": "1",
            "workflow_calls": "0",
            "menu_delegations": "0",
            "other_calls_unclassified": "1",
            "context_fields_pending": "1",
            "p02_reproduced": "0",
            "p02_display_degraded": "0",
            "p02_unqualified": "0",
        },
    ]
    _write_csv(base / "slice4b_surface_review_queue.csv", queue)
    return base


def test_unsigned_handoff_derives_evidence_without_signing_off(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    audit = _module()
    base = _fixture(tmp_path, audit)
    monkeypatch.setattr(audit, "EXPECTED", (2, 4, 6, 4, 4))
    output = audit.build(tmp_path)
    data = json.loads(output[audit.JSON_OUT])
    assert data["schema"] == audit.SCHEMA
    assert data["kind"] == "UNSIGNED_AUDIT_HANDOFF_NOT_RELEASE_CERTIFICATION"
    assert data["coverage"]["surfaces"] == 2
    assert data["coverage"]["context_pending_operations"] == 4
    assert data["evidence_counts"] == {
        "context_first_guards": 13,
        "display_degradations": 2,
        "positive_paths_unqualified": 3,
    }
    assert data["baseline"]["concord_wheel_status"] == "not_provided"
    assert data["baseline"]["captured_installed_concord_version"] == "0.3.2"
    assert all(gate["status"] != "PASSED" for gate in data["gates"])
    assert len(data["source_digests_sha256"]) == 5
    assert all(len(h) == 64 for h in data["source_digests_sha256"].values())
    report = output[audit.MD_OUT].decode("utf-8")
    assert "**NOT PROVIDED**" in report
    assert "Context-first guarded menu failures | 13" in report
    assert "REVIEW_REQUIRED" in report
    assert (base / "baseline.json").exists()


def test_unsigned_handoff_rejects_fabricated_review(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    audit = _module()
    base = _fixture(tmp_path, audit)
    monkeypatch.setattr(audit, "EXPECTED", (2, 4, 6, 4, 4))
    path = base / "slice4b_surface_review_queue.csv"
    rows = list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"))))
    rows[0]["review_status"] = "APPROVED"
    rows[0]["human_reviewer"] = "invented_person"
    _write_csv(path, rows)
    with pytest.raises(audit.HandoffError, match="signoff"):
        audit.build(tmp_path)


def test_unsigned_handoff_rejects_missing_finding_owner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    audit = _module()
    base = _fixture(tmp_path, audit)
    monkeypatch.setattr(audit, "EXPECTED", (2, 4, 6, 4, 4))
    path = base / "slice3e_scoped_dispositions.csv"
    rows = list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"))))
    rows[0]["owner"] = ""
    _write_csv(path, rows)
    with pytest.raises(audit.HandoffError, match="Unowned"):
        audit.build(tmp_path)


def test_unsigned_handoff_rejects_changed_review_totals(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    audit = _module()
    base = _fixture(tmp_path, audit)
    monkeypatch.setattr(audit, "EXPECTED", (2, 4, 6, 4, 4))
    path = base / "slice4b_surface_review_queue.csv"
    rows = list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"))))
    rows[0]["context_fields_pending"] = "0"
    _write_csv(path, rows)
    with pytest.raises(audit.HandoffError, match="totals changed"):
        audit.build(tmp_path)


def test_generate_create_only_and_check_bytes_deterministically(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    audit = _module()
    _fixture(tmp_path, audit)
    monkeypatch.setattr(audit, "EXPECTED", (2, 4, 6, 4, 4))
    with pytest.raises(audit.HandoffError, match="Missing generated"):
        audit.run(tmp_path, check=True)
    assert audit.run(tmp_path, check=False) == (2, 4, 18)
    original = (tmp_path / audit.MD_OUT).read_bytes()
    assert audit.run(tmp_path, check=True) == (2, 4, 18)
    with pytest.raises(audit.HandoffError, match="Create-only"):
        audit.run(tmp_path, check=False)
    (tmp_path / audit.MD_OUT).write_bytes(original + b"tampered\n")
    with pytest.raises(audit.HandoffError, match="Existing handoff differs"):
        audit.run(tmp_path, check=True)


def test_baseline_rejects_release_wheel_status_reclassification(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    audit = _module()
    base = _fixture(tmp_path, audit)
    monkeypatch.setattr(audit, "EXPECTED", (2, 4, 6, 4, 4))
    path = base / "baseline.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    record["published_artifacts"]["concord_v0_3_4_wheel"]["status"] = "verified"
    path.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(audit.HandoffError, match="wheel state changed"):
        audit.build(tmp_path)


def test_live_repository_handoff_matches_frozen_source() -> None:
    audit = _module()
    outputs = audit.build(ROOT)
    assert outputs[audit.JSON_OUT] == (ROOT / audit.JSON_OUT).read_bytes()
    assert outputs[audit.MD_OUT] == (ROOT / audit.MD_OUT).read_bytes()
    data = json.loads(outputs[audit.JSON_OUT])
    assert data["coverage"]["matrix_operations"] == 3685
    assert len(data["scoped_findings"]) == 18
