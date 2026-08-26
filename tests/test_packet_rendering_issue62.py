from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pypdfium2 as pdfium
import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.classes import write_class_roster
from pds_core.rosters import create_roster
from pds_core.routing_models import ModuleWorkRef
from pds_core.workspace import ensure_workspace_root
from PIL import Image, ImageDraw

from concord.models import (
    EffectiveContext,
    PacketAudienceIntent,
    PacketComponent,
    PacketDefinition,
    PacketRenderingRules,
    PacketVersion,
)
from concord.packet_storage import create_packet_library
from concord.routing.starter_layout_pdf import (
    StarterPageRenderContext,
    _draw_concept_map,
    _venn_circle_bounds,
    render_starter_layout_pdf,
)
from concord.starter_templates.catalog import list_starter_templates
from concord.starter_templates.layout import (
    STARTER_DIAGRAM_KINDS,
    STARTER_SECTION_KINDS,
)
from concord.storage import load_current_record_graph
from concord.workflows import (
    CreateActivityContextRequest,
    CreateGroupWithMembersRequest,
    GroupMemberSpec,
    PreparePacketInstantiationRequest,
    PrepareStarterTemplateInstallRequest,
    RenderPacketInstanceRequest,
    WorkflowActor,
    commit_packet_instantiation,
    commit_starter_template_install,
    create_activity_context,
    create_group_with_members,
    prepare_packet_instantiation,
    prepare_starter_template_install,
    render_packet_instance,
)
from concord.workflows.context import provenance


def _clock() -> datetime:
    return datetime(2026, 8, 25, 20, 0, tzinfo=timezone.utc)


def _actor() -> WorkflowActor:
    return WorkflowActor(
        actor_id="teacher-1",
        display_label="Synthetic Teacher",
        role_label="teacher",
    )


def _context() -> EffectiveContext:
    return EffectiveContext(
        activity_id="activity-1",
        session_ids=("session-1",),
    )


