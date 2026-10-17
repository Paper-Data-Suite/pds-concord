from __future__ import annotations

import ast
from pathlib import Path

from scripts.smoke_test_routine_artifact_review_wheel import _smoke_code

ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "scripts" / "smoke_test_routine_artifact_review_wheel.py"
VALIDATOR = ROOT / "scripts" / "validate_repository.py"
PACKAGE_CHECK = ROOT / "scripts" / "check_package.py"


def test_issue107_installed_smoke_is_present_and_isolated() -> None:
    text = SMOKE.read_text(encoding="utf-8")
    assert "EXPECTED_CORE_SHA256" in text
    assert "d6d21e426092b0329bcfd69b6fbee44c345edc46794a914d847d5ea73a2b7301" in text
    assert '"-m", "pip", "check"' in text
    assert '"-I"' in text
    assert "site-packages" in text
    assert "two sequential explicit teacher REVIEW confirmations" in text
    assert "Detailed Review path remains reachable" in text
    assert "Issue #107 isolated installed-wheel acceptance: PASS" in text


def test_issue107_smoke_is_wired_into_authoritative_repository_validation() -> None:
    text = VALIDATOR.read_text(encoding="utf-8")
    assert "scripts/smoke_test_routine_artifact_review_wheel.py" in text
    assert "installed-wheel smoke: issue #107 routine Artifact Review" in text


def test_issue107_workflow_modules_are_required_package_content() -> None:
    text = PACKAGE_CHECK.read_text(encoding="utf-8")
    for path in (
        "concord/workflows/artifact_routine_review.py",
        "concord/workflows/artifact_routine_review_profiles.py",
        "concord/workflows/artifact_routine_review_commit.py",
        "concord/workflows/artifact_review_next.py",
    ):
        assert path in text


def test_issue107_installed_smoke_binds_teacher_choices_to_same_workspace() -> None:
    # The installed fixture uses a non-default synthetic workspace; never read
    # an unrelated teacher workspace or bypass canonical snapshot validation.
    smoke = _smoke_code()
    ast.parse(smoke)
    assert "real_teacher_choices = artifact_menu.list_teacher_artifact_choices" in smoke
    assert "def teacher_choices_bound(" in smoke
    assert "expected_snapshot_revision=expected_snapshot_revision" in smoke
    # Check the call structurally; generated smoke code has been dedented.
    parsed = ast.parse(smoke)
    assert any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "patch"
        and node.func.attr == "object"
        and len(node.args) == 3
        and isinstance(node.args[0], ast.Name)
        and node.args[0].id == "artifact_menu"
        and isinstance(node.args[1], ast.Constant)
        and node.args[1].value == "list_teacher_artifact_choices"
        and isinstance(node.args[2], ast.Name)
        and node.args[2].id == "teacher_choices_bound"
        for node in ast.walk(parsed)
    )
    assert "workspace_root=root" in smoke
    assert "snapshot-scoped teacher Artifact choice projection" in smoke
    assert '== ("artifact-1", "artifact-2")' in smoke
