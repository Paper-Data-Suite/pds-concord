"""Auditable correction records preserving immutable history."""

from __future__ import annotations

from dataclasses import dataclass

from concord.models.common import (
    ActorReference,
    ConcordModelError,
    ConcordRecordReference,
    PrivacyPolicy,
    controlled,
    identifier,
    optional_identifier,
    optional_text,
    require_text,
    timestamp,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class CorrectionRecord:
    correction_id: str
    target_reference: ConcordRecordReference
    correction_type: str
    reason: str
    correcting_actor: ActorReference
    corrected_at: str
    privacy_policy: PrivacyPolicy
    replacement_reference: ConcordRecordReference | None = None
    related_source_reference: ConcordRecordReference | None = None
    note: str | None = None
    supersedes_correction_id: str | None = None

    def __post_init__(self) -> None:
        identifier(self.correction_id, "correction_id")
        if not isinstance(self.target_reference, ConcordRecordReference):
            raise ConcordModelError("target_reference must be ConcordRecordReference.")
        controlled(
            self.correction_type,
            "correction_type",
            frozenset(
                {
                    "author_correction",
                    "subject_correction",
                    "membership_correction",
                    "role_correction",
                    "responsibility_correction",
                    "review_correction",
                    "moderation_revision",
                    "score_revision",
                    "metadata_correction",
                }
            ),
        )
        require_text(self.reason, "reason")
        if not isinstance(self.correcting_actor, ActorReference):
            raise ConcordModelError("correcting_actor must be ActorReference.")
        timestamp(self.corrected_at, "corrected_at")
        if self.replacement_reference is not None and not isinstance(
            self.replacement_reference, ConcordRecordReference
        ):
            raise ConcordModelError(
                "replacement_reference must be ConcordRecordReference."
            )
        if self.related_source_reference is not None and not isinstance(
            self.related_source_reference, ConcordRecordReference
        ):
            raise ConcordModelError(
                "related_source_reference must be ConcordRecordReference."
            )
        optional_text(self.note, "note")
        optional_identifier(self.supersedes_correction_id, "supersedes_correction_id")
