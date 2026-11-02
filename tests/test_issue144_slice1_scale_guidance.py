"""Issue #144 Slice 1: pure Scale drafting; no menu or workspace side effects."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

import pytest

from concord.models import ConcordModelError, ScoringScaleLevel
from concord.scale_guidance import (
    GuidedScaleDraft,
    GuidedScaleInputError,
    describe_draft,
    format_typed_value,
    four_level_proficiency,
    move_level,
    parse_typed_value,
    remove_level,
    replace_level,
    scale_type_for_choice,
    validate_draft,
    yes_no_scale,
)
from concord.workflows import WorkflowActor
from concord.workflows.context import provenance


def _created():
    return provenance(
        WorkflowActor(actor_id="synthetic-teacher"),
        clock=lambda: datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc),
    )


def _validate(draft: GuidedScaleDraft) -> None:
    validate_draft(
        draft,
        name="Synthetic practice Scale",
        created_provenance=_created(),
    )


def test_proficiency_has_four_exact_numeric_levels_and_meanings() -> None:
    draft = four_level_proficiency()
    assert draft.scale_type == "ordinal"
    assert [type(level.value) for level in draft.levels] == [int] * 4
    assert [level.value for level in draft.levels] == [1, 2, 3, 4]
    assert [level.position for level in draft.levels] == [1, 2, 3, 4]
    assert [level.label for level in draft.levels] == [
        "Developing", "Approaching", "Meeting", "Exceeding"
    ]
    assert all(level.meaning and level.description is None for level in draft.levels)
    _validate(draft)
    preview = describe_draft(draft)
    assert "1 [integer]" in "\n".join(preview)
    assert "No Scores, Grades" in preview[-1]
    assert all("threshold" not in line.casefold() for line in preview)


def test_yes_no_starter_retains_real_booleans_and_exactly_two_levels() -> None:
    draft = yes_no_scale()
    assert draft.scale_type == "binary"
    assert tuple(type(level.value) for level in draft.levels) == (bool, bool)
    assert tuple(level.value for level in draft.levels) == (False, True)
    assert tuple(level.position for level in draft.levels) == (None, None)
    _validate(draft)
    assert "false [boolean]" in "\n".join(describe_draft(draft))


@pytest.mark.parametrize(
    ("choice", "canonical"),
    [
        ("proficiency", "ordinal"), ("number", "numeric"),
        ("text", "teacher_defined"), ("category", "categorical"),
        ("yes_no", "binary"), ("ordered", "ordinal"),
        ("advanced", "teacher_defined"),
    ],
)
def test_menu_only_choices_map_to_existing_enum(choice, canonical: str) -> None:
    assert scale_type_for_choice(choice) == canonical


def test_bad_choice_refuses_without_guessing() -> None:
    with pytest.raises(GuidedScaleInputError, match="Unsupported"):
        scale_type_for_choice("percentage")


@pytest.mark.parametrize("raw,expected", [("-9", -9), ("0", 0), ("+3", 3)])
def test_whole_number_input_is_exact_integer(raw: str, expected: int) -> None:
    result = parse_typed_value(raw, "integer")
    assert result.value == expected and type(result.value) is int
    assert result.precision_notice is None


@pytest.mark.parametrize(
    "raw,expected",
    [("-1.5", -1.5), ("0.25", 0.25), ("1", 1.0), ("1e2", 100.0)],
)
def test_exact_binary64_decimal_input_retains_explicit_float(raw, expected) -> None:
    result = parse_typed_value(raw, "decimal")
    assert type(result.value) is float
    assert result.value == expected
    assert result.precision_notice is None


def test_nonrepresentable_fraction_requires_explicit_approximation_review() -> None:
    with pytest.raises(GuidedScaleInputError, match="cannot be represented exactly"):
        parse_typed_value("0.1", "decimal")
    result = parse_typed_value(
        "0.1", "decimal", accept_float_approximation=True
    )
    assert type(result.value) is float and result.value == 0.1
    assert result.precision_notice is not None
    assert "entered '0.1'" in result.precision_notice
    assert "exact value" in result.precision_notice


@pytest.mark.parametrize(
    "kind,raw",
    [
        ("integer", ""), ("integer", "1.0"), ("integer", "01"),
        ("integer", "1,000"), ("integer", "1" * 129),
        ("decimal", "NaN"), ("decimal", "Infinity"),
        ("decimal", "1e999999"), ("decimal", "1e-999999"),
        ("decimal", "1,25"), ("decimal", "01.3"),
        ("yes_no", "1"), ("yes_no", "maybe"),
        ("text", ""), ("category", "  code  "),
    ],
)
def test_invalid_input_refuses_with_no_implicit_coercion(kind, raw) -> None:
    with pytest.raises(GuidedScaleInputError):
        parse_typed_value(raw, kind)


def test_ambiguous_looking_text_and_unicode_remain_literal_strings() -> None:
    for raw in ("1", "01", "true", "needs_revision", "Jíbara", "  padded  "):
        result = parse_typed_value(raw, "text")
        assert type(result.value) is str
        assert result.value == raw
    assert parse_typed_value("needs_revision", "category").value == "needs_revision"


@pytest.mark.parametrize("raw,expected", [("Yes", True), ("true", True), ("NO", False)])
def test_explicit_yes_no_channel_never_uses_integer(raw, expected: bool) -> None:
    result = parse_typed_value(raw, "yes_no")
    assert type(result.value) is bool and result.value is expected


def test_type_review_disambiguates_four_different_values() -> None:
    assert format_typed_value(1) == "1 [integer]"
    assert format_typed_value(1.0) == "1.0 [decimal/float]"
    assert format_typed_value("1") == '"1" [text]'
    assert format_typed_value(True) == "true [boolean]"
    assert format_typed_value("Jíbara") == '"Jíbara" [text]'


def test_replace_one_level_preserves_all_untouched_levels_and_metadata() -> None:
    original = four_level_proficiency()
    prior = original.levels[2]
    changed = replace_level(
        original,
        2,
        replace(prior, meaning="Exact revised meaning", description="Optional note"),
    )
    assert original != changed
    assert original.levels[2] is prior
    assert changed.levels[:2] == original.levels[:2]
    assert changed.levels[3] is original.levels[3]
    assert changed.levels[2].meaning == "Exact revised meaning"
    assert changed.levels[2].description == "Optional note"
    _validate(changed)
    assert "Optional note" in "\n".join(describe_draft(changed))


def test_explicit_ordinal_move_changes_only_sequence_and_positions() -> None:
    original = four_level_proficiency()
    moved = move_level(original, 3, 0)
    assert [level.value for level in moved.levels] == [4, 1, 2, 3]
    assert [level.position for level in moved.levels] == [1, 2, 3, 4]
    assert [level.value for level in original.levels] == [1, 2, 3, 4]
    _validate(moved)
    assert move_level(original, 1, 1) is original


def test_remove_is_draft_only_and_native_validation_refuses_invalid_binary() -> None:
    original = yes_no_scale()
    removed = remove_level(original, 0)
    assert len(original.levels) == 2 and len(removed.levels) == 1
    with pytest.raises(ConcordModelError, match="exactly two"):
        _validate(removed)


def test_native_validator_rejects_type_mismatch_and_typed_duplicates() -> None:
    number = GuidedScaleDraft(
        scale_type="numeric",
        levels=(
            ScoringScaleLevel(value=1, label="One", meaning="Integer value"),
            ScoringScaleLevel(value=2, label="Two", meaning="Integer value"),
        ),
    )
    _validate(number)
    wrong = replace_level(
        number, 0, ScoringScaleLevel(value=True, label="Yes", meaning="Bool")
    )
    with pytest.raises(ConcordModelError, match="numeric"):
        _validate(wrong)
    duplicate = replace_level(number, 1, number.levels[0])
    with pytest.raises(ConcordModelError, match="type-sensitively unique"):
        _validate(duplicate)
    mixed = GuidedScaleDraft(
        scale_type="teacher_defined",
        levels=tuple(
            ScoringScaleLevel(value=value, label=str(i), meaning="Typed")
            for i, value in enumerate((1, 1.0, "1", True), 1)
        ),
    )
    _validate(mixed)


def test_invalid_level_selection_does_not_edit_draft() -> None:
    draft = four_level_proficiency()
    with pytest.raises(GuidedScaleInputError):
        replace_level(draft, 9, draft.levels[0])
    with pytest.raises(GuidedScaleInputError):
        move_level(draft, -1, 0)
    with pytest.raises(GuidedScaleInputError):
        remove_level(draft, 8)
    assert [level.value for level in draft.levels] == [1, 2, 3, 4]
