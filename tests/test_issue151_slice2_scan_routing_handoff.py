"""#151 Slice 2: Collect delegates shared Core PDS2 intake without new writes.

All inputs, identities and outcomes are synthetic. This suite tests the UI
handoff and ownership boundary, not physical scanning or PDS2 decoding.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest

import concord.menu_artifact as artifact_menu
import concord.menu_scan as scan_menu
from concord.menu_context import MenuSessionContext
from concord.menu_navigation import QuitPDS, ReturnToMainMenu
from concord.workflows.models import ActivitySummary


def _activity() -> ActivitySummary:
    return ActivitySummary(
        class_id="synthetic-class-151",
        activity_id="synthetic-activity-151",
        title="Synthetic Six-Cluster Council",
        status="active",
        scoring_orientation="mixed",
        session_count=1,
        group_count=6,
        snapshot_revision=9,
    )


def _inputs(monkeypatch: pytest.MonkeyPatch, *answers: str) -> None:
    supplied: Iterator[str] = iter(answers)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(supplied))


def _menus(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(artifact_menu, "clear_screen", lambda: None)
    monkeypatch.setattr(scan_menu, "clear_screen", lambda: None)


def _forbid(*_args: object, **_kwargs: object) -> None:
    pytest.fail("Navigation-only handoff performed an academic or routing write")


def test_collect_exposes_shared_scan_routing_without_changing_existing_actions(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _menus(monkeypatch)
    _inputs(monkeypatch, "b")
    artifact_menu.launch_collect_work_menu(_activity(), MenuSessionContext())
    printed = capsys.readouterr().out.casefold()
    assert "r. route or review scans (shared pds workspace)" in printed
    for expected in (
        "1. View returned work",
        "2. Assemble returned work",
        "3. Review attribution",
        "4. Advanced attribution tools",
        "O. Open returned work",
        "V. Open a verified saved assembly version",
        "S. Collection status (read-only)",
        "B. Back",
        "M. Main menu",
        "Q. Quit",
    ):
        assert expected.casefold() in printed


@pytest.mark.parametrize("choice", ("r", "R"))
def test_handoff_passes_exact_existing_actor_context_without_implied_route(
    monkeypatch: pytest.MonkeyPatch,
    choice: str,
) -> None:
    _menus(monkeypatch)
    session = MenuSessionContext()
    received: list[MenuSessionContext] = []
    monkeypatch.setattr(
        artifact_menu,
        "launch_scan_routing_menu",
        lambda state: received.append(state),
    )
    monkeypatch.setattr(artifact_menu, "batch_confirm_artifact_attribution", _forbid)
    _inputs(monkeypatch, choice, "b")
    artifact_menu.launch_collect_work_menu(_activity(), session)
    assert received == [session]
    assert received[0] is session


def test_return_from_scan_menu_goes_back_to_collect_then_back_to_caller(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _menus(monkeypatch)
    _inputs(monkeypatch, "r", "b", "b")
    monkeypatch.setattr(scan_menu, "_route", _forbid)
    monkeypatch.setattr(scan_menu, "_review", _forbid)
    monkeypatch.setattr(artifact_menu, "assemble_returned_artifact", _forbid)
    artifact_menu.launch_collect_work_menu(_activity(), MenuSessionContext())
    output = capsys.readouterr().out
    assert "Scan Routing" in output
    assert output.count("R. Route or review scans") == 2


def test_route_scans_calls_only_the_existing_intake_owner_after_second_choice(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _menus(monkeypatch)
    _inputs(monkeypatch, "r", "1", "b", "b")
    routed: list[str] = []
    monkeypatch.setattr(scan_menu, "_route", lambda: routed.append("route"))
    monkeypatch.setattr(scan_menu, "_review", _forbid)
    monkeypatch.setattr(artifact_menu, "prepare_artifact_pages", _forbid)
    artifact_menu.launch_collect_work_menu(_activity(), MenuSessionContext())
    assert routed == ["route"]


def test_routing_review_calls_existing_exception_review_owner_with_same_actor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _menus(monkeypatch)
    _inputs(monkeypatch, "r", "2", "b", "b")
    session = MenuSessionContext()
    reviewed: list[MenuSessionContext] = []
    monkeypatch.setattr(scan_menu, "_route", _forbid)
    monkeypatch.setattr(scan_menu, "_review", lambda state: reviewed.append(state))
    artifact_menu.launch_collect_work_menu(_activity(), session)
    assert reviewed == [session]
    assert reviewed[0] is session


def test_merely_entering_and_exiting_scan_menu_does_not_retain_or_route(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _menus(monkeypatch)
    _inputs(monkeypatch, "r", "b", "b")
    monkeypatch.setattr(scan_menu, "route_scan_sources", _forbid)
    monkeypatch.setattr(scan_menu, "list_routing_failures", _forbid)
    monkeypatch.setattr(artifact_menu, "batch_confirm_artifact_attribution", _forbid)
    artifact_menu.launch_collect_work_menu(_activity(), MenuSessionContext())


@pytest.mark.parametrize(
    ("choice", "signal"),
    (("m", ReturnToMainMenu), ("q", QuitPDS)),
)
def test_navigation_from_nested_scan_routing_reaches_module_owner(
    monkeypatch: pytest.MonkeyPatch,
    choice: str,
    signal: type[Exception],
) -> None:
    _menus(monkeypatch)
    _inputs(monkeypatch, "r", choice)
    monkeypatch.setattr(artifact_menu, "_handle_error", _forbid)
    with pytest.raises(signal):
        artifact_menu.launch_collect_work_menu(_activity(), MenuSessionContext())


def test_collect_help_discloses_global_destination_and_refresh(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _menus(monkeypatch)
    _inputs(monkeypatch, "h", "b")
    monkeypatch.setattr(artifact_menu, "pause_for_user", lambda: None)
    artifact_menu.launch_collect_work_menu(_activity(), MenuSessionContext())
    help_text = capsys.readouterr().out
    assert "shared PDS workspace" in help_text
    assert "other Activities or modules" in help_text
    assert "Only verified routes" in help_text
    assert "Collection status after routing" in help_text


def test_collection_status_still_available_after_nested_routing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _menus(monkeypatch)
    _inputs(monkeypatch, "r", "b", "s", "b")
    calls: list[str] = []
    monkeypatch.setattr(
        artifact_menu,
        "_show_collection_status",
        lambda activity: calls.append(activity.activity_id),
    )
    artifact_menu.launch_collect_work_menu(_activity(), MenuSessionContext())
    assert calls == ["synthetic-activity-151"]


def test_route_menu_does_not_preselect_active_activity_as_a_destination(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _menus(monkeypatch)
    _inputs(monkeypatch, "r", "b", "b")
    selected: list[str] = []
    monkeypatch.setattr(
        scan_menu,
        "_select_routing_destination_candidate",
        lambda *_args: selected.append("preselected") or _forbid(),
    )
    artifact_menu.launch_collect_work_menu(_activity(), MenuSessionContext())
    assert selected == []


def test_bad_scan_menu_entry_is_not_misreported_as_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _menus(monkeypatch)
    _inputs(monkeypatch, "r", "b")
    recorded: list[str] = []

    def bad_entry(_state: MenuSessionContext) -> None:
        raise ValueError("synthetic scan navigation failure")

    monkeypatch.setattr(artifact_menu, "launch_scan_routing_menu", bad_entry)
    monkeypatch.setattr(
        artifact_menu,
        "_handle_error",
        lambda _activity, error, **_kw: recorded.append(str(error)),
    )
    artifact_menu.launch_collect_work_menu(_activity(), MenuSessionContext())
    assert recorded == ["synthetic scan navigation failure"]
