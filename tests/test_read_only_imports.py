from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _run(statement: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", statement],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )


def test_all_public_baseline_modules_import_read_only(
    unchanged_directory: Path,
) -> None:
    result = _run(
        (
            "import concord, concord.cli, concord.constants, "
            "concord.pds_publication as p; "
            "assert p.get_publication_producer_profile().module_id=='concord'; "
            "print(concord.__version__)"
        ),
        unchanged_directory,
    )
    assert result.returncode == 0, result.stderr


def test_import_does_not_import_sibling_modules(unchanged_directory: Path) -> None:
    statement = (
        "import sys, concord, concord.pds_publication as p; "
        "assert p.get_publication_producer_profile().module_id=='concord'; "
        "forbidden={'scoreform','quillan','portia','meridian','vitrine'}; "
        "assert forbidden.isdisjoint({n.split('.')[0].lower() for n in sys.modules})"
    )
    result = _run(statement, unchanged_directory)
    assert result.returncode == 0, result.stderr


def test_metadata_inspection_is_read_only(unchanged_directory: Path) -> None:
    result = _run(
        "import importlib.metadata as m; "
        "assert m.metadata('pds-concord')['Name']=='pds-concord'",
        unchanged_directory,
    )
    assert result.returncode == 0, result.stderr
