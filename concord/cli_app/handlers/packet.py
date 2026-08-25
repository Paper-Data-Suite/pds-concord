"""Direct noninteractive reusable Packet commands."""

from __future__ import annotations

import argparse
from pathlib import Path

from concord.cli_app.common import workflow_actor, workspace_arg
from concord.models import PacketComponent, PacketVersion
from concord.workflows.errors import (
    ConcordWorkflowNotFoundError,
    ConcordWorkflowValidationError,
)
from concord.workflows.packet import (
    PacketDetail,
    PacketMutationResult,
    PreparePacketActivationRequest,
    PreparePacketCreateRequest,
    PreparePacketRetireRequest,
    PreparePacketRetireVersionRequest,
    PreparePacketRevisionRequest,
    PreparePacketUpdateRequest,
    commit_packet_activation,
    commit_packet_create,
    commit_packet_retire,
    commit_packet_retire_version,
    commit_packet_revision,
    commit_packet_update,
    get_packet,
    list_packets,
    prepare_packet_activation,
    prepare_packet_create,
    prepare_packet_retire,
    prepare_packet_retire_version,
    prepare_packet_revision,
    prepare_packet_update,
)


def _print_result(result: PacketMutationResult) -> None:
    print(f"Packet: {result.packet_definition_id}")
    print(f"Status: {result.status}")
    print(f"Snapshot: {result.snapshot_revision}")
    print(f"Snapshot SHA-256: {result.snapshot_sha256}")
    print(f"Current Version: {result.current_packet_version_id or '-'}")
    print(f"Head Version: {result.head_packet_version_id}")
    if result.workspace_created:
        print("Workspace created: yes")


def _component_description(component: PacketComponent) -> str:
    if component.component_kind == "concord_template":
        source = f"template={component.template_id}:{component.template_version_id}"
    else:
        reference = component.external_reference
        assert reference is not None
        source = (
            f"external={reference.module_id}:"
            f"{reference.record_kind}:{reference.record_id}"
        )
        if reference.contract_version is not None:
            source += f"@{reference.contract_version}"
    audience = component.audience_intent.audience_kind
    if component.audience_intent.role_keys:
        audience += f"[{','.join(component.audience_intent.role_keys)}]"
    condition = (
        component.condition.condition_kind
        if component.condition is not None
        else "-"
    )
    return (
        f"{component.sequence}. {component.packet_component_id} "
        f"[{component.component_kind}] {source}; "
        f"copies={component.copies_per_target}; audience={audience}; "
        f"requirement={component.requirement_level}; condition={condition}"
    )


def _find_version(detail: PacketDetail, version_id: str) -> PacketVersion:
    match = next(
        (
            item
            for item in detail.versions
            if item.packet_version_id == version_id
        ),
        None,
    )
    if match is None:
        raise ConcordWorkflowNotFoundError(
            f"Packet Version is not available: {version_id}"
        )
    return match


def _print_detail(detail: PacketDetail) -> None:
    summary = detail.summary
    definition = detail.definition
    print(f"Packet: {summary.packet_definition_id}")
    print(f"Name: {summary.name}")
    print(f"Purpose: {definition.purpose}")
    print(f"Status: {summary.status}")
    print(f"Current Version: {summary.current_packet_version_id or '-'}")
    print(f"Head Version: {summary.head_packet_version_id}")
    print(f"Snapshot: {summary.snapshot_revision}")
    print(f"Versions: {len(detail.versions)}")
    print(f"Head Components: {summary.component_count}")
    if definition.description is not None:
        print(f"Description: {definition.description}")


def _print_version(detail: PacketDetail, version_id: str) -> None:
    version = _find_version(detail, version_id)
    print(f"Packet: {version.packet_definition_id}")
    print(f"Packet Version: {version.packet_version_id}")
    print(f"Version Label: {version.version_label}")
    print(f"Revision Sequence: {version.revision_sequence}")
    print(f"Status: {version.status}")
    print(f"Components: {len(version.components)}")
    print(
        "Preserve Component Order: "
        f"{'yes' if version.rendering_rules.preserve_component_order else 'no'}"
    )
    print(
        "Start Each Component On New Page: "
        f"{'yes' if version.rendering_rules.start_each_component_on_new_page else 'no'}"
    )
    print(f"Copy Collation: {version.rendering_rules.copy_collation}")
    print(f"Target Order: {version.rendering_rules.target_order}")
    print(f"Supersedes: {version.supersedes_packet_version_id or '-'}")
    for component in version.components:
        print(f"Component: {_component_description(component)}")


