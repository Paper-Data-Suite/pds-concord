"""Side-effect-free argparse construction for Concord direct commands."""

from __future__ import annotations

import argparse

from concord import __version__
from concord.cli_app.handlers import (
    activity,
    artifact,
    group,
    responsibility,
    role,
    scan,
    session,
    workspace,
)


def _launch_menu_command(_args: argparse.Namespace) -> int:
    """Launch the teacher-facing menu only after explicit dispatch."""
    from concord.menu import launch_menu

    return launch_menu()


def _workspace_option(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--workspace-root",
        help="Explicit Paper Data Suite workspace root.",
    )


def _actor_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--actor-id", required=True, help="Authorized actor identifier."
    )
    parser.add_argument("--actor-label", help="Optional actor display-label snapshot.")
    parser.add_argument("--actor-role", help="Optional actor role-label snapshot.")


def _standards_option(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--standards-library",
        help=(
            "Core standards-library JSON. When omitted, Concord uses the canonical "
            "workspace standards/library.json when it exists."
        ),
    )


def _expected_option(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--expected-snapshot",
        type=int,
        required=True,
        help="Exact current Activity snapshot revision.",
    )


def _mutating_options(parser: argparse.ArgumentParser) -> None:
    _workspace_option(parser)
    _expected_option(parser)
    _actor_options(parser)
    _standards_option(parser)


def _context_options(
    parser: argparse.ArgumentParser,
    *,
    required: bool,
) -> None:
    parser.add_argument(
        "--session-id",
        action="append",
        required=required,
        default=None,
        help="Session in the Effective Context; repeat for several Sessions.",
    )
    parser.add_argument("--sequence-start", type=int)
    parser.add_argument("--sequence-end", type=int)
    parser.add_argument(
        "--applies-to-remaining-activity",
        action="store_true",
    )


