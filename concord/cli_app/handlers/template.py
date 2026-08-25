"""Direct noninteractive reusable Template commands."""

from __future__ import annotations

import argparse
from pathlib import Path

from concord.cli_app.common import workflow_actor, workspace_arg
from concord.workflows.errors import (
    ConcordWorkflowNotFoundError,
    ConcordWorkflowValidationError,
)
from concord.workflows.template import (
    PrepareTemplateActivationRequest,
    PrepareTemplateCreateRequest,
    PrepareTemplateRetireRequest,
    PrepareTemplateRetireVersionRequest,
    PrepareTemplateRevisionRequest,
    PrepareTemplateUpdateRequest,
    TemplateDetail,
    TemplateMutationResult,
    commit_template_activation,
    commit_template_create,
    commit_template_retire,
    commit_template_retire_version,
    commit_template_revision,
    commit_template_update,
    get_template,
    list_templates,
    prepare_template_activation,
    prepare_template_create,
    prepare_template_retire,
    prepare_template_retire_version,
    prepare_template_revision,
    prepare_template_update,
)


def _print_result(result: TemplateMutationResult) -> None:
    print(f"Template: {result.template_id}")
    print(f"Status: {result.status}")
    print(f"Snapshot: {result.snapshot_revision}")
    print(f"Snapshot SHA-256: {result.snapshot_sha256}")
    print(
        "Current Version: "
        f"{result.current_template_version_id or '-'}"
    )
    print(f"Head Version: {result.head_template_version_id}")
    if result.workspace_created:
        print("Workspace created: yes")


def _print_detail(detail: TemplateDetail) -> None:
    summary = detail.summary
    definition = detail.definition
    print(f"Template: {summary.template_id}")
    print(f"Name: {summary.name}")
    print(f"Purpose: {definition.purpose}")
    print(f"Status: {summary.status}")
    print(f"Artifact Category: {summary.artifact_category}")
    print(
        "Current Version: "
        f"{summary.current_template_version_id or '-'}"
    )
    print(f"Head Version: {summary.head_template_version_id}")
    print(f"Snapshot: {summary.snapshot_revision}")
    print(f"Versions: {len(detail.versions)}")
    if definition.description is not None:
        print(f"Description: {definition.description}")


def _print_version(detail: TemplateDetail, version_id: str) -> None:
    version = next(
        (
            item
            for item in detail.versions
            if item.template_version_id == version_id
        ),
        None,
    )
    if version is None:
        raise ConcordWorkflowNotFoundError(
            f"Template Version is not available: {version_id}"
        )
    print(f"Template: {version.template_id}")
    print(f"Template Version: {version.template_version_id}")
    print(f"Version Label: {version.version_label}")
    print(f"Revision Sequence: {version.revision_sequence}")
    print(f"Status: {version.status}")
    print(f"Artifact Category: {version.artifact_category}")
    print(f"Pages: {len(version.page_manifest)}")
    print(
        "Expected Return: "
        f"{version.default_expected_return_status}"
    )
    print(
        "Privacy: "
        f"{version.default_privacy_policy.classification}"
    )
    print(
        "Rendering Contract: "
        f"{version.rendering_contract_version}"
    )
    print(
        "Rendering Reference: "
        f"{version.rendering_specification_reference}"
    )
    print(
        "Rendering SHA-256: "
        f"{version.rendering_specification_sha256}"
    )
    print(
        "Supersedes: "
        f"{version.supersedes_template_version_id or '-'}"
    )


def handle_list(args: argparse.Namespace) -> int:
    items = list_templates(workspace_root=workspace_arg(args))
    if not items:
        print("No reusable Concord Templates found.")
        return 0
    for item in items:
        print(
            f"{item.template_id}: {item.name} "
            f"[{item.status}] "
            f"current={item.current_template_version_id or '-'} "
            f"head={item.head_template_version_id} "
            f"snapshot={item.snapshot_revision}"
        )
    return 0


def handle_show(args: argparse.Namespace) -> int:
    _print_detail(
        get_template(
            args.template_id,
            workspace_root=workspace_arg(args),
        )
    )
    return 0


