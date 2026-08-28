from __future__ import annotations

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "v0.3.0-activity-attention-next-actions.md"
SMOKE = ROOT / "scripts" / "smoke_test_attention_provider_wheel.py"


def test_normative_attention_document_records_issue67_boundaries() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = (
        "ActivityAttentionItem",
        "ActivityAttentionSummary",
        "inspect_activity_attention",
        "list_activity_attention",
        "attention != readiness",
        "Plan -> Prepare -> Collect -> Review -> Score -> Share",
        "concord_score_ready",
        "concord_share_publish",
        "concord_attention_partial",
        "concord_attention_unavailable",
        "paper_data_suite.module_operations",
        "concord.pds_operations:get_module_operations_profile",
        "readiness_provider = None",
        "A. Open next action",
        "A. Attention needed",
        "scripts/smoke_test_attention_provider_wheel.py",
        "pds-core>=0.6.3,<0.7",
    )
    for phrase in required:
        assert phrase in text


def test_package_declares_exact_module_operations_entry_point() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    groups = data["project"]["entry-points"]
    assert groups["paper_data_suite.module_operations"] == {
        "concord": "concord.pds_operations:get_module_operations_profile"
    }


def test_package_checker_requires_operations_provider_and_files() -> None:
    text = (ROOT / "scripts" / "check_package.py").read_text(encoding="utf-8")
    assert "[paper_data_suite.module_operations]" in text
    assert "concord = concord.pds_operations:get_module_operations_profile" in text
    assert "The Concord module-operations entry point must occur exactly once." in text
    assert '"paper-data-suite"' in text
    for path in (
        "concord/attention_provider.py",
        "concord/pds_operations.py",
        "concord/workflows/activity_attention.py",
        "concord/academic_result_share_attention.py",
    ):
        assert path in text


def test_repository_validation_runs_installed_attention_smoke() -> None:
    text = (ROOT / "scripts" / "validate_repository.py").read_text(
        encoding="utf-8"
    )
    assert "scripts/smoke_test_attention_provider_wheel.py" in text


def test_installed_smoke_isolated_and_uses_core_invocation() -> None:
    text = SMOKE.read_text(encoding="utf-8")
    required = (
        'env.pop("PYTHONPATH", None)',
        'env["PYTHONNOUSERSITE"] = "1"',
        '"-I"',
        "diagnose_core_providers",
        "invoke_module_attention",
        "invoke_module_readiness",
        '"module_operations.evaluated"',
        '"module_operations.evaluation_unavailable"',
        '"concord_plan_prepare"',
        '"concord_attention_unavailable"',
        "fingerprint(root)",
        "assert fingerprint(root) == before",
        '"paper-data-suite"',
        '"quillan"',
        '"pds-meridian"',
    )
    for phrase in required:
        assert phrase in text


def test_documentation_validation_requires_attention_document() -> None:
    text = (ROOT / "scripts" / "check_documentation.py").read_text(
        encoding="utf-8"
    )
    assert "ACTIVITY_ATTENTION_NEXT_ACTIONS_DOC" in text
    assert "REQUIRED_ACTIVITY_ATTENTION_NEXT_ACTIONS_PHRASES" in text
    assert "v0.3.0-activity-attention-next-actions.md" in text


def test_active_docs_expose_attention_navigation_and_issue68_boundary() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    docs_index = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    cli = (ROOT / "docs" / "cli-contract.md").read_text(encoding="utf-8")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

    assert "v0.3.0-activity-attention-next-actions.md" in readme
    assert "v0.3.0-activity-attention-next-actions.md" in docs_index
    assert "A. Open next action" in cli
    assert "A. Attention needed" in cli
    assert "readiness_provider=None" in changelog
