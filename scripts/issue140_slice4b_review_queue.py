"""Deterministic, review-required source-surface queue for Concord issue #140.

The queue is an audit-work assignment, never a business-safety certification.
Only frozen, checked-in Slice 1/3E metadata is read; no Concord/Core imports.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
from collections import Counter
from pathlib import Path
from typing import Any, Final

BASE: Final[str] = "docs/audits/issue140"
OUTPUT: Final[str] = f"{BASE}/slice4b_surface_review_queue.csv"
FIELDS: Final[tuple[str, ...]] = (
    "source_file",
    "surface",
    "review_area",
    "proposed_child_owner",
    "handlers",
    "workflow_calls",
    "menu_delegations",
    "other_calls_unclassified",
    "matrix_operations",
    "context_fields_pending",
    "p02_reproduced",
    "p02_display_degraded",
    "p02_unqualified",
    "review_status",
    "human_reviewer",
    "review_date",
    "required_review",
)
P02_STATES: Final[frozenset[str]] = frozenset(
    {
        "SYNTHETIC_MENU_REPRODUCED",
        "SYNTHETIC_DISPLAY_DEGRADED",
        "BLOCKED_OR_UNTESTED",
    }
)
CONTEXT_FIELDS: Final[tuple[str, ...]] = (
    "activity_modes",
    "standards_graph_condition",
    "standards_contract",
    "core_roster",
    "activity_session_group",
    "actor",
    "workspace",
    "provenance",
    "privacy_authority",
    "record_effect",
    "snapshot_cas",
    "cancellation_recovery",
)
REVIEW_REQUIRED: Final[str] = "REVIEW_REQUIRED"


class QueueError(ValueError):
    """Frozen audit input is inconsistent or queue approval was fabricated."""


def _read_csv(path: Path, required: tuple[str, ...]) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        names = tuple(reader.fieldnames or ())
        if len(names) != len(set(names)) or not set(required).issubset(names):
            raise QueueError(f"Invalid reviewed-input CSV schema: {path.name}")
        rows = list(reader)
    if any(None in row or any(v is None for v in row.values()) for row in rows):
        raise QueueError(f"Invalid reviewed-input CSV row: {path.name}")
    return rows


def _review_area(source: str) -> tuple[str, str]:
    """Propose child ownership; this is NOT a reviewer acceptance decision."""
    if source.startswith("concord/cli"):
        return "Direct CLI parity", "#155"
    name = source.removeprefix("concord/")
    if name.startswith(("menu_activity", "menu_guided_activity")):
        return "Activity lifecycle and guided setup", "#141"
    if name.startswith(
        ("menu_group", "menu_saved_group", "menu_role", "menu_responsibility")
    ):
        return "GroupPlan, roles and grouping", "#147"
    if name.startswith("menu_session"):
        return "Session and roster context", "#151"
    if name.startswith("menu_artifact_scoring"):
        return "Routine Artifact scoring", "#142/#152"
    if name.startswith(("menu_artifact", "menu_scan")):
        return "Artifact return, attribution and review", "#142/#151"
    if name.startswith(("menu_score", "menu_scoring", "menu_presets")):
        return "Criterion, Scale, scoring and labels", "#143/#145/#152"
    if name.startswith(("menu_template", "menu_packet")):
        return "Template, packet and page routing", "#151/#155"
    if name.startswith("menu_publication"):
        return "Publication and Core reader contract", "#155"
    if name.startswith("menu_attention"):
        return "Stage-aware attention", "#149"
    if name.startswith("menu_teacher_history"):
        return "Teacher history and provenance", "#148"
    if name.startswith("menu_student_feedback"):
        return "Feedback and privacy", "#151"
    return "Navigation, other or unresolved dispatch", "#140/#153"


def _pending(row: dict[str, str]) -> bool:
    return any(
        not row.get(field, "")
        or row[field].startswith(("unreviewed", "all_modes_to_classify"))
        or row[field]
        in (
            "read_preview_write_to_classify",
            "orientation_or_standard_backed_criteria_or_scores",
        )
        for field in CONTEXT_FIELDS
    )


def build(root: Path) -> tuple[bytes, tuple[int, int, int, int]]:
    base = root / BASE
    with (base / "surface_inventory.json").open(encoding="utf-8") as stream:
        summary: dict[str, Any] = json.load(stream)
    if summary.get("schema") != "concord_issue140_slice1_census_v1":
        raise QueueError("Unsupported Slice 1 source inventory schema")
    sources = summary.get("source_surfaces")
    entries = summary.get("source_inventory")
    if not isinstance(sources, list) or not isinstance(entries, list):
        raise QueueError("Missing source inventory coverage")
    if len(sources) != len(set(sources)) or len(sources) != len(entries):
        raise QueueError("Duplicate or missing source surfaces")
    entries_by_file = {item["source_file"]: item for item in entries}
    if len(entries_by_file) != len(entries) or set(entries_by_file) != set(sources):
        raise QueueError("Source surface / AST inventory mismatch")
    matrix = _read_csv(
        base / "teacher_operation_matrix.csv",
        ("operation_id", "source_file", "boundary_kind", *CONTEXT_FIELDS),
    )
    if len(matrix) != summary.get("matrix_row_count"):
        raise QueueError("Frozen operation matrix count mismatch")
    ids = [row["operation_id"] for row in matrix]
    if len(ids) != len(set(ids)):
        raise QueueError("Duplicate source operation IDs")
    matrix_by_file: dict[str, list[dict[str, str]]] = {name: [] for name in sources}
    for row in matrix:
        if row["source_file"] not in matrix_by_file:
            raise QueueError(f"Uninventoried matrix surface: {row['source_file']}")
        matrix_by_file[row["source_file"]].append(row)
    ledger = _read_csv(
        base / "slice3e_scoped_dispositions.csv",
        ("source_file", "service_name", "slice3e_evidence_status", "owner"),
    )
    if len(ledger) != 18 or len({r["service_name"] for r in ledger}) != 18:
        raise QueueError("Scoped evidence ledger has invalid family coverage")
    states = Counter(row["slice3e_evidence_status"] for row in ledger)
    if set(states) - P02_STATES or (
        states["SYNTHETIC_MENU_REPRODUCED"],
        states["SYNTHETIC_DISPLAY_DEGRADED"],
        states["BLOCKED_OR_UNTESTED"],
    ) != (13, 2, 3):
        raise QueueError("Scoped evidence ledger status counts changed")
    scoped: dict[str, Counter[str]] = {name: Counter() for name in sources}
    for row in ledger:
        if row["source_file"] not in scoped or not row["owner"]:
            raise QueueError("Unowned or unrecognized P0.2 source family")
        scoped[row["source_file"]][row["slice3e_evidence_status"]] += 1
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    operation_count = 0
    other_count = 0
    pending_count = 0
    for filename in sorted(sources):
        entry = entries_by_file[filename]
        rows = matrix_by_file[filename]
        handlers = len(entry["handlers"])
        workflow = int(entry["count_workflow_calls"])
        delegation = int(entry["count_menu_delegations"])
        total = len(entry["calls"])
        other = total - workflow - delegation
        if min(workflow, delegation, other) < 0:
            raise QueueError(f"Invalid AST call counts: {filename}")
        boundaries = Counter(row["boundary_kind"] for row in rows)
        if (
            boundaries["HANDLER_INVENTORY"] != handlers
            or boundaries["WORKFLOW_SERVICE"] != workflow
            or boundaries["MENU_DELEGATION"] != delegation
            or len(rows) != handlers + workflow + delegation
        ):
            raise QueueError(f"Matrix/AST coverage mismatch: {filename}")
        if total != workflow + delegation + other:
            raise QueueError(f"Call accounting mismatch: {filename}")
        pending = sum(_pending(row) for row in rows)
        area, child = _review_area(filename)
        counts = scoped[filename]
        writer.writerow(
            {
                "source_file": filename,
                "surface": "CLI" if filename.startswith("concord/cli") else "MENU",
                "review_area": area,
                "proposed_child_owner": child,
                "handlers": handlers,
                "workflow_calls": workflow,
                "menu_delegations": delegation,
                "other_calls_unclassified": other,
                "matrix_operations": len(rows),
                "context_fields_pending": pending,
                "p02_reproduced": counts["SYNTHETIC_MENU_REPRODUCED"],
                "p02_display_degraded": counts["SYNTHETIC_DISPLAY_DEGRADED"],
                "p02_unqualified": counts["BLOCKED_OR_UNTESTED"],
                "review_status": REVIEW_REQUIRED,
                "human_reviewer": "UNASSIGNED",
                "review_date": "",
                "required_review": (
                    "Inspect contextual authority, indirect calls, read/write and "
                    "CAS/privacy/roster; decide each route; do not infer safety"
                ),
            }
        )
        operation_count += len(rows)
        other_count += other
        pending_count += pending
    if operation_count != summary["matrix_row_count"]:
        raise QueueError("Not every matrix operation received a review queue")
    if (
        other_count + summary["workflow_call_count"] + summary["menu_delegation_count"]
        != summary["all_calls"]
    ):
        raise QueueError("Other-call exclusion accounting mismatch")
    return output.getvalue().encode("utf-8"), (
        len(sources),
        operation_count,
        other_count,
        pending_count,
    )


def run(root: Path, *, check: bool) -> tuple[int, int, int, int]:
    payload, counts = build(root.resolve())
    path = root.resolve() / OUTPUT
    if path.exists():
        if not path.is_file() or path.read_bytes() != payload:
            raise QueueError("Review queue drift; review rather than overwrite")
    elif check:
        raise QueueError("Review queue is missing")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(payload)
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--generate", action="store_true")
    modes.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        sources, operations, other, pending = run(args.repo, check=args.check)
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"Issue #140 Slice 4B review queue FAILED: {error}\n")
    print(
        f"Slice 4B review queue: {sources} surfaces; {operations} operations; "
        f"{other} other/unclassified calls; {pending} context-pending operations"
    )
    print("All reviewer signoffs remain UNASSIGNED / REVIEW_REQUIRED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
