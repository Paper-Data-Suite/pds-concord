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

from concord.group_plan_application import derive_group_id
from concord.models import (
    ActorReference,
    EffectiveContext,
    Group,
    GroupPlan,
    PlannedGroup,
    Provenance,
)
from concord.storage import (
    commit_record_batch,
    list_work_snapshots,
    load_current_record_graph,
    load_current_snapshot,
)
from concord.workflows import (
    CreateActivityContextRequest,
    PrepareGroupPlanApplicationRequest,
    WorkflowActor,
    create_activity_context,
    prepare_group_plan_application,
    select_grouping_signal_dimension,
)
from concord.workflows._collaboration import work_ref
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowValidationError,
)


def _clock(day: int) -> datetime:
    return datetime(2026, 8, day, 15, 0, tzinfo=timezone.utc)


def _provenance(day: int = 1) -> Provenance:
    return Provenance(
        actor=ActorReference(
            actor_kind="authorized_adult",
            actor_id="teacher-1",
            owning_system="concord",
        ),
        timestamp=_clock(day).isoformat(),
        source_kind="manual",
        application_version="0.3.0",
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


def _workspace(tmp_path: Path, *, name: str = "workspace") -> tuple[Path, int]:
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
            title="Application Preview Activity",
            activity_type="project",
            scoring_orientation="evidence_only",
            session_id="session-1",
            actor=WorkflowActor(actor_id="teacher-1"),
        ),
        workspace_root=root,
        clock=lambda: _clock(2),
    )
    return root, created.commit.snapshot_revision


def _context() -> EffectiveContext:
    return EffectiveContext(
        activity_id="activity-1",
        session_ids=("session-1",),
    )


def _plan(
    *,
    status: str = "approved",
    all_contexts: bool = False,
) -> GroupPlan:
    group_b_context = _context() if all_contexts else None
    values: dict[str, object] = {
        "group_plan_id": "plan-1",
        "activity_id": "activity-1",
        "class_reference": ModuleRecordRef(
            module_id="core",
            record_kind="class",
            record_id="class-1",
        ),
        "strategy": "manual",
        "status": status,
        "roster_student_ids": ("student-1", "student-2", "student-3"),
        "proposed_groups": (
            PlannedGroup(
                planned_group_key="group-a",
                label="Group A",
                student_ids=("student-1",),
                description="Explicit context",
                effective_context=_context(),
            ),
            PlannedGroup(
                planned_group_key="group-b",
                label="Group B",
                student_ids=("student-2", "student-3"),
                effective_context=group_b_context,
            ),
            PlannedGroup(
                planned_group_key="empty-group",
                label="Empty Group",
                student_ids=(),
            ),
        ),
        "unresolved_student_ids": (),
        "created_provenance": _provenance(2),
    }
    if status in {"previewed", "approved", "applied"}:
        values["previewed_provenance"] = _provenance(3)
    if status in {"approved", "applied"}:
        values["approved_provenance"] = _provenance(4)
    if status == "cancelled":
        values["cancelled_provenance"] = _provenance(5)
    if status == "applied":
        values["applied_provenance"] = _provenance(5)
        values["applied_application_id"] = "apply-prior"
        values["applied_application_digest"] = "a" * 64
    return GroupPlan(**values)  # type: ignore[arg-type]


def _commit_plan(root: Path, revision: int, plan: GroupPlan) -> int:
    result = commit_record_batch(
        root,
        work_ref("class-1", "activity-1"),
        (plan,),
        expected_snapshot_revision=revision,
    )
    return result.snapshot_revision


def _request(
    *,
    application_id: str | None = "apply-preview-1",
    fallback: EffectiveContext | None = None,
) -> PrepareGroupPlanApplicationRequest:
    return PrepareGroupPlanApplicationRequest(
        class_id="class-1",
        activity_id="activity-1",
        group_plan_id="plan-1",
        application_id=application_id,
        fallback_effective_context=fallback,
    )


