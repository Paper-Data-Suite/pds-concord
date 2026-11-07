"""Concord #146 Slice 2: guided Session status and actual service boundary.

All fixtures use synthetic Core classes and Concord Activity records only.
"""

from __future__ import annotations

from dataclasses import replace
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

import concord.menu_prompts as prompts
import concord.menu_session as menu
from concord.menu_context import CancelMenuAction, MenuSessionContext
from concord.storage import list_work_snapshots
from concord.workflows import list_sessions, show_activity, show_session

_STATUSES = (
    "planned",
    "active",
    "completed",
    "cancelled",
    "interrupted",
    "archived",
)
_SESSION_ID = "issue140-synthetic-session"


def _work() -> ModuleWorkRef:
    return ModuleWorkRef("concord", SOURCE_CLASS, ACTIVITY_ID)


def _fake_activity() -> SimpleNamespace:
    return SimpleNamespace(
        class_id="fake-class",
        activity_id="fake-activity",
        title="Synthetic Discussion",
        snapshot_revision=8,
    )


def _fake_session() -> SimpleNamespace:
    return SimpleNamespace(
        class_id="fake-class",
        activity_id="fake-activity",
        session_id="fake-session",
        sequence=2,
        label="Second Day",
        status="planned",
        snapshot_revision=8,
    )


def test_chooser_native_values_explanations_and_exact_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[tuple[str, tuple[str, ...], tuple[str, ...], str]] = []

    def capture(
        title: str,
        choices: tuple[str, ...],
        labels: tuple[str, ...],
        *,
        help_text: str,
    ) -> str:
        seen.append((title, choices, labels, help_text))
        return "active"

    monkeypatch.setattr(menu, "select_one", capture)
    assert menu._choose_session_status(_fake_activity(), _fake_session()) == "active"
    assert len(seen) == 1
    title, choices, labels, help_text = seen[0]
    assert choices == _STATUSES
    assert len(labels) == len(_STATUSES)
    assert labels[0].endswith("[current]")
    assert all(not x.endswith("[current]") for x in labels[1:])
    for status, label in zip(choices, labels, strict=True):
        assert status.title() in label
        assert " - " in label
    for fragment in (
        "Synthetic Discussion",
        "fake-class",
        "fake-activity",
        "Second Day",
        "fake-session",
        "Current status: planned",
        "Snapshot: 8",
    ):
        assert fragment in title
    assert "not an Activity status" in help_text
    assert "timestamps" in help_text


