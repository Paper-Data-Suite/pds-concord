from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from pathlib import Path

import pytest
from pds_core.routing_models import ModuleRecordRef, ModuleWorkRef

from concord.model_validation import ConcordRecordGraph
from concord.models import (
    Activity,
    ActorReference,
    Criterion,
    PrivacyPolicy,
    Provenance,
    ScoreRecord,
    ScoreTargetReference,
    ScoringScale,
    ScoringScaleLevel,
)
from concord.workflows import (
    SCORE_ANALYSIS_BASIS,
    STUDENT_FEEDBACK_BOUNDARY_STATEMENT,
    STUDENT_FEEDBACK_SCOPE,
    TARGET_DETAIL_SCOPE,
    StudentFeedbackProjection,
    StudentFeedbackResult,
    TargetScoreDetail,
    TargetScoreResult,
    student_feedback_projection_from_context,
    student_feedback_projection_from_target_detail,
)
from concord.workflows.activity_read import ActivityReadContext
from concord.workflows.errors import ConcordWorkflowValidationError


def _actor() -> ActorReference:
    return ActorReference(
        actor_kind="authorized_adult",
        actor_id="teacher-1",
        owning_system="concord",
        display_label_snapshot="Synthetic Teacher",
    )


def _provenance() -> Provenance:
    return Provenance(
        actor=_actor(),
        timestamp="2026-10-07T18:00:00+00:00",
        source_kind="manual",
    )


def _target(kind: str, target_id: str) -> ScoreTargetReference:
    return ScoreTargetReference(
        target_kind=kind,
        target_id=target_id,
        owning_system="core" if kind == "core_student" else "concord",
    )


def _activity() -> Activity:
    return Activity(
        activity_id="activity-1",
        class_reference=ModuleRecordRef(
            module_id="core",
            record_kind="class",
            record_id="class-1",
        ),
        title="Memoir Revision",
        activity_type="project",
        scoring_orientation="local_criteria_only",
        status="active",
        created_provenance=_provenance(),
    )


def _criterion(criterion_id: str, label: str) -> Criterion:
    return Criterion(
        criterion_id=criterion_id,
        criterion_set_id="set-1",
        key=criterion_id,
        label=label,
        definition=f"Synthetic definition for {label}.",
        criterion_kind="local",
        supported_target_kinds=(
            "core_student",
            "concord_group",
            "concord_artifact_instance",
            "concord_session",
            "concord_activity",
        ),
        status="active",
        created_provenance=_provenance(),
        default_scoring_scale_id="scale-1",
    )


def _scale() -> ScoringScale:
    return ScoringScale(
        scoring_scale_id="scale-1",
        lineage_id="scale-lineage",
        name="Four Levels",
        revision=1,
        scale_type="ordinal",
        levels=(
            ScoringScaleLevel(
                value=1,
                label="Beginning",
                meaning="Beginning evidence",
                position=1,
            ),
            ScoringScaleLevel(
                value=2,
                label="Developing",
                meaning="Developing evidence",
                position=2,
            ),
            ScoringScaleLevel(
                value=3,
                label="Meeting",
                meaning="Meeting evidence",
                position=3,
            ),
            ScoringScaleLevel(
                value=4,
                label="Exceeding",
                meaning="Exceeding evidence",
                position=4,
            ),
        ),
        status="active",
        created_provenance=_provenance(),
    )


def _score(
    score_record_id: str,
    *,
    target: ScoreTargetReference,
    criterion_id: str,
    value: int | None = 3,
    disposition: str = "scored",
    supersedes: str | None = None,
) -> ScoreRecord:
    return ScoreRecord(
        score_record_id=score_record_id,
        activity_id="activity-1",
        target_reference=target,
        criterion_id=criterion_id,
        score_kind="local",
        scoring_scale_id="scale-1",
        disposition=disposition,
        value=value,
        basis="professional_judgment",
        scorer=_actor(),
        scored_at="2026-10-07T18:05:00+00:00",
        rationale="Teacher-only rationale must never enter student feedback.",
        moderation_complete=disposition == "scored",
        privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
        session_id=None,
        supersedes_score_record_id=supersedes,
    )


