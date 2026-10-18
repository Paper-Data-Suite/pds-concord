"""#136 Slice 5A: actual teacher-menu dispatch and reviewed save/reuse boundaries."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

import concord.menu_group as group_menu
import concord.menu_group_plan as plan_menu
import concord.menu_saved_groupings as saved_menu
from concord.menu_context import MenuSessionContext
from concord.workflows import ActivitySummary, WorkflowActor
from concord.workflows.class_group_arrangements import StudentPlacementDecision


def _activity() -> ActivitySummary:
    return ActivitySummary(
        class_id="synthetic-class",
        activity_id="synthetic-activity",
        title="Synthetic Discussion",
        status="draft",
        scoring_orientation="mixed",
        session_count=1,
        group_count=0,
        snapshot_revision=8,
    )


def _state() -> MenuSessionContext:
    return MenuSessionContext(actor=WorkflowActor(actor_id="teacher-1"))


def _saved(*, status: str = "active") -> Any:
    return SimpleNamespace(
        sha256="a" * 64,
        revision=SimpleNamespace(
            arrangement_id="six-tables",
            name="Six Table Groups",
            revision=1,
            status=status,
            groups=(
                SimpleNamespace(key="a", label="Table A", student_ids=("s1",)),
                SimpleNamespace(key="b", label="Table B", student_ids=("s2",)),
            ),
            unresolved_student_ids=(),
        ),
    )


def _no_ui(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(saved_menu, "_latest", lambda _a: _activity())
    monkeypatch.setattr(saved_menu, "_show_placements", lambda *_a, **_k: None)
    monkeypatch.setattr(saved_menu, "show_result", lambda *_a, **_k: None)
    monkeypatch.setattr(
        saved_menu,
        "prompt_text",
        lambda *_a, **kw: kw.get("default", "Six Table Groups"),
    )


def test_group_menu_adds_saved_groupings_without_renumbering(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    choices = iter(["1", "2", "3", "b"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(choices))
    monkeypatch.setattr(group_menu, "clear_screen", lambda: None)
    monkeypatch.setattr(group_menu, "print_menu_header", lambda *_a, **_k: None)
    monkeypatch.setattr(group_menu, "print_navigation", lambda *_a, **_k: None)
    monkeypatch.setattr(
        group_menu, "launch_group_plan_menu", lambda *_a: calls.append("plan")
    )
    monkeypatch.setattr(
        group_menu, "launch_direct_group_menu", lambda *_a: calls.append("direct")
    )
    monkeypatch.setattr(
        group_menu, "launch_saved_groupings_menu", lambda *_a: calls.append("saved")
    )
    group_menu.launch_group_menu(_activity(), _state())
    assert calls == ["plan", "direct", "saved"]


def test_plan_menu_exposes_saved_groupings_as_new_choice(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    choices = iter(["9", "b"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(choices))
    monkeypatch.setattr(plan_menu, "clear_screen", lambda: None)
    monkeypatch.setattr(plan_menu, "print_menu_header", lambda *_a, **_k: None)
    monkeypatch.setattr(plan_menu, "print_navigation", lambda *_a, **_k: None)
    monkeypatch.setattr(plan_menu, "_latest", lambda a: a)
    monkeypatch.setattr(
        plan_menu, "launch_saved_groupings_menu", lambda *_a: calls.append("saved")
    )
    plan_menu.launch_group_plan_menu(_activity(), _state())
    assert calls == ["saved"]


@pytest.mark.parametrize("signal,choice", [(False, "11"), (True, "12")])
def test_open_editable_plan_exposes_save_without_renumbering_apply(
    monkeypatch: pytest.MonkeyPatch,
    signal: bool,
    choice: str,
) -> None:
    calls: list[str] = []
    options = iter([choice, "b"])
    detail = SimpleNamespace(
        plan=SimpleNamespace(
            group_plan_id="source-plan",
            strategy="mixed_signal" if signal else "manual",
            status="draft",
        ),
        summary=SimpleNamespace(unresolved_student_count=0),
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(options))
    monkeypatch.setattr(plan_menu, "show_group_plan", lambda *_a: detail)
    monkeypatch.setattr(plan_menu, "clear_screen", lambda: None)
    monkeypatch.setattr(plan_menu, "print_menu_header", lambda *_a, **_k: None)
    monkeypatch.setattr(plan_menu, "print_navigation", lambda *_a, **_k: None)
    monkeypatch.setattr(
        plan_menu,
        "save_grouping_from_plan",
        lambda _a, _s, *, group_plan_id: calls.append(group_plan_id),
    )
    selected = SimpleNamespace(
        class_id="synthetic-class",
        activity_id="synthetic-activity",
        group_plan_id="source-plan",
    )
    plan_menu._open_plan(_activity(), selected, _state())
    assert calls == ["source-plan"]


def test_save_menu_reviews_exact_source_and_forwards_digest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _no_ui(monkeypatch)
    events: list[str] = []
    preview = SimpleNamespace(
        name="Six Table Groups",
        groups=_saved().revision.groups,
        unresolved_student_ids=(),
        assigned_count=2,
        review_digest="b" * 64,
    )
    monkeypatch.setattr(
        saved_menu,
        "prepare_save_grouping",
        lambda request: events.append("prepare") or preview,
    )
    monkeypatch.setattr(
        saved_menu, "_show_placements", lambda *_a, **_k: events.append("review")
    )
    monkeypatch.setattr(
        saved_menu, "confirm_write", lambda *_a, **_k: events.append("confirm") or True
    )

    def commit(request: Any, *, review_digest: str) -> Any:
        assert request.class_id == "synthetic-class"
        assert request.activity_id == "synthetic-activity"
        assert request.group_plan_id == "source-plan"
        assert request.expected_snapshot_revision == 8
        assert request.actor.actor_id == "teacher-1"
        assert review_digest == "b" * 64
        events.append("commit")
        return _saved()

    monkeypatch.setattr(saved_menu, "save_grouping", commit)
    saved_menu.save_grouping_from_plan(
        _activity(), _state(), group_plan_id="source-plan"
    )
    assert events == ["prepare", "review", "confirm", "commit"]


def test_save_cancel_never_calls_write(monkeypatch: pytest.MonkeyPatch) -> None:
    _no_ui(monkeypatch)
    monkeypatch.setattr(
        saved_menu,
        "prepare_save_grouping",
        lambda _: SimpleNamespace(
            name="Six Tables",
            groups=_saved().revision.groups,
            unresolved_student_ids=(),
            assigned_count=2,
            review_digest="x" * 64,
        ),
    )
    monkeypatch.setattr(saved_menu, "confirm_write", lambda *_a, **_k: False)
    monkeypatch.setattr(
        saved_menu,
        "save_grouping",
        lambda *_a, **_k: pytest.fail("Cancelled save must not write"),
    )
    saved_menu.save_grouping_from_plan(_activity(), _state(), group_plan_id="p1")


def test_reuse_menu_creates_fresh_draft_with_exact_review_and_standards(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _no_ui(monkeypatch)
    events: list[str] = []
    sentinel = object()
    preview = SimpleNamespace(
        review_digest="c" * 64,
        groups=_saved().revision.groups,
        unresolved_student_ids=(),
        assigned_count=2,
    )
    monkeypatch.setattr(saved_menu, "_select_saved", lambda *_a: _saved())
    monkeypatch.setattr(saved_menu, "list_group_plans", lambda *_a: ())
    monkeypatch.setattr(saved_menu, "_collect_decisions", lambda *_a: ((), ()))
    monkeypatch.setattr(
        saved_menu,
        "prepare_reuse_grouping",
        lambda _: events.append("prepare") or preview,
    )
    monkeypatch.setattr(
        saved_menu, "_preview_reuse", lambda *_a: events.append("review")
    )
    monkeypatch.setattr(
        saved_menu, "confirm_write", lambda *_a, **_k: events.append("confirm") or True
    )
    monkeypatch.setattr(
        saved_menu,
        "standards_kwargs_for_activity",
        lambda _: {"standards_library": sentinel},
    )

    def commit(request: Any, *, review_digest: str, standards_library: object) -> Any:
        assert request.class_id == "synthetic-class"
        assert request.activity_id == "synthetic-activity"
        assert request.arrangement_id == "six-tables"
        assert request.new_group_plan_id != request.arrangement_id
        assert request.expected_snapshot_revision == 8
        assert request.actor.actor_id == "teacher-1"
        assert review_digest == preview.review_digest
        assert standards_library is sentinel
        events.append("commit")
        return SimpleNamespace(
            group_plan_id=request.new_group_plan_id,
            commit=SimpleNamespace(snapshot_revision=9),
        )

    monkeypatch.setattr(saved_menu, "reuse_grouping", commit)
    saved_menu.use_saved_grouping(_activity(), _state())
    assert events == ["prepare", "review", "confirm", "commit"]


def test_reuse_cancel_never_writes(monkeypatch: pytest.MonkeyPatch) -> None:
    _no_ui(monkeypatch)
    monkeypatch.setattr(saved_menu, "_select_saved", lambda *_a: _saved())
    monkeypatch.setattr(saved_menu, "list_group_plans", lambda *_a: ())
    monkeypatch.setattr(saved_menu, "_collect_decisions", lambda *_a: ((), ()))
    monkeypatch.setattr(
        saved_menu,
        "prepare_reuse_grouping",
        lambda _: SimpleNamespace(
            review_digest="d" * 64,
            groups=_saved().revision.groups,
            unresolved_student_ids=(),
            assigned_count=2,
        ),
    )
    monkeypatch.setattr(saved_menu, "_preview_reuse", lambda *_a: None)
    monkeypatch.setattr(saved_menu, "confirm_write", lambda *_a, **_k: False)
    monkeypatch.setattr(
        saved_menu,
        "reuse_grouping",
        lambda *_a, **_k: pytest.fail("Cancelled reuse must not create a plan"),
    )
    saved_menu.use_saved_grouping(_activity(), _state())


def test_reuse_preserves_missing_standards_fail_before_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _no_ui(monkeypatch)
    monkeypatch.setattr(saved_menu, "_select_saved", lambda *_a: _saved())
    monkeypatch.setattr(saved_menu, "list_group_plans", lambda *_a: ())
    monkeypatch.setattr(saved_menu, "_collect_decisions", lambda *_a: ((), ()))
    monkeypatch.setattr(
        saved_menu,
        "prepare_reuse_grouping",
        lambda _: SimpleNamespace(
            review_digest="d" * 64,
            groups=_saved().revision.groups,
            unresolved_student_ids=(),
            assigned_count=2,
        ),
    )
    monkeypatch.setattr(saved_menu, "_preview_reuse", lambda *_a: None)
    monkeypatch.setattr(saved_menu, "confirm_write", lambda *_a, **_k: True)
    monkeypatch.setattr(
        saved_menu,
        "standards_kwargs_for_activity",
        lambda _: (_ for _ in ()).throw(ValueError("Core library missing")),
    )
    shown: list[str] = []
    monkeypatch.setattr(
        saved_menu, "handle_write_error", lambda exc, **_k: shown.append(str(exc))
    )
    monkeypatch.setattr(
        saved_menu,
        "reuse_grouping",
        lambda *_a, **_k: pytest.fail("Missing standards must prevent writes"),
    )
    saved_menu.use_saved_grouping(_activity(), _state())
    assert shown == ["Core library missing"]


def test_select_saved_excludes_retired(monkeypatch: pytest.MonkeyPatch) -> None:
    _no_ui(monkeypatch)
    monkeypatch.setattr(
        saved_menu, "_saved", lambda *_a: (_saved(status="retired"), _saved())
    )
    captured: list[tuple[Any, ...]] = []

    def choose(_title: str, items: Any, labels: Any, **_kw: Any) -> Any:
        captured.append(tuple(items))
        assert len(labels) == 1
        return items[0]

    monkeypatch.setattr(saved_menu, "select_one", choose)
    chosen = saved_menu._select_saved(_activity(), _state())
    assert chosen is not None
    assert chosen.revision.status == "active"
    assert len(captured[0]) == 1


def test_roster_reconciliation_collects_decisions_without_individual_writes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _no_ui(monkeypatch)
    monkeypatch.setattr(saved_menu, "resolve_workspace_root", lambda: "synthetic-root")
    monkeypatch.setattr(
        saved_menu,
        "require_core_class",
        lambda *_a: SimpleNamespace(school_year="2026-2027"),
    )
    monkeypatch.setattr(
        saved_menu,
        "load_required_roster",
        lambda *_a: SimpleNamespace(
            students=(
                SimpleNamespace(student_id="s1"),
                SimpleNamespace(student_id="s3"),
            )
        ),
    )
    monkeypatch.setattr(
        saved_menu,
        "compare_roster",
        lambda *_a, **_k: SimpleNamespace(
            departed_ids=("s2",), newly_enrolled_ids=("s3",), unresolved_ids=()
        ),
    )
    monkeypatch.setattr(
        saved_menu, "_names", lambda *_a: {"s1": "Student One", "s3": "Student Three"}
    )
    confirmations: list[str] = []
    monkeypatch.setattr(
        saved_menu,
        "confirm_write",
        lambda *_a, **_k: confirmations.append("ack") or True,
    )
    monkeypatch.setattr(saved_menu, "select_one", lambda *_a, **_k: "b")
    decisions = saved_menu._collect_decisions(_activity(), _saved())
    assert decisions is not None
    placements, departed = decisions
    assert placements == (StudentPlacementDecision(student_id="s3", group_key="b"),)
    assert departed == ("s2",)
    assert confirmations == ["ack"]
