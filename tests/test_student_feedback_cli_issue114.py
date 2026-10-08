
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import concord.cli_app.handlers.feedback as feedback_handler
from concord.cli_app.main import EXIT_CONFLICT, EXIT_OK, main
from concord.cli_app.parser import build_parser
from concord.workflows import (
    FEEDBACK_SELECTION_ALL,
    FEEDBACK_SELECTION_SELECTED,
    PreparedStudentFeedbackDistribution,
    StudentFeedbackDistributionPreview,
)


def _preview() -> StudentFeedbackDistributionPreview:
    return StudentFeedbackDistributionPreview(
        class_id="class-1",
        activity_id="activity-1",
        activity_title="Memoir Revision",
        snapshot_revision=10,
        snapshot_sha256="b" * 64,
        selection_mode=FEEDBACK_SELECTION_ALL,
        roster_count=3,
        distributable_count=2,
        no_feedback_count=1,
        unresolved_count=0,
        requested_count=3,
        requested_distributable_count=2,
        requested_no_feedback_count=1,
        requested_unresolved_count=0,
        selected_for_output_count=2,
        has_unavailable_requested_students=True,
        requires_available_only_decision=True,
        roster_student_ids=(
            "student-private-001",
            "student-private-002",
            "student-private-003",
        ),
        no_feedback_student_ids=("student-private-002",),
        unresolved_student_ids=(),
        requested_entries=(),
        selected_entries=(),
    )


def _plan(tmp_path: Path) -> PreparedStudentFeedbackDistribution:
    return PreparedStudentFeedbackDistribution(
        schema_version="concord-student-feedback-distribution-plan-v1",
        class_id="class-1",
        activity_id="activity-1",
        activity_title="Memoir Revision",
        expected_snapshot_revision=10,
        expected_snapshot_sha256="b" * 64,
        selection_mode=FEEDBACK_SELECTION_ALL,
        available_only_authorized=True,
        destination=tmp_path / "feedback",
        roster_student_ids=(
            "student-private-001",
            "student-private-002",
            "student-private-003",
        ),
        requested_student_ids=(
            "student-private-001",
            "student-private-002",
            "student-private-003",
        ),
        no_feedback_student_ids=("student-private-002",),
        unresolved_student_ids=(),
        students=(),
        output_filenames=(
            "Print All Feedback.pdf",
            "Feedback Index.html",
            "distribution-manifest.json",
        ),
        plan_digest="a" * 64,
    )


def _base_preview_args(tmp_path: Path) -> tuple[str, ...]:
    return (
        "feedback",
        "distribution-preview",
        "--workspace-root",
        str(tmp_path / "workspace"),
        "--class-id",
        "class-1",
        "--activity-id",
        "activity-1",
        "--all-roster",
        "--available-only",
        "--destination",
        str(tmp_path / "feedback"),
    )


def test_feedback_preview_parser_is_noninteractive_and_explicit(
    tmp_path: Path,
) -> None:
    parser = build_parser()
    args = parser.parse_args(_base_preview_args(tmp_path))

    assert args.handler is feedback_handler.handle_distribution_preview
    assert args.all_roster is True
    assert args.student_id is None
    assert args.available_only is True
    assert not hasattr(args, "actor_id")
    assert not hasattr(args, "expected_snapshot")


def test_feedback_selection_requires_all_roster_or_student_ids(
    tmp_path: Path,
) -> None:
    parser = build_parser()
    with pytest.raises(SystemExit) as captured:
        parser.parse_args(
            (
                "feedback",
                "distribution-preview",
                "--class-id",
                "class-1",
                "--activity-id",
                "activity-1",
                "--destination",
                str(tmp_path / "feedback"),
            )
        )
    assert captured.value.code == 2


def test_selected_student_ids_are_repeatable_and_distinct_from_all_roster(
    tmp_path: Path,
) -> None:
    parser = build_parser()
    args = parser.parse_args(
        (
            "feedback",
            "distribution-preview",
            "--class-id",
            "class-1",
            "--activity-id",
            "activity-1",
            "--student-id",
            "student-2",
            "--student-id",
            "student-1",
            "--destination",
            str(tmp_path / "feedback"),
        )
    )

    assert args.all_roster is False
    assert args.student_id == ["student-2", "student-1"]
    assert feedback_handler._selection(args) == (
        FEEDBACK_SELECTION_SELECTED,
        ("student-2", "student-1"),
    )


