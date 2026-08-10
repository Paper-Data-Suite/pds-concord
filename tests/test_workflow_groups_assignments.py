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
from pds_core.routing_models import ModuleWorkRef
from pds_core.workspace import ensure_workspace_root

from concord.models import EffectiveContext, ParticipantReference
from concord.storage import (
    list_record_revisions,
    list_work_snapshots,
    load_current_record_graph,
)
from concord.storage_errors import ConcordStorageValidationError
from concord.workflows import (
    AddMembershipRequest,
    AddMembershipsRequest,
    AssignResponsibilityRequest,
    AssignRoleRequest,
    ConcordWorkflowConflictError,
    ConcordWorkflowNotFoundError,
    ConcordWorkflowValidationError,
    CreateActivityContextRequest,
    CreateGroupRequest,
    CreateGroupWithMembersRequest,
    CreateSessionRequest,
    EndMembershipRequest,
    EndResponsibilityRequest,
    EndRoleRequest,
    GroupMemberSpec,
    GroupResponsibilitySpec,
    GroupRoleSpec,
    ReassignMembershipRequest,
    ReassignResponsibilityRequest,
    ReassignRoleRequest,
    UpdateGroupRequest,
    WorkflowActor,
    add_membership,
    add_memberships,
    assign_responsibility,
    assign_role,
    core_student_participant,
    create_activity_context,
    create_group,
    create_group_with_members,
    create_session,
    end_membership,
    end_responsibility,
    end_role,
    group_record_reference,
    list_groups,
    list_memberships,
    list_responsibilities,
    list_roles,
    reassign_membership,
    reassign_responsibility,
    reassign_role,
    show_group,
    update_group,
)


def _clock(day: int) -> datetime:
    return datetime(2026, 8, day, 15, 0, tzinfo=timezone.utc)


def _actor() -> WorkflowActor:
    return WorkflowActor(
        actor_id="teacher-1",
        display_label="Synthetic Teacher",
        role_label="teacher",
    )


def _work() -> ModuleWorkRef:
    return ModuleWorkRef(
        module_id="concord",
        class_id="class-1",
        work_id="activity-1",
    )


def _context(*session_ids: str) -> EffectiveContext:
    return EffectiveContext(
        activity_id="activity-1",
        session_ids=tuple(session_ids),
    )


def _workspace_with_activity(tmp_path: Path) -> tuple[Path, int]:
    root = ensure_workspace_root(tmp_path / "workspace")
    metadata = create_class_metadata(
        "class-1",
        "2026-2027",
        created_at=_clock(1),
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
            session_label="Session One",
        ),
        workspace_root=root,
        clock=lambda: _clock(2),
    )
    added = create_session(
        CreateSessionRequest(
            class_id="class-1",
            activity_id="activity-1",
            session_id="session-2",
            sequence=2,
            expected_snapshot_revision=created.commit.snapshot_revision,
            actor=_actor(),
            label="Session Two",
        ),
        workspace_root=root,
        clock=lambda: _clock(3),
    )
    return root, added.commit.snapshot_revision


def _group_with_members(
    root: Path,
    expected_snapshot_revision: int,
    *,
    group_id: str = "group-a",
    member_ids: tuple[tuple[str, str], ...] = (
        ("membership-1", "student-1"),
    ),
) -> int:
    result = create_group_with_members(
        CreateGroupWithMembersRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_id=group_id,
            label=f"Synthetic {group_id}",
            expected_snapshot_revision=expected_snapshot_revision,
            actor=_actor(),
            status="active",
            effective_context=_context("session-1", "session-2"),
            members=tuple(
                GroupMemberSpec(
                    membership_id=membership_id,
                    student_id=student_id,
                    effective_context=_context("session-1", "session-2"),
                )
                for membership_id, student_id in member_ids
            ),
        ),
        workspace_root=root,
        clock=lambda: _clock(4),
    )
    return result.commit.snapshot_revision


