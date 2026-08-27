from __future__ import annotations

import re
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.routing_models import ModuleWorkRef
from pds_core.workspace import ensure_workspace_root

from concord.cli import main
from concord.menu_activity import (
    _confirm_copy,
    _copy_review_lines,
    launch_activity_management_menu,
)
from concord.models import PrivacyPolicy
from concord.storage import load_current_record_graph
from concord.workflows import PreparedActivityCopy


def _inputs(monkeypatch: pytest.MonkeyPatch, values: list[str]) -> None:
    iterator: Iterator[str] = iter(values)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(iterator))


@pytest.fixture
def copy_cli_workspace(tmp_path: Path) -> Path:
    root = ensure_workspace_root(tmp_path / "workspace")
    for class_id in ("class-source", "class-target"):
        metadata = create_class_metadata(
            class_id,
            "2026-2027",
            created_at=datetime(2026, 8, 26, tzinfo=timezone.utc),
        )
        write_class_metadata_for_class(root, metadata)
    return root


def _create_source(root: Path) -> None:
    assert (
        main(
            [
                "activity",
                "create",
                "--workspace-root",
                str(root),
                "--class-id",
                "class-source",
                "--activity-id",
                "activity-source",
                "--title",
                "Source Seminar",
                "--description",
                "Source description",
                "--activity-type",
                "socratic_seminar",
                "--scoring-orientation",
                "evidence_only",
                "--session-id",
                "source-session",
                "--actor-id",
                "teacher-1",
            ]
        )
        == 0
    )


def _copy_args(root: Path) -> list[str]:
    return [
        "--workspace-root",
        str(root),
        "--source-class-id",
        "class-source",
        "--source-activity-id",
        "activity-source",
        "--target-class-id",
        "class-target",
        "--target-activity-id",
        "activity-copy",
        "--title",
        "Copied Seminar",
        "--clear-description",
        "--session-id",
        "copy-session",
        "--session-label",
        "Opening Copy Session",
        "--actor-id",
        "teacher-1",
    ]


def test_direct_copy_preview_and_copy_are_noninteractive(
    copy_cli_workspace: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _create_source(copy_cli_workspace)
    capsys.readouterr()
    monkeypatch.setattr(
        "builtins.input",
        lambda *_args, **_kwargs: pytest.fail("direct Activity copy must not prompt"),
    )

    assert main(["activity", "copy-preview", *_copy_args(copy_cli_workspace)]) == 0
    preview = capsys.readouterr()
    assert preview.err == ""
    assert "Source Activity: class-source/activity-source" in preview.out
    assert "Target Activity: class-target/activity-copy" in preview.out
    assert "Target status: draft" in preview.out
    assert "Description: -" in preview.out
    assert "Will not copy:" in preview.out
    digest_match = re.search(r"Review digest: ([0-9a-f]{64})", preview.out)
    assert digest_match is not None
    digest = digest_match.group(1)

    assert (
        main(
            [
                "activity",
                "copy",
                *_copy_args(copy_cli_workspace),
                "--review-digest",
                digest,
            ]
        )
        == 0
    )
    committed = capsys.readouterr()
    assert committed.err == ""
    assert "Committed snapshot 1." in committed.out
    assert "First Session: copy-session" in committed.out
    assert f"Review digest: {digest}" in committed.out

    target = load_current_record_graph(
        copy_cli_workspace,
        ModuleWorkRef("concord", "class-target", "activity-copy"),
    )
    assert len(target.graph.activities) == 1
    assert len(target.graph.sessions) == 1
    assert not target.graph.groups
    activity = target.graph.activities[0]
    session = target.graph.sessions[0]
    assert activity.title == "Copied Seminar"
    assert activity.description is None
    assert activity.status == "draft"
    assert session.session_id == "copy-session"
    assert session.status == "planned"


def test_direct_copy_requires_exact_review_digest(
    copy_cli_workspace: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _create_source(copy_cli_workspace)
    capsys.readouterr()
    result = main(
        [
            "activity",
            "copy",
            *_copy_args(copy_cli_workspace),
            "--review-digest",
            "0" * 64,
        ]
    )
    captured = capsys.readouterr()
    assert result == 3
    assert "Conflict:" in captured.err
    assert "review is stale" in captured.err


def test_activity_copy_commands_have_help() -> None:
    for arguments in (
        ["activity", "copy-preview", "--help"],
        ["activity", "copy", "--help"],
    ):
        with pytest.raises(SystemExit) as exit_info:
            main(arguments)
        assert exit_info.value.code == 0


def test_activity_management_exposes_copy(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _inputs(monkeypatch, ["b"])
    monkeypatch.setattr("concord.menu_activity.clear_screen", lambda: None)
    launch_activity_management_menu()
    output = capsys.readouterr().out
    assert "1. Create an Activity" in output
    assert "2. Copy an Activity" in output
    assert "3. List Activities" in output
    assert "4. Open an Activity" in output


def test_copy_review_lines_show_config_ordered_standards_and_exclusions() -> None:
    prepared = PreparedActivityCopy(
        source_class_id="class-source",
        source_activity_id="activity-source",
        source_status="completed",
        target_class_id="class-target",
        target_activity_id="activity-copy",
        title="Copied title",
        description="Copied description",
        activity_type="project",
        scoring_orientation="standards_based",
        standards_profile_id="profile-1",
        focus_standard_ids=("standard-b", "standard-a"),
        privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
        first_session_id="session-copy",
        first_session_label="Opening",
        diagnostics=(),
        excluded_state=("source Groups",),
        review_digest="a" * 64,
    )
    lines = _copy_review_lines(prepared)
    assert "Source status (not copied): completed" in lines
    assert "Description: Copied description" in lines
    start = lines.index("Focus Standards (ordered):")
    assert lines[start + 1 : start + 3] == (
        "  1. standard-b",
        "  2. standard-a",
    )
    assert any(line.startswith("NOT COPIED:") for line in lines)


def test_copy_confirmation_requires_uppercase_copy(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _inputs(monkeypatch, ["copy", "", "COPY"])
    monkeypatch.setattr("concord.menu_activity.clear_screen", lambda: None)
    assert _confirm_copy(("Target: class-target/activity-copy",))
    output = capsys.readouterr().out
    assert "Type uppercase COPY exactly" in output
