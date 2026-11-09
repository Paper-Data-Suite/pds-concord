"""Issue #148 Slice 3B1: bounded reviewed GroupPlan actor callsites.

All input is synthetic. The source contract tests cover every adopted path;
the service tests assert that the reviewed actor, not the cached default,
is what reaches the existing immutable GroupPlan lifecycle request.
"""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import concord.menu_group_plan as menu
from concord.workflows import WorkflowActor

ROOT = Path(__file__).resolve().parents[1]
TARGETS = (
    ("concord/menu_group_plan.py", "_create_random", "CreateRandomGroupPlanRequest"),
    (
        "concord/menu_group_plan.py",
        "_import_arrangement",
        "ImportArrangementGroupPlanRequest",
    ),
    ("concord/menu_group_plan.py", "_add_group", "AddPlannedGroupRequest"),
    ("concord/menu_group_plan.py", "_edit_group", "EditPlannedGroupRequest"),
    ("concord/menu_group_plan.py", "_remove_group", "RemovePlannedGroupRequest"),
    ("concord/menu_group_plan.py", "_place_student", "PlaceStudentInPlanRequest"),
    (
        "concord/menu_group_plan.py",
        "_unassign_student",
        "UnassignStudentFromPlanRequest",
    ),
    ("concord/menu_group_plan.py", "_refresh_roster", "RefreshGroupPlanRosterRequest"),
    (
        "concord/menu_group_plan.py",
        "_replace_arrangement",
        "ReplaceArrangementGroupPlanRequest",
    ),
    ("concord/menu_group_plan.py", "_preview", "PreviewGroupPlanRequest"),
    ("concord/menu_group_plan.py", "_approve", "ApproveGroupPlanRequest"),
    ("concord/menu_group_plan.py", "_cancel", "CancelGroupPlanRequest"),
    (
        "concord/menu_group_plan_signal.py",
        "create_signal_group_plan_from_menu",
        "CreateSignalGroupPlanRequest",
    ),
    (
        "concord/menu_group_plan_application.py",
        "apply_approved_group_plan_from_menu",
        "ApplyGroupPlanRequest",
    ),
)


def _calls(node: ast.AST, name: str) -> list[ast.Call]:
    return [
        child
        for child in ast.walk(node)
        if isinstance(child, ast.Call)
        and isinstance(child.func, ast.Name)
        and child.func.id == name
    ]


@pytest.mark.parametrize(("path", "function", "request_name"), TARGETS)
def test_one_reviewed_actor_reaches_exact_groupplan_write(
    path: str, function: str, request_name: str
) -> None:
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"), filename=path)
    functions = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == function
    ]
    assert len(functions) == 1, (path, function)
    func = functions[0]
    reviews = _calls(func, "confirm_actor_write")
    requests = _calls(func, request_name)
    assert len(reviews) == len(requests) == 1, (path, function)
    assert not _calls(func, "confirm_write"), (path, function)
    review = reviews[0]
    assert {item.arg for item in review.keywords} == {"state", "legacy_confirm"}
    assert isinstance(review.keywords[0].value, ast.Name)
    assert review.keywords[0].value.id == "state"
    assert isinstance(review.keywords[1].value, ast.Name)
    assert review.keywords[1].value.id == "confirm_write"
    actor_keywords = [kw for kw in requests[0].keywords if kw.arg == "actor"]
    assert len(actor_keywords) == 1
    assert isinstance(actor_keywords[0].value, ast.Name)
    assert actor_keywords[0].value.id == "actor"
    require_actor = [
        node
        for node in ast.walk(func)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "require_actor"
    ]
    assert not require_actor, (path, function)
    # No service invocation can precede the confirmation's cancellation gate.
    reviews_assignments = [
        node
        for node in ast.walk(func)
        if isinstance(node, ast.Assign) and node.value is review
    ]
    assert len(reviews_assignments) == 1
    gates = [
        node
        for node in ast.walk(func)
        if isinstance(node, ast.If)
        and isinstance(node.test, ast.Compare)
        and isinstance(node.test.left, ast.Name)
        and node.test.left.id == "actor"
        and len(node.test.ops) == 1
        and isinstance(node.test.ops[0], ast.Is)
        and len(node.test.comparators) == 1
        and isinstance(node.test.comparators[0], ast.Constant)
        and node.test.comparators[0].value is None
    ]
    assert len(gates) == 1
    assert reviews_assignments[0].lineno < gates[0].lineno < requests[0].lineno
    assert len(gates[0].body) == 1 and isinstance(gates[0].body[0], ast.Return)


@pytest.mark.parametrize(
    ("operation", "service_name"),
    (("_approve", "approve_group_plan"), ("_cancel", "cancel_group_plan")),
)
def test_lifecycle_service_receives_exact_reviewed_alternate(
    monkeypatch: pytest.MonkeyPatch, operation: str, service_name: str
) -> None:
    alternate = WorkflowActor(actor_id="adult-alternate", display_label="Alternate")
    observed: list[WorkflowActor] = []
    detail = SimpleNamespace(
        summary=SimpleNamespace(
            class_id="synthetic-class",
            activity_id="synthetic-activity",
            group_plan_id="synthetic-plan",
            snapshot_revision=4,
        ),
        plan=SimpleNamespace(group_plan_id="synthetic-plan"),
    )
    state = SimpleNamespace(require_actor=lambda: pytest.fail("stale actor resolved"))
    monkeypatch.setattr(menu, "confirm_actor_write", lambda *args, **kw: alternate)
    monkeypatch.setattr(menu, "standards_kwargs_for_plan", lambda _: {})
    monkeypatch.setattr(menu, "show_result", lambda *args: None)

    def service(request: Any, **kwargs: Any) -> Any:
        assert not kwargs
        observed.append(request.actor)
        return SimpleNamespace(
            status="approved" if operation == "_approve" else "cancelled",
            commit=SimpleNamespace(snapshot_revision=5),
        )

    monkeypatch.setattr(menu, service_name, service)
    getattr(menu, operation)(detail, state)
    assert observed == [alternate]


@pytest.mark.parametrize(
    ("operation", "service_name"),
    (("_approve", "approve_group_plan"), ("_cancel", "cancel_group_plan")),
)
def test_cancelled_lifecycle_review_never_dispatches(
    monkeypatch: pytest.MonkeyPatch, operation: str, service_name: str
) -> None:
    detail = SimpleNamespace(
        summary=SimpleNamespace(
            class_id="synthetic-class",
            activity_id="synthetic-activity",
            group_plan_id="synthetic-plan",
            snapshot_revision=4,
        ),
        plan=SimpleNamespace(group_plan_id="synthetic-plan"),
    )
    monkeypatch.setattr(menu, "confirm_actor_write", lambda *args, **kw: None)
    monkeypatch.setattr(
        menu,
        service_name,
        lambda *args, **kw: pytest.fail("cancelled review dispatched a write"),
    )
    getattr(menu, operation)(detail, SimpleNamespace())
