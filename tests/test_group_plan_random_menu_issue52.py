from __future__ import annotations

from types import SimpleNamespace

import pytest
from pds_core.routing_models import ModuleWorkRef

import concord.menu_group_plan as plan_menu
import concord.menu_prompts as prompts
from concord.menu_context import MenuSessionContext
from concord.workflows import ActivitySummary, WorkflowActor, WorkflowCommitResult


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


def test_random_menu_creation_uses_latest_snapshot_and_exact_inputs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current = _activity(11)
    captured_requests: list[object] = []
    shown: list[tuple[str, tuple[str, ...]]] = []

    monkeypatch.setattr(plan_menu, "_latest", lambda _activity: current)
    monkeypatch.setattr(
        plan_menu,
        "prompt_text",
        lambda *a, **k: "activity-1-random",
    )
    monkeypatch.setattr(
        plan_menu,
        "prompt_exact_text",
        lambda *a, **k: "seed-52",
    )
    monkeypatch.setattr(plan_menu, "select_one", lambda *a, **k: "size")
    monkeypatch.setattr(
        plan_menu,
        "prompt_positive_int",
        lambda *a, **k: 4,
    )
    monkeypatch.setattr(
        plan_menu,
        "confirm_write",
        lambda *a, **k: True,
    )
    monkeypatch.setattr(
        plan_menu,
        "show_result",
        lambda title, lines: shown.append((title, tuple(lines))),
    )

    def fake_create(request: object) -> object:
        captured_requests.append(request)
        return SimpleNamespace(
            mutation=SimpleNamespace(
                commit=_commit(12),
                group_plan_id="activity-1-random",
                status="draft",
            ),
            group_count=3,
            assigned_student_count=10,
            group_sizes=(4, 3, 3),
        )

    monkeypatch.setattr(
        plan_menu,
        "create_random_group_plan",
        fake_create,
    )
    plan_menu._create_random(current, _state())

    request = captured_requests[0]
    assert getattr(request, "expected_snapshot_revision") == 11
    assert getattr(request, "seed") == "seed-52"
    assert getattr(request, "target_group_size") == 4
    assert getattr(request, "target_group_count") is None

    lines = shown[0][1]
    assert "Random GroupPlan created." in lines
    assert "Generated groups: 3" in lines
    assert "Assigned students: 10" in lines
    assert "Unresolved students: 0" in lines
    assert "Group sizes: 4,3,3" in lines
    assert "Canonical Groups created: no" in lines


def test_plan_groups_menu_exposes_random_creation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    values = iter(["3", "b"])

    monkeypatch.setattr(
        "builtins.input",
        lambda _prompt="": next(values),
    )
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
    monkeypatch.setattr(
        plan_menu,
        "_latest",
        lambda activity: activity,
    )
    monkeypatch.setattr(
        plan_menu,
        "_create_random",
        lambda _activity, _state: calls.append("random"),
    )

    plan_menu.launch_group_plan_menu(_activity(), _state())
    assert calls == ["random"]


def test_exact_text_prompt_preserves_whitespace_for_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "builtins.input",
        lambda _prompt="": " seed-52 ",
    )
    monkeypatch.setattr(prompts, "clear_screen", lambda: None)
    monkeypatch.setattr(
        prompts,
        "print_menu_header",
        lambda *_a, **_k: None,
    )
    monkeypatch.setattr(
        prompts,
        "print_navigation",
        lambda *_a, **_k: None,
    )

    result = prompts.prompt_exact_text(
        "Random Seed",
        "Seed",
        help_text="Exact seed.",
    )
    assert result == " seed-52 "