def _context() -> ActivityReadContext:
    activity = _activity()
    criterion = _criterion("criterion-1", "Use of Evidence")
    target = _target("core_student", "student-1")
    old = _score(
        "score-old",
        target=target,
        criterion_id=criterion.criterion_id,
        value=2,
    )
    current = _score(
        "score-current",
        target=target,
        criterion_id=criterion.criterion_id,
        value=3,
        supersedes=old.score_record_id,
    )
    group = _score(
        "score-group",
        target=_target("concord_group", "group-1"),
        criterion_id=criterion.criterion_id,
        value=4,
    )
    return ActivityReadContext(
        root=Path("/synthetic/read-only"),
        work=ModuleWorkRef("concord", "class-1", "activity-1"),
        snapshot_revision=9,
        snapshot_sha256="a" * 64,
        graph=ConcordRecordGraph(
            activities=(activity,),
            criteria=(criterion,),
            scoring_scales=(_scale(),),
            score_records=(old, current, group),
        ),
        activity=activity,
    )


def _result(
    suffix: str,
    *,
    disposition: str = "scored",
    value: int | None = 3,
    value_label: str | None = "Meeting",
) -> TargetScoreResult:
    return TargetScoreResult(
        score_record_id=f"score-{suffix}",
        criterion_id=f"criterion-{suffix}",
        criterion_label=f"Criterion {suffix}",
        criterion_kind="local",
        standard_id=None,
        scoring_scale_id="scale-1",
        scoring_scale_name="Four Levels",
        scoring_scale_revision=1,
        scoring_scale_type="ordinal",
        disposition=disposition,
        value=value,
        value_label=value_label,
        basis="professional_judgment",
        session_id="session-internal",
        scored_at="2026-10-07T18:05:00+00:00",
    )


def _detail(
    *,
    target: ScoreTargetReference | None = None,
    activity_title: str = "Memoir Revision",
    results: tuple[TargetScoreResult, ...] = (),
) -> TargetScoreDetail:
    selected_target = target or _target("core_student", "student-1")
    return TargetScoreDetail(
        class_id="class-1",
        activity_id="activity-1",
        activity_title=activity_title,
        snapshot_revision=9,
        snapshot_sha256="f" * 64,
        score_basis=SCORE_ANALYSIS_BASIS,
        sharing_scope=TARGET_DETAIL_SCOPE,
        target_reference=selected_target,
        target_label="Teacher-local target label",
        current_score_count=len(results),
        results=results,
    )


def test_projection_is_explicit_allowlist_without_teacher_local_identity() -> None:
    projection = student_feedback_projection_from_target_detail(
        _detail(results=(_result("one"),)),
        student_display_name="Jane Doe",
        class_label="English 12 - Period 2",
    )

    assert projection == StudentFeedbackProjection(
        student_display_name="Jane Doe",
        activity_title="Memoir Revision",
        class_label="English 12 - Period 2",
        boundary_statement=STUDENT_FEEDBACK_BOUNDARY_STATEMENT,
        results=(
            StudentFeedbackResult(
                criterion_label="Criterion one",
                scoring_scale_name="Four Levels",
                disposition="scored",
                value=3,
                value_label="Meeting",
            ),
        ),
    )
    assert STUDENT_FEEDBACK_SCOPE == "student_scoped"
    assert projection.current_score_count == 1

    projection_fields = {item.name for item in fields(StudentFeedbackProjection)}
    result_fields = {item.name for item in fields(StudentFeedbackResult)}
    assert projection_fields == {
        "student_display_name",
        "activity_title",
        "class_label",
        "boundary_statement",
        "results",
    }
    assert result_fields == {
        "criterion_label",
        "scoring_scale_name",
        "disposition",
        "value",
        "value_label",
    }

    rendered = repr(projection)
    for forbidden in (
        "student-1",
        "score-one",
        "criterion-one",
        "scale-1",
        "session-internal",
        "professional_judgment",
        "teacher_restricted",
        "f" * 64,
    ):
        assert forbidden not in rendered

    with pytest.raises(FrozenInstanceError):
        projection.student_display_name = "Changed"  # type: ignore[misc]


