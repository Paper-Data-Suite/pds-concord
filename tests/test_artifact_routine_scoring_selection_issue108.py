from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

import concord.workflows.artifact_routine_scoring_selection as selection
from concord.models.common import (
    ConcordRecordReference,
    ParticipantReference,
    ScoreTargetReference,
    SubjectReference,
)


def _criterion(
    criterion_id: str,
    *,
    kind: str = "standard_backed",
    standard_id: str | None = "std-1",
    targets: tuple[str, ...] = ("core_student",),
    default_scale_id: str | None = "scale-1",
) -> object:
    return SimpleNamespace(
        criterion_id=criterion_id,
        criterion_kind=kind,
        standard_id=standard_id,
        supported_target_kinds=targets,
        default_scoring_scale_id=default_scale_id,
    )


def _scale(scale_id: str, *, status: str = "active") -> object:
    return SimpleNamespace(
        scoring_scale_id=scale_id,
        status=status,
    )


def _context(
    *,
    orientation: str = "mixed",
    focus_standard_ids: tuple[str, ...] = ("std-1",),
    criteria: tuple[object, ...] | None = None,
    scales: tuple[object, ...] = (_scale("scale-1"), _scale("scale-2")),
    subjects: tuple[SubjectReference, ...] | None = None,
    authors: tuple[object, ...] | None = None,
    group_id: str | None = "group-1",
    session_id: str | None = "session-1",
    eligible: bool = True,
) -> Any:
    if criteria is None:
        criteria = (
            _criterion(
                "criterion-all",
                targets=(
                    "core_student",
                    "concord_group",
                    "concord_session",
                    "concord_artifact_instance",
                    "concord_activity",
                ),
            ),
        )
    if subjects is None:
        subjects = (
            SubjectReference(
                subject_kind="core_student",
                subject_id="student-1",
                owning_system="core",
            ),
            SubjectReference(
                subject_kind="concord_session",
                subject_id="session-1",
                owning_system="concord",
            ),
        )
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
            SimpleNamespace(
                attribution_status="confirmed",
                author_reference=ConcordRecordReference(
                    record_kind="group",
                    record_id="group-1",
                ),
                represented_group_id=None,
            ),
        )
    return SimpleNamespace(
        activity_id="activity-1",
        scoring_orientation=orientation,
        focus_standard_ids=focus_standard_ids,
        artifact=SimpleNamespace(
            artifact_instance_id="artifact-1",
            activity_id="activity-1",
            group_id=group_id,
            session_id=session_id,
        ),
        subject_context_candidates=subjects,
        current_authors=authors,
        current_groups=(
            SimpleNamespace(group_id="group-1", activity_id="activity-1"),
        ),
        current_sessions=(
            SimpleNamespace(session_id="session-1", activity_id="activity-1"),
        ),
        eligible_criteria=criteria,
        current_scoring_scales=scales,
        eligibility=SimpleNamespace(
            routine_scoring_eligible=eligible,
            exception_reasons=() if eligible else ("synthetic blocker",),
        ),
    )


def _candidate_map(options: selection.RoutineScoreTargetOptions) -> dict[str, object]:
    return {
        item.target_reference.target_id: item
        for item in options.candidates
    }


def test_target_options_project_candidates_without_selecting_one() -> None:
    options = selection.routine_target_options(_context())  # type: ignore[arg-type]
    candidates = _candidate_map(options)

    assert options.supported_target_kinds == (
        "core_student",
        "concord_group",
        "concord_session",
        "concord_artifact_instance",
        "concord_activity",
    )
    assert tuple(candidates) == (
        "student-1",
        "session-1",
        "group-1",
        "artifact-1",
        "activity-1",
    )
    assert candidates["student-1"].candidate_sources == (
        "artifact_subject",
        "artifact_author",
    )
    assert candidates["group-1"].candidate_sources == (
        "artifact_author",
        "artifact_group",
    )
    assert candidates["session-1"].candidate_sources == (
        "artifact_subject",
        "artifact_session",
    )
    assert not hasattr(options, "selected_target")


def test_unconfirmed_author_does_not_become_target_candidate() -> None:
    authors = (
        SimpleNamespace(
            attribution_status="proposed",
            author_reference=ParticipantReference(
                participant_kind="core_student",
                participant_id="student-2",
                owning_system="core",
            ),
            represented_group_id=None,
        ),
    )
    options = selection.routine_target_options(
        _context(authors=authors)  # type: ignore[arg-type]
    )

    assert "student-2" not in _candidate_map(options)


def test_external_subject_is_not_converted_to_score_target() -> None:
    subjects = (
        SubjectReference(
            subject_kind="external_record",
            subject_id="external-1",
            owning_system="other_system",
        ),
    )
    options = selection.routine_target_options(
        _context(subjects=subjects, authors=())  # type: ignore[arg-type]
    )

    assert "external-1" not in _candidate_map(options)


def test_supported_target_kinds_survive_without_likely_candidate() -> None:
    criterion = _criterion(
        "criterion-1",
        targets=("core_student", "concord_group"),
    )
    options = selection.routine_target_options(
        _context(
            criteria=(criterion,),
            subjects=(),
            authors=(),
            group_id=None,
            session_id=None,
        )  # type: ignore[arg-type]
    )

    assert options.candidates == ()
    assert options.supported_target_kinds == (
        "core_student",
        "concord_group",
    )


