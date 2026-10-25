"""Issue #141: real menu/service Activity edit acceptance on synthetic workspaces.

No live roster, teacher workspace, external network, or real student data.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from issue140_slice2_fixtures import (
    ACTIVITY_ID,
    ACTOR,
    PROFILE_ID,
    SOURCE_CLASS,
    STANDARD_ID,
    TARGET_CLASS,
    WitnessWorkspace,
    build_workspace,
)
from pds_core.routing_models import ModuleWorkRef
from pds_core.standards import StandardsLibrary

import concord.menu_activity as menu
from concord.menu_context import MenuSessionContext
from concord.storage import list_work_snapshots
from concord.workflows import UpdateActivityRequest, show_activity, update_activity
from concord.workflows.activity import _load_activity_context


def _work() -> ModuleWorkRef:
    return ModuleWorkRef("concord", SOURCE_CLASS, ACTIVITY_ID)


def _setup(
    monkeypatch: pytest.MonkeyPatch,
    fixture: WitnessWorkspace,
    *,
    value: str | None = "configured",
    chosen_orientation: str = "mixed",
    selected_profile: str = PROFILE_ID,
    selected_focus: tuple[str, ...] = (STANDARD_ID,),
    authority: StandardsLibrary | None = None,
    use_authority: bool = True,
    confirmed: bool = True,
) -> tuple[list[Any], list[str], list[tuple[Any, ...]], list[Path | None]]:
    root = fixture.root
    forwarded: list[Any] = []
    errors: list[str] = []
    results: list[tuple[Any, ...]] = []
    resolved: list[Path | None] = []
    library = fixture.standards if authority is None else authority

    monkeypatch.setattr(
        menu,
        "show_activity",
        lambda c, a, *, workspace_root=None: show_activity(
            c, a, workspace_root=workspace_root
        ),
    )
    monkeypatch.setattr(
        menu,
        "_load_activity_context",
        lambda c, a, *, workspace_root=None: _load_activity_context(
            c, a, workspace_root=workspace_root
        ),
    )
    monkeypatch.setattr(menu, "resolve_read_workspace_root", lambda: root)
    monkeypatch.setattr(menu, "prompt_text", lambda *a, **k: value)
    monkeypatch.setattr(menu, "_choose_activity_type", lambda: "laboratory")
    monkeypatch.setattr(menu, "_choose_scoring_orientation", lambda: chosen_orientation)
    monkeypatch.setattr(
        menu,
        "_standards_selection",
        lambda orientation, *, workspace_root=None: (
            (library, selected_profile, selected_focus)
            if orientation in {"mixed", "standards_based"}
            else (None, None, ())
        ),
    )
    monkeypatch.setattr(menu, "confirm_write", lambda *a, **k: confirmed)
    monkeypatch.setattr(
        menu, "show_result", lambda *args, **kwargs: results.append(args)
    )
    monkeypatch.setattr(
        menu, "handle_write_error", lambda err, **kwargs: errors.append(str(err))
    )

    def load_library(workspace: Path) -> StandardsLibrary | None:
        resolved.append(workspace)
        assert workspace == root, "canonical library resolved from wrong workspace"
        return library if use_authority else None

    monkeypatch.setattr(menu, "load_menu_standards_library", load_library)

    def real_service(
        request: UpdateActivityRequest,
        *,
        standards_library: StandardsLibrary | None = None,
        workspace_root: Path | None = None,
    ) -> Any:
        assert workspace_root == root
        forwarded.append((request, standards_library))
        return update_activity(
            request, workspace_root=workspace_root, standards_library=standards_library
        )

    monkeypatch.setattr(menu, "update_activity", real_service)
    return forwarded, errors, results, resolved


@pytest.mark.parametrize("orientation", ["mixed", "standards_based"])
@pytest.mark.parametrize(
    ("field", "expected"),
    [
        ("title", "New Synthetic Activity Title"),
        ("description", "New synthetic description"),
        ("status", "configured"),
        ("activity_type", "laboratory"),
    ],
)
def test_all_ordinary_standards_backed_edits_commit_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    orientation: str,
    field: str,
    expected: str,
) -> None:
    fixture = build_workspace(tmp_path, orientation=orientation)
    value = expected if field in {"title", "description", "status"} else None
    forwarded, errors, results, resolved = _setup(monkeypatch, fixture, value=value)
    initial = show_activity(SOURCE_CLASS, ACTIVITY_ID, workspace_root=fixture.root)
    before = list_work_snapshots(fixture.root, _work())
    menu._update_activity_field(initial.summary, MenuSessionContext(actor=ACTOR), field)
    assert not errors
    assert len(results) == 1
    assert len(forwarded) == 1
    request, library = forwarded[0]
    assert library is fixture.standards
    assert request.expected_snapshot_revision == initial.summary.snapshot_revision
    assert request.actor.actor_id == ACTOR.actor_id
    assert resolved == [fixture.root]
    after = show_activity(SOURCE_CLASS, ACTIVITY_ID, workspace_root=fixture.root)
    actual = (
        getattr(after.summary, field)
        if field in {"title", "status"}
        else (after.description if field == "description" else after.activity_type)
    )
    assert actual == expected
    assert after.summary.snapshot_revision == initial.summary.snapshot_revision + 1
    assert len(list_work_snapshots(fixture.root, _work())) == len(before) + 1
    assert after.summary.scoring_orientation == orientation
    assert after.standards_profile_id == PROFILE_ID
    assert after.focus_standard_ids == (STANDARD_ID,)


@pytest.mark.parametrize(
    ("starting", "chosen"),
    [
        ("evidence_only", "mixed"),
        ("local_criteria_only", "standards_based"),
        ("mixed", "evidence_only"),
        ("standards_based", "local_criteria_only"),
    ],
)
def test_orientation_transition_revalidates_existing_and_candidate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    starting: str,
    chosen: str,
) -> None:
    fixture = build_workspace(tmp_path, orientation=starting)
    forwarded, errors, results, resolved = _setup(
        monkeypatch, fixture, chosen_orientation=chosen
    )
    before = show_activity(SOURCE_CLASS, ACTIVITY_ID, workspace_root=fixture.root)
    menu._update_activity_field(
        before.summary, MenuSessionContext(actor=ACTOR), "scoring_orientation"
    )
    assert not errors
    assert len(results) == 1
    assert len(forwarded) == 1
    assert forwarded[0][1] is fixture.standards
    assert resolved == [fixture.root]
    after = show_activity(SOURCE_CLASS, ACTIVITY_ID, workspace_root=fixture.root)
    assert after.summary.scoring_orientation == chosen
    assert after.summary.snapshot_revision == before.summary.snapshot_revision + 1
    if chosen in {"mixed", "standards_based"}:
        assert after.standards_profile_id == PROFILE_ID
        assert after.focus_standard_ids == (STANDARD_ID,)
    else:
        assert after.standards_profile_id is None
        assert after.focus_standard_ids == ()


@pytest.mark.parametrize(
    "choice, field",
    [
        ("1", "title"),
        ("2", "description"),
        ("3", "status"),
        ("4", "activity_type"),
        ("5", "scoring_orientation"),
    ],
)
def test_numbered_edit_menu_dispatches_exactly_one_route(
    monkeypatch: pytest.MonkeyPatch, choice: str, field: str
) -> None:
    summary = show_fake_summary()
    dispatched: list[str] = []
    monkeypatch.setattr("builtins.input", lambda _: choice)
    monkeypatch.setattr(menu, "clear_screen", lambda: None)
    monkeypatch.setattr(menu, "print_menu_header", lambda _: None)
    monkeypatch.setattr(menu, "print_navigation", lambda: None)
    monkeypatch.setattr(
        menu,
        "_update_activity_field",
        lambda activity, state, selected: dispatched.append(selected),
    )
    menu._edit_activity(summary, MenuSessionContext(actor=ACTOR))
    assert dispatched == [field]


def show_fake_summary() -> Any:
    from concord.workflows.models import ActivitySummary

    return ActivitySummary(
        class_id=SOURCE_CLASS,
        activity_id=ACTIVITY_ID,
        title="Synthetic Menu Activity",
        status="draft",
        scoring_orientation="mixed",
        session_count=1,
        group_count=0,
        snapshot_revision=1,
    )


def test_valid_no_op_keeps_snapshot_and_reports_no_change(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = build_workspace(tmp_path, orientation="mixed")
    current = show_activity(SOURCE_CLASS, ACTIVITY_ID, workspace_root=fixture.root)
    forwarded, errors, results, resolved = _setup(
        monkeypatch, fixture, value=current.summary.title
    )
    before = list_work_snapshots(fixture.root, _work())
    menu._update_activity_field(
        current.summary, MenuSessionContext(actor=ACTOR), "title"
    )
    assert not errors
    assert len(forwarded) == 1
    assert forwarded[0][1] is fixture.standards
    assert resolved == [fixture.root]
    assert len(results) == 1
    assert "No changes were needed." in str(results[0])
    assert list_work_snapshots(fixture.root, _work()) == before


@pytest.mark.parametrize(
    "invalid_field, invalid_value",
    [("status", "invalid_status_value"), ("activity_type", "not-a-namespaced-type")],
)
def test_invalid_edit_fails_without_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    invalid_field: str,
    invalid_value: str,
) -> None:
    fixture = build_workspace(tmp_path, orientation="mixed")
    current = show_activity(SOURCE_CLASS, ACTIVITY_ID, workspace_root=fixture.root)
    forwarded, errors, results, _ = _setup(monkeypatch, fixture, value=invalid_value)
    if invalid_field == "activity_type":
        monkeypatch.setattr(menu, "_choose_activity_type", lambda: invalid_value)
    before = list_work_snapshots(fixture.root, _work())
    menu._update_activity_field(
        current.summary, MenuSessionContext(actor=ACTOR), invalid_field
    )
    assert len(forwarded) == 1
    assert len(errors) == 1
    assert not results
    assert list_work_snapshots(fixture.root, _work()) == before


def test_inactive_core_focus_fails_without_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = build_workspace(tmp_path, orientation="mixed")
    inactive = StandardsLibrary(
        standards=(replace(fixture.standards.standards[0], active=False),),
        profiles=fixture.standards.profiles,
    )
    current = show_activity(SOURCE_CLASS, ACTIVITY_ID, workspace_root=fixture.root)
    forwarded, errors, results, _ = _setup(monkeypatch, fixture, authority=inactive)
    before = list_work_snapshots(fixture.root, _work())
    menu._update_activity_field(
        current.summary, MenuSessionContext(actor=ACTOR), "status"
    )
    assert len(forwarded) == 1
    assert forwarded[0][1] is inactive
    assert errors
    assert not results
    assert list_work_snapshots(fixture.root, _work()) == before


def test_wrong_candidate_profile_refused_without_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = build_workspace(tmp_path, orientation="evidence_only")
    current = show_activity(SOURCE_CLASS, ACTIVITY_ID, workspace_root=fixture.root)
    forwarded, errors, results, _ = _setup(
        monkeypatch,
        fixture,
        chosen_orientation="standards_based",
        selected_profile="nonexistent-synthetic-profile",
    )
    before = list_work_snapshots(fixture.root, _work())
    menu._update_activity_field(
        current.summary, MenuSessionContext(actor=ACTOR), "scoring_orientation"
    )
    assert len(forwarded) == 1
    assert errors
    assert not results
    assert list_work_snapshots(fixture.root, _work()) == before


def test_intervening_update_rejects_stale_menu_request(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = build_workspace(tmp_path, orientation="mixed")
    current = show_activity(SOURCE_CLASS, ACTIVITY_ID, workspace_root=fixture.root)
    forwarded, errors, results, _ = _setup(monkeypatch, fixture)
    before = list_work_snapshots(fixture.root, _work())

    def concurrent_writer(
        request: UpdateActivityRequest,
        *,
        standards_library: StandardsLibrary | None,
        workspace_root: Path | None = None,
    ) -> Any:
        assert workspace_root == fixture.root
        forwarded.append((request, standards_library))
        update_activity(
            UpdateActivityRequest(
                class_id=SOURCE_CLASS,
                activity_id=ACTIVITY_ID,
                expected_snapshot_revision=request.expected_snapshot_revision,
                actor=ACTOR,
                title="Synthetic intervening writer",
            ),
            workspace_root=fixture.root,
            standards_library=fixture.standards,
        )
        return update_activity(
            request,
            workspace_root=fixture.root,
            standards_library=standards_library,
        )

    monkeypatch.setattr(menu, "update_activity", concurrent_writer)
    menu._update_activity_field(
        current.summary, MenuSessionContext(actor=ACTOR), "status"
    )
    assert len(forwarded) == 1
    assert errors
    assert not results
    assert len(list_work_snapshots(fixture.root, _work())) == len(before) + 1
    after = show_activity(SOURCE_CLASS, ACTIVITY_ID, workspace_root=fixture.root)
    assert after.summary.title == "Synthetic intervening writer"
    assert after.summary.status == "draft"


def test_wrong_class_lookup_never_reaches_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = build_workspace(tmp_path, orientation="mixed")
    current = show_activity(SOURCE_CLASS, ACTIVITY_ID, workspace_root=fixture.root)
    forwarded, errors, results, _ = _setup(monkeypatch, fixture)
    wrong_class = replace(current.summary, class_id=TARGET_CLASS)
    before = list_work_snapshots(fixture.root, _work())
    menu._update_activity_field(wrong_class, MenuSessionContext(actor=ACTOR), "status")
    assert not forwarded
    assert errors
    assert not results
    assert list_work_snapshots(fixture.root, _work()) == before


def test_neutral_title_update_requires_no_core_library(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = build_workspace(tmp_path, orientation="evidence_only")
    current = show_activity(SOURCE_CLASS, ACTIVITY_ID, workspace_root=fixture.root)
    forwarded, errors, results, resolved = _setup(
        monkeypatch, fixture, value="New neutral title", use_authority=False
    )
    before = list_work_snapshots(fixture.root, _work())
    menu._update_activity_field(
        current.summary, MenuSessionContext(actor=ACTOR), "title"
    )
    assert not errors
    assert len(results) == 1
    assert len(forwarded) == 1
    assert forwarded[0][1] is None
    assert not resolved
    after = show_activity(SOURCE_CLASS, ACTIVITY_ID, workspace_root=fixture.root)
    assert after.summary.title == "New neutral title"
    assert len(list_work_snapshots(fixture.root, _work())) == len(before) + 1