def test_group_create_list_show_update_and_history(tmp_path: Path) -> None:
    root, revision = _workspace_with_activity(tmp_path)
    created = create_group(
        CreateGroupRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_id="group-a",
            label="Group A",
            expected_snapshot_revision=revision,
            actor=_actor(),
            status="active",
            effective_context=_context("session-1", "session-2"),
        ),
        workspace_root=root,
        clock=lambda: _clock(4),
    )
    assert created.commit.snapshot_revision == 3
    groups = list_groups("class-1", "activity-1", workspace_root=root)
    assert [(item.group_id, item.member_count) for item in groups] == [("group-a", 0)]
    assert show_group(
        "class-1", "activity-1", "group-a", workspace_root=root
    ).summary.label == "Group A"

    updated = update_group(
        UpdateGroupRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_id="group-a",
            expected_snapshot_revision=3,
            actor=_actor(),
            label="Revised Group A",
        ),
        workspace_root=root,
        clock=lambda: _clock(5),
    )
    assert updated.commit.snapshot_revision == 4
    assert show_group(
        "class-1", "activity-1", "group-a", workspace_root=root
    ).summary.label == "Revised Group A"
    assert list_record_revisions(
        root,
        updated.commit.work,
        "group",
        "group-a",
    ) == (1, 2)


def test_group_parent_cycle_is_rejected_without_pointer_advance(tmp_path: Path) -> None:
    root, revision = _workspace_with_activity(tmp_path)
    first = create_group(
        CreateGroupRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_id="group-a",
            label="Group A",
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(4),
    )
    second = create_group(
        CreateGroupRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_id="group-b",
            label="Group B",
            parent_group_id="group-a",
            expected_snapshot_revision=first.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(5),
    )
    with pytest.raises(ConcordStorageValidationError):
        update_group(
            UpdateGroupRequest(
                class_id="class-1",
                activity_id="activity-1",
                group_id="group-a",
                parent_group_id="group-b",
                expected_snapshot_revision=second.commit.snapshot_revision,
                actor=_actor(),
            ),
            workspace_root=root,
            clock=lambda: _clock(6),
        )
    assert list_work_snapshots(root, _work()) == (1, 2, 3, 4)


def test_group_and_roster_memberships_commit_atomically(tmp_path: Path) -> None:
    root, revision = _workspace_with_activity(tmp_path)
    result = create_group_with_members(
        CreateGroupWithMembersRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_id="group-a",
            label="Group A",
            expected_snapshot_revision=revision,
            actor=_actor(),
            status="active",
            effective_context=_context("session-1", "session-2"),
            members=(
                GroupMemberSpec(
                    membership_id="membership-1",
                    student_id="student-1",
                    effective_context=_context("session-1", "session-2"),
                ),
                GroupMemberSpec(
                    membership_id="membership-2",
                    student_id="student-2",
                    effective_context=_context("session-1", "session-2"),
                ),
            ),
        ),
        workspace_root=root,
        clock=lambda: _clock(4),
    )
    assert {item.record_kind for item in result.commit.changed_records} == {
        "group",
        "group_membership",
    }
    assert result.membership_ids == ("membership-1", "membership-2")
    assert list_groups(
        "class-1", "activity-1", workspace_root=root
    )[0].member_count == 2
    memberships = list_memberships(
        "class-1",
        "activity-1",
        group_id="group-a",
        workspace_root=root,
    )
    assert {item.participant_display_label for item in memberships} == {
        "Alex One",
        "Blair Two",
    }


