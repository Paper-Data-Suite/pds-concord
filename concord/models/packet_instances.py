"""Activity-owned runtime Packet Instance contracts for Concord v0.3."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import PurePosixPath

from concord.models.collaboration import ROLE_KEYS
from concord.models.common import (
    ActorReference,
    ConcordModelError,
    ParticipantReference,
    Provenance,
    controlled,
    controlled_key,
    identifier,
    optional_identifier,
    positive_int,
    tuple_of_values,
)

PACKET_INSTANCE_AUDIENCE_KINDS = frozenset(
    {"activity", "group", "participant", "teacher", "role"}
)
PACKET_INSTANCE_GENERATION_STATUSES = frozenset(
    {"planned", "routes_pending", "rendering", "generated", "failed", "cancelled"}
)
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True, kw_only=True)
class PacketTargetContext:
    """One concrete Activity/Session audience target for a Packet Instance."""

    audience_kind: str
    activity_id: str
    session_id: str
    group_id: str | None = None
    participant_reference: ParticipantReference | None = None
    actor_reference: ActorReference | None = None
    role_assignment_id: str | None = None
    role_key: str | None = None

    def __post_init__(self) -> None:
        audience = controlled(
            self.audience_kind,
            "audience_kind",
            PACKET_INSTANCE_AUDIENCE_KINDS,
        )
        identifier(self.activity_id, "activity_id")
        identifier(self.session_id, "session_id")
        optional_identifier(self.group_id, "group_id")
        optional_identifier(self.role_assignment_id, "role_assignment_id")
        if self.participant_reference is not None and not isinstance(
            self.participant_reference, ParticipantReference
        ):
            raise ConcordModelError(
                "participant_reference must be a ParticipantReference."
            )
        if self.actor_reference is not None and not isinstance(
            self.actor_reference, ActorReference
        ):
            raise ConcordModelError("actor_reference must be an ActorReference.")
        if self.role_key is not None:
            controlled_key(self.role_key, "role_key", ROLE_KEYS)

        if audience == "activity":
            if any(
                value is not None
                for value in (
                    self.group_id,
                    self.participant_reference,
                    self.actor_reference,
                    self.role_assignment_id,
                    self.role_key,
                )
            ):
                raise ConcordModelError(
                    "activity Packet target must not carry Group, participant, "
                    "teacher, or Role context."
                )
        elif audience == "group":
            if self.group_id is None:
                raise ConcordModelError("group Packet target requires group_id.")
            if any(
                value is not None
                for value in (
                    self.participant_reference,
                    self.actor_reference,
                    self.role_assignment_id,
                    self.role_key,
                )
            ):
                raise ConcordModelError(
                    "group Packet target must not carry participant, teacher, "
                    "or Role context."
                )
        elif audience == "participant":
            if self.participant_reference is None:
                raise ConcordModelError(
                    "participant Packet target requires participant_reference."
                )
            if any(
                value is not None
                for value in (
                    self.actor_reference,
                    self.role_assignment_id,
                    self.role_key,
                )
            ):
                raise ConcordModelError(
                    "participant Packet target must not carry teacher or Role context."
                )
        elif audience == "teacher":
            actor = self.actor_reference
            if actor is None or actor.actor_kind != "authorized_adult":
                raise ConcordModelError(
                    "teacher Packet target requires an authorized-adult actor."
                )
            if any(
                value is not None
                for value in (
                    self.group_id,
                    self.participant_reference,
                    self.role_assignment_id,
                    self.role_key,
                )
            ):
                raise ConcordModelError(
                    "teacher Packet target must not carry Group, participant, "
                    "or Role context."
                )
        else:
            if (
                self.participant_reference is None
                or self.role_assignment_id is None
                or self.role_key is None
            ):
                raise ConcordModelError(
                    "role Packet target requires participant_reference, "
                    "role_assignment_id, and role_key."
                )
            if self.actor_reference is not None:
                raise ConcordModelError(
                    "role Packet target must not carry teacher actor context."
                )


@dataclass(frozen=True, slots=True, kw_only=True)
class PacketRenderingValue:
    """One frozen non-route rendering value for deterministic re-rendering."""

    input_key: str
    source_kind: str
    value_kind: str
    value: str | int | bool

    def __post_init__(self) -> None:
        identifier(self.input_key, "input_key")
        identifier(self.source_kind, "source_kind")
        controlled(
            self.value_kind,
            "value_kind",
            frozenset({"text", "multiline_text", "integer", "boolean", "date"}),
        )
        if self.value_kind in {"text", "multiline_text", "date"}:
            if not isinstance(self.value, str):
                raise ConcordModelError(
                    "text/date Packet rendering values require a string."
                )
            if self.value_kind == "date":
                try:
                    date.fromisoformat(self.value)
                except ValueError as error:
                    raise ConcordModelError(
                        "date Packet rendering values require ISO date."
                    ) from error
        elif self.value_kind == "integer":
            if type(self.value) is not int:
                raise ConcordModelError(
                    "integer Packet rendering values require an integer."
                )
        elif type(self.value) is not bool:
            raise ConcordModelError(
                "boolean Packet rendering values require a boolean."
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class PacketInstanceArtifactBinding:
    """Exact Packet component/copy provenance for one generated Artifact."""

    packet_component_id: str
    component_sequence: int
    copy_index: int
    template_id: str
    template_version_id: str
    artifact_instance_id: str
    rendering_values: tuple[PacketRenderingValue, ...] = ()

    def __post_init__(self) -> None:
        identifier(self.packet_component_id, "packet_component_id")
        positive_int(self.component_sequence, "component_sequence")
        positive_int(self.copy_index, "copy_index")
        identifier(self.template_id, "template_id")
        identifier(self.template_version_id, "template_version_id")
        identifier(self.artifact_instance_id, "artifact_instance_id")
        values = tuple_of_values(
            self.rendering_values,
            PacketRenderingValue,
            "rendering_values",
        )
        values = tuple(sorted(values, key=lambda item: item.input_key))
        if len({item.input_key for item in values}) != len(values):
            raise ConcordModelError(
                "rendering_values must not duplicate input_key."
            )
        object.__setattr__(self, "rendering_values", values)


@dataclass(frozen=True, slots=True, kw_only=True)
class PacketInstance:
    """One concrete target-specific instantiation of one exact Packet Version."""

    packet_instance_id: str
    generation_id: str
    packet_definition_id: str
    packet_version_id: str
    activity_id: str
    session_id: str
    target_context: PacketTargetContext
    artifact_bindings: tuple[PacketInstanceArtifactBinding, ...]
    generation_status: str
    created_provenance: Provenance
    review_digest: str | None = None
    generation_date: str | None = None
    output_relative_path: str | None = None
    output_sha256: str | None = None

    def __post_init__(self) -> None:
        for name in (
            "packet_instance_id",
            "generation_id",
            "packet_definition_id",
            "packet_version_id",
            "activity_id",
            "session_id",
        ):
            identifier(getattr(self, name), name)
        if not isinstance(self.target_context, PacketTargetContext):
            raise ConcordModelError("target_context must be a PacketTargetContext.")
        if (
            self.target_context.activity_id != self.activity_id
            or self.target_context.session_id != self.session_id
        ):
            raise ConcordModelError(
                "Packet target context must match Packet Instance Activity/Session."
            )
        bindings = tuple_of_values(
            self.artifact_bindings,
            PacketInstanceArtifactBinding,
            "artifact_bindings",
            nonempty=True,
        )
        bindings = tuple(
            sorted(
                bindings,
                key=lambda item: (
                    item.component_sequence,
                    item.copy_index,
                    item.artifact_instance_id,
                ),
            )
        )
        object.__setattr__(self, "artifact_bindings", bindings)
        controlled(
            self.generation_status,
            "generation_status",
            PACKET_INSTANCE_GENERATION_STATUSES,
        )
        if not isinstance(self.created_provenance, Provenance):
            raise ConcordModelError("created_provenance must be Provenance.")
        if (self.review_digest is None) != (self.generation_date is None):
            raise ConcordModelError(
                "review_digest and generation_date must be present together."
            )
        if self.review_digest is not None:
            if _SHA256.fullmatch(self.review_digest) is None:
                raise ConcordModelError(
                    "review_digest must be a lowercase SHA-256 digest."
                )
            assert self.generation_date is not None
            try:
                parsed_date = date.fromisoformat(self.generation_date)
            except ValueError as error:
                raise ConcordModelError(
                    "generation_date must be an ISO calendar date."
                ) from error
            if parsed_date.isoformat() != self.generation_date:
                raise ConcordModelError(
                    "generation_date must use canonical ISO date form."
                )

        artifact_ids = tuple(item.artifact_instance_id for item in bindings)
        if len(set(artifact_ids)) != len(artifact_ids):
            raise ConcordModelError(
                "artifact_bindings must not reuse artifact_instance_id."
            )
        component_copy_keys = tuple(
            (item.packet_component_id, item.copy_index) for item in bindings
        )
        if len(set(component_copy_keys)) != len(component_copy_keys):
            raise ConcordModelError(
                "artifact_bindings must not duplicate a component copy."
            )

        by_component: dict[str, list[PacketInstanceArtifactBinding]] = {}
        for binding in bindings:
            by_component.setdefault(binding.packet_component_id, []).append(binding)
        sequence_owners: dict[int, str] = {}
        for component_id, component_bindings in by_component.items():
            first = component_bindings[0]
            prior_owner = sequence_owners.setdefault(
                first.component_sequence, component_id
            )
            if prior_owner != component_id:
                raise ConcordModelError(
                    "component_sequence must identify one Packet component."
                )
            expected_semantics = (
                first.component_sequence,
                first.template_id,
                first.template_version_id,
            )
            if any(
                (
                    item.component_sequence,
                    item.template_id,
                    item.template_version_id,
                )
                != expected_semantics
                for item in component_bindings
            ):
                raise ConcordModelError(
                    "copies of one Packet component must preserve exact "
                    "Template provenance."
                )
            copy_indexes = tuple(
                sorted(item.copy_index for item in component_bindings)
            )
            if copy_indexes != tuple(range(1, len(component_bindings) + 1)):
                raise ConcordModelError(
                    "Packet component copy_index values must form contiguous 1..N."
                )

        if (self.output_relative_path is None) != (self.output_sha256 is None):
            raise ConcordModelError(
                "Packet output path and SHA-256 must be present together."
            )
        if self.output_relative_path is not None:
            path = self.output_relative_path
            relative = PurePosixPath(path)
            if (
                "\\" in path
                or relative.is_absolute()
                or any(part in {"", ".", ".."} for part in relative.parts)
                or relative.parts[:2] != ("rendered", "packets")
                or relative.suffix.lower() != ".pdf"
            ):
                raise ConcordModelError(
                    "Packet output must be a safe PDF path beneath rendered/packets/."
                )
            digest = self.output_sha256
            if digest is None or _SHA256.fullmatch(digest) is None:
                raise ConcordModelError(
                    "output_sha256 must be a lowercase SHA-256 digest."
                )
        if self.generation_status == "generated":
            if self.output_relative_path is None:
                raise ConcordModelError(
                    "generated Packet Instance requires verified output metadata."
                )
        elif self.output_relative_path is not None:
            raise ConcordModelError(
                "only generated Packet Instance state may carry final output metadata."
            )


__all__ = [
    "PACKET_INSTANCE_AUDIENCE_KINDS",
    "PACKET_INSTANCE_GENERATION_STATUSES",
    "PacketInstance",
    "PacketInstanceArtifactBinding",
    "PacketRenderingValue",
    "PacketTargetContext",
]
