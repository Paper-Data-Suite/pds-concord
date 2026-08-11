from __future__ import annotations

import os
import subprocess
import sys
import sysconfig
from pathlib import Path

import pytest

from concord import __version__
from concord.cli import main


def _run(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )


def _console_command() -> str:
    scripts_directory = Path(sysconfig.get_path("scripts"))
    name = "concord.exe" if os.name == "nt" else "concord"
    return str(scripts_directory / name)


def _assert_help(result: subprocess.CompletedProcess[str]) -> None:
    assert result.returncode == 0
    assert "usage: concord" in result.stdout
    assert "Activity workflow" in result.stdout
    assert result.stderr == ""


def test_main_empty_arguments_launches_teacher_menu(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def fake_launch_menu() -> int:
        calls.append("menu")
        return 0

    import concord.menu

    monkeypatch.setattr(concord.menu, "launch_menu", fake_launch_menu)
    assert main([]) == 0
    assert calls == ["menu"]


@pytest.mark.parametrize(
    "command",
    [
        [_console_command(), "--help"],
        [sys.executable, "-m", "concord", "--help"],
    ],
    ids=["concord-help", "python-module-help"],
)
def test_help_invocations_are_read_only(
    command: list[str], unchanged_directory: Path
) -> None:
    _assert_help(_run(command, unchanged_directory))


@pytest.mark.parametrize(
    "command",
    [
        [_console_command(), "--version"],
        [sys.executable, "-m", "concord", "--version"],
    ],
    ids=["concord-version", "python-module-version"],
)
def test_version_invocations_are_read_only(
    command: list[str], unchanged_directory: Path
) -> None:
    result = _run(command, unchanged_directory)
    assert result.returncode == 0
    assert result.stdout.strip() == f"concord {__version__}"
    assert result.stderr == ""


@pytest.mark.parametrize("argument", ["--help", "--version"])
def test_main_valid_requests_exit_successfully(argument: str) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main([argument])
    assert exit_info.value.code == 0


def test_invalid_argument_returns_usage_error(unchanged_directory: Path) -> None:
    result = _run([_console_command(), "--unknown"], unchanged_directory)
    assert result.returncode != 0
    assert "usage:" in result.stderr


def test_explicit_menu_command_dispatches(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_launch_menu() -> int:
        calls.append("menu")
        return 0

    import concord.menu

    monkeypatch.setattr(concord.menu, "launch_menu", fake_launch_menu)
    assert main(["menu"]) == 0
    assert calls == ["menu"]
