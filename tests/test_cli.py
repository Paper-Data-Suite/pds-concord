from __future__ import annotations

import os
import subprocess
import sys
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


@pytest.mark.parametrize("argument", ["--help", "--version"])
def test_main_valid_requests_return_zero(argument: str) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main([argument])
    assert exit_info.value.code == 0


def test_module_help_and_version_are_read_only(unchanged_directory: Path) -> None:
    help_result = _run([sys.executable, "-m", "concord", "--help"], unchanged_directory)
    version_result = _run(
        [sys.executable, "-m", "concord", "--version"], unchanged_directory
    )
    assert help_result.returncode == 0
    assert "complete Activity" in help_result.stdout
    assert "workflow" in help_result.stdout
    assert version_result.returncode == 0
    assert version_result.stdout.strip() == f"concord {__version__}"


def test_invalid_argument_returns_usage_error(unchanged_directory: Path) -> None:
    result = _run([sys.executable, "-m", "concord", "--unknown"], unchanged_directory)
    assert result.returncode != 0
    assert "usage:" in result.stderr
