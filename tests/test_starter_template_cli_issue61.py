from __future__ import annotations

from pathlib import Path

import pytest

from concord.cli_app.main import EXIT_OK, main
from concord.template_storage import load_current_template


def _actor() -> tuple[str, ...]:
    return ("--actor-id", "teacher-1")


def test_starter_list_and_show_are_read_only_for_absent_workspace(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "absent"

    assert main(
        (
            "template",
            "starter-list",
            "--workspace-root",
            str(root),
        )
    ) == EXIT_OK
    output = capsys.readouterr().out
    assert "think_pair_share: Think–Pair–Share Quick Sheet" in output
    assert "team_health_check: Team Health / Contribution Check" in output
    assert "status=missing" in output
    assert not root.exists()

    assert main(
        (
            "template",
            "starter-show",
            "--workspace-root",
            str(root),
            "--starter-key",
            "structured_academic_controversy",
        )
    ) == EXIT_OK
    output = capsys.readouterr().out
    assert "Starter: structured_academic_controversy" in output
    assert "Pages: 2" in output
    assert "Expected Return: returned_expected" in output
    assert "Installation State: missing" in output
    assert not root.exists()


def test_starter_install_one_is_explicit_and_idempotent(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "workspace"

    assert main(
        (
            "template",
            "starter-install",
            "--workspace-root",
            str(root),
            *_actor(),
            "--starter-key",
            "venn_comparison",
        )
    ) == EXIT_OK
    output = capsys.readouterr().out
    assert "Starter: venn_comparison" in output
    assert "Outcome: installed" in output
    loaded = load_current_template(root, "starter-venn-comparison")
    assert loaded.definition.status == "active"
    assert loaded.current_template_version_id == "starter-venn-comparison-v1"

    assert main(
        (
            "template",
            "starter-install",
            "--workspace-root",
            str(root),
            *_actor(),
            "--starter-key",
            "venn_comparison",
        )
    ) == EXIT_OK
    assert "Outcome: already_installed" in capsys.readouterr().out
    replay = load_current_template(root, "starter-venn-comparison")
    assert replay.snapshot_revision == loaded.snapshot_revision
    assert replay.snapshot_sha256 == loaded.snapshot_sha256


def test_starter_install_all_installs_only_missing(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "workspace"

    assert main(
        (
            "template",
            "starter-install",
            "--workspace-root",
            str(root),
            *_actor(),
            "--starter-key",
            "think_pair_share",
        )
    ) == EXIT_OK
    capsys.readouterr()

    assert main(
        (
            "template",
            "starter-install-all",
            "--workspace-root",
            str(root),
            *_actor(),
        )
    ) == EXIT_OK
    output = capsys.readouterr().out
    assert "Installed: 29" in output
    assert "Already installed: 1" in output
    assert "Processed: 30" in output

    assert main(
        (
            "template",
            "starter-install-all",
            "--workspace-root",
            str(root),
            *_actor(),
        )
    ) == EXIT_OK
    output = capsys.readouterr().out
    assert "Installed: 0" in output
    assert "Already installed: 30" in output
