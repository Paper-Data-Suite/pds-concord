"""Direct noninteractive packaged starter Template commands."""

from __future__ import annotations

import argparse

from concord.cli_app.common import workflow_actor, workspace_arg
from concord.starter_templates.catalog import get_starter_template
from concord.workflows.starter_template import (
    PrepareStarterTemplateInstallAllRequest,
    PrepareStarterTemplateInstallRequest,
    StarterTemplateInstallAllResult,
    StarterTemplateInstallResult,
    commit_starter_template_install,
    commit_starter_template_install_all,
    get_starter_template_status,
    list_starter_template_statuses,
    prepare_starter_template_install,
    prepare_starter_template_install_all,
)


def _print_install_result(result: StarterTemplateInstallResult) -> None:
    print(f"Starter: {result.starter_key}")
    print(f"Template: {result.template_id}")
    print(f"Template Version: {result.template_version_id}")
    print(f"Outcome: {result.outcome}")
    print(f"Snapshot: {result.snapshot_revision}")
    print(f"Snapshot SHA-256: {result.snapshot_sha256}")
    if result.workspace_created:
        print("Workspace created: yes")


def _print_install_all_result(result: StarterTemplateInstallAllResult) -> None:
    print(f"Installed: {result.installed_count}")
    print(f"Already installed: {result.already_installed_count}")
    print(f"Processed: {len(result.results)}")
    for item in result.results:
        print(
            f"{item.starter_key}: {item.outcome} "
            f"template={item.template_id} "
            f"version={item.template_version_id}"
        )


def handle_starter_list(args: argparse.Namespace) -> int:
    items = list_starter_template_statuses(
        workspace_root=workspace_arg(args)
    )
    for item in items:
        print(
            f"{item.starter_key}: {item.display_name} "
            f"[{item.family}] "
            f"{item.page_count} page(s) {item.orientation} "
            f"status={item.installation_state}"
        )
    return 0


def handle_starter_show(args: argparse.Namespace) -> int:
    entry = get_starter_template(args.starter_key)
    status = get_starter_template_status(
        args.starter_key,
        workspace_root=workspace_arg(args),
    )
    print(f"Starter: {entry.starter_key}")
    print(f"Name: {entry.display_name}")
    print(f"Family: {entry.family}")
    print(f"Purpose: {entry.purpose}")
    print(f"Description: {entry.description}")
    print(f"Template: {entry.template_id}")
    print(f"Template Version: {entry.template_version_id}")
    print(f"Artifact Category: {entry.artifact_category}")
    print(f"Pages: {entry.page_count}")
    print(f"Orientation: {entry.orientation}")
    print("Expected Return: returned_expected")
    print(f"Privacy: {entry.default_privacy_classification}")
    print(
        "Audience: "
        + ", ".join(entry.suggested_audience_kinds)
    )
    print(
        "Activity Types: "
        + (
            ", ".join(entry.suggested_activity_type_keys)
            if entry.suggested_activity_type_keys
            else "-"
        )
    )
    print(f"Authorship: {entry.default_authorship_mode}")
    print(f"Subject: {entry.default_subject_kind}")
    print(f"Rendering Contract: {entry.layout().schema_version}")
    print(
        "Rendering Reference: "
        f"{entry.rendering_specification_reference}"
    )
    print(f"Rendering SHA-256: {entry.rendering_sha256()}")
    print(f"Installation State: {status.installation_state}")
    return 0


def handle_starter_install(args: argparse.Namespace) -> int:
    prepared = prepare_starter_template_install(
        PrepareStarterTemplateInstallRequest(
            starter_key=args.starter_key,
            actor=workflow_actor(args),
        ),
        workspace_root=workspace_arg(args),
    )
    result = commit_starter_template_install(
        prepared,
        workspace_root=workspace_arg(args),
    )
    _print_install_result(result)
    return 0


def handle_starter_install_all(args: argparse.Namespace) -> int:
    prepared = prepare_starter_template_install_all(
        PrepareStarterTemplateInstallAllRequest(
            actor=workflow_actor(args),
        ),
        workspace_root=workspace_arg(args),
    )
    result = commit_starter_template_install_all(
        prepared,
        workspace_root=workspace_arg(args),
    )
    _print_install_all_result(result)
    return 0


__all__ = [
    "handle_starter_install",
    "handle_starter_install_all",
    "handle_starter_list",
    "handle_starter_show",
]
