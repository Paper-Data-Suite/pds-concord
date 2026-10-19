"""Scriptable history and reviewed immutable saved-grouping revisions (#136)."""

from __future__ import annotations

import argparse
from pathlib import Path

from concord.class_group_arrangement_storage import list_arrangement_history
from concord.cli_app.common import workflow_actor, workspace_arg
from concord.workflows.class_group_arrangement_revision import (
    ChangeGroupingRequest,
    PreparedGroupingChange,
    change_grouping,
    prepare_grouping_change,
)
from concord.workflows.context import require_core_class, resolve_read_workspace_root
from concord.workflows.errors import ConcordWorkflowNotFoundError


def _root_and_year(args: argparse.Namespace) -> tuple[Path, str]:
    root = resolve_read_workspace_root(workspace_arg(args))
    if root is None:
        raise ConcordWorkflowNotFoundError("Paper Data Suite workspace does not exist.")
    metadata = require_core_class(root, args.class_id)
    return root, metadata.school_year


def handle_history(args: argparse.Namespace) -> int:
    root, year = _root_and_year(args)
    revisions = list_arrangement_history(
        root,
        class_id=args.class_id,
        school_year=year,
        arrangement_id=args.arrangement_id,
        actor_id=workflow_actor(args).actor_id,
    )
    for item in revisions:
        r = item.revision
        print(
            f"revision={r.revision}\tname={r.name}\tstatus={r.status}\t"
            f"groups={len(r.groups)}\t"
            f"assigned={sum(len(group.student_ids) for group in r.groups)}\t"
            f"unresolved={len(r.unresolved_student_ids)}\tsha256={item.sha256}"
        )
    print("Historical revisions: immutable; writes: none")
    return 0


def _request(args: argparse.Namespace) -> ChangeGroupingRequest:
    return ChangeGroupingRequest(
        class_id=args.class_id,
        arrangement_id=args.arrangement_id,
        expected_revision=args.expected_revision,
        expected_sha256=args.expected_sha256,
        actor=workflow_actor(args),
        action=args.action.replace("-", "_"),
        new_name=args.new_name,
        source_activity_id=args.source_activity_id,
        source_group_plan_id=args.source_group_plan_id,
        expected_source_snapshot_revision=args.expected_source_snapshot,
    )


def _show(preview: PreparedGroupingChange) -> None:
    print(f"Grouping ID: {preview.arrangement_id}")
    print(f"Action: {preview.action}")
    print(f"Revision: {preview.previous_revision} -> {preview.new_revision}")
    print(f"Name: {preview.name}")
    print(f"Status: {preview.status}")
    print(f"Groups: {len(preview.groups)}")
    print(f"Assigned: {preview.assigned_count}")
    print(f"Unresolved: {len(preview.unresolved_student_ids)}")
    for group in preview.groups:
        print(f"  {group.label}: {len(group.student_ids)} students")
    print(f"Review digest: {preview.review_digest}")
    print("Changes to prior Activity Groups/Memberships/Scores: none")
    print("Writes: none")


def handle_change_preview(args: argparse.Namespace) -> int:
    preview = prepare_grouping_change(
        _request(args), workspace_root=workspace_arg(args)
    )
    _show(preview)
    return 0


def handle_change(args: argparse.Namespace) -> int:
    saved = change_grouping(
        _request(args),
        review_digest=args.review_digest,
        workspace_root=workspace_arg(args),
    )
    print(f"Grouping ID: {saved.revision.arrangement_id}")
    print(f"Name: {saved.revision.name}")
    print(f"Current revision: {saved.revision.revision}")
    print(f"Status: {saved.revision.status}")
    print(f"SHA-256: {saved.sha256}")
    print("Prior revisions and Activity operational state unchanged: yes")
    return 0
