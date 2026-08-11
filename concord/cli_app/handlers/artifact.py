"""Direct Artifact Page preparation, inspection, and rendering commands."""

from __future__ import annotations

import argparse

from concord.cli_app.common import workflow_actor, workspace_arg
from concord.cli_app.output import print_commit
from concord.models import PrivacyPolicy
from concord.routing.rendering import RenderArtifactPagesRequest, render_artifact_pages
from concord.workflows.artifact_page import (
    ArtifactPagePlan,
    PrepareArtifactPagesRequest,
    list_artifact_pages,
    prepare_artifact_pages,
)


def handle_prepare(args: argparse.Namespace) -> int:
    page_ids = tuple(args.page_id or ())
    if page_ids and len(page_ids) != args.page_count:
        raise ValueError("--page-id count must equal --page-count.")
    pages = tuple(
        ArtifactPagePlan(
            page_number=index,
            artifact_page_id=page_ids[index - 1] if page_ids else None,
            page_kind="primary" if index == 1 else "continuation",
        )
        for index in range(1, args.page_count + 1)
    )
    result = prepare_artifact_pages(
        PrepareArtifactPagesRequest(
            class_id=args.class_id,
            activity_id=args.activity_id,
            artifact_instance_id=args.artifact_instance_id,
            template_version_id=args.template_version_id,
            artifact_category=args.artifact_category,
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
            pages=pages,
            expected_return_status=args.expected_return_status,
            privacy_policy=PrivacyPolicy(classification=args.privacy_classification),
            session_id=args.session_id,
            group_id=args.group_id,
        ),
        workspace_root=workspace_arg(args),
    )
    print_commit(result.commit)
    print(f"Artifact Instance: {result.artifact_instance_id}")
    print(f"Routes verified: {result.routes_verified}/{result.routes_expected}")
    for page in result.pages:
        print(
            f"{page.page_number}\t{page.artifact_page_id}\troute={page.route_id or '-'}"
        )
    return 0


def handle_list(args: argparse.Namespace) -> int:
    pages = list_artifact_pages(
        args.class_id, args.activity_id, workspace_root=workspace_arg(args)
    )
    if args.artifact_instance_id is not None:
        pages = tuple(
            page
            for page in pages
            if page.artifact_instance_id == args.artifact_instance_id
        )
    for page in pages:
        print(
            f"{page.artifact_instance_id}\t{page.page_number}\t"
            f"{page.artifact_page_id}\t{page.page_status}\t"
            f"route={page.route_id or '-'}\tsnapshot={page.snapshot_revision}"
        )
    if not pages:
        print("No Artifact Pages found.")
    return 0


def handle_show(args: argparse.Namespace) -> int:
    pages = list_artifact_pages(
        args.class_id, args.activity_id, workspace_root=workspace_arg(args)
    )
    page = next(
        (item for item in pages if item.artifact_page_id == args.artifact_page_id),
        None,
    )
    if page is None:
        raise ValueError(f"Artifact Page is unavailable: {args.artifact_page_id}")
    print(f"Artifact Instance: {page.artifact_instance_id}")
    print(f"Artifact Page: {page.artifact_page_id}")
    print(f"Page number: {page.page_number}")
    print(f"Kind: {page.page_kind}")
    print(f"Status: {page.page_status}")
    print(f"Route: {page.route_id or '-'}")
    print(f"Snapshot revision: {page.snapshot_revision}")
    return 0


def handle_render(args: argparse.Namespace) -> int:
    result = render_artifact_pages(
        RenderArtifactPagesRequest(
            class_id=args.class_id,
            activity_id=args.activity_id,
            artifact_instance_id=args.artifact_instance_id,
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
            output_relative_path=args.output,
        ),
        workspace_root=workspace_arg(args),
    )
    print_commit(result.commit)
    print(f"Rendered pages: {result.page_count}")
    print(f"Output: {result.output_path}")
    return 0


__all__ = ["handle_list", "handle_prepare", "handle_render", "handle_show"]
