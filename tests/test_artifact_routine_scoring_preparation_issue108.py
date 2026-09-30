from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

import concord.workflows.artifact_routine_scoring_preparation as preparation
from concord.models.common import (
    EvidenceReference,
    ParticipantReference,
    ScoreTargetReference,
    SubjectReference,
)


def _criterion(
    criterion_id: str = "criterion-1",
    *,
    targets: tuple[str, ...] = ("core_student",),
    kind: str = "standard_backed",
    standard_id: str | None = "standard-1",
    default_scale_id: str | None = "scale-1",
) -> Any:
    return SimpleNamespace(
        criterion_id=criterion_id,
        criterion_set_id="set-1",
        label=f"Criterion {criterion_id}",
        criterion_kind=kind,
        standard_id=standard_id,
        supported_target_kinds=targets,
        default_scoring_scale_id=default_scale_id,
        status="active",
    )


def _scale(
    scale_id: str = "scale-1",
    *,
    status: str = "active",
    levels: tuple[tuple[object, str], ...] = (
        (1, "Developing"),
        (2, "Approaching"),
        (3, "Meeting"),
        (4, "Exceeding"),
    ),
) -> Any:
    scale_levels = tuple(
        SimpleNamespace(value=value, label=label)
        for value, label in levels
    )

    def level_for_value(value: object) -> Any | None:
        return next(
            (
                level
                for level in scale_levels
                if type(level.value) is type(value) and level.value == value
            ),
            None,
        )

    return SimpleNamespace(
        scoring_scale_id=scale_id,
        name=f"Scale {scale_id}",
        status=status,
        levels=scale_levels,
        level_for_value=level_for_value,
    )


def _subject(
    subject_id: str = "student-1",
    *,
    status: str = "confirmed",
    criterion_id: str | None = None,
) -> Any:
    return SimpleNamespace(
        confirmation_status=status,
        criterion_id=criterion_id,
        subject_reference=SubjectReference(
            subject_kind="core_student",
            subject_id=subject_id,
            owning_system="core",
        ),
    )


def _target(student_id: str = "student-1") -> ScoreTargetReference:
    return ScoreTargetReference(
        target_kind="core_student",
        target_id=student_id,
        owning_system="core",
    )


def _context(
    *,
    criteria: tuple[Any, ...] | None = None,
    scales: tuple[Any, ...] | None = None,
    subjects: tuple[Any, ...] | None = None,
    authors: tuple[Any, ...] | None = None,
    sessions: tuple[Any, ...] | None = None,
    artifact_session_id: str | None = "session-1",
    review_moderation: str = "not_required",
    evidence_moderation: str | None = None,
    scores: tuple[Any, ...] = (),
    eligible: bool = True,
) -> Any:
    if criteria is None:
        criteria = (_criterion(),)
    if scales is None:
        scales = (_scale(), _scale("scale-2"))
    if subjects is None:
        subjects = (_subject(),)
    if authors is None:
        authors = (
            SimpleNamespace(
                attribution_status="confirmed",
                author_reference=ParticipantReference(
                    participant_kind="core_student",
                    participant_id="student-1",
                    owning_system="core",
                ),
                represented_group_id=None,
            ),
        )
    if sessions is None:
        sessions = (
            SimpleNamespace(
                session_id="session-1",
                activity_id="activity-1",
            ),
            SimpleNamespace(
                session_id="session-2",
                activity_id="activity-1",
            ),
        )
    subject_references = tuple(
        item.subject_reference
        for item in subjects
        if item.confirmation_status == "confirmed"
    )
    return SimpleNamespace(
        class_id="class-1",
        activity_id="activity-1",
        scoring_orientation="mixed",
        focus_standard_ids=("standard-1",),
        artifact=SimpleNamespace(
            artifact_instance_id="artifact-1",
            activity_id="activity-1",
            group_id=None,
            session_id=artifact_session_id,
        ),
        current_review=SimpleNamespace(
            moderation_requirement=review_moderation,
        ),
        current_authors=authors,
        current_subjects=subjects,
        subject_context_candidates=subject_references,
        evidence_reference=EvidenceReference(
            evidence_kind="artifact_instance",
            owning_system="concord",
            record_id="artifact-1",
            moderation_requirement=evidence_moderation,
        ),
        eligible_criteria=criteria,
        current_scoring_scales=scales,
        current_sessions=sessions,
        current_groups=(),
        current_memberships=(),
        current_scores=scores,
        eligibility=SimpleNamespace(
            routine_scoring_eligible=eligible,
            exception_reasons=() if eligible else ("synthetic blocker",),
        ),
        snapshot_revision=7,
        snapshot_sha256="a" * 64,
    )


