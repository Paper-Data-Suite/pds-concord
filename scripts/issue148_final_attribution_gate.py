"""Issue #148: fail-closed source-level disposition of Concord menu actor callsites.

Run after the menu changes, before final full-repository and installed-wheel tests.
This is a static audit of source-level candidate functions; it is NOT proof of
successful installed or human classroom acceptance and grants no permission.
"""

from __future__ import annotations

import argparse
import ast
import subprocess
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from scripts.issue148_actor_callsite_census import Callsite, inventory

MENU_MODULE_COUNT = 43
ACTOR_HELPER = "actor-resolved-no-local-review"
OTHER_CONTRACT = "confirm-without-local-actor-resolution"
REVIEWED = "action-reviewed"
LEGACY_ACTOR = "legacy-confirm-with-actor"


@dataclass(frozen=True, slots=True)
class Disposition:
    classification: str
    rationale: str
    evidence: str


# Explicit manual dispositions for every non-action-reviewed AST candidate at
# pinned #148 HEAD 0e96aea. A new, missing, or reclassified candidate is a
# mandatory review failure: do not silently assume it is harmless.
DISPOSITIONS: dict[tuple[str, str], Disposition] = {
    ("concord/menu_actor_action.py", "confirm_actor_write"): Disposition(
        ACTOR_HELPER,
        "Shared actor-review implementation; not a canonical writer.",
        "menu_actor_action.py; #148 action-review regression",
    ),
    ("concord/menu_artifact.py", "_choose_author_semantics"): Disposition(
        ACTOR_HELPER,
        "Chooses an Artifact author, a distinct identity from the recorder.",
        "#148 3D2B author/recorder tests",
    ),
    ("concord/menu_group_plan_bulk.py", "_review_batch"): Disposition(
        ACTOR_HELPER,
        "Custom actor and matching digest review, no direct commit.",
        "#148 3E6D custom bulk-review tests",
    ),
    ("concord/menu_group_plan_bulk.py", "launch_cluster_bulk_editor"): Disposition(
        ACTOR_HELPER,
        "Delegates to _review_batch, then commits its request/digest pair.",
        "#147 bulk tests; #148 3E6D",
    ),
    ("concord/menu_publication.py", "_manifest_request"): Disposition(
        ACTOR_HELPER,
        "Constructs request for later actor-prepared publication review.",
        "#148 3D3A publication tests",
    ),
    ("concord/menu_saved_grouping_revisions.py", "_current"): Disposition(
        ACTOR_HELPER,
        "Read-only resolution of an actor-scoped saved grouping.",
        "#148 3E5C revision actor tests",
    ),
    ("concord/menu_saved_grouping_revisions.py", "_show_history"): Disposition(
        ACTOR_HELPER,
        "Shows saved-grouping revisions; not a write confirmation.",
        "#148 3E5C revision actor tests",
    ),
    ("concord/menu_saved_groupings.py", "_saved"): Disposition(
        ACTOR_HELPER,
        "Reads actor-scoped saved groupings; write reviewed separately.",
        "#148 3E5A saved grouping tests",
    ),
    ("concord/menu_scoring.py", "_score_components"): Disposition(
        ACTOR_HELPER,
        "Draft-only: nested non-score StatusReason is rebound at final review.",
        "#148 3E6E nested Score provenance tests",
    ),
    ("concord/menu_grouping_signal.py", "_import_csv"): Disposition(
        OTHER_CONTRACT,
        "Core grouping-signal import request has no actor field.",
        "GroupingSignal import request and #53 boundary tests",
    ),
    ("concord/menu_publication.py", "_register"): Disposition(
        OTHER_CONTRACT,
        "Core academic-work registry contract has no actor field.",
        "Academic Work Registration service contract",
    ),
    ("concord/menu_publication.py", "_update_registration"): Disposition(
        OTHER_CONTRACT,
        "Core registry update request has no actor field.",
        "Core AcademicWorkRegistrationRequest contract",
    ),
    ("concord/menu_publication.py", "_withdraw"): Disposition(
        OTHER_CONTRACT,
        "Core publication withdrawal accepts reason, not WorkflowActor.",
        "Concord/Core publication withdrawal service contract",
    ),
    ("concord/menu_publication.py", "_rebuild_catalog"): Disposition(
        OTHER_CONTRACT,
        "Rebuilds derived Core catalog; no actor-provenance field.",
        "Core academic-catalog rebuild contract",
    ),
    ("concord/menu_saved_groupings.py", "_collect_decisions"): Disposition(
        OTHER_CONTRACT,
        "ACKNOWLEDGE is an intermediate roster decision, not a write.",
        "#148 3E5A final saved-grouping actor review",
    ),
    ("concord/menu_scan.py", "_route"): Disposition(
        OTHER_CONTRACT,
        (
            "Initial Core PDS2 scan intake is actor-less; "
            "routing failure review has a recorder."
        ),
        "routing/scan_intake.py and #148 routing review tests",
    ),
    ("concord/menu_teacher_settings.py", "_setup"): Disposition(
        OTHER_CONTRACT,
        "Explicit write to local Concord-only profile, not academic state.",
        "#148 teacher-attribution storage/Settings tests",
    ),
    ("concord/menu_teacher_settings.py", "_rename"): Disposition(
        OTHER_CONTRACT,
        "Local profile display-name edit, with CAS and confirmation.",
        "#148 teacher-attribution storage/Settings tests",
    ),
    ("concord/menu_teacher_settings.py", "_replace"): Disposition(
        OTHER_CONTRACT,
        "Local future-only actor-ID replacement, not a record write.",
        "#148 teacher-attribution storage/Settings tests",
    ),
    ("concord/menu_teacher_settings.py", "_reset"): Disposition(
        OTHER_CONTRACT,
        "Confirmed local profile reset, not an academic record write.",
        "#148 teacher-attribution storage/Settings tests",
    ),
}

