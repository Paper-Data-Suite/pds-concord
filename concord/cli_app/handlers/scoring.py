"""Direct Criterion Set, Scoring Scale, and Score commands."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, NoReturn

from concord.cli_app.common import (
    load_command_standards_library,
    workflow_actor,
    workspace_arg,
)
from concord.cli_app.output import print_commit
from concord.models import (
    ConcordRecordReference,
    CorePublicationReference,
    EvidenceLocator,
    EvidenceReference,
    PrivacyPolicy,
    ScoreTargetReference,
    ScoringScaleLevel,
    StatusReason,
    SubjectReference,
)
from concord.workflows import (
    AddScoreRequest,
    CreateCriterionSetRequest,
    CreateScoringScaleRequest,
    CriterionSpec,
    ReplaceScoreRequest,
    ReviseCriterionSetRequest,
    ReviseScoringScaleRequest,
    ScoreEvidenceLinkSpec,
    SelectActivityCriterionSetsRequest,
    add_score,
    create_criterion_set,
    create_scoring_scale,
    list_criterion_sets,
    list_scores,
    list_scoring_scales,
    replace_score,
    revise_criterion_set,
    revise_scoring_scale,
    select_activity_criterion_sets,
    show_criterion_set,
    show_score,
    show_scoring_scale,
)
from concord.workflows.context import actor_reference


def _usage(args: argparse.Namespace, message: str) -> NoReturn:
    parser = getattr(args, "command_parser", None)
    if isinstance(parser, argparse.ArgumentParser):
        parser.error(message)
    raise ValueError(message)


def _privacy(value: str) -> PrivacyPolicy:
    return PrivacyPolicy(classification=value)


def _load_json(path_value: str, args: argparse.Namespace) -> object:
    path = Path(path_value)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        _usage(args, f"Could not read definition file: {error}")
    except json.JSONDecodeError as error:
        _usage(args, f"Definition file is not valid JSON: {error}")


def _object(
    value: object,
    args: argparse.Namespace,
    label: str,
) -> dict[str, Any]:
    if not isinstance(value, dict) or any(
        not isinstance(key, str) for key in value
    ):
        _usage(args, f"{label} must be a JSON object.")
    return value


def _only_keys(
    value: dict[str, Any],
    allowed: frozenset[str],
    args: argparse.Namespace,
    label: str,
) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        _usage(
            args,
            f"{label} contains unsupported field(s): {', '.join(unknown)}.",
        )


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
    if not isinstance(value, list) or any(
        not isinstance(item, str) for item in value
    ):
        _usage(args, f"{label} must be a JSON array of strings.")
    return tuple(value)


def _criterion_specs(
    definition: dict[str, Any],
    args: argparse.Namespace,
) -> tuple[CriterionSpec, ...]:
    raw = _required(definition, "criteria", args, "Criterion Set definition")
    if not isinstance(raw, list) or not raw:
        _usage(args, "Criterion Set criteria must be a nonempty JSON array.")
    result: list[CriterionSpec] = []
    allowed = frozenset(
        {
            "criterion_id",
            "key",
            "label",
            "definition",
            "criterion_kind",
            "supported_target_kinds",
            "standard_id",
            "alignment_standard_ids",
            "default_scoring_scale_id",
            "status",
        }
    )
    for index, item in enumerate(raw):
        data = _object(item, args, f"criteria[{index}]")
        _only_keys(data, allowed, args, f"criteria[{index}]")
        result.append(
            CriterionSpec(
                criterion_id=_required(
                    data, "criterion_id", args, f"criteria[{index}]"
                ),
                key=_required(data, "key", args, f"criteria[{index}]"),
                label=_required(data, "label", args, f"criteria[{index}]"),
                definition=_required(
                    data, "definition", args, f"criteria[{index}]"
                ),
                criterion_kind=_required(
                    data, "criterion_kind", args, f"criteria[{index}]"
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
                default_scoring_scale_id=data.get(
                    "default_scoring_scale_id"
                ),
                status=data.get("status", "active"),
            )
        )
    return tuple(result)


def _criterion_definition(
    args: argparse.Namespace,
) -> dict[str, Any]:
    definition = _object(
        _load_json(args.definition, args),
        args,
        "Criterion Set definition",
    )
    _only_keys(
        definition,
        frozenset(
            {
                "name",
                "purpose",
                "revision",
                "scope",
                "criterion_set_kind",
                "criteria",
                "status",
                "standards_profile_id",
            }
        ),
        args,
        "Criterion Set definition",
    )
    return definition


def _scale_definition(args: argparse.Namespace) -> dict[str, Any]:
    definition = _object(
        _load_json(args.definition, args),
        args,
        "Scoring Scale definition",
    )
    _only_keys(
        definition,
        frozenset(
            {
                "name",
                "revision",
                "scale_type",
                "levels",
                "status",
                "intended_use",
                "aggregation_guidance",
            }
        ),
        args,
        "Scoring Scale definition",
    )
    return definition


def _scale_levels(
    definition: dict[str, Any],
    args: argparse.Namespace,
) -> tuple[ScoringScaleLevel, ...]:
    raw = _required(definition, "levels", args, "Scoring Scale definition")
    if not isinstance(raw, list) or not raw:
        _usage(args, "Scoring Scale levels must be a nonempty JSON array.")
    result: list[ScoringScaleLevel] = []
    allowed = frozenset(
        {"value", "label", "meaning", "position", "description"}
    )
    for index, item in enumerate(raw):
        data = _object(item, args, f"levels[{index}]")
        _only_keys(data, allowed, args, f"levels[{index}]")
        result.append(
            ScoringScaleLevel(
                value=_required(data, "value", args, f"levels[{index}]"),
                label=_required(data, "label", args, f"levels[{index}]"),
                meaning=_required(
                    data, "meaning", args, f"levels[{index}]"
                ),
                position=data.get("position"),
                description=data.get("description"),
            )
        )
    return tuple(result)


def _subject(
    value: object,
    args: argparse.Namespace,
    label: str,
) -> SubjectReference:
    data = _object(value, args, label)
    _only_keys(
        data,
        frozenset(
            {
                "subject_kind",
                "subject_id",
                "owning_system",
                "contract_version",
            }
        ),
        args,
        label,
    )
    return SubjectReference(
        subject_kind=_required(data, "subject_kind", args, label),
        subject_id=_required(data, "subject_id", args, label),
        owning_system=_required(data, "owning_system", args, label),
        contract_version=data.get("contract_version"),
    )


def _locator(
    value: object,
    args: argparse.Namespace,
    label: str,
) -> EvidenceLocator:
    data = _object(value, args, label)
    allowed = frozenset(
        {
            "page_number",
            "source_page_index",
            "section_label",
            "row_label",
            "column_label",
            "participant_label",
            "session_id",
            "note",
        }
    )
    _only_keys(data, allowed, args, label)
    return EvidenceLocator(**data)


def _evidence_reference(
    value: object,
    args: argparse.Namespace,
    label: str,
) -> EvidenceReference:
    data = _object(value, args, label)
    allowed = frozenset(
        {
            "evidence_kind",
            "owning_system",
            "record_id",
            "contract_version",
            "source_publication_reference",
            "immutable_source_version",
            "locator",
            "subject_context",
            "moderation_requirement",
        }
    )
    _only_keys(data, allowed, args, label)
    publication_value = data.get("source_publication_reference")
    publication = None
    if publication_value is not None:
        publication_data = _object(
            publication_value,
            args,
            f"{label}.source_publication_reference",
        )
        _only_keys(
            publication_data,
            frozenset(
                {"publication_id", "publication_schema_version"}
            ),
            args,
            f"{label}.source_publication_reference",
        )
        publication = CorePublicationReference(
            publication_id=_required(
                publication_data,
                "publication_id",
                args,
                f"{label}.source_publication_reference",
            ),
            publication_schema_version=publication_data.get(
                "publication_schema_version"
            ),
        )
    locator_value = data.get("locator")
    locator = (
        None
        if locator_value is None
        else _locator(locator_value, args, f"{label}.locator")
    )
    subjects_raw = data.get("subject_context", [])
    if not isinstance(subjects_raw, list):
        _usage(args, f"{label}.subject_context must be a JSON array.")
    subjects = tuple(
        _subject(item, args, f"{label}.subject_context[{index}]")
        for index, item in enumerate(subjects_raw)
    )
    return EvidenceReference(
        evidence_kind=_required(data, "evidence_kind", args, label),
        owning_system=_required(data, "owning_system", args, label),
        record_id=_required(data, "record_id", args, label),
        contract_version=data.get("contract_version"),
        source_publication_reference=publication,
        immutable_source_version=data.get("immutable_source_version"),
        locator=locator,
        subject_context=subjects,
        moderation_requirement=data.get("moderation_requirement"),
    )


def _evidence_links(
    args: argparse.Namespace,
) -> tuple[ScoreEvidenceLinkSpec, ...]:
    path = getattr(args, "evidence_links", None)
    if path is None:
        return ()
    raw = _load_json(path, args)
    if not isinstance(raw, list):
        _usage(args, "Score evidence-link file must contain a JSON array.")
    result: list[ScoreEvidenceLinkSpec] = []
    allowed = frozenset(
        {
            "score_evidence_link_id",
            "evidence_reference",
            "evidence_locator",
            "subject_context",
            "relevance_description",
            "significance",
            "moderation_record_id",
        }
    )
    for index, item in enumerate(raw):
        data = _object(item, args, f"evidence_links[{index}]")
        _only_keys(data, allowed, args, f"evidence_links[{index}]")
        subjects_raw = data.get("subject_context", [])
        if not isinstance(subjects_raw, list):
            _usage(
                args,
                f"evidence_links[{index}].subject_context must be an array.",
            )
        locator_raw = data.get("evidence_locator")
        result.append(
            ScoreEvidenceLinkSpec(
                score_evidence_link_id=_required(
                    data,
                    "score_evidence_link_id",
                    args,
                    f"evidence_links[{index}]",
                ),
                evidence_reference=_evidence_reference(
                    _required(
                        data,
                        "evidence_reference",
                        args,
                        f"evidence_links[{index}]",
                    ),
                    args,
                    f"evidence_links[{index}].evidence_reference",
                ),
                evidence_locator=(
                    None
                    if locator_raw is None
                    else _locator(
                        locator_raw,
                        args,
                        f"evidence_links[{index}].evidence_locator",
                    )
                ),
                subject_context=tuple(
                    _subject(
                        subject,
                        args,
                        f"evidence_links[{index}].subject_context"
                        f"[{subject_index}]",
                    )
                    for subject_index, subject in enumerate(subjects_raw)
                ),
                relevance_description=_required(
                    data,
                    "relevance_description",
                    args,
                    f"evidence_links[{index}]",
                ),
                significance=data.get("significance"),
                moderation_record_id=data.get("moderation_record_id"),
            )
        )
    return tuple(result)


def _score_value(args: argparse.Namespace) -> object:
    raw = getattr(args, "value_json", None)
    if raw is None:
        if args.disposition == "scored":
            _usage(args, "scored disposition requires --value-json.")
        return None
    if args.disposition != "scored":
        _usage(args, "non-score dispositions forbid --value-json.")
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as error:
        _usage(args, f"--value-json is not valid JSON: {error}")
    if value is None or isinstance(value, (list, dict)):
        _usage(args, "--value-json must be a non-null JSON scalar.")
    return value


def _status_reason(
    args: argparse.Namespace,
) -> StatusReason | None:
    if args.disposition == "scored":
        return None
    actor = workflow_actor(args)
    related_kind = getattr(args, "status_related_kind", None)
    related_id = getattr(args, "status_related_id", None)
    if (related_kind is None) != (related_id is None):
        _usage(
            args,
            "--status-related-kind and --status-related-id must be supplied "
            "together.",
        )
    if related_kind is not None and not isinstance(related_kind, str):
        _usage(args, "--status-related-kind must be text.")
    if related_id is not None and not isinstance(related_id, str):
        _usage(args, "--status-related-id must be text.")
    if related_kind is None:
        related = None
    else:
        if related_id is None:
            _usage(
                args,
                "--status-related-kind and --status-related-id must be "
                "supplied together.",
            )
        related = ConcordRecordReference(
            record_kind=related_kind,
            record_id=related_id,
        )
    return StatusReason(
        reason_code=args.disposition,
        recorded_by=actor_reference(actor),
        recorded_at=datetime.now(timezone.utc).isoformat(),
        note=getattr(args, "status_reason_note", None),
        related_record=related,
    )


def _score_target(args: argparse.Namespace) -> ScoreTargetReference:
    return ScoreTargetReference(
        target_kind=args.target_kind,
        target_id=args.target_id,
        owning_system=args.target_owner,
        contract_version=args.target_contract_version,
    )


def handle_criterion_set_create(args: argparse.Namespace) -> int:
    definition = _criterion_definition(args)
    result = create_criterion_set(
        CreateCriterionSetRequest(
            class_id=args.class_id,
            activity_id=args.activity_id,
            criterion_set_id=args.criterion_set_id,
            lineage_id=args.lineage_id,
            name=_required(
                definition, "name", args, "Criterion Set definition"
            ),
            purpose=_required(
                definition, "purpose", args, "Criterion Set definition"
            ),
            revision=_required(
                definition, "revision", args, "Criterion Set definition"
            ),
            scope=_required(
                definition, "scope", args, "Criterion Set definition"
            ),
            criterion_set_kind=_required(
                definition,
                "criterion_set_kind",
                args,
                "Criterion Set definition",
            ),
            criteria=_criterion_specs(definition, args),
            status=definition.get("status", "active"),
            standards_profile_id=definition.get("standards_profile_id"),
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
        ),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print_commit(result.commit)
    print(f"Criterion Set: {result.criterion_set_id}")
    return 0


def handle_criterion_set_revise(args: argparse.Namespace) -> int:
    definition = _criterion_definition(args)
    result = revise_criterion_set(
        ReviseCriterionSetRequest(
            class_id=args.class_id,
            activity_id=args.activity_id,
            criterion_set_id=args.criterion_set_id,
            replacement_criterion_set_id=args.replacement_criterion_set_id,
            name=_required(
                definition, "name", args, "Criterion Set definition"
            ),
            purpose=_required(
                definition, "purpose", args, "Criterion Set definition"
            ),
            revision=_required(
                definition, "revision", args, "Criterion Set definition"
            ),
            scope=_required(
                definition, "scope", args, "Criterion Set definition"
            ),
            criterion_set_kind=_required(
                definition,
                "criterion_set_kind",
                args,
                "Criterion Set definition",
            ),
            criteria=_criterion_specs(definition, args),
            status=definition.get("status", "active"),
            standards_profile_id=definition.get("standards_profile_id"),
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
        ),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print_commit(result.commit)
    print(f"Replacement Criterion Set: {result.criterion_set_id}")
    return 0


def handle_criterion_set_select(args: argparse.Namespace) -> int:
    result = select_activity_criterion_sets(
        SelectActivityCriterionSetsRequest(
            class_id=args.class_id,
            activity_id=args.activity_id,
            criterion_set_ids=tuple(args.criterion_set_id),
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
        ),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print_commit(result.commit)
    print(
        "Selected Criterion Sets: "
        + (", ".join(result.criterion_set_ids) or "-")
    )
    return 0


def handle_criterion_set_list(args: argparse.Namespace) -> int:
    records = list_criterion_sets(
        args.class_id,
        args.activity_id,
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
        current_only=args.current_only,
    )
    for item in records:
        state = "current" if item.is_current else "historical"
        selected = "selected" if item.is_selected else "not-selected"
        print(
            f"{item.criterion_set_id}\t{item.lineage_id}\trev={item.revision}"
            f"\t{item.name}\t{item.criterion_set_kind}\t{item.scope}\t"
            f"{item.status}\t{state}\t{selected}\t"
            f"criteria={item.criterion_count}\t"
            f"snapshot={item.snapshot_revision}"
        )
    if not records:
        print("No Criterion Sets found.")
    return 0


def handle_criterion_set_show(args: argparse.Namespace) -> int:
    detail = show_criterion_set(
        args.class_id,
        args.activity_id,
        args.criterion_set_id,
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    item = detail.summary
    print(f"Criterion Set: {item.criterion_set_id}")
    print(f"Lineage: {item.lineage_id}")
    print(f"Revision: {item.revision}")
    print(f"Name: {item.name}")
    print(f"Purpose: {detail.purpose}")
    print(f"Kind: {item.criterion_set_kind}")
    print(f"Scope: {item.scope}")
    print(f"Status: {item.status}")
    print(f"Standards profile: {item.standards_profile_id or '-'}")
    print(f"Current: {'yes' if item.is_current else 'no'}")
    print(f"Selected: {'yes' if item.is_selected else 'no'}")
    for criterion in detail.criteria:
        print(
            "Criterion: "
            f"{criterion.criterion_id}\t{criterion.key}\t"
            f"{criterion.label}\t{criterion.criterion_kind}\t"
            f"standard={criterion.standard_id or '-'}\t"
            f"targets={','.join(criterion.supported_target_kinds)}\t"
            f"default_scale={criterion.default_scoring_scale_id or '-'}"
        )
    print(f"Snapshot revision: {item.snapshot_revision}")
    return 0


def handle_scale_create(args: argparse.Namespace) -> int:
    definition = _scale_definition(args)
    result = create_scoring_scale(
        CreateScoringScaleRequest(
            class_id=args.class_id,
            activity_id=args.activity_id,
            scoring_scale_id=args.scoring_scale_id,
            lineage_id=args.lineage_id,
            name=_required(
                definition, "name", args, "Scoring Scale definition"
            ),
            revision=_required(
                definition, "revision", args, "Scoring Scale definition"
            ),
            scale_type=_required(
                definition, "scale_type", args, "Scoring Scale definition"
            ),
            levels=_scale_levels(definition, args),
            status=definition.get("status", "active"),
            intended_use=definition.get("intended_use"),
            aggregation_guidance=definition.get("aggregation_guidance"),
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
        ),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print_commit(result.commit)
    print(f"Scoring Scale: {result.scoring_scale_id}")
    return 0


def handle_scale_revise(args: argparse.Namespace) -> int:
    definition = _scale_definition(args)
    result = revise_scoring_scale(
        ReviseScoringScaleRequest(
            class_id=args.class_id,
            activity_id=args.activity_id,
            scoring_scale_id=args.scoring_scale_id,
            replacement_scoring_scale_id=args.replacement_scoring_scale_id,
            name=_required(
                definition, "name", args, "Scoring Scale definition"
            ),
            revision=_required(
                definition, "revision", args, "Scoring Scale definition"
            ),
            scale_type=_required(
                definition, "scale_type", args, "Scoring Scale definition"
            ),
            levels=_scale_levels(definition, args),
            status=definition.get("status", "active"),
            intended_use=definition.get("intended_use"),
            aggregation_guidance=definition.get("aggregation_guidance"),
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
        ),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print_commit(result.commit)
    print(f"Replacement Scoring Scale: {result.scoring_scale_id}")
    return 0


def handle_scale_list(args: argparse.Namespace) -> int:
    records = list_scoring_scales(
        args.class_id,
        args.activity_id,
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
        current_only=args.current_only,
    )
    for item in records:
        state = "current" if item.is_current else "historical"
        print(
            f"{item.scoring_scale_id}\t{item.lineage_id}\t"
            f"rev={item.revision}\t{item.name}\t{item.scale_type}\t"
            f"{item.status}\t{state}\tlevels={item.level_count}\t"
            f"snapshot={item.snapshot_revision}"
        )
    if not records:
        print("No Scoring Scales found.")
    return 0


def handle_scale_show(args: argparse.Namespace) -> int:
    detail = show_scoring_scale(
        args.class_id,
        args.activity_id,
        args.scoring_scale_id,
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    item = detail.summary
    print(f"Scoring Scale: {item.scoring_scale_id}")
    print(f"Lineage: {item.lineage_id}")
    print(f"Revision: {item.revision}")
    print(f"Name: {item.name}")
    print(f"Type: {item.scale_type}")
    print(f"Status: {item.status}")
    print(f"Intended use: {item.intended_use or '-'}")
    print(f"Current: {'yes' if item.is_current else 'no'}")
    for level in detail.levels:
        print(
            f"Level: value={json.dumps(level.value)}\t"
            f"label={level.label}\tposition={level.position or '-'}\t"
            f"meaning={level.meaning}"
        )
    print(f"Aggregation guidance: {detail.aggregation_guidance or '-'}")
    print(f"Snapshot revision: {item.snapshot_revision}")
    return 0


def _score_request_kwargs(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "class_id": args.class_id,
        "activity_id": args.activity_id,
        "target_reference": _score_target(args),
        "criterion_id": args.criterion_id,
        "scoring_scale_id": args.scoring_scale_id,
        "disposition": args.disposition,
        "value": _score_value(args),
        "basis": args.basis,
        "rationale": args.rationale,
        "status_reason": _status_reason(args),
        "privacy_policy": _privacy(args.privacy_classification),
        "session_id": args.session_id,
        "evidence_links": _evidence_links(args),
        "expected_snapshot_revision": args.expected_snapshot,
        "actor": workflow_actor(args),
    }


def handle_score_add(args: argparse.Namespace) -> int:
    result = add_score(
        AddScoreRequest(
            score_record_id=args.score_record_id,
            **_score_request_kwargs(args),
        ),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print_commit(result.commit)
    print(f"Score Record: {result.score_record_id}")
    print(
        "Evidence Links: "
        + (", ".join(result.score_evidence_link_ids) or "-")
    )
    return 0


def handle_score_replace(args: argparse.Namespace) -> int:
    result = replace_score(
        ReplaceScoreRequest(
            score_record_id=args.score_record_id,
            replacement_score_record_id=args.replacement_score_record_id,
            correction_id=args.correction_id,
            reason=args.reason,
            correction_privacy_policy=_privacy(
                args.correction_privacy_classification
            ),
            **_score_request_kwargs(args),
        ),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print_commit(result.commit)
    print(f"Replacement Score Record: {result.score_record_id}")
    print(
        "Evidence Links: "
        + (", ".join(result.score_evidence_link_ids) or "-")
    )
    return 0


def handle_score_list(args: argparse.Namespace) -> int:
    records = list_scores(
        args.class_id,
        args.activity_id,
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
        current_only=args.current_only,
        criterion_id=args.criterion_id,
    )
    for item in records:
        target = item.target_reference
        state = "current" if item.is_current else "historical"
        rendered_value = (
            "-" if item.value is None else json.dumps(item.value)
        )
        print(
            f"{item.score_record_id}\t"
            f"{target.target_kind}:{target.target_id}\t"
            f"criterion={item.criterion_id}\t{item.score_kind}\t"
            f"{item.disposition}\tvalue={rendered_value}\t"
            f"scale={item.scoring_scale_id}\tbasis={item.basis}\t"
            f"session={item.session_id or '-'}\t{state}\t"
            f"scored_at={item.scored_at}\t"
            f"snapshot={item.snapshot_revision}"
        )
    if not records:
        print("No Score Records found.")
    return 0


def handle_score_show(args: argparse.Namespace) -> int:
    detail = show_score(
        args.class_id,
        args.activity_id,
        args.score_record_id,
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    item = detail.summary
    target = item.target_reference
    print(f"Score Record: {item.score_record_id}")
    print(
        f"Target: {target.target_kind},{target.owning_system},"
        f"{target.target_id}"
    )
    print(f"Criterion: {item.criterion_id}")
    print(f"Score kind: {item.score_kind}")
    print(f"Standard: {item.standard_id or '-'}")
    print(f"Scale: {item.scoring_scale_id}")
    print(f"Disposition: {item.disposition}")
    print(
        "Value: "
        + ("-" if item.value is None else json.dumps(item.value))
    )
    print(f"Basis: {item.basis}")
    print(f"Session: {item.session_id or '-'}")
    print(f"Moderation complete: {'yes' if item.moderation_complete else 'no'}")
    print(f"Rationale: {detail.rationale or '-'}")
    if detail.status_reason is None:
        print("Status reason: -")
    else:
        print(f"Status reason: {detail.status_reason.reason_code}")
        print(f"Status note: {detail.status_reason.note or '-'}")
    print(f"Score privacy: {detail.privacy_policy.classification}")
    print(f"Current: {'yes' if item.is_current else 'no'}")
    for link in detail.evidence_links:
        evidence = link.evidence_reference
        print(
            "Evidence Link: "
            f"{link.score_evidence_link_id}\t"
            f"{evidence.owning_system}:{evidence.evidence_kind}:"
            f"{evidence.record_id}\t"
            f"significance={link.significance or '-'}\t"
            f"moderation={link.moderation_record_id or '-'}"
        )
        print(f"Evidence relevance: {link.relevance_description}")
    print(f"Snapshot revision: {item.snapshot_revision}")
    return 0


__all__ = [
    "handle_criterion_set_create",
    "handle_criterion_set_list",
    "handle_criterion_set_revise",
    "handle_criterion_set_select",
    "handle_criterion_set_show",
    "handle_scale_create",
    "handle_scale_list",
    "handle_scale_revise",
    "handle_scale_show",
    "handle_score_add",
    "handle_score_list",
    "handle_score_replace",
    "handle_score_show",
]
