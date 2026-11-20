"""#150 PR #173 human-acceptance repair: actor, restart, and teacher shortcuts.

Synthetic, isolated menu-level witnesses.  No workspace or Score writes.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import concord.menu_actor_action as actor_actions
import concord.menu_guided_activity as guided
import concord.menu_scoring as scoring
from concord.menu_context import MenuSessionContext
from concord.menu_navigation import QuitPDS, ReturnToMainMenu
from concord.teacher_attribution import (
    TeacherAttributionIdentity,
    TeacherAttributionNotConfiguredError,
)
from concord.workflows import WorkflowActor
from concord.workflows.guided_activity_setup import GuidedActivitySetup, GuidedSetupArea
from concord.workflows.models import ActivitySummary


def _target() -> ActivitySummary:
    return ActivitySummary(
        class_id="target-only",
        activity_id="activity-target",
        title="Synthetic copied seminar",
        status="draft",
        scoring_orientation="mixed",
        session_count=1,
        group_count=0,
        snapshot_revision=3,
    )


def _setup() -> GuidedActivitySetup:
    return GuidedActivitySetup(
        class_id="target-only",
        activity_id="activity-target",
        title="Synthetic copied seminar",
        areas=(
            GuidedSetupArea(
                key="groups",
                label="Student groups",
                status="needs_attention",
                detail="Six empty target draft Clusters",
            ),
        ),
    )


@pytest.mark.parametrize(
    ("shortcut", "owner"),
    (("c", "_launch_target_cluster_planning"), ("r", "_launch_target_assessment")),
)
def test_resumed_guide_offers_exact_target_shortcuts_without_recopied_writes(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    shortcut: str,
    owner: str,
) -> None:
    actions: list[tuple[str, ActivitySummary]] = []
    monkeypatch.setattr(
        guided,
        "show_activity",
        lambda *_a: SimpleNamespace(summary=_target()),
    )
    monkeypatch.setattr(guided, "load_menu_standards_library", lambda: None)
    monkeypatch.setattr(
        guided,
        "inspect_guided_activity_setup",
        lambda *_a, **_kw: _setup(),
    )
    monkeypatch.setattr(guided, "clear_screen", lambda: None)
    monkeypatch.setattr(
        guided,
        "copy_activity",
        lambda *_a, **_k: pytest.fail("recopy"),
    )
    monkeypatch.setattr(
        guided,
        "create_target_six_cluster_draft",
        lambda *_a, **_k: pytest.fail("unreviewed write"),
    )
    monkeypatch.setattr(
        guided,
        "launch_assessment_setup_menu",
        lambda *_a, **_k: pytest.fail("unreviewed write"),
    )
    for name in ("_launch_target_cluster_planning", "_launch_target_assessment"):
        monkeypatch.setattr(
            guided,
            name,
            lambda activity, _state, name=name: actions.append((name, activity)),
        )
    answers = iter((shortcut, "4"))
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    guided.launch_guided_setup_for_activity(_target(), MenuSessionContext())
    assert actions == [(owner, _target())]
    printed = capsys.readouterr().out
    assert "C. Review or plan six target Clusters" in printed
    assert "R. Use saved rubric / target assessment setup" in printed
    assert "4. Finish for now" in printed


@pytest.mark.parametrize("command,signal", (("m", ReturnToMainMenu), ("q", QuitPDS)))
def test_global_navigation_from_resumed_setup_reaches_module_owner(
    monkeypatch: pytest.MonkeyPatch, command: str, signal: type[Exception]
) -> None:
    monkeypatch.setattr(
        guided,
        "resolve_read_workspace_root",
        lambda: Path("synthetic"),
    )
    monkeypatch.setattr(guided, "list_activities", lambda **_k: (_target(),))
    monkeypatch.setattr(guided, "_guided_activity_choice", lambda *_a, **_k: _target())
    monkeypatch.setattr(
        guided,
        "show_activity",
        lambda *_a: SimpleNamespace(summary=_target()),
    )
    monkeypatch.setattr(guided, "load_menu_standards_library", lambda: None)
    monkeypatch.setattr(
        guided,
        "inspect_guided_activity_setup",
        lambda *_a, **_k: _setup(),
    )
    monkeypatch.setattr(guided, "clear_screen", lambda: None)
    monkeypatch.setattr(
        guided,
        "show_result",
        lambda *_a: pytest.fail("swallowed navigation"),
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": command)
    with pytest.raises(signal):
        guided.launch_guided_continue_setup(MenuSessionContext())


@pytest.mark.parametrize("signal", (ReturnToMainMenu, QuitPDS))
def test_target_assessment_owner_navigation_is_not_an_unconfirmed_receipt(
    monkeypatch: pytest.MonkeyPatch, signal: type[Exception]
) -> None:
    from concord.workflows.target_assessment_preflight import TargetAssessmentCheckpoint

    monkeypatch.setattr(
        guided,
        "resolve_read_workspace_root",
        lambda: Path("synthetic"),
    )
    monkeypatch.setattr(
        guided,
        "show_activity",
        lambda *_a, **_k: SimpleNamespace(summary=_target()),
    )
    monkeypatch.setattr(guided, "standards_for_activity", lambda _a: None)
    monkeypatch.setattr(
        guided,
        "inspect_target_assessment",
        lambda *_a, **_k: TargetAssessmentCheckpoint(
            class_id="target-only",
            activity_id="activity-target",
            title="Synthetic",
            scoring_orientation="mixed",
            snapshot_revision=3,
            scale_ids=(),
            criterion_set_ids=(),
            selected_criterion_set_ids=(),
            score_record_ids=(),
            criterion_count=0,
        ),
    )
    monkeypatch.setattr(guided, "clear_screen", lambda: None)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "1")
    monkeypatch.setattr(
        guided,
        "launch_assessment_setup_menu",
        lambda *_a: (_ for _ in ()).throw(signal()),
    )
    monkeypatch.setattr(
        guided,
        "show_result",
        lambda *_a: pytest.fail("false unconfirmed"),
    )
    with pytest.raises(signal):
        guided._launch_target_assessment(_target(), MenuSessionContext())


def _scoring_fixtures(monkeypatch: pytest.MonkeyPatch) -> list[object]:
    saved = SimpleNamespace(
        name="Synthetic rubric",
        preset_id="set-saved",
        preset_revision_id="rev-1",
        revision=1,
        status="active",
        criterion_set_kind="standards_based",
        criteria=(SimpleNamespace(key="evidence"),),
    )
    monkeypatch.setattr(scoring, "_latest", lambda _a: _target())
    monkeypatch.setattr(scoring, "CriterionSetPresetRevision", SimpleNamespace)
    monkeypatch.setattr(scoring, "list_presets", lambda kind: (saved,))
    monkeypatch.setattr(scoring, "get_preset_revision", lambda *_a: saved)
    monkeypatch.setattr(scoring, "select_one", lambda *_a, **_k: saved)
    monkeypatch.setattr(
        scoring,
        "_saved_criteria_preview",
        lambda _value: ("Rubric summary",),
    )
    monkeypatch.setattr(scoring, "_choose_saved_scale_for_preset", lambda _value: None)
    monkeypatch.setattr(scoring, "_library", lambda: None)
    monkeypatch.setattr(
        scoring,
        "prepare_scoring_setup",
        lambda request, **_k: SimpleNamespace(
            recorded_actor=request.actor,
            review_digest="a" * 64,
            criterion_count=1,
            scoring_scale_preset_name=None,
            standards_profile_id=None,
        ),
    )
    committed: list[object] = []
    monkeypatch.setattr(
        scoring,
        "materialize_scoring_setup",
        lambda request, **_k: (
            committed.append(request),
            SimpleNamespace(
                criterion_set_id=request.criterion_set_id,
                criterion_ids=tuple(
                    item.criterion_id for item in request.criterion_ids
                ),
                scoring_scale_id=None,
                commit=SimpleNamespace(snapshot_revision=4),
            ),
        )[1],
    )
    monkeypatch.setattr(scoring, "clear_screen", lambda: None)
    monkeypatch.setattr(actor_actions, "clear_screen", lambda: None)
    monkeypatch.setattr(scoring, "show_result", lambda *_a: None)
    return committed


class _MissingDefaultProvider:
    def resolve_with_fingerprint(self) -> tuple[TeacherAttributionIdentity, str]:
        raise TeacherAttributionNotConfiguredError("synthetic preference absent")


@pytest.mark.parametrize("approved", (True, False))
def test_saved_setup_missing_default_uses_reviewed_temporary_actor(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], approved: bool
) -> None:
    committed = _scoring_fixtures(monkeypatch)
    alternate = TeacherAttributionIdentity("adult-temporary", "Test Adult", "temporary")
    monkeypatch.setattr(actor_actions, "_choose_temporary_actor", lambda: alternate)
    answers = iter(("a", "USE") if approved else ("",))
    monkeypatch.setattr("builtins.input", lambda _p="": next(answers))
    state = MenuSessionContext(attribution_provider=_MissingDefaultProvider())
    scoring._use_saved_scoring_setup(_target(), state)
    assert len(committed) == (1 if approved else 0)
    if committed:
        assert committed[0].actor == alternate.workflow_actor()
        assert committed[0].expected_snapshot_revision == 3
    assert state.actor is None
    output = capsys.readouterr().out
    assert "Recorded by: not configured" in output
    if approved:
        assert "Attribution: temporary for THIS action" in output


def test_saved_scoring_setup_review_reprepares_request_for_each_actor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    committed = _scoring_fixtures(monkeypatch)
    default = WorkflowActor(actor_id="adult-default")
    alternate = WorkflowActor(actor_id="adult-other")
    prepared: list[object] = []

    def review(_title: str, _expected: str, **kwargs: object) -> object:
        prepare = kwargs["prepare_for_actor"]
        first, _ = prepare(default)  # type: ignore[operator]
        second, _ = prepare(alternate)  # type: ignore[operator]
        prepared.extend((first, second))
        return second

    monkeypatch.setattr(scoring, "confirm_prepared_actor_write", review)
    scoring._use_saved_scoring_setup(_target(), MenuSessionContext(actor=default))
    assert len(committed) == 1
    assert committed[0].actor == alternate
    assert prepared[0][0].actor == default
    assert prepared[1][0].actor == alternate
    assert prepared[0][0].criterion_set_id == prepared[1][0].criterion_set_id
