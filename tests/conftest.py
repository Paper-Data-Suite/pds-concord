from __future__ import annotations

import json
import shutil
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "core_v0_6" / "baseline_context.json"


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def load_strict_json(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="strict")

    def reject_constant(value: str) -> None:
        raise ValueError(f"Non-standard JSON number: {value}")

    value = json.loads(
        text,
        object_pairs_hook=_unique_pairs,
        parse_constant=reject_constant,
    )
    if not isinstance(value, dict):
        raise ValueError("Fixture root must be an object.")
    return value


@pytest.fixture(scope="session")
def baseline_context() -> dict[str, Any]:
    return load_strict_json(FIXTURE_PATH)


@pytest.fixture(scope="session")
def built_dist(tmp_path_factory: pytest.TempPathFactory) -> Path:
    destination = tmp_path_factory.mktemp("dist")
    source = tmp_path_factory.mktemp("source")
    shutil.copytree(
        ROOT,
        source,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            "build",
            "dist",
            "*.egg-info",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
        ),
    )
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(destination)],
        cwd=source,
        check=True,
    )
    return destination


@pytest.fixture(scope="session")
def built_wheel(built_dist: Path) -> Path:
    wheels = list(built_dist.glob("*.whl"))
    assert len(wheels) == 1
    return wheels[0]


@pytest.fixture
def unchanged_directory(tmp_path: Path) -> Iterator[Path]:
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    yield tmp_path
    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    assert after == before
