from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import concord.workflows.artifact_routine_review as routine_review


def _context(
    *,
    authors: tuple[object, ...] = (),
    subjects: tuple[object, ...] = (),
    reviews: tuple[object, ...] = (),
) -> Any:
    artifact = SimpleNamespace(
        artifact_instance_id="artifact-1",
        activity_id="activity-1",
    )
    return SimpleNamespace(
        root=Path("workspace"),
        work=SimpleNamespace(
            class_id="class-1",
            work_id="activity-1",
        ),
        snapshot_revision=17,
        snapshot_sha256="a" * 64,
        graph=SimpleNamespace(
            artifact_instances=(artifact,),
            artifact_authors=authors,
            artifact_subjects=subjects,
            artifact_reviews=reviews,
            moderation_records=(),
        ),
    )


def _author(status: str = "confirmed") -> object:
    return SimpleNamespace(
        artifact_author_id="author-1",
        artifact_instance_id="artifact-1",
        attribution_status=status,
        supersedes_artifact_author_id=None,
    )


def _subject(status: str = "confirmed") -> object:
    return SimpleNamespace(
        artifact_subject_id="subject-1",
        artifact_instance_id="artifact-1",
        confirmation_status=status,
        supersedes_artifact_subject_id=None,
        subject_reference=SimpleNamespace(subject_id="student-1"),
    )


@pytest.fixture(autouse=True)
def _projection_boundaries(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        routine_review,
        "_assembly_state",
        lambda *_a, **_k: "assembled",
    )
    monkeypatch.setattr(
        routine_review,
        "_validate_author_semantics",
        lambda *_a, **_k: None,
    )
    monkeypatch.setattr(
        routine_review,
        "_validate_subject_semantics",
        lambda *_a, **_k: None,
    )
    monkeypatch.setattr(
        routine_review,
        "_ensure_author_not_duplicate",
        lambda *_a, **_k: None,
    )
    monkeypatch.setattr(
        routine_review,
        "_ensure_subject_not_duplicate",
        lambda *_a, **_k: None,
    )
    monkeypatch.setattr(
        routine_review,
        "_applicable_records",
        lambda *_a, **_k: (),
    )


def test_ready_projection_preserves_exact_snapshot_and_current_state() -> None:
    context = _context(
        authors=(_author(),),
        subjects=(_subject(),),
    )

    projected = routine_review._project_artifact_routine_review_from_context(
        context,  # type: ignore[arg-type]
        "artifact-1",
    )

    assert projected.artifact.artifact_instance_id == "artifact-1"
    assert projected.current_review is None
    assert projected.assembly_state == "assembled"
    assert len(projected.current_authors) == 1
    assert len(projected.current_subjects) == 1
    assert projected.first_review_pending
    assert projected.eligibility.quick_review_eligible
    assert projected.eligibility.exception_reasons == ()
    assert projected.snapshot_revision == 17
    assert projected.snapshot_sha256 == "a" * 64


@pytest.mark.parametrize(
    ("authors", "subjects", "expected"),
    (
        (
            (_author("proposed"),),
            (_subject(),),
            "Author attribution is not confirmed",
        ),
        (
            (_author("disputed"),),
            (_subject(),),
            "Author attribution is not confirmed",
        ),
        (
            (_author("unknown"),),
            (_subject(),),
            "Author attribution is not confirmed",
        ),
        (
            (_author(),),
            (_subject("proposed"),),
            "Subject attribution is not confirmed",
        ),
        (
            (_author(),),
            (_subject("disputed"),),
            "Subject attribution is not confirmed",
        ),
        (
            (_author(),),
            (_subject("unresolved"),),
            "Subject attribution is not confirmed",
        ),
        (
            (),
            (_subject(),),
            "no current Author relationship",
        ),
        (
            (_author(),),
            (),
            "no current Subject relationship",
        ),
    ),
)
def test_attribution_exceptions_conservatively_gate_quick_review(
    authors: tuple[object, ...],
    subjects: tuple[object, ...],
    expected: str,
) -> None:
    projected = routine_review._project_artifact_routine_review_from_context(
        _context(authors=authors, subjects=subjects),  # type: ignore[arg-type]
        "artifact-1",
    )

    assert projected.first_review_pending
    assert not projected.eligibility.quick_review_eligible
    assert any(
        expected in reason
        for reason in projected.eligibility.exception_reasons
    )


