from __future__ import annotations

import os
import subprocess
import sys
import tomllib
from dataclasses import fields
from datetime import datetime, timezone
from pathlib import Path

from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.classes import write_class_roster
from pds_core.grouping_signal_storage import (
    calculate_grouping_signal_digest,
    write_grouping_signal,
)
from pds_core.grouping_signals import (
    GroupingSignalDimension,
    GroupingSignalSet,
    GroupingSignalSource,
    GroupingSignalStudentBand,
)
from pds_core.rosters import create_roster
from pds_core.routing_models import ModuleWorkRef
from pds_core.workspace import ensure_workspace_root

from concord.model_validation import collect_record_graph_issues
from concord.models import EffectiveContext, PlannedGroup
from concord.storage import list_work_snapshots, load_current_record_graph
from concord.workflows import (
    AddMembershipsRequest,
    ApplyGroupPlanRequest,
    ApproveGroupPlanRequest,
    CreateActivityContextRequest,
    CreateGroupRequest,
    CreateGroupWithMembersRequest,
    CreateManualGroupPlanRequest,
    CreateRandomGroupPlanRequest,
    CreateSignalGroupPlanRequest,
    GroupMemberSpec,
    ImportArrangementGroupPlanRequest,
    PlaceStudentInPlanRequest,
    PrepareGroupPlanApplicationRequest,
    PreviewGroupPlanRequest,
    SetMissingSignalDispositionRequest,
    WorkflowActor,
    add_memberships,
    apply_group_plan,
    approve_group_plan,
    create_activity_context,
    create_group,
    create_group_with_members,
    create_manual_group_plan,
    create_random_group_plan,
    create_signal_group_plan,
    import_arrangement_group_plan,
    inspect_group_plan_missing_signal,
    place_student_in_plan,
    prepare_group_plan_application,
    preview_group_plan,
    set_missing_signal_disposition,
    show_group_plan,
)

ROOT = Path(__file__).resolve().parents[1]
CLASS_ID = "class-acceptance"
ACTIVITY_ID = "activity-acceptance"
SESSION_ID = "session-1"
STUDENT_IDS = tuple(f"student-{index}" for index in range(1, 7))

_PLANNING_ONLY_FIELDS = frozenset(
    {
        "strategy",
        "seed",
        "source_signal_set_id",
        "source_signal_set_digest",
        "source_signal_dimension_id",
        "missing_signal_disposition",
        "missing_signal_random_seed",
        "applied_application_id",
        "applied_application_digest",
    }
)


def _clock(minute: int) -> datetime:
    return datetime(2026, 8, 29, 20, minute, tzinfo=timezone.utc)


def _actor() -> WorkflowActor:
    return WorkflowActor(
        actor_id="teacher-acceptance",
        display_label="Synthetic Teacher",
        role_label="teacher",
    )


def _context() -> EffectiveContext:
    return EffectiveContext(
        activity_id=ACTIVITY_ID,
        session_ids=(SESSION_ID,),
    )


def _work() -> ModuleWorkRef:
    return ModuleWorkRef(
        module_id="concord",
        class_id=CLASS_ID,
        work_id=ACTIVITY_ID,
    )


def _workspace(tmp_path: Path) -> tuple[Path, int]:
    root = ensure_workspace_root(tmp_path / "workspace")
    write_class_metadata_for_class(
        root,
        create_class_metadata(
            CLASS_ID,
            "2026-2027",
            created_at=_clock(0),
        ),
    )
    write_class_roster(
        root,
        create_roster(
            CLASS_ID,
            tuple(
                {
                    "student_id": student_id,
                    "last_name": f"Last{index}",
                    "first_name": f"First{index}",
                    "period": "1",
                }
                for index, student_id in enumerate(STUDENT_IDS, start=1)
            ),
        ),
    )
    created = create_activity_context(
        CreateActivityContextRequest(
            class_id=CLASS_ID,
            activity_id=ACTIVITY_ID,
            title="Repository-local Group Planning Acceptance",
            activity_type="project",
            scoring_orientation="evidence_only",
            session_id=SESSION_ID,
            actor=_actor(),
            session_label="Acceptance Session",
        ),
        workspace_root=root,
        clock=lambda: _clock(1),
    )
    return root, created.commit.snapshot_revision


def _assert_no_canonical_group_state(root: Path) -> None:
    graph = load_current_record_graph(root, _work()).graph
    assert graph.groups == ()
    assert graph.memberships == ()
    assert collect_record_graph_issues(graph) == ()


