from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from pds_core.module_operations import ModuleOperationsRequest
from pds_core.routing_models import ModuleWorkRef

import concord.attention_provider as provider
from concord.storage_errors import ConcordStorageIntegrityError
from concord.workflows.activity_attention import (
    ActivityAttentionItem,
    ActivityAttentionSummary,
)


def _work(class_id: str, activity_id: str) -> ModuleWorkRef:
    return ModuleWorkRef(
        module_id="concord",
        class_id=class_id,
        work_id=activity_id,
    )


def _summary(
    class_id: str,
    activity_id: str,
    *,
    code: str = "concord_plan_approve",
    label: str = "Group plans are waiting for teacher approval",
    count: int = 1,
    action_id: str = "open_activity_plan",
) -> ActivityAttentionSummary:
    return ActivityAttentionSummary(
        class_id=class_id,
        activity_id=activity_id,
        title=f"Activity {activity_id}",
        items=(
            ActivityAttentionItem(
                code=code,
                label=label,
                task="plan",
                count=count,
                action_id=action_id,
            ),
        ),
    )


def _resolved_root(monkeypatch: pytest.MonkeyPatch, root: Path) -> None:
    monkeypatch.setattr(
        provider,
        "resolve_read_workspace_root",
        lambda _root: root,
    )


def test_missing_explicit_workspace_is_unavailable() -> None:
    report = provider.evaluate_concord_attention(ModuleOperationsRequest())
    assert report.evaluation == "unavailable"
    assert report.summaries == ()
    assert [notice.code for notice in report.notices] == [
        "concord_attention_unavailable"
    ]


