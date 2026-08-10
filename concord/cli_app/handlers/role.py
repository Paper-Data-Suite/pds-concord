"""Direct Role Assignment commands."""

from __future__ import annotations

import argparse

from concord.cli_app.common import (
    effective_context,
    load_command_standards_library,
    student_participant,
    workflow_actor,
    workspace_arg,
)
from concord.cli_app.output import print_commit, print_role
from concord.workflows import (
    AssignRoleRequest,
    EndRoleRequest,
    ReassignRoleRequest,
    assign_role,
    end_role,
    list_roles,
    reassign_role,
)


def handle_assign(args: argparse.Namespace) -> int:
    request = AssignRoleRequest(
        class_id=args.class_id,
        activity_id=args.activity_id,
        role_assignment_id=args.role_assignment_id,
        participant_reference=student_participant(args),
        role_key=args.role_key,
        effective_context=effective_context(args),
        expected_snapshot_revision=args.expected_snapshot,
        actor=workflow_actor(args),
        status=args.status,
        membership_id=args.membership_id,
        group_id=args.group_id,
        role_label_snapshot=args.role_label,
    )
    result = assign_role(
        request,
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print_commit(result.commit)
    return 0


def handle_list(args: argparse.Namespace) -> int:
    items = list_roles(
        args.class_id,
        args.activity_id,
        group_id=args.group_id,
        workspace_root=workspace_arg(args),
    )
    if not items:
        print("No Role Assignments found.")
        return 0
    for item in items:
        print_role(item)
    return 0


def handle_end(args: argparse.Namespace) -> int:
    request = EndRoleRequest(
        class_id=args.class_id,
        activity_id=args.activity_id,
        role_assignment_id=args.role_assignment_id,
        expected_snapshot_revision=args.expected_snapshot,
        actor=workflow_actor(args),
        status=args.status,
    )
    result = end_role(
        request,
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print_commit(result.commit)
    return 0


def handle_reassign(args: argparse.Namespace) -> int:
    request = ReassignRoleRequest(
        class_id=args.class_id,
        activity_id=args.activity_id,
        role_assignment_id=args.role_assignment_id,
        successor_role_assignment_id=args.successor_role_assignment_id,
        participant_reference=student_participant(args),
        role_key=args.role_key,
        effective_context=effective_context(args),
        expected_snapshot_revision=args.expected_snapshot,
        actor=workflow_actor(args),
        membership_id=args.membership_id,
        group_id=args.group_id,
        role_label_snapshot=args.role_label,
        predecessor_status=args.predecessor_status,
        successor_status=args.successor_status,
    )
    result = reassign_role(
        request,
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print_commit(result.commit)
    print(f"Role Assignment: {result.role_assignment_id}")
    print(f"Predecessor: {result.predecessor_role_assignment_id}")
    return 0