def test_group_context_setup_commits_memberships_roles_and_responsibilities_atomically(
    tmp_path: Path,
) -> None:
    root, revision = _workspace_with_activity(tmp_path)
    participant = core_student_participant(root, "class-1", "student-1")
    result = create_group_with_members(
        CreateGroupWithMembersRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_id="group-a",
            label="Group A",
            expected_snapshot_revision=revision,
            actor=_actor(),
            status="active",
            effective_context=_context("session-1", "session-2"),
            members=(
                GroupMemberSpec(
                    membership_id="membership-1",
                    student_id="student-1",
                    effective_context=_context("session-1", "session-2"),
                ),
            ),
            roles=(
                GroupRoleSpec(
                    role_assignment_id="role-1",
                    participant_reference=participant,
                    role_key="recorder",
                    effective_context=_context("session-1"),
                    membership_id="membership-1",
                ),
            ),
            responsibilities=(
                GroupResponsibilitySpec(
                    responsibility_assignment_id="responsibility-1",
                    assignee_reference=group_record_reference("group-a"),
                    description="Record observations",
                    effective_context=_context("session-1"),
                ),
            ),
        ),
        workspace_root=root,
        clock=lambda: _clock(4),
    )
    assert {item.record_kind for item in result.commit.changed_records} == {
        "group",
        "group_membership",
        "role_assignment",
        "responsibility_assignment",
    }
    assert result.membership_ids == ("membership-1",)
    assert result.role_assignment_ids == ("role-1",)
    assert result.responsibility_assignment_ids == ("responsibility-1",)

    loaded = load_current_record_graph(root, result.commit.work).graph
    role = next(
        item
        for item in loaded.role_assignments
        if item.role_assignment_id == "role-1"
    )
    responsibility = next(
        item
        for item in loaded.responsibility_assignments
        if item.responsibility_assignment_id == "responsibility-1"
    )
    assert role.group_id == "group-a"
    assert role.membership_id == "membership-1"
    assert responsibility.group_id == "group-a"
    assert responsibility.assignee_reference == group_record_reference("group-a")


def test_invalid_composite_group_setup_publishes_no_intermediate_group(
    tmp_path: Path,
) -> None:
    root, revision = _workspace_with_activity(tmp_path)
    participant = core_student_participant(root, "class-1", "student-1")
    with pytest.raises(ConcordWorkflowNotFoundError):
        create_group_with_members(
            CreateGroupWithMembersRequest(
                class_id="class-1",
                activity_id="activity-1",
                group_id="group-a",
                label="Group A",
                expected_snapshot_revision=revision,
                actor=_actor(),
                members=(),
                roles=(
                    GroupRoleSpec(
                        role_assignment_id="role-1",
                        participant_reference=participant,
                        role_key="recorder",
                        effective_context=_context("session-1"),
                        membership_id="membership-missing",
                    ),
                ),
            ),
            workspace_root=root,
            clock=lambda: _clock(4),
        )
    assert list_work_snapshots(root, _work()) == (1, 2)
    assert list_groups("class-1", "activity-1", workspace_root=root) == ()


def test_existing_group_accepts_multiple_memberships_atomically(
    tmp_path: Path,
) -> None:
    root, revision = _workspace_with_activity(tmp_path)
    group = create_group(
        CreateGroupRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_id="group-a",
            label="Group A",
            expected_snapshot_revision=revision,
            actor=_actor(),
            status="active",
            effective_context=_context("session-1", "session-2"),
        ),
        workspace_root=root,
        clock=lambda: _clock(4),
    )
    added = add_memberships(
        AddMembershipsRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_id="group-a",
            members=(
                GroupMemberSpec(
                    membership_id="membership-1",
                    student_id="student-1",
                    effective_context=_context("session-1"),
                ),
                GroupMemberSpec(
                    membership_id="membership-2",
                    student_id="student-2",
                    effective_context=_context("session-2"),
                ),
            ),
            expected_snapshot_revision=group.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(5),
    )
    assert added.membership_ids == ("membership-1", "membership-2")
    assert added.commit.snapshot_revision == group.commit.snapshot_revision + 1
    assert {
        item.record_id for item in added.commit.changed_records
    } == {"membership-1", "membership-2"}
    assert list_groups(
        "class-1", "activity-1", workspace_root=root
    )[0].member_count == 2


def test_unknown_roster_student_blocks_membership_without_snapshot(
    tmp_path: Path,
) -> None:
    root, revision = _workspace_with_activity(tmp_path)
    group_revision = _group_with_members(root, revision, member_ids=())
    with pytest.raises(ConcordWorkflowNotFoundError):
        add_membership(
            AddMembershipRequest(
                class_id="class-1",
                activity_id="activity-1",
                group_id="group-a",
                membership_id="membership-missing",
                student_id="student-404",
                effective_context=_context("session-1"),
                expected_snapshot_revision=group_revision,
                actor=_actor(),
            ),
            workspace_root=root,
            clock=lambda: _clock(5),
        )
    assert list_work_snapshots(root, _work()) == (1, 2, 3)


