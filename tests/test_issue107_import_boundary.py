from __future__ import annotations

import subprocess
import sys


def test_manifest_generation_import_does_not_cycle_through_review_next() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            (
                "import concord.academic_result_manifest_generation as module; "
                "assert hasattr(module, 'ConcordManifestGenerationError')"
            ),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
