"""#153 C2: feedback visibility and explicit selection scope."""

from __future__ import annotations

import pytest

import concord.menu_attention as attention_menu
import concord.menu_prompts as prompts
from concord.workflows.activity_attention import (
    ActivityAttentionItem,
    ActivityAttentionSummary,
)

CLEAR = "<<<CLEAR>>>"


def _summary() -> ActivityAttentionSummary:
    return ActivityAttentionSummary(
        class_id="class-1",
        activity_id="activity-1",
        title="Synthetic Activity",
        items=tuple(
            ActivityAttentionItem(
                code=f"item-{index}",
                label=f"Category {index}",
                task="prepare",
                count=1,
                action_id="open_activity_prepare",
            )
            for index in range(12)
        ),
    )


def test_attention_feedback_redraw_retains_page(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(attention_menu, "clear_screen", lambda: print(CLEAR))
    values = iter(("n", "h", "invalid", "p", "b"))
    screens: list[str] = []

    def read(_prompt: str = "") -> str:
        screens.append(capsys.readouterr().out.split(CLEAR)[-1])
        return next(values)

    monkeypatch.setattr("builtins.input", read)
    attention_menu.launch_activity_attention_details(_summary())
    assert len(screens) == 5
    assert "Page 1 of 2" in screens[0]
    for screen in screens[1:4]:
        assert "Page 2 of 2" in screen
        assert "Category 11" in screen
        assert "Category 0" not in screen
    assert "This view is read-only." in screens[2]
    assert "Use N/P for pages, B to return, or H for help." in screens[3]
    assert "Page 1 of 2" in screens[4]
    assert "This view is read-only." not in screens[4]


@pytest.mark.parametrize("view", ("attention", "readiness"))
def test_unavailable_read_only_feedback_stays_visible(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    view: str,
) -> None:
    monkeypatch.setattr(attention_menu, "clear_screen", lambda: print(CLEAR))
    values = iter(("h", "invalid", "b"))
    screens: list[str] = []

    def read(_prompt: str = "") -> str:
        screens.append(capsys.readouterr().out)
        return next(values)

    monkeypatch.setattr("builtins.input", read)
    if view == "attention":
        attention_menu.launch_activity_attention_details(None)
    else:
        attention_menu.launch_activity_prelesson_readiness(None)
    assert len(screens) == 3
    assert "unavailable" in screens[0]
    assert "read-only Concord snapshot facts" in screens[1]
    assert "Enter B to return or H for help." in screens[2]
    assert all(CLEAR not in screen for screen in screens[1:])


def test_generic_select_all_explicitly_includes_every_page(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    items = tuple(range(12))
    labels = tuple(f"Item {index}" for index in items)
    values = iter(("n", "h", "", "a", "d"))
    monkeypatch.setattr(prompts, "clear_screen", lambda: print(CLEAR))
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(values))
    assert prompts.select_many(
        "Choose Items", items, labels, help_text="Choose items."
    ) == items
    output = capsys.readouterr().out
    assert "A. Select all items across every page" in output
    assert "A selects all items across every page, not just this page." in output
    assert "Selected: 12" in output
