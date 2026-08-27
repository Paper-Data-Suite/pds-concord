"""Concise default formatting for direct Concord commands."""

from __future__ import annotations

from concord.models import ConcordRecordReference, ParticipantReference, Session
from concord.workflows import (
    ActivityDetail,
    ActivitySummary,
    GroupDetail,
    GroupSummary,
    MembershipSummary,
    PreparedActivityCopy,
    ResponsibilitySummary,
    RoleSummary,
    SessionSummary,
    WorkflowCommitResult,
)


def print_commit(result: WorkflowCommitResult) -> None:
    if result.workspace_created:
        print("Created Paper Data Suite workspace.")
    if result.no_op:
        print("No changes were needed.")
    else:
        print(f"Committed snapshot {result.snapshot_revision}.")
    print(f"Activity: {result.work.work_id}")
    print(f"Snapshot SHA-256: {result.snapshot_sha256}")
    if result.changed_records:
        changed = ", ".join(
            f"{item.record_kind}:{item.record_id}@{item.record_revision}"
            for item in result.changed_records
        )
        print(f"Changed: {changed}")


def print_activity_copy_preview(item: PreparedActivityCopy) -> None:
    print(
        f"Source Activity: {item.source_class_id}/{item.source_activity_id}"
    )
    print(f"Source status: {item.source_status}")
    print(
        f"Target Activity: {item.target_class_id}/{item.target_activity_id}"
    )
    print("Target status: draft")
    print(f"Title: {item.title}")
    print(f"Description: {item.description if item.description is not None else '-'}")
    print(f"Activity type: {item.activity_type}")
    print(f"Scoring orientation: {item.scoring_orientation}")
    print(f"Standards profile: {item.standards_profile_id or '-'}")
    print(
        "Focus standards: "
        + (", ".join(item.focus_standard_ids) if item.focus_standard_ids else "-")
    )
    classification = (
        item.privacy_policy.classification
        if item.privacy_policy is not None
        else "none"
    )
    print(f"Target privacy: {classification}")
    print(
        f"First Session: {item.first_session_id}"
        + (f" ({item.first_session_label})" if item.first_session_label else "")
    )
    if item.diagnostics:
        print("Diagnostics:")
        for diagnostic in item.diagnostics:
            print(f"- {diagnostic.code}: {diagnostic.message}")
    print("Will not copy:")
    for excluded in item.excluded_state:
        print(f"- {excluded}")
    print(f"Review digest: {item.review_digest}")


def print_activity_summary(item: ActivitySummary) -> None:
    print(
        f"{item.class_id}\t{item.activity_id}\t{item.status}\t"
        f"sessions={item.session_count}\tgroups={item.group_count}\t"
        f"snapshot={item.snapshot_revision}\t{item.title}"
    )


def print_activity_detail(detail: ActivityDetail) -> None:
    item = detail.summary
    print(f"Class: {item.class_id}")
    print(f"Activity: {item.activity_id}")
    print(f"Title: {item.title}")
    print(f"Status: {item.status}")
    print(f"Activity type: {detail.activity_type}")
    print(f"Scoring orientation: {item.scoring_orientation}")
    print(f"Sessions: {item.session_count}")
    print(f"Groups: {item.group_count}")
    print(f"Snapshot revision: {item.snapshot_revision}")
    if detail.description is not None:
        print(f"Description: {detail.description}")
    if detail.standards_profile_id is not None:
        print(f"Standards profile: {detail.standards_profile_id}")
        print(f"Focus standards: {', '.join(detail.focus_standard_ids)}")


def print_session_summary(item: SessionSummary) -> None:
    label = item.label or "-"
    start = item.scheduled_start or "-"
    print(
        f"{item.sequence}\t{item.session_id}\t{item.status}\t{start}\t"
        f"{label}\tsnapshot={item.snapshot_revision}"
    )


def print_session_detail(item: Session) -> None:
    print(f"Session: {item.session_id}")
    print(f"Activity: {item.activity_id}")
    print(f"Sequence: {item.sequence}")
    print(f"Status: {item.status}")
    if item.label is not None:
        print(f"Label: {item.label}")
    if item.scheduled_start is not None:
        print(f"Scheduled start: {item.scheduled_start}")
    if item.scheduled_end is not None:
        print(f"Scheduled end: {item.scheduled_end}")
    if item.actual_start is not None:
        print(f"Actual start: {item.actual_start}")
    if item.actual_end is not None:
        print(f"Actual end: {item.actual_end}")
    if item.notes is not None:
        print(f"Notes: {item.notes}")


def print_group_summary(item: GroupSummary) -> None:
    print(
        f"{item.group_id}\t{item.status}\tmembers={item.member_count}\t"
        f"sessions={item.effective_session_count}\tparent="
        f"{item.parent_group_id or '-'}\t{item.label}\t"
        f"snapshot={item.snapshot_revision}"
    )


def print_group_detail(detail: GroupDetail) -> None:
    item = detail.summary
    print(f"Group: {item.group_id}")
    print(f"Activity: {item.activity_id}")
    print(f"Label: {item.label}")
    print(f"Status: {item.status}")
    print(f"Members: {item.member_count}")
    print(f"Snapshot revision: {item.snapshot_revision}")
    if item.parent_group_id is not None:
        print(f"Parent Group: {item.parent_group_id}")
    if detail.description is not None:
        print(f"Description: {detail.description}")
    if detail.effective_context is not None:
        print(f"Sessions: {', '.join(detail.effective_context.session_ids)}")


def print_membership(item: MembershipSummary) -> None:
    label = item.participant_display_label or item.participant_reference.participant_id
    print(
        f"{item.membership_id}\tgroup={item.group_id}\t{item.status}\t"
        f"participant={label} ({item.participant_reference.participant_id})\t"
        f"sessions={','.join(item.effective_context.session_ids)}\t"
        f"snapshot={item.snapshot_revision}"
    )


def print_role(item: RoleSummary) -> None:
    label = item.participant_display_label or item.participant_reference.participant_id
    print(
        f"{item.role_assignment_id}\t{item.role_key}\t{item.status}\t"
        f"participant={label} ({item.participant_reference.participant_id})\t"
        f"group={item.group_id or '-'}\tsnapshot={item.snapshot_revision}"
    )


def _assignee_id(reference: ParticipantReference | ConcordRecordReference) -> str:
    if isinstance(reference, ParticipantReference):
        return reference.participant_id
    return reference.record_id


def print_responsibility(item: ResponsibilitySummary) -> None:
    label = item.assignee_display_label or _assignee_id(item.assignee_reference)
    print(
        f"{item.responsibility_assignment_id}\t{item.status}\tassignee={label}\t"
        f"group={item.group_id or '-'}\t{item.description}\t"
        f"snapshot={item.snapshot_revision}"
    )
