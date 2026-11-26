"""#153 E2b: Activity summary and status picker technical disclosure."""

from __future__ import annotations

import pytest

import concord.menu_activity as menu
import concord.menu_prompts as prompts
from concord.menu_context import CancelMenuAction
from concord.menu_navigation import QuitPDS, ReturnToMainMenu
from concord.workflows import ActivityDetail, ActivitySummary, ConcordWorkflowError

SUMMARY = ActivitySummary(
    class_id="class-1",
    activity_id="discussion-2",
    title="Discussion",
    status="draft",
    scoring_orientation="evidence_only",
    session_count=2,
    group_count=3,
    snapshot_revision=7,
)
DETAIL = ActivityDetail(
    summary=SUMMARY,
    description="Read the passage.",
    activity_type="project",
    standards_profile_id=None,
    focus_standard_ids=(),
)


def _screens(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    choices: tuple[str, ...],
) -> list[str]:
    answers = iter(choices)
    screens: list[str] = []

    def read(_prompt: str = "") -> str:
        screens.append(capsys.readouterr().out)
        return next(answers)

    monkeypatch.setattr("builtins.input", read)
    return screens


def test_summary_details_uses_same_verified_read(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    reads: list[tuple[str, str]] = []

    def load(class_id: str, activity_id: str) -> ActivityDetail:
        reads.append((class_id, activity_id))
        return DETAIL

    monkeypatch.setattr(menu, "show_activity", load)
    screens = _screens(monkeypatch, capsys, ("t", "b", ""))
    menu._print_summary(SUMMARY)
    assert reads == [("class-1", "discussion-2")]
    assert len(screens) == 3
    assert screens[0] == screens[2]
    assert "Activity: Discussion" in screens[0]
    assert "Activity ID: discussion-2" in screens[0]
    assert "Class: class-1" in screens[0]
    assert "Sessions: 2" in screens[0]
    assert "Groups: 3" in screens[0]
    assert "Description: Read the passage." in screens[0]
    assert "Snapshot:" not in screens[0]
    assert "Snapshot: 7" in screens[1]
    assert "Activity ID: discussion-2" in screens[1]


def test_status_details_returns_to_exact_numbered_choices(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    screens = _screens(monkeypatch, capsys, ("t", "", "2"))
    assert menu._choose_activity_status(SUMMARY) == "configured"
    assert screens[0] == screens[2]
    assert "Current status: draft" in screens[0]
    assert "Activity ID: discussion-2" in screens[0]
    assert "Snapshot:" not in screens[0]
    assert "Snapshot: 7" in screens[1]
    assert "1. Draft" in screens[0]
    assert "[current]" in screens[0]
    assert "2. Configured" in screens[0]
    assert "2. Configured" not in screens[1]


@pytest.mark.parametrize("surface", ("summary", "status"))
@pytest.mark.parametrize("choice", ("m", "q"))
@pytest.mark.parametrize("technical", (False, True))
def test_activity_details_navigation_unwinds(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    surface: str,
    choice: str,
    technical: bool,
) -> None:
    monkeypatch.setattr(menu, "show_activity", lambda *_a: DETAIL)
    screens = _screens(monkeypatch, capsys, ("t", choice) if technical else (choice,))
    error = ReturnToMainMenu if choice == "m" else QuitPDS
    with pytest.raises(error):
        if surface == "summary":
            menu._print_summary(SUMMARY)
        else:
            menu._choose_activity_status(SUMMARY)
    assert len(screens) == (2 if technical else 1)


def test_status_back_from_details_then_picker_cancels(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    screens = _screens(monkeypatch, capsys, ("t", "b", "b"))
    with pytest.raises(CancelMenuAction):
        menu._choose_activity_status(SUMMARY)
    assert len(screens) == 3


def test_unavailable_summary_redacts_exception(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fail(*_a: object) -> ActivityDetail:
        raise ConcordWorkflowError("/private/student/workspace")

    monkeypatch.setattr(menu, "show_activity", fail)
    screens = _screens(monkeypatch, capsys, ("",))
    menu._print_summary(SUMMARY)
    assert "Activity could not be loaded safely" in screens[0]
    assert "/private/student/" not in screens[0]
    assert "Technical Details" not in screens[0]


def test_picker_without_details_does_not_offer_or_accept_t(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(prompts, "pause_for_user", lambda: None)
    screens = _screens(monkeypatch, capsys, ("t", "1"))
    assert prompts.select_one("Pick", ("a",), ("A",), help_text="Pick.") == "a"
    assert len(screens) == 2
    assert all("Technical Details" not in screen for screen in screens)
    assert "Please choose a listed option" in screens[1]
