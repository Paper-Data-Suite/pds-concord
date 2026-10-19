"""Current candidate Core 0.6.6 pins and archived release isolation."""

from __future__ import annotations

import ast
import tomllib
from pathlib import Path

from concord import __version__
from scripts.verify_core_wheel import (
    EXPECTED_CORE_VERSION,
    EXPECTED_CORE_WHEEL_FILENAME,
    EXPECTED_CORE_WHEEL_SHA256,
)
from scripts.verify_release_artifacts import (
    EXPECTED_SDIST,
    EXPECTED_WHEEL,
    RELEASE_VERSION,
)
from scripts.verify_release_compatibility import EXPECTED_CORE_SPECIFIER

ROOT = Path(__file__).resolve().parents[1]
CORE_SHA = "d6d21e426092b0329bcfd69b6fbee44c345edc46794a914d847d5ea73a2b7301"


def test_current_candidate_identity_is_new_and_requires_core066() -> None:
    assert __version__ == RELEASE_VERSION == "0.3.4"
    assert EXPECTED_WHEEL == "pds_concord-0.3.4-py3-none-any.whl"
    assert EXPECTED_SDIST == "pds_concord-0.3.4.tar.gz"
    assert EXPECTED_CORE_VERSION == "0.6.6"
    assert EXPECTED_CORE_WHEEL_FILENAME == "pds_core-0.6.6-py3-none-any.whl"
    assert EXPECTED_CORE_WHEEL_SHA256 == CORE_SHA
    assert str(EXPECTED_CORE_SPECIFIER) == "<0.7,>=0.6.6"
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert project["project"]["dependencies"][0] == "pds-core>=0.6.6,<0.7"


def test_ci_authenticates_official_core066_on_all_matrix_rows() -> None:
    ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "/v0.6.6/pds_core-0.6.6-py3-none-any.whl" in ci
    assert "pds_core-0.6.5-py3-none-any.whl" not in ci
    assert "python scripts/verify_core_wheel.py --installed" in ci
    assert 'python scripts/verify_core_wheel.py "$env:PDS_CORE_WHEEL"' in ci


def test_installed_wheel_smokes_have_current_version_assertions() -> None:
    smoke = (
        *sorted((ROOT / "scripts").glob("smoke_test_*_wheel.py")),
        ROOT / "scripts/smoke_test_wheel.py",
    )
    current = [
        p
        for p in smoke
        if 'metadata.version("pds-core")' in p.read_text(encoding="utf-8")
    ]
    assert len(current) >= 8
    for path in smoke:
        source = path.read_text(encoding="utf-8")
        assert "0.6.5" not in source, path.name
        assert "0.3.2" not in source, path.name


def test_historical_issue129_harness_unchanged_and_separate() -> None:
    historical = (ROOT / "scripts/run_issue129_installed_acceptance.py").read_text(
        encoding="utf-8"
    )
    assert 'EXPECTED_CONCORD_VERSION = "0.3.2"' in historical
    assert 'EXPECTED_CORE_VERSION = "0.6.5"' in historical
    current = (ROOT / "scripts/run_issue134_installed_acceptance.py").read_text(
        encoding="utf-8"
    )
    ast.parse(current)
    assert 'EXPECTED_CONCORD_VERSION = "0.3.3"' in current
    assert 'EXPECTED_CORE_VERSION = "0.6.6"' in current
    assert CORE_SHA in current
    assert "venv.EnvBuilder(with_pip=True)" in current
    assert '"-m", "pip", "check"' in current
    assert 'environment.pop("PYTHONPATH", None)' in current
    validator = (ROOT / "scripts/validate_repository.py").read_text(encoding="utf-8")
    assert '"scripts/run_issue136_installed_acceptance.py"' in validator
    assert '"scripts/run_issue129_installed_acceptance.py"' not in validator
    assert "installed-wheel smoke: issue #136 Core 0.6.6 reader contract" in validator


def test_viewer_protection_remains_in_core_after_evidence_verification() -> None:
    for source_file in (
        "concord/workflows/artifact_evidence_opening.py",
        "concord/workflows/rendered_output.py",
        "concord/workflows/student_feedback_distribution_opening.py",
    ):
        source = (ROOT / source_file).read_text(encoding="utf-8")
        assert "open_local_path" in source
        assert "LocalOpenError" in source
        assert "os.startfile" not in source
    assert (ROOT / "scripts/probe_issue134_core066_viewer.py").is_file()
