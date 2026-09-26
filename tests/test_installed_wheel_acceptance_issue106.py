from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "scripts" / "smoke_test_artifact_attribution_batch_wheel.py"
VALIDATOR = ROOT / "scripts" / "validate_repository.py"
DOC = ROOT / "docs" / "v0.3.1-artifact-attribution-batching.md"
README = ROOT / "README.md"
DOCS_README = ROOT / "docs" / "README.md"
CHANGELOG = ROOT / "CHANGELOG.md"
PACKAGE_CHECK = ROOT / "scripts" / "check_package.py"


def _smoke_source() -> str:
    return SMOKE.read_text(encoding="utf-8")


def test_issue106_installed_smoke_compiles_and_isolated() -> None:
    source = _smoke_source()
    ast.parse(source)
    required = (
        "venv.EnvBuilder(with_pip=True)",
        '"pip", "install"',
        '"pip", "check"',
        '[str(python), "-I", str(smoke_path)]',
        "site-packages",
        'metadata.version("pds-core") == "0.6.3"',
        'metadata.version("pds-concord") == "0.3.0"',
        "98d7596ce0eed26e4d56a17bbbbd644db3014259b56a45783a173fe8237af5e5",
        "Issue #106 candidate wheel SHA-256:",
        "Issue #106 Core wheel SHA-256:",
    )
    for fragment in required:
        assert fragment in source


def test_issue106_installed_smoke_covers_teacher_batch_and_multi_add() -> None:
    source = _smoke_source()
    required = (
        "_launch_attribution_review_menu",
        'responses = iter(("a", "CONFIRM", "b"))',
        '"Needs individual attention: 1"',
        '"Authors: 0"',
        '"Subjects: 0"',
        "_launch_advanced_attribution_menu",
        "_add_multiple_subjects",
        'add_tokens == ["ADD"]',
        "Issue #106 isolated installed-wheel acceptance: PASS",
    )
    for fragment in required:
        assert fragment in source


def test_issue106_installed_smoke_is_wired_into_authoritative_validator() -> None:
    source = VALIDATOR.read_text(encoding="utf-8")
    assert "scripts/smoke_test_artifact_attribution_batch_wheel.py" in source
    tree = ast.parse(source)
    assert any(
        isinstance(node, ast.Constant)
        and node.value
        == "installed-wheel smoke: issue #106 Artifact attribution batching"
        for node in ast.walk(tree)
    )


def test_issue106_docs_and_package_checks_freeze_batch_boundary() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = (
        "Artifact Author != Artifact Subject",
        "BatchConfirmArtifactAttributionRequest",
        "commit_record_batch",
        "20 Artifacts",
        "40 relationships",
        "one canonical commit",
        "Review attribution",
        "Confirm all straightforward proposals",
        "Select multiple proposals",
        "Create several relationships",
        "Advanced attribution tools",
        "no migration",
        "smoke_test_artifact_attribution_batch_wheel.py",
        "python -I",
    )
    for fragment in required:
        assert fragment in text

    readme = README.read_text(encoding="utf-8")
    docs_readme = DOCS_README.read_text(encoding="utf-8")
    changelog = CHANGELOG.read_text(encoding="utf-8")
    assert "## Reviewing Artifact attribution" in readme
    assert "v0.3.1-artifact-attribution-batching.md" in docs_readme
    assert "Issue #106" in changelog

    package = PACKAGE_CHECK.read_text(encoding="utf-8")
    for required_module in (
        "concord/menu_artifact.py",
        "concord/workflows/artifact_attribution.py",
        "concord/workflows/artifact_attribution_review.py",
    ):
        assert required_module in package
