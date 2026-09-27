from __future__ import annotations

from types import SimpleNamespace
from typing import cast

import pytest

from concord import menu_artifact
from concord.workflows.artifact_routine_review import (
    ArtifactRoutineReviewContext,
    ArtifactRoutineReviewEligibility,
)
from concord.workflows.models import ActivitySummary


def _activity(revision: int = 10) -> ActivitySummary:
    return cast(
        ActivitySummary,
        SimpleNamespace(
            class_id="class-1",
            activity_id="activity-1",
            title="Essay",
            snapshot_revision=revision,
        ),
    )


def _state() -> object:
    return SimpleNamespace(require_actor=lambda: SimpleNamespace(actor_id="teacher-1"))


def _artifact(artifact_id: str) -> object:
    return SimpleNamespace(artifact_instance_id=artifact_id)


def _context(artifact_id: str, *, quick: bool) -> ArtifactRoutineReviewContext:
    return cast(
        ArtifactRoutineReviewContext,
        SimpleNamespace(
            class_id="class-1",
            activity_id="activity-1",
            artifact=_artifact(artifact_id),
            current_review=None,
            first_review_pending=True,
            snapshot_revision=10,
            snapshot_sha256="sha",
            eligibility=ArtifactRoutineReviewEligibility(
                quick_review_eligible=quick,
                exception_reasons=()
                if quick
                else ("Author attribution requires review.",),
            ),
        ),
    )


