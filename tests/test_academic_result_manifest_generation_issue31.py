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
from pds_core.workspace import ensure_workspace_root

from concord.academic_result_manifest import (
    RevisionReason,
    academic_result_manifest_from_bytes,
)
from concord.academic_result_manifest_generation import (
    ConcordManifestGenerationConflictError,
    ConcordManifestGenerationValidationError,
    GenerateAcademicResultManifestRequest,
    academic_result_manifest_relative_path,
    generate_academic_result_manifest,
    list_academic_result_manifest_revisions,
    load_academic_result_manifest_head,
    load_academic_result_manifest_revision,
    manifest_generation_summary,
)
from concord.academic_work_registration import (
    register_concord_academic_work,
)
from concord.models import (
    PlannedGroup,
    PrivacyPolicy,
    ScoreTargetReference,
    ScoringScaleLevel,
    StatusReason,
    SubjectReference,
)
from concord.workflows import (
    AddScoreRequest,
    CreateActivityContextRequest,
    CreateCriterionSetRequest,
    CreateGroupPlanRequest,
    CreateGroupRequest,
    CreateScoringScaleRequest,
    CriterionSpec,
    ReplaceScoreRequest,
    SelectActivityCriterionSetsRequest,
    UpdateActivityRequest,
    WorkflowActor,
    add_score,
    create_activity_context,
    create_criterion_set,
    create_group,
    create_group_plan,
    create_scoring_scale,
    replace_score,
    select_activity_criterion_sets,
    update_activity,
)
from concord.workflows.context import actor_reference


def _clock(hour: int) -> datetime:
    return datetime(2026, 8, 14, hour, 0, tzinfo=timezone.utc)


def _actor() -> WorkflowActor:
    return WorkflowActor(
        actor_id="teacher-1",
        display_label="Synthetic Teacher",
        role_label="teacher",
    )


def _student_subject() -> SubjectReference:
    return SubjectReference(
        subject_kind="core_student",
        subject_id="student-1",
        owning_system="core",
    )


