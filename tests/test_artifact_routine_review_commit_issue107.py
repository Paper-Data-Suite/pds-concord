from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace
from typing import cast

import pytest

from concord.models import PrivacyPolicy
from concord.workflows import artifact_routine_review_commit as commit_module
from concord.workflows.artifact_review import ArtifactReviewMutationResult
from concord.workflows.artifact_routine_review import (
    ArtifactRoutineReviewContext,
    ArtifactRoutineReviewEligibility,
)
from concord.workflows.artifact_routine_review_commit import (
    record_routine_artifact_review,
)
from concord.workflows.artifact_routine_review_profiles import (
    ArtifactRoutineReviewValues,
    routine_qualified_review_values,
    routine_ready_review_values,
)
from concord.workflows.errors import ConcordWorkflowValidationError
from concord.workflows.models import WorkflowActor


def _actor() -> WorkflowActor:
    return WorkflowActor(
        actor_id="teacher-1",
        actor_kind="authorized_adult",
        owning_system="concord",
        display_label="Teacher",
    )


def _context() -> ArtifactRoutineReviewContext:
    return ArtifactRoutineReviewContext(
        class_id="class-1",
        activity_id="activity-1",
        artifact=SimpleNamespace(artifact_instance_id="artifact-1"),
        current_review=None,
        assembly_state="assembled",
        current_authors=(),
        current_subjects=(),
        applicable_moderation_records=(),
        first_review_pending=True,
        eligibility=ArtifactRoutineReviewEligibility(
            quick_review_eligible=True,
            exception_reasons=(),
        ),
        snapshot_revision=17,
        snapshot_sha256="abc123",
    )


def _mutation_result() -> ArtifactReviewMutationResult:
    # The service under test only passes through the canonical mutation result.
    # Keep this unit-test sentinel independent of WorkflowCommitResult's full
    # storage-facing shape.
    return cast(
        ArtifactReviewMutationResult,
        SimpleNamespace(artifact_review_id="artifact-review-generated"),
    )


@pytest.mark.parametrize(
    ("values", "expected_readiness", "expected_outcome"),
    (
        (routine_ready_review_values(), "ready", "ready"),
        (
            routine_qualified_review_values("Minor scan shadow."),
            "ready_with_qualification",
            "ready_with_qualification",
        ),
    ),
)
def test_record_routine_review_maps_complete_profile_and_exact_snapshot(
    monkeypatch: pytest.MonkeyPatch,
    values: ArtifactRoutineReviewValues,
    expected_readiness: str,
    expected_outcome: str,
) -> None:
    captured: dict[str, object] = {}
    result = _mutation_result()

    monkeypatch.setattr(
        commit_module,
        "_new_artifact_review_id",
        lambda: "artifact-review-generated",
    )

    def fake_add(request: object, **kwargs: object) -> ArtifactReviewMutationResult:
        captured["request"] = request
        captured["kwargs"] = kwargs
        return result

    monkeypatch.setattr(commit_module, "add_artifact_review", fake_add)

    actual = record_routine_artifact_review(
        _context(),
        values,
        actor=_actor(),
        workspace_root="workspace",
    )

    assert actual is result
    request = captured["request"]
    assert request.class_id == "class-1"
    assert request.activity_id == "activity-1"
    assert request.artifact_instance_id == "artifact-1"
    assert request.artifact_review_id == "artifact-review-generated"
    assert request.expected_snapshot_revision == 17
    assert request.readability_judgment == "readable"
    assert request.page_completeness_judgment == "complete"
    assert request.filing_judgment == "correct"
    assert request.author_judgment == "confirmed"
    assert request.subject_judgment == "confirmed"
    assert request.privacy_judgment == "teacher_restricted"
    assert request.relevance_judgment == "relevant"
    assert request.moderation_requirement == "not_required"
    assert request.scoring_readiness == expected_readiness
    assert request.review_outcome == expected_outcome
    assert request.notes == values.notes
    assert request.privacy_policy == values.privacy_policy
    assert request.actor == _actor()
    assert captured["kwargs"]["workspace_root"] == "workspace"


