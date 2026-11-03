"""Teacher-facing, in-memory Criterion Set editor for Concord assessment setup.

This menu owns presentation only; it never writes native records or presets.
The existing Criterion Set workflow remains the mutation authority.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

from pds_core.standards import StandardsLibrary, find_standards_profile

from concord.criterion_guidance import (
    TARGET_CHOICES,
    CriterionDraft,
    CriterionSetDraft,
    FocusStandardChoice,
    add_criterion,
    describe_draft,
    focus_standard_choices,
    move_criterion,
    remove_criterion,
    replace_criterion,
)
from concord.menu_prompts import prompt_text, select_many, select_one, slug_identifier
from concord.menu_ui import clear_screen, pause_for_user, print_menu_header

_KIND_LABELS = {
    "standard_backed": "Linked to a Focus Standard",
    "local": "Local classroom judgment (no governing Standard)",
}
_SCOPE_CHOICES = ("activity_specific", "reusable")


def _kind_choices(orientation: str) -> tuple[str, ...]:
    if orientation == "mixed":
        return ("standard_backed", "local")
    if orientation == "standards_based":
        return ("standard_backed",)
    if orientation == "local_criteria_only":
        return ("local",)
    raise ValueError(
        "This Activity cannot receive a scored Criterion Set "
        "in its current orientation."
    )


def _one_criterion(
    *,
    orientation: str,
    focus_choices: tuple[FocusStandardChoice, ...],
    library: StandardsLibrary | None,
    profile_id: str | None,
    choose_scale: Callable[[], str | None],
    previous: CriterionDraft | None = None,
) -> CriterionDraft:
    label = prompt_text(
        "Rubric Criterion",
        "What are you assessing? (Criterion name)",
        help_text="Name a judgment, for example Individual discussion participation.",
        default=previous.label if previous else None,
    )
    definition = prompt_text(
        "Rubric Criterion",
        "Describe the evidence or judgment",
        help_text="Explain what a teacher will actually evaluate.",
        default=previous.definition if previous else None,
    )
    assert label is not None and definition is not None
    permitted = _kind_choices(orientation)
    if previous is not None and previous.criterion_kind not in permitted:
        raise ValueError("Previously selected Criterion type is unavailable here.")
    kind = (
        permitted[0] if len(permitted) == 1 else select_one(
            "How is this Criterion assessed?",
            permitted,
            tuple(_KIND_LABELS[item] for item in permitted),
            help_text="A standard-backed Criterion governs an Activity Focus Standard; "
            "a local Criterion has no governing Standard.",
        )
    )
    standard_id: str | None = None
    if kind == "standard_backed":
        if not focus_choices:
            raise ValueError(
                "No active Core Focus Standards are available for this Activity."
            )
        selection = select_one(
            "Select governing Focus Standard",
            focus_choices,
            tuple(item.label for item in focus_choices),
            help_text=("Only the exact governing Standard selected for "
                       "this Activity may be used."),
        )
        standard_id = selection.standard_id
    targets = (
        previous.supported_target_kinds
        if previous is not None and select_one(
            "Criterion targets",
            (True, False),
            ("Keep current target kinds", "Change target kinds"),
            help_text="The target permission is not an actual Score recipient.",
        ) else select_many(
            "Who or what can receive this Criterion?",
            tuple(item.value for item in TARGET_CHOICES),
            tuple(f"{item.label} — {item.explanation}" for item in TARGET_CHOICES),
            help_text=("Select allowed targets. A Group judgment "
                       "is never an individual Score."),
        )
    )
    alignments = previous.alignment_standard_ids if previous is not None else ()
    if library is not None and profile_id is not None:
        add_alignments = select_one(
            "Additional alignment Standards",
            (False, True),
            ("Keep current alignments (or none)", "Choose alignment Standards"),
            help_text="Alignments are not governing Standards and do not change Focus.",
        )
        if add_alignments:
            profile = find_standards_profile(library, profile_id)
            if profile is None:
                raise ValueError("Core Standards profile is unavailable.")
            by_id = {item.standard_id: item for item in library.standards}
            allowed = tuple(
                by_id[item] for item in profile.standards
                if item in by_id and by_id[item].active
                and "deprecated" not in by_id[item].tags
            )
            if not allowed:
                raise ValueError(
                    "No active profile Standards are available for alignment."
                )
            alignments = select_many(
                "Select alignment Standards",
                tuple(item.standard_id for item in allowed),
                tuple(f"{item.code} — {item.short_name}" for item in allowed),
                help_text=("Alignments do not imply proficiency "
                           "or change a governing Standard."),
            )
    scale_id = (
        previous.default_scoring_scale_id
        if previous is not None and select_one(
            "Default Scoring Scale",
            (True, False),
            ("Keep existing Scale choice", "Choose a different Scale"),
            help_text="No Score or grade is created from a default Scale.",
        ) else choose_scale()
    )
    return CriterionDraft(
        key=(previous.key if previous is not None
             else slug_identifier(label, "criterion")),
        label=label,
        definition=definition,
        criterion_kind=kind,
        supported_target_kinds=targets,
        standard_id=standard_id,
        alignment_standard_ids=alignments,
        default_scoring_scale_id=scale_id,
        status=previous.status if previous is not None else "active",
    )


def guide_native_criterion_set(
    *,
    orientation: str,
    standards_library: StandardsLibrary | None,
    standards_profile_id: str | None,
    focus_standard_ids: tuple[str, ...],
    choose_scale: Callable[[], str | None],
    existing: CriterionSetDraft | None = None,
) -> tuple[CriterionSetDraft, tuple[FocusStandardChoice, ...]]:
    """Edit a Criterion Set solely in memory; caller still validates and approves.

    `B` in any field unwinds the in-memory draft with no persistence.
    """
    kinds = _kind_choices(orientation)
    choices: tuple[FocusStandardChoice, ...] = ()
    if "standard_backed" in kinds and focus_standard_ids:
        if standards_library is None or standards_profile_id is None:
            raise ValueError("Canonical Core Standards context is unavailable.")
        choices = focus_standard_choices(
            standards_library, standards_profile_id, focus_standard_ids
        )
    title = "Revise a rubric" if existing is not None else "Create a rubric"
    name = prompt_text(
        title,
        "Assessment/rubric name",
        help_text="Name this Activity-owned rubric definition.",
        default=existing.name if existing is not None else None,
    )
    purpose = prompt_text(
        title,
        "Purpose",
        help_text="Explain what the complete rubric is intended to assess.",
        default=existing.purpose if existing is not None else None,
    )
    assert name is not None and purpose is not None
    scope = select_one(
        "Rubric scope",
        _SCOPE_CHOICES,
        ("Specific to this Activity", "Reusable intent (still Activity-owned)"),
        help_text="Reusable intent does not save a workspace-level preset. "
        "Saving for another class is a separate reviewed action.",
    )
    draft = CriterionSetDraft(
        name=name,
        purpose=purpose,
        criterion_set_kind=(
            existing.criterion_set_kind if existing is not None else kinds[0]
        ),
        criteria=existing.criteria if existing is not None else (),
        scope=scope,
    )
    while True:
        clear_screen()
        print_menu_header("Draft Rubric — no changes saved")
        for line in describe_draft(draft, focus_choices=choices):
            print(line)
        print()
        action = select_one(
            "Edit draft rubric",
            ("add", "edit", "move", "remove", "review"),
            (
                "Add a Criterion",
                "Edit a Criterion",
                "Move/reorder Criteria",
                "Remove a Criterion",
                "Finish and review (no write yet)",
            ),
            help_text=("These changes exist only in memory "
                       "until an explicit final CREATE."),
        )
        if action == "review":
            if not draft.criteria:
                print_menu_header("A rubric requires at least one Criterion")
                pause_for_user()
                continue
            # Mixed sets may contain one or both kinds; retain canonical mixture.
            kinds_present = {item.criterion_kind for item in draft.criteria}
            set_kind = (
                "mixed" if len(kinds_present) == 2
                else next(iter(kinds_present))
            )
            # Unmodified Criterion membership does not silently alter a
            # historical Set-kind declaration, even if only metadata changed.
            if existing is not None and draft.criteria == existing.criteria:
                if draft == existing:
                    return existing, choices
                return replace(
                    draft, criterion_set_kind=existing.criterion_set_kind
                ), choices
            return replace(draft, criterion_set_kind=set_kind), choices
        if action == "add":
            draft = add_criterion(
                draft,
                _one_criterion(
                    orientation=orientation, focus_choices=choices,
                    library=standards_library, profile_id=standards_profile_id,
                    choose_scale=choose_scale,
                ),
            )
            continue
        if not draft.criteria:
            print_menu_header("No Criteria to edit")
            pause_for_user()
            continue
        index = select_one(
            "Choose draft Criterion",
            tuple(range(len(draft.criteria))),
            tuple(f"{i + 1}. {item.label}" for i, item in enumerate(draft.criteria)),
            help_text="Choose a Criterion already in this unsaved draft.",
        )
        if action == "edit":
            draft = replace_criterion(
                draft, index,
                _one_criterion(
                    orientation=orientation, focus_choices=choices,
                    library=standards_library, profile_id=standards_profile_id,
                    choose_scale=choose_scale, previous=draft.criteria[index],
                ),
            )
        elif action == "remove":
            draft = remove_criterion(draft, index)
        else:
            destination = select_one(
                "Move Criterion to position",
                tuple(range(len(draft.criteria))),
                tuple(str(i + 1) for i in range(len(draft.criteria))),
                help_text="Reordering changes only the unsaved draft sequence.",
            )
            draft = move_criterion(draft, index, destination)
