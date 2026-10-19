"""#136 Slice 5F: existing Group save through real menu and CLI dispatch boundaries.

Synthetic IDs only. These tests do not write real student data.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

import concord.menu_saved_groupings as menu_root
import concord.menu_saved_operational_grouping as menu
from concord.cli_app.handlers import saved_grouping_operational as direct
from concord.cli_app.parser import build_parser
from concord.menu_context import MenuSessionContext
from concord.workflows import ActivitySummary, WorkflowActor


def _activity() -> ActivitySummary:
    return ActivitySummary(
        class_id="class-synthetic",
        activity_id="activity-synthetic",
        title="Synthetic discussion",
        status="draft",
        scoring_orientation="mixed",
        session_count=1,
        group_count=6,
        snapshot_revision=12,
    )


def _state() -> MenuSessionContext:
    return MenuSessionContext(actor=WorkflowActor(actor_id="teacher-synthetic"))


def _preview(*, unresolved: tuple[str, ...] = ()) -> Any:
    groups = tuple(
        SimpleNamespace(
            label=f"Table {n}",
            student_ids=(f"student-{n}",),
        )
        for n in range(1, 7)
    )
    return SimpleNamespace(
        name="Six Tables",
        arrangement_id="six-tables",
        source_activity_id="activity-synthetic",
        source_session_id="session-1",
        source_snapshot_revision=12,
        groups=groups,
        assigned_count=6,
        unresolved_student_ids=unresolved,
        review_digest="f" * 64,
    )


def _saved() -> Any:
    return SimpleNamespace(
        sha256="a" * 64,
        revision=SimpleNamespace(
            name="Six Tables",
            arrangement_id="six-tables",
            revision=1,
            groups=_preview().groups,
        ),
    )


def _mock_menu(
    monkeypatch: pytest.MonkeyPatch, *, unresolved: tuple[str, ...] = ()
) -> list[str]:
    events: list[str] = []
    monkeypatch.setattr(
        menu, "show_activity", lambda *_a: SimpleNamespace(summary=_activity())
    )
    monkeypatch.setattr(
        menu,
        "list_sessions",
        lambda *_a: (SimpleNamespace(session_id="session-1", label="First Session"),),
    )
    monkeypatch.setattr(
        menu,
        "choose_session",
        lambda *_a, **_k: SimpleNamespace(
            session_id="session-1", label="First Session"
        ),
    )
    monkeypatch.setattr(
        menu,
        "prompt_text",
        lambda _title, label, **_k: (
            "Six Tables" if label == "Grouping name" else "six-tables"
        ),
    )
    monkeypatch.setattr(menu, "_review_placements", lambda *_a: events.append("review"))
    monkeypatch.setattr(menu, "show_result", lambda *_a, **_k: None)
    monkeypatch.setattr(
        menu, "handle_write_error", lambda error, **_k: pytest.fail(str(error))
    )
    monkeypatch.setattr(
        menu,
        "prepare_save_operational_grouping",
        lambda request: events.append("prepare") or _preview(unresolved=unresolved),
    )
    return events


def test_menu_dispatch_preserves_existing_three_options(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called: list[str] = []
    choices = iter(["1", "2", "3", "4", "b"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(choices))
    monkeypatch.setattr(menu_root, "clear_screen", lambda: None)
    monkeypatch.setattr(menu_root, "print_menu_header", lambda *_a: None)
    monkeypatch.setattr(menu_root, "print_navigation", lambda: None)
    monkeypatch.setattr(
        menu_root, "use_saved_grouping", lambda *_a: called.append("use")
    )
    monkeypatch.setattr(
        menu_root, "save_grouping_from_plan", lambda *_a: called.append("plan")
    )
    monkeypatch.setattr(
        menu_root, "manage_saved_groupings", lambda *_a: called.append("manage")
    )
    monkeypatch.setattr(
        menu_root,
        "save_grouping_from_existing_groups",
        lambda *_a: called.append("operational"),
    )
    menu_root.launch_saved_groupings_menu(_activity(), _state())
    assert called == ["use", "plan", "manage", "operational"]


def test_menu_commits_one_reviewed_operational_grouping(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events = _mock_menu(monkeypatch)
    monkeypatch.setattr(
        menu, "confirm_write", lambda *_a: events.append("confirm") or True
    )

    def commit(request: Any, *, review_digest: str) -> Any:
        assert request.session_id == "session-1"
        assert request.activity_id == "activity-synthetic"
        assert request.expected_snapshot_revision == 12
        assert request.actor.actor_id == "teacher-synthetic"
        assert request.acknowledge_unresolved is True
        assert review_digest == "f" * 64
        events.append("commit")
        return _saved()

    monkeypatch.setattr(menu, "save_operational_grouping", commit)
    menu.save_grouping_from_existing_groups(_activity(), _state())
    assert events == ["prepare", "review", "confirm", "commit"]


def test_menu_unresolved_requires_extra_acknowledgment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events = _mock_menu(monkeypatch, unresolved=("student-29",))
    monkeypatch.setattr(
        menu, "confirm_write", lambda *_a, **_k: events.append("ack") or False
    )
    monkeypatch.setattr(
        menu,
        "save_operational_grouping",
        lambda *_a, **_k: pytest.fail("Canceled save wrote"),
    )
    menu.save_grouping_from_existing_groups(_activity(), _state())
    assert events == ["prepare", "review", "ack"]


def test_menu_final_save_cancellation_leaves_library_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events = _mock_menu(monkeypatch)
    monkeypatch.setattr(menu, "confirm_write", lambda *_a, **_k: False)
    monkeypatch.setattr(
        menu,
        "save_operational_grouping",
        lambda *_a, **_k: pytest.fail("Canceled save wrote"),
    )
    menu.save_grouping_from_existing_groups(_activity(), _state())
    assert events == ["prepare", "review"]


def _args(command: str, *extra: str) -> Any:
    argv = [
        "saved-grouping",
        command,
        "--class-id",
        "class-synthetic",
        "--activity-id",
        "activity-synthetic",
        "--actor-id",
        "teacher-synthetic",
        "--expected-snapshot",
        "12",
        "--session-id",
        "session-1",
        "--arrangement-id",
        "six-tables",
        "--name",
        "Six Tables",
        *extra,
    ]
    if command == "save-groups":
        argv += ["--review-digest", "f" * 64]
    return build_parser().parse_args(argv)


def test_cli_new_commands_have_explicit_source_session_and_actor() -> None:
    for command in ("save-groups-preview", "save-groups"):
        args = _args(command)
        assert args.session_id == "session-1"
        assert args.actor_id == "teacher-synthetic"
        assert args.expected_snapshot == 12
        assert callable(args.handler)


def test_cli_save_requires_digest_and_snapshot() -> None:
    parser = build_parser()
    full = [
        "saved-grouping",
        "save-groups",
        "--class-id",
        "class-synthetic",
        "--activity-id",
        "activity-synthetic",
        "--actor-id",
        "teacher-synthetic",
        "--session-id",
        "session-1",
        "--arrangement-id",
        "six-tables",
        "--name",
        "Six Tables",
        "--expected-snapshot",
        "12",
    ]
    with pytest.raises(SystemExit) as missing_digest:
        parser.parse_args(full)
    assert missing_digest.value.code == 2
    without_snapshot = [x for x in full if x not in ("--expected-snapshot", "12")]
    with pytest.raises(SystemExit) as missing_snapshot:
        parser.parse_args(without_snapshot + ["--review-digest", "f" * 64])
    assert missing_snapshot.value.code == 2


def test_cli_preview_is_read_only_and_private_by_default(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    events: list[str] = []
    monkeypatch.setattr(
        direct,
        "prepare_save_operational_grouping",
        lambda request, **_k: (
            events.append("prepare") or _preview(unresolved=("student-29",))
        ),
    )
    monkeypatch.setattr(
        direct,
        "save_operational_grouping",
        lambda *_a, **_k: pytest.fail("Preview wrote"),
    )
    assert direct.handle_save_groups_preview(_args("save-groups-preview")) == 0
    output = capsys.readouterr().out
    assert events == ["prepare"]
    assert "Table 1" in output and "Review digest:" in output
    assert "student-29" not in output and "student-1" not in output
    assert "--acknowledge-unresolved" in output
    assert (
        direct.handle_save_groups_preview(
            _args("save-groups-preview", "--show-members")
        )
        == 0
    )
    revealed = capsys.readouterr().out
    assert "student-29" in revealed and "student-1" in revealed


def test_cli_save_forwards_exact_review_and_unresolved_choice(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def commit(request: Any, *, review_digest: str, workspace_root: Any) -> Any:
        assert request.session_id == "session-1"
        assert request.expected_snapshot_revision == 12
        assert request.acknowledge_unresolved is True
        assert review_digest == "f" * 64
        return _saved()

    monkeypatch.setattr(direct, "save_operational_grouping", commit)
    assert (
        direct.handle_save_groups(_args("save-groups", "--acknowledge-unresolved")) == 0
    )
    output = capsys.readouterr().out
    assert "Source Activity and canonical Groups unchanged: yes" in output
