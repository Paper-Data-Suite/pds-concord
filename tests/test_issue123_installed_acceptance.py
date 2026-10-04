from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "scripts" / "smoke_test_activity_score_analysis_wheel.py"
VALIDATOR = ROOT / "scripts" / "validate_repository.py"
PACKAGE_CHECK = ROOT / "scripts" / "check_package.py"
DOC = ROOT / "docs" / "v0.3.1-activity-score-analysis-local-reports.md"
PYPROJECT = ROOT / "pyproject.toml"

CORE_064_SHA256 = (
    "48cea9317f2967bdc0f2d4c14349a56677c7c3f8211f0f33978ccb1a1c75859b"
)


def _source() -> str:
    return SMOKE.read_text(encoding="utf-8")


def test_issue123_installed_smoke_compiles_and_authenticates_core064() -> None:
    source = _source()
    ast.parse(source)
    required = (
        "venv.EnvBuilder(with_pip=True)",
        '"pip",',
        '[str(python), "-I", str(smoke_path)]',
        'metadata.version("pds-core") == "0.6.4"',
        'metadata.version("pds-concord") == "0.3.0"',
        CORE_064_SHA256,
        "Issue #123 candidate wheel SHA-256:",
        "Issue #123 Core wheel SHA-256:",
        "site-packages",
    )
    for fragment in required:
        assert fragment in source


def test_issue123_installed_smoke_covers_required_analysis_surfaces() -> None:
    source = _source()
    required = (
        "validate_record_graph(graph)",
        "ScoreEvidenceLink(",
        "CorrectionRecord(",
        'target("core_student", "student-1")',
        'target("core_student", "student-2")',
        'target("concord_group", group.group_id)',
        '"concord_artifact_instance"',
        'target("concord_session", session.session_id)',
        'target("concord_activity", activity.activity_id)',
        "activity_score_analysis_from_context(",
        "target_score_detail_from_context(",
        "score_history_analysis_from_context(",
        '"50.0"',
        '"deferred"',
        "prepare_activity_analysis_report(",
        "prepare_target_detail_report(",
        "execute_prepared_score_analysis_report(",
        '"report.json"',
        '"activity_overview.csv"',
        '"criterion_distributions.csv"',
        '"score_dispositions.csv"',
        '"standards_criteria.csv"',
        '"activity_analysis.pdf"',
        '"target_detail.pdf"',
        "REPORT_BOUNDARY_STATEMENT",
        "CURRENT_HEAD_BOUNDARY_STATEMENT",
        "STANDARDS_BOUNDARY_STATEMENT",
        "TARGET_LOCAL_BOUNDARY_STATEMENT",
        "build_human_readable_output_filename(",
        "validate_generated_output_token(",
        "fingerprints(root, exports_root)",
        "Issue #123 isolated installed-wheel acceptance: PASS",
    )
    for fragment in required:
        assert fragment in source


def test_issue123_human_readable_smoke_uses_current_generated_path_api() -> None:
    source = _source()
    assert "build_human_readable_output_filename(" in source
    assert "display_label=LONG_STUDENT" in source
    assert 'extension=".pdf"' in source
    assert "visible_stem=" not in source
    assert 'extension="pdf"' not in source


def test_issue123_installed_smoke_is_wired_into_validator() -> None:
    source = VALIDATOR.read_text(encoding="utf-8")
    assert "scripts/smoke_test_activity_score_analysis_wheel.py" in source
    tree = ast.parse(source)
    assert any(
        isinstance(node, ast.Constant)
        and node.value
        == "installed-wheel smoke: issue #123 Activity Score Analysis"
        for node in ast.walk(tree)
    )


def test_issue123_modules_are_required_wheel_content() -> None:
    source = PACKAGE_CHECK.read_text(encoding="utf-8")
    required = (
        "concord/menu_score_analysis.py",
        "concord/menu_score_analysis_export.py",
        "concord/workflows/_score_lineage.py",
        "concord/workflows/activity_score_analysis.py",
        "concord/workflows/activity_score_reports.py",
        "concord/workflows/activity_score_report_output.py",
        "concord/workflows/activity_score_report_pdf.py",
    )
    for fragment in required:
        assert fragment in source


def test_issue123_dependency_floor_remains_core063_compatible() -> None:
    text = PYPROJECT.read_text(encoding="utf-8")
    assert '"pds-core>=0.6.3,<0.7"' in text
    assert '"pds-core>=0.6.4,<0.7"' not in text


def test_issue123_docs_record_installed_qualification_surface() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = (
        "Installed-wheel qualification",
        "scripts/smoke_test_activity_score_analysis_wheel.py",
        "Core 0.6.4",
        CORE_064_SHA256,
        "python -I",
        "site-packages",
        "publication and module-operations providers",
    )
    for fragment in required:
        assert fragment in text
