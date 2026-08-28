from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.module_operations import (
    MODULE_OPERATIONS_CONTRACT_VERSION,
    ModuleOperationsRequest,
    invoke_module_attention,
    invoke_module_operations,
    invoke_module_readiness,
    validate_module_operations_profile,
)
from pds_core.routing_models import ModuleWorkRef

import concord.attention_provider as attention_provider
import concord.pds_operations as operations
from concord.workflows.activity_attention import (
    ActivityAttentionItem,
    ActivityAttentionSummary,
)


def _workspace(tmp_path: Path) -> Path:
    root = tmp_path / "workspace"
    root.mkdir()
    return root


def _class(root: Path, class_id: str = "class-1") -> None:
    timestamp = datetime(2026, 8, 28, tzinfo=timezone.utc)
    metadata = create_class_metadata(
        class_id,
        "2026-2027",
        created_at=timestamp,
    )
    write_class_metadata_for_class(root, metadata)


def test_profile_exposes_both_core_v1_operations_capabilities() -> None:
    profile = operations.get_module_operations_profile()

    assert validate_module_operations_profile(profile) is profile
    assert profile.module_id == "concord"
    assert profile.supported_core_operations_contract_versions == frozenset(
        {MODULE_OPERATIONS_CONTRACT_VERSION}
    )
    assert profile.readiness_provider is not None
    assert profile.attention_provider is not None


def test_missing_workspace_is_unavailable_for_both_capabilities() -> None:
    profile = operations.get_module_operations_profile()
    readiness, attention = invoke_module_operations(
        profile,
        ModuleOperationsRequest(),
    )

    assert readiness.code == "module_operations.evaluation_unavailable"
    assert readiness.report is not None
    assert readiness.report.evaluation == "unavailable"
    assert readiness.report.ready is None

    assert attention.code == "module_operations.evaluation_unavailable"
    assert attention.report is not None
    assert attention.report.evaluation == "unavailable"


def test_valid_empty_workspace_evaluates_ready_and_attention_empty(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    profile = operations.get_module_operations_profile()
    request = ModuleOperationsRequest(workspace_root=root)

    readiness = invoke_module_readiness(profile, request)
    attention = invoke_module_attention(profile, request)

    assert readiness.code == "module_operations.evaluated"
    assert readiness.report is not None
    assert readiness.report.evaluation == "evaluated"
    assert readiness.report.ready is True

    assert attention.code == "module_operations.evaluated"
    assert attention.report is not None
    assert attention.report.evaluation == "evaluated"
    assert attention.report.summaries == ()


def test_ready_class_can_coexist_with_nonempty_attention(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _workspace(tmp_path)
    _class(root)

    work = ModuleWorkRef(
        module_id="concord",
        class_id="class-1",
        work_id="activity-1",
    )
    monkeypatch.setattr(
        attention_provider,
        "list_activity_work_refs",
        lambda *_args: (work,),
    )
    monkeypatch.setattr(
        attention_provider,
        "inspect_activity_attention",
        lambda *_args, **_kwargs: ActivityAttentionSummary(
            class_id="class-1",
            activity_id="activity-1",
            title="Synthetic Activity",
            items=(
                ActivityAttentionItem(
                    code="concord_plan_approve",
                    label="Group plans are waiting for teacher approval",
                    task="plan",
                    count=2,
                    action_id="open_activity_plan",
                ),
            ),
        ),
    )

    profile = operations.get_module_operations_profile()
    readiness, attention = invoke_module_operations(
        profile,
        ModuleOperationsRequest(
            workspace_root=root,
            class_id="class-1",
        ),
    )

    assert readiness.code == "module_operations.evaluated"
    assert readiness.report is not None
    assert readiness.report.ready is True

    assert attention.code == "module_operations.evaluated"
    assert attention.report is not None
    assert len(attention.report.summaries) == 1
    assert attention.report.summaries[0].code == "concord_plan_approve"
    assert attention.report.summaries[0].count == 2


def test_readiness_failure_isolated_from_attention(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _workspace(tmp_path)

    def _broken_readiness(_request: ModuleOperationsRequest) -> object:
        raise RuntimeError("synthetic readiness failure")

    monkeypatch.setattr(
        operations,
        "evaluate_concord_readiness",
        _broken_readiness,
    )
    profile = operations.get_module_operations_profile()

    readiness, attention = invoke_module_operations(
        profile,
        ModuleOperationsRequest(workspace_root=root),
    )

    assert readiness.code == "module_operations.provider_failed"
    assert readiness.report is None

    assert attention.code == "module_operations.evaluated"
    assert attention.report is not None
    assert attention.report.summaries == ()
