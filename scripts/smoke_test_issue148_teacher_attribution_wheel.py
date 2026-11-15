"""Isolated installed-wheel setup, restart, and authoring acceptance for #148.

The candidate Concord wheel and official Core wheel install in a disposable
virtual environment without sibling modules. Synthetic Settings and workflow
stages execute from a temporary directory, never the repository checkout.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "tests" / "fixtures" / "issue148" / "installed_attribution_stage.py"


def _python(root: Path) -> Path:
    return (
        root / "Scripts" / "python.exe" if os.name == "nt" else root / "bin" / "python"
    )


def _run(command: list[str], *, cwd: Path, env: dict[str, str]) -> None:
    print("+", subprocess.list2cmdline(command), flush=True)
    subprocess.run(command, cwd=cwd, check=True, env=env)


def smoke(concord_wheel: Path, core_wheel: Path) -> None:
    """Execute the three strict staged acceptance subprocesses."""
    if not concord_wheel.is_file() or not core_wheel.is_file():
        raise FileNotFoundError("Both candidate and official Core wheels are required")
    if not STAGE.is_file():
        raise FileNotFoundError(STAGE)
    with tempfile.TemporaryDirectory(prefix="concord-issue148-installed-") as raw:
        work = Path(raw).resolve()
        venv_root = work / "venv"
        venv.EnvBuilder(with_pip=True).create(venv_root)
        python = _python(venv_root)
        env = dict(os.environ)
        for name in (
            "PYTHONPATH",
            "PYTHONHOME",
            "VIRTUAL_ENV",
            "PDS_WORKSPACE_ROOT",
        ):
            env.pop(name, None)
        env.update(
            {
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONNOUSERSITE": "1",
                "PIP_DISABLE_PIP_VERSION_CHECK": "1",
                "PIP_CACHE_DIR": str(work / "pip-cache"),
                "PDS_148_TEST_CONFIG_HOME": str(work / "config"),
                "PDS_WORKSPACE_ROOT": str(work / "workspace"),
                "APPDATA": str(work / "config"),
                "XDG_CONFIG_HOME": str(work / "config"),
            }
        )
        _run(
            [str(python), "-m", "pip", "install", str(core_wheel.resolve())],
            cwd=work,
            env=env,
        )
        _run(
            [str(python), "-m", "pip", "install", str(concord_wheel.resolve())],
            cwd=work,
            env=env,
        )
        _run([str(python), "-m", "pip", "check"], cwd=work, env=env)
        stage = work / "isolated_stage.py"
        shutil.copyfile(STAGE, stage)
        for action in ("setup", "author", "relaunch"):
            _run([str(python), "-I", str(stage), action], cwd=work, env=env)
        print("QUALIFIED: #148 isolated installed-wheel attribution", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("concord_wheel", type=Path)
    parser.add_argument("core_wheel", type=Path)
    args = parser.parse_args()
    smoke(args.concord_wheel, args.core_wheel)
    return 0


if __name__ == "__main__":
    sys.exit(main())
