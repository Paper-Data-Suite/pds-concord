"""Synthetic operational Group -> reusable grouping tests for Concord #136."""

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
    list_current_arrangements,
    load_current_arrangement,
)
from concord.models import EffectiveContext
from concord.workflows import (
    CreateActivityContextRequest,
    CreateGroupWithMembersRequest,
    EndMembershipRequest,
    GroupMemberSpec,
    WorkflowActor,
    create_activity_context,
    create_group_with_members,
    end_membership,
    list_groups,
    show_activity,
)
from concord.workflows.class_group_arrangement_operational import (
    SaveOperationalGroupingRequest,
    prepare_save_operational_grouping,
    save_operational_grouping,
)
from concord.workflows.class_group_arrangements import (
    ReuseGroupingRequest,
    prepare_reuse_grouping,
    reuse_grouping,
)
from concord.workflows.errors import ConcordWorkflowConflictError

ACTOR = WorkflowActor(actor_id="teacher-1")
CLASS = "class-1"
YEAR = "2026-2027"
SOURCE = "source-activity"
TARGET = "target-activity"
SESSION = "source-session-1"
STUDENTS = tuple(f"student-{n:02d}" for n in range(1, 30))


def _setup(root_path: Path) -> tuple[Path, int, int]:
    root = ensure_workspace_root(root_path / "workspace")
    write_class_metadata_for_class(
        root,
        create_class_metadata(
            CLASS,
            YEAR,
            created_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
        ),
    )
    write_class_roster(
        root,
        create_roster(
            CLASS,
            tuple(
                {
                    "student_id": sid,
                    "first_name": "Synthetic",
                    "last_name": f"Learner-{n}",
                    "period": "1",
                }
                for n, sid in enumerate(STUDENTS, 1)
            ),
        ),
    )
    revs: list[int] = []
    for activity_id in (SOURCE, TARGET):
        created = create_activity_context(
            CreateActivityContextRequest(
                class_id=CLASS,
                activity_id=activity_id,
                title=f"Synthetic {activity_id}",
                activity_type="project",
                scoring_orientation="evidence_only",
                session_id=f"{activity_id.removesuffix('-activity')}-session-1",
                actor=ACTOR,
            ),
            workspace_root=root,
        )
        revs.append(created.commit.snapshot_revision)
    return root, revs[0], revs[1]


def _install_groups(
    root: Path, revision: int, *, missing: tuple[str, ...] = (), overlap: bool = False
) -> int:
    for n in range(1, 7):
        selected = tuple(
            sid
            for pos, sid in enumerate(STUDENTS)
            if pos % 6 == n - 1 and sid not in missing
        )
        if overlap and n == 2:
            selected = (*selected, "student-01")
        result = create_group_with_members(
            CreateGroupWithMembersRequest(
                class_id=CLASS,
                activity_id=SOURCE,
                group_id=f"operational-private-{n}",
                label=f"Table {n}",
                description=f"Group description {n}",
                expected_snapshot_revision=revision,
                actor=ACTOR,
                status="active",
                members=tuple(
                    GroupMemberSpec(
                        membership_id=f"membership-{n}-{sid}",
                        student_id=sid,
                        effective_context=EffectiveContext(
                            activity_id=SOURCE, session_ids=(SESSION,)
                        ),
                    )
                    for sid in selected
                ),
            ),
            workspace_root=root,
        )
        revision = result.commit.snapshot_revision
    return revision


def _request(revision: int, **changes: object) -> SaveOperationalGroupingRequest:
    return replace(
        SaveOperationalGroupingRequest(
            class_id=CLASS,
            activity_id=SOURCE,
            session_id=SESSION,
            arrangement_id="saved-six-tables",
            name="Six Table Groups",
            expected_snapshot_revision=revision,
            actor=ACTOR,
        ),
        **changes,
    )


def _save(root: Path, request: SaveOperationalGroupingRequest):
    preview = prepare_save_operational_grouping(request, workspace_root=root)
    return save_operational_grouping(
        request, workspace_root=root, review_digest=preview.review_digest
    )


