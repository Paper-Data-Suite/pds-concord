
from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace

import pytest

import concord.menu_publication as publication_menu
import concord.menu_student_feedback as feedback_menu
from concord.menu_context import MenuSessionContext
from concord.workflows import (
    FEEDBACK_AVAILABILITY_DISTRIBUTABLE,
    FEEDBACK_AVAILABILITY_NONE,
    FEEDBACK_AVAILABILITY_UNRESOLVED,
    SCORE_ANALYSIS_BASIS,
    STUDENT_FEEDBACK_BOUNDARY_STATEMENT,
    STUDENT_FEEDBACK_PREPARATION_SCOPE,
    ActivitySummary,
    StudentFeedbackProjection,
    StudentFeedbackResult,
    StudentFeedbackRosterEntry,
    StudentFeedbackRosterPreparation,
)


def _inputs(monkeypatch: pytest.MonkeyPatch, values: list[str]) -> None:
    iterator: Iterator[str] = iter(values)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(iterator))


def _activity() -> ActivitySummary:
    return ActivitySummary(
        class_id="class-1",
        activity_id="activity-1",
        title="Memoir Revision",
        status="active",
        scoring_orientation="mixed",
        session_count=1,
        group_count=0,
        snapshot_revision=10,
    )


def _projection(name: str) -> StudentFeedbackProjection:
    return StudentFeedbackProjection(
        student_display_name=name,
        activity_title="Memoir Revision",
        class_label=None,
        boundary_statement=STUDENT_FEEDBACK_BOUNDARY_STATEMENT,
        results=(
            StudentFeedbackResult(
                criterion_label="Use of Evidence",
                scoring_scale_name="Four Levels",
                disposition="scored",
                value=3,
                value_label="Meeting",
            ),
        ),
    )


def _preparation() -> StudentFeedbackRosterPreparation:
    return StudentFeedbackRosterPreparation(
        class_id="class-1",
        activity_id="activity-1",
        activity_title="Memoir Revision",
        snapshot_revision=10,
        snapshot_sha256="b" * 64,
        score_basis=SCORE_ANALYSIS_BASIS,
        sharing_scope=STUDENT_FEEDBACK_PREPARATION_SCOPE,
        entries=(
            StudentFeedbackRosterEntry(
                student_id="student-private-001",
                student_display_name="Jane Doe",
                availability=FEEDBACK_AVAILABILITY_DISTRIBUTABLE,
                projection=_projection("Jane Doe"),
            ),
            StudentFeedbackRosterEntry(
                student_id="student-private-002",
                student_display_name="John Smith",
                availability=FEEDBACK_AVAILABILITY_NONE,
                projection=StudentFeedbackProjection(
                    student_display_name="John Smith",
                    activity_title="Memoir Revision",
                    class_label=None,
                    boundary_statement=STUDENT_FEEDBACK_BOUNDARY_STATEMENT,
                    results=(),
                ),
            ),
            StudentFeedbackRosterEntry(
                student_id="student-private-003",
                student_display_name=None,
                availability=FEEDBACK_AVAILABILITY_UNRESOLVED,
                projection=None,
                unresolved_reason="unsafe required display semantics",
            ),
        ),
    )


def _stub_preparation(
    monkeypatch: pytest.MonkeyPatch,
    preparation: StudentFeedbackRosterPreparation,
) -> None:
    monkeypatch.setattr(
        feedback_menu,
        "_load_preparation",
        lambda _activity: (Path("C:/workspace"), preparation),
    )


