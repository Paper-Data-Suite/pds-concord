
"""Read-only opening of exact verified student feedback distribution outputs."""

from __future__ import annotations

from pathlib import Path

from pds_core.local_open import LocalOpenError, open_local_path

from concord.workflows.errors import ConcordWorkflowOpenError
from concord.workflows.student_feedback_distribution_plan import (
    FEEDBACK_PRINT_FILENAME,
)
from concord.workflows.student_feedback_distribution_storage import (
    VerifiedStudentFeedbackDistribution,
    verify_student_feedback_distribution_directory,
)


def _open_verified_distribution_path(
    path: Path,
    *,
    target_label: str,
) -> None:
    try:
        open_local_path(path)
    except LocalOpenError as error:
        raise ConcordWorkflowOpenError(
            f"Concord verified the {target_label}, but the system could not "
            "open it with the default application."
        ) from error


def open_student_feedback_distribution_directory(
    directory: str | Path,
    *,
    expected_plan_digest: str | None = None,
    expected_package_digest: str | None = None,
) -> VerifiedStudentFeedbackDistribution:
    """Verify one exact distribution package, then open its folder."""
    verified = verify_student_feedback_distribution_directory(
        directory,
        expected_plan_digest=expected_plan_digest,
        expected_package_digest=expected_package_digest,
    )
    _open_verified_distribution_path(
        verified.directory,
        target_label="student feedback distribution folder",
    )
    return verified


def open_student_feedback_distribution_print_pdf(
    directory: str | Path,
    *,
    expected_plan_digest: str | None = None,
    expected_package_digest: str | None = None,
) -> VerifiedStudentFeedbackDistribution:
    """Verify one exact package, then open only its fixed class-print PDF."""
    verified = verify_student_feedback_distribution_directory(
        directory,
        expected_plan_digest=expected_plan_digest,
        expected_package_digest=expected_package_digest,
    )
    print_pdf = verified.directory / FEEDBACK_PRINT_FILENAME
    _open_verified_distribution_path(
        print_pdf,
        target_label="student feedback class print PDF",
    )
    return verified


__all__ = [
    "open_student_feedback_distribution_directory",
    "open_student_feedback_distribution_print_pdf",
]
