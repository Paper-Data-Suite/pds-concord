from __future__ import annotations

from types import SimpleNamespace
from typing import cast

import pytest
from pds_core.routing_models import ModuleWorkRef

import concord.menu_group_plan as plan_menu
import concord.menu_group_plan_signal as signal_menu
from concord.group_plan_signal import SignalGroupPlanProposal
from concord.menu_context import MenuSessionContext
from concord.models import PlannedGroup
from concord.workflows import (
    ActivitySummary,
    GroupingSignalDimensionSelection,
    WorkflowActor,
    WorkflowCommitResult,
)


def _activity(snapshot: int = 7) -> ActivitySummary:
    return ActivitySummary(
        class_id="class-1",
        activity_id="activity-1",
        title="Planning Activity",
        status="draft",
        scoring_orientation="evidence_only",
        session_count=1,
        group_count=0,
        snapshot_revision=snapshot,
    )


def _state() -> MenuSessionContext:
    return MenuSessionContext(actor=WorkflowActor(actor_id="teacher-1"))


def _commit(snapshot: int = 8) -> WorkflowCommitResult:
    return WorkflowCommitResult(
        work=ModuleWorkRef(
            module_id="concord",
            class_id="class-1",
            work_id="activity-1",
        ),
        snapshot_revision=snapshot,
        snapshot_sha256="a" * 64,
        changed_records=(),
        no_op=False,
    )


def _selection() -> GroupingSignalDimensionSelection:
    diagnostics = SimpleNamespace(
        roster_student_count=4,
        matched_student_count=3,
        missing_student_count=1,
        band_counts=((1, 1), (2, 1), (3, 1)),
    )
    signal = SimpleNamespace(student_bands=())
    return cast(
        GroupingSignalDimensionSelection,
        SimpleNamespace(
            signal_set_id="signal-1",
            digest="d" * 64,
            dimension_id="collaboration-context",
            dimension_diagnostics=diagnostics,
            inspection=SimpleNamespace(stored=SimpleNamespace(signal=signal)),
        ),
    )


def _proposal() -> SignalGroupPlanProposal:
    return cast(
        SignalGroupPlanProposal,
        SimpleNamespace(
            roster_student_ids=(
                "student-1",
                "student-2",
                "student-3",
                "student-4",
            ),
            proposed_groups=(
                PlannedGroup(
                    planned_group_key="similar-1",
                    label="Group 1",
                    student_ids=("student-1", "student-2"),
                ),
                PlannedGroup(
                    planned_group_key="similar-2",
                    label="Group 2",
                    student_ids=("student-3",),
                ),
            ),
            unresolved_student_ids=("student-4",),
            group_count=2,
            assigned_student_count=3,
            unresolved_student_count=1,
            group_sizes=(2, 1),
        ),
    )


