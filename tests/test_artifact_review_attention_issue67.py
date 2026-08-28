from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import concord.workflows.artifact_review_attention as review_attention
from concord.workflows.artifact_collection import ArtifactCollectionState


def _collection(assembly: str) -> ArtifactCollectionState:
    return ArtifactCollectionState(
        class_id="class-1",
        activity_id="activity-1",
        artifact_instance_id="artifact-1",
        assembly_state=assembly,  # type: ignore[arg-type]
        author_confirmation_pending=False,
        subject_confirmation_pending=False,
    )


def _review(
    *,
    outcome: str = "ready",
    moderation: str = "not_required",
) -> SimpleNamespace:
    return SimpleNamespace(
        review_outcome=outcome,
        moderation_requirement=moderation,
    )


def test_first_review_requires_completed_exact_assembly(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        review_attention,
        "current_artifact_review",
        lambda *_a, **_k: None,
    )
    monkeypatch.setattr(
        review_attention,
        "inspect_artifact_collection_state",
        lambda *_a, **_k: _collection("not_ready"),
    )
    state = review_attention.inspect_artifact_review_attention_state(
        "class-1", "activity-1", "artifact-1", workspace_root=tmp_path
    )
    assert not state.first_review_pending

    monkeypatch.setattr(
        review_attention,
        "inspect_artifact_collection_state",
        lambda *_a, **_k: _collection("assembled"),
    )
    state = review_attention.inspect_artifact_review_attention_state(
        "class-1", "activity-1", "artifact-1", workspace_root=tmp_path
    )
    assert state.first_review_pending
    assert not state.review_attention_pending


def test_current_ready_or_terminal_not_suitable_review_is_not_false_attention(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for outcome in ("ready", "ready_with_qualification", "not_suitable_for_scoring"):
        monkeypatch.setattr(
            review_attention,
            "current_artifact_review",
            lambda *_a, _outcome=outcome, **_k: _review(outcome=_outcome),
        )
        state = review_attention.inspect_artifact_review_attention_state(
            "class-1", "activity-1", "artifact-1", workspace_root=tmp_path
        )
        assert not state.review_attention_pending
        assert not state.moderation_pending


def test_explicit_blocking_review_outcomes_create_review_attention(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    outcomes = (
        "incomplete",
        "unreadable",
        "misrouted",
        "duplicate",
        "awaiting_correction",
        "awaiting_additional_evidence",
    )
    for outcome in outcomes:
        monkeypatch.setattr(
            review_attention,
            "current_artifact_review",
            lambda *_a, _outcome=outcome, **_k: _review(outcome=_outcome),
        )
        state = review_attention.inspect_artifact_review_attention_state(
            "class-1", "activity-1", "artifact-1", workspace_root=tmp_path
        )
        assert state.review_attention_pending


def test_required_moderation_without_applicable_current_decision_is_attention(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        review_attention,
        "current_artifact_review",
        lambda *_a, **_k: _review(
            outcome="moderation_required",
            moderation="required",
        ),
    )
    monkeypatch.setattr(
        review_attention,
        "list_artifact_subjects",
        lambda *_a, **_k: (
            SimpleNamespace(subject_reference=SimpleNamespace(subject_id="private")),
        ),
    )
    seen: list[tuple[object, ...]] = []

    def assess(*args: object, **kwargs: object) -> SimpleNamespace:
        seen.append((args, kwargs))
        return SimpleNamespace(applicable_moderation_records=())

    monkeypatch.setattr(review_attention, "assess_moderation_requirement", assess)
    state = review_attention.inspect_artifact_review_attention_state(
        "class-1", "activity-1", "artifact-1", workspace_root=tmp_path
    )
    assert state.moderation_pending
    assert not state.post_moderation_review_pending
    assert len(seen) == 1


def test_exact_applicable_current_moderation_moves_attention_to_review_update(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        review_attention,
        "current_artifact_review",
        lambda *_a, **_k: _review(
            outcome="moderation_required",
            moderation="required",
        ),
    )
    monkeypatch.setattr(
        review_attention,
        "list_artifact_subjects",
        lambda *_a, **_k: (),
    )
    monkeypatch.setattr(
        review_attention,
        "assess_moderation_requirement",
        lambda *_a, **_k: SimpleNamespace(
            applicable_moderation_records=(
                SimpleNamespace(
                    moderation_record_id="private-id",
                    status="rejected",
                    rationale="private rationale",
                ),
            )
        ),
    )
    state = review_attention.inspect_artifact_review_attention_state(
        "class-1", "activity-1", "artifact-1", workspace_root=tmp_path
    )
    assert not state.moderation_pending
    assert state.post_moderation_review_pending
    rendered = repr(state)
    assert "private-id" not in rendered
    assert "private rationale" not in rendered
