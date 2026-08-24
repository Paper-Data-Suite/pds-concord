from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.classes import write_class_roster
from pds_core.grouping_signal_storage import write_grouping_signal
from pds_core.grouping_signals import (
    GroupingSignalDimension,
    GroupingSignalSet,
    GroupingSignalSource,
    GroupingSignalStudentBand,
)
from pds_core.rosters import create_roster
from pds_core.routing_models import ModuleRecordRef
from pds_core.workspace import ensure_workspace_root

from concord.models import (
    ActorReference,
    EffectiveContext,
    GroupPlan,
    PlannedGroup,
    Provenance,
)
from concord.storage import (
    commit_record_batch,
    list_record_revisions,
    list_work_snapshots,
    load_current_record_graph,
    load_record_revision,
)
from concord.workflows import (
    ApplyGroupPlanRequest,
    CreateActivityContextRequest,
    CreateGroupRequest,
    CreateSessionRequest,
    PrepareGroupPlanApplicationRequest,
    WorkflowActor,
    apply_group_plan,
    create_activity_context,
    create_group,
    create_session,
    prepare_group_plan_application,
    select_grouping_signal_dimension,
)
from concord.workflows._collaboration import work_ref
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowValidationError,
)


def _clock(day: int) -> datetime:
    return datetime(2026, 8, day, 16, 0, tzinfo=timezone.utc)


def _provenance(day: int, actor_id: str = "teacher-plan") -> Provenance:
    return Provenance(
        actor=ActorReference(
            actor_kind="authorized_adult",
            actor_id=actor_id,
            owning_system="concord",
        ),
        timestamp=_clock(day).isoformat(),
        source_kind="manual",
        application_version="0.3.0.dev0",
    )


def _actor(actor_id: str) -> WorkflowActor:
    return WorkflowActor(
        actor_id=actor_id,
        display_label="Synthetic Teacher",
        role_label="teacher",
    )


def _roster(*student_ids: str):
    return create_roster(
        "class-1",
        tuple(
            {
                "student_id": student_id,
                "last_name": f"Last-{index}",
                "first_name": f"First-{index}",
                "period": "1",
            }
            for index, student_id in enumerate(student_ids, start=1)
        ),
    )


def _workspace(
    tmp_path: Path,
    *,
    name: str = "workspace",
    second_session: bool = False,
) -> tuple[Path, int]:
    root = ensure_workspace_root(tmp_path / name)
    write_class_metadata_for_class(
        root,
        create_class_metadata("class-1", "2026-2027", created_at=_clock(1)),
    )
    write_class_roster(root, _roster("student-1", "student-2", "student-3"))
    created = create_activity_context(
        CreateActivityContextRequest(
            class_id="class-1",
            activity_id="activity-1",
            title="Atomic Application Activity",
            activity_type="project",
            scoring_orientation="evidence_only",
            session_id="session-1",
            actor=_actor("teacher-create"),
        ),
        workspace_root=root,
        clock=lambda: _clock(2),
    )
    revision = created.commit.snapshot_revision
    if second_session:
        added = create_session(
            CreateSessionRequest(
                class_id="class-1",
                activity_id="activity-1",
                session_id="session-2",
                sequence=2,
                expected_snapshot_revision=revision,
                actor=_actor("teacher-session"),
            ),
            workspace_root=root,
            clock=lambda: _clock(3),
        )
        revision = added.commit.snapshot_revision
    return root, revision


def _context(session_id: str = "session-1") -> EffectiveContext:
    return EffectiveContext(
        activity_id="activity-1",
        session_ids=(session_id,),
    )


def _approved_plan() -> GroupPlan:
    return GroupPlan(
        group_plan_id="plan-1",
        activity_id="activity-1",
        class_reference=ModuleRecordRef(
            module_id="core",
            record_kind="class",
            record_id="class-1",
        ),
        strategy="manual",
        status="approved",
        roster_student_ids=("student-1", "student-2", "student-3"),
        proposed_groups=(
            PlannedGroup(
                planned_group_key="group-a",
                label="Group A",
                student_ids=("student-1",),
                description="Uses explicit context",
                effective_context=_context(),
            ),
            PlannedGroup(
                planned_group_key="group-b",
                label="Group B",
                student_ids=("student-2", "student-3"),
            ),
            PlannedGroup(
                planned_group_key="empty-group",
                label="Empty Group",
                student_ids=(),
            ),
        ),
        unresolved_student_ids=(),
        created_provenance=_provenance(2),
        previewed_provenance=_provenance(3),
        approved_provenance=_provenance(4),
    )