def test_overlapping_duplicate_active_membership_is_rejected(tmp_path: Path) -> None:
    root, revision = _workspace_with_activity(tmp_path)
    group_revision = _group_with_members(root, revision)
    with pytest.raises(ConcordWorkflowConflictError):
        add_membership(
            AddMembershipRequest(
                class_id="class-1",
                activity_id="activity-1",
                group_id="group-a",
                membership_id="membership-duplicate",
                student_id="student-1",
                effective_context=_context("session-2"),
                expected_snapshot_revision=group_revision,
                actor=_actor(),
            ),
            workspace_root=root,
            clock=lambda: _clock(5),
        )
    assert list_work_snapshots(root, _work()) == (1, 2, 3)


def test_membership_end_preserves_identity_and_revision_history(tmp_path: Path) -> None:
    root, revision = _workspace_with_activity(tmp_path)
    group_revision = _group_with_members(root, revision)
    ended = end_membership(
        EndMembershipRequest(
            class_id="class-1",
            activity_id="activity-1",
            membership_id="membership-1",
            expected_snapshot_revision=group_revision,
            actor=_actor(),
            status="completed",
        ),
        workspace_root=root,
        clock=lambda: _clock(5),
    )
    memberships = list_memberships(
        "class-1", "activity-1", workspace_root=root
    )
    assert memberships[0].membership_id == "membership-1"
    assert memberships[0].status == "completed"
    assert list_record_revisions(
        root,
        ended.commit.work,
        "group_membership",
        "membership-1",
    ) == (1, 2)


