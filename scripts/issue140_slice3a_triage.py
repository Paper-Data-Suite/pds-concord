"""Offline #140 Slice 3A census of named Artifact/Score suspect calls.

Presence and missing explicit kwargs are not runtime bug certification.
"""

from __future__ import annotations

import argparse
import ast
import csv
import io
from pathlib import Path
from typing import Final

OUTPUT: Final[str] = "docs/audits/issue140/slice3a_candidate_boundaries.csv"
FIELDS: Final[tuple[str, ...]] = (
    "source_file",
    "service_name",
    "call_lines",
    "calls",
    "standards_supply",
    "evidence_status",
    "disposition",
    "qualification_owner",
)
# Each site is drawn from the #138 P0.2 list and must remain present.  No
# inference is made from unrelated calls in the same module.
ARTIFACT: Final[tuple[str, ...]] = (
    "add_artifact_author",
    "update_artifact_author",
    "replace_artifact_author",
    "add_artifact_subject",
    "update_artifact_subject",
    "replace_artifact_subject",
    "add_artifact_authors",
    "add_artifact_subjects",
    "batch_confirm_artifact_attribution",
    "record_routine_artifact_review",
    "add_artifact_review",
    "replace_artifact_review",
    "add_moderation_record",
    "replace_moderation_record",
)
SCORE: Final[tuple[str, ...]] = ("record_prepared_routine_score",)
LABELS: Final[tuple[str, ...]] = (
    "list_scoring_scales",
    "list_criterion_sets",
    "show_criterion_set",
)
SITES: Final[tuple[tuple[str, tuple[str, ...], str], ...]] = (
    ("concord/menu_artifact.py", ARTIFACT, "#142"),
    ("concord/menu_artifact_scoring.py", SCORE, "#142"),
    ("concord/menu_score_teacher_labels.py", LABELS, "#142/#152"),
)


class TriageError(ValueError):
    """A documented suspect callsite is missing or source inventory drifted."""


def _calls(path: Path, targets: tuple[str, ...]) -> dict[str, list[ast.Call]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=path.as_posix())
    results: dict[str, list[ast.Call]] = {key: [] for key in targets}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            name = node.func.attr
        else:
            continue
        if name in results:
            results[name].append(node)
    return results


def build(root: Path) -> bytes:
    rows: list[dict[str, str]] = []
    for filename, required, destination in SITES:
        path = root / filename
        if not path.is_file():
            raise TriageError(f"Required source file missing: {filename}")
        discovered = _calls(path, required)
        for service in required:
            calls = discovered[service]
            if not calls:
                raise TriageError(f"Source boundary disappeared: {filename}::{service}")
            kinds: set[str] = set()
            for call in calls:
                if any(kw.arg == "standards_library" for kw in call.keywords):
                    kinds.add("explicit_keyword")
                elif any(kw.arg is None for kw in call.keywords):
                    kinds.add("kwargs_expansion_unverified")
                else:
                    kinds.add("no_keyword_visible")
            rows.append(
                {
                    "source_file": filename,
                    "service_name": service,
                    "call_lines": ";".join(
                        str(x.lineno) for x in sorted(calls, key=lambda x: x.lineno)
                    ),
                    "calls": str(len(calls)),
                    "standards_supply": ";".join(sorted(kinds)),
                    "evidence_status": "BLOCKED_OR_UNTESTED",
                    "disposition": "INVESTIGATE",
                    "qualification_owner": destination,
                }
            )
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def run(root: Path, *, check: bool) -> int:
    payload = build(root)
    destination = root / OUTPUT
    if destination.exists():
        if not destination.is_file() or destination.read_bytes() != payload:
            raise TriageError(
                "Slice 3A candidate inventory drift; review before replacing"
            )
    elif check:
        raise TriageError("Missing generated Slice 3A candidate inventory")
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb") as stream:
            stream.write(payload)
    return len(SCORE) + len(ARTIFACT) + len(LABELS)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--generate", action="store_true")
    action.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    try:
        count = run(arguments.repo.resolve(), check=arguments.check)
    except (TriageError, OSError, SyntaxError) as error:
        parser.exit(1, f"Slice 3A triage failed: {error}\n")
    print(
        f"Issue #140 Slice 3A: {count} suspect callsite families inventoried; "
        "no behavior inferred"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
