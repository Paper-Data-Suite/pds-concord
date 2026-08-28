from __future__ import annotations

from collections.abc import Iterator

import pytest

import concord.menu as menu_module
import concord.menu_activity as activity_module
import concord.menu_ui as ui_module
from concord.menu_navigation import (
    ConcordMenuChoice,
    NavigationChoice,
    navigation_hint_with_help,
    navigation_labels_with_help,
    parse_menu_navigation,
)
from concord.menu_ui import page_count, page_items
from concord.workflows import ActivitySummary


def _inputs(monkeypatch: pytest.MonkeyPatch, values: list[str]) -> None:
    iterator: Iterator[str] = iter(values)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(iterator))


def test_navigation_uses_help_plus_core_semantics() -> None:
    assert parse_menu_navigation("h") is ConcordMenuChoice.HELP
    assert parse_menu_navigation("B") is NavigationChoice.BACK
    assert navigation_labels_with_help() == (
        "H. Help",
        "B. Back",
        "M. Main Menu",
        "Q. Quit",
    )
    assert navigation_labels_with_help(back=False, main_menu=False) == (
        "H. Help",
        "Q. Quit",
    )
    assert navigation_hint_with_help(back=False, main_menu=False) == (
        "Please choose a listed option, H or Q."
    )


def test_main_menu_shows_no_back_or_main_menu(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _inputs(monkeypatch, ["q"])
    monkeypatch.setattr(menu_module, "clear_screen", lambda: None)
    assert menu_module.launch_menu() == 0
    output = capsys.readouterr().out
    assert "H. Help" in output
    assert "Q. Quit" in output
    assert "B. Back" not in output
    assert "M. Main Menu" not in output


def test_help_returns_to_same_main_menu(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _inputs(monkeypatch, ["h", "", "q"])
    clears: list[str] = []
    monkeypatch.setattr(menu_module, "clear_screen", lambda: clears.append("clear"))
    assert menu_module.launch_menu() == 0
    output = capsys.readouterr().out
    assert output.count("1. Activity Management") == 2
    assert "Complete direct command help:" in output
    assert len(clears) >= 3


def test_activity_selection_pages_after_ten_items() -> None:
    values = tuple(range(23))
    assert page_count(len(values)) == 3
    assert page_items(values, 0) == tuple(range(10))
    assert page_items(values, 1) == tuple(range(10, 20))
    assert page_items(values, 2) == tuple(range(20, 23))


def test_activity_context_keeps_only_compact_parent_header(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    activity = ActivitySummary(
        class_id="class-1",
        activity_id="activity-1",
        title="Seminar One",
        status="draft",
        scoring_orientation="evidence_only",
        session_count=2,
        group_count=3,
        snapshot_revision=4,
    )
    _inputs(monkeypatch, ["b"])
    monkeypatch.setattr(activity_module, "clear_screen", lambda: None)
    activity_module.launch_activity_context_menu(activity)
    output = capsys.readouterr().out
    assert "Activity: Seminar One" in output
    assert "1. Plan" in output
    assert "6. Share" in output
    assert "7. Advanced Activity tools" in output
    assert "Class: class-1" not in output
    assert "Status: draft" not in output
    assert "Snapshot: 4" not in output
    assert "Scoring: evidence_only" not in output


def test_clear_screen_is_suppressed_for_captured_streams(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(ui_module.sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr(ui_module.sys.stdout, "isatty", lambda: False)
    monkeypatch.setattr(ui_module.os, "system", lambda command: calls.append(command))
    ui_module.clear_screen()
    assert calls == []
