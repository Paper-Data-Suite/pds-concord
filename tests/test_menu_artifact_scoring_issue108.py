from __future__ import annotations

from types import SimpleNamespace
from typing import cast

import pytest

import concord.menu_artifact_scoring as scoring_menu
from concord import menu_artifact
from concord.models import ScoreTargetReference
from concord.workflows.artifact_routine_scoring_preparation import RoutineScorePreview
from concord.workflows.models import ActivitySummary, WorkflowActor


def _activity(revision: int = 20) -> ActivitySummary:
    return cast(
        ActivitySummary,
        SimpleNamespace(
            class_id="class-1",
            activity_id="activity-1",
            title="Seminar Reflection",
            scoring_orientation="mixed",
            snapshot_revision=revision,
        ),
    )


def _state() -> object:
    actor = WorkflowActor(actor_id="teacher-1")
    return SimpleNamespace(require_actor=lambda: actor)


def _context(*, eligible: bool = True) -> object:
    return SimpleNamespace(
        class_id="class-1",
        activity_id="activity-1",
        artifact=SimpleNamespace(
            artifact_instance_id="artifact-1",
            session_id=None,
        ),
        current_review=SimpleNamespace(scoring_readiness="ready"),
        current_sessions=(),
        current_groups=(),
        eligibility=SimpleNamespace(
            routine_scoring_eligible=eligible,
            exception_reasons=()
            if eligible
            else ("The current Artifact Review is not ready for scoring.",),
        ),
    )


def _target() -> ScoreTargetReference:
    return ScoreTargetReference(
        target_kind="concord_artifact_instance",
        target_id="artifact-1",
        owning_system="concord",
    )


def _preview(*, existing: tuple[str, ...] = ()) -> RoutineScorePreview:
    return cast(
        RoutineScorePreview,
        SimpleNamespace(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            target_reference=_target(),
            criterion_id="criterion-1",
            criterion_label="Uses textual evidence",
            scoring_scale_id="scale-1",
            scoring_scale_name="Standards 4-point rubric",
            value=3,
            selected_level=SimpleNamespace(value=3, label="Proficient"),
            session_id=None,
            disposition="scored",
            basis="linked_evidence",
            evidence=SimpleNamespace(
                subject_context=(),
                moderation_requirement="not_required",
                relevance_description=(
                    "Returned Artifact evidence for this Score."
                ),
            ),
            existing_current_score_ids=existing,
        ),
    )


def _patch_preparation(
    monkeypatch: pytest.MonkeyPatch,
    *,
    preview: RoutineScorePreview,
) -> None:
    context = _context()
    criterion = SimpleNamespace(
        criterion_id="criterion-1",
        label="Uses textual evidence",
    )
    scale = SimpleNamespace(scoring_scale_id="scale-1")
    level = SimpleNamespace(value=3, label="Proficient")
    monkeypatch.setattr(scoring_menu, "_current_activity", lambda activity: activity)
    monkeypatch.setattr(
        scoring_menu,
        "inspect_artifact_routine_scoring",
        lambda *args, **kwargs: context,
    )
    monkeypatch.setattr(scoring_menu, "_choose_target", lambda *args: _target())
    monkeypatch.setattr(scoring_menu, "_choose_criterion", lambda *args: criterion)
    monkeypatch.setattr(scoring_menu, "_choose_scale", lambda *args: scale)
    monkeypatch.setattr(scoring_menu, "_choose_level", lambda *args: level)
    monkeypatch.setattr(scoring_menu, "_choose_session", lambda *args: None)
    monkeypatch.setattr(
        scoring_menu,
        "_choose_subject_context",
        lambda *args: (),
    )
    monkeypatch.setattr(
        scoring_menu,
        "_choose_relevance",
        lambda: "Returned Artifact evidence for this Score.",
    )
    monkeypatch.setattr(
        scoring_menu,
        "prepare_routine_score_preview",
        lambda *args, **kwargs: preview,
    )


def test_preview_shows_complete_teacher_significant_routine_decision() -> None:
    lines = scoring_menu._preview_lines(
        _activity(),
        cast(object, _context()),
        _preview(),
    )

    assert lines == (
        "Artifact: this reviewed Artifact",
        "Target: This Artifact",
        "Criterion: Uses textual evidence",
        "Scale: Standards 4-point rubric",
        "Value: 3 — Proficient",
        "Disposition: scored",
        "Basis: linked_evidence",
        "Evidence: this reviewed Artifact",
        "Subject context: None",
        "Session: None",
        "Moderation: not_required",
        "Relevance: Returned Artifact evidence for this Score.",
    )


def test_cancelled_score_confirmation_never_executes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    preview = _preview()
    _patch_preparation(monkeypatch, preview=preview)
    monkeypatch.setattr(scoring_menu, "confirm_write", lambda *args: False)
    monkeypatch.setattr(
        scoring_menu,
        "record_prepared_routine_score",
        lambda *args, **kwargs: pytest.fail("Score must not be written"),
    )

    recorded = scoring_menu._record_selected_artifact_score(
        _activity(),
        "artifact-1",
        cast(object, _state()),
    )

    assert not recorded


