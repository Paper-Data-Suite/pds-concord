from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import concord.workflows.artifact_routine_scoring_next as scoring_next
from concord.workflows.errors import ConcordWorkflowConflictError


def _artifact(artifact_id: str) -> SimpleNamespace:
    return SimpleNamespace(artifact_instance_id=artifact_id)


def _context(
    *,
    artifact_ids: tuple[str, ...] = ("artifact-c", "artifact-a", "artifact-b"),
    ready_ids: tuple[str, ...] = ("artifact-a", "artifact-b", "artifact-c"),
    revision: int = 8,
) -> SimpleNamespace:
    artifacts = tuple(_artifact(item) for item in artifact_ids)
    return SimpleNamespace(
        root=Path("workspace"),
        work=SimpleNamespace(class_id="class-1", work_id="activity-1"),
        snapshot_revision=revision,
        snapshot_sha256=f"sha-{revision}",
        graph=SimpleNamespace(
            artifact_instances=artifacts,
            score_records=(
                SimpleNamespace(score_record_id="score-existing"),
            ),
        ),
        ready_ids=frozenset(ready_ids),
    )


def _patch_attention(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        scoring_next,
        "_build_attention_index",
        lambda _context: object(),
    )

    def score_state(
        context: Any,
        _index: object,
        artifact_instance_id: str,
    ) -> SimpleNamespace:
        return SimpleNamespace(
            scoring_ready=artifact_instance_id in context.ready_ids,
        )

    monkeypatch.setattr(
        scoring_next,
        "_score_state_from_context",
        score_state,
    )


def test_first_score_ready_artifact_uses_deterministic_identity_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_attention(monkeypatch)

    projected = scoring_next._next_score_ready_artifact_from_context(
        _context(),  # type: ignore[arg-type]
    )

    assert projected is not None
    assert projected.artifact.artifact_instance_id == "artifact-a"
    assert projected.snapshot_revision == 8
    assert projected.snapshot_sha256 == "sha-8"


def test_next_after_current_moves_forward_in_current_ready_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_attention(monkeypatch)

    projected = scoring_next._next_score_ready_artifact_from_context(
        _context(),  # type: ignore[arg-type]
        after_artifact_instance_id="artifact-a",
    )

    assert projected is not None
    assert projected.artifact.artifact_instance_id == "artifact-b"


def test_next_after_last_wraps_to_first_other_ready_artifact(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_attention(monkeypatch)

    projected = scoring_next._next_score_ready_artifact_from_context(
        _context(),  # type: ignore[arg-type]
        after_artifact_instance_id="artifact-c",
    )

    assert projected is not None
    assert projected.artifact.artifact_instance_id == "artifact-a"


def test_current_artifact_is_never_returned_as_its_own_next_item(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_attention(monkeypatch)

    projected = scoring_next._next_score_ready_artifact_from_context(
        _context(ready_ids=("artifact-b",)),  # type: ignore[arg-type]
        after_artifact_instance_id="artifact-b",
    )

    assert projected is None


def test_no_current_score_ready_artifact_returns_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_attention(monkeypatch)

    projected = scoring_next._next_score_ready_artifact_from_context(
        _context(ready_ids=()),  # type: ignore[arg-type]
    )

    assert projected is None


def test_existing_scores_never_drive_score_ready_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_attention(monkeypatch)
    context = _context(ready_ids=("artifact-a", "artifact-c"))
    first = scoring_next._next_score_ready_artifact_from_context(
        context,  # type: ignore[arg-type]
        after_artifact_instance_id="artifact-a",
    )
    context.graph.score_records = (
        SimpleNamespace(score_record_id="score-1"),
        SimpleNamespace(score_record_id="score-2"),
        SimpleNamespace(score_record_id="score-3"),
    )
    second = scoring_next._next_score_ready_artifact_from_context(
        context,  # type: ignore[arg-type]
        after_artifact_instance_id="artifact-a",
    )

    assert first is not None and second is not None
    assert first.artifact.artifact_instance_id == "artifact-c"
    assert second.artifact.artifact_instance_id == "artifact-c"


def test_missing_current_anchor_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_attention(monkeypatch)

    with pytest.raises(
        ConcordWorkflowConflictError,
        match="no longer available",
    ):
        scoring_next._next_score_ready_artifact_from_context(
            _context(),  # type: ignore[arg-type]
            after_artifact_instance_id="artifact-missing",
        )


def test_public_selector_reloads_one_exact_current_activity_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_attention(monkeypatch)
    context = _context(revision=12)
    calls = {"load": 0}

    monkeypatch.setattr(
        scoring_next,
        "resolve_read_workspace_root",
        lambda _root: tmp_path,
    )
    monkeypatch.setattr(
        scoring_next,
        "require_core_class",
        lambda *_args, **_kwargs: None,
    )

    def load(*_args: object, **_kwargs: object) -> Any:
        calls["load"] += 1
        return context

    monkeypatch.setattr(
        scoring_next,
        "load_activity_read_context",
        load,
    )

    projected = scoring_next.inspect_next_score_ready_artifact(
        "class-1",
        "activity-1",
        after_artifact_instance_id="artifact-a",
        minimum_snapshot_revision=11,
        workspace_root=tmp_path,
    )

    assert calls == {"load": 1}
    assert projected is not None
    assert projected.artifact.artifact_instance_id == "artifact-b"
    assert projected.snapshot_revision == 12


def test_public_selector_rejects_snapshot_older_than_completed_score(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_attention(monkeypatch)
    monkeypatch.setattr(
        scoring_next,
        "resolve_read_workspace_root",
        lambda _root: tmp_path,
    )
    monkeypatch.setattr(
        scoring_next,
        "require_core_class",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        scoring_next,
        "load_activity_read_context",
        lambda *_args, **_kwargs: _context(revision=4),
    )

    with pytest.raises(
        ConcordWorkflowConflictError,
        match="predates the completed Score mutation",
    ):
        scoring_next.inspect_next_score_ready_artifact(
            "class-1",
            "activity-1",
            minimum_snapshot_revision=5,
            workspace_root=tmp_path,
        )
