from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "scripts" / "smoke_test_returned_artifact_evidence_opening_wheel.py"
VALIDATOR = ROOT / "scripts" / "validate_repository.py"
DOC = ROOT / "docs" / "v0.3.1-returned-artifact-evidence-opening.md"
README = ROOT / "README.md"
CHANGELOG = ROOT / "CHANGELOG.md"
CLI_DOC = ROOT / "docs" / "cli-contract.md"
PACKAGE_CHECK = ROOT / "scripts" / "check_package.py"
RELEASE_CHECK = ROOT / "scripts" / "verify_release_artifacts.py"


def _smoke_source() -> str:
    return SMOKE.read_text(encoding="utf-8")


def test_issue105_installed_smoke_compiles_and_isolated() -> None:
    source = _smoke_source()
    ast.parse(source)
    required = (
        "venv.EnvBuilder(with_pip=True)",
        '"pip", "install"',
        '[str(python), "-I", str(smoke_path)]',
        "site-packages",
        'metadata.version("pds-core") == "0.6.3"',
        'metadata.version("pds-concord") == "0.3.0"',
        "98d7596ce0eed26e4d56a17bbbbd644db3014259b56a45783a173fe8237af5e5",
        "Issue #105 candidate wheel SHA-256:",
        "Issue #105 Core wheel SHA-256:",
    )
    for fragment in required:
        assert fragment in source


def test_issue105_installed_smoke_covers_verified_open_boundary() -> None:
    source = _smoke_source()
    required = (
        "prepare_artifact_pages(",
        "resolve_route_registration(",
        "handle_concord_route(",
        "assemble_returned_artifact(",
        "resolve_returned_artifact_assembly(",
        "open_returned_artifact_evidence(",
        "opening_module.open_local_path = fake_open",
        "canonical_before.snapshot_revision",
        "canonical_before.snapshot_sha256",
        "stale teacher selection was opened",
        "issue105-installed-tamper",
        "missing assembly manifest was opened",
        "LocalOpenError",
        "ConcordWorkflowOpenError",
        "Issue #105 isolated installed-wheel acceptance: PASS",
    )
    for fragment in required:
        assert fragment in source


def test_issue105_installed_smoke_is_wired_into_authoritative_validator() -> None:
    source = VALIDATOR.read_text(encoding="utf-8")
    assert "scripts/smoke_test_returned_artifact_evidence_opening_wheel.py" in source
    tree = ast.parse(source)
    assert any(
        isinstance(node, ast.Constant)
        and node.value
        == "installed-wheel smoke: issue #105 returned Artifact evidence opening"
        for node in ast.walk(tree)
    )


def test_issue105_docs_and_package_checks_freeze_open_boundary() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = (
        "OPEN != ASSEMBLE",
        "OPEN != REVIEW",
        "OPEN != SCORE",
        "resolve_returned_artifact_assembly",
        "open_returned_artifact_evidence",
        "pds_core.local_open.open_local_path",
        "expected_snapshot_revision",
        "snapshot_sha256",
        "O. Open returned work",
        "not_applicable",
        "not_ready",
        "ready",
        "selection_required",
        "assembled",
        "needs_recovery",
        "scripts/smoke_test_returned_artifact_evidence_opening_wheel.py",
        "python -I",
    )
    for fragment in required:
        assert fragment in text

    readme = README.read_text(encoding="utf-8")
    changelog = CHANGELOG.read_text(encoding="utf-8")
    cli = CLI_DOC.read_text(encoding="utf-8")
    assert "## Opening returned Artifact evidence" in readme
    assert "Issue #105" in changelog
    assert "O. Open returned work" in cli
    assert "does not create a Review or Score" in cli

    package = PACKAGE_CHECK.read_text(encoding="utf-8")
    release = RELEASE_CHECK.read_text(encoding="utf-8")
    for source in (package, release):
        assert "concord/workflows/artifact_evidence_opening.py" in source
