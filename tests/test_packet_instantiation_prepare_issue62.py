from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.classes import write_class_roster
from pds_core.rosters import create_roster
from pds_core.routing_models import ModuleRecordRef
from pds_core.workspace import ensure_workspace_root

from concord.models import (
    EffectiveContext,
    PacketAudienceIntent,
    PacketComponent,
    PacketCondition,
    PacketDefinition,
    PacketRenderingRules,
    PacketVersion,
)
from concord.packet_storage import create_packet_library
from concord.starter_templates.catalog import list_starter_templates
from concord.template_storage import (
    load_template_rendering_specification,
)
from concord.workflows import (
    CreateActivityContextRequest,
    CreateGroupWithMembersRequest,
    GroupMemberSpec,
    GroupRoleSpec,
    PacketComponentChoice,
    PreparePacketInstantiationRequest,
    PrepareStarterTemplateInstallRequest,
    WorkflowActor,
    commit_starter_template_install,
    core_student_participant,
    create_activity_context,
    create_group_with_members,
    prepare_packet_instantiation,
    prepare_starter_template_install,
)
from concord.workflows.context import provenance
from concord.workflows.errors import ConcordWorkflowValidationError


def _clock() -> datetime:
    return datetime(2026, 8, 25, 18, 30, tzinfo=timezone.utc)


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


