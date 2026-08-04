"""Install built wheels in isolation and smoke-test outside the checkout."""

from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
import venv
from pathlib import Path


def _run(command: list[str], cwd: Path) -> None:
    subprocess.run(
        command, cwd=cwd, check=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    )


def smoke_test(concord_wheel: Path, core_wheel: Path) -> None:
    """Install exact local wheels without indexes and exercise import and CLI."""
    with tempfile.TemporaryDirectory(prefix="pds-concord-smoke-") as raw_temp:
        root = Path(raw_temp)
        environment = root / "venv"
        outside = root / "outside"
        outside.mkdir()
        venv.EnvBuilder(with_pip=True).create(environment)
        scripts = environment / ("Scripts" if os.name == "nt" else "bin")
        python = scripts / ("python.exe" if os.name == "nt" else "python")
        concord = scripts / ("concord.exe" if os.name == "nt" else "concord")
        _run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--no-index",
                "--no-deps",
                str(core_wheel.resolve()),
                str(concord_wheel.resolve()),
            ],
            outside,
        )
        _run(
            [
                str(python),
                "-c",
                (
                    "import importlib.metadata as m, concord, pds_core; "
                    "assert concord.__version__ == m.version('pds-concord'); "
                    "assert m.version('pds-core') == '0.6.0'"
                ),
            ],
            outside,
        )
        _run([str(concord), "--help"], outside)
        _run([str(concord), "--version"], outside)
        _run([str(python), "-m", "concord", "--help"], outside)


def main() -> int:
    """Run an isolated smoke test for local Concord and Core wheels."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("concord_wheel", type=Path)
    parser.add_argument("core_wheel", type=Path)
    args = parser.parse_args()
    smoke_test(args.concord_wheel, args.core_wheel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
