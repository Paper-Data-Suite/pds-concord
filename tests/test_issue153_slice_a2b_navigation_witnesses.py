"""#153 A2b: bounded failing-before witnesses for local navigation."""

from __future__ import annotations

from collections.abc import Callable
from types import SimpleNamespace

import pytest

import concord.menu_activity as activity_menu
import concord.menu_attention as attention_menu
import concord.menu_responsibility as responsibility_menu
import concord.menu_role as role_menu
from concord.menu_context import CancelMenuAction
from concord.menu_navigation import QuitPDS, ReturnToMainMenu
from concord.workflows import ActivitySummary
from concord.workflows.activity_attention import ActivityAttentionSummary

SELECTORS = ("activity", "role", "responsibility")


class RecursiveRetryDetected(AssertionError):
    """A local selector reentered itself instead of redrawing in place."""


class HelpClearedBeforeAcknowledgement(AssertionError):
    """A help message disappeared before the next input boundary."""


def _selector(
    monkeypatch: pytest.MonkeyPatch, name: str
) -> tuple[Callable[[], object], object]:
    activity = ActivitySummary(
        class_id="class-1",
        activity_id="activity-1",
        title="Synthetic Activity",
        status="draft",
        scoring_orientation="evidence_only",
        session_count=1,
        group_count=1,
        snapshot_revision=1,
    )
    group = SimpleNamespace(group_id="group-1", label="Cluster A")
    if name == "activity":
        module = activity_menu
        attribute = "_choose_activity_type"
        args = ()
        expected = tuple(activity_menu._ACTIVITY_TYPES)[0]
    elif name == "role":
        module = role_menu
        attribute = "_choose_optional_group"
        args = (activity,)
        expected = None
        monkeypatch.setattr(module, "list_groups", lambda *_a: (group,))
    else:
        module = responsibility_menu
        attribute = "_choose_assignee"
        args = (activity,)
        expected = (
            responsibility_menu.group_record_reference(group.group_id),
            group.group_id,
            group.label,
        )
        monkeypatch.setattr(module, "list_groups", lambda *_a: (group,))
        monkeypatch.setattr(module, "choose_group", lambda *_a, **_k: group)
    monkeypatch.setattr(module, "clear_screen", lambda: None)
    original = getattr(module, attribute)

    def reject_reentry(*_args: object) -> object:
        raise RecursiveRetryDetected(attribute)

    monkeypatch.setattr(module, attribute, reject_reentry)
    return lambda: original(*args), expected


@pytest.mark.xfail(
    strict=True,
    raises=RecursiveRetryDetected,
    reason="A2b: confirmed recursive Help/invalid-input retry path",
)
@pytest.mark.parametrize("selector", SELECTORS)
@pytest.mark.parametrize("retry", ("h", "invalid"))
def test_selector_retry_keeps_one_controller_frame(
    monkeypatch: pytest.MonkeyPatch, selector: str, retry: str
) -> None:
    run, expected = _selector(monkeypatch, selector)
    valid = "2" if selector == "responsibility" else "1"
    values = iter((retry, "", valid))
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(values))
    assert run() == expected


@pytest.mark.parametrize("selector", SELECTORS)
def test_selector_initial_choice_is_unchanged(
    monkeypatch: pytest.MonkeyPatch, selector: str
) -> None:
    run, expected = _selector(monkeypatch, selector)
    valid = "2" if selector == "responsibility" else "1"
    monkeypatch.setattr("builtins.input", lambda _prompt="": valid)
    assert run() == expected


@pytest.mark.parametrize("selector", SELECTORS)
@pytest.mark.parametrize(
    ("choice", "error"),
    (("b", CancelMenuAction), ("m", ReturnToMainMenu), ("q", QuitPDS)),
)
def test_selector_navigation_preserves_existing_unwind(
    monkeypatch: pytest.MonkeyPatch, selector: str, choice: str, error: type[Exception]
) -> None:
    run, _expected = _selector(monkeypatch, selector)
    monkeypatch.setattr("builtins.input", lambda _prompt="": choice)
    with pytest.raises(error):
        run()


@pytest.mark.xfail(
    strict=True,
    raises=HelpClearedBeforeAcknowledgement,
    reason="A2b: attention Help is cleared before acknowledgement",
)
def test_attention_help_remains_visible_until_input(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    clear = "<<<CLEAR>>>"
    help_text = "This view is read-only. Use N/P to page and B to return."
    values = iter(("h", "b"))

    def read(_prompt: str = "") -> str:
        output = capsys.readouterr().out
        if help_text in output and clear in output.split(help_text, 1)[1]:
            raise HelpClearedBeforeAcknowledgement
        return next(values)

    monkeypatch.setattr(attention_menu, "clear_screen", lambda: print(clear))
    monkeypatch.setattr("builtins.input", read)
    summary = ActivityAttentionSummary(
        class_id="class-1", activity_id="activity-1", title="Synthetic Activity"
    )
    attention_menu.launch_activity_attention_details(summary)
