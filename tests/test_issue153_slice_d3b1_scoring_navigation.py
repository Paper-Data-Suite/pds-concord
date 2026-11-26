"""#153 D3b1: assessment/Score navigation and post-create boundaries."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import concord.menu_scoring as scoring
from concord.menu_context import MenuSessionContext
from concord.menu_navigation import QuitPDS, ReturnToMainMenu
from concord.menu_prompts import select_one
from concord.workflows import ActivitySummary, WorkflowActor

ACTIVITY = ActivitySummary(
    class_id="class-1",
    activity_id="activity-1",
    title="Synthetic Activity",
    status="draft",
    scoring_orientation="mixed",
    session_count=1,
    group_count=1,
    snapshot_revision=1,
)
ROUTES = (
    ("_create_scale", "prompt_text"),
    ("_revise_scale", "select_one"),
    ("_browse_scales", "select_one"),
    ("_import_saved_scale", "select_one"),
    ("_create_criterion_set", "prompt_text"),
    ("_create_guided_criterion_set", "guide_native_criterion_set"),
    ("_revise_criterion_set_advanced", "select_one"),
    ("_select_criterion_sets_advanced", "select_many"),
    ("_browse_criterion_sets", "select_one"),
    ("_record_score", "_score_components"),
    ("_browse_scores", "select_one"),
    ("_revise_score", "select_one"),
    ("_save_scale_as_preset", "select_one"),
    ("_save_criterion_set_as_preset", "select_one"),
    ("_use_existing_criterion_set", "select_one"),
    ("_revise_criterion_set", "select_one"),
    ("_use_saved_scoring_setup", "select_one"),
)
READ_ONLY = {"_browse_scales", "_browse_criterion_sets", "_browse_scores"}


def _state() -> MenuSessionContext:
    return MenuSessionContext(actor=WorkflowActor(actor_id="synthetic-teacher"))


def _choose(*_args: object, **_kwargs: object) -> str:
    return select_one("Synthetic choice", ("one",), ("One",), help_text="Choose one.")


def _forbidden(*_args: object, **_kwargs: object) -> None:
    pytest.fail("Navigation must not reach confirmation or an error receipt")


@pytest.mark.parametrize(("action", "prompt"), ROUTES)
@pytest.mark.parametrize("choice", ("b", "m", "q"))
def test_assessment_action_navigation_unwinds(
    monkeypatch: pytest.MonkeyPatch, action: str, prompt: str, choice: str
) -> None:
    monkeypatch.setattr("builtins.input", lambda _prompt="": choice)
    monkeypatch.setattr(scoring, "_latest", lambda *_a: ACTIVITY)
    monkeypatch.setattr(scoring, "_library", lambda: None)
    monkeypatch.setattr(scoring, "_handle_error", _forbidden)
    monkeypatch.setattr(scoring, "show_result", _forbidden)
    monkeypatch.setattr(scoring, "confirm_actor_write", _forbidden)
    monkeypatch.setattr(scoring, "confirm_prepared_actor_write", _forbidden)
    item = SimpleNamespace(
        name="Synthetic definition",
        revision=1,
        is_current=True,
        scoring_scale_id="scale-1",
        criterion_set_id="set-1",
        snapshot_revision=1,
        preset_id="preset-1",
        preset_revision_id="revision-1",
        status="active",
        scale_type="ordinal",
        levels=(),
        criteria=(),
        criterion_set_kind="mixed",
    )
    detail = SimpleNamespace(standards_profile_id=None, focus_standard_ids=())
    selection = SimpleNamespace(snapshot_revision=1)
    monkeypatch.setattr(scoring, "show_activity", lambda *_a: detail)
    monkeypatch.setattr(
        scoring, "read_activity_criterion_set_selection", lambda *_a, **_k: selection
    )
    for name in (
        "list_scoring_scales",
        "list_criterion_sets",
        "list_scores",
        "list_current_score_heads",
        "list_presets",
    ):
        monkeypatch.setattr(scoring, name, lambda *_a, **_k: (item,))
    # Stand-ins are limited to preset/label reads before the real prompt.
    monkeypatch.setattr(scoring, "ScoringScalePresetRevision", SimpleNamespace)
    monkeypatch.setattr(scoring, "CriterionSetPresetRevision", SimpleNamespace)
    monkeypatch.setattr(scoring, "get_preset_revision", lambda *_a: item)
    monkeypatch.setattr(
        scoring, "build_score_teacher_labels", lambda *_a, **_k: object()
    )
    monkeypatch.setattr(scoring, "_score_history_label", lambda *_a: "Score")
    monkeypatch.setattr(scoring, "_revisable_score_label", lambda *_a: "Score")
    monkeypatch.setattr(scoring, prompt, _choose)
    run = getattr(scoring, action)
    args = (ACTIVITY,) if action in READ_ONLY else (ACTIVITY, _state())
    if choice == "b":
        assert run(*args) is None
    else:
        error = ReturnToMainMenu if choice == "m" else QuitPDS
        with pytest.raises(error):
            run(*args)


@pytest.mark.parametrize("next_step", ("2", "3"))
@pytest.mark.parametrize("choice", ("b", "m", "q"))
def test_created_scale_continuation_navigation_preserves_prior_receipt(
    monkeypatch: pytest.MonkeyPatch, next_step: str, choice: str
) -> None:
    answers = iter((next_step, choice))
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    monkeypatch.setattr(scoring, "_latest", lambda *_a: ACTIVITY)
    monkeypatch.setattr(scoring, "_criterion_set_menu", _choose)
    monkeypatch.setattr(scoring, "_save_scale_id_as_preset", _choose)
    receipts: list[str] = []
    monkeypatch.setattr(
        scoring, "show_result", lambda title, _lines: receipts.append(title)
    )
    if choice == "b":
        scoring._continue_created_scale(ACTIVITY, _state(), "already-created-scale")
    else:
        error = ReturnToMainMenu if choice == "m" else QuitPDS
        with pytest.raises(error):
            scoring._continue_created_scale(ACTIVITY, _state(), "already-created-scale")
    expected = (
        ["Configure Criteria — Native Scale Available"] if next_step == "2" else []
    )
    assert receipts == expected