def test_exact_six_groups_29_students_save_and_reuse(tmp_path: Path) -> None:
    root, src_rev, target_rev = _setup(tmp_path)
    src_rev = _install_groups(root, src_rev)
    request = _request(src_rev)
    source_before = show_activity(CLASS, SOURCE, workspace_root=root).summary
    preview = prepare_save_operational_grouping(request, workspace_root=root)
    assert len(preview.groups) == 6
    assert preview.assigned_count == 29
    assert preview.unresolved_student_ids == ()
    assert all(group.key.startswith("saved-group-") for group in preview.groups)
    assert not any("operational-private" in group.key for group in preview.groups)
    assert (
        list_current_arrangements(
            root, class_id=CLASS, school_year=YEAR, actor_id=ACTOR.actor_id
        )
        == ()
    )
    saved = _save(root, request)
    assert saved.revision.groups[0].description == "Group description 1"
    assert sum(len(group.student_ids) for group in saved.revision.groups) == 29
    assert show_activity(CLASS, SOURCE, workspace_root=root).summary == source_before
    assert len(list_groups(CLASS, SOURCE, workspace_root=root)) == 6
    target_request = ReuseGroupingRequest(
        class_id=CLASS,
        activity_id=TARGET,
        arrangement_id=request.arrangement_id,
        new_group_plan_id="fresh-plan",
        expected_snapshot_revision=target_rev,
        actor=ACTOR,
    )
    target_preview = prepare_reuse_grouping(target_request, workspace_root=root)
    assert target_preview.assigned_count == 29
    result = reuse_grouping(
        target_request, workspace_root=root, review_digest=target_preview.review_digest
    )
    assert result.status == "draft"
    assert list_groups(CLASS, TARGET, workspace_root=root) == ()
    assert (
        load_current_arrangement(
            root,
            class_id=CLASS,
            school_year=YEAR,
            arrangement_id=request.arrangement_id,
            actor_id=ACTOR.actor_id,
        )
        == saved
    )


def test_preview_never_writes_and_wrong_digest_rejected(tmp_path: Path) -> None:
    root, revision, _ = _setup(tmp_path)
    revision = _install_groups(root, revision)
    request = _request(revision)
    prepare_save_operational_grouping(request, workspace_root=root)
    assert (
        list_current_arrangements(
            root, class_id=CLASS, school_year=YEAR, actor_id=ACTOR.actor_id
        )
        == ()
    )
    with pytest.raises(ConcordWorkflowConflictError, match="preview changed"):
        save_operational_grouping(request, review_digest="0" * 64, workspace_root=root)


def test_missing_student_needs_explicit_acknowledgment(tmp_path: Path) -> None:
    root, revision, _ = _setup(tmp_path)
    revision = _install_groups(root, revision, missing=("student-29",))
    request = _request(revision)
    preview = prepare_save_operational_grouping(request, workspace_root=root)
    assert preview.unresolved_student_ids == ("student-29",)
    with pytest.raises(ConcordWorkflowConflictError, match="acknowledge unresolved"):
        save_operational_grouping(
            request, review_digest=preview.review_digest, workspace_root=root
        )
    saved = save_operational_grouping(
        replace(request, acknowledge_unresolved=True),
        review_digest=preview.review_digest,
        workspace_root=root,
    )
    assert saved.revision.unresolved_student_ids == ("student-29",)


def test_double_membership_in_same_session_refuses_without_write(
    tmp_path: Path,
) -> None:
    root, revision, _ = _setup(tmp_path)
    revision = _install_groups(root, revision, overlap=True)
    with pytest.raises(ConcordWorkflowConflictError, match="multiple active"):
        prepare_save_operational_grouping(_request(revision), workspace_root=root)
    assert (
        list_current_arrangements(
            root, class_id=CLASS, school_year=YEAR, actor_id=ACTOR.actor_id
        )
        == ()
    )


def test_ended_membership_is_not_current_placement(tmp_path: Path) -> None:
    root, revision, _ = _setup(tmp_path)
    revision = _install_groups(root, revision)
    result = end_membership(
        EndMembershipRequest(
            class_id=CLASS,
            activity_id=SOURCE,
            membership_id="membership-1-student-01",
            expected_snapshot_revision=revision,
            actor=ACTOR,
            status="completed",
        ),
        workspace_root=root,
    )
    request = _request(result.commit.snapshot_revision)
    preview = prepare_save_operational_grouping(request, workspace_root=root)
    assert preview.unresolved_student_ids == ("student-01",)


def test_stale_activity_snapshot_rejected(tmp_path: Path) -> None:
    root, revision, _ = _setup(tmp_path)
    revision = _install_groups(root, revision)
    with pytest.raises(ConcordWorkflowConflictError, match="Source Activity changed"):
        prepare_save_operational_grouping(_request(revision - 1), workspace_root=root)


def test_selected_session_must_exist(tmp_path: Path) -> None:
    root, revision, _ = _setup(tmp_path)
    revision = _install_groups(root, revision)
    with pytest.raises(Exception, match="source Session"):
        prepare_save_operational_grouping(
            _request(revision, session_id="never-created"), workspace_root=root
        )


def test_no_operational_groups_rejected(tmp_path: Path) -> None:
    root, revision, _ = _setup(tmp_path)
    with pytest.raises(Exception, match="No operational Groups"):
        prepare_save_operational_grouping(_request(revision), workspace_root=root)


def test_different_actor_type_rejected(tmp_path: Path) -> None:
    root, revision, _ = _setup(tmp_path)
    revision = _install_groups(root, revision)
    with pytest.raises(Exception, match="authorized Concord teacher"):
        prepare_save_operational_grouping(
            _request(
                revision, actor=WorkflowActor(actor_id="user-1", actor_kind="system")
            ),
            workspace_root=root,
        )
