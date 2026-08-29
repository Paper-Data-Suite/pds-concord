from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_guided_workflow_document_records_recovery_and_density_contract() -> None:
    text = _text("docs/v0.3.0-guided-create-classroom-activity.md")
    required = (
        "Create Classroom Activity",
        "Continue setup",
        "inspect_guided_activity_setup",
        "No persistent `WizardState`",
        "Information Density and screen-refresh contract",
        "Clearing/redrawing the screen is the default",
        "prepare_packet_from_template",
        "commit_packet_from_template",
        "GroupPlan != Group != GroupMembership",
        "Score != reusable configuration",
        "scripts/smoke_test_guided_activity_wheel.py",
        "pds-core>=0.6.3,<0.7",
    )
    for phrase in required:
        assert phrase in text


def test_guided_materials_reuse_packet_authority_not_artifact_shortcut() -> None:
    text = _text("concord/menu_guided_activity.py")
    assert "generate_saved_packet" in text
    assert "prepare_packet_from_template" in text
    assert "commit_packet_from_template" in text
    assert "launch_packet_library_menu" in text
    assert "create_artifact" not in text
    assert "prepare_artifact" not in text


def test_guided_menu_source_keeps_teacher_language_and_refresh_calls() -> None:
    text = _text("concord/menu_guided_activity.py")
    for phrase in (
        "Create Classroom Activity",
        "Continue Classroom Setup",
        "Classroom Materials",
        "Student Groups",
        "Roles and Responsibilities",
        "Review Classroom Setup",
        "Finish for now",
    ):
        assert phrase in text
    assert text.count("clear_screen()") >= 10
    assert 'input("Activity ID' not in text
    assert 'input("Session ID' not in text
    assert "WizardState" not in text


def test_repository_qualification_wires_guided_installed_smoke_and_package() -> None:
    validator = _text("scripts/validate_repository.py")
    feature_smokes = _text("scripts/smoke_test_feature_wheels.py")
    package = _text("scripts/check_package.py")
    documentation = _text("scripts/check_documentation.py")

    assert "scripts/smoke_test_feature_wheels.py" in validator
    assert "scripts/smoke_test_guided_activity_wheel.py" in feature_smokes
    assert '"concord/menu_guided_activity.py"' in package
    assert '"concord/workflows/guided_activity_setup.py"' in package
    assert "GUIDED_ACTIVITY_WORKFLOW_DOC" in documentation
    assert "REQUIRED_GUIDED_ACTIVITY_WORKFLOW_PHRASES" in documentation