def test_review_next_reloads_selector_after_each_successful_review(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    next_items = iter(
        (
            SimpleNamespace(artifact=_artifact("artifact-a")),
            SimpleNamespace(artifact=_artifact("artifact-b")),
            None,
        )
    )
    selector_calls: list[str] = []
    handled: list[tuple[str, str]] = []

    monkeypatch.setattr(menu_artifact, "_latest", lambda activity: activity)

    def fake_next(class_id: str, activity_id: str) -> object | None:
        selector_calls.append(activity_id)
        return next(next_items)

    monkeypatch.setattr(menu_artifact, "inspect_next_artifact_review", fake_next)
    monkeypatch.setattr(
        menu_artifact,
        "_review_next_artifact_summary",
        lambda activity, artifact_id: _artifact(artifact_id),
    )
    monkeypatch.setattr(
        menu_artifact,
        "inspect_artifact_routine_review",
        lambda class_id, activity_id, artifact_id: _context(
            artifact_id,
            quick=artifact_id == "artifact-a",
        ),
    )
    monkeypatch.setattr(
        menu_artifact,
        "_quick_review_selected",
        lambda current, artifact, state: handled.append(
            ("quick", artifact.artifact_instance_id)
        )
        or True,
    )
    monkeypatch.setattr(menu_artifact, "select_one", lambda *args, **kwargs: "continue")
    monkeypatch.setattr(
        menu_artifact,
        "_record_review_selected",
        lambda current, artifact, state: handled.append(
            ("detailed", artifact.artifact_instance_id)
        )
        or True,
    )
    monkeypatch.setattr(menu_artifact, "show_result", lambda *args, **kwargs: None)

    menu_artifact._review_next(_activity(), _state())

    assert handled == [
        ("quick", "artifact-a"),
        ("detailed", "artifact-b"),
    ]
    assert selector_calls == ["activity-1", "activity-1", "activity-1"]


def test_review_next_does_not_skip_detailed_review_case(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    monkeypatch.setattr(menu_artifact, "_latest", lambda activity: activity)
    monkeypatch.setattr(
        menu_artifact,
        "inspect_next_artifact_review",
        lambda class_id, activity_id: SimpleNamespace(
            artifact=_artifact("artifact-detailed")
        ),
    )
    monkeypatch.setattr(
        menu_artifact,
        "_review_next_artifact_summary",
        lambda activity, artifact_id: _artifact(artifact_id),
    )
    monkeypatch.setattr(
        menu_artifact,
        "inspect_artifact_routine_review",
        lambda *args: _context("artifact-detailed", quick=False),
    )
    monkeypatch.setattr(
        menu_artifact,
        "_quick_review_selected",
        lambda *args, **kwargs: pytest.fail("must not route to Quick Review"),
    )
    monkeypatch.setattr(menu_artifact, "select_one", lambda *args, **kwargs: "continue")

    def fake_detailed(current: object, artifact: object, state: object) -> bool:
        calls.append(artifact.artifact_instance_id)
        return False

    monkeypatch.setattr(menu_artifact, "_record_review_selected", fake_detailed)
    monkeypatch.setattr(menu_artifact, "show_result", lambda *args, **kwargs: None)

    menu_artifact._review_next(_activity(), _state())

    assert calls == ["artifact-detailed"]


@pytest.mark.parametrize("route", ("quick", "detailed"))
def test_review_next_stops_without_reload_when_review_not_committed(
    monkeypatch: pytest.MonkeyPatch,
    route: str,
) -> None:
    selector_calls = 0

    monkeypatch.setattr(menu_artifact, "_latest", lambda activity: activity)

    def fake_next(class_id: str, activity_id: str) -> object:
        nonlocal selector_calls
        selector_calls += 1
        if selector_calls > 1:
            pytest.fail("selector must not reload after an uncommitted Review")
        return SimpleNamespace(artifact=_artifact("artifact-a"))

    monkeypatch.setattr(menu_artifact, "inspect_next_artifact_review", fake_next)
    monkeypatch.setattr(
        menu_artifact,
        "_review_next_artifact_summary",
        lambda activity, artifact_id: _artifact(artifact_id),
    )
    monkeypatch.setattr(
        menu_artifact,
        "inspect_artifact_routine_review",
        lambda *args: _context("artifact-a", quick=route == "quick"),
    )
    monkeypatch.setattr(menu_artifact, "show_result", lambda *args, **kwargs: None)
    monkeypatch.setattr(menu_artifact, "select_one", lambda *args, **kwargs: "continue")
    monkeypatch.setattr(
        menu_artifact,
        "_quick_review_selected",
        lambda *args, **kwargs: False,
    )
    monkeypatch.setattr(
        menu_artifact,
        "_record_review_selected",
        lambda *args, **kwargs: False,
    )

    menu_artifact._review_next(_activity(), _state())

    assert selector_calls == 1


def test_review_next_detailed_evidence_open_failure_stops_before_review(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(menu_artifact, "_latest", lambda activity: activity)
    monkeypatch.setattr(
        menu_artifact,
        "inspect_next_artifact_review",
        lambda class_id, activity_id: SimpleNamespace(
            artifact=_artifact("artifact-detailed")
        ),
    )
    monkeypatch.setattr(
        menu_artifact,
        "_review_next_artifact_summary",
        lambda activity, artifact_id: _artifact(artifact_id),
    )
    monkeypatch.setattr(
        menu_artifact,
        "inspect_artifact_routine_review",
        lambda *args: _context("artifact-detailed", quick=False),
    )
    monkeypatch.setattr(menu_artifact, "show_result", lambda *args, **kwargs: None)
    monkeypatch.setattr(menu_artifact, "select_one", lambda *args, **kwargs: "open")
    monkeypatch.setattr(
        menu_artifact,
        "_open_selected_returned_work",
        lambda current, artifact: False,
    )
    monkeypatch.setattr(
        menu_artifact,
        "_record_review_selected",
        lambda *args, **kwargs: pytest.fail("Detailed Review must not start"),
    )

    menu_artifact._review_next(_activity(), _state())


def test_review_next_summary_lookup_uses_exact_current_artifact(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        menu_artifact,
        "list_artifacts",
        lambda class_id, activity_id: (
            _artifact("artifact-a"),
            _artifact("artifact-b"),
        ),
    )

    result = menu_artifact._review_next_artifact_summary(
        _activity(),
        "artifact-b",
    )

    assert result.artifact_instance_id == "artifact-b"
