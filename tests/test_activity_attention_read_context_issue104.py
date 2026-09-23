from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import concord.menu_activity as menu_activity
import concord.workflows.activity_attention as attention
from concord.academic_result_share_attention import AcademicResultShareAttentionState
from concord.workflows import ActivitySummary


def _context(root: Path, artifact_count: int, *, title: str = "Seminar") -> Any:
    artifacts = tuple(
        SimpleNamespace(
            artifact_instance_id=f"artifact-{index:03d}",
            activity_id="activity-1",
        )
        for index in range(artifact_count)
    )
    graph = SimpleNamespace(
        sessions=(SimpleNamespace(session_id="session-1"),),
        groups=(),
        group_plans=(),
        packet_instances=(),
        artifact_instances=artifacts,
        artifact_authors=(),
        artifact_subjects=(),
        artifact_reviews=(),
        moderation_records=(),
    )
    return SimpleNamespace(
        root=root,
        work=SimpleNamespace(class_id="class-1", work_id="activity-1"),
        snapshot_revision=7,
        snapshot_sha256="a" * 64,
        graph=graph,
        activity=SimpleNamespace(
            activity_id="activity-1",
            title=title,
            status="active",
            scoring_orientation="evidence_only",
        ),
    )


def _inactive_share() -> AcademicResultShareAttentionState:
    return AcademicResultShareAttentionState(
        class_id="class-1",
        activity_id="activity-1",
        status="inactive",
    )


@pytest.mark.parametrize("artifact_count", (1, 20))
def test_attention_loads_one_activity_context_regardless_of_artifact_count(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    artifact_count: int,
) -> None:
    context = _context(tmp_path, artifact_count)
    loads = 0
    assembly_calls = 0

    def load(*_args: object, **_kwargs: object) -> Any:
        nonlocal loads
        loads += 1
        return context

    def assembly(*_args: object, **_kwargs: object) -> str:
        nonlocal assembly_calls
        assembly_calls += 1
        return "not_ready"

    monkeypatch.setattr(attention, "_load_activity_context", load)
    monkeypatch.setattr(attention, "_assembly_state", assembly)
    monkeypatch.setattr(
        attention,
        "_share_attention_from_context",
        lambda _context: _inactive_share(),
    )

    result = attention.inspect_activity_attention(
        "class-1",
        "activity-1",
        workspace_root=tmp_path,
    )

    assert result.items == ()
    assert loads == 1
    assert assembly_calls == artifact_count


def test_open_activity_reuses_context_then_reloads_on_redraw(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = _context(tmp_path, 0, title="First state")
    second = _context(tmp_path, 0, title="Second state")
    pending = [first, second]
    loaded: list[Any] = []
    attention_contexts: list[Any] = []
    choices = iter(("1", "B"))

    def load(*_args: object, **_kwargs: object) -> Any:
        context = pending.pop(0)
        loaded.append(context)
        return context

    def inspect(context: Any) -> attention.ActivityAttentionSummary:
        attention_contexts.append(context)
        return attention.ActivityAttentionSummary(
            class_id="class-1",
            activity_id="activity-1",
            title=context.activity.title,
        )

    monkeypatch.setattr(menu_activity, "_load_activity_context", load)
    monkeypatch.setattr(
        menu_activity,
        "_inspect_activity_attention_from_context",
        inspect,
    )
    monkeypatch.setattr(
        menu_activity,
        "inspect_activity_attention",
        lambda *_a, **_k: (_ for _ in ()).throw(
            AssertionError("fallback attention reader should not be used")
        ),
    )
    monkeypatch.setattr(menu_activity, "launch_plan_menu", lambda *_a, **_k: None)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(choices))

    menu_activity.launch_activity_context_menu(
        ActivitySummary(
            class_id="class-1",
            activity_id="activity-1",
            title="Stale selection",
            status="active",
            scoring_orientation="evidence_only",
            session_count=1,
            group_count=0,
            snapshot_revision=1,
        )
    )

    assert loaded == [first, second]
    assert attention_contexts == [first, second]
    assert pending == []
