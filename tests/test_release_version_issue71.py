from __future__ import annotations

from pathlib import Path

from concord import __version__

ROOT = Path(__file__).resolve().parents[1]
FINAL_VERSION = "0.3.0"
DEV_SUFFIX = ".dev0"


def test_authoritative_version_is_final_v030() -> None:
    assert __version__ == FINAL_VERSION


def test_release_files_name_exact_v030_artifacts() -> None:
    release = (ROOT / "scripts" / "verify_release_artifacts.py").read_text(
        encoding="utf-8"
    )
    package = (ROOT / "scripts" / "check_package.py").read_text(encoding="utf-8")
    compatibility = (
        ROOT / "scripts" / "verify_release_compatibility.py"
    ).read_text(encoding="utf-8")

    assert 'RELEASE_VERSION = "0.3.0"' in release
    assert 'EXPECTED_WHEEL = "pds_concord-0.3.0-py3-none-any.whl"' in release
    assert 'EXPECTED_SDIST = "pds_concord-0.3.0.tar.gz"' in release
    assert 'EXPECTED_DIST_INFO = "pds_concord-0.3.0.dist-info"' in release
    assert 'EXPECTED_VERSION = "0.3.0"' in package
    assert 'RELEASE_VERSION = "0.3.0"' in compatibility


def test_active_python_qualification_surfaces_have_no_dev_version_literal() -> None:
    forbidden = FINAL_VERSION + DEV_SUFFIX
    offenders: list[str] = []

    for top in ("concord", "scripts", "tests"):
        for path in sorted((ROOT / top).rglob("*.py")):
            relative = path.relative_to(ROOT)
            if "issue70" in relative.name.casefold():
                continue
            if path == Path(__file__).resolve():
                continue
            if forbidden in path.read_text(encoding="utf-8"):
                offenders.append(relative.as_posix())

    assert offenders == []


def test_release_documentation_is_rolled_to_v030() -> None:
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    notes = (ROOT / "RELEASE_NOTES_v0.3.0.md").read_text(encoding="utf-8")
    checklist = (ROOT / "docs" / "release_checklist.md").read_text(
        encoding="utf-8"
    )

    assert "## Unreleased\n\n## 0.3.0 - 2026-08-31" in changelog
    assert notes.startswith("# Concord v0.3.0\n")
    assert "Issue #71 intentionally does not repeat the physical run." in notes
    assert checklist.startswith("# Concord v0.3.0 release checklist\n")
    assert "pds_core-0.6.3-py3-none-any.whl" in checklist
    assert "pds_concord-0.3.0-py3-none-any.whl" in checklist
    normalized_checklist = " ".join(checklist.split())
    assert "do not perform a new physical print/mark/scan run" in normalized_checklist
    assert "- [x] authoritative validator passes with `--allow-dirty`" in checklist
    assert "- [x] physical qualification delta audit confirms" in checklist
