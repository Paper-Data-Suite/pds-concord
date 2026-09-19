from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.classes import write_class_roster
from pds_core.pds2 import parse_pds2_payload
from pds_core.rosters import create_roster
from pds_core.route_registrations import load_route_registration
from pds_core.routing_models import ModuleWorkRef
from pds_core.workspace import ensure_workspace_root

from concord.models import (
    PacketAudienceIntent,
    PacketComponent,
    PacketDefinition,
    PacketRenderingRules,
    PacketVersion,
    ParticipantReference,
)
from concord.packet_storage import create_packet_library
from concord.starter_templates.catalog import get_starter_template
from concord.storage import load_current_record_graph
from concord.workflows import (
    ConcordWorkflowConflictError,
    CreateActivityContextRequest,
    PreparePacketInstantiationRequest,
    PrepareStarterTemplateInstallRequest,
    RenderPacketInstanceRequest,
    WorkflowActor,
    commit_packet_instantiation,
    commit_starter_template_install,
    create_activity_context,
    prepare_packet_instantiation,
    prepare_starter_template_install,
    render_packet_instance,
)
from concord.workflows.context import provenance
from concord.workflows.participants import participant_print_label


def _clock() -> datetime:
    return datetime(2026, 9, 18, 18, 30, tzinfo=timezone.utc)


def _actor() -> WorkflowActor:
    return WorkflowActor(
        actor_id="teacher-1",
        display_label="Synthetic Teacher",
        role_label="teacher",
    )


def _roster(first_name: str = "Alex", last_name: str = "One"):
    return create_roster(
        "english12-p2",
        (
            {
                "student_id": "student-1",
                "last_name": last_name,
                "first_name": first_name,
                "period": "2",
            },
        ),
    )


def _workspace(tmp_path: Path) -> Path:
    root = ensure_workspace_root(tmp_path / "workspace")
    write_class_metadata_for_class(
        root,
        create_class_metadata(
            "english12-p2",
            "2026-2027",
            created_at=_clock(),
        ),
    )
    write_class_roster(root, _roster())
    create_activity_context(
        CreateActivityContextRequest(
            class_id="english12-p2",
            activity_id="activity-1",
            title="Think Pair Share",
            activity_type="project",
            scoring_orientation="evidence_only",
            session_id="session-1",
            actor=_actor(),
            activity_status="active",
            session_status="active",
            session_label="Session One",
        ),
        workspace_root=root,
        clock=_clock,
    )
    return root


def _install_participant_packet(root: Path) -> None:
    entry = get_starter_template("think_pair_share")
    installed = commit_starter_template_install(
        prepare_starter_template_install(
            PrepareStarterTemplateInstallRequest(
                starter_key=entry.starter_key,
                actor=_actor(),
            ),
            workspace_root=root,
            clock=_clock,
        ),
        workspace_root=root,
    )
    created = provenance(_actor(), clock=_clock, source_kind="manual")
    definition = PacketDefinition(
        packet_definition_id="packet-1",
        name="Synthetic Participant Packet",
        purpose="Exercise issue #102 physical print identity.",
        status="active",
        created_provenance=created,
    )
    version = PacketVersion(
        packet_version_id="packet-version-1",
        packet_definition_id=definition.packet_definition_id,
        version_label="v1",
        revision_sequence=1,
        components=(
            PacketComponent(
                packet_component_id="component-participant",
                sequence=1,
                component_kind="concord_template",
                template_id=installed.template_id,
                template_version_id=installed.template_version_id,
                copies_per_target=1,
                audience_intent=PacketAudienceIntent(
                    audience_kind="participant"
                ),
                requirement_level="required",
            ),
        ),
        rendering_rules=PacketRenderingRules(),
        created_provenance=created,
        status="active",
    )
    create_packet_library(
        root,
        definition=definition,
        initial_version=version,
    )


def _prepare(root: Path):
    return prepare_packet_instantiation(
        PreparePacketInstantiationRequest(
            class_id="english12-p2",
            activity_id="activity-1",
            session_id="session-1",
            packet_definition_id="packet-1",
            packet_version_id="packet-version-1",
            actor=_actor(),
        ),
        workspace_root=root,
        clock=_clock,
    )


def test_participant_print_label_uses_structured_roster_fields() -> None:
    roster = create_roster(
        "english12-p2",
        (
            {
                "student_id": "student-1",
                "last_name": "de la Cruz",
                "first_name": "Jordan",
                "period": "2",
            },
        ),
    )
    participant = ParticipantReference(
        participant_kind="core_student",
        participant_id="student-1",
        owning_system="core",
    )

    assert participant_print_label(roster, participant) == "Jordan d."


def test_new_participant_packet_freezes_class_and_minimized_student_fallback(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    _install_participant_packet(root)
    prepared = _prepare(root)

    assert len(prepared.target_plans) == 1
    assert prepared.target_plans[0].participant_print_label == "Alex O."

    committed = commit_packet_instantiation(
        prepared,
        workspace_root=root,
        clock=_clock,
    )
    work = ModuleWorkRef("concord", "english12-p2", "activity-1")
    graph = load_current_record_graph(root, work).graph
    packet = graph.packet_instances[0]

    for page in graph.artifact_pages:
        if not page.route_required:
            continue
        fallback = page.human_fallback
        assert fallback is not None
        assert "Class: english12-p2" in fallback
        assert "Student: Alex O." in fallback
        assert "student-1" not in fallback
        assert "Alex One" not in fallback
        committed_page = next(
            item
            for item in committed.pages
            if item.artifact_page_id == page.artifact_page_id
        )
        assert committed_page.pds2_payload is not None
        locator = parse_pds2_payload(committed_page.pds2_payload)
        registration = load_route_registration(root, locator)
        assert registration.human_fallback == fallback
        assert set(registration.module_details) == {
            "activity_id",
            "artifact_instance_id",
            "artifact_page_id",
            "page_number",
        }
        assert locator.class_id == "english12-p2"

    rendered = render_packet_instance(
        RenderPacketInstanceRequest(
            class_id="english12-p2",
            activity_id="activity-1",
            packet_instance_id=packet.packet_instance_id,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    first_bytes = rendered.output_path.read_bytes()
    first_digest = rendered.output_sha256
    first_payloads = rendered.payloads
    before = load_current_record_graph(root, work)

    write_class_roster(
        root,
        _roster(first_name="Alicia"),
        overwrite=True,
    )

    replay = render_packet_instance(
        RenderPacketInstanceRequest(
            class_id="english12-p2",
            activity_id="activity-1",
            packet_instance_id=packet.packet_instance_id,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    after = load_current_record_graph(root, work)

    assert replay.replayed
    assert replay.output_sha256 == first_digest
    assert replay.payloads == first_payloads
    assert replay.output_path.read_bytes() == first_bytes
    assert replay.commit.no_op
    assert after.snapshot_revision == before.snapshot_revision
    assert after.snapshot_sha256 == before.snapshot_sha256


def test_roster_change_after_preview_rejects_stale_generation(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    _install_participant_packet(root)
    prepared = _prepare(root)

    write_class_roster(
        root,
        _roster(first_name="Alicia"),
        overwrite=True,
    )

    with pytest.raises(ConcordWorkflowConflictError, match="stale"):
        commit_packet_instantiation(
            prepared,
            workspace_root=root,
            clock=_clock,
        )