def _request(**overrides: object) -> preparation.RoutineScorePreparationRequest:
    values: dict[str, object] = {
        "target_reference": _target(),
        "criterion_id": "criterion-1",
        "scoring_scale_id": "scale-1",
        "value": 3,
    }
    values.update(overrides)
    return preparation.RoutineScorePreparationRequest(
        **values  # type: ignore[arg-type]
    )


def test_preview_preserves_exact_explicit_score_choices_and_artifact_evidence() -> None:
    subject = SubjectReference(
        subject_kind="core_student",
        subject_id="student-1",
        owning_system="core",
    )
    preview = preparation.prepare_routine_score_preview(
        _context(),  # type: ignore[arg-type]
        _request(
            session_id="session-2",
            subject_context=(subject,),
            significance="primary",
        ),
    )

    assert preview.target_reference == _target()
    assert preview.criterion_id == "criterion-1"
    assert preview.scoring_scale_id == "scale-1"
    assert preview.value == 3
    assert preview.selected_level.label == "Meeting"
    assert preview.session_id == "session-2"
    assert preview.disposition == "scored"
    assert preview.basis == "linked_evidence"
    assert preview.rationale is None
    assert preview.status_reason is None
    assert preview.privacy_policy.classification == "teacher_restricted"
    assert preview.evidence.evidence_reference.evidence_kind == "artifact_instance"
    assert preview.evidence.evidence_reference.owning_system == "concord"
    assert preview.evidence.evidence_reference.record_id == "artifact-1"
    assert preview.evidence.subject_context == (subject,)
    assert preview.evidence.significance == "primary"
    assert preview.snapshot_revision == 7
    assert preview.snapshot_sha256 == "a" * 64


def test_preview_has_no_internal_score_or_evidence_link_ids() -> None:
    preview = preparation.prepare_routine_score_preview(
        _context(),  # type: ignore[arg-type]
        _request(),
    )

    assert not hasattr(preview, "score_record_id")
    assert not hasattr(preview.evidence, "score_evidence_link_id")


def test_exact_scale_value_is_required_type_sensitively() -> None:
    scale = _scale(
        levels=((1, "Numeric one"), ("1", "String one")),
    )
    numeric = preparation.prepare_routine_score_preview(
        _context(scales=(scale,)),  # type: ignore[arg-type]
        _request(value=1),
    )
    string = preparation.prepare_routine_score_preview(
        _context(scales=(scale,)),  # type: ignore[arg-type]
        _request(value="1"),
    )

    assert numeric.selected_level.label == "Numeric one"
    assert string.selected_level.label == "String one"


def test_invalid_scale_value_fails_closed() -> None:
    with pytest.raises(
        preparation.ConcordWorkflowValidationError,
        match="exact level",
    ):
        preparation.prepare_routine_score_preview(
            _context(),  # type: ignore[arg-type]
            _request(value=99),
        )


def test_explicit_nondefault_active_scale_is_not_replaced_by_default() -> None:
    preview = preparation.prepare_routine_score_preview(
        _context(),  # type: ignore[arg-type]
        _request(scoring_scale_id="scale-2", value=4),
    )

    assert preview.scoring_scale_id == "scale-2"
    assert preview.value == 4


def test_inactive_or_unknown_scale_cannot_be_prepared() -> None:
    scales = (_scale("scale-1", status="inactive"), _scale("scale-2"))

    with pytest.raises(
        preparation.ConcordWorkflowValidationError,
        match="current active Scale",
    ):
        preparation.prepare_routine_score_preview(
            _context(scales=scales),  # type: ignore[arg-type]
            _request(scoring_scale_id="scale-1"),
        )


def test_artifact_session_is_not_guessed_when_teacher_selects_none() -> None:
    preview = preparation.prepare_routine_score_preview(
        _context(artifact_session_id="session-1"),  # type: ignore[arg-type]
        _request(session_id=None),
    )

    assert preview.session_id is None


def test_explicit_current_session_is_preserved_and_unknown_session_rejected() -> None:
    preview = preparation.prepare_routine_score_preview(
        _context(),  # type: ignore[arg-type]
        _request(session_id="session-1"),
    )
    assert preview.session_id == "session-1"

    with pytest.raises(
        preparation.ConcordWorkflowValidationError,
        match="current Session",
    ):
        preparation.prepare_routine_score_preview(
            _context(),  # type: ignore[arg-type]
            _request(session_id="session-99"),
        )


