from __future__ import annotations

from types import SimpleNamespace
from typing import cast

import pytest

import concord.menu_activity as menu_activity
import concord.menu_scoring as menu_scoring
from concord.menu_context import MenuSessionContext
from concord.models import Criterion, ScoreTargetReference
from concord.workflows import (
    ActivityDetail,
    ActivitySummary,
    ScoringScaleSummary,
    WorkflowActor,
)


def _activity() -> ActivitySummary:
    return ActivitySummary(
        class_id="class-1",
        activity_id="activity-1",
        title="Synthetic Scoring Activity",
        status="active",
        scoring_orientation="local_criteria_only",
        session_count=1,
        group_count=1,
        snapshot_revision=7,
    )


def test_json_scalar_parser_preserves_native_types() -> None:
    integer = menu_scoring._parse_json_scalar("1")
    floating = menu_scoring._parse_json_scalar("1.0")
    string = menu_scoring._parse_json_scalar('"1"')
    boolean = menu_scoring._parse_json_scalar("true")

    assert type(integer) is int
    assert type(floating) is float
    assert type(string) is str
    assert type(boolean) is bool


def test_group_score_confirmation_warns_against_individual_propagation() -> None:
    activity = _activity()
    target = ScoreTargetReference(
        target_kind="concord_group",
        target_id="group-1",
        owning_system="concord",
    )
    criterion = cast(
        Criterion,
        SimpleNamespace(label="Collaboration", criterion_id="criterion-1"),
    )
    scale = cast(
        ScoringScaleSummary,
        SimpleNamespace(name="Local scale", scoring_scale_id="scale-1"),
    )

    lines = menu_scoring._score_confirmation_lines(
        activity,
        target,
        criterion,
        scale,
        None,
        "scored",
        3,
        "professional_judgment",
        0,
    )

    assert "GROUP SCORE WARNING:" in lines
    assert "This Score applies only to the Group." in lines
    assert "It creates no individual student Scores." in lines


def test_record_score_requires_literal_score_confirmation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    activity = _activity()
    target = ScoreTargetReference(
        target_kind="concord_group",
        target_id="group-1",
        owning_system="concord",
    )
    criterion = cast(
        Criterion,
        SimpleNamespace(label="Collaboration", criterion_id="criterion-1"),
    )
    scale = cast(
        ScoringScaleSummary,
        SimpleNamespace(name="Local scale", scoring_scale_id="scale-1"),
    )
    draft = menu_scoring._ScoreDraft(
        criterion=criterion,
        target=target,
        scale=scale,
        session_id=None,
        disposition="scored",
        basis="professional_judgment",
        value=3,
        rationale="Teacher judgment.",
        links=(),
        status_reason=None,
    )
    captured: dict[str, object] = {}

    monkeypatch.setattr(menu_scoring, "_latest", lambda value: value)
    monkeypatch.setattr(
        menu_scoring,
        "_score_components",
        lambda current, state: draft,
    )
    monkeypatch.setattr(
        menu_scoring,
        "_identifier",
        lambda title, label, default: "score-1",
    )

    def fake_confirm(
        title: str,
        expected: str,
        lines: tuple[str, ...],
    ) -> bool:
        captured["title"] = title
        captured["expected"] = expected
        captured["lines"] = lines
        return False

    monkeypatch.setattr(menu_scoring, "confirm_write", fake_confirm)
    state = MenuSessionContext(actor=WorkflowActor(actor_id="teacher-1"))
    menu_scoring._record_score(activity, state)

    assert captured["title"] == "Record a Score"
    assert captured["expected"] == "SCORE"
    assert "GROUP SCORE WARNING:" in cast(tuple[str, ...], captured["lines"])


def test_activity_context_menu_dispatches_to_scoring(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    activity = _activity()
    detail = ActivityDetail(
        summary=activity,
        description=None,
        activity_type="project",
        standards_profile_id=None,
        focus_standard_ids=(),
    )
    calls: list[str] = []
    answers = iter(("8", "b"))

    monkeypatch.setattr(
        menu_activity,
        "show_activity",
        lambda class_id, activity_id: detail,
    )
    monkeypatch.setattr(
        menu_activity,
        "launch_scoring_menu",
        lambda selected, state: calls.append(selected.activity_id),
    )
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))

    menu_activity.launch_activity_context_menu(
        activity,
        MenuSessionContext(actor=WorkflowActor(actor_id="teacher-1")),
    )

    assert calls == ["activity-1"]
