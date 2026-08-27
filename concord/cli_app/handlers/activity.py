"""Direct Activity commands."""

from __future__ import annotations

import argparse

from concord.cli_app.common import (
    load_command_standards_library,
    workflow_actor,
    workspace_arg,
)
from concord.cli_app.output import (
    print_activity_copy_preview,
    print_activity_detail,
    print_activity_summary,
    print_commit,
)
from concord.workflows import (
    CopyActivityRequest,
    CreateActivityContextRequest,
    PrepareActivityCopyRequest,
    UpdateActivityRequest,
    copy_activity,
    create_activity_context,
    list_activities,
    prepare_activity_copy,
    show_activity,
    update_activity,
)
from concord.workflows.models import UNSET, OptionalTextUpdate, TextUpdate


def handle_create(args: argparse.Namespace) -> int:
    request = CreateActivityContextRequest(
        class_id=args.class_id,
        activity_id=args.activity_id,
        title=args.title,
        activity_type=args.activity_type,
        scoring_orientation=args.scoring_orientation,
        session_id=args.session_id,
        actor=workflow_actor(args),
        activity_status=args.status,
        session_sequence=args.session_sequence,
        session_status=args.session_status,
        description=args.description,
        standards_profile_id=args.standards_profile_id,
        focus_standard_ids=tuple(args.focus_standard_id or ()),
        external_reference_ids=tuple(args.external_reference_id or ()),
        session_label=args.session_label,
        scheduled_start=args.scheduled_start,
        scheduled_end=args.scheduled_end,
        session_notes=args.session_notes,
    )
    result = create_activity_context(
        request,
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print_commit(result.commit)
    print(f"First Session: {result.first_session_id}")
    return 0


def _prepare_copy_request(args: argparse.Namespace) -> PrepareActivityCopyRequest:
    title: TextUpdate = UNSET if args.title is None else args.title
    description: OptionalTextUpdate
    if args.clear_description:
        description = None
    elif args.description is not None:
        description = args.description
    else:
        description = UNSET
    return PrepareActivityCopyRequest(
        source_class_id=args.source_class_id,
        source_activity_id=args.source_activity_id,
        target_class_id=args.target_class_id,
        target_activity_id=args.target_activity_id,
        first_session_id=args.session_id,
        first_session_label=args.session_label,
        title=title,
        description=description,
    )


def handle_copy_preview(args: argparse.Namespace) -> int:
    # Actor context is required and structurally validated for parity with the
    # eventual write, but is intentionally absent from the semantic review digest.
    workflow_actor(args)
    prepared = prepare_activity_copy(
        _prepare_copy_request(args),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print_activity_copy_preview(prepared)
    return 0


def handle_copy(args: argparse.Namespace) -> int:
    prepared_request = _prepare_copy_request(args)
    result = copy_activity(
        CopyActivityRequest(
            source_class_id=prepared_request.source_class_id,
            source_activity_id=prepared_request.source_activity_id,
            target_class_id=prepared_request.target_class_id,
            target_activity_id=prepared_request.target_activity_id,
            first_session_id=prepared_request.first_session_id,
            actor=workflow_actor(args),
            review_digest=args.review_digest,
            title=prepared_request.title,
            description=prepared_request.description,
            first_session_label=prepared_request.first_session_label,
        ),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print_commit(result.commit)
    print(f"First Session: {result.first_session_id}")
    print(f"Review digest: {result.review_digest}")
    return 0


def handle_list(args: argparse.Namespace) -> int:
    items = list_activities(
        workspace_root=workspace_arg(args),
        class_id=args.class_id,
    )
    if not items:
        print("No Concord Activities found.")
        return 0
    for item in items:
        print_activity_summary(item)
    return 0


def handle_show(args: argparse.Namespace) -> int:
    detail = show_activity(
        args.class_id,
        args.activity_id,
        workspace_root=workspace_arg(args),
    )
    print_activity_detail(detail)
    return 0


def _update_request(
    args: argparse.Namespace, *, status_only: bool = False
) -> UpdateActivityRequest:
    values: dict[str, object] = {
        "class_id": args.class_id,
        "activity_id": args.activity_id,
        "expected_snapshot_revision": args.expected_snapshot,
        "actor": workflow_actor(args),
    }
    if status_only:
        values["status"] = args.status
    else:
        for source, target in (
            ("title", "title"),
            ("description", "description"),
            ("activity_type", "activity_type"),
            ("scoring_orientation", "scoring_orientation"),
            ("standards_profile_id", "standards_profile_id"),
            ("status", "status"),
        ):
            value = getattr(args, source)
            if value is not None:
                values[target] = value
        if args.focus_standard_id is not None:
            values["focus_standard_ids"] = tuple(args.focus_standard_id)
        if args.external_reference_id is not None:
            values["external_reference_ids"] = tuple(args.external_reference_id)
    return UpdateActivityRequest(**values)  # type: ignore[arg-type]


def _run_update(args: argparse.Namespace, *, status_only: bool = False) -> int:
    result = update_activity(
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
