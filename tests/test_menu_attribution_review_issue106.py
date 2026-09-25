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

def test_issue106_subset_choices_hide_ids_and_exclude_exceptions() -> None:
    choices = menu_artifact._attribution_proposal_choices(_review())

    assert tuple(item.relationship_kind for item in choices) == (
        "author",
        "subject",
    )
    assert tuple(item.association_id for item in choices) == (
        "author-1",
        "subject-1",
    )
    assert "artifact-1 - Completed by Alex One" in choices[0].display_label
    assert "artifact-1 - Concerns Alex One" in choices[1].display_label
    assert "author-1" not in choices[0].display_label
    assert "subject-1" not in choices[1].display_label
    assert all("Blair Two" not in item.display_label for item in choices)
    assert all("Casey Three" not in item.display_label for item in choices)


def test_issue106_explicit_subset_confirms_only_selected_relationship(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    review = _review()
    requests: list[object] = []
    confirmations: list[tuple[str, tuple[str, ...]]] = []

    def _select(
        _title: str,
        items: object,
        _labels: object,
        **_kwargs: object,
    ) -> tuple[object, ...]:
        available = tuple(items)
        return (available[1],)

    def _confirm(
        _title: str,
        expected: str,
        lines: object,
    ) -> bool:
        confirmations.append((expected, tuple(lines)))
        return True

    monkeypatch.setattr(menu_artifact, "select_many", _select)
    monkeypatch.setattr(menu_artifact, "confirm_write", _confirm)
    monkeypatch.setattr(menu_artifact, "show_result", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        menu_artifact,
        "batch_confirm_artifact_attribution",
        lambda request: requests.append(request)
        or SimpleNamespace(
            confirmed_author_count=0,
            confirmed_subject_count=1,
            commit=SimpleNamespace(snapshot_revision=10),
        ),
    )

    menu_artifact._confirm_selected_straightforward_attribution(
        _activity(),
        review,
        _state(),
    )

    assert len(confirmations) == 1
    expected, lines = confirmations[0]
    assert expected == "CONFIRM"
    assert "Authors to confirm: 0" in lines
    assert "Subjects to confirm: 1" in lines
    assert "Other straightforward proposals not selected: 1" in lines
    assert len(requests) == 1
    request = requests[0]
    assert request.artifact_author_ids == ()
    assert request.artifact_subject_ids == ("subject-1",)
    assert request.expected_snapshot_revision == 9


def test_issue106_subset_selection_pages_without_losing_prior_choices(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    author_ids = tuple(f"author-{index}" for index in range(1, 13))
    review = SimpleNamespace(
        candidate_author_ids=author_ids,
        candidate_subject_ids=(),
        candidate_count=12,
        exception_count=0,
        confirmed_relationship_count=0,
        snapshot_revision=9,
        artifacts=(
            SimpleNamespace(
                artifact_instance_id="artifact-many",
                authors=tuple(
                    SimpleNamespace(
                        artifact_author_id=artifact_author_id,
                        reference_display_label=f"Student {index}",
                        authorship_mode="co_author",
                        attribution_status="proposed",
                        represented_group_id=None,
                        role_assignment_id=None,
                        representation_status=None,
                        disposition="candidate",
                        exception_code=None,
                    )
                    for index, artifact_author_id in enumerate(
                        author_ids,
                        start=1,
                    )
                ),
                subjects=(),
            ),
        ),
    )
    answers = iter(("1", "n", "1", "d"))
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))

    selected = menu_artifact._select_attribution_proposals(review)

    assert tuple(item.association_id for item in selected) == (
        "author-1",
        "author-11",
    )


def test_issue106_subset_cancel_before_confirm_produces_no_mutation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    choices = menu_artifact._attribution_proposal_choices(_review())
    monkeypatch.setattr(
        menu_artifact,
        "select_many",
        lambda *_args, **_kwargs: (choices[0],),
    )
    monkeypatch.setattr(
        menu_artifact,
        "confirm_write",
        lambda *_args, **_kwargs: False,
    )
    monkeypatch.setattr(
        menu_artifact,
        "batch_confirm_artifact_attribution",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("canceled subset confirmation must not mutate")
        ),
    )

    menu_artifact._confirm_selected_straightforward_attribution(
        _activity(),
        _review(),
        _state(),
    )

