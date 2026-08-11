"""Direct Group and Membership commands."""

from __future__ import annotations

import argparse
import uuid

from concord.cli_app.common import (
    effective_context,
    load_command_standards_library,
    workflow_actor,
    workspace_arg,
)
from concord.cli_app.output import (
    print_commit,
    print_group_detail,
    print_group_summary,
    print_membership,
)
from concord.workflows import (
    AddMembershipsRequest,
    ConcordWorkflowValidationError,
    CreateGroupRequest,
    EndMembershipRequest,
    GroupMemberSpec,
    ReassignMembershipRequest,
    UpdateGroupRequest,
    add_memberships,
    create_group,
    end_membership,
    list_groups,
    list_memberships,
    reassign_membership,
    show_group,
    update_group,
)


def handle_create(args: argparse.Namespace) -> int:
    context = effective_context(args) if args.session_id else None
    request = CreateGroupRequest(
        class_id=args.class_id,
        activity_id=args.activity_id,
        group_id=args.group_id,
        label=args.label,
        expected_snapshot_revision=args.expected_snapshot,
        actor=workflow_actor(args),
        status=args.status,
        description=args.description,
        parent_group_id=args.parent_group_id,
        effective_context=context,
    )
    result = create_group(
        request,
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print_commit(result.commit)
    return 0


def handle_list(args: argparse.Namespace) -> int:
    items = list_groups(
        args.class_id,
        args.activity_id,
        workspace_root=workspace_arg(args),
    )
    if not items:
        print("No Groups found.")
        return 0
    for item in items:
        print_group_summary(item)
    return 0


def handle_show(args: argparse.Namespace) -> int:
    detail = show_group(
        args.class_id,
        args.activity_id,
        args.group_id,
        workspace_root=workspace_arg(args),
    )
    print_group_detail(detail)
    return 0


def _update_request(
    args: argparse.Namespace, *, status_only: bool = False
) -> UpdateGroupRequest:
    values: dict[str, object] = {
        "class_id": args.class_id,
        "activity_id": args.activity_id,
        "group_id": args.group_id,
        "expected_snapshot_revision": args.expected_snapshot,
        "actor": workflow_actor(args),
    }
    if status_only:
        values["status"] = args.status
    else:
        for field in ("label", "status", "description", "parent_group_id"):
            value = getattr(args, field)
            if value is not None:
                values[field] = value
        if args.session_id is not None:
            values["effective_context"] = effective_context(args)
    return UpdateGroupRequest(**values)  # type: ignore[arg-type]


def _run_update(args: argparse.Namespace, *, status_only: bool = False) -> int:
    result = update_group(
        _update_request(args, status_only=status_only),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print_commit(result.commit)
    return 0


def handle_update(args: argparse.Namespace) -> int:
    return _run_update(args)


def handle_set_status(args: argparse.Namespace) -> int:
    return _run_update(args, status_only=True)


def handle_member_add(args: argparse.Namespace) -> int:
    student_ids = tuple(args.student_id)
    supplied_ids = tuple(args.membership_id or ())
    if supplied_ids and len(supplied_ids) != len(student_ids):
        raise ConcordWorkflowValidationError(
            "Repeat --membership-id exactly once per --student-id, or omit it."
        )
    context = effective_context(args)
    membership_ids = supplied_ids or tuple(
        f"membership-{uuid.uuid4().hex}" for _ in student_ids
    )
    request = AddMembershipsRequest(
        class_id=args.class_id,
        activity_id=args.activity_id,
        group_id=args.group_id,
        members=tuple(
            GroupMemberSpec(
                membership_id=membership_id,
                student_id=student_id,
                effective_context=context,
                status=args.status,
            )
            for membership_id, student_id in zip(
                membership_ids, student_ids, strict=True
            )
        ),
        expected_snapshot_revision=args.expected_snapshot,
        actor=workflow_actor(args),
    )
    result = add_memberships(
        request,
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print_commit(result.commit)
    for membership_id in result.membership_ids:
        print(f"Membership: {membership_id}")
    return 0


def handle_member_list(args: argparse.Namespace) -> int:
    items = list_memberships(
        args.class_id,
        args.activity_id,
        group_id=args.group_id,
        workspace_root=workspace_arg(args),
    )
    if not items:
        print("No Group Memberships found.")
        return 0
    for item in items:
        print_membership(item)
    return 0


def handle_member_end(args: argparse.Namespace) -> int:
    request = EndMembershipRequest(
        class_id=args.class_id,
        activity_id=args.activity_id,
        membership_id=args.membership_id,
        expected_snapshot_revision=args.expected_snapshot,
        actor=workflow_actor(args),
        status=args.status,
    )
    result = end_membership(
        request,
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print_commit(result.commit)
    return 0


def handle_member_reassign(args: argparse.Namespace) -> int:
    successor_id = args.successor_membership_id or f"membership-{uuid.uuid4().hex}"
    request = ReassignMembershipRequest(
        class_id=args.class_id,
        activity_id=args.activity_id,
        membership_id=args.membership_id,
        successor_membership_id=successor_id,
        new_group_id=args.new_group_id,
        effective_context=effective_context(args),
        expected_snapshot_revision=args.expected_snapshot,
        actor=workflow_actor(args),
        predecessor_status=args.predecessor_status,
        successor_status=args.successor_status,
    )
    result = reassign_membership(
        request,
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print_commit(result.commit)
    print(f"Membership: {result.membership_id}")
    print(f"Predecessor: {result.predecessor_membership_id}")
    return 0
