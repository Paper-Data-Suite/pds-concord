from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "scripts" / "smoke_test_student_feedback_distribution_wheel.py"
VALIDATOR = ROOT / "scripts" / "validate_repository.py"
PACKAGE_CHECK = ROOT / "scripts" / "check_package.py"
RELEASE_CHECK = ROOT / "scripts" / "verify_release_artifacts.py"
DOC_CHECK = ROOT / "scripts" / "check_documentation.py"
DOC = ROOT / "docs" / "v0.3.1-student-feedback-distribution.md"
DOC_INDEX = ROOT / "docs" / "README.md"
README = ROOT / "README.md"
CLI_DOC = ROOT / "docs" / "cli-contract.md"
CHANGELOG = ROOT / "CHANGELOG.md"
PYPROJECT = ROOT / "pyproject.toml"

CORE_064_SHA256 = (
    "48cea9317f2967bdc0f2d4c14349a56677c7c3f8211f0f33978ccb1a1c75859b"
)

ISSUE114_MODULES = (
    "concord/menu_student_feedback.py",
    "concord/cli_app/handlers/feedback.py",
    "concord/workflows/student_feedback.py",
    "concord/workflows/student_feedback_distribution.py",
    "concord/workflows/student_feedback_distribution_plan.py",
    "concord/workflows/student_feedback_distribution_rendering.py",
    "concord/workflows/student_feedback_distribution_pdf.py",
    "concord/workflows/student_feedback_distribution_package.py",
    "concord/workflows/student_feedback_distribution_storage.py",
    "concord/workflows/student_feedback_distribution_execution.py",
    "concord/workflows/student_feedback_distribution_opening.py",
)


def _smoke_source() -> str:
    return SMOKE.read_text(encoding="utf-8")


def test_issue114_installed_smoke_compiles_and_authenticates_core064() -> None:
    source = _smoke_source()
    ast.parse(source)
    required = (
        "venv.EnvBuilder(with_pip=True)",
        '"pip",',
        '[str(python), "-I", str(smoke_path)]',
        'metadata.version("pds-core") == "0.6.4"',
        'metadata.version("pds-concord") == "0.3.0"',
        CORE_064_SHA256,
        "Issue #114 candidate wheel SHA-256:",
        "Issue #114 Core wheel SHA-256:",
        "site-packages",
        "Issue #114 isolated installed-wheel acceptance: PASS",
    )
    for fragment in required:
        assert fragment in source


def test_issue114_installed_smoke_covers_required_feedback_boundaries() -> None:
    source = _smoke_source()
    required = (
        "create_roster(",
        "commit_record_batch(",
        '"score-student-old"',
        '"score-student-current"',
        'CorrectionRecord(',
        'disposition="absent"',
        '"score-group"',
        '"score-session"',
        'counts == {"graph": 1, "roster": 1, "batch": 1}',
        "preview_student_feedback_distribution(",
        "requires_available_only_decision",
        "prepare_student_feedback_distribution_plan(",
        "ConcordWorkflowConflictError",
        "execute_student_feedback_distribution(",
        '"concord_feedback_distribution_v1"',
        '"Feedback Index.html"',
        '"Print All Feedback.pdf"',
        '"distribution-manifest.json"',
        "verify_student_feedback_distribution_directory(",
        "tampered",
        "open_student_feedback_distribution_directory(",
        "open_student_feedback_distribution_print_pdf(",
        "STUDENT_FEEDBACK_INSTALL_ACTION_REUSED",
        '"distribution-preview"',
        '"6. Student feedback distribution (local package)"',
        "fingerprint(root)",
    )
    for fragment in required:
        assert fragment in source


def test_issue114_installed_smoke_is_wired_into_authoritative_validator() -> None:
    source = VALIDATOR.read_text(encoding="utf-8")
    assert "scripts/smoke_test_student_feedback_distribution_wheel.py" in source
    tree = ast.parse(source)
    assert any(
        isinstance(node, ast.Constant)
        and node.value
        == "installed-wheel smoke: issue #114 student feedback distribution"
        for node in ast.walk(tree)
    )


def test_issue114_runtime_modules_are_required_package_content() -> None:
    package = PACKAGE_CHECK.read_text(encoding="utf-8")
    release = RELEASE_CHECK.read_text(encoding="utf-8")
    for module in ISSUE114_MODULES:
        assert module in package
        assert module in release


def test_issue114_normative_document_and_checker_cover_contract() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = (
        "one exact ActivityReadContext",
        "current Score lineage heads",
        'ScoreTargetReference.target_kind == "core_student"',
        "Target Detail is teacher-local",
        "StudentFeedbackProjection",
        "StudentFeedbackResult",
        "PREPARE AVAILABLE ONLY",
        "last-safe-point currentness check",
        "reviewed plan digest",
        "Print All Feedback.pdf",
        "Feedback Index.html",
        "distribution-manifest.json",
        "concord_feedback_distribution_v1",
        "build_human_readable_output_filename",
        "pds_core.local_open.open_local_path",
        "individual PDFs are student-scoped",
        "staff-scoped",
        "no Grade or standards-proficiency",
        "no email integration",
        "no cloud permission management",
        "no delivery state",
        "historical package",
        "scripts/smoke_test_student_feedback_distribution_wheel.py",
        "python -I",
        "Core 0.6.4",
        CORE_064_SHA256,
        "pds-core>=0.6.3,<0.7",
        "Issue #111",
    )
    for fragment in required:
        assert fragment in text

    checker = DOC_CHECK.read_text(encoding="utf-8")
    assert "STUDENT_FEEDBACK_DISTRIBUTION_DOC" in checker
    assert "REQUIRED_STUDENT_FEEDBACK_DISTRIBUTION_PHRASES" in checker
    assert DOC.name in checker
    assert DOC.name in DOC_INDEX.read_text(encoding="utf-8")


def test_issue114_active_docs_expose_menu_and_direct_cli() -> None:
    readme = README.read_text(encoding="utf-8")
    cli = CLI_DOC.read_text(encoding="utf-8")
    for text in (readme, cli):
        assert "concord feedback distribution-preview" in text
        assert "concord feedback distribution-prepare" in text
        assert "concord feedback distribution-verify" in text
    assert "Student feedback distribution (local package)" in readme
    assert "PREPARE AVAILABLE ONLY" in cli
    assert "--review-digest" in cli


def test_issue114_changelog_records_distribution_and_qualification() -> None:
    text = CHANGELOG.read_text(encoding="utf-8")
    required = (
        "Issue #114",
        "StudentFeedbackProjection",
        "PREPARE AVAILABLE ONLY",
        "Feedback Index.html",
        "Print All Feedback.pdf",
        "concord_feedback_distribution_v1",
        "historical exact-package reuse",
        "Core 0.6.4",
        "python -I",
    )
    for fragment in required:
        assert fragment in text


def test_issue114_preserves_declared_version_and_core_floor() -> None:
    text = PYPROJECT.read_text(encoding="utf-8")
    assert '"pds-core>=0.6.3,<0.7"' in text
    assert '"pds-core>=0.6.4,<0.7"' not in text
    version = (ROOT / "concord" / "_version.py").read_text(encoding="utf-8")
    assert '__version__ = "0.3.0"' in version
