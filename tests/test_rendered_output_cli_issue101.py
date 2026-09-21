from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import concord.cli_app.handlers.packet_runtime as packet_runtime
from concord.cli_app.main import EXIT_ERROR, EXIT_OK, main
from concord.cli_app.parser import build_parser
from concord.workflows import ConcordWorkflowOpenError


def _base_args(command: str, root: Path) -> tuple[str, ...]:
    return (
        "packet",
        command,
        "--workspace-root",
        str(root),
        "--class-id",
        "class-1",
        "--activity-id",
        "activity-1",
        "--packet-instance-id",
        "packet-instance-1",
    )


def test_instance_open_parser_is_direct_and_nonmutating() -> None:
    parser = build_parser()
    args = parser.parse_args(
        (
            "packet",
            "instance-open",
            "--class-id",
            "class-1",
            "--activity-id",
            "activity-1",
            "--packet-instance-id",
            "packet-instance-1",
        )
    )

    assert args.handler is packet_runtime.handle_instance_open
    assert not hasattr(args, "actor_id")
    assert not hasattr(args, "expected_snapshot")
    assert not hasattr(args, "path")


def test_instance_open_folder_parser_is_direct_and_nonmutating() -> None:
    parser = build_parser()
    args = parser.parse_args(
        (
            "packet",
            "instance-open-folder",
            "--class-id",
            "class-1",
            "--activity-id",
            "activity-1",
            "--packet-instance-id",
            "packet-instance-1",
        )
    )

    assert args.handler is packet_runtime.handle_instance_open_folder
    assert not hasattr(args, "actor_id")
    assert not hasattr(args, "expected_snapshot")
    assert not hasattr(args, "path")


def test_instance_open_cli_uses_shared_verified_service_without_prompt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "workspace"
    calls: list[tuple[str, str, str, Path | None]] = []
    output = root / "classes" / "class-1" / "packet.pdf"

    def open_packet(
        class_id: str,
        activity_id: str,
        packet_instance_id: str,
        *,
        workspace_root: str | Path | None = None,
    ):
        calls.append(
            (
                class_id,
                activity_id,
                packet_instance_id,
                None if workspace_root is None else Path(workspace_root),
            )
        )
        return SimpleNamespace(output_path=output)

    monkeypatch.setattr(
        packet_runtime,
        "open_rendered_packet_output",
        open_packet,
    )
    monkeypatch.setattr(
        "builtins.input",
        lambda _prompt="": (_ for _ in ()).throw(
            AssertionError("direct Open CLI must not prompt")
        ),
    )

    assert main(_base_args("instance-open", root)) == EXIT_OK
    assert calls == [
        ("class-1", "activity-1", "packet-instance-1", root)
    ]
    rendered = capsys.readouterr().out
    assert f"Opened rendered Packet: {output}" in rendered


def test_instance_open_folder_cli_uses_shared_verified_service_without_prompt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "workspace"
    calls: list[tuple[str, str, str, Path | None]] = []
    folder = root / "classes" / "class-1" / "rendered" / "packets"

    def open_folder(
        class_id: str,
        activity_id: str,
        packet_instance_id: str,
        *,
        workspace_root: str | Path | None = None,
    ):
        calls.append(
            (
                class_id,
                activity_id,
                packet_instance_id,
                None if workspace_root is None else Path(workspace_root),
            )
        )
        return SimpleNamespace(output_directory=folder)

    monkeypatch.setattr(
        packet_runtime,
        "open_rendered_packet_output_directory",
        open_folder,
    )
    monkeypatch.setattr(
        "builtins.input",
        lambda _prompt="": (_ for _ in ()).throw(
            AssertionError("direct folder Open CLI must not prompt")
        ),
    )

    assert main(_base_args("instance-open-folder", root)) == EXIT_OK
    assert calls == [
        ("class-1", "activity-1", "packet-instance-1", root)
    ]
    rendered = capsys.readouterr().out
    assert f"Opened rendered Packet folder: {folder}" in rendered


def test_instance_open_cli_reports_controlled_viewer_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "workspace"

    def fail_open(*_args: object, **_kwargs: object) -> object:
        raise ConcordWorkflowOpenError(
            "Concord verified the rendered Packet, but the system viewer failed."
        )

    monkeypatch.setattr(
        packet_runtime,
        "open_rendered_packet_output",
        fail_open,
    )

    assert main(_base_args("instance-open", root)) == EXIT_ERROR
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Error:" in captured.err
    assert "verified the rendered Packet" in captured.err
