"""Issue #136: exact v0.3.4 release-preparation identity and isolation."""

from __future__ import annotations

import ast
import tomllib
from pathlib import Path

from concord import __version__
from scripts.check_package import EXPECTED_VERSION
from scripts.verify_core_wheel import (
    EXPECTED_CORE_VERSION,
    EXPECTED_CORE_WHEEL_SHA256,
)
from scripts.verify_release_artifacts import (
    EXPECTED_SDIST,
    EXPECTED_WHEEL,
    RELEASE_VERSION,
    REQUIRED_WHEEL_FILES,
)
from scripts.verify_release_compatibility import validate_release_compatibility

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_GROUPING_MODULES = frozenset(
    {
        "concord/class_group_arrangements.py",
        "concord/class_group_arrangement_storage.py",
        "concord/workflows/class_group_arrangements.py",
        "concord/workflows/class_group_arrangement_operational.py",
        "concord/workflows/class_group_arrangement_revision.py",
        "concord/workflows/class_group_arrangement_csv.py",
        "concord/menu_saved_groupings.py",
        "concord/menu_saved_grouping_revisions.py",
        "concord/menu_saved_operational_grouping.py",
        "concord/cli_app/handlers/saved_grouping.py",
        "concord/cli_app/handlers/saved_grouping_revision.py",
        "concord/cli_app/handlers/saved_grouping_operational.py",
        "concord/cli_app/handlers/saved_grouping_csv.py",
    }
)


def test_current_candidate_version_and_exact_core_floor() -> None:
    assert __version__ == EXPECTED_VERSION == RELEASE_VERSION == "0.3.4"
    assert EXPECTED_WHEEL == "pds_concord-0.3.4-py3-none-any.whl"
    assert EXPECTED_SDIST == "pds_concord-0.3.4.tar.gz"
    assert EXPECTED_CORE_VERSION == "0.6.6"
    assert EXPECTED_CORE_WHEEL_SHA256 == (
        "d6d21e426092b0329bcfd69b6fbee44c345edc46794a914d847d5ea73a2b7301"
    )
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert project["project"]["dependencies"][0] == "pds-core>=0.6.6,<0.7"
    validate_release_compatibility()


def test_v034_installed_acceptance_is_separate_from_historical_v033() -> None:
    historical = (ROOT / "scripts/run_issue134_installed_acceptance.py").read_text(
        encoding="utf-8"
    )
    candidate = (ROOT / "scripts/run_issue136_installed_acceptance.py").read_text(
        encoding="utf-8"
    )
    ast.parse(candidate)
    assert 'EXPECTED_CONCORD_VERSION = "0.3.3"' in historical
    assert 'EXPECTED_CONCORD_VERSION = "0.3.4"' in candidate
    assert 'EXPECTED_CORE_VERSION = "0.6.6"' in candidate
    assert "venv.EnvBuilder(with_pip=True)" in candidate
    assert 'environment.pop("PYTHONPATH", None)' in candidate
    assert '"-m", "pip", "check"' in candidate
    validator = (ROOT / "scripts/validate_repository.py").read_text(encoding="utf-8")
    assert '"scripts/run_issue136_installed_acceptance.py"' in validator
    assert '"scripts/run_issue134_installed_acceptance.py"' not in validator


def test_new_saved_grouping_modules_required_in_distribution() -> None:
    assert REQUIRED_GROUPING_MODULES <= REQUIRED_WHEEL_FILES
    assert all((ROOT / item).is_file() for item in REQUIRED_GROUPING_MODULES)


def test_release_docs_are_prepublication_and_historical_releases_are_retained() -> None:
    notes = (ROOT / "RELEASE_NOTES_v0.3.4.md").read_text(encoding="utf-8")
    checklist = (ROOT / "docs/v0.3.4-release-checklist.md").read_text(encoding="utf-8")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert notes.startswith("# Concord v0.3.4")
    assert "#136" in notes
    assert "Core v0.6.6" in notes
    assert "PRE-RELEASE" in checklist
    assert "## 0.3.4 - 2026-10-18 (candidate)" in changelog
    assert "## 0.3.2 - 2026-10-10" in changelog
    assert (ROOT / "RELEASE_NOTES_v0.3.2.md").is_file()
    assert (ROOT / "docs/v0.3.2-release-checklist.md").is_file()
