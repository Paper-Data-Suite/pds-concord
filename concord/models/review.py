"""Administrative review and evidence moderation records."""

from __future__ import annotations

from dataclasses import dataclass

from concord.models.common import (
    ActorReference,
    ConcordModelError,
    EvidenceReference,
    PrivacyPolicy,
    SubjectReference,
    controlled,
    identifier,
    optional_identifier,
    optional_text,
    require_text,
    timestamp,
    tuple_of_values,
)

_BLOCKING_REVIEW_OUTCOMES = frozenset(
    {
        "incomplete",
        "unreadable",
        "misrouted",
        "duplicate",
        "awaiting_correction",
        "awaiting_additional_evidence",
        "moderation_required",
        "not_suitable_for_scoring",
    }
)


@dataclass(frozen=True, slots=True, kw_only=True)
class ArtifactReview:
    artifact_review_id: str
    artifact_instance_id: str
    reviewer: ActorReference
    reviewed_at: str
    readability_judgment: str
    page_completeness_judgment: str
    filing_judgment: str
    author_judgment: str
    subject_judgment: str
    privacy_judgment: str
    relevance_judgment: str
    moderation_requirement: str
    scoring_readiness: str
    review_outcome: str
    privacy_policy: PrivacyPolicy
    notes: str | None = None
    supersedes_artifact_review_id: str | None = None

    def __post_init__(self) -> None:
        identifier(self.artifact_review_id, "artifact_review_id")
        identifier(self.artifact_instance_id, "artifact_instance_id")
        if not isinstance(self.reviewer, ActorReference):
            raise ConcordModelError("reviewer must be ActorReference.")
        timestamp(self.reviewed_at, "reviewed_at")
        controlled(
            self.readability_judgment,
            "readability_judgment",
            frozenset(
                {"readable", "partially_readable", "unreadable", "not_reviewed"}
            ),
        )
        controlled(
            self.page_completeness_judgment,
            "page_completeness_judgment",
            frozenset(
                {"complete", "partially_complete", "incomplete", "not_reviewed"}
            ),
        )
        controlled(
            self.filing_judgment,
            "filing_judgment",
            frozenset(
                {"correct", "misfiled", "duplicate", "unresolved", "not_reviewed"}
            ),
        )
        controlled(
            self.author_judgment,
            "author_judgment",
            frozenset(
                {"confirmed", "qualified", "disputed", "unknown", "not_reviewed"}
            ),
        )
        controlled(
            self.subject_judgment,
            "subject_judgment",
            frozenset(
                {"confirmed", "qualified", "disputed", "unresolved", "not_reviewed"}
            ),
        )
        controlled(
            self.privacy_judgment,
            "privacy_judgment",
            frozenset(
                {
                    "teacher_restricted",
                    "teacher_and_subjects",
                    "group_and_teacher",
                    "classroom_shared",
                }
            ),
        )
        controlled(
            self.relevance_judgment,
            "relevance_judgment",
            frozenset(
                {"relevant", "partially_relevant", "not_relevant", "not_reviewed"}
            ),
        )
        moderation = controlled(
            self.moderation_requirement,
            "moderation_requirement",
            frozenset({"required", "not_required", "completed"}),
        )
        readiness = controlled(
            self.scoring_readiness,
            "scoring_readiness",
            frozenset({"ready", "ready_with_qualification", "not_ready"}),
        )
        outcome = controlled(
            self.review_outcome,
            "review_outcome",
            frozenset(
                {
                    "ready",
                    "ready_with_qualification",
                    "incomplete",
                    "unreadable",
                    "misrouted",
                    "duplicate",
                    "awaiting_correction",
                    "awaiting_additional_evidence",
                    "moderation_required",
                    "not_suitable_for_scoring",
                }
            ),
        )
        optional_text(self.notes, "notes")
        if not isinstance(self.privacy_policy, PrivacyPolicy):
            raise ConcordModelError("privacy_policy must be PrivacyPolicy.")

        if moderation == "required" and readiness != "not_ready":
            raise ConcordModelError(
                "required moderation must remain not_ready until explicitly completed."
            )
        if outcome == "ready":
            if readiness != "ready":
                raise ConcordModelError(
                    "ready outcome requires ready scoring_readiness."
                )
            if moderation == "required":
                raise ConcordModelError("ready outcome cannot have pending moderation.")
            if self.readability_judgment == "unreadable":
                raise ConcordModelError("ready outcome cannot be unreadable.")
            if self.page_completeness_judgment == "incomplete":
                raise ConcordModelError("ready outcome cannot be incomplete.")
            if self.filing_judgment in {"misfiled", "duplicate"}:
                raise ConcordModelError(
                    "ready outcome cannot have blocking filing state."
                )
            if self.relevance_judgment == "not_relevant":
                raise ConcordModelError("ready outcome cannot be not_relevant.")
        if outcome == "ready_with_qualification":
            if readiness != "ready_with_qualification":
                raise ConcordModelError(
                    "qualified outcome requires qualified scoring_readiness."
                )
            if self.notes is None:
                raise ConcordModelError(
                    "ready_with_qualification requires explanatory notes."
                )
        if outcome == "moderation_required":
            if moderation != "required" or readiness != "not_ready":
                raise ConcordModelError(
                    "moderation_required outcome requires required moderation "
                    "and not_ready scoring readiness."
                )
        if outcome in _BLOCKING_REVIEW_OUTCOMES and readiness != "not_ready":
            raise ConcordModelError(
                "blocking Review outcomes require not_ready scoring readiness."
            )
        optional_identifier(
            self.supersedes_artifact_review_id, "supersedes_artifact_review_id"
        )


