"""#148 3E6D: qualify preexisting #147 custom action review of bulk GroupPlans.

Synthetic only. No real roster, academic workspace, or local profile is read.
"""

from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from concord import menu_group_plan_bulk as bulk
from concord.menu_context import CancelMenuAction, MenuSessionContext
from concord.teacher_attribution import TeacherAttributionIdentity
from concord.workflows.group_plan_manual import (
    BulkPlannedGroupEditPreview,
    BulkPlannedGroupEditRequest,
    BulkPlannedGroupStudentChange,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = TeacherAttributionIdentity("default-adult", "Default Adult", "saved")
ALTERNATE = TeacherAttributionIdentity(
    "alternate-adult", "Alternate Adult", "temporary"
)


def _state(*, fingerprint: str = "synthetic-fingerprint") -> MenuSessionContext:
    provider = SimpleNamespace(
        resolve_with_fingerprint=lambda: (DEFAULT, fingerprint),
    )
    return MenuSessionContext(
        actor=DEFAULT.workflow_actor(),
        actor_fingerprint=fingerprint,
        attribution_provider=provider,
    )


def _request() -> BulkPlannedGroupEditRequest:
    return BulkPlannedGroupEditRequest(
        class_id="synthetic-class",
        activity_id="synthetic-activity",
        group_plan_id="synthetic-plan",
        planned_group_key="c1",
        operation="place_or_move",
        student_ids=("student-1",),
        expected_snapshot_revision=7,
        expected_record_revision=3,
        actor=DEFAULT.workflow_actor(),
    )


def _preview(request: BulkPlannedGroupEditRequest) -> BulkPlannedGroupEditPreview:
    return BulkPlannedGroupEditPreview(
        class_id=request.class_id,
        activity_id=request.activity_id,
        group_plan_id=request.group_plan_id,
        planned_group_key=request.planned_group_key,
        operation=request.operation,
        snapshot_revision=request.expected_snapshot_revision,
        record_revision=request.expected_record_revision,
        original_status="draft",
        roster_student_ids=("student-1",),
        selected_student_ids=("student-1",),
        changes=(
            BulkPlannedGroupStudentChange(
                student_id="student-1",
                from_group_key=None,
                to_group_key="c1",
            ),
        ),
        unchanged_count=0,
        before_sizes=(("c1", 0),),
        after_sizes=(("c1", 1),),
        unresolved_before=1,
        unresolved_after=0,
        proposed_groups=(),
        review_digest=f"digest-for-{request.actor.actor_id}",
        no_op=False,
    )


def _setup_ui(monkeypatch: pytest.MonkeyPatch, commands: tuple[str, ...]) -> None:
    choices = iter(commands)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(choices))
    monkeypatch.setattr(bulk, "clear_screen", lambda: None)
    monkeypatch.setattr(bulk, "print_menu_header", lambda *_a: None)
    monkeypatch.setattr(bulk, "print_navigation", lambda **_kw: None)
    monkeypatch.setattr(bulk, "pause_for_user", lambda *_a: None)
    monkeypatch.setattr(bulk, "_choose_temporary_actor", lambda: ALTERNATE)


def _review(
    state: MenuSessionContext,
    prepare: Any,
) -> tuple[BulkPlannedGroupEditRequest, BulkPlannedGroupEditPreview] | None:
    detail = SimpleNamespace(
        plan=SimpleNamespace(
            proposed_groups=(SimpleNamespace(planned_group_key="c1", label="One"),)
        )
    )
    request = _request()
    return bulk._review_batch(
        detail,
        _preview(request),
        {"student-1": "Student One"},
        state=state,
        request=request,
        prepare_review=prepare,
    )


def test_existing_bulk_menu_uses_reviewed_request_and_its_digest() -> None:
    """The custom, paginated SAVE BATCH boundary is already actor-reviewed."""
    tree = ast.parse(
        (ROOT / "concord/menu_group_plan_bulk.py").read_text(encoding="utf-8")
    )
    funcs = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    review = funcs["_review_batch"]
    editor = funcs["launch_cluster_bulk_editor"]
    review_calls = [
        call
        for call in ast.walk(review)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Attribute)
        and call.func.attr == "actor_for_action"
    ]
    assert len(review_calls) >= 3
    assert any(
        isinstance(call, ast.Call)
        and isinstance(call.func, ast.Name)
        and call.func.id == "prepare_review"
        for call in ast.walk(review)
    )
    commits = [
        call
        for call in ast.walk(editor)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Name)
        and call.func.id == "commit_bulk_planned_group_edit"
    ]
    assert len(commits) == 1
    commit = commits[0]
    assert isinstance(commit.args[0], ast.Name)
    assert commit.args[0].id == "reviewed_request"
    digest = next(kw.value for kw in commit.keywords if kw.arg == "review_digest")
    assert isinstance(digest, ast.Attribute)
    assert isinstance(digest.value, ast.Name)
    assert digest.value.id == "reviewed_preview"
    assert digest.attr == "review_digest"


@pytest.mark.parametrize(
    ("commands", "expected_actor", "prepares"),
    [
        (("save batch",), "default-adult", ()),
        (("a", "save batch"), "alternate-adult", ("alternate-adult",)),
        (
            ("a", "d", "save batch"),
            "default-adult",
            ("alternate-adult", "default-adult"),
        ),
        (("a", "b"), None, ("alternate-adult",)),
        (("b",), None, ()),
    ],
)
def test_custom_review_is_action_scoped_and_request_digest_paired(
    monkeypatch: pytest.MonkeyPatch,
    commands: tuple[str, ...],
    expected_actor: str | None,
    prepares: tuple[str, ...],
) -> None:
    _setup_ui(monkeypatch, commands)
    state = _state()
    visited: list[str] = []

    def prepare(request: BulkPlannedGroupEditRequest) -> BulkPlannedGroupEditPreview:
        visited.append(request.actor.actor_id)
        return _preview(request)

    result = _review(state, prepare)
    assert tuple(visited) == prepares
    if expected_actor is None:
        assert result is None
    else:
        assert result is not None
        request, preview = result
        assert request.actor.actor_id == expected_actor
        assert request.actor.display_label == (
            "Default Adult" if expected_actor == "default-adult" else "Alternate Adult"
        )
        assert preview.review_digest == f"digest-for-{expected_actor}"
        assert request.student_ids == ("student-1",)
        assert request.expected_snapshot_revision == 7
        assert request.expected_record_revision == 3
    assert state.actor == DEFAULT.workflow_actor()


def test_no_op_after_actor_change_never_returns_commit_pair(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _setup_ui(monkeypatch, ("a",))
    state = _state()
    shown: list[str] = []
    monkeypatch.setattr(
        bulk,
        "show_result",
        lambda title, _lines: shown.append(title),
    )
    assert (
        _review(state, lambda request: replace(_preview(request), no_op=True)) is None
    )
    assert shown == ["Bulk Planning"]
    assert state.actor == DEFAULT.workflow_actor()


def test_changed_profile_fingerprint_cancels_before_batch_commit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _setup_ui(monkeypatch, ("save batch",))
    state = _state()
    checks = 0

    def resolve() -> tuple[TeacherAttributionIdentity, str]:
        nonlocal checks
        checks += 1
        return (
            DEFAULT,
            "synthetic-fingerprint" if checks == 1 else "changed-fingerprint",
        )

    state.attribution_provider = SimpleNamespace(resolve_with_fingerprint=resolve)
    with pytest.raises(CancelMenuAction, match="attribution changed"):
        _review(state, _preview)
    assert checks == 2
    assert state.actor is None  # Cached default invalidated; no alternate persists.
