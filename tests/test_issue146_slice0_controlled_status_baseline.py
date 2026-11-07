"""#146 controlled-status audit: all six text prompts are now eliminated.

Source-level contract guards are read-only; Slice 1-4 tests separately prove
teacher-menu behavior and canonical service writes in synthetic workspaces.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

# The six original controlled-field defect sites, retained as regression scope.
CONTROLLED_STATUS_SITES = (
    ("concord/menu_activity.py", "_update_activity_field", "Status"),
    ("concord/menu_session.py", "_edit_field", "Status"),
    ("concord/menu_group.py", "_end_member", "End status"),
    ("concord/menu_role.py", "_end", "End status"),
    ("concord/menu_responsibility.py", "_end", "End status"),
    ("concord/menu_group.py", "_edit_group", "Status"),
)


def _parse(path: str) -> ast.Module:
    return ast.parse((ROOT / path).read_text(encoding="utf-8"), filename=path)


def _function(path: str, name: str) -> ast.FunctionDef:
    matches = (
        node
        for node in _parse(path).body
        if isinstance(node, ast.FunctionDef) and node.name == name
    )
    result = next(matches, None)
    assert result is not None, f"Missing menu function: {path}:{name}"
    return result


def _called_name(node: ast.AST) -> str | None:
    if not isinstance(node, ast.Call):
        return None
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def _calls(node: ast.AST, name: str) -> tuple[ast.Call, ...]:
    return tuple(
        sub for sub in ast.walk(node)
        if isinstance(sub, ast.Call) and _called_name(sub) == name
    )


def _literal(node: ast.AST) -> object:
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
        return None


def _controlled_prompt_sites(path: str, function: str, label: str) -> tuple[int, ...]:
    return tuple(
        call.lineno
        for call in _calls(_function(path, function), "prompt_text")
        if len(call.args) >= 2 and _literal(call.args[1]) == label
    )


@pytest.mark.parametrize(("path", "function", "label"), CONTROLLED_STATUS_SITES)
def test_routine_status_uses_a_bounded_choice_not_free_text(
    path: str,
    function: str,
    label: str,
) -> None:
    """All six controlled status prompts must have a numbered chooser."""
    lines = _controlled_prompt_sites(path, function, label)
    assert not lines, f"Free-text status remains at {path}:{lines}"


@pytest.mark.parametrize(
    ("path", "function", "helper"),
    (
        ("concord/menu_activity.py", "_choose_scoring_orientation", "select_one"),
        ("concord/menu_scoring.py", "_choose_disposition", "_choose_enum"),
        ("concord/menu_artifact.py", "_author_status", "select_one"),
        ("concord/menu_artifact.py", "_representation_status", "select_one"),
        (
            "concord/menu_group_plan_missing_signal.py",
            "resolve_missing_signal_from_menu",
            "select_one",
        ),
    ),
)
def test_existing_numbered_choices_must_not_be_rewritten(
    path: str,
    function: str,
    helper: str,
) -> None:
    assert _calls(_function(path, function), helper), (
        f"Existing controlled choice is missing: {path}:{function}"
    )


def _model_status_values(name: str) -> frozenset[str]:
    tree = _parse("concord/models/collaboration.py")
    cls = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == name
    )
    method = next(
        node for node in cls.body
        if isinstance(node, ast.FunctionDef) and node.name == "__post_init__"
    )
    statuses = tuple(
        call.args[2]
        for call in _calls(method, "controlled")
        if len(call.args) == 3 and _literal(call.args[1]) == "status"
    )
    assert len(statuses) == 1, f"Expected one canonical status field on {name}"
    expr = statuses[0]
    assert isinstance(expr, ast.Call) and _called_name(expr) == "frozenset"
    assert len(expr.args) == 1
    values = _literal(expr.args[0])
    assert isinstance(values, set)
    return frozenset(values)


@pytest.mark.parametrize(
    ("model", "expected"),
    (
        (
            "Activity",
            {"draft", "configured", "active", "completed", "cancelled", "archived"},
        ),
        (
            "Session",
            {"planned", "active", "completed", "cancelled", "interrupted", "archived"},
        ),
        (
            "Group",
            {
                "planned", "active", "inactive", "completed", "cancelled",
                "archived", "superseded",
            },
        ),
    ),
)
def test_source_model_status_values_are_authoritative(
    model: str,
    expected: set[str],
) -> None:
    assert _model_status_values(model) == expected


def test_assignment_end_status_is_a_separate_canonical_subset() -> None:
    tree = _parse("concord/workflows/_collaboration.py")
    candidates = (
        node.value for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name)
            and target.id == "END_ASSIGNMENT_STATUSES"
            for target in node.targets
        )
    )
    expression = next(candidates, None)
    assert isinstance(expression, ast.Call)
    assert _called_name(expression) == "frozenset"
    assert len(expression.args) == 1
    assert _literal(expression.args[0]) == {"completed", "withdrawn", "cancelled"}


def test_activity_edit_keeps_merged_standards_context_guard() -> None:
    node = _function("concord/menu_activity.py", "_update_activity_field")
    for helper in (
        "_load_activity_context",
        "load_menu_standards_library",
        "update_activity",
        "confirm_write",
    ):
        assert _calls(node, helper), f"Lost Activity write guard: {helper}"
    assert any(
        keyword.arg == "standards_library"
        for call in _calls(node, "update_activity")
        for keyword in call.keywords
    )


def test_group_plan_still_has_separate_preview_approve_apply_cancel() -> None:
    content = (ROOT / "concord/menu_group_plan.py").read_text(encoding="utf-8")
    for handler in (
        "_preview(detail, state)",
        "_approve(detail, state)",
        "_cancel(detail, state)",
        "apply_approved_group_plan_from_menu(detail, state)",
    ):
        assert handler in content, f"Lost plan-stage action: {handler}"


@pytest.mark.parametrize(
    ("path", "function"),
    (
        ("concord/menu_activity.py", "_update_activity_field"),
        ("concord/menu_session.py", "_edit_field"),
        ("concord/menu_group.py", "_end_member"),
        ("concord/menu_role.py", "_end"),
        ("concord/menu_responsibility.py", "_end"),
        ("concord/menu_group.py", "_edit_group"),
    ),
)
def test_current_write_surfaces_have_review_gate(path: str, function: str) -> None:
    """The new choosers must not discard the existing confirmation boundary."""
    assert _calls(_function(path, function), "confirm_write")
