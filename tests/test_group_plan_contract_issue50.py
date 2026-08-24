from __future__ import annotations

from dataclasses import fields, replace
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.classes import write_class_roster
from pds_core.rosters import create_roster
from pds_core.routing_models import ModuleRecordRef, ModuleWorkRef
from pds_core.workspace import ensure_workspace_root

from concord.model_conversion import record_from_dict, record_to_dict
from concord.model_validation import (
    ConcordRecordGraph,
    collect_record_graph_issues,
)
from concord.models import (
    Activity,
    ActorReference,
    ConcordModelError,
    EffectiveContext,
    GroupPlan,
    PlannedGroup,
    Provenance,
    Session,
)
from concord.record_registry import RECORD_DESCRIPTORS, descriptor_for_kind
from concord.storage import (
    commit_record_batch,
    list_record_revisions,
    list_work_snapshots,
    load_current_record_graph,
    load_record_revision,
)
from concord.workflows import (
    CreateActivityContextRequest,
    WorkflowActor,
    create_activity_context,
)


def _timestamp(day: int) -> str:
    return datetime(
        2026,
        8,
        day,
        15,
        0,
        tzinfo=timezone.utc,
    ).isoformat()


def _native_provenance(day: int = 1) -> Provenance:
    return Provenance(
        actor=ActorReference(
            actor_kind="authorized_adult",
            actor_id="teacher-1",
            owning_system="concord",
        ),
        timestamp=_timestamp(day),
        source_kind="manual",
        application_version="0.3.0.dev0",
    )


def _class_ref(class_id: str = "class-1") -> ModuleRecordRef:
    return ModuleRecordRef(
        module_id="core",
        record_kind="class",
        record_id=class_id,
    )


def _draft_plan(
    *,
    class_id: str = "class-1",
    activity_id: str = "activity-1",
) -> GroupPlan:
    return GroupPlan(
        group_plan_id="plan-1",
        activity_id=activity_id,
        class_reference=_class_ref(class_id),
        strategy="manual",
        status="draft",
        roster_student_ids=("student-3", "student-1", "student-2"),
        proposed_groups=(
            PlannedGroup(
                planned_group_key="group-a",
                label="Group A",
                student_ids=("student-2", "student-1"),
            ),
        ),
        unresolved_student_ids=("student-3",),
        created_provenance=_native_provenance(),
    )


def _activity_graph(plan: GroupPlan) -> ConcordRecordGraph:
    created = _native_provenance()
    activity = Activity(
        activity_id="activity-1",
        class_reference=_class_ref(),
        title="Synthetic Activity",
        activity_type="project",
        scoring_orientation="evidence_only",
        status="draft",
        created_provenance=created,
    )
    session = Session(
        session_id="session-1",
        activity_id=activity.activity_id,
        sequence=1,
        status="planned",
        created_provenance=created,
    )
    return ConcordRecordGraph(
        activities=(activity,),
        sessions=(session,),
        group_plans=(plan,),
    )


def _workspace_with_activity(tmp_path: Path) -> tuple[Path, int]:
    root = ensure_workspace_root(tmp_path / "workspace")
    metadata = create_class_metadata(
        "class-1",
        "2026-2027",
        created_at=datetime(
            2026,
            8,
            1,
            15,
            0,
            tzinfo=timezone.utc,
        ),
    )
    write_class_metadata_for_class(root, metadata)
    roster = create_roster(
        "class-1",
        (
            {
                "student_id": "student-1",
                "last_name": "One",
                "first_name": "Alex",
                "period": "1",
            },
            {
                "student_id": "student-2",
                "last_name": "Two",
                "first_name": "Blair",
                "period": "1",
            },
            {
                "student_id": "student-3",
                "last_name": "Three",
                "first_name": "Casey",
                "period": "1",
            },
        ),
    )
    write_class_roster(root, roster)
    created = create_activity_context(
        CreateActivityContextRequest(
            class_id="class-1",
            activity_id="activity-1",
            title="Synthetic Activity",
            activity_type="project",
            scoring_orientation="evidence_only",
            session_id="session-1",
            actor=WorkflowActor(actor_id="teacher-1"),
        ),
        workspace_root=root,
        clock=lambda: datetime(
            2026,
            8,
            2,
            15,
            0,
            tzinfo=timezone.utc,
        ),
    )
    return root, created.commit.snapshot_revision


