from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from concord.generated_paths import validate_human_readable_output_filename
from concord.workflows import (
    FEEDBACK_AVAILABILITY_DISTRIBUTABLE,
    FEEDBACK_AVAILABILITY_NONE,
    FEEDBACK_INDEX_FILENAME,
    FEEDBACK_MANIFEST_FILENAME,
    FEEDBACK_PRINT_FILENAME,
    FEEDBACK_SELECTION_ALL,
    FEEDBACK_SELECTION_SELECTED,
    SCORE_ANALYSIS_BASIS,
    STUDENT_FEEDBACK_BOUNDARY_STATEMENT,
    STUDENT_FEEDBACK_PREPARATION_SCOPE,
    StudentFeedbackProjection,
    StudentFeedbackResult,
    StudentFeedbackRosterEntry,
    StudentFeedbackRosterPreparation,
    prepare_student_feedback_distribution_plan,
    preview_student_feedback_distribution,
    verify_student_feedback_distribution_plan_digest,
)
from concord.workflows.errors import ConcordWorkflowValidationError


def _projection(
    name: str,
    *,
    value: int = 3,
    label: str = "Meeting",
) -> StudentFeedbackProjection:
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
                value=value,
                value_label=label,
            ),
        ),
    )


def _preparation(
    *,
    duplicate_names: bool = False,
    first_value: int = 3,
) -> StudentFeedbackRosterPreparation:
    first_name = "Alex Smith" if duplicate_names else "Jane Doe"
    third_name = "Alex Smith" if duplicate_names else "Alex Rivera"
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
                student_id="student-private-001",
                student_display_name=first_name,
                availability=FEEDBACK_AVAILABILITY_DISTRIBUTABLE,
                projection=_projection(
                    first_name,
                    value=first_value,
                    label="Meeting" if first_value == 3 else "Exceeding",
                ),
            ),
            StudentFeedbackRosterEntry(
                student_id="student-private-002",
                student_display_name="John Smith",
                availability=FEEDBACK_AVAILABILITY_NONE,
                projection=StudentFeedbackProjection(
                    student_display_name="John Smith",
                    activity_title="Memoir Revision",
                    class_label=None,
                    boundary_statement=STUDENT_FEEDBACK_BOUNDARY_STATEMENT,
                    results=(),
                ),
            ),
            StudentFeedbackRosterEntry(
                student_id="student-private-003",
                student_display_name=third_name,
                availability=FEEDBACK_AVAILABILITY_DISTRIBUTABLE,
                projection=_projection(third_name),
            ),
        ),
    )


def test_all_roster_plan_requires_explicit_available_only_authorization(
    tmp_path: Path,
) -> None:
    preview = preview_student_feedback_distribution(
        _preparation(),
        selection_mode=FEEDBACK_SELECTION_ALL,
    )
    destination = tmp_path / "feedback"

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="available-only authorization",
    ):
        prepare_student_feedback_distribution_plan(
            preview,
            destination=destination,
        )

    plan = prepare_student_feedback_distribution_plan(
        preview,
        destination=destination,
        authorize_available_only=True,
    )

    assert plan.available_only_authorized is True
    assert plan.expected_snapshot_revision == 10
    assert plan.expected_snapshot_sha256 == "b" * 64
    assert plan.roster_student_ids == (
        "student-private-001",
        "student-private-002",
        "student-private-003",
    )
    assert plan.requested_student_ids == plan.roster_student_ids
    assert plan.no_feedback_student_ids == ("student-private-002",)
    assert plan.unresolved_student_ids == ()
    assert tuple(item.student_id for item in plan.students) == (
        "student-private-001",
        "student-private-003",
    )
    assert not destination.exists()
    assert len(plan.plan_digest) == 64
    assert verify_student_feedback_distribution_plan_digest(plan) is plan


def test_selected_plan_preserves_roster_order_and_rejects_hidden_omission(
    tmp_path: Path,
) -> None:
    preparation = _preparation()
    clean_preview = preview_student_feedback_distribution(
        preparation,
        selection_mode=FEEDBACK_SELECTION_SELECTED,
        selected_student_ids=("student-private-003", "student-private-001"),
    )

    plan = prepare_student_feedback_distribution_plan(
        clean_preview,
        destination=tmp_path / "selected",
    )
    assert tuple(item.student_id for item in plan.students) == (
        "student-private-001",
        "student-private-003",
    )
    assert plan.available_only_authorized is False

    unavailable_preview = preview_student_feedback_distribution(
        preparation,
        selection_mode=FEEDBACK_SELECTION_SELECTED,
        selected_student_ids=("student-private-002", "student-private-003"),
    )
    with pytest.raises(
        ConcordWorkflowValidationError,
        match="revise the reviewed selection",
    ):
        prepare_student_feedback_distribution_plan(
            unavailable_preview,
            destination=tmp_path / "unavailable-selected",
        )


