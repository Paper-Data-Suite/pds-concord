"""Side-effect-free guided Scoring Scale drafts for Concord teacher menus.

This is an input/presentation adapter, not a second Scale model or a write API.
The canonical ScoringScale constructor remains the final semantic validator.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation
from typing import Literal

from concord.models import Provenance, ScoringScale, ScoringScaleLevel
from concord.models.common import JsonScalar, scalar_key

ValueInputKind = Literal["integer", "decimal", "text", "category", "yes_no"]
ScaleStartingChoice = Literal[
    "proficiency", "number", "text", "category", "yes_no", "ordered", "advanced"
]

_INT = re.compile(r"[+-]?(?:0|[1-9][0-9]*)\Z")
_DECIMAL = re.compile(
    r"[+-]?(?:(?:0|[1-9][0-9]*)(?:\.[0-9]*)?|\.[0-9]+)"
    r"(?:[eE][+-]?[0-9]+)?\Z"
)
_MAX_NUMBER_LENGTH = 128


class GuidedScaleInputError(ValueError):
    """One teacher-entered typed value cannot be represented safely."""


@dataclass(frozen=True, slots=True)
class ParsedScaleValue:
    """One explicitly typed value, with any reviewed float approximation noted."""

    value: JsonScalar
    precision_notice: str | None = None


@dataclass(frozen=True, slots=True)
class GuidedScaleDraft:
    """In-memory proposed definition; neither a native nor a preset record."""

    scale_type: str
    levels: tuple[ScoringScaleLevel, ...]


def scale_type_for_choice(choice: ScaleStartingChoice) -> str:
    """Map menu-only choices to EXISTING canonical Scale types."""
    mapping = {
        "proficiency": "ordinal",
        "number": "numeric",
        "text": "teacher_defined",
        "category": "categorical",
        "yes_no": "binary",
        "ordered": "ordinal",
        "advanced": "teacher_defined",
    }
    try:
        return mapping[choice]
    except (KeyError, TypeError) as error:
        raise GuidedScaleInputError(
            f"Unsupported Scale starting choice: {choice!r}"
        ) from error


def four_level_proficiency() -> GuidedScaleDraft:
    """Four integer values, with editable explanatory examples (not grade rules)."""
    examples = (
        ("Developing", "The assessed skill is beginning to emerge."),
        ("Approaching", "The assessed skill is demonstrated in part."),
        ("Meeting", "The assessed skill is demonstrated for this task."),
        ("Exceeding", "The skill is demonstrated with additional depth."),
    )
    return GuidedScaleDraft(
        scale_type="ordinal",
        levels=tuple(
            ScoringScaleLevel(
                value=index,
                label=label,
                meaning=meaning,
                position=index,
            )
            for index, (label, meaning) in enumerate(examples, 1)
        ),
    )


def yes_no_scale() -> GuidedScaleDraft:
    """Two actual boolean values, with no inferred grade or pass threshold."""
    return GuidedScaleDraft(
        scale_type="binary",
        levels=(
            ScoringScaleLevel(
                value=False,
                label="No",
                meaning="The specified condition was not observed.",
            ),
            ScoringScaleLevel(
                value=True,
                label="Yes",
                meaning="The specified condition was observed.",
            ),
        ),
    )


def parse_typed_value(
    raw: str,
    kind: ValueInputKind,
    *,
    accept_float_approximation: bool = False,
) -> ParsedScaleValue:
    """Parse a teacher-selected type without JSON syntax or implicit coercion.

    Decimal literals that are not exactly representable as binary64 refuse by
    default. A later menu may *explicitly* ask approval before passing
    ``accept_float_approximation=True``; the returned notice is mandatory review
    text, not evidence of arbitrary-precision decimal storage.
    """
    if not isinstance(raw, str):
        raise GuidedScaleInputError("Enter a text value for the chosen type.")
    if kind in ("text", "category"):
        if not raw.strip():
            raise GuidedScaleInputError("A text/Category value cannot be blank.")
        if kind == "category" and raw != raw.strip():
            raise GuidedScaleInputError(
                "A Category code cannot start or end with whitespace."
            )
        return ParsedScaleValue(raw)
    if kind == "yes_no":
        value = raw.strip().casefold()
        if value in ("yes", "true"):
            return ParsedScaleValue(True)
        if value in ("no", "false"):
            return ParsedScaleValue(False)
        raise GuidedScaleInputError("Choose Yes or No; 0, 1 and text are not booleans.")
    if kind not in ("integer", "decimal"):
        raise GuidedScaleInputError(f"Unsupported value input type: {kind!r}")
    if len(raw) > _MAX_NUMBER_LENGTH:
        raise GuidedScaleInputError("The number is too long (maximum 128 characters).")
    if kind == "integer":
        if _INT.fullmatch(raw) is None:
            raise GuidedScaleInputError(
                "Enter a whole number, such as -2, 0, or 10; no commas."
            )
        value_int = int(raw)
        scalar_key(value_int)
        return ParsedScaleValue(value_int)
    if _DECIMAL.fullmatch(raw) is None:
        raise GuidedScaleInputError(
            "Enter a decimal number, such as -1.5, 0.25, or 1e2; no commas."
        )
    try:
        decimal = Decimal(raw)
        value_float = float(decimal)
    except (InvalidOperation, OverflowError, ValueError) as error:
        raise GuidedScaleInputError(
            "The decimal number is not representable."
        ) from error
    if not math.isfinite(value_float):
        raise GuidedScaleInputError("The number must be finite; Infinity is not valid.")
    if decimal != 0 and value_float == 0.0:
        raise GuidedScaleInputError("The decimal is too small and would become zero.")
    scalar_key(value_float)
    if Decimal.from_float(value_float) != decimal:
        approximate = repr(value_float)
        if not accept_float_approximation:
            raise GuidedScaleInputError(
                "This decimal cannot be represented exactly by a stored float. "
                f"Explicitly review and accept the approximate value {approximate} "
                "or enter an exactly representable number."
            )
        return ParsedScaleValue(
            value_float,
            "Approximate binary float explicitly accepted: "
            f"entered {raw!r}; stored {approximate} "
            f"(exact value {Decimal.from_float(value_float)}).",
        )
    return ParsedScaleValue(value_float)


def format_typed_value(value: JsonScalar) -> str:
    """Distinguish 1 / 1.0 / '1' / true in all review screens."""
    scalar_key(value)
    if type(value) is bool:
        return f"{'true' if value else 'false'} [boolean]"
    if type(value) is int:
        return f"{value} [integer]"
    if type(value) is float:
        return f"{repr(value)} [decimal/float]"
    return f"{json.dumps(value, ensure_ascii=False)} [text]"


def describe_draft(draft: GuidedScaleDraft) -> tuple[str, ...]:
    """Complete, read-only preview; canonical validity is checked separately."""
    lines: tuple[str, ...] = (f"Canonical Scale type: {draft.scale_type}",)
    for ordinal, level in enumerate(draft.levels, 1):
        position = "none" if level.position is None else str(level.position)
        lines += (
            f"{ordinal}. {format_typed_value(level.value)} | "
            f"Label: {level.label} | Ordinal position: {position}",
            f"   Meaning: {level.meaning}",
            "   Description: " + (level.description or "(none)"),
        )
    return lines + (
        "No Scores, Grades, evidence, student/Group records "
        "or publication will be created.",
    )


def validate_draft(
    draft: GuidedScaleDraft,
    *,
    name: str,
    created_provenance: Provenance,
    intended_use: str | None = None,
    aggregation_guidance: str | None = None,
) -> None:
    """Apply the actual native model's constraints without committing a record."""
    ScoringScale(
        scoring_scale_id="scale-preview",
        lineage_id="scale-preview-lineage",
        name=name,
        revision=1,
        scale_type=draft.scale_type,
        levels=draft.levels,
        status="active",
        created_provenance=created_provenance,
        intended_use=intended_use,
        aggregation_guidance=aggregation_guidance,
    )


