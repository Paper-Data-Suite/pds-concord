"""#146 Slice 4: guided Group status, history, audit and no-write paths.

Only fabricated temporary Core/Concord workspaces are used.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from pds_core.routing_models import ModuleWorkRef
from test_workflow_groups_assignments import _actor, _workspace_with_activity

import concord.menu_group as menu
import concord.menu_prompts as prompts
from concord.menu_context import CancelMenuAction, MenuSessionContext
from concord.storage import list_record_revisions, list_work_snapshots
from concord.workflows import (
    CreateGroupRequest,
    UpdateGroupRequest,
    create_group,
    list_groups,
    show_activity,
    show_group,
    update_group,
)

STATUSES = (
    "planned", "active", "inactive", "completed", "cancelled", "archived",
    "superseded",
)


def _work() -> ModuleWorkRef:
    return ModuleWorkRef("concord", "class-1", "activity-1")


def _seed(tmp_path: Path) -> Path:
    root, revision = _workspace_with_activity(tmp_path)
    result = create_group(
        CreateGroupRequest(
            class_id="class-1", activity_id="activity-1", group_id="group-a",
            label="Cluster A", status="planned", expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    assert result.commit.snapshot_revision == revision + 1
    return root


def _wire(
    monkeypatch: pytest.MonkeyPatch,
    root: Path,
    *,
    choice: str = "active",
    confirmed: bool = True,
) -> tuple[list[tuple[str, str, tuple[str, ...]]], list[tuple[Any, ...]], list[str]]:
    monkeypatch.setattr(menu, "_latest", lambda _activity: show_activity(
        "class-1", "activity-1", workspace_root=root
    ).summary)
    monkeypatch.setattr(menu, "list_groups", lambda c, a: list_groups(
        c, a, workspace_root=root
    ))
    monkeypatch.setattr(menu, "show_group", lambda c, a, g: show_group(
        c, a, g, workspace_root=root
    ))
    monkeypatch.setattr(menu, "choose_group", lambda groups, **_kw: groups[0])
    monkeypatch.setattr(menu, "standards_kwargs_for_activity", lambda _activity: {
        "workspace_root": root
    })
    monkeypatch.setattr(menu, "select_one", lambda *_a, **_kw: choice)
    monkeypatch.setattr("builtins.input", lambda _prompt: "3")
    reviews: list[tuple[str, str, tuple[str, ...]]] = []
    results: list[tuple[Any, ...]] = []
    errors: list[str] = []
    monkeypatch.setattr(menu, "confirm_write", lambda title, token, lines: (
        reviews.append((title, token, lines)) or confirmed
    ))
    monkeypatch.setattr(menu, "show_result", lambda *args: results.append(args))
    monkeypatch.setattr(menu, "_handle_error", lambda _activity, _title, error: (
        errors.append(str(error))
    ))
    return reviews, results, errors


def _invoke(root: Path) -> None:
    activity = show_activity("class-1", "activity-1", workspace_root=root).summary
    menu._edit_group(activity, MenuSessionContext(actor=_actor()))


def test_group_chooser_exact_statuses_and_successor_caveat(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from concord.workflows.models import ActivitySummary, GroupSummary

    activity = ActivitySummary(
        class_id="class-1", activity_id="activity-1", title="Discussion",
        status="draft", scoring_orientation="evidence_only",
        session_count=1, group_count=1, snapshot_revision=8,
    )
    group = GroupSummary(
        class_id="class-1", activity_id="activity-1", group_id="group-a",
        label="Cluster A", status="planned", member_count=0,
        parent_group_id=None, effective_session_count=0, snapshot_revision=8,
    )
    seen: list[tuple[str, tuple[str, ...], tuple[str, ...], str]] = []

    def choose(title: str, items: tuple[str, ...], labels: tuple[str, ...], *,
               help_text: str) -> str:
        seen.append((title, items, labels, help_text))
        return "superseded"

    monkeypatch.setattr(menu, "select_one", choose)
    assert menu._choose_group_status(activity, group) == "superseded"
    title, items, labels, help_text = seen[0]
    assert items == STATUSES and len(labels) == len(STATUSES)
    assert labels[0].endswith("[current]")
    assert "Current status: planned" in title
    assert "Snapshot: 8" in title
    assert "Group ID: group-a" in title
    assert "does not create another Group" in help_text
    assert "move students" in help_text


def test_numbered_picker_rejects_unlisted_values_and_supports_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from concord.workflows.models import ActivitySummary, GroupSummary

    activity = ActivitySummary(
        class_id="class-1", activity_id="activity-1", title="Discussion",
        status="draft", scoring_orientation="evidence_only",
        session_count=1, group_count=1, snapshot_revision=8,
    )
    group = GroupSummary(
        class_id="class-1", activity_id="activity-1", group_id="group-a",
        label="Cluster A", status="planned", member_count=0,
        parent_group_id=None, effective_session_count=0, snapshot_revision=8,
    )
    entries = iter(("99", "7"))
    monkeypatch.setattr("builtins.input", lambda _prompt: next(entries))
    monkeypatch.setattr(prompts, "clear_screen", lambda: None)
    monkeypatch.setattr(prompts, "pause_for_user", lambda: None)
    assert menu._choose_group_status(activity, group) == "superseded"
    monkeypatch.setattr("builtins.input", lambda _prompt: "B")
    with pytest.raises(CancelMenuAction):
        menu._choose_group_status(activity, group)


@pytest.mark.parametrize("status", STATUSES)
def test_group_status_real_service_and_immutable_lineage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, status: str,
) -> None:
    root = _seed(tmp_path)
    original = show_group("class-1", "activity-1", "group-a", workspace_root=root)
    snapshots = list_work_snapshots(root, _work())
    versions = list_record_revisions(root, _work(), "group", "group-a")
    reviews, receipts, errors = _wire(monkeypatch, root, choice=status)
    _invoke(root)
    assert not errors and len(receipts) == 1
    after = show_group("class-1", "activity-1", "group-a", workspace_root=root)
    assert after.summary.status == status
    assert after.summary.group_id == original.summary.group_id
    assert after.supersedes_group_id == original.supersedes_group_id
    assert after.summary.member_count == original.summary.member_count
    assert after.effective_context == original.effective_context
    if status == "planned":
        assert not reviews
        assert "No Group changes were needed" in str(receipts)
        assert list_work_snapshots(root, _work()) == snapshots
        assert list_record_revisions(root, _work(), "group", "group-a") == versions
    else:
        assert len(reviews) == 1
        assert reviews[0][:2] == ("Edit Group", "UPDATE")
        review = "\n".join(reviews[0][2])
        assert "Current status: planned" in review
        assert f"Requested status: {status}" in review
        assert "No Group successor" in review
        assert len(list_work_snapshots(root, _work())) == len(snapshots) + 1
        assert (
            len(list_record_revisions(root, _work(), "group", "group-a"))
            == len(versions) + 1
        )
        assert f"Status: planned -> {status}" in str(receipts)


@pytest.mark.parametrize("mode", ("decline", "back", "invalid"))
def test_cancelled_and_invalid_status_do_not_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str,
) -> None:
    root = _seed(tmp_path)
    snapshots = list_work_snapshots(root, _work())
    reviews, receipts, errors = _wire(
        monkeypatch,
        root,
        choice="not-a-group-status" if mode == "invalid" else "active",
        confirmed=mode != "decline",
    )
    if mode == "back":
        def back(*_args: object, **_kwargs: object) -> str:
            raise CancelMenuAction
        monkeypatch.setattr(menu, "select_one", back)
    _invoke(root)
    assert list_work_snapshots(root, _work()) == snapshots
    assert not receipts
    if mode == "decline":
        assert len(reviews) == 1 and not errors
    else:
        assert not reviews
        assert (len(errors) == 1) == (mode == "invalid")
    assert (
        show_group("class-1", "activity-1", "group-a", workspace_root=root)
        .summary.status
        == "planned"
    )


def test_stale_group_selection_refused_before_menu_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _seed(tmp_path)
    snapshots = list_work_snapshots(root, _work())
    reviews, receipts, errors = _wire(monkeypatch, root)
    selected = list_groups("class-1", "activity-1", workspace_root=root)[0]
    before = show_activity("class-1", "activity-1", workspace_root=root).summary
    result = update_group(
        UpdateGroupRequest(
            class_id="class-1", activity_id="activity-1", group_id="group-a",
            expected_snapshot_revision=before.snapshot_revision, actor=_actor(),
            label="Cluster A Updated in Another Menu",
        ),
        workspace_root=root,
    )
    assert result.commit.snapshot_revision == before.snapshot_revision + 1
    monkeypatch.setattr(menu, "list_groups", lambda *_a: (selected,))
    _invoke(root)
    assert errors and "changed since it was selected" in errors[0]
    assert not reviews and not receipts
    assert len(list_work_snapshots(root, _work())) == len(snapshots) + 1
    assert (
        show_group("class-1", "activity-1", "group-a", workspace_root=root)
        .summary.status
        == "planned"
    )


def test_existing_group_label_text_edit_remains_allowed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _seed(tmp_path)
    reviews, receipts, errors = _wire(monkeypatch, root)
    monkeypatch.setattr("builtins.input", lambda _prompt: "1")
    monkeypatch.setattr(menu, "prompt_text", lambda *_a, **_kw: "Updated Group Label")
    _invoke(root)
    assert not errors and len(reviews) == len(receipts) == 1
    assert (
        show_group("class-1", "activity-1", "group-a", workspace_root=root)
        .summary.label
        == "Updated Group Label"
    )
