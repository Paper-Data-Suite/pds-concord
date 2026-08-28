from __future__ import annotations

from pathlib import Path

from pds_core.module_operations import (
    MODULE_OPERATIONS_CONTRACT_VERSION,
    ModuleOperationsRequest,
    invoke_module_attention,
    invoke_module_readiness,
    validate_module_operations_profile,
)

from concord.pds_operations import get_module_operations_profile


def test_profile_exposes_attention_only_for_issue67() -> None:
    profile = get_module_operations_profile()
    assert validate_module_operations_profile(profile) is profile
    assert profile.module_id == "concord"
    assert profile.supported_core_operations_contract_versions == frozenset(
        {MODULE_OPERATIONS_CONTRACT_VERSION}
    )
    assert profile.attention_provider is not None
    assert profile.readiness_provider is None


def test_core_invocation_preserves_absent_readiness_and_unavailable_attention() -> None:
    profile = get_module_operations_profile()
    request = ModuleOperationsRequest()

    readiness = invoke_module_readiness(profile, request)
    attention = invoke_module_attention(profile, request)

    assert readiness.code == "module_operations.capability_absent"
    assert readiness.report is None
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
