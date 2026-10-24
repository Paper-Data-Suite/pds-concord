"""Offline, deterministic Issue #140 Slice 1 source census and context matrix.

Inventory is deliberately conservative: static findings do not certify safety.
No Concord/Core modules are imported and no workspace is opened.
"""

from __future__ import annotations

import argparse
import ast
import csv
import io
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Final

SCHEMA: Final[str] = "concord_issue140_slice1_census_v1"
REL_DIR: Final[str] = "docs/audits/issue140"
SURFACES: Final[tuple[str, ...]] = (
    "concord/menu.py",
    "concord/menu_navigation.py",
    "concord/cli.py",
)
COLUMNS: Final[tuple[str, ...]] = (
    "operation_id",
    "surface",
    "ui_path",
    "source_file",
    "owner_function",
    "line",
    "boundary_kind",
    "service_or_delegate",
    "service_definition",
    "activity_modes",
    "standards_graph_condition",
    "standards_contract",
    "standards_supply",
    "core_roster",
    "activity_session_group",
    "actor",
    "workspace",
    "provenance",
    "privacy_authority",
    "record_effect",
    "snapshot_cas",
    "cancellation_recovery",
    "expected_failure",
    "evidence_status",
    "evidence_ref",
    "disposition",
    "reviewer_date",
)
SERVICE_COLUMNS: Final[tuple[str, ...]] = (
    "service_key",
    "source_file",
    "function",
    "line",
    "standards_parameter",
    "standards_default",
    "guarded_graph_load",
    "guarded_record_write",
    "internal_workspace_library_lookup",
    "contract_interpretation",
    "evidence_status",
    "follow_up",
)
# Explicitly documented candidates from #138. Status is static ONLY, not a
# demonstrated interactive failure. No other callers inherit that judgment.
CANDIDATES: Final[dict[str, dict[str, str]]] = {
    "concord/menu_activity.py": {"update_activity": "FIX_141"},
    "concord/menu_artifact.py": {
        name: "FIX_142"
        for name in (
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
    },
    "concord/menu_artifact_scoring.py": {
        "record_prepared_routine_score": "FIX_142",
    },
    "concord/menu_score_teacher_labels.py": {
        "list_scoring_scales": "FIX_142",
        "list_criterion_sets": "FIX_142",
        "show_criterion_set": "FIX_142",
    },
}


class AuditError(ValueError):
    """The census cannot claim valid, complete source coverage."""


@dataclass(frozen=True)
class Site:
    source_file: str
    owner_function: str
    line: int
    name: str
    shape: str
    ordinal: int
    source_kind: str
    standards_supply: str
    action: str


def _source_paths(root: Path) -> tuple[str, ...]:
    candidates = [root / x for x in SURFACES]
    candidates.extend(sorted((root / "concord").glob("menu_*.py")))
    candidates.extend(sorted((root / "concord/cli_app").rglob("*.py")))
    results = tuple(
        sorted({p.relative_to(root).as_posix() for p in candidates if p.is_file()})
    )
    missing = [p for p in SURFACES if p not in results]
    if missing:
        raise AuditError("Missing mandatory menu/CLI surface: " + ", ".join(missing))
    if len(results) < 4:
        raise AuditError("Menu/CLI inventory unexpectedly small")
    return results


def _expr_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        stem = _expr_name(node.value)
        return f"{stem}.{node.attr}" if stem else node.attr
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
                    result[alias.name.split(".")[0]] = alias.name.split(".")[0]
    return result


def _is_workflow(qualified: str) -> bool:
    return qualified.startswith("concord.workflows.")


def _is_menu(qualified: str) -> bool:
    return qualified.startswith(("concord.menu_", "concord.menu."))


def _service_catalog(root: Path) -> tuple[list[dict[str, str]], dict[str, str]]:
    rows: list[dict[str, str]] = []
    by_name: dict[str, list[str]] = {}
    for path in sorted((root / "concord/workflows").rglob("*.py")):
        relative = path.relative_to(root).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative)
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            keywords = node.args.kwonlyargs + node.args.args + node.args.posonlyargs
            parameter = "standards_library" in {x.arg for x in keywords}
            called = {
                _expr_name(x.func).split(".")[-1]
                for x in ast.walk(node)
                if isinstance(x, ast.Call)
            }
            guarded_load = bool(
                called & {"load_current_record_graph", "load_current_snapshot_graph"}
            )
            guarded_write = bool(called & {"commit_record_batch"})
            internal_lookup = bool(
                called & {"load_workspace_standards_library", "_standards"}
            )
            if not (parameter or guarded_load or guarded_write or internal_lookup):
                continue
            default = "unknown_or_required"
            if parameter and node.args.kw_defaults:
                for arg, value in zip(node.args.kwonlyargs, node.args.kw_defaults):
                    if arg.arg == "standards_library":
                        default = (
                            "None"
                            if isinstance(value, ast.Constant) and value.value is None
                            else "explicit_or_other"
                        )
            key = f"{relative}::{node.name}"
            by_name.setdefault(node.name, []).append(key)
            rows.append(
                {
                    "service_key": key,
                    "source_file": relative,
                    "function": node.name,
                    "line": str(node.lineno),
                    "standards_parameter": str(parameter).lower(),
                    "standards_default": default,
                    "guarded_graph_load": str(guarded_load).lower(),
                    "guarded_record_write": str(guarded_write).lower(),
                    "internal_workspace_library_lookup": str(internal_lookup).lower(),
                    "contract_interpretation": (
                        "requires_per_graph_review"
                        if (guarded_load or guarded_write)
                        else "indirect_or_neutral_to_confirm"
                    ),
                    "evidence_status": "BLOCKED_OR_UNTESTED",
                    "follow_up": "INVESTIGATE",
                }
            )
    return rows, {name: keys[0] for name, keys in by_name.items() if len(keys) == 1}