def _workspace(tmp_path: Path) -> Path:
    root = ensure_workspace_root(tmp_path / "workspace")
    write_class_metadata_for_class(
        root,
        create_class_metadata("class-1", "2026-2027", created_at=_clock()),
    )
    write_class_roster(
        root,
        create_roster(
            "class-1",
            (
                {
                    "student_id": "student-1",
                    "last_name": "One",
                    "first_name": "Alex",
                    "period": "1",
                },
            ),
        ),
    )
    activity = create_activity_context(
        CreateActivityContextRequest(
            class_id="class-1",
            activity_id="activity-1",
            title="Synthetic Packet Rendering",
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
    create_group_with_members(
        CreateGroupWithMembersRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_id="group-a",
            label="Group A",
            expected_snapshot_revision=activity.commit.snapshot_revision,
            actor=_actor(),
            status="active",
            effective_context=_context(),
            members=(
                GroupMemberSpec(
                    membership_id="membership-1",
                    student_id="student-1",
                    effective_context=_context(),
                ),
            ),
        ),
        workspace_root=root,
        clock=_clock,
    )
    return root


def _landscape_group_starter():
    for entry in list_starter_templates():
        if (
            entry.orientation == "landscape"
            and "group" in entry.suggested_audience_kinds
            and (
                not entry.suggested_activity_type_keys
                or "project" in entry.suggested_activity_type_keys
            )
        ):
            return entry
    raise AssertionError("no compatible landscape group starter")


def _installed_packet(root: Path):
    entry = _landscape_group_starter()
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
        name="Synthetic Rendering Packet",
        purpose="Exercise #62 real starter PDF rendering.",
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
                packet_component_id="component-1",
                sequence=1,
                component_kind="concord_template",
                template_id=installed.template_id,
                template_version_id=installed.template_version_id,
                copies_per_target=2,
                audience_intent=PacketAudienceIntent(audience_kind="group"),
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
    prepared = prepare_packet_instantiation(
        PreparePacketInstantiationRequest(
            class_id="class-1",
            activity_id="activity-1",
            session_id="session-1",
            packet_definition_id=definition.packet_definition_id,
            packet_version_id=version.packet_version_id,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=_clock,
    )
    committed = commit_packet_instantiation(
        prepared,
        workspace_root=root,
        clock=_clock,
    )
    return entry, committed


def _pdf_dimensions(path: Path) -> list[tuple[float, float]]:
    document = pdfium.PdfDocument(path)
    try:
        return [
            tuple(document[index].get_size())
            for index in range(len(document))
        ]
    finally:
        document.close()


def test_all_30_starter_layouts_render_without_clipping_contract_failures() -> None:
    section_kinds: set[str] = set()
    diagram_kinds: set[str] = set()
    for entry in list_starter_templates():
        layout = entry.layout()
        contexts = []
        for page in layout.pages:
            section_kinds.update(item.kind for item in page.sections)
            diagram_kinds.update(
                item.diagram_kind
                for item in page.sections
                if item.diagram_kind is not None
            )
            values = {
                "activity_title": (
                    "Visual Review - Socratic Seminar Preparation and Evidence Notes"
                ),
                "session_label": "Session One",
                "group_label": "Group A",
                "participant_display_label": "Alex One",
                "current_date": "2026-08-25",
                "teacher_prompt": (
                    "Use specific evidence and record concise collaborative thinking."
                ),
                "pds2_route_payload": (
                    "PDS2:concord:synthetic-class:synthetic-work:route-preview"
                ),
                "human_fallback": "Concord synthetic preview page",
            }
            contexts.append(
                StarterPageRenderContext(
                    page_key=page.page_key,
                    values=tuple(sorted(values.items())),
                )
            )
        data = render_starter_layout_pdf(
            layout,
            tuple(contexts),
            created_at=_clock().isoformat(),
        )
        assert data.startswith(b"%PDF")
        document = pdfium.PdfDocument(data)
        try:
            assert len(document) == entry.page_count
            for page_index, layout_page in enumerate(layout.pages):
                width, height = document[page_index].get_size()
                if layout_page.orientation == "portrait":
                    assert height > width
                else:
                    assert width > height
        finally:
            document.close()

    assert section_kinds == STARTER_SECTION_KINDS
    assert diagram_kinds == STARTER_DIAGRAM_KINDS


def test_venn_overlap_is_wide_enough_for_shared_writing() -> None:
    first, second = _venn_circle_bounds(120, 1080, 120, 780)
    radius = (first[2] - first[0]) // 2
    overlap_width = min(first[2], second[2]) - max(first[0], second[0])
    assert overlap_width >= int(radius * 0.75)


def test_concept_map_connectors_do_not_cross_shape_interiors() -> None:
    image = Image.new("RGB", (1200, 900), "white")
    draw = ImageDraw.Draw(image)
    left = 120
    right = 1080
    top = 120
    bottom = 780
    _draw_concept_map(draw, left, right, top, bottom)

    center_x = left + (right - left) // 2
    center_y = top + (bottom - top) // 2
    assert image.getpixel((center_x, center_y)) == (255, 255, 255)

    box_w = max(120, (right - left) // 5)
    box_h = max(50, (bottom - top) // 6)
    box_centers = (
        (left + 10 + box_w // 2, top + 10 + box_h // 2),
        (right - 10 - box_w // 2, top + 10 + box_h // 2),
        (left + 10 + box_w // 2, bottom - 10 - box_h // 2),
        (right - 10 - box_w // 2, bottom - 10 - box_h // 2),
    )
    for point in box_centers:
        assert image.getpixel(point) == (255, 255, 255)


def test_packet_rendering_preserves_component_copy_page_order_and_lifecycle(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    entry, committed = _installed_packet(root)
    packet_id = committed.packet_instance_ids[0]

    rendered = render_packet_instance(
        RenderPacketInstanceRequest(
            class_id="class-1",
            activity_id="activity-1",
            packet_instance_id=packet_id,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    assert rendered.output_installed
    assert rendered.output_path.is_file()
    assert rendered.output_path.read_bytes().startswith(b"%PDF")
    assert rendered.page_count == entry.page_count * 2
    assert rendered.route_count == rendered.page_count
    assert len(rendered.output_sha256) == 64
    dimensions = _pdf_dimensions(rendered.output_path)
    assert all(width > height for width, height in dimensions)

    work = ModuleWorkRef("concord", "class-1", "activity-1")
    graph = load_current_record_graph(root, work).graph
    packet = next(
        item for item in graph.packet_instances
        if item.packet_instance_id == packet_id
    )
    assert packet.generation_status == "generated"
    assert packet.output_relative_path == f"rendered/packets/{packet_id}.pdf"
    assert packet.output_sha256 == rendered.output_sha256

    bound_ids = [
        binding.artifact_instance_id
        for binding in packet.artifact_bindings
    ]
    artifacts = [
        item for artifact_id in bound_ids
        for item in graph.artifact_instances
        if item.artifact_instance_id == artifact_id
    ]
    assert [item.artifact_instance_id for item in artifacts] == bound_ids
    assert all(item.generation_status == "completed" for item in artifacts)
    assert all(item.artifact_status == "generated" for item in artifacts)
    page_ids = {
        page_id for artifact in artifacts for page_id in artifact.page_ids
    }
    pages = [
        item for item in graph.artifact_pages if item.artifact_page_id in page_ids
    ]
    assert all(item.page_status == "generated" for item in pages)


def test_completed_packet_reprint_reuses_exact_pdf_and_routes(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    _, committed = _installed_packet(root)
    packet_id = committed.packet_instance_ids[0]
    first = render_packet_instance(
        RenderPacketInstanceRequest(
            class_id="class-1",
            activity_id="activity-1",
            packet_instance_id=packet_id,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    before_bytes = first.output_path.read_bytes()
    before_graph = load_current_record_graph(
        root,
        ModuleWorkRef("concord", "class-1", "activity-1"),
    )
    before_routes = first.payloads

    replay = render_packet_instance(
        RenderPacketInstanceRequest(
            class_id="class-1",
            activity_id="activity-1",
            packet_instance_id=packet_id,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    after_graph = load_current_record_graph(
        root,
        ModuleWorkRef("concord", "class-1", "activity-1"),
    )
    assert replay.replayed
    assert not replay.output_installed
    assert replay.output_sha256 == first.output_sha256
    assert replay.payloads == before_routes
    assert replay.output_path.read_bytes() == before_bytes
    assert replay.commit.no_op
    assert after_graph.snapshot_revision == before_graph.snapshot_revision
    assert after_graph.snapshot_sha256 == before_graph.snapshot_sha256


def test_packet_output_conflict_does_not_overwrite_existing_bytes(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    _, committed = _installed_packet(root)
    packet_id = committed.packet_instance_ids[0]
    work_root = (
        root
        / "classes"
        / "class-1"
        / "modules"
        / "concord"
        / "work"
        / "activity-1"
    )
    target = work_root / "rendered" / "packets" / f"{packet_id}.pdf"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"contradictory existing output")

    with pytest.raises(Exception, match="different Packet render already exists"):
        render_packet_instance(
            RenderPacketInstanceRequest(
                class_id="class-1",
                activity_id="activity-1",
                packet_instance_id=packet_id,
                actor=_actor(),
            ),
            workspace_root=root,
        )
    assert target.read_bytes() == b"contradictory existing output"

def test_packet_generated_surfaces_remain_planning_signal_free(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from argparse import Namespace

    from pds_core.pds2 import parse_pds2_payload
    from pds_core.route_registrations import load_route_registration

    from concord.cli_app.handlers import packet_runtime
    from concord.model_conversion import record_to_dict

    root = _workspace(tmp_path)
    _, committed = _installed_packet(root)
    packet_id = committed.packet_instance_ids[0]
    rendered = render_packet_instance(
        RenderPacketInstanceRequest(
            class_id="class-1",
            activity_id="activity-1",
            packet_instance_id=packet_id,
            actor=_actor(),
        ),
        workspace_root=root,
    )

    work = ModuleWorkRef("concord", "class-1", "activity-1")
    graph = load_current_record_graph(root, work).graph
    packet = next(
        item
        for item in graph.packet_instances
        if item.packet_instance_id == packet_id
    )
    forbidden = (
        "group_plan_id",
        "signal_set_id",
        "source_signal_set_id",
        "source_signal_set_digest",
        "dimension_id",
        "missing_signal_disposition",
        "proficiency",
    )
    native_text = str(record_to_dict(packet)).casefold()
    for value in forbidden:
        assert value not in native_text

    for payload in rendered.payloads:
        lowered = payload.casefold()
        for value in forbidden:
            assert value not in lowered
        registration = load_route_registration(root, parse_pds2_payload(payload))
        assert set(registration.module_details) == {
            "activity_id",
            "artifact_instance_id",
            "artifact_page_id",
            "page_number",
        }
        route_text = str(registration.module_details).casefold()
        for value in forbidden:
            assert value not in route_text

    packet_runtime.handle_instance_show(
        Namespace(
            class_id="class-1",
            activity_id="activity-1",
            packet_instance_id=packet_id,
            workspace_root=str(root),
        )
    )
    cli_text = capsys.readouterr().out.casefold()
    for value in forbidden:
        assert value not in cli_text

