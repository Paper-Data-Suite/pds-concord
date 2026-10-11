from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "v0.3.1-teacher-friendly-routing-review.md"
DOC_INDEX = ROOT / "docs" / "README.md"
README = ROOT / "README.md"
CHANGELOG = ROOT / "CHANGELOG.md"
DOC_CHECK = ROOT / "scripts" / "check_documentation.py"
PYPROJECT = ROOT / "pyproject.toml"

CORE_064_SHA256 = (
    "48cea9317f2967bdc0f2d4c14349a56677c7c3f8211f0f33978ccb1a1c75859b"
)


def test_issue109_documentation_freezes_routing_review_boundaries() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = (
        "Route scans != Routing Review",
        "load_activity_read_context(...)",
        "load_route_registration(...)",
        "validate_concord_route_target(...)",
        "Candidate discovery is read-only",
        "does not create or repair route registrations",
        "Packet target != Artifact Author != Artifact Subject",
        "human_fallback",
        "DEFER",
        "RESOLVE",
        "resolve_routing_failure_with_route(...)",
        "RoutingFailureAlreadyResolvedError",
        "no workspace migration",
        "pds-core>=0.6.3,<0.7",
        "scripts/smoke_test_routing_review_wheel.py",
        "python -I",
        "Core 0.6.4",
        CORE_064_SHA256,
    )
    for fragment in required:
        assert fragment in text


def test_issue109_teacher_readme_explains_route_scans_vs_review() -> None:
    text = README.read_text(encoding="utf-8")
    required = (
        "Routing Review is the explicit recovery path",
        "Route to an existing Concord page",
        "DEFER",
        "RESOLVE",
        "does not create, repair, or guess routes",
        "v0.3.1-teacher-friendly-routing-review.md",
    )
    for fragment in required:
        assert fragment in text


def test_issue109_documentation_is_indexed_and_changelog_is_current() -> None:
    index = DOC_INDEX.read_text(encoding="utf-8")
    changelog = CHANGELOG.read_text(encoding="utf-8")
    assert DOC.name in index
    assert "Issue #109" in changelog
    assert "teacher-friendly Routing Review" in changelog
    assert "Core 0.6.4" in changelog
    assert "RESOLVE" in changelog


def test_issue109_documentation_validator_enforces_current_contract() -> None:
    source = DOC_CHECK.read_text(encoding="utf-8")
    assert "TEACHER_ROUTING_REVIEW_DOC" in source
    assert "REQUIRED_TEACHER_ROUTING_REVIEW_PHRASES" in source
    assert DOC.name in source


def test_issue109_historical_floor_is_superseded_by_issue129_core065() -> None:
    text = PYPROJECT.read_text(encoding="utf-8")
    assert '"pds-core>=0.6.5,<0.7"' in text