class _Reader(ast.NodeVisitor):
    def __init__(self, source: str, imports: dict[str, str]) -> None:
        self.source = source
        self.imports = imports
        self.stack: list[str] = []
        self.handlers: list[tuple[str, int]] = []
        self.calls: list[Site] = []
        self.seen: dict[tuple[str, str], int] = {}

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._function(node)

    def _function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        self.stack.append(node.name)
        self.handlers.append((".".join(self.stack), node.lineno))
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
        raw = _expr_name(node.func)
        base = raw.split(".", 1)[0]
        imported = self.imports.get(base)
        qualified = imported + raw[len(base) :] if imported else raw
        if _is_workflow(qualified):
            kind = "WORKFLOW_CALL"
        elif _is_menu(qualified):
            kind = "MENU_DELEGATION"
        else:
            kind = "OTHER_CALL"
        value = "none_visible"
        if any(x.arg == "standards_library" for x in node.keywords):
            value = "explicit_standards_keyword"
        elif any(
            x.arg is None and "standards" in _expr_name(x.value) for x in node.keywords
        ):
            value = "standards_kwargs_expansion"
        elif any(x.arg is None for x in node.keywords):
            value = "generic_kwargs_expansion_unverified"
        key = (owner, raw)
        self.seen[key] = self.seen.get(key, 0) + 1
        self.calls.append(
            Site(
                self.source,
                owner,
                node.lineno,
                raw,
                qualified,
                self.seen[key],
                kind,
                value,
                "menu" if self.source.startswith("concord/menu") else "cli",
            )
        )
        self.generic_visit(node)


def _row(**kwargs: str) -> dict[str, str]:
    return {name: kwargs.get(name, "") for name in COLUMNS}


