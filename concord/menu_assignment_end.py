"""Concord-local, contract-bound choices for ending assignment records.

Does not create a transition engine; all writes remain owned by existing services.
"""

from __future__ import annotations

from concord.menu_prompts import select_one
from concord.workflows._collaboration import (
    ACTIVE_ASSIGNMENT_STATUSES,
    END_ASSIGNMENT_STATUSES,
)
from concord.workflows.errors import ConcordWorkflowValidationError
from concord.workflows.models import ActivitySummary

_END_CHOICES = ("completed", "withdrawn", "cancelled")
_END_LABELS = (
    "Completed - the assignment concluded as intended",
    "Withdrawn - the assignment was intentionally withdrawn",
    "Cancelled - the assignment was cancelled",
)


def choose_assignment_end_status(
    activity: ActivitySummary,
    *,
    record_kind: str,
    record_id: str,
    display_label: str,
    current_status: str,
) -> str:
    """Offer only end statuses accepted by the existing Concord service."""
    if current_status not in ACTIVE_ASSIGNMENT_STATUSES:
        raise ConcordWorkflowValidationError(
            "Only a planned or active assignment may be ended through this menu. "
            "Reopen the record and check its current state."
        )
    if frozenset(_END_CHOICES) != END_ASSIGNMENT_STATUSES:
        raise ConcordWorkflowValidationError(
            "End status choices do not match the canonical Concord service. "
            "No assignment was changed."
        )
    title = (
        f"End {record_kind}\n"
        f"Activity: {activity.title}\n"
        f"Class: {activity.class_id}\n"
        f"{record_kind}: {display_label}\n"
        f"Record ID: {record_id}\n"
        f"Current status: {current_status}\n"
        f"Snapshot: {activity.snapshot_revision}"
    )
    result = select_one(
        title,
        _END_CHOICES,
        _END_LABELS,
        help_text=(
            "Ending retains the original assignment and its history. "
            "Reassignment and supersession are separate actions, never End reasons. "
            "This choice does not create evidence, Scores, Grades or publication."
        ),
    )
    if result not in END_ASSIGNMENT_STATUSES:
        raise ConcordWorkflowValidationError(
            "Invalid ending status; no assignment was changed."
        )
    return result


def assignment_end_review(
    activity: ActivitySummary,
    *,
    record_kind: str,
    record_id: str,
    display_label: str,
    previous_status: str,
    requested_status: str,
) -> tuple[str, ...]:
    """Describe a single guarded assignment revision before confirmation."""
    if previous_status not in ACTIVE_ASSIGNMENT_STATUSES:
        raise ConcordWorkflowValidationError(
            "The selected assignment is no longer active."
        )
    if requested_status not in END_ASSIGNMENT_STATUSES:
        raise ConcordWorkflowValidationError("Invalid ending status; no write.")
    return (
        f"Activity: {activity.title}",
        f"Class: {activity.class_id}",
        f"{record_kind}: {display_label}",
        f"{record_kind} ID: {record_id}",
        f"Current status: {previous_status}",
        f"Requested status: {requested_status}",
        f"Snapshot: {activity.snapshot_revision}",
        "The assignment remains in immutable history; no successor is created.",
        "No authorship, Scores, Grades, evidence, or publication is inferred.",
    )