def handle_version_list(args: argparse.Namespace) -> int:
    detail = get_template(
        args.template_id,
        workspace_root=workspace_arg(args),
    )
    for version in detail.versions:
        labels: list[str] = []
        if (
            version.template_version_id
            == detail.summary.current_template_version_id
        ):
            labels.append("current")
        if (
            version.template_version_id
            == detail.summary.head_template_version_id
        ):
            labels.append("head")
        marker = f" ({', '.join(labels)})" if labels else ""
        print(
            f"{version.revision_sequence}: "
            f"{version.template_version_id} "
            f"[{version.status}] "
            f"{version.version_label}{marker}"
        )
    return 0


def handle_version_show(args: argparse.Namespace) -> int:
    detail = get_template(
        args.template_id,
        workspace_root=workspace_arg(args),
    )
    _print_version(detail, args.template_version_id)
    return 0


def handle_create(args: argparse.Namespace) -> int:
    prepared = prepare_template_create(
        PrepareTemplateCreateRequest(
            template_id=args.template_id,
            template_version_id=args.template_version_id,
            authoring_file=Path(args.authoring_file),
            rendering_specification=Path(args.rendering_spec),
            actor=workflow_actor(args),
            activate=args.activate,
        ),
        workspace_root=workspace_arg(args),
    )
    _print_result(
        commit_template_create(
            prepared,
            workspace_root=workspace_arg(args),
        )
    )
    return 0


def handle_revise(args: argparse.Namespace) -> int:
    prepared = prepare_template_revision(
        PrepareTemplateRevisionRequest(
            template_id=args.template_id,
            template_version_id=args.template_version_id,
            authoring_file=Path(args.authoring_file),
            rendering_specification=Path(args.rendering_spec),
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
        ),
        workspace_root=workspace_arg(args),
    )
    _print_result(
        commit_template_revision(
            prepared,
            workspace_root=workspace_arg(args),
        )
    )
    return 0


def handle_activate(args: argparse.Namespace) -> int:
    prepared = prepare_template_activation(
        PrepareTemplateActivationRequest(
            template_id=args.template_id,
            template_version_id=args.template_version_id,
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
        ),
        workspace_root=workspace_arg(args),
    )
    _print_result(
        commit_template_activation(
            prepared,
            workspace_root=workspace_arg(args),
        )
    )
    return 0


def handle_update(args: argparse.Namespace) -> int:
    detail = get_template(
        args.template_id,
        workspace_root=workspace_arg(args),
    )
    definition = detail.definition
    if (
        args.name is None
        and args.purpose is None
        and args.description is None
        and not args.clear_description
    ):
        raise ConcordWorkflowValidationError(
            "Template update requires at least one metadata change."
        )
    description = definition.description
    if args.clear_description:
        description = None
    elif args.description is not None:
        description = args.description
    prepared = prepare_template_update(
        PrepareTemplateUpdateRequest(
            template_id=args.template_id,
            name=args.name if args.name is not None else definition.name,
            purpose=(
                args.purpose
                if args.purpose is not None
                else definition.purpose
            ),
            description=description,
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
        ),
        workspace_root=workspace_arg(args),
    )
    _print_result(
        commit_template_update(
            prepared,
            workspace_root=workspace_arg(args),
        )
    )
    return 0


def handle_retire_version(args: argparse.Namespace) -> int:
    prepared = prepare_template_retire_version(
        PrepareTemplateRetireVersionRequest(
            template_id=args.template_id,
            template_version_id=args.template_version_id,
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
        ),
        workspace_root=workspace_arg(args),
    )
    _print_result(
        commit_template_retire_version(
            prepared,
            workspace_root=workspace_arg(args),
        )
    )
    return 0


def handle_retire(args: argparse.Namespace) -> int:
    prepared = prepare_template_retire(
        PrepareTemplateRetireRequest(
            template_id=args.template_id,
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
        ),
        workspace_root=workspace_arg(args),
    )
    _print_result(
        commit_template_retire(
            prepared,
            workspace_root=workspace_arg(args),
        )
    )
    return 0
