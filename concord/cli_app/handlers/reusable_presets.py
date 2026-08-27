"""Direct noninteractive reusable Role, Responsibility, and scoring presets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, NoReturn

from concord.cli_app.common import (
    effective_context,
    group_assignee,
    load_command_standards_library,
    student_participant,
    workflow_actor,
    workspace_arg,
)
from concord.cli_app.output import print_commit
from concord.models import (
    ConcordRecordReference,
    ParticipantReference,
    ScoringScaleLevel,
)
from concord.reusable_presets import (
    CriterionPresetSpec,
    CriterionSetPresetRevision,
    ResponsibilityPresetRevision,
    RolePresetRevision,
    ScoringScalePresetRevision,
)
from concord.workflows.reusable_presets import (
    ApplyResponsibilityPresetRequest,
    ApplyRolePresetRequest,
    CreateCriterionSetPresetRequest,
    CreateResponsibilityPresetRequest,
    CreateRolePresetRequest,
    CreateScoringScalePresetRequest,
    CriterionTargetIdentity,
    MaterializeScoringSetupRequest,
    ReviseCriterionSetPresetRequest,
    ReviseResponsibilityPresetRequest,
    ReviseRolePresetRequest,
    ReviseScoringScalePresetRequest,
    SaveCriterionSetPresetFromActivityRequest,
    SaveResponsibilityPresetFromAssignmentRequest,
    SaveRolePresetFromAssignmentRequest,
    SaveScoringScalePresetFromActivityRequest,
    apply_responsibility_preset,
    apply_role_preset,
    create_criterion_set_preset,
    create_responsibility_preset,
    create_role_preset,
    create_scoring_scale_preset,
    get_preset,
    list_presets,
    materialize_scoring_setup,
    prepare_criterion_set_preset_from_activity,
    prepare_responsibility_preset_application,
    prepare_responsibility_preset_from_assignment,
    prepare_role_preset_application,
    prepare_role_preset_from_assignment,
    prepare_scoring_scale_preset_from_activity,
    prepare_scoring_setup,
    retire_preset,
    revise_criterion_set_preset,
    revise_responsibility_preset,
    revise_role_preset,
    revise_scoring_scale_preset,
    save_criterion_set_preset_from_activity,
    save_responsibility_preset_from_assignment,
    save_role_preset_from_assignment,
    save_scoring_scale_preset_from_activity,
    validate_preset,
)


def _usage(args: argparse.Namespace, message: str) -> NoReturn:
    parser = getattr(args, "command_parser", None)
    if isinstance(parser, argparse.ArgumentParser):
        parser.error(message)
    raise ValueError(message)


def _load_object(
    path_value: str,
    args: argparse.Namespace,
    label: str,
) -> dict[str, Any]:
    path = Path(path_value)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        _usage(args, f"Could not read {label}: {error}")
    except json.JSONDecodeError as error:
        _usage(args, f"{label} is not valid JSON: {error}")
    if not isinstance(raw, dict) or any(not isinstance(key, str) for key in raw):
        _usage(args, f"{label} must be a JSON object.")
    return raw


def _only_keys(
    value: dict[str, Any],
    allowed: frozenset[str],
    args: argparse.Namespace,
    label: str,
) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        _usage(args, f"{label} contains unsupported field(s): {', '.join(unknown)}.")


def _required(
    value: dict[str, Any],
    name: str,
    args: argparse.Namespace,
    label: str,
) -> Any:
    if name not in value:
        _usage(args, f"{label} requires {name}.")
    return value[name]


def _string_tuple(
    value: object,
    args: argparse.Namespace,
    label: str,
) -> tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        _usage(args, f"{label} must be a JSON array of strings.")
    return tuple(value)


def _scale_levels(
    definition: dict[str, Any],
    args: argparse.Namespace,
) -> tuple[ScoringScaleLevel, ...]:
    raw = _required(definition, "levels", args, "Scoring Scale preset definition")
    if not isinstance(raw, list) or not raw:
        _usage(args, "Scoring Scale preset levels must be a nonempty array.")
    result: list[ScoringScaleLevel] = []
    allowed = frozenset({"value", "label", "meaning", "position", "description"})
    for index, item in enumerate(raw):
        if not isinstance(item, dict) or any(not isinstance(key, str) for key in item):
            _usage(args, f"levels[{index}] must be a JSON object.")
        data = item
        _only_keys(data, allowed, args, f"levels[{index}]")
        result.append(
            ScoringScaleLevel(
                value=_required(data, "value", args, f"levels[{index}]"),
                label=_required(data, "label", args, f"levels[{index}]"),
                meaning=_required(data, "meaning", args, f"levels[{index}]"),
                position=data.get("position"),
                description=data.get("description"),
            )
        )
    return tuple(result)


def _scale_definition(args: argparse.Namespace) -> dict[str, Any]:
    value = _load_object(args.definition, args, "Scoring Scale preset definition")
    _only_keys(
        value,
        frozenset(
            {
                "name",
                "scale_type",
                "levels",
                "intended_use",
                "aggregation_guidance",
            }
        ),
        args,
        "Scoring Scale preset definition",
    )
    return value


def _criterion_specs(
    definition: dict[str, Any],
    args: argparse.Namespace,
) -> tuple[CriterionPresetSpec, ...]:
    raw = _required(definition, "criteria", args, "Criterion Set preset definition")
    if not isinstance(raw, list) or not raw:
        _usage(args, "Criterion Set preset criteria must be a nonempty array.")
    allowed = frozenset(
        {
            "key",
            "label",
            "definition",
            "criterion_kind",
            "supported_target_kinds",
            "standard_id",
            "alignment_standard_ids",
            "default_scoring_scale_preset_id",
            "default_scoring_scale_preset_revision_id",
            "status",
        }
    )
    result: list[CriterionPresetSpec] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict) or any(not isinstance(key, str) for key in item):
            _usage(args, f"criteria[{index}] must be a JSON object.")
        data = item
        _only_keys(data, allowed, args, f"criteria[{index}]")
        result.append(
            CriterionPresetSpec(
                key=_required(data, "key", args, f"criteria[{index}]"),
                label=_required(data, "label", args, f"criteria[{index}]"),
                definition=_required(data, "definition", args, f"criteria[{index}]"),
                criterion_kind=_required(
                    data,
                    "criterion_kind",
                    args,
                    f"criteria[{index}]",
                ),
                supported_target_kinds=_string_tuple(
                    _required(
                        data,
                        "supported_target_kinds",
                        args,
                        f"criteria[{index}]",
                    ),
                    args,
                    f"criteria[{index}].supported_target_kinds",
                ),
                standard_id=data.get("standard_id"),
                alignment_standard_ids=_string_tuple(
                    data.get("alignment_standard_ids", []),
                    args,
                    f"criteria[{index}].alignment_standard_ids",
                ),
                default_scoring_scale_preset_id=data.get(
                    "default_scoring_scale_preset_id"
                ),
                default_scoring_scale_preset_revision_id=data.get(
                    "default_scoring_scale_preset_revision_id"
                ),
                status=data.get("status", "active"),
            )
        )
    return tuple(result)


def _criterion_definition(args: argparse.Namespace) -> dict[str, Any]:
    value = _load_object(args.definition, args, "Criterion Set preset definition")
    _only_keys(
        value,
        frozenset(
            {
                "name",
                "purpose",
                "criterion_set_kind",
                "criteria",
                "standards_profile_id",
            }
        ),
        args,
        "Criterion Set preset definition",
    )
    return value


def _print_mutation(result: object) -> None:
    print(f"Preset: {getattr(result, 'preset_id')}")
    print(f"Preset Revision: {getattr(result, 'preset_revision_id')}")
    print(f"Revision: {getattr(result, 'revision')}")
    print(f"Status: {getattr(result, 'status')}")
    if getattr(result, "workspace_created", False):
        print("Workspace created: yes")


def handle_list(args: argparse.Namespace) -> int:
    items = list_presets(
        args.preset_kind,
        workspace_root=workspace_arg(args),
        include_retired=args.include_retired,
    )
    if not items:
        print("No reusable presets found.")
        return 0
    for item in items:
        print(
            f"{item.preset_id}\t{item.preset_revision_id}\t"
            f"rev={item.revision}\t{item.name}\t{item.status}"
        )
    return 0


def handle_show(args: argparse.Namespace) -> int:
    value = get_preset(
        args.preset_kind,
        args.preset_id,
        workspace_root=workspace_arg(args),
    )
    print(f"Preset: {value.preset_id}")
    print(f"Preset Revision: {value.preset_revision_id}")
    print(f"Revision: {value.revision}")
    print(f"Name: {value.name}")
    print(f"Status: {value.status}")
    if isinstance(value, RolePresetRevision):
        print(f"Role key: {value.role_key}")
        print(f"Role label: {value.role_label or '-'}")
        print(f"Description: {value.description or '-'}")
    elif isinstance(value, ResponsibilityPresetRevision):
        print(f"Responsibility: {value.description}")
        print(f"Expected output: {value.expected_output or '-'}")
    elif isinstance(value, ScoringScalePresetRevision):
        print(f"Type: {value.scale_type}")
        print(f"Levels: {len(value.levels)}")
        print(f"Intended use: {value.intended_use or '-'}")
    elif isinstance(value, CriterionSetPresetRevision):
        print(f"Purpose: {value.purpose}")
        print(f"Kind: {value.criterion_set_kind}")
        print(f"Criteria: {len(value.criteria)}")
        print(f"Standards profile: {value.standards_profile_id or '-'}")
    return 0


def handle_validate(args: argparse.Namespace) -> int:
    item = validate_preset(
        args.preset_kind,
        args.preset_id,
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print(f"Preset: {item.preset_id}")
    print(f"Status: {item.status}")
    print("Validation: valid")
    return 0



def _print_save_preview(prepared: object) -> None:
    print(f"Preset: {getattr(prepared, 'preset_id')}")
    print(f"Name: {getattr(prepared, 'name')}")
    print(
        "Source: "
        f"{getattr(prepared, 'source_class_id')}/"
        f"{getattr(prepared, 'source_activity_id')}/"
        f"{getattr(prepared, 'source_record_kind')}:"
        f"{getattr(prepared, 'source_record_id')}"
    )
    print("Reusable fields:")
    for line in getattr(prepared, "reusable_fields"):
        print(f"  {line}")
    print("Will not copy:")
    for line in getattr(prepared, "excluded_state"):
        print(f"  {line}")
    print(f"Review digest: {getattr(prepared, 'review_digest')}")
    print("Writes: none")


def _role_save_request(args: argparse.Namespace) -> SaveRolePresetFromAssignmentRequest:
    return SaveRolePresetFromAssignmentRequest(
        class_id=args.class_id,
        activity_id=args.activity_id,
        role_assignment_id=args.source_role_assignment_id,
        preset_id=args.preset_id,
        preset_revision_id=args.preset_revision_id,
        name=args.name,
        description=args.description,
        applicability_hints=tuple(args.hint or ()),
        expected_snapshot_revision=args.expected_snapshot,
        actor=workflow_actor(args),
    )


def handle_role_save_preview(args: argparse.Namespace) -> int:
    prepared = prepare_role_preset_from_assignment(
        _role_save_request(args),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    _print_save_preview(prepared)
    return 0


def handle_role_save(args: argparse.Namespace) -> int:
    result = save_role_preset_from_assignment(
        _role_save_request(args),
        review_digest=args.review_digest,
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    _print_mutation(result)
    return 0


def handle_role_create(args: argparse.Namespace) -> int:
    result = create_role_preset(
        CreateRolePresetRequest(
            preset_id=args.preset_id,
            preset_revision_id=args.preset_revision_id,
            name=args.name,
            role_key=args.role_key,
            role_label=args.role_label,
            description=args.description,
            applicability_hints=tuple(args.hint or ()),
            actor=workflow_actor(args),
        ),
        workspace_root=workspace_arg(args),
    )
    _print_mutation(result)
    return 0


def handle_role_revise(args: argparse.Namespace) -> int:
    result = revise_role_preset(
        ReviseRolePresetRequest(
            preset_id=args.preset_id,
            preset_revision_id=args.preset_revision_id,
            expected_revision=args.expected_preset_revision,
            name=args.name,
            role_key=args.role_key,
            role_label=args.role_label,
            description=args.description,
            applicability_hints=tuple(args.hint or ()),
            actor=workflow_actor(args),
        ),
        workspace_root=workspace_arg(args),
    )
    _print_mutation(result)
    return 0


def _role_apply_request(args: argparse.Namespace) -> ApplyRolePresetRequest:
    return ApplyRolePresetRequest(
        preset_id=args.preset_id,
        preset_revision_id=args.preset_revision_id,
        class_id=args.class_id,
        activity_id=args.activity_id,
        role_assignment_id=args.role_assignment_id,
        participant_reference=student_participant(args),
        effective_context=effective_context(args),
        expected_snapshot_revision=args.expected_snapshot,
        actor=workflow_actor(args),
        status=args.status,
        membership_id=args.membership_id,
        group_id=args.group_id,
    )


def handle_role_apply_preview(args: argparse.Namespace) -> int:
    prepared = prepare_role_preset_application(
        _role_apply_request(args),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print(f"Role preset: {prepared.preset_name}")
    print(f"Role: {prepared.role_key}")
    print(f"Target Role Assignment: {prepared.request.role_assignment_id}")
    print(f"Review digest: {prepared.review_digest}")
    print("Writes: none")
    return 0


def handle_role_apply(args: argparse.Namespace) -> int:
    result = apply_role_preset(
        _role_apply_request(args),
        review_digest=args.review_digest,
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print_commit(result.commit)
    print(f"Role Assignment: {result.role_assignment_id}")
    return 0



def _responsibility_save_request(
    args: argparse.Namespace,
) -> SaveResponsibilityPresetFromAssignmentRequest:
    return SaveResponsibilityPresetFromAssignmentRequest(
        class_id=args.class_id,
        activity_id=args.activity_id,
        responsibility_assignment_id=args.source_responsibility_assignment_id,
        preset_id=args.preset_id,
        preset_revision_id=args.preset_revision_id,
        name=args.name,
        applicability_hints=tuple(args.hint or ()),
        expected_snapshot_revision=args.expected_snapshot,
        actor=workflow_actor(args),
    )


def handle_responsibility_save_preview(args: argparse.Namespace) -> int:
    prepared = prepare_responsibility_preset_from_assignment(
        _responsibility_save_request(args),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    _print_save_preview(prepared)
    return 0


def handle_responsibility_save(args: argparse.Namespace) -> int:
    result = save_responsibility_preset_from_assignment(
        _responsibility_save_request(args),
        review_digest=args.review_digest,
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    _print_mutation(result)
    return 0


def handle_responsibility_create(args: argparse.Namespace) -> int:
    result = create_responsibility_preset(
        CreateResponsibilityPresetRequest(
            preset_id=args.preset_id,
            preset_revision_id=args.preset_revision_id,
            name=args.name,
            description=args.description,
            expected_output=args.expected_output,
            applicability_hints=tuple(args.hint or ()),
            actor=workflow_actor(args),
        ),
        workspace_root=workspace_arg(args),
    )
    _print_mutation(result)
    return 0


def handle_responsibility_revise(args: argparse.Namespace) -> int:
    result = revise_responsibility_preset(
        ReviseResponsibilityPresetRequest(
            preset_id=args.preset_id,
            preset_revision_id=args.preset_revision_id,
            expected_revision=args.expected_preset_revision,
            name=args.name,
            description=args.description,
            expected_output=args.expected_output,
            applicability_hints=tuple(args.hint or ()),
            actor=workflow_actor(args),
        ),
        workspace_root=workspace_arg(args),
    )
    _print_mutation(result)
    return 0


def _responsibility_assignee(
    args: argparse.Namespace,
) -> ParticipantReference | ConcordRecordReference:
    if args.group_assignee_id is not None:
        return group_assignee(args.group_assignee_id)
    return student_participant(args)


def _responsibility_apply_request(
    args: argparse.Namespace,
) -> ApplyResponsibilityPresetRequest:
    return ApplyResponsibilityPresetRequest(
        preset_id=args.preset_id,
        preset_revision_id=args.preset_revision_id,
        class_id=args.class_id,
        activity_id=args.activity_id,
        responsibility_assignment_id=args.responsibility_assignment_id,
        assignee_reference=_responsibility_assignee(args),
        effective_context=effective_context(args),
        expected_snapshot_revision=args.expected_snapshot,
        actor=workflow_actor(args),
        status=args.status,
        group_id=args.group_id,
        work_item_id=args.work_item_id,
    )


def handle_responsibility_apply_preview(args: argparse.Namespace) -> int:
    prepared = prepare_responsibility_preset_application(
        _responsibility_apply_request(args),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print(f"Responsibility preset: {prepared.preset_name}")
    print(f"Responsibility: {prepared.description}")
    print(f"Expected output: {prepared.expected_output or '-'}")
    print(f"Target Responsibility: {prepared.request.responsibility_assignment_id}")
    print(f"Review digest: {prepared.review_digest}")
    print("Writes: none")
    return 0


def handle_responsibility_apply(args: argparse.Namespace) -> int:
    result = apply_responsibility_preset(
        _responsibility_apply_request(args),
        review_digest=args.review_digest,
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print_commit(result.commit)
    print(f"Responsibility: {result.responsibility_assignment_id}")
    return 0



def _scale_save_request(
    args: argparse.Namespace,
) -> SaveScoringScalePresetFromActivityRequest:
    return SaveScoringScalePresetFromActivityRequest(
        class_id=args.class_id,
        activity_id=args.activity_id,
        scoring_scale_id=args.source_scoring_scale_id,
        preset_id=args.preset_id,
        preset_revision_id=args.preset_revision_id,
        name=args.name,
        expected_snapshot_revision=args.expected_snapshot,
        actor=workflow_actor(args),
    )


def handle_scale_save_preview(args: argparse.Namespace) -> int:
    prepared = prepare_scoring_scale_preset_from_activity(
        _scale_save_request(args),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    _print_save_preview(prepared)
    return 0


def handle_scale_save(args: argparse.Namespace) -> int:
    result = save_scoring_scale_preset_from_activity(
        _scale_save_request(args),
        review_digest=args.review_digest,
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    _print_mutation(result)
    return 0


def handle_scale_create(args: argparse.Namespace) -> int:
    definition = _scale_definition(args)
    result = create_scoring_scale_preset(
        CreateScoringScalePresetRequest(
            preset_id=args.preset_id,
            preset_revision_id=args.preset_revision_id,
            name=_required(definition, "name", args, "Scoring Scale preset definition"),
            scale_type=_required(
                definition,
                "scale_type",
                args,
                "Scoring Scale preset definition",
            ),
            levels=_scale_levels(definition, args),
            intended_use=definition.get("intended_use"),
            aggregation_guidance=definition.get("aggregation_guidance"),
            actor=workflow_actor(args),
        ),
        workspace_root=workspace_arg(args),
    )
    _print_mutation(result)
    return 0


def handle_scale_revise(args: argparse.Namespace) -> int:
    definition = _scale_definition(args)
    result = revise_scoring_scale_preset(
        ReviseScoringScalePresetRequest(
            preset_id=args.preset_id,
            preset_revision_id=args.preset_revision_id,
            expected_revision=args.expected_preset_revision,
            name=_required(definition, "name", args, "Scoring Scale preset definition"),
            scale_type=_required(
                definition,
                "scale_type",
                args,
                "Scoring Scale preset definition",
            ),
            levels=_scale_levels(definition, args),
            intended_use=definition.get("intended_use"),
            aggregation_guidance=definition.get("aggregation_guidance"),
            actor=workflow_actor(args),
        ),
        workspace_root=workspace_arg(args),
    )
    _print_mutation(result)
    return 0



def _criterion_save_request(
    args: argparse.Namespace,
) -> SaveCriterionSetPresetFromActivityRequest:
    return SaveCriterionSetPresetFromActivityRequest(
        class_id=args.class_id,
        activity_id=args.activity_id,
        criterion_set_id=args.source_criterion_set_id,
        preset_id=args.preset_id,
        preset_revision_id=args.preset_revision_id,
        name=args.name,
        recommended_scoring_scale_preset_id=(
            args.recommended_scoring_scale_preset_id
        ),
        recommended_scoring_scale_preset_revision_id=(
            args.recommended_scoring_scale_preset_revision_id
        ),
        expected_snapshot_revision=args.expected_snapshot,
        actor=workflow_actor(args),
    )


def handle_criterion_save_preview(args: argparse.Namespace) -> int:
    prepared = prepare_criterion_set_preset_from_activity(
        _criterion_save_request(args),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    _print_save_preview(prepared)
    return 0


def handle_criterion_save(args: argparse.Namespace) -> int:
    result = save_criterion_set_preset_from_activity(
        _criterion_save_request(args),
        review_digest=args.review_digest,
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    _print_mutation(result)
    return 0


def handle_criterion_create(args: argparse.Namespace) -> int:
    definition = _criterion_definition(args)
    result = create_criterion_set_preset(
        CreateCriterionSetPresetRequest(
            preset_id=args.preset_id,
            preset_revision_id=args.preset_revision_id,
            name=_required(definition, "name", args, "Criterion Set preset definition"),
            purpose=_required(
                definition,
                "purpose",
                args,
                "Criterion Set preset definition",
            ),
            criterion_set_kind=_required(
                definition,
                "criterion_set_kind",
                args,
                "Criterion Set preset definition",
            ),
            criteria=_criterion_specs(definition, args),
            standards_profile_id=definition.get("standards_profile_id"),
            actor=workflow_actor(args),
        ),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    _print_mutation(result)
    return 0


def handle_criterion_revise(args: argparse.Namespace) -> int:
    definition = _criterion_definition(args)
    result = revise_criterion_set_preset(
        ReviseCriterionSetPresetRequest(
            preset_id=args.preset_id,
            preset_revision_id=args.preset_revision_id,
            expected_revision=args.expected_preset_revision,
            name=_required(definition, "name", args, "Criterion Set preset definition"),
            purpose=_required(
                definition,
                "purpose",
                args,
                "Criterion Set preset definition",
            ),
            criterion_set_kind=_required(
                definition,
                "criterion_set_kind",
                args,
                "Criterion Set preset definition",
            ),
            criteria=_criterion_specs(definition, args),
            standards_profile_id=definition.get("standards_profile_id"),
            actor=workflow_actor(args),
        ),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    _print_mutation(result)
    return 0


def _criterion_targets(args: argparse.Namespace) -> tuple[CriterionTargetIdentity, ...]:
    values: list[CriterionTargetIdentity] = []
    for raw in args.criterion_target:
        key, separator, criterion_id = raw.partition("=")
        if not separator or not key or not criterion_id:
            _usage(args, "--criterion-target must use KEY=CRITERION_ID.")
        values.append(
            CriterionTargetIdentity(
                criterion_key=key,
                criterion_id=criterion_id,
            )
        )
    return tuple(values)


def _scoring_request(args: argparse.Namespace) -> MaterializeScoringSetupRequest:
    return MaterializeScoringSetupRequest(
        criterion_preset_id=args.preset_id,
        criterion_preset_revision_id=args.preset_revision_id,
        class_id=args.class_id,
        activity_id=args.activity_id,
        criterion_set_id=args.criterion_set_id,
        criterion_set_lineage_id=args.criterion_set_lineage_id,
        criterion_ids=_criterion_targets(args),
        expected_snapshot_revision=args.expected_snapshot,
        actor=workflow_actor(args),
        scoring_scale_preset_id=args.scoring_scale_preset_id,
        scoring_scale_preset_revision_id=args.scoring_scale_preset_revision_id,
        scoring_scale_id=args.scoring_scale_id,
        scoring_scale_lineage_id=args.scoring_scale_lineage_id,
    )


def handle_scoring_apply_preview(args: argparse.Namespace) -> int:
    prepared = prepare_scoring_setup(
        _scoring_request(args),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print(f"Criterion preset: {prepared.criterion_preset_name}")
    print(f"Criteria: {prepared.criterion_count}")
    print(f"Scale preset: {prepared.scoring_scale_preset_name or '-'}")
    print(f"Standards profile: {prepared.standards_profile_id or '-'}")
    print(f"Review digest: {prepared.review_digest}")
    print("Writes: none")
    return 0


def handle_scoring_apply(args: argparse.Namespace) -> int:
    result = materialize_scoring_setup(
        _scoring_request(args),
        review_digest=args.review_digest,
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print_commit(result.commit)
    print(f"Criterion Set: {result.criterion_set_id}")
    print("Criteria: " + ", ".join(result.criterion_ids))
    print(f"Scoring Scale: {result.scoring_scale_id or '-'}")
    return 0


def handle_retire(args: argparse.Namespace) -> int:
    result = retire_preset(
        args.preset_kind,
        args.preset_id,
        preset_revision_id=args.preset_revision_id,
        expected_revision=args.expected_preset_revision,
        actor=workflow_actor(args),
        workspace_root=workspace_arg(args),
    )
    _print_mutation(result)
    return 0
