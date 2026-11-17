"""#149 Slice 1: applied-plan provenance, status and roster guard regressions.

These tests use synthetic in-memory state and a fake Core roster read.
No classroom workspace, profile, or academic data is opened.
"""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

import pytest

import concord.workflows.activity_attention as attention
from concord.group_plan_application import derive_group_id, derive_membership_id


def _activity_case(
    *,
    roster_count: int = 29,
    omit_membership: bool = False,
    group_status: str = "planned",
    membership_status: str = "active",
    additional_applied: bool = False,
) -> tuple[SimpleNamespace, tuple[str, ...]]:
    roster_ids = tuple(f"student-{i:02d}" for i in range(roster_count))
    group_specs = tuple(
        SimpleNamespace(
            planned_group_key=f"cluster-{i}",
            student_ids=roster_ids[i::6],
        )
        for i in range(6)
    )
    app_id = "apply-main"
    plan_id = "plan-main"
    applied = SimpleNamespace(
        status="applied",
        group_plan_id=plan_id,
        applied_application_id=app_id,
        proposed_groups=group_specs,
        roster_student_ids=roster_ids,
    )
    draft = SimpleNamespace(
        status="draft",
        strategy="manual",
        unresolved_student_ids=("draft-only",),
        missing_signal_disposition=None,
    )
    plans: tuple[object, ...] = (applied, draft)
    if additional_applied:
        plans += (SimpleNamespace(status="applied"),)
    groups = tuple(
        SimpleNamespace(
            group_id=derive_group_id(app_id, plan_id, g.planned_group_key),
            status=group_status,
        )
        for g in group_specs
    )
    members = tuple(
        SimpleNamespace(
            membership_id=derive_membership_id(
                app_id, plan_id, g.planned_group_key, student_id
            ),
            group_id=derive_group_id(app_id, plan_id, g.planned_group_key),
            status=membership_status,
            participant_reference=SimpleNamespace(
                participant_kind="core_student",
                owning_system="core",
                participant_id=student_id,
            ),
        )
        for g in group_specs
        for student_id in g.student_ids
    )
    if omit_membership:
        members = members[:-1]
    return SimpleNamespace(
        root=Path("synthetic-not-opened"),
        work=SimpleNamespace(class_id="class-synthetic", work_id="activity"),
        graph=SimpleNamespace(group_plans=plans, groups=groups, memberships=members),
    ), roster_ids


def _mock_roster(
    monkeypatch: pytest.MonkeyPatch, roster_ids: tuple[str, ...]
) -> list[str]:
    seen: list[str] = []

    def load(_root: Path, class_id: str) -> SimpleNamespace:
        seen.append(class_id)
        return SimpleNamespace(
            students=tuple(SimpleNamespace(student_id=x) for x in roster_ids)
        )

    monkeypatch.setattr(attention, "load_required_roster", load)
    return seen


def test_exact_current_operational_plan_suppresses_unused_draft(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context, roster = _activity_case()
    seen = _mock_roster(monkeypatch, roster)
    assert attention._plan_attention_counts_from_context(context) == {}
    assert seen == ["class-synthetic"]


@pytest.mark.parametrize(
    ("case", "kwargs"),
    [
        ("missing-member", {"omit_membership": True}),
        ("inactive-member", {"membership_status": "completed"}),
        ("inactive-group", {"group_status": "cancelled"}),
        ("ambiguous-applications", {"additional_applied": True}),
    ],
)
def test_stale_or_ambiguous_application_does_not_suppress_real_plan_attention(
    monkeypatch: pytest.MonkeyPatch, case: str, kwargs: dict[str, object]
) -> None:
    context, roster = _activity_case(**kwargs)  # type: ignore[arg-type]
    _mock_roster(monkeypatch, roster)
    counts = attention._plan_attention_counts_from_context(context)
    assert counts == {
        "concord_plan_prepare": 1,
        "concord_plan_unresolved_placements": 1,
    }, case


def test_extra_operational_group_membership_prevents_false_ready(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context, roster = _activity_case()
    _mock_roster(monkeypatch, roster)
    context.graph.memberships += (
        SimpleNamespace(
            membership_id="membership-unrelated",
            group_id="unrelated-operational-group",
            status="active",
        ),
    )
    assert attention._plan_attention_counts_from_context(context) == {
        "concord_plan_prepare": 1,
        "concord_plan_unresolved_placements": 1,
    }


def test_changed_core_roster_does_not_count_old_applied_plan_as_current(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context, roster = _activity_case()
    _mock_roster(monkeypatch, roster[:-1])
    assert attention._plan_attention_counts_from_context(context) == {
        "concord_plan_prepare": 1,
        "concord_plan_unresolved_placements": 1,
    }


def test_unverifiable_core_roster_propagates_unavailable_instead_of_guessing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context, _ = _activity_case()

    def unavailable(*_args: object) -> None:
        raise OSError("synthetic permission denial")

    monkeypatch.setattr(attention, "load_required_roster", unavailable)
    with pytest.raises(OSError, match="synthetic permission"):
        attention._plan_attention_counts_from_context(context)


def test_cancel_is_the_existing_explicit_cas_service_not_a_read_side_effect() -> None:
    root = Path(__file__).resolve().parents[1]
    menu = ast.parse((root / "concord/menu_group_plan.py").read_text(encoding="utf-8"))
    fn = next(
        node
        for node in menu.body
        if isinstance(node, ast.FunctionDef) and node.name == "_cancel"
    )
    called = [
        node.func.id
        for node in ast.walk(fn)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    ]
    assert "confirm_actor_write" in called
    assert "CancelGroupPlanRequest" in called
    assert "cancel_group_plan" in called
    source = (root / "concord/workflows/activity_attention.py").read_text(
        encoding="utf-8"
    )
    assert "cancel_group_plan(" not in source
