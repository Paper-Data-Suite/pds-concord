from __future__ import annotations

import dataclasses
from dataclasses import fields, replace

import pytest
from pds_core.routing_models import ModuleRecordRef

from concord.model_conversion import record_to_dict
from concord.models import (
    ActorReference,
    ArtifactInstance,
    ConcordModelError,
    PacketAudienceIntent,
    PacketComponent,
    PacketCondition,
    PacketDefinition,
    PacketRenderingRules,
    PacketVersion,
    PrivacyPolicy,
    Provenance,
)
from concord.models.collaboration import ROLE_KEYS
from concord.record_registry import RECORD_DESCRIPTORS


def _provenance() -> Provenance:
    return Provenance(
        actor=ActorReference(
            actor_kind="authorized_adult",
            actor_id="teacher-1",
            owning_system="concord",
        ),
        timestamp="2026-08-24T22:45:00-04:00",
        source_kind="manual",
        application_version="0.3.0.dev0",
    )


def _audience(
    kind: str = "group",
    *,
    role_keys: tuple[str, ...] = (),
) -> PacketAudienceIntent:
    return PacketAudienceIntent(
        audience_kind=kind,
        role_keys=role_keys,
    )


def _component(
    *,
    component_id: str = "component-1",
    sequence: int = 1,
    copies: int = 1,
    audience: PacketAudienceIntent | None = None,
    requirement_level: str = "required",
    condition: PacketCondition | None = None,
) -> PacketComponent:
    return PacketComponent(
        packet_component_id=component_id,
        sequence=sequence,
        component_kind="concord_template",
        template_id="template-1",
        template_version_id="template-version-1",
        copies_per_target=copies,
        audience_intent=audience or _audience(),
        requirement_level=requirement_level,
        condition=condition,
    )


def _version(**changes: object) -> PacketVersion:
    kwargs: dict[str, object] = {
        "packet_version_id": "packet-version-1",
        "packet_definition_id": "packet-1",
        "version_label": "v1",
        "revision_sequence": 1,
        "components": (_component(),),
        "rendering_rules": PacketRenderingRules(),
        "created_provenance": _provenance(),
        "status": "active",
    }
    kwargs.update(changes)
    return PacketVersion(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize("status", ("draft", "active", "retired"))
def test_packet_definition_accepts_reusable_lifecycle(status: str) -> None:
    definition = PacketDefinition(
        packet_definition_id="packet-1",
        name="Seminar Packet",
        purpose="Collect seminar collaboration evidence.",
        status=status,
        created_provenance=_provenance(),
        description="Reusable packet definition.",
    )
    assert definition.status == status


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("packet_definition_id", "../bad"),
        ("name", " "),
        ("purpose", "  padded"),
        ("status", "distributed"),
    ),
)
def test_packet_definition_rejects_invalid_fields(
    field_name: str,
    value: object,
) -> None:
    kwargs: dict[str, object] = {
        "packet_definition_id": "packet-1",
        "name": "Name",
        "purpose": "Purpose",
        "status": "draft",
        "created_provenance": _provenance(),
    }
    kwargs[field_name] = value
    with pytest.raises(ConcordModelError):
        PacketDefinition(**kwargs)  # type: ignore[arg-type]


def test_packet_models_contain_no_instance_or_signal_fields() -> None:
    forbidden = {
        "class_id",
        "class_reference",
        "activity_id",
        "session_id",
        "group_id",
        "group_plan_id",
        "membership_id",
        "student_id",
        "participant_id",
        "participant_reference",
        "role_assignment_id",
        "source_signal_set_id",
        "source_signal_set_digest",
        "source_signal_dimension_id",
        "band",
        "packet_instance_id",
        "artifact_instance_id",
        "artifact_page_id",
        "route_id",
        "scan_reference_id",
        "score_record_id",
        "publication_id",
    }
    for model in (
        PacketDefinition,
        PacketVersion,
        PacketComponent,
        PacketAudienceIntent,
        PacketCondition,
        PacketRenderingRules,
    ):
        assert forbidden.isdisjoint(field.name for field in fields(model))


def test_packet_version_canonicalizes_component_order() -> None:
    component_2 = _component(
        component_id="component-2",
        sequence=2,
    )
    version = _version(components=(component_2, _component()))
    assert tuple(item.sequence for item in version.components) == (1, 2)


def test_packet_version_requires_unique_contiguous_components() -> None:
    with pytest.raises(ConcordModelError, match="packet_component_id"):
        _version(
            components=(
                _component(),
                _component(sequence=2),
            )
        )
    with pytest.raises(ConcordModelError, match="contiguous"):
        _version(
            components=(
                _component(),
                _component(
                    component_id="component-3",
                    sequence=3,
                ),
            )
        )


def test_packet_version_requires_at_least_one_component() -> None:
    with pytest.raises(ConcordModelError, match="must not be empty"):
        _version(components=())


def test_first_version_and_successor_lineage_rules() -> None:
    with pytest.raises(ConcordModelError, match="first Packet Version"):
        _version(supersedes_packet_version_id="packet-version-0")
    successor = _version(
        packet_version_id="packet-version-2",
        revision_sequence=2,
        supersedes_packet_version_id="packet-version-1",
        status="draft",
    )
    assert successor.supersedes_packet_version_id == "packet-version-1"
    with pytest.raises(ConcordModelError, match="successor Packet Versions"):
        _version(
            packet_version_id="packet-version-2",
            revision_sequence=2,
        )
    with pytest.raises(ConcordModelError, match="cannot supersede itself"):
        _version(
            packet_version_id="packet-version-2",
            revision_sequence=2,
            supersedes_packet_version_id="packet-version-2",
        )


