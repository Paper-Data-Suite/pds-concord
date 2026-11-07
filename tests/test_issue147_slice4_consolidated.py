"""#147 final cross-surface, lifecycle, and workspace-isolation acceptance.

All records use temporary synthetic Core-compatible workspaces. The whole
repository and installed-wheel gates run separately in validate_repository.py.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pds_core.classes import load_class_roster
from test_group_plan_manual_issue51 import _actor
from test_issue147_slice1_bulk_engine import _history, _request, _setup
from test_issue147_slice3_batch_cli import _batch_command, _digest

import concord.menu_group_plan_bulk as bulk_menu
from concord.cli import main
from concord.menu_context import MenuSessionContext
from concord.workflows import (
    ApproveGroupPlanRequest,
    PreviewGroupPlanRequest,
    approve_group_plan,
    preview_group_plan,
    show_activity,
    show_group_plan,
)
from concord.workflows.errors import ConcordWorkflowConflictError
from concord.workflows.group_plan_manual import (
    commit_bulk_planned_group_edit,
    prepare_bulk_planned_group_edit,
)


def test_direct_review_then_menu_save_invalidates_old_review(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """CLI review and menu save share one immutable Activity revision boundary."""
    root, snapshot, revision = _setup(tmp_path)
    before = _history(root)
    capsys.readouterr()
    assert main(_batch_command(root, snapshot, revision, "batch-place-preview")) == 0
    old_digest = _digest(capsys.readouterr().out)
    assert _history(root) == before

    monkeypatch.setenv("PDS_WORKSPACE_ROOT", str(root))
    inputs = iter(("1", "1", "2", "d", "SAVE BATCH"))
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))
    monkeypatch.setattr(bulk_menu, "show_result", lambda *_args: None)
    selected = show_group_plan(
        "class-1", "activity-1", "plan-1", workspace_root=root
    )
    bulk_menu.launch_cluster_bulk_editor(selected, MenuSessionContext(actor=_actor()))

    current = show_group_plan(
        "class-1", "activity-1", "plan-1", workspace_root=root
    )
    assert current.plan.proposed_groups[0].student_ids == (
        "student-1", "student-2"
    )
    assert current.plan.proposed_groups[1].student_ids == ()
    assert _history(root) == (before[0] + 1, before[1] + 1)
    assert len(load_class_roster(root, "class-1").students) == 3
    assert show_activity(
        "class-1", "activity-1", workspace_root=root
    ).summary.group_count == 0

    stale = _batch_command(root, snapshot, revision, "batch-place")
    assert main([*stale, "--review-digest", old_digest]) == 3
    assert "Conflict:" in capsys.readouterr().err
    assert _history(root) == (before[0] + 1, before[1] + 1)


def test_completed_manual_group_plan_requires_separate_approval(
    tmp_path: Path,
) -> None:
    """Batch plan assignment never approves or creates operational Groups."""
    root, snapshot, revision = _setup(tmp_path)
    request = _request(
        snapshot, revision, selection=("student-3",), target="a"
    )
    reviewed = prepare_bulk_planned_group_edit(request, workspace_root=root)
    saved = commit_bulk_planned_group_edit(
        request, review_digest=reviewed.review_digest, workspace_root=root
    )
    assert saved.detail.plan.status == "draft"
    assert saved.detail.plan.unresolved_student_ids == ()
    assert show_activity(
        "class-1", "activity-1", workspace_root=root
    ).summary.group_count == 0

    preview = preview_group_plan(
        PreviewGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-1",
            expected_snapshot_revision=saved.detail.summary.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    assert preview.plan.status == "previewed"
    approved = approve_group_plan(
        ApproveGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-1",
            expected_snapshot_revision=preview.summary.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    assert approved.status == "approved"
    assert show_activity(
        "class-1", "activity-1", workspace_root=root
    ).summary.group_count == 0

    current = show_group_plan(
        "class-1", "activity-1", "plan-1", workspace_root=root
    )
    before = _history(root)
    with pytest.raises(ConcordWorkflowConflictError, match="draft|previewed"):
        prepare_bulk_planned_group_edit(
            _request(
                current.summary.snapshot_revision,
                current.record_revision,
                selection=("student-2",),
            ),
            workspace_root=root,
        )
    assert _history(root) == before


def test_review_digest_is_bound_to_exact_workspace(
    tmp_path: Path,
) -> None:
    """Identical synthetic IDs in another workspace cannot reuse a review."""
    first, snapshot, revision = _setup(tmp_path / "workspace-one")
    second, second_snapshot, second_revision = _setup(
        tmp_path / "workspace-two"
    )
    assert (snapshot, revision) == (second_snapshot, second_revision)
    request = _request(snapshot, revision)
    reviewed = prepare_bulk_planned_group_edit(request, workspace_root=first)
    before = _history(second)
    with pytest.raises(ConcordWorkflowConflictError, match="review"):
        commit_bulk_planned_group_edit(
            request,
            review_digest=reviewed.review_digest,
            workspace_root=second,
        )
    assert _history(second) == before
