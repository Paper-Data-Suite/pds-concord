"""Read-only #140 Slice 4A audit guard for frozen teacher-menu coverage.

This is an inventory and review gate, not a proof of business correctness.
It does not import Concord/Core, discover a workspace, or modify files.
"""

from __future__ import annotations

import argparse
import ast
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any, Final, NamedTuple

BASE: Final[str] = "docs/audits/issue140"
REQUIRED: Final[tuple[str, ...]] = (
    "concord/menu.py",
    "concord/menu_navigation.py",
    "concord/cli.py",
)
BOUNDARIES: Final[frozenset[str]] = frozenset({"WORKFLOW_CALL", "MENU_DELEGATION"})
GUARD_STATES: Final[frozenset[str]] = frozenset(
    {
        "SYNTHETIC_MENU_REPRODUCED",
        "SYNTHETIC_DISPLAY_DEGRADED",
        "BLOCKED_OR_UNTESTED",
    }
)
EXCEPTION_FILE: Final[str] = "concord/workflows/artifact_page.py"
EXCEPTION_FUNCTION: Final[str] = "prepare_artifact_pages"
EXCEPTION_TEST: Final[str] = (
    "tests/test_issue140_slice3a_triage.py::"
    "test_page_preparation_uses_explicit_or_internal_canonical_context_without_write"
)


class GuardError(ValueError):
    """An existing audit has unexplained source, evidence, or schema drift."""


class Coverage(NamedTuple):
    surfaces: int
    calls: int
    matrix_rows: int
    scoped_families: int


