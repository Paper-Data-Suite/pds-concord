"""#147 Slice 1: real proposal/service acceptance on synthetic Core workspaces."""

from __future__ import annotations

from pathlib import Path

import pytest
from pds_core.classes import write_class_roster
from test_group_plan_manual_issue51 import _actor, _roster, _workspace

import concord.workflows.group_plan_manual as manual
from concord.models import PlannedGroup
from concord.storage import list_record_revisions, list_work_snapshots
from concord.workflows import (
    PreviewGroupPlanRequest,
    preview_group_plan,
    show_group_plan,
)
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowNotFoundError,
    ConcordWorkflowValidationError,
)
from concord.workflows.group_plan_manual import (
    BulkPlannedGroupEditRequest,
    CreateManualGroupPlanRequest,
    commit_bulk_planned_group_edit,
    create_manual_group_plan,
    prepare_bulk_planned_group_edit,
)


def _setup(tmp_path: Path) -> tuple[Path, int, int]:
    root, revision = _workspace(tmp_path)
    created = create_manual_group_plan(
        CreateManualGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-1",
            proposed_groups=(
                PlannedGroup(
                    planned_group_key="a", label="Table A",
                    student_ids=("student-1",), description="Preserve this",
                ),
                PlannedGroup(
                    planned_group_key="b", label="Table B",
                    student_ids=("student-2",),
                ),
            ),
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    detail = show_group_plan("class-1", "activity-1", "plan-1", workspace_root=root)
    assert detail.record_revision == 1
    return root, created.commit.snapshot_revision, detail.record_revision


def _request(
    snapshot: int,
    record: int,
    *,
    selection: tuple[str, ...] = ("student-2", "student-3"),
    operation: str = "place_or_move",
    target: str = "a",
    actor=None,
) -> BulkPlannedGroupEditRequest:
    return BulkPlannedGroupEditRequest(
        class_id="class-1",
        activity_id="activity-1",
        group_plan_id="plan-1",
        planned_group_key=target,
        operation=operation,
        student_ids=selection,
        expected_snapshot_revision=snapshot,
        expected_record_revision=record,
        actor=_actor() if actor is None else actor,
    )


def _history(root: Path) -> tuple[int, int]:
    from pds_core.routing_models import ModuleWorkRef

    work = ModuleWorkRef("concord", "class-1", "activity-1")
    return (
        len(list_work_snapshots(root, work)),
        len(list_record_revisions(root, work, "group_plan", "plan-1")),
    )


def test_read_only_review_and_one_canonical_move_commit(tmp_path: Path) -> None:
    root, snapshot, revision = _setup(tmp_path)
    before = _history(root)
    request = _request(snapshot, revision)
    reviewed = prepare_bulk_planned_group_edit(request, workspace_root=root)
    assert _history(root) == before
    assert reviewed.original_status == "draft"
    assert reviewed.roster_student_ids == ("student-1", "student-2", "student-3")
    assert reviewed.selected_student_ids == ("student-2", "student-3")
    assert tuple(
        (item.student_id, item.from_group_key, item.to_group_key)
        for item in reviewed.changes
    ) == (
        ("student-2", "b", "a"),
        ("student-3", None, "a"),
    )
    assert reviewed.before_sizes == (("a", 1), ("b", 1))
    assert reviewed.after_sizes == (("a", 3), ("b", 0))
    assert (reviewed.unresolved_before, reviewed.unresolved_after) == (1, 0)
    assert not reviewed.no_op
    assert len(reviewed.review_digest) == 64

    saved = commit_bulk_planned_group_edit(
        request, workspace_root=root, review_digest=reviewed.review_digest
    )
    assert saved.changed is True
    assert saved.mutation is not None
    assert saved.detail.plan.strategy == "manual"
    assert saved.detail.plan.proposed_groups[0].student_ids == (
        "student-1", "student-2", "student-3"
    )
    assert saved.detail.plan.proposed_groups[0].description == "Preserve this"
    assert saved.detail.plan.proposed_groups[1].student_ids == ()
    assert saved.detail.plan.unresolved_student_ids == ()
    assert _history(root) == (before[0] + 1, before[1] + 1)
    assert saved.detail.record_revision == revision + 1


def test_unassign_to_unresolved_and_unchanged_noop(tmp_path: Path) -> None:
    root, snapshot, record = _setup(tmp_path)
    removing = _request(
        snapshot, record,
        selection=("student-1",), operation="unassign_from_target",
    )
    review = prepare_bulk_planned_group_edit(removing, workspace_root=root)
    assert len(review.changes) == 1
    assert review.changes[0].to_group_key is None
    edited = commit_bulk_planned_group_edit(
        removing, workspace_root=root, review_digest=review.review_digest
    )
    assert "student-1" in edited.detail.plan.unresolved_student_ids
    assert edited.detail.plan.proposed_groups[0].student_ids == ()

    current = edited.detail
    same = _request(
        current.summary.snapshot_revision, current.record_revision,
        selection=("student-2",), target="b",
    )
    before = _history(root)
    no_op_review = prepare_bulk_planned_group_edit(same, workspace_root=root)
    assert no_op_review.no_op
    assert no_op_review.unchanged_count == 1
    saved = commit_bulk_planned_group_edit(
        same, workspace_root=root, review_digest=no_op_review.review_digest
    )
    assert saved.changed is False
    assert _history(root) == before


@pytest.mark.parametrize(
    ("selection", "target", "operation", "expected_error"),
    (
        (("student-2", "student-2"), "a", "place_or_move", "duplicate"),
        (("student-unknown",), "a", "place_or_move", "Core roster"),
        (("student-2",), "missing", "place_or_move", "not available"),
        (("student-2",), "a", "unassign_from_target", "not in"),
        (("student-2",), "a", "unknown", "Unsupported"),
    ),
)
def test_invalid_request_is_zero_write(
    tmp_path: Path,
    selection: tuple[str, ...],
    target: str,
    operation: str,
    expected_error: str,
) -> None:
    root, snapshot, record = _setup(tmp_path)
    before = _history(root)
    request = _request(
        snapshot, record, selection=selection, target=target, operation=operation
    )
    with pytest.raises(
        (ConcordWorkflowValidationError, ConcordWorkflowNotFoundError),
        match=expected_error,
    ):
        prepare_bulk_planned_group_edit(request, workspace_root=root)
    assert _history(root) == before


def test_changed_review_digest_and_stale_snapshot_refuse(tmp_path: Path) -> None:
    root, snapshot, record = _setup(tmp_path)
    request = _request(snapshot, record)
    reviewed = prepare_bulk_planned_group_edit(request, workspace_root=root)
    before = _history(root)
    with pytest.raises(ConcordWorkflowConflictError, match="review"):
        commit_bulk_planned_group_edit(
            request, workspace_root=root, review_digest="0" * 64
        )
    assert _history(root) == before
    with pytest.raises(ConcordWorkflowConflictError, match="revision"):
        prepare_bulk_planned_group_edit(
            _request(snapshot, record + 1), workspace_root=root
        )
    assert _history(root) == before
    commit_bulk_planned_group_edit(
        request, workspace_root=root, review_digest=reviewed.review_digest
    )
    with pytest.raises(ConcordWorkflowConflictError, match="snapshot"):
        commit_bulk_planned_group_edit(
            request, workspace_root=root, review_digest=reviewed.review_digest
        )


def test_core_roster_drift_refuses_without_implicit_refresh(tmp_path: Path) -> None:
    root, snapshot, record = _setup(tmp_path)
    request = _request(snapshot, record)
    reviewed = prepare_bulk_planned_group_edit(request, workspace_root=root)
    before = _history(root)
    write_class_roster(
        root, _roster("student-1", "student-2", "student-4"), overwrite=True
    )
    with pytest.raises(ConcordWorkflowConflictError, match="Core roster"):
        commit_bulk_planned_group_edit(
            request, workspace_root=root, review_digest=reviewed.review_digest
        )
    assert _history(root) == before


def test_previewed_plan_bulk_edit_returns_to_draft(tmp_path: Path) -> None:
    root, snapshot, record = _setup(tmp_path)
    preview = preview_group_plan(
        PreviewGroupPlanRequest(
            class_id="class-1", activity_id="activity-1",
            group_plan_id="plan-1", expected_snapshot_revision=snapshot,
            actor=_actor(),
        ), workspace_root=root,
    )
    assert preview.plan.status == "previewed"
    request = _request(preview.summary.snapshot_revision, record + 1)
    reviewed = prepare_bulk_planned_group_edit(request, workspace_root=root)
    saved = commit_bulk_planned_group_edit(
        request, review_digest=reviewed.review_digest, workspace_root=root
    )
    assert saved.detail.plan.status == "draft"
    assert saved.detail.plan.approved_provenance is None


def test_canonical_write_rechecks_roster_during_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, snapshot, record = _setup(tmp_path)
    request = _request(snapshot, record)
    reviewed = prepare_bulk_planned_group_edit(request, workspace_root=root)
    before = _history(root)
    original = manual._replace_preserving_origin

    def changed_core_before_service(*args, **kwargs):
        write_class_roster(
            root, _roster("student-1", "student-2", "student-4"), overwrite=True
        )
        return original(*args, **kwargs)

    monkeypatch.setattr(
        manual, "_replace_preserving_origin", changed_core_before_service
    )
    with pytest.raises(ConcordWorkflowConflictError, match="Core roster"):
        commit_bulk_planned_group_edit(
            request, workspace_root=root, review_digest=reviewed.review_digest
        )
    assert _history(root) == before
