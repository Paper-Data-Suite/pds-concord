from __future__ import annotations

import subprocess
import sys


def test_score_next_does_not_cycle_through_activity_attention_on_import() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            (
                "import concord.academic_result_manifest_generation as manifest; "
                "import concord.workflows.artifact_routine_scoring_next as nextmod; "
                "assert hasattr(manifest, 'ConcordManifestGenerationError'); "
                "assert hasattr(nextmod, 'inspect_next_score_ready_artifact')"
            ),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
