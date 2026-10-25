"""#141 Slice 5: Activity read, authority and write share an exact workspace.

All test data is fabricated; no live teacher workspace is opened or modified.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from issue140_slice2_fixtures import (
    ACTIVITY_ID,
    ACTOR,
    SOURCE_CLASS,
    STANDARD_ID,
    build_workspace,
)
from pds_core.routing_models import ModuleWorkRef

import concord.menu_activity as menu
from concord.menu_context import MenuSessionContext
from concord.storage import list_work_snapshots
from concord.workflows import show_activity, update_activity
from concord.workflows.activity import _load_activity_context


def _work() -> ModuleWorkRef:
    return ModuleWorkRef("concord", SOURCE_CLASS, ACTIVITY_ID)


def _rooted_menu_read(monkeypatch: pytest.MonkeyPatch, root: Path) -> None:
    monkeypatch.setattr(menu, "resolve_read_workspace_root", lambda: root)
    monkeypatch.setattr(
        menu,
        "show_activity",
        lambda class_id, activity_id, *, workspace_root=None: show_activity(
            class_id, activity_id, workspace_root=workspace_root
        ),
    )
    monkeypatch.setattr(menu, "prompt_text", lambda *a, **k: "configured")
    monkeypatch.setattr(menu, "confirm_write", lambda *a, **k: True)


def test_workspace_root_mismatch_refuses_all_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = build_workspace(tmp_path / "source", orientation="mixed")
    foreign = build_workspace(tmp_path / "foreign", orientation="mixed")
    _rooted_menu_read(monkeypatch, source.root)
    current = show_activity(
        SOURCE_CLASS, ACTIVITY_ID, workspace_root=source.root
    ).summary
    original_source = list_work_snapshots(source.root, _work())
    original_foreign = list_work_snapshots(foreign.root, _work())
    errors: list[str] = []
    selection_roots: list[Path] = []

    def reject_foreign_library(root: Path) -> None:
        selection_roots.append(root)
        pytest.fail("foreign context must be rejected before Standards load")

    monkeypatch.setattr(
        menu,
        "_load_activity_context",
        lambda c, a, *, workspace_root=None: _load_activity_context(
            c, a, workspace_root=foreign.root
        ),
    )
    monkeypatch.setattr(
        menu,
        "load_menu_standards_library",
        reject_foreign_library,
    )
    monkeypatch.setattr(
        menu,
        "update_activity",
        lambda *a, **k: pytest.fail("workspace drift reached write service"),
    )
    monkeypatch.setattr(
        menu, "show_result", lambda *a, **k: pytest.fail("unexpected success")
    )
    monkeypatch.setattr(
        menu, "handle_write_error", lambda error, **k: errors.append(str(error))
    )
    menu._update_activity_field(current, MenuSessionContext(actor=ACTOR), "status")
    assert len(errors) == 1
    assert "workspace changed" in errors[0].lower()
    assert "No Activity was updated" in errors[0]
    assert not selection_roots
    assert list_work_snapshots(source.root, _work()) == original_source
    assert list_work_snapshots(foreign.root, _work()) == original_foreign


def test_real_mutation_is_pinned_to_initial_workspace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = build_workspace(tmp_path / "source", orientation="mixed")
    foreign = build_workspace(tmp_path / "foreign", orientation="mixed")
    _rooted_menu_read(monkeypatch, source.root)
    current = show_activity(
        SOURCE_CLASS, ACTIVITY_ID, workspace_root=source.root
    ).summary
    source_before = list_work_snapshots(source.root, _work())
    foreign_before = list_work_snapshots(foreign.root, _work())
    monkeypatch.setattr(
        menu,
        "_load_activity_context",
        lambda c, a, *, workspace_root=None: _load_activity_context(
            c, a, workspace_root=workspace_root
        ),
    )
    roots: list[Path] = []
    errors: list[str] = []
    results: list[tuple[Any, ...]] = []

    def library_loader(root: Path) -> Any:
        roots.append(root)
        assert root == source.root
        return source.standards

    def guarded_service(
        request: Any, *, workspace_root: Path, standards_library: Any
    ) -> Any:
        assert workspace_root == source.root
        assert standards_library is source.standards
        return update_activity(
            request, workspace_root=workspace_root, standards_library=standards_library
        )

    monkeypatch.setattr(menu, "load_menu_standards_library", library_loader)
    monkeypatch.setattr(menu, "update_activity", guarded_service)
    monkeypatch.setattr(menu, "show_result", lambda *a, **k: results.append(a))
    monkeypatch.setattr(
        menu, "handle_write_error", lambda e, **k: errors.append(str(e))
    )
    menu._update_activity_field(current, MenuSessionContext(actor=ACTOR), "status")
    assert not errors
    assert len(results) == 1
    assert roots == [source.root]
    assert len(list_work_snapshots(source.root, _work())) == len(source_before) + 1
    assert list_work_snapshots(foreign.root, _work()) == foreign_before


def test_scoring_selection_uses_pinned_workspace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = build_workspace(tmp_path / "source", orientation="evidence_only")
    foreign = build_workspace(tmp_path / "foreign", orientation="evidence_only")
    _rooted_menu_read(monkeypatch, source.root)
    current = show_activity(
        SOURCE_CLASS, ACTIVITY_ID, workspace_root=source.root
    ).summary
    foreign_before = list_work_snapshots(foreign.root, _work())
    monkeypatch.setattr(
        menu,
        "_load_activity_context",
        lambda c, a, *, workspace_root=None: _load_activity_context(
            c, a, workspace_root=workspace_root
        ),
    )
    roots: list[Path] = []
    errors: list[str] = []

    def library_loader(root: Path) -> Any:
        roots.append(root)
        assert root == source.root
        return source.standards

    monkeypatch.setattr(menu, "load_menu_standards_library", library_loader)
    monkeypatch.setattr(menu, "_choose_scoring_orientation", lambda: "mixed")
    monkeypatch.setattr(
        menu, "choose_standards_profile", lambda library: library.profiles[0]
    )
    monkeypatch.setattr(
        menu, "choose_focus_standards", lambda library, profile: (STANDARD_ID,)
    )
    monkeypatch.setattr(
        menu,
        "update_activity",
        lambda request, *, workspace_root, standards_library: update_activity(
            request, workspace_root=workspace_root, standards_library=standards_library
        ),
    )
    monkeypatch.setattr(menu, "show_result", lambda *a, **k: None)
    monkeypatch.setattr(
        menu, "handle_write_error", lambda e, **k: errors.append(str(e))
    )
    menu._update_activity_field(
        current, MenuSessionContext(actor=ACTOR), "scoring_orientation"
    )
    assert not errors
    assert roots == [source.root, source.root]
    updated = show_activity(SOURCE_CLASS, ACTIVITY_ID, workspace_root=source.root)
    assert updated.summary.scoring_orientation == "mixed"
    assert updated.focus_standard_ids == (STANDARD_ID,)
    assert list_work_snapshots(foreign.root, _work()) == foreign_before


def test_unavailable_workspace_never_attempts_read_or_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = build_workspace(tmp_path, orientation="mixed")
    current = show_activity(
        SOURCE_CLASS, ACTIVITY_ID, workspace_root=fixture.root
    ).summary
    before = list_work_snapshots(fixture.root, _work())
    errors: list[str] = []
    monkeypatch.setattr(menu, "resolve_read_workspace_root", lambda: None)
    monkeypatch.setattr(
        menu, "show_activity", lambda *a, **k: pytest.fail("read without root")
    )
    monkeypatch.setattr(
        menu, "update_activity", lambda *a, **k: pytest.fail("write without root")
    )
    monkeypatch.setattr(
        menu, "handle_write_error", lambda e, **k: errors.append(str(e))
    )
    menu._update_activity_field(current, MenuSessionContext(actor=ACTOR), "status")
    assert len(errors) == 1
    assert "workspace is unavailable" in errors[0]
    assert list_work_snapshots(fixture.root, _work()) == before
