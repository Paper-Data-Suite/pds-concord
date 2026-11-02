"""#144 Slice 4: guarded Scale continuation and separate preset receipts."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

import concord.menu_scoring as scoring
from concord.menu_context import CancelMenuAction, MenuSessionContext
from concord.workflows import ActivitySummary, WorkflowActor


def _activity(revision: int = 9) -> ActivitySummary:
    return ActivitySummary(
        class_id="class-synthetic",
        activity_id="activity-synthetic",
        title="Synthetic Discussion",
        status="draft",
        scoring_orientation="local_criteria_only",
        session_count=1,
        group_count=0,
        snapshot_revision=revision,
    )


def _state() -> MenuSessionContext:
    return MenuSessionContext(actor=WorkflowActor(actor_id="teacher-synthetic"))


def _messages(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, tuple[str, ...]]]:
    shown: list[tuple[str, tuple[str, ...]]] = []
    monkeypatch.setattr(
        scoring,
        "show_result",
        lambda title, lines: shown.append((title, tuple(lines))),
    )
    return shown


def test_preset_save_requires_separate_explicit_confirmation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests: list[Any] = []
    reviews: list[tuple[str, tuple[str, ...]]] = []
    monkeypatch.setattr(scoring, "_library", lambda: None)

    def prepare(request: Any, **_kwargs: Any) -> SimpleNamespace:
        requests.append(request)
        return SimpleNamespace(
            name="Synthetic Preset",
            reusable_fields=("Levels: 1–4",),
            excluded_state=("Scores",),
            review_digest="digest-synthetic",
        )

    def confirm(title: str, expected: str, lines: tuple[str, ...]) -> bool:
        assert expected == "SAVE"
        reviews.append((title, lines))
        return False

    monkeypatch.setattr(scoring, "prepare_scoring_scale_preset_from_activity", prepare)
    monkeypatch.setattr(scoring, "confirm_write", confirm)
    monkeypatch.setattr(
        scoring,
        "save_scoring_scale_preset_from_activity",
        lambda *_args, **_kwargs: pytest.fail("Declined save cannot commit"),
    )
    result = scoring._save_scale_id_as_preset(_activity(), _state(), "scale-1")
    assert result is None
    assert len(requests) == 1
    assert requests[0].scoring_scale_id == "scale-1"
    assert requests[0].expected_snapshot_revision == 9
    assert any("Source native Scale ID: scale-1" in text for text in reviews[0][1])
    assert any("second, independently reviewed" in text for text in reviews[0][1])


def test_preset_save_uses_review_digest_and_exact_native_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[Any] = []
    monkeypatch.setattr(scoring, "_library", lambda: None)
    monkeypatch.setattr(
        scoring,
        "prepare_scoring_scale_preset_from_activity",
        lambda request, **_kw: SimpleNamespace(
            name="Preset", reusable_fields=(), excluded_state=("Scores",),
            review_digest="verified-digest",
        ),
    )
    monkeypatch.setattr(scoring, "confirm_write", lambda *_args: True)

    def commit(request: Any, **kwargs: Any) -> SimpleNamespace:
        seen.append((request, kwargs))
        return SimpleNamespace(preset_id=request.preset_id)

    monkeypatch.setattr(scoring, "save_scoring_scale_preset_from_activity", commit)
    saved = scoring._save_scale_id_as_preset(_activity(), _state(), "scale-a")
    assert len(seen) == 1
    assert saved == seen[0][0].preset_id
    assert seen[0][0].scoring_scale_id == "scale-a"
    assert seen[0][0].preset_revision_id == f"{saved}-v1"
    assert seen[0][1]["review_digest"] == "verified-digest"


def test_continuation_back_does_not_open_other_workflows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(scoring, "select_one", lambda *_a, **_kw: "back")
    monkeypatch.setattr(
        scoring, "_save_scale_id_as_preset",
        lambda *_args: pytest.fail("Back must not save"),
    )
    monkeypatch.setattr(
        scoring, "_criterion_set_menu",
        lambda *_args: pytest.fail("Back must not open Criteria"),
    )
    scoring._continue_created_scale(_activity(), _state(), "scale-a")


def test_continuation_back_navigation_does_not_undo_native_scale(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def cancel(*_args: Any, **_kwargs: Any) -> Any:
        raise CancelMenuAction

    monkeypatch.setattr(scoring, "select_one", cancel)
    monkeypatch.setattr(
        scoring, "_save_scale_id_as_preset",
        lambda *_args: pytest.fail("Back navigation must not write"),
    )
    scoring._continue_created_scale(_activity(), _state(), "scale-a")


def test_criteria_continuation_does_not_claim_a_link(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    shown = _messages(monkeypatch)
    opened: list[ActivitySummary] = []
    monkeypatch.setattr(scoring, "select_one", lambda *_a, **_kw: "criteria")
    monkeypatch.setattr(scoring, "_latest", lambda _item: _activity(10))
    monkeypatch.setattr(
        scoring,
        "_criterion_set_menu",
        lambda activity, _state: opened.append(activity),
    )
    scoring._continue_created_scale(_activity(), _state(), "scale-a")
    assert len(opened) == 1 and opened[0].snapshot_revision == 10
    assert "No Criterion is linked yet." in shown[0][1]
    assert any("separate successful Criterion write" in x for x in shown[0][1])


def test_reuse_continuation_refreshes_snapshot_before_preset_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    shown = _messages(monkeypatch)
    captured: list[Any] = []
    monkeypatch.setattr(scoring, "select_one", lambda *_a, **_kw: "reuse")
    monkeypatch.setattr(scoring, "_latest", lambda _item: _activity(10))

    def saved(activity: ActivitySummary, _state: Any, scale_id: str) -> str:
        captured.append((activity.snapshot_revision, scale_id))
        return "preset-1"

    monkeypatch.setattr(scoring, "_save_scale_id_as_preset", saved)
    scoring._continue_created_scale(_activity(), _state(), "scale-a")
    assert captured == [(10, "scale-a")]
    assert "Both writes succeeded independently." in shown[-1][1]
    assert "No Criterion is linked by saving a preset." in shown[-1][1]


def test_reuse_declined_preserves_native_success_and_no_preset_claim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    shown = _messages(monkeypatch)
    monkeypatch.setattr(scoring, "select_one", lambda *_a, **_kw: "reuse")
    monkeypatch.setattr(scoring, "_latest", lambda _item: _activity(10))
    monkeypatch.setattr(scoring, "_save_scale_id_as_preset", lambda *_args: None)
    scoring._continue_created_scale(_activity(), _state(), "scale-a")
    assert "Native Scale remains created: scale-a" in shown[-1][1]
    assert any("approval was declined" in x for x in shown[-1][1])


def test_reuse_failure_never_claims_rollback_or_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    shown = _messages(monkeypatch)
    monkeypatch.setattr(scoring, "select_one", lambda *_a, **_kw: "reuse")
    monkeypatch.setattr(scoring, "_latest", lambda _item: _activity(10))

    def failing(*_args: Any) -> Any:
        raise RuntimeError("stale snapshot")

    monkeypatch.setattr(scoring, "_save_scale_id_as_preset", failing)
    scoring._continue_created_scale(_activity(), _state(), "scale-a")
    assert "Native Scale Saved — Preset Outcome Not Confirmed" == shown[-1][0]
    assert "Native Scale remains created: scale-a" in shown[-1][1]
    assert any("Do not assume" in x for x in shown[-1][1])
    assert any("Inspect Reusable Presets" in x for x in shown[-1][1])


def test_save_existing_menu_delegates_to_same_guarded_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    shown = _messages(monkeypatch)
    selected = SimpleNamespace(scoring_scale_id="scale-old", name="Old")
    monkeypatch.setattr(scoring, "_latest", lambda _item: _activity(10))
    monkeypatch.setattr(scoring, "_library", lambda: None)
    monkeypatch.setattr(scoring, "list_scoring_scales", lambda *_a, **_kw: (selected,))
    monkeypatch.setattr(scoring, "select_one", lambda *_a, **_kw: selected)
    captured: list[str] = []

    def save(_activity: Any, _state: Any, scale_id: str) -> str:
        captured.append(scale_id)
        return "preset-2"

    monkeypatch.setattr(scoring, "_save_scale_id_as_preset", save)
    scoring._save_scale_as_preset(_activity(), _state())
    assert captured == ["scale-old"]
    assert "Reusable preset: preset-2" in shown[-1][1]


def test_scales_menu_offers_continuation_only_after_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    choices = iter(("1", "1", "b"))
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(choices))
    monkeypatch.setattr(scoring, "clear_screen", lambda: None)
    monkeypatch.setattr(scoring, "print_menu_header", lambda *_args: None)
    monkeypatch.setattr(scoring, "print_navigation", lambda: None)
    captured: list[str] = []
    monkeypatch.setattr(
        scoring, "_create_scale", lambda *_args: "native-id"
    )
    monkeypatch.setattr(
        scoring,
        "_continue_created_scale",
        lambda _activity, _state, scale_id: captured.append(scale_id),
    )
    scoring._scale_menu(_activity(), _state())
    assert captured == ["native-id", "native-id"]


def test_scales_menu_does_not_continue_canceled_creation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    choices = iter(("1", "b"))
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(choices))
    monkeypatch.setattr(scoring, "clear_screen", lambda: None)
    monkeypatch.setattr(scoring, "print_menu_header", lambda *_args: None)
    monkeypatch.setattr(scoring, "print_navigation", lambda: None)
    monkeypatch.setattr(scoring, "_create_scale", lambda *_args: None)
    monkeypatch.setattr(
        scoring,
        "_continue_created_scale",
        lambda *_args: pytest.fail("Canceled create cannot continue"),
    )
    scoring._scale_menu(_activity(), _state())
