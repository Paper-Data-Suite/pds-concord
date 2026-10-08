
from __future__ import annotations

from pathlib import Path

import pytest

import concord.workflows.student_feedback_distribution_storage as storage
from concord.workflows import (
    FEEDBACK_AVAILABILITY_DISTRIBUTABLE,
    FEEDBACK_SELECTION_ALL,
    SCORE_ANALYSIS_BASIS,
    STUDENT_FEEDBACK_BOUNDARY_STATEMENT,
    STUDENT_FEEDBACK_PREPARATION_SCOPE,
    StudentFeedbackProjection,
    StudentFeedbackResult,
    StudentFeedbackRosterEntry,
    StudentFeedbackRosterPreparation,
    install_staged_student_feedback_distribution,
    prepare_student_feedback_distribution_plan,
    preview_student_feedback_distribution,
    render_student_feedback_distribution_package,
    stage_student_feedback_distribution,
)
from concord.workflows.errors import ConcordWorkflowConflictError


def _projection() -> StudentFeedbackProjection:
    return StudentFeedbackProjection(
        student_display_name="Jane Doe",
        activity_title="Memoir Revision",
        class_label="English 12 - Period 2",
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


def _plan(tmp_path: Path):
    preparation = StudentFeedbackRosterPreparation(
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
                projection=_projection(),
            ),
        ),
    )
    preview = preview_student_feedback_distribution(
        preparation,
        selection_mode=FEEDBACK_SELECTION_ALL,
    )
    return prepare_student_feedback_distribution_plan(
        preview,
        destination=tmp_path / "feedback",
    )


def _stage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    workspace = tmp_path / "workspace"
    workspace.mkdir(exist_ok=True)
    plan = _plan(tmp_path)
    package = render_student_feedback_distribution_package(
        plan,
        created_at="2026-10-08T09:00:00+00:00",
    )
    monkeypatch.setattr(
        storage,
        "require_student_feedback_plan_current",
        lambda *args, **kwargs: plan,
    )
    staged = stage_student_feedback_distribution(
        plan,
        package,
        workspace_root=workspace,
    )
    return plan, staged


def test_exclusive_promotion_never_replaces_existing_empty_directory(
    tmp_path: Path,
) -> None:
    staging = tmp_path / ".concord-feedback-staging-direct"
    destination = tmp_path / "feedback"
    staging.mkdir()
    marker = staging / "marker.txt"
    marker.write_text("verified stage", encoding="utf-8")
    destination.mkdir()

    with pytest.raises(FileExistsError):
        storage._promote_staging_directory(staging, destination)

    assert staging.is_dir()
    assert marker.read_text(encoding="utf-8") == "verified stage"
    assert destination.is_dir()
    assert tuple(destination.iterdir()) == ()


def test_destination_race_is_conflict_and_never_overwrites_racer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan, staged = _stage(tmp_path, monkeypatch)
    real_fsync = storage._fsync_directory_if_supported
    injected = False

    def inject_race(path: Path) -> None:
        nonlocal injected
        real_fsync(path)
        if path == staged.directory and not injected:
            injected = True
            plan.destination.mkdir()

    monkeypatch.setattr(
        storage,
        "_fsync_directory_if_supported",
        inject_race,
    )

    with pytest.raises(
        ConcordWorkflowConflictError,
        match="already exists",
    ):
        install_staged_student_feedback_distribution(plan, staged)

    assert injected is True
    assert plan.destination.is_dir()
    assert tuple(plan.destination.iterdir()) == ()
    assert not staged.directory.exists()


def test_exclusive_promotion_uses_platform_no_replace_primitives() -> None:
    source = Path(
        "concord/workflows/student_feedback_distribution_storage.py"
    ).read_text(encoding="utf-8")

    start = source.index("def _promote_staging_directory")
    end = source.index(
        "\ndef install_staged_student_feedback_distribution",
        start,
    )
    body = source[start:end]

    assert "RENAME_NOREPLACE" in source
    assert "renameat2" in source
    assert "renamex_np" in source
    assert "os.rename" in body
    assert "staging.rename(destination)" not in body
    assert "os.replace" not in body


def test_unsupported_exclusive_rename_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    staging = tmp_path / ".concord-feedback-staging-unsupported"
    destination = tmp_path / "feedback"
    staging.mkdir()
    (staging / "marker.txt").write_text("keep", encoding="utf-8")

    monkeypatch.setattr(storage.os, "name", "posix")
    monkeypatch.setattr(storage.sys, "platform", "unsupported-os")

    with pytest.raises(OSError, match="atomic no-replace rename"):
        storage._promote_staging_directory(staging, destination)

    assert staging.is_dir()
    assert not destination.exists()
