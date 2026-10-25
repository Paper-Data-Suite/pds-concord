"""#141: historical #140 receipt integrity and source replay remain honest."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import pytest
from issue141_frozen_audit import SnapshotError, materialize, verify_receipts

ROOT = Path(__file__).resolve().parents[1]


def _guard() -> Any:
    path = ROOT / "scripts/issue140_slice4a_guard.py"
    spec = importlib.util.spec_from_file_location("issue140_slice4a_guard", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    import sys

    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_authenticated_frozen_source_replays_original_4a_guard(tmp_path: Path) -> None:
    frozen = tmp_path / "frozen"
    manifest = materialize(ROOT, frozen)
    assert manifest["source_commit"] == ("40837d54376f70cffb9ca539d52f7e40453ec1e6")
    result = _guard().run(frozen)
    assert result.surfaces == 67
    assert result.calls == 10182
    assert result.matrix_rows == 3685
    assert result.scoped_families == 18


def test_frozen_receipt_drift_detected_without_changing_repo(tmp_path: Path) -> None:
    frozen = tmp_path / "frozen"
    materialize(ROOT, frozen)
    verify_receipts(frozen)
    target = frozen / "docs/audits/issue140/baseline.md"
    target.write_bytes(target.read_bytes() + b"\nTAMPER\n")
    with pytest.raises(SnapshotError, match="differs from merge"):
        verify_receipts(frozen)
