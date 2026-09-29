from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import concord.workflows.artifact_routine_scoring_continuation as continuation
from concord.models import (
    EvidenceReference,
    ScoreTargetReference,
    ScoringScaleLevel,
    SubjectReference,
)
from concord.workflows.artifact_routine_scoring_preparation import (
    ROUTINE_ARTIFACT_RELEVANCE_DESCRIPTION,
    ROUTINE_SCORE_BASIS,
    ROUTINE_SCORE_DISPOSITION,
    ROUTINE_SCORE_PRIVACY,
    RoutineScoreEvidencePreview,
    RoutineScorePreview,
)
from concord.workflows.artifact_routine_scoring_selection import (
    RoutineScoreTargetCandidate,
    RoutineScoreTargetOptions,
)
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowValidationError,
)


def _target() -> ScoreTargetReference:
    return ScoreTargetReference(
        target_kind="core_student",
        target_id="student-1",
        owning_system="core",
    )


def _preview(*, session_id: str | None = "session-1") -> RoutineScorePreview:
    subject = SubjectReference(
        subject_kind="core_student",
        subject_id="student-1",
        owning_system="core",
    )
    level = ScoringScaleLevel(
        value=3,
        label="Meeting",
        meaning="Meets the standard.",
    )
    return RoutineScorePreview(
        class_id="class-1",
        activity_id="activity-1",
        artifact_instance_id="artifact-1",
        target_reference=_target(),
        criterion_id="criterion-1",
        criterion_label="Uses textual evidence",
        score_kind="standard_backed",
        standard_id="standard-1",
        scoring_scale_id="scale-1",
        scoring_scale_name="Standards 4-point rubric",
        value=3,
        selected_level=level,
        session_id=session_id,
        disposition=ROUTINE_SCORE_DISPOSITION,
        basis=ROUTINE_SCORE_BASIS,
        rationale=None,
        status_reason=None,
        privacy_policy=ROUTINE_SCORE_PRIVACY,
        evidence=RoutineScoreEvidencePreview(
            evidence_reference=EvidenceReference(
                evidence_kind="artifact_instance",
                owning_system="concord",
                record_id="artifact-1",
            ),
            subject_context=(subject,),
            relevance_description=ROUTINE_ARTIFACT_RELEVANCE_DESCRIPTION,
            significance="primary",
            evidence_locator=None,
            moderation_required=False,
            moderation_requirement="not_required",
            moderation_record_id=None,
        ),
        existing_current_score_ids=(),
        snapshot_revision=17,
        snapshot_sha256="a" * 64,
    )


def _result(*, revision: int = 18, no_op: bool = False) -> Any:
    return SimpleNamespace(
        commit=SimpleNamespace(
            snapshot_revision=revision,
            no_op=no_op,
        ),
        score_record_id="score-new",
        score_evidence_link_ids=("score-link-new",),
    )


def _context(
    *,
    revision: int = 18,
    eligible: bool = True,
    sessions: tuple[object, ...] | None = None,
) -> Any:
    if sessions is None:
        sessions = (
            SimpleNamespace(
                session_id="session-1",
                activity_id="activity-1",
            ),
        )
    return SimpleNamespace(
        activity_id="activity-1",
        snapshot_revision=revision,
        snapshot_sha256="b" * 64,
        current_sessions=sessions,
        eligibility=SimpleNamespace(
            routine_scoring_eligible=eligible,
            exception_reasons=()
            if eligible
            else ("Review is no longer score-ready.",),
        ),
        current_scores=(
            SimpleNamespace(
                score_record_id="score-new",
                criterion_id="criterion-1",
                target_reference=_target(),
            ),
        ),
    )


def _target_options(*_args: object, **_kwargs: object) -> RoutineScoreTargetOptions:
    target = _target()
    return RoutineScoreTargetOptions(
        candidates=(
            RoutineScoreTargetCandidate(
                target_reference=target,
                candidate_sources=("artifact_subject",),
                compatible_criterion_ids=("criterion-1", "criterion-2"),
            ),
        ),
        supported_target_kinds=("core_student",),
    )


