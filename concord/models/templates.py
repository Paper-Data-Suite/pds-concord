"""Typed reusable Template Definition contracts for Concord v0.3."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

from concord.models.artifacts import (
    ARTIFACT_CATEGORIES,
    ARTIFACT_EXPECTED_RETURN_STATUSES,
    ARTIFACT_PAGE_KINDS,
    AUTHORSHIP_MODES,
)
from concord.models.collaboration import ACTIVITY_TYPES, SCORING_ORIENTATIONS
from concord.models.common import (
    ActorReference,
    ConcordModelError,
    PrivacyPolicy,
    Provenance,
    controlled,
    controlled_key,
    identifier,
    optional_identifier,
    optional_positive_int,
    optional_text,
    positive_int,
    require_bool,
    require_text,
    tuple_of_identifiers,
    tuple_of_values,
)

TEMPLATE_DEFINITION_STATUSES = frozenset({"draft", "active", "retired"})
TEMPLATE_VERSION_STATUSES = frozenset({"draft", "active", "retired", "superseded"})
TEMPLATE_RENDERING_INPUT_SOURCES = frozenset(
    {
        "teacher_text",
        "activity_title",
        "session_label",
        "group_label",
        "participant_display_label",
        "current_date",
        "criterion_label",
        "pds2_route_payload",
        "human_fallback",
    }
)
TEMPLATE_RENDERING_VALUE_KINDS = frozenset(
    {"text", "multiline_text", "integer", "boolean", "date"}
)
TEMPLATE_RESPONSE_REGION_KINDS = frozenset(
    {
        "free_response",
        "structured_entry",
        "selection",
        "table",
        "drawing",
        "annotation",
        "teacher_observation",
    }
)
TEMPLATE_AUDIENCE_KINDS = frozenset({"activity", "group", "participant", "teacher"})
TEMPLATE_CRITERION_KINDS = frozenset({"standard_backed", "local"})
TEMPLATE_SUBJECT_KINDS = frozenset(
    {
        "core_student",
        "concord_group",
        "concord_session",
        "concord_activity",
        "external_record",
    }
)
TEMPLATE_DIRECT_PRIVACY_CLASSIFICATIONS = frozenset(
    {
        "teacher_restricted",
        "teacher_and_subjects",
        "group_and_teacher",
        "classroom_shared",
    }
)
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _controlled_tuple(
    value: Iterable[str],
    field_name: str,
    allowed: frozenset[str],
    *,
    allow_extensions: bool = False,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ConcordModelError(f"{field_name} must be an iterable.")
    try:
        values = tuple(value)
    except TypeError as error:
        raise ConcordModelError(f"{field_name} must be iterable.") from error
    normalized = tuple(
        (
            controlled_key(item, f"{field_name}[{index}]", allowed)
            if allow_extensions
            else controlled(item, f"{field_name}[{index}]", allowed)
        )
        for index, item in enumerate(values)
    )
    if len(set(normalized)) != len(normalized):
        raise ConcordModelError(f"{field_name} must not contain duplicates.")
    return tuple(sorted(normalized))


def _sha256(value: object, field_name: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise ConcordModelError(
            f"{field_name} must be a lowercase 64-character SHA-256 digest."
        )
    return value


@dataclass(frozen=True, slots=True, kw_only=True)
class TemplateRenderingInput:
    """One reusable declaration for a value bound only during generation."""

    input_key: str
    label: str
    source_kind: str
    value_kind: str
    required: bool
    description: str | None = None
    max_length: int | None = None

    def __post_init__(self) -> None:
        identifier(self.input_key, "input_key")
        require_text(self.label, "label")
        controlled_key(
            self.source_kind,
            "source_kind",
            TEMPLATE_RENDERING_INPUT_SOURCES,
        )
        controlled(
            self.value_kind,
            "value_kind",
            TEMPLATE_RENDERING_VALUE_KINDS,
        )
        require_bool(self.required, "required")
        optional_text(self.description, "description")
        maximum = optional_positive_int(self.max_length, "max_length")
        if maximum is not None and self.value_kind not in {"text", "multiline_text"}:
            raise ConcordModelError(
                "max_length is permitted only for text rendering inputs."
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class TemplateResponseRegion:
    """One semantic printable evidence-capture region."""

    region_key: str
    label: str
    region_kind: str
    required: bool
    description: str | None = None

    def __post_init__(self) -> None:
        identifier(self.region_key, "region_key")
        require_text(self.label, "label")
        controlled_key(
            self.region_kind,
            "region_kind",
            TEMPLATE_RESPONSE_REGION_KINDS,
        )
        require_bool(self.required, "required")
        optional_text(self.description, "description")


@dataclass(frozen=True, slots=True, kw_only=True)
class TemplatePageDefinition:
    """One reusable page declaration; never a generated ArtifactPage."""

    page_key: str
    sequence: int
    page_kind: str
    return_expected: bool
    route_required: bool
    rendering_input_keys: tuple[str, ...] = ()
    response_regions: tuple[TemplateResponseRegion, ...] = ()
    label: str | None = None
    route_payload_input_key: str | None = None
    human_fallback_input_key: str | None = None

    def __post_init__(self) -> None:
        identifier(self.page_key, "page_key")
        positive_int(self.sequence, "sequence")
        controlled_key(self.page_kind, "page_kind", ARTIFACT_PAGE_KINDS)
        require_bool(self.return_expected, "return_expected")
        require_bool(self.route_required, "route_required")
        object.__setattr__(
            self,
            "rendering_input_keys",
            tuple_of_identifiers(
                self.rendering_input_keys,
                "rendering_input_keys",
            ),
        )
        object.__setattr__(
            self,
            "response_regions",
            tuple_of_values(
                self.response_regions,
                TemplateResponseRegion,
                "response_regions",
            ),
        )
        optional_text(self.label, "label")
        optional_identifier(self.route_payload_input_key, "route_payload_input_key")
        optional_identifier(self.human_fallback_input_key, "human_fallback_input_key")

        region_keys = tuple(item.region_key for item in self.response_regions)
        if len(set(region_keys)) != len(region_keys):
            raise ConcordModelError(
                "response_regions must not duplicate region_key within one page."
            )

        if self.route_required:
            if not self.return_expected:
                raise ConcordModelError(
                    "route-required Template pages must be expected to return."
                )
            if (
                self.route_payload_input_key is None
                or self.human_fallback_input_key is None
            ):
                raise ConcordModelError(
                    "route-required Template pages require route payload and "
                    "human-fallback rendering input keys."
                )
            for key in (
                self.route_payload_input_key,
                self.human_fallback_input_key,
            ):
                if key not in self.rendering_input_keys:
                    raise ConcordModelError(
                        "route rendering input keys must appear in "
                        "rendering_input_keys."
                    )
        elif (
            self.route_payload_input_key is not None
            or self.human_fallback_input_key is not None
        ):
            raise ConcordModelError(
                "non-route Template pages must not declare route rendering slots."
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class TemplateAuthorshipExpectation:
    """Reusable authorship expectation, never an ArtifactAuthor association."""

    authorship_mode: str
    required: bool = True
    multiple_allowed: bool = False

    def __post_init__(self) -> None:
        controlled(self.authorship_mode, "authorship_mode", AUTHORSHIP_MODES)
        require_bool(self.required, "required")
        require_bool(self.multiple_allowed, "multiple_allowed")


@dataclass(frozen=True, slots=True, kw_only=True)
class TemplateSubjectExpectation:
    """Reusable Subject-kind expectation without a concrete Subject identity."""

    subject_kind: str
    required: bool = True
    multiple_allowed: bool = False

    def __post_init__(self) -> None:
        controlled(self.subject_kind, "subject_kind", TEMPLATE_SUBJECT_KINDS)
        require_bool(self.required, "required")
        require_bool(self.multiple_allowed, "multiple_allowed")


@dataclass(frozen=True, slots=True, kw_only=True)
class TemplateCompatibility:
    """Identity-free compatibility guidance for later Template selection."""

    audience_kinds: tuple[str, ...] = ()
    activity_type_keys: tuple[str, ...] = ()
    scoring_orientations: tuple[str, ...] = ()
    criterion_kinds: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "audience_kinds",
            _controlled_tuple(
                self.audience_kinds,
                "audience_kinds",
                TEMPLATE_AUDIENCE_KINDS,
            ),
        )
        object.__setattr__(
            self,
            "activity_type_keys",
            _controlled_tuple(
                self.activity_type_keys,
                "activity_type_keys",
                ACTIVITY_TYPES,
                allow_extensions=True,
            ),
        )
        object.__setattr__(
            self,
            "scoring_orientations",
            _controlled_tuple(
                self.scoring_orientations,
                "scoring_orientations",
                SCORING_ORIENTATIONS,
            ),
        )
        object.__setattr__(
            self,
            "criterion_kinds",
            _controlled_tuple(
                self.criterion_kinds,
                "criterion_kinds",
                TEMPLATE_CRITERION_KINDS,
            ),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class TemplateDefinition:
    """Stable reusable lineage identity for one printable design."""

    template_id: str
    name: str
    purpose: str
    artifact_category: str
    status: str
    created_provenance: Provenance
    description: str | None = None
    owner_reference: ActorReference | None = None

    def __post_init__(self) -> None:
        identifier(self.template_id, "template_id")
        require_text(self.name, "name")
        require_text(self.purpose, "purpose")
        controlled_key(
            self.artifact_category,
            "artifact_category",
            ARTIFACT_CATEGORIES,
        )
        controlled(self.status, "status", TEMPLATE_DEFINITION_STATUSES)
        if not isinstance(self.created_provenance, Provenance):
            raise ConcordModelError("created_provenance must be Provenance.")
        optional_text(self.description, "description")
        if self.owner_reference is not None:
            if not isinstance(self.owner_reference, ActorReference):
                raise ConcordModelError("owner_reference must be an ActorReference.")
            if self.owner_reference.actor_kind == "core_student":
                raise ConcordModelError(
                    "reusable Template ownership must not embed a Core student."
                )


@dataclass(frozen=True, slots=True, kw_only=True)
class TemplateVersion:
    """One exact immutable printable revision of a Template Definition."""

    template_version_id: str
    template_id: str
    version_label: str
    revision_sequence: int
    rendering_contract_version: str
    rendering_specification_reference: str
    rendering_specification_sha256: str
    artifact_category: str
    page_manifest: tuple[TemplatePageDefinition, ...]
    rendering_inputs: tuple[TemplateRenderingInput, ...]
    default_expected_return_status: str
    default_privacy_policy: PrivacyPolicy
    compatibility: TemplateCompatibility
    created_provenance: Provenance
    status: str
    supersedes_template_version_id: str | None = None
    default_authorship_expectation: TemplateAuthorshipExpectation | None = None
    default_subject_expectation: TemplateSubjectExpectation | None = None

    def __post_init__(self) -> None:
        identifier(self.template_version_id, "template_version_id")
        identifier(self.template_id, "template_id")
        require_text(self.version_label, "version_label")
        revision = positive_int(self.revision_sequence, "revision_sequence")
        identifier(self.rendering_contract_version, "rendering_contract_version")
        identifier(
            self.rendering_specification_reference,
            "rendering_specification_reference",
        )
        _sha256(
            self.rendering_specification_sha256,
            "rendering_specification_sha256",
        )
        controlled_key(
            self.artifact_category,
            "artifact_category",
            ARTIFACT_CATEGORIES,
        )
        pages = tuple_of_values(
            self.page_manifest,
            TemplatePageDefinition,
            "page_manifest",
            nonempty=True,
        )
        pages = tuple(sorted(pages, key=lambda item: item.sequence))
        object.__setattr__(self, "page_manifest", pages)
        inputs = tuple_of_values(
            self.rendering_inputs,
            TemplateRenderingInput,
            "rendering_inputs",
        )
        inputs = tuple(sorted(inputs, key=lambda item: item.input_key))
        object.__setattr__(self, "rendering_inputs", inputs)
        expected_return = controlled(
            self.default_expected_return_status,
            "default_expected_return_status",
            ARTIFACT_EXPECTED_RETURN_STATUSES,
        )
        if not isinstance(self.default_privacy_policy, PrivacyPolicy):
            raise ConcordModelError(
                "default_privacy_policy must be a PrivacyPolicy."
            )
        if (
            self.default_privacy_policy.classification
            not in TEMPLATE_DIRECT_PRIVACY_CLASSIFICATIONS
            or self.default_privacy_policy.audience_references
            or self.default_privacy_policy.policy_reference is not None
            or self.default_privacy_policy.inherited_from is not None
        ):
            raise ConcordModelError(
                "Template privacy defaults must be identity-free direct "
                "classifications."
            )
        if not isinstance(self.compatibility, TemplateCompatibility):
            raise ConcordModelError(
                "compatibility must be a TemplateCompatibility."
            )
        if not isinstance(self.created_provenance, Provenance):
            raise ConcordModelError("created_provenance must be Provenance.")
        controlled(self.status, "status", TEMPLATE_VERSION_STATUSES)
        predecessor = optional_identifier(
            self.supersedes_template_version_id,
            "supersedes_template_version_id",
        )
        if revision == 1 and predecessor is not None:
            raise ConcordModelError(
                "the first Template Version must not supersede another version."
            )
        if revision > 1 and predecessor is None:
            raise ConcordModelError(
                "successor Template Versions require "
                "supersedes_template_version_id."
            )
        if predecessor == self.template_version_id:
            raise ConcordModelError("a Template Version cannot supersede itself.")
        if (
            self.default_authorship_expectation is not None
            and not isinstance(
                self.default_authorship_expectation,
                TemplateAuthorshipExpectation,
            )
        ):
            raise ConcordModelError(
                "default_authorship_expectation is invalid."
            )
        if (
            self.default_subject_expectation is not None
            and not isinstance(
                self.default_subject_expectation,
                TemplateSubjectExpectation,
            )
        ):
            raise ConcordModelError("default_subject_expectation is invalid.")

        page_keys = tuple(item.page_key for item in pages)
        if len(set(page_keys)) != len(page_keys):
            raise ConcordModelError("page_manifest must not duplicate page_key.")
        sequences = tuple(item.sequence for item in pages)
        if sequences != tuple(range(1, len(pages) + 1)):
            raise ConcordModelError(
                "page_manifest sequences must form contiguous 1..N order."
            )

        input_by_key = {item.input_key: item for item in inputs}
        if len(input_by_key) != len(inputs):
            raise ConcordModelError(
                "rendering_inputs must not duplicate input_key."
            )
        region_keys: list[str] = []
        for page in pages:
            unknown = sorted(set(page.rendering_input_keys) - set(input_by_key))
            if unknown:
                raise ConcordModelError(
                    "Template page references undeclared rendering input(s): "
                    + ", ".join(unknown)
                    + "."
                )
            region_keys.extend(item.region_key for item in page.response_regions)
            if page.route_required:
                assert page.route_payload_input_key is not None
                assert page.human_fallback_input_key is not None
                route_input = input_by_key[page.route_payload_input_key]
                fallback_input = input_by_key[page.human_fallback_input_key]
                if route_input.source_kind != "pds2_route_payload":
                    raise ConcordModelError(
                        "route_payload_input_key must reference a "
                        "pds2_route_payload input."
                    )
                if fallback_input.source_kind != "human_fallback":
                    raise ConcordModelError(
                        "human_fallback_input_key must reference a "
                        "human_fallback input."
                    )
        if len(set(region_keys)) != len(region_keys):
            raise ConcordModelError(
                "response region keys must be unique within one Template Version."
            )

        any_return = any(page.return_expected for page in pages)
        if expected_return == "return_not_expected" and any_return:
            raise ConcordModelError(
                "return_not_expected Template Versions cannot contain "
                "return-expected pages."
            )
        if expected_return != "return_not_expected" and not any_return:
            raise ConcordModelError(
                "returnable Template Versions require at least one "
                "return-expected page."
            )


__all__ = [
    "TemplateAuthorshipExpectation",
    "TemplateCompatibility",
    "TemplateDefinition",
    "TemplatePageDefinition",
    "TemplateRenderingInput",
    "TemplateResponseRegion",
    "TemplateSubjectExpectation",
    "TemplateVersion",
]