def test_semantic_attribution_conflict_gates_without_normalizing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def conflict(*_args: object, **_kwargs: object) -> None:
        raise routine_review.ConcordWorkflowError("synthetic conflict")

    monkeypatch.setattr(
        routine_review,
        "_ensure_author_not_duplicate",
        conflict,
    )

    projected = routine_review._project_artifact_routine_review_from_context(
        _context(
            authors=(_author(),),
            subjects=(_subject(),),
        ),  # type: ignore[arg-type]
        "artifact-1",
    )

    assert not projected.eligibility.quick_review_eligible
    assert any(
        "Author attribution is invalid or conflicting" in reason
        for reason in projected.eligibility.exception_reasons
    )


def test_existing_current_review_preserves_first_review_boundary() -> None:
    review = SimpleNamespace(
        artifact_review_id="review-1",
        artifact_instance_id="artifact-1",
        supersedes_artifact_review_id=None,
    )
    projected = routine_review._project_artifact_routine_review_from_context(
        _context(
            authors=(_author(),),
            subjects=(_subject(),),
            reviews=(review,),
        ),  # type: ignore[arg-type]
        "artifact-1",
    )

    assert projected.current_review is review
    assert not projected.first_review_pending
    assert not projected.eligibility.quick_review_eligible
    assert any(
        "successor/correction" in reason
        for reason in projected.eligibility.exception_reasons
    )


def test_assembly_exception_prevents_quick_review(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        routine_review,
        "_assembly_state",
        lambda *_a, **_k: "needs_recovery",
    )
    projected = routine_review._project_artifact_routine_review_from_context(
        _context(
            authors=(_author(),),
            subjects=(_subject(),),
        ),  # type: ignore[arg-type]
        "artifact-1",
    )

    assert not projected.first_review_pending
    assert not projected.eligibility.quick_review_eligible
    assert any(
        "needs recovery" in reason
        for reason in projected.eligibility.exception_reasons
    )


def test_applicable_moderation_conservatively_routes_to_detailed_review(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    moderation = SimpleNamespace(moderation_record_id="moderation-1")
    monkeypatch.setattr(
        routine_review,
        "_applicable_records",
        lambda *_a, **_k: (moderation,),
    )
    projected = routine_review._project_artifact_routine_review_from_context(
        _context(
            authors=(_author(),),
            subjects=(_subject(),),
        ),  # type: ignore[arg-type]
        "artifact-1",
    )

    assert projected.applicable_moderation_records == (moderation,)
    assert not projected.eligibility.quick_review_eligible
    assert any(
        "Moderation" in reason
        for reason in projected.eligibility.exception_reasons
    )


def test_public_inspection_loads_one_activity_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _context(
        authors=(_author(),),
        subjects=(_subject(),),
    )
    calls = {"load": 0}

    monkeypatch.setattr(
        routine_review,
        "resolve_read_workspace_root",
        lambda _root: tmp_path,
    )
    monkeypatch.setattr(
        routine_review,
        "require_core_class",
        lambda *_a, **_k: None,
    )

    def load(*_args: object, **_kwargs: object) -> Any:
        calls["load"] += 1
        return context

    monkeypatch.setattr(
        routine_review,
        "load_activity_read_context",
        load,
    )

    projected = routine_review.inspect_artifact_routine_review(
        "class-1",
        "activity-1",
        "artifact-1",
        workspace_root=tmp_path,
    )

    assert calls == {"load": 1}
    assert projected.snapshot_revision == 17
