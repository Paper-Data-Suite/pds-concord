"""#140 Slice 3E: reconcile the 18 scoped P0.2 source candidates with tests.

This read-only validator never imports Concord/Core or opens a workspace.
An observed context-first guard is NOT successful teacher business acceptance.
"""

from __future__ import annotations

import argparse
import ast
import csv
import io
from collections import Counter
from pathlib import Path
from typing import Final, NamedTuple

SOURCE: Final[str] = "docs/audits/issue140/slice3a_candidate_boundaries.csv"
OUTPUT: Final[str] = "docs/audits/issue140/slice3e_scoped_dispositions.csv"
SOURCE_FIELDS: Final[tuple[str, ...]] = (
    "source_file",
    "service_name",
    "call_lines",
    "calls",
    "standards_supply",
    "evidence_status",
    "disposition",
    "qualification_owner",
)
FIELDS: Final[tuple[str, ...]] = (
    "source_file",
    "service_name",
    "call_lines",
    "calls",
    "visible_context_supply",
    "slice3a_source_status",
    "slice3e_evidence_status",
    "evidence_test",
    "evidence_case",
    "finding_scope",
    "disposition",
    "owner",
)
GUARD: Final[str] = "SYNTHETIC_MENU_REPRODUCED"
LABEL: Final[str] = "SYNTHETIC_DISPLAY_DEGRADED"
UNTESTED: Final[str] = "BLOCKED_OR_UNTESTED"


class AuditError(ValueError):
    """The frozen candidate inventory, witness references, or ledger drifted."""


class Claim(NamedTuple):
    status: str
    test: str
    case: str
    scope: str
    disposition: str
    owner: str


B = (
    "tests/test_issue140_slice3b_menu_guard.py::"
    "test_mixed_teacher_menu_reaches_real_guard_before_missing_artifact"
)
C = (
    "tests/test_issue140_slice3c_attribution_guards.py::"
    "test_mixed_menu_write_hits_standards_guard_before_missing_relationship"
)
D = (
    "tests/test_issue140_slice3d_review_score_boundaries.py::"
    "test_mixed_successor_menu_guard_precedes_missing_predecessor"
)
REFUSAL = (
    "tests/test_issue140_slice3d_review_score_boundaries.py::"
    "test_planned_unreturned_artifact_blocks_quick_review_and_routine_score"
)
L = (
    "tests/test_issue140_slice3a_triage.py::"
    "test_mixed_activity_score_label_reader_silently_loses_native_definitions"
)

# Deliberately finite: adding a source callsite is a review event, never auto-safe.
CLAIMS: Final[dict[str, Claim]] = {
    "add_artifact_author": Claim(
        GUARD,
        B,
        "author",
        "context-first; nonexistent Artifact; no write",
        "FIX_142",
        "#142",
    ),
    "update_artifact_author": Claim(
        GUARD,
        C,
        "update_author",
        "context-first; nonexistent association; no write",
        "FIX_142",
        "#142",
    ),
    "replace_artifact_author": Claim(
        GUARD,
        C,
        "correct_author",
        "context-first; nonexistent predecessor; no write",
        "FIX_142",
        "#142",
    ),
    "add_artifact_subject": Claim(
        GUARD,
        B,
        "subject",
        "context-first; nonexistent Artifact; no write",
        "FIX_142",
        "#142",
    ),
    "update_artifact_subject": Claim(
        GUARD,
        C,
        "update_subject",
        "context-first; nonexistent association; no write",
        "FIX_142",
        "#142",
    ),
    "replace_artifact_subject": Claim(
        GUARD,
        C,
        "correct_subject",
        "context-first; nonexistent predecessor; no write",
        "FIX_142",
        "#142",
    ),
    "add_artifact_authors": Claim(
        GUARD,
        C,
        "multi_author",
        "context-first; nonexistent Artifact; no write",
        "FIX_142",
        "#142",
    ),
    "add_artifact_subjects": Claim(
        GUARD,
        C,
        "multi_subject",
        "context-first; nonexistent Artifact; no write",
        "FIX_142",
        "#142",
    ),
    "batch_confirm_artifact_attribution": Claim(
        GUARD,
        C,
        "batch_confirm",
        "context-first; nonexistent proposals; no write",
        "FIX_142",
        "#142",
    ),
    "record_routine_artifact_review": Claim(
        UNTESTED,
        REFUSAL,
        "mixed/evidence_only",
        "planned Artifact refused; eligible returned write untested",
        "HUMAN_GATE",
        "#142/#151/#155/#159",
    ),
    "add_artifact_review": Claim(
        GUARD,
        B,
        "review",
        "context-first; nonexistent Artifact; no write",
        "FIX_142",
        "#142",
    ),
    "replace_artifact_review": Claim(
        GUARD,
        D,
        "review",
        "context-first; nonexistent predecessor; no write",
        "FIX_142",
        "#142",
    ),
    "add_moderation_record": Claim(
        GUARD,
        B,
        "moderation",
        "context-first; nonexistent evidence; no write",
        "FIX_142",
        "#142",
    ),
    "replace_moderation_record": Claim(
        GUARD,
        D,
        "moderation",
        "context-first; nonexistent predecessor; no write",
        "FIX_142",
        "#142",
    ),
    "record_prepared_routine_score": Claim(
        UNTESTED,
        REFUSAL,
        "mixed/evidence_only",
        "planned Artifact refused; both eligible Score writes untested",
        "HUMAN_GATE",
        "#142/#151/#155/#159",
    ),
    "list_scoring_scales": Claim(
        LABEL,
        L,
        "mixed",
        "native definitions exist but display labels absent",
        "FIX_142",
        "#142/#152",
    ),
    "list_criterion_sets": Claim(
        LABEL,
        L,
        "mixed",
        "native definitions exist but display labels absent",
        "FIX_142",
        "#142/#152",
    ),
    "show_criterion_set": Claim(
        UNTESTED,
        "",
        "",
        "nested reader not reached after Criterion Set list failure",
        "INVESTIGATE",
        "#142/#152",
    ),
}