def _class_activity(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--class-id", required=True)
    parser.add_argument("--activity-id", required=True)


def _activity_commands(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    parent = subparsers.add_parser("activity", help="Create and manage Activities.")
    actions = parent.add_subparsers(dest="activity_command", required=True)

    create = actions.add_parser("create", help="Create an Activity and first Session.")
    _workspace_option(create)
    _actor_options(create)
    _standards_option(create)
    _class_activity(create)
    create.add_argument("--title", required=True)
    create.add_argument("--activity-type", required=True)
    create.add_argument(
        "--scoring-orientation",
        required=True,
        choices=("evidence_only", "standards_based", "mixed", "local_criteria_only"),
    )
    create.add_argument("--status", default="draft")
    create.add_argument("--description")
    create.add_argument("--standards-profile-id")
    create.add_argument("--focus-standard-id", action="append")
    create.add_argument("--external-reference-id", action="append")
    create.add_argument("--session-id", required=True)
    create.add_argument("--session-sequence", type=int, default=1)
    create.add_argument("--session-status", default="planned")
    create.add_argument("--session-label")
    create.add_argument("--scheduled-start")
    create.add_argument("--scheduled-end")
    create.add_argument("--session-notes")
    create.set_defaults(handler=activity.handle_create)

    list_command = actions.add_parser("list", help="List current Activities.")
    _workspace_option(list_command)
    list_command.add_argument("--class-id")
    list_command.set_defaults(handler=activity.handle_list)

    show = actions.add_parser("show", help="Show one current Activity.")
    _workspace_option(show)
    _class_activity(show)
    show.set_defaults(handler=activity.handle_show)

    update = actions.add_parser("update", help="Revise Activity configuration.")
    _mutating_options(update)
    _class_activity(update)
    update.add_argument("--title")
    update.add_argument("--description")
    update.add_argument("--activity-type")
    update.add_argument(
        "--scoring-orientation",
        choices=("evidence_only", "standards_based", "mixed", "local_criteria_only"),
    )
    update.add_argument("--standards-profile-id")
    update.add_argument("--focus-standard-id", action="append")
    update.add_argument("--external-reference-id", action="append")
    update.add_argument("--status")
    update.set_defaults(handler=activity.handle_update)

    set_status = actions.add_parser(
        "set-status", help="Revise Activity lifecycle status."
    )
    _mutating_options(set_status)
    _class_activity(set_status)
    set_status.add_argument("--status", required=True)
    set_status.set_defaults(handler=activity.handle_set_status)


def _session_commands(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    parent = subparsers.add_parser("session", help="Manage Activity Sessions.")
    actions = parent.add_subparsers(dest="session_command", required=True)

    add = actions.add_parser("add", help="Add a Session.")
    _mutating_options(add)
    _class_activity(add)
    add.add_argument("--session-id", required=True)
    add.add_argument("--sequence", type=int, required=True)
    add.add_argument("--status", default="planned")
    add.add_argument("--label")
    add.add_argument("--scheduled-start")
    add.add_argument("--scheduled-end")
    add.add_argument("--actual-start")
    add.add_argument("--actual-end")
    add.add_argument("--notes")
    add.set_defaults(handler=session.handle_add)

    list_command = actions.add_parser("list", help="List current Sessions.")
    _workspace_option(list_command)
    _class_activity(list_command)
    list_command.set_defaults(handler=session.handle_list)

    show = actions.add_parser("show", help="Show one current Session.")
    _workspace_option(show)
    _class_activity(show)
    show.add_argument("--session-id", required=True)
    show.set_defaults(handler=session.handle_show)

    update = actions.add_parser("update", help="Revise Session configuration.")
    _mutating_options(update)
    _class_activity(update)
    update.add_argument("--session-id", required=True)
    update.add_argument("--sequence", type=int)
    update.add_argument("--status")
    update.add_argument("--label")
    update.add_argument("--scheduled-start")
    update.add_argument("--scheduled-end")
    update.add_argument("--actual-start")
    update.add_argument("--actual-end")
    update.add_argument("--notes")
    update.set_defaults(handler=session.handle_update)

    set_status = actions.add_parser(
        "set-status", help="Revise Session lifecycle status."
    )
    _mutating_options(set_status)
    _class_activity(set_status)
    set_status.add_argument("--session-id", required=True)
    set_status.add_argument("--status", required=True)
    set_status.set_defaults(handler=session.handle_set_status)


def _group_commands(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    parent = subparsers.add_parser("group", help="Manage Groups and Memberships.")
    actions = parent.add_subparsers(dest="group_command", required=True)

    create = actions.add_parser("create", help="Create an Activity-specific Group.")
    _mutating_options(create)
    _class_activity(create)
    create.add_argument("--group-id", required=True)
    create.add_argument("--label", required=True)
    create.add_argument("--status", default="planned")
    create.add_argument("--description")
    create.add_argument("--parent-group-id")
    _context_options(create, required=False)
    create.set_defaults(handler=group.handle_create)

    list_command = actions.add_parser("list", help="List current Groups.")
    _workspace_option(list_command)
    _class_activity(list_command)
    list_command.set_defaults(handler=group.handle_list)

    show = actions.add_parser("show", help="Show one current Group.")
    _workspace_option(show)
    _class_activity(show)
    show.add_argument("--group-id", required=True)
    show.set_defaults(handler=group.handle_show)

    update = actions.add_parser("update", help="Revise Group configuration.")
    _mutating_options(update)
    _class_activity(update)
    update.add_argument("--group-id", required=True)
    update.add_argument("--label")
    update.add_argument("--status")
    update.add_argument("--description")
    update.add_argument("--parent-group-id")
    _context_options(update, required=False)
    update.set_defaults(handler=group.handle_update)

    set_status = actions.add_parser("set-status", help="Revise Group lifecycle status.")
    _mutating_options(set_status)
    _class_activity(set_status)
    set_status.add_argument("--group-id", required=True)
    set_status.add_argument("--status", required=True)
    set_status.set_defaults(handler=group.handle_set_status)

    member = actions.add_parser("member", help="Manage Group Memberships.")
    member_actions = member.add_subparsers(dest="member_command", required=True)

    add = member_actions.add_parser("add", help="Add a rostered student Membership.")
    _mutating_options(add)
    _class_activity(add)
    add.add_argument("--group-id", required=True)
    add.add_argument(
        "--student-id",
        action="append",
        required=True,
        help="Core roster student ID; repeat to add several students atomically.",
    )
    add.add_argument(
        "--membership-id",
        action="append",
        help=(
            "Optional durable Membership ID; when supplied, repeat once per "
            "--student-id in the same order."
        ),
    )
    add.add_argument("--status", default="active")
    _context_options(add, required=True)
    add.set_defaults(handler=group.handle_member_add)

    member_list = member_actions.add_parser("list", help="List current Memberships.")
    _workspace_option(member_list)
    _class_activity(member_list)
    member_list.add_argument("--group-id")
    member_list.set_defaults(handler=group.handle_member_list)

    end = member_actions.add_parser("end", help="End a Membership without deletion.")
    _mutating_options(end)
    _class_activity(end)
    end.add_argument("--membership-id", required=True)
    end.add_argument(
        "--status",
        required=True,
        choices=("completed", "withdrawn", "cancelled"),
    )
    end.set_defaults(handler=group.handle_member_end)

    reassign = member_actions.add_parser(
        "reassign", help="Reassign Membership to another Group."
    )
    _mutating_options(reassign)
    _class_activity(reassign)
    reassign.add_argument("--membership-id", required=True)
    reassign.add_argument("--successor-membership-id")
    reassign.add_argument("--new-group-id", required=True)
    reassign.add_argument(
        "--predecessor-status",
        default="reassigned",
        choices=("reassigned", "superseded"),
    )
    reassign.add_argument(
        "--successor-status", default="active", choices=("planned", "active")
    )
    _context_options(reassign, required=True)
    reassign.set_defaults(handler=group.handle_member_reassign)


def _role_commands(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    parent = subparsers.add_parser("role", help="Manage contextual Role Assignments.")
    actions = parent.add_subparsers(dest="role_command", required=True)

    assign = actions.add_parser("assign", help="Assign a Role to a rostered student.")
    _mutating_options(assign)
    _class_activity(assign)
    assign.add_argument("--role-assignment-id", required=True)
    assign.add_argument("--student-id", required=True)
    assign.add_argument("--role-key", required=True)
    assign.add_argument("--status", default="active")
    assign.add_argument("--membership-id")
    assign.add_argument("--group-id")
    assign.add_argument("--role-label")
    _context_options(assign, required=True)
    assign.set_defaults(handler=role.handle_assign)

    list_command = actions.add_parser("list", help="List current Role Assignments.")
    _workspace_option(list_command)
    _class_activity(list_command)
    list_command.add_argument("--group-id")
    list_command.set_defaults(handler=role.handle_list)

    end = actions.add_parser("end", help="End a Role Assignment without deletion.")
    _mutating_options(end)
    _class_activity(end)
    end.add_argument("--role-assignment-id", required=True)
    end.add_argument(
        "--status",
        required=True,
        choices=("completed", "withdrawn", "cancelled"),
    )
    end.set_defaults(handler=role.handle_end)

    reassign = actions.add_parser(
        "reassign", help="Create a successor Role Assignment."
    )
    _mutating_options(reassign)
    _class_activity(reassign)
    reassign.add_argument("--role-assignment-id", required=True)
    reassign.add_argument("--successor-role-assignment-id", required=True)
    reassign.add_argument("--student-id", required=True)
    reassign.add_argument("--role-key", required=True)
    reassign.add_argument("--membership-id")
    reassign.add_argument("--group-id")
    reassign.add_argument("--role-label")
    reassign.add_argument(
        "--predecessor-status",
        default="reassigned",
        choices=("reassigned", "superseded"),
    )
    reassign.add_argument(
        "--successor-status", default="active", choices=("planned", "active")
    )
    _context_options(reassign, required=True)
    reassign.set_defaults(handler=role.handle_reassign)


def _responsibility_commands(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    parent = subparsers.add_parser(
        "responsibility", help="Manage Responsibility Assignments."
    )
    actions = parent.add_subparsers(dest="responsibility_command", required=True)

    assign = actions.add_parser("assign", help="Assign a contextual Responsibility.")
    _mutating_options(assign)
    _class_activity(assign)
    assign.add_argument("--responsibility-assignment-id", required=True)
    assignee = assign.add_mutually_exclusive_group(required=True)
    assignee.add_argument("--student-id")
    assignee.add_argument("--group-assignee-id")
    assign.add_argument("--description", required=True)
    assign.add_argument("--status", default="active")
    assign.add_argument("--group-id")
    assign.add_argument("--work-item-id")
    assign.add_argument("--expected-output")
    _context_options(assign, required=True)
    assign.set_defaults(handler=responsibility.handle_assign)

    list_command = actions.add_parser("list", help="List current Responsibilities.")
    _workspace_option(list_command)
    _class_activity(list_command)
    list_command.add_argument("--group-id")
    list_command.set_defaults(handler=responsibility.handle_list)

    end = actions.add_parser("end", help="End a Responsibility without deletion.")
    _mutating_options(end)
    _class_activity(end)
    end.add_argument("--responsibility-assignment-id", required=True)
    end.add_argument(
        "--status",
        required=True,
        choices=("completed", "withdrawn", "cancelled"),
    )
    end.set_defaults(handler=responsibility.handle_end)

    reassign = actions.add_parser("reassign", help="Create a successor Responsibility.")
    _mutating_options(reassign)
    _class_activity(reassign)
    reassign.add_argument("--responsibility-assignment-id", required=True)
    reassign.add_argument("--successor-responsibility-assignment-id", required=True)
    assignee = reassign.add_mutually_exclusive_group(required=True)
    assignee.add_argument("--student-id")
    assignee.add_argument("--group-assignee-id")
    reassign.add_argument("--description", required=True)
    reassign.add_argument("--group-id")
    reassign.add_argument("--work-item-id")
    reassign.add_argument("--expected-output")
    reassign.add_argument(
        "--predecessor-status",
        default="reassigned",
        choices=("reassigned", "superseded"),
    )
    reassign.add_argument(
        "--successor-status", default="active", choices=("planned", "active")
    )
    _context_options(reassign, required=True)
    reassign.set_defaults(handler=responsibility.handle_reassign)


def _workspace_commands(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    parent = subparsers.add_parser(
        "workspace", help="Inspect and configure the Core workspace."
    )
    actions = parent.add_subparsers(dest="workspace_command", required=True)

    show = actions.add_parser(
        "show", help="Show workspace resolution without creating it."
    )
    _workspace_option(show)
    show.set_defaults(handler=workspace.handle_show)

    set_command = actions.add_parser(
        "set", help="Create/validate and save a workspace root."
    )
    set_command.add_argument("path")
    set_command.set_defaults(handler=workspace.handle_set)

    validate = actions.add_parser(
        "validate", help="Create or validate the resolved workspace."
    )
    _workspace_option(validate)
    validate.set_defaults(handler=workspace.handle_validate)

    reset = actions.add_parser(
        "reset", help="Clear only the saved workspace preference."
    )
    reset.set_defaults(handler=workspace.handle_reset)


def _artifact_commands(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    parent = subparsers.add_parser(
        "artifact", help="Manage Artifacts, attribution, and physical pages."
    )
    actions = parent.add_subparsers(dest="artifact_command", required=True)

    list_artifacts = actions.add_parser("list", help="List Artifact Instances.")
    _workspace_option(list_artifacts)
    _class_activity(list_artifacts)
    list_artifacts.set_defaults(handler=artifact.handle_artifact_list)

    show_artifact = actions.add_parser("show", help="Show one Artifact Instance.")
    _workspace_option(show_artifact)
    _class_activity(show_artifact)
    show_artifact.add_argument("--artifact-instance-id", required=True)
    show_artifact.set_defaults(handler=artifact.handle_artifact_show)

    assemble = actions.add_parser(
        "assemble", help="Assemble exact returned physical-page evidence."
    )
    _workspace_option(assemble)
    _expected_option(assemble)
    _actor_options(assemble)
    _class_activity(assemble)
    assemble.add_argument("--artifact-instance-id", required=True)
    assemble.add_argument(
        "--select",
        action="append",
        help=(
            "Exact ambiguous occurrence selection as "
            "ARTIFACT_PAGE_ID=SCAN_REFERENCE_ID; repeat when needed."
        ),
    )
    assemble.set_defaults(
        handler=artifact.handle_assemble,
        command_parser=assemble,
    )

    author = actions.add_parser("author", help="Manage Artifact Authors.")
    author_actions = author.add_subparsers(dest="author_command", required=True)

    author_add = author_actions.add_parser("add", help="Add an explicit Author.")
    _mutating_options(author_add)
    _class_activity(author_add)
    author_add.add_argument("--artifact-instance-id", required=True)
    author_add.add_argument("--artifact-author-id", required=True)
    _artifact_author_semantic_options(author_add)
    author_add.set_defaults(
        handler=artifact.handle_author_add,
        command_parser=author_add,
    )

    author_list = author_actions.add_parser("list", help="List Artifact Authors.")
    _workspace_option(author_list)
    _class_activity(author_list)
    author_list.add_argument("--artifact-instance-id")
    author_list.add_argument("--include-historical", action="store_true")
    author_list.set_defaults(handler=artifact.handle_author_list)

    author_show = author_actions.add_parser("show", help="Show one Artifact Author.")
    _workspace_option(author_show)
    _class_activity(author_show)
    author_show.add_argument("--artifact-author-id", required=True)
    author_show.set_defaults(handler=artifact.handle_author_show)

    author_update = author_actions.add_parser(
        "update", help="Update the state of the same Author association."
    )
    _mutating_options(author_update)
    _class_activity(author_update)
    author_update.add_argument("--artifact-author-id", required=True)
    author_update.add_argument(
        "--attribution-status",
        required=True,
        choices=("proposed", "confirmed", "disputed", "unknown"),
    )
    author_update.set_defaults(handler=artifact.handle_author_update)

    author_replace = author_actions.add_parser(
        "replace", help="Create a corrected successor Author association."
    )
    _mutating_options(author_replace)
    _class_activity(author_replace)
    author_replace.add_argument("--artifact-author-id", required=True)
    author_replace.add_argument("--replacement-artifact-author-id", required=True)
    author_replace.add_argument("--correction-id", required=True)
    author_replace.add_argument("--reason", required=True)
    _artifact_author_semantic_options(author_replace)
    author_replace.add_argument("--correction-privacy-classification")
    author_replace.set_defaults(
        handler=artifact.handle_author_replace,
        command_parser=author_replace,
    )

    subject = actions.add_parser("subject", help="Manage Artifact Subjects.")
    subject_actions = subject.add_subparsers(dest="subject_command", required=True)

    subject_add = subject_actions.add_parser("add", help="Add an explicit Subject.")
    _mutating_options(subject_add)
    _class_activity(subject_add)
    subject_add.add_argument("--artifact-instance-id", required=True)
    subject_add.add_argument("--artifact-subject-id", required=True)
    _artifact_subject_semantic_options(subject_add)
    subject_add.set_defaults(
        handler=artifact.handle_subject_add,
        command_parser=subject_add,
    )

    subject_list = subject_actions.add_parser("list", help="List Artifact Subjects.")
    _workspace_option(subject_list)
    _class_activity(subject_list)
    subject_list.add_argument("--artifact-instance-id")
    subject_list.add_argument("--include-historical", action="store_true")
    subject_list.set_defaults(handler=artifact.handle_subject_list)

    subject_show = subject_actions.add_parser("show", help="Show one Artifact Subject.")
    _workspace_option(subject_show)
    _class_activity(subject_show)
    subject_show.add_argument("--artifact-subject-id", required=True)
    subject_show.set_defaults(handler=artifact.handle_subject_show)

    subject_update = subject_actions.add_parser(
        "update", help="Update the state of the same Subject association."
    )
    _mutating_options(subject_update)
    _class_activity(subject_update)
    subject_update.add_argument("--artifact-subject-id", required=True)
    subject_update.add_argument(
        "--confirmation-status",
        required=True,
        choices=("proposed", "confirmed", "disputed", "unresolved"),
    )
    subject_update.set_defaults(handler=artifact.handle_subject_update)

    subject_replace = subject_actions.add_parser(
        "replace", help="Create a corrected successor Subject association."
    )
    _mutating_options(subject_replace)
    _class_activity(subject_replace)
    subject_replace.add_argument("--artifact-subject-id", required=True)
    subject_replace.add_argument("--replacement-artifact-subject-id", required=True)
    subject_replace.add_argument("--correction-id", required=True)
    subject_replace.add_argument("--reason", required=True)
    _artifact_subject_semantic_options(subject_replace)
    subject_replace.add_argument("--correction-privacy-classification")
    subject_replace.set_defaults(
        handler=artifact.handle_subject_replace,
        command_parser=subject_replace,
    )

    page = actions.add_parser("page", help="Prepare or inspect physical pages.")
    page_actions = page.add_subparsers(dest="page_command", required=True)
    prepare = page_actions.add_parser("prepare", help="Preallocate pages and routes.")
    _mutating_options(prepare)
    _class_activity(prepare)
    prepare.add_argument("--artifact-instance-id", required=True)
    prepare.add_argument("--template-version-id", required=True)
    prepare.add_argument("--artifact-category", default="student_work")
    prepare.add_argument("--page-count", type=int, required=True)
    prepare.add_argument("--page-id", action="append")
    prepare.add_argument("--session-id")
    prepare.add_argument("--group-id")
    prepare.add_argument("--expected-return-status", default="returned_expected")
    prepare.add_argument("--privacy-classification", default="teacher_restricted")
    prepare.set_defaults(handler=artifact.handle_prepare)
    list_command = page_actions.add_parser("list", help="List Artifact Pages.")
    _workspace_option(list_command)
    _class_activity(list_command)
    list_command.add_argument("--artifact-instance-id")
    list_command.set_defaults(handler=artifact.handle_list)
    show = page_actions.add_parser("show", help="Show one Artifact Page.")
    _workspace_option(show)
    _class_activity(show)
    show.add_argument("--artifact-page-id", required=True)
    show.set_defaults(handler=artifact.handle_show)

    render = actions.add_parser("render", help="Render verified route-bearing pages.")
    _workspace_option(render)
    _expected_option(render)
    _actor_options(render)
    _class_activity(render)
    render.add_argument("--artifact-instance-id", required=True)
    render.add_argument("--output")
    render.set_defaults(handler=artifact.handle_render)


def _artifact_author_semantic_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--author-kind",
        required=True,
        choices=(
            "core_student",
            "concord_group",
            "current_actor",
            "authorized_adult",
            "unknown",
        ),
    )
    parser.add_argument("--author-id")
    parser.add_argument("--author-owner")
    parser.add_argument("--author-label")
    parser.add_argument(
        "--authorship-mode",
        required=True,
        choices=(
            "individual_author",
            "co_author",
            "observer",
            "recorder",
            "recorder_for_group",
            "collective_group_author",
            "teacher_author",
            "authorized_adult_author",
            "unknown",
        ),
    )
    parser.add_argument(
        "--attribution-status",
        default="confirmed",
        choices=("proposed", "confirmed", "disputed", "unknown"),
    )
    parser.add_argument(
        "--attribution-source",
        default="teacher",
        choices=("teacher", "participant", "imported", "system", "unknown"),
    )
    parser.add_argument("--represented-group-id")
    parser.add_argument("--role-assignment-id")
    parser.add_argument(
        "--representation-status",
        choices=(
            "individual_view",
            "recorder_summary",
            "majority_position",
            "unanimous_position",
            "multiple_named_positions",
            "no_consensus",
            "not_applicable",
        ),
    )
    parser.add_argument("--privacy-classification")


def _artifact_subject_semantic_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--subject-kind",
        required=True,
        choices=(
            "core_student",
            "concord_group",
            "concord_session",
            "concord_activity",
            "concord_artifact_instance",
            "external_record",
        ),
    )
    parser.add_argument("--subject-id", required=True)
    parser.add_argument("--subject-owner")
    parser.add_argument("--subject-contract-version")
    parser.add_argument("--subject-role", required=True)
    parser.add_argument(
        "--confirmation-status",
        default="confirmed",
        choices=("proposed", "confirmed", "disputed", "unresolved"),
    )
    parser.add_argument(
        "--assignment-source",
        default="teacher",
        choices=("teacher", "participant", "imported", "system"),
    )
    parser.add_argument("--criterion-id")
    parser.add_argument("--privacy-classification")

def _scan_commands(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    parent = subparsers.add_parser(
        "scan", help="Route retained scans and review failures."
    )
    actions = parent.add_subparsers(dest="scan_command", required=True)
    route = actions.add_parser("route", help="Retain and route source files.")
    _workspace_option(route)
    route.add_argument("source", nargs="+")
    route.set_defaults(handler=scan.handle_route)
    review = actions.add_parser("review", help="Inspect append-only routing review.")
    review_actions = review.add_subparsers(dest="review_command", required=True)
    list_command = review_actions.add_parser("list")
    _workspace_option(list_command)
    list_command.add_argument("--activity-id")
    list_command.set_defaults(handler=scan.handle_review_list)
    show = review_actions.add_parser("show")
    _workspace_option(show)
    show.add_argument("--failure-id", required=True)
    show.set_defaults(handler=scan.handle_review_show)
    resolve = review_actions.add_parser("resolve")
    _workspace_option(resolve)
    _actor_options(resolve)
    resolve.add_argument("--failure-id", required=True)
    resolve.add_argument("--message", required=True)
    resolve.add_argument("--defer", action="store_true")
    resolve.add_argument("--module-id", choices=("concord",), default="concord")
    resolve.add_argument("--class-id")
    resolve.add_argument("--work-id")
    resolve.add_argument("--route-id")
    resolve.set_defaults(handler=scan.handle_review_resolve, command_parser=resolve)


def build_parser() -> argparse.ArgumentParser:
    """Build the complete direct-command parser without touching workspace state."""
    parser = argparse.ArgumentParser(
        prog="concord",
        description=(
            "Concord is the Paper Data Suite module for paper-first collaborative "
            "classroom evidence. The complete Activity workflow is being built as "
            "a shared direct-command and teacher-menu surface."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command")
    menu = subparsers.add_parser("menu", help="Launch the teacher-facing menu.")
    menu.set_defaults(handler=_launch_menu_command)
    _workspace_commands(subparsers)
    _activity_commands(subparsers)
    _session_commands(subparsers)
    _group_commands(subparsers)
    _role_commands(subparsers)
    _responsibility_commands(subparsers)
    _artifact_commands(subparsers)
    _scan_commands(subparsers)
    return parser