# Representative consequential menu surfaces that must remain action-reviewed.
# This is a witness list, NOT the entirety of the action-reviewed population.
MUST_REVIEW: frozenset[tuple[str, str]] = frozenset(
    {
        ("concord/menu_activity.py", "_copy_activity"),
        ("concord/menu_activity.py", "_update_activity_field"),
        ("concord/menu_guided_activity.py", "_create_fresh"),
        ("concord/menu_guided_activity.py", "_create_from_activity"),
        ("concord/menu_guided_activity.py", "_start_packet_from_template"),
        ("concord/menu_packet_generation.py", "_generate"),
        ("concord/menu_packet_generation.py", "_render_generation"),
        ("concord/menu_packet_generation.py", "_render_instance"),
        ("concord/menu_scoring.py", "_record_score"),
        ("concord/menu_scoring.py", "_revise_score"),
        ("concord/menu_publication.py", "_generate"),
        ("concord/menu_publication.py", "_publish"),
        (
            "concord/menu_saved_operational_grouping.py",
            "save_grouping_from_existing_groups",
        ),
        ("concord/menu_saved_grouping_revisions.py", "_change"),
        ("concord/menu_artifact.py", "_add_author"),
        ("concord/menu_group.py", "_create_group"),
        ("concord/menu_session.py", "_add"),
        ("concord/menu_template.py", "_create"),
        ("concord/menu_packet.py", "_create"),
    }
)

# These actor-less menu operations must keep their existing service contract.
# Validate source calls rather than assuming a method name proves safety.
CORE_BOUNDARIES: dict[tuple[str, str], str] = {
    ("concord/menu_grouping_signal.py", "_import_csv"): "import_grouping_signal_csv",
    ("concord/menu_publication.py", "_register"): "register_concord_academic_work",
    (
        "concord/menu_publication.py",
        "_update_registration",
    ): "update_academic_work_registration",
    (
        "concord/menu_publication.py",
        "_withdraw",
    ): "withdraw_concord_academic_result_publication",
    (
        "concord/menu_publication.py",
        "_rebuild_catalog",
    ): "rebuild_full_academic_catalog",
    ("concord/menu_scan.py", "_route"): "route_scan_sources",
}


