from __future__ import annotations

from pathlib import Path

import pytest

from concord.workflows import (
    FEEDBACK_AVAILABILITY_DISTRIBUTABLE,
    FEEDBACK_AVAILABILITY_NONE,
    FEEDBACK_AVAILABILITY_UNRESOLVED,
    FEEDBACK_SELECTION_ALL,
    FEEDBACK_SELECTION_SELECTED,
    SCORE_ANALYSIS_BASIS,
    STUDENT_FEEDBACK_BOUNDARY_STATEMENT,
    STUDENT_FEEDBACK_PREPARATION_SCOPE,
    StudentFeedbackProjection,
    StudentFeedbackResult,
    StudentFeedbackRosterEntry,
    StudentFeedbackRosterPreparation,
    preview_student_feedback_distribution,
)
from concord.workflows.errors import ConcordWorkflowValidationError


def _projection(name: str) -> StudentFeedbackProjection:
    return StudentFeedbackProjection(
        student_display_name=name,
        activity_title="Memoir Revision",
        class_label=None,
        boundary_statement=STUDENT_FEEDBACK_BOUNDARY_STATEMENT,
        results=(
            StudentFeedbackResult(
                criterion_label="Use of Evidence",
                scoring_scale_name="Four Levels",
                disposition="scored",
                value=3,
                value_label="Meeting",
            ),
        ),
    )


def _preparation(
    *, unresolved_second: bool = False
) -> StudentFeedbackRosterPreparation:
    second = (
        StudentFeedbackRosterEntry(
            student_id="student-2",
            student_display_name=None,
            availability=FEEDBACK_AVAILABILITY_UNRESOLVED,
            projection=None,
            unresolved_reason="unsafe_student_feedback_semantics",
        )
        if unresolved_second
        else StudentFeedbackRosterEntry(
            student_id="student-2",
            student_display_name="John Smith",
            availability=FEEDBACK_AVAILABILITY_NONE,
            projection=StudentFeedbackProjection(
                student_display_name="John Smith",
                activity_title="Memoir Revision",
                class_label=None,
                boundary_statement=STUDENT_FEEDBACK_BOUNDARY_STATEMENT,
                results=(),
            ),
        )
    )
    return StudentFeedbackRosterPreparation(
        class_id="class-1",
        activity_id="activity-1",
        activity_title="Memoir Revision",
        snapshot_revision=10,
        snapshot_sha256="b" * 64,
        score_basis=SCORE_ANALYSIS_BASIS,
        sharing_scope=STUDENT_FEEDBACK_PREPARATION_SCOPE,
        entries=(
            StudentFeedbackRosterEntry(
                student_id="student-1",
                student_display_name="Jane Doe",
                availability=FEEDBACK_AVAILABILITY_DISTRIBUTABLE,
                projection=_projection("Jane Doe"),
            ),
            second,
            StudentFeedbackRosterEntry(
                student_id="student-3",
                student_display_name="Alex Rivera",
                availability=FEEDBACK_AVAILABILITY_DISTRIBUTABLE,
                projection=_projection("Alex Rivera"),
            ),
        ),
    )


def test_all_roster_preview_requires_explicit_available_only_decision() -> None:
    preview = preview_student_feedback_distribution(
        _preparation(),
        selection_mode=FEEDBACK_SELECTION_ALL,
    )

    assert preview.class_id == "class-1"
    assert preview.activity_id == "activity-1"
    assert preview.activity_title == "Memoir Revision"
    assert preview.roster_count == 3
    assert preview.distributable_count == 2
    assert preview.no_feedback_count == 1
    assert preview.unresolved_count == 0
    assert preview.requested_count == 3
    assert preview.requested_distributable_count == 2
    assert preview.requested_no_feedback_count == 1
    assert preview.requested_unresolved_count == 0
    assert preview.selected_for_output_count == 2
    assert preview.has_unavailable_requested_students is True
    assert preview.requires_available_only_decision is True
    assert tuple(item.student_id for item in preview.requested_entries) == (
        "student-1",
        "student-2",
        "student-3",
    )
    assert tuple(item.student_id for item in preview.selected_entries) == (
        "student-1",
        "student-3",
    )


def test_selected_preview_preserves_roster_not_input_order() -> None:
    preview = preview_student_feedback_distribution(
        _preparation(),
        selection_mode=FEEDBACK_SELECTION_SELECTED,
        selected_student_ids=("student-3", "student-1"),
    )

    assert preview.requested_count == 2
    assert preview.selected_for_output_count == 2
    assert preview.has_unavailable_requested_students is False
    assert preview.requires_available_only_decision is False
    assert tuple(item.student_id for item in preview.requested_entries) == (
        "student-1",
        "student-3",
    )
    assert tuple(item.student_id for item in preview.selected_entries) == (
        "student-1",
        "student-3",
    )


def test_selected_preview_keeps_unavailable_student_visible() -> None:
    preview = preview_student_feedback_distribution(
        _preparation(),
        selection_mode=FEEDBACK_SELECTION_SELECTED,
        selected_student_ids=("student-2", "student-3"),
    )

    assert preview.requested_count == 2
    assert preview.requested_distributable_count == 1
    assert preview.requested_no_feedback_count == 1
    assert preview.selected_for_output_count == 1
    assert preview.has_unavailable_requested_students is True
    assert preview.requires_available_only_decision is False
    assert tuple(item.student_id for item in preview.requested_entries) == (
        "student-2",
        "student-3",
    )
    assert tuple(item.student_id for item in preview.selected_entries) == (
        "student-3",
    )


def test_all_roster_preview_reports_unresolved_student() -> None:
    preview = preview_student_feedback_distribution(
        _preparation(unresolved_second=True),
        selection_mode=FEEDBACK_SELECTION_ALL,
    )

    assert preview.roster_count == 3
    assert preview.distributable_count == 2
    assert preview.no_feedback_count == 0
    assert preview.unresolved_count == 1
    assert preview.requested_unresolved_count == 1
    assert preview.selected_for_output_count == 2
    assert preview.requires_available_only_decision is True


@pytest.mark.parametrize(
    "selected_student_ids,match",
    (
        ((), "requires at least one"),
        (("student-1", "student-1"), "unique student IDs"),
        (("student-1", "student-not-rostered"), "exact subset"),
    ),
)
def test_selected_preview_rejects_invalid_selection(
    selected_student_ids: tuple[str, ...],
    match: str,
) -> None:
    with pytest.raises(ConcordWorkflowValidationError, match=match):
        preview_student_feedback_distribution(
            _preparation(),
            selection_mode=FEEDBACK_SELECTION_SELECTED,
            selected_student_ids=selected_student_ids,
        )


def test_all_roster_preview_rejects_selected_ids() -> None:
    with pytest.raises(
        ConcordWorkflowValidationError,
        match="does not accept",
    ):
        preview_student_feedback_distribution(
            _preparation(),
            selection_mode=FEEDBACK_SELECTION_ALL,
            selected_student_ids=("student-1",),
        )


def test_preview_rejects_unknown_selection_mode() -> None:
    with pytest.raises(
        ConcordWorkflowValidationError,
        match="unsupported",
    ):
        preview_student_feedback_distribution(
            _preparation(),
            selection_mode="mystery",
        )


def test_preview_is_zero_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    preview_student_feedback_distribution(
        _preparation(),
        selection_mode=FEEDBACK_SELECTION_ALL,
    )

    assert tuple(tmp_path.iterdir()) == ()
