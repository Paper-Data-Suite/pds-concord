"""#146 Slice 3: assignment-ending menus, exact statuses, history and cancellation.

Only disposable Core/Concord classes are used; no live roster or assessment data.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from pds_core.routing_models import ModuleWorkRef
from test_workflow_groups_assignments import (
    _actor,
    _context,
    _group_with_members,
    _workspace_with_activity,
)

import concord.menu_assignment_end as end_choices
import concord.menu_group as group_menu
import concord.menu_responsibility as responsibility_menu
import concord.menu_role as role_menu
from concord.menu_context import CancelMenuAction, MenuSessionContext
from concord.storage import list_record_revisions, list_work_snapshots
from concord.workflows import (
    AssignResponsibilityRequest,
    AssignRoleRequest,
    ConcordWorkflowValidationError,
    assign_responsibility,
    assign_role,
    core_student_participant,
    group_record_reference,
    list_groups,
    list_memberships,
    list_responsibilities,
    list_roles,
    show_activity,
)

END_STATUSES = ("completed", "withdrawn", "cancelled")
KINDS = ("membership", "role", "responsibility")


def _work() -> ModuleWorkRef:
    return ModuleWorkRef("concord", "class-1", "activity-1")


def _seed(tmp_path: Path, kind: str) -> tuple[Path, str]:
    root, revision = _workspace_with_activity(tmp_path)
    revision = _group_with_members(root, revision)
    if kind == "membership":
        return root, "membership-1"
    if kind == "role":
        result = assign_role(
            AssignRoleRequest(
                class_id="class-1",
                activity_id="activity-1",
                role_assignment_id="role-1",
                participant_reference=core_student_participant(
                    root, "class-1", "student-1"
                ),
                role_key="speaker",
                membership_id="membership-1",
                effective_context=_context("session-1"),
                expected_snapshot_revision=revision,
                actor=_actor(),
            ),
            workspace_root=root,
        )
    else:
        result = assign_responsibility(
            AssignResponsibilityRequest(
                class_id="class-1",
                activity_id="activity-1",
                responsibility_assignment_id="responsibility-1",
                assignee_reference=group_record_reference("group-a"),
                description="Prepare synthetic materials.",
                effective_context=_context("session-1"),
                expected_snapshot_revision=revision,
                actor=_actor(),
            ),
            workspace_root=root,
        )
    assert result.commit.snapshot_revision == revision + 1
    return root, "role-1" if kind == "role" else "responsibility-1"


def _wire(
    monkeypatch: pytest.MonkeyPatch,
    root: Path,
    kind: str,
    *,
    selected: str = "completed",
    confirmed: bool = True,
) -> tuple[list[tuple[str, str, tuple[str, ...]]], list[tuple[Any, ...]], list[str]]:
    module = {
        "membership": group_menu,
        "role": role_menu,
        "responsibility": responsibility_menu,
    }[kind]
    monkeypatch.setattr(
        module,
        "_latest",
        lambda _activity: show_activity(
            "class-1", "activity-1", workspace_root=root
        ).summary,
    )
    monkeypatch.setattr(
        module,
        "standards_kwargs_for_activity",
        lambda _activity: {"workspace_root": root},
    )
    if kind == "membership":
        monkeypatch.setattr(
            module, "list_groups",
            lambda c, a: list_groups(c, a, workspace_root=root),
        )
        monkeypatch.setattr(
            module, "list_memberships",
            lambda c, a: list_memberships(c, a, workspace_root=root),
        )
        monkeypatch.setattr(module, "choose_membership", lambda items, **_kw: items[0])
    elif kind == "role":
        monkeypatch.setattr(
            module, "list_roles", lambda c, a: list_roles(c, a, workspace_root=root)
        )
        monkeypatch.setattr(module, "_choose_existing", lambda items, _title: items[0])
    else:
        monkeypatch.setattr(
            module, "list_responsibilities",
            lambda c, a: list_responsibilities(c, a, workspace_root=root),
        )
        monkeypatch.setattr(module, "_choose_existing", lambda items, _title: items[0])
    monkeypatch.setattr(end_choices, "select_one", lambda *_args, **_kwargs: selected)
    review: list[tuple[str, str, tuple[str, ...]]] = []
    receipts: list[tuple[Any, ...]] = []
    errors: list[str] = []

    def confirm(title: str, token: str, lines: tuple[str, ...]) -> bool:
        review.append((title, token, lines))
        return confirmed

    monkeypatch.setattr(module, "confirm_write", confirm)
    monkeypatch.setattr(module, "show_result", lambda *args: receipts.append(args))
    monkeypatch.setattr(
        module, "handle_write_error", lambda error, **_kw: errors.append(str(error))
    )
    return review, receipts, errors


def _invoke(kind: str, root: Path) -> None:
    activity = show_activity("class-1", "activity-1", workspace_root=root).summary
    state = MenuSessionContext(actor=_actor())
    if kind == "membership":
        group_menu._end_member(activity, state)
    elif kind == "role":
        role_menu._end(activity, state)
    else:
        responsibility_menu._end(activity, state)


def _read_status(kind: str, root: Path) -> str:
    if kind == "membership":
        return list_memberships("class-1", "activity-1", workspace_root=root)[0].status
    if kind == "role":
        return list_roles("class-1", "activity-1", workspace_root=root)[0].status
    return list_responsibilities("class-1", "activity-1", workspace_root=root)[0].status


@pytest.mark.parametrize("kind", KINDS)
def test_chooser_exact_semantics_and_current_context(
    monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    root_title = "Synthetic Activity"
    from concord.workflows.models import ActivitySummary

    activity = ActivitySummary(
        class_id="class-1", activity_id="activity-1", title=root_title,
        status="draft", scoring_orientation="evidence_only",
        session_count=1, group_count=1, snapshot_revision=7,
    )
    captured: list[tuple[str, tuple[str, ...], tuple[str, ...], str]] = []

    def choose(title: str, items: tuple[str, ...], labels: tuple[str, ...], *,
               help_text: str) -> str:
        captured.append((title, items, labels, help_text))
        return "withdrawn"

    monkeypatch.setattr(end_choices, "select_one", choose)
    assert end_choices.choose_assignment_end_status(
        activity, record_kind=kind.title(), record_id="record-1",
        display_label="Synthetic student / Cluster A", current_status="active",
    ) == "withdrawn"
    title, items, labels, help_text = captured[0]
    assert items == END_STATUSES and len(labels) == 3
    assert "Current status: active" in title and "Snapshot: 7" in title
    assert "Synthetic student" in title and "record-1" in title
    assert "Reassignment" in help_text and "Scores" in help_text


@pytest.mark.parametrize("status", ("reassigned", "superseded", "active", "bad"))
def test_chooser_rejects_invalid_values_before_write(
    monkeypatch: pytest.MonkeyPatch, status: str
) -> None:
    from concord.workflows.models import ActivitySummary

    activity = ActivitySummary(
        class_id="class-1", activity_id="activity-1", title="Synthetic",
        status="draft", scoring_orientation="evidence_only",
        session_count=1, group_count=1, snapshot_revision=1,
    )
    monkeypatch.setattr(end_choices, "select_one", lambda *_a, **_k: status)
    with pytest.raises(ConcordWorkflowValidationError, match="Invalid ending status"):
        end_choices.choose_assignment_end_status(
            activity, record_kind="Role", record_id="role-1",
            display_label="Synthetic", current_status="active",
        )


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("status", END_STATUSES)
def test_end_menu_commits_one_canonical_revision_with_teacher_review(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str, status: str
) -> None:
    root, record_id = _seed(tmp_path, kind)
    before = list_work_snapshots(root, _work())
    review, receipts, errors = _wire(monkeypatch, root, kind, selected=status)
    _invoke(kind, root)
    assert not errors
    assert len(review) == len(receipts) == 1
    assert review[0][1] == "END"
    confirmation = "\n".join(review[0][2])
    assert "Current status: active" in confirmation
    assert f"Requested status: {status}" in confirmation
    assert "Snapshot:" in confirmation and record_id in confirmation
    assert "immutable history" in confirmation
    assert _read_status(kind, root) == status
    assert len(list_work_snapshots(root, _work())) == len(before) + 1
    record_kind = {
        "membership": "group_membership",
        "role": "role_assignment",
        "responsibility": "responsibility_assignment",
    }[kind]
    assert list_record_revisions(root, _work(), record_kind, record_id) == (1, 2)
    assert f"active -> {status}" in str(receipts)


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("confirmed", (True, False))
def test_no_eligible_or_declined_confirmation_is_zero_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str, confirmed: bool
) -> None:
    root, _ = _seed(tmp_path, kind)
    before = list_work_snapshots(root, _work())
    review, receipts, errors = _wire(
        monkeypatch, root, kind, selected="completed", confirmed=confirmed
    )
    if confirmed:
        _invoke(kind, root)
        after_first = list_work_snapshots(root, _work())
        review.clear()
        receipts.clear()
        _invoke(kind, root)
        assert list_work_snapshots(root, _work()) == after_first
        assert not review and not errors
        assert "No planned or active" in str(receipts)
    else:
        _invoke(kind, root)
        assert len(review) == 1 and not receipts and not errors
        assert list_work_snapshots(root, _work()) == before


@pytest.mark.parametrize("kind", KINDS)
def test_back_cancels_before_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    root, _ = _seed(tmp_path, kind)
    before = list_work_snapshots(root, _work())
    review, receipts, errors = _wire(monkeypatch, root, kind)

    def back(*_args: object, **_kwargs: object) -> str:
        raise CancelMenuAction

    monkeypatch.setattr(end_choices, "select_one", back)
    _invoke(kind, root)
    assert not review and not receipts and not errors
    assert list_work_snapshots(root, _work()) == before


@pytest.mark.parametrize("kind", KINDS)
def test_stale_selected_assignment_refused_without_new_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    root, _ = _seed(tmp_path, kind)
    before = list_work_snapshots(root, _work())
    review, receipts, errors = _wire(monkeypatch, root, kind)
    module = {
        "membership": group_menu,
        "role": role_menu,
        "responsibility": responsibility_menu,
    }[kind]

    def stale(items: Any, *_args: object, **_kw: object) -> Any:
        current = items[0]
        return replace(current, snapshot_revision=current.snapshot_revision - 1)

    monkeypatch.setattr(
        module, "choose_membership" if kind == "membership" else "_choose_existing",
        stale,
    )
    _invoke(kind, root)
    assert not review and not receipts and errors
    assert "stale" in errors[0].lower()
    assert list_work_snapshots(root, _work()) == before
