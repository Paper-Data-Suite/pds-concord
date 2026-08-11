"""Direct scan intake and routing-review commands."""

from __future__ import annotations

import argparse

from pds_core.routing_models import PDS2_SCHEMA, ModuleWorkRef, RouteLocator

from concord.cli_app.common import workflow_actor, workspace_arg
from concord.routing.review import (
    defer_routing_failure,
    list_routing_failures,
    resolve_routing_failure_with_route,
    show_routing_failure,
)
from concord.routing.scan_intake import route_scan_sources


def handle_route(args: argparse.Namespace) -> int:
    result = route_scan_sources(args.source, workspace_root=workspace_arg(args))
    for source in result.sources:
        if source.source_error is not None:
            print(f"ERROR\t{source.source_path.name}\t{source.source_error}")
        for page in source.pages:
            print(
                f"{page.status.upper()}\t{source.source_path.name}\t"
                f"page={page.source_page_number}\t"
                f"failure={page.failure_id or '-'}"
            )
    print(f"Dispatched: {result.dispatched_count}")
    print(f"Review required: {result.failure_count}")
    return (
        1
        if result.failure_count or any(item.source_error for item in result.sources)
        else 0
    )


def handle_review_list(args: argparse.Namespace) -> int:
    items = list_routing_failures(
        workspace_root=workspace_arg(args), activity_id=args.activity_id
    )
    for item in items:
        print(
            f"{item.failure_id}\t{item.category}\t"
            f"page={item.source_page_number or '-'}\t"
            f"status={item.latest_status or 'unresolved'}\t{item.source_filename}"
        )
    if not items:
        print("No routing failures found.")
    return 0


def handle_review_show(args: argparse.Namespace) -> int:
    item = show_routing_failure(args.failure_id, workspace_root=workspace_arg(args))
    print(f"Failure: {item.failure_id}")
    print(f"Category: {item.failure_category}")
    print(f"Stage: {item.stage}")
    print(f"Source: {item.source_filename}")
    print(f"Physical page: {item.source_page_number or '-'}")
    print(f"Message: {item.failure_message}")
    return 0


def handle_review_resolve(args: argparse.Namespace) -> int:
    route_values = (args.class_id, args.work_id, args.route_id)
    if args.defer and any(value is not None for value in route_values):
        args.command_parser.error(
            "--defer cannot be combined with --class-id, --work-id, or --route-id"
        )
    if not args.defer and any(value is None for value in route_values):
        args.command_parser.error(
            "route resolution requires --class-id, --work-id, and --route-id"
        )
    if args.defer:
        result = defer_routing_failure(
            args.failure_id,
            message=args.message,
            workspace_root=workspace_arg(args),
            reviewer=workflow_actor(args),
        )
    else:
        assert args.class_id is not None
        assert args.work_id is not None
        assert args.route_id is not None
        locator = RouteLocator(
            PDS2_SCHEMA,
            ModuleWorkRef(args.module_id, args.class_id, args.work_id),
            args.route_id,
        )
        result = resolve_routing_failure_with_route(
            args.failure_id,
            locator,
            message=args.message,
            workspace_root=workspace_arg(args),
            reviewer=workflow_actor(args),
        )
    print(f"Resolution: {result.resolution_id}")
    print(f"Status: {result.resolution_status}")
    print(f"Action: {result.resolution_action}")
    return 0


__all__ = [
    "handle_review_list",
    "handle_review_resolve",
    "handle_review_show",
    "handle_route",
]