def test_context_projection_uses_current_student_head_only() -> None:
    projection = student_feedback_projection_from_context(
        _context(),
        _target("core_student", "student-1"),
        student_display_name="Jane Doe",
    )

    assert projection.current_score_count == 1
    assert projection.results == (
        StudentFeedbackResult(
            criterion_label="Use of Evidence",
            scoring_scale_name="Four Levels",
            disposition="scored",
            value=3,
            value_label="Meeting",
        ),
    )
    rendered = repr(projection)
    assert "score-old" not in rendered
    assert "score-current" not in rendered
    assert "score-group" not in rendered
    assert "group-1" not in rendered


@pytest.mark.parametrize(
    "kind,target_id",
    (
        ("concord_group", "group-1"),
        ("concord_artifact_instance", "artifact-1"),
        ("concord_session", "session-1"),
        ("concord_activity", "activity-1"),
    ),
)
def test_nonstudent_targets_fail_closed(kind: str, target_id: str) -> None:
    with pytest.raises(
        ConcordWorkflowValidationError,
        match="Core-owned core_student",
    ):
        student_feedback_projection_from_target_detail(
            _detail(target=_target(kind, target_id)),
            student_display_name="Jane Doe",
        )


def test_non_score_dispositions_remain_exact_non_scores() -> None:
    dispositions = (
        "insufficient_evidence",
        "absent",
        "excused",
        "not_observed",
        "not_applicable",
        "deferred",
    )
    results = tuple(
        _result(
            disposition,
            disposition=disposition,
            value=None,
            value_label=None,
        )
        for disposition in dispositions
    )

    projection = student_feedback_projection_from_target_detail(
        _detail(results=results),
        student_display_name="Jane Doe",
    )

    assert tuple(item.disposition for item in projection.results) == dispositions
    assert all(item.value is None for item in projection.results)
    assert all(item.value_label is None for item in projection.results)
    assert all(item.value != 0 for item in projection.results)


def test_empty_current_student_feedback_does_not_infer_missing_or_required() -> None:
    projection = student_feedback_projection_from_target_detail(
        _detail(),
        student_display_name="Jane Doe",
    )

    assert projection.results == ()
    assert projection.current_score_count == 0
    names = {
        item.name
        for model in (StudentFeedbackProjection, StudentFeedbackResult)
        for item in fields(model)
    }
    assert not names.intersection(
        {
            "average",
            "grade",
            "mastery",
            "proficiency",
            "missing",
            "required",
            "percentage",
        }
    )


def test_public_semantic_text_policy_fails_closed_for_unsafe_display_text() -> None:
    with pytest.raises(
        ConcordWorkflowValidationError,
        match="student.display_name",
    ):
        student_feedback_projection_from_target_detail(
            _detail(results=(_result("one"),)),
            student_display_name=r"C:\Users\Teacher\student",
        )

    unsafe = _result("unsafe")
    unsafe = TargetScoreResult(
        score_record_id=unsafe.score_record_id,
        criterion_id=unsafe.criterion_id,
        criterion_label="Unsafe\nCriterion",
        criterion_kind=unsafe.criterion_kind,
        standard_id=unsafe.standard_id,
        scoring_scale_id=unsafe.scoring_scale_id,
        scoring_scale_name=unsafe.scoring_scale_name,
        scoring_scale_revision=unsafe.scoring_scale_revision,
        scoring_scale_type=unsafe.scoring_scale_type,
        disposition=unsafe.disposition,
        value=unsafe.value,
        value_label=unsafe.value_label,
        basis=unsafe.basis,
        session_id=unsafe.session_id,
        scored_at=unsafe.scored_at,
    )
    with pytest.raises(
        ConcordWorkflowValidationError,
        match="criterion.label",
    ):
        student_feedback_projection_from_target_detail(
            _detail(results=(unsafe,)),
            student_display_name="Jane Doe",
        )


def test_inconsistent_teacher_local_source_fails_closed() -> None:
    detail = _detail(results=(_result("one"),))
    inconsistent = TargetScoreDetail(
        class_id=detail.class_id,
        activity_id=detail.activity_id,
        activity_title=detail.activity_title,
        snapshot_revision=detail.snapshot_revision,
        snapshot_sha256=detail.snapshot_sha256,
        score_basis=detail.score_basis,
        sharing_scope=detail.sharing_scope,
        target_reference=detail.target_reference,
        target_label=detail.target_label,
        current_score_count=2,
        results=detail.results,
    )

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="source count",
    ):
        student_feedback_projection_from_target_detail(
            inconsistent,
            student_display_name="Jane Doe",
        )
