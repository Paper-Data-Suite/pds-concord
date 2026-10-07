from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "v0.3.1-generation-wide-packet-rendering.md"
DOC_INDEX = ROOT / "docs" / "README.md"
ROOT_README = ROOT / "README.md"
CHANGELOG = ROOT / "CHANGELOG.md"
DOC_CHECK = ROOT / "scripts" / "check_documentation.py"
PACKAGE_CHECK = ROOT / "scripts" / "check_package.py"
PYPROJECT = ROOT / "pyproject.toml"
PERFORMANCE = ROOT / "tests" / "test_packet_generation_performance_issue110.py"

CORE_064_SHA256 = (
    "48cea9317f2967bdc0f2d4c14349a56677c7c3f8211f0f33978ccb1a1c75859b"
)


def test_issue110_normative_document_covers_generation_contract() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = (
        "Generation is the runtime unit",
        "PacketGenerationSummary",
        "expected_snapshot_revision",
        "last-safe-point currentness check",
        "Render / reprint a complete generation",
        "REPRINT",
        "RENDER",
        "routes_pending",
        "Packet target != Artifact Author != Artifact Subject",
        "(template_id, template_version_id)",
        "Reprint allocates zero replacement routes",
        "rendered/packets/cgo_<24hex>.pdf",
        "PacketGenerationRenderPartialSuccessError",
        "PacketGenerationLifecyclePartialSuccessError",
        "full Activity graph materializations = 1",
        "generation lifecycle commits = 1",
        "scripts/smoke_test_packet_generation_rendering_wheel.py",
        "Core 0.6.4",
        CORE_064_SHA256,
        "python -I",
        "site-packages",
        "pds-core>=0.6.3,<0.7",
        "No dependency-floor change",
        "Issue #114",
    )
    for fragment in required:
        assert fragment in text


def test_issue110_document_is_indexed_and_root_readme_exposes_workflow() -> None:
    index = DOC_INDEX.read_text(encoding="utf-8")
    readme = ROOT_README.read_text(encoding="utf-8")
    assert DOC.name in index
    assert "Issue #110" in readme
    assert "complete-generation" in readme
    assert "RENDER" in readme
    assert "REPRINT" in readme


def test_issue110_changelog_records_optimized_generation_behavior() -> None:
    text = CHANGELOG.read_text(encoding="utf-8")
    required = (
        "Issue #110",
        "one exact Activity snapshot",
        "complete-generation",
        "RENDER",
        "REPRINT",
        "1, 10, and 30",
        "one canonical lifecycle commit",
    )
    for fragment in required:
        assert fragment in text


def test_issue110_documentation_checker_requires_normative_contract() -> None:
    source = DOC_CHECK.read_text(encoding="utf-8")
    required = (
        "GENERATION_PACKET_RENDERING_DOC",
        "REQUIRED_GENERATION_PACKET_RENDERING_PHRASES",
        "v0.3.1-generation-wide-packet-rendering.md",
        "PacketGenerationSummary",
        "Render / reprint a complete generation",
        "scripts/smoke_test_packet_generation_rendering_wheel.py",
        CORE_064_SHA256,
    )
    for fragment in required:
        assert fragment in source


def test_issue110_generation_modules_are_required_wheel_content() -> None:
    source = PACKAGE_CHECK.read_text(encoding="utf-8")
    required = (
        "concord/menu_packet_generation.py",
        "concord/workflows/packet_generation.py",
        "concord/workflows/packet_rendering.py",
    )
    for fragment in required:
        assert fragment in source


def test_issue110_structural_acceptance_records_1_10_30_and_bounded_commit() -> None:
    text = PERFORMANCE.read_text(encoding="utf-8")
    assert '@pytest.mark.parametrize("target_count", (1, 10, 30))' in text
    assert "assert graph_loads == [(tmp_path, work)]" in text
    assert "assert pointer_loads == [(tmp_path, work)]" in text
    assert "assert commits == [(target_count, 9)]" in text


def test_issue110_dependency_floor_remains_core063_compatible() -> None:
    text = PYPROJECT.read_text(encoding="utf-8")
    assert '"pds-core>=0.6.3,<0.7"' in text
    assert '"pds-core>=0.6.4,<0.7"' not in text
