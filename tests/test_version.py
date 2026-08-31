from __future__ import annotations

import ast
from pathlib import Path

import concord


def test_initial_version() -> None:
    assert concord.__version__ == "0.3.0"


def test_version_has_one_authoritative_literal() -> None:
    root = Path(__file__).resolve().parents[1]
    declarations: list[tuple[Path, str]] = []
    for path in (root / "concord").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Assign)
                and any(
                    isinstance(target, ast.Name) and target.id == "__version__"
                    for target in node.targets
                )
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
            ):
                declarations.append((path, node.value.value))
    assert declarations == [(root / "concord" / "_version.py", "0.3.0")]