def test_membership_reassignment_moves_group_and_preserves_lineage(
    tmp_path: Path,
) -> None:
    root, revision = _workspace_with_activity(tmp_path)
    group_a_revision = _group_with_members(root, revision)
    group_b = create_group(
        CreateGroupRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_id="group-b",
            label="Group B",
            expected_snapshot_revision=group_a_revision,
            actor=_actor(),
            status="active",
            effective_context=_context("session-1", "session-2"),
        ),
        workspace_root=root,
        clock=lambda: _clock(5),
    )
    moved = reassign_membership(
        ReassignMembershipRequest(
            class_id="class-1",
            activity_id="activity-1",
            membership_id="membership-1",
            successor_membership_id="membership-1b",
            new_group_id="group-b",
            effective_context=_context("session-2"),
            expected_snapshot_revision=group_b.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(6),
    )
    assert moved.predecessor_membership_id == "membership-1"
    graph = load_current_record_graph(root, _work()).graph
    predecessor = next(
        item for item in graph.memberships if item.membership_id == "membership-1"
    )
    successor = next(
        item for item in graph.memberships if item.membership_id == "membership-1b"
    )
    assert predecessor.status == "reassigned"
    assert successor.group_id == "group-b"
    assert successor.participant_reference == predecessor.participant_reference
    assert successor.supersedes_membership_id == "membership-1"
    assert list_record_revisions(
        root,
        moved.commit.work,
        "group_membership",
        "membership-1",
    ) == (1, 2)
    assert list_record_revisions(
        root,
        moved.commit.work,
        "group_membership",
        "membership-1b",
    ) == (1,)


def test_role_assignment_infers_group_from_membership_and_lists_display_name(
    tmp_path: Path,
) -> None:
    root, revision = _workspace_with_activity(tmp_path)
    group_revision = _group_with_members(root, revision)
    participant = core_student_participant(root, "class-1", "student-1")
    assigned = assign_role(
        AssignRoleRequest(
            class_id="class-1",
            activity_id="activity-1",
            role_assignment_id="role-1",
            participant_reference=participant,
            role_key="recorder",
            effective_context=_context("session-1"),
            expected_snapshot_revision=group_revision,
            actor=_actor(),
            membership_id="membership-1",
        ),
        workspace_root=root,
        clock=lambda: _clock(5),
    )
    assert assigned.commit.snapshot_revision == 4
    roles = list_roles("class-1", "activity-1", workspace_root=root)
    assert roles[0].group_id == "group-a"
    assert roles[0].participant_display_label == "Alex One"


def test_role_membership_participant_mismatch_is_rejected(tmp_path: Path) -> None:
    root, revision = _workspace_with_activity(tmp_path)
    group_revision = _group_with_members(root, revision)
    other = core_student_participant(root, "class-1", "student-2")
    with pytest.raises(ConcordWorkflowValidationError):
        assign_role(
            AssignRoleRequest(
                class_id="class-1",
                activity_id="activity-1",
                role_assignment_id="role-invalid",
                participant_reference=other,
                role_key="speaker",
                effective_context=_context("session-1"),
                expected_snapshot_revision=group_revision,
                actor=_actor(),
                membership_id="membership-1",
            ),
            workspace_root=root,
            clock=lambda: _clock(5),
        )
    assert list_work_snapshots(root, _work()) == (1, 2, 3)


def test_role_end_and_reassignment_preserve_history(tmp_path: Path) -> None:
    root, revision = _workspace_with_activity(tmp_path)
    group_revision = _group_with_members(
        root,
        revision,
        member_ids=(
            ("membership-1", "student-1"),
            ("membership-2", "student-2"),
        ),
    )
    participant_1 = core_student_participant(root, "class-1", "student-1")
    assigned = assign_role(
        AssignRoleRequest(
            class_id="class-1",
            activity_id="activity-1",
            role_assignment_id="role-1",
            participant_reference=participant_1,
            role_key="speaker",
            effective_context=_context("session-1"),
            expected_snapshot_revision=group_revision,
            actor=_actor(),
            membership_id="membership-1",
        ),
        workspace_root=root,
        clock=lambda: _clock(5),
    )
    participant_2 = core_student_participant(root, "class-1", "student-2")
    reassigned = reassign_role(
        ReassignRoleRequest(
            class_id="class-1",
            activity_id="activity-1",
            role_assignment_id="role-1",
            successor_role_assignment_id="role-2",
            participant_reference=participant_2,
            role_key="speaker",
            effective_context=_context("session-2"),
            expected_snapshot_revision=assigned.commit.snapshot_revision,
            actor=_actor(),
            membership_id="membership-2",
        ),
        workspace_root=root,
        clock=lambda: _clock(6),
    )
    roles = {item.role_assignment_id: item for item in list_roles(
        "class-1", "activity-1", workspace_root=root
    )}
    assert roles["role-1"].status == "reassigned"
    assert roles["role-2"].supersedes_role_assignment_id == "role-1"
    ended = end_role(
        EndRoleRequest(
            class_id="class-1",
            activity_id="activity-1",
            role_assignment_id="role-2",
            expected_snapshot_revision=reassigned.commit.snapshot_revision,
            actor=_actor(),
            status="completed",
        ),
        workspace_root=root,
        clock=lambda: _clock(7),
    )
    assert ended.commit.snapshot_revision == 6
    assert list_record_revisions(root, _work(), "role_assignment", "role-1") == (
        1,
        2,
    )
    assert list_record_revisions(root, _work(), "role_assignment", "role-2") == (
        1,
        2,
    )


def test_role_context_cannot_extend_beyond_membership(tmp_path: Path) -> None:
    root, revision = _workspace_with_activity(tmp_path)
    group = create_group_with_members(
        CreateGroupWithMembersRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_id="group-a",
            label="Group A",
            expected_snapshot_revision=revision,
            actor=_actor(),
            status="active",
            effective_context=_context("session-1", "session-2"),
            members=(
                GroupMemberSpec(
                    membership_id="membership-1",
                    student_id="student-1",
                    effective_context=_context("session-1"),
                ),
            ),
        ),
        workspace_root=root,
        clock=lambda: _clock(4),
    )
    participant = core_student_participant(root, "class-1", "student-1")
    with pytest.raises(ConcordWorkflowValidationError):
        assign_role(
            AssignRoleRequest(
                class_id="class-1",
                activity_id="activity-1",
                role_assignment_id="role-invalid-context",
                participant_reference=participant,
                role_key="speaker",
                effective_context=_context("session-2"),
                expected_snapshot_revision=group.commit.snapshot_revision,
                actor=_actor(),
                membership_id="membership-1",
            ),
            workspace_root=root,
            clock=lambda: _clock(5),
        )


