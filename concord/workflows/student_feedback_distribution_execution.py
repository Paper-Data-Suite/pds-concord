
"""Literal-PREPARE execution orchestration for student feedback distribution."""

from __future__ import annotations

from pathlib import Path
from typing import Final

from concord.workflows.errors import ConcordWorkflowValidationError
from concord.workflows.student_feedback_distribution_package import (
    render_student_feedback_distribution_package,
)
from concord.workflows.student_feedback_distribution_plan import (
    PreparedStudentFeedbackDistribution,
    verify_student_feedback_distribution_plan_digest,
)
from concord.workflows.student_feedback_distribution_storage import (
    InstalledStudentFeedbackDistribution,
    install_staged_student_feedback_distribution,
    stage_student_feedback_distribution,
)

STUDENT_FEEDBACK_PREPARE_CONFIRMATION: Final[str] = "PREPARE"


def execute_student_feedback_distribution(
    plan: PreparedStudentFeedbackDistribution,
    *,
    confirmation: str,
    workspace_root: str | Path,
    created_at: str,
) -> InstalledStudentFeedbackDistribution:
    """Execute one already-reviewed distribution after exact PREPARE."""
    if confirmation != STUDENT_FEEDBACK_PREPARE_CONFIRMATION:
        raise ConcordWorkflowValidationError(
            "Student feedback distribution requires the exact confirmation PREPARE."
        )

    verify_student_feedback_distribution_plan_digest(plan)
    package = render_student_feedback_distribution_package(
        plan,
        created_at=created_at,
    )
    staged = stage_student_feedback_distribution(
        plan,
        package,
        workspace_root=workspace_root,
    )
    return install_staged_student_feedback_distribution(
        plan,
        staged,
    )


__all__ = [
    "STUDENT_FEEDBACK_PREPARE_CONFIRMATION",
    "execute_student_feedback_distribution",
]