def _make_rows(site: Site, service_map: dict[str, str]) -> dict[str, str]:
    callee = site.shape.split(".")[-1]
    key = f"{site.source_file}::{site.owner_function}::{site.name}::{site.ordinal}"
    candidate = CANDIDATES.get(site.source_file, {}).get(callee)
    confirmed_omission = (
        candidate is not None and site.standards_supply == "none_visible"
    )
    if site.source_kind == "MENU_DELEGATION":
        label = "MENU_DELEGATION"
    else:
        label = "WORKFLOW_SERVICE"
    return _row(
        operation_id=key,
        surface=site.action,
        ui_path=f"{site.owner_function} → {callee}",
        source_file=site.source_file,
        owner_function=site.owner_function,
        line=str(site.line),
        boundary_kind=label,
        service_or_delegate=site.shape,
        service_definition=service_map.get(callee, "unresolved_or_multiple"),
        activity_modes="all_modes_to_classify",
        standards_graph_condition="orientation_or_standard_backed_criteria_or_scores",
        standards_contract="conditional_per_guarded_graph; verify service contract",
        standards_supply=site.standards_supply,
        core_roster="unreviewed",
        activity_session_group="unreviewed",
        actor="unreviewed",
        workspace="unreviewed",
        provenance="unreviewed",
        privacy_authority="unreviewed",
        record_effect="read_preview_write_to_classify",
        snapshot_cas="unreviewed",
        cancellation_recovery="unreviewed",
        expected_failure=(
            "source-suspected context omission, not menu-proven"
            if confirmed_omission
            else "unverified"
        ),
        evidence_status=(
            "CODE_PATH_VERIFIED" if confirmed_omission else "BLOCKED_OR_UNTESTED"
        ),
        evidence_ref=(
            "Issue #138 P0.1/P0.2 source triage; current menu call census"
            if confirmed_omission
            else "Source census only; behavioral proof pending"
        ),
        disposition=candidate
        if confirmed_omission and candidate is not None
        else "INVESTIGATE",
        reviewer_date="pending independent contract review",
    )


def _csv_bytes(rows: list[dict[str, str]], columns: tuple[str, ...]) -> bytes:
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue().encode("utf-8")


def build(root: Path) -> dict[str, bytes]:
    surfaces = _source_paths(root)
    contracts, services = _service_catalog(root)
    rows: list[dict[str, str]] = []
    inventory: list[dict[str, Any]] = []
    for filename in surfaces:
        tree = ast.parse(
            (root / filename).read_text(encoding="utf-8"), filename=filename
        )
        reader = _Reader(filename, _imports(tree))
        reader.visit(tree)
        relevant = [
            x
            for x in reader.calls
            if x.source_kind in {"WORKFLOW_CALL", "MENU_DELEGATION"}
        ]
        for owner, line in reader.handlers:
            handler = _row(
                operation_id=f"{filename}::{owner}::ENTRY",
                surface="cli" if filename.startswith("concord/cli") else "menu",
                ui_path=owner,
                source_file=filename,
                owner_function=owner,
                line=str(line),
                boundary_kind="HANDLER_INVENTORY",
                service_or_delegate="see child callsite rows or all-call inventory",
                activity_modes="unreviewed",
                standards_graph_condition="unreviewed",
                standards_contract="unreviewed",
                standards_supply="unreviewed",
                core_roster="unreviewed",
                activity_session_group="unreviewed",
                actor="unreviewed",
                workspace="unreviewed",
                provenance="unreviewed",
                privacy_authority="unreviewed",
                record_effect="unreviewed",
                snapshot_cas="unreviewed",
                cancellation_recovery="unreviewed",
                expected_failure="unverified",
                evidence_status="BLOCKED_OR_UNTESTED",
                evidence_ref="AST handler enumeration; no runtime witness",
                disposition="INVESTIGATE",
                reviewer_date="pending human review",
            )
            rows.append(handler)
        for call in relevant:
            rows.append(_make_rows(call, services))
        inventory.append(
            {
                "source_file": filename,
                "handlers": [
                    {"owner": fn, "line": line} for fn, line in reader.handlers
                ],
                "calls": [asdict(x) for x in reader.calls],
                "count_workflow_calls": sum(
                    x.source_kind == "WORKFLOW_CALL" for x in reader.calls
                ),
                "count_menu_delegations": sum(
                    x.source_kind == "MENU_DELEGATION" for x in reader.calls
                ),
                "other_call_exclusion_reason": (
                    "Every other call remains inventoried here for explicit review: "
                    "Python builtins, UI helpers, constructors, unresolved aliases "
                    "and dynamic delegation; exclusion from the service matrix "
                    "does not certify neutrality."
                ),
            }
        )
    ids = [r["operation_id"] for r in rows]
    if len(set(ids)) != len(ids):
        raise AuditError("Duplicate matrix operation IDs")
    rows.sort(key=lambda x: x["operation_id"])
    contracts.sort(key=lambda x: x["service_key"])
    summary = {
        "schema": SCHEMA,
        "source_surfaces": surfaces,
        "surface_count": len(surfaces),
        "handler_count": sum(len(x["handlers"]) for x in inventory),
        "all_calls": sum(len(x["calls"]) for x in inventory),
        "workflow_call_count": sum(x["count_workflow_calls"] for x in inventory),
        "menu_delegation_count": sum(x["count_menu_delegations"] for x in inventory),
        "matrix_row_count": len(rows),
        "service_contract_count": len(contracts),
        "classification_scope": "AST inventory, NOT semantic qualification",
        "service_resolution_limit": (
            "Dynamic calls, aliased imports, wrappers and reexports "
            "require manual verification"
        ),
        "source_inventory": inventory,
    }
    return {
        "teacher_operation_matrix.csv": _csv_bytes(rows, COLUMNS),
        "service_context_catalog.csv": _csv_bytes(contracts, SERVICE_COLUMNS),
        "surface_inventory.json": (
            json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        ).encode("utf-8"),
    }