def test_prepare_is_zero_write_and_preserves_exact_group_context_semantics(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    revision = _commit_plan(root, revision, _plan())
    work = work_ref("class-1", "activity-1")
    before = load_current_snapshot(root, work)
    snapshots_before = list_work_snapshots(root, work)

    preview = prepare_group_plan_application(
        _request(fallback=_context()),
        workspace_root=root,
    )

    after = load_current_snapshot(root, work)
    graph = load_current_record_graph(root, work).graph
    assert after == before
    assert list_work_snapshots(root, work) == snapshots_before
    assert graph.groups == ()
    assert graph.memberships == ()
    assert graph.group_plans[0].status == "approved"

    assert preview.expected_snapshot_revision == revision
    assert preview.group_count == 3
    assert preview.membership_count == 3
    assert preview.unresolved_count == 0
    assert {item.planned_group_key for item in preview.groups} == {
        "empty-group",
        "group-a",
        "group-b",
    }

    group_a = next(
        item for item in preview.groups if item.planned_group_key == "group-a"
    )
    group_b = next(
        item for item in preview.groups if item.planned_group_key == "group-b"
    )
    assert group_a.effective_context == _context()
    assert group_b.effective_context is None

    memberships_a = tuple(
        item for item in preview.memberships if item.planned_group_key == "group-a"
    )
    memberships_b = tuple(
        item for item in preview.memberships if item.planned_group_key == "group-b"
    )
    assert {item.effective_context for item in memberships_a} == {_context()}
    assert {item.effective_context for item in memberships_b} == {_context()}


def test_same_explicit_application_request_reproduces_exact_preview(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    _commit_plan(root, revision, _plan())
    request = _request(fallback=_context())
    first = prepare_group_plan_application(request, workspace_root=root)
    second = prepare_group_plan_application(request, workspace_root=root)
    assert first == second


def test_prepare_generates_fresh_application_id_when_omitted(tmp_path: Path) -> None:
    root, revision = _workspace(tmp_path)
    _commit_plan(root, revision, _plan())
    preview = prepare_group_plan_application(
        _request(application_id=None, fallback=_context()),
        workspace_root=root,
    )
    assert preview.application_id.startswith("apply-")
    assert len(preview.application_digest) == 64


def test_contextless_nonempty_group_requires_fallback(tmp_path: Path) -> None:
    root, revision = _workspace(tmp_path)
    _commit_plan(root, revision, _plan())
    with pytest.raises(
        ConcordWorkflowValidationError,
        match="fallback_effective_context",
    ):
        prepare_group_plan_application(_request(), workspace_root=root)


def test_irrelevant_fallback_is_rejected_when_all_nonempty_groups_have_context(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    _commit_plan(root, revision, _plan(all_contexts=True))
    with pytest.raises(ConcordWorkflowValidationError, match="not allowed"):
        prepare_group_plan_application(
            _request(fallback=_context()),
            workspace_root=root,
        )


def test_fallback_must_identify_selected_activity(tmp_path: Path) -> None:
    root, revision = _workspace(tmp_path)
    _commit_plan(root, revision, _plan())
    wrong = EffectiveContext(
        activity_id="activity-2",
        session_ids=("session-1",),
    )
    with pytest.raises(ConcordWorkflowValidationError, match="selected Activity"):
        prepare_group_plan_application(
            _request(fallback=wrong),
            workspace_root=root,
        )


def test_fallback_must_reference_existing_session(tmp_path: Path) -> None:
    root, revision = _workspace(tmp_path)
    _commit_plan(root, revision, _plan())
    missing = EffectiveContext(
        activity_id="activity-1",
        session_ids=("session-missing",),
    )
    with pytest.raises(
        ConcordWorkflowValidationError,
        match="effective_context.session.missing",
    ):
        prepare_group_plan_application(
            _request(fallback=missing),
            workspace_root=root,
        )


@pytest.mark.parametrize("status", ("draft", "previewed", "cancelled"))
def test_prepare_requires_approved_status(tmp_path: Path, status: str) -> None:
    root, revision = _workspace(tmp_path, name=status)
    _commit_plan(root, revision, _plan(status=status))
    with pytest.raises(ConcordWorkflowConflictError, match="Only an approved"):
        prepare_group_plan_application(
            _request(fallback=_context()),
            workspace_root=root,
        )


def test_prepare_rejects_already_applied_plan(tmp_path: Path) -> None:
    root, revision = _workspace(tmp_path)
    _commit_plan(root, revision, _plan(status="applied"))
    with pytest.raises(ConcordWorkflowConflictError, match="already been applied"):
        prepare_group_plan_application(
            _request(fallback=_context()),
            workspace_root=root,
        )


def test_prepare_fails_closed_on_core_roster_drift(tmp_path: Path) -> None:
    root, revision = _workspace(tmp_path)
    _commit_plan(root, revision, _plan())
    write_class_roster(
        root,
        _roster("student-1", "student-2", "student-3", "student-4"),
        overwrite=True,
    )
    with pytest.raises(ConcordWorkflowConflictError, match="Core roster changed"):
        prepare_group_plan_application(
            _request(fallback=_context()),
            workspace_root=root,
        )


def test_prepare_rejects_derived_group_identity_collision(tmp_path: Path) -> None:
    root, revision = _workspace(tmp_path)
    revision = _commit_plan(root, revision, _plan())
    collision_id = derive_group_id("apply-preview-1", "plan-1", "group-a")
    collision = Group(
        group_id=collision_id,
        activity_id="activity-1",
        label="Existing Group",
        status="planned",
        created_provenance=_provenance(5),
    )
    commit_record_batch(
        root,
        work_ref("class-1", "activity-1"),
        (collision,),
        expected_snapshot_revision=revision,
    )
    with pytest.raises(ConcordWorkflowConflictError, match="Group already exists"):
        prepare_group_plan_application(
            _request(fallback=_context()),
            workspace_root=root,
        )


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


def _signal_plan(digest: str) -> GroupPlan:
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


def test_signal_leave_unassigned_preview_revalidates_exact_missing_set(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    signal = _signal()
    write_grouping_signal(root, signal)
    selection = select_grouping_signal_dimension(
        "class-1",
        "signal-1",
        "collaboration",
        workspace_root=root,
    )
    _commit_plan(root, revision, _signal_plan(selection.digest))

    preview = prepare_group_plan_application(
        _request(fallback=_context()),
        workspace_root=root,
    )
    assert preview.membership_count == 2
    assert preview.unresolved_student_ids == ("student-3",)
    assert {item.student_id for item in preview.memberships} == {
        "student-1",
        "student-2",
    }


def test_signal_preview_fails_closed_on_bound_digest_mismatch(tmp_path: Path) -> None:
    root, revision = _workspace(tmp_path)
    write_grouping_signal(root, _signal())
    _commit_plan(root, revision, _signal_plan("a" * 64))
    with pytest.raises(ConcordWorkflowConflictError, match="canonical digest"):
        prepare_group_plan_application(
            _request(fallback=_context()),
            workspace_root=root,
        )