def _commit_plan(root: Path, revision: int, plan: GroupPlan) -> int:
    result = commit_record_batch(
        root,
        work_ref("class-1", "activity-1"),
        (plan,),
        expected_snapshot_revision=revision,
    )
    return result.snapshot_revision


def _preview(
    root: Path,
    *,
    fallback: EffectiveContext | None = None,
    application_id: str = "apply-atomic-1",
):
    return prepare_group_plan_application(
        PrepareGroupPlanApplicationRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-1",
            application_id=application_id,
            fallback_effective_context=fallback,
        ),
        workspace_root=root,
    )


def _apply_request(
    preview,
    *,
    fallback: EffectiveContext | None = None,
    digest: str | None = None,
) -> ApplyGroupPlanRequest:
    return ApplyGroupPlanRequest(
        class_id="class-1",
        activity_id="activity-1",
        group_plan_id="plan-1",
        application_id=preview.application_id,
        application_digest=(preview.application_digest if digest is None else digest),
        expected_snapshot_revision=preview.expected_snapshot_revision,
        actor=_actor("teacher-apply"),
        fallback_effective_context=fallback,
    )


def test_apply_commits_groups_memberships_and_terminal_plan_once(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    _commit_plan(root, revision, _approved_plan())
    preview = _preview(root, fallback=_context())
    work = work_ref("class-1", "activity-1")
    snapshots_before = list_work_snapshots(root, work)

    result = apply_group_plan(
        _apply_request(preview, fallback=_context()),
        workspace_root=root,
        clock=lambda: _clock(6),
    )

    assert result.status == "applied"
    assert result.application_id == preview.application_id
    assert result.application_digest == preview.application_digest
    assert result.group_count == 3
    assert result.membership_count == 3
    assert result.unresolved_count == 0
    assert result.commit.snapshot_revision == preview.expected_snapshot_revision + 1
    assert list_work_snapshots(root, work) == (
        *snapshots_before,
        result.commit.snapshot_revision,
    )

    graph = load_current_record_graph(root, work).graph
    assert len(graph.groups) == 3
    assert len(graph.memberships) == 3
    applied = graph.group_plans[0]
    assert applied.status == "applied"
    assert applied.applied_application_id == preview.application_id
    assert applied.applied_application_digest == preview.application_digest
    assert applied.applied_provenance is not None
    assert applied.applied_provenance.actor.actor_id == "teacher-apply"

    assert set(result.group_ids) == {item.group_id for item in preview.groups}
    assert set(result.membership_ids) == {
        item.membership_id for item in preview.memberships
    }
    assert {group.status for group in graph.groups} == {"planned"}
    assert {membership.status for membership in graph.memberships} == {"active"}
    assert {group.created_provenance for group in graph.groups} == {
        applied.applied_provenance
    }
    assert {membership.created_provenance for membership in graph.memberships} == {
        applied.applied_provenance
    }

    by_label = {group.label: group for group in graph.groups}
    assert by_label["Group A"].effective_context == _context()
    assert by_label["Group B"].effective_context is None
    assert by_label["Empty Group"].effective_context is None
    empty_id = by_label["Empty Group"].group_id
    assert not any(item.group_id == empty_id for item in graph.memberships)

    group_b_id = by_label["Group B"].group_id
    group_b_members = tuple(
        item for item in graph.memberships if item.group_id == group_b_id
    )
    assert {item.participant_reference.participant_id for item in group_b_members} == {
        "student-2",
        "student-3",
    }
    assert {item.effective_context for item in group_b_members} == {_context()}

    assert list_record_revisions(root, work, "group_plan", "plan-1") == (1, 2)
    approved, approved_envelope = load_record_revision(
        root,
        work,
        "group_plan",
        "plan-1",
        1,
    )
    terminal, terminal_envelope = load_record_revision(
        root,
        work,
        "group_plan",
        "plan-1",
        2,
    )
    assert isinstance(approved, GroupPlan)
    assert isinstance(terminal, GroupPlan)
    assert approved.status == "approved"
    assert approved.applied_application_id is None
    assert terminal.status == "applied"
    assert approved_envelope.record_revision == 1
    assert terminal_envelope.record_revision == 2


def test_digest_mismatch_writes_nothing(tmp_path: Path) -> None:
    root, revision = _workspace(tmp_path)
    _commit_plan(root, revision, _approved_plan())
    preview = _preview(root, fallback=_context())
    work = work_ref("class-1", "activity-1")
    snapshots_before = list_work_snapshots(root, work)

    with pytest.raises(ConcordWorkflowConflictError, match="digest"):
        apply_group_plan(
            _apply_request(
                preview,
                fallback=_context(),
                digest="0" * 64,
            ),
            workspace_root=root,
        )

    graph = load_current_record_graph(root, work).graph
    assert list_work_snapshots(root, work) == snapshots_before
    assert graph.group_plans[0].status == "approved"
    assert graph.groups == ()
    assert graph.memberships == ()


def test_invalid_digest_shape_is_rejected_before_write(tmp_path: Path) -> None:
    root, revision = _workspace(tmp_path)
    _commit_plan(root, revision, _approved_plan())
    preview = _preview(root, fallback=_context())
    work = work_ref("class-1", "activity-1")
    snapshots_before = list_work_snapshots(root, work)

    with pytest.raises(ConcordWorkflowValidationError, match="SHA-256"):
        apply_group_plan(
            _apply_request(preview, fallback=_context(), digest="BAD"),
            workspace_root=root,
        )

    assert list_work_snapshots(root, work) == snapshots_before


def test_activity_change_after_preview_causes_stale_conflict(tmp_path: Path) -> None:
    root, revision = _workspace(tmp_path)
    _commit_plan(root, revision, _approved_plan())
    preview = _preview(root, fallback=_context())
    create_group(
        CreateGroupRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_id="unrelated-group",
            label="Unrelated",
            expected_snapshot_revision=preview.expected_snapshot_revision,
            actor=_actor("teacher-other"),
        ),
        workspace_root=root,
    )
    work = work_ref("class-1", "activity-1")
    snapshots_before_apply = list_work_snapshots(root, work)

    with pytest.raises(ConcordWorkflowConflictError, match="changed since"):
        apply_group_plan(
            _apply_request(preview, fallback=_context()),
            workspace_root=root,
        )

    graph = load_current_record_graph(root, work).graph
    assert list_work_snapshots(root, work) == snapshots_before_apply
    assert graph.group_plans[0].status == "approved"
    assert {group.group_id for group in graph.groups} == {"unrelated-group"}
    assert graph.memberships == ()


