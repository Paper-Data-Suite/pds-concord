"""#148 3E4B2: digest-bound preset operations use exactly the reviewed actor.

Synthetic menu tests, no actual student records, profile or workspace writes.
"""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from concord import menu_responsibility, menu_role
from concord.menu_context import MenuSessionContext
from concord.workflows.models import WorkflowActor

ROOT = Path(__file__).resolve().parents[1]
CASES = (
    (
        "concord/menu_role.py",
        "_assign",
        "ApplyRolePresetRequest",
        "prepare_role_preset_application",
        "apply_role_preset",
    ),
    (
        "concord/menu_responsibility.py",
        "_assign",
        "ApplyResponsibilityPresetRequest",
        "prepare_responsibility_preset_application",
        "apply_responsibility_preset",
    ),
    (
        "concord/menu_role.py",
        "_save_role_as_preset",
        "SaveRolePresetFromAssignmentRequest",
        "prepare_role_preset_from_assignment",
        "save_role_preset_from_assignment",
    ),
    (
        "concord/menu_responsibility.py",
        "_save_responsibility_as_preset",
        "SaveResponsibilityPresetFromAssignmentRequest",
        "prepare_responsibility_preset_from_assignment",
        "save_responsibility_preset_from_assignment",
    ),
)


def _calls(node: ast.AST, name: str) -> list[ast.Call]:
    return [
        item
        for item in ast.walk(node)
        if isinstance(item, ast.Call)
        and isinstance(item.func, ast.Name)
        and item.func.id == name
    ]


@pytest.mark.parametrize(
    ("path", "operation", "request_type", "prepare", "service"), CASES
)
def test_preset_request_digest_review_remain_in_single_actor_callback(
    path: str, operation: str, request_type: str, prepare: str, service: str
) -> None:
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    fn = next(
        x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == operation
    )
    callbacks = [
        x
        for x in ast.walk(fn)
        if isinstance(x, ast.FunctionDef) and x.name == "_prepare_for_actor"
    ]
    assert len(callbacks) == 1
    callback = callbacks[0]
    assert len(_calls(callback, request_type)) == 1
    assert len(_calls(callback, prepare)) == 1
    assert not _calls(fn, "confirm_write")
    reviews = _calls(fn, "confirm_prepared_actor_write")
    assert len(reviews) == 1
    assert {kw.arg for kw in reviews[0].keywords} >= {
        "state",
        "legacy_confirm",
        "prepare_for_actor",
    }
    assert len(_calls(fn, service)) == 1
    assert not any(
        isinstance(x, ast.Call)
        and isinstance(x.func, ast.Attribute)
        and x.func.attr == "require_actor"
        for x in ast.walk(fn)
    )
    # A service call must use the request and digest unpacked from the same
    # returned review tuple (rather than a separately cached digest).
    write = _calls(fn, service)[0]
    assert isinstance(write.args[0], ast.Name) and write.args[0].id == "request"
    digest = [kw for kw in write.keywords if kw.arg == "review_digest"]
    assert len(digest) == 1
    assert isinstance(digest[0].value, ast.Name)
    assert digest[0].value.id == "review_digest"