def replace_level(
    draft: GuidedScaleDraft, index: int, level: ScoringScaleLevel
) -> GuidedScaleDraft:
    """Edit one selected draft level; preserve every untouched value exactly."""
    if not isinstance(level, ScoringScaleLevel):
        raise GuidedScaleInputError("Replacement must be a typed ScoringScaleLevel.")
    if not 0 <= index < len(draft.levels):
        raise GuidedScaleInputError("Selected level does not exist.")
    revised = list(draft.levels)
    revised[index] = level
    return replace(draft, levels=tuple(revised))


def move_level(
    draft: GuidedScaleDraft, source: int, target: int
) -> GuidedScaleDraft:
    """Explicitly reorder draft entries; renumber positions only for ordinal."""
    if not (0 <= source < len(draft.levels) and 0 <= target < len(draft.levels)):
        raise GuidedScaleInputError("Selected level position does not exist.")
    if source == target:
        return draft
    moved = list(draft.levels)
    moved.insert(target, moved.pop(source))
    if draft.scale_type == "ordinal":
        moved = [replace(level, position=i) for i, level in enumerate(moved, 1)]
    return replace(draft, levels=tuple(moved))


def remove_level(draft: GuidedScaleDraft, index: int) -> GuidedScaleDraft:
    """Propose a removal in memory; native validation will refuse invalid counts."""
    if not 0 <= index < len(draft.levels):
        raise GuidedScaleInputError("Selected level does not exist.")
    remaining = list(draft.levels)
    del remaining[index]
    if draft.scale_type == "ordinal":
        remaining = [replace(level, position=i) for i, level in enumerate(remaining, 1)]
    return replace(draft, levels=tuple(remaining))
