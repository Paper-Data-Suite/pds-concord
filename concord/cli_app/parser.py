"""Side-effect-free argparse construction for Concord direct commands."""

from __future__ import annotations

import argparse

from concord import __version__
from concord.cli_app.handlers import (
    activity,
    group,
    responsibility,
    role,
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
    return parser
