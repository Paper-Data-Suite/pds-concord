
"""Direct noninteractive Student Feedback Distribution commands."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from pds_core.routing_models import ModuleWorkRef

from concord.cli_app.common import workspace_arg
from concord.pds_contract import CONCORD_MODULE_ID
from concord.workflows import (
    FEEDBACK_SELECTION_ALL,
    FEEDBACK_SELECTION_SELECTED,
    ConcordWorkflowConflictError,
    PreparedStudentFeedbackDistribution,
    StudentFeedbackDistributionPreview,
    execute_student_feedback_distribution,
    load_student_feedback_roster_preparation,
    prepare_student_feedback_distribution_plan,
    preview_student_feedback_distribution,
    verify_student_feedback_distribution_directory,
)
from concord.workflows.activity_read import load_activity_read_context
from concord.workflows.context import resolve_read_workspace_root


def _root(args: argparse.Namespace) -> Path:
    root = resolve_read_workspace_root(workspace_arg(args))
    if root is None:
        raise FileNotFoundError("Paper Data Suite workspace does not exist.")
    return Path(root)


def _created_at() -> str:
    return datetime.now(timezone.utc).isoformat()


def _selection(
    args: argparse.Namespace,
) -> tuple[str, tuple[str, ...]]:
    if args.all_roster:
        return FEEDBACK_SELECTION_ALL, ()
    return FEEDBACK_SELECTION_SELECTED, tuple(args.student_id or ())


def _preview_and_plan(
    args: argparse.Namespace,
) -> tuple[
    Path,
    StudentFeedbackDistributionPreview,
    PreparedStudentFeedbackDistribution,
]:
    root = _root(args)
    context = load_activity_read_context(
        root,
        ModuleWorkRef(
            module_id=CONCORD_MODULE_ID,
            class_id=args.class_id,
            work_id=args.activity_id,
        ),
    )
    preparation = load_student_feedback_roster_preparation(context)
    selection_mode, student_ids = _selection(args)
    preview = preview_student_feedback_distribution(
        preparation,
        selection_mode=selection_mode,
        selected_student_ids=student_ids,
    )
    plan = prepare_student_feedback_distribution_plan(
        preview,
        destination=args.destination,
        authorize_available_only=args.available_only,
    )
    return root, preview, plan


def _print_preview(
    preview: StudentFeedbackDistributionPreview,
    plan: PreparedStudentFeedbackDistribution,
) -> None:
    print(f"Class: {preview.class_id}")
    print(f"Activity: {preview.activity_title}")
    print(f"Roster students: {preview.roster_count}")
    print(f"Distributable feedback: {preview.distributable_count}")
    print(f"No distributable feedback: {preview.no_feedback_count}")
    print(f"Unresolved: {preview.unresolved_count}")
    print(f"Requested students: {preview.requested_count}")
    print(f"Selected for distribution: {preview.selected_for_output_count}")
    print(f"Destination: {plan.destination}")
    print(f"Managed outputs: {len(plan.output_filenames)}")
    print(f"Review digest: {plan.plan_digest}")
    if plan.available_only_authorized:
        print("Available-only omission: explicitly authorized")
    print("Academic Result publication: unchanged")
    print("Delivery state: not recorded")


def handle_distribution_preview(args: argparse.Namespace) -> int:
    """Prepare and print one exact zero-write reviewed distribution plan."""
    _root_value, preview, plan = _preview_and_plan(args)
    _print_preview(preview, plan)
    return 0


def handle_distribution_prepare(args: argparse.Namespace) -> int:
    """Execute only the exact current plan reviewed by distribution-preview."""
    root, _preview, plan = _preview_and_plan(args)
    if plan.plan_digest != args.review_digest:
        raise ConcordWorkflowConflictError(
            "Student feedback review digest does not match the current exact plan. "
            "Run feedback distribution-preview again and review the changed plan."
        )

    result = execute_student_feedback_distribution(
        plan,
        confirmation=args.confirmation,
        workspace_root=root,
        created_at=_created_at(),
    )
    print(f"Disposition: {result.action}")
    print(f"Destination: {result.directory}")
    print(f"Feedback files: {result.verification.selected_count}")
    print(f"Class print pages: {result.verification.combined_page_count}")
    print(f"Review digest: {result.verification.plan_digest}")
    print(f"Package digest: {result.verification.package_digest}")
    print("Delivery state: not recorded")
    return 0


def handle_distribution_verify(args: argparse.Namespace) -> int:
    """Verify one existing distribution package without source-state mutation."""
    verified = verify_student_feedback_distribution_directory(args.directory)
    print("Verification: passed")
    print(f"Directory: {verified.directory}")
    print(f"Schema: {verified.schema_version}")
    print(f"Feedback files: {verified.selected_count}")
    print(f"Class print pages: {verified.combined_page_count}")
    print(f"Review digest: {verified.plan_digest}")
    print(f"Package digest: {verified.package_digest}")
    print("Delivery state: not recorded")
    return 0


__all__ = [
    "handle_distribution_prepare",
    "handle_distribution_preview",
    "handle_distribution_verify",
]