def _key(row: Callsite) -> tuple[str, str]:
    return row.path, row.function


def validate_rows(rows: tuple[Callsite, ...]) -> None:
    """Fail closed on any undisposed top-level AST candidate or review regression."""
    seen: dict[tuple[str, str], Callsite] = {}
    for row in rows:
        key = _key(row)
        if key in seen:
            raise ValueError(f"Duplicate menu callsite candidate: {key}")
        seen[key] = row
    legacy = sorted(
        key for key, row in seen.items() if row.classification == LEGACY_ACTOR
    )
    unexpected = sorted(
        key
        for key, row in seen.items()
        if row.classification != REVIEWED and key not in DISPOSITIONS
    )
    missing = sorted(key for key in DISPOSITIONS if key not in seen)
    misplaced = sorted(
        key
        for key, disposition in DISPOSITIONS.items()
        if key in seen and seen[key].classification != disposition.classification
    )
    uncovered = sorted(
        key
        for key in MUST_REVIEW
        if key not in seen or seen[key].classification != REVIEWED
    )
    if legacy or unexpected or missing or misplaced or uncovered:
        raise ValueError(
            "Concord #148 attribution census requires explicit review: "
            f"legacy_actor={legacy}; unclassified={unexpected}; "
            f"missing_disposition={missing}; reclassified={misplaced}; "
            f"review_regressions={uncovered}"
        )


def _function(repo: Path, path: str, name: str) -> ast.FunctionDef:
    source = (repo / path).read_text(encoding="utf-8")
    tree = ast.parse(source, filename=path)
    matches = [
        item
        for item in tree.body
        if isinstance(item, ast.FunctionDef) and item.name == name
    ]
    if len(matches) != 1:
        raise ValueError(f"Expected one canonical function: {path}::{name}")
    return matches[0]


def _calls(fn: ast.FunctionDef, name: str) -> list[ast.Call]:
    return [
        item
        for item in ast.walk(fn)
        if isinstance(item, ast.Call)
        and (
            (isinstance(item.func, ast.Name) and item.func.id == name)
            or (isinstance(item.func, ast.Attribute) and item.func.attr == name)
        )
    ]


def validate_contracts(repo: Path) -> None:
    """Bind service dispositions to named, actual source callsites."""
    for (path, fn_name), call_name in CORE_BOUNDARIES.items():
        fn = _function(repo, path, fn_name)
        calls = _calls(fn, call_name)
        if len(calls) != 1:
            raise ValueError(f"Core boundary changed: {path}::{fn_name}")
        if any(arg.arg == "actor" for arg in calls[0].keywords):
            raise ValueError(f"Unexpected actor injection: {path}::{fn_name}")

    for fn_name, canonical in (
        ("_record_score", "AddScoreRequest"),
        ("_revise_score", "ReplaceScoreRequest"),
    ):
        fn = _function(repo, "concord/menu_scoring.py", fn_name)
        calls = _calls(fn, canonical)
        if len(calls) != 1:
            raise ValueError(f"Score request changed: {fn_name}")
        status = [arg.value for arg in calls[0].keywords if arg.arg == "status_reason"]
        if len(status) != 1 or not isinstance(status[0], ast.Call):
            raise ValueError(f"Score nested status provenance changed: {fn_name}")
        nested = status[0]
        if not isinstance(nested.func, ast.Name) or (
            nested.func.id != "_reviewed_score_status_reason"
        ):
            raise ValueError(f"Nested status reason not actor-bound: {fn_name}")
        if (
            len(nested.args) != 2
            or not isinstance(nested.args[1], ast.Name)
            or nested.args[1].id != "actor"
        ):
            raise ValueError(f"Nested status reason uses unreviewed actor: {fn_name}")

    bulk = _function(
        repo, "concord/menu_group_plan_bulk.py", "launch_cluster_bulk_editor"
    )
    commits = _calls(bulk, "commit_bulk_planned_group_edit")
    if (
        len(commits) != 1
        or not commits[0].args
        or (
            not isinstance(commits[0].args[0], ast.Name)
            or commits[0].args[0].id != "reviewed_request"
        )
    ):
        raise ValueError("Bulk GroupPlan commit no longer uses reviewed request")
    digests = [arg.value for arg in commits[0].keywords if arg.arg == "review_digest"]
    if (
        len(digests) != 1
        or not isinstance(digests[0], ast.Attribute)
        or (
            digests[0].attr != "review_digest"
            or not isinstance(digests[0].value, ast.Name)
            or digests[0].value.id != "reviewed_preview"
        )
    ):
        raise ValueError("Bulk GroupPlan commit no longer uses reviewed digest")