def test_confirmed_score_uses_score_token_then_canonical_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    preview = _preview()
    _patch_preparation(monkeypatch, preview=preview)
    captured: dict[str, object] = {}

    def fake_confirm(
        title: str,
        token: str,
        lines: tuple[str, ...],
    ) -> bool:
        captured["confirmation"] = (title, token, lines)
        return True

    def fake_record(
        supplied_preview: RoutineScorePreview,
        *,
        actor: WorkflowActor,
    ) -> object:
        captured["preview"] = supplied_preview
        captured["actor"] = actor
        return SimpleNamespace(commit=SimpleNamespace(snapshot_revision=21))

    monkeypatch.setattr(scoring_menu, "confirm_write", fake_confirm)
    monkeypatch.setattr(scoring_menu, "record_prepared_routine_score", fake_record)
    monkeypatch.setattr(scoring_menu, "show_result", lambda *args: None)

    recorded = scoring_menu._record_selected_artifact_score(
        _activity(),
        "artifact-1",
        cast(object, _state()),
    )

    assert recorded
    title, token, lines = cast(
        tuple[str, str, tuple[str, ...]],
        captured["confirmation"],
    )
    assert title == "Score this work"
    assert token == "SCORE"
    assert "Evidence: this reviewed Artifact" in lines
    assert "Relevance: Returned Artifact evidence for this Score." in lines
    assert captured["preview"] is preview
    assert cast(WorkflowActor, captured["actor"]).actor_id == "teacher-1"


def test_existing_current_score_does_not_create_parallel_routine_score(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_preparation(monkeypatch, preview=_preview(existing=("score-current",)))
    results: list[tuple[str, tuple[str, ...]]] = []
    monkeypatch.setattr(
        scoring_menu,
        "show_result",
        lambda title, lines: results.append((title, tuple(lines))),
    )
    monkeypatch.setattr(
        scoring_menu,
        "confirm_write",
        lambda *args: pytest.fail("Confirmation must not occur"),
    )
    monkeypatch.setattr(
        scoring_menu,
        "record_prepared_routine_score",
        lambda *args, **kwargs: pytest.fail("Score must not be written"),
    )

    recorded = scoring_menu._record_selected_artifact_score(
        _activity(),
        "artifact-1",
        cast(object, _state()),
    )

    assert not recorded
    assert "parallel Score" in results[-1][1][1]


def test_ineligible_routine_context_stops_before_teacher_score_choices(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(scoring_menu, "_current_activity", lambda activity: activity)
    monkeypatch.setattr(
        scoring_menu,
        "inspect_artifact_routine_scoring",
        lambda *args, **kwargs: _context(eligible=False),
    )
    monkeypatch.setattr(
        scoring_menu,
        "_choose_target",
        lambda *args: pytest.fail("Target must not be requested"),
    )
    results: list[tuple[str, tuple[str, ...]]] = []
    monkeypatch.setattr(
        scoring_menu,
        "show_result",
        lambda title, lines: results.append((title, tuple(lines))),
    )

    recorded = scoring_menu._record_selected_artifact_score(
        _activity(),
        "artifact-1",
        cast(object, _state()),
    )

    assert not recorded
    assert "not ready for scoring" in " ".join(results[-1][1])


def test_open_returned_work_keeps_exact_selected_artifact(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    activity = _activity()
    opened: list[tuple[str, int]] = []
    inputs = iter(("O", "B"))
    monkeypatch.setattr(scoring_menu, "_current_activity", lambda item: item)
    monkeypatch.setattr(
        scoring_menu,
        "inspect_artifact_routine_scoring",
        lambda *args, **kwargs: _context(),
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))
    monkeypatch.setattr(scoring_menu, "clear_screen", lambda: None)
    monkeypatch.setattr(scoring_menu, "print_menu_header", lambda *args: None)
    monkeypatch.setattr(scoring_menu, "print_navigation", lambda: None)

    def open_selected(current: ActivitySummary, artifact_id: str) -> bool:
        opened.append((artifact_id, current.snapshot_revision))
        return True

    scoring_menu.launch_selected_artifact_scoring(
        activity,
        "artifact-1",
        cast(object, _state()),
        open_selected_work=open_selected,
    )

    assert opened == [("artifact-1", 20)]


def test_review_score_entry_selects_artifact_once_then_preserves_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    activity = _activity()
    chosen = SimpleNamespace(artifact_instance_id="artifact-7")
    calls: list[str] = []
    monkeypatch.setattr(menu_artifact, "_latest", lambda item: item)
    monkeypatch.setattr(
        menu_artifact,
        "_choose_artifact",
        lambda *args, **kwargs: chosen,
    )

    def fake_launch(
        supplied_activity: ActivitySummary,
        artifact_id: str,
        state: object,
        *,
        open_selected_work: object,
    ) -> None:
        assert supplied_activity is activity
        assert callable(open_selected_work)
        calls.append(artifact_id)

    monkeypatch.setattr(
        scoring_menu,
        "launch_selected_artifact_scoring",
        fake_launch,
    )

    menu_artifact._score_selected_artifact(activity, cast(object, _state()))

    assert calls == ["artifact-7"]
