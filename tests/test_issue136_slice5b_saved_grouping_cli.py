"""Concord #136 Slice 5B: direct CLI command presentation/service contracts."""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from concord.class_group_arrangement_storage import (
    ArrangementConflictError,
    ArrangementStorageError,
)
from concord.cli_app.handlers import saved_grouping as command
from concord.cli_app.main import main as cli_main
from concord.cli_app.parser import build_parser
from concord.workflows.errors import ConcordWorkflowValidationError

ACTOR = "teacher-synthetic"
CLASS = "class-synthetic"
ACTIVITY = "activity-source"


def _base() -> list[str]:
    return [
        "--class-id",
        CLASS,
        "--actor-id",
        ACTOR,
    ]


def _save_args(action: str) -> Namespace:
    argv = [
        "saved-grouping",
        action,
        *_base(),
        "--activity-id",
        ACTIVITY,
        "--group-plan-id",
        "plan-source",
        "--arrangement-id",
        "tables-six",
        "--name",
        "Six Table Groups",
        "--expected-snapshot",
        "9",
    ]
    if action == "save":
        argv += ["--review-digest", "c" * 64]
    return build_parser().parse_args(argv)


def _reuse_args(action: str, *extra: str) -> Namespace:
    argv = [
        "saved-grouping",
        action,
        *_base(),
        "--activity-id",
        "activity-target",
        "--arrangement-id",
        "tables-six",
        "--new-group-plan-id",
        "plan-target",
        "--expected-snapshot",
        "6",
        *extra,
    ]
    if action == "reuse":
        argv += ["--review-digest", "b" * 64]
    return build_parser().parse_args(argv)


def _group(label: str, key: str, *students: str) -> SimpleNamespace:
    return SimpleNamespace(
        label=label,
        key=key,
        planned_group_key=key,
        student_ids=students,
    )


def _revision() -> SimpleNamespace:
    return SimpleNamespace(
        arrangement_id="tables-six",
        name="Six Table Groups",
        class_id=CLASS,
        school_year="2026-2027",
        revision=1,
        status="active",
        roster_student_ids=("student-1", "student-2"),
        unresolved_student_ids=("student-2",),
        groups=(_group("Table A", "table-a", "student-1"),),
    )


def test_commands_parse_without_activity_or_workspace_side_effects() -> None:
    parser = build_parser()
    for action in (
        "list",
        "show",
        "roster-diff",
        "save-preview",
        "save",
        "reuse-preview",
        "reuse",
    ):
        text = parser.format_help()
        assert "saved-grouping" in text
        if action in {"save-preview", "save"}:
            ns = _save_args(action)
        elif action in {"reuse-preview", "reuse"}:
            ns = _reuse_args(action)
        elif action in {"show", "roster-diff"}:
            ns = parser.parse_args(
                ["saved-grouping", action, *_base(), "--arrangement-id", "tables-six"]
            )
        else:
            ns = parser.parse_args(["saved-grouping", action, *_base()])
        assert ns.command == "saved-grouping"
        assert ns.saved_grouping_command == action
        assert callable(ns.handler)


def test_direct_reads_require_teacher_actor_and_explicit_class() -> None:
    parser = build_parser()
    with pytest.raises(SystemExit) as error:
        parser.parse_args(["saved-grouping", "list", "--class-id", CLASS])
    assert error.value.code == 2
    with pytest.raises(SystemExit) as error:
        parser.parse_args(["saved-grouping", "list", "--actor-id", ACTOR])
    assert error.value.code == 2


def test_save_and_reuse_commits_require_the_review_digest() -> None:
    parser = build_parser()
    for action in ("save", "reuse"):
        ns = _save_args(action) if action == "save" else _reuse_args(action)
        args = [
            "saved-grouping",
            action,
            *_base(),
            "--activity-id",
            ns.activity_id,
            "--arrangement-id",
            ns.arrangement_id,
            "--expected-snapshot",
            str(ns.expected_snapshot),
        ]
        if action == "save":
            args += ["--group-plan-id", ns.group_plan_id, "--name", ns.name]
        else:
            args += ["--new-group-plan-id", ns.new_group_plan_id]
        with pytest.raises(SystemExit) as error:
            parser.parse_args(args)
        assert error.value.code == 2


