"""#140 Slice 4C: deterministic, unsigned handoff from frozen audit evidence.

Reads repository audit receipts only. Never imports Concord/Core, discovers a
classroom workspace, changes a source baseline, or signs off an operation.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Final

BASE: Final[str] = "docs/audits/issue140"
JSON_OUT: Final[str] = f"{BASE}/slice4c_handoff.json"
MD_OUT: Final[str] = f"{BASE}/slice4c_handoff.md"
INPUTS: Final[tuple[str, ...]] = (
    f"{BASE}/baseline.json",
    f"{BASE}/surface_inventory.json",
    f"{BASE}/teacher_operation_matrix.csv",
    f"{BASE}/slice3e_scoped_dispositions.csv",
    f"{BASE}/slice4b_surface_review_queue.csv",
)
SCHEMA: Final[str] = "concord_issue140_slice4c_handoff_v1"
RELEASE_COMMIT: Final[str] = "68ddd804d2733fa900ee396ac7a2ba6bd98aa819"
SLICE4B_COMMIT: Final[str] = "5c8e29c889ad88538adb8c13b8fc5d440c32f5d8"
GUARD: Final[str] = "SYNTHETIC_MENU_REPRODUCED"
DEGRADED: Final[str] = "SYNTHETIC_DISPLAY_DEGRADED"
UNTESTED: Final[str] = "BLOCKED_OR_UNTESTED"
EXPECTED: Final[tuple[int, int, int, int, int]] = (
    67,
    3685,
    10182,
    7466,
    3685,
)


class HandoffError(ValueError):
    """Audit evidence does not support a faithful release-blocking handoff."""


def _read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        result: dict[str, Any] = json.load(stream)
    if not isinstance(result, dict):
        raise HandoffError(f"Expected JSON object: {path.name}")
    return result


def _read_csv(path: Path, fields: tuple[str, ...]) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        header = tuple(reader.fieldnames or ())
        if len(header) != len(set(header)) or not set(fields).issubset(header):
            raise HandoffError(f"CSV schema differs: {path.name}")
        rows = list(reader)
    if any(None in row or any(v is None for v in row.values()) for row in rows):
        raise HandoffError(f"Malformed CSV row: {path.name}")
    return rows


def _number(row: dict[str, str], key: str) -> int:
    value = row.get(key, "")
    if not value.isdecimal():
        raise HandoffError(f"Invalid unsigned count: {key}={value!r}")
    return int(value)


def _validate_baseline(baseline: dict[str, Any]) -> dict[str, Any]:
    git = baseline["git"]
    source = baseline["source"]
    wheels = baseline["published_artifacts"]
    installed = baseline["environment"]["installed_distributions"]
    if (
        git["head"] != RELEASE_COMMIT
        or git["tag_peeled_commit"] != RELEASE_COMMIT
        or git["tag"] != "v0.3.4"
        or source["version"] != "0.3.4"
    ):
        raise HandoffError("Published-source baseline identity changed")
    core = wheels["core_v0_6_6_wheel"]
    concord = wheels["concord_v0_3_4_wheel"]
    if core["status"] != "verified_published_bytes_and_metadata":
        raise HandoffError("Core published-wheel verification was downgraded")
    if concord["status"] != "not_provided":
        raise HandoffError("Concord wheel state changed: review a new receipt")
    return {
        "repository": git["origin_repository"],
        "release_tag": git["tag"],
        "release_commit": RELEASE_COMMIT,
        "source_version": source["version"],
        "source_core_requirement": next(
            (x for x in source["dependencies"] if x.startswith("pds-core")),
            "not_recorded",
        ),
        "core_wheel_status": core["status"],
        "core_wheel_sha256": core["sha256"],
        "concord_wheel_status": concord["status"],
        "captured_installed_concord_version": installed["concord"]["version"],
        "captured_installed_concord_editable": installed["concord"]["editable"],
        "captured_installed_core_version": installed["core"]["version"],
        "host_os": baseline["environment"]["system"],
        "host_architecture": baseline["environment"]["machine_architecture"],
        "python": baseline["environment"]["python"],
        "audit_branch_parent": SLICE4B_COMMIT,
    }


def _validate_ledger(rows: list[dict[str, str]]) -> dict[str, int]:
    if len(rows) != 18 or len({r["service_name"] for r in rows}) != 18:
        raise HandoffError("Scoped P0.2 family coverage is not exactly 18")
    counts = Counter(r["slice3e_evidence_status"] for r in rows)
    if (counts[GUARD], counts[DEGRADED], counts[UNTESTED]) != (13, 2, 3):
        raise HandoffError("Scoped evidence status totals changed")
    if set(counts) != {GUARD, DEGRADED, UNTESTED}:
        raise HandoffError("Unknown status in scoped evidence ledger")
    for row in rows:
        if not row["owner"] or not row["finding_scope"]:
            raise HandoffError(f"Unowned scoped finding: {row['service_name']}")
        if row["slice3e_evidence_status"] != UNTESTED and not row["evidence_test"]:
            raise HandoffError(f"Missing witness: {row['service_name']}")
        if row["slice3e_evidence_status"] == UNTESTED:
            if row["disposition"] not in {"HUMAN_GATE", "INVESTIGATE"}:
                raise HandoffError("Unqualified path claims an unsupported disposition")
    return {
        "context_first_guards": counts[GUARD],
        "display_degradations": counts[DEGRADED],
        "positive_paths_unqualified": counts[UNTESTED],
    }


def _validate_review_queue(
    rows: list[dict[str, str]],
    ledger: list[dict[str, str]],
    summary: dict[str, Any],
    matrix: list[dict[str, str]],
) -> dict[str, int]:
    sources = summary["source_surfaces"]
    if len(rows) != len(sources) or len({r["source_file"] for r in rows}) != len(rows):
        raise HandoffError("Surface review queue is incomplete or duplicated")
    if set(r["source_file"] for r in rows) != set(sources):
        raise HandoffError("Review queue surface set differs from source census")
    if len(matrix) != summary["matrix_row_count"] or len(
        {r["operation_id"] for r in matrix}
    ) != len(matrix):
        raise HandoffError("Missing or duplicated operation in frozen matrix")
    if any(row["source_file"] not in sources for row in matrix):
        raise HandoffError("Frozen matrix contains an unknown source surface")
    if any(
        row["review_status"] != "REVIEW_REQUIRED"
        or row["human_reviewer"] != "UNASSIGNED"
        or row["review_date"]
        for row in rows
    ):
        raise HandoffError("Reviewer signoff must remain explicitly unassigned")
    totals = {
        "surfaces": len(rows),
        "matrix_operations": sum(_number(r, "matrix_operations") for r in rows),
        "ast_calls": int(summary["all_calls"]),
        "other_calls_unclassified": sum(
            _number(r, "other_calls_unclassified") for r in rows
        ),
        "context_pending_operations": sum(
            _number(r, "context_fields_pending") for r in rows
        ),
    }
    if tuple(totals.values()) != EXPECTED:
        raise HandoffError(f"Frozen review totals changed: {totals}")
    if totals["matrix_operations"] != len(matrix):
        raise HandoffError("Matrix operations do not reconcile with review queue")
    total_from_counts = sum(
        _number(r, "workflow_calls")
        + _number(r, "menu_delegations")
        + _number(r, "other_calls_unclassified")
        for r in rows
    )
    if total_from_counts != totals["ast_calls"]:
        raise HandoffError("Review queue AST call accounting does not reconcile")
    for column, status in (
        ("p02_reproduced", GUARD),
        ("p02_display_degraded", DEGRADED),
        ("p02_unqualified", UNTESTED),
    ):
        if sum(_number(r, column) for r in rows) != sum(
            r["slice3e_evidence_status"] == status for r in ledger
        ):
            raise HandoffError(f"Surface queue evidence disagrees: {column}")
    return totals


def _hashes(root: Path) -> dict[str, str]:
    return {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in INPUTS
    }


def _gates() -> list[dict[str, str]]:
    return [
        {
            "gate": "Published Concord v0.3.4 wheel replay",
            "status": "NOT_PERFORMED",
            "owner": "#154/#155",
            "next_proof": "Authenticate wheel bytes and replay menu witnesses",
        },
        {
            "gate": "Full repository test suite on exact audit branch",
            "status": "NOT_RECORDED",
            "owner": "#140/#155",
            "next_proof": "Run full pytest/Ruff/mypy and attach exact commit receipt",
        },
        {
            "gate": "Positive returned/assembled Review and Score lifecycle",
            "status": "NOT_QUALIFIED",
            "owner": "#142/#151/#155",
            "next_proof": "Use truthful synthetic returns and explicit human judgments",
        },
        {
            "gate": "Physical Windows return scan and long-path opening",
            "status": "NOT_PERFORMED",
            "owner": "#159",
            "next_proof": "Preserve original scans and qualify installed path behavior",
        },
        {
            "gate": "Core publication reader and Meridian ingestion",
            "status": "NOT_PERFORMED",
            "owner": "#155/#159",
            "next_proof": "Authorize source-versioned publication and downstream read",
        },
        {
            "gate": "Independent route-level human semantic review",
            "status": "UNASSIGNED",
            "owner": "#140/#156/#157",
            "next_proof": "Review the unsigned operation matrix and all other calls",
        },
        {
            "gate": "Corbeau and Gemini independent attestations",
            "status": "NOT_PERFORMED",
            "owner": "#156/#157/#158",
            "next_proof": "Obtain separate reviews after implementation",
        },
    ]


def build(root: Path) -> dict[str, bytes]:
    root = root.resolve()
    base = root / BASE
    baseline = _read_json(base / "baseline.json")
    summary = _read_json(base / "surface_inventory.json")
    if summary.get("schema") != "concord_issue140_slice1_census_v1":
        raise HandoffError("Unexpected frozen Slice 1 census schema")
    matrix = _read_csv(
        base / "teacher_operation_matrix.csv",
        ("operation_id", "source_file"),
    )
    ledger = _read_csv(
        base / "slice3e_scoped_dispositions.csv",
        (
            "source_file",
            "service_name",
            "slice3e_evidence_status",
            "finding_scope",
            "evidence_test",
            "disposition",
            "owner",
        ),
    )
    queue = _read_csv(
        base / "slice4b_surface_review_queue.csv",
        (
            "source_file",
            "review_status",
            "human_reviewer",
            "review_date",
            "matrix_operations",
            "workflow_calls",
            "menu_delegations",
            "other_calls_unclassified",
            "context_fields_pending",
            "p02_reproduced",
            "p02_display_degraded",
            "p02_unqualified",
        ),
    )
    provenance = _validate_baseline(baseline)
    evidence = _validate_ledger(ledger)
    coverage = _validate_review_queue(queue, ledger, summary, matrix)
    findings = [
        {
            "source": row["source_file"],
            "service": row["service_name"],
            "status": row["slice3e_evidence_status"],
            "scope": row["finding_scope"],
            "test": row["evidence_test"],
            "case": row["evidence_case"],
            "disposition": row["disposition"],
            "owner": row["owner"],
        }
        for row in ledger
    ]
    handoff: dict[str, Any] = {
        "schema": SCHEMA,
        "kind": "UNSIGNED_AUDIT_HANDOFF_NOT_RELEASE_CERTIFICATION",
        "baseline": provenance,
        "evidence_counts": evidence,
        "coverage": coverage,
        "source_digests_sha256": _hashes(root),
        "scoped_findings": findings,
        "witnesses": {
            "activity_edit": (
                "tests/test_issue140_slice2_failing_before.py"
                " (source-menu failing-before; owner #141)"
            ),
            "criterion_preset": (
                "tests/test_issue140_slice2_failing_before.py"
                " (valid dotted Standard rejected; owner #143)"
            ),
            "artifact_page": (
                "tests/test_issue140_slice3a_triage.py"
                " (internal canonical-context forwarding only)"
            ),
            "pre_return": (
                "tests/test_issue140_slice3d_review_score_boundaries.py"
                " (planned/unreturned work refused)"
            ),
        },
        "gates": _gates(),
        "review_protocol": (
            "Keep full matrix and original source census immutable; "
            "review every route, other call, authority and exception using "
            "operation IDs. Issue a separately reviewed successor ledger "
            "with real reviewer/date, exact test and child owner."
        ),
    }
    json_blob = (json.dumps(handoff, indent=2, sort_keys=True) + "\n").encode("utf-8")
    lines = [
        "# Concord #140 — Unsigned baseline and handoff (Slice 4C)",
        "",
        "**This is an audit of known evidence, not a release qualification or",
        "completed route-by-route semantic review.** No human signoffs recorded.",
        "",
        "## Frozen release and observed environment",
        "",
        f"- Release: Concord {provenance['source_version']} / tag",
        f"  `{provenance['release_tag']}` at `{provenance['release_commit']}`.",
        f"- Core published-wheel status: {provenance['core_wheel_status']};",
        f"  SHA-256 `{provenance['core_wheel_sha256']}`.",
        "- Concord published wheel: **NOT PROVIDED**. A clean installed-wheel",
        "  replay of v0.3.4 has **not** been authenticated by this audit.",
        "- Captured Windows host: Python",
        f"  `{provenance['python']}` / `{provenance['host_architecture']}`;",
        "  editable installed Concord metadata",
        f"  `{provenance['captured_installed_concord_version']}`",
        "  did **not** match the v0.3.4 source tag. Do not mistake this for",
        "  verified release-wheel parity.",
        f"- Source-only audit branch parent: `{SLICE4B_COMMIT}`.",
        "",
        "## Coverage and review debt",
        "",
        f"- Teacher/CLI source surfaces: **{coverage['surfaces']}**.",
        f"- Inventoried operations: **{coverage['matrix_operations']}**.",
        f"- AST calls (all kinds): **{coverage['ast_calls']}**.",
        "- Additional calls outside the narrowed operation matrix:",
        f"  **{coverage['other_calls_unclassified']}** (not certified neutral).",
        "- Operation rows still pending contextual contract review:",
        f"  **{coverage['context_pending_operations']}**.",
        "- Every queue row: `REVIEW_REQUIRED`, reviewer `UNASSIGNED`.",
        "  Owner proposals are routing suggestions, not approvals.",
        "",
        "## 18 specifically named #138 P0.2 service families",
        "",
        "| Evidence classification | Families |",
        "|---|---:|",
        f"| Context-first guarded menu failures | {evidence['context_first_guards']} |",
        f"| Silently degraded Score labels | {evidence['display_degradations']} |",
        (
            "| Positive behavior unqualified (including Score) | "
            f"{evidence['positive_paths_unqualified']} |"
        ),
        "",
        "Context-first witnesses use deliberately absent targets, proving the",
        "Standards context guard fires first; they **do not** prove return,",
        "attribution, Moderation or Score succeeds with legitimate evidence.",
        "The two routine Score callsites are represented by one family.",
        "",
        "| Operation family | Evidence | Follow-up | Exact witness |",
        "|---|---|---|---|",
    ]
    for row in findings:
        evidence_ref = row["test"] + (f" ({row['case']})" if row["case"] else "")
        if not evidence_ref:
            evidence_ref = "No positive witness"
        lines.append(
            f"| `{row['service']}` | `{row['status']}` | "
            f"{row['owner']} | `{evidence_ref}` |"
        )
    lines.extend(
        [
            "",
            "## Other confirmed evidence and ownership",
            "",
            "- **#141:** Actual Activity-edit menu failing-before witness:",
            "  `tests/test_issue140_slice2_failing_before.py`.",
            "- **#143:** The valid dotted Core Standard Criterion-preset save",
            "  fails in that same Slice 2 witness; do not normalize the code.",
            "- **#142/#152:** Scoped Artifact/context and Score-label failures",
            "  require repairs; eligible returned Score paths remain unqualified.",
            "- **Internal resolution:** `prepare_artifact_pages` has a tested",
            "  forwarding mechanism and a separate planned/unreturned control,",
            "  not complete physical PDS2 return acceptance.",
            "",
            "## Outstanding gates (no assumed passes)",
            "",
            "| Gate | Recorded state | Owner | Required next proof |",
            "|---|---|---|---|",
        ]
    )
    for gate in handoff["gates"]:
        lines.append(
            f"| {gate['gate']} | `{gate['status']}` | {gate['owner']} | "
            f"{gate['next_proof']} |"
        )
    lines.extend(
        [
            "",
            "## Reproduce, review and transfer",
            "",
            "```powershell",
            "python scripts/issue140_slice1_census.py --repo . --check",
            "python scripts/issue140_slice3a_triage.py --repo . --check",
            "python scripts/issue140_slice3e_dispositions.py --repo . --check",
            "python scripts/issue140_slice4a_guard.py --repo . --check",
            "python scripts/issue140_slice4b_review_queue.py --repo . --check",
            "python scripts/issue140_slice4c_handoff.py --repo . --check",
            "```",
            "",
            "This report is deterministic from the immutable source receipts.",
            "Its structured JSON records SHA-256 digests for all five inputs.",
            "The editable branch's focused test result and full-suite status",
            "must be attached separately as exact-commit qualification receipts.",
            "Follow `ISSUE140_SLICE4B_REVIEW_QUEUE.md` for review protocol.",
            "No operation may be declared `NEUTRAL_VERIFIED` solely from AST",
            "absence of a keyword or a synthetic failing-before assertion.",
            "Do not publish, overwrite prior audits, or add fake review dates.",
            "",
        ]
    )
    return {
        JSON_OUT: json_blob,
        MD_OUT: ("\n".join(lines)).encode("utf-8"),
    }


def run(root: Path, *, check: bool) -> tuple[int, int, int]:
    output = build(root)
    for name, payload in output.items():
        path = root.resolve() / name
        if path.exists() and (not path.is_file() or path.read_bytes() != payload):
            raise HandoffError(f"Existing handoff differs: {name}")
        if check and not path.exists():
            raise HandoffError(f"Missing generated handoff: {name}")
    if not check:
        existing = [name for name in output if (root.resolve() / name).exists()]
        if existing:
            raise HandoffError(f"Create-only output exists: {existing}")
        for name, payload in output.items():
            path = root.resolve() / name
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as stream:
                stream.write(payload)
    handoff = json.loads(output[JSON_OUT])
    return (
        handoff["coverage"]["surfaces"],
        handoff["coverage"]["matrix_operations"],
        len(handoff["scoped_findings"]),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--generate", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        surfaces, operations, families = run(args.repo, check=args.check)
    except (
        HandoffError,
        KeyError,
        OSError,
        ValueError,
        UnicodeError,
        TypeError,
        json.JSONDecodeError,
    ) as error:
        parser.exit(1, f"Slice 4C handoff FAILED: {error}\n")
    print(
        f"Slice 4C unsigned handoff: {surfaces} surfaces; "
        f"{operations} operations; {families} P0.2 families"
    )
    print("No human review, full-suite, release-wheel, or physical signoff implied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