def test_group_plan_model_normalizes_identity_sets_and_round_trips() -> None:
    plan = _draft_plan()
    assert plan.roster_student_ids == (
        "student-1",
        "student-2",
        "student-3",
    )
    assert plan.proposed_groups[0].student_ids == (
        "student-1",
        "student-2",
    )
    assert record_from_dict("group_plan", record_to_dict(plan)) == plan


def test_group_plan_registry_has_one_native_descriptor() -> None:
    descriptors = [
        item
        for item in RECORD_DESCRIPTORS
        if item.kind == "group_plan"
    ]
    assert len(descriptors) == 1
    descriptor = descriptor_for_kind("group_plan")
    assert descriptor.identity_field == "group_plan_id"
    assert descriptor.graph_collection == "group_plans"
    assert descriptor.model_type is GroupPlan


def test_group_plan_rejects_unknown_fields_and_has_no_band_storage() -> None:
    plan = _draft_plan()
    field_names = {item.name for item in fields(GroupPlan)}
    assert not any("band" in name for name in field_names)
    payload = record_to_dict(plan)
    payload["student_bands"] = {"student-1": 1}
    with pytest.raises(ConcordModelError, match="unknown field"):
        record_from_dict("group_plan", payload)


@pytest.mark.parametrize(
    ("groups", "unresolved", "message"),
    (
        (
            (
                PlannedGroup(
                    planned_group_key="a",
                    label="A",
                    student_ids=("student-1",),
                ),
                PlannedGroup(
                    planned_group_key="b",
                    label="B",
                    student_ids=("student-1",),
                ),
            ),
            ("student-2", "student-3"),
            "more than one",
        ),
        (
            (
                PlannedGroup(
                    planned_group_key="a",
                    label="A",
                    student_ids=("student-1",),
                ),
            ),
            ("student-1", "student-2", "student-3"),
            "both grouped and unresolved",
        ),
        (
            (
                PlannedGroup(
                    planned_group_key="a",
                    label="A",
                    student_ids=("student-1",),
                ),
            ),
            ("student-2",),
            "exactly cover",
        ),
    ),
)
def test_group_plan_rejects_invalid_roster_partition(
    groups: tuple[PlannedGroup, ...],
    unresolved: tuple[str, ...],
    message: str,
) -> None:
    with pytest.raises(ConcordModelError, match=message):
        replace(
            _draft_plan(),
            proposed_groups=groups,
            unresolved_student_ids=unresolved,
        )


def test_group_plan_target_and_signal_constraints_are_structural() -> None:
    with pytest.raises(ConcordModelError, match="mutually exclusive"):
        replace(
            _draft_plan(),
            target_group_size=3,
            target_group_count=2,
        )
    with pytest.raises(ConcordModelError, match="supplied together"):
        replace(
            _draft_plan(),
            strategy="similar_signal",
            source_signal_set_id="signal-1",
        )
    with pytest.raises(ConcordModelError, match="lowercase SHA-256"):
        replace(
            _draft_plan(),
            strategy="similar_signal",
            source_signal_set_id="signal-1",
            source_signal_set_digest="A" * 64,
            source_signal_dimension_id="writing",
        )
    with pytest.raises(ConcordModelError, match="signal-dependent"):
        replace(
            _draft_plan(),
            source_signal_set_id="signal-1",
            source_signal_set_digest="a" * 64,
            source_signal_dimension_id="writing",
        )


