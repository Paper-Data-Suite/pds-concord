"""#148 Slice 4B Repair 1: legacy provider-shaped review contexts remain valid.

All actor identities are synthetic. No workspace or profile files are accessed.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import cast

import pytest

import concord.menu_actor_action as actor_action
from concord.menu_context import MenuSessionContext
from concord.teacher_attribution import TeacherAttributionIdentity
from concord.workflows import WorkflowActor


class _ProviderShapedContext:
    """Intentionally no actor or actor_fingerprint attributes."""

    attribution_provider = object()

    def __init__(self) -> None:
        self.calls: list[str] = []
        self.default = WorkflowActor(
            actor_id="adult-default", display_label="Default Adult"
        )

    def actor_for_action(
        self,
        *,
        action_label: str,
        alternate: TeacherAttributionIdentity | None = None,
    ) -> WorkflowActor:
        self.calls.append(action_label)
        return self.default if alternate is None else alternate.workflow_actor()

    def require_actor(self) -> WorkflowActor:
        return self.default


def _ui(monkeypatch: pytest.MonkeyPatch, answers: list[str]) -> None:
    monkeypatch.setattr(actor_action, "clear_screen", lambda: None)
    monkeypatch.setattr(actor_action, "print_menu_header", lambda *_a: None)
    monkeypatch.setattr(actor_action, "print_navigation", lambda: None)
    monkeypatch.setattr(actor_action, "show_result", lambda *_a: None)
    monkeypatch.setattr("builtins.input", lambda _p="": answers.pop(0))
    monkeypatch.setattr(
        actor_action,
        "_choose_temporary_actor",
        lambda: TeacherAttributionIdentity(
            "adult-alternate", "Other Adult", "temporary"
        ),
    )


@pytest.mark.parametrize(
    ("choices", "expected_id"),
    [
        (["SAVE"], "adult-default"),
        (["a", "SAVE"], "adult-alternate"),
        (["a", "d", "SAVE"], "adult-default"),
        ([""], None),
    ],
)
def test_existing_review_context_requires_no_cache_attributes(
    monkeypatch: pytest.MonkeyPatch, choices: list[str], expected_id: str | None
) -> None:
    state = _ProviderShapedContext()
    _ui(monkeypatch, choices)
    selected = actor_action.confirm_actor_write(
        "Synthetic exact review",
        "SAVE",
        ("Target: synthetic",),
        state=cast(MenuSessionContext, state),
        legacy_confirm=lambda *_a: pytest.fail("Legacy confirmation bypass"),
    )
    assert (selected.actor_id if selected is not None else None) == expected_id
    assert state.calls
    assert state.default.actor_id == "adult-default"


def test_existing_prepared_context_rebinds_alternate_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = _ProviderShapedContext()
    _ui(monkeypatch, ["a", "COMMIT"])
    prepared_for: list[str] = []

    def prepare(
        actor: WorkflowActor,
    ) -> tuple[SimpleNamespace, tuple[str, ...]]:
        prepared_for.append(actor.actor_id)
        return SimpleNamespace(request=SimpleNamespace(actor=actor)), (
            f"Reviewed actor: {actor.actor_id}",
        )

    result = actor_action.confirm_prepared_actor_write(
        "Synthetic prepared write",
        "COMMIT",
        state=cast(MenuSessionContext, state),
        legacy_confirm=lambda *_a: pytest.fail("Legacy confirmation bypass"),
        prepare_for_actor=prepare,
    )
    assert result is not None
    assert result.request.actor.actor_id == "adult-alternate"
    assert prepared_for == ["adult-default", "adult-alternate"]
    assert state.default.actor_id == "adult-default"