def test_changed_fallback_context_breaks_preview_digest(tmp_path: Path) -> None:
    root, revision = _workspace(tmp_path, second_session=True)
    _commit_plan(root, revision, _approved_plan())
    preview = _preview(root, fallback=_context("session-1"))
    work = work_ref("class-1", "activity-1")
    snapshots_before = list_work_snapshots(root, work)

    with pytest.raises(ConcordWorkflowConflictError, match="digest"):
        apply_group_plan(
            _apply_request(preview, fallback=_context("session-2")),
            workspace_root=root,
        )

    graph = load_current_record_graph(root, work).graph
    assert list_work_snapshots(root, work) == snapshots_before
    assert graph.groups == ()
    assert graph.memberships == ()
    assert graph.group_plans[0].status == "approved"


def test_roster_change_after_preview_fails_closed_without_write(tmp_path: Path) -> None:
    root, revision = _workspace(tmp_path)
    _commit_plan(root, revision, _approved_plan())
    preview = _preview(root, fallback=_context())
    write_class_roster(
        root,
        _roster("student-1", "student-2", "student-3", "student-4"),
        overwrite=True,
    )
    work = work_ref("class-1", "activity-1")
    snapshots_before = list_work_snapshots(root, work)

    with pytest.raises(ConcordWorkflowConflictError, match="Core roster changed"):
        apply_group_plan(
            _apply_request(preview, fallback=_context()),
            workspace_root=root,
        )

    graph = load_current_record_graph(root, work).graph
    assert list_work_snapshots(root, work) == snapshots_before
    assert graph.group_plans[0].status == "approved"
    assert graph.groups == ()
    assert graph.memberships == ()


