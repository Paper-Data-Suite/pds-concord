"""Installed Concord module-operations profile for Core v1."""

from __future__ import annotations

from pds_core.module_operations import (
    MODULE_OPERATIONS_CONTRACT_VERSION,
    ModuleAttentionReport,
    ModuleOperationsProfile,
    ModuleOperationsRequest,
    ModuleReadinessReport,
    validate_module_operations_profile,
)

from concord.pds_contract import CONCORD_MODULE_ID


def evaluate_concord_attention(
    request: ModuleOperationsRequest,
    /,
) -> ModuleAttentionReport:
    """Lazily evaluate Concord-owned attention for one neutral Core request."""
    from concord.attention_provider import evaluate_concord_attention as _evaluate

    return _evaluate(request)


def evaluate_concord_readiness(
    request: ModuleOperationsRequest,
    /,
) -> ModuleReadinessReport:
    """Lazily evaluate Concord-owned readiness for one neutral Core request."""
    from concord.readiness_provider import evaluate_concord_readiness as _evaluate

    return _evaluate(request)


def get_module_operations_profile() -> ModuleOperationsProfile:
    """Return Concord's validated Core v1 operations profile."""
    return validate_module_operations_profile(
        ModuleOperationsProfile(
            module_id=CONCORD_MODULE_ID,
            supported_core_operations_contract_versions=frozenset(
                {MODULE_OPERATIONS_CONTRACT_VERSION}
            ),
            readiness_provider=evaluate_concord_readiness,
            attention_provider=evaluate_concord_attention,
        )
    )


__all__ = [
    "evaluate_concord_attention",
    "evaluate_concord_readiness",
    "get_module_operations_profile",
]
