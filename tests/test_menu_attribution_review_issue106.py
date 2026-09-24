from __future__ import annotations

from types import SimpleNamespace

import pytest

from concord import menu_artifact
from concord.menu_context import MenuSessionContext
from concord.workflows import ActivitySummary, WorkflowActor


def _activity() -> ActivitySummary:
    return ActivitySummary(
        class_id="class-1",
        activity_id="activity-1",
        title="Seminar Reflection",
        status="active",
        scoring_orientation="evidence_only",
        session_count=1,
        group_count=0,
        snapshot_revision=9,
    )


def _state() -> MenuSessionContext:
    return MenuSessionContext(
        actor=WorkflowActor(actor_id="teacher-1"),
    )


def _review() -> SimpleNamespace:
    return SimpleNamespace(
        snapshot_revision=9,
        candidate_author_ids=("author-1",),
        candidate_subject_ids=("subject-1",),
        candidate_count=2,
        exception_count=2,
        confirmed_relationship_count=7,
        artifacts=(
            SimpleNamespace(
                artifact_instance_id="artifact-1",
                authors=(
                    SimpleNamespace(
                        artifact_author_id="author-1",
                        reference_display_label="Alex One",
                        authorship_mode="individual_author",
                        attribution_status="proposed",
                        represented_group_id=None,
                        role_assignment_id=None,
                        representation_status=None,
                        disposition="candidate",
                        exception_code=None,
                    ),
                    SimpleNamespace(
                        artifact_author_id="author-disputed",
                        reference_display_label="Blair Two",
                        authorship_mode="observer",
                        attribution_status="disputed",
                        represented_group_id=None,
                        role_assignment_id=None,
                        representation_status=None,
                        disposition="exception",
                        exception_code="disputed",
                    ),
                ),
                subjects=(
                    SimpleNamespace(
                        artifact_subject_id="subject-1",
                        reference_display_label="Alex One",
                        subject_role="observed_participant",
                        confirmation_status="proposed",
                        criterion_id=None,
                        disposition="candidate",
                        exception_code=None,
                    ),
                    SimpleNamespace(
                        artifact_subject_id="subject-unresolved",
                        reference_display_label="Casey Three",
                        subject_role="observed_participant",
                        confirmation_status="unresolved",
                        criterion_id=None,
                        disposition="exception",
                        exception_code="unresolved",
                    ),
                ),
            ),
        ),
    )


def test_issue106_collect_defaults_to_review_and_advanced_attribution(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("builtins.input", lambda _prompt="": "b")
    monkeypatch.setattr(menu_artifact, "clear_screen", lambda: None)

    menu_artifact.launch_collect_work_menu(_activity(), _state())

    output = capsys.readouterr().out
    assert "3. Review attribution" in output
    assert "4. Advanced attribution tools" in output
    assert "Confirm who produced the work" not in output
    assert "Confirm who or what the work is about" not in output


def test_issue106_advanced_attribution_keeps_author_and_subject_tools_reachable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    answers = iter(("1", "2", "b"))
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    monkeypatch.setattr(menu_artifact, "clear_screen", lambda: None)
    monkeypatch.setattr(
        menu_artifact,
        "_launch_author_menu",
        lambda activity, _state: calls.append(f"author:{activity.activity_id}"),
    )
    monkeypatch.setattr(
        menu_artifact,
        "_launch_subject_menu",
        lambda activity, _state: calls.append(f"subject:{activity.activity_id}"),
    )

    menu_artifact._launch_advanced_attribution_menu(_activity(), _state())

    assert calls == ["author:activity-1", "subject:activity-1"]


def test_issue106_review_screen_groups_candidates_and_exceptions_without_ids(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    answers = iter(("b",))
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    monkeypatch.setattr(menu_artifact, "clear_screen", lambda: None)
    monkeypatch.setattr(
        menu_artifact,
        "inspect_artifact_attribution_review",
        lambda *_args, **_kwargs: _review(),
    )

    menu_artifact._launch_attribution_review_menu(_activity(), _state())

    output = capsys.readouterr().out
    assert "Review Attribution" in output
    assert "Authors: 1" in output
    assert "Subjects: 1" in output
    assert "Needs individual attention: 2" in output
    assert "Already confirmed: 7" in output
    assert "Completed by: Alex One [proposed; candidate]" in output
    assert "Completed by: Blair Two [disputed; individual review]" in output
    assert "Concerns: Alex One [proposed; candidate]" in output
    assert "Concerns: Casey Three [unresolved; individual review]" in output
    assert "author-1" not in output
    assert "subject-1" not in output


def test_issue106_confirm_all_uses_one_confirmation_and_one_exact_batch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    review = _review()
    confirmations: list[tuple[str, tuple[str, ...]]] = []
    requests: list[object] = []

    def _confirm(
        _title: str,
        expected: str,
        lines: object,
    ) -> bool:
        confirmations.append((expected, tuple(lines)))
        return True

    monkeypatch.setattr(menu_artifact, "confirm_write", _confirm)
    monkeypatch.setattr(menu_artifact, "show_result", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        menu_artifact,
        "batch_confirm_artifact_attribution",
        lambda request: requests.append(request)
        or SimpleNamespace(
            confirmed_author_count=1,
            confirmed_subject_count=1,
            commit=SimpleNamespace(snapshot_revision=10),
        ),
    )

    menu_artifact._confirm_all_straightforward_attribution(
        _activity(),
        review,
        _state(),
    )

    assert len(confirmations) == 1
    expected, lines = confirmations[0]
    assert expected == "CONFIRM"
    assert "Authors to confirm: 1" in lines
    assert "Subjects to confirm: 1" in lines
    assert "Excluded for individual attention: 2" in lines
    assert len(requests) == 1
    request = requests[0]
    assert request.artifact_author_ids == ("author-1",)
    assert request.artifact_subject_ids == ("subject-1",)
    assert request.expected_snapshot_revision == 9
    assert request.actor.actor_id == "teacher-1"


def test_issue106_cancel_before_confirm_produces_no_batch_mutation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        menu_artifact,
        "confirm_write",
        lambda *_args, **_kwargs: False,
    )
    monkeypatch.setattr(
        menu_artifact,
        "batch_confirm_artifact_attribution",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("canceled review must not mutate attribution")
        ),
    )

    menu_artifact._confirm_all_straightforward_attribution(
        _activity(),
        _review(),
        _state(),
    )


def test_issue106_confirm_all_with_no_candidates_is_read_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    review = SimpleNamespace(
        candidate_author_ids=(),
        candidate_subject_ids=(),
        candidate_count=0,
        exception_count=2,
        snapshot_revision=9,
    )
    shown: list[str] = []
    monkeypatch.setattr(
        menu_artifact,
        "show_result",
        lambda title, _lines: shown.append(title),
    )
    monkeypatch.setattr(
        menu_artifact,
        "batch_confirm_artifact_attribution",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("empty candidate review must not mutate attribution")
        ),
    )

    menu_artifact._confirm_all_straightforward_attribution(
        _activity(),
        review,
        _state(),
    )

    assert shown == ["Confirm Attribution"]
