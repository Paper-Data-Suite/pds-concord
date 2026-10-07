"""Roster-wide preparation for share-safe student feedback distribution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from pds_core.rosters import Roster, student_display_name

from concord.models import ScoreTargetReference
from concord.workflows.activity_read import ActivityReadContext
from concord.workflows.activity_score_analysis import (
    SCORE_ANALYSIS_BASIS,
    target_score_detail_batch_from_context,
)
from concord.workflows.errors import ConcordWorkflowValidationError
from concord.workflows.participants import load_required_roster
from concord.workflows.student_feedback import (
    StudentFeedbackProjection,
    student_feedback_projection_from_target_detail,
)

FEEDBACK_AVAILABILITY_DISTRIBUTABLE: Final[str] = "distributable"
FEEDBACK_AVAILABILITY_NONE: Final[str] = "no_distributable_feedback"
FEEDBACK_AVAILABILITY_UNRESOLVED: Final[str] = "unresolved"
STUDENT_FEEDBACK_PREPARATION_SCOPE: Final[str] = "teacher_local"
_UNSAFE_SEMANTICS_REASON: Final[str] = "unsafe_student_feedback_semantics"


@dataclass(frozen=True, slots=True, kw_only=True)
class StudentFeedbackRosterEntry:
    """Teacher-local preparation state for one exact current roster student."""

    student_id: str
    student_display_name: str | None
    availability: str
    projection: StudentFeedbackProjection | None
    unresolved_reason: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class StudentFeedbackRosterPreparation:
    """Immutable whole-roster feedback availability from one exact Activity state."""

    class_id: str
    activity_id: str
    snapshot_revision: int
    snapshot_sha256: str
    score_basis: str
    sharing_scope: str
    entries: tuple[StudentFeedbackRosterEntry, ...]

    @property
    def roster_count(self) -> int:
        return len(self.entries)

    @property
    def distributable_count(self) -> int:
        return sum(
            item.availability == FEEDBACK_AVAILABILITY_DISTRIBUTABLE
            for item in self.entries
        )

    @property
    def no_feedback_count(self) -> int:
        return sum(
            item.availability == FEEDBACK_AVAILABILITY_NONE
            for item in self.entries
        )

    @property
    def unresolved_count(self) -> int:
        return sum(
            item.availability == FEEDBACK_AVAILABILITY_UNRESOLVED
            for item in self.entries
        )


def _student_target(student_id: str) -> ScoreTargetReference:
    return ScoreTargetReference(
        target_kind="core_student",
        target_id=student_id,
        owning_system="core",
    )


def _validate_roster_matches_context(
    context: ActivityReadContext,
    roster: Roster,
) -> None:
    if roster.class_id != context.work.class_id:
        raise ConcordWorkflowValidationError(
            "Student feedback roster does not match the Activity class."
        )
    if any(student.class_id != roster.class_id for student in roster.students):
        raise ConcordWorkflowValidationError(
            "Student feedback roster contains a mismatched student class."
        )


def _reject_unresolved_current_student_targets(
    *,
    current_targets: tuple[ScoreTargetReference, ...],
    roster_student_ids: frozenset[str],
) -> None:
    unresolved = tuple(
        target
        for target in current_targets
        if target.target_kind == "core_student"
        and (
            target.owning_system != "core"
            or target.target_id not in roster_student_ids
        )
    )
    if unresolved:
        raise ConcordWorkflowValidationError(
            "Current core_student Score target cannot be resolved against "
            "the current Core roster."
        )


def student_feedback_roster_preparation_from_context(
    context: ActivityReadContext,
    roster: Roster,
) -> StudentFeedbackRosterPreparation:
    """Classify one current Core roster from one exact Activity read context."""
    _validate_roster_matches_context(context, roster)

    targets = tuple(_student_target(student.student_id) for student in roster.students)
    batch = target_score_detail_batch_from_context(context, targets)

    roster_student_ids = frozenset(student.student_id for student in roster.students)
    _reject_unresolved_current_student_targets(
        current_targets=batch.current_target_references,
        roster_student_ids=roster_student_ids,
    )

    if len(batch.details) != len(roster.students):
        raise ConcordWorkflowValidationError(
            "Student feedback target-detail batch does not match the Core roster."
        )

    entries: list[StudentFeedbackRosterEntry] = []
    for student, detail in zip(roster.students, batch.details, strict=True):
        display_name = student_display_name(student)
        try:
            projection = student_feedback_projection_from_target_detail(
                detail,
                student_display_name=display_name,
            )
        except ConcordWorkflowValidationError:
            entries.append(
                StudentFeedbackRosterEntry(
                    student_id=student.student_id,
                    student_display_name=None,
                    availability=FEEDBACK_AVAILABILITY_UNRESOLVED,
                    projection=None,
                    unresolved_reason=_UNSAFE_SEMANTICS_REASON,
                )
            )
            continue

        availability = (
            FEEDBACK_AVAILABILITY_DISTRIBUTABLE
            if projection.current_score_count > 0
            else FEEDBACK_AVAILABILITY_NONE
        )
        entries.append(
            StudentFeedbackRosterEntry(
                student_id=student.student_id,
                student_display_name=projection.student_display_name,
                availability=availability,
                projection=projection,
            )
        )

    return StudentFeedbackRosterPreparation(
        class_id=context.work.class_id,
        activity_id=context.activity.activity_id,
        snapshot_revision=context.snapshot_revision,
        snapshot_sha256=context.snapshot_sha256,
        score_basis=SCORE_ANALYSIS_BASIS,
        sharing_scope=STUDENT_FEEDBACK_PREPARATION_SCOPE,
        entries=tuple(entries),
    )


def load_student_feedback_roster_preparation(
    context: ActivityReadContext,
) -> StudentFeedbackRosterPreparation:
    """Load the current Core roster once and prepare whole-class feedback."""
    roster = load_required_roster(
        context.root,
        context.work.class_id,
    )
    return student_feedback_roster_preparation_from_context(
        context,
        roster,
    )


__all__ = [
    "FEEDBACK_AVAILABILITY_DISTRIBUTABLE",
    "FEEDBACK_AVAILABILITY_NONE",
    "FEEDBACK_AVAILABILITY_UNRESOLVED",
    "STUDENT_FEEDBACK_PREPARATION_SCOPE",
    "StudentFeedbackRosterEntry",
    "StudentFeedbackRosterPreparation",
    "load_student_feedback_roster_preparation",
    "student_feedback_roster_preparation_from_context",
]
