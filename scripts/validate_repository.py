"""Run the principal local checks mirrored by continuous integration."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run(command: list[str], *, cwd: Path = ROOT) -> None:
    print("+", subprocess.list2cmdline(command), flush=True)
    subprocess.run(
        command,
        cwd=cwd,
        check=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )


def validate(core_wheel: Path, *, allow_dirty: bool) -> None:
    """Run tests, static checks, builds, package checks, and smoke validation."""
    python = sys.executable
    _run([python, "scripts/verify_core_wheel.py", str(core_wheel), "--installed"])
    _run([python, "scripts/verify_core_grouping_fixtures.py"])
    _run([python, "-m", "pip", "check"])
    with tempfile.TemporaryDirectory(prefix="pds-concord-validation-") as raw_temp:
        temp = Path(raw_temp)
        env = {
            **os.environ,
            "TMP": str(temp),
            "TEMP": str(temp),
            "PDS_CORE_WHEEL": str(core_wheel.resolve()),
            "PYTHONDONTWRITEBYTECODE": "1",
            "RUFF_CACHE_DIR": str(temp / "ruff-cache"),
            "MYPY_CACHE_DIR": str(temp / "mypy-cache"),
        }
        commands = [
            [
                python,
                "-m",
                "pytest",
                "--basetemp",
                str(temp / "pytest"),
                "-o",
                f"cache_dir={temp / 'pytest-cache'}",
            ],
            [python, "-m", "ruff", "check", "."],
            [python, "-m", "mypy"],
            [python, "scripts/check_documentation.py"],
            [python, "scripts/verify_release_compatibility.py"],
        ]
        for command in commands:
            print("+", subprocess.list2cmdline(command), flush=True)
            subprocess.run(command, cwd=ROOT, check=True, env=env)
        dist = temp / "dist"
        source = temp / "source"
        shutil.copytree(
            ROOT,
            source,
            ignore=shutil.ignore_patterns(
                ".git",
                ".venv",
                "build",
                "dist",
                "*.egg-info",
                "__pycache__",
                ".pytest_cache",
                ".mypy_cache",
                ".ruff_cache",
            ),
        )
        _run([python, "-m", "build", "--outdir", str(dist)], cwd=source)
        artifacts = sorted(dist.iterdir())
        _run([python, "-m", "twine", "check", *map(str, artifacts)])
        wheels = list(dist.glob("*.whl"))
        if len(wheels) != 1:
            raise RuntimeError("Expected exactly one built Concord wheel.")
        _run([python, "scripts/check_package.py", str(wheels[0])])
        _run([python, "scripts/verify_release_artifacts.py", str(dist)])
        _run([python, "scripts/smoke_test_wheel.py", str(wheels[0]), str(core_wheel)])
    _run(["git", "diff", "--check"])
    if not allow_dirty:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        if result.stdout:
            raise RuntimeError(
                "Repository validation left or found working-tree residue."
            )


def main() -> int:
    """Parse arguments and validate the repository."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core-wheel", required=True, type=Path)
    parser.add_argument("--allow-dirty", action="store_true")
    args = parser.parse_args()
    validate(args.core_wheel, allow_dirty=args.allow_dirty)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
