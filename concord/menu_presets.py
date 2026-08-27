"""Workspace-level teacher menu for reusable Concord presets."""

from __future__ import annotations

import json
from uuid import uuid4

from pds_core.standards_selection import (
    list_profiles_for_selection,
    list_standards_for_profile_selection,
    list_standards_for_selection,
)

from concord.menu_context import CancelMenuAction, MenuSessionContext
from concord.menu_navigation import (
    ConcordMenuChoice,
    NavigationChoice,
    navigation_hint_with_help,
    parse_menu_navigation,
)
from concord.menu_prompts import (
    confirm_write,
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
from concord.models import ScoringScaleLevel
from concord.reusable_presets import (
    CriterionPresetSpec,
    CriterionSetPresetRevision,
    ResponsibilityPresetRevision,
    RolePresetRevision,
    ScoringScalePresetRevision,
)
from concord.workflows import (
    CreateCriterionSetPresetRequest,
    CreateResponsibilityPresetRequest,
    CreateRolePresetRequest,
    CreateScoringScalePresetRequest,
    PresetSummary,
    ReviseCriterionSetPresetRequest,
    ReviseResponsibilityPresetRequest,
    ReviseRolePresetRequest,
    ReviseScoringScalePresetRequest,
    create_criterion_set_preset,
    create_responsibility_preset,
    create_role_preset,
    create_scoring_scale_preset,
    get_preset,
    list_presets,
    retire_preset,
    revise_criterion_set_preset,
    revise_responsibility_preset,
    revise_role_preset,
    revise_scoring_scale_preset,
)
from concord.workflows.errors import ConcordWorkflowError

_ROLE_KEYS = (
    "facilitator",
    "recorder",
    "observer",
    "speaker",
    "researcher",
    "builder",
    "presenter",
)
_SCALE_TYPES = ("numeric", "ordinal", "categorical", "binary", "teacher_defined")
_TARGET_KINDS = (
    "core_student",
    "concord_group",
    "concord_session",
    "concord_activity",
    "concord_artifact_instance",
)
_PRESET_KINDS = (
    "role",
    "responsibility",
    "criterion_set",
    "scoring_scale",
)
_PRESET_LABELS = (
    "Roles",
    "Responsibilities",
    "Criterion Sets",
    "Scoring Scales",
)


def _help() -> None:
    clear_screen()
    print_menu_header("Reusable Presets Help")
    print("Presets are saved definitions for future setup.")
    print("Using a preset creates fresh Activity or assignment state.")
    print("Changing a preset never changes an Activity that already used it.")
    print(
        "Scores, students, Groups, evidence, and prior assignment history "
        "are not presets."
    )
    print()
    pause_for_user()


def _kind_label(kind: str) -> str:
    return {
        "role": "Role",
        "responsibility": "Responsibility",
        "criterion_set": "Criterion Set",
        "scoring_scale": "Scoring Scale",
    }[kind]


def _choose_kind(title: str = "Choose a Preset Type") -> str:
    return select_one(
        title,
        _PRESET_KINDS,
        _PRESET_LABELS,
        help_text="Choose the kind of reusable definition you want to manage.",
    )


def _summary_label(item: PresetSummary) -> str:
    return f"{item.name} ({item.preset_id}) - {item.status}"


def _choose_preset(
    kind: str,
    *,
    title: str,
    include_retired: bool = False,
) -> PresetSummary:
    items = list_presets(kind, include_retired=include_retired)
    if not items:
        raise ConcordWorkflowError(
            f"No reusable {_kind_label(kind)} presets are available."
        )
    return select_one(
        title,
        items,
        tuple(_summary_label(item) for item in items),
        help_text=(
            "Choose one saved preset. Revision details remain hidden unless viewed."
        ),
    )


def _list(kind: str) -> None:
    items = list_presets(kind, include_retired=True)
    lines = tuple(_summary_label(item) for item in items)
    if not lines:
        lines = (f"No reusable {_kind_label(kind)} presets are available.",)
    show_result(f"Saved {_kind_label(kind)} Presets", lines)


def _detail_lines(kind: str, preset_id: str) -> tuple[str, ...]:
    value = get_preset(kind, preset_id)
    lines = [
        f"Name: {value.name}",
        f"Status: {value.status}",
        f"Saved version: {value.revision}",
    ]
    if isinstance(value, RolePresetRevision):
        lines.extend(
            (
                f"Role: {value.role_label or value.role_key}",
                f"Role key: {value.role_key}",
                f"Description: {value.description or '-'}",
            )
        )
    elif isinstance(value, ResponsibilityPresetRevision):
        lines.extend(
            (
                f"Responsibility: {value.description}",
                f"Expected output: {value.expected_output or '-'}",
            )
        )
    elif isinstance(value, ScoringScalePresetRevision):
        lines.extend(
            (
                f"Scale type: {value.scale_type}",
                f"Levels: {len(value.levels)}",
                f"Intended use: {value.intended_use or '-'}",
            )
        )
        lines.extend(
            f"  {json.dumps(level.value)} - {level.label}: {level.meaning}"
            for level in value.levels
        )
    elif isinstance(value, CriterionSetPresetRevision):
        lines.extend(
            (
                f"Purpose: {value.purpose}",
                f"Kind: {value.criterion_set_kind}",
                f"Standards profile: {value.standards_profile_id or '-'}",
                f"Criteria: {len(value.criteria)}",
            )
        )
        lines.extend(
            f"  {criterion.label} ({criterion.key}) - {criterion.criterion_kind}"
            for criterion in value.criteria
        )
    return tuple(lines)


def _show(kind: str) -> None:
    selected = _choose_preset(
        kind,
        title=f"Choose a {_kind_label(kind)} Preset",
        include_retired=True,
    )
    show_result(f"{_kind_label(kind)} Preset", _detail_lines(kind, selected.preset_id))


def _role_key(default: str | None = None) -> str:
    choices = (*_ROLE_KEYS, "__custom__")
    labels = tuple(item.replace("_", " ").title() for item in _ROLE_KEYS) + (
        "Custom namespaced role",
    )
    if default is not None and default not in _ROLE_KEYS:
        return prompt_text(
            "Role Preset",
            "Role key",
            help_text="Use a built-in Role key or a namespace-qualified custom key.",
            default=default,
        ) or default
    selected = select_one(
        "Role Preset",
        choices,
        labels,
        help_text="Choose the reusable Role definition.",
    )
    if selected != "__custom__":
        return selected
    value = prompt_text(
        "Role Preset",
        "Custom Role key",
        help_text="Example: school:discussion_leader",
        default=default,
    )
    assert value is not None
    return value


def _optional_text(title: str, label: str, *, default: str | None = None) -> str | None:
    return prompt_text(
        title,
        label,
        help_text="Optional teacher-facing reusable guidance.",
        optional=True,
        default=default,
    )


def _preset_identity(
    title: str,
    *,
    default_name: str | None = None,
) -> tuple[str, str, str]:
    name = prompt_text(
        title,
        "Preset name",
        help_text="Use the short teacher-facing name shown during setup.",
        default=default_name,
    )
    assert name is not None
    preset_id = prompt_text(
        title,
        "Preset ID",
        help_text="Durable reusable preset identifier.",
        default=slug_identifier(name, f"preset-{uuid4().hex[:8]}"),
    )
    assert preset_id is not None
    revision_id = prompt_text(
        title,
        "Saved-version ID",
        help_text="Fresh immutable identifier for the first saved version.",
        default=f"{preset_id}-v1",
    )
    assert revision_id is not None
    return name, preset_id, revision_id


def _create_role(state: MenuSessionContext) -> None:
    name, preset_id, revision_id = _preset_identity("Create Role Preset")
    role_key = _role_key()
    label = _optional_text("Create Role Preset", "Display label")
    description = _optional_text("Create Role Preset", "Description")
    if not confirm_write(
        "Create Role Preset",
        "CREATE",
        (f"Name: {name}", f"Role: {label or role_key}"),
    ):
        return
    result = create_role_preset(
        CreateRolePresetRequest(
            preset_id=preset_id,
            preset_revision_id=revision_id,
            name=name,
            role_key=role_key,
            role_label=label,
            description=description,
            actor=state.require_actor(),
        )
    )
    show_result("Role Preset Created", (f"Preset: {result.preset_id}",))


def _create_responsibility(state: MenuSessionContext) -> None:
    name, preset_id, revision_id = _preset_identity("Create Responsibility Preset")
    description = prompt_text(
        "Create Responsibility Preset",
        "Responsibility",
        help_text="Describe the reusable obligation or expected work.",
    )
    assert description is not None
    output = _optional_text("Create Responsibility Preset", "Expected output")
    if not confirm_write(
        "Create Responsibility Preset",
        "CREATE",
        (f"Name: {name}", f"Responsibility: {description}"),
    ):
        return
    result = create_responsibility_preset(
        CreateResponsibilityPresetRequest(
            preset_id=preset_id,
            preset_revision_id=revision_id,
            name=name,
            description=description,
            expected_output=output,
            actor=state.require_actor(),
        )
    )
    show_result("Responsibility Preset Created", (f"Preset: {result.preset_id}",))


def _json_scalar(raw: str) -> str | int | float | bool:
    value: object = json.loads(raw)
    if value is None or isinstance(value, (list, dict)):
        raise ValueError("Scale values must be non-null JSON scalars.")
    if not isinstance(value, (str, int, float, bool)):
        raise ValueError("Scale values must be JSON strings, numbers, or booleans.")
    return value


def _build_scale_levels(
    scale_type: str,
    defaults: tuple[ScoringScaleLevel, ...] = (),
) -> tuple[ScoringScaleLevel, ...]:
    count = prompt_positive_int(
        "Scoring Scale Preset",
        "Number of levels",
        help_text="Every level and exact value is preserved in the saved preset.",
        default=len(defaults) or (2 if scale_type == "binary" else 4),
    )
    if scale_type == "binary" and count != 2:
        raise ValueError("A binary Scale requires exactly two levels.")
    result: list[ScoringScaleLevel] = []
    for index in range(count):
        previous = defaults[index] if index < len(defaults) else None
        raw = prompt_text(
            f"Scale Level {index + 1}",
            "Exact JSON value",
            help_text='Examples: 1, 1.0, "1", and true remain distinct.',
            default=None if previous is None else json.dumps(previous.value),
        )
        assert raw is not None
        value = _json_scalar(raw)
        label = prompt_text(
            f"Scale Level {index + 1}",
            "Label",
            help_text="Teacher-facing label for this exact value.",
            default=None if previous is None else previous.label,
        )
        meaning = prompt_text(
            f"Scale Level {index + 1}",
            "Meaning",
            help_text="Describe what this exact level means.",
            default=None if previous is None else previous.meaning,
        )
        assert label is not None and meaning is not None
        description = _optional_text(
            f"Scale Level {index + 1}",
            "Description",
            default=None if previous is None else previous.description,
        )
        result.append(
            ScoringScaleLevel(
                value=value,
                label=label,
                meaning=meaning,
                position=index + 1 if scale_type == "ordinal" else None,
                description=description,
            )
        )
    return tuple(result)


def _scale_type(default: str | None = None) -> str:
    if default in _SCALE_TYPES:
        labels = tuple(
            f"{item.replace('_', ' ').title()}{' (current)' if item == default else ''}"
            for item in _SCALE_TYPES
        )
    else:
        labels = tuple(item.replace("_", " ").title() for item in _SCALE_TYPES)
    return select_one(
        "Scoring Scale Preset",
        _SCALE_TYPES,
        labels,
        help_text="Choose the exact native value semantics for this saved Scale.",
    )


def _create_scale(state: MenuSessionContext) -> None:
    name, preset_id, revision_id = _preset_identity("Create Scoring Scale Preset")
    scale_type = _scale_type()
    levels = _build_scale_levels(scale_type)
    intended_use = _optional_text("Create Scoring Scale Preset", "Intended use")
    aggregation = _optional_text("Create Scoring Scale Preset", "Aggregation guidance")
    if not confirm_write(
        "Create Scoring Scale Preset",
        "CREATE",
        (f"Name: {name}", f"Type: {scale_type}", f"Levels: {len(levels)}"),
    ):
        return
    result = create_scoring_scale_preset(
        CreateScoringScalePresetRequest(
            preset_id=preset_id,
            preset_revision_id=revision_id,
            name=name,
            scale_type=scale_type,
            levels=levels,
            intended_use=intended_use,
            aggregation_guidance=aggregation,
            actor=state.require_actor(),
        )
    )
    show_result("Scoring Scale Preset Created", (f"Preset: {result.preset_id}",))


def _profile_id() -> str | None:
    library = load_menu_standards_library()
    if library is None:
        return _optional_text("Criterion Set Preset", "Standards profile ID")
    profiles = list_profiles_for_selection(library)
    if not profiles:
        return None
    values = (None, *(item.profile_id for item in profiles))
    labels = ("No profile restriction", *(item.label for item in profiles))
    return select_one(
        "Criterion Set Preset",
        values,
        labels,
        help_text="Optionally bind this saved rubric to one Core standards profile.",
    )


def _standard_id(profile_id: str | None) -> str:
    library = load_menu_standards_library()
    if library is None:
        value = prompt_text(
            "Criterion Preset",
            "Core Standard ID",
            help_text="Enter the exact current Core Standard identifier.",
        )
        assert value is not None
        return value
    items = (
        list_standards_for_profile_selection(library, profile_id)
        if profile_id is not None
        else list_standards_for_selection(library, available_module="concord")
    )
    if not items:
        raise ValueError("No current Core Standards are available for this preset.")
    selected = select_one(
        "Criterion Preset Standard",
        items,
        tuple(item.label for item in items),
        help_text="Choose the exact Core Standard this reusable Criterion governs.",
    )
    return selected.standard_id


def _recommended_scale() -> tuple[str | None, str | None]:
    scales = list_presets("scoring_scale")
    if not scales:
        return None, None
    values = (None, *scales)
    labels = (
        "No recommended Scale",
        *tuple(f"{item.name} ({item.preset_id})" for item in scales),
    )
    selected = select_one(
        "Recommended Scoring Scale",
        values,
        labels,
        help_text=(
            "This is a setup recommendation; a teacher may choose another Scale later."
        ),
    )
    if selected is None:
        return None, None
    return selected.preset_id, selected.preset_revision_id


def _criterion_specs(
    set_kind: str,
    profile_id: str | None,
    defaults: tuple[CriterionPresetSpec, ...] = (),
) -> tuple[CriterionPresetSpec, ...]:
    count = prompt_positive_int(
        "Criterion Set Preset",
        "Number of Criteria",
        help_text="Create the ordered reusable Criterion definitions.",
        default=len(defaults) or 1,
    )
    result: list[CriterionPresetSpec] = []
    recommended_id, recommended_revision_id = _recommended_scale()
    for index in range(count):
        previous = defaults[index] if index < len(defaults) else None
        key = prompt_text(
            f"Criterion {index + 1}",
            "Key",
            help_text="Short stable reusable Criterion key.",
            default=None if previous is None else previous.key,
        )
        label = prompt_text(
            f"Criterion {index + 1}",
            "Label",
            help_text="Teacher-facing Criterion label.",
            default=None if previous is None else previous.label,
        )
        definition = prompt_text(
            f"Criterion {index + 1}",
            "Definition",
            help_text="Define the judgment represented by this Criterion.",
            default=None if previous is None else previous.definition,
        )
        assert key is not None and label is not None and definition is not None
        if set_kind == "mixed":
            kind = select_one(
                f"Criterion {index + 1} Kind",
                ("standard_backed", "local"),
                ("Standard-backed", "Local"),
                help_text="Mixed presets may contain both Criterion kinds.",
            )
        else:
            kind = set_kind
        standard_id = _standard_id(profile_id) if kind == "standard_backed" else None
        targets = select_many(
            f"Criterion {index + 1} Targets",
            _TARGET_KINDS,
            tuple(item.replace("_", " ").title() for item in _TARGET_KINDS),
            help_text="Select every target kind this reusable Criterion permits.",
        )
        result.append(
            CriterionPresetSpec(
                key=key,
                label=label,
                definition=definition,
                criterion_kind=kind,
                supported_target_kinds=targets,
                standard_id=standard_id,
                default_scoring_scale_preset_id=recommended_id,
                default_scoring_scale_preset_revision_id=recommended_revision_id,
            )
        )
    return tuple(result)


def _create_criterion(state: MenuSessionContext) -> None:
    name, preset_id, revision_id = _preset_identity("Create Criterion Set Preset")
    purpose = prompt_text(
        "Create Criterion Set Preset",
        "Purpose",
        help_text="Describe what this reusable Criterion Set is for.",
    )
    assert purpose is not None
    kind = select_one(
        "Criterion Set Kind",
        ("standard_backed", "local", "mixed"),
        ("Standard-backed", "Local", "Mixed"),
        help_text="Choose which Criterion kinds the saved Set may contain.",
    )
    profile_id = _profile_id() if kind in {"standard_backed", "mixed"} else None
    criteria = _criterion_specs(kind, profile_id)
    if not confirm_write(
        "Create Criterion Set Preset",
        "CREATE",
        (f"Name: {name}", f"Kind: {kind}", f"Criteria: {len(criteria)}"),
    ):
        return
    result = create_criterion_set_preset(
        CreateCriterionSetPresetRequest(
            preset_id=preset_id,
            preset_revision_id=revision_id,
            name=name,
            purpose=purpose,
            criterion_set_kind=kind,
            criteria=criteria,
            standards_profile_id=profile_id,
            actor=state.require_actor(),
        ),
        standards_library=load_menu_standards_library(),
    )
    show_result("Criterion Set Preset Created", (f"Preset: {result.preset_id}",))


def _create(kind: str, state: MenuSessionContext) -> None:
    if kind == "role":
        _create_role(state)
    elif kind == "responsibility":
        _create_responsibility(state)
    elif kind == "criterion_set":
        _create_criterion(state)
    else:
        _create_scale(state)


def _successor_id(preset_id: str, revision: int) -> str:
    value = prompt_text(
        "Edit Preset",
        "New saved-version ID",
        help_text=(
            "Editing saves a new immutable version; old versions remain unchanged."
        ),
        default=f"{preset_id}-v{revision + 1}",
    )
    assert value is not None
    return value


def _edit_role(summary: PresetSummary, state: MenuSessionContext) -> None:
    current = get_preset("role", summary.preset_id)
    assert isinstance(current, RolePresetRevision)
    name = prompt_text(
        "Edit Role Preset",
        "Name",
        help_text="Teacher-facing name.",
        default=current.name,
    )
    assert name is not None
    role_key = _role_key(current.role_key)
    label = _optional_text(
        "Edit Role Preset", "Display label", default=current.role_label
    )
    description = _optional_text(
        "Edit Role Preset", "Description", default=current.description
    )
    revision_id = _successor_id(current.preset_id, current.revision)
    if not confirm_write(
        "Edit Role Preset",
        "REVISE",
        (f"Preset: {current.name}", f"New version: {current.revision + 1}"),
    ):
        return
    revise_role_preset(
        ReviseRolePresetRequest(
            preset_id=current.preset_id,
            preset_revision_id=revision_id,
            expected_revision=current.revision,
            name=name,
            role_key=role_key,
            role_label=label,
            description=description,
            applicability_hints=current.applicability_hints,
            actor=state.require_actor(),
        )
    )


def _edit_responsibility(summary: PresetSummary, state: MenuSessionContext) -> None:
    current = get_preset("responsibility", summary.preset_id)
    assert isinstance(current, ResponsibilityPresetRevision)
    name = prompt_text(
        "Edit Responsibility Preset",
        "Name",
        help_text="Teacher-facing name.",
        default=current.name,
    )
    description = prompt_text(
        "Edit Responsibility Preset",
        "Responsibility",
        help_text="Reusable obligation.",
        default=current.description,
    )
    assert name is not None and description is not None
    output = _optional_text(
        "Edit Responsibility Preset",
        "Expected output",
        default=current.expected_output,
    )
    revision_id = _successor_id(current.preset_id, current.revision)
    if not confirm_write(
        "Edit Responsibility Preset",
        "REVISE",
        (f"Preset: {current.name}", f"New version: {current.revision + 1}"),
    ):
        return
    revise_responsibility_preset(
        ReviseResponsibilityPresetRequest(
            preset_id=current.preset_id,
            preset_revision_id=revision_id,
            expected_revision=current.revision,
            name=name,
            description=description,
            expected_output=output,
            applicability_hints=current.applicability_hints,
            actor=state.require_actor(),
        )
    )


def _edit_scale(summary: PresetSummary, state: MenuSessionContext) -> None:
    current = get_preset("scoring_scale", summary.preset_id)
    assert isinstance(current, ScoringScalePresetRevision)
    name = prompt_text(
        "Edit Scoring Scale Preset",
        "Name",
        help_text="Teacher-facing name.",
        default=current.name,
    )
    assert name is not None
    scale_type = _scale_type(current.scale_type)
    keep = select_one(
        "Edit Scoring Scale Preset",
        (True, False),
        ("Keep the current exact levels", "Revise the levels"),
        help_text="A revision never mutates the old saved Scale version.",
    )
    levels = current.levels if keep else _build_scale_levels(scale_type, current.levels)
    intended = _optional_text(
        "Edit Scoring Scale Preset",
        "Intended use",
        default=current.intended_use,
    )
    aggregation = _optional_text(
        "Edit Scoring Scale Preset",
        "Aggregation guidance",
        default=current.aggregation_guidance,
    )
    revision_id = _successor_id(current.preset_id, current.revision)
    if not confirm_write(
        "Edit Scoring Scale Preset",
        "REVISE",
        (f"Preset: {current.name}", f"New version: {current.revision + 1}"),
    ):
        return
    revise_scoring_scale_preset(
        ReviseScoringScalePresetRequest(
            preset_id=current.preset_id,
            preset_revision_id=revision_id,
            expected_revision=current.revision,
            name=name,
            scale_type=scale_type,
            levels=levels,
            intended_use=intended,
            aggregation_guidance=aggregation,
            actor=state.require_actor(),
        )
    )


def _edit_criterion(summary: PresetSummary, state: MenuSessionContext) -> None:
    current = get_preset("criterion_set", summary.preset_id)
    assert isinstance(current, CriterionSetPresetRevision)
    name = prompt_text(
        "Edit Criterion Set Preset",
        "Name",
        help_text="Teacher-facing name.",
        default=current.name,
    )
    purpose = prompt_text(
        "Edit Criterion Set Preset",
        "Purpose",
        help_text="Reusable purpose.",
        default=current.purpose,
    )
    assert name is not None and purpose is not None
    kind = select_one(
        "Criterion Set Kind",
        ("standard_backed", "local", "mixed"),
        ("Standard-backed", "Local", "Mixed"),
        help_text="Choose the kinds permitted by the successor saved version.",
    )
    profile_id = _profile_id() if kind in {"standard_backed", "mixed"} else None
    keep = select_one(
        "Edit Criterion Set Preset",
        (True, False),
        ("Keep the current Criteria", "Revise the Criteria"),
        help_text="Keeping Criteria preserves their reusable definitions exactly.",
    )
    criteria = (
        current.criteria
        if keep
        else _criterion_specs(kind, profile_id, current.criteria)
    )
    revision_id = _successor_id(current.preset_id, current.revision)
    if not confirm_write(
        "Edit Criterion Set Preset",
        "REVISE",
        (f"Preset: {current.name}", f"New version: {current.revision + 1}"),
    ):
        return
    revise_criterion_set_preset(
        ReviseCriterionSetPresetRequest(
            preset_id=current.preset_id,
            preset_revision_id=revision_id,
            expected_revision=current.revision,
            name=name,
            purpose=purpose,
            criterion_set_kind=kind,
            criteria=criteria,
            standards_profile_id=profile_id,
            actor=state.require_actor(),
        ),
        standards_library=load_menu_standards_library(),
    )


def _edit(kind: str, state: MenuSessionContext) -> None:
    selected = _choose_preset(kind, title=f"Edit a {_kind_label(kind)} Preset")
    if kind == "role":
        _edit_role(selected, state)
    elif kind == "responsibility":
        _edit_responsibility(selected, state)
    elif kind == "criterion_set":
        _edit_criterion(selected, state)
    else:
        _edit_scale(selected, state)
    show_result("Preset Updated", ("Saved as a new immutable version.",))


def _retire(kind: str, state: MenuSessionContext) -> None:
    selected = _choose_preset(kind, title=f"Retire a {_kind_label(kind)} Preset")
    current = get_preset(kind, selected.preset_id)
    revision_id = _successor_id(current.preset_id, current.revision)
    if not confirm_write(
        "Retire Preset",
        "RETIRE",
        (
            f"Preset: {current.name}",
            "Past Activities and assignments remain unchanged.",
            "The preset will no longer appear in ordinary saved-preset selection.",
        ),
    ):
        return
    retire_preset(
        kind,
        current.preset_id,
        preset_revision_id=revision_id,
        expected_revision=current.revision,
        actor=state.require_actor(),
    )
    show_result("Preset Retired", (f"Preset: {current.name}",))


def _kind_menu(kind: str, state: MenuSessionContext) -> None:
    label = _kind_label(kind)
    while True:
        clear_screen()
        print_menu_header(f"{label} Presets")
        print("1. View saved presets")
        print("2. Create a preset")
        print("3. Edit a preset")
        print("4. Retire a preset")
        print_navigation()
        print()
        raw = input("Select an option: ").strip()
        navigation = parse_menu_navigation(raw)
        if navigation is ConcordMenuChoice.HELP:
            _help()
        elif navigation is NavigationChoice.BACK:
            return
        else:
            try:
                if raw == "1":
                    _list(kind)
                elif raw == "2":
                    _create(kind, state)
                elif raw == "3":
                    _edit(kind, state)
                elif raw == "4":
                    _retire(kind, state)
                else:
                    print(navigation_hint_with_help())
                    pause_for_user()
            except CancelMenuAction:
                continue
            except Exception as error:
                show_result("Preset Error", (str(error),))


def launch_preset_library_menu(state: MenuSessionContext) -> None:
    """Manage workspace-level saved configuration without exposing storage mechanics."""
    while True:
        clear_screen()
        print_menu_header("Reusable Presets")
        print("1. Roles")
        print("2. Responsibilities")
        print("3. Criterion Sets")
        print("4. Scoring Scales")
        print_navigation()
        print()
        raw = input("Select an option: ").strip()
        navigation = parse_menu_navigation(raw)
        if navigation is ConcordMenuChoice.HELP:
            _help()
        elif navigation is NavigationChoice.BACK:
            return
        elif raw in {"1", "2", "3", "4"}:
            _kind_menu(_PRESET_KINDS[int(raw) - 1], state)
        else:
            print(navigation_hint_with_help())
            pause_for_user()


__all__ = ["launch_preset_library_menu"]
