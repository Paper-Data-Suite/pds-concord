"""Direct CLI access to reviewed class-scoped grouping save and reuse (#136)."""

from __future__ import annotations

import argparse
from pathlib import Path

from concord.class_group_arrangement_storage import (
    list_current_arrangements,
    load_current_arrangement,
    review_arrangement_roster,
)
from concord.cli_app.common import (
    load_command_standards_library,
    workflow_actor,
    workspace_arg,
)
from concord.workflows.class_group_arrangements import (
    PreparedGroupingReuse,
    PreparedGroupingSave,
    ReuseGroupingRequest,
    SaveGroupingRequest,
    StudentPlacementDecision,
    prepare_reuse_grouping,
    prepare_save_grouping,
    reuse_grouping,
    save_grouping,
)
from concord.workflows.context import (
    require_core_class,
    resolve_read_workspace_root,
)
from concord.workflows.errors import (
    ConcordWorkflowNotFoundError,
    ConcordWorkflowValidationError,
)


def _scope(args: argparse.Namespace) -> tuple[str, Path]:
    """Require an existing workspace and authoritative class/year metadata."""
    root = resolve_read_workspace_root(workspace_arg(args))
    if root is None:
        raise ConcordWorkflowNotFoundError("Paper Data Suite workspace does not exist.")
    metadata = require_core_class(root, args.class_id)
    return metadata.school_year, root


def handle_list(args: argparse.Namespace) -> int:
    year, root = _scope(args)
    records = list_current_arrangements(
        root,
        class_id=args.class_id,
        school_year=year,
        actor_id=workflow_actor(args).actor_id,
    )
    if not records:
        print("No saved groupings found for this class and teacher.")
        return 0
    for item in records:
        record = item.revision
        print(
            f"{record.arrangement_id}\t{record.name}\t"
            f"revision={record.revision}\tstatus={record.status}\t"
            f"groups={len(record.groups)}\t"
            f"assigned={sum(len(g.student_ids) for g in record.groups)}\t"
            f"unresolved={len(record.unresolved_student_ids)}"
        )
    return 0


def handle_show(args: argparse.Namespace) -> int:
    year, root = _scope(args)
    saved = load_current_arrangement(
        root,
        class_id=args.class_id,
        school_year=year,
        arrangement_id=args.arrangement_id,
        actor_id=workflow_actor(args).actor_id,
    )
    revision = saved.revision
    print(f"Saved grouping: {revision.name}")
    print(f"Grouping ID: {revision.arrangement_id}")
    print(f"Class: {revision.class_id}")
    print(f"School year: {revision.school_year}")
    print(f"Revision: {revision.revision}")
    print(f"Status: {revision.status}")
    print(f"Roster students: {len(revision.roster_student_ids)}")
    print(f"Unresolved students: {len(revision.unresolved_student_ids)}")
    for group in revision.groups:
        print(f"Group: {group.label} ({group.key}); members={len(group.student_ids)}")
        if args.show_members:
            for student_id in group.student_ids:
                print(f"  Student ID: {student_id}")
    if args.show_members:
        for student_id in revision.unresolved_student_ids:
            print(f"  Unresolved student ID: {student_id}")
    print("No Activity-specific Group or Membership IDs are stored.")
    return 0


def handle_roster_diff(args: argparse.Namespace) -> int:
    """Read-only exact-ID difference check before requesting reuse decisions."""
    year, root = _scope(args)
    saved, difference = review_arrangement_roster(
        root,
        class_id=args.class_id,
        school_year=year,
        arrangement_id=args.arrangement_id,
        actor_id=workflow_actor(args).actor_id,
    )
    print(f"Saved grouping: {saved.revision.name}")
    print(f"Revision: {saved.revision.revision}")
    print(f"Retained assigned students: {difference.retained_assigned_count}")
    print(f"New student IDs: {', '.join(difference.newly_enrolled_ids) or '-'}")
    print(f"Departed student IDs: {', '.join(difference.departed_ids) or '-'}")
    print(f"Previously unresolved IDs: {', '.join(difference.unresolved_ids) or '-'}")
    print("Exact placement/acknowledgment decisions are required for changes.")
    print("Writes: none")
    return 0


def _save_request(args: argparse.Namespace) -> SaveGroupingRequest:
    return SaveGroupingRequest(
        class_id=args.class_id,
        activity_id=args.activity_id,
        group_plan_id=args.group_plan_id,
        arrangement_id=args.arrangement_id,
        name=args.name,
        expected_snapshot_revision=args.expected_snapshot,
        actor=workflow_actor(args),
    )


