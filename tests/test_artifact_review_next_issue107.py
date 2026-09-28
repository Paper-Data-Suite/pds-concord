from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from concord.workflows import artifact_review_next as review_next


def _context(*artifact_ids: str) -> Any:
    return SimpleNamespace(
        root=Path("workspace"),
        work=SimpleNamespace(class_id="class-1", work_id="activity-1"),
        snapshot_revision=41,
        snapshot_sha256="sha-41",
        graph=SimpleNamespace(
            artifact_instances=tuple(
                SimpleNamespace(
                    artifact_instance_id=artifact_id,
                    activity_id="activity-1",
                )
                for artifact_id in artifact_ids
            ),
            artifact_authors=(),
            artifact_subjects=(),
            artifact_reviews=(),
        ),
    )


def test_review_next_uses_deterministic_artifact_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _context("artifact-c", "artifact-a", "artifact-b")
    monkeypatch.setattr(
        review_next, "_build_attention_index", lambda supplied: object()
    )
    monkeypatch.setattr(
        review_next,
        "_collection_state_from_context",
        lambda supplied, index, artifact_id: SimpleNamespace(
            artifact_instance_id=artifact_id,
        ),
    )
    monkeypatch.setattr(
        review_next,
        "_review_state_from_context",
        lambda supplied, index, artifact_id, collection: SimpleNamespace(
            first_review_pending=True,
        ),
    )

    result = review_next._next_artifact_review_from_context(context)

    assert result is not None
    assert result.artifact.artifact_instance_id == "artifact-a"
    assert result.snapshot_revision == 41
    assert result.snapshot_sha256 == "sha-41"


def test_review_next_skips_only_items_not_in_concord_review_first(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _context("artifact-a", "artifact-b", "artifact-c")
    monkeypatch.setattr(
        review_next, "_build_attention_index", lambda supplied: object()
    )
    monkeypatch.setattr(
        review_next,
        "_collection_state_from_context",
        lambda supplied, index, artifact_id: SimpleNamespace(
            artifact_instance_id=artifact_id,
        ),
    )

    pending = {
        "artifact-a": False,
        "artifact-b": True,
        "artifact-c": True,
    }
    monkeypatch.setattr(
        review_next,
        "_review_state_from_context",
        lambda supplied, index, artifact_id, collection: SimpleNamespace(
            first_review_pending=pending[artifact_id],
        ),
    )

    result = review_next._next_artifact_review_from_context(context)

    assert result is not None
    assert result.artifact.artifact_instance_id == "artifact-b"


def test_review_next_does_not_consult_quick_review_eligibility(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _context("artifact-detailed", "artifact-quick")
    monkeypatch.setattr(
        review_next, "_build_attention_index", lambda supplied: object()
    )
    monkeypatch.setattr(
        review_next,
        "_collection_state_from_context",
        lambda supplied, index, artifact_id: SimpleNamespace(
            artifact_instance_id=artifact_id,
        ),
    )
    monkeypatch.setattr(
        review_next,
        "_review_state_from_context",
        lambda supplied, index, artifact_id, collection: SimpleNamespace(
            first_review_pending=True,
        ),
    )

    result = review_next._next_artifact_review_from_context(context)

    assert result is not None
    assert result.artifact.artifact_instance_id == "artifact-detailed"


def test_review_next_returns_none_when_no_first_review_is_pending(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _context("artifact-a", "artifact-b")
    monkeypatch.setattr(
        review_next, "_build_attention_index", lambda supplied: object()
    )
    monkeypatch.setattr(
        review_next,
        "_collection_state_from_context",
        lambda supplied, index, artifact_id: object(),
    )
    monkeypatch.setattr(
        review_next,
        "_review_state_from_context",
        lambda supplied, index, artifact_id, collection: SimpleNamespace(
            first_review_pending=False,
        ),
    )

    assert review_next._next_artifact_review_from_context(context) is None


def test_public_review_next_loads_one_current_activity_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _context("artifact-a")
    calls: list[tuple[str, object]] = []

    monkeypatch.setattr(
        review_next,
        "resolve_read_workspace_root",
        lambda workspace_root: Path("workspace"),
    )
    monkeypatch.setattr(
        review_next,
        "require_core_class",
        lambda root, class_id: None,
    )

    def fake_load(root: Path, work: object) -> Any:
        calls.append(("load", work))
        return context

    monkeypatch.setattr(review_next, "load_activity_read_context", fake_load)
    monkeypatch.setattr(
        review_next,
        "_next_artifact_review_from_context",
        lambda supplied: SimpleNamespace(
            artifact=SimpleNamespace(artifact_instance_id="artifact-a")
        ),
    )

    result = review_next.inspect_next_artifact_review(
        "class-1",
        "activity-1",
        workspace_root="workspace",
    )

    assert result is not None
    assert result.artifact.artifact_instance_id == "artifact-a"
    assert len(calls) == 1


def test_public_review_next_returns_none_without_workspace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        review_next,
        "resolve_read_workspace_root",
        lambda workspace_root: None,
    )
    monkeypatch.setattr(
        review_next,
        "load_activity_read_context",
        lambda *args, **kwargs: pytest.fail("must not load"),
    )

    assert (
        review_next.inspect_next_artifact_review(
            "class-1",
            "activity-1",
            workspace_root="missing",
        )
        is None
    )
