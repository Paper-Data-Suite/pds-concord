"""Offline, source-only Issue #140 Slice 0 regression/identity checks."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "issue140_slice0_baseline.py"


def _module() -> Any:
    spec = importlib.util.spec_from_file_location("issue140_slice0_baseline", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_slice0_known_immutable_release_identity() -> None:
    audit = _module()
    contract = audit._source_contract(ROOT)
    assert contract["version"] == "0.3.4"
    assert "pds-core>=0.6.6,<0.7" in contract["dependencies"]
    assert len(contract["pyproject_sha256"]) == 64


def test_slice0_existing_regressions_and_inventory() -> None:
    audit = _module()
    inventory = audit._inventory(ROOT)
    menu = inventory["source_surfaces"]["teacher_menu_modules"]
    assert "concord/menu_activity.py" in menu
    assert "concord/menu_artifact.py" in menu
    assert "concord/menu_score_teacher_labels.py" in menu
    assert "concord/menu.py" in menu
    assert inventory["counts"]["prior_issue134_tests"] >= 1
    assert inventory["counts"]["prior_issue136_tests"] >= 1
    assert len(inventory["prior_regression_and_contract_sha256"]) >= 10


def test_slice0_capture_not_written_before_branch_guard(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    audit = _module()
    monkeypatch.setattr(
        audit,
        "_git_identity",
        lambda _: (_ for _ in ()).throw(audit.BaselineError("wrong branch")),
    )
    with pytest.raises(audit.BaselineError, match="wrong branch"):
        audit.capture(ROOT, core_wheel=None, concord_wheel=None)
    assert not tuple(tmp_path.iterdir())


def test_slice0_missing_artifact_is_not_verified() -> None:
    audit = _module()
    result = audit._wheel(
        None,
        filename="pds_core-0.6.6-py3-none-any.whl",
        digest=audit.CORE_SHA256,
        distribution="pds-core",
        version="0.6.6",
    )
    assert result["status"] == "not_provided"
    assert "sha256" not in result


def test_slice0_rejects_fake_wheel_even_with_correct_name(tmp_path: Path) -> None:
    audit = _module()
    fake = tmp_path / "pds_core-0.6.6-py3-none-any.whl"
    fake.write_bytes(b"not a published artifact")
    with pytest.raises(audit.BaselineError, match="SHA-256 mismatch"):
        audit._wheel(
            fake,
            filename=fake.name,
            digest=audit.CORE_SHA256,
            distribution="pds-core",
            version="0.6.6",
        )


def test_slice0_markdown_cannot_claim_real_classroom_acceptance() -> None:
    audit = _module()
    sample: dict[str, Any] = {
        "captured_utc": "2026-10-20T00:00:00+00:00",
        "repository": "Paper-Data-Suite/pds-concord",
        "git": {
            "branch": audit.EXPECTED_BRANCH,
            "head": audit.BASELINE_COMMIT,
            "tag": "v0.3.4",
            "tag_object": "tagobject",
            "tag_peeled_commit": audit.BASELINE_COMMIT,
            "tracked_files_clean": True,
        },
        "source": {"version": "0.3.4"},
        "environment": {
            "python": "3.11",
            "system": "Windows",
            "machine_architecture": "ARM64",
        },
        "published_artifacts": {
            "core_v0_6_6_wheel": {"status": "not_provided"},
            "concord_v0_3_4_wheel": {"status": "not_provided"},
        },
        "inventory": {"counts": {"teacher_menu_modules": 1}},
    }
    text = audit._markdown(sample)
    assert "**unperformed**" in text
    assert "not_provided" in text
    assert "Slice 2" in text


def test_slice0_refuses_output_overwrite(tmp_path: Path) -> None:
    # Even a valid prior result cannot be rewritten with altered timestamps.
    output = tmp_path / "receipt"
    output.mkdir()
    (output / "baseline.json").write_text("{}", encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--repo",
            str(ROOT),
            "--output-dir",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "refusing overwrite" in result.stderr
    assert json.loads((output / "baseline.json").read_text(encoding="utf-8")) == {}
