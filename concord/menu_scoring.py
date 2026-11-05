"""Teacher-facing Criterion, Scale, and Score workflows."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from pds_core.standards import StandardsLibrary

from concord.criterion_guidance import (
    criterion_specs,
)
from concord.criterion_guidance import (
    describe_draft as describe_criterion_draft,
)
from concord.criterion_guidance import (
    validate_draft as validate_criterion_draft,
)
from concord.criterion_preset_guidance import (
    assess_native_defaults,
    matches_native_scale,
    scale_mapping_receipt,
)
from concord.criterion_revision_guidance import (
    describe_native_criterion_set,
    project_native_criterion_set,
)
from concord.menu_artifact import (
    open_returned_work,
    open_verified_assembly_version,
)
from concord.menu_context import CancelMenuAction, MenuSessionContext
from concord.menu_criterion_guidance import guide_native_criterion_set
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
    prompt_scale_combining_notes,
    prompt_text,
    select_many,
    select_one,
    show_result,
    slug_identifier,
)
from concord.menu_scale_guidance import draft_from_existing, guide_scale_levels
from concord.menu_score_analysis import launch_score_analysis_menu
from concord.menu_score_teacher_labels import (
    ScoreTeacherLabels,
    build_score_teacher_labels,
)
from concord.menu_teacher_history import (
    distinguish_equal_labels,
    teacher_recorded_instant,
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
    StatusReason,
    SubjectReference,
)
from concord.reusable_presets import (
    CriterionSetPresetRevision,
    ScoringScalePresetRevision,
)
from concord.scale_guidance import describe_draft, validate_draft
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
    WorkflowActor,
    add_score,
    create_criterion_set,
    create_scoring_scale,
    get_preset,
    get_preset_revision,
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
    read_activity_criterion_set_selection,
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
from concord.workflows.context import actor_reference, provenance
from concord.workflows.moderation import list_applicable_moderation_records
from concord.workflows.teacher_artifact_choices import (
    list_teacher_artifact_choices,
)

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
        distinguish_equal_labels(
            tuple(f"{item.name} - revision {item.revision}" for item in scales),
            noun="Scoring Scale choice",
        ),
        help_text=(
            "Choose the exact native Scale revision. Concord does not normalize "
            "or infer equivalence between Scales."
        ),
    )


def _edit_optional_scale_field(
    title: str, label: str, previous: str | None, *,
    combining_notes: bool = False,
) -> str | None:
    if previous is None:
        if combining_notes:
            return prompt_scale_combining_notes(title)
        return _optional_text(title, label, "Optional teacher-facing guidance.")
    action = select_one(
        title,
        ("keep", "change", "clear"),
        (f"Keep current {label}: {previous}", f"Change {label}", f"Clear {label}"),
        help_text="The historical Scale retains its original guidance.",
    )
    if action == "keep":
        return previous
    if action == "clear":
        return None
    if combining_notes:
        return prompt_scale_combining_notes(title)
    return _optional_text(title, label, "Enter replacement guidance.")


def _create_scale(
    activity: ActivitySummary,
    state: MenuSessionContext,
) -> str | None:
    try:
        current = _latest(activity)
        name = prompt_text(
            "Create Scoring Scale",
            "Scale name",
            help_text="Name this exact native scoring Scale.",
        )
        assert name is not None
        # Native identities are implementation details, never teacher-facing prompts.
        # Fresh UUIDs also avoid collisions between Scales with identical names.
        scale_id = f"scale-{uuid4().hex}"
        lineage_id = f"scale-lineage-{uuid4().hex}"
        guided = guide_scale_levels(
            title="Create Scoring Scale — Choose Levels",
            validator=lambda draft: validate_draft(
                draft,
                name=name,
                created_provenance=provenance(state.require_actor()),
            ),
        )
        scale_type = guided.draft.scale_type
        levels = guided.draft.levels
        intended_use = _optional_text(
            "Create Scoring Scale",
            "Intended use",
            "Optional teacher-facing intended-use guidance.",
        )
        aggregation = prompt_scale_combining_notes("Create Scoring Scale")
        validate_draft(
            guided.draft,
            name=name,
            created_provenance=provenance(state.require_actor()),
            intended_use=intended_use,
            aggregation_guidance=aggregation,
        )
        if not confirm_write(
            "Create Scoring Scale",
            "CREATE",
            (
                f"Activity: {current.title}",
                f"Scale: {name}",
                "New native Scale identity and lineage generated automatically.",
                "Revision: 1 (new lineage)",
                *describe_draft(guided.draft),
                *guided.precision_notices,
                f"Intended use: {intended_use or '(none)'}",
                f"Notes on combining assessment results: {aggregation or '(none)'}",
                "No Scores, Grades, evidence, or publication are created.",
                "Native Scale only; this does not link a Criterion or save a preset.",
            ),
        ):
            return None
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
                f"Scale: {name} ({result.scoring_scale_id})",
                f"Snapshot: {result.commit.snapshot_revision}",
                "Scale created; not yet linked to a Criterion.",
                "Continue to Assessment Setup > Criteria to use this Scale.",
                "Save as Preset remains a separately reviewed operation.",
            ),
        )
        return result.scoring_scale_id
    except CancelMenuAction:
        return None
    except Exception as error:
        _handle_error(activity, error)
        return None


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
        guided = guide_scale_levels(
            title="Revise Scoring Scale — Choose Levels",
            existing=draft_from_existing(detail.summary.scale_type, detail.levels),
            validator=lambda draft: validate_draft(
                draft,
                name=name,
                created_provenance=provenance(state.require_actor()),
            ),
        )
        scale_type = guided.draft.scale_type
        levels = guided.draft.levels
        intended_use = _edit_optional_scale_field(
            "Revise Scoring Scale", "Intended use", detail.summary.intended_use
        )
        aggregation = _edit_optional_scale_field(
            "Revise Scoring Scale", "Notes on combining assessment results",
            detail.aggregation_guidance, combining_notes=True,
        )
        validate_draft(
            guided.draft,
            name=name,
            created_provenance=provenance(state.require_actor()),
            intended_use=intended_use,
            aggregation_guidance=aggregation,
        )
        if not confirm_write(
            "Revise Scoring Scale",
            "REVISE",
            (
                f"Activity: {current.title}",
                f"Current: {detail.summary.scoring_scale_id}",
                f"Successor native ID: {replacement_id}",
                f"Revision: {predecessor.revision + 1}",
                *describe_draft(guided.draft),
                *guided.precision_notices,
                f"Intended use: {intended_use or '(none)'}",
                f"Notes on combining assessment results: {aggregation or '(none)'}",
                "Historical Scale and Scores remain unchanged.",
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
                f"Successor Scale: {name} ({result.scoring_scale_id})",
                f"Prior revision: {predecessor.scoring_scale_id}",
                f"Snapshot: {result.commit.snapshot_revision}",
                "Existing Scores remain bound to their exact prior Scale revision.",
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
            f"Intended use: {detail.summary.intended_use or '-'}",
            f"Notes on combining assessment results: "
            f"{detail.aggregation_guidance or '-'}",
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


def _saved_scale_menu_labels(
    presets: tuple[ScoringScalePresetRevision, ...],
) -> tuple[str, ...]:
    """Distinguish reusable definitions with grounded, exact revision details."""
    base = tuple(
        f"{item.name} | {item.scale_type} | {len(item.levels)} levels | "
        f"saved revision {item.revision}"
        for item in presets
    )
    return tuple(
        f"{label} | Preset ID: {item.preset_id}"
        if base.count(label) > 1 else label
        for label, item in zip(base, presets, strict=True)
    )


def _saved_scale_preview(value: ScoringScalePresetRevision) -> tuple[str, ...]:
    """Display the exact saved, typed Scale definition without a write."""
    lines = [
        f"Saved Scale: {value.name}",
        f"Preset ID: {value.preset_id}",
        f"Saved revision: {value.revision} ({value.preset_revision_id})",
        f"Status: {value.status}",
        f"Scale type: {value.scale_type}",
        f"Levels: {len(value.levels)} (exact typed values)",
        f"Intended use: {value.intended_use or '-'}",
        "Notes on combining assessment results: "
        f"{value.aggregation_guidance or '-'}",
    ]
    lines.extend(
        f"  {json.dumps(level.value, ensure_ascii=False)} "
        f"[{type(level.value).__name__}] - {level.label}: {level.meaning}"
        for level in value.levels
    )
    return tuple(lines)


def _import_saved_scale(
    activity: ActivitySummary,
    state: MenuSessionContext,
) -> None:
    """Create only a fresh native Scale from an exact, reviewed saved revision."""
    try:
        current = _latest(activity)
        summaries = list_presets("scoring_scale")
        if not summaries:
            show_result(
                "No Saved Scoring Scales",
                ("Save or create a reusable Scoring Scale preset first.",),
            )
            return
        available: list[ScoringScalePresetRevision] = []
        for summary in summaries:
            exact = get_preset_revision(
                "scoring_scale", summary.preset_id, summary.preset_revision_id
            )
            if not isinstance(exact, ScoringScalePresetRevision):
                raise ValueError("Saved Scoring Scale has an unexpected type.")
            if exact.revision != summary.revision or exact.status != "active":
                raise ValueError("Saved Scale changed. Reopen the selection.")
            available.append(exact)
        chosen = select_one(
            "Choose a Saved Scoring Scale",
            available,
            _saved_scale_menu_labels(tuple(available)),
            help_text=(
                "Choose one exact saved definition. A separate review and "
                "confirmation creates only a fresh native Activity Scale."
            ),
        )
        show_result(
            "Saved Scoring Scale — Read-only Preview",
            (*_saved_scale_preview(chosen), "No Activity records were changed."),
        )
        new_scale_id = f"scale-{uuid4().hex}"
        new_lineage_id = f"scale-lineage-{uuid4().hex}"
        if not confirm_write(
            "Use Saved Scoring Scale",
            "USE",
            (
                f"Activity: {current.title}",
                *_saved_scale_preview(chosen),
                "A new native Scale identity and lineage will be generated.",
                "One native Scoring Scale will be created in this Activity.",
                "No Criteria, Criterion Sets, Scores, Grades, student/Group "
                "data, evidence, or presets will be created or copied.",
                "The new Scale must be chosen separately when configuring Criteria.",
            ),
        ):
            return
        # A concurrent Activity change or preset revision must fail before writing.
        if _latest(activity).snapshot_revision != current.snapshot_revision:
            raise ValueError("Activity changed during review. Reopen the Activity.")
        head = get_preset("scoring_scale", chosen.preset_id)
        if (
            not isinstance(head, ScoringScalePresetRevision)
            or head != chosen
            or head.status != "active"
        ):
            raise ValueError("Saved Scoring Scale changed during review. Reopen it.")
        request = CreateScoringScaleRequest(
            class_id=current.class_id,
            activity_id=current.activity_id,
            scoring_scale_id=new_scale_id,
            lineage_id=new_lineage_id,
            name=chosen.name,
            revision=1,
            scale_type=chosen.scale_type,
            levels=chosen.levels,
            status="active",
            intended_use=chosen.intended_use,
            aggregation_guidance=chosen.aggregation_guidance,
            expected_snapshot_revision=current.snapshot_revision,
            actor=state.require_actor(),
        )
        try:
            result = create_scoring_scale(
                request, standards_library=_library()
            )
        except Exception as error:
            show_result(
                "Saved Scoring Scale Import — Outcome Unconfirmed",
                (
                    f"Proposed native Scale ID: {new_scale_id}",
                    f"Service error: {error}",
                    "Do not retry blindly. Browse native Scoring Scales first.",
                ),
            )
            return
        try:
            observed = show_scoring_scale(
                current.class_id, current.activity_id, new_scale_id,
                standards_library=_library(),
            )
        except Exception as error:
            show_result(
                "Saved Scoring Scale Imported — Verification Unavailable",
                (
                    f"Native Scale: {result.scoring_scale_id}",
                    f"Activity snapshot: {result.commit.snapshot_revision}",
                    f"Read-back error: {error}",
                    "Do not retry; inspect the created native Scale first.",
                ),
            )
            return
        exact_levels = (
            len(observed.levels) == len(chosen.levels)
            and all(
                type(left.value) is type(right.value) and left == right
                for left, right in zip(observed.levels, chosen.levels, strict=True)
            )
        )
        if not (
            observed.summary.scoring_scale_id == new_scale_id
            and observed.summary.lineage_id == new_lineage_id
            and observed.summary.revision == 1
            and observed.summary.scale_type == chosen.scale_type
            and observed.summary.name == chosen.name
            and observed.summary.status == "active"
            and observed.summary.intended_use == chosen.intended_use
            and observed.aggregation_guidance == chosen.aggregation_guidance
            and observed.summary.snapshot_revision == result.commit.snapshot_revision
            and exact_levels
        ):
            show_result(
                "Saved Scoring Scale Imported — Verification Mismatch",
                (
                    f"Native Scale: {new_scale_id}",
                    "The write receipt exists, but read-back did not match.",
                    "Inspect the Scale and Activity before any retry.",
                ),
            )
            return
        show_result(
            "Saved Scoring Scale Imported",
            (
                f"Saved preset: {chosen.preset_id} ({chosen.preset_revision_id})",
                f"New native Scale: {new_scale_id}",
                f"New lineage: {new_lineage_id}",
                f"Activity snapshot: {result.commit.snapshot_revision}",
                "Exact typed levels and guidance verified after creation.",
                "No Criterion, Criterion Set, Score, Grade, or evidence was created.",
                "Use Assessment Setup > Criteria to select this new native Scale.",
            ),
        )
    except CancelMenuAction:
        return
    except Exception as error:
        _handle_error(activity, error)


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


def _create_guided_criterion_set(
    activity: ActivitySummary,
    state: MenuSessionContext,
    *,
    use_after_create: bool = False,
) -> None:
    """Guarded native Create only or Create & Use; no cross-store atomicity."""
    try:
        current = _latest(activity)
        detail = show_activity(current.class_id, current.activity_id)
        library = _library()
        draft, focus_choices = guide_native_criterion_set(
            orientation=current.scoring_orientation,
            standards_library=library,
            standards_profile_id=detail.standards_profile_id,
            focus_standard_ids=tuple(detail.focus_standard_ids),
            choose_scale=lambda: _default_scale(current),
        )
        actor = state.require_actor()
        validate_criterion_draft(
            draft,
            activity_scoring_orientation=current.scoring_orientation,
            standards_profile_id=detail.standards_profile_id,
            focus_standard_ids=tuple(detail.focus_standard_ids),
            standards_library=library,
            created_provenance=provenance(actor),
        )
        criterion_set_id = f"criterion-set-{uuid4().hex}"
        lineage_id = f"{criterion_set_id}-lineage"
        criterion_ids = tuple(f"criterion-{uuid4().hex}" for _ in draft.criteria)
        specs = criterion_specs(draft, criterion_ids)
        before_selection = (
            read_activity_criterion_set_selection(
                current.class_id, current.activity_id, standards_library=library
            )
            if use_after_create
            else None
        )
        if (
            before_selection is not None
            and before_selection.snapshot_revision != current.snapshot_revision
        ):
            raise ValueError(
                "Activity selection changed during review. Reopen the rubric."
            )
        if not confirm_write(
            (
                "Create and Use Rubric"
                if use_after_create
                else "Create Rubric (Definition Only)"
            ),
            "CREATE & USE" if use_after_create else "CREATE",
            (
                f"Class: {current.class_id}",
                f"Activity: {current.title} ({current.activity_id})",
                f"Scoring orientation: {current.scoring_orientation}",
                f"Current snapshot: {current.snapshot_revision}",
                f"Core Standards profile: {detail.standards_profile_id or 'none'}",
                *describe_criterion_draft(draft, focus_choices=focus_choices),
                f"New native Criterion Set ID: {criterion_set_id}",
                (
                    "CREATE & USE: create the Set, then select the exact revision."
                    if use_after_create
                    else "CREATE ONLY: the Set will NOT be selected for scoring."
                ),
                (
                    "Existing selected Sets and their order will be retained."
                    if use_after_create
                    else "Select the Set separately when you want to use it."
                ),
                "Creation and Activity selection are separately guarded "
                "durable writes.",
                "Saving a reusable preset requires separate explicit authorization.",
            ),
        ):
            return
        if _latest(activity).snapshot_revision != current.snapshot_revision:
            raise ValueError(
                "Activity changed after rubric review. "
                "Reopen and review before creating."
            )
        result = create_criterion_set(
            CreateCriterionSetRequest(
                class_id=current.class_id,
                activity_id=current.activity_id,
                criterion_set_id=criterion_set_id,
                lineage_id=lineage_id,
                name=draft.name,
                purpose=draft.purpose,
                revision=1,
                scope=draft.scope,
                criterion_set_kind=draft.criterion_set_kind,
                criteria=specs,
                status="active",
                standards_profile_id=(
                    detail.standards_profile_id
                    if draft.criterion_set_kind in {"standard_backed", "mixed"}
                    else None
                ),
                expected_snapshot_revision=current.snapshot_revision,
                actor=actor,
            ),
            standards_library=_library(),
        )
        if use_after_create:
            assert before_selection is not None
            _complete_guided_criterion_selection(
                current, actor, result.criterion_set_id,
                created_snapshot=result.commit.snapshot_revision,
                original_selection=before_selection.criterion_set_ids,
            )
            return
        show_result(
            "Rubric Created — Not Yet Selected",
            (
                f"Native Criterion Set: {result.criterion_set_id}",
                f"Snapshot: {result.commit.snapshot_revision}",
                "This definition has been saved but is not automatically selected.",
                "Use 'Use an existing rubric' to select it, then choose "
                "Save this assessment for another class.",
                "No Score, Grade, evidence, Group/student record "
                "or publication was created.",
            ),
        )
    except CancelMenuAction:
        return
    except Exception as error:
        _handle_error(activity, error)


def _complete_guided_criterion_selection(
    activity: ActivitySummary,
    actor: WorkflowActor,
    criterion_set_id: str,
    *,
    created_snapshot: int,
    original_selection: tuple[str, ...],
) -> None:
    """Select after native creation with one approval, truthful partial receipts.

    No automatic replay: if this stage fails, the native Set remains durable.
    A later teacher action may explicitly select that existing Set instead.
    """
    selected = (*original_selection, criterion_set_id)
    try:
        prior = read_activity_criterion_set_selection(
            activity.class_id, activity.activity_id, standards_library=_library()
        )
        if (
            prior.snapshot_revision != created_snapshot
            or prior.criterion_set_ids != original_selection
        ):
            raise ValueError(
                "Activity selection changed after rubric creation; no automatic "
                "overwrite was attempted."
            )
        result = select_activity_criterion_sets(
            SelectActivityCriterionSetsRequest(
                class_id=activity.class_id,
                activity_id=activity.activity_id,
                criterion_set_ids=selected,
                expected_snapshot_revision=created_snapshot,
                actor=actor,
            ),
            standards_library=_library(),
        )
        verified = read_activity_criterion_set_selection(
            activity.class_id, activity.activity_id, standards_library=_library()
        )
        if (
            verified.criterion_set_ids != selected
            or verified.snapshot_revision != result.commit.snapshot_revision
        ):
            raise ValueError(
                "Selection result does not match the authoritative Activity state."
            )
    except Exception as error:
        # A service exception can occur after durable storage succeeds. Re-read
        # canonical state; never present a guessed rollback or blindly retry.
        try:
            observed = read_activity_criterion_set_selection(
                activity.class_id, activity.activity_id,
                standards_library=_library(),
            )
        except Exception as inspection_error:
            show_result(
                "Rubric Created — Selection Outcome Unknown",
                (
                    f"Created native Criterion Set: {criterion_set_id}",
                    f"Selection/review error: {error}",
                    f"Current-state inspection also failed: {inspection_error}",
                    "Do not create another rubric or assume selection failed.",
                    "Reopen this Activity and inspect its selected Criteria.",
                ),
            )
            return
        if observed.criterion_set_ids == selected:
            show_result(
                "Rubric Created — Selection Verified After Error",
                (
                    f"Native Criterion Set: {criterion_set_id}",
                    f"Verified Activity snapshot: {observed.snapshot_revision}",
                    f"A service/verification error occurred: {error}",
                    "The exact intended selection is present in canonical state.",
                    "No Scores, Grades, evidence, or publication were created.",
                ),
            )
        else:
            show_result(
                "Rubric Created — Selection Requires Review",
                (
                    f"Native Criterion Set: {criterion_set_id}",
                    f"Current Activity snapshot: {observed.snapshot_revision}",
                    f"Selection error: {error}",
                    "The intended Create & Use selection is NOT verified.",
                    "Use 'Select Activity Criterion Sets' on the EXISTING rubric;",
                    "do not repeat creation. No automatic retry was attempted.",
                ),
            )
        return
    show_result(
        "Rubric Created and Selected",
        (
            f"Native Criterion Set: {criterion_set_id}",
            f"Selected Activity snapshot: {verified.snapshot_revision}",
            f"Existing selected Sets preserved: {len(original_selection)}",
            "This rubric is now selected for future Activity Scores.",
            "No Score, Grade, evidence, or publication was created.",
            "Next: Criterion Sets > Save this assessment for another class.",
        ),
    )


def _create_and_use_guided_criterion_set(
    activity: ActivitySummary,
    state: MenuSessionContext,
) -> None:
    _create_guided_criterion_set(activity, state, use_after_create=True)


def _revise_criterion_set_advanced(
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


def _select_criterion_sets_advanced(
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
    """Inspect an exact current/historical native rubric without writing."""
    try:
        current = _latest(activity)
        library = _library()
        selection = read_activity_criterion_set_selection(
            current.class_id,
            current.activity_id,
            standards_library=library,
        )
        if selection.snapshot_revision != current.snapshot_revision:
            raise ValueError(
                "Activity changed before rubric review. Reopen this Activity."
            )
        sets = list_criterion_sets(
            current.class_id,
            current.activity_id,
            standards_library=library,
            current_only=False,
        )
        if not sets:
            show_result(
                "No Rubrics Yet",
                (
                    "This Activity has no native Criterion Sets yet.",
                    "Choose 'Create and use a rubric (guided)' to begin.",
                    "No Activity selection, Scores, or saved presets changed.",
                ),
            )
            return
        selected = select_one(
            "Review an existing rubric",
            sets,
            tuple(
                f"{item.name} (revision {item.revision}; "
                f"{'current' if item.is_current else 'historical'}; "
                f"{'selected' if item.is_selected else 'not selected'})"
                for item in sets
            ),
            help_text=(
                "Review the exact native revision. Historical definitions remain "
                "unchanged and may still be selected for previous Scores."
            ),
        )
        detail = show_criterion_set(
            current.class_id,
            current.activity_id,
            selected.criterion_set_id,
            standards_library=library,
        )
        review = project_native_criterion_set(detail, selection)
        scales = list_scoring_scales(
            current.class_id,
            current.activity_id,
            standards_library=library,
        )
        scale_names = {item.scoring_scale_id: item.name for item in scales}
        show_result(
            "Existing Rubric — Read Only",
            describe_native_criterion_set(
                review,
                standards_library=library,
                native_scale_names=scale_names,
            ),
        )
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
        distinguish_equal_labels(
            tuple(
                f"{criterion.label} [{criterion.criterion_kind}]"
                for _, criterion in pairs
            ),
            noun="Criterion choice",
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
    choices = list_teacher_artifact_choices(
        activity.class_id, activity.activity_id
    )
    selected = select_one(
        "Choose Score Target Artifact",
        choices,
        tuple(item.label for item in choices),
        help_text=(
            "Choose the Group, Session and work to score. "
            "This selects one exact Artifact; it does not choose scan history."
        ),
    )
    return ScoreTargetReference(
        target_kind=target_kind,
        target_id=selected.summary.artifact_instance_id,
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
            f"Session {item.sequence}: "
            f"{item.label or 'Unlabeled session'} - {item.status}"
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
    labels = build_score_teacher_labels(activity)
    lines = [
        f"Activity: {activity.title}",
        f"Target: {labels.target(target.target_kind, target.target_id)}",
        f"Criterion: {criterion.label}",
        f"Scale: {scale.name}",
        f"Session context: {labels.session(session_id)}",
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
                "The exact Score was saved.",
                f"Evidence Links: {len(result.score_evidence_link_ids)}",
                "Use View Scores to inspect the current record.",
            ),
        )
    except CancelMenuAction:
        return
    except Exception as error:
        _handle_error(activity, error)


def _score_label(
    item: ScoreSummary, labels: ScoreTeacherLabels | None = None
) -> str:
    value = "-" if item.value is None else json.dumps(item.value)
    state = "current" if item.is_current else "historical"
    reference = item.target_reference
    target = (
        labels.target(reference.target_kind, reference.target_id)
        if labels is not None
        else reference.target_kind.replace("_", " ")
    )
    return (
        f"{teacher_recorded_instant(item.scored_at, kind='Scored')} - "
        f"{target} - {item.disposition.replace('_', ' ')} {value} "
        f"[{state}]"
    )


def _browse_scores(activity: ActivitySummary) -> None:
    try:
        scores = list_scores(
            activity.class_id,
            activity.activity_id,
            standards_library=_library(),
            current_only=False,
        )
        labels = build_score_teacher_labels(
            activity, include_score_definitions=True
        )
        selected = select_one(
            "Scores",
            scores,
            distinguish_equal_labels(
                tuple(_score_label(item, labels) for item in scores),
                noun="Score choice",
            ),
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
            _score_label(selected, labels),
            "Exact scored scan version not recorded in Score metadata.",
            "Target: " + labels.target(
                selected.target_reference.target_kind,
                selected.target_reference.target_id,
            ),
            f"Criterion: {labels.criterion(selected.criterion_id)}",
            f"Disposition: {selected.disposition}",
            (
                "Value: "
                + ("-" if selected.value is None else json.dumps(selected.value))
            ),
            f"Scale: {labels.scale(selected.scoring_scale_id)}",
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
        labels = build_score_teacher_labels(
            current, include_score_definitions=True
        )
        predecessor = select_one(
            "Revise a Score",
            heads,
            distinguish_equal_labels(
                tuple(_score_label(item, labels) for item in heads),
                noun="Score choice",
            ),
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
            "Current Score: " + _score_label(predecessor, labels),
            "A new immutable Score revision will be recorded.",
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
                "A new immutable Score revision was saved.",
                f"Evidence Links: {len(result.score_evidence_link_ids)}",
                "The previous Score remains in history.",
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


def _save_scale_id_as_preset(
    current: ActivitySummary,
    state: MenuSessionContext,
    scale_id: str,
) -> str | None:
    """Separately review and commit a native Scale definition for reuse.

    A declined approval writes nothing; a successful return is the exact saved
    preset ID. This operation never changes the native Scale or any Scores.
    """
    preset_id = f"scale-preset-{uuid4().hex}"
    request = SaveScoringScalePresetFromActivityRequest(
        class_id=current.class_id,
        activity_id=current.activity_id,
        scoring_scale_id=scale_id,
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
        (
            f"Source Activity: {current.title} ({current.activity_id})",
            f"Source native Scale ID: {scale_id}",
            f"Current Activity snapshot: {current.snapshot_revision}",
            *_preset_save_lines(prepared),
            "This is a second, independently reviewed write.",
            "No Scores, student/Group data, or evidence will be copied.",
        ),
    ):
        return None
    saved = save_scoring_scale_preset_from_activity(
        request,
        review_digest=prepared.review_digest,
        standards_library=_library(),
    )
    return saved.preset_id


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
        saved_id = _save_scale_id_as_preset(
            current, state, selected.scoring_scale_id
        )
        if saved_id is None:
            return
        show_result(
            "Scoring Scale Preset Saved",
            (
                f"Native Scale: {selected.scoring_scale_id}",
                f"Reusable preset: {saved_id}",
                "Scores and native IDs were not copied.",
            ),
        )
    except CancelMenuAction:
        return
    except Exception as error:
        _handle_error(activity, error)


def _recommended_scale_for_native_set(
    detail: CriterionSetDetail,
) -> tuple[str | None, str | None]:
    """Offer only exact typed, separately saved native Scale definitions.

    The source preset service supports one recommended Scale only. Multiple
    native defaults, no default, or no exact saved match mean explicit omission.
    """
    assessment = assess_native_defaults(detail.criteria)
    if assessment.native_scale_id is None:
        if assessment.default_ids:
            show_result("Scale Recommendation Excluded", (assessment.notice,))
        return None, None
    native = show_scoring_scale(
        detail.summary.class_id,
        detail.summary.activity_id,
        assessment.native_scale_id,
        standards_library=_library(),
    )
    matches: list[ScoringScalePresetRevision] = []
    for summary in list_presets("scoring_scale"):
        exact = get_preset_revision(
            "scoring_scale", summary.preset_id, summary.preset_revision_id
        )
        if not isinstance(exact, ScoringScalePresetRevision):
            raise ValueError("Saved Scale has an unexpected preset record type.")
        if matches_native_scale(native, exact):
            matches.append(exact)
    if not matches:
        show_result(
            "No Exact Reusable Scale Match",
            (
                f"Native Scale ID: {assessment.native_scale_id}",
                "No active Scale preset has exactly matching typed levels,",
                "labels, meanings, ordering, type, and scoring guidance.",
                "You may save this rubric without a default Scale recommendation.",
                "To retain one, first save the native Scale as its own preset",
                "through Scoring Scales, then return to save this rubric.",
                "A different Scale will never be silently substituted.",
            ),
        )
        return None, None
    selected = select_one(
        "Exact Scoring Scale for Another Class",
        (None, *matches),
        (
            "Omit native default Scale reference from the saved rubric",
            *(
                f"{item.name} — saved revision {item.revision} "
                f"({item.preset_id} / {item.preset_revision_id})"
                for item in matches
            ),
        ),
        help_text=(
            "Every listed Scale matches the native definition exactly, "
            "including typed level values. This is a new, separate preset "
            "reference, not a copied Activity-native Scale ID."
        ),
    )
    if selected is None:
        return None, None
    return selected.preset_id, selected.preset_revision_id


def _save_criterion_set_as_preset(
    activity: ActivitySummary,
    state: MenuSessionContext,
    *,
    criterion_set_id: str | None = None,
) -> None:
    """Save any exact existing native revision via the #143 reviewed contract.

    A reusable preset is distinct from a native 'reusable' scope and does not
    carry Scores, class/Group/student identity, or native Scale record IDs.
    """
    try:
        current = _latest(activity)
        library = _library()
        selection = read_activity_criterion_set_selection(
            current.class_id, current.activity_id, standards_library=library
        )
        if selection.snapshot_revision != current.snapshot_revision:
            raise ValueError("Activity changed before saved-rubric review. Reload.")
        sets = list_criterion_sets(
            current.class_id,
            current.activity_id,
            standards_library=library,
            current_only=False,
        )
        if not sets:
            show_result(
                "No Native Rubric to Save",
                ("Create a rubric first; no reusable preset was written.",),
            )
            return
        if criterion_set_id is None:
            selected = select_one(
                "Save an existing assessment for another class",
                sets,
                tuple(
                    f"{item.name} (revision {item.revision}; "
                    f"{'current' if item.is_current else 'historical'}; "
                    f"{'selected' if item.is_selected else 'not selected'})"
                    for item in sets
                ),
                help_text=(
                    "Choose the exact native rubric revision to reuse. "
                    "Saving a preset does not select or Score anything."
                ),
            )
        else:
            found = next(
                (item for item in sets if item.criterion_set_id == criterion_set_id),
                None,
            )
            if found is None:
                raise ValueError("The requested native rubric is not in this Activity.")
            selected = found
        detail = show_criterion_set(
            current.class_id,
            current.activity_id,
            selected.criterion_set_id,
            standards_library=library,
        )
        if (
            selected.snapshot_revision != current.snapshot_revision
            or detail.summary.snapshot_revision != current.snapshot_revision
            or detail.summary.criterion_set_id != selected.criterion_set_id
        ):
            raise ValueError("Native rubric changed before reusable review. Reload.")
        recommended_id, recommended_revision_id = _recommended_scale_for_native_set(
            detail
        )
        assessment = assess_native_defaults(detail.criteria)
        scale_lines = scale_mapping_receipt(
            assessment,
            preset_id=recommended_id,
            preset_revision_id=recommended_revision_id,
        )
        preset_id = f"criterion-preset-{uuid4().hex}"
        revision_id = f"{preset_id}-v1"
        request = SaveCriterionSetPresetFromActivityRequest(
            class_id=current.class_id,
            activity_id=current.activity_id,
            criterion_set_id=selected.criterion_set_id,
            preset_id=preset_id,
            preset_revision_id=revision_id,
            expected_snapshot_revision=current.snapshot_revision,
            actor=state.require_actor(),
            recommended_scoring_scale_preset_id=recommended_id,
            recommended_scoring_scale_preset_revision_id=recommended_revision_id,
        )
        prepared = prepare_criterion_set_preset_from_activity(
            request, standards_library=library
        )
        if not confirm_write(
            "Save this assessment for another class",
            "SAVE",
            (
                f"Source Activity: {current.title} ({current.activity_id})",
                f"Exact native Set: {selected.criterion_set_id}",
                f"Native revision: {selected.revision}",
                f"Current or historical: "
                f"{'current' if selected.is_current else 'historical'}",
                f"Selected for this Activity: "
                f"{'yes' if selected.is_selected else 'no'}",
                f"Source Activity snapshot: {current.snapshot_revision}",
                *scale_lines,
                *_preset_save_lines(prepared),
                "SAVE is one separate reusable-preset write; it will not",
                "change this Activity or configure any other class yet.",
                "No Scores, Grades, student/Group IDs, evidence, or publication",
                "are copied. The target Activity must later be reviewed.",
            ),
        ):
            return
        fresh = read_activity_criterion_set_selection(
            current.class_id, current.activity_id, standards_library=library
        )
        if (
            fresh != selection
            or _latest(activity).snapshot_revision != current.snapshot_revision
        ):
            raise ValueError("Activity changed since preset review. Reopen to save.")
        # The service rechecks the reviewed source fields and Scale-preset
        # revision through its digest; do not implement a second preset writer.
        try:
            result = save_criterion_set_preset_from_activity(
                request,
                review_digest=prepared.review_digest,
                standards_library=library,
            )
        except Exception as error:
            # A failed call does not prove a failed durable write. Do not offer
            # a blind retry with a fresh ID after an uncertain receipt.
            try:
                existing = get_preset_revision(
                    "criterion_set", preset_id, revision_id
                )
            except Exception:
                show_result(
                    "Reusable Assessment Save Outcome Unknown",
                    (
                        f"Proposed preset: {preset_id} / {revision_id}",
                        f"Service error: {error}",
                        "Do not create a duplicate. Inspect saved assessments",
                        "before deciding whether another save is necessary.",
                    ),
                )
                return
            if not isinstance(existing, CriterionSetPresetRevision):
                raise ValueError("Saved assessment has an unexpected preset type.")
            show_result(
                "Reusable Assessment Verified After Error",
                (
                    f"Exact saved preset: {preset_id} / {revision_id}",
                    f"Service error: {error}",
                    "A reusable definition exists; no automatic retry occurred.",
                ),
            )
            return
        try:
            existing = get_preset_revision(
                "criterion_set", result.preset_id, result.preset_revision_id
            )
            if not isinstance(existing, CriterionSetPresetRevision):
                raise ValueError("Saved assessment has an unexpected preset type.")
        except Exception as inspection_error:
            show_result(
                "Reusable Assessment Saved — Verification Unavailable",
                (
                    "Service receipt: "
                    f"{result.preset_id} / {result.preset_revision_id}",
                    f"Verification error: {inspection_error}",
                    "Do not retry blindly; inspect the reusable-preset library.",
                ),
            )
            return
        show_result(
            "Assessment Saved for Another Class",
            (
                f"Saved preset: {result.preset_id} / {result.preset_revision_id}",
                f"Source native rubric: {selected.criterion_set_id}",
                *scale_lines,
                "Only the reusable definition was saved; no target Activity",
                "was configured, and no Scores or evidence were copied.",
                "Use 'Use saved assessment setup' in the other class later.",
            ),
        )
    except CancelMenuAction:
        return
    except Exception as error:
        _handle_error(activity, error)


def _plan_existing_rubric_selection(
    selected_ids: tuple[str, ...],
    chosen_id: str,
    lineage_ids: frozenset[str],
    *,
    replace_prior_revisions: bool,
) -> tuple[str, ...]:
    """Preserve selection order; replace only this lineage when authorized."""
    if not replace_prior_revisions:
        return selected_ids if chosen_id in selected_ids else (*selected_ids, chosen_id)
    result: list[str] = []
    inserted = False
    for selected_id in selected_ids:
        if selected_id in lineage_ids:
            if not inserted:
                result.append(chosen_id)
                inserted = True
        else:
            result.append(selected_id)
    if not inserted:
        result.append(chosen_id)
    return tuple(result)


def _describe_selected_rubric_revisions(
    selected_ids: tuple[str, ...],
    descriptions: dict[str, str],
) -> tuple[str, ...]:
    if not selected_ids:
        return ("  (none)",)
    return tuple(
        f"  {position}. {descriptions.get(item, item)} [exact ID: {item}]"
        for position, item in enumerate(selected_ids, 1)
    )


def _use_existing_criterion_set(
    activity: ActivitySummary,
    state: MenuSessionContext,
) -> None:
    """Select an exact existing rubric revision with a verified Activity receipt."""
    try:
        current = _latest(activity)
        library = _library()
        selection = read_activity_criterion_set_selection(
            current.class_id,
            current.activity_id,
            standards_library=library,
        )
        if selection.snapshot_revision != current.snapshot_revision:
            raise ValueError("Activity changed before rubric selection. Reload.")
        sets = list_criterion_sets(
            current.class_id,
            current.activity_id,
            standards_library=library,
            current_only=False,
        )
        if not sets:
            show_result(
                "No Existing Rubrics",
                ("Create a rubric before trying to select one.",),
            )
            return
        chosen = select_one(
            "Use an existing rubric",
            sets,
            tuple(
                f"{item.name} (revision {item.revision}; "
                f"{'current' if item.is_current else 'historical'}; "
                f"{'selected' if item.is_selected else 'not selected'})"
                for item in sets
            ),
            help_text=(
                "Choose the exact native revision. Historical Scores "
                "are never rewritten or copied."
            ),
        )
        detail = show_criterion_set(
            current.class_id,
            current.activity_id,
            chosen.criterion_set_id,
            standards_library=library,
        )
        review = project_native_criterion_set(detail, selection)
        selected_id = review.criterion_set_id
        descriptions = {
            item.criterion_set_id: f"{item.name} (revision {item.revision})"
            for item in sets
        }
        lineage_ids = frozenset(
            item.criterion_set_id
            for item in sets
            if item.lineage_id == chosen.lineage_id
        )
        prior_same_lineage = tuple(
            item for item in selection.criterion_set_ids
            if item in lineage_ids and item != selected_id
        )
        replace_prior = False
        if prior_same_lineage:
            action = select_one(
                "Using a revised rubric — Selection choice",
                ("replace", "retain"),
                (
                    "Replace earlier selected revisions of this rubric lineage",
                    "Keep earlier revisions selected alongside this revision",
                ),
                help_text=(
                    "Replacing changes only future Activity selection, never "
                    "historical definitions or Scores. Concord refuses "
                    "deselection when earlier revisions have Score references. "
                    "Keeping both may show both revisions during Score entry."
                ),
            )
            replace_prior = action == "replace"
        proposed = _plan_existing_rubric_selection(
            selection.criterion_set_ids,
            selected_id,
            lineage_ids,
            replace_prior_revisions=replace_prior,
        )
        displaced = tuple(
            item for item in selection.criterion_set_ids if item not in proposed
        )
        if not confirm_write(
            "Use Existing Rubric",
            "USE",
            (
                f"Activity: {current.title}",
                *describe_native_criterion_set(
                    review, standards_library=library
                ),
                "Current selections (ordered):",
                *_describe_selected_rubric_revisions(
                    selection.criterion_set_ids, descriptions
                ),
                "Proposed selections (ordered):",
                *_describe_selected_rubric_revisions(proposed, descriptions),
                (
                    "Action: replace earlier selected revisions of this lineage."
                    if replace_prior else
                    "Action: retain existing selected revisions."
                ),
                f"Earlier selections to deselect: {len(displaced)}",
                "Existing rubric definitions and historical Scores are preserved.",
                "If a deselected revision has Scores, the canonical service "
                "refuses replacement; no selection write is made.",
                "No Scores, Grades, evidence, or presets are created.",
            ),
        ):
            return
        fresh = read_activity_criterion_set_selection(
            current.class_id,
            current.activity_id,
            standards_library=library,
        )
        if fresh != selection or (
            _latest(activity).snapshot_revision != current.snapshot_revision
        ):
            raise ValueError(
                "Activity changed since rubric review. Reload before selecting."
            )
        if proposed == selection.criterion_set_ids:
            show_result(
                "Rubric Already Selected — No Change",
                (
                    f"Exact Criterion Set revision: {selected_id}",
                    "No Activity write was needed; the existing order is intact.",
                    "To reuse it elsewhere, choose "
                    "Save this assessment for another class.",
                ),
            )
            return
        actor = state.require_actor()
        try:
            result = select_activity_criterion_sets(
                SelectActivityCriterionSetsRequest(
                    class_id=current.class_id,
                    activity_id=current.activity_id,
                    criterion_set_ids=proposed,
                    expected_snapshot_revision=selection.snapshot_revision,
                    actor=actor,
                ),
                standards_library=library,
            )
            observed = read_activity_criterion_set_selection(
                current.class_id,
                current.activity_id,
                standards_library=library,
            )
            if (
                observed.criterion_set_ids != proposed
                or observed.snapshot_revision != result.commit.snapshot_revision
            ):
                raise ValueError("Canonical selection verification did not match.")
        except Exception as error:
            try:
                observed = read_activity_criterion_set_selection(
                    current.class_id,
                    current.activity_id,
                    standards_library=library,
                )
            except Exception:
                show_result(
                    "Rubric Selection Outcome Unknown",
                    (
                        f"Exact Criterion Set: {selected_id}",
                        f"Selection error: {error}",
                        "Do not repeat or assume failure; inspect this Activity.",
                    ),
                )
                return
            if observed.criterion_set_ids == proposed:
                show_result(
                    "Existing Rubric Selection Verified After Error",
                    (
                        f"Exact Criterion Set: {selected_id}",
                        f"Activity snapshot: {observed.snapshot_revision}",
                        "The exact intended selection is present.",
                    ),
                )
            else:
                show_result(
                    "Existing Rubric Selection Not Verified",
                    (
                        f"Exact Criterion Set: {selected_id}",
                        f"Activity snapshot: {observed.snapshot_revision}",
                        f"Selection error: {error}",
                        "Reload and review before attempting another selection.",
                    ),
                )
            return
        show_result(
            "Existing Rubric Selected",
            (
                f"Exact Criterion Set: {selected_id}",
                f"Activity snapshot: {observed.snapshot_revision}",
                f"Selected rubric revisions now: {len(proposed)}",
                f"Earlier selections deselected: {len(displaced)}",
                "Selected revisions (ordered):",
                *_describe_selected_rubric_revisions(proposed, descriptions),
                "Historical definitions and Scores remain unchanged.",
                "No Score, Grade, evidence, or preset was created.",
                "Next: Criterion Sets > Save this assessment "
                "for another class.",
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
    """Create a guarded immutable native successor; never silently select it."""
    try:
        current = _latest(activity)
        library = _library()
        activity_detail = show_activity(current.class_id, current.activity_id)
        selection = read_activity_criterion_set_selection(
            current.class_id,
            current.activity_id,
            standards_library=library,
        )
        if selection.snapshot_revision != current.snapshot_revision:
            raise ValueError("Activity changed before rubric revision. Reload.")
        heads = list_criterion_sets(
            current.class_id,
            current.activity_id,
            standards_library=library,
            current_only=True,
        )
        if not heads:
            show_result(
                "No Current Rubrics",
                ("Create a rubric before revising one.",),
            )
            return
        predecessor = select_one(
            "Revise a current rubric",
            heads,
            tuple(
                f"{item.name} (revision {item.revision})"
                for item in heads
            ),
            help_text=(
                "Historical revisions cannot be edited in place. "
                "A revision creates a new native Criterion Set."
            ),
        )
        detail = show_criterion_set(
            current.class_id,
            current.activity_id,
            predecessor.criterion_set_id,
            standards_library=library,
        )
        review = project_native_criterion_set(detail, selection)
        if not review.is_current:
            raise ValueError("A historical rubric cannot be revised as a head.")
        draft, focus_choices = guide_native_criterion_set(
            orientation=current.scoring_orientation,
            standards_library=library,
            standards_profile_id=activity_detail.standards_profile_id,
            focus_standard_ids=tuple(activity_detail.focus_standard_ids),
            choose_scale=lambda: _default_scale(current),
            existing=review.draft,
        )
        if draft == review.draft:
            show_result(
                "Rubric Unchanged — No Revision Created",
                (
                    f"Exact original revision: {review.criterion_set_id}",
                    "The draft matches the original; no record was written.",
                ),
            )
            return
        actor = state.require_actor()
        validate_criterion_draft(
            draft,
            activity_scoring_orientation=current.scoring_orientation,
            standards_profile_id=activity_detail.standards_profile_id,
            focus_standard_ids=tuple(activity_detail.focus_standard_ids),
            standards_library=library,
            created_provenance=provenance(actor),
        )
        replacement_id = f"criterion-set-{uuid4().hex}"
        criterion_ids = tuple(
            f"criterion-{uuid4().hex}" for _ in draft.criteria
        )
        new_specs = criterion_specs(draft, criterion_ids)
        if not confirm_write(
            "Revise Native Rubric",
            "REVISE",
            (
                f"Activity: {current.title}",
                f"Original: {review.criterion_set_id} "
                f"(revision {review.revision}, lineage {review.lineage_id})",
                *describe_criterion_draft(draft, focus_choices=focus_choices),
                f"Successor Set ID: {replacement_id}",
                f"Successor revision: {review.revision + 1}",
                "All successor Criteria receive new native identities.",
                "The original revision and historical Scores are preserved.",
                "No Activity selection is changed by this revision.",
                "After creation, use 'Use an existing rubric' to choose whether "
                "to replace an earlier selected revision or keep both.",
            ),
        ):
            return
        fresh = read_activity_criterion_set_selection(
            current.class_id,
            current.activity_id,
            standards_library=library,
        )
        if fresh != selection or (
            _latest(activity).snapshot_revision != current.snapshot_revision
        ):
            raise ValueError("Activity changed since review. Reopen the revision.")
        fresh_heads = list_criterion_sets(
            current.class_id,
            current.activity_id,
            standards_library=library,
            current_only=True,
        )
        if review.criterion_set_id not in {
            item.criterion_set_id for item in fresh_heads
        }:
            raise ValueError(
                "The original is no longer a current head. Reload to revise."
            )
        try:
            result = revise_criterion_set(
                ReviseCriterionSetRequest(
                    class_id=current.class_id,
                    activity_id=current.activity_id,
                    criterion_set_id=review.criterion_set_id,
                    replacement_criterion_set_id=replacement_id,
                    name=draft.name,
                    purpose=draft.purpose,
                    revision=review.revision + 1,
                    scope=draft.scope,
                    criterion_set_kind=draft.criterion_set_kind,
                    criteria=new_specs,
                    status="active",
                    standards_profile_id=(
                        activity_detail.standards_profile_id
                        if draft.criterion_set_kind in {"standard_backed", "mixed"}
                        else None
                    ),
                    expected_snapshot_revision=selection.snapshot_revision,
                    actor=actor,
                ),
                standards_library=library,
            )
            verified = show_criterion_set(
                current.class_id,
                current.activity_id,
                replacement_id,
                standards_library=library,
            )
            selected_after = read_activity_criterion_set_selection(
                current.class_id,
                current.activity_id,
                standards_library=library,
            )
            if (
                verified.summary.lineage_id != review.lineage_id
                or verified.summary.revision != review.revision + 1
                or verified.summary.supersedes_criterion_set_id
                != review.criterion_set_id
                or verified.summary.snapshot_revision
                != result.commit.snapshot_revision
                or selected_after.snapshot_revision
                != result.commit.snapshot_revision
                or selected_after.criterion_set_ids
                != selection.criterion_set_ids
                or not verified.summary.is_current
            ):
                raise ValueError("Successor/selection verification mismatch.")
        except Exception as error:
            try:
                observed = show_criterion_set(
                    current.class_id,
                    current.activity_id,
                    replacement_id,
                    standards_library=library,
                )
            except Exception:
                show_result(
                    "Rubric Revision Outcome Unknown",
                    (
                        f"Proposed successor: {replacement_id}",
                        f"Revision error: {error}",
                        "Do not retry blindly. Inspect lineage before revising.",
                    ),
                )
                return
            if (
                observed.summary.lineage_id == review.lineage_id
                and observed.summary.supersedes_criterion_set_id
                == review.criterion_set_id
                and observed.summary.revision == review.revision + 1
            ):
                show_result(
                    "Rubric Revision Verified After Error",
                    (
                        f"Native successor: {replacement_id}",
                        "Immutable predecessor retained.",
                        "Activity selection was not automatically changed.",
                    ),
                )
            else:
                show_result(
                    "Rubric Revision Requires Review",
                    (
                        f"Proposed successor: {replacement_id}",
                        f"Revision error: {error}",
                        "Inspect lineage and selection before any retry.",
                    ),
                )
            return
        show_result(
            "Rubric Revised — Successor Not Yet Selected",
            (
                f"Original revision: {review.criterion_set_id}",
                f"New revision: {replacement_id}",
                f"Lineage: {review.lineage_id}",
                f"Snapshot: {verified.summary.snapshot_revision}",
                "Historical Scores and original Criterion IDs remain intact.",
                "Previously selected rubric revisions remain selected.",
                "Use 'Use an existing rubric' to choose replacement or retention "
                "of earlier selected revisions of this lineage.",
                "No Scores, Grades, evidence, or presets were created.",
                "Next: choose Save this assessment for another class.",
            ),
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
        print("1. Create and use a rubric (guided)")
        print("2. Browse Criterion Sets")
        print("3. Revise an existing rubric (guided)")
        print("4. Use an existing rubric (guided)")
        print("5. Save this assessment for another class")
        print("6. Advanced: create native Criterion Set")
        print("7. Create a rubric definition only (guided)")
        print("8. Advanced: revise a native Criterion Set")
        print("9. Advanced: select Activity Criterion Sets")
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
            _create_and_use_guided_criterion_set(activity, state)
        elif choice == "2":
            _browse_criterion_sets(activity)
        elif choice == "3":
            _revise_criterion_set(activity, state)
        elif choice == "4":
            _use_existing_criterion_set(activity, state)
        elif choice == "5":
            _save_criterion_set_as_preset(activity, state)
        elif choice == "6":
            _create_criterion_set(activity, state)
        elif choice == "7":
            _create_guided_criterion_set(activity, state)
        elif choice == "8":
            _revise_criterion_set_advanced(activity, state)
        elif choice == "9":
            _select_criterion_sets_advanced(activity, state)
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


def _saved_criteria_menu_labels(
    presets: tuple[CriterionSetPresetRevision, ...],
) -> tuple[str, ...]:
    """Show verified distinctions; use a stable ID only for true label collisions."""
    base = tuple(
        f"{value.name} | {len(value.criteria)} Criteria | "
        f"{value.criterion_set_kind.replace('_', ' ')} | "
        f"saved revision {value.revision}"
        for value in presets
    )
    return tuple(
        f"{label} | Preset ID: {value.preset_id}"
        if base.count(label) > 1 else label
        for label, value in zip(base, presets)
    )


def _saved_criteria_preview(
    value: CriterionSetPresetRevision,
) -> tuple[str, ...]:
    """Describe the exact immutable definition before creating Activity records."""
    lines = [
        f"Assessment: {value.name}",
        f"Preset ID: {value.preset_id}",
        f"Saved revision: {value.revision} ({value.preset_revision_id})",
        f"Purpose: {value.purpose}",
        f"Assessment kind: {value.criterion_set_kind.replace('_', ' ')}",
        f"Standards profile: {value.standards_profile_id or '-'}",
        f"Criteria: {len(value.criteria)}",
    ]
    for index, criterion in enumerate(value.criteria, start=1):
        lines.extend(
            (
                f"{index}. {criterion.label} [{criterion.criterion_kind}]",
                f"   What is assessed: {criterion.definition}",
                "   Targets: " + ", ".join(
                    kind.replace('_', ' ') for kind in criterion.supported_target_kinds
                ),
                f"   Governing Standard: {criterion.standard_id or '-'}",
                "   Alignment Standards: "
                + (", ".join(criterion.alignment_standard_ids) or "-"),
                "   Recommended Scale preset: "
                + (
                    f"{criterion.default_scoring_scale_preset_id} "
                    f"({criterion.default_scoring_scale_preset_revision_id})"
                    if criterion.default_scoring_scale_preset_id is not None
                    else "none"
                ),
            )
        )
    return tuple(lines)


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
        # Resolve exact immutable revisions before displaying options. Do not
        # silently replace a selected preset with a later library head.
        available: list[CriterionSetPresetRevision] = []
        for summary in summaries:
            exact = get_preset_revision(
                "criterion_set", summary.preset_id, summary.preset_revision_id
            )
            if not isinstance(exact, CriterionSetPresetRevision):
                raise ValueError("Saved Criterion Set preset has the wrong type.")
            if exact.revision != summary.revision or exact.status != "active":
                raise ValueError("Saved assessment changed; reopen the selection.")
            available.append(exact)
        value = select_one(
            "Choose Saved Assessment",
            available,
            _saved_criteria_menu_labels(tuple(available)),
            help_text=(
                "Choose the exact saved assessment. Read its full definition "
                "before deciding whether to use it."
            ),
        )
        show_result(
            "Saved Assessment — Read-only Preview",
            (
                *_saved_criteria_preview(value),
                "No Activity configuration, Scores, or evidence changed.",
            ),
        )
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
                *_saved_criteria_preview(value),
                f"Verified Criteria count: {prepared.criterion_count}",
                f"Selected Scale: {prepared.scoring_scale_preset_name or 'none'}",
                (
                    f"Saved Scale revision: {scale.revision} "
                    f"({scale.preset_revision_id}); Preset ID: {scale.preset_id}"
                    if scale is not None else "Saved Scale revision: none"
                ),
                f"Verified Standards profile: {prepared.standards_profile_id or '-'}",
                "This creates fresh Activity configuration only.",
                "No Scores, Groups, student data, or evidence will be copied.",
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


def _continue_created_scale(
    activity: ActivitySummary,
    state: MenuSessionContext,
    scale_id: str,
) -> None:
    """Offer optional next steps without claiming a Criterion is linked."""
    try:
        choice = select_one(
            "Scoring Scale Created — Next Step",
            ("back", "criteria", "reuse"),
            (
                "Back to Scoring Scales (created but not linked)",
                "Open Criteria setup (choose this Scale explicitly)",
                "Save this Scale for another class (separate approval)",
            ),
            help_text=(
                "The native Scale already exists. Criteria and saved presets "
                "are separate operations. Back does not undo creation."
            ),
        )
    except CancelMenuAction:
        return
    if choice == "back":
        return
    if choice == "criteria":
        show_result(
            "Configure Criteria — Native Scale Available",
            (
                f"Native Scale already created: {scale_id}",
                "No Criterion is linked yet.",
                "The existing Criteria setup will let you choose an exact "
                "native Scale for each applicable Criterion.",
                "A link exists only after a separate successful Criterion write.",
                "This continuation creates no Scores or Grades.",
            ),
        )
        try:
            _criterion_set_menu(_latest(activity), state)
        except CancelMenuAction:
            return
        except Exception as error:
            show_result(
                "Native Scale Saved — Criteria Not Confirmed",
                (
                    f"Native Scale remains created: {scale_id}",
                    f"Criteria setup error: {error}",
                    "Inspect the current Criterion Sets before retrying.",
                    "No Criterion link is claimed by this continuation.",
                ),
            )
        return
    if choice != "reuse":
        raise ValueError("Unknown native Scale continuation action")
    try:
        # Refresh snapshot AFTER native Scale creation. The separate preset
        # prepare/review/commit service owns its own currentness checks.
        saved_id = _save_scale_id_as_preset(
            _latest(activity), state, scale_id
        )
    except CancelMenuAction:
        return
    except Exception as error:
        show_result(
            "Native Scale Saved — Preset Outcome Not Confirmed",
            (
                f"Native Scale remains created: {scale_id}",
                f"Preset operation error: {error}",
                "Do not assume the preset write was rolled back.",
                "Inspect Reusable Presets before trying again.",
                "No Scores, Grades, or student records were created here.",
            ),
        )
        return
    if saved_id is None:
        show_result(
            "Native Scale Saved — Reuse Declined",
            (
                f"Native Scale remains created: {scale_id}",
                "Reusable preset was not saved; approval was declined.",
            ),
        )
        return
    show_result(
        "Native Scale and Reusable Preset Saved Separately",
        (
            f"Native Scale: {scale_id}",
            f"Reusable preset: {saved_id}",
            "Both writes succeeded independently.",
            "No Criterion is linked by saving a preset.",
            "No Scores, Grades, evidence, or student records were copied.",
        ),
    )


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
        print("5. Use a saved Scoring Scale")
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
            created_id = _create_scale(activity, state)
            if created_id is not None:
                _continue_created_scale(activity, state, created_id)
        elif choice == "2":
            _browse_scales(activity)
        elif choice == "3":
            _revise_scale(activity, state)
        elif choice == "4":
            _save_scale_as_preset(activity, state)
        elif choice == "5":
            _import_saved_scale(activity, state)
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
        print("4. Review Score Analysis")
        print("O. Open returned work")
        print("V. Open a verified saved assembly version")
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
            print(
                "Open returned work uses your normal PDF viewer and "
                "records no Score."
            )
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
        elif choice == "4":
            launch_score_analysis_menu(activity)
        elif choice.upper() == "O":
            open_returned_work(activity)
        elif choice.upper() == "V":
            open_verified_assembly_version(activity)
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
        print("7. Review Score Analysis")
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
        elif choice == "7":
            launch_score_analysis_menu(activity)
        else:
            print(navigation_hint_with_help())
            pause_for_user()


__all__ = [
    "launch_assessment_setup_menu",
    "launch_score_menu",
    "launch_scoring_menu",
]
