"""#146 Slice 5: synthetic cross-surface status and direct-CLI qualification.

All mutable state lives inside pytest's disposable workspace; no classroom data.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from issue140_slice2_fixtures import (
    ACTIVITY_ID,
    ACTOR,
    SOURCE_CLASS,
    build_workspace,
)
from pds_core.routing_models import ModuleWorkRef
from test_workflow_groups_assignments import _actor, _workspace_with_activity

import concord.menu_activity as activity_menu
import concord.menu_group as group_menu
import concord.menu_session as session_menu
from concord.cli import build_parser
from concord.cli import main as cli_main
from concord.menu_context import MenuSessionContext
from concord.storage import list_work_snapshots
from concord.workflows import (
    CreateGroupRequest,
    create_group,
    list_groups,
    list_sessions,
    show_activity,
    show_group,
    show_session,
)


def _work(class_id: str, activity_id: str) -> ModuleWorkRef:
    return ModuleWorkRef("concord", class_id, activity_id)


@pytest.mark.parametrize("orientation", ("evidence_only", "mixed", "standards_based"))
def test_statuses_across_three_real_teacher_menus(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    orientation: str,
) -> None:
    """Activity -> Session -> Group retain one canonical snapshot history."""
    fixture = build_workspace(tmp_path, orientation=orientation)
    root = fixture.root
    state = MenuSessionContext(actor=ACTOR)
    work = _work(SOURCE_CLASS, ACTIVITY_ID)
    receipts: list[object] = []
    reviews: list[tuple[str, ...]] = []

    def confirm(_title: str, _token: str, lines: tuple[str, ...]) -> bool:
        reviews.append(lines)
        return True

    def no_errors(error: Exception, **_kwargs: object) -> None:
        pytest.fail(f"Teacher workflow rejected synthetic data: {error}")

    monkeypatch.setattr(activity_menu, "resolve_read_workspace_root", lambda: root)
    monkeypatch.setattr(
        activity_menu, "load_menu_standards_library", lambda _root: fixture.standards
    )
    monkeypatch.setattr(activity_menu, "confirm_write", confirm)
    monkeypatch.setattr(activity_menu, "select_one", lambda *_a, **_kw: "configured")
    monkeypatch.setattr(
        activity_menu, "show_result", lambda *args: receipts.append(args)
    )
    monkeypatch.setattr(activity_menu, "handle_write_error", no_errors)

    initial = show_activity(SOURCE_CLASS, ACTIVITY_ID, workspace_root=root)
    assert initial.summary.status == "draft"
    original = list_work_snapshots(root, work)
    activity_menu._update_activity_field(initial.summary, state, "status")
    after_activity = show_activity(SOURCE_CLASS, ACTIVITY_ID, workspace_root=root)
    assert after_activity.summary.status == "configured"
    assert len(reviews) == 1
    assert "Current status: draft" in "\n".join(reviews[-1])
    assert "Requested status: configured" in "\n".join(reviews[-1])
    assert len(list_work_snapshots(root, work)) == len(original) + 1
    assert after_activity.standards_profile_id == initial.standards_profile_id
    assert after_activity.focus_standard_ids == initial.focus_standard_ids

    monkeypatch.setattr(
        session_menu,
        "_latest",
        lambda _activity: show_activity(
            SOURCE_CLASS, ACTIVITY_ID, workspace_root=root
        ).summary,
    )
    monkeypatch.setattr(session_menu, "select_one", lambda *_a, **_kw: "active")
    monkeypatch.setattr(session_menu, "confirm_write", confirm)
    monkeypatch.setattr(
        session_menu, "show_result", lambda *args: receipts.append(args)
    )
    monkeypatch.setattr(session_menu, "handle_write_error", no_errors)
    write_kwargs: dict[str, object] = {"workspace_root": root}
    if orientation in {"mixed", "standards_based"}:
        write_kwargs["standards_library"] = fixture.standards
    monkeypatch.setattr(
        session_menu, "standards_kwargs_for_activity", lambda _activity: write_kwargs
    )
    session = list_sessions(SOURCE_CLASS, ACTIVITY_ID, workspace_root=root)[0]
    assert session.status == "planned"
    session_menu._edit_field(after_activity.summary, session, state, "status")
    current_session = show_session(
        SOURCE_CLASS, ACTIVITY_ID, session.session_id, workspace_root=root
    )
    assert current_session.status == "active"
    assert current_session.actual_start is None
    assert current_session.actual_end is None
    assert current_session.status_reason is None
    assert len(reviews) == 2

    current = show_activity(SOURCE_CLASS, ACTIVITY_ID, workspace_root=root).summary
    created = create_group(
        CreateGroupRequest(
            class_id=SOURCE_CLASS,
            activity_id=ACTIVITY_ID,
            group_id="slice5-synthetic-group",
            label="Synthetic Cluster",
            status="planned",
            expected_snapshot_revision=current.snapshot_revision,
            actor=ACTOR,
        ),
        **write_kwargs,
    )
    assert created.commit.snapshot_revision == current.snapshot_revision + 1
    monkeypatch.setattr(
        group_menu,
        "_latest",
        lambda _activity: show_activity(
            SOURCE_CLASS, ACTIVITY_ID, workspace_root=root
        ).summary,
    )
    monkeypatch.setattr(
        group_menu,
        "list_groups",
        lambda c, a: list_groups(c, a, workspace_root=root),
    )
    monkeypatch.setattr(
        group_menu,
        "show_group",
        lambda c, a, g: show_group(c, a, g, workspace_root=root),
    )
    monkeypatch.setattr(group_menu, "choose_group", lambda groups, **_kw: groups[0])
    monkeypatch.setattr(
        group_menu, "standards_kwargs_for_activity", lambda _activity: write_kwargs
    )
    monkeypatch.setattr(group_menu, "select_one", lambda *_a, **_kw: "superseded")
    monkeypatch.setattr(group_menu, "confirm_write", confirm)
    monkeypatch.setattr(
        group_menu, "show_result", lambda *args: receipts.append(args)
    )
    monkeypatch.setattr(
        group_menu,
        "_handle_error",
        lambda _activity, _title, error: pytest.fail(str(error)),
    )
    monkeypatch.setattr("builtins.input", lambda _prompt: "3")
    group_menu._edit_group(
        show_activity(SOURCE_CLASS, ACTIVITY_ID, workspace_root=root).summary,
        state,
    )
    group = show_group(
        SOURCE_CLASS, ACTIVITY_ID, "slice5-synthetic-group", workspace_root=root
    )
    assert group.summary.status == "superseded"
    assert group.supersedes_group_id is None
    assert group.summary.member_count == 0
    assert len(reviews) == 3
    assert "No Group successor" in "\n".join(reviews[-1])
    assert len(receipts) == 3
    assert len(list_work_snapshots(root, work)) == len(original) + 4


def test_direct_cli_preserves_exact_status_arguments_and_conflict_exit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, revision = _workspace_with_activity(tmp_path)
    work = _work("class-1", "activity-1")
    monkeypatch.setattr(
        "builtins.input",
        lambda *_a, **_kw: pytest.fail("direct CLI requested interactive input"),
    )

    def options(expected: int) -> list[str]:
        return [
            "--workspace-root", str(root),
            "--class-id", "class-1",
            "--activity-id", "activity-1",
            "--actor-id", "teacher-1",
            "--expected-snapshot", str(expected),
        ]

    assert cli_main(["activity", "set-status", *options(revision),
                     "--status", "configured"]) == 0
    assert show_activity(
        "class-1", "activity-1", workspace_root=root
    ).summary.status == "configured"
    revision += 1
    assert cli_main(["session", "set-status", *options(revision),
                     "--session-id", "session-1", "--status", "interrupted"]) == 0
    assert show_session(
        "class-1", "activity-1", "session-1", workspace_root=root
    ).status == "interrupted"
    revision += 1
    created = create_group(
        CreateGroupRequest(
            class_id="class-1", activity_id="activity-1",
            group_id="cli-group", label="CLI Group", status="planned",
            expected_snapshot_revision=revision, actor=_actor(),
        ),
        workspace_root=root,
    )
    revision = created.commit.snapshot_revision
    assert cli_main(["group", "set-status", *options(revision),
                     "--group-id", "cli-group", "--status", "superseded"]) == 0
    assert show_group(
        "class-1", "activity-1", "cli-group", workspace_root=root
    ).summary.status == "superseded"
    assert show_group(
        "class-1", "activity-1", "cli-group", workspace_root=root
    ).supersedes_group_id is None
    assert cli_main(["group", "set-status", *options(revision),
                     "--group-id", "cli-group", "--status", "active"]) == 3
    assert len(list_work_snapshots(root, work)) == revision + 1


@pytest.mark.parametrize(
    ("family", "record_option"),
    (
        (("group", "member", "end"), "--membership-id"),
        (("role", "end"), "--role-assignment-id"),
        (("responsibility", "end"), "--responsibility-assignment-id"),
    ),
)
def test_direct_cli_end_status_contract_is_unchanged(
    family: tuple[str, ...], record_option: str
) -> None:
    parser = build_parser()
    common = [
        "--workspace-root", "synthetic-no-workspace",
        "--class-id", "synthetic-class", "--activity-id", "synthetic-activity",
        "--expected-snapshot", "1", "--actor-id", "synthetic-actor",
        record_option, "synthetic-assignment",
    ]
    for allowed in ("completed", "withdrawn", "cancelled"):
        chosen = parser.parse_args([*family, *common, "--status", allowed])
        assert chosen.status == allowed
    for forbidden in ("reassigned", "superseded", "active"):
        with pytest.raises(SystemExit) as rejected:
            parser.parse_args([*family, *common, "--status", forbidden])
        assert rejected.value.code == 2
