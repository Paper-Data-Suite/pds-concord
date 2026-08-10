"""Direct Session commands."""

from __future__ import annotations

import argparse

from concord.cli_app.common import (
    load_command_standards_library,
    workflow_actor,
    workspace_arg,
)
from concord.cli_app.output import (
    print_commit,
    print_session_detail,
    print_session_summary,
)
from concord.workflows import (
    CreateSessionRequest,
    UpdateSessionRequest,
    create_session,
    list_sessions,
    show_session,
    update_session,
)


def handle_add(args: argparse.Namespace) -> int:
    request = CreateSessionRequest(
        class_id=args.class_id,
        activity_id=args.activity_id,
        session_id=args.session_id,
        sequence=args.sequence,
        expected_snapshot_revision=args.expected_snapshot,
        actor=workflow_actor(args),
        status=args.status,
        label=args.label,
        scheduled_start=args.scheduled_start,
        scheduled_end=args.scheduled_end,
        actual_start=args.actual_start,
        actual_end=args.actual_end,
        notes=args.notes,
    )
    result = create_session(
        request,
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print_commit(result.commit)
    return 0


def handle_list(args: argparse.Namespace) -> int:
    items = list_sessions(
        args.class_id,
        args.activity_id,
        workspace_root=workspace_arg(args),
    )
    if not items:
        print("No Sessions found.")
        return 0
    for item in items:
        print_session_summary(item)
    return 0


def handle_show(args: argparse.Namespace) -> int:
    item = show_session(
        args.class_id,
        args.activity_id,
        args.session_id,
        workspace_root=workspace_arg(args),
    )
    print_session_detail(item)
    return 0


def _update_request(
    args: argparse.Namespace, *, status_only: bool = False
) -> UpdateSessionRequest:
    values: dict[str, object] = {
        "class_id": args.class_id,
        "activity_id": args.activity_id,
        "session_id": args.session_id,
        "expected_snapshot_revision": args.expected_snapshot,
        "actor": workflow_actor(args),
    }
    if status_only:
        values["status"] = args.status
    else:
        for field in (
            "sequence",
            "status",
            "label",
            "scheduled_start",
            "scheduled_end",
            "actual_start",
            "actual_end",
            "notes",
        ):
            value = getattr(args, field)
            if value is not None:
                values[field] = value
    return UpdateSessionRequest(**values)  # type: ignore[arg-type]


def _run_update(args: argparse.Namespace, *, status_only: bool = False) -> int:
    result = update_session(
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
