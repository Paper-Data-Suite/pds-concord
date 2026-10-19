"""#136 Slice 7B: real two-page group Packet + native PDS2 after saved reuse.

Only synthetic Core students and an isolated pytest workspace are used.
"""

from __future__ import annotations

import hashlib
from datetime import date, datetime, timezone
from pathlib import Path

import pypdfium2 as pdfium
from pds_core.pds2 import parse_pds2_payload
from pds_core.route_registrations import (
    load_route_registration,
    resolve_route_registration,
)
from pds_core.scan_retention import RetainedSourceScan
from pds_core.standards import write_workspace_standards_library
from test_issue136_slice6a_classroom_acceptance import (
    ACTOR,
    CLASS,
    SOURCE,
    TARGET,
    _saved_source,
    _setup,
    _work,
)
from test_issue136_slice6b_scoring_publication_acceptance import _approved_applied

from concord.class_group_arrangement_storage import load_current_arrangement
from concord.models import (
    PacketAudienceIntent,
    PacketComponent,
    PacketDefinition,
    PacketRenderingRules,
    PacketVersion,
)
from concord.packet_storage import create_packet_library
from concord.starter_templates.catalog import get_starter_template
from concord.storage import load_current_record_graph
from concord.workflows import (
    PreparePacketInstantiationRequest,
    PrepareStarterTemplateInstallRequest,
    RenderPacketInstanceRequest,
    commit_packet_instantiation,
    commit_starter_template_install,
    prepare_packet_instantiation,
    prepare_starter_template_install,
    render_packet_instance,
    show_activity,
)
from concord.workflows.artifact_page import handle_concord_route
from concord.workflows.context import provenance


def _clock() -> datetime:
    return datetime(2026, 10, 18, 19, 0, tzinfo=timezone.utc)


