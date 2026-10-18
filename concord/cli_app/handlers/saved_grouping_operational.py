"""Direct CLI preview/save of existing Session-specific operational Groups."""

from __future__ import annotations

import argparse

from concord.cli_app.common import workflow_actor, workspace_arg
from concord.workflows.class_group_arrangement_operational import (
    PreparedOperationalGroupingSave,
    SaveOperationalGroupingRequest,
    prepare_save_operational_grouping,
    save_operational_grouping,
)


def _request(args: argparse.Namespace) -> SaveOperationalGroupingRequest:
    return SaveOperationalGroupingRequest(
        class_id=args.class_id,
        activity_id=args.activity_id,
        session_id=args.session_id,
        arrangement_id=args.arrangement_id,
        name=args.name,
        expected_snapshot_revision=args.expected_snapshot,
        actor=workflow_actor(args),
        acknowledge_unresolved=args.acknowledge_unresolved,
    )


def _print_review(
    preview: PreparedOperationalGroupingSave, *, show_members: bool
) -> None:
    print(f"Saved grouping name: {preview.name}")
    print(f"Grouping ID: {preview.arrangement_id}")
    print(f"Source Activity: {preview.source_activity_id}")
    print(f"Source Session: {preview.source_session_id}")
    print(f"Source snapshot: {preview.source_snapshot_revision}")
    print(f"Groups: {len(preview.groups)}")
    print(f"Assigned: {preview.assigned_count}")
    print(f"Unassigned: {len(preview.unresolved_student_ids)}")
    for group in preview.groups:
        print(f"  {group.label}: {len(group.student_ids)} students")
        if show_members:
            for student_id in group.student_ids:
                print(f"    Student ID: {student_id}")
    if show_members:
        for student_id in preview.unresolved_student_ids:
            print(f"    Unassigned student ID: {student_id}")
    if preview.unresolved_student_ids:
        print("Saving requires --acknowledge-unresolved.")
    print(f"Review digest: {preview.review_digest}")
    print("Writes: none")


def handle_save_groups_preview(args: argparse.Namespace) -> int:
    preview = prepare_save_operational_grouping(
        _request(args), workspace_root=workspace_arg(args)
    )
    _print_review(preview, show_members=args.show_members)
    return 0


def handle_save_groups(args: argparse.Namespace) -> int:
    saved = save_operational_grouping(
        _request(args),
        review_digest=args.review_digest,
        workspace_root=workspace_arg(args),
    )
    print(f"Saved grouping: {saved.revision.name}")
    print(f"Grouping ID: {saved.revision.arrangement_id}")
    print(f"Revision: {saved.revision.revision}")
    print(f"SHA-256: {saved.sha256}")
    print("Source Activity and canonical Groups unchanged: yes")
    return 0


__all__ = ["handle_save_groups", "handle_save_groups_preview"]