def test_valid_scope_with_no_activities_is_evaluated_empty(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _resolved_root(monkeypatch, tmp_path)
    monkeypatch.setattr(provider, "list_activity_work_refs", lambda *_args: ())

    report = provider.evaluate_concord_attention(
        ModuleOperationsRequest(
            workspace_root=tmp_path,
            class_id="class-1",
        )
    )

    assert report.evaluation == "evaluated"
    assert report.summaries == ()
    assert report.notices == ()


def test_exact_class_filter_is_used_for_discovery(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _resolved_root(monkeypatch, tmp_path)
    seen: list[str] = []

    def _refs(_root: Path, class_id: str) -> tuple[ModuleWorkRef, ...]:
        seen.append(class_id)
        return ()

    monkeypatch.setattr(provider, "list_activity_work_refs", _refs)

    provider.evaluate_concord_attention(
        ModuleOperationsRequest(
            workspace_root=tmp_path,
            class_id="class-exact",
        )
    )

    assert seen == ["class-exact"]


def test_aggregate_preserves_single_work_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _resolved_root(monkeypatch, tmp_path)
    monkeypatch.setattr(
        provider,
        "list_activity_work_refs",
        lambda *_args: (_work("class-1", "activity-1"),),
    )
    monkeypatch.setattr(
        provider,
        "inspect_activity_attention",
        lambda *_args, **_kwargs: _summary("class-1", "activity-1", count=3),
    )

    report = provider.evaluate_concord_attention(
        ModuleOperationsRequest(
            workspace_root=tmp_path,
            class_id="class-1",
        )
    )

    assert len(report.summaries) == 1
    summary = report.summaries[0]
    assert summary.code == "concord_plan_approve"
    assert summary.count == 3
    assert summary.class_id == "class-1"
    assert summary.work_ref == _work("class-1", "activity-1")
    assert summary.action is not None
    assert summary.action.module_id == "concord"
    assert summary.action.action_id == "open_activity_plan"


def test_multi_activity_aggregate_omits_ambiguous_work_ref(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _resolved_root(monkeypatch, tmp_path)
    works = (
        _work("class-1", "activity-a"),
        _work("class-1", "activity-b"),
    )
    monkeypatch.setattr(provider, "list_activity_work_refs", lambda *_args: works)
    monkeypatch.setattr(
        provider,
        "inspect_activity_attention",
        lambda class_id, activity_id, **_kwargs: _summary(
            class_id,
            activity_id,
            count=2,
        ),
    )

    report = provider.evaluate_concord_attention(
        ModuleOperationsRequest(
            workspace_root=tmp_path,
            class_id="class-1",
        )
    )

    summary = report.summaries[0]
    assert summary.count == 4
    assert summary.class_id == "class-1"
    assert summary.work_ref is None


def test_workspace_aggregate_omits_ambiguous_class_and_work_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _resolved_root(monkeypatch, tmp_path)
    monkeypatch.setattr(
        provider,
        "list_available_classes",
        lambda _root: (
            SimpleNamespace(class_id="class-a"),
            SimpleNamespace(class_id="class-b"),
        ),
    )
    monkeypatch.setattr(
        provider,
        "list_activity_work_refs",
        lambda _root, class_id: (_work(class_id, f"{class_id}-activity"),),
    )
    monkeypatch.setattr(
        provider,
        "inspect_activity_attention",
        lambda class_id, activity_id, **_kwargs: _summary(class_id, activity_id),
    )

    report = provider.evaluate_concord_attention(
        ModuleOperationsRequest(workspace_root=tmp_path)
    )

    summary = report.summaries[0]
    assert summary.count == 2
    assert summary.class_id is None
    assert summary.work_ref is None


def test_partial_activity_failure_preserves_unrelated_attention(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _resolved_root(monkeypatch, tmp_path)
    works = (
        _work("class-1", "good"),
        _work("class-1", "bad"),
    )
    monkeypatch.setattr(provider, "list_activity_work_refs", lambda *_args: works)

    def _inspect(
        class_id: str,
        activity_id: str,
        **_kwargs: object,
    ) -> ActivityAttentionSummary:
        if activity_id == "bad":
            raise ConcordStorageIntegrityError("private corrupt path detail")
        return _summary(class_id, activity_id)

    monkeypatch.setattr(provider, "inspect_activity_attention", _inspect)

    report = provider.evaluate_concord_attention(
        ModuleOperationsRequest(
            workspace_root=tmp_path,
            class_id="class-1",
        )
    )

    assert report.evaluation == "evaluated"
    assert len(report.summaries) == 1
    assert report.summaries[0].count == 1
    assert [notice.code for notice in report.notices] == [
        "concord_attention_partial"
    ]
    assert "private corrupt path detail" not in repr(report)


def test_foundational_requested_scope_failure_is_unavailable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _resolved_root(monkeypatch, tmp_path)

    def _broken(*_args: object) -> tuple[ModuleWorkRef, ...]:
        raise ConcordStorageIntegrityError("unsafe class work collection")

    monkeypatch.setattr(provider, "list_activity_work_refs", _broken)

    report = provider.evaluate_concord_attention(
        ModuleOperationsRequest(
            workspace_root=tmp_path,
            class_id="class-1",
        )
    )

    assert report.evaluation == "unavailable"
    assert report.summaries == ()
    assert report.notices[0].code == "concord_attention_unavailable"
    assert "unsafe class work collection" not in repr(report)


def test_unrequested_class_discovery_failure_is_partial(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _resolved_root(monkeypatch, tmp_path)
    monkeypatch.setattr(
        provider,
        "list_available_classes",
        lambda _root: (
            SimpleNamespace(class_id="good-class"),
            SimpleNamespace(class_id="bad-class"),
        ),
    )

    def _refs(_root: Path, class_id: str) -> tuple[ModuleWorkRef, ...]:
        if class_id == "bad-class":
            raise ConcordStorageIntegrityError("unsafe")
        return (_work(class_id, "activity-1"),)

    monkeypatch.setattr(provider, "list_activity_work_refs", _refs)
    monkeypatch.setattr(
        provider,
        "inspect_activity_attention",
        lambda class_id, activity_id, **_kwargs: _summary(class_id, activity_id),
    )

    report = provider.evaluate_concord_attention(
        ModuleOperationsRequest(workspace_root=tmp_path)
    )

    assert report.evaluation == "evaluated"
    assert len(report.summaries) == 1
    assert report.summaries[0].class_id == "good-class"
    assert report.notices[0].code == "concord_attention_partial"


def test_unexpected_provider_failure_is_not_flattened(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _resolved_root(monkeypatch, tmp_path)
    monkeypatch.setattr(
        provider,
        "list_activity_work_refs",
        lambda *_args: (_work("class-1", "activity-1"),),
    )

    def _bug(*_args: object, **_kwargs: object) -> ActivityAttentionSummary:
        raise RuntimeError("synthetic programming failure")

    monkeypatch.setattr(provider, "inspect_activity_attention", _bug)

    with pytest.raises(RuntimeError, match="synthetic programming failure"):
        provider.evaluate_concord_attention(
            ModuleOperationsRequest(
                workspace_root=tmp_path,
                class_id="class-1",
            )
        )


def test_active_school_year_does_not_invent_attention_semantics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _resolved_root(monkeypatch, tmp_path)
    monkeypatch.setattr(provider, "list_activity_work_refs", lambda *_args: ())

    report = provider.evaluate_concord_attention(
        ModuleOperationsRequest(
            workspace_root=tmp_path,
            active_school_year="2026-2027",
            class_id="class-1",
        )
    )

    assert report.evaluation == "evaluated"
    assert report.summaries == ()
