from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from concord import __version__
from concord.cli import main

STATUS_TEXT = "complete Activity workflow"


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
    executable = Path(sys.executable)
    name = "concord.exe" if os.name == "nt" else "concord"
    return str(executable.with_name(name))


def _assert_help(result: subprocess.CompletedProcess[str]) -> None:
    assert result.returncode == 0
    assert "usage: concord" in result.stdout
    assert "complete Activity" in result.stdout
    assert "workflow" in result.stdout
    assert result.stderr == ""


def test_main_empty_arguments_prints_help(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 0
    captured = capsys.readouterr()
    assert "usage: concord" in captured.out
    assert STATUS_TEXT in captured.out.replace("\n", " ")
    assert captured.err == ""


@pytest.mark.parametrize(
    "command",
    [
        [_console_command()],
        [sys.executable, "-m", "concord"],
    ],
    ids=["concord", "python-module"],
)
def test_bare_invocation_prints_help_read_only(
    command: list[str], unchanged_directory: Path
) -> None:
    _assert_help(_run(command, unchanged_directory))


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
