
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
    prepare_student_feedback_distribution_plan,
    preview_student_feedback_distribution,
    render_student_feedback_distribution_package,
    stage_student_feedback_distribution,
)
from concord.workflows.errors import ConcordWorkflowValidationError


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


def _preview():
    projection = _projection()
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
                projection=projection,
            ),
        ),
    )
    return preview_student_feedback_distribution(
        preparation,
        selection_mode=FEEDBACK_SELECTION_ALL,
    )


def _plan(destination: Path):
    return prepare_student_feedback_distribution_plan(
        _preview(),
        destination=destination,
    )


def _package(plan):
    return render_student_feedback_distribution_package(
        plan,
        created_at="2026-10-08T07:00:00+00:00",
    )


def test_plan_rejects_lexical_parent_traversal(tmp_path: Path) -> None:
    destination = tmp_path / "teacher" / ".." / "feedback"

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="parent traversal",
    ):
        _plan(destination)


def test_plan_rejects_filesystem_root_destination(tmp_path: Path) -> None:
    filesystem_root = Path(tmp_path.anchor)

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="filesystem root",
    ):
        _plan(filesystem_root)


def test_stage_rejects_destination_inside_workspace_before_currentness_or_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    parent = workspace / "exports"
    parent.mkdir(parents=True)
    plan = _plan(parent / "feedback")
    package = _package(plan)
    currentness_calls = 0

    def unexpected_currentness(*args: object, **kwargs: object) -> object:
        nonlocal currentness_calls
        currentness_calls += 1
        return plan

    monkeypatch.setattr(
        storage,
        "require_student_feedback_plan_current",
        unexpected_currentness,
    )
    monkeypatch.setattr(
        storage.tempfile,
        "mkdtemp",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("unsafe destination must fail before staging")
        ),
    )

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="must not overlap",
    ):
        stage_student_feedback_distribution(
            plan,
            package,
            workspace_root=workspace,
        )

    assert currentness_calls == 0
    assert not plan.destination.exists()


def test_stage_rejects_destination_that_contains_workspace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destination = tmp_path / "feedback-root"
    workspace = destination / "workspace"
    workspace.mkdir(parents=True)
    plan = _plan(destination)
    package = _package(plan)

    monkeypatch.setattr(
        storage,
        "require_student_feedback_plan_current",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("overlap must fail before currentness")
        ),
    )

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="must not overlap",
    ):
        stage_student_feedback_distribution(
            plan,
            package,
            workspace_root=workspace,
        )


def test_stage_allows_sibling_destination_outside_workspace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    destination_parent = tmp_path / "teacher-feedback"
    destination_parent.mkdir()
    plan = _plan(destination_parent / "feedback")
    package = _package(plan)
    calls = 0

    def exact_current(*args: object, **kwargs: object) -> object:
        nonlocal calls
        calls += 1
        return plan

    monkeypatch.setattr(
        storage,
        "require_student_feedback_plan_current",
        exact_current,
    )

    staged = stage_student_feedback_distribution(
        plan,
        package,
        workspace_root=workspace,
    )

    assert calls == 1
    assert staged.directory.parent == destination_parent
    storage._cleanup_staging(staged.directory)


def test_stage_rejects_existing_file_destination_before_currentness(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    destination = tmp_path / "feedback"
    destination.write_bytes(b"do not overwrite")
    plan = _plan(destination)
    package = _package(plan)

    monkeypatch.setattr(
        storage,
        "require_student_feedback_plan_current",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("unsafe overwrite must fail before currentness")
        ),
    )

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="not a safe directory",
    ):
        stage_student_feedback_distribution(
            plan,
            package,
            workspace_root=workspace,
        )

    assert destination.read_bytes() == b"do not overwrite"


def test_stage_rejects_redirecting_ancestor_where_supported(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    target = tmp_path / "target"
    (target / "nested").mkdir(parents=True)
    redirect = tmp_path / "redirect"
    try:
        redirect.symlink_to(target, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("directory symlink creation is unavailable on this platform")

    plan = _plan(redirect / "nested" / "feedback")
    package = _package(plan)
    monkeypatch.setattr(
        storage,
        "require_student_feedback_plan_current",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("redirect must fail before currentness")
        ),
    )

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="redirecting filesystem path",
    ):
        stage_student_feedback_distribution(
            plan,
            package,
            workspace_root=workspace,
        )


def test_destination_guard_includes_windows_junction_detection() -> None:
    source = Path(
        "concord/workflows/student_feedback_distribution_storage.py"
    ).read_text(encoding="utf-8")

    assert "is_junction" in source
    assert "_require_no_redirecting_ancestors" in source
    assert "_require_distribution_destination_safe" in source