def test_six_reused_groups_two_page_packet_render_pds2_return_and_replay(
    tmp_path: Path,
) -> None:
    root, standards, source_revision, target_revision = _setup(tmp_path, "mixed")
    # Packet services deliberately reload the canonical workspace Standards Library.
    write_workspace_standards_library(root, standards)
    _saved_source(root, standards, source_revision)
    source_before = show_activity(CLASS, SOURCE, workspace_root=root).summary
    saved_before = load_current_arrangement(
        root,
        class_id=CLASS,
        school_year="2026-2027",
        arrangement_id="class-six-table-arrangement",
        actor_id=ACTOR.actor_id,
    )
    _, _ = _approved_applied(root, standards, target_revision)
    graph = load_current_record_graph(
        root, _work(TARGET), standards_library=standards
    ).graph
    assert len(graph.groups) == 6
    assert len(graph.memberships) == 29
    assert graph.score_records == ()

    starter = get_starter_template("structured_academic_controversy")
    assert starter.page_count == 2
    assert "group" in starter.suggested_audience_kinds
    prepared_starter = prepare_starter_template_install(
        PrepareStarterTemplateInstallRequest(
            starter_key=starter.starter_key, actor=ACTOR
        ),
        workspace_root=root,
        clock=_clock,
    )
    installed = commit_starter_template_install(prepared_starter, workspace_root=root)
    created = provenance(ACTOR, clock=_clock, source_kind="manual")
    definition = PacketDefinition(
        packet_definition_id="packet-six-tables-two-pages",
        name="Synthetic two-page table discussion",
        purpose="Verify saved six-group arrangements remain routable.",
        status="active",
        created_provenance=created,
    )
    version = PacketVersion(
        packet_version_id="packet-six-tables-two-pages-v1",
        packet_definition_id=definition.packet_definition_id,
        version_label="v1",
        revision_sequence=1,
        components=(
            PacketComponent(
                packet_component_id="group-worksheet-two-pages",
                sequence=1,
                component_kind="concord_template",
                template_id=installed.template_id,
                template_version_id=installed.template_version_id,
                copies_per_target=1,
                audience_intent=PacketAudienceIntent(audience_kind="group"),
                requirement_level="required",
            ),
        ),
        rendering_rules=PacketRenderingRules(),
        created_provenance=created,
        status="active",
    )
    create_packet_library(root, definition=definition, initial_version=version)
    request = PreparePacketInstantiationRequest(
        class_id=CLASS,
        activity_id=TARGET,
        session_id=f"{TARGET}-session",
        packet_definition_id=definition.packet_definition_id,
        packet_version_id=version.packet_version_id,
        actor=ACTOR,
    )
    before_preview = load_current_record_graph(
        root, _work(TARGET), standards_library=standards
    )
    prepared = prepare_packet_instantiation(request, workspace_root=root, clock=_clock)
    assert prepared.ready_for_commit
    assert prepared.packet_instance_count == 6
    assert prepared.artifact_count == 6
    assert prepared.page_count == 12
    assert prepared.route_count == 12
    after_preview = load_current_record_graph(
        root, _work(TARGET), standards_library=standards
    )
    assert after_preview.snapshot_revision == before_preview.snapshot_revision
    assert after_preview.snapshot_sha256 == before_preview.snapshot_sha256

    committed = commit_packet_instantiation(prepared, workspace_root=root, clock=_clock)
    assert not committed.replayed
    assert len(committed.packet_instance_ids) == 6
    assert len(committed.artifact_instance_ids) == 6
    assert len(committed.pages) == 12
    assert committed.routes_verified == committed.routes_expected == 12
    assert len(set(committed.route_ids)) == 12
    assert len(set(committed.artifact_page_ids)) == 12
    locators = []
    for page in committed.pages:
        assert page.pds2_payload is not None
        locator = parse_pds2_payload(page.pds2_payload)
        registration = load_route_registration(root, locator)
        assert locator.work == _work(TARGET)
        assert locator.class_id == CLASS
        assert registration.target.record_kind == "artifact_page"
        assert registration.target.record_id == page.artifact_page_id
        assert str(registration.module_details["page_number"]) == str(page.page_number)
        locators.append(locator)

    first_packet = committed.packet_instance_ids[0]
    rendered = render_packet_instance(
        RenderPacketInstanceRequest(
            class_id=CLASS,
            activity_id=TARGET,
            packet_instance_id=first_packet,
            actor=ACTOR,
        ),
        workspace_root=root,
    )
    assert rendered.output_installed
    assert rendered.page_count == 2
    assert rendered.route_count == 2
    content = rendered.output_path.read_bytes()
    assert content.startswith(b"%PDF")
    assert hashlib.sha256(content).hexdigest() == rendered.output_sha256
    pdf = pdfium.PdfDocument(content)
    try:
        assert len(pdf) == 2
    finally:
        pdf.close()

    before_replay = load_current_record_graph(
        root, _work(TARGET), standards_library=standards
    )
    replay = render_packet_instance(
        RenderPacketInstanceRequest(
            class_id=CLASS,
            activity_id=TARGET,
            packet_instance_id=first_packet,
            actor=ACTOR,
        ),
        workspace_root=root,
    )
    assert replay.replayed
    assert replay.commit.no_op
    assert replay.output_sha256 == rendered.output_sha256
    assert replay.output_path.read_bytes() == content
    after_replay = load_current_record_graph(
        root, _work(TARGET), standards_library=standards
    )
    assert after_replay.snapshot_revision == before_replay.snapshot_revision
    assert after_replay.snapshot_sha256 == before_replay.snapshot_sha256

    # Exercise actual Concord route dispatch on retained bytes; no score inference.
    retained_path = root / "scans" / "source" / "2026-10-18" / "synthetic.png"
    retained_path.parent.mkdir(parents=True, exist_ok=True)
    retained_path.write_bytes(b"synthetic retained scanned page")
    retained = RetainedSourceScan(
        source_scan_id="scan-six-table-page-1",
        source_filename="synthetic.png",
        source_sha256=hashlib.sha256(retained_path.read_bytes()).hexdigest(),
        retained_source_path=retained_path,
        retained_source_relative_path=retained_path.relative_to(root).as_posix(),
        intake_timestamp=_clock(),
        intake_date=date(2026, 10, 18),
    )
    resolution = resolve_route_registration(root, locators[0])
    routed = handle_concord_route(resolution, retained, 1)
    rerouted = handle_concord_route(resolution, retained, 1)
    assert not routed.replayed
    assert rerouted.replayed
    assert routed.scan_reference_id == rerouted.scan_reference_id
    after_scan = load_current_record_graph(
        root, _work(TARGET), standards_library=standards
    ).graph
    assert len(after_scan.scan_references) == 1
    assert (
        after_scan.scan_references[0].artifact_page_id
        == committed.pages[0].artifact_page_id
    )
    assert len(after_scan.groups) == 6
    assert len(after_scan.memberships) == 29
    assert after_scan.score_records == ()
    assert after_scan.score_evidence_links == ()
    assert show_activity(CLASS, SOURCE, workspace_root=root).summary == source_before
    assert (
        load_current_arrangement(
            root,
            class_id=CLASS,
            school_year="2026-2027",
            arrangement_id="class-six-table-arrangement",
            actor_id=ACTOR.actor_id,
        )
        == saved_before
    )
