"""Concord-owned guided Scale draft editor; no durable writes.

This is intentionally independent of Core's shared terminal/navigation APIs and
of Concord's native/preset storage. Both controllers may use the same editor.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace

from concord.menu_prompts import (
    prompt_exact_text,
    prompt_positive_int,
    prompt_text,
    select_one,
    show_result,
)
from concord.models import ScoringScaleLevel
from concord.models.common import JsonScalar
from concord.scale_guidance import (
    GuidedScaleDraft,
    GuidedScaleInputError,
    ScaleStartingChoice,
    ValueInputKind,
    describe_draft,
    format_typed_value,
    four_level_proficiency,
    move_level,
    parse_typed_value,
    remove_level,
    replace_level,
    scale_type_for_choice,
    yes_no_scale,
)


@dataclass(frozen=True, slots=True)
class GuidedScaleMenuResult:
    draft: GuidedScaleDraft
    precision_notices: tuple[str, ...] = ()


_STARTERS: tuple[ScaleStartingChoice, ...] = (
    "proficiency", "number", "text", "yes_no", "category", "ordered", "advanced"
)
_STARTER_LABELS = (
    "Four-level proficiency — 1 Developing to 4 Exceeding",
    "Custom Number — integer or decimal values",
    "Custom Text — exact literal text, not JSON",
    "Yes–No — actual boolean values",
    "Category — exact text codes and teacher labels",
    "Ordered — custom values with ordinal positions",
    "Advanced — mixed exact value types",
)


def _value_kind(scale_type: str, previous: JsonScalar | None) -> ValueInputKind:
    if scale_type == "numeric":
        choices: tuple[ValueInputKind, ...] = ("integer", "decimal")
    elif scale_type == "categorical" and previous is None:
        return "category"
    elif scale_type == "binary" and previous is None:
        return "yes_no"
    elif scale_type == "teacher_defined" or scale_type == "ordinal":
        choices = ("integer", "decimal", "text", "yes_no")
    else:
        choices = ("integer", "decimal", "text", "yes_no", "category")
    initial = (
        "yes_no" if type(previous) is bool
        else "integer" if type(previous) is int
        else "decimal" if type(previous) is float
        else "category" if scale_type == "categorical"
        else "text" if type(previous) is str
        else None
    )
    return select_one(
        "Level Value Type", choices,
        tuple(
            f"{kind.replace('_', ' ').title()}"
            + (" (current)" if kind == initial else "")
            for kind in choices
        ),
        help_text="The chosen type is retained exactly. No JSON quotation is needed.",
    )


def _number_or_text(
    kind: ValueInputKind, previous: JsonScalar | None
) -> tuple[JsonScalar, str | None]:
    if kind == "yes_no":
        options = (False, True)
        choice = select_one(
            "Yes–No Value", options, ("No [boolean]", "Yes [boolean]"),
            help_text="These are actual boolean values; not text or numbers.",
        )
        return choice, None
    label = "Category code" if kind == "category" else "Exact value"
    default = None
    if previous is not None:
        # Only default an existing value when its type actually matches.
        if (kind == "integer" and type(previous) is int) or (
            kind == "decimal" and type(previous) is float
        ) or (kind in ("text", "category") and type(previous) is str):
            default = str(previous)
    raw: str | None
    while True:
        if kind in ("text", "category") and default is None:
            raw = prompt_exact_text(
                "Scale Level Value", label,
                help_text=(
                    "Enter literal text; no JSON quotes. B cancels safely."
                ),
            )
        else:
            raw = prompt_text(
                "Scale Level Value", label,
                help_text=(
                    "Type a value directly, without JSON quotes; B cancels."
                ),
                default=default,
            )
        assert raw is not None
        try:
            parsed = parse_typed_value(raw, kind)
            return parsed.value, parsed.precision_notice
        except GuidedScaleInputError as error:
            message = str(error)
            if kind == "decimal" and message.startswith(
                "This decimal cannot be represented exactly"
            ):
                choice = select_one(
                    "Decimal Precision Review", (False, True),
                    (
                        "Re-enter an exactly representable number",
                        "Accept stored float approximation",
                    ),
                    help_text=message,
                )
                if choice:
                    accepted = parse_typed_value(
                        raw, "decimal", accept_float_approximation=True
                    )
                    return accepted.value, accepted.precision_notice
            show_result("Invalid Scale Value", (message, "No Scale was written."))
            default = None


def _edit_optional_description(previous: str | None) -> str | None:
    if previous is None:
        return prompt_text(
            "Scale Level", "Optional description", optional=True,
            help_text="Extra teacher-facing explanation; blank omits it.",
        )
    action = select_one(
        "Scale Level Description", ("keep", "change", "clear"),
        ("Keep existing description", "Change description", "Clear description"),
        help_text="Historical versions retain the old description.",
    )
    if action == "keep":
        return previous
    if action == "clear":
        return None
    return prompt_text(
        "Scale Level", "Replacement description", optional=True,
        help_text="Blank removes the optional description.",
    )


def _edit_one_level(
    scale_type: str, previous: ScoringScaleLevel | None, position: int,
    *, preferred_kind: ValueInputKind | None = None,
) -> tuple[ScoringScaleLevel, str | None]:
    value: JsonScalar
    notice: str | None = None
    if previous is not None:
        selected = select_one(
            "Edit Scale Level Value", ("keep", "replace"),
            (
                f"Keep exact {format_typed_value(previous.value)}",
                "Change exact value/type",
            ),
            help_text="Keeping a value never converts its type.",
        )
        if selected == "keep":
            value = previous.value
        else:
            kind = _value_kind(scale_type, previous.value)
            value, notice = _number_or_text(kind, previous.value)
    else:
        kind = preferred_kind or _value_kind(scale_type, None)
        value, notice = _number_or_text(kind, None)
    label = prompt_text(
        "Scale Level", "Teacher-facing label",
        help_text="This label describes the selected exact value.",
        default=previous.label if previous is not None else None,
    )
    meaning = prompt_text(
        "Scale Level", "Meaning",
        help_text="Explain the level without inventing a grade or threshold.",
        default=previous.meaning if previous is not None else None,
    )
    assert label is not None and meaning is not None
    description = _edit_optional_description(
        previous.description if previous is not None else None
    )
    return (
        ScoringScaleLevel(
            value=value, label=label, meaning=meaning,
            position=(
                position if scale_type == "ordinal"
                else previous.position if previous is not None else None
            ),
            description=description,
        ),
        notice,
    )


def _fresh_draft(choice: ScaleStartingChoice) -> GuidedScaleMenuResult:
    if choice == "proficiency":
        return GuidedScaleMenuResult(four_level_proficiency())
    if choice == "yes_no":
        return GuidedScaleMenuResult(yes_no_scale())
    scale_type = scale_type_for_choice(choice)
    count = prompt_positive_int(
        "Custom Scoring Scale", "Number of levels",
        help_text="Choose how many distinct values the Scale contains.", default=4,
    )
    if count > 50:
        raise GuidedScaleInputError("Guided Scales support at most 50 levels.")
    levels: list[ScoringScaleLevel] = []
    notices: list[str] = []
    for index in range(count):
        preferred: ValueInputKind | None = (
            "text" if choice == "text" else "category" if choice == "category" else None
        )
        item, notice = _edit_one_level(
            scale_type, None, index + 1, preferred_kind=preferred
        )
        levels.append(item)
        if notice is not None:
            notices.append(notice)
    return GuidedScaleMenuResult(
        GuidedScaleDraft(scale_type, tuple(levels)), tuple(notices)
    )


def _show(draft: GuidedScaleDraft, notices: tuple[str, ...]) -> None:
    show_result(
        "Review Exact Scale Draft",
        (*describe_draft(draft), *notices, "No durable changes before approval."),
    )


def _edit_draft(
    result: GuidedScaleMenuResult,
    validator: Callable[[GuidedScaleDraft], None] | None,
) -> GuidedScaleMenuResult:
    draft = result.draft
    notices = list(result.precision_notices)
    while True:
        _show(draft, tuple(notices))
        action = select_one(
            "Edit Scale Draft",
            ("done", "edit", "add", "move", "remove"),
            ("Use this draft", "Edit one level", "Add a level", "Move a level",
             "Remove a level"),
            help_text=(
                "Changes are in memory. Final validation and approval follow."
            ),
        )
        if action == "done":
            if validator is not None:
                try:
                    validator(draft)
                except ValueError as error:
                    show_result(
                        "Scale Definition Needs Correction",
                        (str(error), "No Scale was written. Edit the draft to retry."),
                    )
                    continue
            return GuidedScaleMenuResult(draft, tuple(notices))
        if action == "add":
            notices.clear()
            if len(draft.levels) >= 50:
                show_result("Scale Editor", ("Maximum 50 levels.",))
                continue
            item, notice = _edit_one_level(
                draft.scale_type, None, len(draft.levels) + 1
            )
            if draft.scale_type != "ordinal" and draft.levels and all(
                level.position is not None for level in draft.levels
            ):
                positions = [level.position for level in draft.levels]
                next_position = max(
                    pos for pos in positions if pos is not None
                ) + 1
                item = replace(item, position=next_position)
            draft = GuidedScaleDraft(draft.scale_type, (*draft.levels, item))
            if notice:
                notices.append(notice)
            continue
        if action == "edit":
            notices.clear()
            index = _choose_level(draft)
            item, notice = _edit_one_level(
                draft.scale_type, draft.levels[index], index + 1
            )
            draft = replace_level(draft, index, item)
            if notice:
                notices.append(notice)
            continue
        if action == "remove":
            notices.clear()
            draft = remove_level(draft, _choose_level(draft))
            continue
        source = _choose_level(draft)
        destination = _choose_level(draft)
        draft = move_level(draft, source, destination)


def _choose_level(draft: GuidedScaleDraft) -> int:
    indexes = tuple(range(len(draft.levels)))
    return select_one(
        "Choose Scale Level", indexes,
        tuple(
            f"{i + 1}. {level.label} — {format_typed_value(level.value)}"
            for i, level in enumerate(draft.levels)
        ),
        help_text="Select the exact level to change. Historical records are unchanged.",
    )


def guide_scale_levels(
    *,
    title: str,
    existing: GuidedScaleDraft | None = None,
    validator: Callable[[GuidedScaleDraft], None] | None = None,
) -> GuidedScaleMenuResult:
    """Build/revise a complete in-memory draft; caller validates and writes."""
    if existing is not None:
        _show(existing, ())
        action = select_one(
            title, ("keep", "edit", "restart"),
            (
                "Keep all existing exact levels and types",
                "Edit selected existing levels",
             "Choose a completely new starting point"),
            help_text="Replacing the starting point does not alter the prior revision.",
        )
        if action == "keep":
            if validator is not None:
                validator(existing)
            return GuidedScaleMenuResult(existing)
        if action == "edit":
            return _edit_draft(GuidedScaleMenuResult(existing), validator)
    choice = select_one(
        title, _STARTERS, _STARTER_LABELS,
        help_text=(
            "Choose a starter; all values are previewed before saving."
        ),
    )
    return _edit_draft(_fresh_draft(choice), validator)


def draft_from_existing(
    scale_type: str, levels: tuple[ScoringScaleLevel, ...]
) -> GuidedScaleDraft:
    """Exactly retain historical types/values/positions; no normalization."""
    return GuidedScaleDraft(scale_type=scale_type, levels=levels)
