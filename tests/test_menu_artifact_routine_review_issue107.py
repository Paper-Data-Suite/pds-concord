from __future__ import annotations

from types import SimpleNamespace
from typing import cast

import pytest

from concord import menu_artifact
from concord.models import PrivacyPolicy
from concord.workflows.artifact_routine_review import (
    ArtifactRoutineReviewContext,
    ArtifactRoutineReviewEligibility,
)
from concord.workflows.artifact_routine_review_profiles import (
    ArtifactRoutineReviewValues,
)
from concord.workflows.models import ActivitySummary, WorkflowActor


def _activity() -> ActivitySummary:
    return cast(
        ActivitySummary,
        SimpleNamespace(
            class_id="class-1",
            activity_id="activity-1",
            title="Essay",
            snapshot_revision=12,
        ),
    )


def _actor() -> WorkflowActor:
    return WorkflowActor(actor_id="teacher-1")


def _state() -> object:
    return SimpleNamespace(require_actor=lambda: _actor())


def _artifact() -> object:
    return SimpleNamespace(artifact_instance_id="artifact-1")


def _context(*, eligible: bool = True) -> ArtifactRoutineReviewContext:
    reasons = () if eligible else ("Author attribution requires review.",)
    return cast(
        ArtifactRoutineReviewContext,
        SimpleNamespace(
            class_id="class-1",
            activity_id="activity-1",
            artifact=SimpleNamespace(artifact_instance_id="artifact-1"),
            current_review=None,
            first_review_pending=True,
            snapshot_revision=17,
            snapshot_sha256="abc123",
            eligibility=ArtifactRoutineReviewEligibility(
                quick_review_eligible=eligible,
                exception_reasons=reasons,
            ),
        ),
    )


def test_routine_review_preview_lists_complete_explicit_bundle() -> None:
    values = ArtifactRoutineReviewValues(
        readability_judgment="readable",
        page_completeness_judgment="complete",
        filing_judgment="correct",
        author_judgment="confirmed",
        subject_judgment="confirmed",
        privacy_judgment="teacher_restricted",
        relevance_judgment="relevant",
        moderation_requirement="not_required",
        scoring_readiness="ready",
        review_outcome="ready",
        notes=None,
        privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
    )

    assert menu_artifact._routine_review_value_lines(values) == (
        "Readability: readable",
        "Page completeness: complete",
        "Filing: correct",
        "Author judgment: confirmed",
        "Subject judgment: confirmed",
        "Evidence privacy: teacher_restricted",
        "Relevance: relevant",
        "Moderation requirement: not_required",
        "Scoring readiness: ready",
        "Outcome: ready",
        "Notes: -",
        "Review privacy: teacher_restricted",
    )


def test_quick_ready_review_uses_selected_artifact_and_review_confirmation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _context()
    captured: dict[str, object] = {}
    results: list[tuple[str, tuple[str, ...]]] = []

    monkeypatch.setattr(menu_artifact, "_latest", lambda activity: activity)
    monkeypatch.setattr(
        menu_artifact,
        "_choose_artifact",
        lambda activity, *, title: _artifact(),
    )
    monkeypatch.setattr(
        menu_artifact,
        "inspect_artifact_routine_review",
        lambda class_id, activity_id, artifact_id: context,
    )
    choices = iter(("continue", "ready"))
    monkeypatch.setattr(
        menu_artifact,
        "select_one",
        lambda *args, **kwargs: next(choices),
    )

    def fake_confirm(
        title: str,
        token: str,
        lines: tuple[str, ...],
    ) -> bool:
        captured["confirmation"] = (title, token, lines)
        return True

    monkeypatch.setattr(menu_artifact, "confirm_write", fake_confirm)

    def fake_record(
        supplied_context: ArtifactRoutineReviewContext,
        values: ArtifactRoutineReviewValues,
        *,
        actor: WorkflowActor,
    ) -> object:
        captured["context"] = supplied_context
        captured["values"] = values
        captured["actor"] = actor
        return SimpleNamespace(
            artifact_review_id="artifact-review-generated",
            commit=SimpleNamespace(snapshot_revision=18),
        )

    monkeypatch.setattr(menu_artifact, "record_routine_artifact_review", fake_record)
    monkeypatch.setattr(
        menu_artifact,
        "show_result",
        lambda title, lines: results.append((title, tuple(lines))),
    )

    menu_artifact._quick_review(_activity(), _state())

    assert captured["context"] is context
    values = cast(ArtifactRoutineReviewValues, captured["values"])
    assert values.review_outcome == "ready"
    assert values.scoring_readiness == "ready"
    assert captured["actor"] == _actor()

    title, token, lines = cast(
        tuple[str, str, tuple[str, ...]],
        captured["confirmation"],
    )
    assert title == "Quick Artifact Review"
    assert token == "REVIEW"
    assert "Artifact: artifact-1" in lines
    assert "Inspected snapshot: 17" in lines
    assert "Snapshot SHA-256: abc123" in lines
    assert "Readability: readable" in lines
    assert "Review privacy: teacher_restricted" in lines
    assert results[-1][0] == "Artifact Review Recorded"


