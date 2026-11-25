"""Read-only #153 Slice A1 teacher-interface callsite inventory.

This is a syntactic census, not semantic classification or conformance.
Run from any directory; JSON is written only to stdout.
"""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CALLS = frozenset(
    {
        "input",
        "clear_screen",
        "print_menu_header",
        "print_navigation",
        "parse_menu_navigation",
        "parse_navigation_choice",
        "pause_for_user",
        "prompt_text",
        "prompt_exact_text",
        "prompt_positive_int",
        "select_one",
        "select_many",
        "confirm_write",
        "confirm_actor_write",
        "show_result",
        "handle_write_error",
        "prompt_conflict_reload",
        "show_partial_success",
        "teacher_planned_date",
        "teacher_recorded_instant",
        "launch_menu",
        "parse_shared_teacher_command",
        "print_teacher_header",
    }
)


def _call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def _source_paths() -> tuple[Path, ...]:
    package = ROOT / "concord"
    return tuple(
        sorted(
            {
                package / "menu.py",
                *package.glob("menu_*.py"),
                package / "cli.py",
                package / "cli_app" / "main.py",
                package / "cli_app" / "handlers" / "menu.py",
            }
        )
    )


def _inventory_file(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    source = raw.decode("utf-8")
    tree = ast.parse(source, filename=str(path.relative_to(ROOT)))
    calls: list[dict[str, object]] = []
    mentions: list[dict[str, object]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = _call_name(node)
            if name in CALLS:
                calls.append(
                    {
                        "line": node.lineno,
                        "column": node.col_offset,
                        "call": name,
                        "first_argument": (
                            ast.unparse(node.args[0]) if node.args else None
                        ),
                        "keywords": [item.arg for item in node.keywords],
                    }
                )
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and ":notes" in node.value.casefold()
        ):
            mentions.append(
                {
                    "line": node.lineno,
                    "column": node.col_offset,
                    "literal": node.value,
                }
            )
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "calls": sorted(
            calls,
            key=lambda row: (
                str(row["line"]).zfill(8),
                str(row["column"]).zfill(8),
            ),
        ),
        "notes_literal_mentions": sorted(
            mentions,
            key=lambda row: (
                str(row["line"]).zfill(8),
                str(row["column"]).zfill(8),
            ),
        ),
    }


def main() -> None:
    files = [_inventory_file(path) for path in _source_paths()]
    print(
        json.dumps(
            {
                "schema": "concord.issue153.callsite-census.v1",
                "classification": "syntactic_only",
                "files": files,
            },
            indent=2,
            ensure_ascii=True,
        )
    )


if __name__ == "__main__":
    main()