def test_group_assignee_responsibility_is_preserved_as_group(tmp_path: Path) -> None:
    root, revision = _workspace_with_activity(tmp_path)
    group_revision = _group_with_members(root, revision)
    assigned = assign_responsibility(
        AssignResponsibilityRequest(
            class_id="class-1",
            activity_id="activity-1",
            responsibility_assignment_id="responsibility-1",
            assignee_reference=group_record_reference("group-a"),
            description="Prepare the shared synthetic presentation.",
            effective_context=_context("session-1"),
            expected_snapshot_revision=group_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(5),
    )
    assert assigned.commit.snapshot_revision == 4
    responsibilities = list_responsibilities(
        "class-1", "activity-1", workspace_root=root
    )
    assert responsibilities[0].group_id == "group-a"
    assert responsibilities[0].assignee_display_label == "Synthetic group-a"
    assert responsibilities[0].assignee_reference == group_record_reference("group-a")


def test_responsibility_end_and_reassignment_preserve_lineage(tmp_path: Path) -> None:
    root, revision = _workspace_with_activity(tmp_path)
    group_revision = _group_with_members(root, revision)
    assigned = assign_responsibility(
        AssignResponsibilityRequest(
            class_id="class-1",
            activity_id="activity-1",
            responsibility_assignment_id="responsibility-1",
            assignee_reference=group_record_reference("group-a"),
            description="Prepare materials.",
            effective_context=_context("session-1"),
            expected_snapshot_revision=group_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(5),
    )
    student = core_student_participant(root, "class-1", "student-1")
    moved = reassign_responsibility(
        ReassignResponsibilityRequest(
            class_id="class-1",
            activity_id="activity-1",
            responsibility_assignment_id="responsibility-1",
            successor_responsibility_assignment_id="responsibility-2",
            assignee_reference=student,
            description="Present the prepared materials.",
            effective_context=_context("session-2"),
            expected_snapshot_revision=assigned.commit.snapshot_revision,
            actor=_actor(),
            group_id="group-a",
        ),
        workspace_root=root,
        clock=lambda: _clock(6),
    )
    values = {
        item.responsibility_assignment_id: item
        for item in list_responsibilities(
            "class-1", "activity-1", workspace_root=root
        )
    }
    assert values["responsibility-1"].status == "reassigned"
    assert (
        values["responsibility-2"].supersedes_responsibility_assignment_id
        == "responsibility-1"
    )
    ended = end_responsibility(
        EndResponsibilityRequest(
            class_id="class-1",
            activity_id="activity-1",
            responsibility_assignment_id="responsibility-2",
            expected_snapshot_revision=moved.commit.snapshot_revision,
            actor=_actor(),
            status="completed",
        ),
        workspace_root=root,
        clock=lambda: _clock(7),
    )
    assert ended.commit.snapshot_revision == 6
    assert list_record_revisions(
        root,
        _work(),
        "responsibility_assignment",
        "responsibility-1",
    ) == (1, 2)
    assert list_record_revisions(
        root,
        _work(),
        "responsibility_assignment",
        "responsibility-2",
    ) == (1, 2)


def test_responsibility_rejects_non_group_concord_assignee(tmp_path: Path) -> None:
    root, revision = _workspace_with_activity(tmp_path)
    group_revision = _group_with_members(root, revision)
    from concord.models import ConcordRecordReference

    with pytest.raises(ConcordWorkflowValidationError):
        assign_responsibility(
            AssignResponsibilityRequest(
                class_id="class-1",
                activity_id="activity-1",
                responsibility_assignment_id="responsibility-invalid",
                assignee_reference=ConcordRecordReference(
                    record_kind="session",
                    record_id="session-1",
                ),
                description="Invalid synthetic responsibility.",
                effective_context=_context("session-1"),
                expected_snapshot_revision=group_revision,
                actor=_actor(),
            ),
            workspace_root=root,
            clock=lambda: _clock(5),
        )


def test_core_student_participant_requires_roster_membership(tmp_path: Path) -> None:
    root, _ = _workspace_with_activity(tmp_path)
    participant = core_student_participant(root, "class-1", "student-3")
    assert participant == ParticipantReference(
        participant_kind="core_student",
        participant_id="student-3",
        owning_system="core",
    )
    with pytest.raises(ConcordWorkflowNotFoundError):
        core_student_participant(root, "class-1", "student-404")
