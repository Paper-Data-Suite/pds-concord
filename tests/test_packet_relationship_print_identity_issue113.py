from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

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
    EffectiveContext,
    PacketAudienceIntent,
    PacketComponent,
    PacketDefinition,
    PacketRenderingRules,
    PacketVersion,
    SubjectReference,
)
from concord.packet_storage import create_packet_library
from concord.storage import load_current_record_graph
from concord.workflows import (
    CreateActivityContextRequest,
    CreateGroupWithMembersRequest,
    GroupMemberSpec,
    GroupRoleSpec,
    PacketSubjectBinding,
    PreparedPacketInstantiation,
    PreparePacketInstantiationRequest,
    PrepareStarterTemplateInstallRequest,
    RenderPacketInstanceRequest,
    WorkflowActor,
    commit_packet_instantiation,
    commit_starter_template_install,
    core_student_participant,
    create_activity_context,
    create_group_with_members,
    prepare_packet_instantiation,
    prepare_starter_template_install,
    render_packet_instance,
)
from concord.workflows.context import provenance


def _clock() -> datetime:
    return datetime(2026, 9, 19, 20, 30, tzinfo=timezone.utc)


def _actor() -> WorkflowActor:
    return WorkflowActor(
        actor_id="teacher-1",
        display_label="Synthetic Teacher",
        role_label="teacher",
    )


def _roster(
    *,
    reviewer_first: str = "Alex",
    reviewee_first: str = "Blair",
):
    return create_roster(
        "english12-p2",
        (
            {
                "student_id": "student-1",
                "last_name": "One",
                "first_name": reviewer_first,
                "period": "2",
            },
            {
                "student_id": "student-2",
                "last_name": "Two",
                "first_name": reviewee_first,
                "period": "2",
            },
        ),
    )


def _context() -> EffectiveContext:
    return EffectiveContext(
        activity_id="activity-1",
        session_ids=("session-1",),
    )


def _workspace(
    tmp_path: Path,
    *,
    activity_type: str = "socratic_seminar",
) -> Path:
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
    created = create_activity_context(
        CreateActivityContextRequest(
            class_id="english12-p2",
            activity_id="activity-1",
            title="Relationship Review",
            activity_type=activity_type,
            scoring_orientation="evidence_only",
            session_id="session-1",
            actor=_actor(),
            activity_status="active",
            session_status="active",
            session_label="Seminar Session 1",
        ),
        workspace_root=root,
        clock=_clock,
    )
    first = create_group_with_members(
        CreateGroupWithMembersRequest(
            class_id="english12-p2",
            activity_id="activity-1",
            group_id="group-a",
            label="Group A",
            expected_snapshot_revision=created.commit.snapshot_revision,
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
            roles=(
                GroupRoleSpec(
                    role_assignment_id="role-observer",
                    participant_reference=core_student_participant(
                        root,
                        "english12-p2",
                        "student-1",
                    ),
                    role_key="observer",
                    effective_context=_context(),
                    membership_id="membership-1",
                ),
            ),
        ),
        workspace_root=root,
        clock=_clock,
    )
    create_group_with_members(
        CreateGroupWithMembersRequest(
            class_id="english12-p2",
            activity_id="activity-1",
            group_id="group-b",
            label="Group B",
            expected_snapshot_revision=first.commit.snapshot_revision,
            actor=_actor(),
            status="active",
            effective_context=_context(),
            members=(
                GroupMemberSpec(
                    membership_id="membership-2",
                    student_id="student-2",
                    effective_context=_context(),
                ),
            ),
        ),
        workspace_root=root,
        clock=_clock,
    )
    return root


