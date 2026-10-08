
from __future__ import annotations

from pathlib import Path

import pytest

import concord.workflows.student_feedback_distribution_execution as execution
import concord.workflows.student_feedback_distribution_storage as storage
from concord.workflows import (
    FEEDBACK_AVAILABILITY_DISTRIBUTABLE,
    FEEDBACK_SELECTION_ALL,
    SCORE_ANALYSIS_BASIS,
    STUDENT_FEEDBACK_BOUNDARY_STATEMENT,
    STUDENT_FEEDBACK_INSTALL_ACTION_INSTALLED,
    STUDENT_FEEDBACK_INSTALL_ACTION_REUSED,
    STUDENT_FEEDBACK_PREPARATION_SCOPE,
    StudentFeedbackProjection,
    StudentFeedbackResult,
    StudentFeedbackRosterEntry,
    StudentFeedbackRosterPreparation,
    execute_student_feedback_distribution,
    prepare_student_feedback_distribution_plan,
    preview_student_feedback_distribution,
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


def _install_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    plan = _plan(tmp_path)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    monkeypatch.setattr(
        storage,
        "require_student_feedback_plan_current",
        lambda *args, **kwargs: plan,
    )
    result = execute_student_feedback_distribution(
        plan,
        confirmation="PREPARE",
        workspace_root=workspace,
        created_at="2026-10-08T07:30:00+00:00",
    )
    assert result.action == STUDENT_FEEDBACK_INSTALL_ACTION_INSTALLED
    return plan, workspace, result


def test_historical_exact_package_reuse_skips_render_and_currentness(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan, workspace, first = _install_once(tmp_path, monkeypatch)
    before = {
        path.name: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in first.directory.iterdir()
    }

    monkeypatch.setattr(
        execution,
        "render_student_feedback_distribution_package",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("historical exact package reuse must not rerender")
        ),
    )
    monkeypatch.setattr(
        storage,
        "require_student_feedback_plan_current",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("historical exact package reuse must not read source state")
        ),
    )

    second = execute_student_feedback_distribution(
        plan,
        confirmation="PREPARE",
        workspace_root=workspace,
        created_at="2026-10-08T08:30:00+00:00",
    )

    after = {
        path.name: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in second.directory.iterdir()
    }
    assert second.action == STUDENT_FEEDBACK_INSTALL_ACTION_REUSED
    assert second.verification.plan_digest == plan.plan_digest
    assert second.verification.package_digest == first.verification.package_digest
    assert before == after
    assert tuple(tmp_path.glob(".concord-feedback-staging-*")) == ()


def test_historical_reuse_ignores_new_created_at(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan, workspace, first = _install_once(tmp_path, monkeypatch)
    original_package_digest = first.verification.package_digest

    monkeypatch.setattr(
        execution,
        "render_student_feedback_distribution_package",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("reuse must ignore new package provenance")
        ),
    )

    reused = execute_student_feedback_distribution(
        plan,
        confirmation="PREPARE",
        workspace_root=workspace,
        created_at="2099-01-01T00:00:00+00:00",
    )

    assert reused.action == STUDENT_FEEDBACK_INSTALL_ACTION_REUSED
    assert reused.verification.package_digest == original_package_digest


def test_existing_conflicting_directory_fails_before_render_or_currentness(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan(tmp_path)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    plan.destination.mkdir()
    (plan.destination / "unrelated.txt").write_text(
        "not a Concord distribution",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        execution,
        "render_student_feedback_distribution_package",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("conflicting existing destination must not rerender")
        ),
    )
    monkeypatch.setattr(
        storage,
        "require_student_feedback_plan_current",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("conflicting destination must fail before currentness")
        ),
    )

    with pytest.raises(
        ConcordWorkflowConflictError,
        match="already exists",
    ):
        execute_student_feedback_distribution(
            plan,
            confirmation="PREPARE",
            workspace_root=workspace,
            created_at="2026-10-08T08:30:00+00:00",
        )

    assert (plan.destination / "unrelated.txt").read_text(
        encoding="utf-8"
    ) == "not a Concord distribution"


def test_tampered_historical_package_fails_before_render(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan, workspace, first = _install_once(tmp_path, monkeypatch)
    student_file = plan.destination / plan.students[0].filename
    student_file.write_bytes(student_file.read_bytes() + b"tampered")

    monkeypatch.setattr(
        execution,
        "render_student_feedback_distribution_package",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("tampered destination must fail before rerender")
        ),
    )

    with pytest.raises(ConcordWorkflowConflictError):
        execute_student_feedback_distribution(
            plan,
            confirmation="PREPARE",
            workspace_root=workspace,
            created_at="2026-10-08T08:30:00+00:00",
        )

    assert first.directory == plan.destination


def test_missing_destination_still_uses_render_stage_install_chain(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan(tmp_path)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    currentness_calls = 0

    def exact_current(*args: object, **kwargs: object) -> object:
        nonlocal currentness_calls
        currentness_calls += 1
        return plan

    monkeypatch.setattr(
        storage,
        "require_student_feedback_plan_current",
        exact_current,
    )

    result = execute_student_feedback_distribution(
        plan,
        confirmation="PREPARE",
        workspace_root=workspace,
        created_at="2026-10-08T08:30:00+00:00",
    )

    assert result.action == STUDENT_FEEDBACK_INSTALL_ACTION_INSTALLED
    assert currentness_calls == 1


def test_reuse_probe_is_read_only_and_source_currentness_free() -> None:
    source = Path(
        "concord/workflows/student_feedback_distribution_storage.py"
    ).read_text(encoding="utf-8")

    start = source.index("def reuse_existing_student_feedback_distribution")
    end = source.index(
        "\ndef _promote_staging_directory",
        start,
    )
    body = source[start:end]

    assert "verify_student_feedback_distribution_directory" in body
    assert "verify_student_feedback_distribution_plan_digest" in body
    assert "_require_distribution_destination_safe" in body
    assert "require_student_feedback_plan_current" not in body
    assert "render_student_feedback" not in body
    assert "mkdtemp" not in body
    assert "write_bytes" not in body
    assert "open(\"x" not in body