def test_group_plan_status_provenance_is_coherent() -> None:
    with pytest.raises(ConcordModelError, match="requires previewed_provenance"):
        replace(_draft_plan(), status="previewed")
    previewed = replace(
        _draft_plan(),
        status="previewed",
        previewed_provenance=_native_provenance(2),
    )
    with pytest.raises(ConcordModelError, match="requires preview and approval"):
        replace(previewed, status="approved")
    resolved_previewed = replace(
        previewed,
        proposed_groups=(
            PlannedGroup(
                planned_group_key="group-a",
                label="Group A",
                student_ids=("student-1", "student-2", "student-3"),
            ),
        ),
        unresolved_student_ids=(),
    )
    approved = replace(
        resolved_previewed,
        status="approved",
        approved_provenance=_native_provenance(3),
    )
    with pytest.raises(
        ConcordModelError,
        match="preview, approval, and application",
    ):
        replace(approved, status="applied")
    applied = replace(
        approved,
        status="applied",
        applied_provenance=_native_provenance(4),
        applied_application_id="apply-1",
        applied_application_digest="a" * 64,
    )
    assert applied.status == "applied"


def test_random_and_signal_non_draft_inputs_are_explicit() -> None:
    random_draft = replace(
        _draft_plan(),
        strategy="random",
        target_group_size=2,
    )
    with pytest.raises(ConcordModelError, match="explicit seed"):
        replace(
            random_draft,
            status="previewed",
            previewed_provenance=_native_provenance(2),
        )
    signal_draft = replace(
        _draft_plan(),
        strategy="similar_signal",
        target_group_count=2,
    )
    with pytest.raises(ConcordModelError, match="exact signal binding"):
        replace(
            signal_draft,
            status="previewed",
            previewed_provenance=_native_provenance(2),
        )


def test_group_plan_graph_validates_activity_class_and_context() -> None:
    wrong_class = _draft_plan(class_id="class-2")
    issues = collect_record_graph_issues(_activity_graph(wrong_class))
    assert "group_plan.class.mismatch" in {item.code for item in issues}

    wrong_activity = _draft_plan(activity_id="activity-2")
    issues = collect_record_graph_issues(_activity_graph(wrong_activity))
    assert "group_plan.activity.missing" in {item.code for item in issues}

    wrong_context = replace(
        _draft_plan(),
        proposed_groups=(
            PlannedGroup(
                planned_group_key="group-a",
                label="Group A",
                student_ids=("student-1", "student-2"),
                effective_context=EffectiveContext(
                    activity_id="activity-2",
                    session_ids=("session-1",),
                ),
            ),
        ),
    )
    issues = collect_record_graph_issues(_activity_graph(wrong_context))
    codes = {item.code for item in issues}
    assert "group_plan.context.activity_mismatch" in codes
    assert "effective_context.session.activity_mismatch" in codes


def test_group_plan_uses_native_revision_history_without_group_side_effects(
    tmp_path: Path,
) -> None:
    root, revision = _workspace_with_activity(tmp_path)
    work = ModuleWorkRef(
        module_id="concord",
        class_id="class-1",
        work_id="activity-1",
    )
    before = load_current_record_graph(root, work)
    assert before.graph.group_plans == ()
    assert before.graph.groups == ()
    assert before.graph.memberships == ()

    plan = _draft_plan()
    first = commit_record_batch(
        root,
        work,
        (plan,),
        expected_snapshot_revision=revision,
    )
    assert first.snapshot_revision == revision + 1

    revised = replace(
        plan,
        proposed_groups=(
            PlannedGroup(
                planned_group_key="group-a",
                label="Group A",
                student_ids=(
                    "student-1",
                    "student-2",
                    "student-3",
                ),
            ),
        ),
        unresolved_student_ids=(),
        updated_provenance=_native_provenance(3),
    )
    second = commit_record_batch(
        root,
        work,
        (revised,),
        expected_snapshot_revision=first.snapshot_revision,
    )
    assert list_record_revisions(
        root,
        work,
        "group_plan",
        "plan-1",
    ) == (1, 2)
    historical, envelope = load_record_revision(
        root,
        work,
        "group_plan",
        "plan-1",
        1,
    )
    assert historical == plan
    assert envelope.record_revision == 1
    assert list_work_snapshots(root, work) == (
        1,
        first.snapshot_revision,
        second.snapshot_revision,
    )

    current = load_current_record_graph(root, work)
    assert current.graph.group_plans == (revised,)
    assert current.graph.groups == ()
    assert current.graph.memberships == ()
