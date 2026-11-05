"""#144 Slice 2: guided native Scoring Scale menu safety and type fidelity."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

import concord.menu_scale_guidance as guided_menu
import concord.menu_scoring as scoring_menu
from concord.menu_context import CancelMenuAction, MenuSessionContext
from concord.models import ScoringScaleLevel
from concord.scale_guidance import (
    GuidedScaleDraft,
    four_level_proficiency,
    yes_no_scale,
)
from concord.workflows import ActivitySummary, WorkflowActor


def _activity() -> ActivitySummary:
    return ActivitySummary(
        class_id="class-synthetic", activity_id="lesson-synthetic",
        title="Synthetic Discussion", status="draft",
        scoring_orientation="local_criteria_only",
        session_count=1, group_count=0, snapshot_revision=7,
    )


def _state() -> MenuSessionContext:
    return MenuSessionContext(actor=WorkflowActor(actor_id="teacher-synthetic"))


def _success(record_id: str) -> SimpleNamespace:
    return SimpleNamespace(
        scoring_scale_id=record_id,
        commit=SimpleNamespace(snapshot_revision=8),
    )


def test_guided_starter_is_four_ordered_integers_and_not_written(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    choices = iter(("proficiency", "done"))
    previews: list[tuple[str, ...]] = []
    monkeypatch.setattr(guided_menu, "select_one", lambda *a, **kw: next(choices))
    monkeypatch.setattr(
        guided_menu, "show_result", lambda _title, lines: previews.append(tuple(lines))
    )
    seen: list[GuidedScaleDraft] = []
    proposed = guided_menu.guide_scale_levels(
        title="Create Scale", validator=seen.append,
    )
    assert seen == [proposed.draft]
    assert proposed.draft.scale_type == "ordinal"
    assert [
        (type(item.value), item.value, item.position)
        for item in proposed.draft.levels
    ] == [
        (int, 1, 1), (int, 2, 2), (int, 3, 3), (int, 4, 4),
    ]
    assert any("[integer]" in line for group in previews for line in group)
    assert all("No durable changes before approval." in group for group in previews)


def test_guided_yes_no_has_real_booleans(monkeypatch: pytest.MonkeyPatch) -> None:
    choices = iter(("yes_no", "done"))
    monkeypatch.setattr(guided_menu, "select_one", lambda *a, **kw: next(choices))
    monkeypatch.setattr(guided_menu, "show_result", lambda *_: None)
    draft = guided_menu.guide_scale_levels(title="Create Scale").draft
    assert draft.scale_type == "binary"
    assert [(type(item.value), item.value) for item in draft.levels] == [
        (bool, False), (bool, True),
    ]


def test_guided_keep_preserves_exact_historical_types(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current = GuidedScaleDraft(
        scale_type="teacher_defined",
        levels=(
            ScoringScaleLevel(value=1, label="Integer", meaning="One"),
            ScoringScaleLevel(value=1.0, label="Float", meaning="One float"),
            ScoringScaleLevel(value="1", label="Text", meaning="One string"),
            ScoringScaleLevel(value=True, label="Bool", meaning="True"),
        ),
    )
    monkeypatch.setattr(guided_menu, "select_one", lambda *a, **kw: "keep")
    monkeypatch.setattr(guided_menu, "show_result", lambda *_: None)
    proposed = guided_menu.guide_scale_levels(title="Revise Scale", existing=current)
    assert proposed.draft is current
    assert [type(item.value) for item in proposed.draft.levels] == [
        int, float, str, bool
    ]


def test_guided_invalid_draft_is_rejected_before_return(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    choices = iter(("proficiency", "done", "done"))
    messages: list[tuple[str, ...]] = []
    monkeypatch.setattr(guided_menu, "select_one", lambda *a, **kw: next(choices))
    monkeypatch.setattr(
        guided_menu, "show_result", lambda _name, lines: messages.append(tuple(lines))
    )
    attempts: list[int] = []

    def validate(draft: GuidedScaleDraft) -> None:
        attempts.append(len(draft.levels))
        if len(attempts) == 1:
            raise ValueError("Duplicate values are not allowed")

    guided_menu.guide_scale_levels(title="Scale", validator=validate)
    assert attempts == [4, 4]
    assert any("Duplicate values" in " ".join(item) for item in messages)


def test_precision_approximation_requires_an_explicit_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses = iter((False, True))
    monkeypatch.setattr(guided_menu, "select_one", lambda *a, **kw: next(responses))
    monkeypatch.setattr(guided_menu, "prompt_text", lambda *a, **kw: "0.1")
    monkeypatch.setattr(guided_menu, "show_result", lambda *_: None)
    value, notice = guided_menu._number_or_text("decimal", None)
    assert type(value) is float and value == 0.1
    assert notice is not None and "explicitly accepted" in notice


def test_category_code_stays_literal_text(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(guided_menu, "prompt_exact_text", lambda *a, **kw: "01")
    value, notice = guided_menu._number_or_text("category", None)
    assert value == "01" and type(value) is str
    assert notice is None


def _native_mocks(monkeypatch: pytest.MonkeyPatch) -> list[Any]:
    calls: list[Any] = []
    monkeypatch.setattr(scoring_menu, "_latest", lambda _current: _activity())
    monkeypatch.setattr(scoring_menu, "_library", lambda: None)
    # Slice 2 native creation now displays a distinct descriptive-notes prompt.
    monkeypatch.setattr(
        scoring_menu, "prompt_scale_combining_notes", lambda _title: None
    )
    monkeypatch.setattr(
        scoring_menu, "show_result",
        lambda *args: calls.append(("receipt", args)),
    )
    return calls


def test_native_create_review_exact_levels_before_commit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _native_mocks(monkeypatch)
    monkeypatch.setattr(
        scoring_menu, "prompt_text", lambda *a, **kw: "Four-Level Proficiency"
    )
    monkeypatch.setattr(scoring_menu, "_optional_text", lambda *a, **kw: None)
    monkeypatch.setattr(
        scoring_menu, "guide_scale_levels",
        lambda **kw: guided_menu.GuidedScaleMenuResult(four_level_proficiency()),
    )

    def confirm(_title: str, expected: str, lines: tuple[str, ...]) -> bool:
        calls.append(("confirm", expected, lines))
        assert expected == "CREATE"
        assert any("1 [integer]" in line for line in lines)
        assert any("4 [integer]" in line for line in lines)
        assert any("No Scores" in line for line in lines)
        return True

    def save(request: Any, *, standards_library: Any) -> SimpleNamespace:
        calls.append(("write", request, standards_library))
        assert request.scale_type == "ordinal"
        assert [type(item.value) for item in request.levels] == [int] * 4
        assert request.expected_snapshot_revision == 7
        return _success(request.scoring_scale_id)

    monkeypatch.setattr(scoring_menu, "confirm_write", confirm)
    monkeypatch.setattr(scoring_menu, "create_scoring_scale", save)
    scoring_menu._create_scale(_activity(), _state())
    assert [call[0] for call in calls] == ["confirm", "write", "receipt"]
    assert "not yet linked" in str(calls[-1])


def test_native_create_cancel_does_not_call_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _native_mocks(monkeypatch)
    monkeypatch.setattr(
        scoring_menu, "prompt_text", lambda *a, **kw: "Four-Level Proficiency"
    )
    monkeypatch.setattr(scoring_menu, "_optional_text", lambda *a, **kw: None)
    monkeypatch.setattr(
        scoring_menu, "guide_scale_levels",
        lambda **kw: guided_menu.GuidedScaleMenuResult(four_level_proficiency()),
    )
    monkeypatch.setattr(scoring_menu, "confirm_write", lambda *a: False)
    monkeypatch.setattr(
        scoring_menu, "create_scoring_scale",
        lambda *a, **kw: pytest.fail("Canceled creation must not write"),
    )
    scoring_menu._create_scale(_activity(), _state())
    assert calls == []


def test_native_create_cancel_during_guidance_does_not_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _native_mocks(monkeypatch)
    monkeypatch.setattr(scoring_menu, "prompt_text", lambda *a, **kw: "Name")

    def cancel(**kw: Any) -> Any:
        raise CancelMenuAction

    monkeypatch.setattr(scoring_menu, "guide_scale_levels", cancel)
    monkeypatch.setattr(
        scoring_menu, "create_scoring_scale",
        lambda *a, **kw: pytest.fail("Cancel must not write"),
    )
    scoring_menu._create_scale(_activity(), _state())


def test_native_revision_preserves_existing_values_and_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _native_mocks(monkeypatch)
    levels = yes_no_scale().levels
    old = SimpleNamespace(
        name="Observation", scoring_scale_id="old-scale", revision=2,
        scale_type="binary", intended_use="Observation use",
    )
    detail = SimpleNamespace(
        summary=old, levels=levels, aggregation_guidance="Optional guidance"
    )
    monkeypatch.setattr(scoring_menu, "list_scoring_scales", lambda *a, **kw: (old,))
    monkeypatch.setattr(scoring_menu, "select_one", lambda *a, **kw: old)
    monkeypatch.setattr(scoring_menu, "show_scoring_scale", lambda *a, **kw: detail)
    monkeypatch.setattr(
        scoring_menu, "prompt_text", lambda *a, **kw: kw.get("default") or "Observation"
    )
    monkeypatch.setattr(
        scoring_menu, "guide_scale_levels",
        lambda **kw: guided_menu.GuidedScaleMenuResult(kw["existing"]),
    )
    monkeypatch.setattr(
        scoring_menu, "_edit_optional_scale_field",
        lambda _title, _label, previous, **_kwargs: previous,
    )
    monkeypatch.setattr(
        scoring_menu, "confirm_write",
        lambda _title, expected, lines: (
            calls.append(("confirm", expected, lines)) or True
        ),
    )

    def revise(request: Any, *, standards_library: Any) -> SimpleNamespace:
        calls.append(("write", request))
        assert request.scoring_scale_id == "old-scale"
        assert request.replacement_scoring_scale_id == "old-scale-r3"
        assert request.revision == 3
        assert request.levels is levels
        assert request.intended_use == "Observation use"
        assert request.aggregation_guidance == "Optional guidance"
        return _success(request.replacement_scoring_scale_id)

    monkeypatch.setattr(scoring_menu, "revise_scoring_scale", revise)
    scoring_menu._revise_scale(_activity(), _state())
    assert [call[0] for call in calls] == ["confirm", "write", "receipt"]
    assert "Historical Scale" in str(calls[0])


def test_revision_stale_conflict_receipt_does_not_claim_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _native_mocks(monkeypatch)
    levels = four_level_proficiency().levels
    old = SimpleNamespace(
        name="Proficiency", scoring_scale_id="old-scale", revision=1,
        scale_type="ordinal", intended_use=None,
    )
    detail = SimpleNamespace(summary=old, levels=levels, aggregation_guidance=None)
    monkeypatch.setattr(scoring_menu, "list_scoring_scales", lambda *a, **kw: (old,))
    monkeypatch.setattr(scoring_menu, "select_one", lambda *a, **kw: old)
    monkeypatch.setattr(scoring_menu, "show_scoring_scale", lambda *a, **kw: detail)
    monkeypatch.setattr(
        scoring_menu, "prompt_text", lambda *a, **kw: kw.get("default") or "Name"
    )
    monkeypatch.setattr(
        scoring_menu, "_edit_optional_scale_field", lambda *a, **kw: None
    )
    monkeypatch.setattr(
        scoring_menu, "guide_scale_levels",
        lambda **kw: guided_menu.GuidedScaleMenuResult(kw["existing"]),
    )
    monkeypatch.setattr(scoring_menu, "confirm_write", lambda *a: True)
    monkeypatch.setattr(
        scoring_menu, "revise_scoring_scale",
        lambda *a, **kw: (_ for _ in ()).throw(ValueError("stale snapshot")),
    )
    monkeypatch.setattr(
        scoring_menu, "_handle_error",
        lambda activity, error: calls.append(("error", str(error))),
    )
    scoring_menu._revise_scale(_activity(), _state())
    assert calls == [("error", "stale snapshot")]


def test_guided_entry_never_requires_json_literal_syntax(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    choices = iter(("number", "decimal", "done"))
    inputs = iter(("0.5", "Half", "Half of expected evidence"))
    monkeypatch.setattr(guided_menu, "select_one", lambda *a, **kw: next(choices))
    monkeypatch.setattr(guided_menu, "prompt_positive_int", lambda *a, **kw: 1)
    monkeypatch.setattr(
        guided_menu, "prompt_text",
        lambda *a, **kw: next(inputs) if not kw.get("optional") else None,
    )
    monkeypatch.setattr(guided_menu, "show_result", lambda *a: None)
    proposal = guided_menu.guide_scale_levels(title="Create")
    assert proposal.draft.scale_type == "numeric"
    level = proposal.draft.levels[0]
    assert type(level.value) is float and level.value == 0.5
