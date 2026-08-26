from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace

import pytest
from pds_core.routing_models import ModuleRecordRef

from concord.model_conversion import record_from_dict, record_to_dict
from concord.model_validation import ConcordRecordGraph, collect_record_graph_issues
from concord.models import (
    Activity,
    ActorReference,
    ArtifactInstance,
    ArtifactPage,
    ConcordModelError,
    Group,
    PacketInstance,
    PacketInstanceArtifactBinding,
    PacketTargetContext,
    ParticipantReference,
    PrivacyPolicy,
    Provenance,
    Session,
)
from concord.record_registry import descriptor_for_record


def _provenance() -> Provenance:
    return Provenance(
        actor=ActorReference(
            actor_kind="authorized_adult",
            actor_id="teacher-1",
            owning_system="concord",
        ),
        timestamp="2026-08-25T17:30:00-04:00",
        source_kind="generated",
        application_version="0.3.0.dev0",
    )


def _participant() -> ParticipantReference:
    return ParticipantReference(
        participant_kind="core_student",
        participant_id="student-1",
        owning_system="core",
    )


def _binding(
    *,
    artifact_id: str = "artifact-1",
    component_id: str = "component-1",
    component_sequence: int = 1,
    copy_index: int = 1,
) -> PacketInstanceArtifactBinding:
    return PacketInstanceArtifactBinding(
        packet_component_id=component_id,
        component_sequence=component_sequence,
        copy_index=copy_index,
        template_id="template-1",
        template_version_id="template-version-1",
        artifact_instance_id=artifact_id,
    )


def _target(audience_kind: str = "group", **changes: object) -> PacketTargetContext:
    values: dict[str, object] = {
        "audience_kind": audience_kind,
        "activity_id": "activity-1",
        "session_id": "session-1",
        "group_id": "group-1" if audience_kind == "group" else None,
    }
    values.update(changes)
    return PacketTargetContext(**values)  # type: ignore[arg-type]


def _instance(**changes: object) -> PacketInstance:
    values: dict[str, object] = {
        "packet_instance_id": "packet-instance-1",
        "generation_id": "generation-1",
        "packet_definition_id": "packet-1",
        "packet_version_id": "packet-version-1",
        "activity_id": "activity-1",
        "session_id": "session-1",
        "target_context": _target(),
        "artifact_bindings": (_binding(),),
        "generation_status": "planned",
        "created_provenance": _provenance(),
    }
    values.update(changes)
    return PacketInstance(**values)  # type: ignore[arg-type]


def _graph(
    *,
    packet_instances: tuple[PacketInstance, ...] = (),
    artifacts: tuple[ArtifactInstance, ...] = (),
    pages: tuple[ArtifactPage, ...] = (),
    groups: tuple[Group, ...] = (),
) -> ConcordRecordGraph:
    activity = Activity(
        activity_id="activity-1",
        class_reference=ModuleRecordRef(
            module_id="core", record_kind="class", record_id="class-1"
        ),
        title="Synthetic Activity",
        activity_type="project",
        scoring_orientation="evidence_only",
        status="active",
        created_provenance=_provenance(),
    )
    session = Session(
        session_id="session-1",
        activity_id="activity-1",
        sequence=1,
        status="active",
        created_provenance=_provenance(),
    )
    return ConcordRecordGraph(
        activities=(activity,),
        sessions=(session,),
        groups=groups,
        packet_instances=packet_instances,
        artifact_instances=artifacts,
        artifact_pages=pages,
    )


def _artifact(
    *,
    packet_instance_id: str | None = "packet-instance-1",
    group_id: str | None = "group-1",
) -> tuple[ArtifactInstance, ArtifactPage]:
    page = ArtifactPage(
        artifact_page_id="artifact-1-page-1",
        artifact_instance_id="artifact-1",
        page_number=1,
        page_kind="primary",
        return_expected=True,
        route_required=True,
        page_status="planned",
        created_provenance=_provenance(),
        expected_page_count=1,
        route_id="route-artifact-1",
        human_fallback="Synthetic artifact page",
    )
    artifact = ArtifactInstance(
        artifact_instance_id="artifact-1",
        template_version_id="template-version-1",
        activity_id="activity-1",
        artifact_category="student_work",
        generation_status="planned",
        expected_return_status="returned_expected",
        artifact_status="planned",
        privacy_policy=PrivacyPolicy(classification="group_and_teacher"),
        page_ids=(page.artifact_page_id,),
        created_provenance=_provenance(),
        packet_instance_id=packet_instance_id,
        session_id="session-1",
        group_id=group_id,
    )
    return artifact, page


def test_packet_instance_is_frozen_registered_native_record() -> None:
    instance = _instance()
    descriptor = descriptor_for_record(instance)
    assert (descriptor.kind, descriptor.graph_collection) == (
        "packet_instance",
        "packet_instances",
    )
    with pytest.raises(FrozenInstanceError):
        instance.generation_status = "generated"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("kind", "changes"),
    (
        ("activity", {}),
        ("group", {"group_id": "group-1"}),
        ("participant", {"participant_reference": _participant()}),
        (
            "teacher",
            {
                "actor_reference": ActorReference(
                    actor_kind="authorized_adult",
                    actor_id="teacher-1",
                    owning_system="concord",
                )
            },
        ),
        (
            "role",
            {
                "participant_reference": _participant(),
                "role_assignment_id": "role-1",
                "role_key": "recorder",
            },
        ),
    ),
)
def test_packet_target_context_accepts_bounded_audiences(
    kind: str, changes: dict[str, object]
) -> None:
    assert _target(kind, **changes).audience_kind == kind


