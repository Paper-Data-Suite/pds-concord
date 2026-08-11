from __future__ import annotations

from collections.abc import Iterator

import pytest

import concord.menu as menu_module
import concord.menu_prompts as prompts
from concord.menu_navigation import QuitPDS, ReturnToMainMenu
from concord.storage_errors import ConcordStoragePartialSuccessError
from concord.workflows import ConcordWorkflowConflictError, SessionSummary

CLEAR = "<<<CLEAR>>>"


def _inputs(monkeypatch: pytest.MonkeyPatch, values: list[str]) -> None:
    iterator: Iterator[str] = iter(values)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(iterator))


def _record_clear() -> None:
    print(CLEAR)


def test_main_help_is_a_separate_low_density_screen(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _inputs(monkeypatch, ["h", "", "q"])
    monkeypatch.setattr(menu_module, "clear_screen", _record_clear)
    assert menu_module.launch_menu() == 0
    screens = [
        screen for screen in capsys.readouterr().out.split(CLEAR) if screen.strip()
    ]
    main_screens = [screen for screen in screens if "1. Activity Management" in screen]
    help_screens = [
        screen for screen in screens if "Complete direct command help" in screen
    ]
    assert len(main_screens) == 2
    assert len(help_screens) == 1
    assert "1. Activity Management" not in help_screens[0]
    assert "raw JSON" not in "".join(screens)
    assert "ActivitySummary(" not in "".join(screens)


def test_multi_select_pages_after_ten_without_repeating_full_list(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    items = tuple(range(12))
    labels = tuple(f"Synthetic Student {index}" for index in items)
    _inputs(monkeypatch, ["1", "n", "1", "d"])
    monkeypatch.setattr(prompts, "clear_screen", _record_clear)
    selected = prompts.select_many(
        "Choose Students",
        items,
        labels,
        help_text="Synthetic help.",
    )
    assert selected == (0, 10)
    screens = [
        screen for screen in capsys.readouterr().out.split(CLEAR) if screen.strip()
    ]
    selection_screens = [screen for screen in screens if "Choose Students" in screen]
    assert selection_screens
    assert all(screen.count("Synthetic Student") <= 10 for screen in selection_screens)
    assert any("Selected: 2" in screen for screen in selection_screens)


def test_remaining_activity_context_preserves_starting_sequence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sessions = tuple(
        SessionSummary(
            class_id="class-1",
            activity_id="activity-1",
            session_id=f"session-{sequence}",
            sequence=sequence,
            label=f"Day {sequence}",
            status="planned",
            scheduled_start=None,
            snapshot_revision=3,
        )
        for sequence in (1, 2, 3)
    )
    _inputs(monkeypatch, ["3"])
    monkeypatch.setattr(prompts, "clear_screen", lambda: None)
    monkeypatch.setattr(prompts, "choose_session", lambda *_a, **_k: sessions[1])
    context = prompts.choose_effective_context("activity-1", sessions)
    assert context.session_ids == ("session-2", "session-3")
    assert context.sequence_start == 2
    assert context.sequence_end is None
    assert context.applies_to_remaining_activity is True

def test_confirmation_honors_help_and_navigation(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _inputs(monkeypatch, ["h", "", "CREATE"])
    monkeypatch.setattr(prompts, "clear_screen", _record_clear)
    assert prompts.confirm_write(
        "Create Group",
        "CREATE",
        ("Group: Group A",),
    )
    output = capsys.readouterr().out
    assert "H. Help" in output
    assert "B. Back" in output
    assert "M. Main Menu" in output
    assert "Q. Quit" in output
    assert "Type CREATE only when the displayed change is correct." in output

    _inputs(monkeypatch, ["b"])
    assert not prompts.confirm_write("Create Group", "CREATE", ("Group: A",))
    _inputs(monkeypatch, ["m"])
    with pytest.raises(ReturnToMainMenu):
        prompts.confirm_write("Create Group", "CREATE", ("Group: A",))
    _inputs(monkeypatch, ["q"])
    with pytest.raises(QuitPDS):
        prompts.confirm_write("Create Group", "CREATE", ("Group: A",))


def test_conflict_screen_offers_explicit_reload_without_retry(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _inputs(monkeypatch, ["h", "", "1"])
    monkeypatch.setattr(prompts, "clear_screen", _record_clear)
    assert prompts.prompt_conflict_reload() is True
    output = capsys.readouterr().out
    assert "1. Reload" in output
    assert "B. Back" in output
    assert "M. Main Menu" in output
    assert "Q. Quit" in output
    assert "never force-overwrites" in output


def test_partial_success_reports_commit_identity_without_paths(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _inputs(monkeypatch, [""])
    monkeypatch.setattr(prompts, "clear_screen", _record_clear)
    prompts.show_partial_success(
        ConcordStoragePartialSuccessError(
            "synthetic partial success",
            durable_paths=("state/revisions/1.json", "state/snapshots/2.json"),
            pointer_published=True,
            snapshot_revision=2,
            snapshot_sha256="a" * 64,
        )
    )
    output = capsys.readouterr().out
    assert "The Activity was committed" in output
    assert "Snapshot: 2" in output
    assert f"Snapshot SHA-256: {'a' * 64}" in output
    assert "Durable recovery paths: 2" in output
    assert "state/revisions/1.json" not in output


def test_domain_conflict_is_not_mislabeled_as_stale_snapshot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    shown: list[tuple[str, tuple[str, ...]]] = []
    monkeypatch.setattr(
        prompts,
        "prompt_conflict_reload",
        lambda: (_ for _ in ()).throw(AssertionError("unexpected stale prompt")),
    )
    monkeypatch.setattr(
        prompts,
        "show_result",
        lambda title, lines: shown.append((title, tuple(lines))),
    )
    prompts.handle_write_error(
        ConcordWorkflowConflictError("Participant is already active."),
        reload=lambda: None,
        error_title="Membership Error",
    )
    assert shown == [
        ("Membership Error", ("Participant is already active.",)),
    ]