def test_reload_after_score_reads_fresh_state_and_retains_valid_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fresh = _context()
    calls = {"inspect": 0}

    def inspect(*_args: object, **_kwargs: object) -> Any:
        calls["inspect"] += 1
        return fresh

    criteria = (
        SimpleNamespace(criterion_id="criterion-1"),
        SimpleNamespace(criterion_id="criterion-2"),
    )
    monkeypatch.setattr(continuation, "inspect_artifact_routine_scoring", inspect)
    monkeypatch.setattr(continuation, "routine_target_options", _target_options)
    monkeypatch.setattr(
        continuation,
        "routine_criteria_for_target",
        lambda *_a, **_k: criteria,
    )

    projected = continuation.reload_routine_scoring_after_score(
        _preview(),
        _result(),  # type: ignore[arg-type]
        workspace_root=Path("workspace"),
    )

    assert calls == {"inspect": 1}
    assert projected.context is fresh
    assert projected.completed_score_record_id == "score-new"
    assert projected.completed_criterion_id == "criterion-1"
    assert projected.retained_target_reference == _target()
    assert projected.retained_session_id == "session-1"
    assert projected.target_context_retained is True
    assert projected.session_context_retained is True
    assert tuple(item.criterion_id for item in projected.available_criteria) == (
        "criterion-1",
        "criterion-2",
    )
    assert projected.dropped_context_reasons == ()


def test_existing_score_does_not_turn_continuation_into_completion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        continuation,
        "inspect_artifact_routine_scoring",
        lambda *_a, **_k: _context(),
    )
    monkeypatch.setattr(continuation, "routine_target_options", _target_options)
    monkeypatch.setattr(
        continuation,
        "routine_criteria_for_target",
        lambda *_a, **_k: (SimpleNamespace(criterion_id="criterion-2"),),
    )

    projected = continuation.reload_routine_scoring_after_score(
        _preview(),
        _result(),  # type: ignore[arg-type]
    )

    assert projected.target_context_retained is True
    assert tuple(item.criterion_id for item in projected.available_criteria) == (
        "criterion-2",
    )


def test_reload_drops_target_and_session_that_are_no_longer_current(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fresh = _context(sessions=())
    monkeypatch.setattr(
        continuation,
        "inspect_artifact_routine_scoring",
        lambda *_a, **_k: fresh,
    )
    monkeypatch.setattr(
        continuation,
        "routine_target_options",
        lambda *_a, **_k: RoutineScoreTargetOptions(
            candidates=(),
            supported_target_kinds=("core_student",),
        ),
    )

    projected = continuation.reload_routine_scoring_after_score(
        _preview(),
        _result(),  # type: ignore[arg-type]
    )

    assert projected.retained_target_reference is None
    assert projected.retained_session_id is None
    assert projected.target_context_retained is False
    assert projected.session_context_retained is False
    assert projected.available_criteria == ()
    assert any("Score target" in item for item in projected.dropped_context_reasons)
    assert any("Session" in item for item in projected.dropped_context_reasons)


@pytest.mark.parametrize(
    "result",
    (
        _result(no_op=True),
        _result(revision=17),
    ),
)
def test_reload_requires_a_real_snapshot_advancing_score_commit(result: Any) -> None:
    expected = (
        ConcordWorkflowValidationError
        if result.commit.no_op
        else ConcordWorkflowConflictError
    )
    with pytest.raises(expected):
        continuation.reload_routine_scoring_after_score(
            _preview(),
            result,  # type: ignore[arg-type]
        )


def test_reload_rejects_state_older_than_completed_commit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        continuation,
        "inspect_artifact_routine_scoring",
        lambda *_a, **_k: _context(revision=18),
    )

    with pytest.raises(ConcordWorkflowConflictError, match="predates"):
        continuation.reload_routine_scoring_after_score(
            _preview(),
            _result(revision=19),  # type: ignore[arg-type]
        )