def _workspace(tmp_path: Path) -> tuple[Path, int]:
    root = ensure_workspace_root(tmp_path / "workspace")
    metadata = create_class_metadata(
        "class-1",
        "2026-2027",
        created_at=_clock(),
    )
    write_class_metadata_for_class(root, metadata)
    roster = create_roster(
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
    )
    write_class_roster(root, roster)
    created = create_activity_context(
        CreateActivityContextRequest(
            class_id="class-1",
            activity_id="activity-1",
            title="Synthetic Collaboration Activity",
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
    revision = created.commit.snapshot_revision
    first = create_group_with_members(
        CreateGroupWithMembersRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_id="group-a",
            label="Group A",
            expected_snapshot_revision=revision,
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
                    role_assignment_id="role-1",
                    participant_reference=core_student_participant(
                        root, "class-1", "student-1"
                    ),
                    role_key="recorder",
                    effective_context=_context(),
                    membership_id="membership-1",
                ),
            ),
        ),
        workspace_root=root,
        clock=_clock,
    )
    second = create_group_with_members(
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
    return root, second.commit.snapshot_revision


def _starter_key(audience: str) -> str:
    synthetic_provenance = provenance(
        _actor(),
        clock=_clock,
        source_kind="imported",
    )
    for entry in list_starter_templates():
        _, version = entry.build_template_records(
            created_provenance=synthetic_provenance,
            status="active",
        )
        activity_types = version.compatibility.activity_type_keys
        scoring = version.compatibility.scoring_orientations
        if (
            audience in version.compatibility.audience_kinds
            and (not activity_types or "project" in activity_types)
            and (not scoring or "evidence_only" in scoring)
        ):
            return entry.starter_key
    raise AssertionError(f"no starter supports {audience}")


def _install(root: Path, starter_key: str):
    return commit_starter_template_install(
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


def _packet(
    root: Path,
    *,
    conditional_teacher_choice: bool = False,
    external: bool = False,
) -> tuple[str, str]:
    group_key = _starter_key("group")
    participant_key = _starter_key("participant")
    group_install = _install(root, group_key)
    participant_install = (
        group_install
        if participant_key == group_key
        else _install(root, participant_key)
    )
    created = provenance(_actor(), clock=_clock, source_kind="manual")

    components: list[PacketComponent] = []
    if external:
        components.append(
            PacketComponent(
                packet_component_id="component-external",
                sequence=1,
                component_kind="external_component",
                external_reference=ModuleRecordRef(
                    module_id="quillan",
                    record_kind="submission",
                    record_id="submission-1",
                    contract_version="1",
                ),
                copies_per_target=1,
                audience_intent=PacketAudienceIntent(
                    audience_kind="participant",
                ),
                requirement_level="required",
            )
        )
    else:
        components.extend(
            (
                PacketComponent(
                    packet_component_id="component-group",
                    sequence=1,
                    component_kind="concord_template",
                    template_id=group_install.template_id,
                    template_version_id=group_install.template_version_id,
                    copies_per_target=1,
                    audience_intent=PacketAudienceIntent(
                        audience_kind="group",
                    ),
                    requirement_level="required",
                ),
                PacketComponent(
                    packet_component_id="component-participant",
                    sequence=2,
                    component_kind="concord_template",
                    template_id=participant_install.template_id,
                    template_version_id=participant_install.template_version_id,
                    copies_per_target=1,
                    audience_intent=PacketAudienceIntent(
                        audience_kind="participant",
                    ),
                    requirement_level=(
                        "conditional"
                        if conditional_teacher_choice
                        else "required"
                    ),
                    condition=(
                        PacketCondition(condition_kind="teacher_choice")
                        if conditional_teacher_choice
                        else None
                    ),
                ),
                PacketComponent(
                    packet_component_id="component-role",
                    sequence=3,
                    component_kind="concord_template",
                    template_id=participant_install.template_id,
                    template_version_id=participant_install.template_version_id,
                    copies_per_target=1,
                    audience_intent=PacketAudienceIntent(
                        audience_kind="role",
                        role_keys=("recorder",),
                    ),
                    requirement_level="required",
                ),
            )
        )
    definition = PacketDefinition(
        packet_definition_id="packet-1",
        name="Synthetic Packet",
        purpose="Exercise Activity-specific Packet planning.",
        status="active",
        created_provenance=created,
    )
    version = PacketVersion(
        packet_version_id="packet-version-1",
        packet_definition_id=definition.packet_definition_id,
        version_label="v1",
        revision_sequence=1,
        components=tuple(components),
        rendering_rules=PacketRenderingRules(),
        created_provenance=created,
        status="active",
    )
    create_packet_library(
        root,
        definition=definition,
        initial_version=version,
    )
    return definition.packet_definition_id, version.packet_version_id


def _request(
    *,
    choices: tuple[PacketComponentChoice, ...] = (),
) -> PreparePacketInstantiationRequest:
    return PreparePacketInstantiationRequest(
        class_id="class-1",
        activity_id="activity-1",
        session_id="session-1",
        packet_definition_id="packet-1",
        packet_version_id="packet-version-1",
        actor=_actor(),
        component_choices=choices,
    )


def _tree(root: Path) -> tuple[tuple[str, int], ...]:
    return tuple(
        sorted(
            (
                path.relative_to(root).as_posix(),
                path.stat().st_size if path.is_file() else -1,
            )
            for path in root.rglob("*")
        )
    )


def test_public_template_asset_read_returns_exact_verified_bytes(
    tmp_path: Path,
) -> None:
    root, _ = _workspace(tmp_path)
    key = _starter_key("participant")
    installed = _install(root, key)
    data = load_template_rendering_specification(
        root,
        installed.template_id,
        installed.template_version_id,
    )
    assert data.startswith(b"{")
    assert data.endswith(b"\n")


def test_prepare_is_zero_write_and_expands_group_participant_and_role_targets(
    tmp_path: Path,
) -> None:
    root, _ = _workspace(tmp_path)
    _packet(root)
    before = _tree(root)
    prepared = prepare_packet_instantiation(
        _request(),
        workspace_root=root,
        clock=_clock,
    )
    after = _tree(root)

    assert after == before
    assert prepared.ready_for_commit
    assert prepared.generation_date == "2026-08-25"
    assert prepared.packet_instance_count == 6
    assert prepared.artifact_count == 6
    assert prepared.page_count >= 6
    assert prepared.route_count >= 6
    assert len(prepared.review_digest) == 64
    assert {item.target_context.audience_kind for item in prepared.target_plans} == {
        "group",
        "participant",
        "role",
    }
    assert [item.target_key for item in prepared.target_plans] == [
        "group:group-a",
        "group:group-b",
        "participant:student-1",
        "participant:student-2",
        "participant:student-3",
        "role:role-1",
    ]
    assert all(
        "pending_route"
        in {value.status for value in artifact.rendering_inputs}
        for target in prepared.target_plans
        for artifact in target.artifacts
    )


def test_preview_digest_is_deterministic_for_same_reviewed_state(
    tmp_path: Path,
) -> None:
    root, _ = _workspace(tmp_path)
    _packet(root)
    first = prepare_packet_instantiation(
        _request(),
        workspace_root=root,
        clock=_clock,
    )
    second = prepare_packet_instantiation(
        _request(),
        workspace_root=root,
        clock=_clock,
    )
    assert first.review_digest == second.review_digest
    assert first.target_plans == second.target_plans


def test_teacher_choice_is_explicit_and_preview_can_be_not_ready(
    tmp_path: Path,
) -> None:
    root, _ = _workspace(tmp_path)
    _packet(root, conditional_teacher_choice=True)
    unresolved = prepare_packet_instantiation(
        _request(),
        workspace_root=root,
        clock=_clock,
    )
    assert not unresolved.ready_for_commit
    assert {
        item.code for item in unresolved.diagnostics if item.blocking
    } == {"teacher_choice_required"}

    included = prepare_packet_instantiation(
        _request(
            choices=(
                PacketComponentChoice(
                    packet_component_id="component-participant",
                    include=True,
                ),
            )
        ),
        workspace_root=root,
        clock=_clock,
    )
    assert included.ready_for_commit
    participant_preview = next(
        item
        for item in included.component_previews
        if item.packet_component_id == "component-participant"
    )
    assert participant_preview.included_target_count == 3


def test_external_component_fails_preflight_before_mutation(tmp_path: Path) -> None:
    root, _ = _workspace(tmp_path)
    _packet(root, external=True)
    before = _tree(root)
    with pytest.raises(
        ConcordWorkflowValidationError,
        match="does not yet support external_component",
    ):
        prepare_packet_instantiation(
            _request(),
            workspace_root=root,
            clock=_clock,
        )
    assert _tree(root) == before


def test_required_component_cannot_be_explicitly_omitted(tmp_path: Path) -> None:
    root, _ = _workspace(tmp_path)
    _packet(root)
    with pytest.raises(
        ConcordWorkflowValidationError,
        match="required Packet components cannot",
    ):
        prepare_packet_instantiation(
            _request(
                choices=(
                    PacketComponentChoice(
                        packet_component_id="component-group",
                        include=False,
                    ),
                )
            ),
            workspace_root=root,
            clock=_clock,
        )
