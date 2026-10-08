
from __future__ import annotations

from pathlib import Path

import pytest

import concord.workflows.student_feedback_distribution_execution as execution
import concord.workflows.student_feedback_distribution_storage as storage
from concord.workflows import (
    FEEDBACK_AVAILABILITY_DISTRIBUTABLE,
    FEEDBACK_AVAILABILITY_NONE,
    FEEDBACK_SELECTION_ALL,
    SCORE_ANALYSIS_BASIS,
    STUDENT_FEEDBACK_BOUNDARY_STATEMENT,
    STUDENT_FEEDBACK_INSTALL_ACTION_INSTALLED,
    STUDENT_FEEDBACK_INSTALL_ACTION_REUSED,
    STUDENT_FEEDBACK_PREPARATION_SCOPE,
    STUDENT_FEEDBACK_PREPARE_CONFIRMATION,
    StudentFeedbackProjection,
    StudentFeedbackResult,
    StudentFeedbackRosterEntry,
    StudentFeedbackRosterPreparation,
    execute_student_feedback_distribution,
    prepare_student_feedback_distribution_plan,
    preview_student_feedback_distribution,
)
from concord.workflows.errors import ConcordWorkflowValidationError


def _projection(name: str) -> StudentFeedbackProjection:
    return StudentFeedbackProjection(
        student_display_name=name,
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
                projection=_projection("Jane Doe"),
            ),
            StudentFeedbackRosterEntry(
                student_id="student-private-002",
                student_display_name="John Smith",
                availability=FEEDBACK_AVAILABILITY_NONE,
                projection=StudentFeedbackProjection(
                    student_display_name="John Smith",
                    activity_title="Memoir Revision",
                    class_label="English 12 - Period 2",
                    boundary_statement=STUDENT_FEEDBACK_BOUNDARY_STATEMENT,
                    results=(),
                ),
            ),
            StudentFeedbackRosterEntry(
                student_id="student-private-003",
                student_display_name="Alex Rivera",
                availability=FEEDBACK_AVAILABILITY_DISTRIBUTABLE,
                projection=_projection("Alex Rivera"),
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
        authorize_available_only=True,
    )


@pytest.mark.parametrize(
    "confirmation",
    (
        "",
        "prepare",
        "Prepare",
        " PREPARE",
        "PREPARE ",
        "PREPARE\n",
        "PUBLISH",
    ),
)
def test_nonliteral_confirmation_stops_before_render_or_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    confirmation: str,
) -> None:
    plan = _plan(tmp_path)
    render_called = False
    stage_called = False

    def unexpected_render(*args: object, **kwargs: object) -> object:
        nonlocal render_called
        render_called = True
        raise AssertionError("render must not run without literal PREPARE")

    def unexpected_stage(*args: object, **kwargs: object) -> object:
        nonlocal stage_called
        stage_called = True
        raise AssertionError("stage must not run without literal PREPARE")

    monkeypatch.setattr(
        execution,
        "render_student_feedback_distribution_package",
        unexpected_render,
    )
    monkeypatch.setattr(
        execution,
        "stage_student_feedback_distribution",
        unexpected_stage,
    )

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="exact confirmation PREPARE",
    ):
        execute_student_feedback_distribution(
            plan,
            confirmation=confirmation,
            workspace_root=tmp_path / "workspace",
            created_at="2026-10-08T05:30:00+00:00",
        )

    assert render_called is False
    assert stage_called is False
    assert not plan.destination.exists()
    assert tuple(tmp_path.glob(".concord-feedback-staging-*")) == ()


def test_literal_prepare_executes_full_verified_install_chain(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan(tmp_path)
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
        confirmation=STUDENT_FEEDBACK_PREPARE_CONFIRMATION,
        workspace_root=tmp_path / "workspace",
        created_at="2026-10-08T05:30:00+00:00",
    )

    assert result.action == STUDENT_FEEDBACK_INSTALL_ACTION_INSTALLED
    assert result.directory == plan.destination
    assert result.verification.plan_digest == plan.plan_digest
    assert result.verification.managed_filenames == plan.output_filenames
    assert currentness_calls == 1
    assert tuple(tmp_path.glob(".concord-feedback-staging-*")) == ()


def test_exact_repeat_reuses_verified_destination_without_rewrite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan(tmp_path)
    monkeypatch.setattr(
        storage,
        "require_student_feedback_plan_current",
        lambda *args, **kwargs: plan,
    )

    first = execute_student_feedback_distribution(
        plan,
        confirmation="PREPARE",
        workspace_root=tmp_path / "workspace",
        created_at="2026-10-08T05:30:00+00:00",
    )
    before = {
        path.name: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in first.directory.iterdir()
    }

    second = execute_student_feedback_distribution(
        plan,
        confirmation="PREPARE",
        workspace_root=tmp_path / "workspace",
        created_at="2026-10-08T05:30:00+00:00",
    )
    after = {
        path.name: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in second.directory.iterdir()
    }

    assert second.action == STUDENT_FEEDBACK_INSTALL_ACTION_REUSED
    assert before == after
    assert tuple(tmp_path.glob(".concord-feedback-staging-*")) == ()


def test_execution_does_not_mutate_unrelated_canonical_surfaces(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan(tmp_path)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    canonical = workspace / "canonical"
    canonical.mkdir()
    files = {
        "activity.json": b'{"revision":10}',
        "scores.jsonl": b'{"score":"current"}\n',
        "publication.json": b'{"published":false}',
        "routes.json": b'{"routes":[]}',
    }
    for name, content in files.items():
        (canonical / name).write_bytes(content)
    before = {
        path.name: path.read_bytes()
        for path in canonical.iterdir()
    }

    monkeypatch.setattr(
        storage,
        "require_student_feedback_plan_current",
        lambda *args, **kwargs: plan,
    )

    execute_student_feedback_distribution(
        plan,
        confirmation="PREPARE",
        workspace_root=workspace,
        created_at="2026-10-08T05:30:00+00:00",
    )

    after = {
        path.name: path.read_bytes()
        for path in canonical.iterdir()
    }
    assert after == before


def test_execution_module_is_composition_only() -> None:
    source = Path(
        "concord/workflows/student_feedback_distribution_execution.py"
    ).read_text(encoding="utf-8")

    assert "load_activity_read_context" not in source
    assert "load_required_roster" not in source
    assert "load_current_snapshot_pointer" not in source
    assert "load_current_snapshot_graph" not in source
    assert "add_score" not in source
    assert "replace_score" not in source
    assert "publication" not in source.casefold()
    assert "route" not in source.casefold()
    assert "render_student_feedback_distribution_package" in source
    assert "stage_student_feedback_distribution" in source
    assert "install_staged_student_feedback_distribution" in source
