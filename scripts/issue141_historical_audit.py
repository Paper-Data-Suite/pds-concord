"""Run the two source-pinned #140 checks on authenticated historical code.

Intentional edits after PR #161 must NOT be silently treated as part of #140.
This is not a successor live-tree semantic review or #162 signoff.
"""

from __future__ import annotations

import argparse
import runpy
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import cast

CHECKS = (
    "scripts/issue140_slice1_census.py",
    "scripts/issue140_slice4a_guard.py",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    if not all((repo / name).is_file() for name in CHECKS):
        parser.error("Frozen audit scripts are missing")
    # Load the local, authenticated audit helper without importing from a
    # non-installed test directory or changing global import search paths.
    candidate = runpy.run_path(str(repo / "tests/issue141_frozen_audit.py")).get(
        "materialize"
    )
    if not callable(candidate):
        raise RuntimeError("Historical materializer is unavailable")
    materialize = cast(Callable[[Path, Path], dict[str, object]], candidate)

    with tempfile.TemporaryDirectory(prefix="concord141-frozen140-") as folder:
        frozen = Path(folder) / "historical"
        record = materialize(repo, frozen)
        for name in CHECKS:
            command = [
                sys.executable,
                str(repo / name),
                "--repo",
                str(frozen),
                "--check",
            ]
            finished = subprocess.run(command, cwd=repo, check=False)
            if finished.returncode:
                raise RuntimeError(f"Historical audit check failed: {name}")
            print(f"PASS: historical #140 {Path(name).name}", flush=True)
    print(
        f"FROZEN #140 SOURCE CHECKS PASSED: {record['source_commit']}; "
        "live-tree #162 review remains separate and outstanding.",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, ValueError, OSError) as exc:
        print(f"HISTORICAL AUDIT FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