def test_prepare_next_reuses_only_fresh_retained_target_and_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fresh = _context()
    state = continuation.RoutineScoringContinuation(
        context=fresh,  # type: ignore[arg-type]
        completed_score_record_id="score-new",
        completed_criterion_id="criterion-1",
        retained_target_reference=_target(),
        retained_session_id="session-1",
        target_context_retained=True,
        session_context_retained=True,
        available_criteria=(
            SimpleNamespace(criterion_id="criterion-2"),
        ),  # type: ignore[arg-type]
        dropped_context_reasons=(),
    )
    subject = SubjectReference(
        subject_kind="core_student",
        subject_id="student-1",
        owning_system="core",
    )
    captured: dict[str, object] = {}
    sentinel = object()

    def prepare(context: object, request: object) -> object:
        captured["context"] = context
        captured["request"] = request
        return sentinel

    monkeypatch.setattr(continuation, "prepare_routine_score_preview", prepare)
    request = continuation.ContinuedRoutineScorePreparationRequest(
        criterion_id="criterion-2",
        scoring_scale_id="scale-1",
        value=4,
        subject_context=(subject,),
        significance="primary",
    )

    result = continuation.prepare_next_routine_score_preview(state, request)

    assert result is sentinel
    prepared: Any = captured["request"]
    assert captured["context"] is fresh
    assert prepared.target_reference == _target()
    assert prepared.session_id == "session-1"
    assert prepared.criterion_id == "criterion-2"
    assert prepared.scoring_scale_id == "scale-1"
    assert prepared.value == 4
    assert prepared.subject_context == (subject,)
    assert prepared.relevance_description == ROUTINE_ARTIFACT_RELEVANCE_DESCRIPTION
    assert prepared.significance == "primary"
    assert not hasattr(request, "target_reference")
    assert not hasattr(request, "session_id")


def test_prepare_next_requires_a_fresh_criterion() -> None:
    state = continuation.RoutineScoringContinuation(
        context=_context(),  # type: ignore[arg-type]
        completed_score_record_id="score-new",
        completed_criterion_id="criterion-1",
        retained_target_reference=_target(),
        retained_session_id="session-1",
        target_context_retained=True,
        session_context_retained=True,
        available_criteria=(),
        dropped_context_reasons=(),
    )

    with pytest.raises(ConcordWorkflowValidationError, match="fresh Criterion"):
        continuation.prepare_next_routine_score_preview(
            state,
            continuation.ContinuedRoutineScorePreparationRequest(
                criterion_id="criterion-1",
                scoring_scale_id="scale-1",
                value=4,
            ),
        )


def test_prepare_next_fails_closed_when_retained_context_changed() -> None:
    target_missing = continuation.RoutineScoringContinuation(
        context=_context(),  # type: ignore[arg-type]
        completed_score_record_id="score-new",
        completed_criterion_id="criterion-1",
        retained_target_reference=None,
        retained_session_id="session-1",
        target_context_retained=False,
        session_context_retained=True,
        available_criteria=(),
        dropped_context_reasons=("target changed",),
    )
    request = continuation.ContinuedRoutineScorePreparationRequest(
        criterion_id="criterion-2",
        scoring_scale_id="scale-1",
        value=4,
    )

    with pytest.raises(ConcordWorkflowValidationError, match="choose a target again"):
        continuation.prepare_next_routine_score_preview(target_missing, request)

    session_changed = continuation.RoutineScoringContinuation(
        context=_context(),  # type: ignore[arg-type]
        completed_score_record_id="score-new",
        completed_criterion_id="criterion-1",
        retained_target_reference=_target(),
        retained_session_id=None,
        target_context_retained=True,
        session_context_retained=False,
        available_criteria=(),
        dropped_context_reasons=("session changed",),
    )
    with pytest.raises(ConcordWorkflowValidationError, match="Session context changed"):
        continuation.prepare_next_routine_score_preview(session_changed, request)
