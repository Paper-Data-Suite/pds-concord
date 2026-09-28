from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "scripts" / "smoke_test_routine_artifact_review_wheel.py"
VALIDATOR = ROOT / "scripts" / "validate_repository.py"
PACKAGE_CHECK = ROOT / "scripts" / "check_package.py"


def test_issue107_installed_smoke_is_present_and_isolated() -> None:
    text = SMOKE.read_text(encoding="utf-8")
    assert "EXPECTED_CORE_SHA256" in text
    assert "98d7596ce0eed26e4d56a17bbbbd644db3014259b56a45783a173fe8237af5e5" in text
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
