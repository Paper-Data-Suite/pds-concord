from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.classes import write_class_roster
from pds_core.module_profiles import build_module_registry
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
    ParticipantReference,
    SubjectReference,
)
from concord.packet_storage import create_packet_library, load_current_packet
from concord.pds_module import get_module_profile
from concord.routing.scan_intake import route_scan_sources
from concord.starter_templates.catalog import get_starter_template
from concord.storage import load_current_record_graph
from concord.template_storage import create_template_library, load_current_template
from concord.workflows import (
    AddArtifactAuthorRequest,
    CreateActivityContextRequest,
    CreateGroupWithMembersRequest,
    GroupMemberSpec,
    GroupRoleSpec,
    PacketSubjectBinding,
    PreparePacketInstantiationRequest,
    PrepareStarterTemplateInstallRequest,
    RenderPacketInstanceRequest,
    ReplaceArtifactSubjectRequest,
    WorkflowActor,
    add_artifact_author,
    commit_packet_instantiation,
    commit_starter_template_install,
    core_student_participant,
    create_activity_context,
    create_group_with_members,
    prepare_packet_instantiation,
    prepare_starter_template_install,
    render_packet_instance,
    replace_artifact_subject,
)
from concord.workflows.context import provenance

CLASS_ID = "english12-p2"
ACTIVITY_ID = "activity-1"
SESSION_ID = "session-1"
PACKET_ID = "packet-1"
PACKET_VERSION_ID = "packet-version-1"
PACKET_COMPONENT_ID = "component-review"
REVIEWER_ID = "student-1"
REVIEWEE_ID = "student-2"
TARGET_KEY = "role:role-observer"


def _clock() -> datetime:
    return datetime(2026, 9, 20, 5, 0, tzinfo=timezone.utc)


def _actor() -> WorkflowActor:
    return WorkflowActor(
        actor_id="teacher-1",
        display_label="Synthetic Teacher",
        role_label="teacher",
    )


def _context() -> EffectiveContext:
    return EffectiveContext(
        activity_id=ACTIVITY_ID,
        session_ids=(SESSION_ID,),
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
            CLASS_ID,
            "2026-2027",
            created_at=_clock(),
        ),
    )
    write_class_roster(
        root,
        create_roster(
            CLASS_ID,
            (
                {
                    "student_id": REVIEWER_ID,
                    "last_name": "One",
                    "first_name": "Alex",
                    "period": "2",
                },
                {
                    "student_id": REVIEWEE_ID,
                    "last_name": "Two",
                    "first_name": "Blair",
                    "period": "2",
                },
            ),
        ),
    )
    created = create_activity_context(
        CreateActivityContextRequest(
            class_id=CLASS_ID,
            activity_id=ACTIVITY_ID,
            title="Historical Relationship Review",
            activity_type=activity_type,
            scoring_orientation="evidence_only",
            session_id=SESSION_ID,
            actor=_actor(),
            activity_status="active",
            session_status="active",
            session_label="Review Session 1",
        ),
        workspace_root=root,
        clock=_clock,
    )
    create_group_with_members(
        CreateGroupWithMembersRequest(
            class_id=CLASS_ID,
            activity_id=ACTIVITY_ID,
            group_id="group-reviewers",
            label="Reviewers",
            expected_snapshot_revision=created.commit.snapshot_revision,
            actor=_actor(),
            status="active",
            effective_context=_context(),
            members=(
                GroupMemberSpec(
                    membership_id="membership-reviewer",
                    student_id=REVIEWER_ID,
                    effective_context=_context(),
                ),
            ),
            roles=(
                GroupRoleSpec(
                    role_assignment_id="role-observer",
                    participant_reference=core_student_participant(
                        root,
                        CLASS_ID,
                        REVIEWER_ID,
                    ),
                    role_key="observer",
                    effective_context=_context(),
                    membership_id="membership-reviewer",
                ),
            ),
        ),
        workspace_root=root,
        clock=_clock,
    )
    return root