def evaluate(repo: Path) -> tuple[int, tuple[Callsite, ...]]:
    n, rows = inventory(repo)
    if n != MENU_MODULE_COUNT:
        raise ValueError(f"Concord menu module set changed: {n} != {MENU_MODULE_COUNT}")
    validate_rows(rows)
    validate_contracts(repo)
    return n, rows


def render_report(head: str, count: int, rows: tuple[Callsite, ...]) -> str:
    totals = Counter(row.classification for row in rows)
    lines = [
        "# Concord #148 — final menu attribution disposition (source gate)",
        "",
        f"**Source HEAD:** `{head}`",
        f"**Menu modules enumerated:** {count}",
        f"**AST candidate functions:** {len(rows)}",
        "",
        "## Candidate classifications",
        "",
        "| Classification | Functions |",
        "|---|---:|",
    ]
    for label in (REVIEWED, LEGACY_ACTOR, ACTOR_HELPER, OTHER_CONTRACT):
        lines.append(f"| `{label}` | {totals[label]} |")
    lines += [
        "",
        "## Explicit dispositions for all non-action-reviewed functions",
        "",
        "| Function | Classification | Disposition | Evidence |",
        "|---|---|---|---|",
    ]
    for (path, name), disp in sorted(DISPOSITIONS.items()):
        lines.append(
            f"| `{path}::{name}` | `{disp.classification}` | "
            f"{disp.rationale} | {disp.evidence} |"
        )
    lines += [
        "",
        "## Evidence boundary",
        "",
        "This report is an AST inventory and manual service-contract disposition. "
        "It does **not** prove every indirect or aliased operation safe, nor "
        "prove Windows installed-wheel or Suite foreground behavior.",
        "",
        "Final release gate remains: full repository tests once, full Ruff/mypy, "
        "package/build/install, official Core-wheel acceptance, Windows/Linux CI "
        "and PR review. Direct CLI actor flags remain separately verified.",
        "",
    ]
    return "\n".join(lines)


def _head(repo: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    repo = args.repo.resolve(strict=True)
    actual = _head(repo)
    if actual != args.expected_head:
        raise SystemExit(f"Concord #148 census HEAD mismatch: {actual}")
    n, rows = evaluate(repo)
    report = render_report(actual, n, rows)
    out = args.out
    if out.is_symlink() or (out.exists() and not out.is_file()):
        raise SystemExit("Unsafe census output target")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8", newline="\n")
    totals = Counter(row.classification for row in rows)
    print(
        f"CENSUS QUALIFIED: {n} menu modules; {len(rows)} candidate functions; "
        f"{totals[REVIEWED]} action-reviewed, {totals[ACTOR_HELPER]} "
        f"indirect actor, {totals[OTHER_CONTRACT]} other contracts; "
        "zero undisposed AST candidates",
        flush=True,
    )
    print(f"Wrote report: {out}", flush=True)


if __name__ == "__main__":
    main()
