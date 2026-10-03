from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "scripts" / "smoke_test_generated_path_safety_wheel.py"
VALIDATOR = ROOT / "scripts" / "validate_repository.py"
CORE_VERIFY = ROOT / "scripts" / "verify_core_wheel.py"
DOC = ROOT / "docs" / "v0.3.1-generated-path-safety.md"
PYPROJECT = ROOT / "pyproject.toml"
PACKAGE_CHECK = ROOT / "scripts" / "check_package.py"
RELEASE_CHECK = ROOT / "scripts" / "verify_release_artifacts.py"

CORE_064_SHA256 = (
    "48cea9317f2967bdc0f2d4c14349a56677c7c3f8211f0f33978ccb1a1c75859b"
)
CORE_063_SHA256 = (
    "98d7596ce0eed26e4d56a17bbbbd644db3014259b56a45783a173fe8237af5e5"
)

REPINNED_SMOKES = (
    "scripts/smoke_test_artifact_attribution_batch_wheel.py",
    "scripts/smoke_test_attention_provider_wheel.py",
    "scripts/smoke_test_guided_activity_wheel.py",
    "scripts/smoke_test_issue113_relationships_wheel.py",
    "scripts/smoke_test_rendered_output_opening_wheel.py",
    "scripts/smoke_test_returned_artifact_evidence_opening_wheel.py",
    "scripts/smoke_test_reusable_presets_wheel.py",
    "scripts/smoke_test_routine_artifact_review_wheel.py",
    "scripts/smoke_test_routine_artifact_scoring_wheel.py",
    "scripts/smoke_test_scan_inbox_routing_wheel.py",
    "scripts/smoke_test_starter_workflows_wheel.py",
    "scripts/smoke_test_task_oriented_activity_menu_wheel.py",
    "scripts/smoke_test_wheel.py",
)


def _smoke_source() -> str:
    return SMOKE.read_text(encoding="utf-8")


def test_issue124_installed_smoke_compiles_and_authenticates_core064() -> None:
    source = _smoke_source()
    ast.parse(source)
    required = (
        "venv.EnvBuilder(with_pip=True)",
        '"pip", "install"',
        '[str(python), "-I", str(smoke_path)]',
        "site-packages",
        'metadata.version("pds-core") == "0.6.4"',
        'metadata.version("pds-concord") == "0.3.0"',
        CORE_064_SHA256,
        "Issue #124 candidate wheel SHA-256:",
        "Issue #124 Core wheel SHA-256:",
    )
    for fragment in required:
        assert fragment in source
    assert CORE_063_SHA256 not in source


def test_issue124_installed_smoke_covers_path_and_provenance_boundaries() -> None:
    source = _smoke_source()
    required = (
        "while len(str(candidate)) < 119",
        "validate_generated_output_filename(",
        'scoring_orientation="local_criteria_only"',
        "CreateScoringScaleRequest(",
        "CreateCriterionSetRequest(",
        "SelectActivityCriterionSetsRequest(",
        "AddScoreRequest(",
        'basis="professional_judgment"',
        '"Synthetic installed path qualification Score."',
        "add_score(",
        "render_packet_instance(",
        "retain_source_scan(",
        "RETAINED_SOURCE_FILENAME_MAX_LENGTH",
        "SOURCE_SCAN_ID_MAX_LENGTH",
        "handle_concord_route(",
        "assemble_returned_artifact(",
        'assembled.output_path.name == "artifact.pdf"',
        'assembled.manifest_path.name == "manifest.json"',
        "register_concord_academic_work(",
        "generate_academic_result_manifest(",
        'manifest.path.name == "1.json"',
        "LEGACY_RETAINED_FILENAME",
        "LEGACY_SOURCE_SCAN_ID",
        "build_retained_source_filename(",
        "legacy_scan.retained_source_relative_path",
        "legacy_replay.replayed",
        "Issue #124 isolated installed-wheel acceptance: PASS",
    )
    for fragment in required:
        assert fragment in source


def test_issue124_repin_moves_authoritative_qualification_to_core064() -> None:
    verifier = CORE_VERIFY.read_text(encoding="utf-8")
    assert 'EXPECTED_CORE_VERSION = "0.6.4"' in verifier
    assert (
        'EXPECTED_CORE_WHEEL_FILENAME = "pds_core-0.6.4-py3-none-any.whl"'
        in verifier
    )
    assert CORE_064_SHA256 in verifier
    assert CORE_063_SHA256 not in verifier

    for relative in REPINNED_SMOKES:
        source = (ROOT / relative).read_text(encoding="utf-8")
        assert '== "0.6.3"' not in source
        assert "== '0.6.3'" not in source
        assert CORE_063_SHA256 not in source


def test_issue124_runtime_dependency_floor_is_not_raised_here() -> None:
    text = PYPROJECT.read_text(encoding="utf-8")
    assert '"pds-core>=0.6.3,<0.7"' in text
    assert '"pds-core>=0.6.4,<0.7"' not in text


def test_issue124_installed_smoke_is_wired_into_authoritative_validator() -> None:
    source = VALIDATOR.read_text(encoding="utf-8")
    assert "scripts/smoke_test_generated_path_safety_wheel.py" in source
    tree = ast.parse(source)
    assert any(
        isinstance(node, ast.Constant)
        and node.value
        == "installed-wheel smoke: issue #124 generated path safety"
        for node in ast.walk(tree)
    )


def test_issue124_generated_path_module_is_required_package_content() -> None:
    package = PACKAGE_CHECK.read_text(encoding="utf-8")
    release = RELEASE_CHECK.read_text(encoding="utf-8")
    for source in (package, release):
        assert "concord/generated_paths.py" in source


def test_issue124_docs_freeze_core064_installed_qualification() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = (
        "Slice 4",
        "Core 0.6.4",
        CORE_064_SHA256,
        "fresh bounded retained-source provenance",
        "historical Core 0.6 retained-source provenance",
        "No dependency-floor change",
        "scripts/smoke_test_generated_path_safety_wheel.py",
    )
    for fragment in required:
        assert fragment in text

def test_issue124_preserves_historical_issue113_acceptance_evidence() -> None:
    issue113_test = (
        ROOT / "tests" / "test_installed_wheel_acceptance_issue113.py"
    ).read_text(encoding="utf-8")
    assert (
        "98d7596ce0eed26e4d56a17bbbbd644db3014259b56a45783a173fe8237af5e5"
        in issue113_test
    )
