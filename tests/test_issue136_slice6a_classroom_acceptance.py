"""Issue #136 Slice 6A: synthetic six-table classroom acceptance.

Uses exact Core student identifiers. Nothing here accesses teacher workspace data,
creates scores, or publishes academic results.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.classes import write_class_roster
from pds_core.rosters import create_roster
from pds_core.routing_models import ModuleWorkRef
from pds_core.standards import StandardDefinition, StandardsLibrary, StandardsProfile
from pds_core.workspace import ensure_workspace_root

from concord.class_group_arrangement_storage import load_current_arrangement
from concord.model_validation import collect_record_graph_issues
from concord.models import EffectiveContext, PlannedGroup
from concord.storage import list_work_snapshots, load_current_record_graph
from concord.workflows import (
    ApplyGroupPlanRequest,
    ApproveGroupPlanRequest,
    CreateActivityContextRequest,
    CreateManualGroupPlanRequest,
    PrepareGroupPlanApplicationRequest,
    PreviewGroupPlanRequest,
    WorkflowActor,
    apply_group_plan,
    approve_group_plan,
    create_activity_context,
    create_manual_group_plan,
    prepare_group_plan_application,
    preview_group_plan,
    show_activity,
    show_group_plan,
)
from concord.workflows.class_group_arrangements import (
    ReuseGroupingRequest,
    SaveGroupingRequest,
    prepare_reuse_grouping,
    prepare_save_grouping,
    reuse_grouping,
    save_grouping,
)
from concord.workflows.errors import ConcordWorkflowConflictError

CLASS = "class-six-tables"
YEAR = "2026-2027"
SOURCE = "activity-source-discussion"
TARGET = "activity-new-discussion"
SAVED = "class-six-table-arrangement"
NEW_PLAN = "new-activity-six-table-plan"
STUDENTS = tuple(f"student-{i:02}" for i in range(1, 30))
ACTOR = WorkflowActor(actor_id="teacher-synthetic")


def _clock() -> datetime:
    return datetime(2026, 10, 18, 15, 0, tzinfo=timezone.utc)


def _standards() -> StandardsLibrary:
    return StandardsLibrary(
        standards=(
            StandardDefinition(
                standard_id="standard-synthetic-discussion",
                code="SYN.DISCUSS.1",
                source="synthetic",
                short_name="Synthetic discussion standard",
                description="Synthetic evidence of collaborative discussion.",
                available_modules=("concord",),
            ),
        ),
        profiles=(
            StandardsProfile(
                profile_id="profile-synthetic-discussion",
                standards=("standard-synthetic-discussion",),
                title="Synthetic discussion profile",
            ),
        ),
    )


def _setup(tmp_path: Path, orientation: str) -> tuple[Path, StandardsLibrary, int, int]:
    root = ensure_workspace_root(tmp_path / "workspace")
    write_class_metadata_for_class(
        root,
        create_class_metadata(CLASS, YEAR, created_at=_clock()),
    )
    write_class_roster(
        root,
        create_roster(
            CLASS,
            tuple(
                {
                    "student_id": student,
                    "first_name": "Synthetic",
                    "last_name": f"Learner{i:02}",
                    "period": "1",
                }
                for i, student in enumerate(STUDENTS, 1)
            ),
        ),
    )
    standards = _standards()
    revisions = []
    for activity_id in (SOURCE, TARGET):
        created = create_activity_context(
            CreateActivityContextRequest(
                class_id=CLASS,
                activity_id=activity_id,
                title=f"Synthetic {activity_id}",
                activity_type="project",
                scoring_orientation=orientation,
                standards_profile_id="profile-synthetic-discussion",
                focus_standard_ids=("standard-synthetic-discussion",),
                session_id=f"{activity_id}-session",
                actor=ACTOR,
            ),
            workspace_root=root,
            standards_library=standards,
        )
        revisions.append(created.commit.snapshot_revision)
    return root, standards, revisions[0], revisions[1]


def _planned() -> tuple[PlannedGroup, ...]:
    return tuple(
        PlannedGroup(
            planned_group_key=f"table-{i}",
            label=f"Table {i}",
            description=f"Synthetic table group {i}",
            student_ids=tuple(sid for n, sid in enumerate(STUDENTS) if n % 6 == i - 1),
        )
        for i in range(1, 7)
    )


def _saved_source(root: Path, standards: StandardsLibrary, source_revision: int) -> int:
    created = create_manual_group_plan(
        CreateManualGroupPlanRequest(
            class_id=CLASS,
            activity_id=SOURCE,
            group_plan_id="source-manual-plan",
            proposed_groups=_planned(),
            expected_snapshot_revision=source_revision,
            actor=ACTOR,
        ),
        workspace_root=root,
        standards_library=standards,
    )
    request = SaveGroupingRequest(
        class_id=CLASS,
        activity_id=SOURCE,
        group_plan_id="source-manual-plan",
        arrangement_id=SAVED,
        name="Six Synthetic Table Groups",
        expected_snapshot_revision=created.commit.snapshot_revision,
        actor=ACTOR,
    )
    before = list_work_snapshots(root, _work(SOURCE))
    preview = prepare_save_grouping(request, workspace_root=root)
    assert len(preview.groups) == 6
    assert preview.assigned_count == 29
    assert preview.unresolved_student_ids == ()
    assert list_work_snapshots(root, _work(SOURCE)) == before
    result = save_grouping(
        request, review_digest=preview.review_digest, workspace_root=root
    )
    assert result.revision.revision == 1
    assert len(result.revision.groups) == 6
    assert list_work_snapshots(root, _work(SOURCE)) == before
    return created.commit.snapshot_revision


def _work(activity: str) -> ModuleWorkRef:
    return ModuleWorkRef(module_id="concord", class_id=CLASS, work_id=activity)


@pytest.mark.parametrize("orientation", ("mixed", "standards_based"))
def test_29_students_six_saved_tables_reuse_preview_approve_apply(
    tmp_path: Path, orientation: str
) -> None:
    root, standards, source_revision, target_revision = _setup(tmp_path, orientation)
    source_revision = _saved_source(root, standards, source_revision)
    unchanged_source = show_activity(CLASS, SOURCE, workspace_root=root).summary
    saved_before = load_current_arrangement(
        root,
        class_id=CLASS,
        school_year=YEAR,
        arrangement_id=SAVED,
        actor_id=ACTOR.actor_id,
    )
    reuse = ReuseGroupingRequest(
        class_id=CLASS,
        activity_id=TARGET,
        arrangement_id=SAVED,
        new_group_plan_id=NEW_PLAN,
        expected_snapshot_revision=target_revision,
        actor=ACTOR,
    )
    original = list_work_snapshots(root, _work(TARGET))
    prepared = prepare_reuse_grouping(reuse, workspace_root=root)
    assert prepared.assigned_count == 29
    assert len(prepared.groups) == 6
    assert list_work_snapshots(root, _work(TARGET)) == original
    with pytest.raises(ConcordWorkflowConflictError):
        reuse_grouping(reuse, review_digest="0" * 64, workspace_root=root)
    assert list_work_snapshots(root, _work(TARGET)) == original
    draft = reuse_grouping(
        reuse,
        review_digest=prepared.review_digest,
        workspace_root=root,
        standards_library=standards,
    )
    assert draft.status == "draft"
    target_revision = draft.commit.snapshot_revision
    assert (
        show_group_plan(CLASS, TARGET, NEW_PLAN, workspace_root=root).plan.status
        == "draft"
    )
    draft_graph = load_current_record_graph(
        root, _work(TARGET), standards_library=standards
    ).graph
    assert draft_graph.groups == ()
    assert draft_graph.memberships == ()
    assert draft_graph.score_records == ()

    previewed = preview_group_plan(
        PreviewGroupPlanRequest(
            class_id=CLASS,
            activity_id=TARGET,
            group_plan_id=NEW_PLAN,
            expected_snapshot_revision=target_revision,
            actor=ACTOR,
        ),
        workspace_root=root,
        standards_library=standards,
    )
    assert previewed.plan.status == "previewed"
    approved = approve_group_plan(
        ApproveGroupPlanRequest(
            class_id=CLASS,
            activity_id=TARGET,
            group_plan_id=NEW_PLAN,
            expected_snapshot_revision=previewed.summary.snapshot_revision,
            actor=ACTOR,
        ),
        workspace_root=root,
        standards_library=standards,
    )
    assert approved.status == "approved"
    assert (
        load_current_record_graph(
            root, _work(TARGET), standards_library=standards
        ).graph.memberships
        == ()
    )
    fallback = EffectiveContext(activity_id=TARGET, session_ids=(f"{TARGET}-session",))
    before_application_preview = list_work_snapshots(root, _work(TARGET))
    application = prepare_group_plan_application(
        PrepareGroupPlanApplicationRequest(
            class_id=CLASS,
            activity_id=TARGET,
            group_plan_id=NEW_PLAN,
            application_id="apply-six-tables-once",
            fallback_effective_context=fallback,
        ),
        workspace_root=root,
        standards_library=standards,
    )
    assert application.group_count == 6
    assert application.membership_count == 29
    assert application.unresolved_count == 0
    assert list_work_snapshots(root, _work(TARGET)) == before_application_preview
    with pytest.raises(ConcordWorkflowConflictError):
        apply_group_plan(
            ApplyGroupPlanRequest(
                class_id=CLASS,
                activity_id=TARGET,
                group_plan_id=NEW_PLAN,
                application_id=application.application_id,
                application_digest="0" * 64,
                expected_snapshot_revision=application.expected_snapshot_revision,
                fallback_effective_context=fallback,
                actor=ACTOR,
            ),
            workspace_root=root,
            standards_library=standards,
        )
    assert list_work_snapshots(root, _work(TARGET)) == before_application_preview
    applied = apply_group_plan(
        ApplyGroupPlanRequest(
            class_id=CLASS,
            activity_id=TARGET,
            group_plan_id=NEW_PLAN,
            application_id=application.application_id,
            application_digest=application.application_digest,
            expected_snapshot_revision=application.expected_snapshot_revision,
            fallback_effective_context=fallback,
            actor=ACTOR,
        ),
        workspace_root=root,
        standards_library=standards,
    )
    assert applied.status == "applied"
    assert applied.group_count == 6
    assert applied.membership_count == 29
    graph = load_current_record_graph(
        root, _work(TARGET), standards_library=standards
    ).graph
    assert collect_record_graph_issues(graph) == ()
    assert len(graph.groups) == 6
    assert len(graph.memberships) == 29
    assert (
        len({m.participant_reference.participant_id for m in graph.memberships}) == 29
    )
    assert all(
        m.participant_reference.owning_system == "core" for m in graph.memberships
    )
    assert all(
        m.participant_reference.participant_kind == "core_student"
        for m in graph.memberships
    )
    assert graph.score_records == ()
    assert graph.criterion_sets == ()
    assert graph.artifact_instances == ()
    assert {g.label for g in graph.groups} == {f"Table {i}" for i in range(1, 7)}
    assert (
        next(p for p in graph.group_plans if p.group_plan_id == NEW_PLAN).status
        == "applied"
    )
    assert show_activity(CLASS, SOURCE, workspace_root=root).summary == unchanged_source
    assert (
        load_current_arrangement(
            root,
            class_id=CLASS,
            school_year=YEAR,
            arrangement_id=SAVED,
            actor_id=ACTOR.actor_id,
        )
        == saved_before
    )
    source_graph = load_current_record_graph(
        root, _work(SOURCE), standards_library=standards
    ).graph
    assert source_graph.groups == ()
    assert source_graph.memberships == ()
    assert source_graph.score_records == ()
    assert source_revision == unchanged_source.snapshot_revision
    assert set(applied.group_ids).isdisjoint(
        {p.group_plan_id for p in source_graph.group_plans}
    )
    with pytest.raises(ConcordWorkflowConflictError):
        apply_group_plan(
            ApplyGroupPlanRequest(
                class_id=CLASS,
                activity_id=TARGET,
                group_plan_id=NEW_PLAN,
                application_id=application.application_id,
                application_digest=application.application_digest,
                expected_snapshot_revision=application.expected_snapshot_revision,
                fallback_effective_context=fallback,
                actor=ACTOR,
            ),
            workspace_root=root,
            standards_library=standards,
        )