def _apply_approved_plan(
    root: Path,
    *,
    group_plan_id: str,
    draft_snapshot_revision: int,
    application_id: str,
    clock_minute: int,
    expected_unresolved_student_ids: tuple[str, ...] = (),
):
    """Exercise audited planning state, zero-write application preview, and apply."""
    snapshots_before_preview = list_work_snapshots(root, _work())
    previewed = preview_group_plan(
        PreviewGroupPlanRequest(
            class_id=CLASS_ID,
            activity_id=ACTIVITY_ID,
            group_plan_id=group_plan_id,
            expected_snapshot_revision=draft_snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(clock_minute),
    )
    assert previewed.plan.status == "previewed"
    assert previewed.summary.snapshot_revision == draft_snapshot_revision + 1
    assert list_work_snapshots(root, _work()) == (
        *snapshots_before_preview,
        previewed.summary.snapshot_revision,
    )
    _assert_no_canonical_group_state(root)

    approved = approve_group_plan(
        ApproveGroupPlanRequest(
            class_id=CLASS_ID,
            activity_id=ACTIVITY_ID,
            group_plan_id=group_plan_id,
            expected_snapshot_revision=previewed.summary.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(clock_minute + 1),
    )
    assert approved.status == "approved"
    assert approved.commit.snapshot_revision == previewed.summary.snapshot_revision + 1
    _assert_no_canonical_group_state(root)

    snapshots_before_application_preview = list_work_snapshots(root, _work())
    application = prepare_group_plan_application(
        PrepareGroupPlanApplicationRequest(
            class_id=CLASS_ID,
            activity_id=ACTIVITY_ID,
            group_plan_id=group_plan_id,
            application_id=application_id,
            fallback_effective_context=_context(),
        ),
        workspace_root=root,
    )
    assert application.expected_snapshot_revision == approved.commit.snapshot_revision
    assert application.unresolved_student_ids == expected_unresolved_student_ids
    assert list_work_snapshots(root, _work()) == snapshots_before_application_preview
    _assert_no_canonical_group_state(root)

    result = apply_group_plan(
        ApplyGroupPlanRequest(
            class_id=CLASS_ID,
            activity_id=ACTIVITY_ID,
            group_plan_id=group_plan_id,
            application_id=application.application_id,
            application_digest=application.application_digest,
            expected_snapshot_revision=application.expected_snapshot_revision,
            actor=_actor(),
            fallback_effective_context=_context(),
        ),
        workspace_root=root,
        clock=lambda: _clock(clock_minute + 2),
    )
    assert result.status == "applied"
    assert result.application_id == application.application_id
    assert result.application_digest == application.application_digest
    assert result.commit.snapshot_revision == application.expected_snapshot_revision + 1
    assert result.unresolved_count == len(expected_unresolved_student_ids)
    assert result.group_ids == tuple(group.group_id for group in application.groups)
    assert result.membership_ids == tuple(
        membership.membership_id for membership in application.memberships
    )
    assert set(result.group_ids).isdisjoint(
        group.planned_group_key for group in application.groups
    )
    assert set(result.membership_ids).isdisjoint(STUDENT_IDS)

    graph = load_current_record_graph(root, _work()).graph
    assert collect_record_graph_issues(graph) == ()
    applied_plan = next(
        plan for plan in graph.group_plans if plan.group_plan_id == group_plan_id
    )
    assert applied_plan.status == "applied"
    assert applied_plan.applied_application_id == application.application_id
    assert applied_plan.applied_application_digest == application.application_digest
    assert {group.group_id for group in graph.groups} == set(result.group_ids)
    assert {membership.membership_id for membership in graph.memberships} == set(
        result.membership_ids
    )

    membership_by_id = {
        membership.membership_id: membership for membership in graph.memberships
    }
    for expected in application.memberships:
        membership = membership_by_id[expected.membership_id]
        assert membership.group_id == expected.group_id
        assert membership.participant_reference.participant_kind == "core_student"
        assert membership.participant_reference.participant_id == expected.student_id
        assert membership.participant_reference.owning_system == "core"
        assert membership.effective_context == expected.effective_context

    for record in (*graph.groups, *graph.memberships):
        record_fields = {field.name for field in fields(record)}
        assert record_fields.isdisjoint(_PLANNING_ONLY_FIELDS)

    return application, result, graph



def _core_signal() -> GroupingSignalSet:
    dimension_id = "proficiency-band"
    return GroupingSignalSet(
        schema_version="1",
        record_type="grouping_signal_set",
        signal_set_id="signal-acceptance",
        class_id=CLASS_ID,
        created_at=_clock(1),
        source=GroupingSignalSource(
            kind="module_generated",
            module_id="meridian",
            snapshot_id="academic-period-2026-q1",
            snapshot_digest_algorithm="sha256",
            snapshot_digest="b" * 64,
        ),
        dimensions=(
            GroupingSignalDimension(
                dimension_id=dimension_id,
                band_count=4,
            ),
        ),
        student_bands=(
            GroupingSignalStudentBand(
                student_id="student-1",
                dimension_id=dimension_id,
                band=1,
            ),
            GroupingSignalStudentBand(
                student_id="student-2",
                dimension_id=dimension_id,
                band=1,
            ),
            GroupingSignalStudentBand(
                student_id="student-3",
                dimension_id=dimension_id,
                band=1,
            ),
            GroupingSignalStudentBand(
                student_id="student-4",
                dimension_id=dimension_id,
                band=2,
            ),
            GroupingSignalStudentBand(
                student_id="student-5",
                dimension_id=dimension_id,
                band=2,
            ),
            GroupingSignalStudentBand(
                student_id="student-6",
                dimension_id=dimension_id,
                band=3,
            ),
        ),
    )


def _create_signal_plan(
    root: Path,
    *,
    revision: int,
    strategy: str,
    group_plan_id: str,
):
    signal = _core_signal()
    write_grouping_signal(root, signal)
    canonical_digest = calculate_grouping_signal_digest(signal)
    created = create_signal_group_plan(
        CreateSignalGroupPlanRequest(
            class_id=CLASS_ID,
            activity_id=ACTIVITY_ID,
            group_plan_id=group_plan_id,
            strategy=strategy,
            signal_set_id=signal.signal_set_id,
            dimension_id="proficiency-band",
            expected_snapshot_revision=revision,
            actor=_actor(),
            target_group_count=2,
            expected_roster_student_ids=STUDENT_IDS,
            expected_signal_set_digest=canonical_digest,
        ),
        workspace_root=root,
        clock=lambda: _clock(2),
    )
    detail = show_group_plan(
        CLASS_ID,
        ACTIVITY_ID,
        group_plan_id,
        workspace_root=root,
    )
    assert created.strategy == strategy
    assert created.group_count == 2
    assert created.assigned_student_count == 6
    assert created.unresolved_student_count == 0
    assert created.group_sizes == (3, 3)
    assert created.signal_set_id == signal.signal_set_id
    assert created.signal_set_digest == canonical_digest
    assert created.signal_set_digest != signal.source.snapshot_digest
    assert created.dimension_id == "proficiency-band"
    assert detail.plan.status == "draft"
    assert detail.plan.strategy == strategy
    assert detail.plan.source_signal_set_id == signal.signal_set_id
    assert detail.plan.source_signal_set_digest == canonical_digest
    assert detail.plan.source_signal_dimension_id == "proficiency-band"
    assert detail.plan.unresolved_student_ids == ()
    _assert_no_canonical_group_state(root)
    return signal, canonical_digest, created, detail


def _assert_signal_metadata_stays_on_plan(
    graph,
    *,
    group_plan_id: str,
    signal: GroupingSignalSet,
    canonical_digest: str,
) -> None:
    applied_plan = next(
        plan for plan in graph.group_plans if plan.group_plan_id == group_plan_id
    )
    assert applied_plan.source_signal_set_id == signal.signal_set_id
    assert applied_plan.source_signal_set_digest == canonical_digest
    assert applied_plan.source_signal_dimension_id == "proficiency-band"

    for record in (*graph.groups, *graph.memberships):
        rendered = repr(record)
        assert signal.signal_set_id not in rendered
        assert canonical_digest not in rendered
        assert "proficiency-band" not in rendered


def test_package_metadata_keeps_meridian_outside_concord_dependencies() -> None:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        project = tomllib.load(handle)["project"]

    declared = [*project.get("dependencies", ())]
    for dependencies in project.get("optional-dependencies", {}).values():
        declared.extend(dependencies)

    assert all("meridian" not in dependency.casefold() for dependency in declared)
    assert "meridian" not in repr(project.get("entry-points", {})).casefold()


def test_importing_concord_workflows_does_not_attempt_meridian_import() -> None:
    script = """
import builtins

real_import = builtins.__import__


def guarded_import(name, *args, **kwargs):
    if name == "meridian" or name.startswith("meridian."):
        raise RuntimeError(f"Concord attempted forbidden Meridian import: {name}")
    return real_import(name, *args, **kwargs)


builtins.__import__ = guarded_import
import concord.workflows  # noqa: F401, E402
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_direct_groups_remain_canonical_without_group_plan_or_signal(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    context = _context()

    first = create_group_with_members(
        CreateGroupWithMembersRequest(
            class_id=CLASS_ID,
            activity_id=ACTIVITY_ID,
            group_id="group-a",
            label="Group A",
            expected_snapshot_revision=revision,
            actor=_actor(),
            status="active",
            effective_context=context,
            members=tuple(
                GroupMemberSpec(
                    membership_id=f"membership-{index}",
                    student_id=f"student-{index}",
                    effective_context=context,
                )
                for index in range(1, 4)
            ),
        ),
        workspace_root=root,
        clock=lambda: _clock(2),
    )
    second = create_group(
        CreateGroupRequest(
            class_id=CLASS_ID,
            activity_id=ACTIVITY_ID,
            group_id="group-b",
            label="Group B",
            expected_snapshot_revision=first.commit.snapshot_revision,
            actor=_actor(),
            status="active",
            effective_context=context,
        ),
        workspace_root=root,
        clock=lambda: _clock(3),
    )
    added = add_memberships(
        AddMembershipsRequest(
            class_id=CLASS_ID,
            activity_id=ACTIVITY_ID,
            group_id="group-b",
            members=tuple(
                GroupMemberSpec(
                    membership_id=f"membership-{index}",
                    student_id=f"student-{index}",
                    effective_context=context,
                )
                for index in range(4, 7)
            ),
            expected_snapshot_revision=second.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(4),
    )

    assert first.membership_ids == (
        "membership-1",
        "membership-2",
        "membership-3",
    )
    assert added.membership_ids == (
        "membership-4",
        "membership-5",
        "membership-6",
    )

    graph = load_current_record_graph(root, _work()).graph
    assert graph.group_plans == ()
    assert {group.group_id for group in graph.groups} == {"group-a", "group-b"}
    assert len(graph.memberships) == 6
    assert collect_record_graph_issues(graph) == ()

    membership_by_id = {
        membership.membership_id: membership for membership in graph.memberships
    }
    expected_groups = {
        "membership-1": "group-a",
        "membership-2": "group-a",
        "membership-3": "group-a",
        "membership-4": "group-b",
        "membership-5": "group-b",
        "membership-6": "group-b",
    }
    for index, student_id in enumerate(STUDENT_IDS, start=1):
        membership = membership_by_id[f"membership-{index}"]
        assert membership.group_id == expected_groups[membership.membership_id]
        assert membership.participant_reference.participant_kind == "core_student"
        assert membership.participant_reference.participant_id == student_id
        assert membership.participant_reference.owning_system == "core"
        assert membership.effective_context == context
        assert membership.status == "active"

    for record in (*graph.groups, *graph.memberships):
        record_fields = {field.name for field in fields(record)}
        assert record_fields.isdisjoint(_PLANNING_ONLY_FIELDS)


def test_manual_group_plan_uses_editor_then_explicit_application(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    created = create_manual_group_plan(
        CreateManualGroupPlanRequest(
            class_id=CLASS_ID,
            activity_id=ACTIVITY_ID,
            group_plan_id="plan-manual",
            expected_snapshot_revision=revision,
            actor=_actor(),
            proposed_groups=(
                PlannedGroup(planned_group_key="alpha", label="Alpha"),
                PlannedGroup(planned_group_key="beta", label="Beta"),
            ),
        ),
        workspace_root=root,
        clock=lambda: _clock(2),
    )
    detail = show_group_plan(
        CLASS_ID,
        ACTIVITY_ID,
        "plan-manual",
        workspace_root=root,
    )
    assert detail.plan.strategy == "manual"
    assert detail.plan.status == "draft"
    assert detail.plan.unresolved_student_ids == STUDENT_IDS
    _assert_no_canonical_group_state(root)

    current_revision = created.commit.snapshot_revision
    destinations = {
        **{student_id: "alpha" for student_id in STUDENT_IDS[:3]},
        **{student_id: "beta" for student_id in STUDENT_IDS[3:]},
    }
    for offset, student_id in enumerate(STUDENT_IDS, start=3):
        placed = place_student_in_plan(
            PlaceStudentInPlanRequest(
                class_id=CLASS_ID,
                activity_id=ACTIVITY_ID,
                group_plan_id="plan-manual",
                student_id=student_id,
                planned_group_key=destinations[student_id],
                expected_snapshot_revision=current_revision,
                actor=_actor(),
            ),
            workspace_root=root,
            clock=lambda offset=offset: _clock(offset),
        )
        assert placed.changed is True
        current_revision = placed.detail.summary.snapshot_revision

    detail = show_group_plan(
        CLASS_ID,
        ACTIVITY_ID,
        "plan-manual",
        workspace_root=root,
    )
    assert detail.plan.unresolved_student_ids == ()
    assert tuple(
        (group.planned_group_key, group.student_ids)
        for group in detail.plan.proposed_groups
    ) == (
        ("alpha", STUDENT_IDS[:3]),
        ("beta", STUDENT_IDS[3:]),
    )
    _assert_no_canonical_group_state(root)

    application, result, _ = _apply_approved_plan(
        root,
        group_plan_id="plan-manual",
        draft_snapshot_revision=current_revision,
        application_id="apply-manual-acceptance",
        clock_minute=10,
    )
    assert application.group_count == 2
    assert application.membership_count == 6
    assert result.group_count == 2
    assert result.membership_count == 6


def test_arrangement_csv_remains_a_plan_until_explicit_application(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    source = tmp_path / "arrangement.csv"
    source.write_text(
        "student_id,group\n"
        "student-1,alpha\n"
        "student-2,alpha\n"
        "student-3,alpha\n"
        "student-4,beta\n"
        "student-5,beta\n"
        "student-6,beta\n",
        encoding="utf-8",
    )
    imported = import_arrangement_group_plan(
        ImportArrangementGroupPlanRequest(
            class_id=CLASS_ID,
            activity_id=ACTIVITY_ID,
            group_plan_id="plan-arrangement",
            csv_path=source,
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(2),
    )
    assert imported.data_row_count == 6
    assert imported.proposed_group_count == 2
    assert imported.assigned_student_count == 6
    assert imported.unresolved_student_count == 0

    detail = show_group_plan(
        CLASS_ID,
        ACTIVITY_ID,
        "plan-arrangement",
        workspace_root=root,
    )
    assert detail.plan.strategy == "imported_arrangement"
    assert detail.plan.status == "draft"
    assert detail.plan.unresolved_student_ids == ()
    assert tuple(
        (group.planned_group_key, group.student_ids)
        for group in detail.plan.proposed_groups
    ) == (
        ("alpha", STUDENT_IDS[:3]),
        ("beta", STUDENT_IDS[3:]),
    )
    assert str(source) not in repr(detail.plan)
    _assert_no_canonical_group_state(root)

    application, result, _ = _apply_approved_plan(
        root,
        group_plan_id="plan-arrangement",
        draft_snapshot_revision=imported.mutation.commit.snapshot_revision,
        application_id="apply-arrangement-acceptance",
        clock_minute=10,
    )
    assert application.group_count == 2
    assert application.membership_count == 6
    assert result.group_count == 2
    assert result.membership_count == 6


def test_random_group_plan_is_reproducible_then_explicitly_applied(
    tmp_path: Path,
) -> None:
    first_root, first_revision = _workspace(tmp_path / "first")
    first = create_random_group_plan(
        CreateRandomGroupPlanRequest(
            class_id=CLASS_ID,
            activity_id=ACTIVITY_ID,
            group_plan_id="plan-random",
            expected_snapshot_revision=first_revision,
            actor=_actor(),
            seed="issue69-seed",
            target_group_count=2,
        ),
        workspace_root=first_root,
        clock=lambda: _clock(2),
    )
    first_detail = show_group_plan(
        CLASS_ID,
        ACTIVITY_ID,
        "plan-random",
        workspace_root=first_root,
    )
    assert first.group_count == 2
    assert first.assigned_student_count == 6
    assert first.group_sizes == (3, 3)
    assert first_detail.plan.strategy == "random"
    assert first_detail.plan.seed == "issue69-seed"
    assert first_detail.plan.target_group_count == 2
    assert first_detail.plan.unresolved_student_ids == ()
    _assert_no_canonical_group_state(first_root)

    second_root, second_revision = _workspace(tmp_path / "second")
    second = create_random_group_plan(
        CreateRandomGroupPlanRequest(
            class_id=CLASS_ID,
            activity_id=ACTIVITY_ID,
            group_plan_id="plan-random",
            expected_snapshot_revision=second_revision,
            actor=_actor(),
            seed="issue69-seed",
            target_group_count=2,
        ),
        workspace_root=second_root,
        clock=lambda: _clock(2),
    )
    second_detail = show_group_plan(
        CLASS_ID,
        ACTIVITY_ID,
        "plan-random",
        workspace_root=second_root,
    )
    assert second.group_sizes == first.group_sizes
    assert second_detail.plan.proposed_groups == first_detail.plan.proposed_groups

    application, result, _ = _apply_approved_plan(
        first_root,
        group_plan_id="plan-random",
        draft_snapshot_revision=first.mutation.commit.snapshot_revision,
        application_id="apply-random-acceptance",
        clock_minute=10,
    )
    assert application.group_count == 2
    assert application.membership_count == 6
    assert result.group_count == 2
    assert result.membership_count == 6


def test_similar_signal_plan_binds_core_digest_then_explicitly_applies(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    signal, canonical_digest, created, detail = _create_signal_plan(
        root,
        revision=revision,
        strategy="similar_signal",
        group_plan_id="plan-similar",
    )
    assert tuple(
        (group.planned_group_key, group.student_ids)
        for group in detail.plan.proposed_groups
    ) == (
        ("similar-1", STUDENT_IDS[:3]),
        ("similar-2", STUDENT_IDS[3:]),
    )

    application, result, graph = _apply_approved_plan(
        root,
        group_plan_id="plan-similar",
        draft_snapshot_revision=created.mutation.commit.snapshot_revision,
        application_id="apply-similar-acceptance",
        clock_minute=10,
    )
    assert application.group_count == 2
    assert application.membership_count == 6
    assert result.group_count == 2
    assert result.membership_count == 6
    _assert_signal_metadata_stays_on_plan(
        graph,
        group_plan_id="plan-similar",
        signal=signal,
        canonical_digest=canonical_digest,
    )


def test_mixed_signal_plan_binds_core_digest_then_explicitly_applies(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    signal, canonical_digest, created, detail = _create_signal_plan(
        root,
        revision=revision,
        strategy="mixed_signal",
        group_plan_id="plan-mixed",
    )
    assert tuple(
        (group.planned_group_key, group.student_ids)
        for group in detail.plan.proposed_groups
    ) == (
        ("mixed-1", ("student-2", "student-5", "student-6")),
        ("mixed-2", ("student-1", "student-3", "student-4")),
    )

    application, result, graph = _apply_approved_plan(
        root,
        group_plan_id="plan-mixed",
        draft_snapshot_revision=created.mutation.commit.snapshot_revision,
        application_id="apply-mixed-acceptance",
        clock_minute=10,
    )
    assert application.group_count == 2
    assert application.membership_count == 6
    assert result.group_count == 2
    assert result.membership_count == 6
    _assert_signal_metadata_stays_on_plan(
        graph,
        group_plan_id="plan-mixed",
        signal=signal,
        canonical_digest=canonical_digest,
    )




def _partial_core_signal() -> GroupingSignalSet:
    dimension_id = "proficiency-band"
    return GroupingSignalSet(
        schema_version="1",
        record_type="grouping_signal_set",
        signal_set_id="signal-partial-acceptance",
        class_id=CLASS_ID,
        created_at=_clock(1),
        source=GroupingSignalSource(
            kind="module_generated",
            module_id="meridian",
            snapshot_id="academic-period-2026-q1-partial",
            snapshot_digest_algorithm="sha256",
            snapshot_digest="c" * 64,
        ),
        dimensions=(
            GroupingSignalDimension(
                dimension_id=dimension_id,
                band_count=4,
            ),
        ),
        student_bands=(
            GroupingSignalStudentBand(
                student_id="student-1",
                dimension_id=dimension_id,
                band=4,
            ),
            GroupingSignalStudentBand(
                student_id="student-2",
                dimension_id=dimension_id,
                band=1,
            ),
            GroupingSignalStudentBand(
                student_id="student-3",
                dimension_id=dimension_id,
                band=3,
            ),
            GroupingSignalStudentBand(
                student_id="student-4",
                dimension_id=dimension_id,
                band=2,
            ),
        ),
    )


def _create_partial_signal_plan(
    root: Path,
    *,
    revision: int,
    group_plan_id: str,
):
    signal = _partial_core_signal()
    write_grouping_signal(root, signal)
    canonical_digest = calculate_grouping_signal_digest(signal)
    created = create_signal_group_plan(
        CreateSignalGroupPlanRequest(
            class_id=CLASS_ID,
            activity_id=ACTIVITY_ID,
            group_plan_id=group_plan_id,
            strategy="mixed_signal",
            signal_set_id=signal.signal_set_id,
            dimension_id="proficiency-band",
            expected_snapshot_revision=revision,
            actor=_actor(),
            target_group_count=2,
            expected_roster_student_ids=STUDENT_IDS,
            expected_signal_set_digest=canonical_digest,
        ),
        workspace_root=root,
        clock=lambda: _clock(2),
    )
    detail = show_group_plan(
        CLASS_ID,
        ACTIVITY_ID,
        group_plan_id,
        workspace_root=root,
    )
    inspection = inspect_group_plan_missing_signal(
        CLASS_ID,
        ACTIVITY_ID,
        group_plan_id,
        workspace_root=root,
    )
    assert created.assigned_student_count == 4
    assert created.unresolved_student_count == 2
    assert detail.plan.unresolved_student_ids == ("student-5", "student-6")
    assert inspection.missing_student_ids == ("student-5", "student-6")
    assert inspection.missing_assigned_student_ids == ()
    assert inspection.missing_unresolved_student_ids == inspection.missing_student_ids
    assert inspection.signal_set_digest == canonical_digest
    assert inspection.signal_set_digest != signal.source.snapshot_digest
    assert {entry.student_id for entry in signal.student_bands} == set(STUDENT_IDS[:4])
    _assert_no_canonical_group_state(root)
    return signal, canonical_digest, created, detail, inspection


def _set_missing_disposition(
    root: Path,
    *,
    group_plan_id: str,
    disposition: str,
    expected_snapshot_revision: int,
    random_seed: str | None = None,
    clock_minute: int,
):
    return set_missing_signal_disposition(
        SetMissingSignalDispositionRequest(
            class_id=CLASS_ID,
            activity_id=ACTIVITY_ID,
            group_plan_id=group_plan_id,
            disposition=disposition,
            expected_snapshot_revision=expected_snapshot_revision,
            actor=_actor(),
            random_seed=random_seed,
        ),
        workspace_root=root,
        clock=lambda: _clock(clock_minute),
    )


def _student_group_mapping(detail) -> dict[str, str]:
    return {
        student_id: group.planned_group_key
        for group in detail.plan.proposed_groups
        for student_id in group.student_ids
    }


def test_missing_signal_manual_resolution_requires_placement_then_applies(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    signal, canonical_digest, created, _, inspection = _create_partial_signal_plan(
        root,
        revision=revision,
        group_plan_id="plan-missing-manual",
    )
    assert inspection.missing_student_ids == ("student-5", "student-6")

    current_revision = created.mutation.commit.snapshot_revision
    for minute, (student_id, group_key) in enumerate(
        (("student-5", "mixed-1"), ("student-6", "mixed-2")),
        start=3,
    ):
        placed = place_student_in_plan(
            PlaceStudentInPlanRequest(
                class_id=CLASS_ID,
                activity_id=ACTIVITY_ID,
                group_plan_id="plan-missing-manual",
                student_id=student_id,
                planned_group_key=group_key,
                expected_snapshot_revision=current_revision,
                actor=_actor(),
            ),
            workspace_root=root,
            clock=lambda minute=minute: _clock(minute),
        )
        current_revision = placed.detail.summary.snapshot_revision

    placed_detail = show_group_plan(
        CLASS_ID,
        ACTIVITY_ID,
        "plan-missing-manual",
        workspace_root=root,
    )
    assert placed_detail.plan.unresolved_student_ids == ()
    placed_inspection = inspect_group_plan_missing_signal(
        CLASS_ID,
        ACTIVITY_ID,
        "plan-missing-manual",
        workspace_root=root,
    )
    assert placed_inspection.missing_student_ids == ("student-5", "student-6")
    assert placed_inspection.missing_assigned_student_ids == (
        "student-5",
        "student-6",
    )
    assert placed_inspection.missing_unresolved_student_ids == ()

    disposition = _set_missing_disposition(
        root,
        group_plan_id="plan-missing-manual",
        disposition="manual",
        expected_snapshot_revision=current_revision,
        clock_minute=5,
    )
    detail = show_group_plan(
        CLASS_ID,
        ACTIVITY_ID,
        "plan-missing-manual",
        workspace_root=root,
    )
    assert disposition.disposition == "manual"
    assert disposition.missing_student_count == 2
    assert disposition.unresolved_student_count == 0
    assert disposition.random_seed is None
    assert detail.plan.missing_signal_disposition == "manual"
    assert detail.plan.missing_signal_random_seed is None
    assert detail.plan.unresolved_student_ids == ()
    _assert_no_canonical_group_state(root)

    application, result, graph = _apply_approved_plan(
        root,
        group_plan_id="plan-missing-manual",
        draft_snapshot_revision=disposition.mutation.commit.snapshot_revision,
        application_id="apply-missing-manual-acceptance",
        clock_minute=10,
    )
    assert application.membership_count == 6
    assert result.membership_count == 6
    _assert_signal_metadata_stays_on_plan(
        graph,
        group_plan_id="plan-missing-manual",
        signal=signal,
        canonical_digest=canonical_digest,
    )
    applied_plan = next(
        plan
        for plan in graph.group_plans
        if plan.group_plan_id == "plan-missing-manual"
    )
    assert applied_plan.missing_signal_disposition == "manual"
    assert applied_plan.missing_signal_random_seed is None


def test_missing_signal_random_places_only_missing_reproducibly_then_applies(
    tmp_path: Path,
) -> None:
    first_root, first_revision = _workspace(tmp_path / "first")
    signal, canonical_digest, first_created, first_before, _ = (
        _create_partial_signal_plan(
            first_root,
            revision=first_revision,
            group_plan_id="plan-missing-random",
        )
    )
    represented_before = _student_group_mapping(first_before)
    assert set(represented_before) == set(STUDENT_IDS[:4])

    first_disposition = _set_missing_disposition(
        first_root,
        group_plan_id="plan-missing-random",
        disposition="random",
        random_seed="issue69-missing-seed",
        expected_snapshot_revision=first_created.mutation.commit.snapshot_revision,
        clock_minute=3,
    )
    first_after = show_group_plan(
        CLASS_ID,
        ACTIVITY_ID,
        "plan-missing-random",
        workspace_root=first_root,
    )
    represented_after = _student_group_mapping(first_after)
    assert all(
        represented_after[student_id] == group_key
        for student_id, group_key in represented_before.items()
    )
    assert set(represented_after) == set(STUDENT_IDS)
    assert first_after.plan.unresolved_student_ids == ()
    assert first_after.plan.missing_signal_disposition == "random"
    assert first_after.plan.missing_signal_random_seed == "issue69-missing-seed"
    assert first_disposition.random_seed == "issue69-missing-seed"

    second_root, second_revision = _workspace(tmp_path / "second")
    _, _, second_created, _, _ = _create_partial_signal_plan(
        second_root,
        revision=second_revision,
        group_plan_id="plan-missing-random",
    )
    _set_missing_disposition(
        second_root,
        group_plan_id="plan-missing-random",
        disposition="random",
        random_seed="issue69-missing-seed",
        expected_snapshot_revision=second_created.mutation.commit.snapshot_revision,
        clock_minute=3,
    )
    second_after = show_group_plan(
        CLASS_ID,
        ACTIVITY_ID,
        "plan-missing-random",
        workspace_root=second_root,
    )
    assert second_after.plan.proposed_groups == first_after.plan.proposed_groups

    application, result, graph = _apply_approved_plan(
        first_root,
        group_plan_id="plan-missing-random",
        draft_snapshot_revision=first_disposition.mutation.commit.snapshot_revision,
        application_id="apply-missing-random-acceptance",
        clock_minute=10,
    )
    assert application.membership_count == 6
    assert result.membership_count == 6
    _assert_signal_metadata_stays_on_plan(
        graph,
        group_plan_id="plan-missing-random",
        signal=signal,
        canonical_digest=canonical_digest,
    )
    applied_plan = next(
        plan
        for plan in graph.group_plans
        if plan.group_plan_id == "plan-missing-random"
    )
    assert applied_plan.missing_signal_disposition == "random"
    assert applied_plan.missing_signal_random_seed == "issue69-missing-seed"


def test_missing_signal_leave_unassigned_applies_without_missing_memberships(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    signal, canonical_digest, created, before, inspection = _create_partial_signal_plan(
        root,
        revision=revision,
        group_plan_id="plan-missing-leave",
    )
    represented_mapping = _student_group_mapping(before)
    assert set(represented_mapping) == set(STUDENT_IDS[:4])
    assert inspection.missing_student_ids == ("student-5", "student-6")

    disposition = _set_missing_disposition(
        root,
        group_plan_id="plan-missing-leave",
        disposition="leave_unassigned",
        expected_snapshot_revision=created.mutation.commit.snapshot_revision,
        clock_minute=3,
    )
    detail = show_group_plan(
        CLASS_ID,
        ACTIVITY_ID,
        "plan-missing-leave",
        workspace_root=root,
    )
    assert disposition.disposition == "leave_unassigned"
    assert disposition.unresolved_student_count == 2
    assert detail.plan.unresolved_student_ids == ("student-5", "student-6")
    assert detail.plan.missing_signal_disposition == "leave_unassigned"
    assert detail.plan.missing_signal_random_seed is None
    _assert_no_canonical_group_state(root)

    application, result, graph = _apply_approved_plan(
        root,
        group_plan_id="plan-missing-leave",
        draft_snapshot_revision=disposition.mutation.commit.snapshot_revision,
        application_id="apply-missing-leave-acceptance",
        clock_minute=10,
        expected_unresolved_student_ids=("student-5", "student-6"),
    )
    assert application.membership_count == 4
    assert result.membership_count == 4
    assert result.unresolved_count == 2
    membership_students = {
        membership.participant_reference.participant_id
        for membership in graph.memberships
    }
    assert membership_students == set(STUDENT_IDS[:4])
    assert membership_students.isdisjoint({"student-5", "student-6"})
    assert _student_group_mapping(detail) == represented_mapping
    _assert_signal_metadata_stays_on_plan(
        graph,
        group_plan_id="plan-missing-leave",
        signal=signal,
        canonical_digest=canonical_digest,
    )
    applied_plan = next(
        plan for plan in graph.group_plans if plan.group_plan_id == "plan-missing-leave"
    )
    assert applied_plan.unresolved_student_ids == ("student-5", "student-6")
    assert applied_plan.missing_signal_disposition == "leave_unassigned"
    assert applied_plan.missing_signal_random_seed is None