def test_share_menu_separates_local_feedback_from_academic_sharing(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    activity = _activity()
    monkeypatch.setattr(
        publication_menu,
        "show_activity",
        lambda *_args, **_kwargs: SimpleNamespace(summary=activity),
    )
    monkeypatch.setattr(
        publication_menu,
        "_root",
        lambda: Path("C:/workspace"),
    )
    monkeypatch.setattr(publication_menu, "clear_screen", lambda: None)
    _inputs(monkeypatch, ["b"])

    publication_menu.launch_share_results_menu(
        activity,
        MenuSessionContext(),
    )

    output = capsys.readouterr().out
    assert "1. Set up sharing" in output
    assert "2. Review what will be shared" in output
    assert "3. Share results" in output
    assert "4. View sharing history" in output
    assert "5. Stop sharing current results" in output
    assert "6. Student feedback distribution (local package)" in output


def test_share_menu_routes_feedback_to_distinct_submenu(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    activity = _activity()
    calls: list[str] = []
    monkeypatch.setattr(
        publication_menu,
        "show_activity",
        lambda *_args, **_kwargs: SimpleNamespace(summary=activity),
    )
    monkeypatch.setattr(
        publication_menu,
        "_root",
        lambda: Path("C:/workspace"),
    )
    monkeypatch.setattr(
        publication_menu,
        "launch_student_feedback_distribution_menu",
        lambda selected, _state: calls.append(selected.activity_id),
    )
    monkeypatch.setattr(publication_menu, "clear_screen", lambda: None)
    _inputs(monkeypatch, ["6", "b"])

    publication_menu.launch_share_results_menu(
        activity,
        MenuSessionContext(),
    )

    assert calls == ["activity-1"]


def test_feedback_submenu_exposes_ticketed_actions(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(feedback_menu, "clear_screen", lambda: None)
    _inputs(monkeypatch, ["b"])

    feedback_menu.launch_student_feedback_distribution_menu(
        _activity(),
        MenuSessionContext(),
    )

    output = capsys.readouterr().out
    assert "Student Feedback Distribution" in output
    assert "1. Prepare feedback for all roster students" in output
    assert "2. Prepare feedback for selected students" in output
    assert "3. Verify an existing distribution" in output
    assert "4. Open a verified distribution folder" in output
    assert "5. Open a verified class print PDF" in output


def test_incomplete_all_roster_requires_exact_available_only_phrase(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    activity = _activity()
    _stub_preparation(monkeypatch, _preparation())
    calls: list[object] = []
    monkeypatch.setattr(
        feedback_menu,
        "prepare_student_feedback_distribution_plan",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )
    monkeypatch.setattr(feedback_menu, "clear_screen", lambda: None)
    monkeypatch.setattr(feedback_menu, "pause_for_user", lambda: None)

    _inputs(monkeypatch, ["PREPARE available only", "b"])
    feedback_menu._prepare_distribution(activity, selected=False)
    assert calls == []

    _inputs(monkeypatch, [" PREPARE AVAILABLE ONLY", "b"])
    feedback_menu._prepare_distribution(activity, selected=False)
    assert calls == []


def test_incomplete_all_roster_authorization_reaches_reviewed_plan(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    activity = _activity()
    _stub_preparation(monkeypatch, _preparation())
    captured: list[dict[str, object]] = []
    plan = SimpleNamespace(destination=Path("C:/feedback"))

    def fake_plan(_preview, **kwargs):
        captured.append(kwargs)
        return plan

    monkeypatch.setattr(
        feedback_menu,
        "prepare_student_feedback_distribution_plan",
        fake_plan,
    )
    monkeypatch.setattr(
        feedback_menu,
        "execute_student_feedback_distribution",
        lambda *_args, **_kwargs: SimpleNamespace(
            action="installed",
            verification=SimpleNamespace(
                selected_count=1,
                combined_page_count=1,
            ),
        ),
    )
    monkeypatch.setattr(feedback_menu, "show_result", lambda *_args: None)
    monkeypatch.setattr(feedback_menu, "clear_screen", lambda: None)
    monkeypatch.setattr(
        feedback_menu,
        "_created_at",
        lambda: "2026-10-08T06:00:00+00:00",
    )
    _inputs(
        monkeypatch,
        [
            "PREPARE AVAILABLE ONLY",
            "C:/feedback",
            "PREPARE",
        ],
    )

    feedback_menu._prepare_distribution(activity, selected=False)

    assert captured == [
        {
            "destination": Path("C:/feedback"),
            "authorize_available_only": True,
        }
    ]


def test_selected_mode_refuses_unavailable_without_creating_plan(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    activity = _activity()
    _stub_preparation(monkeypatch, _preparation())
    captured: list[tuple[str, tuple[str, ...]]] = []
    monkeypatch.setattr(
        feedback_menu,
        "select_many",
        lambda *_args, **_kwargs: _preparation().entries[:2],
    )
    monkeypatch.setattr(
        feedback_menu,
        "prepare_student_feedback_distribution_plan",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("unavailable selection must not create a plan")
        ),
    )
    monkeypatch.setattr(
        feedback_menu,
        "show_result",
        lambda title, lines: captured.append((title, tuple(lines))),
    )

    feedback_menu._prepare_distribution(activity, selected=True)

    assert len(captured) == 1
    rendered = "\n".join(captured[0][1])
    assert "contains unavailable or unresolved feedback" in rendered
    assert "student-private-001" not in rendered
    assert "student-private-002" not in rendered


def test_routine_preview_hides_ids_hashes_and_workspace_internals() -> None:
    activity = _activity()
    preview = feedback_menu.preview_student_feedback_distribution(
        _preparation(),
        selection_mode=feedback_menu.FEEDBACK_SELECTION_ALL,
    )

    rendered = "\n".join(feedback_menu._preview_lines(activity, preview))

    assert "Jane Doe" in rendered
    assert "John Smith" in rendered
    assert "student-private-001" not in rendered
    assert "student-private-002" not in rendered
    assert "bbbbbbbb" not in rendered
    assert "C:/workspace" not in rendered


def test_verify_and_open_menu_actions_use_read_only_services(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    activity = _activity()
    calls: list[tuple[str, Path]] = []
    verified = SimpleNamespace(
        selected_count=2,
        combined_page_count=2,
    )

    monkeypatch.setattr(
        feedback_menu,
        "verify_student_feedback_distribution_directory",
        lambda path: calls.append(("verify", Path(path))) or verified,
    )
    monkeypatch.setattr(
        feedback_menu,
        "open_student_feedback_distribution_directory",
        lambda path: calls.append(("folder", Path(path))) or verified,
    )
    monkeypatch.setattr(
        feedback_menu,
        "open_student_feedback_distribution_print_pdf",
        lambda path: calls.append(("pdf", Path(path))) or verified,
    )
    monkeypatch.setattr(feedback_menu, "show_result", lambda *_args: None)
    monkeypatch.setattr(feedback_menu, "clear_screen", lambda: None)
    _inputs(
        monkeypatch,
        [
            "3",
            "C:/feedback",
            "4",
            "C:/feedback",
            "5",
            "C:/feedback",
            "b",
        ],
    )

    feedback_menu.launch_student_feedback_distribution_menu(
        activity,
        MenuSessionContext(),
    )

    assert calls == [
        ("verify", Path("C:/feedback")),
        ("folder", Path("C:/feedback")),
        ("pdf", Path("C:/feedback")),
    ]


def test_menu_module_does_not_call_publication_services() -> None:
    source = Path("concord/menu_student_feedback.py").read_text(encoding="utf-8")

    forbidden = (
        "register_concord_academic_work",
        "generate_academic_result_manifest",
        "publish_concord_academic_results",
        "withdraw_concord_academic_result_publication",
        "publication_history",
    )
    for token in forbidden:
        assert token not in source
