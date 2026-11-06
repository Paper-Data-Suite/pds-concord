"""#145 Slice 2: aggregation notes are explained and can be inspected."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from concord import menu_presets as presets
from concord import menu_prompts as prompts
from concord import menu_scoring as scoring


def test_notes_prompt_explains_metadata_without_help(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("builtins.input", lambda message: "")
    monkeypatch.setattr(prompts, "clear_screen", lambda: None)
    assert prompts.prompt_scale_combining_notes("Create Scoring Scale") is None
    display = capsys.readouterr().out
    assert "Optional notes on combining assessment results" in display
    assert "reference only" in display
    assert "does not automatically combine Scores or calculate Grades" in display
    assert "most recent consistent evidence" in display
    assert "Press Enter to leave this blank" in display


@pytest.mark.parametrize("module", (scoring, presets))
@pytest.mark.parametrize("action,expected", (
    ("keep", "previous note"),
    ("change", "replacement note"),
    ("clear", None),
))
def test_revision_notes_keep_change_clear(
    monkeypatch: pytest.MonkeyPatch, module: object,
    action: str, expected: str | None,
) -> None:
    monkeypatch.setattr(module, "select_one", lambda *args, **kwargs: action)
    prompted: list[str] = []

    def replacement(title: str) -> str:
        prompted.append(title)
        return "replacement note"

    monkeypatch.setattr(module, "prompt_scale_combining_notes", replacement)
    fn = (
        scoring._edit_optional_scale_field
        if module is scoring else presets._edit_optional_preset_scale_field
    )
    actual = fn(
        "Revise Scoring Scale", "Notes on combining assessment results",
        "previous note", combining_notes=True,
    )
    assert actual == expected
    assert bool(prompted) == (action == "change")


def test_native_scale_details_include_saved_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summary = SimpleNamespace(
        class_id="synthetic-class", activity_id="synthetic-activity",
        scoring_scale_id="scale-one", lineage_id="lineage-one",
        revision=1, name="Four-level", scale_type="ordinal", status="active",
        is_current=True, intended_use="Student and Group assessment",
    )
    detail = SimpleNamespace(
        summary=summary, aggregation_guidance="Use most recent evidence", levels=(),
    )
    monkeypatch.setattr(scoring, "_library", lambda: None)
    monkeypatch.setattr(scoring, "list_scoring_scales", lambda *a, **k: (summary,))
    monkeypatch.setattr(scoring, "select_one", lambda *a, **k: summary)
    monkeypatch.setattr(scoring, "show_scoring_scale", lambda *a, **k: detail)
    shown: list[tuple[str, tuple[str, ...]]] = []
    monkeypatch.setattr(
        scoring, "show_result", lambda title, lines: shown.append((title, lines))
    )
    scoring._browse_scales(summary)
    assert shown[0][0] == "Scoring Scale Detail"
    assert "Intended use: Student and Group assessment" in shown[0][1]
    assert (
        "Notes on combining assessment results: Use most recent evidence"
        in shown[0][1]
    )


def test_saved_preset_details_include_guidance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class SyntheticScalePreset:
        pass

    value = SyntheticScalePreset()
    value.name = "Four-level"  # type: ignore[attr-defined]
    value.status = "active"  # type: ignore[attr-defined]
    value.revision = 1  # type: ignore[attr-defined]
    value.scale_type = "ordinal"  # type: ignore[attr-defined]
    value.levels = ()  # type: ignore[attr-defined]
    value.intended_use = "Rubric assessment"  # type: ignore[attr-defined]
    value.aggregation_guidance = "Do not average"  # type: ignore[attr-defined]
    monkeypatch.setattr(presets, "ScoringScalePresetRevision", SyntheticScalePreset)
    monkeypatch.setattr(presets, "get_preset", lambda kind, preset_id: value)
    lines = presets._detail_lines("scoring_scale", "synthetic-preset")
    assert "Intended use: Rubric assessment" in lines
    assert "Notes on combining assessment results: Do not average" in lines


def test_scale_preset_detail_route_is_visible_and_read_only(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    inputs = iter(("5", "B"))
    monkeypatch.setattr("builtins.input", lambda message: next(inputs))
    monkeypatch.setattr(presets, "clear_screen", lambda: None)
    visits: list[str] = []
    monkeypatch.setattr(presets, "_show", lambda kind: visits.append(kind))
    presets._kind_menu("scoring_scale", SimpleNamespace())
    assert visits == ["scoring_scale"]
    assert "5. View a preset's details" in capsys.readouterr().out
