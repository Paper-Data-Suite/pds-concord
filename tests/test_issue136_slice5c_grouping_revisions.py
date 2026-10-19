"""Synthetic #136 saved-grouping revision lifecycle; no real student data."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.classes import write_class_roster
from pds_core.rosters import create_roster
from pds_core.workspace import ensure_workspace_root

from concord.class_group_arrangement_storage import (
    ArrangementConflictError,
    create_arrangement,
    load_current_arrangement,
)
from concord.class_group_arrangements import (
    SavedArrangementGroup,
    SavedArrangementRevision,
)
from concord.models import PlannedGroup
from concord.workflows import (
    CreateActivityContextRequest,
    CreateManualGroupPlanRequest,
    WorkflowActor,
    create_activity_context,
    create_manual_group_plan,
    show_activity,
    show_group_plan,
)
from concord.workflows.class_group_arrangement_revision import (
    ChangeGroupingRequest,
    change_grouping,
    prepare_grouping_change,
)
from concord.workflows.class_group_arrangements import (
    ReuseGroupingRequest,
    prepare_reuse_grouping,
)
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowValidationError,
)

CLASS = "class-1"
YEAR = "2026-2027"
ACTOR = WorkflowActor(actor_id="teacher-1")
IDS = tuple(f"student-{i:02}" for i in range(1, 30))


def _roster(ids: tuple[str, ...]):
    return create_roster(
        CLASS,
        tuple(
            {
                "student_id": sid,
                "first_name": "Synthetic",
                "last_name": f"Student-{i}",
                "period": "1",
            }
            for i, sid in enumerate(ids, 1)
        ),
    )


def _root(tmp_path: Path) -> Path:
    root = ensure_workspace_root(tmp_path / "pds")
    write_class_metadata_for_class(
        root,
        create_class_metadata(
            CLASS, YEAR, created_at=datetime(2026, 9, 1, tzinfo=timezone.utc)
        ),
    )
    write_class_roster(root, _roster(IDS))
    return root


def _groups() -> tuple[SavedArrangementGroup, ...]:
    return tuple(
        SavedArrangementGroup(
            key=f"table-{number}",
            label=f"Table {number}",
            student_ids=tuple(s for i, s in enumerate(IDS) if i % 6 == number - 1),
        )
        for number in range(1, 7)
    )


def _create(root: Path):
    return create_arrangement(
        root,
        SavedArrangementRevision(
            arrangement_id="tables-six",
            class_id=CLASS,
            school_year=YEAR,
            revision=1,
            name="Six Tables",
            owner_actor_id=ACTOR.actor_id,
            created_by_actor_id=ACTOR.actor_id,
            created_at="2026-10-17T22:00:00-04:00",
            groups=_groups(),
            roster_student_ids=IDS,
        ),
        actor_id=ACTOR.actor_id,
    )


def _request(saved, *, action: str, **kw: object) -> ChangeGroupingRequest:
    return ChangeGroupingRequest(
        class_id=CLASS,
        arrangement_id="tables-six",
        expected_revision=saved.revision.revision,
        expected_sha256=saved.sha256,
        actor=ACTOR,
        action=action,
        **kw,
    )


def _current(root: Path):
    return load_current_arrangement(
        root,
        class_id=CLASS,
        school_year=YEAR,
        arrangement_id="tables-six",
        actor_id=ACTOR.actor_id,
    )


def _commit(root: Path, request: ChangeGroupingRequest):
    preview = prepare_grouping_change(request, workspace_root=root)
    result = change_grouping(
        request, review_digest=preview.review_digest, workspace_root=root
    )
    return preview, result


def _plan(root: Path) -> int:
    created = create_activity_context(
        CreateActivityContextRequest(
            class_id=CLASS,
            activity_id="source-activity",
            title="Synthetic Six Tables",
            activity_type="project",
            scoring_orientation="evidence_only",
            session_id="session-source-1",
            actor=ACTOR,
        ),
        workspace_root=root,
    )
    groups = tuple(
        PlannedGroup(
            planned_group_key=group.key,
            label=f"Revised {group.label}",
            student_ids=group.student_ids,
        )
        for group in _groups()
    )
    plan = create_manual_group_plan(
        CreateManualGroupPlanRequest(
            class_id=CLASS,
            activity_id="source-activity",
            group_plan_id="plan-six",
            expected_snapshot_revision=created.commit.snapshot_revision,
            actor=ACTOR,
            proposed_groups=groups,
        ),
        workspace_root=root,
    )
    return plan.commit.snapshot_revision


def test_rename_appends_history_without_touching_activity(tmp_path: Path) -> None:
    root = _root(tmp_path)
    first = _create(root)
    before = first.revision
    preview, second = _commit(
        root, _request(first, action="rename", new_name="Six Discussion Tables")
    )
    assert preview.new_revision == 2
    assert second.revision.revision == 2
    assert second.revision.name == "Six Discussion Tables"
    assert second.revision.groups == before.groups
    assert second.revision.predecessor_sha256 == first.sha256
    assert first.revision.name == "Six Tables"
    revision_path = (
        root
        / "shared"
        / "concord"
        / "class-group-arrangements"
        / YEAR
        / CLASS
        / "tables-six"
        / "revisions"
        / "00000001.json"
    )
    assert revision_path.is_file()
    assert _current(root) == second
    assert not (root / "classes" / CLASS / "work").exists()


def test_replace_from_editable_plan_creates_fresh_revision_only(tmp_path: Path) -> None:
    root = _root(tmp_path)
    first = _create(root)
    revision = _plan(root)
    summary_before = show_activity(
        CLASS, "source-activity", workspace_root=root
    ).summary
    plan_before = show_group_plan(
        CLASS, "source-activity", "plan-six", workspace_root=root
    )
    request = _request(
        first,
        action="replace_from_plan",
        source_activity_id="source-activity",
        source_group_plan_id="plan-six",
        expected_source_snapshot_revision=revision,
    )
    preview, second = _commit(root, request)
    assert preview.assigned_count == 29
    assert len(second.revision.groups) == 6
    assert second.revision.groups[0].label == "Revised Table 1"
    assert second.revision.revision == 2
    assert second.revision.predecessor_sha256 == first.sha256
    assert _current(root) == second
    assert (
        show_activity(CLASS, "source-activity", workspace_root=root).summary
        == summary_before
    )
    assert (
        show_group_plan(CLASS, "source-activity", "plan-six", workspace_root=root)
        == plan_before
    )


def test_retire_is_terminal_and_cannot_be_reused(tmp_path: Path) -> None:
    root = _root(tmp_path)
    first = _create(root)
    preview, retired = _commit(root, _request(first, action="retire"))
    assert preview.status == "retired"
    assert retired.revision.status == "retired"
    assert retired.revision.groups == first.revision.groups
    activity = create_activity_context(
        CreateActivityContextRequest(
            class_id=CLASS,
            activity_id="reuse-target",
            title="Synthetic Reuse Target",
            activity_type="project",
            scoring_orientation="evidence_only",
            session_id="reuse-session-1",
            actor=ACTOR,
        ),
        workspace_root=root,
    )
    with pytest.raises(ConcordWorkflowConflictError, match="retired"):
        prepare_reuse_grouping(
            ReuseGroupingRequest(
                class_id=CLASS,
                activity_id="reuse-target",
                arrangement_id="tables-six",
                new_group_plan_id="target-plan",
                expected_snapshot_revision=activity.commit.snapshot_revision,
                actor=ACTOR,
            ),
            workspace_root=root,
        )
    with pytest.raises(ArrangementConflictError, match="Retired"):
        prepare_grouping_change(
            _request(retired, action="rename", new_name="Resurrected"),
            workspace_root=root,
        )
    with pytest.raises(ArrangementConflictError, match="Retired"):
        prepare_grouping_change(_request(retired, action="retire"), workspace_root=root)


def test_stale_revision_and_review_digest_preserve_old_pointer(tmp_path: Path) -> None:
    root = _root(tmp_path)
    first = _create(root)
    request = _request(first, action="rename", new_name="Updated")
    preview = prepare_grouping_change(request, workspace_root=root)
    with pytest.raises(ConcordWorkflowConflictError, match="review changed"):
        change_grouping(request, review_digest="f" * 64, workspace_root=root)
    assert _current(root) == first
    second = change_grouping(
        request, review_digest=preview.review_digest, workspace_root=root
    )
    assert second.revision.revision == 2
    with pytest.raises(ArrangementConflictError, match="changed"):
        change_grouping(
            request, review_digest=preview.review_digest, workspace_root=root
        )
    assert _current(root) == second


def test_wrong_teacher_cannot_preview_or_modify(tmp_path: Path) -> None:
    root = _root(tmp_path)
    first = _create(root)
    request = replace(
        _request(first, action="rename", new_name="Unauthorized"),
        actor=WorkflowActor(actor_id="teacher-2"),
    )
    with pytest.raises(ArrangementConflictError, match="owning teacher"):
        prepare_grouping_change(request, workspace_root=root)
    assert _current(root) == first


def test_rename_and_retire_are_allowed_after_roster_drift(tmp_path: Path) -> None:
    root = _root(tmp_path)
    first = _create(root)
    write_class_roster(root, _roster(IDS[:-1] + ("student-30",)), overwrite=True)
    _, renamed = _commit(
        root, _request(first, action="rename", new_name="Old Roster Arrangement")
    )
    assert renamed.revision.roster_student_ids == IDS
    _, retired = _commit(root, _request(renamed, action="retire"))
    assert retired.revision.status == "retired"
    assert _current(root) == retired


def test_stale_source_snapshot_is_rejected_before_storage_write(tmp_path: Path) -> None:
    root = _root(tmp_path)
    first = _create(root)
    revision = _plan(root)
    request = _request(
        first,
        action="replace_from_plan",
        source_activity_id="source-activity",
        source_group_plan_id="plan-six",
        expected_source_snapshot_revision=revision + 1,
    )
    with pytest.raises(ConcordWorkflowConflictError, match="Source Activity changed"):
        prepare_grouping_change(request, workspace_root=root)
    assert _current(root) == first


def test_invalid_or_noop_actions_fail_before_writes(tmp_path: Path) -> None:
    root = _root(tmp_path)
    first = _create(root)
    for request in (
        _request(first, action="rename", new_name="Six Tables"),
        _request(first, action="retire", new_name="Invalid"),
        _request(first, action="rename"),
        _request(first, action="replace_from_plan"),
        _request(first, action="unknown"),
    ):
        with pytest.raises(
            (ConcordWorkflowValidationError, ConcordWorkflowConflictError)
        ):
            prepare_grouping_change(request, workspace_root=root)
    assert _current(root) == first


def test_replacement_requires_current_roster(tmp_path: Path) -> None:
    root = _root(tmp_path)
    first = _create(root)
    revision = _plan(root)
    write_class_roster(root, _roster(IDS[:-1] + ("student-30",)), overwrite=True)
    request = _request(
        first,
        action="replace_from_plan",
        source_activity_id="source-activity",
        source_group_plan_id="plan-six",
        expected_source_snapshot_revision=revision,
    )
    with pytest.raises(ConcordWorkflowConflictError, match="Core class roster changed"):
        prepare_grouping_change(request, workspace_root=root)
    assert _current(root) == first
