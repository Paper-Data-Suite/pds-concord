from __future__ import annotations

from pathlib import Path

from scripts import smoke_test_feature_wheels as feature_smokes
from scripts import smoke_test_scan_inbox_routing_wheel as scan_smoke

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
CHANGELOG = ROOT / "CHANGELOG.md"
VALIDATOR = ROOT / "scripts" / "validate_repository.py"


def test_issue103_registers_shared_installed_scan_routing_scenario() -> None:
    matches = tuple(
        item
        for item in feature_smokes.SCENARIOS
        if item[2] == "scripts/smoke_test_scan_inbox_routing_wheel.py"
    )
    assert matches == (
        (
            "scan inbox routing",
            "scan_inbox_routing_smoke.py",
            "scripts/smoke_test_scan_inbox_routing_wheel.py",
        ),
    )


def test_issue103_installed_smoke_covers_required_teacher_path() -> None:
    source = scan_smoke._smoke_code()
    compile(source, "scan_inbox_routing_smoke.py", "exec")
    required = (
        'metadata.version("pds-core") == "0.6.3"',
        'metadata.version("pds-concord") == "0.3.0"',
        '"site-packages"',
        'scans_inbox_dir(root)',
        'first = inbox / "alpha.pdf"',
        'selected = inbox / "beta.pdf"',
        'unsupported = inbox / "notes.txt"',
        'input="4\\n1\\n2\\n\\nb\\nq\\n"',
        '"4. Scan Routing"',
        '"Scan Routing — Route Scans"',
        '"1. alpha.pdf"',
        '"2. beta.pdf"',
        '"notes.txt" not in rendered',
        '"C. Choose custom file/folder path"',
        '"R. Refresh"',
        'f"Source: {selected}"',
        '"Type ROUTE to confirm"',
        '"Scan Routing Complete" not in rendered',
        'after == before',
        'not any(scans_source_dir(root).iterdir())',
        'not any(routing_review_dir(root).iterdir())',
        "Issue #103 shared installed-wheel scan-inbox acceptance: PASS",
    )
    for fragment in required:
        assert fragment in source


def test_issue103_shared_smoke_is_wired_into_authoritative_validator() -> None:
    source = VALIDATOR.read_text(encoding="utf-8")
    assert "scripts/smoke_test_feature_wheels.py" in source
    assert "installed-wheel smoke: shared feature scenarios" in source
    assert "scripts/smoke_test_scan_inbox_routing_wheel.py" in (
        ROOT / "scripts" / "smoke_test_feature_wheels.py"
    ).read_text(encoding="utf-8")


def test_issue103_teacher_documentation_freezes_inbox_first_boundary() -> None:
    readme = README.read_text(encoding="utf-8")
    normalized_readme = " ".join(readme.split())
    required = (
        "## Scan Routing",
        "shared Paper Data Suite `scans_inbox/`",
        "supported top-level PDF/image files",
        "`R. Refresh`",
        "`C. Choose custom file/folder path`",
        "`ROUTE`",
        "Core PDS2",
        "does not delete, move, rename, or archive",
    )
    for fragment in required:
        assert fragment in normalized_readme

    changelog = CHANGELOG.read_text(encoding="utf-8")
    assert "Issue #103" in changelog
    assert "inbox-first teacher scan routing" in changelog
    assert "custom file/folder fallback" in changelog
    assert "retain-first Core PDS2" in changelog