def test_preview_prints_review_identity_without_internal_source_details(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    plan = _plan(tmp_path)
    monkeypatch.setattr(
        feedback_handler,
        "_preview_and_plan",
        lambda _args: (tmp_path / "workspace", _preview(), plan),
    )

    assert main(_base_preview_args(tmp_path)) == EXIT_OK

    rendered = capsys.readouterr().out
    assert "Class: class-1" in rendered
    assert "Activity: Memoir Revision" in rendered
    assert "Roster students: 3" in rendered
    assert "Distributable feedback: 2" in rendered
    assert "No distributable feedback: 1" in rendered
    assert "Selected for distribution: 2" in rendered
    assert f"Destination: {plan.destination}" in rendered
    assert f"Review digest: {plan.plan_digest}" in rendered
    assert "student-private-001" not in rendered
    assert "student-private-002" not in rendered
    assert "bbbbbbbb" not in rendered
    assert "workspace" not in rendered


def test_prepare_rejects_stale_review_digest_before_execution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    plan = _plan(tmp_path)
    calls: list[object] = []
    monkeypatch.setattr(
        feedback_handler,
        "_preview_and_plan",
        lambda _args: (tmp_path / "workspace", _preview(), plan),
    )
    monkeypatch.setattr(
        feedback_handler,
        "execute_student_feedback_distribution",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    result = main(
        (
            "feedback",
            "distribution-prepare",
            "--workspace-root",
            str(tmp_path / "workspace"),
            "--class-id",
            "class-1",
            "--activity-id",
            "activity-1",
            "--all-roster",
            "--available-only",
            "--destination",
            str(tmp_path / "feedback"),
            "--review-digest",
            "c" * 64,
            "--confirmation",
            "PREPARE",
        )
    )

    assert result == EXIT_CONFLICT
    assert calls == []
    assert "review digest does not match" in capsys.readouterr().err


def test_prepare_executes_exact_reviewed_plan_with_literal_confirmation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    plan = _plan(tmp_path)
    calls: list[tuple[object, str, Path, str]] = []
    verification = SimpleNamespace(
        selected_count=2,
        combined_page_count=2,
        plan_digest=plan.plan_digest,
        package_digest="d" * 64,
    )

    monkeypatch.setattr(
        feedback_handler,
        "_preview_and_plan",
        lambda _args: (tmp_path / "workspace", _preview(), plan),
    )
    monkeypatch.setattr(
        feedback_handler,
        "_created_at",
        lambda: "2026-10-08T06:30:00+00:00",
    )

    def execute(
        selected_plan,
        *,
        confirmation: str,
        workspace_root: Path,
        created_at: str,
    ):
        calls.append(
            (selected_plan, confirmation, Path(workspace_root), created_at)
        )
        return SimpleNamespace(
            action="installed",
            directory=plan.destination,
            verification=verification,
        )

    monkeypatch.setattr(
        feedback_handler,
        "execute_student_feedback_distribution",
        execute,
    )

    result = main(
        (
            "feedback",
            "distribution-prepare",
            "--workspace-root",
            str(tmp_path / "workspace"),
            "--class-id",
            "class-1",
            "--activity-id",
            "activity-1",
            "--all-roster",
            "--available-only",
            "--destination",
            str(tmp_path / "feedback"),
            "--review-digest",
            plan.plan_digest,
            "--confirmation",
            "PREPARE",
        )
    )

    assert result == EXIT_OK
    assert calls == [
        (
            plan,
            "PREPARE",
            tmp_path / "workspace",
            "2026-10-08T06:30:00+00:00",
        )
    ]
    rendered = capsys.readouterr().out
    assert "Disposition: installed" in rendered
    assert f"Review digest: {plan.plan_digest}" in rendered
    assert "Delivery state: not recorded" in rendered


def test_verify_uses_shared_read_only_package_verifier(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    directory = tmp_path / "feedback"
    calls: list[Path] = []
    verified = SimpleNamespace(
        directory=directory,
        schema_version="concord_feedback_distribution_v1",
        selected_count=2,
        combined_page_count=2,
        plan_digest="a" * 64,
        package_digest="d" * 64,
    )
    monkeypatch.setattr(
        feedback_handler,
        "verify_student_feedback_distribution_directory",
        lambda value: calls.append(Path(value)) or verified,
    )

    result = main(
        (
            "feedback",
            "distribution-verify",
            "--directory",
            str(directory),
        )
    )

    assert result == EXIT_OK
    assert calls == [directory]
    rendered = capsys.readouterr().out
    assert "Verification: passed" in rendered
    assert f"Directory: {directory}" in rendered
    assert "Feedback files: 2" in rendered


@pytest.mark.parametrize(
    "command",
    (
        "distribution-preview",
        "distribution-prepare",
        "distribution-verify",
    ),
)
def test_feedback_distribution_commands_have_help(command: str) -> None:
    with pytest.raises(SystemExit) as captured:
        main(("feedback", command, "--help"))
    assert captured.value.code == 0


def test_cli_handler_uses_shared_distribution_services_only() -> None:
    source = Path("concord/cli_app/handlers/feedback.py").read_text(
        encoding="utf-8"
    )
    assert "load_activity_read_context" in source
    assert "load_student_feedback_roster_preparation" in source
    assert "preview_student_feedback_distribution" in source
    assert "prepare_student_feedback_distribution_plan" in source
    assert "execute_student_feedback_distribution" in source
    assert "verify_student_feedback_distribution_directory" in source
    assert "render_student_feedback" not in source
    assert "stage_student_feedback" not in source
    assert "install_staged_student_feedback" not in source
