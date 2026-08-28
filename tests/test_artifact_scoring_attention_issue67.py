from __future__ import annotations

from types import SimpleNamespace

import pytest

import concord.workflows.artifact_scoring_attention as scoring_attention


def _activity(orientation: str) -> object:
    return SimpleNamespace(
        summary=SimpleNamespace(scoring_orientation=orientation)
    )


def _review(
    *,
    outcome: str = "ready",
    readiness: str = "ready",
    moderation: str = "not_required",
) -> object:
    return SimpleNamespace(
        review_outcome=outcome,
        scoring_readiness=readiness,
        moderation_requirement=moderation,
        notes="private teacher note",
        reviewer_display_label="Private Teacher",
    )


def test_evidence_only_activity_never_gets_routine_score_attention(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        scoring_attention,
        "show_activity",
        lambda *_a, **_k: _activity("evidence_only"),
    )
    seen: list[str] = []

    def _review_reader(*_args: object, **_kwargs: object) -> object:
        seen.append("review")
        return _review()

    monkeypatch.setattr(
        scoring_attention,
        "current_artifact_review",
        _review_reader,
    )
    result = scoring_attention.inspect_artifact_scoring_attention_state(
        "class-1", "activity-1", "artifact-1"
    )
    assert not result.scoring_ready
    assert seen == []


@pytest.mark.parametrize(
    ("orientation", "outcome", "readiness", "moderation"),
    (
        ("local_criteria_only", "ready", "ready", "not_required"),
        (
            "standards_based",
            "ready_with_qualification",
            "ready_with_qualification",
            "not_required",
        ),
        ("mixed", "ready", "ready", "completed"),
    ),
)
def test_explicit_current_review_can_establish_mechanical_scoring_readiness(
    monkeypatch: pytest.MonkeyPatch,
    orientation: str,
    outcome: str,
    readiness: str,
    moderation: str,
) -> None:
    monkeypatch.setattr(
        scoring_attention,
        "show_activity",
        lambda *_a, **_k: _activity(orientation),
    )
    monkeypatch.setattr(
        scoring_attention,
        "current_artifact_review",
        lambda *_a, **_k: _review(
            outcome=outcome,
            readiness=readiness,
            moderation=moderation,
        ),
    )
    result = scoring_attention.inspect_artifact_scoring_attention_state(
        "class-1", "activity-1", "artifact-private-id"
    )
    assert result.scoring_ready
    rendered = repr(result)
    assert "private teacher note" not in rendered
    assert "Private Teacher" not in rendered


@pytest.mark.parametrize(
    ("review",),
    (
        (None,),
        (_review(outcome="incomplete", readiness="not_ready"),),
        (
            _review(
                outcome="moderation_required",
                readiness="not_ready",
                moderation="required",
            ),
        ),
        (
            _review(
                outcome="not_suitable_for_scoring",
                readiness="not_ready",
            ),
        ),
    ),
)
def test_absence_or_nonready_review_does_not_infer_missing_score(
    monkeypatch: pytest.MonkeyPatch,
    review: object | None,
) -> None:
    monkeypatch.setattr(
        scoring_attention,
        "show_activity",
        lambda *_a, **_k: _activity("mixed"),
    )
    monkeypatch.setattr(
        scoring_attention,
        "current_artifact_review",
        lambda *_a, **_k: review,
    )
    result = scoring_attention.inspect_artifact_scoring_attention_state(
        "class-1", "activity-1", "artifact-1"
    )
    assert not result.scoring_ready
