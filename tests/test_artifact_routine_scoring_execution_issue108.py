from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import concord.workflows.artifact_routine_scoring_execution as execution
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
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowValidationError,
)
from concord.workflows.models import WorkflowActor


class _FakeUuid:
    def __init__(self, hex_value: str) -> None:
        self.hex = hex_value


def _preview(
    *,
    existing_score_ids: tuple[str, ...] = (),
    session_id: str | None = None,
    significance: str | None = "primary",
) -> RoutineScorePreview:
    target = ScoreTargetReference(
        target_kind="core_student",
        target_id="student-1",
        owning_system="core",
    )
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
    evidence = RoutineScoreEvidencePreview(
        evidence_reference=EvidenceReference(
            evidence_kind="artifact_instance",
            owning_system="concord",
            record_id="artifact-1",
        ),
        subject_context=(subject,),
        relevance_description=ROUTINE_ARTIFACT_RELEVANCE_DESCRIPTION,
        significance=significance,
        evidence_locator=None,
        moderation_required=False,
        moderation_requirement="not_required",
        moderation_record_id=None,
    )
    return RoutineScorePreview(
        class_id="class-1",
        activity_id="activity-1",
        artifact_instance_id="artifact-1",
        target_reference=target,
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
        evidence=evidence,
        existing_current_score_ids=existing_score_ids,
        snapshot_revision=17,
        snapshot_sha256="a" * 64,
    )


def test_execution_generates_opaque_ids_and_delegates_exact_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generated = iter(("1" * 32, "2" * 32))
    monkeypatch.setattr(
        execution,
        "uuid4",
        lambda: _FakeUuid(next(generated)),
    )
    captured: dict[str, Any] = {}
    sentinel = object()

    def add_score(request: object, **kwargs: object) -> object:
        captured["request"] = request
        captured["kwargs"] = kwargs
        return sentinel

    monkeypatch.setattr(execution, "add_score", add_score)
    actor = WorkflowActor(actor_id="teacher-1")
    workspace = Path("workspace")
    library = SimpleNamespace(name="standards")
    clock = SimpleNamespace(name="clock")

    result = execution.record_prepared_routine_score(
        _preview(session_id="session-1"),
        actor=actor,
        workspace_root=workspace,
        standards_library=library,  # type: ignore[arg-type]
        clock=clock,  # type: ignore[arg-type]
    )

    assert result is sentinel
    request = captured["request"]
    assert request.score_record_id == f"score-{'1' * 32}"
    assert request.class_id == "class-1"
    assert request.activity_id == "activity-1"
    assert request.target_reference.target_id == "student-1"
    assert request.criterion_id == "criterion-1"
    assert request.scoring_scale_id == "scale-1"
    assert request.session_id == "session-1"
    assert request.disposition == "scored"
    assert request.basis == "linked_evidence"
    assert request.value == 3
    assert request.rationale is None
    assert request.status_reason is None
    assert request.privacy_policy == ROUTINE_SCORE_PRIVACY
    assert request.expected_snapshot_revision == 17
    assert request.actor == actor

    assert len(request.evidence_links) == 1
    link = request.evidence_links[0]
    assert link.score_evidence_link_id == f"score-link-{'2' * 32}"
    assert link.evidence_reference.evidence_kind == "artifact_instance"
    assert link.evidence_reference.owning_system == "concord"
    assert link.evidence_reference.record_id == "artifact-1"
    assert link.evidence_locator is None
    assert tuple(item.subject_id for item in link.subject_context) == ("student-1",)
    assert link.relevance_description == ROUTINE_ARTIFACT_RELEVANCE_DESCRIPTION
    assert link.significance == "primary"
    assert link.moderation_record_id is None

    assert captured["kwargs"] == {
        "workspace_root": workspace,
        "standards_library": library,
        "clock": clock,
    }


def test_existing_current_same_target_criterion_routes_out_before_id_generation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        execution,
        "uuid4",
        lambda: pytest.fail("IDs must not be generated for a conflicting preview"),
    )
    monkeypatch.setattr(
        execution,
        "add_score",
        lambda *_a, **_k: pytest.fail("canonical mutation must not be called"),
    )

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="current Score already exists",
    ):
        execution.record_prepared_routine_score(
            _preview(existing_score_ids=("score-current",)),
            actor=WorkflowActor(actor_id="teacher-1"),
        )


def test_canonical_stale_snapshot_conflict_propagates_without_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"count": 0, "revision": None}
    conflict = ConcordWorkflowConflictError("synthetic stale snapshot")

    def stale(request: object, **_kwargs: object) -> object:
        calls["count"] += 1
        calls["revision"] = request.expected_snapshot_revision
        raise conflict

    monkeypatch.setattr(execution, "add_score", stale)

    with pytest.raises(ConcordWorkflowConflictError) as caught:
        execution.record_prepared_routine_score(
            _preview(),
            actor=WorkflowActor(actor_id="teacher-1"),
        )

    assert caught.value is conflict
    assert calls == {"count": 1, "revision": 17}


@pytest.mark.parametrize(
    ("mutator", "message"),
    (
        (
            lambda preview: replace(preview, basis="professional_judgment"),
            "linked-evidence basis",
        ),
        (
            lambda preview: replace(preview, value=True),
            "selected Scale level",
        ),
        (
            lambda preview: replace(
                preview,
                evidence=replace(
                    preview.evidence,
                    evidence_reference=EvidenceReference(
                        evidence_kind="artifact_instance",
                        owning_system="concord",
                        record_id="artifact-other",
                    ),
                ),
            ),
            "exact selected Concord Artifact",
        ),
        (
            lambda preview: replace(
                preview,
                evidence=replace(
                    preview.evidence,
                    moderation_required=True,
                    moderation_requirement="required",
                ),
            ),
            "cannot bypass required Moderation",
        ),
    ),
)
def test_execution_fails_closed_for_nonroutine_or_tampered_preview(
    monkeypatch: pytest.MonkeyPatch,
    mutator: Any,
    message: str,
) -> None:
    monkeypatch.setattr(
        execution,
        "add_score",
        lambda *_a, **_k: pytest.fail("invalid preview must not mutate"),
    )

    with pytest.raises(ConcordWorkflowValidationError, match=message):
        execution.record_prepared_routine_score(
            mutator(_preview()),
            actor=WorkflowActor(actor_id="teacher-1"),
        )


def test_ids_are_not_part_of_prepared_teacher_preview() -> None:
    preview = _preview()

    assert not hasattr(preview, "score_record_id")
    assert not hasattr(preview.evidence, "score_evidence_link_id")