def test_quick_qualified_review_requires_note_and_previews_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _context()
    captured: dict[str, object] = {}

    monkeypatch.setattr(menu_artifact, "_latest", lambda activity: activity)
    monkeypatch.setattr(
        menu_artifact,
        "_choose_artifact",
        lambda activity, *, title: _artifact(),
    )
    monkeypatch.setattr(
        menu_artifact,
        "inspect_artifact_routine_review",
        lambda *args: context,
    )
    choices = iter(("continue", "ready_with_qualification"))
    monkeypatch.setattr(
        menu_artifact,
        "select_one",
        lambda *args, **kwargs: next(choices),
    )
    monkeypatch.setattr(
        menu_artifact,
        "prompt_text",
        lambda *args, **kwargs: "Minor scan shadow.",
    )

    def fake_confirm(
        title: str,
        token: str,
        lines: tuple[str, ...],
    ) -> bool:
        captured["lines"] = lines
        return True

    monkeypatch.setattr(menu_artifact, "confirm_write", fake_confirm)

    def fake_record(
        supplied_context: ArtifactRoutineReviewContext,
        values: ArtifactRoutineReviewValues,
        *,
        actor: WorkflowActor,
    ) -> object:
        captured["values"] = values
        return SimpleNamespace(
            artifact_review_id="artifact-review-generated",
            commit=SimpleNamespace(snapshot_revision=18),
        )

    monkeypatch.setattr(menu_artifact, "record_routine_artifact_review", fake_record)
    monkeypatch.setattr(menu_artifact, "show_result", lambda *args, **kwargs: None)

    menu_artifact._quick_review(_activity(), _state())

    values = cast(ArtifactRoutineReviewValues, captured["values"])
    assert values.review_outcome == "ready_with_qualification"
    assert values.notes == "Minor scan shadow."
    assert "Notes: Minor scan shadow." in cast(tuple[str, ...], captured["lines"])


def test_ineligible_quick_review_surfaces_reasons_without_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _context(eligible=False)
    results: list[tuple[str, tuple[str, ...]]] = []

    monkeypatch.setattr(menu_artifact, "_latest", lambda activity: activity)
    monkeypatch.setattr(
        menu_artifact,
        "_choose_artifact",
        lambda activity, *, title: _artifact(),
    )
    monkeypatch.setattr(
        menu_artifact,
        "inspect_artifact_routine_review",
        lambda *args: context,
    )
    monkeypatch.setattr(
        menu_artifact,
        "select_one",
        lambda *args, **kwargs: "continue",
    )
    monkeypatch.setattr(
        menu_artifact,
        "confirm_write",
        lambda *args, **kwargs: pytest.fail("confirmation must not occur"),
    )
    monkeypatch.setattr(
        menu_artifact,
        "record_routine_artifact_review",
        lambda *args, **kwargs: pytest.fail("write must not occur"),
    )
    monkeypatch.setattr(
        menu_artifact,
        "show_result",
        lambda title, lines: results.append((title, tuple(lines))),
    )

    menu_artifact._quick_review(_activity(), _state())

    assert results == [
        (
            "Quick Artifact Review",
            (
                "Artifact: artifact-1",
                "Quick Review is not available for this Artifact.",
                "Author attribution requires review.",
                "Use Detailed Review to record the explicit exception judgment.",
            ),
        )
    ]


