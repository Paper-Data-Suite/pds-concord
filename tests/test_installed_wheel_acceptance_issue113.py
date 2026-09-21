from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "scripts" / "smoke_test_issue113_relationships_wheel.py"
VALIDATOR = ROOT / "scripts" / "validate_repository.py"
DOC = ROOT / "docs" / "v0.3.1-starter-subject-relationships.md"


def _smoke_source() -> str:
    return SMOKE.read_text(encoding="utf-8")


def test_issue113_installed_smoke_compiles_and_is_isolated() -> None:
    source = _smoke_source()
    ast.parse(source)
    required = (
        "venv.EnvBuilder(with_pip=True)",
        '"pip", "install"',
        '[str(python), "-I", str(smoke_path)]',
        "site-packages",
        'metadata.version("pds-core") == "0.6.3"',
        'metadata.version("pds-concord") == "0.3.0"',
        "Issue #113 candidate wheel SHA-256:",
        "Issue #113 Core wheel SHA-256:",
    )
    for fragment in required:
        assert fragment in source


def test_issue113_installed_smoke_covers_required_acceptance_path() -> None:
    source = _smoke_source()
    required = (
        "create_template_library(",
        "prepare_starter_template_install(",
        "commit_starter_template_install(",
        'fresh_install.outcome == "installed"',
        'upgrade.outcome == "upgraded"',
        "PacketSubjectBinding(",
        "prepare_packet_instantiation(",
        "commit_packet_instantiation(",
        "render_packet_instance(",
        "parse_pds2_payload(",
        "load_route_registration(",
        "route_scan_sources(",
        "load_current_record_graph(",
        "generated.artifact_authors",
        "generated.artifact_subjects",
        "returned.scan_references",
        "load_current_packet(",
        "replay.replayed",
        "replay.output_sha256 == first_sha",
        "replay.output_path.read_bytes() == first_bytes",
        "Issue #113 isolated installed-wheel acceptance: PASS",
    )
    for fragment in required:
        assert fragment in source


def test_issue113_installed_smoke_freezes_relationship_and_route_semantics() -> None:
    source = _smoke_source()
    required = (
        'proposed_subject_role == "reviewed_subject"',
        'attribution_status == "proposed"',
        'confirmation_status == "proposed"',
        '"Reviewer: Alexandria M."',
        '"Reviewee: Christopher V."',
        '"activity_id"',
        '"artifact_instance_id"',
        '"artifact_page_id"',
        '"page_number"',
        'page.page_status for page in returned.artifact_pages',
        '"returned"',
        'historical_plan.proposed_subject_role == "observed_participant"',
    )
    for fragment in required:
        assert fragment in source


def test_issue113_installed_smoke_is_wired_into_authoritative_validator() -> None:
    source = VALIDATOR.read_text(encoding="utf-8")
    assert "scripts/smoke_test_issue113_relationships_wheel.py" in source
    assert "installed-wheel smoke: issue #113 starter relationships" in source


def test_issue113_documentation_defines_installed_wheel_gate() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = (
        "## Issue #113 installed-wheel acceptance",
        "scripts/smoke_test_issue113_relationships_wheel.py",
        "fresh affected-starter install",
        "packaged v1 -> v2 upgrade",
        "explicit peer-review Subject binding",
        "real PDF rendering",
        "PDS2 route verification",
        "returned scan routing",
        "Artifact Author/Subject inspection",
        "historical v1 byte-for-byte replay",
        "python -I",
    )
    for fragment in required:
        assert fragment in text


def test_issue113_documentation_records_installed_wheel_acceptance() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = (
        "### Accepted installed-wheel evidence — 2026-09-20",
        "038f37a450addb1c267d9e89a9bb082b398cc4f6",
        "78a133e0317f336dc81efb3dbc977bb84ed4b20048d2d00ace11ebc0f56322e2",
        "98d7596ce0eed26e4d56a17bbbbd644db3014259b56a45783a173fe8237af5e5",
        "pip check:",
        "historical v1 byte-for-byte replay after upgrade:",
        "overall installed-wheel acceptance:",
        "PASS",
    )
    for fragment in required:
        assert fragment in text
