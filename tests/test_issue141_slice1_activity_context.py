"""Issue #141 Slice 1: fail-closed Activity context and preserved neutral paths."""

from __future__ import annotations

from pathlib import Path

import pytest
from issue140_slice2_fixtures import (
    ACTIVITY_ID,
    ACTOR,
    SOURCE_CLASS,
    build_workspace,
)
from pds_core.routing_models import ModuleWorkRef

import concord.menu_activity as activity_menu
from concord.menu_context import MenuSessionContext
from concord.storage import list_work_snapshots
from concord.workflows import show_activity
from concord.workflows.activity import _load_activity_context


def _work() -> ModuleWorkRef:
    return ModuleWorkRef("concord", SOURCE_CLASS, ACTIVITY_ID)


def test_missing_canonical_library_refuses_mixed_status_edit_before_service(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = build_workspace(tmp_path, orientation="mixed")
    root = fixture.root
    activity = show_activity(SOURCE_CLASS, ACTIVITY_ID, workspace_root=root).summary
    before = list_work_snapshots(root, _work())
    errors: list[str] = []
    monkeypatch.setattr(
        activity_menu,
        "show_activity",
        lambda c, a, *, workspace_root=None: show_activity(
            c, a, workspace_root=workspace_root
        ),
    )
    monkeypatch.setattr(
        activity_menu,
        "_load_activity_context",
        lambda c, a, *, workspace_root=None: _load_activity_context(
            c, a, workspace_root=workspace_root
        ),
    )
    monkeypatch.setattr(activity_menu, "resolve_read_workspace_root", lambda: root)
    monkeypatch.setattr(activity_menu, "prompt_text", lambda *a, **k: "configured")
    monkeypatch.setattr(activity_menu, "confirm_write", lambda *a, **k: True)
    monkeypatch.setattr(
        activity_menu, "load_menu_standards_library", lambda _root: None
    )
    monkeypatch.setattr(
        activity_menu,
        "update_activity",
        lambda *a, **k: pytest.fail("missing library reached mutation service"),
    )
    monkeypatch.setattr(
        activity_menu, "handle_write_error", lambda e, **k: errors.append(str(e))
    )
    activity_menu._update_activity_field(
        activity, MenuSessionContext(actor=ACTOR), "status"
    )
    assert len(errors) == 1
    assert "Core Standards Library" in errors[0]
    assert "No Activity was updated" in errors[0]
    assert list_work_snapshots(root, _work()) == before
    assert (
        show_activity(SOURCE_CLASS, ACTIVITY_ID, workspace_root=root).summary.status
        == "draft"
    )


def test_cancellation_does_not_load_standards_or_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = build_workspace(tmp_path, orientation="mixed")
    root = fixture.root
    activity = show_activity(SOURCE_CLASS, ACTIVITY_ID, workspace_root=root).summary
    before = list_work_snapshots(root, _work())
    monkeypatch.setattr(
        activity_menu,
        "show_activity",
        lambda c, a, *, workspace_root=None: show_activity(
            c, a, workspace_root=workspace_root
        ),
    )
    monkeypatch.setattr(activity_menu, "resolve_read_workspace_root", lambda: root)
    monkeypatch.setattr(activity_menu, "prompt_text", lambda *a, **k: "configured")
    monkeypatch.setattr(activity_menu, "confirm_write", lambda *a, **k: False)
    monkeypatch.setattr(
        activity_menu,
        "load_menu_standards_library",
        lambda: pytest.fail("cancelled menu loaded Standards"),
    )
    monkeypatch.setattr(
        activity_menu,
        "update_activity",
        lambda *a, **k: pytest.fail("cancelled menu committed"),
    )
    activity_menu._update_activity_field(
        activity, MenuSessionContext(actor=ACTOR), "status"
    )
    assert list_work_snapshots(root, _work()) == before
