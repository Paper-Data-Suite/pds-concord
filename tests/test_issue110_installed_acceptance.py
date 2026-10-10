from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "scripts" / "smoke_test_packet_generation_rendering_wheel.py"
VALIDATOR = ROOT / "scripts" / "validate_repository.py"
DOC = ROOT / "docs" / "v0.3.1-generation-wide-packet-rendering.md"
PYPROJECT = ROOT / "pyproject.toml"

CORE_064_SHA256 = (
    "48cea9317f2967bdc0f2d4c14349a56677c7c3f8211f0f33978ccb1a1c75859b"
)
CORE_065_SHA256 = (
    "9ace75f17b23b7f0ed6a709d531af5120db43d0325b4148d26f2d6ba1d4b3c18"
)


def _source() -> str:
    return SMOKE.read_text(encoding="utf-8")


def test_issue110_installed_smoke_compiles_and_authenticates_core064() -> None:
    source = _source()
    ast.parse(source)
    required = (
        "venv.EnvBuilder(with_pip=True)",
        '"pip", "install"',
        '[str(python), "-I", str(smoke_path)]',
        'metadata.version("pds-core") == "0.6.5"',
        'metadata.version("pds-concord") == "0.3.1"',
        CORE_065_SHA256,
        "Issue #110 candidate wheel SHA-256:",
        "Issue #110 Core wheel SHA-256:",
        "site-packages",
    )
    for fragment in required:
        assert fragment in source


def test_issue110_installed_smoke_covers_generation_render_and_reprint() -> None:
    source = _source()
    required = (
        "prepared.packet_instance_count == 3",
        "len(committed.packet_instance_ids) == 3",
        "list_packet_generations(",
        "RenderPacketGenerationRequest(",
        "expected_snapshot_revision=reviewed.snapshot_revision",
        "render_packet_generation(",
        "first_revision == source.snapshot_revision + 1",
        "expected_snapshot_revision=reviewed_reprint.snapshot_revision",
        "all(packet.replayed for packet in replay.packets)",
        "all(packet.commit.no_op for packet in replay.packets)",
        "output_state(replay) == first_outputs",
        "route_state(root, replay) == first_routes",
        "load_route_registration(",
        "parse_pds2_payload(payload)",
        "Issue #110 isolated installed-wheel acceptance: PASS",
    )
    for fragment in required:
        assert fragment in source


def test_issue110_installed_smoke_covers_cli_menu_and_output_opening() -> None:
    source = _source()
    required = (
        "packet_runtime.handle_generation_render(",
        '"Packet Instances: 3"',
        "launch_packet_generation_menu(",
        '"4. Render / reprint a complete generation"',
        '"5. Render / reprint one Packet Instance"',
        "open_rendered_packet_output(",
        "open_rendered_packet_output_directory(",
        "rendered_output_module.open_local_path = fake_open",
        "canonical_after_open.snapshot_revision",
    )
    for fragment in required:
        assert fragment in source


def test_issue110_installed_smoke_is_wired_into_authoritative_validator() -> None:
    source = VALIDATOR.read_text(encoding="utf-8")
    assert "scripts/smoke_test_packet_generation_rendering_wheel.py" in source
    tree = ast.parse(source)
    assert any(
        isinstance(node, ast.Constant)
        and node.value
        == "installed-wheel smoke: issue #110 Packet generation rendering"
        for node in ast.walk(tree)
    )


def test_issue110_docs_and_dependency_floor_match_installed_qualification() -> None:
    doc = DOC.read_text(encoding="utf-8")
    pyproject = PYPROJECT.read_text(encoding="utf-8")
    assert "scripts/smoke_test_packet_generation_rendering_wheel.py" in doc
    assert "Core 0.6.4" in doc
    assert CORE_064_SHA256 in doc
    assert "python -I" in doc
    assert "site-packages" in doc
    assert '"pds-core>=0.6.5,<0.7"' in pyproject
