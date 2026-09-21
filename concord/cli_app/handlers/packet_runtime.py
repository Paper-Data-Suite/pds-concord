"Direct noninteractive Activity-specific Packet generation commands."

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import cast

from concord.cli_app.common import workflow_actor, workspace_arg
from concord.models import ParticipantReference, SubjectReference
from concord.workflows.context import resolve_read_workspace_root
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowValidationError,
)
from concord.workflows.group import show_group
from concord.workflows.packet_instance import (
    PacketInstanceDetail,
    list_packet_instances,
    show_packet_instance,
)
from concord.workflows.packet_instantiation import (
    PacketComponentChoice,
    PacketInstantiationTargetPlan,
    PacketRenderingBinding,
    PacketSubjectBinding,
    PlannedPacketArtifact,
    PreparedPacketInstantiation,
    PreparePacketInstantiationRequest,
    prepare_packet_instantiation,
)
from concord.workflows.packet_instantiation_commit import (
    commit_packet_instantiation,
    resume_packet_instantiation,
)
from concord.workflows.packet_rendering import (
    RenderPacketGenerationRequest,
    RenderPacketInstanceRequest,
    render_packet_generation,
    render_packet_instance,
)
from concord.workflows.participants import (
    load_required_roster,
    participant_print_label,
)
from concord.workflows.rendered_output import (
    open_rendered_packet_output,
    open_rendered_packet_output_directory,
)


def handle_instantiate_preview(args: argparse.Namespace) -> int:
    prepared = _prepare(args)
    _print_preview(prepared, workspace_root=workspace_arg(args))
    return 0


def handle_instantiate(args: argparse.Namespace) -> int:
    prepared = _prepare(args)
    if prepared.review_digest != args.review_digest:
        raise ConcordWorkflowConflictError(
            "review digest does not match the current zero-write Packet preview."
        )
    if not prepared.ready_for_commit:
        _print_preview(prepared, workspace_root=workspace_arg(args))
        raise ConcordWorkflowValidationError(
            "Packet preview contains blocking diagnostics."
        )
    result = commit_packet_instantiation(
        prepared,
        workspace_root=workspace_arg(args),
        generation_id=args.generation_id,
    )
    print(f"Generation: {result.generation_id}")
    print(f"Review Digest: {result.review_digest}")
    print(f"Packet Instances: {len(result.packet_instance_ids)}")
    print(f"Artifacts: {len(result.artifact_instance_ids)}")
    print(f"Pages: {len(result.pages)}")
    print(f"Routes: {result.routes_verified}/{result.routes_expected}")
    print(f"Replayed: {'yes' if result.replayed else 'no'}")
    return 0


def handle_instantiate_resume(args: argparse.Namespace) -> int:
    result = resume_packet_instantiation(
        args.class_id,
        args.activity_id,
        args.generation_id,
        workspace_root=workspace_arg(args),
    )
    print(f"Generation: {result.generation_id}")
    print(f"Packet Instances: {len(result.packet_instance_ids)}")
    print(f"Artifacts: {len(result.artifact_instance_ids)}")
    print(f"Pages: {len(result.pages)}")
    print(f"Routes: {result.routes_verified}/{result.routes_expected}")
    return 0


def handle_instance_list(args: argparse.Namespace) -> int:
    items = list_packet_instances(
        args.class_id,
        args.activity_id,
        generation_id=args.generation_id,
        workspace_root=workspace_arg(args),
    )
    if not items:
        print("No Activity-specific Packet Instances found.")
        return 0
    for item in items:
        output = item.output_relative_path or "-"
        print(
            f"{item.packet_instance_id}: generation={item.generation_id} "
            f"target={item.target_key} status={item.generation_status} "
            f"artifacts={item.artifact_count} pages={item.page_count} "
            f"routes={item.route_count} output={output}"
        )
    return 0


def handle_instance_show(args: argparse.Namespace) -> int:
    detail = show_packet_instance(
        args.class_id,
        args.activity_id,
        args.packet_instance_id,
        workspace_root=workspace_arg(args),
    )
    _print_detail(detail)
    return 0


def handle_instance_render(args: argparse.Namespace) -> int:
    result = render_packet_instance(
        RenderPacketInstanceRequest(
            class_id=args.class_id,
            activity_id=args.activity_id,
            packet_instance_id=args.packet_instance_id,
            actor=workflow_actor(args),
            expected_snapshot_revision=args.expected_snapshot,
        ),
        workspace_root=workspace_arg(args),
    )
    print(f"Packet Instance: {result.packet_instance_id}")
    print(f"Generation: {result.generation_id}")
    print(f"Output: {result.output_path}")
    print(f"Output SHA-256: {result.output_sha256}")
    print(f"Pages: {result.page_count}")
    print(f"Routes: {result.route_count}")
    print(f"Replayed: {'yes' if result.replayed else 'no'}")
    return 0


