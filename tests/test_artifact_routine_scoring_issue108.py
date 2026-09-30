from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import concord.workflows.artifact_routine_scoring as routine_scoring


def _review(
    *,
    outcome: str = "ready",
    readiness: str = "ready",
    moderation: str = "not_required",
    review_id: str = "review-1",
    supersedes: str | None = None,
) -> object:
    return SimpleNamespace(
        artifact_review_id=review_id,
        artifact_instance_id="artifact-1",
        review_outcome=outcome,
        scoring_readiness=readiness,
        moderation_requirement=moderation,
        supersedes_artifact_review_id=supersedes,
    )


def _author(*, status: str = "confirmed") -> object:
    return SimpleNamespace(
        artifact_author_id="author-1",
        artifact_instance_id="artifact-1",
        attribution_status=status,
        supersedes_artifact_author_id=None,
    )


def _subject(
    *,
    status: str = "confirmed",
    subject_id: str = "student-1",
) -> object:
    return SimpleNamespace(
        artifact_subject_id=f"subject-{subject_id}",
        artifact_instance_id="artifact-1",
        confirmation_status=status,
        supersedes_artifact_subject_id=None,
        subject_reference=SimpleNamespace(
            subject_kind="core_student",
            subject_id=subject_id,
            owning_system="core",
            contract_version=None,
        ),
    )


def _criterion_set(
    *,
    criterion_set_id: str = "set-1",
    status: str = "active",
    supersedes: str | None = None,
) -> object:
    return SimpleNamespace(
        criterion_set_id=criterion_set_id,
        status=status,
        supersedes_criterion_set_id=supersedes,
    )


def _criterion(
    *,
    criterion_id: str = "criterion-1",
    criterion_set_id: str = "set-1",
    status: str = "active",
) -> object:
    return SimpleNamespace(
        criterion_id=criterion_id,
        criterion_set_id=criterion_set_id,
        status=status,
    )


def _scale(
    *,
    scale_id: str = "scale-1",
    status: str = "active",
    supersedes: str | None = None,
) -> object:
    return SimpleNamespace(
        scoring_scale_id=scale_id,
        status=status,
        supersedes_scoring_scale_id=supersedes,
    )


def _score(
    *,
    score_id: str = "score-1",
    supersedes: str | None = None,
) -> object:
    return SimpleNamespace(
        score_record_id=score_id,
        supersedes_score_record_id=supersedes,
    )


def _context(
    *,
    orientation: str = "mixed",
    focus_standard_ids: tuple[str, ...] = ("standard-1",),
    criterion_set_ids: tuple[str, ...] = ("set-1",),
    reviews: tuple[object, ...] = (_review(),),
    authors: tuple[object, ...] = (_author(),),
    subjects: tuple[object, ...] = (_subject(),),
    criterion_sets: tuple[object, ...] = (_criterion_set(),),
    criteria: tuple[object, ...] = (_criterion(),),
    scales: tuple[object, ...] = (_scale(),),
    scores: tuple[object, ...] = (_score(),),
) -> Any:
    artifact = SimpleNamespace(
        artifact_instance_id="artifact-1",
        activity_id="activity-1",
    )
    activity = SimpleNamespace(
        activity_id="activity-1",
        scoring_orientation=orientation,
        focus_standard_ids=focus_standard_ids,
        criterion_set_ids=criterion_set_ids,
    )
    return SimpleNamespace(
        root=Path("workspace"),
        work=SimpleNamespace(
            class_id="class-1",
            work_id="activity-1",
        ),
        snapshot_revision=23,
        snapshot_sha256="b" * 64,
        activity=activity,
        graph=SimpleNamespace(
            artifact_instances=(artifact,),
            artifact_authors=authors,
            artifact_subjects=subjects,
            artifact_reviews=reviews,
            criterion_sets=criterion_sets,
            criteria=criteria,
            scoring_scales=scales,
            sessions=(SimpleNamespace(session_id="session-1"),),
            groups=(SimpleNamespace(group_id="group-1"),),
            memberships=(SimpleNamespace(membership_id="membership-1"),),
            score_records=scores,
        ),
    )