def _expression(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _expression(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return "<dynamic>"


def _imports(tree: ast.Module) -> dict[str, str]:
    result: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.level == 0:
                prefix = node.module
            elif node.module.startswith("workflows"):
                prefix = "concord." + node.module
            else:
                continue
            for alias in node.names:
                result[alias.asname or alias.name] = prefix + "." + alias.name
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname:
                    result[alias.asname] = alias.name
                else:
                    name = alias.name.split(".")[0]
                    result[name] = name
    return result


class _Reader(ast.NodeVisitor):
    def __init__(self, source: str, imports: dict[str, str]) -> None:
        self.source = source
        self.imports = imports
        self.stack: list[str] = []
        self.handlers: list[dict[str, Any]] = []
        self.calls: list[dict[str, Any]] = []
        self.seen: dict[tuple[str, str], int] = {}

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node)

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        self.stack.append(node.name)
        self.handlers.append({"owner": ".".join(self.stack), "line": node.lineno})
        for part in node.body:
            self.visit(part)
        self.stack.pop()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.stack.append(node.name)
        for part in node.body:
            self.visit(part)
        self.stack.pop()

    def visit_Call(self, node: ast.Call) -> None:
        owner = ".".join(self.stack) if self.stack else "<module>"
        raw = _expression(node.func)
        base = raw.split(".", 1)[0]
        imported = self.imports.get(base)
        qualified = imported + raw[len(base) :] if imported else raw
        if qualified.startswith("concord.workflows."):
            kind = "WORKFLOW_CALL"
        elif qualified.startswith(("concord.menu_", "concord.menu.")):
            kind = "MENU_DELEGATION"
        else:
            kind = "OTHER_CALL"
        supply = "none_visible"
        if any(keyword.arg == "standards_library" for keyword in node.keywords):
            supply = "explicit_standards_keyword"
        elif any(
            keyword.arg is None and "standards" in _expression(keyword.value)
            for keyword in node.keywords
        ):
            supply = "standards_kwargs_expansion"
        elif any(keyword.arg is None for keyword in node.keywords):
            supply = "generic_kwargs_expansion_unverified"
        key = (owner, raw)
        self.seen[key] = self.seen.get(key, 0) + 1
        self.calls.append(
            {
                "source_file": self.source,
                "owner_function": owner,
                "line": node.lineno,
                "name": raw,
                "shape": qualified,
                "ordinal": self.seen[key],
                "source_kind": kind,
                "standards_supply": supply,
                "action": "menu" if self.source.startswith("concord/menu") else "cli",
            }
        )
        self.generic_visit(node)


def _source_paths(root: Path) -> tuple[str, ...]:
    paths = [root / name for name in REQUIRED]
    paths.extend(sorted((root / "concord").glob("menu_*.py")))
    paths.extend(sorted((root / "concord/cli_app").rglob("*.py")))
    actual = tuple(
        sorted({p.relative_to(root).as_posix() for p in paths if p.is_file()})
    )
    missing = sorted(set(REQUIRED) - set(actual))
    if missing:
        raise GuardError(f"Mandatory teacher-menu source absent: {missing}")
    return actual


def _read_source(root: Path, path: str) -> _Reader:
    source = root / path
    tree = ast.parse(source.read_text(encoding="utf-8"), filename=path)
    result = _Reader(path, _imports(tree))
    result.visit(tree)
    return result


def _difference(label: str, old: Counter[str], new: Counter[str]) -> None:
    added = list((new - old).elements())
    missing = list((old - new).elements())
    if added or missing:
        raise GuardError(
            f"{label}: added={sorted(added)[:5]}, "
            f"missing={sorted(missing)[:5]}; review audit inventory"
        )


def _surface_guard(root: Path, summary: dict[str, Any]) -> int:
    expected = tuple(summary["source_surfaces"])
    actual = _source_paths(root)
    _difference("Teacher-menu surfaces", Counter(expected), Counter(actual))
    entries = summary["source_inventory"]
    if len(entries) != len(expected) or len(set(expected)) != len(expected):
        raise GuardError("Frozen source-inventory coverage is inconsistent")
    by_file = {item["source_file"]: item for item in entries}
    if set(by_file) != set(expected):
        raise GuardError("Source-inventory entries do not match surface list")
    total_calls = 0
    keys = (
        "source_file",
        "owner_function",
        "line",
        "name",
        "shape",
        "ordinal",
        "source_kind",
        "standards_supply",
        "action",
    )
    for filename in expected:
        current = _read_source(root, filename)
        frozen = by_file[filename]
        _difference(
            f"Handler drift in {filename}",
            Counter(json.dumps(item, sort_keys=True) for item in frozen["handlers"]),
            Counter(json.dumps(item, sort_keys=True) for item in current.handlers),
        )
        _difference(
            f"Callsite drift in {filename}",
            Counter(
                json.dumps({k: item[k] for k in keys}, sort_keys=True)
                for item in frozen["calls"]
            ),
            Counter(
                json.dumps({k: item[k] for k in keys}, sort_keys=True)
                for item in current.calls
            ),
        )
        total_calls += len(current.calls)
    if total_calls != summary["all_calls"]:
        raise GuardError("Frozen all-call count does not match current source")
    return total_calls


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or len(set(reader.fieldnames)) != len(
            reader.fieldnames
        ):
            raise GuardError(f"Invalid CSV header: {path.name}")
        rows = list(reader)
    if any(None in row or any(value is None for value in row.values()) for row in rows):
        raise GuardError(f"Invalid CSV row widths: {path.name}")
    return rows


def _matrix_guard(summary: dict[str, Any], rows: list[dict[str, str]]) -> None:
    expected: dict[str, tuple[str, str, str, str]] = {}
    for item in summary["source_inventory"]:
        filename = item["source_file"]
        for handler in item["handlers"]:
            key = f"{filename}::{handler['owner']}::ENTRY"
            if key in expected:
                raise GuardError(f"Duplicate source handler identity: {key}")
            expected[key] = (
                filename,
                "HANDLER_INVENTORY",
                str(handler["line"]),
                "",
            )
        for call in item["calls"]:
            if call["source_kind"] not in BOUNDARIES:
                continue
            key = (
                f"{filename}::{call['owner_function']}::"
                f"{call['name']}::{call['ordinal']}"
            )
            kind = (
                "WORKFLOW_SERVICE"
                if call["source_kind"] == "WORKFLOW_CALL"
                else "MENU_DELEGATION"
            )
            if key in expected:
                raise GuardError(f"Duplicate source callsite identity: {key}")
            expected[key] = (
                filename,
                kind,
                str(call["line"]),
                call["shape"],
            )
    keys = [row.get("operation_id", "") for row in rows]
    if len(rows) != summary["matrix_row_count"]:
        raise GuardError("Teacher-operation matrix row count changed")
    if len(keys) != len(set(keys)):
        raise GuardError("Duplicate teacher-operation ID in matrix")
    _difference("Teacher-operation IDs", Counter(expected.keys()), Counter(keys))
    for row in rows:
        key = row["operation_id"]
        filename, kind, line, service = expected[key]
        if (
            row.get("source_file") != filename
            or row.get("boundary_kind") != kind
            or row.get("line") != line
        ):
            raise GuardError(f"Source/handler/boundary mismatch: {key}")
        if service and row.get("service_or_delegate") != service:
            raise GuardError(f"Service alias changed: {key}")
        if not row.get("evidence_status") or not row.get("disposition"):
            raise GuardError(f"Unclassified operation missing status: {key}")


def _scoped_guard(
    root: Path,
    matrix: list[dict[str, str]],
) -> int:
    candidates = _read_csv(root / BASE / "slice3a_candidate_boundaries.csv")
    classified = _read_csv(root / BASE / "slice3e_scoped_dispositions.csv")
    if len(candidates) != len(classified) or len(classified) != 18:
        raise GuardError("Expected 18 audited P0.2 service families")
    if len({r["service_name"] for r in classified}) != len(classified):
        raise GuardError("Duplicate P0.2 service classification")
    for original, disposition in zip(candidates, classified, strict=True):
        key = (original["source_file"], original["service_name"])
        if key != (disposition["source_file"], disposition["service_name"]):
            raise GuardError(f"P0.2 evidence order or identity changed: {key}")
        if disposition["slice3e_evidence_status"] not in GUARD_STATES:
            raise GuardError(f"Unsupported claim for {key}")
        if not disposition["owner"] or not disposition["finding_scope"]:
            raise GuardError(f"Missing owner or finding scope: {key}")
        if (
            disposition["call_lines"] != original["call_lines"]
            or disposition["calls"] != original["calls"]
        ):
            raise GuardError(f"P0.2 source-line/count mapping changed: {key}")
        site_rows = [
            row
            for row in matrix
            if row["source_file"] == original["source_file"]
            and row["boundary_kind"] == "WORKFLOW_SERVICE"
            and row["service_or_delegate"].split(".")[-1] == original["service_name"]
        ]
        expected_lines = original["call_lines"].split(";")
        if sorted(row["line"] for row in site_rows) != sorted(expected_lines):
            raise GuardError(
                f"Matrix/P0.2 service witness mismatch: {key}; "
                "inspect service aliases and captured source sites"
            )
    return len(classified)


def _exception_guard(root: Path) -> None:
    file = root / EXCEPTION_FILE
    module = ast.parse(file.read_text(encoding="utf-8"), filename=EXCEPTION_FILE)
    candidates = [
        node
        for node in module.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == EXCEPTION_FUNCTION
    ]
    if len(candidates) != 1:
        raise GuardError("Internal-Standards resolution exception is missing")
    calls = [node for node in ast.walk(candidates[0]) if isinstance(node, ast.Call)]
    if not any(_expression(c.func) == "_standards" for c in calls):
        raise GuardError("Artifact Page exception lost internal Standards lookup")
    for service in ("load_current_record_graph", "commit_record_batch"):
        forwarding = [
            c
            for c in calls
            if _expression(c.func) == service
            and any(
                k.arg == "standards_library"
                and isinstance(k.value, ast.Name)
                and k.value.id == "library"
                for k in c.keywords
            )
        ]
        if not forwarding:
            raise GuardError(f"Artifact Page exception lost forwarding: {service}")
    witness_path, _, test_name = EXCEPTION_TEST.partition("::")
    witness = ast.parse(
        (root / witness_path).read_text(encoding="utf-8"),
        filename=witness_path,
    )
    if not any(
        isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == test_name
        for n in witness.body
    ):
        raise GuardError("Artifact Page exception's focused witness is missing")


def run(root: Path) -> Coverage:
    root = root.resolve()
    base = root / BASE
    with (base / "surface_inventory.json").open(encoding="utf-8") as stream:
        summary = json.load(stream)
    if summary.get("schema") != "concord_issue140_slice1_census_v1":
        raise GuardError("Unknown frozen Slice 1 census schema")
    calls = _surface_guard(root, summary)
    matrix = _read_csv(base / "teacher_operation_matrix.csv")
    _matrix_guard(summary, matrix)
    scoped = _scoped_guard(root, matrix)
    _exception_guard(root)
    return Coverage(len(summary["source_surfaces"]), calls, len(matrix), scoped)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--check", action="store_true", required=True)
    args = parser.parse_args()
    try:
        coverage = run(args.repo)
    except (
        GuardError,
        KeyError,
        OSError,
        SyntaxError,
        UnicodeError,
        ValueError,
    ) as error:
        parser.exit(1, f"Issue #140 Slice 4A guard FAILED: {error}\n")
    print(
        "Slice 4A guarded: "
        f"{coverage.surfaces} surfaces, {coverage.calls} AST calls, "
        f"{coverage.matrix_rows} operations, "
        f"{coverage.scoped_families} scoped P0.2 families"
    )
    print(
        "Internal Standards-resolution exception: forwarding only; "
        "positive returned-work qualification still outstanding"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