def handle_instance_open(args: argparse.Namespace) -> int:
    resolved = open_rendered_packet_output(
        args.class_id,
        args.activity_id,
        args.packet_instance_id,
        workspace_root=workspace_arg(args),
    )
    print(f"Opened rendered Packet: {resolved.output_path}")
    return 0


def handle_instance_open_folder(args: argparse.Namespace) -> int:
    resolved = open_rendered_packet_output_directory(
        args.class_id,
        args.activity_id,
        args.packet_instance_id,
        workspace_root=workspace_arg(args),
    )
    print(f"Opened rendered Packet folder: {resolved.output_directory}")
    return 0


def handle_generation_render(args: argparse.Namespace) -> int:
    result = render_packet_generation(
        RenderPacketGenerationRequest(
            class_id=args.class_id,
            activity_id=args.activity_id,
            generation_id=args.generation_id,
            actor=workflow_actor(args),
        ),
        workspace_root=workspace_arg(args),
    )
    print(f"Generation: {result.generation_id}")
    print(f"Packet Instances: {len(result.packets)}")
    print(f"Pages: {result.page_count}")
    print(f"Routes: {result.route_count}")
    for packet in result.packets:
        print(
            f"Output: {packet.packet_instance_id} -> {packet.output_path} "
            f"sha256={packet.output_sha256}"
        )
    return 0


def _prepare(args: argparse.Namespace) -> PreparedPacketInstantiation:
    choices, bindings, subject_bindings = _load_options(args.options_file)
    return prepare_packet_instantiation(
        PreparePacketInstantiationRequest(
            class_id=args.class_id,
            activity_id=args.activity_id,
            session_id=args.session_id,
            packet_definition_id=args.packet_definition_id,
            packet_version_id=args.packet_version_id,
            actor=workflow_actor(args),
            component_choices=choices,
            rendering_bindings=bindings,
            subject_bindings=subject_bindings,
        ),
        workspace_root=workspace_arg(args),
    )


def _load_options(
    path_value: str | None,
) -> tuple[
    tuple[PacketComponentChoice, ...],
    tuple[PacketRenderingBinding, ...],
    tuple[PacketSubjectBinding, ...],
]:
    if path_value is None:
        return (), (), ()
    path = Path(path_value).expanduser()
    try:
        raw: object = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ConcordWorkflowValidationError(
            f"Packet instantiation options could not be read: {error}"
        ) from error
    if not isinstance(raw, dict):
        raise ConcordWorkflowValidationError(
            "Packet instantiation options must be a JSON object."
        )
    document = cast(dict[str, object], raw)
    allowed = {
        "component_choices",
        "rendering_bindings",
        "subject_bindings",
    }
    unknown = set(document) - allowed
    if unknown:
        raise ConcordWorkflowValidationError(
            "unknown Packet instantiation option keys: "
            + ", ".join(sorted(unknown))
        )
    choices = _parse_choices(document.get("component_choices", []))
    bindings = _parse_bindings(document.get("rendering_bindings", []))
    subject_bindings = _parse_subject_bindings(
        document.get("subject_bindings", [])
    )
    return choices, bindings, subject_bindings


def _parse_choices(value: object) -> tuple[PacketComponentChoice, ...]:
    if not isinstance(value, list):
        raise ConcordWorkflowValidationError("component_choices must be a JSON array.")
    result: list[PacketComponentChoice] = []
    for raw_item in cast(list[object], value):
        if not isinstance(raw_item, dict):
            raise ConcordWorkflowValidationError(
                "each component choice must be a JSON object."
            )
        item = cast(dict[str, object], raw_item)
        if set(item) != {"packet_component_id", "include"}:
            raise ConcordWorkflowValidationError(
                "component choice keys must be packet_component_id and include."
            )
        component_id = item["packet_component_id"]
        include = item["include"]
        if not isinstance(component_id, str) or type(include) is not bool:
            raise ConcordWorkflowValidationError(
                "component choice requires string packet_component_id "
                "and boolean include."
            )
        result.append(
            PacketComponentChoice(
                packet_component_id=component_id,
                include=include,
            )
        )
    return tuple(result)


