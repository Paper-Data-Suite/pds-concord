"""#136 Slice 5D: teacher-menu/direct-CLI immutable revision contracts."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.classes import write_class_roster
from pds_core.rosters import create_roster
from pds_core.workspace import ensure_workspace_root

import concord.menu_saved_grouping_revisions as menu
import concord.menu_saved_groupings as saved_menu
from concord.class_group_arrangement_storage import (
    ArrangementConflictError,
    append_arrangement_revision,
    create_arrangement,
    list_arrangement_history,
)
from concord.class_group_arrangements import (
    SavedArrangementGroup,
    SavedArrangementRevision,
)
from concord.cli_app.handlers import saved_grouping_revision as cli
from concord.cli_app.parser import build_parser
from concord.menu_context import MenuSessionContext
from concord.workflows import ActivitySummary, WorkflowActor

ACTOR = "teacher-synthetic"
CLASS = "class-synthetic"
YEAR = "2026-2027"


def _activity() -> ActivitySummary:
    return ActivitySummary(
        class_id=CLASS,
        activity_id="activity-synthetic",
        title="Synthetic Discussion",
        status="draft",
        scoring_orientation="mixed",
        session_count=1,
        group_count=0,
        snapshot_revision=7,
    )


def _state() -> MenuSessionContext:
    return MenuSessionContext(actor=WorkflowActor(actor_id=ACTOR))


def _saved(*, status: str = "active", revision: int = 1) -> Any:
    return SimpleNamespace(
        sha256="a" * 64,
        revision=SimpleNamespace(
            arrangement_id="tables-six",
            revision=revision,
            name="Six Table Groups",
            status=status,
            groups=(SimpleNamespace(label="Table A", student_ids=("student-01",)),),
            unresolved_student_ids=(),
        ),
    )


def _change_preview(action: str) -> Any:
    return SimpleNamespace(
        arrangement_id="tables-six",
        action=action,
        name="Six Tables Revised",
        previous_revision=1,
        new_revision=2,
        status="retired" if action == "retire" else "active",
        groups=_saved().revision.groups,
        unresolved_student_ids=(),
        assigned_count=1,
        review_digest="d" * 64,
    )


def _common(action: str) -> list[str]:
    return [
        "saved-grouping",
        action,
        "--class-id",
        CLASS,
        "--arrangement-id",
        "tables-six",
        "--actor-id",
        ACTOR,
    ]


def _change_argv(action: str) -> list[str]:
    argv = [
        *_common(action),
        "--action",
        "rename",
        "--new-name",
        "Six Tables Revised",
        "--expected-revision",
        "1",
        "--expected-sha256",
        "a" * 64,
    ]
    if action == "change":
        argv += ["--review-digest", "d" * 64]
    return argv


def test_parser_exposes_history_and_reviewed_revisions() -> None:
    parser = build_parser()
    for action in ("history", "change-preview", "change"):
        argv = _common(action) if action == "history" else _change_argv(action)
        args = parser.parse_args(argv)
        assert args.saved_grouping_command == action
        assert callable(args.handler)


def test_change_requires_digest_and_cas_from_cli() -> None:
    parser = build_parser()
    with pytest.raises(SystemExit) as missing_digest:
        parser.parse_args(_change_argv("change")[:-2])
    assert missing_digest.value.code == 2
    with pytest.raises(SystemExit) as missing_sha:
        parser.parse_args(
            _common("change-preview")
            + ["--action", "retire", "--expected-revision", "1"]
        )
    assert missing_sha.value.code == 2


def test_replacement_cli_carries_exact_source_and_actor() -> None:
    argv = [
        *_common("change-preview"),
        "--action",
        "replace-from-plan",
        "--expected-revision",
        "3",
        "--expected-sha256",
        "b" * 64,
        "--source-activity-id",
        "activity-source",
        "--source-group-plan-id",
        "plan-source",
        "--expected-source-snapshot",
        "11",
    ]
    req = cli._request(build_parser().parse_args(argv))
    assert req.action == "replace_from_plan"
    assert req.expected_revision == 3
    assert req.expected_sha256 == "b" * 64
    assert req.actor.actor_id == ACTOR
    assert req.source_activity_id == "activity-source"
    assert req.source_group_plan_id == "plan-source"
    assert req.expected_source_snapshot_revision == 11


def test_cli_preview_does_not_write_and_hides_student_ids(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    recorded: list[object] = []
    monkeypatch.setattr(
        cli,
        "prepare_grouping_change",
        lambda req, **_k: recorded.append(req) or _change_preview("rename"),
    )
    monkeypatch.setattr(
        cli,
        "change_grouping",
        lambda *_a, **_k: pytest.fail("Preview wrote"),
    )
    assert (
        cli.handle_change_preview(
            build_parser().parse_args(_change_argv("change-preview"))
        )
        == 0
    )
    output = capsys.readouterr().out
    assert "Review digest: " + "d" * 64 in output
    assert "student-01" not in output
    assert "Writes: none" in output
    assert getattr(recorded[0], "action") == "rename"


def test_cli_commit_forwards_exact_review_digest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    received: list[tuple[object, str]] = []

    def commit(req: object, *, review_digest: str, **_kw: Any) -> Any:
        received.append((req, review_digest))
        return _saved(revision=2)

    monkeypatch.setattr(cli, "change_grouping", commit)
    assert cli.handle_change(build_parser().parse_args(_change_argv("change"))) == 0
    assert len(received) == 1
    assert received[0][1] == "d" * 64
    assert getattr(received[0][0], "actor").actor_id == ACTOR


def test_menu_change_previews_then_confirms_before_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []
    monkeypatch.setattr(menu, "prompt_text", lambda *_a, **_k: "Six Tables Revised")
    monkeypatch.setattr(
        menu,
        "prepare_grouping_change",
        lambda _req: events.append("preview") or _change_preview("rename"),
    )
    monkeypatch.setattr(
        menu, "confirm_write", lambda *_a, **_k: events.append("confirm") or True
    )
    monkeypatch.setattr(menu, "show_result", lambda *_a, **_k: None)

    def commit(req: object, *, review_digest: str) -> Any:
        events.append("commit")
        assert review_digest == "d" * 64
        assert getattr(req, "expected_revision") == 1
        return _saved(revision=2)

    monkeypatch.setattr(menu, "change_grouping", commit)
    assert menu._change(
        _activity(),
        _state(),
        _saved(),
        "rename",
        show_placements=lambda *_a, **_k: None,
    )
    assert events == ["preview", "confirm", "commit"]


def test_cancelled_revision_never_writes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        menu, "prepare_grouping_change", lambda _req: _change_preview("retire")
    )
    monkeypatch.setattr(menu, "confirm_write", lambda *_a, **_k: False)
    monkeypatch.setattr(
        menu,
        "change_grouping",
        lambda *_a, **_k: pytest.fail("Cancelled write"),
    )
    assert not menu._change(
        _activity(),
        _state(),
        _saved(),
        "retire",
        show_placements=lambda *_a, **_k: None,
    )


def test_manage_menu_hides_revision_actions_after_retirement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        menu, "_current", lambda *_a: _saved(status="retired", revision=3)
    )
    monkeypatch.setattr(menu, "clear_screen", lambda: None)
    monkeypatch.setattr(menu, "print_menu_header", lambda *_a: None)
    monkeypatch.setattr(menu, "print_navigation", lambda: None)
    options = iter(["5", "b"])
    monkeypatch.setattr("builtins.input", lambda *_a: next(options))
    failures: list[str] = []
    monkeypatch.setattr(menu, "pause_for_user", lambda: failures.append("invalid"))
    monkeypatch.setattr(menu, "_change", lambda *_a, **_k: pytest.fail("Retired write"))
    menu.manage_grouping_revision(
        _activity(),
        _state(),
        _saved(status="retired"),
        show_placements=lambda *_a, **_k: None,
    )
    assert failures == ["invalid"]


def test_manage_from_existing_menu_dispatches_revision_actions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(saved_menu, "_saved", lambda *_a: (_saved(),))
    monkeypatch.setattr(
        saved_menu, "select_one", lambda _title, items, _labels, **_kw: items[0]
    )
    monkeypatch.setattr(saved_menu, "_show_placements", lambda *_a, **_k: None)
    monkeypatch.setattr(saved_menu, "show_result", lambda *_a, **_k: None)
    seen: list[str] = []
    monkeypatch.setattr(
        saved_menu,
        "manage_grouping_revision",
        lambda activity, state, selected, *, show_placements: seen.append(
            selected.revision.arrangement_id
        ),
    )
    saved_menu.manage_saved_groupings(_activity(), _state())
    assert seen == ["tables-six"]


def test_immutable_history_reads_two_revisions_without_modifying_storage(
    tmp_path: Path,
) -> None:
    root = ensure_workspace_root(tmp_path / "workspace")
    write_class_metadata_for_class(
        root,
        create_class_metadata(
            CLASS, YEAR, created_at=datetime(2026, 9, 1, tzinfo=timezone.utc)
        ),
    )
    write_class_roster(
        root,
        create_roster(
            CLASS,
            tuple(
                {
                    "student_id": f"student-{n:02}",
                    "first_name": "Synthetic",
                    "last_name": f"{n}",
                    "period": "1",
                }
                for n in range(1, 30)
            ),
        ),
    )
    roster_ids = tuple(f"student-{n:02}" for n in range(1, 30))
    groups = tuple(
        SavedArrangementGroup(
            key=f"table-{i}",
            label=f"Table {i}",
            student_ids=tuple(roster_ids[k] for k in range(i - 1, 29, 6)),
        )
        for i in range(1, 7)
    )
    initial = SavedArrangementRevision(
        arrangement_id="tables-six",
        class_id=CLASS,
        school_year=YEAR,
        revision=1,
        name="Six Groups",
        owner_actor_id=ACTOR,
        created_by_actor_id=ACTOR,
        created_at="2026-10-17T20:00:00-04:00",
        groups=groups,
        roster_student_ids=roster_ids,
    )
    first = create_arrangement(root, initial, actor_id=ACTOR)
    second = append_arrangement_revision(
        root,
        replace(
            initial,
            revision=2,
            name="Six Revised Groups",
            created_at="2026-10-17T21:00:00-04:00",
            predecessor_sha256=first.sha256,
        ),
        actor_id=ACTOR,
        expected_revision=1,
        expected_sha256=first.sha256,
    )
    history = list_arrangement_history(
        root,
        class_id=CLASS,
        school_year=YEAR,
        arrangement_id="tables-six",
        actor_id=ACTOR,
    )
    assert len(history) == 2
    assert history[0] == first
    assert history[1] == second
    assert sum(len(g.student_ids) for g in history[1].revision.groups) == 29
    with pytest.raises(ArrangementConflictError, match="owning teacher"):
        list_arrangement_history(
            root,
            class_id=CLASS,
            school_year=YEAR,
            arrangement_id="tables-six",
            actor_id="different-teacher",
        )


def test_cli_history_hides_student_ids(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli, "_root_and_year", lambda _args: (Path("synthetic"), YEAR))
    monkeypatch.setattr(cli, "list_arrangement_history", lambda *_a, **_k: (_saved(),))
    assert cli.handle_history(build_parser().parse_args(_common("history"))) == 0
    output = capsys.readouterr().out
    assert "revision=1" in output
    assert "student-01" not in output
