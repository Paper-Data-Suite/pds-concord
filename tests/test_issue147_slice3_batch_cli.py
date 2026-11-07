"""#147 Slice 3: direct CLI parity with the canonical one-write bulk service."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from test_issue147_slice1_bulk_engine import _history, _setup

from concord.cli import build_parser, main
from concord.workflows import show_group_plan


def _batch_command(
    root: Path,
    snapshot: int,
    revision: int,
    command: str,
    *,
    operation: str = "place_or_move",
    target: str = "a",
    selected: tuple[str, ...] = ("student-2", "student-3"),
    actor: str = "teacher-1",
) -> list[str]:
    args = [
        "group-plan", command, "--workspace-root", str(root),
        "--class-id", "class-1", "--activity-id", "activity-1",
        "--group-plan-id", "plan-1", "--planned-group-key", target,
        "--operation", operation,
        "--expected-snapshot", str(snapshot),
        "--expected-record-revision", str(revision),
        "--actor-id", actor,
    ]
    for student in selected:
        args.extend(("--student-id", student))
    return args


def _digest(output: str) -> str:
    match = re.search(r"^Review digest: ([0-9a-f]{64})$", output, re.M)
    assert match, output
    return match.group(1)


def test_parser_registers_both_commands_and_rejects_missing_arguments() -> None:
    parser = build_parser()
    for command in ("batch-place-preview", "batch-place"):
        with pytest.raises(SystemExit) as help_exit:
            parser.parse_args(("group-plan", command, "--help"))
        assert help_exit.value.code == 0
        with pytest.raises(SystemExit) as missing:
            parser.parse_args(("group-plan", command))
        assert missing.value.code == 2


def test_read_only_preview_and_one_write_commit(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root, snapshot, revision = _setup(tmp_path)
    before = _history(root)
    capsys.readouterr()
    preview_command = _batch_command(root, snapshot, revision, "batch-place-preview")
    assert main(preview_command) == 0
    preview = capsys.readouterr().out
    digest = _digest(preview)
    assert "GroupPlan: plan-1" in preview
    assert "Selected students: 2" in preview
    assert "student-2: b -> a" in preview
    assert "student-3: unresolved -> a" in preview
    assert "Unresolved: 1 -> 0" in preview
    assert "No changes have been written." in preview
    assert _history(root) == before

    commit_command = _batch_command(root, snapshot, revision, "batch-place")
    assert main([*commit_command, "--review-digest", digest]) == 0
    output = capsys.readouterr().out
    assert "Committed snapshot" in output
    assert "Canonical Groups created: no" in output
    assert "Status: draft" in output
    detail = show_group_plan("class-1", "activity-1", "plan-1", workspace_root=root)
    assert detail.plan.proposed_groups[0].student_ids == (
        "student-1", "student-2", "student-3"
    )
    assert detail.plan.proposed_groups[1].student_ids == ()
    assert _history(root) == (before[0] + 1, before[1] + 1)
    assert main([*commit_command, "--review-digest", digest]) == 3
    assert "Conflict:" in capsys.readouterr().err
    assert _history(root) == (before[0] + 1, before[1] + 1)


def test_wrong_digest_actor_and_duplicate_ids_fail_closed(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root, snapshot, revision = _setup(tmp_path)
    before = _history(root)
    base = _batch_command(root, snapshot, revision, "batch-place")
    assert main([*base, "--review-digest", "0" * 64]) == 3
    assert "Conflict:" in capsys.readouterr().err
    assert _history(root) == before

    preview_command = _batch_command(root, snapshot, revision, "batch-place-preview")
    assert main(preview_command) == 0
    digest = _digest(capsys.readouterr().out)
    altered_actor = _batch_command(
        root, snapshot, revision, "batch-place", actor="teacher-other"
    )
    assert main([*altered_actor, "--review-digest", digest]) == 3
    assert "Conflict:" in capsys.readouterr().err
    assert _history(root) == before

    duplicates = _batch_command(
        root, snapshot, revision, "batch-place-preview",
        selected=("student-2", "student-2"),
    )
    assert main(duplicates) == 1
    assert "duplicate" in capsys.readouterr().err
    assert _history(root) == before


def test_unassign_and_noop_do_not_change_core_roster(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root, snapshot, revision = _setup(tmp_path)
    capsys.readouterr()
    before = _history(root)
    args = dict(
        operation="unassign_from_target", selected=("student-1",), target="a"
    )
    preview_args = _batch_command(
        root, snapshot, revision, "batch-place-preview", **args
    )
    assert main(preview_args) == 0
    digest = _digest(capsys.readouterr().out)
    assert main([
        *_batch_command(root, snapshot, revision, "batch-place", **args),
        "--review-digest", digest,
    ]) == 0
    assert "Canonical Groups created: no" in capsys.readouterr().out
    detail = show_group_plan("class-1", "activity-1", "plan-1", workspace_root=root)
    assert detail.plan.unresolved_student_ids == ("student-1", "student-3")
    assert _history(root) == (before[0] + 1, before[1] + 1)
    from pds_core.classes import load_class_roster

    assert len(load_class_roster(root, "class-1").students) == 3

    before_noop = _history(root)
    no_op = dict(target="b", selected=("student-2",))
    no_op_preview = _batch_command(
        root, detail.summary.snapshot_revision, detail.record_revision,
        "batch-place-preview", **no_op,
    )
    assert main(no_op_preview) == 0
    output = capsys.readouterr().out
    digest = _digest(output)
    assert "No proposed changes: yes" in output
    assert main([
        *_batch_command(
            root, detail.summary.snapshot_revision, detail.record_revision,
            "batch-place", **no_op,
        ), "--review-digest", digest,
    ]) == 0
    assert "No changes were needed." in capsys.readouterr().out
    assert _history(root) == before_noop


def test_wrong_roster_or_stale_revision_refuses_without_write(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root, snapshot, revision = _setup(tmp_path)
    before = _history(root)
    wrong = _batch_command(root, snapshot, revision + 1, "batch-place-preview")
    assert main(wrong) == 3
    assert "Conflict:" in capsys.readouterr().err
    assert _history(root) == before

    from pds_core.classes import write_class_roster
    from test_group_plan_manual_issue51 import _roster

    write_class_roster(
        root, _roster("student-1", "student-2", "student-4"), overwrite=True
    )
    stale = _batch_command(root, snapshot, revision, "batch-place-preview")
    assert main(stale) == 3
    assert "Core roster" in capsys.readouterr().err
    assert _history(root) == before


def test_cli_explicit_identity_and_digest_format(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root, snapshot, revision = _setup(tmp_path)
    before = _history(root)
    capsys.readouterr()
    args = _batch_command(
        root, snapshot, revision, "batch-place-preview",
        selected=("student-3", "student-2"),
    )
    assert main(args) == 0
    a = capsys.readouterr().out
    assert main(args) == 0
    b = capsys.readouterr().out
    assert _digest(a) == _digest(b)
    assert "Snapshot revision: " in a
    assert "Record revision: " in a
    assert "Core roster changed: no" not in a
    assert "No changes have been written." in a
    # Two previews are read-only and produce no additional GroupPlan records.
    assert _history(root) == before