@pytest.fixture(autouse=True)
def _relationship_boundaries(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        routine_scoring,
        "_validate_author_semantics",
        lambda *_a, **_k: None,
    )
    monkeypatch.setattr(
        routine_scoring,
        "_validate_subject_semantics",
        lambda *_a, **_k: None,
    )
    monkeypatch.setattr(
        routine_scoring,
        "_ensure_author_not_duplicate",
        lambda *_a, **_k: None,
    )
    monkeypatch.setattr(
        routine_scoring,
        "_ensure_subject_not_duplicate",
        lambda *_a, **_k: None,
    )


def test_native_artifact_evidence_reference_contains_only_owned_identity() -> None:
    artifact = SimpleNamespace(artifact_instance_id="artifact-42")

    evidence = routine_scoring.native_artifact_evidence_reference(
        artifact  # type: ignore[arg-type]
    )

    assert evidence.evidence_kind == "artifact_instance"
    assert evidence.owning_system == "concord"
    assert evidence.record_id == "artifact-42"
    assert evidence.contract_version is None
    assert evidence.source_publication_reference is None
    assert evidence.immutable_source_version is None
    assert evidence.locator is None
    assert evidence.subject_context == ()
    assert evidence.moderation_requirement is None


def test_ready_projection_preserves_exact_snapshot_and_scoring_context() -> None:
    projected = routine_scoring._project_artifact_routine_scoring_from_context(
        _context(),  # type: ignore[arg-type]
        "artifact-1",
    )

    assert projected.artifact.artifact_instance_id == "artifact-1"
    assert projected.scoring_orientation == "mixed"
    assert projected.focus_standard_ids == ("standard-1",)
    assert projected.current_review is not None
    assert projected.evidence_reference.record_id == "artifact-1"
    assert len(projected.current_authors) == 1
    assert len(projected.current_subjects) == 1
    assert len(projected.subject_context_candidates) == 1
    selected_set_ids = tuple(
        item.criterion_set_id for item in projected.selected_criterion_sets
    )
    assert selected_set_ids == ("set-1",)
    assert tuple(item.criterion_id for item in projected.eligible_criteria) == (
        "criterion-1",
    )
    assert tuple(
        item.scoring_scale_id for item in projected.current_scoring_scales
    ) == ("scale-1",)
    assert len(projected.current_sessions) == 1
    assert len(projected.current_groups) == 1
    assert len(projected.current_memberships) == 1
    assert tuple(item.score_record_id for item in projected.current_scores) == (
        "score-1",
    )
    assert projected.eligibility.routine_scoring_eligible
    assert projected.eligibility.exception_reasons == ()
    assert projected.snapshot_revision == 23
    assert projected.snapshot_sha256 == "b" * 64


@pytest.mark.parametrize(
    ("reviews", "expected"),
    (
        ((), "current explicit Artifact Review"),
        (
            (_review(outcome="not_suitable_for_scoring", readiness="not_ready"),),
            "outcome does not permit routine scoring",
        ),
        (
            (
                _review(
                    outcome="moderation_required",
                    readiness="not_ready",
                    moderation="required",
                ),
            ),
            "still requires Moderation",
        ),
    ),
)
def test_review_state_conservatively_gates_routine_scoring(
    reviews: tuple[object, ...],
    expected: str,
) -> None:
    projected = routine_scoring._project_artifact_routine_scoring_from_context(
        _context(reviews=reviews),  # type: ignore[arg-type]
        "artifact-1",
    )

    assert not projected.eligibility.routine_scoring_eligible
    assert any(
        expected in reason for reason in projected.eligibility.exception_reasons
    )


def test_ready_with_qualification_remains_routine_eligible() -> None:
    projected = routine_scoring._project_artifact_routine_scoring_from_context(
        _context(
            reviews=(
                _review(
                    outcome="ready_with_qualification",
                    readiness="ready_with_qualification",
                    moderation="completed",
                ),
            )
        ),  # type: ignore[arg-type]
        "artifact-1",
    )

    assert projected.eligibility.routine_scoring_eligible


def test_evidence_only_activity_never_enters_routine_scoring() -> None:
    projected = routine_scoring._project_artifact_routine_scoring_from_context(
        _context(orientation="evidence_only"),  # type: ignore[arg-type]
        "artifact-1",
    )

    assert not projected.eligibility.routine_scoring_eligible
    assert any(
        "Evidence-only" in reason
        for reason in projected.eligibility.exception_reasons
    )


