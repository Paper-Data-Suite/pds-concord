"""Issue #129 installed Core 0.6.5 acceptance contract."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "scripts" / "run_issue129_installed_acceptance.py"
VERSION = ROOT / "concord" / "_version.py"

CORE_065_SHA256 = (
    "9ace75f17b23b7f0ed6a709d531af5120db43d0325b4148d26f2d6ba1d4b3c18"
)


def _source() -> str:
    return HARNESS.read_text(encoding="utf-8")


def test_issue129_candidate_version_is_031() -> None:
    assert VERSION.read_text(encoding="utf-8") == (
        '"""Authoritative Concord package version."""\n\n'
        '__version__ = "0.3.1"\n'
    )


def test_issue129_installed_harness_compiles_and_authenticates_core065() -> None:
    source = _source()
    ast.parse(source)

    required = (
        'EXPECTED_CONCORD_VERSION = "0.3.1"',
        'EXPECTED_CONCORD_WHEEL = "pds_concord-0.3.1-py3-none-any.whl"',
        'EXPECTED_CORE_VERSION = "0.6.5"',
        'EXPECTED_CORE_WHEEL = "pds_core-0.6.5-py3-none-any.whl"',
        CORE_065_SHA256,
        '"-m",\n                "build",\n                "--wheel"',
        "venv.EnvBuilder(with_pip=True)",
        '"-m", "pip", "check"',
        '[str(python), "-I", str(smoke_path)]',
        "Issue #129 candidate wheel SHA-256:",
        "Issue #129 Core wheel SHA-256:",
    )
    for fragment in required:
        assert fragment in source


def test_issue129_installed_harness_uses_real_standards_and_publication_flow(
) -> None:
    source = _source()

    required = (
        'PROFILE_ID = "njsls-ela:profile.2023:11-12"',
        'STANDARD_ID = "njsls-ela:2023:rl-ts-11-12-4"',
        'STANDARD_CODE = "RL.TS.11-12.4"',
        'STANDARD_SHORT_NAME = "Analyze Text Structure"',
        "write_workspace_standards_library(root, library)",
        "create_activity_context(",
        "create_criterion_set(",
        "add_score(",
        "register_concord_academic_work(",
        "publish_concord_academic_results(",
        "read_academic_result_manifest(content)",
        "lookup_publication_reader_support(",
        '"concord_academic_result_reader_v1"',
        'support.distribution_name == "pds-concord"',
        "manifest.criteria[0].standard_id == STANDARD_ID",
        "manifest.scores[0].standard_id == STANDARD_ID",
        'STANDARD_CODE.encode("utf-8") not in content',
    )
    for fragment in required:
        assert fragment in source


def test_issue129_installed_harness_has_no_source_or_fixture_bypass() -> None:
    source = _source()

    required = (
        'environment.pop("PYTHONPATH", None)',
        '"site-packages" in parts',
        "not origin.is_relative_to(REPOSITORY)",
        "candidate != REPOSITORY",
        "not candidate.is_relative_to(REPOSITORY)",
        'forbidden = {{"scoreform", "quillan", "portia", "meridian", "vitrine"}}',
    )
    for fragment in required:
        assert fragment in source

    assert "tests/fixtures" not in source
    assert "tests\\fixtures" not in source
    assert "import tests" not in source
    assert "from tests" not in source


def test_issue129_installed_harness_leaves_historical_release_validators_for_slice8(
) -> None:
    source = (ROOT / "scripts" / "verify_release_artifacts.py").read_text(
        encoding="utf-8"
    )
    assert 'RELEASE_VERSION = "0.3.0"' in source
    assert 'EXPECTED_CORE_SPECIFIER = SpecifierSet(">=0.6.3,<0.7")' in source