def read_candidates(payload: str) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(payload))
    if tuple(reader.fieldnames or ()) != SOURCE_FIELDS:
        raise AuditError("Slice 3A candidate CSV schema changed")
    rows = list(reader)
    keys = [row["service_name"] for row in rows]
    if len(rows) != 18 or len(set(keys)) != len(keys):
        raise AuditError("Expected exactly 18 distinct source candidate families")
    if set(keys) != set(CLAIMS):
        unexpected = sorted(set(keys) - set(CLAIMS))
        missing = sorted(set(CLAIMS) - set(keys))
        raise AuditError(
            f"Candidate coverage drift: new={unexpected}, missing={missing}"
        )
    for row in rows:
        if row["evidence_status"] != UNTESTED or row["disposition"] != "INVESTIGATE":
            raise AuditError(
                "Original Slice 3A status must remain frozen and unverified"
            )
        if row["standards_supply"] != "no_keyword_visible":
            raise AuditError("Source context visibility changed; review the callsite")
        if not row["call_lines"] or not row["calls"].isdecimal():
            raise AuditError("Unusable original candidate callsite evidence")
    return rows


def _check_test_reference(root: Path, claim: Claim) -> None:
    if not claim.test:
        if claim.status != UNTESTED or claim.case:
            raise AuditError("Only an explicitly untested family may omit its proof")
        return
    path, delim, function = claim.test.partition("::")
    if not delim or not path.startswith("tests/") or not function.startswith("test_"):
        raise AuditError(f"Malformed focused test reference: {claim.test}")
    file = root / path
    if not file.is_file():
        raise AuditError(f"Referenced witness file does not exist: {path}")
    try:
        tree = ast.parse(file.read_text(encoding="utf-8"), filename=path)
    except (UnicodeError, SyntaxError) as error:
        raise AuditError(f"Referenced witness is not parseable: {path}") from error
    if function not in {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }:
        raise AuditError(f"Referenced witness function is missing: {claim.test}")
    if not claim.case:
        raise AuditError(f"A case/scope is required for: {claim.test}")


def build(root: Path) -> bytes:
    source = root / SOURCE
    if not source.is_file():
        raise AuditError("Frozen Slice 3A candidate inventory is unavailable")
    rows = read_candidates(source.read_text(encoding="utf-8"))
    for claim in CLAIMS.values():
        _check_test_reference(root, claim)
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        claim = CLAIMS[row["service_name"]]
        writer.writerow(
            {
                "source_file": row["source_file"],
                "service_name": row["service_name"],
                "call_lines": row["call_lines"],
                "calls": row["calls"],
                "visible_context_supply": row["standards_supply"],
                "slice3a_source_status": row["evidence_status"],
                "slice3e_evidence_status": claim.status,
                "evidence_test": claim.test,
                "evidence_case": claim.case,
                "finding_scope": claim.scope,
                "disposition": claim.disposition,
                "owner": claim.owner,
            }
        )
    return out.getvalue().encode("utf-8")


def run(root: Path, *, check: bool) -> Counter[str]:
    payload = build(root)
    target = root / OUTPUT
    if target.exists():
        if not target.is_file() or target.read_bytes() != payload:
            raise AuditError("Slice 3E ledger changed: review rather than overwrite")
    elif check:
        raise AuditError("Slice 3E disposition ledger is missing")
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(payload)
    return Counter(
        row["slice3e_evidence_status"]
        for row in csv.DictReader(io.StringIO(payload.decode("utf-8")))
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--generate", action="store_true")
    action.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        counts = run(args.repo.resolve(), check=args.check)
    except (AuditError, OSError, UnicodeError) as error:
        parser.exit(1, f"Slice 3E audit failure: {error}\n")
    print(
        "Slice 3E classifications: "
        f"{counts[GUARD]} context-first guards; "
        f"{counts[LABEL]} degraded-label reads; "
        f"{counts[UNTESTED]} unqualified behavior families"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
