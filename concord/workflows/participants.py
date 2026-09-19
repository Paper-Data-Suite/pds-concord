"""Core-roster participant resolution for Concord collaboration workflows."""

from __future__ import annotations

import unicodedata
from pathlib import Path

from pds_core.classes import load_class_roster
from pds_core.rosters import (
    Roster,
    RosterError,
    student_display_name,
    student_lookup,
    student_sort_name,
)

from concord.models import ConcordRecordReference, ParticipantReference
from concord.workflows.errors import (
    ConcordWorkflowNotFoundError,
    ConcordWorkflowValidationError,
)


def load_required_roster(root: str | Path, class_id: str) -> Roster:
    """Load the Core-owned class roster required by participant mutations."""
    try:
        return load_class_roster(root, class_id)
    except RosterError as error:
        raise ConcordWorkflowNotFoundError(
            f"Core roster is not available for class: {class_id}"
        ) from error


def core_student_participant(
    root: str | Path,
    class_id: str,
    student_id: str,
) -> ParticipantReference:
    """Resolve one rostered student to the native participant reference."""
    roster = load_required_roster(root, class_id)
    student = student_lookup(roster).get(student_id)
    if student is None:
        raise ConcordWorkflowNotFoundError(
            f"Student is not available in the Core roster: {student_id}"
        )
    return ParticipantReference(
        participant_kind="core_student",
        participant_id=student.student_id,
        owning_system="core",
    )


def validate_participant_reference(
    root: str | Path,
    class_id: str,
    participant: ParticipantReference,
) -> ParticipantReference:
    """Validate participant ownership and Core roster membership where required."""
    if participant.participant_kind == "core_student":
        if participant.owning_system != "core":
            raise ConcordWorkflowValidationError(
                "core_student participants must be owned by Core."
            )
        resolved = core_student_participant(
            root,
            class_id,
            participant.participant_id,
        )
        if resolved != participant:
            raise ConcordWorkflowValidationError(
                "Core student participant reference is inconsistent with the roster."
            )
        return participant
    if participant.participant_kind == "authorized_actor":
        return participant
    raise ConcordWorkflowValidationError(
        f"Unsupported participant kind: {participant.participant_kind}"
    )


def participant_display_label(
    root: str | Path,
    class_id: str,
    participant: ParticipantReference,
) -> str | None:
    """Return a best-effort teacher display label without changing identity."""
    if participant.participant_kind != "core_student":
        return None
    try:
        roster = load_class_roster(root, class_id)
    except RosterError:
        return None
    student = student_lookup(roster).get(participant.participant_id)
    return None if student is None else student_display_name(student)


def participant_print_label(
    roster: Roster | None,
    participant: ParticipantReference | None,
) -> str | None:
    """Return a privacy-minimized physical label from structured roster data."""
    if participant is None or participant.participant_kind != "core_student":
        return None
    if participant.owning_system != "core":
        raise ConcordWorkflowValidationError(
            "core_student print labels require a Core-owned participant."
        )
    if roster is None:
        raise ConcordWorkflowNotFoundError(
            "Core roster is required for a student physical-paper label."
        )
    student = student_lookup(roster).get(participant.participant_id)
    if student is None:
        raise ConcordWorkflowNotFoundError(
            "Student is not available in the Core roster for physical-paper "
            f"labeling: {participant.participant_id}"
        )
    label = f"{student.first_name} {student.last_name[0]}."
    if any(
        unicodedata.category(character) in {"Cc", "Zl", "Zp"}
        for character in label
    ):
        raise ConcordWorkflowValidationError(
            "student physical-paper label must be single-line and free of "
            "control characters."
        )
    return label


def participant_sort_label(
    root: str | Path,
    class_id: str,
    participant: ParticipantReference,
) -> str:
    """Return a deterministic Core-backed sort label for one participant."""
    if participant.participant_kind != "core_student":
        return participant.participant_id
    try:
        roster = load_class_roster(root, class_id)
    except RosterError:
        return participant.participant_id
    student = student_lookup(roster).get(participant.participant_id)
    return participant.participant_id if student is None else student_sort_name(student)

def group_record_reference(group_id: str) -> ConcordRecordReference:
    """Create the native Concord reference used for Group assignees."""
    return ConcordRecordReference(record_kind="group", record_id=group_id)
