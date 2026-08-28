from __future__ import annotations

from pathlib import Path

from pds_core.module_operations import (
    MODULE_OPERATIONS_CONTRACT_VERSION,
    ModuleOperationsRequest,
    invoke_module_attention,
    validate_module_operations_profile,
)

from concord.pds_operations import get_module_operations_profile


def test_profile_preserves_issue67_attention_capability() -> None:
    profile = get_module_operations_profile()
    assert validate_module_operations_profile(profile) is profile
    assert profile.module_id == "concord"
    assert profile.supported_core_operations_contract_versions == frozenset(
        {MODULE_OPERATIONS_CONTRACT_VERSION}
    )
    assert profile.attention_provider is not None


def test_core_invocation_preserves_unavailable_attention_without_workspace() -> None:
    profile = get_module_operations_profile()
    attention = invoke_module_attention(profile, ModuleOperationsRequest())

    assert attention.code == "module_operations.evaluation_unavailable"
    assert attention.report is not None
    assert attention.report.evaluation == "unavailable"


def test_pyproject_registers_exact_concord_operations_entry_point() -> None:
    text = Path("pyproject.toml").read_text(encoding="utf-8")
    assert '[project.entry-points."paper_data_suite.module_operations"]' in text
    assert (
        'concord = "concord.pds_operations:get_module_operations_profile"'
        in text
    )
    assert text.count(
        '[project.entry-points."paper_data_suite.module_operations"]'
    ) == 1
