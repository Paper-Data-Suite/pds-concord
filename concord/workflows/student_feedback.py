"""Share-safe student feedback projections from current Concord Scores."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from concord.academic_result_manifest import (
    ConcordAcademicResultManifestValidationError,
)
from concord.academic_result_manifest import (
    _public_text as _publication_public_text,
)
from concord.models import ScoreTargetReference
from concord.models.common import JsonScalar
from concord.workflows.activity_read import ActivityReadContext
from concord.workflows.activity_score_analysis import (
    SCORE_ANALYSIS_BASIS,
    TARGET_DETAIL_SCOPE,
    TargetScoreDetail,
    TargetScoreResult,
    target_score_detail_from_context,
)
from concord.workflows.errors import ConcordWorkflowValidationError

STUDENT_FEEDBACK_SCOPE: Final[str] = "student_scoped"
STUDENT_FEEDBACK_BOUNDARY_STATEMENT: Final[str] = (
    "This feedback describes current Concord Score observations for this Activity. "
    "It is not a Grade or standards-proficiency report."
)
_STUDENT_FEEDBACK_DISPOSITIONS: Final[frozenset[str]] = frozenset(
    {
        "scored",
        "insufficient_evidence",
        "absent",
        "excused",
        "not_observed",
        "not_applicable",
        "deferred",
    }
)


@dataclass(frozen=True, slots=True, kw_only=True)
class StudentFeedbackResult:
    """One allowlisted current Score observation for student-facing feedback."""

    criterion_label: str
    scoring_scale_name: str
    disposition: str
    value: JsonScalar | None
    value_label: str | None


@dataclass(frozen=True, slots=True, kw_only=True)
class StudentFeedbackProjection:
    """Privacy-minimized feedback for one exact Core-rostered student."""

    student_display_name: str
    activity_title: str
    class_label: str | None
    boundary_statement: str
    results: tuple[StudentFeedbackResult, ...]

    @property
    def current_score_count(self) -> int:
        """Return the represented current student-target Score count."""
        return len(self.results)


def _share_safe_text(value: object, field: str) -> str:
    """Apply Concord's existing publication-safe public-text policy."""
    try:
        return _publication_public_text(value, field)
    except ConcordAcademicResultManifestValidationError as error:
        raise ConcordWorkflowValidationError(
            f"Student feedback cannot safely represent {field}."
        ) from error


def _share_safe_scalar(
    value: JsonScalar | None,
    field: str,
) -> JsonScalar | None:
    if isinstance(value, str):
        return _share_safe_text(value, field)
    return value


def _require_student_target(target: ScoreTargetReference) -> None:
    if target.target_kind != "core_student" or target.owning_system != "core":
        raise ConcordWorkflowValidationError(
            "Student feedback requires an exact Core-owned core_student Score target."
        )


def _project_result(result: TargetScoreResult) -> StudentFeedbackResult:
    if result.disposition not in _STUDENT_FEEDBACK_DISPOSITIONS:
        raise ConcordWorkflowValidationError(
            "Student feedback encountered an unsupported Score disposition."
        )

    if result.disposition == "scored":
        if result.value is None or result.value_label is None:
            raise ConcordWorkflowValidationError(
                "Scored student feedback requires an exact Scale value and label."
            )
        value = _share_safe_scalar(result.value, "score.value")
        value_label = _share_safe_text(result.value_label, "scale_level.label")
    else:
        if result.value is not None or result.value_label is not None:
            raise ConcordWorkflowValidationError(
                "Non-score student feedback must not carry a Scale value."
            )
        value = None
        value_label = None

    return StudentFeedbackResult(
        criterion_label=_share_safe_text(
            result.criterion_label,
            "criterion.label",
        ),
        scoring_scale_name=_share_safe_text(
            result.scoring_scale_name,
            "scoring_scale.name",
        ),
        disposition=result.disposition,
        value=value,
        value_label=value_label,
    )


def student_feedback_projection_from_target_detail(
    detail: TargetScoreDetail,
    *,
    student_display_name: str,
    class_label: str | None = None,
) -> StudentFeedbackProjection:
    """Allowlist one #123 teacher-local Target Detail into student feedback."""
    _require_student_target(detail.target_reference)
    if detail.score_basis != SCORE_ANALYSIS_BASIS:
        raise ConcordWorkflowValidationError(
            "Student feedback requires current Score lineage-head semantics."
        )
    if detail.sharing_scope != TARGET_DETAIL_SCOPE:
        raise ConcordWorkflowValidationError(
            "Student feedback must derive from the established Target Detail boundary."
        )
    if detail.current_score_count != len(detail.results):
        raise ConcordWorkflowValidationError(
            "Student feedback source count does not match its current Score results."
        )

    safe_class_label = (
        None
        if class_label is None
        else _share_safe_text(class_label, "class.label")
    )
    results = tuple(_project_result(item) for item in detail.results)
    return StudentFeedbackProjection(
        student_display_name=_share_safe_text(
            student_display_name,
            "student.display_name",
        ),
        activity_title=_share_safe_text(
            detail.activity_title,
            "activity_context.title",
        ),
        class_label=safe_class_label,
        boundary_statement=STUDENT_FEEDBACK_BOUNDARY_STATEMENT,
        results=results,
    )


def student_feedback_projection_from_context(
    context: ActivityReadContext,
    target_reference: ScoreTargetReference,
    *,
    student_display_name: str,
    class_label: str | None = None,
) -> StudentFeedbackProjection:
    """Project one exact current student target from one Activity read context."""
    _require_student_target(target_reference)
    detail = target_score_detail_from_context(
        context,
        target_reference,
    )
    return student_feedback_projection_from_target_detail(
        detail,
        student_display_name=student_display_name,
        class_label=class_label,
    )


__all__ = [
    "STUDENT_FEEDBACK_BOUNDARY_STATEMENT",
    "STUDENT_FEEDBACK_SCOPE",
    "StudentFeedbackProjection",
    "StudentFeedbackResult",
    "student_feedback_projection_from_context",
    "student_feedback_projection_from_target_detail",
]
