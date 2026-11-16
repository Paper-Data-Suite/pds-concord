"""#148 Slice 4B: unconfigured teacher can explicitly review one alternate.

No real classroom work, OS-user profile, Core workspace or student data.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import concord.menu_actor_action as actor_menu
from concord.menu_context import CancelMenuAction, MenuSessionContext
from concord.teacher_attribution import (
    ConcordTeacherAttributionProvider,
    ConcordTeacherAttributionStore,
    TeacherAttributionIdentity,
)
from concord.workflows import WorkflowActor


def _fixture(
    tmp_path: Path,
) -> tuple[MenuSessionContext, ConcordTeacherAttributionStore]:
    store = ConcordTeacherAttributionStore(config_directory=tmp_path)
    return MenuSessionContext(
        attribution_provider=ConcordTeacherAttributionProvider(store)
    ), store


def _no_ui(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, tuple[str, ...]]]:
    notices: list[tuple[str, tuple[str, ...]]] = []
    monkeypatch.setattr(actor_menu, "clear_screen", lambda: None)
    monkeypatch.setattr(actor_menu, "print_menu_header", lambda *_a: None)
    monkeypatch.setattr(actor_menu, "print_navigation", lambda: None)
    monkeypatch.setattr(
        actor_menu,
        "show_result",
        lambda title, lines: notices.append((title, tuple(lines))),
    )
    return notices


def _confirm(state: MenuSessionContext) -> WorkflowActor | None:
    return actor_menu.confirm_actor_write(
        "Synthetic exact authoring",
        "SAVE",
        ("Target: synthetic activity",),
        state=state,
        legacy_confirm=lambda *_a: pytest.fail("Provider path bypassed review"),
    )


def test_missing_default_requires_explicit_alternate_once_per_action(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state, store = _fixture(tmp_path)
    _no_ui(monkeypatch)
    entries = iter(("a", "SAVE", "a", "SAVE"))
    monkeypatch.setattr("builtins.input", lambda *_a: next(entries))
    monkeypatch.setattr(
        actor_menu,
        "_choose_temporary_actor",
        lambda: TeacherAttributionIdentity(
            "teacher-synthetic-alternate", "Alternate Teacher", "temporary"
        ),
    )
    for _ in range(2):
        chosen = _confirm(state)
        assert chosen is not None
        assert (chosen.actor_id, chosen.display_label) == (
            "teacher-synthetic-alternate", "Alternate Teacher"
        )
        assert state.actor is None
        assert store.load() is None
    assert not store.profile_path.exists()


def test_missing_default_cannot_confirm_without_choosing_advanced(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state, store = _fixture(tmp_path)
    notices = _no_ui(monkeypatch)
    entries = iter(("SAVE", ""))
    monkeypatch.setattr("builtins.input", lambda *_a: next(entries))
    assert _confirm(state) is None
    assert [label for label, _ in notices] == ["Actor Attribution Required"]
    assert store.load() is None


def test_prepared_request_is_only_built_after_alternate_selection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state, store = _fixture(tmp_path)
    _no_ui(monkeypatch)
    prepared: list[WorkflowActor] = []
    entries = iter(("a", "COMMIT"))
    monkeypatch.setattr("builtins.input", lambda *_a: next(entries))
    monkeypatch.setattr(
        actor_menu,
        "_choose_temporary_actor",
        lambda: TeacherAttributionIdentity("teacher-temporary", "Other", "temporary"),
    )

    def prepare(actor: WorkflowActor) -> tuple[SimpleNamespace, tuple[str, ...]]:
        prepared.append(actor)
        return SimpleNamespace(request=SimpleNamespace(actor=actor)), (
            "Exact synthetic digest reviewed",
        )

    result = actor_menu.confirm_prepared_actor_write(
        "Prepared synthetic action",
        "COMMIT",
        state=state,
        legacy_confirm=lambda *_a: pytest.fail("Bypassed actor review"),
        prepare_for_actor=prepare,
    )
    assert result is not None
    assert result.request.actor.actor_id == "teacher-temporary"
    assert len(prepared) == 1
    assert store.load() is None


def test_new_default_during_temporary_review_aborts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state, store = _fixture(tmp_path)
    _no_ui(monkeypatch)
    calls = 0

    def prompt(*_args: object) -> str:
        nonlocal calls
        calls += 1
        if calls == 1:
            return "a"
        store.create("Newly Configured", actor_id="teacher-new-default")
        return "SAVE"

    monkeypatch.setattr("builtins.input", prompt)
    monkeypatch.setattr(
        actor_menu,
        "_choose_temporary_actor",
        lambda: TeacherAttributionIdentity("teacher-alternate", "Other", "temporary"),
    )
    with pytest.raises(CancelMenuAction, match="appeared during this review"):
        _confirm(state)
    assert store.load() is not None


def test_corrupt_profile_is_not_treated_as_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state, store = _fixture(tmp_path)
    store.create("Former Default", actor_id="teacher-former")
    store.profile_path.write_bytes(b"{malformed")
    _no_ui(monkeypatch)
    monkeypatch.setattr(
        "builtins.input",
        lambda *_a: pytest.fail("Corrupt profile must abort before actor review"),
    )
    with pytest.raises(CancelMenuAction, match="unavailable"):
        _confirm(state)


def test_removed_cached_default_requires_new_review(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state, store = _fixture(tmp_path)
    saved = store.create("Existing Default", actor_id="teacher-existing")
    assert state.require_actor().actor_id == "teacher-existing"
    store.reset(saved, confirmed=True)
    _no_ui(monkeypatch)
    monkeypatch.setattr(
        "builtins.input",
        lambda *_a: pytest.fail("Stale actor must abort before review"),
    )
    with pytest.raises(CancelMenuAction, match="unavailable"):
        _confirm(state)


def test_unconfigured_path_rejects_unreviewed_actor(
    tmp_path: Path,
) -> None:
    state, _store = _fixture(tmp_path)
    with pytest.raises(CancelMenuAction, match="explicit alternate actor"):
        state.actor_for_action(
            action_label="Synthetic target", allow_unconfigured_default=True
        )
