
from __future__ import annotations

from dataclasses import fields, replace
from pathlib import Path
from types import SimpleNamespace

import pytest

import concord.workflows.student_feedback_distribution_rendering as rendering
from concord.workflows import (
    FEEDBACK_AVAILABILITY_DISTRIBUTABLE,
    FEEDBACK_AVAILABILITY_NONE,
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
    require_student_feedback_plan_current,
    student_feedback_render_inputs_from_plan,
)
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowValidationError,
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
                    class_label=None,
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


def test_render_inputs_preserve_plan_order_without_student_ids(
    tmp_path: Path,
) -> None:
    plan = _plan(tmp_path)

    prepared = student_feedback_render_inputs_from_plan(plan)

    assert prepared.plan_digest == plan.plan_digest
    assert tuple(item.filename for item in prepared.students) == tuple(
        item.filename for item in plan.students
    )
    assert tuple(
        item.projection.student_display_name for item in prepared.students
    ) == ("Jane Doe", "Alex Rivera")
    assert tuple(field.name for field in fields(prepared.students[0])) == (
        "filename",
        "projection",
    )
    assert not plan.destination.exists()


def test_render_inputs_reject_tampered_reviewed_plan(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    tampered = replace(plan, activity_title="Changed after review")

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="digest does not match",
    ):
        student_feedback_render_inputs_from_plan(tampered)


def test_currentness_guard_reads_pointer_once_and_accepts_exact_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan(tmp_path)
    calls = 0

    def fake_pointer(workspace_root: object, work: object) -> object:
        nonlocal calls
        calls += 1
        assert workspace_root == tmp_path / "workspace"
        assert getattr(work, "module_id") == "concord"
        assert getattr(work, "class_id") == "class-1"
        assert getattr(work, "work_id") == "activity-1"
        return SimpleNamespace(
            snapshot_revision=10,
            snapshot_sha256="b" * 64,
        )

    monkeypatch.setattr(
        rendering,
        "load_current_snapshot_pointer",
        fake_pointer,
    )

    result = require_student_feedback_plan_current(
        plan,
        workspace_root=tmp_path / "workspace",
    )

    assert result is plan
    assert calls == 1
    assert not plan.destination.exists()


@pytest.mark.parametrize(
    ("revision", "sha256"),
    (
        (11, "b" * 64),
        (10, "c" * 64),
    ),
)
def test_currentness_guard_rejects_changed_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    revision: int,
    sha256: str,
) -> None:
    plan = _plan(tmp_path)

    monkeypatch.setattr(
        rendering,
        "load_current_snapshot_pointer",
        lambda _root, _work: SimpleNamespace(
            snapshot_revision=revision,
            snapshot_sha256=sha256,
        ),
    )

    with pytest.raises(
        ConcordWorkflowConflictError,
        match="no longer current",
    ):
        require_student_feedback_plan_current(
            plan,
            workspace_root=tmp_path / "workspace",
        )

    assert not plan.destination.exists()


def test_currentness_guard_rejects_digest_tampering_before_pointer_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan(tmp_path)
    tampered = replace(plan, expected_snapshot_revision=11)
    pointer_called = False

    def unexpected_pointer(_root: object, _work: object) -> object:
        nonlocal pointer_called
        pointer_called = True
        raise AssertionError("pointer read must not happen for a corrupt plan")

    monkeypatch.setattr(
        rendering,
        "load_current_snapshot_pointer",
        unexpected_pointer,
    )

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="digest does not match",
    ):
        require_student_feedback_plan_current(
            tampered,
            workspace_root=tmp_path / "workspace",
        )

    assert pointer_called is False


def test_rendering_boundary_uses_lightweight_pointer_not_graph_reload() -> None:
    source = Path(
        "concord/workflows/student_feedback_distribution_rendering.py"
    ).read_text(encoding="utf-8")

    assert "load_current_snapshot_pointer" in source
    assert "load_activity_read_context" not in source
    assert "load_current_snapshot_graph" not in source
    assert "load_current_record_graph" not in source


def test_render_input_preparation_is_zero_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan(tmp_path)
    working = tmp_path / "working"
    working.mkdir()
    monkeypatch.chdir(working)

    student_feedback_render_inputs_from_plan(plan)

    assert tuple(working.iterdir()) == ()
    assert not plan.destination.exists()