def _subject_sort_key(reference: SubjectReference) -> tuple[str, str, str, str]:
    return (
        reference.subject_kind,
        reference.owning_system,
        reference.subject_id,
        reference.contract_version or "",
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class ModerationRecord:
    moderation_record_id: str
    target_evidence_reference: EvidenceReference
    target_subject_references: tuple[SubjectReference, ...]
    moderator: ActorReference
    moderated_at: str
    status: str
    permitted_use: str
    rationale: str
    privacy_policy: PrivacyPolicy
    qualification: str | None = None
    supersedes_moderation_record_id: str | None = None

    def __post_init__(self) -> None:
        identifier(self.moderation_record_id, "moderation_record_id")
        if not isinstance(self.target_evidence_reference, EvidenceReference):
            raise ConcordModelError(
                "target_evidence_reference must be EvidenceReference."
            )
        subjects = tuple_of_values(
            self.target_subject_references,
            SubjectReference,
            "target_subject_references",
        )
        if len(set(subjects)) != len(subjects):
            raise ConcordModelError(
                "target_subject_references must not contain duplicates."
            )
        object.__setattr__(
            self,
            "target_subject_references",
            tuple(sorted(subjects, key=_subject_sort_key)),
        )
        if not isinstance(self.moderator, ActorReference):
            raise ConcordModelError("moderator must be ActorReference.")
        timestamp(self.moderated_at, "moderated_at")
        status = controlled(
            self.status,
            "status",
            frozenset(
                {
                    "accepted",
                    "accepted_with_qualification",
                    "insufficient",
                    "disputed",
                    "rejected",
                    "not_used_for_scoring",
                }
            ),
        )
        permitted_use = controlled(
            self.permitted_use,
            "permitted_use",
            frozenset(
                {
                    "support_group_score",
                    "support_named_subject",
                    "corroborate_only",
                    "formative_only",
                    "not_independently_determine_score",
                    "not_be_used_for_scoring",
                }
            ),
        )
        require_text(self.rationale, "rationale")
        optional_text(self.qualification, "qualification")
        if not isinstance(self.privacy_policy, PrivacyPolicy):
            raise ConcordModelError("privacy_policy must be PrivacyPolicy.")
        if status == "accepted_with_qualification" and self.qualification is None:
            raise ConcordModelError(
                "accepted_with_qualification requires qualification."
            )
        if status in {"rejected", "not_used_for_scoring"} and (
            permitted_use != "not_be_used_for_scoring"
        ):
            raise ConcordModelError(
                "rejected/not-used evidence must not be permitted for scoring."
            )
        if status in {"insufficient", "disputed"} and permitted_use in {
            "support_group_score",
            "support_named_subject",
        }:
            raise ConcordModelError(
                "insufficient/disputed evidence cannot directly support a Score."
            )
        if permitted_use == "support_named_subject" and not any(
            subject.subject_kind == "core_student"
            for subject in self.target_subject_references
        ):
            raise ConcordModelError(
                "support_named_subject requires an explicit student Subject scope."
            )
        if permitted_use == "support_group_score" and not any(
            subject.subject_kind == "concord_group"
            for subject in self.target_subject_references
        ):
            raise ConcordModelError(
                "support_group_score requires an explicit Concord Group scope."
            )
        optional_identifier(
            self.supersedes_moderation_record_id, "supersedes_moderation_record_id"
        )
