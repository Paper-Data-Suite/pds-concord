"""Read-only derived setup status for the guided classroom Activity workflow."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pds_core.standards import StandardsLibrary

from concord.workflows.activity import show_activity
from concord.workflows.criterion_sets import list_criterion_sets
from concord.workflows.group import list_groups
from concord.workflows.group_plan import list_group_plans
from concord.workflows.packet_instance import list_packet_instances
from concord.workflows.responsibility import list_responsibilities
from concord.workflows.role import list_roles
from concord.workflows.session import list_sessions

SetupStatus = Literal["ready", "needs_attention", "not_set_up", "not_used"]


@dataclass(frozen=True, slots=True, kw_only=True)
class GuidedSetupArea:
    """One teacher-facing setup area derived from canonical Concord state."""

    key: str
    label: str
    status: SetupStatus
    detail: str


@dataclass(frozen=True, slots=True, kw_only=True)
class GuidedActivitySetup:
    """Current setup picture for one Activity; never persisted as workflow state."""

    class_id: str
    activity_id: str
    title: str
    areas: tuple[GuidedSetupArea, ...]

    def area(self, key: str) -> GuidedSetupArea:
        for item in self.areas:
            if item.key == key:
                return item
        raise KeyError(key)

    def recommended_area(self) -> GuidedSetupArea | None:
        """Return the next incomplete teacher-facing area, if one exists."""
        priority = ("session", "groups", "assignments", "assessment", "materials")
        by_key = {item.key: item for item in self.areas}
        for status in ("needs_attention", "not_set_up"):
            for key in priority:
                item = by_key.get(key)
                if item is not None and item.status == status:
                    return item
        return None


_STATUS_LABELS: dict[SetupStatus, str] = {
    "ready": "Ready",
    "needs_attention": "Needs attention",
    "not_set_up": "Not set up",
    "not_used": "Not used",
}


def setup_status_label(status: SetupStatus) -> str:
    """Return stable teacher-facing wording for one derived setup status."""
    return _STATUS_LABELS[status]


def activity_type_label(value: str) -> str:
    """Translate built-in Activity types without exposing raw enum keys."""
    return {
        "socratic_seminar": "Discussion / seminar",
        "laboratory": "Lab / investigation",
        "project": "Project / collaborative work",
    }.get(value, "Other classroom activity")


def scoring_orientation_label(value: str) -> str:
    """Translate scoring orientation into teacher-facing classroom language."""
    return {
        "evidence_only": "Collect evidence without scoring",
        "standards_based": "Standards-based assessment",
        "mixed": "Standards and local criteria",
        "local_criteria_only": "Local classroom criteria",
    }.get(value, "Assessment settings")


def inspect_guided_activity_setup(
    class_id: str,
    activity_id: str,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
) -> GuidedActivitySetup:
    """Derive resume status exclusively from existing canonical Activity records."""
    detail = show_activity(class_id, activity_id, workspace_root=workspace_root)
    sessions = list_sessions(class_id, activity_id, workspace_root=workspace_root)
    groups = list_groups(class_id, activity_id, workspace_root=workspace_root)
    group_plans = list_group_plans(
        class_id,
        activity_id,
        workspace_root=workspace_root,
    )
    roles = list_roles(class_id, activity_id, workspace_root=workspace_root)
    responsibilities = list_responsibilities(
        class_id,
        activity_id,
        workspace_root=workspace_root,
    )
    packets = list_packet_instances(
        class_id,
        activity_id,
        workspace_root=workspace_root,
    )
    criteria = list_criterion_sets(
        class_id,
        activity_id,
        workspace_root=workspace_root,
        standards_library=standards_library,
        current_only=True,
    )

    session_status: SetupStatus = "ready" if sessions else "needs_attention"
    materials_status: SetupStatus = "ready" if packets else "not_set_up"
    pending_plans = tuple(
        item
        for item in group_plans
        if item.status in {"draft", "previewed", "approved"}
    )
    if groups:
        group_status: SetupStatus = "ready"
        group_detail = f"{len(groups)} group(s) available."
    elif pending_plans:
        group_status = "needs_attention"
        if any(item.status == "approved" for item in pending_plans):
            group_detail = "A group plan is approved and ready to apply."
        elif any(item.status == "previewed" for item in pending_plans):
            group_detail = "A group plan is waiting for approval."
        else:
            group_detail = "A group plan is still being prepared."
    else:
        group_status = "not_set_up"
        group_detail = "No groups are set up for this Activity."

    assignment_status: SetupStatus = (
        "ready" if roles or responsibilities else "not_set_up"
    )
    if detail.summary.scoring_orientation == "evidence_only":
        assessment_status: SetupStatus = "not_used"
        assessment_detail = "This Activity collects evidence without Scores."
    else:
        selected = tuple(item for item in criteria if item.is_selected)
        assessment_status = "ready" if selected else "not_set_up"
        assessment_detail = (
            f"{len(selected)} assessment setup(s) selected."
            if selected
            else "Assessment criteria have not been selected yet."
        )

    areas = (
        GuidedSetupArea(
            key="activity",
            label="Activity basics",
            status="ready",
            detail=activity_type_label(detail.activity_type),
        ),
        GuidedSetupArea(
            key="session",
            label="Session",
            status=session_status,
            detail=(
                f"{len(sessions)} session(s) available."
                if sessions
                else "At least one Session is required."
            ),
        ),
        GuidedSetupArea(
            key="materials",
            label="Classroom materials",
            status=materials_status,
            detail=(
                f"{len(packets)} prepared packet set(s) available."
                if packets
                else "No classroom packet has been prepared yet."
            ),
        ),
        GuidedSetupArea(
            key="groups",
            label="Student groups",
            status=group_status,
            detail=group_detail,
        ),
        GuidedSetupArea(
            key="assignments",
            label="Roles and responsibilities",
            status=assignment_status,
            detail=(
                f"{len(roles)} role(s); {len(responsibilities)} responsibility item(s)."
                if roles or responsibilities
                else "No roles or responsibilities are assigned yet."
            ),
        ),
        GuidedSetupArea(
            key="assessment",
            label="Assessment",
            status=assessment_status,
            detail=assessment_detail,
        ),
    )
    return GuidedActivitySetup(
        class_id=detail.summary.class_id,
        activity_id=detail.summary.activity_id,
        title=detail.summary.title,
        areas=areas,
    )


__all__ = [
    "GuidedActivitySetup",
    "GuidedSetupArea",
    "SetupStatus",
    "activity_type_label",
    "inspect_guided_activity_setup",
    "scoring_orientation_label",
    "setup_status_label",
]
