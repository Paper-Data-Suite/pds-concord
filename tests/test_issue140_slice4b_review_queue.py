"""Issue #140 Slice 4B: deterministic reviewer debt, no fabricated signoffs."""

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
SCRIPT = ROOT / "scripts/issue140_slice4b_review_queue.py"


def _module() -> Any:
    spec = importlib.util.spec_from_file_location(
        "issue140_slice4b_review_queue", SCRIPT
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _csv_bytes(rows: list[dict[str, str]], fields: list[str]) -> str:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def _fixture(root: Path, audit: Any) -> Path:
    directory = root / audit.BASE
    directory.mkdir(parents=True)
    menu = "concord/menu_artifact.py"
    cli = "concord/cli.py"
    summary = {
        "schema": "concord_issue140_slice1_census_v1",
        "source_surfaces": [menu, cli],
        "source_inventory": [
            {
                "source_file": menu,
                "handlers": [{"owner": "handle", "line": 2}],
                "calls": [{"name": "workflow"}, {"name": "menu"}],
                "count_workflow_calls": 1,
                "count_menu_delegations": 1,
            },
            {
                "source_file": cli,
                "handlers": [{"owner": "start", "line": 1}],
                "calls": [],
                "count_workflow_calls": 0,
                "count_menu_delegations": 0,
            },
        ],
        "matrix_row_count": 4,
        "all_calls": 2,
        "workflow_call_count": 1,
        "menu_delegation_count": 1,
    }
    (directory / "surface_inventory.json").write_text(
        json.dumps(summary) + "\n", encoding="utf-8"
    )
    cases = (
        (menu, "handle::ENTRY", "HANDLER_INVENTORY"),
        (menu, "handle::call1", "WORKFLOW_SERVICE"),
        (menu, "handle::call2", "MENU_DELEGATION"),
        (cli, "start::ENTRY", "HANDLER_INVENTORY"),
    )
    fields = ["operation_id", "source_file", "boundary_kind", *audit.CONTEXT_FIELDS]
    matrix = [
        {
            "operation_id": f"{source}::{identity}",
            "source_file": source,
            "boundary_kind": kind,
            **{name: "unreviewed" for name in audit.CONTEXT_FIELDS},
        }
        for source, identity, kind in cases
    ]
    for field in audit.CONTEXT_FIELDS:
        matrix[0][field] = "reviewed_fixture_only"
    (directory / "teacher_operation_matrix.csv").write_text(
        _csv_bytes(matrix, fields), encoding="utf-8"
    )
    statuses = (
        ["SYNTHETIC_MENU_REPRODUCED"] * 13
        + ["SYNTHETIC_DISPLAY_DEGRADED"] * 2
        + ["BLOCKED_OR_UNTESTED"] * 3
    )
    ledger = [
        {
            "source_file": menu,
            "service_name": f"synthetic_service_{index}",
            "slice3e_evidence_status": status,
            "owner": "#142",
        }
        for index, status in enumerate(statuses)
    ]
    (directory / "slice3e_scoped_dispositions.csv").write_text(
        _csv_bytes(
            ledger,
            ["source_file", "service_name", "slice3e_evidence_status", "owner"],
        ),
        encoding="utf-8",
    )
    return directory


def test_synthetic_queue_is_complete_but_never_certifies_review(tmp_path: Path) -> None:
    audit = _module()
    _fixture(tmp_path, audit)
    payload, counts = audit.build(tmp_path)
    assert counts == (2, 4, 0, 3)
    rows = list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))
    assert len(rows) == 2
    assert {row["source_file"] for row in rows} == {
        "concord/menu_artifact.py",
        "concord/cli.py",
    }
    assert all(row["review_status"] == audit.REVIEW_REQUIRED for row in rows)
    assert all(row["human_reviewer"] == "UNASSIGNED" for row in rows)
    assert all(not row["review_date"] for row in rows)
    assert sum(int(row["matrix_operations"]) for row in rows) == 4
    assert sum(int(row["p02_reproduced"]) for row in rows) == 13
    assert sum(int(row["p02_display_degraded"]) for row in rows) == 2
    assert sum(int(row["p02_unqualified"]) for row in rows) == 3


