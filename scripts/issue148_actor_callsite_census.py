"""#148: static Concord teacher-menu attribution census (no workspace I/O).

This inventory deliberately reports *candidates*, not proof of unsafe writes:
actor acquisition in delegated helpers or read-only paths needs manual review.
No academic records, local teacher profiles or Core settings are opened.
"""

from __future__ import annotations

import argparse
import ast
import subprocess
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

SCHEMA = 1
REVIEW = frozenset({"confirm_actor_write", "confirm_prepared_actor_write"})


@dataclass(frozen=True)
class Callsite:
    path: str
    function: str
    line: int
    actor_resolution: int
    actor_review: int
    legacy_review: int
    explicit_actor: int
    classification: str


def _call_name(call: ast.Call) -> str | None:
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return None


def inspect_text(path: str, source: str) -> tuple[Callsite, ...]:
    """Return one row per function that resolves actors or reviews a write.

    The source path is a repository-relative label, never a file read target.
    An inner function's calls are attributed to its outer function as an
    additional conservative candidate rather than being silently dropped.
    """
    tree = ast.parse(source, filename=path)
    records: list[Callsite] = []
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        names = [
            _call_name(call) for call in ast.walk(node) if isinstance(call, ast.Call)
        ]
        actor_resolution = sum(
            name in {"require_actor", "actor_for_action"} for name in names
        )
        actor_review = sum(name in REVIEW for name in names)
        legacy_review = names.count("confirm_write")
        explicit_actor = sum(
            kw.arg == "actor"
            for n in ast.walk(node)
            if isinstance(n, ast.Call)
            for kw in n.keywords
        )
        if not (actor_resolution or actor_review or legacy_review):
            continue
        if actor_review:
            classification = "action-reviewed"
        elif actor_resolution and legacy_review:
            classification = "legacy-confirm-with-actor"
        elif actor_resolution:
            classification = "actor-resolved-no-local-review"
        else:
            classification = "confirm-without-local-actor-resolution"
        records.append(
            Callsite(
                path=path,
                function=node.name,
                line=node.lineno,
                actor_resolution=actor_resolution,
                actor_review=actor_review,
                legacy_review=legacy_review,
                explicit_actor=explicit_actor,
                classification=classification,
            )
        )
    return tuple(records)


def inventory(repo: Path) -> tuple[int, tuple[Callsite, ...]]:
    files = sorted((repo / "concord").glob("menu*.py"))
    if not files or not (repo / "pyproject.toml").is_file():
        raise ValueError("Expected Concord repository menu sources are missing")
    rows: list[Callsite] = []
    for file in files:
        if file.is_symlink() or not file.is_file():
            raise ValueError(f"Unsafe or missing menu source: {file.name}")
        label = file.relative_to(repo).as_posix()
        rows.extend(inspect_text(label, file.read_text(encoding="utf-8")))
    rows.sort(key=lambda item: (item.path, item.line, item.function))
    return len(files), tuple(rows)


def render_report(head: str, file_count: int, rows: tuple[Callsite, ...]) -> str:
    counts = Counter(row.classification for row in rows)
    lines = [
        "# Concord #148 — Slice 3E1 actor callsite census",
        "",
        f"**Baseline Git HEAD:** `{head}`",
        f"**Menu Python modules scanned:** {file_count}",
        f"**Functions with an actor-resolution or confirmation call:** {len(rows)}",
        "",
        "## Static classification totals",
        "",
        "| Class | Function count |",
        "|---|---:|",
    ]
    for category in (
        "action-reviewed",
        "legacy-confirm-with-actor",
        "actor-resolved-no-local-review",
        "confirm-without-local-actor-resolution",
    ):
        lines.append(f"| `{category}` | {counts[category]} |")
    lines.extend(
        [
            "",
            "## Interpretation and limitations",
            "",
            "- `action-reviewed`: an action-scoped actor confirmation helper is "
            "called inside this function; this alone does not prove every "
            "request or receipt forwards the reviewed actor.",
            "- `legacy-confirm-with-actor`: an actor is resolved and a legacy "
            "confirmation appears in this function; inspect whether this is "
            "a consequential canonical write that needs the actor override.",
            "- `actor-resolved-no-local-review`: includes orchestration helpers, "
            "authorship semantics, delegates, and potentially uncovered writes. "
            "It is a triage queue, not a blanket security-failure assertion.",
            "- `confirm-without-local-actor-resolution`: may be a Core operation "
            "whose existing contract has no WorkflowActor; do not invent one.",
            "- AST nesting and aliasing can hide indirect paths. This is a "
            "complete static enumeration of top-level `menu*.py` functions, "
            "**not** end-to-end proof of authorization or deployed acceptance.",
            "- Direct noninteractive CLI retains explicit actor requirements. "
            "No real student data, user profiles, or OS config files were read.",
            "",
            "## All candidate functions",
            "",
            "| Source:line | Function | Classification | Actor resolutions | "
            "Actor reviews | Legacy reviews | `actor=` args |",
            "|---|---|---|---:|---:|---:|---:|",
        ]
    )
    for row in rows:
        lines.append(
            f"| `{row.path}:{row.line}` | `{row.function}` | "
            f"`{row.classification}` | {row.actor_resolution} | "
            f"{row.actor_review} | {row.legacy_review} | "
            f"{row.explicit_actor} |"
        )
    lines.extend(
        [
            "",
            "## Follow-on acceptance gate",
            "",
            "1. Manually disposition each `legacy-confirm-with-actor` and "
            "`actor-resolved-no-local-review` function as an actor-attributed "
            "write needing action review, an already-covered delegated write, "
            "a non-mutating helper, or a different service contract.",
            "2. Convert uncovered consequential writes in bounded slices, "
            "retaining exact review/actor forwarding, CAS, privacy, and "
            "no-write cancellation safeguards.",
            "3. Re-run this source-pinned census, the full Concord suite, "
            "strict typing, packaging, installed-wheel acceptance, and CI "
            "**before** marking #148 merge-ready.",
            "",
        ]
    )
    return "\n".join(lines)


def current_head(repo: Path) -> str:
    p = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return p.stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--expected-head", required=True)
    args = parser.parse_args()
    repo = args.repo.resolve(strict=True)
    head = current_head(repo)
    if head != args.expected_head:
        raise SystemExit(f"HEAD mismatch: expected {args.expected_head}, got {head}")
    n, rows = inventory(repo)
    document = render_report(head, n, rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(document, encoding="utf-8", newline="\n")
    print(
        f"CENSUS: {n} menu modules, {len(rows)} candidate functions; "
        "classification is not a final acceptance verdict",
        flush=True,
    )
    for label, total in sorted(Counter(r.classification for r in rows).items()):
        print(f"  {label}: {total}", flush=True)


if __name__ == "__main__":
    main()