def test_subject_context_is_explicit_and_never_inferred_from_author() -> None:
    preview = preparation.prepare_routine_score_preview(
        _context(subjects=()),  # type: ignore[arg-type]
        _request(),
    )

    assert preview.target_reference == _target()
    assert preview.evidence.subject_context == ()


def test_subject_context_must_come_from_confirmed_current_artifact_subjects() -> None:
    other = SubjectReference(
        subject_kind="core_student",
        subject_id="student-2",
        owning_system="core",
    )

    with pytest.raises(
        preparation.ConcordWorkflowValidationError,
        match="current confirmed Artifact Subjects",
    ):
        preparation.prepare_routine_score_preview(
            _context(),  # type: ignore[arg-type]
            _request(subject_context=(other,)),
        )


def test_criterion_scoped_subject_options_do_not_leak_across_criteria() -> None:
    subjects = (
        _subject("student-1"),
        _subject("student-2", criterion_id="criterion-1"),
        _subject("student-3", criterion_id="criterion-2"),
    )
    criteria = (
        _criterion("criterion-1"),
        _criterion("criterion-2"),
    )

    options = preparation.routine_subject_context_options(
        _context(
            criteria=criteria,
            subjects=subjects,
        ),  # type: ignore[arg-type]
        _target(),
        "criterion-1",
    )

    assert tuple(item.subject_id for item in options) == (
        "student-1",
        "student-2",
    )


def test_relevance_uses_visible_deterministic_default_but_can_be_edited() -> None:
    default_preview = preparation.prepare_routine_score_preview(
        _context(),  # type: ignore[arg-type]
        _request(),
    )
    edited_preview = preparation.prepare_routine_score_preview(
        _context(),  # type: ignore[arg-type]
        _request(relevance_description="Exact returned work used for this judgment."),
    )

    assert (
        default_preview.evidence.relevance_description
        == "Returned Artifact evidence for this Score."
    )
    assert (
        edited_preview.evidence.relevance_description
        == "Exact returned work used for this judgment."
    )


def test_moderation_not_required_is_explicit_and_no_decision_is_created() -> None:
    preview = preparation.prepare_routine_score_preview(
        _context(),  # type: ignore[arg-type]
        _request(),
    )

    assert preview.evidence.moderation_required is False
    assert preview.evidence.moderation_requirement == "not_required"
    assert preview.evidence.moderation_record_id is None


def test_completed_review_moderation_is_preserved_in_preview() -> None:
    preview = preparation.prepare_routine_score_preview(
        _context(review_moderation="completed"),  # type: ignore[arg-type]
        _request(),
    )

    assert preview.evidence.moderation_required is False
    assert preview.evidence.moderation_requirement == "completed"


def test_required_moderation_fails_closed_before_any_mutation_boundary() -> None:
    with pytest.raises(
        preparation.ConcordWorkflowValidationError,
        match="requires Moderation",
    ):
        preparation.prepare_routine_score_preview(
            _context(evidence_moderation="required"),  # type: ignore[arg-type]
            _request(),
        )


def test_existing_current_score_is_surfaced_without_completion_policy() -> None:
    score = SimpleNamespace(
        score_record_id="score-existing",
        target_reference=_target(),
        criterion_id="criterion-1",
    )
    preview = preparation.prepare_routine_score_preview(
        _context(scores=(score,)),  # type: ignore[arg-type]
        _request(value=4),
    )

    assert preview.existing_current_score_ids == ("score-existing",)
    assert preview.value == 4


def test_non_candidate_target_still_fails_through_slice2_authority() -> None:
    with pytest.raises(
        preparation.ConcordWorkflowValidationError,
        match="current candidates",
    ):
        preparation.prepare_routine_score_preview(
            _context(),  # type: ignore[arg-type]
            _request(target_reference=_target("student-99")),
        )


def test_relevance_and_significance_are_validated_before_preview() -> None:
    with pytest.raises(
        preparation.ConcordWorkflowValidationError,
        match="relevance",
    ):
        preparation.prepare_routine_score_preview(
            _context(),  # type: ignore[arg-type]
            _request(relevance_description=""),
        )

    with pytest.raises(
        preparation.ConcordWorkflowValidationError,
        match="significance",
    ):
        preparation.prepare_routine_score_preview(
            _context(),  # type: ignore[arg-type]
            _request(significance="invented"),
        )
