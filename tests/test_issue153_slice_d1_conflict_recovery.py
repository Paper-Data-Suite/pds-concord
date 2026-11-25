"""#153 D1: bounded, truthful recovery from Concord storage outcomes."""

from __future__ import annotations

import pytest

import concord.menu_prompts as prompts
from concord.menu_context import CancelMenuAction
from concord.menu_navigation import QuitPDS, ReturnToMainMenu
from concord.storage_errors import (
    ConcordStorageConflictError,
    ConcordStoragePartialSuccessError,
)


@pytest.mark.parametrize(
    "message",
    (
        "expected snapshot 2, found 3.",
        "Concord write lock already exists: /private/student/lock",
        "immutable canonical file already exists: /private/student/record",
        "no current snapshot exists for expected revision.",
    ),
)
def test_storage_conflict_reload_is_read_only_and_cause_is_unverified(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    message: str,
) -> None:
    values = iter(("1",))
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(values))
    reads: list[str] = []
    prompts.handle_write_error(
        ConcordStorageConflictError(message),
        reload=lambda: reads.append("read"),
        error_title="Synthetic Error",
    )
    shown = capsys.readouterr().out
    assert reads == ["read"]
    assert "Activity Write Conflict" in shown
    assert "cause is not yet verified" in shown
    assert "Do not repeat the action" in shown
    assert "This Activity changed after you opened it." not in shown
    assert "/private/student/" not in shown
    assert "OneDrive" not in shown


def test_storage_conflict_back_does_not_reload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("builtins.input", lambda _prompt="": "b")
    reads: list[str] = []
    prompts.handle_write_error(
        ConcordStorageConflictError("synthetic conflict"),
        reload=lambda: reads.append("read"),
        error_title="Synthetic Error",
    )
    assert reads == []


def test_reload_failure_retains_safe_next_action_without_exception_details(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    values = iter(("1", ""))
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(values))
    reads: list[str] = []

    def failed_read() -> None:
        reads.append("read")
        raise OSError("/private/student/record.json")

    prompts.handle_write_error(
        ConcordStorageConflictError("synthetic conflict"),
        reload=failed_read,
        error_title="Synthetic Error",
    )
    shown = capsys.readouterr().out
    assert reads == ["read"]
    assert "The current Activity could not be inspected safely." in shown
    assert "verify the saved state before another write" in shown
    assert "The original action was not retried." in shown
    assert "/private/student/" not in shown


@pytest.mark.parametrize("error", (CancelMenuAction, ReturnToMainMenu, QuitPDS))
def test_reload_preserves_navigation_unwind(
    monkeypatch: pytest.MonkeyPatch, error: type[Exception]
) -> None:
    monkeypatch.setattr("builtins.input", lambda _prompt="": "1")

    def unwind() -> None:
        raise error

    with pytest.raises(error):
        prompts.handle_write_error(
            ConcordStorageConflictError("synthetic conflict"),
            reload=unwind,
            error_title="Synthetic Error",
        )


@pytest.mark.parametrize("published", (True, False))
def test_partial_outcome_never_offers_automatic_resubmission(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    published: bool,
) -> None:
    monkeypatch.setattr("builtins.input", lambda _prompt="": "")
    reads: list[str] = []
    prompts.handle_write_error(
        ConcordStoragePartialSuccessError(
            "synthetic partial outcome",
            durable_paths=("/private/student/recovery.json",),
            pointer_published=published,
            snapshot_revision=3 if published else None,
            snapshot_sha256="a" * 64 if published else None,
        ),
        reload=lambda: reads.append("read"),
        error_title="Synthetic Error",
    )
    shown = capsys.readouterr().out
    assert reads == []
    assert "Review canonical storage before retrying this action." in shown
    assert "Do not resubmit the original action automatically." in shown
    assert "/private/student/" not in shown
    if published:
        assert "The Activity was committed" in shown
    else:
        assert "The Activity was not published as the current snapshot." in shown
        assert "The Activity was committed" not in shown