def test_real_numbered_menu_rejects_arbitrary_status_then_selects_valid(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    inputs = iter(("9", "2"))
    monkeypatch.setattr("builtins.input", lambda _prompt: next(inputs))
    monkeypatch.setattr(prompts, "clear_screen", lambda: None)
    monkeypatch.setattr(prompts, "pause_for_user", lambda: None)
    assert menu._choose_session_status(_fake_activity(), _fake_session()) == "active"
    visible = capsys.readouterr().out
    assert "1. Planned" in visible and "2. Active" in visible
    assert "Snapshot: 8" in visible


def _wire(
    monkeypatch: pytest.MonkeyPatch,
    root: Path,
    library: Any,
    *,
    selected: str = "active",
    confirmed: bool = True,
) -> tuple[list[tuple[str, str, tuple[str, ...]]], list[tuple[Any, ...]], list[str]]:
    reviews: list[tuple[str, str, tuple[str, ...]]] = []
    receipts: list[tuple[Any, ...]] = []
    errors: list[str] = []
    monkeypatch.setattr(
        menu,
        "_latest",
        lambda _summary: show_activity(
            SOURCE_CLASS, ACTIVITY_ID, workspace_root=root
        ).summary,
    )
    monkeypatch.setattr(
        menu,
        "standards_kwargs_for_activity",
        lambda _summary: {"workspace_root": root, "standards_library": library},
    )
    monkeypatch.setattr(menu, "select_one", lambda *_a, **_k: selected)

    def confirm(title: str, token: str, lines: tuple[str, ...]) -> bool:
        reviews.append((title, token, lines))
        return confirmed

    monkeypatch.setattr(menu, "confirm_write", confirm)
    monkeypatch.setattr(menu, "show_result", lambda *args: receipts.append(args))
    monkeypatch.setattr(menu, "_handle_error", lambda _a, e: errors.append(str(e)))
    return reviews, receipts, errors


def _current(root: Path) -> tuple[Any, Any]:
    activity = show_activity(SOURCE_CLASS, ACTIVITY_ID, workspace_root=root).summary
    sessions = list_sessions(SOURCE_CLASS, ACTIVITY_ID, workspace_root=root)
    assert len(sessions) == 1 and sessions[0].session_id == _SESSION_ID
    return activity, sessions[0]


@pytest.mark.parametrize("orientation", ("mixed", "standards_based", "evidence_only"))
@pytest.mark.parametrize(
    "target", ("active", "completed", "interrupted", "cancelled", "archived")
)
def test_real_session_status_commit_preserves_time_and_revision(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    orientation: str,
    target: str,
) -> None:
    fixture = build_workspace(tmp_path, orientation=orientation)
    activity, session = _current(fixture.root)
    before = show_session(SOURCE_CLASS, ACTIVITY_ID, session.session_id,
                          workspace_root=fixture.root)
    snapshots = list_work_snapshots(fixture.root, _work())
    reviews, receipts, errors = _wire(
        monkeypatch, fixture.root, fixture.standards, selected=target
    )
    menu._edit_field(activity, session, MenuSessionContext(actor=ACTOR), "status")
    assert not errors
    assert len(reviews) == len(receipts) == 1
    assert reviews[0][:2] == ("Edit Session", "UPDATE")
    review = "\n".join(reviews[0][2])
    assert "Current status: planned" in review
    assert f"Requested status: {target}" in review
    assert f"Session ID: {session.session_id}" in review
    assert f"Snapshot: {activity.snapshot_revision}" in review
    assert "does not create timestamps" in review
    after = show_session(SOURCE_CLASS, ACTIVITY_ID, session.session_id,
                         workspace_root=fixture.root)
    assert after.status == target
    for name in (
        "scheduled_start", "scheduled_end", "actual_start", "actual_end",
        "status_reason", "notes", "label", "sequence",
    ):
        assert getattr(after, name) == getattr(before, name)
    updated, _ = _current(fixture.root)
    assert updated.snapshot_revision == activity.snapshot_revision + 1
    assert len(list_work_snapshots(fixture.root, _work())) == len(snapshots) + 1
    assert f"Status: planned -> {target}" in str(receipts)


def test_real_second_transition_active_to_completed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = build_workspace(tmp_path, orientation="mixed")
    _wire(monkeypatch, fixture.root, fixture.standards, selected="active")
    activity, session = _current(fixture.root)
    menu._edit_field(activity, session, MenuSessionContext(actor=ACTOR), "status")
    monkeypatch.setattr(menu, "select_one", lambda *_a, **_k: "completed")
    activity, session = _current(fixture.root)
    assert session.status == "active"
    menu._edit_field(activity, session, MenuSessionContext(actor=ACTOR), "status")
    assert show_session(SOURCE_CLASS, ACTIVITY_ID, session.session_id,
                        workspace_root=fixture.root).status == "completed"


def test_current_status_is_no_op_without_confirm_or_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = build_workspace(tmp_path, orientation="mixed")
    activity, session = _current(fixture.root)
    snapshots = list_work_snapshots(fixture.root, _work())
    reviews, receipts, errors = _wire(
        monkeypatch, fixture.root, fixture.standards, selected="planned"
    )
    monkeypatch.setattr(
        menu, "update_session", lambda *_a, **_k: pytest.fail("No-op wrote")
    )
    monkeypatch.setattr(
        menu, "standards_kwargs_for_activity",
        lambda _a: pytest.fail("No-op loaded write context"),
    )
    menu._edit_field(activity, session, MenuSessionContext(actor=ACTOR), "status")
    assert not reviews and not errors
    assert "No Session changes were needed" in str(receipts)
    assert "Status remains: planned" in str(receipts)
    assert list_work_snapshots(fixture.root, _work()) == snapshots


@pytest.mark.parametrize("from_choice", (True, False))
def test_back_and_declined_review_are_zero_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    from_choice: bool,
) -> None:
    fixture = build_workspace(tmp_path, orientation="mixed")
    activity, session = _current(fixture.root)
    before = list_work_snapshots(fixture.root, _work())
    reviews, receipts, errors = _wire(
        monkeypatch, fixture.root, fixture.standards, confirmed=False
    )
    if from_choice:
        def back(*_a: object, **_k: object) -> str:
            raise CancelMenuAction
        monkeypatch.setattr(menu, "select_one", back)
    monkeypatch.setattr(
        menu, "update_session", lambda *_a, **_k: pytest.fail("Cancel wrote")
    )
    menu._edit_field(activity, session, MenuSessionContext(actor=ACTOR), "status")
    assert not errors and not receipts
    assert len(reviews) == (0 if from_choice else 1)
    assert list_work_snapshots(fixture.root, _work()) == before


def test_stale_selected_session_refused_before_choice(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = build_workspace(tmp_path, orientation="mixed")
    activity, session = _current(fixture.root)
    stale = replace(session, snapshot_revision=session.snapshot_revision + 1)
    before = list_work_snapshots(fixture.root, _work())
    reviews, receipts, errors = _wire(monkeypatch, fixture.root, fixture.standards)
    monkeypatch.setattr(
        menu, "select_one", lambda *_a, **_k: pytest.fail("Stale chooser")
    )
    monkeypatch.setattr(
        menu, "update_session", lambda *_a, **_k: pytest.fail("Stale write")
    )
    menu._edit_field(activity, stale, MenuSessionContext(actor=ACTOR), "status")
    assert not reviews and not receipts
    assert errors and "Reopen the Session" in errors[0]
    assert list_work_snapshots(fixture.root, _work()) == before


def test_wrong_class_session_refused_without_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = build_workspace(tmp_path, orientation="mixed")
    activity, session = _current(fixture.root)
    wrong = replace(session, class_id="unrelated-class")
    before = list_work_snapshots(fixture.root, _work())
    reviews, receipts, errors = _wire(monkeypatch, fixture.root, fixture.standards)
    monkeypatch.setattr(
        menu, "select_one", lambda *_a, **_k: pytest.fail("Wrong class")
    )
    menu._edit_field(activity, wrong, MenuSessionContext(actor=ACTOR), "status")
    assert not reviews and not receipts and errors
    assert list_work_snapshots(fixture.root, _work()) == before


def test_missing_standards_rejected_by_service_without_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = build_workspace(tmp_path, orientation="mixed")
    activity, session = _current(fixture.root)
    before = list_work_snapshots(fixture.root, _work())
    reviews, receipts, errors = _wire(monkeypatch, fixture.root, None)
    menu._edit_field(activity, session, MenuSessionContext(actor=ACTOR), "status")
    assert len(reviews) == 1 and not receipts and errors
    assert list_work_snapshots(fixture.root, _work()) == before
    assert show_session(SOURCE_CLASS, ACTIVITY_ID, session.session_id,
                        workspace_root=fixture.root).status == "planned"
