"""Run Concord feature smoke scenarios in one isolated installed-wheel environment."""

from __future__ import annotations

import argparse
import os
import runpy
import subprocess
import tempfile
import venv
from collections.abc import Callable
from pathlib import Path
from typing import cast

ROOT = Path(__file__).resolve().parents[1]
SmokeSource = Callable[[], str]

SCENARIOS: tuple[tuple[str, str, str], ...] = (
    (
        "Activity copying",
        "activity_copying_smoke.py",
        "scripts/smoke_test_activity_copying_wheel.py",
    ),
    (
        "reusable presets",
        "reusable_presets_smoke.py",
        "scripts/smoke_test_reusable_presets_wheel.py",
    ),
    (
        "guided Activity",
        "guided_activity_smoke.py",
        "scripts/smoke_test_guided_activity_wheel.py",
    ),
    (
        "task-oriented menu",
        "task_oriented_activity_menu_smoke.py",
        "scripts/smoke_test_task_oriented_activity_menu_wheel.py",
    ),
)


def _python(venv_root: Path) -> Path:
    return (
        venv_root / "Scripts" / "python.exe"
        if os.name == "nt"
        else venv_root / "bin" / "python"
    )


def _run(command: list[str], cwd: Path) -> None:
    subprocess.run(
        command,
        cwd=cwd,
        check=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )


def _load_smoke_source(script_path: str) -> SmokeSource:
    """Load one existing smoke scenario source without importing script modules."""
    namespace = runpy.run_path(str(ROOT / script_path), run_name="__pds_smoke_source__")
    source = namespace.get("_smoke_code")
    if not callable(source):
        raise RuntimeError(f"{script_path} does not expose callable _smoke_code().")
    return cast(SmokeSource, source)


def smoke(concord_wheel: Path, core_wheel: Path) -> None:
    """Run all retained feature scenarios against one fresh installed environment."""
    if not concord_wheel.is_file():
        raise FileNotFoundError(concord_wheel)
    if not core_wheel.is_file():
        raise FileNotFoundError(core_wheel)

    with tempfile.TemporaryDirectory(prefix="concord-feature-wheel-") as raw:
        work = Path(raw)
        env_root = work / "venv"
        venv.EnvBuilder(with_pip=True).create(env_root)
        python = _python(env_root)

        _run(
            [str(python), "-m", "pip", "install", str(core_wheel.resolve())],
            work,
        )
        _run(
            [str(python), "-m", "pip", "install", str(concord_wheel.resolve())],
            work,
        )
        _run([str(python), "-m", "pip", "check"], work)

        for label, filename, script_path in SCENARIOS:
            print(f"Running installed feature smoke: {label}", flush=True)
            source = _load_smoke_source(script_path)
            smoke_path = work / filename
            smoke_path.write_text(source(), encoding="utf-8")
            _run([str(python), "-I", str(smoke_path)], work)
            print(f"PASSED installed feature smoke: {label}", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("concord_wheel", type=Path)
    parser.add_argument("core_wheel", type=Path)
    args = parser.parse_args()
    smoke(args.concord_wheel, args.core_wheel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