def _parse_bindings(value: object) -> tuple[PacketRenderingBinding, ...]:
    if not isinstance(value, list):
        raise ConcordWorkflowValidationError(
            "rendering_bindings must be a JSON array."
        )
    result: list[PacketRenderingBinding] = []
    for raw_item in cast(list[object], value):
        if not isinstance(raw_item, dict):
            raise ConcordWorkflowValidationError(
                "each rendering binding must be a JSON object."
            )
        item = cast(dict[str, object], raw_item)
        if set(item) != {"packet_component_id", "input_key", "value"}:
            raise ConcordWorkflowValidationError(
                "rendering binding keys must be packet_component_id, "
                "input_key, and value."
            )
        component_id = item["packet_component_id"]
        input_key = item["input_key"]
        binding_value = item["value"]
        if not isinstance(component_id, str) or not isinstance(input_key, str):
            raise ConcordWorkflowValidationError(
                "rendering binding component and input identities must be strings."
            )
        if not isinstance(binding_value, (str, int, bool)):
            raise ConcordWorkflowValidationError(
                "rendering binding value must be a string, integer, or boolean."
            )
        result.append(
            PacketRenderingBinding(
                packet_component_id=component_id,
                input_key=input_key,
                value=binding_value,
            )
        )
    return tuple(result)


def _parse_subject_bindings(
    value: object,
) -> tuple[PacketSubjectBinding, ...]:
    if not isinstance(value, list):
        raise ConcordWorkflowValidationError(
            "subject_bindings must be a JSON array."
        )
    result: list[PacketSubjectBinding] = []
    for raw_item in cast(list[object], value):
        if not isinstance(raw_item, dict):
            raise ConcordWorkflowValidationError(
                "each Subject binding must be a JSON object."
            )
        item = cast(dict[str, object], raw_item)
        if set(item) != {"packet_component_id", "target_key", "subject"}:
            raise ConcordWorkflowValidationError(
                "Subject binding keys must be packet_component_id, "
                "target_key, and subject."
            )
        component_id = item["packet_component_id"]
        target_key = item["target_key"]
        raw_subject = item["subject"]
        if not isinstance(component_id, str) or not isinstance(target_key, str):
            raise ConcordWorkflowValidationError(
                "Subject binding component and target identities must be strings."
            )
        if not isinstance(raw_subject, dict):
            raise ConcordWorkflowValidationError(
                "Subject binding subject must be a JSON object."
            )
        subject_document = cast(dict[str, object], raw_subject)
        required = {"subject_kind", "subject_id", "owning_system"}
        allowed = required | {"contract_version"}
        if not required.issubset(subject_document) or (
            set(subject_document) - allowed
        ):
            raise ConcordWorkflowValidationError(
                "Subject keys must be subject_kind, subject_id, owning_system, "
                "with optional contract_version."
            )
        subject_kind = subject_document["subject_kind"]
        subject_id = subject_document["subject_id"]
        owning_system = subject_document["owning_system"]
        contract_version = subject_document.get("contract_version")
        if (
            not isinstance(subject_kind, str)
            or not isinstance(subject_id, str)
            or not isinstance(owning_system, str)
            or (
                contract_version is not None
                and not isinstance(contract_version, str)
            )
        ):
            raise ConcordWorkflowValidationError(
                "Subject identity fields must be strings; contract_version "
                "may also be null."
            )
        try:
            subject = SubjectReference(
                subject_kind=subject_kind,
                subject_id=subject_id,
                owning_system=owning_system,
                contract_version=contract_version,
            )
            result.append(
                PacketSubjectBinding(
                    packet_component_id=component_id,
                    target_key=target_key,
                    subject_reference=subject,
                )
            )
        except (TypeError, ValueError) as error:
            raise ConcordWorkflowValidationError(
                f"invalid Subject binding: {error}"
            ) from error
    return tuple(result)


def _print_preview(
    prepared: PreparedPacketInstantiation,
    *,
    workspace_root: str | Path | None = None,
) -> None:
    print(f"Packet: {prepared.packet_definition.packet_definition_id}")
    print(f"Packet Version: {prepared.packet_version.packet_version_id}")
    print(f"Activity: {prepared.activity.activity_id}")
    print(f"Session: {prepared.session.session_id}")
    print(f"Generation Date: {prepared.generation_date}")
    print(f"Review Digest: {prepared.review_digest}")
    print(f"Ready for Commit: {'yes' if prepared.ready_for_commit else 'no'}")
    print(f"Packet Instances: {prepared.packet_instance_count}")
    print(f"Artifacts: {prepared.artifact_count}")
    print(f"Pages: {prepared.page_count}")
    print(f"Routes: {prepared.route_count}")
    for component in prepared.component_previews:
        print(
            f"Component: {component.sequence}. {component.packet_component_id} "
            f"[{component.requirement_level}] audience={component.audience_kind} "
            f"targets={component.included_target_count}/"
            f"{component.eligible_target_count} "
            f"artifacts={component.artifact_count} pages={component.page_count} "
            f"routes={component.route_count} disposition={component.disposition}"
        )
    for target in prepared.target_plans:
        print(
            f"Target: {target.target_key} artifacts={len(target.artifacts)} "
            f"pages={sum(item.page_count for item in target.artifacts)}"
        )
        target_label = _target_preview_label(prepared, target, workspace_root)
        for artifact in target.artifacts:
            relationship = _relationship_preview(
                prepared,
                artifact,
                target_label=target_label,
                workspace_root=workspace_root,
            )
            if relationship is not None:
                print(f"Relationship: {relationship}")
    for diagnostic in prepared.diagnostics:
        level = "BLOCKING" if diagnostic.blocking else "NOTICE"
        context = []
        if diagnostic.packet_component_id is not None:
            context.append(f"component={diagnostic.packet_component_id}")
        if diagnostic.target_key is not None:
            context.append(f"target={diagnostic.target_key}")
        if diagnostic.input_key is not None:
            context.append(f"input={diagnostic.input_key}")
        suffix = f" ({', '.join(context)})" if context else ""
        print(f"Diagnostic: {level} {diagnostic.code}{suffix}: {diagnostic.message}")