def test_cancelled_quick_review_does_not_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _context()

    monkeypatch.setattr(menu_artifact, "_latest", lambda activity: activity)
    monkeypatch.setattr(
        menu_artifact,
        "_choose_artifact",
        lambda activity, *, title: _artifact(),
    )
    monkeypatch.setattr(
        menu_artifact,
        "inspect_artifact_routine_review",
        lambda *args: context,
    )
    choices = iter(("continue", "ready"))
    monkeypatch.setattr(
        menu_artifact,
        "select_one",
        lambda *args, **kwargs: next(choices),
    )
    monkeypatch.setattr(menu_artifact, "confirm_write", lambda *args, **kwargs: False)
    monkeypatch.setattr(
        menu_artifact,
        "record_routine_artifact_review",
        lambda *args, **kwargs: pytest.fail("write must not occur"),
    )

    menu_artifact._quick_review(_activity(), _state())


def test_selected_returned_work_opens_exact_artifact_without_reselection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    activity = _activity()
    artifact = _artifact()
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        menu_artifact,
        "_assembly_selections",
        lambda supplied_activity, supplied_artifact: (
            SimpleNamespace(
                artifact_page_id="page-1",
                scan_reference_id="scan-1",
            ),
        ),
    )

    def fake_open(
        class_id: str,
        activity_id: str,
        artifact_instance_id: str,
        **kwargs: object,
    ) -> None:
        captured["class_id"] = class_id
        captured["activity_id"] = activity_id
        captured["artifact_instance_id"] = artifact_instance_id
        captured["kwargs"] = kwargs

    monkeypatch.setattr(menu_artifact, "open_returned_artifact_evidence", fake_open)
    monkeypatch.setattr(menu_artifact, "show_result", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        menu_artifact,
        "_choose_artifact",
        lambda *args, **kwargs: pytest.fail("Artifact must not be reselected"),
    )

    assert menu_artifact._open_selected_returned_work(activity, artifact)

    assert captured["class_id"] == "class-1"
    assert captured["activity_id"] == "activity-1"
    assert captured["artifact_instance_id"] == "artifact-1"
    kwargs = cast(dict[str, object], captured["kwargs"])
    assert kwargs["expected_snapshot_revision"] == 12
    assert len(cast(tuple[object, ...], kwargs["selections"])) == 1


def test_quick_review_open_failure_fails_closed_before_projection_or_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(menu_artifact, "_latest", lambda activity: activity)
    monkeypatch.setattr(
        menu_artifact,
        "_choose_artifact",
        lambda activity, *, title: _artifact(),
    )
    monkeypatch.setattr(menu_artifact, "select_one", lambda *args, **kwargs: "open")
    monkeypatch.setattr(
        menu_artifact,
        "_open_selected_returned_work",
        lambda activity, artifact: False,
    )
    monkeypatch.setattr(
        menu_artifact,
        "inspect_artifact_routine_review",
        lambda *args, **kwargs: pytest.fail("projection must not occur"),
    )
    monkeypatch.setattr(
        menu_artifact,
        "record_routine_artifact_review",
        lambda *args, **kwargs: pytest.fail("write must not occur"),
    )

    menu_artifact._quick_review(_activity(), _state())


def test_quick_review_open_success_keeps_same_artifact_for_projection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _context()
    artifact = _artifact()
    seen: dict[str, object] = {}
    choices = iter(("open", "ready"))

    monkeypatch.setattr(menu_artifact, "_latest", lambda activity: activity)
    monkeypatch.setattr(
        menu_artifact,
        "_choose_artifact",
        lambda activity, *, title: artifact,
    )
    monkeypatch.setattr(
    menu_artifact,
    "select_one",
    lambda *args, **kwargs: next(choices),
    )

    def fake_selected_open(activity: object, supplied_artifact: object) -> bool:
        seen["opened_artifact"] = supplied_artifact
        return True

    monkeypatch.setattr(
        menu_artifact,
        "_open_selected_returned_work",
        fake_selected_open,
    )

    def fake_inspect(
        class_id: str,
        activity_id: str,
        artifact_instance_id: str,
    ) -> ArtifactRoutineReviewContext:
        seen["projected_artifact_id"] = artifact_instance_id
        return context

    monkeypatch.setattr(
        menu_artifact,
        "inspect_artifact_routine_review",
        fake_inspect,
    )
    monkeypatch.setattr(menu_artifact, "confirm_write", lambda *args, **kwargs: False)

    menu_artifact._quick_review(_activity(), _state())

    assert seen["opened_artifact"] is artifact
    assert seen["projected_artifact_id"] == "artifact-1"