def handle_list(args: argparse.Namespace) -> int:
    items = list_packets(workspace_root=workspace_arg(args))
    if not items:
        print("No reusable Concord Packets found.")
        return 0
    for item in items:
        print(
            f"{item.packet_definition_id}: {item.name} [{item.status}] "
            f"current={item.current_packet_version_id or '-'} "
            f"head={item.head_packet_version_id} "
            f"components={item.component_count} snapshot={item.snapshot_revision}"
        )
    return 0


def handle_show(args: argparse.Namespace) -> int:
    _print_detail(
        get_packet(
            args.packet_definition_id,
            workspace_root=workspace_arg(args),
        )
    )
    return 0


def handle_version_list(args: argparse.Namespace) -> int:
    detail = get_packet(
        args.packet_definition_id,
        workspace_root=workspace_arg(args),
    )
    for version in detail.versions:
        labels: list[str] = []
        if version.packet_version_id == detail.summary.current_packet_version_id:
            labels.append("current")
        if version.packet_version_id == detail.summary.head_packet_version_id:
            labels.append("head")
        marker = f" ({', '.join(labels)})" if labels else ""
        print(
            f"{version.revision_sequence}: {version.packet_version_id} "
            f"[{version.status}] {version.version_label} "
            f"components={len(version.components)}{marker}"
        )
    return 0


def handle_version_show(args: argparse.Namespace) -> int:
    detail = get_packet(
        args.packet_definition_id,
        workspace_root=workspace_arg(args),
    )
    _print_version(detail, args.packet_version_id)
    return 0


def handle_create(args: argparse.Namespace) -> int:
    prepared = prepare_packet_create(
        PreparePacketCreateRequest(
            packet_definition_id=args.packet_definition_id,
            packet_version_id=args.packet_version_id,
            authoring_file=Path(args.authoring_file),
            actor=workflow_actor(args),
            activate=args.activate,
        ),
        workspace_root=workspace_arg(args),
    )
    _print_result(
        commit_packet_create(
            prepared,
            workspace_root=workspace_arg(args),
        )
    )
    return 0


def handle_revise(args: argparse.Namespace) -> int:
    prepared = prepare_packet_revision(
        PreparePacketRevisionRequest(
            packet_definition_id=args.packet_definition_id,
            packet_version_id=args.packet_version_id,
            authoring_file=Path(args.authoring_file),
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
        ),
        workspace_root=workspace_arg(args),
    )
    _print_result(
        commit_packet_revision(
            prepared,
            workspace_root=workspace_arg(args),
        )
    )
    return 0


def handle_activate(args: argparse.Namespace) -> int:
    prepared = prepare_packet_activation(
        PreparePacketActivationRequest(
            packet_definition_id=args.packet_definition_id,
            packet_version_id=args.packet_version_id,
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
        ),
        workspace_root=workspace_arg(args),
    )
    _print_result(
        commit_packet_activation(
            prepared,
            workspace_root=workspace_arg(args),
        )
    )
    return 0


def handle_update(args: argparse.Namespace) -> int:
    detail = get_packet(
        args.packet_definition_id,
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
            "Packet update requires at least one metadata change."
        )
    description = definition.description
    if args.clear_description:
        description = None
    elif args.description is not None:
        description = args.description
    prepared = prepare_packet_update(
        PreparePacketUpdateRequest(
            packet_definition_id=args.packet_definition_id,
            name=args.name if args.name is not None else definition.name,
            purpose=args.purpose if args.purpose is not None else definition.purpose,
            description=description,
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
        ),
        workspace_root=workspace_arg(args),
    )
    _print_result(
        commit_packet_update(
            prepared,
            workspace_root=workspace_arg(args),
        )
    )
    return 0


def handle_retire_version(args: argparse.Namespace) -> int:
    prepared = prepare_packet_retire_version(
        PreparePacketRetireVersionRequest(
            packet_definition_id=args.packet_definition_id,
            packet_version_id=args.packet_version_id,
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
        ),
        workspace_root=workspace_arg(args),
    )
    _print_result(
        commit_packet_retire_version(
            prepared,
            workspace_root=workspace_arg(args),
        )
    )
    return 0


def handle_retire(args: argparse.Namespace) -> int:
    prepared = prepare_packet_retire(
        PreparePacketRetireRequest(
            packet_definition_id=args.packet_definition_id,
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
        ),
        workspace_root=workspace_arg(args),
    )
    _print_result(
        commit_packet_retire(
            prepared,
            workspace_root=workspace_arg(args),
        )
    )
    return 0