def test_packet_component_requires_exact_template_pair() -> None:
    with pytest.raises(ConcordModelError, match="template_id"):
        replace(_component(), template_id=None)
    with pytest.raises(ConcordModelError, match="template_version_id"):
        replace(_component(), template_version_id=None)
    with pytest.raises(ConcordModelError, match="external_reference"):
        replace(
            _component(),
            external_reference=ModuleRecordRef(
                module_id="quillan",
                record_kind="submission",
                record_id="submission-1",
            ),
        )


def test_external_component_uses_source_owned_module_record_ref() -> None:
    component = PacketComponent(
        packet_component_id="component-external",
        sequence=1,
        component_kind="external_component",
        copies_per_target=1,
        audience_intent=_audience("participant"),
        requirement_level="recommended",
        external_reference=ModuleRecordRef(
            module_id="quillan",
            record_kind="submission",
            record_id="submission-1",
            contract_version="1",
        ),
    )
    assert component.external_reference is not None
    assert component.external_reference.module_id == "quillan"
    with pytest.raises(ConcordModelError, match="Template identities"):
        replace(
            component,
            template_id="template-1",
            template_version_id="template-version-1",
        )
    with pytest.raises(ConcordModelError, match="requires external_reference"):
        replace(component, external_reference=None)
    with pytest.raises(ConcordModelError, match="outside Concord"):
        replace(
            component,
            external_reference=ModuleRecordRef(
                module_id="concord",
                record_kind="artifact_instance",
                record_id="artifact-1",
            ),
        )


@pytest.mark.parametrize("copies", (0, -1, True))
def test_copy_count_must_be_positive(copies: object) -> None:
    with pytest.raises(ConcordModelError, match="positive integer"):
        _component(copies=copies)  # type: ignore[arg-type]


def test_audience_intent_is_identity_free_and_role_keys_are_bounded() -> None:
    role = _audience("role", role_keys=("observer", "recorder"))
    assert role.role_keys == ("observer", "recorder")
    assert set(role.role_keys).issubset(ROLE_KEYS)

    extension = _audience(
        "role",
        role_keys=("school:discussion_leader",),
    )
    assert extension.role_keys == ("school:discussion_leader",)

    with pytest.raises(ConcordModelError, match="at least one role_key"):
        _audience("role")
    with pytest.raises(ConcordModelError, match="only for role"):
        _audience("group", role_keys=("observer",))
    with pytest.raises(ConcordModelError):
        _audience("role", role_keys=("not valid",))


def test_conditions_are_bounded_and_requirement_level_is_explicit() -> None:
    choice = PacketCondition(condition_kind="teacher_choice")
    conditional = _component(
        requirement_level="conditional",
        condition=choice,
    )
    assert conditional.condition == choice

    with pytest.raises(ConcordModelError, match="explicit condition"):
        _component(requirement_level="conditional")
    with pytest.raises(ConcordModelError, match="non-conditional"):
        _component(condition=choice)
    with pytest.raises(ConcordModelError, match="at least one role_key"):
        PacketCondition(condition_kind="matching_role_present")
    with pytest.raises(ConcordModelError, match="only for matching_role_present"):
        PacketCondition(
            condition_kind="teacher_choice",
            role_keys=("observer",),
        )
    with pytest.raises(ConcordModelError):
        PacketCondition(condition_kind="python_expression")


def test_packet_rendering_rules_are_small_and_deterministic() -> None:
    rules = PacketRenderingRules(
        start_each_component_on_new_page=True,
    )
    assert rules.preserve_component_order is True
    assert rules.copy_collation == "component_major"
    assert rules.target_order == "stable_identity"

    with pytest.raises(ConcordModelError, match="preserve"):
        PacketRenderingRules(preserve_component_order=False)
    with pytest.raises(ConcordModelError):
        PacketRenderingRules(copy_collation="random")
    with pytest.raises(ConcordModelError):
        PacketRenderingRules(target_order="display_name")


def test_packet_contract_models_are_frozen() -> None:
    definition = PacketDefinition(
        packet_definition_id="packet-1",
        name="Name",
        purpose="Purpose",
        status="draft",
        created_provenance=_provenance(),
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        definition.name = "Changed"  # type: ignore[misc]


def test_packet_contract_is_not_activity_native_persistence() -> None:
    registered_types = {descriptor.model_type for descriptor in RECORD_DESCRIPTORS}
    assert PacketDefinition not in registered_types
    assert PacketVersion not in registered_types
    assert PacketComponent not in registered_types
    with pytest.raises(ConcordModelError, match="registered Concord record"):
        record_to_dict(  # type: ignore[arg-type]
            PacketDefinition(
                packet_definition_id="packet-1",
                name="Name",
                purpose="Purpose",
                status="draft",
                created_provenance=_provenance(),
            )
        )


def test_existing_artifact_packet_reference_remains_opaque() -> None:
    artifact = ArtifactInstance(
        artifact_instance_id="artifact-1",
        template_version_id="legacy-template-version",
        packet_instance_id="legacy-packet-instance",
        activity_id="activity-1",
        artifact_category="discussion_record",
        generation_status="planned",
        expected_return_status="returned_expected",
        artifact_status="planned",
        privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
        page_ids=("page-1",),
        created_provenance=_provenance(),
    )
    assert artifact.packet_instance_id == "legacy-packet-instance"


def test_packet_contracts_are_public_model_exports() -> None:
    from concord import models

    required = (
        "PacketAudienceIntent",
        "PacketComponent",
        "PacketCondition",
        "PacketDefinition",
        "PacketRenderingRules",
        "PacketVersion",
    )
    for name in required:
        assert hasattr(models, name), name
        assert name in models.__all__
