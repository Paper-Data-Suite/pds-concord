"""Teacher-facing Criterion, Scale, and Score workflows."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from pds_core.standards import StandardsLibrary

from concord.menu_context import CancelMenuAction, MenuSessionContext
from concord.menu_navigation import (
    ConcordMenuChoice,
    NavigationChoice,
    navigation_hint_with_help,
    parse_menu_navigation,
)
from concord.menu_prompts import (
    choose_group,
    choose_session,
    choose_student,
    confirm_write,
    handle_write_error,
    load_menu_standards_library,
    prompt_positive_int,
    prompt_text,
    select_many,
    select_one,
    show_result,
    slug_identifier,
)
from concord.menu_ui import (
    clear_screen,
    pause_for_user,
    print_menu_header,
    print_navigation,
)
from concord.models import (
    CorePublicationReference,
    Criterion,
    EvidenceReference,
    PrivacyPolicy,
    ScoreTargetReference,
    ScoringScaleLevel,
    StatusReason,
    SubjectReference,
)
from concord.reusable_presets import (
    CriterionSetPresetRevision,
    ScoringScalePresetRevision,
)
from concord.workflows import (
    ActivityDetail,
    ActivitySummary,
    AddScoreRequest,
    CreateCriterionSetRequest,
    CreateScoringScaleRequest,
    CriterionSetDetail,
    CriterionSpec,
    CriterionTargetIdentity,
    MaterializeScoringSetupRequest,
    PreparedPresetSave,
    ReplaceScoreRequest,
    ReviseCriterionSetRequest,
    ReviseScoringScaleRequest,
    SaveCriterionSetPresetFromActivityRequest,
    SaveScoringScalePresetFromActivityRequest,
    ScoreEvidenceLinkSpec,
    ScoreSummary,
    ScoringScaleSummary,
    SelectActivityCriterionSetsRequest,
    add_score,
    create_criterion_set,
    create_scoring_scale,
    get_preset,
    get_preset_revision,
    list_artifacts,
    list_criterion_sets,
    list_current_score_heads,
    list_groups,
    list_presets,
    list_scores,
    list_scoring_scales,
    list_sessions,
    materialize_scoring_setup,
    prepare_criterion_set_preset_from_activity,
    prepare_scoring_scale_preset_from_activity,
    prepare_scoring_setup,
    replace_score,
    resolve_read_workspace_root,
    revise_criterion_set,
    revise_scoring_scale,
    save_criterion_set_preset_from_activity,
    save_scoring_scale_preset_from_activity,
    select_activity_criterion_sets,
    show_activity,
    show_criterion_set,
    show_score,
    show_scoring_scale,
)
from concord.workflows.context import actor_reference
from concord.workflows.moderation import list_applicable_moderation_records

_TARGET_KINDS = (
    "core_student",
    "concord_group",
    "concord_session",
    "concord_activity",
    "concord_artifact_instance",
)
_DISPOSITIONS = (
    "scored",
    "insufficient_evidence",
    "absent",
    "excused",
    "not_observed",
    "not_applicable",
    "deferred",
)
_BASES = ("linked_evidence", "professional_judgment", "mixed_basis")
_SCALE_TYPES = ("numeric", "ordinal", "categorical", "binary", "teacher_defined")
_SIGNIFICANCE = (
    "primary",
    "corroborating",
    "contextual",
    "qualifying",
    "counterevidence",
    "background",
)
_PRIVACY = PrivacyPolicy(classification="teacher_restricted")


def _latest(activity: ActivitySummary) -> ActivitySummary:
    return show_activity(activity.class_id, activity.activity_id).summary


def _library() -> StandardsLibrary | None:
    return load_menu_standards_library()


def _handle_error(
    activity: ActivitySummary,
    error: Exception,
    *,
    title: str = "Scoring Error",
) -> None:
    handle_write_error(
        error,
        reload=lambda: _latest(activity),
        error_title=title,
    )


def _identifier(title: str, label: str, default: str) -> str:
    value = prompt_text(
        title,
        label,
        help_text="Use a durable synthetic identifier for this record.",
        default=default,
    )
    assert value is not None
    return value


def _choose_enum(
    title: str,
    values: tuple[str, ...],
    help_text: str,
) -> str:
    return select_one(
        title,
        values,
        tuple(item.replace("_", " ").title() for item in values),
        help_text=help_text,
    )


def _parse_json_scalar(raw: str) -> str | int | float | bool:
    try:
        value: object = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ValueError(f"Enter one valid JSON scalar: {error}") from error
    if isinstance(value, (str, int, float, bool)):
        return value
    raise ValueError("Enter a non-null JSON string, number, or boolean.")


def _prompt_json_scalar(
    title: str,
    label: str,
    *,
    help_text: str,
) -> str | int | float | bool:
    while True:
        raw = prompt_text(
            title,
            label,
            help_text=help_text,
        )
        assert raw is not None
        try:
            return _parse_json_scalar(raw)
        except ValueError as error:
            show_result(title, (str(error),))


def _optional_text(
    title: str,
    label: str,
    help_text: str,
) -> str | None:
    return prompt_text(
        title,
        label,
        help_text=help_text,
        optional=True,
    )


def _choose_scale(activity: ActivitySummary) -> ScoringScaleSummary:
    scales = list_scoring_scales(
        activity.class_id,
        activity.activity_id,
        standards_library=_library(),
        current_only=False,
    )
    if not scales:
        raise ValueError("Create a Scoring Scale before recording this Score.")
    return select_one(
        "Choose a Scoring Scale",
        scales,
        tuple(
            f"{item.name} ({item.scoring_scale_id}, rev {item.revision})"
            for item in scales
        ),
        help_text=(
            "Choose the exact native Scale revision. Concord does not normalize "
            "or infer equivalence between Scales."
        ),
    )


def _build_levels(scale_type: str) -> tuple[ScoringScaleLevel, ...]:
    count = prompt_positive_int(
        "Scoring Scale",
        "Number of levels",
        help_text="Every native Scale level is recorded exactly.",
        default=2 if scale_type == "binary" else 4,
    )
    if scale_type == "binary" and count != 2:
        raise ValueError("A binary Scale requires exactly two levels.")
    levels: list[ScoringScaleLevel] = []
    for index in range(1, count + 1):
        value = _prompt_json_scalar(
            f"Scale Level {index}",
            "Exact JSON value",
            help_text=(
                "Examples: 1, 1.0, \"1\", and true are distinct native values."
            ),
        )
        label = prompt_text(
            f"Scale Level {index}",
            "Label",
            help_text="Teacher-facing label for this exact native value.",
        )
        meaning = prompt_text(
            f"Scale Level {index}",
            "Meaning",
            help_text="Describe what this level means in this Scale.",
        )
        assert label is not None and meaning is not None
        position = index if scale_type == "ordinal" else None
        description = _optional_text(
            f"Scale Level {index}",
            "Description",
            "Optional additional description.",
        )
        levels.append(
            ScoringScaleLevel(
                value=value,
                label=label,
                meaning=meaning,
                position=position,
                description=description,
            )
        )
    return tuple(levels)


def _create_scale(
    activity: ActivitySummary,
    state: MenuSessionContext,
) -> None:
    try:
        current = _latest(activity)
        name = prompt_text(
            "Create Scoring Scale",
            "Scale name",
            help_text="Name this exact native scoring Scale.",
        )
        assert name is not None
        scale_id = _identifier(
            "Create Scoring Scale",
            "Scoring Scale ID",
            slug_identifier(name, f"scale-{uuid4().hex[:8]}"),
        )
        lineage_id = _identifier(
            "Create Scoring Scale",
            "Lineage ID",
            f"{scale_id}-lineage",
        )
        scale_type = _choose_enum(
            "Scale Type",
            _SCALE_TYPES,
            "Choose the Scale's native value semantics.",
        )
        levels = _build_levels(scale_type)
        intended_use = _optional_text(
            "Create Scoring Scale",
            "Intended use",
            "Optional teacher-facing intended-use guidance.",
        )
        aggregation = _optional_text(
            "Create Scoring Scale",
            "Aggregation guidance",
            "Optional descriptive guidance only; Concord does not aggregate Grades.",
        )
        if not confirm_write(
            "Create Scoring Scale",
            "CREATE",
            (
                f"Activity: {current.title}",
                f"Scale: {name}",
                f"ID: {scale_id}",
                f"Type: {scale_type}",
                f"Levels: {len(levels)}",
                "No Grade calculation or cross-scale normalization will occur.",
            ),
        ):
            return
        result = create_scoring_scale(
            CreateScoringScaleRequest(
                class_id=current.class_id,
                activity_id=current.activity_id,
                scoring_scale_id=scale_id,
                lineage_id=lineage_id,
                name=name,
                revision=1,
                scale_type=scale_type,
                levels=levels,
                status="active",
                intended_use=intended_use,
                aggregation_guidance=aggregation,
                expected_snapshot_revision=current.snapshot_revision,
                actor=state.require_actor(),
            ),
            standards_library=_library(),
        )
        show_result(
            "Scoring Scale Created",
            (
                f"Scale: {result.scoring_scale_id}",
                f"Snapshot: {result.commit.snapshot_revision}",
            ),
        )
    except CancelMenuAction:
        return
    except Exception as error:
        _handle_error(activity, error)


def _revise_scale(
    activity: ActivitySummary,
    state: MenuSessionContext,
) -> None:
    try:
        current = _latest(activity)
        scales = list_scoring_scales(
            current.class_id,
            current.activity_id,
            standards_library=_library(),
            current_only=True,
        )
        predecessor = select_one(
            "Revise Scoring Scale",
            scales,
            tuple(
                f"{item.name} ({item.scoring_scale_id}, rev {item.revision})"
                for item in scales
            ),
            help_text="Choose a current Scale lineage head to revise.",
        )
        detail = show_scoring_scale(
            current.class_id,
            current.activity_id,
            predecessor.scoring_scale_id,
            standards_library=_library(),
        )
        name = prompt_text(
            "Revise Scoring Scale",
            "Scale name",
            help_text="Name the successor Scale revision.",
            default=predecessor.name,
        )
        assert name is not None
        replacement_id = _identifier(
            "Revise Scoring Scale",
            "Replacement Scoring Scale ID",
            f"{predecessor.scoring_scale_id}-r{predecessor.revision + 1}",
        )
        scale_type = _choose_enum(
            "Scale Type",
            _SCALE_TYPES,
            "Choose the successor Scale's exact native semantics.",
        )
        levels = _build_levels(scale_type)
        intended_use = _optional_text(
            "Revise Scoring Scale",
            "Intended use",
            "Optional successor intended-use guidance.",
        )
        aggregation = _optional_text(
            "Revise Scoring Scale",
            "Aggregation guidance",
            "Optional descriptive guidance; Concord does not calculate Grades.",
        )
        if not confirm_write(
            "Revise Scoring Scale",
            "REVISE",
            (
                f"Current: {detail.summary.scoring_scale_id}",
                f"Replacement: {replacement_id}",
                f"Revision: {predecessor.revision + 1}",
                f"Type: {scale_type}",
                f"Levels: {len(levels)}",
            ),
        ):
            return
        result = revise_scoring_scale(
            ReviseScoringScaleRequest(
                class_id=current.class_id,
                activity_id=current.activity_id,
                scoring_scale_id=predecessor.scoring_scale_id,
                replacement_scoring_scale_id=replacement_id,
                name=name,
                revision=predecessor.revision + 1,
                scale_type=scale_type,
                levels=levels,
                status="active",
                intended_use=intended_use,
                aggregation_guidance=aggregation,
                expected_snapshot_revision=current.snapshot_revision,
                actor=state.require_actor(),
            ),
            standards_library=_library(),
        )
        show_result(
            "Scoring Scale Revised",
            (
                f"Replacement: {result.scoring_scale_id}",
                f"Snapshot: {result.commit.snapshot_revision}",
            ),
        )
    except CancelMenuAction:
        return
    except Exception as error:
        _handle_error(activity, error)


def _browse_scales(activity: ActivitySummary) -> None:
    try:
        scales = list_scoring_scales(
            activity.class_id,
            activity.activity_id,
            standards_library=_library(),
            current_only=False,
        )
        selected = select_one(
            "Scoring Scales",
            scales,
            tuple(
                f"{item.name} ({item.scoring_scale_id}, rev {item.revision}) "
                f"[{'current' if item.is_current else 'historical'}]"
                for item in scales
            ),
            help_text="Choose one exact Scale revision for detail.",
        )
        detail = show_scoring_scale(
            activity.class_id,
            activity.activity_id,
            selected.scoring_scale_id,
            standards_library=_library(),
        )
        lines = [
            f"Scale: {selected.scoring_scale_id}",
            f"Lineage: {selected.lineage_id}",
            f"Revision: {selected.revision}",
            f"Type: {selected.scale_type}",
            f"Status: {selected.status}",
        ]
        lines.extend(
            f"{json.dumps(level.value)} - {level.label}: {level.meaning}"
            for level in detail.levels
        )
        show_result("Scoring Scale Detail", tuple(lines))
    except CancelMenuAction:
        return
    except Exception as error:
        show_result("Scoring Scale Error", (str(error),))


def _criterion_kind(set_kind: str) -> str:
    if set_kind == "standard_backed":
        return "standard_backed"
    if set_kind == "local":
        return "local"
    return _choose_enum(
        "Criterion Kind",
        ("standard_backed", "local"),
        "Mixed Criterion Sets may contain both kinds.",
    )


def _criterion_standard(
    activity_detail: ActivityDetail,
    kind: str,
) -> str | None:
    if kind != "standard_backed":
        return None
    focus = tuple(activity_detail.focus_standard_ids)
    if not focus:
        raise ValueError(
            "This Activity has no Focus Standards for a standard-backed Criterion."
        )
    return select_one(
        "Governing Focus Standard",
        focus,
        focus,
        help_text=(
            "Choose exactly one Core Focus Standard governed by this Criterion."
        ),
    )


def _criterion_targets() -> tuple[str, ...]:
    return select_many(
        "Criterion Target Kinds",
        _TARGET_KINDS,
        tuple(item.replace("_", " ").title() for item in _TARGET_KINDS),
        help_text=(
            "Select every target kind this Criterion explicitly permits. "
            "Targets are never inferred from Authors, Subjects, or Groups."
        ),
    )


def _default_scale(activity: ActivitySummary) -> str | None:
    scales = list_scoring_scales(
        activity.class_id,
        activity.activity_id,
        standards_library=_library(),
        current_only=True,
    )
    if not scales:
        return None
    values = ("", *(item.scoring_scale_id for item in scales))
    labels = (
        "No default Scale",
        *(
            f"{item.name} ({item.scoring_scale_id}, rev {item.revision})"
            for item in scales
        ),
    )
    selected_id = select_one(
        "Default Scoring Scale",
        values,
        labels,
        help_text=(
            "A default is descriptive convenience. The teacher still explicitly "
            "chooses the exact Scale when recording a Score."
        ),
    )
    return selected_id or None


def _build_criteria(
    activity: ActivitySummary,
    criterion_set_id: str,
    set_kind: str,
) -> tuple[CriterionSpec, ...]:
    detail = show_activity(activity.class_id, activity.activity_id)
    count = prompt_positive_int(
        "Criterion Set",
        "Number of Criteria",
        help_text="Create the ordered Criteria in this immutable Set revision.",
        default=1,
    )
    criteria: list[CriterionSpec] = []
    for index in range(1, count + 1):
        key = prompt_text(
            f"Criterion {index}",
            "Key",
            help_text="Enter a short stable Criterion key.",
        )
        label = prompt_text(
            f"Criterion {index}",
            "Label",
            help_text="Enter the teacher-facing Criterion label.",
        )
        definition = prompt_text(
            f"Criterion {index}",
            "Definition",
            help_text="Define the judgment this Criterion represents.",
        )
        assert key is not None and label is not None and definition is not None
        criterion_id = _identifier(
            f"Criterion {index}",
            "Criterion ID",
            slug_identifier(
                f"{criterion_set_id}-{key}",
                f"criterion-{uuid4().hex[:8]}",
            ),
        )
        kind = _criterion_kind(set_kind)
        standard_id = _criterion_standard(detail, kind)
        targets = _criterion_targets()
        default_scale_id = _default_scale(activity)
        criteria.append(
            CriterionSpec(
                criterion_id=criterion_id,
                key=key,
                label=label,
                definition=definition,
                criterion_kind=kind,
                supported_target_kinds=targets,
                standard_id=standard_id,
                default_scoring_scale_id=default_scale_id,
                status="active",
            )
        )
    return tuple(criteria)


def _create_criterion_set(
    activity: ActivitySummary,
    state: MenuSessionContext,
) -> None:
    try:
        current = _latest(activity)
        detail = show_activity(current.class_id, current.activity_id)
        name = prompt_text(
            "Create Criterion Set",
            "Set name",
            help_text="Name this immutable ordered Criterion collection.",
        )
        purpose = prompt_text(
            "Create Criterion Set",
            "Purpose",
            help_text="Describe what this Criterion Set is for.",
        )
        assert name is not None and purpose is not None
        criterion_set_id = _identifier(
            "Create Criterion Set",
            "Criterion Set ID",
            slug_identifier(name, f"criterion-set-{uuid4().hex[:8]}"),
        )
        lineage_id = _identifier(
            "Create Criterion Set",
            "Lineage ID",
            f"{criterion_set_id}-lineage",
        )
        scope = _choose_enum(
            "Criterion Set Scope",
            ("activity_specific", "reusable"),
            (
                "Scope is semantic metadata in v0.2; reusable does not create a "
                "cross-Activity library."
            ),
        )
        kind = _choose_enum(
            "Criterion Set Kind",
            ("standard_backed", "local", "mixed"),
            "Choose the kinds of Criteria this Set may contain.",
        )
        criteria = _build_criteria(current, criterion_set_id, kind)
        profile_id = (
            detail.standards_profile_id
            if kind in {"standard_backed", "mixed"}
            else None
        )
        if not confirm_write(
            "Create Criterion Set",
            "CREATE",
            (
                f"Activity: {current.title}",
                f"Set: {name}",
                f"ID: {criterion_set_id}",
                f"Kind: {kind}",
                f"Scope: {scope}",
                f"Criteria: {len(criteria)}",
            ),
        ):
            return
        result = create_criterion_set(
            CreateCriterionSetRequest(
                class_id=current.class_id,
                activity_id=current.activity_id,
                criterion_set_id=criterion_set_id,
                lineage_id=lineage_id,
                name=name,
                purpose=purpose,
                revision=1,
                scope=scope,
                criterion_set_kind=kind,
                criteria=criteria,
                status="active",
                standards_profile_id=profile_id,
                expected_snapshot_revision=current.snapshot_revision,
                actor=state.require_actor(),
            ),
            standards_library=_library(),
        )
        show_result(
            "Criterion Set Created",
            (
                f"Criterion Set: {result.criterion_set_id}",
                f"Snapshot: {result.commit.snapshot_revision}",
            ),
        )
    except CancelMenuAction:
        return
    except Exception as error:
        _handle_error(activity, error)


def _revise_criterion_set(
    activity: ActivitySummary,
    state: MenuSessionContext,
) -> None:
    try:
        current = _latest(activity)
        activity_detail = show_activity(current.class_id, current.activity_id)
        sets = list_criterion_sets(
            current.class_id,
            current.activity_id,
            standards_library=_library(),
            current_only=True,
        )
        predecessor = select_one(
            "Revise Criterion Set",
            sets,
            tuple(
                f"{item.name} ({item.criterion_set_id}, rev {item.revision})"
                for item in sets
            ),
            help_text="Choose a current Criterion Set lineage head to revise.",
        )
        predecessor_detail = show_criterion_set(
            current.class_id,
            current.activity_id,
            predecessor.criterion_set_id,
            standards_library=_library(),
        )
        replacement_id = _identifier(
            "Revise Criterion Set",
            "Replacement Criterion Set ID",
            f"{predecessor.criterion_set_id}-r{predecessor.revision + 1}",
        )
        name = prompt_text(
            "Revise Criterion Set",
            "Set name",
            help_text="Name the successor Set revision.",
            default=predecessor.name,
        )
        purpose = prompt_text(
            "Revise Criterion Set",
            "Purpose",
            help_text="Describe the successor Set's purpose.",
            default=predecessor_detail.purpose,
        )
        assert name is not None and purpose is not None
        scope = _choose_enum(
            "Criterion Set Scope",
            ("activity_specific", "reusable"),
            "Choose the successor Set's semantic scope.",
        )
        kind = _choose_enum(
            "Criterion Set Kind",
            ("standard_backed", "local", "mixed"),
            "Choose the successor Set's Criterion kinds.",
        )
        criteria = _build_criteria(current, replacement_id, kind)
        profile_id = (
            activity_detail.standards_profile_id
            if kind in {"standard_backed", "mixed"}
            else None
        )
        if not confirm_write(
            "Revise Criterion Set",
            "REVISE",
            (
                f"Current: {predecessor.criterion_set_id}",
                f"Replacement: {replacement_id}",
                f"Revision: {predecessor.revision + 1}",
                f"Criteria: {len(criteria)}",
            ),
        ):
            return
        result = revise_criterion_set(
            ReviseCriterionSetRequest(
                class_id=current.class_id,
                activity_id=current.activity_id,
                criterion_set_id=predecessor.criterion_set_id,
                replacement_criterion_set_id=replacement_id,
                name=name,
                purpose=purpose,
                revision=predecessor.revision + 1,
                scope=scope,
                criterion_set_kind=kind,
                criteria=criteria,
                status="active",
                standards_profile_id=profile_id,
                expected_snapshot_revision=current.snapshot_revision,
                actor=state.require_actor(),
            ),
            standards_library=_library(),
        )
        show_result(
            "Criterion Set Revised",
            (
                f"Replacement: {result.criterion_set_id}",
                f"Snapshot: {result.commit.snapshot_revision}",
            ),
        )
    except CancelMenuAction:
        return
    except Exception as error:
        _handle_error(activity, error)


def _select_criterion_sets(
    activity: ActivitySummary,
    state: MenuSessionContext,
) -> None:
    try:
        current = _latest(activity)
        sets = list_criterion_sets(
            current.class_id,
            current.activity_id,
            standards_library=_library(),
            current_only=False,
        )
        selected = select_many(
            "Select Criterion Sets",
            sets,
            tuple(
                f"{item.name} ({item.criterion_set_id}, rev {item.revision}) "
                f"[{'current' if item.is_current else 'historical'}]"
                for item in sets
            ),
            help_text=(
                "Select the exact immutable Set revisions this Activity may use "
                "for future Scores."
            ),
        )
        selected_ids = tuple(item.criterion_set_id for item in selected)
        if not confirm_write(
            "Select Criterion Sets",
            "SELECT",
            (
                f"Activity: {current.title}",
                f"Selected Sets: {len(selected_ids)}",
                *selected_ids,
            ),
        ):
            return
        result = select_activity_criterion_sets(
            SelectActivityCriterionSetsRequest(
                class_id=current.class_id,
                activity_id=current.activity_id,
                criterion_set_ids=selected_ids,
                expected_snapshot_revision=current.snapshot_revision,
                actor=state.require_actor(),
            ),
            standards_library=_library(),
        )
        show_result(
            "Criterion Sets Selected",
            (
                f"Selected: {len(result.criterion_set_ids)}",
                f"Snapshot: {result.commit.snapshot_revision}",
            ),
        )
    except CancelMenuAction:
        return
    except Exception as error:
        _handle_error(activity, error)


def _browse_criterion_sets(activity: ActivitySummary) -> None:
    try:
        sets = list_criterion_sets(
            activity.class_id,
            activity.activity_id,
            standards_library=_library(),
            current_only=False,
        )
        selected = select_one(
            "Criterion Sets",
            sets,
            tuple(
                f"{item.name} ({item.criterion_set_id}, rev {item.revision}) "
                f"[{'selected' if item.is_selected else 'not selected'}]"
                for item in sets
            ),
            help_text="Choose an exact Criterion Set revision for detail.",
        )
        detail = show_criterion_set(
            activity.class_id,
            activity.activity_id,
            selected.criterion_set_id,
            standards_library=_library(),
        )
        lines = [
            f"Criterion Set: {selected.criterion_set_id}",
            f"Revision: {selected.revision}",
            f"Kind: {selected.criterion_set_kind}",
            f"Scope: {selected.scope}",
            f"Selected: {'yes' if selected.is_selected else 'no'}",
            f"Purpose: {detail.purpose}",
        ]
        lines.extend(
            f"{item.key} - {item.label} [{item.criterion_kind}]"
            for item in detail.criteria
        )
        show_result("Criterion Set Detail", tuple(lines))
    except CancelMenuAction:
        return
    except Exception as error:
        show_result("Criterion Set Error", (str(error),))


def _selected_criteria(
    activity: ActivitySummary,
) -> tuple[tuple[CriterionSetDetail, Criterion], ...]:
    summaries = list_criterion_sets(
        activity.class_id,
        activity.activity_id,
        standards_library=_library(),
        current_only=False,
    )
    selected_ids = tuple(
        item.criterion_set_id for item in summaries if item.is_selected
    )
    result: list[tuple[CriterionSetDetail, Criterion]] = []
    for set_id in selected_ids:
        criterion_set = show_criterion_set(
            activity.class_id,
            activity.activity_id,
            set_id,
            standards_library=_library(),
        )
        result.extend((criterion_set, item) for item in criterion_set.criteria)
    return tuple(result)


def _choose_criterion(activity: ActivitySummary) -> Criterion:
    pairs = _selected_criteria(activity)
    if not pairs:
        raise ValueError(
            "Select at least one Criterion Set before recording a Score."
        )
    return select_one(
        "Choose a Criterion",
        pairs,
        tuple(
            f"{criterion.label} ({criterion.criterion_id}) "
            f"[{criterion.criterion_kind}]"
            for _, criterion in pairs
        ),
        help_text=(
            "Choose one explicit Criterion. Concord does not infer a Criterion "
            "from evidence."
        ),
    )[1]


def _choose_target(
    activity: ActivitySummary,
    criterion: Criterion,
) -> ScoreTargetReference:
    supported = tuple(criterion.supported_target_kinds)
    target_kind = _choose_enum(
        "Score Target Kind",
        supported,
        "Choose the exact target kind permitted by this Criterion.",
    )
    if target_kind == "core_student":
        workspace = resolve_read_workspace_root()
        if workspace is None:
            raise ValueError("The Paper Data Suite workspace is unavailable.")
        student = choose_student(workspace, activity.class_id)
        return ScoreTargetReference(
            target_kind=target_kind,
            target_id=student.student_id,
            owning_system="core",
        )
    if target_kind == "concord_group":
        groups = list_groups(activity.class_id, activity.activity_id)
        group = choose_group(groups, title="Choose Score Target Group")
        return ScoreTargetReference(
            target_kind=target_kind,
            target_id=group.group_id,
            owning_system="concord",
        )
    if target_kind == "concord_session":
        sessions = list_sessions(activity.class_id, activity.activity_id)
        session = choose_session(sessions, title="Choose Score Target Session")
        return ScoreTargetReference(
            target_kind=target_kind,
            target_id=session.session_id,
            owning_system="concord",
        )
    if target_kind == "concord_activity":
        return ScoreTargetReference(
            target_kind=target_kind,
            target_id=activity.activity_id,
            owning_system="concord",
        )
    artifacts = list_artifacts(activity.class_id, activity.activity_id)
    artifact = select_one(
        "Choose Score Target Artifact",
        artifacts,
        tuple(
            f"{item.artifact_instance_id} [{item.artifact_status}]"
            for item in artifacts
        ),
        help_text="Choose one explicit Artifact Instance target.",
    )
    return ScoreTargetReference(
        target_kind=target_kind,
        target_id=artifact.artifact_instance_id,
        owning_system="concord",
    )


def _optional_score_session(activity: ActivitySummary) -> str | None:
    sessions = list_sessions(activity.class_id, activity.activity_id)
    if not sessions:
        return None
    values = ("", *(item.session_id for item in sessions))
    labels = (
        "No separate Score Session context",
        *(
            f"{item.sequence}. {item.label or item.session_id} - {item.status}"
            for item in sessions
        ),
    )
    selected = select_one(
        "Score Session Context",
        values,
        labels,
        help_text=(
            "Optionally record one explicit Session context for the Score. "
            "This is separate from the Score target."
        ),
    )
    return selected or None


def _choose_disposition() -> str:
    return _choose_enum(
        "Score Disposition",
        _DISPOSITIONS,
        (
            "Exceptional states are not low Scores. Choose scored only when an "
            "exact native Scale value is being recorded."
        ),
    )


def _choose_basis() -> str:
    return _choose_enum(
        "Score Basis",
        _BASES,
        (
            "Professional judgment uses rationale and no formal Evidence Links; "
            "linked or mixed basis requires explicit Evidence Links."
        ),
    )


def _subject_context() -> tuple[SubjectReference, ...]:
    count_text = _optional_text(
        "Evidence Subject Context",
        "Number of explicit Subjects",
        (
            "Leave blank for no Subject context. Enter a count only when the "
            "evidence use has an explicit Subject scope."
        ),
    )
    if count_text is None:
        return ()
    try:
        count = int(count_text)
    except ValueError as error:
        raise ValueError("Subject count must be a whole number.") from error
    if count < 1:
        raise ValueError("Subject count must be positive when supplied.")
    subjects: list[SubjectReference] = []
    for index in range(1, count + 1):
        kind = prompt_text(
            f"Evidence Subject {index}",
            "Subject kind",
            help_text="Enter the exact native Subject kind.",
        )
        owner = prompt_text(
            f"Evidence Subject {index}",
            "Owning system",
            help_text="Enter the system that owns this Subject identity.",
        )
        subject_id = prompt_text(
            f"Evidence Subject {index}",
            "Subject ID",
            help_text="Enter the exact Subject identifier.",
        )
        assert kind is not None and owner is not None and subject_id is not None
        subjects.append(
            SubjectReference(
                subject_kind=kind,
                subject_id=subject_id,
                owning_system=owner,
            )
        )
    return tuple(subjects)


def _evidence_reference(
    index: int,
) -> tuple[EvidenceReference, tuple[SubjectReference, ...]]:
    kind = _choose_enum(
        f"Evidence {index} Kind",
        (
            "artifact_instance",
            "artifact_page",
            "scoreform_result",
            "quillan_response",
            "external_record",
        ),
        "Choose the exact evidence source kind.",
    )
    default_owner = "concord" if kind.startswith("artifact_") else None
    owner = prompt_text(
        f"Evidence {index}",
        "Owning system",
        help_text="Enter the evidence producer/owner.",
        default=default_owner,
    )
    record_id = prompt_text(
        f"Evidence {index}",
        "Record ID",
        help_text="Enter the exact immutable evidence record identifier.",
    )
    assert owner is not None and record_id is not None
    contract = _optional_text(
        f"Evidence {index}",
        "Contract version",
        "Optional exact producer contract version.",
    )
    immutable: str | None = None
    publication: CorePublicationReference | None = None
    if owner != "concord":
        immutable = _optional_text(
            f"Evidence {index}",
            "Immutable source version",
            "Enter the exact immutable producer version when available.",
        )
        publication_id = _optional_text(
            f"Evidence {index}",
            "Core Publication ID",
            "Optional exact public Core Publication reference.",
        )
        if publication_id is not None:
            schema = _optional_text(
                f"Evidence {index}",
                "Publication schema version",
                "Optional exact publication schema version.",
            )
            publication = CorePublicationReference(
                publication_id=publication_id,
                publication_schema_version=schema,
            )
        if immutable is None and publication is None:
            raise ValueError(
                "External evidence requires an immutable source version or "
                "exact Core Publication reference."
            )
    moderation = _choose_enum(
        f"Evidence {index} Moderation Declaration",
        ("required", "not_required"),
        (
            "Declare the evidence-level requirement explicitly. Current Artifact "
            "Review may still require Moderation even when this says not required."
        ),
    )
    subjects = _subject_context()
    return (
        EvidenceReference(
            evidence_kind=kind,
            owning_system=owner,
            record_id=record_id,
            contract_version=contract,
            source_publication_reference=publication,
            immutable_source_version=immutable,
            moderation_requirement=moderation,
        ),
        subjects,
    )


def _evidence_links(
    activity: ActivitySummary,
    basis: str,
) -> tuple[ScoreEvidenceLinkSpec, ...]:
    if basis == "professional_judgment":
        return ()
    count = prompt_positive_int(
        "Score Evidence",
        "Number of Evidence Links",
        help_text=(
            "Every linked or mixed-basis Score requires at least one explicit "
            "Evidence Link."
        ),
        default=1,
    )
    result: list[ScoreEvidenceLinkSpec] = []
    for index in range(1, count + 1):
        reference, subjects = _evidence_reference(index)
        relevance = prompt_text(
            f"Evidence {index}",
            "Relevance description",
            help_text="Explain how this evidence relates to this Score judgment.",
        )
        assert relevance is not None
        significance = _choose_enum(
            f"Evidence {index} Significance",
            _SIGNIFICANCE,
            "Describe the evidence's role without numeric weighting.",
        )
        moderation_id: str | None = None
        applicable = list_applicable_moderation_records(
            activity.class_id,
            activity.activity_id,
            reference,
            subject_context=subjects,
            standards_library=_library(),
        )
        if applicable:
            moderation_ids = (
                "",
                *(item.moderation_record_id for item in applicable),
            )
            labels = (
                "No Moderation Record",
                *(
                    f"{item.moderation_record_id} - {item.status} / "
                    f"{item.permitted_use}"
                    for item in applicable
                ),
            )
            selected_id = select_one(
                f"Evidence {index} Moderation",
                moderation_ids,
                labels,
                help_text=(
                    "Choose an explicit applicable Moderation Record when this "
                    "consequential evidence use requires one."
                ),
            )
            moderation_id = selected_id or None
        result.append(
            ScoreEvidenceLinkSpec(
                score_evidence_link_id=f"score-link-{uuid4().hex}",
                evidence_reference=reference,
                relevance_description=relevance,
                subject_context=subjects,
                significance=significance,
                moderation_record_id=moderation_id,
            )
        )
    return tuple(result)


@dataclass(frozen=True, slots=True)
class _ScoreDraft:
    criterion: Criterion
    target: ScoreTargetReference
    scale: ScoringScaleSummary
    session_id: str | None
    disposition: str
    basis: str
    value: str | int | float | bool | None
    rationale: str | None
    links: tuple[ScoreEvidenceLinkSpec, ...]
    status_reason: StatusReason | None


def _score_components(
    activity: ActivitySummary,
    state: MenuSessionContext,
) -> _ScoreDraft:
    criterion = _choose_criterion(activity)
    target = _choose_target(activity, criterion)
    scale = _choose_scale(activity)
    session_id = _optional_score_session(activity)
    disposition = _choose_disposition()
    basis = _choose_basis()
    value: str | int | float | bool | None = None
    if disposition == "scored":
        detail = show_scoring_scale(
            activity.class_id,
            activity.activity_id,
            scale.scoring_scale_id,
            standards_library=_library(),
        )
        selected_level = select_one(
            "Choose Exact Score Value",
            detail.levels,
            tuple(
                f"{json.dumps(item.value)} - {item.label}"
                for item in detail.levels
            ),
            help_text=(
                "Choose one exact native Scale value. Concord does not suggest "
                "a value from the evidence."
            ),
        )
        value = selected_level.value
    rationale: str | None = None
    if basis in {"professional_judgment", "mixed_basis"}:
        rationale = prompt_text(
            "Professional Judgment",
            "Rationale",
            help_text=(
                "Record the teacher's professional-judgment rationale. This "
                "does not fabricate a duplicate teacher_rationale evidence record."
            ),
        )
    else:
        rationale = _optional_text(
            "Score",
            "Rationale",
            "Optional private rationale for the linked-evidence judgment.",
        )
    links = _evidence_links(activity, basis)
    reason: StatusReason | None = None
    if disposition != "scored":
        note = _optional_text(
            "Non-score Disposition",
            "Status reason note",
            "Optional context for this exceptional non-score state.",
        )
        actor = state.require_actor()
        reason = StatusReason(
            reason_code=disposition,
            recorded_by=actor_reference(actor),
            recorded_at=datetime.now(timezone.utc).isoformat(),
            note=note,
        )
    return _ScoreDraft(
        criterion=criterion,
        target=target,
        scale=scale,
        session_id=session_id,
        disposition=disposition,
        basis=basis,
        value=value,
        rationale=rationale,
        links=links,
        status_reason=reason,
    )


def _score_confirmation_lines(
    activity: ActivitySummary,
    target: ScoreTargetReference,
    criterion: Criterion,
    scale: ScoringScaleSummary,
    session_id: str | None,
    disposition: str,
    value: str | int | float | bool | None,
    basis: str,
    evidence_count: int,
) -> tuple[str, ...]:
    lines = [
        f"Activity: {activity.title}",
        f"Target: {target.target_kind}:{target.target_id}",
        f"Criterion: {criterion.label} ({criterion.criterion_id})",
        f"Scale: {scale.name} ({scale.scoring_scale_id})",
        f"Session context: {session_id or '-'}",
        f"Disposition: {disposition}",
        f"Value: {'-' if value is None else json.dumps(value)}",
        f"Basis: {basis}",
        f"Evidence Links: {evidence_count}",
    ]
    if target.target_kind == "concord_group":
        lines.extend(
            (
                "GROUP SCORE WARNING:",
                "This Score applies only to the Group.",
                "It creates no individual student Scores.",
            )
        )
    return tuple(lines)


def _record_score(
    activity: ActivitySummary,
    state: MenuSessionContext,
) -> None:
    try:
        current = _latest(activity)
        if current.scoring_orientation == "evidence_only":
            raise ValueError("Evidence-only Activities cannot record Scores.")
        draft = _score_components(current, state)
        score_id = _identifier(
            "Record a Score",
            "Score Record ID",
            f"score-{uuid4().hex}",
        )
        if not confirm_write(
            "Record a Score",
            "SCORE",
            _score_confirmation_lines(
                current,
                draft.target,
                draft.criterion,
                draft.scale,
                draft.session_id,
                draft.disposition,
                draft.value,
                draft.basis,
                len(draft.links),
            ),
        ):
            return
        result = add_score(
            AddScoreRequest(
                class_id=current.class_id,
                activity_id=current.activity_id,
                score_record_id=score_id,
                target_reference=draft.target,
                criterion_id=draft.criterion.criterion_id,
                scoring_scale_id=draft.scale.scoring_scale_id,
                session_id=draft.session_id,
                disposition=draft.disposition,
                basis=draft.basis,
                privacy_policy=_PRIVACY,
                expected_snapshot_revision=current.snapshot_revision,
                actor=state.require_actor(),
                value=draft.value,
                rationale=draft.rationale,
                status_reason=draft.status_reason,
                evidence_links=draft.links,
            ),
            standards_library=_library(),
        )
        show_result(
            "Score Recorded",
            (
                f"Score: {result.score_record_id}",
                f"Evidence Links: {len(result.score_evidence_link_ids)}",
                f"Snapshot: {result.commit.snapshot_revision}",
            ),
        )
    except CancelMenuAction:
        return
    except Exception as error:
        _handle_error(activity, error)


def _score_label(item: ScoreSummary) -> str:
    target = item.target_reference
    value = "-" if item.value is None else json.dumps(item.value)
    return (
        f"{item.score_record_id} - {target.target_kind}:{target.target_id} - "
        f"{item.disposition} {value} [{item.criterion_id}] "
        f"{'current' if item.is_current else 'historical'}"
    )


def _browse_scores(activity: ActivitySummary) -> None:
    try:
        scores = list_scores(
            activity.class_id,
            activity.activity_id,
            standards_library=_library(),
            current_only=False,
        )
        selected = select_one(
            "Scores",
            scores,
            tuple(_score_label(item) for item in scores),
            help_text=(
                "Choose one exact Score revision. Current and historical Scores "
                "remain visible; no latest-by-target heuristic is applied."
            ),
        )
        detail = show_score(
            activity.class_id,
            activity.activity_id,
            selected.score_record_id,
            standards_library=_library(),
        )
        lines = [
            f"Score: {selected.score_record_id}",
            (
                "Target: "
                f"{selected.target_reference.target_kind}:"
                f"{selected.target_reference.target_id}"
            ),
            f"Criterion: {selected.criterion_id}",
            f"Disposition: {selected.disposition}",
            (
                "Value: "
                + ("-" if selected.value is None else json.dumps(selected.value))
            ),
            f"Scale: {selected.scoring_scale_id}",
            f"Basis: {selected.basis}",
            f"Rationale: {detail.rationale or '-'}",
            f"Evidence Links: {len(detail.evidence_links)}",
        ]
        if detail.status_reason is not None:
            lines.append(
                f"Status Reason: {detail.status_reason.reason_code}"
            )
        show_result("Score Detail", tuple(lines))
    except CancelMenuAction:
        return
    except Exception as error:
        show_result("Score Error", (str(error),))


def _revise_score(
    activity: ActivitySummary,
    state: MenuSessionContext,
) -> None:
    try:
        current = _latest(activity)
        heads = list_current_score_heads(
            current.class_id,
            current.activity_id,
            standards_library=_library(),
        )
        predecessor = select_one(
            "Revise a Score",
            heads,
            tuple(_score_label(item) for item in heads),
            help_text="Choose the current Score lineage head to revise.",
        )
        draft = _score_components(current, state)
        replacement_id = _identifier(
            "Revise a Score",
            "Replacement Score Record ID",
            f"{predecessor.score_record_id}-revision-{uuid4().hex[:8]}",
        )
        correction_id = _identifier(
            "Revise a Score",
            "Correction ID",
            f"correction-{uuid4().hex}",
        )
        correction_reason = prompt_text(
            "Revise a Score",
            "Revision reason",
            help_text="Explain why this explicit Score successor is being recorded.",
        )
        assert correction_reason is not None
        lines = (
            f"Current Score: {predecessor.score_record_id}",
            f"Replacement: {replacement_id}",
            *_score_confirmation_lines(
                current,
                draft.target,
                draft.criterion,
                draft.scale,
                draft.session_id,
                draft.disposition,
                draft.value,
                draft.basis,
                len(draft.links),
            ),
        )
        if not confirm_write("Revise a Score", "REVISE", lines):
            return
        result = replace_score(
            ReplaceScoreRequest(
                class_id=current.class_id,
                activity_id=current.activity_id,
                score_record_id=predecessor.score_record_id,
                replacement_score_record_id=replacement_id,
                correction_id=correction_id,
                reason=correction_reason,
                target_reference=draft.target,
                criterion_id=draft.criterion.criterion_id,
                scoring_scale_id=draft.scale.scoring_scale_id,
                session_id=draft.session_id,
                disposition=draft.disposition,
                basis=draft.basis,
                privacy_policy=_PRIVACY,
                correction_privacy_policy=_PRIVACY,
                expected_snapshot_revision=current.snapshot_revision,
                actor=state.require_actor(),
                value=draft.value,
                rationale=draft.rationale,
                status_reason=draft.status_reason,
                evidence_links=draft.links,
            ),
            standards_library=_library(),
        )
        show_result(
            "Score Revised",
            (
                f"Replacement: {result.score_record_id}",
                f"Evidence Links: {len(result.score_evidence_link_ids)}",
                f"Snapshot: {result.commit.snapshot_revision}",
            ),
        )
    except CancelMenuAction:
        return
    except Exception as error:
        _handle_error(activity, error)




def _preset_save_lines(prepared: PreparedPresetSave) -> tuple[str, ...]:
    return (
        f"Preset: {prepared.name}",
        *prepared.reusable_fields,
        "NOT SAVED:",
        *prepared.excluded_state,
    )


def _save_scale_as_preset(
    activity: ActivitySummary,
    state: MenuSessionContext,
) -> None:
    try:
        current = _latest(activity)
        scales = list_scoring_scales(
            current.class_id,
            current.activity_id,
            standards_library=_library(),
            current_only=True,
        )
        selected = select_one(
            "Save Scoring Scale as Preset",
            scales,
            tuple(f"{item.name} ({item.scoring_scale_id})" for item in scales),
            help_text="Choose the native Scale whose reusable definition to save.",
        )
        preset_id = f"scale-preset-{uuid4().hex}"
        request = SaveScoringScalePresetFromActivityRequest(
            class_id=current.class_id,
            activity_id=current.activity_id,
            scoring_scale_id=selected.scoring_scale_id,
            preset_id=preset_id,
            preset_revision_id=f"{preset_id}-v1",
            expected_snapshot_revision=current.snapshot_revision,
            actor=state.require_actor(),
        )
        prepared = prepare_scoring_scale_preset_from_activity(
            request,
            standards_library=_library(),
        )
        if not confirm_write(
            "Save Scoring Scale Preset",
            "SAVE",
            _preset_save_lines(prepared),
        ):
            return
        result = save_scoring_scale_preset_from_activity(
            request,
            review_digest=prepared.review_digest,
            standards_library=_library(),
        )
        show_result(
            "Scoring Scale Preset Saved",
            (f"Preset: {result.preset_id}", "Scores and native IDs were not copied."),
        )
    except CancelMenuAction:
        return
    except Exception as error:
        _handle_error(activity, error)


def _recommended_scale_for_native_set(
    detail: CriterionSetDetail,
) -> tuple[str | None, str | None]:
    native_defaults = {
        item.default_scoring_scale_id
        for item in detail.criteria
        if item.default_scoring_scale_id is not None
    }
    if not native_defaults:
        return None, None
    saved = list_presets("scoring_scale")
    if not saved:
        return None, None
    values = (None, *saved)
    labels = (
        "Do not carry a default Scale recommendation",
        *tuple(f"{item.name} ({item.preset_id})" for item in saved),
    )
    selected = select_one(
        "Reusable Scale Recommendation",
        values,
        labels,
        help_text=(
            "Native Scale IDs cannot become cross-Activity authority. "
            "Choose a saved Scale only when it represents the intended default."
        ),
    )
    if selected is None:
        return None, None
    return selected.preset_id, selected.preset_revision_id


def _save_criterion_set_as_preset(
    activity: ActivitySummary,
    state: MenuSessionContext,
) -> None:
    try:
        current = _latest(activity)
        sets = list_criterion_sets(
            current.class_id,
            current.activity_id,
            standards_library=_library(),
            current_only=True,
        )
        selected = select_one(
            "Save Criterion Set as Preset",
            sets,
            tuple(f"{item.name} ({item.criterion_set_id})" for item in sets),
            help_text=(
                "Choose the native Criterion Set whose reusable definition to save."
            ),
        )
        detail = show_criterion_set(
            current.class_id,
            current.activity_id,
            selected.criterion_set_id,
            standards_library=_library(),
        )
        recommended_id, recommended_revision_id = _recommended_scale_for_native_set(
            detail
        )
        preset_id = f"criterion-preset-{uuid4().hex}"
        request = SaveCriterionSetPresetFromActivityRequest(
            class_id=current.class_id,
            activity_id=current.activity_id,
            criterion_set_id=selected.criterion_set_id,
            preset_id=preset_id,
            preset_revision_id=f"{preset_id}-v1",
            expected_snapshot_revision=current.snapshot_revision,
            actor=state.require_actor(),
            recommended_scoring_scale_preset_id=recommended_id,
            recommended_scoring_scale_preset_revision_id=recommended_revision_id,
        )
        prepared = prepare_criterion_set_preset_from_activity(
            request,
            standards_library=_library(),
        )
        if not confirm_write(
            "Save Criterion Set Preset",
            "SAVE",
            _preset_save_lines(prepared),
        ):
            return
        result = save_criterion_set_preset_from_activity(
            request,
            review_digest=prepared.review_digest,
            standards_library=_library(),
        )
        show_result(
            "Criterion Set Preset Saved",
            (f"Preset: {result.preset_id}", "Scores and native IDs were not copied."),
        )
    except CancelMenuAction:
        return
    except Exception as error:
        _handle_error(activity, error)


def _criterion_set_menu(
    activity: ActivitySummary,
    state: MenuSessionContext,
) -> None:
    while True:
        clear_screen()
        print_menu_header("Criterion Sets")
        print("1. Create Criterion Set")
        print("2. Browse Criterion Sets")
        print("3. Revise Criterion Set")
        print("4. Select Activity Criterion Sets")
        print("5. Save Criterion Set as Preset")
        print_navigation()
        print()
        choice = input("Select an option: ").strip()
        navigation = parse_menu_navigation(choice)
        if navigation is ConcordMenuChoice.HELP:
            show_result(
                "Criterion Set Help",
                (
                    "Criterion Sets are immutable ordered collections.",
                    "Selection is explicit and uses exact Set revisions.",
                    "Saved reusable presets are managed separately from native Sets.",
                ),
            )
        elif navigation is NavigationChoice.BACK:
            return
        elif choice == "1":
            _create_criterion_set(activity, state)
        elif choice == "2":
            _browse_criterion_sets(activity)
        elif choice == "3":
            _revise_criterion_set(activity, state)
        elif choice == "4":
            _select_criterion_sets(activity, state)
        elif choice == "5":
            _save_criterion_set_as_preset(activity, state)
        else:
            print(navigation_hint_with_help())
            pause_for_user()



def _choose_saved_scale_for_preset(
    criterion: CriterionSetPresetRevision,
) -> ScoringScalePresetRevision | None:
    references = {
        (
            item.default_scoring_scale_preset_id,
            item.default_scoring_scale_preset_revision_id,
        )
        for item in criterion.criteria
        if item.default_scoring_scale_preset_id is not None
    }
    recommended: ScoringScalePresetRevision | None = None
    if references:
        preset_id, revision_id = next(iter(references))
        assert preset_id is not None and revision_id is not None
        exact = get_preset_revision("scoring_scale", preset_id, revision_id)
        if not isinstance(exact, ScoringScalePresetRevision):
            raise ValueError("Recommended Scoring Scale preset has the wrong type.")
        recommended = exact

    available = list_presets("scoring_scale")
    while True:
        clear_screen()
        print_menu_header("Scoring Scale")
        if recommended is not None:
            print(f"Recommended: {recommended.name}")
            print("1. Use recommended Scale")
            print("2. Choose another saved Scale")
        else:
            print("No default Scale is recommended by this Criterion preset.")
            print("1. Continue without creating a Scale")
            print("2. Choose a saved Scale")
        print_navigation()
        print()
        raw = input("Select an option: ").strip()
        navigation = parse_menu_navigation(raw)
        if navigation is ConcordMenuChoice.HELP:
            show_result(
                "Scoring Scale Help",
                (
                    "A recommended Scale is a convenience, not a judgment.",
                    "You may choose another saved Scale when appropriate.",
                    "No Score value is selected or inferred here.",
                ),
            )
            continue
        if navigation is NavigationChoice.BACK:
            raise CancelMenuAction
        if raw == "1":
            return recommended
        if raw == "2":
            if not available:
                show_result(
                    "Scoring Scale",
                    ("No saved Scoring Scales are available.",),
                )
                continue
            summary = select_one(
                "Choose a Saved Scoring Scale",
                available,
                tuple(item.name for item in available),
                help_text=(
                    "Choose a reusable Scale definition for fresh Activity state."
                ),
            )
            selected = get_preset("scoring_scale", summary.preset_id)
            if not isinstance(selected, ScoringScalePresetRevision):
                raise ValueError("Selected Scoring Scale preset has the wrong type.")
            return selected
        print(navigation_hint_with_help())
        pause_for_user()


def _use_saved_scoring_setup(
    activity: ActivitySummary,
    state: MenuSessionContext,
) -> None:
    try:
        current = _latest(activity)
        summaries = list_presets("criterion_set")
        if not summaries:
            show_result(
                "Saved Scoring Setup",
                ("No saved Criterion Set presets are available.",),
            )
            return
        summary = select_one(
            "Choose Saved Criteria",
            summaries,
            tuple(item.name for item in summaries),
            help_text="Choose reusable criteria; fresh Activity records are created.",
        )
        value = get_preset("criterion_set", summary.preset_id)
        if not isinstance(value, CriterionSetPresetRevision):
            raise ValueError("Selected Criterion Set preset has the wrong type.")
        scale = _choose_saved_scale_for_preset(value)
        criterion_set_id = f"criterion-set-{uuid4().hex}"
        request = MaterializeScoringSetupRequest(
            criterion_preset_id=value.preset_id,
            criterion_preset_revision_id=value.preset_revision_id,
            class_id=current.class_id,
            activity_id=current.activity_id,
            criterion_set_id=criterion_set_id,
            criterion_set_lineage_id=f"{criterion_set_id}-lineage",
            criterion_ids=tuple(
                CriterionTargetIdentity(
                    criterion_key=item.key,
                    criterion_id=f"criterion-{uuid4().hex}",
                )
                for item in value.criteria
            ),
            expected_snapshot_revision=current.snapshot_revision,
            actor=state.require_actor(),
            scoring_scale_preset_id=None if scale is None else scale.preset_id,
            scoring_scale_preset_revision_id=(
                None if scale is None else scale.preset_revision_id
            ),
            scoring_scale_id=None if scale is None else f"scale-{uuid4().hex}",
            scoring_scale_lineage_id=(
                None if scale is None else f"scale-lineage-{uuid4().hex}"
            ),
        )
        prepared = prepare_scoring_setup(
            request,
            standards_library=_library(),
        )
        if not confirm_write(
            "Use Saved Scoring Setup",
            "USE",
            (
                f"Criteria: {prepared.criterion_preset_name}",
                f"Criteria count: {prepared.criterion_count}",
                f"Scale: {prepared.scoring_scale_preset_name or 'none'}",
                f"Standards profile: {prepared.standards_profile_id or '-'}",
                "No Scores will be created.",
            ),
        ):
            return
        result = materialize_scoring_setup(
            request,
            review_digest=prepared.review_digest,
            standards_library=_library(),
        )
        show_result(
            "Scoring Setup Added",
            (
                f"Criterion Set: {result.criterion_set_id}",
                f"Criteria: {len(result.criterion_ids)}",
                f"Scoring Scale: {result.scoring_scale_id or '-'}",
                "Scores created: 0",
                f"Snapshot: {result.commit.snapshot_revision}",
            ),
        )
    except CancelMenuAction:
        return
    except Exception as error:
        _handle_error(activity, error)


def _scale_menu(
    activity: ActivitySummary,
    state: MenuSessionContext,
) -> None:
    while True:
        clear_screen()
        print_menu_header("Scoring Scales")
        print("1. Create Scoring Scale")
        print("2. Browse Scoring Scales")
        print("3. Revise Scoring Scale")
        print("4. Save Scoring Scale as Preset")
        print_navigation()
        print()
        choice = input("Select an option: ").strip()
        navigation = parse_menu_navigation(choice)
        if navigation is ConcordMenuChoice.HELP:
            show_result(
                "Scoring Scale Help",
                (
                    "Scales preserve exact native values and meanings.",
                    '1, 1.0, "1", and true are distinct values.',
                    "Concord does not normalize different Scales.",
                ),
            )
        elif navigation is NavigationChoice.BACK:
            return
        elif choice == "1":
            _create_scale(activity, state)
        elif choice == "2":
            _browse_scales(activity)
        elif choice == "3":
            _revise_scale(activity, state)
        elif choice == "4":
            _save_scale_as_preset(activity, state)
        else:
            print(navigation_hint_with_help())
            pause_for_user()


def launch_assessment_setup_menu(
    activity: ActivitySummary,
    state: MenuSessionContext | None = None,
) -> None:
    """Configure how an Activity will be assessed without recording Scores."""
    session_state = MenuSessionContext() if state is None else state
    while True:
        try:
            activity = _latest(activity)
        except Exception:
            pass
        clear_screen()
        print_menu_header("Assessment Setup")
        print(f"Activity: {activity.title}")
        print()
        print("1. Use saved assessment setup")
        print("2. Criteria")
        print("3. Scoring scales")
        print_navigation()
        print()
        choice = input("Select an option: ").strip()
        navigation = parse_menu_navigation(choice)
        if navigation is ConcordMenuChoice.HELP:
            show_result(
                "Assessment Setup Help",
                (
                    "Set up criteria and scoring scales for this Activity.",
                    "This setup creates no Scores.",
                    "Actual teacher judgments are recorded from the Score task.",
                ),
            )
        elif navigation is NavigationChoice.BACK:
            return
        elif choice == "1":
            _use_saved_scoring_setup(activity, session_state)
        elif choice == "2":
            _criterion_set_menu(activity, session_state)
        elif choice == "3":
            _scale_menu(activity, session_state)
        else:
            print(navigation_hint_with_help())
            pause_for_user()


def launch_score_menu(
    activity: ActivitySummary,
    state: MenuSessionContext | None = None,
) -> None:
    """Record, inspect, or revise explicit teacher Score judgments."""
    session_state = MenuSessionContext() if state is None else state
    while True:
        try:
            activity = _latest(activity)
        except Exception:
            pass
        clear_screen()
        print_menu_header("Score")
        print(f"Activity: {activity.title}")
        print()
        print("1. Record a Score")
        print("2. View Scores")
        print("3. Revise a Score")
        print_navigation()
        print()
        choice = input("Select an option: ").strip()
        navigation = parse_menu_navigation(choice)
        if navigation is ConcordMenuChoice.HELP:
            clear_screen()
            print_menu_header("Score Help")
            print("Record explicit teacher-approved judgments here.")
            print("Assessment criteria and scales are configured under Plan.")
            print("Concord never infers a Score from evidence.")
            print("A Group Score never creates individual student Scores.")
            print()
            pause_for_user()
        elif navigation is NavigationChoice.BACK:
            return
        elif choice == "1":
            _record_score(activity, session_state)
        elif choice == "2":
            _browse_scores(activity)
        elif choice == "3":
            _revise_score(activity, session_state)
        else:
            print(navigation_hint_with_help())
            pause_for_user()


def launch_scoring_menu(
    activity: ActivitySummary,
    state: MenuSessionContext | None = None,
) -> None:
    """Open the teacher-facing Criterion, Scale, and Score surface."""
    session_state = MenuSessionContext() if state is None else state
    while True:
        try:
            activity = _latest(activity)
        except Exception:
            pass
        clear_screen()
        print_menu_header("Scoring")
        print(f"Activity: {activity.title}")
        print(f"Orientation: {activity.scoring_orientation}")
        print()
        print("1. Use Saved Scoring Setup")
        print("2. Criterion Sets")
        print("3. Scoring Scales")
        print("4. Record a Score")
        print("5. Browse current Scores")
        print("6. Revise a Score")
        print_navigation()
        print()
        choice = input("Select an option: ").strip()
        navigation = parse_menu_navigation(choice)
        if navigation is ConcordMenuChoice.HELP:
            show_result(
                "Scoring Help",
                (
                    "Scoring is teacher-approved judgment; it is not grading.",
                    "Choose Criterion, target, Scale, basis, and evidence explicitly.",
                    "Concord never recommends a Score from evidence.",
                    "Group Scores never create individual student Scores.",
                    "Meridian owns later grading and reporting policy.",
                ),
            )
        elif navigation is NavigationChoice.BACK:
            return
        elif choice == "1":
            _use_saved_scoring_setup(activity, session_state)
        elif choice == "2":
            _criterion_set_menu(activity, session_state)
        elif choice == "3":
            _scale_menu(activity, session_state)
        elif choice == "4":
            _record_score(activity, session_state)
        elif choice == "5":
            _browse_scores(activity)
        elif choice == "6":
            _revise_score(activity, session_state)
        else:
            print(navigation_hint_with_help())
            pause_for_user()


__all__ = [
    "launch_assessment_setup_menu",
    "launch_score_menu",
    "launch_scoring_menu",
]
