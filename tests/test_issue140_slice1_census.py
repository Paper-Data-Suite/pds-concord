"""Offline AST and create-only census checks for Issue #140 Slice 1."""

from __future__ import annotations

import ast
import csv
import importlib.util
import io
import json
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/issue140_slice1_census.py"


def _module() -> Any:
    spec = importlib.util.spec_from_file_location("issue140_slice1_census", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # dataclass looks up its defining module for annotation metadata.
    import sys

    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _fixture(tmp_path: Path) -> Path:
    paths = {
        "concord/menu.py": (
            "from concord.menu_activity import edit_activity\n"
            "def launch():\n    return edit_activity()\n"
        ),
        "concord/menu_navigation.py": "def navigate():\n    return True\n",
        "concord/cli.py": (
            "from concord.workflows import list_activities\n"
            "def main():\n    return list_activities('synthetic')\n"
        ),
        "concord/menu_activity.py": (
            "from concord.workflows import update_activity\n"
            "def edit_activity():\n"
            "    return update_activity('synthetic')\n"
        ),
        "concord/workflows/__init__.py": "",
        "concord/workflows/activity.py": (
            "def update_activity(*, standards_library=None):\n"
            "    return load_current_record_graph(\n"
            "        'synthetic', standards_library=standards_library\n"
            "    )\n"
        ),
    }
    for rel, value in paths.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(value, encoding="utf-8")
    base = tmp_path / "docs/audits/issue140"
    base.mkdir(parents=True)
    (base / "baseline.md").write_text("# Synthetic receipt\n", encoding="utf-8")
    record = {
        "schema": "concord_issue140_slice0_baseline_v1",
        "captured_utc": "2026-10-20T00:00:00+00:00",
        "repository": "Paper-Data-Suite/pds-concord",
        "git": {"head": "68ddd804d2733fa900ee396ac7a2ba6bd98aa819"},
        "source": {"version": "0.3.4"},
        "environment": {},
        "published_artifacts": {
            "core_v0_6_6_wheel": {"status": "verified_published_bytes_and_metadata"}
        },
        "inventory": {},
        "limits": {},
    }
    (base / "baseline.json").write_text(json.dumps(record), encoding="utf-8")
    return tmp_path


def test_census_compiles_without_importing_concord() -> None:
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    assert tree.body
    assert "concord.workflows" not in {
        alias.name
        for stmt in tree.body
        if isinstance(stmt, ast.Import)
        for alias in stmt.names
    }


def test_census_deterministic_and_guarded(tmp_path: Path) -> None:
    audit = _module()
    root = _fixture(tmp_path)
    one = audit.build(root)
    two = audit.build(root)
    assert one == two
    assert set(one) == {
        "teacher_operation_matrix.csv",
        "service_context_catalog.csv",
        "surface_inventory.json",
    }
    matrix_text = one["teacher_operation_matrix.csv"].decode()
    rows = list(csv.DictReader(io.StringIO(matrix_text)))
    assert len(rows) == len({r["operation_id"] for r in rows})
    assert any(
        r["service_or_delegate"] == "concord.workflows.update_activity"
        and r["evidence_status"] == "CODE_PATH_VERIFIED"
        and r["disposition"] == "FIX_141"
        for r in rows
    )
    assert any(r["boundary_kind"] == "HANDLER_INVENTORY" for r in rows)
    assert any(r["boundary_kind"] == "MENU_DELEGATION" for r in rows)
    status = json.loads(one["surface_inventory.json"])
    assert status["all_calls"] >= 3
    assert status["handler_count"] >= 4
    assert audit.run(root, check_only=False)[0] == len(rows)
    assert audit.run(root, check_only=True)[0] == len(rows)
    assert audit.run(root, check_only=False)[0] == len(rows)


def test_new_callsite_requires_inventory_refresh(tmp_path: Path) -> None:
    audit = _module()
    root = _fixture(tmp_path)
    audit.run(root, check_only=False)
    p = root / "concord/menu_activity.py"
    p.write_text(
        p.read_text(encoding="utf-8")
        + "\ndef newly_added():\n    update_activity('x')\n",
        encoding="utf-8",
    )
    with pytest.raises(audit.AuditError, match="differs from source"):
        audit.run(root, check_only=True)
    assert (root / "docs/audits/issue140/teacher_operation_matrix.csv").is_file()


def test_unexpected_baseline_schema_fails_without_writes(tmp_path: Path) -> None:
    audit = _module()
    root = _fixture(tmp_path)
    path = root / "docs/audits/issue140/baseline.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["teacher_email"] = "redacted@example.org"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(audit.AuditError, match="Unexpected keys"):
        audit.run(root, check_only=False)
    assert not (root / "docs/audits/issue140/teacher_operation_matrix.csv").exists()


def test_internal_resolution_not_assumed_neutral(tmp_path: Path) -> None:
    audit = _module()
    root = _fixture(tmp_path)
    p = root / "concord/workflows/activity.py"
    p.write_text(
        p.read_text(encoding="utf-8")
        + "\ndef prepare_artifact_pages(*, standards_library=None):\n"
        + "    library = load_workspace_standards_library('synthetic')\n"
        + "    return load_current_record_graph(\n"
        + "        'synthetic', standards_library=library\n"
        + "    )\n",
        encoding="utf-8",
    )
    results = audit.build(root)
    service_text = results["service_context_catalog.csv"].decode()
    rows = list(csv.DictReader(io.StringIO(service_text)))
    candidate = next(row for row in rows if row["function"] == "prepare_artifact_pages")
    assert candidate["internal_workspace_library_lookup"] == "true"
    assert candidate["evidence_status"] == "BLOCKED_OR_UNTESTED"


def test_all_calls_retained_even_when_not_service(tmp_path: Path) -> None:
    audit = _module()
    root = _fixture(tmp_path)
    p = root / "concord/menu_activity.py"
    p.write_text(
        p.read_text(encoding="utf-8") + "\ndef extra():\n    print('x')\n",
        encoding="utf-8",
    )
    inventory = json.loads(audit.build(root)["surface_inventory.json"])
    section = next(
        x
        for x in inventory["source_inventory"]
        if x["source_file"] == "concord/menu_activity.py"
    )
    assert any(
        x["name"] == "print" and x["source_kind"] == "OTHER_CALL"
        for x in section["calls"]
    )
    assert "does not certify neutrality" in section["other_call_exclusion_reason"]