def test_routine_review_generates_id_internally(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_add(request: object, **kwargs: object) -> ArtifactReviewMutationResult:
        captured["request"] = request
        return _mutation_result()

    monkeypatch.setattr(commit_module, "add_artifact_review", fake_add)

    record_routine_artifact_review(
        _context(),
        routine_ready_review_values(),
        actor=_actor(),
    )

    generated = captured["request"].artifact_review_id
    assert generated.startswith("artifact-review-")
    assert len(generated) > len("artifact-review-")


def test_ineligible_projection_fails_before_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = replace(
        _context(),
        eligibility=ArtifactRoutineReviewEligibility(
            quick_review_eligible=False,
            exception_reasons=("Author attribution requires review.",),
        ),
    )
    called = False

    def fake_add(request: object, **kwargs: object) -> ArtifactReviewMutationResult:
        nonlocal called
        called = True
        return _mutation_result()

    monkeypatch.setattr(commit_module, "add_artifact_review", fake_add)

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="not eligible.*Author attribution requires review",
    ):
        record_routine_artifact_review(
            context,
            routine_ready_review_values(),
            actor=_actor(),
        )

    assert not called


def test_existing_review_cannot_use_routine_write_even_if_context_is_malformed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = replace(
        _context(),
        current_review=SimpleNamespace(artifact_review_id="review-existing"),
        first_review_pending=False,
    )
    monkeypatch.setattr(
        commit_module,
        "add_artifact_review",
        lambda *args, **kwargs: pytest.fail("write must not be attempted"),
    )

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="first Review|not eligible",
    ):
        record_routine_artifact_review(
            context,
            routine_ready_review_values(),
            actor=_actor(),
        )


@pytest.mark.parametrize(
    "changed_field",
    (
        "readability_judgment",
        "page_completeness_judgment",
        "filing_judgment",
        "author_judgment",
        "subject_judgment",
        "relevance_judgment",
        "moderation_requirement",
    ),
)
def test_routine_write_rejects_detailed_review_variants(
    monkeypatch: pytest.MonkeyPatch,
    changed_field: str,
) -> None:
    values = routine_ready_review_values()
    replacements = {
        "readability_judgment": "partially_readable",
        "page_completeness_judgment": "partially_complete",
        "filing_judgment": "unresolved",
        "author_judgment": "qualified",
        "subject_judgment": "qualified",
        "relevance_judgment": "partially_relevant",
        "moderation_requirement": "completed",
    }
    detailed = replace(values, **{changed_field: replacements[changed_field]})
    monkeypatch.setattr(
        commit_module,
        "add_artifact_review",
        lambda *args, **kwargs: pytest.fail("write must not be attempted"),
    )

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="explicit ready or ready-with-qualification profile",
    ):
        record_routine_artifact_review(
            _context(),
            detailed,
            actor=_actor(),
        )


def test_routine_write_rejects_nonroutine_ready_pair(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    values = ArtifactRoutineReviewValues(
        readability_judgment="readable",
        page_completeness_judgment="complete",
        filing_judgment="correct",
        author_judgment="confirmed",
        subject_judgment="confirmed",
        privacy_judgment="teacher_restricted",
        relevance_judgment="relevant",
        moderation_requirement="not_required",
        scoring_readiness="not_ready",
        review_outcome="awaiting_additional_evidence",
        notes=None,
        privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
    )
    monkeypatch.setattr(
        commit_module,
        "add_artifact_review",
        lambda *args, **kwargs: pytest.fail("write must not be attempted"),
    )

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="explicit ready or ready-with-qualification profile",
    ):
        record_routine_artifact_review(
            _context(),
            values,
            actor=_actor(),
        )


def test_underlying_stale_snapshot_failure_is_not_normalized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stale = RuntimeError("stale snapshot")

    def fail_add(request: object, **kwargs: object) -> ArtifactReviewMutationResult:
        assert request.expected_snapshot_revision == 17
        raise stale

    monkeypatch.setattr(commit_module, "add_artifact_review", fail_add)

    with pytest.raises(RuntimeError, match="stale snapshot"):
        record_routine_artifact_review(
            _context(),
            routine_ready_review_values(),
            actor=_actor(),
        )
