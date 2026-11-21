"""#151 Slice 5A: Collect-to-Review navigation and routed-return guidance.

Synthetic menu-only assertions. No scans, teachers, or academic writes are made.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import concord.menu_artifact as menu
from concord.menu_context import MenuSessionContext
from concord.workflows import ConcordWorkflowConflictError
from concord.workflows.models import ActivitySummary


def _activity(*, revision: int = 7, class_id: str = "class-151") -> ActivitySummary:
    return ActivitySummary(
        class_id=class_id,
        activity_id="activity-151",
        title="Synthetic Classroom Review",
        status="active",
        scoring_orientation="mixed",
        session_count=2,
        group_count=6,
        snapshot_revision=revision,
    )


def _inputs(monkeypatch: pytest.MonkeyPatch, choices: tuple[str, ...]) -> None:
    values = iter(choices)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(values))
    monkeypatch.setattr(menu, "clear_screen", lambda: None)


@pytest.mark.parametrize("command", ("n", "N"))
def test_collect_continues_to_review_with_fresh_same_activity_and_session(
    monkeypatch: pytest.MonkeyPatch, command: str
) -> None:
    selected = _activity()
    refreshed = _activity(revision=13)
    state = MenuSessionContext()
    calls: list[tuple[ActivitySummary, MenuSessionContext]] = []
    monkeypatch.setattr(menu, "_latest", lambda _a: refreshed)
    monkeypatch.setattr(
        menu,
        "launch_review_work_menu",
        lambda activity, session: calls.append((activity, session)),
    )
    monkeypatch.setattr(
        menu,
        "_assemble",
        lambda *_a: pytest.fail("continuing cannot assemble"),
    )
    monkeypatch.setattr(
        menu,
        "_launch_attribution_review_menu",
        lambda *_a: pytest.fail("continuing cannot confirm attribution"),
    )
    _inputs(monkeypatch, (command, "b"))
    menu.launch_collect_work_menu(selected, state)
    assert calls == [(refreshed, state)]


def test_nested_review_back_resumes_collect_without_a_write(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    selected = _activity()
    state = MenuSessionContext()
    refreshed = _activity(revision=15)
    entries: list[int] = []
    monkeypatch.setattr(menu, "_latest", lambda _a: refreshed)

    def child(activity: ActivitySummary, session: MenuSessionContext) -> None:
        assert session is state
        assert activity.snapshot_revision == 15
        entries.append(activity.snapshot_revision)
        return  # Child B: no durable continuation state.

    monkeypatch.setattr(menu, "launch_review_work_menu", child)
    _inputs(monkeypatch, ("n", "n", "b"))
    menu.launch_collect_work_menu(selected, state)
    assert entries == [15, 15]
    assert capsys.readouterr().out.count("N. Continue to Review") == 3


def test_collect_back_never_refreshes_or_enters_review(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(menu, "_latest", lambda _a: pytest.fail("back refreshed"))
    monkeypatch.setattr(
        menu,
        "launch_review_work_menu",
        lambda *_a: pytest.fail("back entered review"),
    )
    _inputs(monkeypatch, ("b",))
    menu.launch_collect_work_menu(_activity(), MenuSessionContext())


def test_stale_or_wrong_activity_handoff_never_enters_child(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    errors: list[Exception] = []
    monkeypatch.setattr(menu, "_latest", lambda _a: _activity(class_id="other"))
    monkeypatch.setattr(
        menu,
        "launch_review_work_menu",
        lambda *_a: pytest.fail("cross-class Review entered"),
    )
    monkeypatch.setattr(
        menu,
        "_handle_error",
        lambda _a, error, **_kw: errors.append(error),
    )
    _inputs(monkeypatch, ("n", "b"))
    menu.launch_collect_work_menu(_activity(), MenuSessionContext())
    assert len(errors) == 1
    assert isinstance(errors[0], ConcordWorkflowConflictError)


def test_unavailable_refreshed_activity_is_actionable_not_swallowed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    errors: list[Exception] = []

    def stale(_activity: object) -> ActivitySummary:
        raise ConcordWorkflowConflictError("Synthetic snapshot changed")

    monkeypatch.setattr(menu, "_latest", stale)
    monkeypatch.setattr(
        menu,
        "launch_review_work_menu",
        lambda *_a: pytest.fail("stale Review entered"),
    )
    monkeypatch.setattr(
        menu,
        "_handle_error",
        lambda _a, error, **_kw: errors.append(error),
    )
    _inputs(monkeypatch, ("n", "b"))
    menu.launch_collect_work_menu(_activity(), MenuSessionContext())
    assert len(errors) == 1
    assert isinstance(errors[0], ConcordWorkflowConflictError)


def test_collect_help_describes_independent_review_and_resumption(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _inputs(monkeypatch, ("h", "b"))
    monkeypatch.setattr(menu, "pause_for_user", lambda *_a: None)
    menu.launch_collect_work_menu(_activity(), MenuSessionContext())
    output = capsys.readouterr().out
    assert "N. Continue to Review" in output
    assert "Nothing is reviewed automatically" in output
    assert "B returns to Collect" in output


def test_scan_handoff_remains_independent_of_review(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = MenuSessionContext()
    calls: list[MenuSessionContext] = []
    monkeypatch.setattr(
        menu, "launch_scan_routing_menu", lambda session: calls.append(session)
    )
    monkeypatch.setattr(
        menu,
        "launch_review_work_menu",
        lambda *_a: pytest.fail("routing must not enter review"),
    )
    _inputs(monkeypatch, ("r", "b"))
    menu.launch_collect_work_menu(_activity(), state)
    assert calls == [state]


def _pending_review() -> SimpleNamespace:
    author = SimpleNamespace(
        reference_display_label="Synthetic Author",
        attribution_status="proposed",
        disposition="exception",
        exception_code="return_evidence_pending",
        represented_group_id=None,
    )
    subject = SimpleNamespace(
        reference_display_label="Synthetic Subject",
        confirmation_status="proposed",
        disposition="exception",
        exception_code="return_evidence_pending",
    )
    return SimpleNamespace(
        candidate_author_ids=(),
        candidate_subject_ids=(),
        exception_count=2,
        confirmed_relationship_count=0,
        artifacts=(
            SimpleNamespace(
                artifact_instance_id="artifact-151-synthetic",
                authors=(author,),
                subjects=(subject,),
            ),
        ),
    )


def test_pending_paper_attribution_displays_next_action_for_both_kinds(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(menu, "clear_screen", lambda: None)
    menu._print_attribution_review(_activity(), _pending_review())
    output = capsys.readouterr().out
    assert output.count("Waiting for complete routed paper") == 2
    assert "use Collect R then S before confirming" in output
    assert "Needs individual attention: 2" in output
    assert "Needs confirmation:\n  Authors: 0\n  Subjects: 0" in output


def test_disputed_or_semantic_invalid_does_not_claim_missing_scans(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    review = _pending_review()
    review.artifacts[0].authors[0].exception_code = "disputed"
    review.artifacts[0].subjects[0].exception_code = "semantic_invalid"
    monkeypatch.setattr(menu, "clear_screen", lambda: None)
    menu._print_attribution_review(_activity(), review)
    output = capsys.readouterr().out
    assert "Waiting for complete routed paper" not in output
    assert "individual review" in output


def test_review_attribution_help_names_independent_return_gate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    shown: list[tuple[str, tuple[str, ...]]] = []
    monkeypatch.setattr(
        menu,
        "inspect_artifact_attribution_review",
        lambda *_a: _pending_review(),
    )
    monkeypatch.setattr(menu, "_print_attribution_review", lambda *_a: None)
    monkeypatch.setattr(
        menu,
        "show_result",
        lambda title, lines: shown.append((title, tuple(lines))),
    )
    _inputs(monkeypatch, ("h", "b"))
    menu._launch_attribution_review_menu(_activity(), MenuSessionContext())
    assert len(shown) == 1
    rendered = " ".join(shown[0][1])
    assert "semantic checks and required routed returns" in rendered
    assert "use R to route or review scans" in rendered


def test_review_handoff_does_not_invoke_attribution_writer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(menu, "_latest", lambda activity: activity)
    monkeypatch.setattr(
        menu,
        "batch_confirm_artifact_attribution",
        lambda *_a, **_kw: pytest.fail("unexpected batch confirmation"),
    )
    monkeypatch.setattr(menu, "launch_review_work_menu", lambda *_a: None)
    _inputs(monkeypatch, ("n", "b"))
    menu.launch_collect_work_menu(_activity(), MenuSessionContext())