def test_class_scoped_list_hides_students_by_default(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    record = _revision()
    monkeypatch.setattr(command, "_scope", lambda _args: ("2026-2027", tmp_path))
    arguments: dict[str, Any] = {}

    def fake_list(root: object, **kw: Any) -> tuple[object, ...]:
        arguments.update(kw)
        assert root == tmp_path
        return (SimpleNamespace(revision=record),)

    monkeypatch.setattr(command, "list_current_arrangements", fake_list)
    ns = build_parser().parse_args(["saved-grouping", "list", *_base()])
    assert command.handle_list(ns) == 0
    output = capsys.readouterr().out
    assert "Six Table Groups" in output
    assert "groups=1" in output
    assert "assigned=1" in output
    assert "student-1" not in output
    assert arguments == {
        "class_id": CLASS,
        "school_year": "2026-2027",
        "actor_id": ACTOR,
    }


def test_show_members_requires_explicit_opt_in(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(command, "_scope", lambda _args: ("2026-2027", tmp_path))
    monkeypatch.setattr(
        command,
        "load_current_arrangement",
        lambda *_a, **_k: SimpleNamespace(revision=_revision()),
    )
    args = ["saved-grouping", "show", *_base(), "--arrangement-id", "tables-six"]
    assert command.handle_show(build_parser().parse_args(args)) == 0
    output = capsys.readouterr().out
    assert "Table A" in output
    assert "student-1" not in output
    assert "student-2" not in output
    assert (
        command.handle_show(build_parser().parse_args([*args, "--show-members"])) == 0
    )
    output = capsys.readouterr().out
    assert "Student ID: student-1" in output
    assert "Unresolved student ID: student-2" in output


def test_roster_diff_is_read_only_and_gives_exact_decision_ids(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(command, "_scope", lambda _args: ("2026-2027", tmp_path))
    monkeypatch.setattr(
        command,
        "review_arrangement_roster",
        lambda *_a, **_kw: (
            SimpleNamespace(revision=_revision()),
            SimpleNamespace(
                retained_assigned_count=1,
                newly_enrolled_ids=("student-3",),
                departed_ids=("student-2",),
                unresolved_ids=("student-4",),
            ),
        ),
    )
    monkeypatch.setattr(
        command,
        "reuse_grouping",
        lambda *_a, **_kw: pytest.fail("roster diff wrote Activity data"),
    )
    args = build_parser().parse_args(
        ["saved-grouping", "roster-diff", *_base(), "--arrangement-id", "tables-six"]
    )
    assert command.handle_roster_diff(args) == 0
    output = capsys.readouterr().out
    assert "student-3" in output
    assert "student-2" in output
    assert "student-4" in output
    assert "Writes: none" in output


def test_save_preview_only_reads_and_passes_exact_request(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    capture: list[object] = []
    preview = SimpleNamespace(
        name="Six Table Groups",
        arrangement_id="tables-six",
        source_activity_id=ACTIVITY,
        source_plan_id="plan-source",
        groups=(_group("Table A", "a", "student-1"),),
        assigned_count=1,
        unresolved_student_ids=("student-2",),
        review_digest="a" * 64,
    )
    monkeypatch.setattr(
        command,
        "prepare_save_grouping",
        lambda request, **_kw: capture.append(request) or preview,
    )
    monkeypatch.setattr(
        command,
        "save_grouping",
        lambda *_a, **_kw: pytest.fail("preview attempted a write"),
    )
    assert command.handle_save_preview(_save_args("save-preview")) == 0
    assert getattr(capture[0], "expected_snapshot_revision") == 9
    assert getattr(capture[0], "actor").actor_id == ACTOR
    assert "Writes: none" in capsys.readouterr().out


def test_save_commit_forwards_review_digest_without_reconstructing_it(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    capture: list[tuple[object, str]] = []

    def save(request: object, *, review_digest: str, **_kw: Any) -> object:
        capture.append((request, review_digest))
        return SimpleNamespace(revision=_revision(), sha256="d" * 64)

    monkeypatch.setattr(command, "save_grouping", save)
    assert command.handle_save(_save_args("save")) == 0
    assert capture[0][1] == "c" * 64
    assert getattr(capture[0][0], "group_plan_id") == "plan-source"
    assert "Source Activity unchanged: yes" in capsys.readouterr().out


def test_reuse_preview_requires_exact_explicit_roster_decisions(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    requests: list[object] = []
    preview = SimpleNamespace(
        arrangement_id="tables-six",
        arrangement_revision=1,
        target_activity_id="activity-target",
        new_group_plan_id="plan-target",
        groups=(_group("Table A", "table-a", "student-1"),),
        assigned_count=1,
        unresolved_student_ids=("student-3",),
        added_student_ids=("student-3",),
        departed_student_ids=("student-2",),
        review_digest="f" * 64,
    )
    monkeypatch.setattr(
        command,
        "prepare_reuse_grouping",
        lambda req, **_kw: requests.append(req) or preview,
    )
    monkeypatch.setattr(
        command,
        "reuse_grouping",
        lambda *_a, **_kw: pytest.fail("preview attempted a write"),
    )
    args = _reuse_args(
        "reuse-preview",
        "--place",
        "student-4=table-a",
        "--leave-unresolved",
        "student-3",
        "--acknowledge-departed",
        "student-2",
        "--acknowledge-existing-plans",
    )
    assert command.handle_reuse_preview(args) == 0
    req = requests[0]
    assert req.expected_snapshot_revision == 6
    assert req.placement_decisions[0].student_id == "student-4"
    assert req.placement_decisions[0].group_key == "table-a"
    assert req.placement_decisions[1].student_id == "student-3"
    assert req.placement_decisions[1].group_key is None
    assert req.acknowledged_departed_student_ids == ("student-2",)
    assert req.acknowledge_existing_plans is True
    assert "Writes: none" in capsys.readouterr().out


def test_detailed_reuse_preview_requires_explicit_option(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    preview = SimpleNamespace(
        arrangement_id="tables-six",
        arrangement_revision=1,
        target_activity_id="activity-target",
        new_group_plan_id="plan-target",
        groups=(_group("Table A", "table-a", "student-1"),),
        assigned_count=1,
        unresolved_student_ids=("student-2",),
        added_student_ids=(),
        departed_student_ids=(),
        review_digest="e" * 64,
    )
    monkeypatch.setattr(command, "prepare_reuse_grouping", lambda *_a, **_kw: preview)
    assert command.handle_reuse_preview(_reuse_args("reuse-preview")) == 0
    assert "student-1" not in capsys.readouterr().out
    assert (
        command.handle_reuse_preview(_reuse_args("reuse-preview", "--show-placements"))
        == 0
    )
    output = capsys.readouterr().out
    assert "Student ID: student-1" in output
    assert "Unresolved student ID: student-2" in output


def test_reuse_commit_forwards_review_digest_and_canonical_standards(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    library = object()
    requests: list[tuple[object, dict[str, Any]]] = []
    monkeypatch.setattr(command, "load_command_standards_library", lambda _a: library)

    def reuse(request: object, **kw: Any) -> object:
        requests.append((request, kw))
        return SimpleNamespace(
            group_plan_id="plan-target",
            status="draft",
            commit=SimpleNamespace(snapshot_revision=7),
        )

    monkeypatch.setattr(command, "reuse_grouping", reuse)
    assert command.handle_reuse(_reuse_args("reuse")) == 0
    req, kw = requests[0]
    assert req.actor.actor_id == ACTOR
    assert kw["review_digest"] == "b" * 64
    assert kw["standards_library"] is library
    assert "Canonical Groups/Memberships created: no" in capsys.readouterr().out


@pytest.mark.parametrize(
    "extra",
    [
        ("--place", "invalid"),
        ("--place", "=group-a"),
        ("--place", "student-1="),
        ("--place", "student-1=group-a", "--place", "student-1=group-b"),
        ("--place", "student-1=group-a", "--leave-unresolved", "student-1"),
        ("--leave-unresolved", "student-1", "--leave-unresolved", "student-1"),
    ],
)
def test_duplicate_or_malformed_decisions_fail_before_service(
    extra: tuple[str, ...],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        command,
        "prepare_reuse_grouping",
        lambda *_a, **_kw: pytest.fail("invalid input reached service"),
    )
    with pytest.raises(ConcordWorkflowValidationError):
        command.handle_reuse_preview(_reuse_args("reuse-preview", *extra))


def test_cli_conflict_and_storage_errors_have_stable_exit_codes(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    arguments = ["saved-grouping", "list", *_base()]

    def conflict(_args: Namespace) -> int:
        raise ArrangementConflictError("synthetic concurrent write")

    monkeypatch.setattr(command, "handle_list", conflict)
    assert cli_main(arguments) == 3
    assert "Conflict:" in capsys.readouterr().err

    def read_error(_args: Namespace) -> int:
        raise ArrangementStorageError("synthetic unreadable storage")

    monkeypatch.setattr(command, "handle_list", read_error)
    assert cli_main(arguments) == 1
    assert "Error:" in capsys.readouterr().err