def test_second_application_is_rejected_without_another_snapshot(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    _commit_plan(root, revision, _approved_plan())
    preview = _preview(root, fallback=_context())
    request = _apply_request(preview, fallback=_context())
    first = apply_group_plan(
        request,
        workspace_root=root,
        clock=lambda: _clock(6),
    )
    work = work_ref("class-1", "activity-1")
    snapshots_after_first = list_work_snapshots(root, work)

    with pytest.raises(ConcordWorkflowConflictError, match="already been applied"):
        apply_group_plan(request, workspace_root=root)

    assert list_work_snapshots(root, work) == snapshots_after_first
    assert snapshots_after_first[-1] == first.commit.snapshot_revision


def _signal() -> GroupingSignalSet:
    return GroupingSignalSet(
        schema_version="1",
        record_type="grouping_signal_set",
        signal_set_id="signal-1",
        class_id="class-1",
        created_at=_clock(3),
        source=GroupingSignalSource(
            kind="module_generated",
            module_id="synthetic_module",
            snapshot_id="snapshot-1",
            snapshot_digest_algorithm="sha256",
            snapshot_digest="b" * 64,
        ),
        dimensions=(
            GroupingSignalDimension(
                dimension_id="collaboration",
                band_count=4,
            ),
        ),
        student_bands=(
            GroupingSignalStudentBand(
                student_id="student-1",
                dimension_id="collaboration",
                band=1,
            ),
            GroupingSignalStudentBand(
                student_id="student-2",
                dimension_id="collaboration",
                band=3,
            ),
        ),
    )


def _leave_unassigned_plan(digest: str) -> GroupPlan:
    return GroupPlan(
        group_plan_id="plan-1",
        activity_id="activity-1",
        class_reference=ModuleRecordRef(
            module_id="core",
            record_kind="class",
            record_id="class-1",
        ),
        strategy="similar_signal",
        status="approved",
        roster_student_ids=("student-1", "student-2", "student-3"),
        proposed_groups=(
            PlannedGroup(
                planned_group_key="similar-1",
                label="Signal Group",
                student_ids=("student-1", "student-2"),
            ),
        ),
        unresolved_student_ids=("student-3",),
        target_group_count=1,
        source_signal_set_id="signal-1",
        source_signal_set_digest=digest,
        source_signal_dimension_id="collaboration",
        missing_signal_disposition="leave_unassigned",
        missing_signal_disposition_provenance=_provenance(3),
        created_provenance=_provenance(2),
        previewed_provenance=_provenance(3),
        approved_provenance=_provenance(4),
    )


def test_leave_unassigned_applies_only_proposed_memberships(tmp_path: Path) -> None:
    root, revision = _workspace(tmp_path)
    signal = _signal()
    write_grouping_signal(root, signal)
    selection = select_grouping_signal_dimension(
        "class-1",
        "signal-1",
        "collaboration",
        workspace_root=root,
    )
    _commit_plan(root, revision, _leave_unassigned_plan(selection.digest))
    preview = _preview(root, fallback=_context())

    result = apply_group_plan(
        _apply_request(preview, fallback=_context()),
        workspace_root=root,
        clock=lambda: _clock(6),
    )

    graph = load_current_record_graph(
        root,
        work_ref("class-1", "activity-1"),
    ).graph
    assert result.group_count == 1
    assert result.membership_count == 2
    assert result.unresolved_count == 1
    assert graph.group_plans[0].status == "applied"
    assert graph.group_plans[0].unresolved_student_ids == ("student-3",)
    membership_student_ids = {
        item.participant_reference.participant_id for item in graph.memberships
    }
    assert membership_student_ids == {"student-1", "student-2"}
