"""Reviewed immutable plans for student feedback distribution."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from concord.generated_paths import (
    ConcordGeneratedPathError,
    build_human_readable_output_filename,
    validate_human_readable_output_filename,
)
from concord.workflows.errors import ConcordWorkflowValidationError
from concord.workflows.student_feedback import (
    StudentFeedbackProjection,
    StudentFeedbackResult,
)
from concord.workflows.student_feedback_distribution import (
    FEEDBACK_AVAILABILITY_DISTRIBUTABLE,
    FEEDBACK_AVAILABILITY_NONE,
    FEEDBACK_AVAILABILITY_UNRESOLVED,
    FEEDBACK_SELECTION_ALL,
    FEEDBACK_SELECTION_SELECTED,
    StudentFeedbackDistributionPreview,
    StudentFeedbackRosterEntry,
)

STUDENT_FEEDBACK_PLAN_SCHEMA_VERSION: Final[str] = (
    "concord-student-feedback-distribution-plan-v1"
)
STUDENT_FEEDBACK_FILENAME_DOMAIN: Final[str] = "student-feedback"
FEEDBACK_INDEX_FILENAME: Final[str] = "Feedback Index.html"
FEEDBACK_PRINT_FILENAME: Final[str] = "Print All Feedback.pdf"
FEEDBACK_MANIFEST_FILENAME: Final[str] = "distribution-manifest.json"


@dataclass(frozen=True, slots=True, kw_only=True)
class PlannedStudentFeedback:
    """One roster-ordered student output bound into a reviewed plan."""

    student_id: str
    student_display_name: str
    filename: str
    projection: StudentFeedbackProjection


@dataclass(frozen=True, slots=True, kw_only=True)
class PreparedStudentFeedbackDistribution:
    """Exact reviewed distribution plan; execution remains a later boundary."""

    schema_version: str
    class_id: str
    activity_id: str
    activity_title: str
    expected_snapshot_revision: int
    expected_snapshot_sha256: str
    selection_mode: str
    available_only_authorized: bool
    destination: Path
    roster_student_ids: tuple[str, ...]
    requested_student_ids: tuple[str, ...]
    no_feedback_student_ids: tuple[str, ...]
    unresolved_student_ids: tuple[str, ...]
    students: tuple[PlannedStudentFeedback, ...]
    output_filenames: tuple[str, ...]
    plan_digest: str



def _normalize_destination(destination: str | Path) -> Path:
    try:
        path = Path(destination)
    except TypeError as error:
        raise ConcordWorkflowValidationError(
            "Student feedback distribution destination must be a filesystem path."
        ) from error
    if not path.is_absolute():
        raise ConcordWorkflowValidationError(
            "Student feedback distribution destination must be absolute."
        )
    return Path(os.path.normpath(os.fspath(path)))



def _availability_ids(
    entries: tuple[StudentFeedbackRosterEntry, ...],
    availability: str,
) -> tuple[str, ...]:
    return tuple(
        item.student_id
        for item in entries
        if item.availability == availability
    )



def _validate_preview(preview: StudentFeedbackDistributionPreview) -> None:
    roster_ids = preview.roster_student_ids
    requested_ids = tuple(item.student_id for item in preview.requested_entries)
    selected_ids = tuple(item.student_id for item in preview.selected_entries)

    if len(roster_ids) != len(set(roster_ids)):
        raise ConcordWorkflowValidationError(
            "Student feedback preview roster identity is contradictory."
        )
    if preview.roster_count != len(roster_ids):
        raise ConcordWorkflowValidationError(
            "Student feedback preview roster count is inconsistent."
        )
    if preview.no_feedback_count != len(preview.no_feedback_student_ids):
        raise ConcordWorkflowValidationError(
            "Student feedback preview no-feedback count is inconsistent."
        )
    if preview.unresolved_count != len(preview.unresolved_student_ids):
        raise ConcordWorkflowValidationError(
            "Student feedback preview unresolved count is inconsistent."
        )
    if (
        preview.distributable_count
        + preview.no_feedback_count
        + preview.unresolved_count
        != preview.roster_count
    ):
        raise ConcordWorkflowValidationError(
            "Student feedback preview availability partition is inconsistent."
        )

    roster_set = frozenset(roster_ids)
    no_feedback_set = frozenset(preview.no_feedback_student_ids)
    unresolved_set = frozenset(preview.unresolved_student_ids)
    if not no_feedback_set.issubset(roster_set):
        raise ConcordWorkflowValidationError(
            "Student feedback preview no-feedback identities are not rostered."
        )
    if not unresolved_set.issubset(roster_set):
        raise ConcordWorkflowValidationError(
            "Student feedback preview unresolved identities are not rostered."
        )
    if no_feedback_set & unresolved_set:
        raise ConcordWorkflowValidationError(
            "Student feedback preview availability identities overlap."
        )

    if len(requested_ids) != len(set(requested_ids)):
        raise ConcordWorkflowValidationError(
            "Student feedback preview requested identity is contradictory."
        )
    if not frozenset(requested_ids).issubset(roster_set):
        raise ConcordWorkflowValidationError(
            "Student feedback preview requested identities are not rostered."
        )
    if preview.requested_count != len(requested_ids):
        raise ConcordWorkflowValidationError(
            "Student feedback preview requested count is inconsistent."
        )

    expected_selected = tuple(
        item.student_id
        for item in preview.requested_entries
        if item.availability == FEEDBACK_AVAILABILITY_DISTRIBUTABLE
    )
    if selected_ids != expected_selected:
        raise ConcordWorkflowValidationError(
            "Student feedback preview output selection is inconsistent."
        )
    if preview.selected_for_output_count != len(selected_ids):
        raise ConcordWorkflowValidationError(
            "Student feedback preview selected count is inconsistent."
        )

    requested_no_feedback = _availability_ids(
        preview.requested_entries,
        FEEDBACK_AVAILABILITY_NONE,
    )
    requested_unresolved = _availability_ids(
        preview.requested_entries,
        FEEDBACK_AVAILABILITY_UNRESOLVED,
    )
    if preview.requested_no_feedback_count != len(requested_no_feedback):
        raise ConcordWorkflowValidationError(
            "Student feedback preview requested no-feedback count is inconsistent."
        )
    if preview.requested_unresolved_count != len(requested_unresolved):
        raise ConcordWorkflowValidationError(
            "Student feedback preview requested unresolved count is inconsistent."
        )
    if preview.requested_distributable_count != len(expected_selected):
        raise ConcordWorkflowValidationError(
            "Student feedback preview distributable count is inconsistent."
        )

    has_unavailable = len(expected_selected) != len(requested_ids)
    if preview.has_unavailable_requested_students != has_unavailable:
        raise ConcordWorkflowValidationError(
            "Student feedback preview availability decision is inconsistent."
        )

    if preview.selection_mode == FEEDBACK_SELECTION_ALL:
        if requested_ids != roster_ids:
            raise ConcordWorkflowValidationError(
                "All-roster feedback preview must preserve the full roster order."
            )
        if preview.requires_available_only_decision != has_unavailable:
            raise ConcordWorkflowValidationError(
                "All-roster feedback preview completeness decision is inconsistent."
            )
    elif preview.selection_mode == FEEDBACK_SELECTION_SELECTED:
        if preview.requires_available_only_decision:
            raise ConcordWorkflowValidationError(
                "Selected-student feedback preview cannot authorize available-only."
            )
    else:
        raise ConcordWorkflowValidationError(
            "Student feedback preview selection mode is unsupported."
        )



def _planned_student(
    preview: StudentFeedbackDistributionPreview,
    entry: StudentFeedbackRosterEntry,
) -> PlannedStudentFeedback:
    projection = entry.projection
    if (
        entry.availability != FEEDBACK_AVAILABILITY_DISTRIBUTABLE
        or projection is None
        or entry.student_display_name is None
        or projection.student_display_name != entry.student_display_name
        or projection.current_score_count <= 0
    ):
        raise ConcordWorkflowValidationError(
            "Student feedback plan encountered a contradictory distributable student."
        )

    try:
        filename = build_human_readable_output_filename(
            display_label=f"{projection.student_display_name} - Feedback",
            domain=STUDENT_FEEDBACK_FILENAME_DOMAIN,
            identity_parts=(
                preview.class_id,
                preview.activity_id,
                entry.student_id,
                str(preview.snapshot_revision),
                preview.snapshot_sha256,
            ),
            extension=".pdf",
        )
        validate_human_readable_output_filename(filename)
    except ConcordGeneratedPathError as error:
        raise ConcordWorkflowValidationError(
            "Student feedback plan could not create a safe bounded filename."
        ) from error

    return PlannedStudentFeedback(
        student_id=entry.student_id,
        student_display_name=projection.student_display_name,
        filename=filename,
        projection=projection,
    )



def _result_payload(result: StudentFeedbackResult) -> dict[str, object]:
    return {
        "criterion_label": result.criterion_label,
        "scoring_scale_name": result.scoring_scale_name,
        "disposition": result.disposition,
        "value": result.value,
        "value_label": result.value_label,
    }



def _projection_payload(projection: StudentFeedbackProjection) -> dict[str, object]:
    return {
        "student_display_name": projection.student_display_name,
        "activity_title": projection.activity_title,
        "class_label": projection.class_label,
        "boundary_statement": projection.boundary_statement,
        "results": [_result_payload(item) for item in projection.results],
    }



def _plan_payload(
    *,
    schema_version: str,
    class_id: str,
    activity_id: str,
    activity_title: str,
    expected_snapshot_revision: int,
    expected_snapshot_sha256: str,
    selection_mode: str,
    available_only_authorized: bool,
    destination: Path,
    roster_student_ids: tuple[str, ...],
    requested_student_ids: tuple[str, ...],
    no_feedback_student_ids: tuple[str, ...],
    unresolved_student_ids: tuple[str, ...],
    students: tuple[PlannedStudentFeedback, ...],
    output_filenames: tuple[str, ...],
) -> dict[str, object]:
    return {
        "schema_version": schema_version,
        "class_id": class_id,
        "activity_id": activity_id,
        "activity_title": activity_title,
        "expected_snapshot_revision": expected_snapshot_revision,
        "expected_snapshot_sha256": expected_snapshot_sha256,
        "selection_mode": selection_mode,
        "available_only_authorized": available_only_authorized,
        "destination": os.fspath(destination),
        "roster_student_ids": list(roster_student_ids),
        "requested_student_ids": list(requested_student_ids),
        "no_feedback_student_ids": list(no_feedback_student_ids),
        "unresolved_student_ids": list(unresolved_student_ids),
        "students": [
            {
                "student_id": student.student_id,
                "student_display_name": student.student_display_name,
                "filename": student.filename,
                "projection": _projection_payload(student.projection),
            }
            for student in students
        ],
        "output_filenames": list(output_filenames),
    }



def _digest_payload(payload: dict[str, object]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()



def _digest_for_plan(plan: PreparedStudentFeedbackDistribution) -> str:
    return _digest_payload(
        _plan_payload(
            schema_version=plan.schema_version,
            class_id=plan.class_id,
            activity_id=plan.activity_id,
            activity_title=plan.activity_title,
            expected_snapshot_revision=plan.expected_snapshot_revision,
            expected_snapshot_sha256=plan.expected_snapshot_sha256,
            selection_mode=plan.selection_mode,
            available_only_authorized=plan.available_only_authorized,
            destination=plan.destination,
            roster_student_ids=plan.roster_student_ids,
            requested_student_ids=plan.requested_student_ids,
            no_feedback_student_ids=plan.no_feedback_student_ids,
            unresolved_student_ids=plan.unresolved_student_ids,
            students=plan.students,
            output_filenames=plan.output_filenames,
        )
    )



def prepare_student_feedback_distribution_plan(
    preview: StudentFeedbackDistributionPreview,
    *,
    destination: str | Path,
    authorize_available_only: bool = False,
) -> PreparedStudentFeedbackDistribution:
    """Bind one reviewed zero-write preview to an exact immutable output plan."""
    _validate_preview(preview)

    if preview.selected_for_output_count <= 0:
        raise ConcordWorkflowValidationError(
            "Student feedback distribution requires distributable feedback."
        )

    if preview.selection_mode == FEEDBACK_SELECTION_ALL:
        if preview.has_unavailable_requested_students and not authorize_available_only:
            raise ConcordWorkflowValidationError(
                "All-roster feedback with unavailable students requires explicit "
                "available-only authorization."
            )
        if not preview.has_unavailable_requested_students and authorize_available_only:
            raise ConcordWorkflowValidationError(
                "Available-only authorization is unnecessary for a complete roster."
            )
    else:
        if authorize_available_only:
            raise ConcordWorkflowValidationError(
                "Available-only authorization applies only to incomplete all-roster "
                "feedback."
            )
        if preview.has_unavailable_requested_students:
            raise ConcordWorkflowValidationError(
                "Selected-student feedback contains unavailable students; revise "
                "the reviewed selection instead of omitting them."
            )

    output_destination = _normalize_destination(destination)
    students = tuple(
        _planned_student(preview, entry)
        for entry in preview.selected_entries
    )
    output_filenames = tuple(student.filename for student in students) + (
        FEEDBACK_PRINT_FILENAME,
        FEEDBACK_INDEX_FILENAME,
        FEEDBACK_MANIFEST_FILENAME,
    )
    if len({name.casefold() for name in output_filenames}) != len(output_filenames):
        raise ConcordWorkflowValidationError(
            "Student feedback planned output filenames collide."
        )

    requested_student_ids = tuple(
        item.student_id for item in preview.requested_entries
    )
    payload = _plan_payload(
        schema_version=STUDENT_FEEDBACK_PLAN_SCHEMA_VERSION,
        class_id=preview.class_id,
        activity_id=preview.activity_id,
        activity_title=preview.activity_title,
        expected_snapshot_revision=preview.snapshot_revision,
        expected_snapshot_sha256=preview.snapshot_sha256,
        selection_mode=preview.selection_mode,
        available_only_authorized=authorize_available_only,
        destination=output_destination,
        roster_student_ids=preview.roster_student_ids,
        requested_student_ids=requested_student_ids,
        no_feedback_student_ids=preview.no_feedback_student_ids,
        unresolved_student_ids=preview.unresolved_student_ids,
        students=students,
        output_filenames=output_filenames,
    )
    digest = _digest_payload(payload)
    return PreparedStudentFeedbackDistribution(
        schema_version=STUDENT_FEEDBACK_PLAN_SCHEMA_VERSION,
        class_id=preview.class_id,
        activity_id=preview.activity_id,
        activity_title=preview.activity_title,
        expected_snapshot_revision=preview.snapshot_revision,
        expected_snapshot_sha256=preview.snapshot_sha256,
        selection_mode=preview.selection_mode,
        available_only_authorized=authorize_available_only,
        destination=output_destination,
        roster_student_ids=preview.roster_student_ids,
        requested_student_ids=requested_student_ids,
        no_feedback_student_ids=preview.no_feedback_student_ids,
        unresolved_student_ids=preview.unresolved_student_ids,
        students=students,
        output_filenames=output_filenames,
        plan_digest=digest,
    )



def verify_student_feedback_distribution_plan_digest(
    plan: PreparedStudentFeedbackDistribution,
) -> PreparedStudentFeedbackDistribution:
    """Fail closed if any reviewed plan field no longer matches its digest."""
    if plan.schema_version != STUDENT_FEEDBACK_PLAN_SCHEMA_VERSION:
        raise ConcordWorkflowValidationError(
            "Student feedback distribution plan schema is unsupported."
        )
    expected = _digest_for_plan(plan)
    if plan.plan_digest != expected:
        raise ConcordWorkflowValidationError(
            "Student feedback distribution plan digest does not match "
            "the reviewed plan."
        )
    return plan


__all__ = [
    "FEEDBACK_INDEX_FILENAME",
    "FEEDBACK_MANIFEST_FILENAME",
    "FEEDBACK_PRINT_FILENAME",
    "STUDENT_FEEDBACK_FILENAME_DOMAIN",
    "STUDENT_FEEDBACK_PLAN_SCHEMA_VERSION",
    "PlannedStudentFeedback",
    "PreparedStudentFeedbackDistribution",
    "prepare_student_feedback_distribution_plan",
    "verify_student_feedback_distribution_plan_digest",
]
