"""#142 Slice 0: read-only inventory of exact frozen Artifact write families.

No fixture creation, canonical workspace mutation or inferred success status.
"""

from __future__ import annotations

import argparse
import ast
import csv
import json
from collections import Counter
from pathlib import Path
from typing import cast

# This is a HANDLER/CALLSITE inventory, not a claim about complete nested APIs.
EXPECTED = {
    "concord/menu_artifact.py": {
        "add_artifact_author": 1,
        "update_artifact_author": 1,
        "replace_artifact_author": 1,
        "add_artifact_subject": 1,
        "update_artifact_subject": 1,
        "replace_artifact_subject": 1,
        "add_artifact_authors": 1,
        "add_artifact_subjects": 1,
        "batch_confirm_artifact_attribution": 1,
        "add_artifact_review": 1,
        "replace_artifact_review": 1,
        "add_moderation_record": 1,
        "replace_moderation_record": 1,
        "record_routine_artifact_review": 1,
    },
    "concord/menu_artifact_scoring.py": {
        "record_prepared_routine_score": 2,
    },
}


def _calls(path: Path, service_names: set[str]) -> list[dict[str, object]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    rows: list[dict[str, object]] = []
    for function in ast.walk(tree):
        if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for node in ast.walk(function):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
                continue
            if node.func.id not in service_names:
                continue
            # Exclude any nested function's calls being double-counted.
            if any(
                inner is not function
                and isinstance(inner, (ast.FunctionDef, ast.AsyncFunctionDef))
                and inner.lineno <= node.lineno <= (inner.end_lineno or inner.lineno)
                for inner in ast.walk(function)
            ):
                continue
            rows.append(
                {
                    "service": node.func.id,
                    "handler": function.name,
                    "line_current": node.lineno,
                    "visible_keywords": sorted(
                        key.arg or "**kwargs" for key in node.keywords
                    ),
                    "classification": "CALLSITE_ONLY_NOT_END_TO_END",
                }
            )
    return sorted(rows, key=lambda row: cast(int, row["line_current"]))


def check(repo: Path) -> dict[str, object]:
    source_audit = repo / "docs/audits/issue140/slice3e_scoped_dispositions.csv"
    with source_audit.open("r", encoding="utf-8", newline="") as handle:
        frozen = tuple(csv.DictReader(handle))
    out: list[dict[str, object]] = []
    for source, expected in EXPECTED.items():
        calls = _calls(repo / source, set(expected))
        counts = Counter(str(row["service"]) for row in calls)
        assert counts == Counter(expected), (
            f"Source changed: {source}: actual {counts}, expected {expected}. "
            "Review the contract before continuing."
        )
        for service, number in expected.items():
            frozen_matches = [
                item
                for item in frozen
                if item["source_file"] == source and item["service_name"] == service
            ]
            assert len(frozen_matches) == 1
            old = frozen_matches[0]
            assert old["calls"] == str(number)
            assert old["owner"].startswith("#142")
            for new in (item for item in calls if item["service"] == service):
                out.append(
                    {
                        "source_file": source,
                        **new,
                        "frozen_lines": old["call_lines"],
                        "frozen_status": old["slice3e_evidence_status"],
                        "owner": old["owner"],
                        "current_evidence": "CODE_PATH_VERIFIED_ONLY",
                        "reviewer": "UNASSIGNED",
                    }
                )
    assert len(out) == 16, "Fourteen + two Score call sites were expected."
    return {
        "issue": 142,
        "baseline": "#140 Slice 3E frozen dispositions; not overwritten",
        "status": "SOURCE_CALLSITE_INVENTORY_NOT_PRODUCTION_SIGNOFF",
        "teacher_write_families": 15,
        "teacher_write_callsites": len(out),
        "details": out,
        "unverified": (
            "Direct CLI, canonical profile validity, returned Review/Score paths, "
            "every historical operation ID and all 3,685 route decisions"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--check", action="store_true", required=True)
    args = parser.parse_args()
    print(json.dumps(check(args.repo.resolve()), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