@pytest.mark.parametrize(
    ("path", "operation", "request_type", "prepare", "service"), CASES
)
@pytest.mark.parametrize("approved", [True, False])
def test_preset_actor_switch_reprepares_digest_cancel_never_writes(
    monkeypatch: pytest.MonkeyPatch,
    path: str,
    operation: str,
    request_type: str,
    prepare: str,
    service: str,
    approved: bool,
) -> None:
    module: Any = menu_role if path.endswith("menu_role.py") else menu_responsibility
    is_role = path.endswith("menu_role.py")
    is_assign = operation == "_assign"
    default = WorkflowActor(actor_id="teacher-default", display_label="Default Adult")
    alternate = WorkflowActor(
        actor_id="teacher-temporary", display_label="Temporary Adult"
    )
    state = MenuSessionContext(actor=default)
    activity = SimpleNamespace(
        class_id="class-synthetic",
        activity_id="activity-synthetic",
        title="Synthetic Activity",
        snapshot_revision=7,
    )
    monkeypatch.setattr(module, "_latest", lambda _activity: activity)
    monkeypatch.setattr(module, "standards_kwargs_for_activity", lambda *_a: {})
    monkeypatch.setattr(module, "show_result", lambda *_a, **_k: None)
    monkeypatch.setattr(
        module,
        "_handle_error",
        lambda *_a, **_k: pytest.fail("Unexpected workflow exception"),
    )
    monkeypatch.setattr(
        module,
        "confirm_write",
        lambda *_a, **_k: pytest.fail("Legacy confirmation invoked"),
    )
    monkeypatch.setattr(
        module, request_type, lambda **fields: SimpleNamespace(**fields)
    )
    prepared_ids: list[str] = []
    committed: list[tuple[Any, str]] = []

    def fake_prepare(request: Any, **_kwargs: Any) -> Any:
        prepared_ids.append(request.actor.actor_id)
        return SimpleNamespace(
            review_digest="digest:" + request.actor.actor_id,
            preset_name="Saved Role",
            description="Saved Responsibility",
            expected_output=None,
            name="Saved Preset",
            reusable_fields=("Role-only definition",),
            excluded_state=("Student assignment",),
        )

    def fake_commit(request: Any, *, review_digest: str, **_kwargs: Any) -> Any:
        committed.append((request, review_digest))
        return SimpleNamespace(
            preset_id="preset-new",
            role_assignment_id="role-new",
            responsibility_assignment_id="responsibility-new",
            commit=SimpleNamespace(snapshot_revision=8),
        )

    monkeypatch.setattr(module, prepare, fake_prepare)
    monkeypatch.setattr(module, service, fake_commit)

    def fake_action_review(
        title: str,
        token: str,
        *,
        state: MenuSessionContext,
        legacy_confirm: Any,
        prepare_for_actor: Any,
    ) -> Any:
        assert title and token
        assert legacy_confirm is module.confirm_write
        for actor in (default, alternate, default):
            candidate, review_lines = prepare_for_actor(actor)
            request, digest = candidate
            assert request.actor is actor
            assert request.expected_snapshot_revision == 7
            assert digest == "digest:" + actor.actor_id
            assert review_lines and all(isinstance(x, str) for x in review_lines)
        if not approved:
            return None
        return prepare_for_actor(alternate)[0]

    monkeypatch.setattr(module, "confirm_prepared_actor_write", fake_action_review)
    if is_assign:
        monkeypatch.setattr(module, "list_sessions", lambda *_a: ())
        monkeypatch.setattr(
            module,
            "choose_effective_context",
            lambda *_a: SimpleNamespace(session_ids=()),
        )
        if is_role:
            monkeypatch.setattr(
                module, "resolve_workspace_root", lambda: Path("/synthetic")
            )
            monkeypatch.setattr(
                module,
                "choose_student",
                lambda *_a: SimpleNamespace(
                    student_id="student-1", first_name="Student", last_name="One"
                ),
            )
            monkeypatch.setattr(
                module,
                "_choose_role_preset",
                lambda: SimpleNamespace(
                    preset_id="role-preset", preset_revision_id="v1"
                ),
            )
            monkeypatch.setattr(module, "_choose_optional_group", lambda *_a: None)
            monkeypatch.setattr(
                module, "core_student_participant", lambda *_a: object()
            )
        else:
            monkeypatch.setattr(
                module,
                "_choose_assignee",
                lambda *_a: (object(), None, "Student One"),
            )
            monkeypatch.setattr(
                module,
                "_choose_responsibility_preset",
                lambda: SimpleNamespace(
                    preset_id="responsibility-preset", preset_revision_id="v1"
                ),
            )
    else:
        if is_role:
            monkeypatch.setattr(
                module,
                "list_roles",
                lambda *_a: (
                    SimpleNamespace(role_assignment_id="role-1", role_key="recorder"),
                ),
            )
        else:
            monkeypatch.setattr(
                module,
                "list_responsibilities",
                lambda *_a: (
                    SimpleNamespace(
                        responsibility_assignment_id="responsibility-1",
                        description="Take notes",
                    ),
                ),
            )
        monkeypatch.setattr(module, "_choose_existing", lambda items, title: items[0])
        monkeypatch.setattr(
            module,
            "prompt_text",
            lambda _title, name, **_kwargs: (
                "Saved Preset" if "name" in name.lower() else None
            ),
        )
    getattr(module, operation)(activity, state)
    assert prepared_ids == (
        [default.actor_id, alternate.actor_id, default.actor_id]
        + ([alternate.actor_id] if approved else [])
    )
    assert len(committed) == (1 if approved else 0)
    if committed:
        request, digest = committed[0]
        assert request.actor is alternate
        assert digest == "digest:" + alternate.actor_id
        assert request.expected_snapshot_revision == 7
    assert state.actor is default