def _verify_baseline(root: Path) -> None:
    base = root / REL_DIR
    for f in ("baseline.json", "baseline.md"):
        if not (base / f).is_file():
            raise AuditError(f"Immutable Slice 0 baseline missing: {f}")
    with (base / "baseline.json").open("r", encoding="utf-8") as stream:
        content = json.load(stream)
    if content.get("schema") != "concord_issue140_slice0_baseline_v1":
        raise AuditError("Unexpected Slice 0 baseline schema")
    if content.get("git", {}).get("head") != "68ddd804d2733fa900ee396ac7a2ba6bd98aa819":
        raise AuditError("Unexpected frozen source commit")
    if content.get("source", {}).get("version") != "0.3.4":
        raise AuditError("Unexpected Concord source version")
    core = content.get("published_artifacts", {}).get("core_v0_6_6_wheel", {})
    if core.get("status") != "verified_published_bytes_and_metadata":
        raise AuditError("Published Core wheel was not verified in Slice 0")
    # Capture has a strict known schema: no local path/secret/student field is
    # expected. Explicitly reject a modified JSON with extra metadata keys.
    expected_keys = {
        "schema",
        "captured_utc",
        "repository",
        "git",
        "source",
        "environment",
        "published_artifacts",
        "inventory",
        "limits",
    }
    if set(content) != expected_keys:
        raise AuditError("Unexpected keys in Slice 0 manifest; inspect before staging")
    flattened = json.dumps(content)
    for token in (
        "C:" + chr(92) * 2,
        "C:" + chr(92) + "Dev" + chr(92),
        "/Users/",
        "/home/",
        "student_display_name",
        "teacher_email",
        "onedrive_path",
    ):
        if token.lower() in flattened.lower():
            raise AuditError("Sensitive or local path candidate in baseline JSON")


def run(root: Path, *, check_only: bool) -> tuple[int, int]:
    root = root.resolve()
    _verify_baseline(root)
    data = build(root)
    location = root / REL_DIR
    if not location.is_dir():
        raise AuditError("Audit directory does not exist")
    for filename, payload in data.items():
        path = location / filename
        if path.exists():
            if not path.is_file() or path.read_bytes() != payload:
                raise AuditError(f"Existing census differs from source: {filename}")
        elif check_only:
            raise AuditError(f"Required audited census missing: {filename}")
        else:
            with path.open("xb") as stream:
                stream.write(payload)
    summary = json.loads(data["surface_inventory.json"])
    return summary["matrix_row_count"], summary["all_calls"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--generate", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        rows, calls = run(args.repo, check_only=args.check)
    except (AuditError, OSError, ValueError, SyntaxError, json.JSONDecodeError) as err:
        parser.exit(1, f"Issue #140 Slice 1 census FAILED: {err}\n")
    print(f"Issue #140 Slice 1 census verified: {rows} matrix rows; {calls} callsites")
    print("All unverified outcomes remain labeled as such; no workspace was opened.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
