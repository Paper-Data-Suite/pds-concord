"""Typed reusable Packet Definition contracts for Concord v0.3."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from pds_core.routing_models import ModuleRecordRef

from concord.models.collaboration import ROLE_KEYS
from concord.models.common import (
    ConcordModelError,
    Provenance,
    controlled,
    controlled_key,
    identifier,
    optional_identifier,
    optional_text,
    positive_int,
    require_bool,
    require_text,
    tuple_of_values,
)

PACKET_DEFINITION_STATUSES = frozenset({"draft", "active", "retired"})
PACKET_VERSION_STATUSES = frozenset({"draft", "active", "retired", "superseded"})
PACKET_COMPONENT_KINDS = frozenset({"concord_template", "external_component"})
PACKET_AUDIENCE_KINDS = frozenset(
    {"activity", "group", "participant", "teacher", "role"}
)
PACKET_REQUIREMENT_LEVELS = frozenset(
    {"required", "recommended", "conditional"}
)
PACKET_CONDITION_KINDS = frozenset(
    {
        "teacher_choice",
        "matching_role_present",
        "group_context_present",
        "participant_context_present",
    }
)
PACKET_COPY_COLLATIONS = frozenset({"component_major"})
PACKET_TARGET_ORDERS = frozenset({"stable_identity"})


def _role_keys(value: Iterable[str], field_name: str) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ConcordModelError(f"{field_name} must be an iterable.")
    try:
        values = tuple(value)
    except TypeError as error:
        raise ConcordModelError(f"{field_name} must be iterable.") from error
    normalized = tuple(
        controlled_key(item, f"{field_name}[{index}]", ROLE_KEYS)
        for index, item in enumerate(values)
    )
    if len(set(normalized)) != len(normalized):
        raise ConcordModelError(f"{field_name} must not contain duplicates.")
    return tuple(sorted(normalized))


@dataclass(frozen=True, slots=True, kw_only=True)
class PacketAudienceIntent:
    """Identity-free declaration of the kind of target for one component."""

    audience_kind: str
    role_keys: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        kind = controlled(
            self.audience_kind,
            "audience_kind",
            PACKET_AUDIENCE_KINDS,
        )
        roles = _role_keys(self.role_keys, "role_keys")
        object.__setattr__(self, "role_keys", roles)
        if kind == "role":
            if not roles:
                raise ConcordModelError(
                    "role audience intent requires at least one role_key."
                )
        elif roles:
            raise ConcordModelError(
                "role_keys are permitted only for role audience intent."
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class PacketCondition:
    """Bounded declarative generation condition; never executable code."""

    condition_kind: str
    role_keys: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        kind = controlled(
            self.condition_kind,
            "condition_kind",
            PACKET_CONDITION_KINDS,
        )
        roles = _role_keys(self.role_keys, "role_keys")
        object.__setattr__(self, "role_keys", roles)
        if kind == "matching_role_present":
            if not roles:
                raise ConcordModelError(
                    "matching_role_present requires at least one role_key."
                )
        elif roles:
            raise ConcordModelError(
                "role_keys are permitted only for matching_role_present."
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class PacketRenderingRules:
    """Small deterministic packet-assembly contract above Template rendering."""

    preserve_component_order: bool = True
    start_each_component_on_new_page: bool = False
    copy_collation: str = "component_major"
    target_order: str = "stable_identity"

    def __post_init__(self) -> None:
        preserve = require_bool(
            self.preserve_component_order,
            "preserve_component_order",
        )
        require_bool(
            self.start_each_component_on_new_page,
            "start_each_component_on_new_page",
        )
        controlled(
            self.copy_collation,
            "copy_collation",
            PACKET_COPY_COLLATIONS,
        )
        controlled(
            self.target_order,
            "target_order",
            PACKET_TARGET_ORDERS,
        )
        if not preserve:
            raise ConcordModelError(
                "Packet rendering must preserve declared component order."
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class PacketComponent:
    """One ordered immutable element of an exact Packet Version."""

    packet_component_id: str
    sequence: int
    component_kind: str
    copies_per_target: int
    audience_intent: PacketAudienceIntent
    requirement_level: str
    template_id: str | None = None
    template_version_id: str | None = None
    external_reference: ModuleRecordRef | None = None
    condition: PacketCondition | None = None
    label: str | None = None

    def __post_init__(self) -> None:
        identifier(self.packet_component_id, "packet_component_id")
        positive_int(self.sequence, "sequence")
        kind = controlled(
            self.component_kind,
            "component_kind",
            PACKET_COMPONENT_KINDS,
        )
        positive_int(self.copies_per_target, "copies_per_target")
        if not isinstance(self.audience_intent, PacketAudienceIntent):
            raise ConcordModelError(
                "audience_intent must be a PacketAudienceIntent."
            )
        level = controlled(
            self.requirement_level,
            "requirement_level",
            PACKET_REQUIREMENT_LEVELS,
        )
        template_id = optional_identifier(self.template_id, "template_id")
        version_id = optional_identifier(
            self.template_version_id,
            "template_version_id",
        )
        if self.external_reference is not None and not isinstance(
            self.external_reference,
            ModuleRecordRef,
        ):
            raise ConcordModelError(
                "external_reference must be a Core ModuleRecordRef."
            )
        if self.condition is not None and not isinstance(
            self.condition,
            PacketCondition,
        ):
            raise ConcordModelError("condition must be a PacketCondition.")
        optional_text(self.label, "label")

        if kind == "concord_template":
            if template_id is None or version_id is None:
                raise ConcordModelError(
                    "concord_template components require template_id and "
                    "template_version_id."
                )
            if self.external_reference is not None:
                raise ConcordModelError(
                    "concord_template components must not carry "
                    "external_reference."
                )
        else:
            if template_id is not None or version_id is not None:
                raise ConcordModelError(
                    "external_component must not carry Template identities."
                )
            if self.external_reference is None:
                raise ConcordModelError(
                    "external_component requires external_reference."
                )
            if self.external_reference.module_id == "concord":
                raise ConcordModelError(
                    "external_component must identify a source-owned record "
                    "outside Concord."
                )

        if level == "conditional":
            if self.condition is None:
                raise ConcordModelError(
                    "conditional components require an explicit condition."
                )
        elif self.condition is not None:
            raise ConcordModelError(
                "non-conditional components must not carry a condition."
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class PacketDefinition:
    """Stable reusable lineage identity for one Packet design."""

    packet_definition_id: str
    name: str
    purpose: str
    status: str
    created_provenance: Provenance
    description: str | None = None

    def __post_init__(self) -> None:
        identifier(self.packet_definition_id, "packet_definition_id")
        require_text(self.name, "name")
        require_text(self.purpose, "purpose")
        controlled(
            self.status,
            "status",
            PACKET_DEFINITION_STATUSES,
        )
        if not isinstance(self.created_provenance, Provenance):
            raise ConcordModelError("created_provenance must be Provenance.")
        optional_text(self.description, "description")


@dataclass(frozen=True, slots=True, kw_only=True)
class PacketVersion:
    """One exact immutable ordered composition of reusable components."""

    packet_version_id: str
    packet_definition_id: str
    version_label: str
    revision_sequence: int
    components: tuple[PacketComponent, ...]
    rendering_rules: PacketRenderingRules
    created_provenance: Provenance
    status: str
    supersedes_packet_version_id: str | None = None

    def __post_init__(self) -> None:
        identifier(self.packet_version_id, "packet_version_id")
        identifier(self.packet_definition_id, "packet_definition_id")
        require_text(self.version_label, "version_label")
        revision = positive_int(self.revision_sequence, "revision_sequence")
        components = tuple_of_values(
            self.components,
            PacketComponent,
            "components",
            nonempty=True,
        )
        components = tuple(sorted(components, key=lambda item: item.sequence))
        object.__setattr__(self, "components", components)
        if not isinstance(self.rendering_rules, PacketRenderingRules):
            raise ConcordModelError(
                "rendering_rules must be PacketRenderingRules."
            )
        if not isinstance(self.created_provenance, Provenance):
            raise ConcordModelError("created_provenance must be Provenance.")
        controlled(self.status, "status", PACKET_VERSION_STATUSES)
        predecessor = optional_identifier(
            self.supersedes_packet_version_id,
            "supersedes_packet_version_id",
        )
        if revision == 1 and predecessor is not None:
            raise ConcordModelError(
                "the first Packet Version must not supersede another version."
            )
        if revision > 1 and predecessor is None:
            raise ConcordModelError(
                "successor Packet Versions require "
                "supersedes_packet_version_id."
            )
        if predecessor == self.packet_version_id:
            raise ConcordModelError("a Packet Version cannot supersede itself.")

        component_ids = tuple(
            item.packet_component_id for item in components
        )
        if len(set(component_ids)) != len(component_ids):
            raise ConcordModelError(
                "components must not duplicate packet_component_id."
            )
        sequences = tuple(item.sequence for item in components)
        if sequences != tuple(range(1, len(components) + 1)):
            raise ConcordModelError(
                "component sequences must form contiguous 1..N order."
            )


__all__ = [
    "PACKET_AUDIENCE_KINDS",
    "PACKET_COMPONENT_KINDS",
    "PACKET_CONDITION_KINDS",
    "PACKET_DEFINITION_STATUSES",
    "PACKET_REQUIREMENT_LEVELS",
    "PACKET_VERSION_STATUSES",
    "PacketAudienceIntent",
    "PacketComponent",
    "PacketCondition",
    "PacketDefinition",
    "PacketRenderingRules",
    "PacketVersion",
]
