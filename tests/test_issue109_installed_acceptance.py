from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "scripts" / "smoke_test_routing_review_wheel.py"
VALIDATOR = ROOT / "scripts" / "validate_repository.py"
PACKAGE_CHECK = ROOT / "scripts" / "check_package.py"
PYPROJECT = ROOT / "pyproject.toml"

CORE_065_SHA256 = (
    "9ace75f17b23b7f0ed6a709d531af5120db43d0325b4148d26f2d6ba1d4b3c18"
)


def _source() -> str:
    return SMOKE.read_text(encoding="utf-8")


def test_issue109_installed_smoke_compiles_and_authenticates_core065() -> None:
    source = _source()
    ast.parse(source)
    required = (
        "venv.EnvBuilder(with_pip=True)",
        '"pip", "check"',
        '[str(python), "-I", str(smoke_path)]',
        'metadata.version("pds-core") == "0.6.5"',
        'metadata.version("pds-concord") == "0.3.1"',
        CORE_065_SHA256,
        "Issue #109 candidate wheel SHA-256:",
        "Issue #109 Core wheel SHA-256:",
        "site-packages",
    )
    for fragment in required:
        assert fragment in source


def test_issue109_installed_smoke_covers_teacher_review_contract() -> None:
    source = _source()
    required = (
        "routing_failure_summary_label(summary)",
        "list_routing_destination_classes(",
        "list_routing_destination_activities(",
        "project_routing_destination_candidates(",
        "routing_destination_candidate_label(candidate)",
        "fingerprint(root) == before_browse",
        'first_resolution.resolution_action == "route_selected"',
        "bound_review.bound_work == locator.work",
        "replay_candidate.replayed_occurrence",
        'replay_resolution.resolution_action == "route_corrected"',
        "RoutingFailureAlreadyResolvedError",
        "resolution_count(root) == resolutions_before",
        "route_inventory(root, locator) == routes_before",
        "callable(menu_scan.launch_scan_routing_menu)",
        "Issue #109 isolated installed-wheel acceptance: PASS",
    )
    for fragment in required:
        assert fragment in source


def test_issue109_installed_smoke_is_wired_into_validator() -> None:
    source = VALIDATOR.read_text(encoding="utf-8")
    assert "scripts/smoke_test_routing_review_wheel.py" in source
    assert "installed-wheel smoke: issue #109 teacher Routing Review" in source


def test_issue109_routing_review_modules_are_required_wheel_content() -> None:
    source = PACKAGE_CHECK.read_text(encoding="utf-8")
    for path in (
        "concord/menu_scan.py",
        "concord/routing/candidates.py",
        "concord/routing/destinations.py",
        "concord/routing/review.py",
    ):
        assert path in source


def test_issue109_historical_smoke_is_superseded_by_core065_release_floor() -> None:
    text = PYPROJECT.read_text(encoding="utf-8")
    assert '"pds-core>=0.6.5,<0.7"' in text
