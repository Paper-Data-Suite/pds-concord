"""Artifact identity, page, authorship, and subject records."""

from __future__ import annotations

from dataclasses import dataclass

from concord.models.common import (
    AuthorReference,
    ConcordModelError,
    PrivacyPolicy,
    Provenance,
    SubjectReference,
    controlled,
    controlled_key,
    identifier,
    optional_identifier,
    optional_positive_int,
    optional_text,
    positive_int,
    require_bool,
    tuple_of_identifiers,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class ArtifactInstance:
    artifact_instance_id: str
    template_version_id: str
    activity_id: str
    artifact_category: str
    generation_status: str
    expected_return_status: str
    artifact_status: str
    privacy_policy: PrivacyPolicy
    page_ids: tuple[str, ...]
    created_provenance: Provenance
    packet_instance_id: str | None = None
    session_id: str | None = None
    group_id: str | None = None
    supersedes_artifact_instance_id: str | None = None

    def __post_init__(self) -> None:
        for name in ("artifact_instance_id", "template_version_id", "activity_id"):
            identifier(getattr(self, name), name)
        for name in (
            "packet_instance_id",
            "session_id",
            "group_id",
            "supersedes_artifact_instance_id",
        ):
            optional_identifier(getattr(self, name), name)
        controlled_key(
            self.artifact_category,
            "artifact_category",
            frozenset(
                {
                    "student_work",
                    "observation",
                    "discussion_record",
                    "laboratory_record",
                    "project_record",
                }
            ),
        )
        controlled(
            self.generation_status,
            "generation_status",
            frozenset({"planned", "completed", "failed", "cancelled", "superseded"}),
        )
        controlled(
            self.expected_return_status,
            "expected_return_status",
            frozenset(
                {"returned_expected", "returned_optional", "return_not_expected"}
            ),
        )
        controlled(
            self.artifact_status,
            "artifact_status",
            frozenset(
                {
                    "planned",
                    "generated",
                    "distributed",
                    "partially_returned",
                    "returned",
                    "completed",
                    "cancelled",
                    "archived",
                    "superseded",
                }
            ),
        )
        if not isinstance(self.privacy_policy, PrivacyPolicy):
            raise ConcordModelError("privacy_policy must be PrivacyPolicy.")
        object.__setattr__(
            self,
            "page_ids",
            tuple_of_identifiers(self.page_ids, "page_ids", nonempty=True),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class ArtifactPage:
    artifact_page_id: str
    artifact_instance_id: str
    page_number: int
    page_kind: str
    return_expected: bool
    route_required: bool
    page_status: str
    created_provenance: Provenance
    expected_page_count: int | None = None
    route_id: str | None = None
    human_fallback: str | None = None
    continuation_of_page_id: str | None = None

    def __post_init__(self) -> None:
        identifier(self.artifact_page_id, "artifact_page_id")
        identifier(self.artifact_instance_id, "artifact_instance_id")
        number = positive_int(self.page_number, "page_number")
        count = optional_positive_int(self.expected_page_count, "expected_page_count")
        if count is not None and count < number:
            raise ConcordModelError(
                "expected_page_count must not be less than page_number."
            )
        controlled_key(
            self.page_kind,
            "page_kind",
            frozenset(
                {
                    "primary",
                    "continuation",
                    "rubric",
                    "cover",
                    "instructional",
                    "observation",
                    "attachment_label",
                }
            ),
        )
        require_bool(self.return_expected, "return_expected")
        require_bool(self.route_required, "route_required")
        optional_identifier(self.route_id, "route_id")
        optional_text(self.human_fallback, "human_fallback")
        optional_identifier(self.continuation_of_page_id, "continuation_of_page_id")
        controlled(
            self.page_status,
            "page_status",
            frozenset(
                {
                    "planned",
                    "generated",
                    "distributed",
                    "returned",
                    "missing",
                    "duplicate",
                    "damaged",
                    "cancelled",
                    "archived",
                    "superseded",
                }
            ),
        )
        if self.route_required and (
            self.route_id is None or self.human_fallback is None
        ):
            raise ConcordModelError(
                "route-required pages require route_id and human_fallback."
            )
        if not self.route_required and self.route_id is not None:
            raise ConcordModelError("non-route pages must not carry route_id.")


@dataclass(frozen=True, slots=True, kw_only=True)
class ArtifactAuthor:
    artifact_author_id: str
    artifact_instance_id: str
    author_reference: AuthorReference
    authorship_mode: str
    attribution_status: str
    attribution_source: str
    created_provenance: Provenance
    represented_group_id: str | None = None
    role_assignment_id: str | None = None
    representation_status: str | None = None
    privacy_policy: PrivacyPolicy | None = None
    supersedes_artifact_author_id: str | None = None

    def __post_init__(self) -> None:
        identifier(self.artifact_author_id, "artifact_author_id")
        identifier(self.artifact_instance_id, "artifact_instance_id")
        controlled(
            self.authorship_mode,
            "authorship_mode",
            frozenset(
                {
                    "individual_author",
                    "co_author",
                    "observer",
                    "recorder",
                    "recorder_for_group",
                    "collective_group_author",
                    "teacher_author",
                    "authorized_adult_author",
                    "unknown",
                }
            ),
        )
        controlled(
            self.attribution_status,
            "attribution_status",
            frozenset({"proposed", "confirmed", "disputed", "unknown", "superseded"}),
        )
        controlled_key(
            self.attribution_source,
            "attribution_source",
            frozenset({"teacher", "participant", "imported", "system", "unknown"}),
        )
        for name in (
            "represented_group_id",
            "role_assignment_id",
            "supersedes_artifact_author_id",
        ):
            optional_identifier(getattr(self, name), name)
        if self.representation_status is not None:
            controlled(
                self.representation_status,
                "representation_status",
                frozenset(
                    {
                        "individual_view",
                        "recorder_summary",
                        "majority_position",
                        "unanimous_position",
                        "multiple_named_positions",
                        "no_consensus",
                        "not_applicable",
                    }
                ),
            )
        if (
            self.authorship_mode == "recorder_for_group"
            and self.represented_group_id is None
        ):
            raise ConcordModelError("recorder_for_group requires represented_group_id.")


@dataclass(frozen=True, slots=True, kw_only=True)
class ArtifactSubject:
    artifact_subject_id: str
    artifact_instance_id: str
    subject_reference: SubjectReference
    subject_role: str
    confirmation_status: str
    assignment_source: str
    created_provenance: Provenance
    criterion_id: str | None = None
    privacy_policy: PrivacyPolicy | None = None
    supersedes_artifact_subject_id: str | None = None

    def __post_init__(self) -> None:
        identifier(self.artifact_subject_id, "artifact_subject_id")
        identifier(self.artifact_instance_id, "artifact_instance_id")
        if not isinstance(self.subject_reference, SubjectReference):
            raise ConcordModelError("subject_reference must be SubjectReference.")
        controlled_key(
            self.subject_role,
            "subject_role",
            frozenset(
                {
                    "observed_participant",
                    "represented_group",
                    "activity_context",
                    "session_context",
                    "evaluated_artifact",
                    "general_subject",
                }
            ),
        )
        controlled(
            self.confirmation_status,
            "confirmation_status",
            frozenset(
                {"proposed", "confirmed", "disputed", "unresolved", "superseded"}
            ),
        )
        controlled_key(
            self.assignment_source,
            "assignment_source",
            frozenset({"teacher", "participant", "imported", "system"}),
        )
        optional_identifier(self.criterion_id, "criterion_id")
        optional_identifier(
            self.supersedes_artifact_subject_id, "supersedes_artifact_subject_id"
        )
