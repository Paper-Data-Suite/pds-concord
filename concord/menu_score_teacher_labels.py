"""Read-only, best-effort teacher labels for exact Score identities.

All displayed names are optional projections. Missing or conflicting labels never
change the underlying canonical Score target, Criterion, Scale, or Session ID.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import NoReturn

from pds_core.classes import load_class_roster
from pds_core.rosters import student_display_name

from concord.menu_standards_context import standards_for_activity
from concord.menu_teacher_history import distinguish_equal_labels
from concord.workflows import (
    ActivitySummary,
    ConcordWorkflowConflictError,
    ConcordWorkflowValidationError,
    list_criterion_sets,
    list_groups,
    list_scoring_scales,
    list_sessions,
    resolve_read_workspace_root,
    show_criterion_set,
)
from concord.workflows.teacher_artifact_choices import list_teacher_artifact_choices


@dataclass(frozen=True, slots=True)
class ScoreTeacherLabels:
    """Exact canonical keys, optional classroom-facing labels."""

    targets: dict[tuple[str, str], str] = field(default_factory=dict)
    sessions: dict[str, str] = field(default_factory=dict)
    criteria: dict[str, str] = field(default_factory=dict)
    scales: dict[str, str] = field(default_factory=dict)

    def target(self, kind: str, target_id: str) -> str:
        return self.targets.get(
            (kind, target_id),
            {
                "core_student": "Student name unavailable",
                "concord_group": "Group name unavailable",
                "concord_session": "Session name unavailable",
                "concord_artifact_instance": "Work label unavailable",
                "concord_activity": "Activity",
            }.get(kind, "Target label unavailable"),
        )

    def session(self, session_id: str | None) -> str:
        if session_id is None:
            return "No separate Session"
        return self.sessions.get(session_id, "Session label unavailable")

    def criterion(self, criterion_id: str) -> str:
        return self.criteria.get(criterion_id, "Criterion label unavailable")

    def scale(self, scale_id: str) -> str:
        return self.scales.get(scale_id, "Scoring Scale label unavailable")

    def require_target(self, kind: str, target_id: str) -> str:
        """Refuse a consequential Score decision on an unknown exact target."""
        return _required_label(
            self.targets.get((kind, target_id)), "Score target"
        )

    def require_session(self, session_id: str | None) -> str:
        if session_id is None:
            return "No separate Session"
        return _required_label(self.sessions.get(session_id), "Score Session")

    def require_criterion(self, criterion_id: str) -> str:
        return _required_label(self.criteria.get(criterion_id), "Score Criterion")

    def require_scale(self, scale_id: str) -> str:
        return _required_label(self.scales.get(scale_id), "Scoring Scale")


def _required_label(label: str | None, source: str) -> str:
    """Validate display identity without exposing sensitive canonical IDs."""
    if (
        label is None
        or not label.strip()
        or label.startswith("Criterion label ambiguous across revisions")
    ):
        raise ConcordWorkflowValidationError(
            f"{source} label is missing or ambiguous. "
            "Reopen the Activity and inspect the current records before "
            "confirming or revising a Score; no Score was recorded."
        )
    return label


def _label_unique(
    keys: tuple[str, ...], names: tuple[str, ...], noun: str
) -> dict[str, str]:
    return dict(
        zip(
            keys,
            distinguish_equal_labels(names, noun=noun),
            strict=True,
        )
    )


def _raise_label_read_failure(source: str, error: Exception) -> NoReturn:
    """Fail closed without exposing lower-level paths or student information."""
    if isinstance(error, ConcordWorkflowConflictError):
        raise ConcordWorkflowConflictError(
            f"{source} labels could not be verified because the Activity "
            "changed. Reopen the Activity and retry; no Score was recorded."
        ) from error
    raise ConcordWorkflowValidationError(
        f"{source} labels could not be verified from authoritative records. "
        "Reopen the Activity or repair the source before scoring; "
        "no Score was recorded."
    ) from error


def build_score_teacher_labels(
    activity: ActivitySummary,
    *,
    include_score_definitions: bool = False,
) -> ScoreTeacherLabels:
    """Read teacher labels with a pinned workspace and real Standards context.

    A failed canonical read is not equivalent to a missing human display name.
    Never silently omit an entire identity family on exception. The optional
    missing-workspace fallback is retained only for legacy, summary-only
    inspection; Score history and revision require an actual workspace.
    """
    targets: dict[tuple[str, str], str] = {
        ("concord_activity", activity.activity_id): activity.title,
    }
    sessions: dict[str, str] = {}
    criteria: dict[str, str] = {}
    scales: dict[str, str] = {}

    root = resolve_read_workspace_root()
    if root is None:
        if include_score_definitions:
            raise ConcordWorkflowValidationError(
                "Scoring labels require the selected Paper Data Suite workspace. "
                "Select the workspace and reopen the Activity; no Score was recorded."
            )
        return ScoreTeacherLabels(targets, sessions, criteria, scales)

    # Standards-bearing graph readers must use the same Core library as writes.
    # Never interpret a missing required library as an empty assessment.
    library = standards_for_activity(activity)

    try:
        groups = tuple(
            sorted(
                list_groups(
                    activity.class_id, activity.activity_id, workspace_root=root
                ),
                key=lambda item: item.group_id,
            )
        )
        names = _label_unique(
            tuple(item.group_id for item in groups),
            tuple(item.label for item in groups),
            "Group",
        )
        targets.update(
            (("concord_group", group_id), label)
            for group_id, label in names.items()
        )
    except Exception as error:
        _raise_label_read_failure("Cluster Group", error)

    try:
        for item in list_sessions(
            activity.class_id, activity.activity_id, workspace_root=root
        ):
            label = f"Session {item.sequence}"
            if item.label:
                label += f" - {item.label}"
            sessions[item.session_id] = label
            targets[("concord_session", item.session_id)] = label
    except Exception as error:
        _raise_label_read_failure("Session", error)

    try:
        choices = list_teacher_artifact_choices(
            activity.class_id,
            activity.activity_id,
            expected_snapshot_revision=activity.snapshot_revision,
            workspace_root=root,
            standards_library=library,
        )
        targets.update(
            (
                ("concord_artifact_instance", choice.summary.artifact_instance_id),
                choice.label,
            )
            for choice in choices
        )
    except Exception as error:
        _raise_label_read_failure("Returned work", error)

    try:
        roster = load_class_roster(root, activity.class_id)
        students = tuple(
            sorted(roster.students, key=lambda student: student.student_id)
        )
        names = _label_unique(
            tuple(student.student_id for student in students),
            tuple(student_display_name(student) for student in students),
            "Student",
        )
        targets.update(
            (("core_student", student_id), name)
            for student_id, name in names.items()
        )
    except Exception as error:
        _raise_label_read_failure("Core student roster", error)

    if include_score_definitions:
        try:
            scale_items = list_scoring_scales(
                activity.class_id,
                activity.activity_id,
                workspace_root=root,
                standards_library=library,
                current_only=False,
            )
            ordered_scales = tuple(
                sorted(scale_items, key=lambda item: item.scoring_scale_id)
            )
            scales.update(
                _label_unique(
                    tuple(item.scoring_scale_id for item in ordered_scales),
                    tuple(item.name for item in ordered_scales),
                    "Scoring Scale",
                )
            )
        except Exception as error:
            _raise_label_read_failure("Scoring Scale", error)

        try:
            for criterion_set_item in list_criterion_sets(
                activity.class_id,
                activity.activity_id,
                workspace_root=root,
                standards_library=library,
                current_only=False,
            ):
                detail = show_criterion_set(
                    activity.class_id,
                    activity.activity_id,
                    criterion_set_item.criterion_set_id,
                    workspace_root=root,
                    standards_library=library,
                )
                for criterion in detail.criteria:
                    existing = criteria.get(criterion.criterion_id)
                    if existing is None:
                        criteria[criterion.criterion_id] = criterion.label
                    elif existing != criterion.label:
                        criteria[criterion.criterion_id] = (
                            "Criterion label ambiguous across revisions"
                        )
            ordered_criterion_ids = tuple(sorted(criteria))
            criteria = _label_unique(
                ordered_criterion_ids,
                tuple(criteria[key] for key in ordered_criterion_ids),
                "Criterion",
            )
        except Exception as error:
            _raise_label_read_failure("Criterion Set", error)

    return ScoreTeacherLabels(targets, sessions, criteria, scales)


__all__ = ["ScoreTeacherLabels", "build_score_teacher_labels"]
