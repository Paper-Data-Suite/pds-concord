from __future__ import annotations

from types import SimpleNamespace

import pytest

from concord import menu_template
from concord.cli_app.handlers import starter_template as starter_cli
from concord.cli_app.main import EXIT_OK, main
from concord.menu_context import MenuSessionContext
from concord.workflows.models import WorkflowActor
from concord.workflows.starter_template import (
    STARTER_INSTALLATION_UPGRADE_AVAILABLE,
    get_starter_template_status,
)


def _state() -> MenuSessionContext:
    return MenuSessionContext(actor=WorkflowActor(actor_id="teacher-1"))


def test_relationship_aware_starter_detail_distinguishes_initial_and_current(
    tmp_path,
) -> None:
    status = get_starter_template_status(
        "peer_review_writing",
        workspace_root=tmp_path / "absent",
    )
    lines = menu_template._starter_detail_lines(status)

    assert "Initial Version: starter-peer-review-writing-v1" in lines
    assert "Package Current Version: starter-peer-review-writing-v2" in lines
    assert "Initial v1 Authorship: individual_author" in lines
    assert "Initial v1 Subject: core_student" in lines
    assert status.installation_state == "missing"
    assert not (tmp_path / "absent").exists()


def test_starter_show_reports_package_current_successor_read_only(
    tmp_path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "absent"
    assert main(
        (
            "template",
            "starter-show",
            "--workspace-root",
            str(root),
            "--starter-key",
            "peer_review_writing",
        )
    ) == EXIT_OK

    output = capsys.readouterr().out
    assert "Initial Version: starter-peer-review-writing-v1" in output
    assert "Package Current Version: starter-peer-review-writing-v2" in output
    assert (
        "Packaged Lineage: starter-peer-review-writing-v1 -> "
        "starter-peer-review-writing-v2"
    ) in output
    assert "Initial v1 Subject: core_student" in output
    assert "Installation State: missing" in output
    assert not root.exists()


def test_install_all_results_report_upgrades_separately(
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = SimpleNamespace(
        installed_count=1,
        upgraded_count=2,
        already_installed_count=27,
        results=(),
    )

    assert menu_template._starter_install_all_lines(result) == (
        "Installed: 1",
        "Upgraded: 2",
        "Already current: 27",
        "Processed: 0",
    )
    starter_cli._print_install_all_result(result)
    output = capsys.readouterr().out
    assert "Installed: 1" in output
    assert "Upgraded: 2" in output
    assert "Already current: 27" in output


def test_single_starter_upgrade_confirmation_describes_append_only_successor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    status = SimpleNamespace(
        starter_key="peer_review_writing",
        family="peer_feedback",
        display_name="Peer Review — Writing",
        template_id="starter-peer-review-writing",
        template_version_id="starter-peer-review-writing-v2",
        page_count=2,
        orientation="portrait",
        installation_state=STARTER_INSTALLATION_UPGRADE_AVAILABLE,
    )
    prepared = SimpleNamespace(
        initial_state=STARTER_INSTALLATION_UPGRADE_AVAILABLE,
    )
    captured: list[tuple[str, str, tuple[str, ...]]] = []

    monkeypatch.setattr(
        menu_template,
        "_choose_starter",
        lambda *, title: status,
    )
    monkeypatch.setattr(
        menu_template,
        "prepare_starter_template_install",
        lambda _request: prepared,
    )

    def confirm(title: str, expected: str, lines) -> bool:
        captured.append((title, expected, tuple(lines)))
        return False

    monkeypatch.setattr(menu_template, "confirm_write", confirm)

    menu_template._install_starter(_state())

    assert len(captured) == 1
    title, expected, lines = captured[0]
    assert title == "Install / Update Starter Template"
    assert expected == "INSTALL"
    assert any("successor Version will be appended" in line for line in lines)
    assert any("remain immutable and loadable" in line for line in lines)
    assert any(
        "Package Current Version after update: starter-peer-review-writing-v2"
        == line
        for line in lines
    )
