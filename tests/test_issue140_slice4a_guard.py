"""#140 Slice 4A: offline audit guard, including mutation/drift controls."""

from __future__ import annotations

import importlib.util
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts/issue140_slice4a_guard.py"


def _module() -> Any:
    spec = importlib.util.spec_from_file_location("issue140_slice4a_guard", SOURCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _small_menu(root: Path) -> str:
    for relative in (
        "concord/menu.py",
        "concord/menu_navigation.py",
        "concord/cli.py",
    ):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("def base_handler():\n    return None\n", encoding="utf-8")
    target = root / "concord/menu_example.py"
    target.write_text(
        "from concord.workflows import add_artifact_author\n"
        "def teacher_handler():\n"
        "    return add_artifact_author(None)\n",
        encoding="utf-8",
    )
    return "concord/menu_example.py"


def test_new_call_in_existing_audited_module_is_not_silently_ignored(
    tmp_path: Path,
) -> None:
    audit = _module()
    path = _small_menu(tmp_path)
    frozen = audit._read_source(tmp_path, path)
    inventory = {
        "source_surfaces": audit._source_paths(tmp_path),
        "source_inventory": [
            {
                "source_file": filename,
                "handlers": audit._read_source(tmp_path, filename).handlers,
                "calls": audit._read_source(tmp_path, filename).calls,
            }
            for filename in audit._source_paths(tmp_path)
        ],
        "all_calls": sum(
            len(audit._read_source(tmp_path, filename).calls)
            for filename in audit._source_paths(tmp_path)
        ),
    }
    assert audit._surface_guard(tmp_path, inventory) == inventory["all_calls"]
    target = tmp_path / path
    target.write_text(
        target.read_text(encoding="utf-8")
        + "\ndef another_handler():\n    return add_artifact_author(None)\n",
        encoding="utf-8",
    )
    with pytest.raises(audit.GuardError, match="Handler drift|Callsite drift"):
        audit._surface_guard(tmp_path, inventory)
    assert len(frozen.calls) == 1


def test_new_menu_module_triggers_surface_coverage_review(tmp_path: Path) -> None:
    audit = _module()
    _small_menu(tmp_path)
    frozen = audit._source_paths(tmp_path)
    (tmp_path / "concord/menu_new_action.py").write_text(
        "def new_teacher_action():\n    pass\n", encoding="utf-8"
    )
    with pytest.raises(audit.GuardError, match="Teacher-menu surfaces"):
        audit._difference(
            "Teacher-menu surfaces",
            Counter(frozen),
            Counter(audit._source_paths(tmp_path)),
        )


def test_matrix_rejects_missing_ids_and_wrong_alias() -> None:
    audit = _module()
    source = "concord/menu_example.py"
    frozen = {
        "source_inventory": [
            {
                "source_file": source,
                "handlers": [{"owner": "teacher_handler", "line": 2}],
                "calls": [
                    {
                        "source_kind": "WORKFLOW_CALL",
                        "owner_function": "teacher_handler",
                        "name": "add_artifact_author",
                        "ordinal": 1,
                        "line": 3,
                        "shape": "concord.workflows.add_artifact_author",
                    }
                ],
            }
        ],
        "matrix_row_count": 2,
    }
    entry = {
        "operation_id": f"{source}::teacher_handler::ENTRY",
        "source_file": source,
        "boundary_kind": "HANDLER_INVENTORY",
        "line": "2",
        "service_or_delegate": "",
        "evidence_status": "BLOCKED_OR_UNTESTED",
        "disposition": "INVESTIGATE",
    }
    service = {
        **entry,
        "operation_id": f"{source}::teacher_handler::add_artifact_author::1",
        "boundary_kind": "WORKFLOW_SERVICE",
        "line": "3",
        "service_or_delegate": "concord.workflows.add_artifact_author",
    }
    audit._matrix_guard(frozen, [entry, service])
    with pytest.raises(audit.GuardError, match="Teacher-operation IDs"):
        audit._matrix_guard(frozen, [entry, {**service, "operation_id": "unknown"}])
    with pytest.raises(audit.GuardError, match="Service alias changed"):
        audit._matrix_guard(
            frozen, [entry, {**service, "service_or_delegate": "wrong.alias"}]
        )
    with pytest.raises(audit.GuardError, match="Duplicate teacher-operation ID"):
        audit._matrix_guard(frozen, [entry, entry])


def test_narrow_exception_checks_real_forwarding_and_witness(tmp_path: Path) -> None:
    audit = _module()
    service = tmp_path / audit.EXCEPTION_FILE
    service.parent.mkdir(parents=True, exist_ok=True)
    valid = (
        "def prepare_artifact_pages(root, work):\n"
        "    library = _standards(root)\n"
        "    load_current_record_graph(root, work, standards_library=library)\n"
        "    commit_record_batch(root, work, (), standards_library=library)\n"
    )
    service.write_text(valid, encoding="utf-8")
    reference, _, function = audit.EXCEPTION_TEST.partition("::")
    witness = tmp_path / reference
    witness.parent.mkdir(parents=True, exist_ok=True)
    witness.write_text(f"def {function}():\n    pass\n", encoding="utf-8")
    audit._exception_guard(tmp_path)
    service.write_text(
        valid.replace(
            "commit_record_batch(root, work, (), standards_library=library)",
            "commit_record_batch(root, work, ())",
        ),
        encoding="utf-8",
    )
    with pytest.raises(audit.GuardError, match="lost forwarding"):
        audit._exception_guard(tmp_path)


def test_full_repository_guard_uses_existing_audits_without_rewriting(
    tmp_path: Path,
) -> None:
    # #140's source inventory is historical. Run its original drift guard on
    # authenticated frozen source, not on intentional post-merge #141 edits.
    # Current-source semantic coverage and changes belong to successor #162.
    from issue141_frozen_audit import materialize

    audit = _module()
    frozen = tmp_path / "issue140"
    materialize(ROOT, frozen)
    counts = audit.run(frozen)
    assert counts.scoped_families == 18
    assert counts.matrix_rows >= 18
    assert counts.calls >= counts.matrix_rows
    assert counts.surfaces >= 4