def _install_packet(root: Path, starter_key: str) -> None:
    installed = commit_starter_template_install(
        prepare_starter_template_install(
            PrepareStarterTemplateInstallRequest(
                starter_key=starter_key,
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
        name="Relationship Physical Output",
        purpose="Exercise issue #113 role-aware physical output.",
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
                packet_component_id="component-review",
                sequence=1,
                component_kind="concord_template",
                template_id=installed.template_id,
                template_version_id=installed.template_version_id,
                copies_per_target=1,
                audience_intent=PacketAudienceIntent(
                    audience_kind="role",
                    role_keys=("observer",),
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


def _student_subject() -> SubjectReference:
    return SubjectReference(
        subject_kind="core_student",
        subject_id="student-2",
        owning_system="core",
    )


def _group_subject() -> SubjectReference:
    return SubjectReference(
        subject_kind="concord_group",
        subject_id="group-b",
        owning_system="concord",
    )


def _request(
    subject: SubjectReference | None = None,
) -> PreparePacketInstantiationRequest:
    bindings = ()
    if subject is not None:
        bindings = (
            PacketSubjectBinding(
                packet_component_id="component-review",
                target_key="role:role-observer",
                subject_reference=subject,
            ),
        )
    return PreparePacketInstantiationRequest(
        class_id="english12-p2",
        activity_id="activity-1",
        session_id="session-1",
        packet_definition_id="packet-1",
        packet_version_id="packet-version-1",
        actor=_actor(),
        subject_bindings=bindings,
    )


def _input_values(
    prepared: PreparedPacketInstantiation,
) -> dict[str, object]:
    assert len(prepared.target_plans) == 1
    artifact = prepared.target_plans[0].artifacts[0]
    return {
        item.input_key: item.value
        for item in artifact.rendering_inputs
        if item.status == "resolved"
    }


def test_peer_review_freezes_role_headers_and_minimized_fallback(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    _install_packet(root, "peer_review_writing")
    prepared = prepare_packet_instantiation(
        _request(_student_subject()),
        workspace_root=root,
        clock=_clock,
    )

    assert prepared.ready_for_commit
    artifact_plan = prepared.target_plans[0].artifacts[0]
    assert artifact_plan.subject_print_label == "Blair T."
    values = _input_values(prepared)
    assert values["reviewer_display_label"] == "Alex One"
    assert values["reviewee_display_label"] == "Blair Two"
    assert "participant_display_label" not in values

    committed = commit_packet_instantiation(
        prepared,
        workspace_root=root,
        clock=_clock,
    )
    work = ModuleWorkRef("concord", "english12-p2", "activity-1")
    graph = load_current_record_graph(root, work).graph
    packet = graph.packet_instances[0]
    binding = packet.artifact_bindings[0]
    frozen = {item.input_key: item.value for item in binding.rendering_values}
    assert frozen["reviewer_display_label"] == "Alex One"
    assert frozen["reviewee_display_label"] == "Blair Two"

    for page in graph.artifact_pages:
        fallback = page.human_fallback
        assert fallback is not None
        assert "Reviewer: Alex O." in fallback
        assert "Reviewee: Blair T." in fallback
        assert "Student:" not in fallback
        assert "student-1" not in fallback
        assert "student-2" not in fallback

        committed_page = next(
            item
            for item in committed.pages
            if item.artifact_page_id == page.artifact_page_id
        )
        assert committed_page.pds2_payload is not None
        registration = load_route_registration(
            root,
            parse_pds2_payload(committed_page.pds2_payload),
        )
        assert registration.human_fallback == fallback
        assert set(registration.module_details) == {
            "activity_id",
            "artifact_instance_id",
            "artifact_page_id",
            "page_number",
        }

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

    write_class_roster(
        root,
        _roster(
            reviewer_first="Alicia",
            reviewee_first="Bianca",
        ),
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
    assert replay.replayed
    assert replay.output_sha256 == first_digest
    assert replay.payloads == first_payloads
    assert replay.output_path.read_bytes() == first_bytes


def test_observer_output_names_observer_and_selected_session(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    _install_packet(root, "fishbowl_observer")
    prepared = prepare_packet_instantiation(
        _request(),
        workspace_root=root,
        clock=_clock,
    )

    assert prepared.ready_for_commit
    artifact_plan = prepared.target_plans[0].artifacts[0]
    assert artifact_plan.subject_print_label == "Seminar Session 1"
    values = _input_values(prepared)
    assert values["observer_display_label"] == "Alex One"
    assert values["observed_display_label"] == "Seminar Session 1"
    assert "participant_display_label" not in values

    commit_packet_instantiation(
        prepared,
        workspace_root=root,
        clock=_clock,
    )
    graph = load_current_record_graph(
        root,
        ModuleWorkRef("concord", "english12-p2", "activity-1"),
    ).graph
    for page in graph.artifact_pages:
        fallback = page.human_fallback
        assert fallback is not None
        assert "Observer: Alex O." in fallback
        assert "Observed: Seminar Session 1" in fallback
        assert "Student:" not in fallback


def test_group_review_output_uses_reviewed_group_without_member_enumeration(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path, activity_type="project")
    _install_packet(root, "peer_review_presentation")
    prepared = prepare_packet_instantiation(
        _request(_group_subject()),
        workspace_root=root,
        clock=_clock,
    )

    assert prepared.ready_for_commit
    artifact_plan = prepared.target_plans[0].artifacts[0]
    assert artifact_plan.subject_print_label == "Group B"
    values = _input_values(prepared)
    assert values["reviewer_display_label"] == "Alex One"
    assert values["reviewed_display_label"] == "Group B"

    commit_packet_instantiation(
        prepared,
        workspace_root=root,
        clock=_clock,
    )
    graph = load_current_record_graph(
        root,
        ModuleWorkRef("concord", "english12-p2", "activity-1"),
    ).graph
    for page in graph.artifact_pages:
        fallback = page.human_fallback
        assert fallback is not None
        assert "Reviewer: Alex O." in fallback
        assert "Reviewed: Group B" in fallback
        assert "Blair" not in fallback
        assert "student-2" not in fallback