def _target_preview_label(
    prepared: PreparedPacketInstantiation,
    target: PacketInstantiationTargetPlan,
    workspace_root: str | Path | None,
) -> str:
    if target.participant_print_label is not None:
        return target.participant_print_label
    context = target.target_context
    if context.group_id is not None:
        return show_group(
            prepared.request.class_id,
            prepared.request.activity_id,
            context.group_id,
            workspace_root=workspace_root,
        ).summary.label
    if context.actor_reference is not None:
        return (
            context.actor_reference.display_label_snapshot
            or context.actor_reference.actor_id
        )
    return target.target_key


def _relationship_preview(
    prepared: PreparedPacketInstantiation,
    artifact: PlannedPacketArtifact,
    *,
    target_label: str,
    workspace_root: str | Path | None,
) -> str | None:
    subject = artifact.proposed_subject_reference
    role = artifact.proposed_subject_role
    if subject is None or role is None:
        return None

    subject_label = _subject_preview_label(
        prepared,
        subject,
        workspace_root=workspace_root,
    )
    if role == "reviewed_subject":
        right_label = (
            "Reviewee" if subject.subject_kind == "core_student" else "Reviewed"
        )
        return f"Reviewer: {target_label} | {right_label}: {subject_label}"
    if artifact.authorship_mode == "observer" and role == "session_context":
        return f"Observer: {target_label} | Observed: {subject_label}"
    return f"Author: {target_label} | Subject: {subject_label}"


def _subject_preview_label(
    prepared: PreparedPacketInstantiation,
    subject: SubjectReference,
    *,
    workspace_root: str | Path | None,
) -> str:
    if subject.subject_kind == "core_student":
        root = resolve_read_workspace_root(workspace_root)
        if root is None:
            raise ConcordWorkflowValidationError(
                "Paper Data Suite workspace does not exist."
            )
        roster = load_required_roster(
            root,
            prepared.request.class_id,
        )
        label = participant_print_label(
            roster,
            ParticipantReference(
                participant_kind="core_student",
                participant_id=subject.subject_id,
                owning_system=subject.owning_system,
            ),
        )
        return label or subject.subject_id
    if subject.subject_kind == "concord_group":
        return show_group(
            prepared.request.class_id,
            prepared.request.activity_id,
            subject.subject_id,
            workspace_root=workspace_root,
        ).summary.label
    if (
        subject.subject_kind == "concord_session"
        and subject.subject_id == prepared.session.session_id
    ):
        return prepared.session.label or f"Session {prepared.session.sequence}"
    if (
        subject.subject_kind == "concord_activity"
        and subject.subject_id == prepared.activity.activity_id
    ):
        return prepared.activity.title
    return f"{subject.subject_kind}:{subject.subject_id}"


def _print_detail(detail: PacketInstanceDetail) -> None:
    item = detail.summary
    print(f"Packet Instance: {item.packet_instance_id}")
    print(f"Generation: {item.generation_id}")
    print(f"Packet: {item.packet_definition_id}")
    print(f"Packet Version: {item.packet_version_id}")
    print(f"Activity: {item.activity_id}")
    print(f"Session: {item.session_id}")
    print(f"Target: {item.target_key}")
    print(f"Status: {item.generation_status}")
    print(f"Artifacts: {item.artifact_count}")
    print(f"Pages: {item.page_count}")
    print(f"Routes: {item.route_count}")
    print(f"Output: {item.output_relative_path or '-'}")
    print(f"Output SHA-256: {item.output_sha256 or '-'}")
    print(f"Created: {item.created_at}")
    for artifact_id in detail.artifact_instance_ids:
        print(f"Artifact: {artifact_id}")
    for page_id in detail.artifact_page_ids:
        print(f"Page: {page_id}")
    for route_id in detail.route_ids:
        print(f"Route: {route_id}")
