"""#153 E2a: explicit read-only technical details on partial receipts."""

from __future__ import annotations

import pytest

import concord.menu_prompts as prompts
from concord.menu_navigation import QuitPDS, ReturnToMainMenu
from concord.storage_errors import ConcordStoragePartialSuccessError

CLEAR = "<<<CLEAR>>>"
HASH = "a" * 64


def _error(published: bool) -> ConcordStoragePartialSuccessError:
    return ConcordStoragePartialSuccessError(
        "/private/student/error",
        durable_paths=("/private/student/recovery.json",),
        pointer_published=published,
        snapshot_revision=3,
        snapshot_sha256=HASH,
    )


def _screens(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    choices: tuple[str, ...],
) -> list[str]:
    screens: list[str] = []
    answers = iter(choices)
    monkeypatch.setattr(prompts, "clear_screen", lambda: print(CLEAR))

    def read(_prompt: str = "") -> str:
        screens.append(capsys.readouterr().out)
        return next(answers)

    monkeypatch.setattr("builtins.input", read)
    return screens


@pytest.mark.parametrize("published", (True, False))
def test_ordinary_receipt_preserves_outcome_without_technical_metadata(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    published: bool,
) -> None:
    screens = _screens(monkeypatch, capsys, ("",))
    prompts.show_partial_success(_error(published))
    assert len(screens) == 1
    shown = screens[0]
    expected = (
        "The Activity was committed"
        if published
        else "The Activity was not published as the current snapshot."
    )
    assert expected in shown
    assert "Review canonical storage before retrying this action." in shown
    assert "Do not resubmit the original action automatically." in shown
    assert "T. Technical Details (read-only)" in shown
    assert "Snapshot:" not in shown
    assert HASH not in shown
    assert "Durable recovery paths:" not in shown
    assert "/private/student/" not in shown


@pytest.mark.parametrize("published", (True, False))
def test_opt_in_details_then_back_preserves_original_outcome(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    published: bool,
) -> None:
    screens = _screens(monkeypatch, capsys, (" T ", "b", ""))
    reads: list[str] = []
    prompts.handle_write_error(
        _error(published),
        reload=lambda: reads.append("read"),
        error_title="Synthetic error",
    )
    assert reads == []
    assert len(screens) == 3
    assert "Snapshot: 3" in screens[1]
    assert f"Snapshot SHA-256: {HASH}" in screens[1]
    assert "Durable recovery paths: 1" in screens[1]
    assert "Partial Success - Technical Details" in screens[1]
    assert all("/private/student/" not in screen for screen in screens)
    assert screens[0] == screens[2]
    assert HASH not in screens[0]
    assert all(
        "Do not resubmit the original action automatically." in s for s in screens
    )


@pytest.mark.parametrize("technical", (False, True))
@pytest.mark.parametrize("choice", ("m", "q"))
def test_receipt_navigation_propagates(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    technical: bool,
    choice: str,
) -> None:
    screens = _screens(monkeypatch, capsys, ("t", choice) if technical else (choice,))
    error = ReturnToMainMenu if choice == "m" else QuitPDS
    with pytest.raises(error):
        prompts.show_partial_success(_error(True))
    assert len(screens) == (2 if technical else 1)


def test_invalid_choices_do_not_clear_unacknowledged_receipt(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    screens = _screens(monkeypatch, capsys, ("invalid", "t", "invalid", "", "b"))
    prompts.show_partial_success(_error(True))
    assert len(screens) == 5
    assert "Use Enter, T, B, M or Q." in screens[1]
    assert "Use Enter, B, M or Q." in screens[3]
    assert HASH in screens[2]
    assert HASH in screens[3]
    assert HASH not in screens[4]
    assert all("The Activity was committed" in screen for screen in screens)


@pytest.mark.parametrize("invalid_hash", (None, "/private/student/invalid-hash"))
def test_missing_or_invalid_metadata_is_not_invented_or_exposed(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    invalid_hash: str | None,
) -> None:
    screens = _screens(monkeypatch, capsys, ("t", "b", ""))
    prompts.show_partial_success(
        ConcordStoragePartialSuccessError(
            "synthetic",
            durable_paths=(),
            pointer_published=False,
            snapshot_revision=None,
            snapshot_sha256=invalid_hash,
        )
    )
    expected = (
        "No snapshot identity or recovery path count was reported."
        if invalid_hash is None
        else "Snapshot SHA-256 unavailable."
    )
    assert expected in screens[1]
    assert "Snapshot: " not in screens[1]
    assert "/private/student/" not in "".join(screens)
