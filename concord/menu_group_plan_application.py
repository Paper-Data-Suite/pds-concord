"""Teacher-facing exact preview and application of approved GroupPlans."""

from __future__ import annotations

from concord.group_plan_application import ApplicationMembershipSpec
from concord.menu_context import MenuSessionContext
from concord.menu_prompts import (
    choose_effective_context,
    confirm_write,
    show_result,
)
from concord.menu_ui import clear_screen, pause_for_user, print_menu_header
from concord.models import EffectiveContext
from concord.workflows import (
    ApplyGroupPlanRequest,
    GroupPlanApplicationPreview,
    GroupPlanDetail,
    PrepareGroupPlanApplicationRequest,
    apply_group_plan,
    list_sessions,
    prepare_group_plan_application,
)


def _needs_fallback(detail: GroupPlanDetail) -> bool:
    return any(
        group.student_ids and group.effective_context is None
        for group in detail.plan.proposed_groups
    )


def _context_label(context: EffectiveContext | None) -> str:
    if context is None:
        return "none"
    sessions = ", ".join(context.session_ids)
    if context.applies_to_remaining_activity:
        return f"{sessions} (through remaining Activity)"
    return sessions


def _show_application_preview(preview: GroupPlanApplicationPreview) -> None:
    clear_screen()
    print_menu_header("GroupPlan Application Preview")
    print(f"GroupPlan: {preview.group_plan_id}")
    print(f"Application ID: {preview.application_id}")
    print(f"Application digest: {preview.application_digest}")
    print(f"Expected Activity snapshot: {preview.expected_snapshot_revision}")
    print(f"Canonical Groups to create: {preview.group_count}")
    print(f"Canonical Memberships to create: {preview.membership_count}")
    print(f"Students left without Membership: {preview.unresolved_count}")
    if preview.fallback_effective_context is not None:
        print(
            "Fallback Membership context: "
            f"{_context_label(preview.fallback_effective_context)}"
        )
    print()
    memberships_by_group: dict[str, list[ApplicationMembershipSpec]] = {}
    for preview_membership in preview.memberships:
        memberships_by_group.setdefault(
            preview_membership.group_id, []
        ).append(preview_membership)
    for group in preview.groups:
        print(f"{group.label} ({group.planned_group_key})")
        print(f"  Canonical Group ID: {group.group_id}")
        print(f"  Group context: {_context_label(group.effective_context)}")
        members = memberships_by_group.get(group.group_id, [])
        if not members:
            print("  Memberships: none")
        for member in members:
            print(f"  {member.student_id} -> {member.membership_id}")
            print(
                "    Membership context: "
                f"{_context_label(member.effective_context)}"
            )
    if preview.unresolved_student_ids:
        print()
        print("These roster students will receive no GroupMembership:")
        for student_id in preview.unresolved_student_ids:
            print(f"  {student_id}")
    print()
    print("No changes have been written.")
    print("All Groups, Memberships, and the applied GroupPlan will commit together.")
    print()


def apply_approved_group_plan_from_menu(
    detail: GroupPlanDetail,
    state: MenuSessionContext,
) -> None:
    """Preview and explicitly apply one approved GroupPlan."""

    if detail.plan.status != "approved":
        raise ValueError("Only an approved GroupPlan may be applied.")

    fallback: EffectiveContext | None = None
    if _needs_fallback(detail):
        sessions = list_sessions(detail.summary.class_id, detail.summary.activity_id)
        fallback = choose_effective_context(detail.summary.activity_id, sessions)

    preview = prepare_group_plan_application(
        PrepareGroupPlanApplicationRequest(
            class_id=detail.summary.class_id,
            activity_id=detail.summary.activity_id,
            group_plan_id=detail.summary.group_plan_id,
            fallback_effective_context=fallback,
        )
    )
    _show_application_preview(preview)
    pause_for_user()
    if not confirm_write(
        "Apply Approved GroupPlan",
        "APPLY",
        (
            f"GroupPlan: {preview.group_plan_id}",
            f"Application ID: {preview.application_id}",
            f"Application digest: {preview.application_digest}",
            f"Canonical Groups: {preview.group_count}",
            f"Canonical Memberships: {preview.membership_count}",
            f"Without Membership: {preview.unresolved_count}",
            "This is one atomic Activity update.",
        ),
    ):
        return

    result = apply_group_plan(
        ApplyGroupPlanRequest(
            class_id=preview.class_id,
            activity_id=preview.activity_id,
            group_plan_id=preview.group_plan_id,
            application_id=preview.application_id,
            application_digest=preview.application_digest,
            expected_snapshot_revision=preview.expected_snapshot_revision,
            actor=state.require_actor(),
            fallback_effective_context=preview.fallback_effective_context,
        )
    )
    show_result(
        "GroupPlan Application Result",
        (
            f"GroupPlan: {result.group_plan_id}",
            f"Status: {result.status}",
            f"Application ID: {result.application_id}",
            f"Application digest: {result.application_digest}",
            f"Groups created: {result.group_count}",
            f"Memberships created: {result.membership_count}",
            f"Students left unresolved: {result.unresolved_count}",
            f"Snapshot: {result.commit.snapshot_revision}",
        ),
    )


__all__ = ["apply_approved_group_plan_from_menu"]
