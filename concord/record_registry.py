"""One authoritative descriptor registry for Concord native records."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from concord.models import (
    Activity,
    ArtifactAuthor,
    ArtifactInstance,
    ArtifactPage,
    ArtifactReview,
    ArtifactSubject,
    CorrectionRecord,
    Criterion,
    CriterionSet,
    Group,
    GroupMembership,
    GroupPlan,
    ModerationRecord,
    ResponsibilityAssignment,
    RoleAssignment,
    ScanReference,
    ScoreEvidenceLink,
    ScoreRecord,
    ScoringScale,
    Session,
)


@dataclass(frozen=True, slots=True)
class RecordDescriptor:
    kind: str
    model_type: type[Any]
    identity_field: str
    graph_collection: str


RECORD_DESCRIPTORS: tuple[RecordDescriptor, ...] = (
    RecordDescriptor("activity", Activity, "activity_id", "activities"),
    RecordDescriptor("session", Session, "session_id", "sessions"),
    RecordDescriptor("group_plan", GroupPlan, "group_plan_id", "group_plans"),
    RecordDescriptor("group", Group, "group_id", "groups"),
    RecordDescriptor(
        "group_membership", GroupMembership, "membership_id", "memberships"
    ),
    RecordDescriptor(
        "role_assignment", RoleAssignment, "role_assignment_id", "role_assignments"
    ),
    RecordDescriptor(
        "responsibility_assignment",
        ResponsibilityAssignment,
        "responsibility_assignment_id",
        "responsibility_assignments",
    ),
    RecordDescriptor(
        "artifact_instance",
        ArtifactInstance,
        "artifact_instance_id",
        "artifact_instances",
    ),
    RecordDescriptor(
        "artifact_page", ArtifactPage, "artifact_page_id", "artifact_pages"
    ),
    RecordDescriptor(
        "scan_reference", ScanReference, "scan_reference_id", "scan_references"
    ),
    RecordDescriptor(
        "artifact_author", ArtifactAuthor, "artifact_author_id", "artifact_authors"
    ),
    RecordDescriptor(
        "artifact_subject", ArtifactSubject, "artifact_subject_id", "artifact_subjects"
    ),
    RecordDescriptor(
        "artifact_review", ArtifactReview, "artifact_review_id", "artifact_reviews"
    ),
    RecordDescriptor(
        "moderation_record",
        ModerationRecord,
        "moderation_record_id",
        "moderation_records",
    ),
    RecordDescriptor(
        "criterion_set", CriterionSet, "criterion_set_id", "criterion_sets"
    ),
    RecordDescriptor("criterion", Criterion, "criterion_id", "criteria"),
    RecordDescriptor(
        "scoring_scale", ScoringScale, "scoring_scale_id", "scoring_scales"
    ),
    RecordDescriptor("score_record", ScoreRecord, "score_record_id", "score_records"),
    RecordDescriptor(
        "score_evidence_link",
        ScoreEvidenceLink,
        "score_evidence_link_id",
        "score_evidence_links",
    ),
    RecordDescriptor(
        "correction", CorrectionRecord, "correction_id", "correction_records"
    ),
)

DESCRIPTOR_BY_KIND = {item.kind: item for item in RECORD_DESCRIPTORS}
DESCRIPTOR_BY_TYPE = {item.model_type: item for item in RECORD_DESCRIPTORS}
CONVERSION_KIND_ALIASES = {"correction_record": "correction"}


def descriptor_for_kind(kind: str, *, allow_alias: bool = False) -> RecordDescriptor:
    canonical = CONVERSION_KIND_ALIASES.get(kind, kind) if allow_alias else kind
    try:
        return DESCRIPTOR_BY_KIND[canonical]
    except (KeyError, TypeError) as error:
        raise ValueError(f"unsupported record_kind {kind!r}.") from error


def descriptor_for_record(record: object) -> RecordDescriptor:
    try:
        return DESCRIPTOR_BY_TYPE[type(record)]
    except KeyError as error:
        raise ValueError(f"unsupported record type {type(record).__name__}.") from error


__all__ = [
    "CONVERSION_KIND_ALIASES",
    "DESCRIPTOR_BY_KIND",
    "DESCRIPTOR_BY_TYPE",
    "RECORD_DESCRIPTORS",
    "RecordDescriptor",
    "descriptor_for_kind",
    "descriptor_for_record",
]
