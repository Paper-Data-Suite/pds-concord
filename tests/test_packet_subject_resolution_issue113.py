from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.classes import write_class_roster
from pds_core.rosters import create_roster
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
from concord.packet_storage import create_packet_library
from concord.starter_templates.catalog import get_starter_template
from concord.storage import load_current_record_graph
from concord.workflows import (
    CreateActivityContextRequest,
    CreateGroupWithMembersRequest,
    GroupMemberSpec,
    GroupRoleSpec,
    PrepareStarterTemplateInstallRequest,
    WorkflowActor,
    commit_starter_template_install,
    core_student_participant,
    create_activity_context,
    create_group_with_members,
    prepare_starter_template_install,
)
from concord.workflows.context import provenance
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowValidationError,
)
from concord.workflows.packet_instantiation import (
    PacketSubjectBinding,
    PreparePacketInstantiationRequest,
    prepare_packet_instantiation,
)
from concord.workflows.packet_instantiation_commit import (
    commit_packet_instantiation,
)


def _clock() -> datetime:
    return datetime(2026, 9, 19, 17, 30, tzinfo=timezone.utc)


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


def _workspace(tmp_path: Path, *, activity_type: str = "project") -> Path:
    root = ensure_workspace_root(tmp_path / "workspace")
    write_class_metadata_for_class(
        root,
        create_class_metadata(
            "class-1",
            "2026-2027",
            created_at=_clock(),
        ),
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
                {
                    "student_id": "student-2",
                    "last_name": "Two",
                    "first_name": "Blair",
                    "period": "1",
                },
                {
                    "student_id": "student-3",
                    "last_name": "Three",
                    "first_name": "Casey",
                    "period": "1",
                },
            ),
        ),
    )
    created = create_activity_context(
        CreateActivityContextRequest(
            class_id="class-1",
            activity_id="activity-1",
            title="Synthetic Relationship Activity",
            activity_type=activity_type,
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
    first = create_group_with_members(
        CreateGroupWithMembersRequest(
            class_id="class-1",
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
                GroupMemberSpec(
                    membership_id="membership-2",
                    student_id="student-2",
                    effective_context=_context(),
                ),
            ),
            roles=(
                GroupRoleSpec(
                    role_assignment_id="role-observer",
                    participant_reference=core_student_participant(
                        root,
                        "class-1",
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
            class_id="class-1",
            activity_id="activity-1",
            group_id="group-b",
            label="Group B",
            expected_snapshot_revision=first.commit.snapshot_revision,
            actor=_actor(),
            status="active",
            effective_context=_context(),
            members=(
                GroupMemberSpec(
                    membership_id="membership-3",
                    student_id="student-3",
                    effective_context=_context(),
                ),
            ),
        ),
        workspace_root=root,
        clock=_clock,
    )
    return root


def _install_packet(root: Path, starter_key: str) -> None:
    entry = get_starter_template(starter_key)
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
        name="Relationship Packet",
        purpose="Exercise issue #113 Subject resolution.",
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


def _student_subject(student_id: str) -> SubjectReference:
    return SubjectReference(
        subject_kind="core_student",
        subject_id=student_id,
        owning_system="core",
    )


def _group_subject(group_id: str) -> SubjectReference:
    return SubjectReference(
        subject_kind="concord_group",
        subject_id=group_id,
        owning_system="concord",
    )


def _binding(subject: SubjectReference) -> PacketSubjectBinding:
    return PacketSubjectBinding(
        packet_component_id="component-review",
        target_key="role:role-observer",
        subject_reference=subject,
    )


def _request(
    *,
    subject_bindings: tuple[PacketSubjectBinding, ...] = (),
) -> PreparePacketInstantiationRequest:
    return PreparePacketInstantiationRequest(
        class_id="class-1",
        activity_id="activity-1",
        session_id="session-1",
        packet_definition_id="packet-1",
        packet_version_id="packet-version-1",
        actor=_actor(),
        subject_bindings=subject_bindings,
    )


def _only_artifact(prepared):
    assert len(prepared.target_plans) == 1
    target = prepared.target_plans[0]
    assert target.target_key == "role:role-observer"
    assert len(target.artifacts) == 1
    return target.artifacts[0]


def test_duplicate_subject_binding_for_same_component_target_is_rejected(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    _install_packet(root, "peer_review_writing")
    first = _binding(_student_subject("student-2"))
    second = _binding(_student_subject("student-3"))

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="must not duplicate component/target pairs",
    ):
        prepare_packet_instantiation(
            _request(subject_bindings=(first, second)),
            workspace_root=root,
            clock=_clock,
        )



def test_peer_review_missing_binding_blocks_preview_without_guessing(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    _install_packet(root, "peer_review_writing")

    prepared = prepare_packet_instantiation(
        _request(),
        workspace_root=root,
        clock=_clock,
    )

    assert not prepared.ready_for_commit
    artifact = _only_artifact(prepared)
    assert artifact.proposed_subject_reference is None
    assert artifact.proposed_subject_role is None
    blockers = tuple(item for item in prepared.diagnostics if item.blocking)
    assert len(blockers) == 1
    assert blockers[0].code == "artifact_subject_binding_required"
    assert blockers[0].packet_component_id == "component-review"
    assert blockers[0].target_key == "role:role-observer"


def test_peer_review_explicit_student_binding_is_frozen_into_preview(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    _install_packet(root, "peer_review_writing")
    reviewee = _student_subject("student-2")

    prepared = prepare_packet_instantiation(
        _request(subject_bindings=(_binding(reviewee),)),
        workspace_root=root,
        clock=_clock,
    )

    assert prepared.ready_for_commit
    artifact = _only_artifact(prepared)
    assert artifact.authorship_mode == "individual_author"
    assert artifact.proposed_author_reference == ParticipantReference(
        participant_kind="core_student",
        participant_id="student-1",
        owning_system="core",
    )
    assert artifact.proposed_subject_reference == reviewee
    assert artifact.proposed_subject_role == "reviewed_subject"
    assert artifact.effective_privacy_policy.classification == (
        "teacher_and_subjects"
    )
    assert artifact.effective_privacy_policy.audience_references == (reviewee,)


def test_peer_review_subject_binding_changes_review_digest(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    _install_packet(root, "peer_review_writing")

    blair = prepare_packet_instantiation(
        _request(subject_bindings=(_binding(_student_subject("student-2")),)),
        workspace_root=root,
        clock=_clock,
    )
    casey = prepare_packet_instantiation(
        _request(subject_bindings=(_binding(_student_subject("student-3")),)),
        workspace_root=root,
        clock=_clock,
    )

    assert blair.review_digest != casey.review_digest
    assert (
        _only_artifact(blair).proposed_subject_reference
        != _only_artifact(casey).proposed_subject_reference
    )


def test_peer_review_rejects_reviewer_as_reviewee(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    _install_packet(root, "peer_review_writing")

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="must differ from the Packet target",
    ):
        prepare_packet_instantiation(
            _request(
                subject_bindings=(_binding(_student_subject("student-1")),)
            ),
            workspace_root=root,
            clock=_clock,
        )


def test_peer_review_rejects_student_outside_exact_roster(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    _install_packet(root, "peer_review_writing")

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="not present in the exact Core class roster",
    ):
        prepare_packet_instantiation(
            _request(
                subject_bindings=(_binding(_student_subject("student-x")),)
            ),
            workspace_root=root,
            clock=_clock,
        )


def test_writing_peer_review_rejects_group_subject_kind(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    _install_packet(root, "peer_review_writing")

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="Subject kind is not permitted",
    ):
        prepare_packet_instantiation(
            _request(subject_bindings=(_binding(_group_subject("group-b")),)),
            workspace_root=root,
            clock=_clock,
        )


def test_presentation_peer_review_accepts_exact_activity_group_subject(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    _install_packet(root, "peer_review_presentation")
    reviewed_group = _group_subject("group-b")

    prepared = prepare_packet_instantiation(
        _request(subject_bindings=(_binding(reviewed_group),)),
        workspace_root=root,
        clock=_clock,
    )

    assert prepared.ready_for_commit
    artifact = _only_artifact(prepared)
    assert artifact.proposed_subject_reference == reviewed_group
    assert artifact.proposed_subject_role == "reviewed_subject"


def test_presentation_peer_review_rejects_stale_or_wrong_context_group(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    _install_packet(root, "peer_review_presentation")

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="not active in the selected Activity/Session",
    ):
        prepare_packet_instantiation(
            _request(subject_bindings=(_binding(_group_subject("group-z")),)),
            workspace_root=root,
            clock=_clock,
        )


def test_observer_v2_resolves_selected_session_and_observer_author(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path, activity_type="socratic_seminar")
    _install_packet(root, "fishbowl_observer")

    prepared = prepare_packet_instantiation(
        _request(),
        workspace_root=root,
        clock=_clock,
    )

    assert prepared.ready_for_commit
    artifact = _only_artifact(prepared)
    assert artifact.authorship_mode == "observer"
    assert artifact.proposed_author_reference == ParticipantReference(
        participant_kind="core_student",
        participant_id="student-1",
        owning_system="core",
    )
    assert artifact.proposed_subject_reference == SubjectReference(
        subject_kind="concord_session",
        subject_id="session-1",
        owning_system="concord",
    )
    assert artifact.proposed_subject_role == "session_context"


def test_binding_on_non_explicit_template_is_rejected(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    _install_packet(root, "think_pair_share")

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="does not match an explicit Subject resolution",
    ):
        prepare_packet_instantiation(
            _request(subject_bindings=(_binding(_student_subject("student-2")),)),
            workspace_root=root,
            clock=_clock,
        )


def test_legacy_v1_subject_semantics_remain_unchanged(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    _install_packet(root, "think_pair_share")

    prepared = prepare_packet_instantiation(
        _request(),
        workspace_root=root,
        clock=_clock,
    )

    assert prepared.ready_for_commit
    artifact = _only_artifact(prepared)
    assert artifact.proposed_subject_reference == _student_subject("student-1")
    assert artifact.proposed_subject_role == "observed_participant"


def test_commit_rejects_subject_binding_changed_after_review(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    _install_packet(root, "peer_review_writing")
    reviewed = prepare_packet_instantiation(
        _request(subject_bindings=(_binding(_student_subject("student-2")),)),
        workspace_root=root,
        clock=_clock,
    )
    tampered = replace(
        reviewed,
        request=replace(
            reviewed.request,
            subject_bindings=(_binding(_student_subject("student-3")),),
        ),
    )

    with pytest.raises(ConcordWorkflowConflictError, match="stale"):
        commit_packet_instantiation(
            tampered,
            workspace_root=root,
            clock=_clock,
        )



def test_commit_persists_explicit_reviewed_subject_role_without_kind_guessing(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    _install_packet(root, "peer_review_writing")
    reviewee = _student_subject("student-2")
    prepared = prepare_packet_instantiation(
        _request(subject_bindings=(_binding(reviewee),)),
        workspace_root=root,
        clock=_clock,
    )

    committed = commit_packet_instantiation(
        prepared,
        workspace_root=root,
        clock=_clock,
    )
    assert committed.artifact_instance_ids

    graph = load_current_record_graph(
        root,
        ModuleWorkRef("concord", "class-1", "activity-1"),
    ).graph
    assert len(graph.artifact_subjects) == 1
    subject = graph.artifact_subjects[0]
    assert subject.subject_reference == reviewee
    assert subject.subject_role == "reviewed_subject"
    assert subject.confirmation_status == "proposed"
    assert subject.assignment_source == "system"

    assert len(graph.artifact_authors) == 1
    author = graph.artifact_authors[0]
    assert author.authorship_mode == "individual_author"
    assert author.author_reference == ParticipantReference(
        participant_kind="core_student",
        participant_id="student-1",
        owning_system="core",
    )


def test_commit_persists_observer_session_relationship(tmp_path: Path) -> None:
    root = _workspace(tmp_path, activity_type="socratic_seminar")
    _install_packet(root, "talk_moves_observer")
    prepared = prepare_packet_instantiation(
        _request(),
        workspace_root=root,
        clock=_clock,
    )

    commit_packet_instantiation(
        prepared,
        workspace_root=root,
        clock=_clock,
    )
    graph = load_current_record_graph(
        root,
        ModuleWorkRef("concord", "class-1", "activity-1"),
    ).graph

    assert len(graph.artifact_subjects) == 1
    assert graph.artifact_subjects[0].subject_reference == SubjectReference(
        subject_kind="concord_session",
        subject_id="session-1",
        owning_system="concord",
    )
    assert graph.artifact_subjects[0].subject_role == "session_context"
    assert len(graph.artifact_authors) == 1
    assert graph.artifact_authors[0].authorship_mode == "observer"
