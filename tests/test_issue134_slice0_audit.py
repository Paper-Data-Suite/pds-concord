"""Slice 0 source-only coverage; no Concord workflow writes or migration."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.audit_issue134_teacher_surfaces import (
    AUDIT_SCHEMA,
    BASELINE_COMMIT,
    CORE_RELEASE_WHEEL_SHA256,
    ENTRYPOINTS,
    canonical_bytes,
    classify,
    collect,
)
from scripts.verify_issue134_core_release_input import (
    CORE_RELEASE_WHEEL_SHA256 as VERIFIED_CORE_WHEEL_SHA256,
)

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "docs/validation/issue134_teacher_surface_inventory.json"


def test_baseline_identity_is_immutable_release_identity() -> None:
    assert len(BASELINE_COMMIT) == 40
    assert len(CORE_RELEASE_WHEEL_SHA256) == 64
    assert VERIFIED_CORE_WHEEL_SHA256 == CORE_RELEASE_WHEEL_SHA256
    assert BASELINE_COMMIT != "35af5d0642e84a625cd143285c4ef6de98dbcca4"


def test_routine_and_technical_candidates_are_not_conflated() -> None:
    assert classify('f"SHA-256: {item.output_sha256}"', "_render") == (
        "teacher_display_candidate"
    )
    assert classify(
        'f"Source SHA-256: {item.source_sha256}"',
        "_routing_technical_detail_lines",
    ) == ("advanced_technical_candidate")
    assert classify('"Artifact Instance ID",', "_prepare") == (
        "teacher_input_candidate"
    )


def test_inventory_covers_teacher_entrypoints_without_workspace_access() -> None:
    report = collect(ROOT)
    assert report["schema"] == AUDIT_SCHEMA
    assert set(ENTRYPOINTS).issubset(report["source_checksums"])
    assert len(report["source_checksums"]) >= len(ENTRYPOINTS)
    assert report["scope"].startswith("source-only")
    assert report["findings"]
    assert all(item["path"].startswith("concord/menu") for item in report["findings"])
    assert all(isinstance(item["line"], int) for item in report["findings"])
    assert not any("C:\\Users\\" in item["path"] for item in report["findings"])


def test_committed_inventory_is_deterministic_and_complete() -> None:
    expected = canonical_bytes(collect(ROOT))
    assert INVENTORY.is_file()
    assert INVENTORY.read_bytes() == expected
    parsed = json.loads(expected)
    assert parsed["source_checksums"]["concord/menu_artifact.py"]
    assert parsed["source_checksums"]["concord/menu_scoring.py"]
    assert parsed["source_checksums"]["concord/menu_publication.py"]


def test_inventory_fails_closed_on_absent_source(tmp_path: Path) -> None:
    (tmp_path / "concord").mkdir()
    try:
        collect(tmp_path)
    except FileNotFoundError:
        pass
    else:
        raise AssertionError(
            "Missing teacher menu source must not look like an empty audit."
        )
