from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "scripts" / "smoke_test_rendered_output_opening_wheel.py"
VALIDATOR = ROOT / "scripts" / "validate_repository.py"
DOC = ROOT / "docs" / "v0.3.1-rendered-output-opening.md"
CLI_DOC = ROOT / "docs" / "cli-contract.md"
PACKAGE_CHECK = ROOT / "scripts" / "check_package.py"
RELEASE_CHECK = ROOT / "scripts" / "verify_release_artifacts.py"


def _smoke_source() -> str:
    return SMOKE.read_text(encoding="utf-8")


def test_issue101_installed_smoke_compiles_and_isolated() -> None:
    source = _smoke_source()
    ast.parse(source)
    required = (
        "venv.EnvBuilder(with_pip=True)",
        '"pip", "install"',
        '[str(python), "-I", str(smoke_path)]',
        "site-packages",
        'metadata.version("pds-core") == "0.6.3"',
        'metadata.version("pds-concord") == "0.3.0"',
        "98d7596ce0eed26e4d56a17bbbbd644db3014259b56a45783a173fe8237af5e5",
        "Issue #101 candidate wheel SHA-256:",
        "Issue #101 Core wheel SHA-256:",
    )
    for fragment in required:
        assert fragment in source


def test_issue101_installed_smoke_covers_required_opening_path() -> None:
    source = _smoke_source()
    required = (
        'starter_key="think_pair_share"',
        "prepare_packet_from_template(",
        "commit_packet_from_template(",
        "prepare_packet_instantiation(",
        "commit_packet_instantiation(",
        "render_packet_instance(",
        "resolve_rendered_packet_output(",
        "open_rendered_packet_output(",
        "open_rendered_packet_output_directory(",
        "rendered_output_module.open_local_path = fake_open",
        "canonical_before.snapshot_revision",
        "canonical_before.snapshot_sha256",
        "routes_after_open == routes_before",
        "issue101-installed-tamper",
        "ConcordWorkflowConflictError",
        "ConcordWorkflowNotFoundError",
        "assert not rendered.output_path.exists()",
        "Issue #101 isolated installed-wheel acceptance: PASS",
    )
    for fragment in required:
        assert fragment in source


def test_issue101_installed_smoke_is_wired_into_authoritative_validator() -> None:
    source = VALIDATOR.read_text(encoding="utf-8")
    assert "scripts/smoke_test_rendered_output_opening_wheel.py" in source
    assert "installed-wheel smoke: issue #101 rendered output opening" in source


def test_issue101_docs_freeze_open_vs_render_boundary() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = (
        "PacketInstance.output_relative_path",
        "PacketInstance.output_sha256",
        "OPEN != RENDER / REPRINT",
        "resolve_rendered_packet_output",
        "open_rendered_packet_output",
        "open_rendered_packet_output_directory",
        "pds_core.local_open.open_local_path",
        "ConcordWorkflowOpenError",
        "Activity",
        "Prepare",
        "View prepared materials",
        "Render / reprint",
        "teacher-local working convenience",
        "Historical compatibility",
        "concord packet instance-open",
        "concord packet instance-open-folder",
        "scripts/smoke_test_rendered_output_opening_wheel.py",
        "issue #111",
    )
    for fragment in required:
        assert fragment in text


def test_issue101_cli_and_package_qualification_are_documented() -> None:
    cli = CLI_DOC.read_text(encoding="utf-8")
    assert "concord packet instance-open" in cli
    assert "concord packet instance-open-folder" in cli
    assert "Open is read-only" in cli

    package = PACKAGE_CHECK.read_text(encoding="utf-8")
    release = RELEASE_CHECK.read_text(encoding="utf-8")
    for source in (package, release):
        assert "concord/workflows/rendered_output.py" in source
