from __future__ import annotations

from types import SimpleNamespace

import pytest

from concord import menu_packet
from concord.menu_context import MenuSessionContext
from concord.menu_navigation import QuitPDS, ReturnToMainMenu
from concord.workflows.models import WorkflowActor


def _state() -> MenuSessionContext:
    return MenuSessionContext(
        actor=WorkflowActor(actor_id="teacher-1")
    )


def test_packet_library_menu_lists_all_management_surfaces(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("builtins.input", lambda _prompt="": "B")
    menu_packet.launch_packet_library_menu(_state())
    output = capsys.readouterr().out
    assert "1. List / select Packets" in output
    assert "2. Create Packet" in output
    assert "3. View Packet and version history" in output
    assert "4. Create successor version" in output
    assert "5. Activate current version" in output
    assert "6. Update Packet metadata" in output
    assert "7. Retire version" in output
    assert "8. Retire Packet" in output


@pytest.mark.parametrize(
    ("key", "expected"),
    (("M", ReturnToMainMenu), ("Q", QuitPDS)),
)
def test_packet_menu_navigation_unwinds(
    key: str,
    expected: type[BaseException],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("builtins.input", lambda _prompt="": key)
    with pytest.raises(expected):
        menu_packet.launch_packet_library_menu(_state())


def _prepared_packet() -> SimpleNamespace:
    component = SimpleNamespace(
        component_kind="external_component",
        external_reference=SimpleNamespace(
            module_id="quillan",
            record_kind="submission",
            record_id="submission-1",
            contract_version="1",
        ),
        template_id=None,
        template_version_id=None,
        audience_intent=SimpleNamespace(
            audience_kind="participant",
            role_keys=(),
        ),
        condition=None,
        packet_component_id="component-1",
        sequence=1,
        copies_per_target=1,
        requirement_level="recommended",
        label=None,
    )
    return SimpleNamespace(
        definition=SimpleNamespace(
            packet_definition_id="packet-1",
            name="Reusable Packet",
        ),
        version=SimpleNamespace(
            packet_version_id="version-1",
            version_label="v1",
            components=(component,),
            status="draft",
        ),
    )


def test_packet_create_menu_requires_create_confirmation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepared = _prepared_packet()
    captured: list[tuple[str, object]] = []
    committed_result = SimpleNamespace(
        packet_definition_id="packet-1",
        status="draft",
        snapshot_revision=1,
        snapshot_sha256="b" * 64,
        current_packet_version_id=None,
        head_packet_version_id="version-1",
        workspace_created=False,
    )
    monkeypatch.setattr(
        menu_packet,
        "prepare_packet_create",
        lambda request: captured.append(("prepare", request)) or prepared,
    )
    monkeypatch.setattr(
        menu_packet,
        "commit_packet_create",
        lambda value: captured.append(("commit", value)) or committed_result,
    )
    answers = iter(
        (
            "2",
            "packet-1",
            "version-1",
            "authoring.json",
            "1",
            "CREATE",
            "",
            "B",
        )
    )
    monkeypatch.setattr(
        "builtins.input",
        lambda _prompt="": next(answers),
    )
    menu_packet.launch_packet_library_menu(_state())
    assert [kind for kind, _ in captured] == ["prepare", "commit"]


def test_packet_create_menu_cancel_writes_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepared = _prepared_packet()
    committed: list[object] = []
    monkeypatch.setattr(
        menu_packet,
        "prepare_packet_create",
        lambda request: prepared,
    )
    monkeypatch.setattr(
        menu_packet,
        "commit_packet_create",
        lambda value: committed.append(value),
    )
    answers = iter(
        (
            "2",
            "packet-1",
            "version-1",
            "authoring.json",
            "1",
            "",
            "B",
        )
    )
    monkeypatch.setattr(
        "builtins.input",
        lambda _prompt="": next(answers),
    )
    menu_packet.launch_packet_library_menu(_state())
    assert committed == []


def test_main_menu_exposes_workspace_level_packet_library(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from concord import menu

    answers = iter(("Q",))
    monkeypatch.setattr(
        "builtins.input",
        lambda _prompt="": next(answers),
    )
    assert menu.launch_menu() == 0
    output = capsys.readouterr().out
    assert "6. Packet Library" in output
