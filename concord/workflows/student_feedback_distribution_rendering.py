
"""Last-safe-point and in-memory rendering inputs for student feedback."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pds_core.routing_models import ModuleWorkRef

from concord.storage import load_current_snapshot_pointer
from concord.workflows.errors import ConcordWorkflowConflictError
from concord.workflows.student_feedback import StudentFeedbackProjection
from concord.workflows.student_feedback_distribution_plan import (
    PreparedStudentFeedbackDistribution,
    verify_student_feedback_distribution_plan_digest,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class StudentFeedbackRenderInput:
    """One student-scoped rendering input with no canonical student identifier."""

    filename: str
    projection: StudentFeedbackProjection


@dataclass(frozen=True, slots=True, kw_only=True)
class PreparedStudentFeedbackRendering:
    """Deterministic in-memory rendering inputs from one reviewed plan."""

    plan_digest: str
    students: tuple[StudentFeedbackRenderInput, ...]


def student_feedback_render_inputs_from_plan(
    plan: PreparedStudentFeedbackDistribution,
) -> PreparedStudentFeedbackRendering:
    """Derive deterministic renderer inputs solely from the immutable plan."""
    verify_student_feedback_distribution_plan_digest(plan)
    students = tuple(
        StudentFeedbackRenderInput(
            filename=student.filename,
            projection=student.projection,
        )
        for student in plan.students
    )
    return PreparedStudentFeedbackRendering(
        plan_digest=plan.plan_digest,
        students=students,
    )


def require_student_feedback_plan_current(
    plan: PreparedStudentFeedbackDistribution,
    *,
    workspace_root: str | Path,
) -> PreparedStudentFeedbackDistribution:
    """Fail closed unless the reviewed Activity snapshot is still exact-current."""
    verify_student_feedback_distribution_plan_digest(plan)
    work = ModuleWorkRef(
        module_id="concord",
        class_id=plan.class_id,
        work_id=plan.activity_id,
    )
    current = load_current_snapshot_pointer(workspace_root, work)
    if (
        current.snapshot_revision != plan.expected_snapshot_revision
        or current.snapshot_sha256 != plan.expected_snapshot_sha256
    ):
        raise ConcordWorkflowConflictError(
            "Reviewed student feedback source is no longer current; "
            "review the changed feedback set before preparing output."
        )
    return plan


__all__ = [
    "PreparedStudentFeedbackRendering",
    "StudentFeedbackRenderInput",
    "require_student_feedback_plan_current",
    "student_feedback_render_inputs_from_plan",
]