def test_only_confirmed_valid_subjects_become_typed_context_candidates() -> None:
    projected = routine_scoring._project_artifact_routine_scoring_from_context(
        _context(
            subjects=(
                _subject(status="confirmed", subject_id="student-1"),
                _subject(status="proposed", subject_id="student-2"),
            )
        ),  # type: ignore[arg-type]
        "artifact-1",
    )

    assert tuple(
        item.subject_id for item in projected.subject_context_candidates
    ) == ("student-1",)


def test_subject_context_candidates_deduplicate_by_semantic_identity() -> None:
    first = _subject(status="confirmed", subject_id="student-1")
    duplicate = _subject(status="confirmed", subject_id="student-1")
    duplicate.artifact_subject_id = "subject-student-1-duplicate"

    projected = routine_scoring._project_artifact_routine_scoring_from_context(
        _context(subjects=(first, duplicate)),  # type: ignore[arg-type]
        "artifact-1",
    )

    assert len(projected.subject_context_candidates) == 1
    assert projected.subject_context_candidates[0].subject_id == "student-1"


def test_invalid_relationship_state_fails_closed_without_normalizing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def invalid(*_args: object, **_kwargs: object) -> None:
        raise routine_scoring.ConcordWorkflowError("synthetic conflict")

    monkeypatch.setattr(routine_scoring, "_validate_subject_semantics", invalid)

    projected = routine_scoring._project_artifact_routine_scoring_from_context(
        _context(),  # type: ignore[arg-type]
        "artifact-1",
    )

    assert not projected.eligibility.routine_scoring_eligible
    assert projected.subject_context_candidates == ()
    assert any(
        "Subject state is invalid or conflicting" in reason
        for reason in projected.eligibility.exception_reasons
    )


def test_historical_contract_heads_are_not_projected_as_current() -> None:
    projected = routine_scoring._project_artifact_routine_scoring_from_context(
        _context(
            criterion_set_ids=("set-new",),
            criterion_sets=(
                _criterion_set(criterion_set_id="set-old"),
                _criterion_set(
                    criterion_set_id="set-new",
                    supersedes="set-old",
                ),
            ),
            criteria=(
                _criterion(
                    criterion_id="criterion-new",
                    criterion_set_id="set-new",
                ),
            ),
            scales=(
                _scale(scale_id="scale-old"),
                _scale(scale_id="scale-new", supersedes="scale-old"),
            ),
            scores=(
                _score(score_id="score-old"),
                _score(score_id="score-new", supersedes="score-old"),
            ),
        ),  # type: ignore[arg-type]
        "artifact-1",
    )

    assert tuple(
        item.criterion_set_id for item in projected.selected_criterion_sets
    ) == ("set-new",)
    assert tuple(
        item.scoring_scale_id for item in projected.current_scoring_scales
    ) == ("scale-new",)
    assert tuple(item.score_record_id for item in projected.current_scores) == (
        "score-new",
    )


def test_historical_selected_criterion_set_fails_closed() -> None:
    projected = routine_scoring._project_artifact_routine_scoring_from_context(
        _context(
            criterion_set_ids=("set-old",),
            criterion_sets=(
                _criterion_set(criterion_set_id="set-old"),
                _criterion_set(
                    criterion_set_id="set-new",
                    supersedes="set-old",
                ),
            ),
            criteria=(
                _criterion(
                    criterion_id="criterion-old",
                    criterion_set_id="set-old",
                ),
            ),
        ),  # type: ignore[arg-type]
        "artifact-1",
    )

    assert not projected.eligibility.routine_scoring_eligible
    assert projected.selected_criterion_sets == ()
    assert projected.eligible_criteria == ()
    assert any(
        "missing or historical" in reason
        for reason in projected.eligibility.exception_reasons
    )


def test_public_inspection_loads_one_activity_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _context()
    calls = {"load": 0}

    monkeypatch.setattr(
        routine_scoring,
        "resolve_read_workspace_root",
        lambda _root: tmp_path,
    )
    monkeypatch.setattr(
        routine_scoring,
        "require_core_class",
        lambda *_a, **_k: None,
    )

    def load(*_args: object, **_kwargs: object) -> Any:
        calls["load"] += 1
        return context

    monkeypatch.setattr(
        routine_scoring,
        "load_activity_read_context",
        load,
    )

    projected = routine_scoring.inspect_artifact_routine_scoring(
        "class-1",
        "activity-1",
        "artifact-1",
        workspace_root=tmp_path,
    )

    assert calls == {"load": 1}
    assert projected.snapshot_revision == 23