def _install_exact_v1_and_packet(root: Path, starter_key: str) -> str:
    entry = get_starter_template(starter_key)
    created = provenance(_actor(), clock=_clock, source_kind="manual")
    definition, v1 = entry.build_template_records(
        created_provenance=created,
        status="active",
    )
    create_template_library(
        root,
        definition=definition,
        initial_version=v1,
        rendering_specification=entry.rendering_specification_bytes(),
    )
    packet_definition = PacketDefinition(
        packet_definition_id=PACKET_ID,
        name="Historical Starter Packet",
        purpose="Exercise issue #113 historical starter compatibility.",
        status="active",
        created_provenance=created,
    )
    packet_version = PacketVersion(
        packet_version_id=PACKET_VERSION_ID,
        packet_definition_id=PACKET_ID,
        version_label="v1",
        revision_sequence=1,
        components=(
            PacketComponent(
                packet_component_id=PACKET_COMPONENT_ID,
                sequence=1,
                component_kind="concord_template",
                template_id=entry.template_id,
                template_version_id=v1.template_version_id,
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
        definition=packet_definition,
        initial_version=packet_version,
    )
    return v1.template_version_id


def _install_current_starter_and_packet(root: Path, starter_key: str) -> str:
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
    packet_definition = PacketDefinition(
        packet_definition_id=PACKET_ID,
        name="Mixed Response Packet",
        purpose="Exercise issue #113 mixed-response authorship.",
        status="active",
        created_provenance=created,
    )
    packet_version = PacketVersion(
        packet_version_id=PACKET_VERSION_ID,
        packet_definition_id=PACKET_ID,
        version_label="v1",
        revision_sequence=1,
        components=(
            PacketComponent(
                packet_component_id=PACKET_COMPONENT_ID,
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
        definition=packet_definition,
        initial_version=packet_version,
    )
    return installed.template_version_id


def _request(*, reviewed_subject: SubjectReference | None = None):
    subject_bindings = ()
    if reviewed_subject is not None:
        subject_bindings = (
            PacketSubjectBinding(
                packet_component_id=PACKET_COMPONENT_ID,
                target_key=TARGET_KEY,
                subject_reference=reviewed_subject,
            ),
        )
    return PreparePacketInstantiationRequest(
        class_id=CLASS_ID,
        activity_id=ACTIVITY_ID,
        session_id=SESSION_ID,
        packet_definition_id=PACKET_ID,
        packet_version_id=PACKET_VERSION_ID,
        actor=_actor(),
        subject_bindings=subject_bindings,
    )


def _student_subject(student_id: str) -> SubjectReference:
    return SubjectReference(
        subject_kind="core_student",
        subject_id=student_id,
        owning_system="core",
    )


def _render_only_packet(root: Path):
    graph = load_current_record_graph(
        root,
        ModuleWorkRef("concord", CLASS_ID, ACTIVITY_ID),
    ).graph
    assert len(graph.packet_instances) == 1
    packet = graph.packet_instances[0]
    return render_packet_instance(
        RenderPacketInstanceRequest(
            class_id=CLASS_ID,
            activity_id=ACTIVITY_ID,
            packet_instance_id=packet.packet_instance_id,
            actor=_actor(),
        ),
        workspace_root=root,
    )


def _upgrade_starter(root: Path, starter_key: str) -> str:
    result = commit_starter_template_install(
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
    assert result.outcome == "upgraded"
    return result.template_version_id


def test_affected_v1_packet_replays_identically_after_packaged_upgrade(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    v1_id = _install_exact_v1_and_packet(root, "peer_review_writing")
    prepared = prepare_packet_instantiation(
        _request(),
        workspace_root=root,
        clock=_clock,
    )

    assert prepared.ready_for_commit
    plan = prepared.target_plans[0].artifacts[0]
    assert plan.template_version_id == v1_id
    assert plan.proposed_subject_reference == _student_subject(REVIEWER_ID)
    assert plan.proposed_subject_role == "observed_participant"

    commit_packet_instantiation(
        prepared,
        workspace_root=root,
        clock=_clock,
    )
    rendered = _render_only_packet(root)
    first_bytes = rendered.output_path.read_bytes()
    first_digest = rendered.output_sha256
    first_payloads = rendered.payloads

    work = ModuleWorkRef("concord", CLASS_ID, ACTIVITY_ID)
    before = load_current_record_graph(root, work)
    packet = before.graph.packet_instances[0]
    binding = packet.artifact_bindings[0]
    frozen_values = binding.rendering_values
    fallbacks = tuple(page.human_fallback for page in before.graph.artifact_pages)
    routes = tuple(
        load_route_registration(root, parse_pds2_payload(payload))
        for payload in first_payloads
    )

    v2_id = _upgrade_starter(root, "peer_review_writing")
    assert v2_id != v1_id
    loaded_template = load_current_template(
        root,
        get_starter_template("peer_review_writing").template_id,
    )
    assert loaded_template.current_template_version_id == v2_id
    installed_version_ids = tuple(
        version.template_version_id for version in loaded_template.versions
    )
    assert installed_version_ids == (v1_id, v2_id)

    packet_library = load_current_packet(root, PACKET_ID)
    assert (
        packet_library.head_version.components[0].template_version_id
        == v1_id
    )

    after_upgrade = load_current_record_graph(root, work)
    assert after_upgrade == before
    packet_after = after_upgrade.graph.packet_instances[0]
    binding_after = packet_after.artifact_bindings[0]
    assert binding_after.template_version_id == v1_id
    assert binding_after.rendering_values == frozen_values
    assert tuple(
        page.human_fallback for page in after_upgrade.graph.artifact_pages
    ) == fallbacks
    assert tuple(
        load_route_registration(root, parse_pds2_payload(payload))
        for payload in first_payloads
    ) == routes

    replay = _render_only_packet(root)
    assert replay.replayed
    assert replay.payloads == first_payloads
    assert replay.output_sha256 == first_digest
    assert replay.output_path.read_bytes() == first_bytes


def test_returned_v1_evidence_survives_upgrade_and_remains_correctable(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    v1_id = _install_exact_v1_and_packet(root, "peer_review_writing")
    prepared = prepare_packet_instantiation(
        _request(),
        workspace_root=root,
        clock=_clock,
    )
    committed = commit_packet_instantiation(
        prepared,
        workspace_root=root,
        clock=_clock,
    )
    rendered = _render_only_packet(root)

    work = ModuleWorkRef("concord", CLASS_ID, ACTIVITY_ID)
    generated = load_current_record_graph(root, work).graph
    assert len(generated.artifact_authors) == 1
    initial_author = generated.artifact_authors[0]
    assert isinstance(initial_author.author_reference, ParticipantReference)
    assert initial_author.author_reference.participant_id == REVIEWER_ID
    assert initial_author.attribution_status == "proposed"
    assert len(generated.artifact_subjects) == 1
    initial_subject = generated.artifact_subjects[0]
    assert initial_subject.subject_reference == _student_subject(REVIEWER_ID)
    assert initial_subject.subject_role == "observed_participant"
    assert initial_subject.confirmation_status == "proposed"

    registry = build_module_registry(
        explicit_profiles=(get_module_profile(),),
        discover_installed=False,
    )
    batch = route_scan_sources(
        (rendered.output_path,),
        workspace_root=root,
        registry=registry,
    )
    assert batch.dispatched_count == len(committed.pages)
    assert batch.failure_count == 0

    returned = load_current_record_graph(root, work)
    assert len(returned.graph.scan_references) == len(committed.pages)
    assert {page.page_status for page in returned.graph.artifact_pages} == {
        "returned"
    }
    returned_routes = tuple(
        load_route_registration(root, parse_pds2_payload(payload))
        for payload in rendered.payloads
    )
    returned_scan_references = returned.graph.scan_references
    returned_author = returned.graph.artifact_authors[0]
    returned_subject = returned.graph.artifact_subjects[0]

    v2_id = _upgrade_starter(root, "peer_review_writing")
    assert v2_id != v1_id

    after_upgrade = load_current_record_graph(root, work)
    assert after_upgrade == returned
    assert after_upgrade.graph.scan_references == returned_scan_references
    assert after_upgrade.graph.artifact_authors[0] == returned_author
    assert after_upgrade.graph.artifact_subjects[0] == returned_subject
    assert tuple(
        load_route_registration(root, parse_pds2_payload(payload))
        for payload in rendered.payloads
    ) == returned_routes

    artifact_id = after_upgrade.graph.artifact_instances[0].artifact_instance_id
    corrected = replace_artifact_subject(
        ReplaceArtifactSubjectRequest(
            class_id=CLASS_ID,
            activity_id=ACTIVITY_ID,
            artifact_subject_id=returned_subject.artifact_subject_id,
            replacement_artifact_subject_id="subject-reviewee-corrected",
            correction_id="correction-reviewee-subject",
            reason="Returned peer review concerns the reviewee, not the reviewer.",
            subject_reference=_student_subject(REVIEWEE_ID),
            subject_role="reviewed_subject",
            confirmation_status="confirmed",
            assignment_source="teacher",
            expected_snapshot_revision=after_upgrade.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=_clock,
    )
    added = add_artifact_author(
        AddArtifactAuthorRequest(
            class_id=CLASS_ID,
            activity_id=ACTIVITY_ID,
            artifact_instance_id=artifact_id,
            artifact_author_id="author-reviewee-response",
            author_reference=core_student_participant(
                root,
                CLASS_ID,
                REVIEWEE_ID,
            ),
            authorship_mode="co_author",
            attribution_status="confirmed",
            attribution_source="teacher",
            expected_snapshot_revision=corrected.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=_clock,
    )

    final = load_current_record_graph(root, work)
    assert final.snapshot_revision == added.commit.snapshot_revision
    author_ids: set[str] = set()
    for author in final.graph.artifact_authors:
        reference = author.author_reference
        if isinstance(reference, ParticipantReference):
            author_ids.add(reference.participant_id)
    assert author_ids == {REVIEWER_ID, REVIEWEE_ID}

    replacement = next(
        subject
        for subject in final.graph.artifact_subjects
        if subject.supersedes_artifact_subject_id
        == returned_subject.artifact_subject_id
    )
    assert replacement.subject_reference == _student_subject(REVIEWEE_ID)
    assert replacement.subject_role == "reviewed_subject"
    assert replacement.confirmation_status == "confirmed"
    assert returned_subject in final.graph.artifact_subjects
    assert final.graph.scan_references == returned_scan_references


@pytest.mark.parametrize(
    ("starter_key", "activity_type"),
    (
        ("peer_review_writing", "socratic_seminar"),
        ("peer_review_presentation", "project"),
    ),
)
def test_mixed_response_v2_starts_with_reviewer_then_accepts_reviewee_author(
    tmp_path: Path,
    starter_key: str,
    activity_type: str,
) -> None:
    root = _workspace(tmp_path, activity_type=activity_type)
    v2_id = _install_current_starter_and_packet(root, starter_key)
    entry = get_starter_template(starter_key)
    loaded_template = load_current_template(root, entry.template_id)
    current = next(
        version
        for version in loaded_template.versions
        if version.template_version_id == v2_id
    )
    assert current.default_authorship_expectation is not None
    assert current.default_authorship_expectation.multiple_allowed is True

    prepared = prepare_packet_instantiation(
        _request(reviewed_subject=_student_subject(REVIEWEE_ID)),
        workspace_root=root,
        clock=_clock,
    )
    assert prepared.ready_for_commit
    commit_packet_instantiation(
        prepared,
        workspace_root=root,
        clock=_clock,
    )

    work = ModuleWorkRef("concord", CLASS_ID, ACTIVITY_ID)
    generated = load_current_record_graph(root, work)
    assert len(generated.graph.artifact_authors) == 1
    reviewer = generated.graph.artifact_authors[0]
    assert isinstance(reviewer.author_reference, ParticipantReference)
    assert reviewer.author_reference.participant_id == REVIEWER_ID
    assert generated.graph.artifact_subjects[0].subject_reference == (
        _student_subject(REVIEWEE_ID)
    )

    artifact_id = generated.graph.artifact_instances[0].artifact_instance_id
    added = add_artifact_author(
        AddArtifactAuthorRequest(
            class_id=CLASS_ID,
            activity_id=ACTIVITY_ID,
            artifact_instance_id=artifact_id,
            artifact_author_id=f"author-reviewee-{starter_key}",
            author_reference=core_student_participant(
                root,
                CLASS_ID,
                REVIEWEE_ID,
            ),
            authorship_mode="co_author",
            attribution_status="confirmed",
            attribution_source="teacher",
            expected_snapshot_revision=generated.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=_clock,
    )

    final = load_current_record_graph(root, work)
    assert final.snapshot_revision == added.commit.snapshot_revision
    author_ids: set[str] = set()
    for author in final.graph.artifact_authors:
        reference = author.author_reference
        if isinstance(reference, ParticipantReference):
            author_ids.add(reference.participant_id)
    assert author_ids == {REVIEWER_ID, REVIEWEE_ID}