def test_plan_uses_issue124_filenames_without_raw_student_ids(
    tmp_path: Path,
) -> None:
    preview = preview_student_feedback_distribution(
        _preparation(duplicate_names=True),
        selection_mode=FEEDBACK_SELECTION_ALL,
    )
    plan = prepare_student_feedback_distribution_plan(
        preview,
        destination=tmp_path / "feedback",
        authorize_available_only=True,
    )

    filenames = tuple(item.filename for item in plan.students)
    assert len(filenames) == 2
    assert filenames[0] != filenames[1]
    assert all(name.startswith("Alex-Smith-Feedback--") for name in filenames)
    assert all(
        validate_human_readable_output_filename(name) == name
        for name in filenames
    )
    for filename in filenames:
        assert "student-private-001" not in filename
        assert "student-private-003" not in filename

    assert plan.output_filenames == filenames + (
        FEEDBACK_PRINT_FILENAME,
        FEEDBACK_INDEX_FILENAME,
        FEEDBACK_MANIFEST_FILENAME,
    )


def test_plan_digest_is_deterministic_and_binds_exact_semantics(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "feedback"
    first_preview = preview_student_feedback_distribution(
        _preparation(first_value=3),
        selection_mode=FEEDBACK_SELECTION_ALL,
    )
    repeated = prepare_student_feedback_distribution_plan(
        first_preview,
        destination=destination,
        authorize_available_only=True,
    )
    same = prepare_student_feedback_distribution_plan(
        first_preview,
        destination=destination,
        authorize_available_only=True,
    )
    changed_preview = preview_student_feedback_distribution(
        _preparation(first_value=4),
        selection_mode=FEEDBACK_SELECTION_ALL,
    )
    changed = prepare_student_feedback_distribution_plan(
        changed_preview,
        destination=destination,
        authorize_available_only=True,
    )
    changed_destination = prepare_student_feedback_distribution_plan(
        first_preview,
        destination=tmp_path / "other-feedback",
        authorize_available_only=True,
    )

    assert repeated.plan_digest == same.plan_digest
    assert repeated.plan_digest != changed.plan_digest
    assert repeated.plan_digest != changed_destination.plan_digest


def test_plan_digest_verification_fails_closed_for_changed_plan(
    tmp_path: Path,
) -> None:
    preview = preview_student_feedback_distribution(
        _preparation(),
        selection_mode=FEEDBACK_SELECTION_ALL,
    )
    plan = prepare_student_feedback_distribution_plan(
        preview,
        destination=tmp_path / "feedback",
        authorize_available_only=True,
    )
    tampered = replace(
        plan,
        destination=tmp_path / "different-destination",
    )

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="digest does not match",
    ):
        verify_student_feedback_distribution_plan_digest(tampered)


def test_plan_requires_absolute_destination(tmp_path: Path) -> None:
    preview = preview_student_feedback_distribution(
        _preparation(),
        selection_mode=FEEDBACK_SELECTION_ALL,
    )

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="must be absolute",
    ):
        prepare_student_feedback_distribution_plan(
            preview,
            destination=Path("relative/feedback"),
            authorize_available_only=True,
        )


def test_complete_all_roster_rejects_meaningless_available_only(
    tmp_path: Path,
) -> None:
    preparation = StudentFeedbackRosterPreparation(
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
        ),
    )
    preview = preview_student_feedback_distribution(
        preparation,
        selection_mode=FEEDBACK_SELECTION_ALL,
    )

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="unnecessary",
    ):
        prepare_student_feedback_distribution_plan(
            preview,
            destination=tmp_path / "feedback",
            authorize_available_only=True,
        )


def test_plan_source_reuses_issue124_without_local_filename_sanitizer() -> None:
    source = Path(
        "concord/workflows/student_feedback_distribution_plan.py"
    ).read_text(encoding="utf-8")

    assert "build_human_readable_output_filename" in source
    assert "validate_human_readable_output_filename" in source
    for forbidden in (
        "def slugify",
        "def sanitize_filename",
        "def truncate_filename",
        "def hash_filename",
        "def _sanitize_human_visible_stem",
    ):
        assert forbidden not in source
