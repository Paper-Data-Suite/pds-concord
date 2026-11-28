"""#153 E2c: opt-in details remain bound to the reviewed prepared request."""

from __future__ import annotations

import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest

import concord.menu_actor_action as actions
import concord.menu_packet_generation as packets
import concord.menu_prompts as prompts
from concord.menu_context import CancelMenuAction, MenuSessionContext
from concord.menu_navigation import QuitPDS, ReturnToMainMenu
from concord.teacher_attribution import (
    ConcordTeacherAttributionProvider,
    ConcordTeacherAttributionStore,
    TeacherAttributionIdentity,
)
from concord.workflows import WorkflowActor


def _state(
    root: Path, provider: bool
) -> tuple[MenuSessionContext, ConcordTeacherAttributionStore | None]:
    if not provider:
        return MenuSessionContext(actor=WorkflowActor(actor_id="teacher-default")), None
    store = ConcordTeacherAttributionStore(config_directory=root)
    store.create("Default Teacher", actor_id="teacher-default")
    return (
        MenuSessionContext(
            attribution_provider=ConcordTeacherAttributionProvider(store)
        ),
        store,
    )


def _digest(actor: WorkflowActor) -> str:
    return hashlib.sha256(actor.actor_id.encode()).hexdigest()


def _review(
    state: MenuSessionContext, prepared: list[SimpleNamespace]
) -> SimpleNamespace | None:
    def prepare(actor: WorkflowActor) -> tuple[SimpleNamespace, tuple[str, ...]]:
        item = SimpleNamespace(actor=actor, review_digest=_digest(actor))
        prepared.append(item)
        return item, ("Packet: Synthetic", "Target: group-one")

    return actions.confirm_prepared_actor_write(
        "Generate Packet",
        "GENERATE",
        state=state,
        legacy_confirm=lambda *_a: pytest.fail("Unscoped legacy review"),
        prepare_for_actor=prepare,
        prepare_details=packets._preview_details,
        legacy_details_confirm=prompts.confirm_write,
    )


def _screens(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    choices: tuple[str, ...],
) -> list[str]:
    screens: list[str] = []
    answers = iter(choices)

    def read(_prompt: str = "") -> str:
        screens.append(capsys.readouterr().out)
        return next(answers)

    monkeypatch.setattr("builtins.input", read)
    return screens


@pytest.mark.parametrize("provider", (False, True))
def test_details_returns_to_same_prepared_review(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    provider: bool,
) -> None:
    state, _ = _state(tmp_path, provider)
    screens = _screens(monkeypatch, capsys, ("t", "b", "GENERATE"))
    prepared: list[SimpleNamespace] = []
    result = _review(state, prepared)
    assert len(prepared) == 1
    assert result is prepared[0]
    assert screens[0] == screens[2]
    assert "Target: group-one" in screens[0]
    assert "Review digest:" not in screens[0]
    assert f"Review digest: {result.review_digest}" in screens[1]


def test_actor_changes_replace_the_disclosed_digest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    state, _ = _state(tmp_path, True)
    monkeypatch.setattr(
        actions,
        "_choose_temporary_actor",
        lambda: TeacherAttributionIdentity("teacher-other", "Other Adult", "temporary"),
    )
    screens = _screens(
        monkeypatch, capsys, ("t", "b", "a", "t", "b", "d", "t", "b", "GENERATE")
    )
    prepared: list[SimpleNamespace] = []
    result = _review(state, prepared)
    assert [item.actor.actor_id for item in prepared] == [
        "teacher-default",
        "teacher-other",
        "teacher-default",
    ]
    assert result is prepared[-1]
    for item, screen in zip(
        prepared, (screens[1], screens[4], screens[7]), strict=True
    ):
        assert f"Review digest: {item.review_digest}" in screen
    assert all("Review digest:" not in screens[i] for i in (0, 2, 3, 5, 6, 8))


@pytest.mark.parametrize("provider", (False, True))
@pytest.mark.parametrize("choice", ("m", "q", "b"))
def test_details_navigation_never_returns_an_approved_request(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    provider: bool,
    choice: str,
) -> None:
    state, _ = _state(tmp_path, provider)
    screens = _screens(
        monkeypatch, capsys, ("t", "b", "b") if choice == "b" else ("t", choice)
    )
    prepared: list[SimpleNamespace] = []
    if choice == "b":
        assert _review(state, prepared) is None
    else:
        error = ReturnToMainMenu if choice == "m" else QuitPDS
        with pytest.raises(error):
            _review(state, prepared)
    assert len(prepared) == 1
    assert len(screens) == (3 if choice == "b" else 2)


@pytest.mark.parametrize("provider", (False, True))
def test_confirmation_token_inside_details_cannot_approve(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    provider: bool,
) -> None:
    state, _ = _state(tmp_path, provider)
    screens = _screens(monkeypatch, capsys, ("t", "GENERATE", "b", ""))
    prepared: list[SimpleNamespace] = []
    assert _review(state, prepared) is None
    assert len(prepared) == 1
    assert "Use Enter, B, M or Q." in screens[2]


def test_provider_change_while_in_details_invalidates_approval(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state, store = _state(tmp_path, True)
    assert store is not None
    inputs = iter(("t", "b", "GENERATE"))

    def read(_prompt: str = "") -> str:
        choice = next(inputs)
        if choice == "b":
            profile = store.load()
            assert profile is not None
            store.update_display_name(profile, "Changed Teacher")
        return choice

    monkeypatch.setattr("builtins.input", read)
    prepared: list[SimpleNamespace] = []
    with pytest.raises(CancelMenuAction, match="changed"):
        _review(state, prepared)
    assert len(prepared) == 1


def test_packet_preview_keeps_blocking_diagnostics_and_exact_targets() -> None:
    prepared = SimpleNamespace(
        packet_definition=SimpleNamespace(name="Synthetic Packet"),
        packet_version=SimpleNamespace(packet_version_id="version-one"),
        activity=SimpleNamespace(activity_id="activity-one"),
        session=SimpleNamespace(label="Day One"),
        generation_date="2026-10-19",
        packet_instance_count=1,
        artifact_count=0,
        page_count=0,
        route_count=0,
        review_digest="a" * 64,
        component_previews=(),
        target_plans=(),
        diagnostics=(
            SimpleNamespace(blocking=True, code="missing", message="Input required"),
        ),
    )
    lines = packets._preview_lines(prepared)
    assert "Packet Version: version-one" in lines
    assert "Generation date: 2026-10-19" in lines
    assert "BLOCKING missing: Input required" in lines
    assert all("Review digest:" not in line for line in lines)
    assert packets._preview_details(prepared) == (f"Review digest: {'a' * 64}",)


def test_receipt_details_preserve_output_location_and_counts(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    screens = _screens(monkeypatch, capsys, ("t", "b", ""))
    prompts.show_result_with_details(
        "Packet Render Result",
        ("Output: packet.pdf", "Pages: 2", "Routes: 1", "Reprint: yes"),
        (f"Output SHA-256: {'e' * 64}",),
    )
    assert screens[0] == screens[2]
    assert "Output: packet.pdf" in screens[0]
    assert "Pages: 2" in screens[0]
    assert "Output SHA-256:" not in screens[0]
    assert f"Output SHA-256: {'e' * 64}" in screens[1]
