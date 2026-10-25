"""Issue #141 Slice 2: narrow graph-history context and CAS probes.

The unusual neutral-orientation + standards-backed-history case below is an
isolated STRUCTURAL PROBE, not evidence that this graph is durably valid under
Concord's current domain rules. Storage validation remains authoritative.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from issue140_slice2_fixtures import (
    ACTIVITY_ID,
    ACTOR,
    SOURCE_CLASS,
    build_workspace,
)
from pds_core.routing_models import ModuleWorkRef

import concord.menu_activity as menu
from concord.menu_context import MenuSessionContext
from concord.storage import list_work_snapshots
from concord.workflows import show_activity
from concord.workflows.activity import _load_activity_context


def _work() -> ModuleWorkRef:
    return ModuleWorkRef("concord", SOURCE_CLASS, ACTIVITY_ID)


def _prepare(
    monkeypatch: pytest.MonkeyPatch,
    root: Path,
    *,
    criterion_backed: bool = False,
    score_backed: bool = False,
    stale: bool = False,
) -> Any:
    actual = _load_activity_context(SOURCE_CLASS, ACTIVITY_ID, workspace_root=root)
    fake_graph = SimpleNamespace(
        criteria=(
            [SimpleNamespace(criterion_kind="standard_backed")]
            if criterion_backed
            else []
        ),
        score_records=(
            [SimpleNamespace(score_kind="standard_backed")] if score_backed else []
        ),
    )
    context = SimpleNamespace(
        root=actual.root,
        graph=fake_graph,
        snapshot_revision=actual.snapshot_revision + (1 if stale else 0),
    )
    monkeypatch.setattr(
        menu, "_load_activity_context", lambda c, a, *, workspace_root=None: context
    )
    monkeypatch.setattr(
        menu,
        "show_activity",
        lambda c, a, *, workspace_root=None: show_activity(
            c, a, workspace_root=workspace_root
        ),
    )
    monkeypatch.setattr(menu, "resolve_read_workspace_root", lambda: root)
    monkeypatch.setattr(menu, "prompt_text", lambda *a, **k: "configured")
    monkeypatch.setattr(menu, "confirm_write", lambda *a, **k: True)
    monkeypatch.setattr(menu, "show_result", lambda *a, **k: None)
    return show_activity(SOURCE_CLASS, ACTIVITY_ID, workspace_root=root).summary


@pytest.mark.parametrize("family", ["criterion", "score"])
def test_neutral_orientation_structural_history_requires_library(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, family: str
) -> None:
    fixture = build_workspace(tmp_path, orientation="evidence_only")
    activity = _prepare(
        monkeypatch,
        fixture.root,
        criterion_backed=family == "criterion",
        score_backed=family == "score",
    )
    before = list_work_snapshots(fixture.root, _work())
    captured: list[Any] = []
    errors: list[str] = []
    monkeypatch.setattr(
        menu,
        "load_menu_standards_library",
        lambda root: (
            fixture.standards if root == fixture.root else pytest.fail("wrong root")
        ),
    )

    def _record_update(
        request: Any, *, standards_library: Any, workspace_root: Path | None = None
    ) -> SimpleNamespace:
        captured.append(standards_library)
        return SimpleNamespace(
            activity_id=ACTIVITY_ID,
            commit=SimpleNamespace(no_op=True, snapshot_revision=1),
        )

    monkeypatch.setattr(menu, "update_activity", _record_update)
    monkeypatch.setattr(
        menu, "handle_write_error", lambda error, **k: errors.append(str(error))
    )
    menu._update_activity_field(activity, MenuSessionContext(actor=ACTOR), "status")
    assert not errors
    assert captured == [fixture.standards]
    assert list_work_snapshots(fixture.root, _work()) == before


@pytest.mark.parametrize("family", ["criterion", "score"])
def test_neutral_structural_history_missing_library_refuses_service(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, family: str
) -> None:
    fixture = build_workspace(tmp_path, orientation="local_criteria_only")
    activity = _prepare(
        monkeypatch,
        fixture.root,
        criterion_backed=family == "criterion",
        score_backed=family == "score",
    )
    before = list_work_snapshots(fixture.root, _work())
    errors: list[str] = []
    monkeypatch.setattr(menu, "load_menu_standards_library", lambda root: None)
    monkeypatch.setattr(
        menu, "update_activity", lambda *a, **k: pytest.fail("unexpected write")
    )
    monkeypatch.setattr(
        menu, "handle_write_error", lambda error, **k: errors.append(str(error))
    )
    menu._update_activity_field(activity, MenuSessionContext(actor=ACTOR), "status")
    assert len(errors) == 1
    assert "Core Standards Library" in errors[0]
    assert "No Activity was updated" in errors[0]
    assert list_work_snapshots(fixture.root, _work()) == before


def test_structure_changed_since_menu_preview_blocks_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = build_workspace(tmp_path, orientation="mixed")
    activity = _prepare(monkeypatch, fixture.root, stale=True)
    before = list_work_snapshots(fixture.root, _work())
    errors: list[str] = []
    monkeypatch.setattr(
        menu,
        "load_menu_standards_library",
        lambda root: pytest.fail("stale edit accessed Core library"),
    )
    monkeypatch.setattr(
        menu, "update_activity", lambda *a, **k: pytest.fail("stale edit wrote")
    )
    monkeypatch.setattr(
        menu, "handle_write_error", lambda error, **k: errors.append(str(error))
    )
    menu._update_activity_field(activity, MenuSessionContext(actor=ACTOR), "status")
    assert len(errors) == 1
    assert "changed before" in errors[0]
    assert list_work_snapshots(fixture.root, _work()) == before
