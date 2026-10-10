"""Issue #129 final v0.3.1 release-boundary qualification."""

from __future__ import annotations

import tomllib
from pathlib import Path

from concord import __version__

ROOT = Path(__file__).resolve().parents[1]
CORE_065_SHA256 = (
    "9ace75f17b23b7f0ed6a709d531af5120db43d0325b4148d26f2d6ba1d4b3c18"
)


def test_issue129_active_release_identity_and_core_floor() -> None:
    assert __version__ == "0.3.1"
    project = tomllib.loads(
        (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )["project"]
    assert project["dependencies"][0] == "pds-core>=0.6.5,<0.7"

    for relative in (
        "scripts/check_package.py",
        "scripts/verify_release_artifacts.py",
        "scripts/verify_release_compatibility.py",
    ):
        source = (ROOT / relative).read_text(encoding="utf-8")
        assert "0.3.1" in source
        assert "pds-core>=0.6.5,<0.7" in source


def test_issue129_exact_core065_is_active_ci_and_repository_baseline() -> None:
    verifier = (ROOT / "scripts" / "verify_core_wheel.py").read_text(
        encoding="utf-8"
    )
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )
    validator = (ROOT / "scripts" / "validate_repository.py").read_text(
        encoding="utf-8"
    )

    assert 'EXPECTED_CORE_VERSION = "0.6.5"' in verifier
    assert (
        'EXPECTED_CORE_WHEEL_FILENAME = "pds_core-0.6.5-py3-none-any.whl"'
        in verifier
    )
    assert CORE_065_SHA256 in verifier
    assert "pds_core-0.6.5-py3-none-any.whl" in ci
    assert "/v0.6.5/pds_core-0.6.5-py3-none-any.whl" in ci
    assert "scripts/run_issue129_installed_acceptance.py" in validator
    assert (
        "installed-wheel smoke: issue #129 Core 0.6.5 reader contract"
        in validator
    )


def test_issue129_release_compatibility_freezes_reader_support() -> None:
    source = (
        ROOT / "scripts" / "verify_release_compatibility.py"
    ).read_text(encoding="utf-8")
    for fragment in (
        "CONCORD_ACADEMIC_RESULT_READER_CONTRACT_VERSION",
        "CONCORD_DISTRIBUTION_NAME",
        "support.reader_support",
        "publication reader-support declaration changed",
        "contracts/profile/reader-support exact",
    ):
        assert fragment in source


def test_issue129_required_wheel_content_includes_standards_display() -> None:
    for relative in (
        "scripts/check_package.py",
        "scripts/verify_release_artifacts.py",
    ):
        source = (ROOT / relative).read_text(encoding="utf-8")
        assert '"concord/standards_display.py"' in source


def test_issue129_historical_v030_release_evidence_is_unchanged() -> None:
    audit = (ROOT / "docs" / "v0.3.0-release-audit.md").read_text(
        encoding="utf-8"
    )
    checklist = (ROOT / "docs" / "release_checklist.md").read_text(
        encoding="utf-8"
    )
    assert "v0.3.0" in audit
    assert "pds-core>=0.6.3,<0.7" in audit
    assert checklist.startswith("# Concord v0.3.0 release checklist")
    assert "pds_core-0.6.3-py3-none-any.whl" in checklist


def test_issue129_v031_release_docs_define_contract_and_pending_final_gate() -> None:
    notes = (ROOT / "RELEASE_NOTES_v0.3.1.md").read_text(
        encoding="utf-8"
    )
    checklist = (ROOT / "docs" / "v0.3.1-release-checklist.md").read_text(
        encoding="utf-8"
    )
    for value in (
        "concord_academic_result_manifest_v1",
        "concord_academic_result_reader_v1",
        "pds-core>=0.6.5,<0.7",
        "Standards",
    ):
        assert value in notes
    assert "full repository qualification" in checklist
    assert "Core 0.6.5" in checklist