def _workspace(
    tmp_path: Path,
) -> tuple[Path, int]:
    root = ensure_workspace_root(tmp_path / "workspace")
    write_class_metadata_for_class(
        root,
        create_class_metadata(
            "class-1",
            "2026-2027",
            created_at=_clock(8),
        ),
    )
    write_class_roster(
        root,
        create_roster(
            "class-1",
            (
                {
                    "student_id": "student-1",
                    "last_name": "One",
                    "first_name": "Alex",
                    "period": "1",
                },
            ),
        ),
    )
    activity = create_activity_context(
        CreateActivityContextRequest(
            class_id="class-1",
            activity_id="activity-1",
            title="Synthetic Publication Activity",
            activity_type="project",
            scoring_orientation="local_criteria_only",
            session_id="session-1",
            actor=_actor(),
            activity_status="active",
            session_status="active",
            privacy_policy=PrivacyPolicy(
                classification="classroom_shared"
            ),
        ),
        workspace_root=root,
        clock=lambda: _clock(9),
    )
    scale = create_scoring_scale(
        CreateScoringScaleRequest(
            class_id="class-1",
            activity_id="activity-1",
            scoring_scale_id="scale-1",
            lineage_id="scale-lineage",
            name="Local scale",
            revision=1,
            scale_type="teacher_defined",
            levels=(
                ScoringScaleLevel(
                    value=1,
                    label="One",
                    meaning="First exact level.",
                ),
                ScoringScaleLevel(
                    value=2,
                    label="Two",
                    meaning="Second exact level.",
                ),
            ),
            status="active",
            expected_snapshot_revision=activity.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(10),
    )
    criterion_set = create_criterion_set(
        CreateCriterionSetRequest(
            class_id="class-1",
            activity_id="activity-1",
            criterion_set_id="set-1",
            lineage_id="set-lineage",
            name="Local criteria",
            purpose="Synthetic publication validation.",
            revision=1,
            scope="activity_specific",
            criterion_set_kind="local",
            criteria=(
                CriterionSpec(
                    criterion_id="criterion-1",
                    key="collaboration",
                    label="Collaboration",
                    definition="Demonstrates collaborative practice.",
                    criterion_kind="local",
                    supported_target_kinds=(
                        "core_student",
                        "concord_group",
                    ),
                    default_scoring_scale_id="scale-1",
                ),
            ),
            status="active",
            expected_snapshot_revision=scale.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(11),
    )
    selected = select_activity_criterion_sets(
        SelectActivityCriterionSetsRequest(
            class_id="class-1",
            activity_id="activity-1",
            criterion_set_ids=("set-1",),
            expected_snapshot_revision=(
                criterion_set.commit.snapshot_revision
            ),
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(12),
    )
    group = create_group(
        CreateGroupRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_id="group-1",
            label="Group One",
            status="active",
            expected_snapshot_revision=selected.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(13),
    )
    group_score = add_score(
        AddScoreRequest(
            class_id="class-1",
            activity_id="activity-1",
            score_record_id="score-group-1",
            target_reference=ScoreTargetReference(
                target_kind="concord_group",
                target_id="group-1",
                owning_system="concord",
            ),
            criterion_id="criterion-1",
            scoring_scale_id="scale-1",
            disposition="scored",
            value=1,
            basis="professional_judgment",
            rationale=(
                "Private teacher rationale must never appear in the manifest."
            ),
            privacy_policy=PrivacyPolicy(
                classification="group_and_teacher",
                audience_references=(
                    SubjectReference(
                        subject_kind="concord_group",
                        subject_id="group-1",
                        owning_system="concord",
                    ),
                ),
            ),
            expected_snapshot_revision=group.commit.snapshot_revision,
            actor=_actor(),
            session_id="session-1",
        ),
        workspace_root=root,
        clock=lambda: _clock(14),
    )
    absent_reason = StatusReason(
        reason_code="absent",
        recorded_by=actor_reference(_actor()),
        recorded_at=_clock(14).isoformat(),
        note="Private absence note must never appear in the manifest.",
    )
    absent = add_score(
        AddScoreRequest(
            class_id="class-1",
            activity_id="activity-1",
            score_record_id="score-absent",
            target_reference=ScoreTargetReference(
                target_kind="core_student",
                target_id="student-1",
                owning_system="core",
            ),
            criterion_id="criterion-1",
            scoring_scale_id="scale-1",
            disposition="absent",
            basis="professional_judgment",
            rationale="Private non-score rationale.",
            status_reason=absent_reason,
            privacy_policy=PrivacyPolicy(
                classification="teacher_and_subjects",
                audience_references=(_student_subject(),),
            ),
            expected_snapshot_revision=(
                group_score.commit.snapshot_revision
            ),
            actor=_actor(),
            session_id="session-1",
        ),
        workspace_root=root,
        clock=lambda: _clock(15),
    )
    register_concord_academic_work(
        root,
        "class-1",
        "activity-1",
        academic_intent="summative",
        lifecycle="active",
    )
    return root, absent.commit.snapshot_revision


def _request(
    revision: int,
    *,
    reason: RevisionReason = "initial",
) -> GenerateAcademicResultManifestRequest:
    return GenerateAcademicResultManifestRequest(
        class_id="class-1",
        activity_id="activity-1",
        expected_snapshot_revision=revision,
        actor=_actor(),
        revision_reason=reason,
    )


def test_generation_projects_native_scores_and_writes_revision_one(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    result = generate_academic_result_manifest(
        _request(revision),
        workspace_root=root,
        clock=lambda: _clock(16),
    )

    assert result.disposition == "created"
    assert result.revision == 1
    assert result.registration_revision == 1
    assert result.source_snapshot_revision == revision
    assert result.relative_path == (
        "classes/class-1/modules/concord/work/activity-1/"
        "exports/manifests/academic_results/1.json"
    )
    assert result.path.read_bytes() == result.content
    assert academic_result_manifest_from_bytes(result.content) == result.manifest
    assert result.manifest.projection.source_snapshot_revision == revision
    assert [item.score_record_id for item in result.manifest.scores] == [
        "score-absent",
        "score-group-1",
    ]
    group_score = result.manifest.scores[1]
    assert group_score.target_reference.target_kind == "concord_group"
    assert group_score.target_reference.target_id == "group-1"
    assert group_score.value == 1
    absent = result.manifest.scores[0]
    assert absent.disposition == "absent"
    assert absent.value is None
    assert absent.status_reason is not None
    assert absent.status_reason.reason_code == "absent"

    assert result.manifest.privacy.classification == "teacher_restricted"
    assert b"Private teacher rationale" not in result.content
    assert b"Private absence note" not in result.content
    assert b"Private non-score rationale" not in result.content
    assert b"display_label_snapshot" not in result.content
    assert b"role_snapshot" not in result.content

    replay = generate_academic_result_manifest(
        _request(revision),
        workspace_root=root,
        clock=lambda: _clock(17),
    )
    assert replay.disposition == "existing"
    assert replay.revision == 1
    assert replay.content == result.content

    summary = manifest_generation_summary(result)
    assert summary["score_count"] == 2
    assert summary["current_score_count"] == 2
    assert summary["historical_score_count"] == 0
    assert summary["non_score_count"] == 1
    assert summary["capabilities"] == ("criterion_scores",)


def test_unrelated_native_change_reuses_existing_semantic_projection(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    first = generate_academic_result_manifest(
        _request(revision),
        workspace_root=root,
        clock=lambda: _clock(16),
    )
    first_bytes = first.content

    updated = update_activity(
        UpdateActivityRequest(
            class_id="class-1",
            activity_id="activity-1",
            expected_snapshot_revision=revision,
            actor=_actor(),
            description=(
                "Operational description is intentionally outside the "
                "academic-result projection."
            ),
        ),
        workspace_root=root,
        clock=lambda: _clock(17),
    )
    second = generate_academic_result_manifest(
        _request(
            updated.commit.snapshot_revision,
            reason="native_state_change",
        ),
        workspace_root=root,
        clock=lambda: _clock(18),
    )

    assert second.disposition == "existing"
    assert second.revision == 1
    assert second.content == first_bytes
    assert second.source_snapshot_revision == revision
    assert second.manifest.projection.source_snapshot_revision == revision
    assert len(
        list_academic_result_manifest_revisions(root, first.manifest.work)
    ) == 1


def test_material_score_revision_creates_next_manifest_revision(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    first = generate_academic_result_manifest(
        _request(revision),
        workspace_root=root,
        clock=lambda: _clock(16),
    )
    first_bytes = first.content

    replacement = replace_score(
        ReplaceScoreRequest(
            class_id="class-1",
            activity_id="activity-1",
            score_record_id="score-group-1",
            replacement_score_record_id="score-group-2",
            correction_id="correction-score-group",
            reason="Additional observation changed the teacher judgment.",
            target_reference=ScoreTargetReference(
                target_kind="concord_group",
                target_id="group-1",
                owning_system="concord",
            ),
            criterion_id="criterion-1",
            scoring_scale_id="scale-1",
            disposition="scored",
            value=2,
            basis="professional_judgment",
            rationale="Revised private teacher rationale.",
            privacy_policy=PrivacyPolicy(
                classification="group_and_teacher",
                audience_references=(
                    SubjectReference(
                        subject_kind="concord_group",
                        subject_id="group-1",
                        owning_system="concord",
                    ),
                ),
            ),
            expected_snapshot_revision=revision,
            actor=_actor(),
            session_id="session-1",
        ),
        workspace_root=root,
        clock=lambda: _clock(17),
    )
    second = generate_academic_result_manifest(
        _request(
            replacement.commit.snapshot_revision,
            reason="native_state_change",
        ),
        workspace_root=root,
        clock=lambda: _clock(18),
    )

    assert second.disposition == "created"
    assert second.revision == 2
    assert second.manifest.projection.source_snapshot_revision == (
        replacement.commit.snapshot_revision
    )
    assert first.path.read_bytes() == first_bytes
    assert first.content != second.content
    assert first.manifest.projection.projection_digest != (
        second.manifest.projection.projection_digest
    )
    states = {
        item.score_record_id: item.current_state
        for item in second.manifest.scores
    }
    assert states["score-group-1"] == "superseded"
    assert states["score-group-2"] == "current"

    history = list_academic_result_manifest_revisions(
        root, first.manifest.work
    )
    assert [item.revision for item in history] == [1, 2]
    assert load_academic_result_manifest_revision(
        root, first.manifest.work, 1
    ).content == first_bytes
    assert load_academic_result_manifest_head(
        root, first.manifest.work
    ) == history[-1]


def test_generation_rejects_stale_snapshot_before_writing(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    updated = update_activity(
        UpdateActivityRequest(
            class_id="class-1",
            activity_id="activity-1",
            expected_snapshot_revision=revision,
            actor=_actor(),
            description="Native revision advances.",
        ),
        workspace_root=root,
        clock=lambda: _clock(16),
    )
    assert updated.commit.snapshot_revision > revision

    with pytest.raises(ConcordManifestGenerationConflictError):
        generate_academic_result_manifest(
            _request(revision),
            workspace_root=root,
            clock=lambda: _clock(17),
        )

    work = updated.commit.work
    assert list_academic_result_manifest_revisions(root, work) == ()


def test_generation_requires_explicit_registration(tmp_path: Path) -> None:
    root, _ = _workspace(tmp_path)

    # The exact Core path is intentionally not relied on here; create a second
    # unregistered Activity instead.
    activity = create_activity_context(
        CreateActivityContextRequest(
            class_id="class-1",
            activity_id="activity-unregistered",
            title="Unregistered Activity",
            activity_type="project",
            scoring_orientation="evidence_only",
            session_id="session-unregistered",
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(16),
    )

    with pytest.raises(
        ConcordManifestGenerationValidationError,
        match="explicit current Academic Work Registration",
    ):
        generate_academic_result_manifest(
            GenerateAcademicResultManifestRequest(
                class_id="class-1",
                activity_id="activity-unregistered",
                expected_snapshot_revision=activity.commit.snapshot_revision,
                actor=_actor(),
                revision_reason="initial",
            ),
            workspace_root=root,
            clock=lambda: _clock(17),
        )


def test_generation_rejects_registration_title_drift(tmp_path: Path) -> None:
    root, revision = _workspace(tmp_path)
    updated = update_activity(
        UpdateActivityRequest(
            class_id="class-1",
            activity_id="activity-1",
            expected_snapshot_revision=revision,
            actor=_actor(),
            title="Title Changed After Registration",
        ),
        workspace_root=root,
        clock=lambda: _clock(16),
    )

    with pytest.raises(
        ConcordManifestGenerationValidationError,
        match="explicitly update the registration",
    ):
        generate_academic_result_manifest(
            _request(updated.commit.snapshot_revision),
            workspace_root=root,
            clock=lambda: _clock(17),
        )


def test_manifest_path_helper_is_exact() -> None:
    work = ModuleWorkRef(
        module_id="concord",
        class_id="class-1",
        work_id="activity-1",
    )
    assert academic_result_manifest_relative_path(work, 7) == (
        "classes/class-1/modules/concord/work/activity-1/"
        "exports/manifests/academic_results/7.json"
    )


def test_group_plan_native_change_is_excluded_from_manifest_projection(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    first = generate_academic_result_manifest(
        _request(revision),
        workspace_root=root,
        clock=lambda: _clock(16),
    )
    plan = create_group_plan(
        CreateGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="private-plan-marker",
            strategy="similar_signal",
            expected_snapshot_revision=revision,
            actor=_actor(),
            proposed_groups=(
                PlannedGroup(
                    planned_group_key="private-planned-group-marker",
                    label="Private Planning Group",
                    student_ids=("student-1",),
                ),
            ),
            target_group_count=1,
            source_signal_set_id="private-signal-set",
            source_signal_set_digest="f" * 64,
            source_signal_dimension_id="private-dimension",
        ),
        workspace_root=root,
        clock=lambda: _clock(17),
    )
    second = generate_academic_result_manifest(
        _request(
            plan.commit.snapshot_revision,
            reason="native_state_change",
        ),
        workspace_root=root,
        clock=lambda: _clock(18),
    )

    assert second.disposition == "existing"
    assert second.revision == first.revision == 1
    assert second.content == first.content
    assert second.source_snapshot_revision == revision
    assert b"private-plan-marker" not in second.content
    assert b"private-planned-group-marker" not in second.content
    assert b"private-signal-set" not in second.content
    assert b"private-dimension" not in second.content