def _show_save_preview(preview: PreparedGroupingSave) -> None:
    print(f"Saved grouping name: {preview.name}")
    print(f"Grouping ID: {preview.arrangement_id}")
    print(f"Source Activity: {preview.source_activity_id}")
    print(f"Source GroupPlan: {preview.source_plan_id}")
    print(f"Groups: {len(preview.groups)}")
    print(f"Assigned: {preview.assigned_count}")
    print(f"Unresolved: {len(preview.unresolved_student_ids)}")
    for group in preview.groups:
        print(f"  {group.label}: {len(group.student_ids)} students")
    print(f"Review digest: {preview.review_digest}")
    print("Writes: none")


def handle_save_preview(args: argparse.Namespace) -> int:
    preview = prepare_save_grouping(
        _save_request(args), workspace_root=workspace_arg(args)
    )
    _show_save_preview(preview)
    return 0


def handle_save(args: argparse.Namespace) -> int:
    saved = save_grouping(
        _save_request(args),
        review_digest=args.review_digest,
        workspace_root=workspace_arg(args),
    )
    print(f"Saved grouping: {saved.revision.name}")
    print(f"Grouping ID: {saved.revision.arrangement_id}")
    print(f"Revision: {saved.revision.revision}")
    print(f"SHA-256: {saved.sha256}")
    print("Source Activity unchanged: yes")
    return 0


def _reuse_request(args: argparse.Namespace) -> ReuseGroupingRequest:
    choices: list[StudentPlacementDecision] = []
    seen: set[str] = set()
    for raw in args.place or ():
        if raw.count("=") != 1:
            raise ConcordWorkflowValidationError(
                "--place expects STUDENT_ID=GROUP_KEY."
            )
        student_id, group_key = raw.split("=", 1)
        if not student_id or not group_key:
            raise ConcordWorkflowValidationError(
                "--place requires nonempty student and group keys."
            )
        if student_id in seen:
            raise ConcordWorkflowValidationError(
                "Multiple decisions for one student are not permitted."
            )
        seen.add(student_id)
        choices.append(
            StudentPlacementDecision(student_id=student_id, group_key=group_key)
        )
    for student_id in args.leave_unresolved or ():
        if student_id in seen:
            raise ConcordWorkflowValidationError(
                "Multiple decisions for one student are not permitted."
            )
        seen.add(student_id)
        choices.append(StudentPlacementDecision(student_id=student_id, group_key=None))
    return ReuseGroupingRequest(
        class_id=args.class_id,
        activity_id=args.activity_id,
        arrangement_id=args.arrangement_id,
        new_group_plan_id=args.new_group_plan_id,
        expected_snapshot_revision=args.expected_snapshot,
        actor=workflow_actor(args),
        placement_decisions=tuple(choices),
        acknowledged_departed_student_ids=tuple(args.acknowledge_departed or ()),
        acknowledge_existing_plans=args.acknowledge_existing_plans,
    )


def _show_reuse_preview(
    preview: PreparedGroupingReuse, *, show_placements: bool = False
) -> None:
    print(f"Saved grouping: {preview.arrangement_id}")
    print(f"Revision: {preview.arrangement_revision}")
    print(f"Target Activity: {preview.target_activity_id}")
    print(f"New GroupPlan: {preview.new_group_plan_id}")
    print(f"Groups: {len(preview.groups)}")
    print(f"Assigned: {preview.assigned_count}")
    print(f"Unresolved: {len(preview.unresolved_student_ids)}")
    print(f"New student IDs: {', '.join(preview.added_student_ids) or '-'}")
    print(f"Departed student IDs: {', '.join(preview.departed_student_ids) or '-'}")
    for group in preview.groups:
        print(
            f"  {group.label} ({group.planned_group_key}): "
            f"{len(group.student_ids)} students"
        )
        if show_placements:
            for student_id in group.student_ids:
                print(f"    Student ID: {student_id}")
    if show_placements:
        for student_id in preview.unresolved_student_ids:
            print(f"    Unresolved student ID: {student_id}")
    print(f"Review digest: {preview.review_digest}")
    print("Creates canonical Groups/Memberships: no")
    print("Writes: none")


def handle_reuse_preview(args: argparse.Namespace) -> int:
    preview = prepare_reuse_grouping(
        _reuse_request(args), workspace_root=workspace_arg(args)
    )
    _show_reuse_preview(preview, show_placements=args.show_placements)
    return 0


def handle_reuse(args: argparse.Namespace) -> int:
    result = reuse_grouping(
        _reuse_request(args),
        review_digest=args.review_digest,
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print(f"New draft GroupPlan: {result.group_plan_id}")
    print(f"Status: {result.status}")
    print(f"Activity snapshot: {result.commit.snapshot_revision}")
    print("Canonical Groups/Memberships created: no")
    return 0