def test_signal_menu_creation_carries_exact_preview_preconditions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current = _activity(11)
    selection = _selection()
    proposal = _proposal()
    captured: list[object] = []
    shown: list[tuple[str, tuple[str, ...]]] = []
    previewed: list[SignalGroupPlanProposal] = []
    diagnosed: list[GroupingSignalDimensionSelection] = []

    monkeypatch.setattr(signal_menu, "_latest", lambda _activity: current)
    monkeypatch.setattr(
        signal_menu,
        "prompt_text",
        lambda *a, **k: "activity-1-similar",
    )
    monkeypatch.setattr(
        signal_menu,
        "_select_signal_dimension",
        lambda _activity: (selection, proposal.roster_student_ids),
    )
    monkeypatch.setattr(
        signal_menu,
        "_show_signal_diagnostics",
        lambda selected: diagnosed.append(selected),
    )
    monkeypatch.setattr(
        signal_menu,
        "_choose_target",
        lambda _strategy, _count: (None, 2, "Target group count: 2"),
    )
    monkeypatch.setattr(signal_menu, "_proposal", lambda *a, **k: proposal)
    monkeypatch.setattr(
        signal_menu,
        "_show_preview",
        lambda _strategy, _selection, item, _target: previewed.append(item),
    )
    monkeypatch.setattr(signal_menu, "confirm_write", lambda *a, **k: True)
    monkeypatch.setattr(
        signal_menu,
        "show_result",
        lambda title, lines: shown.append((title, tuple(lines))),
    )

    def fake_create(request: object) -> object:
        captured.append(request)
        return SimpleNamespace(
            mutation=SimpleNamespace(
                commit=_commit(12),
                group_plan_id="activity-1-similar",
                status="draft",
            ),
            strategy="similar_signal",
            signal_set_id="signal-1",
            signal_set_digest="d" * 64,
            dimension_id="collaboration-context",
            group_count=2,
            assigned_student_count=3,
            unresolved_student_count=1,
            group_sizes=(2, 1),
        )

    monkeypatch.setattr(signal_menu, "create_signal_group_plan", fake_create)

    signal_menu.create_signal_group_plan_from_menu(
        current,
        _state(),
        "similar_signal",
    )

    assert diagnosed == [selection]
    assert previewed == [proposal]
    request = captured[0]
    assert getattr(request, "expected_snapshot_revision") == 11
    assert getattr(request, "strategy") == "similar_signal"
    assert getattr(request, "signal_set_id") == "signal-1"
    assert getattr(request, "dimension_id") == "collaboration-context"
    assert getattr(request, "target_group_size") is None
    assert getattr(request, "target_group_count") == 2
    assert getattr(request, "expected_roster_student_ids") == (
        "student-1",
        "student-2",
        "student-3",
        "student-4",
    )
    assert getattr(request, "expected_signal_set_digest") == "d" * 64

    lines = shown[0][1]
    assert "Similar-signal GroupPlan created." in lines
    assert "Signal set: signal-1" in lines
    assert f"Core signal digest: {'d' * 64}" in lines
    assert "Unresolved students: 1" in lines
    assert "Group sizes: 2,1" in lines
    assert "Canonical Groups created: no" in lines
    assert not any("student-1" in line for line in lines)


def test_signal_diagnostics_show_distribution_without_student_band_table(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(signal_menu, "clear_screen", lambda: None)
    monkeypatch.setattr(
        signal_menu,
        "print_menu_header",
        lambda *_a, **_k: None,
    )
    monkeypatch.setattr(signal_menu, "pause_for_user", lambda: None)

    signal_menu._show_signal_diagnostics(_selection())
    output = capsys.readouterr().out

    assert "Matched students: 3" in output
    assert "Missing students: 1" in output
    assert "Band 1: 1" in output
    assert "Band 2: 1" in output
    assert "Band 3: 1" in output
    assert "student-1" not in output
    assert "Missing signal coverage remains unresolved" in output


def test_signal_preview_shows_planned_memberships_not_student_bands(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(signal_menu, "clear_screen", lambda: None)
    monkeypatch.setattr(
        signal_menu,
        "print_menu_header",
        lambda *_a, **_k: None,
    )
    monkeypatch.setattr(signal_menu, "pause_for_user", lambda: None)

    signal_menu._show_preview(
        "similar_signal",
        _selection(),
        _proposal(),
        "Target group count: 2",
    )
    output = capsys.readouterr().out

    assert "Planned memberships:" in output
    assert "Group 1 (similar-1): student-1, student-2" in output
    assert "Unresolved IDs: student-4" in output
    assert "Band 1:" not in output
    assert "academic rank" in output
    assert "No canonical Groups or Memberships have been created." in output


def test_plan_groups_menu_exposes_both_signal_creation_choices(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    values = iter(["7", "8", "b"])

    monkeypatch.setattr("builtins.input", lambda _prompt="": next(values))
    monkeypatch.setattr(plan_menu, "clear_screen", lambda: None)
    monkeypatch.setattr(
        plan_menu,
        "print_menu_header",
        lambda *_a, **_k: None,
    )
    monkeypatch.setattr(
        plan_menu,
        "print_navigation",
        lambda *_a, **_k: None,
    )
    monkeypatch.setattr(plan_menu, "_latest", lambda activity: activity)
    monkeypatch.setattr(
        plan_menu,
        "create_signal_group_plan_from_menu",
        lambda _activity, _state, strategy: calls.append(strategy),
    )

    plan_menu.launch_group_plan_menu(_activity(), _state())
    assert calls == ["similar_signal", "mixed_signal"]