def test_generate_is_create_only_and_check_is_read_only(tmp_path: Path) -> None:
    audit = _module()
    _fixture(tmp_path, audit)
    output = tmp_path / audit.OUTPUT
    assert not output.exists()
    with pytest.raises(audit.QueueError, match="missing"):
        audit.run(tmp_path, check=True)
    assert audit.run(tmp_path, check=False) == (2, 4, 0, 3)
    before = output.read_bytes()
    assert audit.run(tmp_path, check=True) == (2, 4, 0, 3)
    assert output.read_bytes() == before
    output.write_bytes(before + b"tampered\n")
    with pytest.raises(audit.QueueError, match="drift"):
        audit.run(tmp_path, check=False)
    assert output.read_bytes() == before + b"tampered\n"


def test_rejects_missing_matrix_operation(tmp_path: Path) -> None:
    audit = _module()
    directory = _fixture(tmp_path, audit)
    path = directory / "teacher_operation_matrix.csv"
    lines = path.read_text(encoding="utf-8").splitlines()
    path.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
    with pytest.raises(audit.QueueError, match="matrix count mismatch"):
        audit.build(tmp_path)


def test_rejects_duplicate_matrix_operation_identity(tmp_path: Path) -> None:
    audit = _module()
    directory = _fixture(tmp_path, audit)
    path = directory / "teacher_operation_matrix.csv"
    source = path.read_text(encoding="utf-8")
    rows = list(csv.DictReader(io.StringIO(source)))
    rows[1]["operation_id"] = rows[0]["operation_id"]
    path.write_text(_csv_bytes(rows, list(rows[0])), encoding="utf-8")
    with pytest.raises(audit.QueueError, match="Duplicate source operation IDs"):
        audit.build(tmp_path)


def test_rejects_falsified_scoped_evidence_count(tmp_path: Path) -> None:
    audit = _module()
    directory = _fixture(tmp_path, audit)
    path = directory / "slice3e_scoped_dispositions.csv"
    rows = list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"))))
    rows[0]["slice3e_evidence_status"] = "BLOCKED_OR_UNTESTED"
    path.write_text(_csv_bytes(rows, list(rows[0])), encoding="utf-8")
    with pytest.raises(audit.QueueError, match="status counts changed"):
        audit.build(tmp_path)


def test_rejects_matrix_boundary_count_drift(tmp_path: Path) -> None:
    audit = _module()
    directory = _fixture(tmp_path, audit)
    path = directory / "teacher_operation_matrix.csv"
    rows = list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"))))
    rows[1]["boundary_kind"] = "OTHER_CALL"
    path.write_text(_csv_bytes(rows, list(rows[0])), encoding="utf-8")
    with pytest.raises(audit.QueueError, match="Matrix/AST coverage mismatch"):
        audit.build(tmp_path)


def test_child_owner_is_proposal_and_unmatched_routes_remain_pending() -> None:
    audit = _module()
    assert audit._review_area("concord/menu_activity.py")[1] == "#141"
    assert audit._review_area("concord/menu_artifact.py")[1] == "#142/#151"
    assert audit._review_area("concord/cli.py")[1] == "#155"
    assert audit._review_area("concord/menu_unfamiliar.py")[1] == "#140/#153"


def test_live_source_receipts_generate_an_unchanged_review_queue() -> None:
    audit = _module()
    payload, counts = audit.build(ROOT)
    assert counts[0] == 67
    assert counts[1] == 3685
    assert 0 <= counts[2] <= 10182
    assert counts[3] > 0
    assert (ROOT / audit.OUTPUT).read_bytes() == payload
