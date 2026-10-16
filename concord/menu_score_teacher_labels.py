"""Read-only, best-effort teacher labels for exact Score identities.

All displayed names are optional projections. Missing or conflicting labels never
change the underlying canonical Score target, Criterion, Scale, or Session ID.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pds_core.classes import load_class_roster
from pds_core.rosters import student_display_name

from concord.menu_teacher_history import distinguish_equal_labels
from concord.workflows import (
    ActivitySummary,
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


def build_score_teacher_labels(
    activity: ActivitySummary,
    *,
    include_score_definitions: bool = False,
) -> ScoreTeacherLabels:
    """Build once per screen, never per Score history row.

    These are display-only reads. The canonical Score APIs are authoritative for
    permission, state, currentness, and identity. A failed display read yields
    an explicit unavailable label, never a guessed or exposed identifier.
    """
    targets: dict[tuple[str, str], str] = {
        ("concord_activity", activity.activity_id): activity.title,
    }
    sessions: dict[str, str] = {}
    criteria: dict[str, str] = {}
    scales: dict[str, str] = {}
    try:
        groups = tuple(sorted(
            list_groups(activity.class_id, activity.activity_id),
            key=lambda item: item.group_id,
        ))
        names = _label_unique(
            tuple(item.group_id for item in groups),
            tuple(item.label for item in groups),
            "Group",
        )
        targets.update(
            (("concord_group", group_id), label)
            for group_id, label in names.items()
        )
    except Exception:
        pass
    try:
        for item in list_sessions(activity.class_id, activity.activity_id):
            label = f"Session {item.sequence}"
            if item.label:
                label += f" - {item.label}"
            sessions[item.session_id] = label
            targets[("concord_session", item.session_id)] = label
    except Exception:
        pass
    try:
        choices = list_teacher_artifact_choices(
            activity.class_id,
            activity.activity_id,
            expected_snapshot_revision=activity.snapshot_revision,
        )
        targets.update(
            (("concord_artifact_instance", choice.summary.artifact_instance_id),
             choice.label)
            for choice in choices
        )
    except Exception:
        pass
    try:
        root = resolve_read_workspace_root()
        if root is not None:
            roster = load_class_roster(root, activity.class_id)
            students = tuple(sorted(
                roster.students, key=lambda student: student.student_id
            ))
            names = _label_unique(
                tuple(student.student_id for student in students),
                tuple(student_display_name(student) for student in students),
                "Student",
            )
            targets.update(
                (("core_student", student_id), name)
                for student_id, name in names.items()
            )
    except Exception:
        pass
    if include_score_definitions:
        try:
            for scale_item in list_scoring_scales(
                activity.class_id, activity.activity_id, current_only=False
            ):
                scales[scale_item.scoring_scale_id] = scale_item.name
        except Exception:
            pass
        try:
            for criterion_set_item in list_criterion_sets(
                activity.class_id, activity.activity_id, current_only=False
            ):
                detail = show_criterion_set(
                    activity.class_id,
                    activity.activity_id,
                    criterion_set_item.criterion_set_id,
                )
                for criterion in detail.criteria:
                    existing = criteria.get(criterion.criterion_id)
                    if existing is None:
                        criteria[criterion.criterion_id] = criterion.label
                    elif existing != criterion.label:
                        criteria[criterion.criterion_id] = (
                            "Criterion label ambiguous across revisions"
                        )
        except Exception:
            pass
    return ScoreTeacherLabels(targets, sessions, criteria, scales)


__all__ = ["ScoreTeacherLabels", "build_score_teacher_labels"]
