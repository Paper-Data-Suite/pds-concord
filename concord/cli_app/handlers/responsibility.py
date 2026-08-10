"""Direct Responsibility Assignment commands."""

from __future__ import annotations

import argparse

from concord.cli_app.common import (
    effective_context,
    group_assignee,
    load_command_standards_library,
    student_participant,
    workflow_actor,
    workspace_arg,
)
from concord.cli_app.output import print_commit, print_responsibility
from concord.models import ConcordRecordReference, ParticipantReference
from concord.workflows import (
    AssignResponsibilityRequest,
    EndResponsibilityRequest,
    ReassignResponsibilityRequest,
    assign_responsibility,
    end_responsibility,
    list_responsibilities,
    reassign_responsibility,
)


def _assignee(
    args: argparse.Namespace,
) -> ParticipantReference | ConcordRecordReference:
    if args.group_assignee_id is not None:
        return group_assignee(args.group_assignee_id)
    return student_participant(args)


def handle_assign(args: argparse.Namespace) -> int:
    request = AssignResponsibilityRequest(
        class_id=args.class_id,
        activity_id=args.activity_id,
        responsibility_assignment_id=args.responsibility_assignment_id,
        assignee_reference=_assignee(args),
        description=args.description,
        effective_context=effective_context(args),
        expected_snapshot_revision=args.expected_snapshot,
        actor=workflow_actor(args),
        status=args.status,
        group_id=args.group_id,
        work_item_id=args.work_item_id,
        expected_output=args.expected_output,
    )
    result = assign_responsibility(
        request,
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print_commit(result.commit)
    return 0


def handle_list(args: argparse.Namespace) -> int:
    items = list_responsibilities(
        args.class_id,
        args.activity_id,
        group_id=args.group_id,
        workspace_root=workspace_arg(args),
    )
    if not items:
        print("No Responsibility Assignments found.")
        return 0
    for item in items:
        print_responsibility(item)
    return 0


def handle_end(args: argparse.Namespace) -> int:
    request = EndResponsibilityRequest(
        class_id=args.class_id,
        activity_id=args.activity_id,
        responsibility_assignment_id=args.responsibility_assignment_id,
        expected_snapshot_revision=args.expected_snapshot,
        actor=workflow_actor(args),
        status=args.status,
    )
    result = end_responsibility(
        request,
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print_commit(result.commit)
    return 0


def handle_reassign(args: argparse.Namespace) -> int:
    request = ReassignResponsibilityRequest(
        class_id=args.class_id,
        activity_id=args.activity_id,
        responsibility_assignment_id=args.responsibility_assignment_id,
        successor_responsibility_assignment_id=(
            args.successor_responsibility_assignment_id
        ),
        assignee_reference=_assignee(args),
        description=args.description,
        effective_context=effective_context(args),
        expected_snapshot_revision=args.expected_snapshot,
        actor=workflow_actor(args),
        group_id=args.group_id,
        work_item_id=args.work_item_id,
        expected_output=args.expected_output,
        predecessor_status=args.predecessor_status,
        successor_status=args.successor_status,
    )
    result = reassign_responsibility(
        request,
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print_commit(result.commit)
    print(f"Responsibility: {result.responsibility_assignment_id}")
    print(f"Predecessor: {result.predecessor_responsibility_assignment_id}")
    return 0