def test_explicit_target_filters_criteria_by_target_kind() -> None:
    criteria = (
        _criterion("student", targets=("core_student",)),
        _criterion("artifact", targets=("concord_artifact_instance",)),
        _criterion(
            "both",
            targets=("core_student", "concord_artifact_instance"),
        ),
    )
    context = _context(criteria=criteria)
    target = ScoreTargetReference(
        target_kind="core_student",
        target_id="student-1",
        owning_system="core",
    )

    projected = selection.routine_criteria_for_target(
        context,  # type: ignore[arg-type]
        target,
    )

    assert tuple(item.criterion_id for item in projected) == (
        "student",
        "both",
    )


def test_non_candidate_target_fails_closed() -> None:
    target = ScoreTargetReference(
        target_kind="core_student",
        target_id="student-99",
        owning_system="core",
    )

    with pytest.raises(
        selection.ConcordWorkflowValidationError,
        match="explicitly chosen from current candidates",
    ):
        selection.routine_criteria_for_target(
            _context(),  # type: ignore[arg-type]
            target,
        )


def test_activity_orientation_and_focus_standards_filter_criteria() -> None:
    criteria = (
        _criterion("focus-standard", standard_id="std-1"),
        _criterion("other-standard", standard_id="std-2"),
        _criterion(
            "local",
            kind="local",
            standard_id=None,
            default_scale_id=None,
        ),
    )
    target = ScoreTargetReference(
        target_kind="core_student",
        target_id="student-1",
        owning_system="core",
    )

    mixed = selection.routine_criteria_for_target(
        _context(criteria=criteria),  # type: ignore[arg-type]
        target,
    )
    standards_only = selection.routine_criteria_for_target(
        _context(
            criteria=criteria,
            orientation="standards_based",
        ),  # type: ignore[arg-type]
        target,
    )

    assert tuple(item.criterion_id for item in mixed) == (
        "focus-standard",
        "local",
    )
    assert tuple(item.criterion_id for item in standards_only) == (
        "focus-standard",
    )


def test_no_canonically_compatible_criterion_fails_closed() -> None:
    criteria = (
        _criterion(
            "local",
            kind="local",
            standard_id=None,
            default_scale_id=None,
        ),
    )

    with pytest.raises(
        selection.ConcordWorkflowValidationError,
        match="no Criterion compatible",
    ):
        selection.routine_target_options(
            _context(
                criteria=criteria,
                orientation="standards_based",
            )  # type: ignore[arg-type]
        )


def test_valid_current_default_scale_is_visible_but_not_a_score_value() -> None:
    context = _context()
    target = ScoreTargetReference(
        target_kind="core_student",
        target_id="student-1",
        owning_system="core",
    )

    options = selection.routine_scale_options(
        context,  # type: ignore[arg-type]
        target,
        "criterion-all",
    )

    assert tuple(item.scoring_scale_id for item in options.scales) == (
        "scale-1",
        "scale-2",
    )
    assert options.configured_default_scoring_scale_id == "scale-1"
    assert options.default_scale is not None
    assert options.default_scale.scoring_scale_id == "scale-1"
    assert options.default_scale_status == "valid"
    assert not hasattr(options, "value")


def test_missing_or_historical_default_is_not_substituted() -> None:
    criterion = _criterion("criterion-1", default_scale_id="scale-old")
    target = ScoreTargetReference(
        target_kind="core_student",
        target_id="student-1",
        owning_system="core",
    )

    options = selection.routine_scale_options(
        _context(
            criteria=(criterion,),
            scales=(_scale("scale-new"),),
        ),  # type: ignore[arg-type]
        target,
        "criterion-1",
    )

    assert options.default_scale is None
    assert options.default_scale_status == "missing_or_historical"
    assert tuple(item.scoring_scale_id for item in options.scales) == (
        "scale-new",
    )


def test_inactive_current_default_is_not_used() -> None:
    criterion = _criterion("criterion-1", default_scale_id="scale-1")
    target = ScoreTargetReference(
        target_kind="core_student",
        target_id="student-1",
        owning_system="core",
    )

    options = selection.routine_scale_options(
        _context(
            criteria=(criterion,),
            scales=(
                _scale("scale-1", status="inactive"),
                _scale("scale-2"),
            ),
        ),  # type: ignore[arg-type]
        target,
        "criterion-1",
    )

    assert options.default_scale is None
    assert options.default_scale_status == "not_active"
    assert tuple(item.scoring_scale_id for item in options.scales) == (
        "scale-2",
    )


def test_no_configured_default_requires_explicit_scale_choice() -> None:
    criterion = _criterion("criterion-1", default_scale_id=None)
    target = ScoreTargetReference(
        target_kind="core_student",
        target_id="student-1",
        owning_system="core",
    )

    options = selection.routine_scale_options(
        _context(criteria=(criterion,)),  # type: ignore[arg-type]
        target,
        "criterion-1",
    )

    assert options.configured_default_scoring_scale_id is None
    assert options.default_scale is None
    assert options.default_scale_status == "not_configured"
    assert len(options.scales) == 2


def test_ineligible_projection_cannot_prepare_routine_choices() -> None:
    with pytest.raises(
        selection.ConcordWorkflowValidationError,
        match="synthetic blocker",
    ):
        selection.routine_target_options(
            _context(eligible=False)  # type: ignore[arg-type]
        )
