from __future__ import annotations

from pathlib import Path

from concord import __version__

ROOT = Path(__file__).resolve().parents[1]
FINAL_VERSION = "0.3.1"
DEV_SUFFIX = ".dev0"


def test_authoritative_version_is_final_v031() -> None:
    assert __version__ == FINAL_VERSION


def test_active_release_files_name_exact_v031_artifacts() -> None:
    release = (ROOT / "scripts" / "verify_release_artifacts.py").read_text(
        encoding="utf-8"
    )
    package = (ROOT / "scripts" / "check_package.py").read_text(encoding="utf-8")
    compatibility = (
        ROOT / "scripts" / "verify_release_compatibility.py"
    ).read_text(encoding="utf-8")

    assert 'RELEASE_VERSION = "0.3.1"' in release
    assert 'EXPECTED_WHEEL = "pds_concord-0.3.1-py3-none-any.whl"' in release
    assert 'EXPECTED_SDIST = "pds_concord-0.3.1.tar.gz"' in release
    assert 'EXPECTED_DIST_INFO = "pds_concord-0.3.1.dist-info"' in release
    assert 'EXPECTED_VERSION = "0.3.1"' in package
    assert 'RELEASE_VERSION = "0.3.1"' in compatibility


def test_active_python_qualification_surfaces_have_no_dev_version_literal() -> None:
    forbidden = FINAL_VERSION + DEV_SUFFIX
    offenders: list[str] = []

    for top in ("concord", "scripts", "tests"):
        for path in sorted((ROOT / top).rglob("*.py")):
            relative = path.relative_to(ROOT)
            if path == Path(__file__).resolve():
                continue
            if forbidden in path.read_text(encoding="utf-8"):
                offenders.append(relative.as_posix())

    assert offenders == []


def test_v031_release_documents_exist_while_v030_evidence_is_retained() -> None:
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    notes = (ROOT / "RELEASE_NOTES_v0.3.1.md").read_text(encoding="utf-8")
    checklist = (ROOT / "docs" / "v0.3.1-release-checklist.md").read_text(
        encoding="utf-8"
    )
    historical_notes = (ROOT / "RELEASE_NOTES_v0.3.0.md").read_text(
        encoding="utf-8"
    )
    historical_checklist = (ROOT / "docs" / "release_checklist.md").read_text(
        encoding="utf-8"
    )

    assert "## Unreleased" in changelog
    assert "## 0.3.1 - 2026-10-09" in changelog
    assert changelog.index("## Unreleased") < changelog.index(
        "## 0.3.1 - 2026-10-09"
    )
    assert notes.startswith("# Concord v0.3.1")
    assert "pds-core>=0.6.5,<0.7" in notes
    assert "concord_academic_result_reader_v1" in notes
    assert checklist.startswith("# Concord v0.3.1 release checklist")
    assert "pds_core-0.6.5-py3-none-any.whl" in checklist

    assert historical_notes.startswith("# Concord v0.3.0")
    assert historical_checklist.startswith("# Concord v0.3.0 release checklist")
    assert "pds_core-0.6.3-py3-none-any.whl" in historical_checklist
