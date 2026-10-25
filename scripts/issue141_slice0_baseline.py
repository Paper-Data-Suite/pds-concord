"""Freeze and replay issue #141's real-menu, failing-before baseline.

A one-time --generate run executes the five synthetic #140 tests. --check is
read-only and validates the historical baseline from pinned Git objects, so
later production repairs do not retroactively change this evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Final

BASELINE: Final[str] = "40837d54376f70cffb9ca539d52f7e40453ec1e6"
CORE_237_MERGED_MAIN: Final[str] = "a0d5e1a50580bbe025f0cad23c7e8524203a52ec"
OUTPUT: Final[str] = "docs/audits/issue141/slice0_baseline.json"
TEST_FILE: Final[str] = "tests/test_issue140_slice2_failing_before.py"
SOURCES: Final[tuple[str, ...]] = (
    "concord/menu_activity.py",
    "concord/menu_standards_context.py",
    "concord/workflows/activity.py",
    "concord/storage.py",
    "tests/test_issue140_slice2_failing_before.py",
    "tests/issue140_slice2_fixtures.py",
    "docs/audits/issue140/slice4c_handoff.json",
    "pyproject.toml",
)


class BaselineError(Exception):
    """The frozen baseline or deterministic witness is inconsistent."""


def _git(root: Path, *args: str) -> bytes:
    done = subprocess.run(["git", *args], cwd=root, capture_output=True, check=False)
    if done.returncode != 0:
        raise BaselineError(
            f"git {args[0]} failed: {done.stderr.decode('utf-8', errors='replace')}"
        )
    return done.stdout


def _source_bytes(root: Path, path: str) -> bytes:
    """Read pinned Git objects, never a mutable workspace or newer branch."""
    return _git(root, "show", f"{BASELINE}:{path}")


def _record(root: Path) -> dict[str, object]:
    manifest = {
        path: hashlib.sha256(_source_bytes(root, path)).hexdigest() for path in SOURCES
    }
    pyproject = _source_bytes(root, "pyproject.toml").decode("utf-8")
    if '"pds-core>=0.6.6,<0.7"' not in pyproject:
        raise BaselineError("Unexpected Core dependency in frozen pyproject.toml")

    menu = _source_bytes(root, "concord/menu_activity.py").decode("utf-8")
    beginning = menu.index("def _update_activity_field(")
    ending = menu.index("\ndef _edit_activity(", beginning)
    edit = menu[beginning:ending]
    required = (
        "library: StandardsLibrary | None = None",
        'field == "title"',
        'field == "description"',
        'field == "status"',
        'field == "activity_type"',
        'field == "scoring_orientation"',
        "_standards_selection(orientation)",
        "standards_library=library",
    )
    if any(part not in edit for part in required):
        raise BaselineError("Frozen Activity menu contract differs from #140 C1")

    storage = _source_bytes(root, "concord/storage.py").decode("utf-8")
    if (
        'item.criterion_kind == "standard_backed"' not in storage
        or 'item.score_kind == "standard_backed"' not in storage
    ):
        raise BaselineError("Frozen graph-history Standards contract differs")

    return {
        "schema": "pds-concord.issue141.slice0/1",
        "concord_baseline_commit": BASELINE,
        "core_237_main_merge_commit": CORE_237_MERGED_MAIN,
        "core_237_semantics": (
            "merged_to_source_main_not_qualified_as_released_dependency"
        ),
        "concord_core_requirement": "pds-core>=0.6.6,<0.7",
        "source_sha256": manifest,
        "synthetic_witness": {
            "test_file": TEST_FILE,
            "expected_test_cases": 5,
            "replay_status": (
                "five_tests_passed_at_frozen_baseline_on_local_installed_environment"
            ),
            "c1_observation": (
                "mixed_status_update_forwards_None_and_fails_before_write"
            ),
            "neutral_controls": ["evidence_only", "local_criteria_only"],
            "cancellation": "no_write",
            "c2_reference_only": (
                "criterion_preset_failing_before_retained_for_issue_143"
            ),
        },
        "graph_requirement": (
            "standards_needed_if_orientation_mixed_or_standards_based_or_"
            "criteria_or_score_history_standard_backed"
        ),
        "future_check_semantics": (
            "revalidate_historical_git_object_hashes_only; "
            "does_not_replay_expected_failure_after_141_fix"
        ),
        "not_claimed": [
            "published_concord_0.3.4_wheel_replay",
            "fixed_after_behavior",
            "all_five_edit_routes_working",
            "physical_or_live_teacher_evidence",
            "core_237_released_or_consumed_by_concord",
        ],
    }


def _json_bytes(record: dict[str, object]) -> bytes:
    return (json.dumps(record, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _replay(root: Path) -> None:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    with tempfile.TemporaryDirectory(prefix="concord141-slice0-") as temp:
        command = [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "--basetemp",
            str(Path(temp) / "pytest"),
            "-o",
            f"cache_dir={Path(temp) / 'pytest-cache'}",
            TEST_FILE,
        ]
        result = subprocess.run(
            command,
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    if result.returncode != 0 or re.search(r"\b5 passed\b", result.stdout) is None:
        raise BaselineError(
            "Slice 0 expected precisely five passing #140 synthetic witness cases; "
            "a failure or changed test count cannot certify this baseline."
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--generate", action="store_true")
    action.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        root = args.repo.resolve(strict=True)
        if not (root / ".git").exists():
            raise BaselineError("Not a Git repository worktree root")
        head = _git(root, "rev-parse", "HEAD").decode("ascii").strip()
        if args.generate and head != BASELINE:
            raise BaselineError("Generate only on the clean #141 Slice 0 baseline")
        output = root / OUTPUT
        if args.generate and output.exists():
            raise BaselineError("Create-only receipt already exists; no overwrite")
        payload = _json_bytes(_record(root))
        if args.generate:
            if (root / "concord/menu_activity.py").read_bytes().replace(
                b"\r\n", b"\n"
            ) != _source_bytes(root, "concord/menu_activity.py"):
                raise BaselineError("Current Activity menu is not the pinned baseline")
            _replay(root)
            output.parent.mkdir(parents=True, exist_ok=True)
            with output.open("xb") as handle:
                handle.write(payload)
            print("#141 Slice 0 baseline reproduced: five synthetic tests passed.")
        else:
            if not output.is_file() or output.read_bytes() != payload:
                raise BaselineError(
                    "Historical receipt missing or bytewise inconsistent"
                )
            print("#141 Slice 0 frozen source receipt: PASS (read-only check).")
        return 0
    except (BaselineError, OSError, UnicodeError, ValueError) as exc:
        print(f"#141 Slice 0: FAILED — {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