def test_packet_target_context_rejects_incomplete_context() -> None:
    with pytest.raises(ConcordModelError):
        _target("group", group_id=None)
    with pytest.raises(ConcordModelError):
        _target("participant")
    with pytest.raises(ConcordModelError):
        _target("role", participant_reference=_participant(), role_key="recorder")


def test_packet_binding_order_and_copy_indexes_are_canonical() -> None:
    instance = _instance(
        artifact_bindings=(
            _binding(artifact_id="artifact-2", copy_index=2),
            _binding(),
            _binding(
                artifact_id="artifact-3",
                component_id="component-2",
                component_sequence=2,
            ),
        )
    )
    assert tuple(
        (item.component_sequence, item.copy_index)
        for item in instance.artifact_bindings
    ) == ((1, 1), (1, 2), (2, 1))
    with pytest.raises(ConcordModelError, match="contiguous"):
        _instance(
            artifact_bindings=(
                _binding(),
                _binding(artifact_id="artifact-3", copy_index=3),
            )
        )


def test_generated_instance_requires_safe_verified_pdf() -> None:
    digest = "a" * 64
    generated = _instance(
        generation_status="generated",
        output_relative_path="rendered/packets/packet-instance-1.pdf",
        output_sha256=digest,
    )
    assert generated.output_sha256 == digest
    with pytest.raises(ConcordModelError):
        _instance(generation_status="generated")
    with pytest.raises(ConcordModelError):
        _instance(
            generation_status="generated",
            output_relative_path="../escape.pdf",
            output_sha256=digest,
        )


def test_native_serialization_round_trip_is_exact_and_signal_free() -> None:
    instance = _instance()
    body = record_to_dict(instance)
    assert record_from_dict("packet_instance", body) == instance
    serialized = str(body)
    assert "group_plan_id" not in serialized
    assert "signal_set" not in serialized


def test_runtime_contract_has_no_group_plan_or_signal_fields() -> None:
    forbidden = {
        "group_plan_id",
        "strategy",
        "seed",
        "signal_set_id",
        "source_signal_set_id",
        "source_signal_set_digest",
        "dimension_id",
        "band",
        "missing_signal_disposition",
    }
    for model in (PacketInstance, PacketTargetContext, PacketInstanceArtifactBinding):
        assert forbidden.isdisjoint(field.name for field in fields(model))


def test_graph_accepts_exact_packet_artifact_binding() -> None:
    group = Group(
        group_id="group-1",
        activity_id="activity-1",
        label="Group 1",
        status="active",
        created_provenance=_provenance(),
    )
    artifact, page = _artifact()
    issues = collect_record_graph_issues(
        _graph(
            packet_instances=(_instance(),),
            artifacts=(artifact,),
            pages=(page,),
            groups=(group,),
        )
    )
    assert not any(issue.code.startswith("packet_instance.") for issue in issues)


def test_graph_rejects_wrong_packet_artifact_backlink() -> None:
    group = Group(
        group_id="group-1",
        activity_id="activity-1",
        label="Group 1",
        status="active",
        created_provenance=_provenance(),
    )
    artifact, page = _artifact(packet_instance_id="other-packet")
    codes = {
        issue.code
        for issue in collect_record_graph_issues(
            _graph(
                packet_instances=(_instance(),),
                artifacts=(artifact,),
                pages=(page,),
                groups=(group,),
            )
        )
    }
    assert "packet_instance.artifact.packet_mismatch" in codes


def test_legacy_opaque_artifact_packet_reference_remains_valid() -> None:
    artifact, page = _artifact(
        packet_instance_id="legacy-opaque-packet",
        group_id=None,
    )
    issues = collect_record_graph_issues(_graph(artifacts=(artifact,), pages=(page,)))
    assert not any(
        issue.code.startswith("artifact.packet_instance.")
        or issue.code == "packet_instance.artifact.unbound"
        for issue in issues
    )


def test_generation_id_preserves_contract_and_unique_target() -> None:
    duplicate = replace(
        _instance(),
        packet_instance_id="packet-instance-2",
        artifact_bindings=(_binding(artifact_id="artifact-2"),),
    )
    changed = replace(
        duplicate,
        packet_instance_id="packet-instance-3",
        packet_version_id="packet-version-2",
        target_context=_target("activity"),
        artifact_bindings=(_binding(artifact_id="artifact-3"),),
    )
    codes = {
        issue.code
        for issue in collect_record_graph_issues(
            _graph(packet_instances=(_instance(), duplicate, changed))
        )
    }
    assert "packet_instance.generation.target_duplicate" in codes
    assert "packet_instance.generation.contract_mismatch" in codes
