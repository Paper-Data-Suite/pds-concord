"""#144 Slice 3: guided saved Scoring Scale presets and typed history."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

import concord.menu_presets as presets
from concord.menu_context import CancelMenuAction, MenuSessionContext
from concord.menu_scale_guidance import GuidedScaleMenuResult
from concord.models import ScoringScaleLevel
from concord.scale_guidance import (
    GuidedScaleDraft,
    four_level_proficiency,
    yes_no_scale,
)
from concord.workflows import WorkflowActor


def _state() -> MenuSessionContext:
    return MenuSessionContext(actor=WorkflowActor(actor_id="teacher-synthetic"))


def _preset() -> SimpleNamespace:
    return SimpleNamespace(
        preset_id="scale-preset-1", revision=2,
        name="Existing Scale", scale_type="teacher_defined",
        levels=(
            ScoringScaleLevel(value=1, label="Integer", meaning="Integer meaning"),
            ScoringScaleLevel(value=1.0, label="Decimal", meaning="Float meaning"),
            ScoringScaleLevel(value="1", label="Text", meaning="Text meaning"),
            ScoringScaleLevel(value=True, label="Yes", meaning="Boolean meaning"),
        ),
        intended_use="Discussion", aggregation_guidance="No aggregation",
    )


def _stub_existing(
    monkeypatch: pytest.MonkeyPatch, current: SimpleNamespace,
) -> list[tuple[str, tuple[str, ...]]]:
    # Model type guard remains in production; this fixture is just a read-only
    # stand-in for the known immutable saved revision.
    monkeypatch.setattr(presets, "ScoringScalePresetRevision", SimpleNamespace)
    monkeypatch.setattr(presets, "get_preset", lambda *_args: current)
    monkeypatch.setattr(presets, "_successor_id", lambda *_args: "scale-preset-1-v3")
    receipts: list[tuple[str, tuple[str, ...]]] = []
    monkeypatch.setattr(
        presets, "show_result",
        lambda title, lines: receipts.append((title, tuple(lines))),
    )
    return receipts


def test_preset_create_reviews_four_integer_levels_before_one_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        presets, "_preset_identity", lambda *_args: (
            "Four-level discussion", "scale-preset-1", "scale-preset-1-v1"
        ),
    )
    monkeypatch.setattr(presets, "_optional_text", lambda *_args: None)
    monkeypatch.setattr(
        presets, "guide_scale_levels",
        lambda **_kwargs: GuidedScaleMenuResult(four_level_proficiency()),
    )
    calls: list[str] = []
    receipts: list[tuple[str, ...]] = []

    def confirm(_title: str, verb: str, lines: tuple[str, ...]) -> bool:
        assert verb == "CREATE"
        assert any("1 [integer]" in line for line in lines)
        assert any("4 [integer]" in line for line in lines)
        assert any("scale-preset-1-v1" in line for line in lines)
        assert any("No Scores" in line for line in lines)
        assert any("no Activity Scale" in line for line in lines)
        calls.append("review")
        return True

    def write(request: Any) -> SimpleNamespace:
        assert calls == ["review"]
        calls.append("write")
        assert request.preset_id == "scale-preset-1"
        assert request.preset_revision_id == "scale-preset-1-v1"
        assert request.scale_type == "ordinal"
        assert [
            (type(item.value), item.value, item.position)
            for item in request.levels
        ] == [(int, 1, 1), (int, 2, 2), (int, 3, 3), (int, 4, 4)]
        return SimpleNamespace(preset_id=request.preset_id)

    monkeypatch.setattr(presets, "confirm_write", confirm)
    monkeypatch.setattr(presets, "create_scoring_scale_preset", write)
    monkeypatch.setattr(
        presets, "show_result", lambda _title, lines: receipts.append(tuple(lines)),
    )
    presets._create_scale(_state())
    assert calls == ["review", "write"]
    assert len(receipts) == 1
    assert "scale-preset-1-v1" in " ".join(receipts[0])


def test_preset_create_yes_no_saves_real_booleans(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        presets, "_preset_identity",
        lambda *_args: ("Yes No", "bool-preset", "bool-v1"),
    )
    monkeypatch.setattr(presets, "_optional_text", lambda *_args: None)
    monkeypatch.setattr(
        presets, "guide_scale_levels",
        lambda **_kwargs: GuidedScaleMenuResult(yes_no_scale()),
    )
    monkeypatch.setattr(presets, "confirm_write", lambda *_args: True)
    monkeypatch.setattr(presets, "show_result", lambda *_args: None)
    observed: list[Any] = []

    def save(request: Any) -> SimpleNamespace:
        observed.append(request)
        return SimpleNamespace(preset_id=request.preset_id)

    monkeypatch.setattr(presets, "create_scoring_scale_preset", save)
    presets._create_scale(_state())
    assert len(observed) == 1
    assert observed[0].scale_type == "binary"
    assert [(type(level.value), level.value) for level in observed[0].levels] == [
        (bool, False), (bool, True)
    ]


def test_preset_create_cancel_before_approval_never_writes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        presets, "_preset_identity", lambda *_args: ("Scale", "scale", "scale-v1"),
    )
    monkeypatch.setattr(presets, "_optional_text", lambda *_args: None)
    monkeypatch.setattr(
        presets, "guide_scale_levels",
        lambda **_kwargs: GuidedScaleMenuResult(four_level_proficiency()),
    )
    monkeypatch.setattr(presets, "confirm_write", lambda *_args: False)
    monkeypatch.setattr(
        presets, "create_scoring_scale_preset",
        lambda *_args: pytest.fail("Canceled creation must not write"),
    )
    monkeypatch.setattr(
        presets, "show_result",
        lambda *_args: pytest.fail("Canceled creation must not show success"),
    )
    presets._create_scale(_state())


def test_preset_guidance_back_does_not_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        presets, "_preset_identity", lambda *_args: ("Scale", "scale", "scale-v1"),
    )

    def cancel(**_kwargs: Any) -> GuidedScaleMenuResult:
        raise CancelMenuAction

    monkeypatch.setattr(presets, "guide_scale_levels", cancel)
    monkeypatch.setattr(
        presets, "create_scoring_scale_preset",
        lambda *_args: pytest.fail("Canceled guidance must not write"),
    )
    with pytest.raises(CancelMenuAction):
        presets._create_scale(_state())


def test_preset_revision_preserves_exact_types_metadata_and_revision_guard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current = _preset()
    receipts = _stub_existing(monkeypatch, current)
    monkeypatch.setattr(presets, "prompt_text", lambda *_args, **_kw: "Revised Scale")
    monkeypatch.setattr(
        presets, "_edit_optional_preset_scale_field",
        lambda _title, _label, previous: previous,
    )
    incoming: list[GuidedScaleDraft] = []

    def guide(**kwargs: Any) -> GuidedScaleMenuResult:
        incoming.append(kwargs["existing"])
        return GuidedScaleMenuResult(kwargs["existing"])

    monkeypatch.setattr(presets, "guide_scale_levels", guide)
    calls: list[str] = []

    def confirm(_title: str, verb: str, lines: tuple[str, ...]) -> bool:
        assert verb == "REVISE"
        assert any("1 [integer]" in line for line in lines)
        assert any("1.0 [decimal/float]" in line for line in lines)
        assert any('"1" [text]' in line for line in lines)
        assert any("true [boolean]" in line for line in lines)
        assert any("scale-preset-1-v3" in line for line in lines)
        calls.append("review")
        return True

    def save(request: Any) -> None:
        assert calls == ["review"]
        calls.append("write")
        assert request.preset_id == current.preset_id
        assert request.preset_revision_id == "scale-preset-1-v3"
        assert request.expected_revision == current.revision
        assert request.intended_use == current.intended_use
        assert request.aggregation_guidance == current.aggregation_guidance
        assert request.levels is current.levels

    monkeypatch.setattr(presets, "confirm_write", confirm)
    monkeypatch.setattr(presets, "revise_scoring_scale_preset", save)
    presets._edit_scale(SimpleNamespace(preset_id=current.preset_id), _state())
    assert len(incoming) == 1
    assert incoming[0].levels is current.levels
    assert [type(item.value) for item in incoming[0].levels] == [
        int, float, str, bool
    ]
    assert calls == ["review", "write"]
    assert [name for name, _lines in receipts] == ["Scoring Scale Preset Revised"]


def test_preset_revision_canceled_confirmation_never_writes_or_claims_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current = _preset()
    receipts = _stub_existing(monkeypatch, current)
    monkeypatch.setattr(presets, "prompt_text", lambda *_args, **_kw: "Revised Scale")
    monkeypatch.setattr(
        presets, "guide_scale_levels",
        lambda **kwargs: GuidedScaleMenuResult(kwargs["existing"]),
    )
    monkeypatch.setattr(
        presets, "_edit_optional_preset_scale_field",
        lambda _title, _label, previous: previous,
    )
    monkeypatch.setattr(presets, "confirm_write", lambda *_args: False)
    monkeypatch.setattr(
        presets, "revise_scoring_scale_preset",
        lambda *_args: pytest.fail("Canceled revision must not write"),
    )
    presets._edit_scale(SimpleNamespace(preset_id=current.preset_id), _state())
    assert receipts == []


def test_preset_revision_noop_is_read_only_even_for_type_sensitive_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current = _preset()
    receipts = _stub_existing(monkeypatch, current)
    monkeypatch.setattr(presets, "prompt_text", lambda *_args, **_kw: current.name)
    monkeypatch.setattr(
        presets, "guide_scale_levels",
        lambda **kwargs: GuidedScaleMenuResult(kwargs["existing"]),
    )
    monkeypatch.setattr(
        presets, "_edit_optional_preset_scale_field",
        lambda _title, _label, previous: previous,
    )
    monkeypatch.setattr(
        presets, "revise_scoring_scale_preset",
        lambda *_args: pytest.fail("Unchanged Scale must not write"),
    )
    monkeypatch.setattr(
        presets, "confirm_write", lambda *_args: pytest.fail("No-op must not confirm"),
    )
    presets._edit_scale(SimpleNamespace(preset_id=current.preset_id), _state())
    assert [name for name, _lines in receipts] == ["Scoring Scale Preset Unchanged"]


def test_noop_comparison_distinguishes_int_float_and_boolean() -> None:
    old = (ScoringScaleLevel(value=1, label="One", meaning="Evidence"),)
    assert presets._same_exact_scale_levels(old, old)
    assert not presets._same_exact_scale_levels(
        old, (ScoringScaleLevel(value=1.0, label="One", meaning="Evidence"),),
    )
    assert not presets._same_exact_scale_levels(
        old, (ScoringScaleLevel(value=True, label="One", meaning="Evidence"),),
    )
    assert not presets._same_exact_scale_levels(old, ())


def test_preset_stale_revision_does_not_show_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current = _preset()
    receipts = _stub_existing(monkeypatch, current)
    monkeypatch.setattr(presets, "prompt_text", lambda *_args, **_kw: "Revised Scale")
    monkeypatch.setattr(
        presets, "guide_scale_levels",
        lambda **kwargs: GuidedScaleMenuResult(kwargs["existing"]),
    )
    monkeypatch.setattr(
        presets, "_edit_optional_preset_scale_field",
        lambda _title, _label, previous: previous,
    )
    monkeypatch.setattr(presets, "confirm_write", lambda *_args: True)

    def stale(_request: Any) -> None:
        raise ValueError("stale preset revision")

    monkeypatch.setattr(presets, "revise_scoring_scale_preset", stale)
    with pytest.raises(ValueError, match="stale preset revision"):
        presets._edit_scale(SimpleNamespace(preset_id=current.preset_id), _state())
    assert receipts == []


def test_scale_preset_dispatch_does_not_issue_false_generic_updated_receipt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []
    monkeypatch.setattr(
        presets, "_choose_preset",
        lambda *_args, **_kw: SimpleNamespace(preset_id="scale"),
    )
    monkeypatch.setattr(presets, "_edit_scale", lambda *_args: events.append("scale"))
    monkeypatch.setattr(
        presets, "show_result", lambda *_args: events.append("generic receipt"),
    )
    presets._edit("scoring_scale", _state())
    assert events == ["scale"]


@pytest.mark.parametrize("action,expected", [
    ("keep", "Keep this"), ("clear", None), ("change", "New meaning"),
])
def test_revision_optional_guidance_is_explicit(
    monkeypatch: pytest.MonkeyPatch, action: str, expected: str | None,
) -> None:
    monkeypatch.setattr(presets, "select_one", lambda *_args, **_kw: action)
    monkeypatch.setattr(presets, "_optional_text", lambda *_args: "New meaning")
    assert presets._edit_optional_preset_scale_field(
        "Title", "Intended use", "Keep this"
    ) == expected