def test_issue106_review_surface_offers_homogeneous_multi_add(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(menu_artifact, "clear_screen", lambda: None)

    menu_artifact._print_attribution_review(_activity(), _review())

    output = capsys.readouterr().out
    assert "C. Create several relationships" in output


def test_issue106_multi_add_menu_routes_authors_and_subjects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    answers = iter(("1", "2", "b"))
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    monkeypatch.setattr(menu_artifact, "clear_screen", lambda: None)
    monkeypatch.setattr(
        menu_artifact,
        "_add_multiple_authors",
        lambda activity, _state: calls.append(f"authors:{activity.activity_id}"),
    )
    monkeypatch.setattr(
        menu_artifact,
        "_add_multiple_subjects",
        lambda activity, _state: calls.append(f"subjects:{activity.activity_id}"),
    )

    menu_artifact._launch_multi_add_attribution_menu(_activity(), _state())

    assert calls == ["authors:activity-1", "subjects:activity-1"]


def test_issue106_multi_add_authors_uses_one_reviewed_atomic_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = SimpleNamespace(
        artifact_instance_id="artifact-selected",
        snapshot_revision=17,
    )
    students = (
        SimpleNamespace(student_id="student-1"),
        SimpleNamespace(student_id="student-2"),
    )
    confirmations: list[tuple[str, tuple[str, ...]]] = []
    requests: list[object] = []

    monkeypatch.setattr(menu_artifact, "_latest", lambda activity: activity)
    monkeypatch.setattr(
        menu_artifact,
        "_choose_artifact",
        lambda *_args, **_kwargs: artifact,
    )
    monkeypatch.setattr(menu_artifact, "_require_workspace", lambda: object())
    monkeypatch.setattr(
        menu_artifact,
        "choose_students",
        lambda *_args, **_kwargs: students,
    )
    monkeypatch.setattr(
        menu_artifact,
        "_routine_multi_author_mode",
        lambda: "co_author",
    )
    monkeypatch.setattr(
        menu_artifact,
        "_routine_add_status",
        lambda **_kwargs: "confirmed",
    )

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
        "add_artifact_authors",
        lambda request: requests.append(request)
        or SimpleNamespace(
            artifact_author_ids=("generated-1", "generated-2"),
            commit=SimpleNamespace(snapshot_revision=18),
        ),
    )

    menu_artifact._add_multiple_authors(_activity(), _state())

    assert len(confirmations) == 1
    expected, lines = confirmations[0]
    assert expected == "ADD"
    assert "Artifact: artifact-selected" in lines
    assert "Students selected: 2" in lines
    assert "Shared authorship mode: co author" in lines
    assert len(requests) == 1
    request = requests[0]
    assert request.student_ids == ("student-1", "student-2")
    assert request.authorship_mode == "co_author"
    assert request.attribution_status == "confirmed"
    assert request.attribution_source == "teacher"
    assert request.expected_snapshot_revision == 17
    assert request.actor.actor_id == "teacher-1"


def test_issue106_multi_add_subjects_uses_one_reviewed_atomic_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = SimpleNamespace(
        artifact_instance_id="artifact-selected",
        snapshot_revision=23,
    )
    students = (
        SimpleNamespace(student_id="student-2"),
        SimpleNamespace(student_id="student-3"),
    )
    confirmations: list[tuple[str, tuple[str, ...]]] = []
    requests: list[object] = []

    monkeypatch.setattr(menu_artifact, "_latest", lambda activity: activity)
    monkeypatch.setattr(
        menu_artifact,
        "_choose_artifact",
        lambda *_args, **_kwargs: artifact,
    )
    monkeypatch.setattr(menu_artifact, "_require_workspace", lambda: object())
    monkeypatch.setattr(
        menu_artifact,
        "choose_students",
        lambda *_args, **_kwargs: students,
    )
    monkeypatch.setattr(
        menu_artifact,
        "_routine_multi_subject_role",
        lambda: "observed_participant",
    )
    monkeypatch.setattr(
        menu_artifact,
        "_routine_add_status",
        lambda **_kwargs: "proposed",
    )
    monkeypatch.setattr(
        menu_artifact,
        "prompt_text",
        lambda *_args, **_kwargs: "criterion-1",
    )

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
        "add_artifact_subjects",
        lambda request: requests.append(request)
        or SimpleNamespace(
            artifact_subject_ids=("generated-1", "generated-2"),
            commit=SimpleNamespace(snapshot_revision=24),
        ),
    )

    menu_artifact._add_multiple_subjects(_activity(), _state())

    assert len(confirmations) == 1
    expected, lines = confirmations[0]
    assert expected == "ADD"
    assert "Artifact: artifact-selected" in lines
    assert "Students selected: 2" in lines
    assert "Shared Subject role: observed participant" in lines
    assert "Shared Criterion context: criterion-1" in lines
    assert len(requests) == 1
    request = requests[0]
    assert request.student_ids == ("student-2", "student-3")
    assert request.subject_role == "observed_participant"
    assert request.confirmation_status == "proposed"
    assert request.assignment_source == "teacher"
    assert request.criterion_id == "criterion-1"
    assert request.expected_snapshot_revision == 23
    assert request.actor.actor_id == "teacher-1"


def test_issue106_multi_add_cancel_stops_before_service_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = SimpleNamespace(
        artifact_instance_id="artifact-selected",
        snapshot_revision=17,
    )
    students = (SimpleNamespace(student_id="student-1"),)
    monkeypatch.setattr(menu_artifact, "_latest", lambda activity: activity)
    monkeypatch.setattr(
        menu_artifact,
        "_choose_artifact",
        lambda *_args, **_kwargs: artifact,
    )
    monkeypatch.setattr(menu_artifact, "_require_workspace", lambda: object())
    monkeypatch.setattr(
        menu_artifact,
        "choose_students",
        lambda *_args, **_kwargs: students,
    )
    monkeypatch.setattr(
        menu_artifact,
        "_routine_multi_author_mode",
        lambda: "individual_author",
    )
    monkeypatch.setattr(
        menu_artifact,
        "_routine_add_status",
        lambda **_kwargs: "proposed",
    )
    monkeypatch.setattr(
        menu_artifact,
        "confirm_write",
        lambda *_args, **_kwargs: False,
    )
    monkeypatch.setattr(
        menu_artifact,
        "add_artifact_authors",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("canceled multi-add must not call the service")
        ),
    )

    menu_artifact._add_multiple_authors(_activity(), _state())
