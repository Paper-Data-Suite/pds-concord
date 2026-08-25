from __future__ import annotations

from types import SimpleNamespace

import pytest

from concord import menu_template
from concord.menu_context import MenuSessionContext
from concord.workflows.models import WorkflowActor


def _state() -> MenuSessionContext:
    return MenuSessionContext(actor=WorkflowActor(actor_id="teacher-1"))


def test_template_library_menu_exposes_starter_library(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("builtins.input", lambda _prompt="": "B")
    menu_template.launch_template_library_menu(_state())
    assert "9. Browse / install starter Templates" in capsys.readouterr().out


def test_starter_library_submenu_lists_surfaces(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    answers = iter(("9", "B", "B"))
    monkeypatch.setattr(
        "builtins.input",
        lambda _prompt="": next(answers),
    )
    menu_template.launch_template_library_menu(_state())
    output = capsys.readouterr().out
    assert "Starter Template Library" in output
    assert "1. Browse / preview starter Templates" in output
    assert "2. Install one starter Template" in output
    assert "3. Install all missing starter Templates" in output


def test_starter_install_menu_requires_install_confirmation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    status = SimpleNamespace(
        starter_key="think_pair_share",
        family="discussion",
        display_name="Think-Pair-Share Quick Sheet",
        template_id="starter-think-pair-share",
        template_version_id="starter-think-pair-share-v1",
        page_count=1,
        orientation="portrait",
        installation_state="missing",
    )
    entry = SimpleNamespace(
        starter_key="think_pair_share",
        family="discussion",
        display_name="Think-Pair-Share Quick Sheet",
        purpose="Structure individual, partner, and class-ready thinking.",
        description="Synthetic starter.",
        template_id="starter-think-pair-share",
        template_version_id="starter-think-pair-share-v1",
        artifact_category="discussion_record",
        page_count=1,
        orientation="portrait",
        default_privacy_classification="group_and_teacher",
        suggested_audience_kinds=("group",),
        suggested_activity_type_keys=(),
        default_authorship_mode="collective_group_author",
        default_subject_kind="concord_group",
        rendering_specification_reference=(
            "starter-think-pair-share-layout-v1"
        ),
        rendering_sha256=lambda: "a" * 64,
    )
    prepared = SimpleNamespace(
        entry=entry,
        initial_state="missing",
    )
    result = SimpleNamespace(
        starter_key="think_pair_share",
        template_id="starter-think-pair-share",
        template_version_id="starter-think-pair-share-v1",
        outcome="installed",
        snapshot_revision=1,
        snapshot_sha256="b" * 64,
        workspace_created=False,
    )
    captured: list[tuple[str, object]] = []
    monkeypatch.setattr(
        menu_template,
        "list_starter_template_statuses",
        lambda: (status,),
    )
    monkeypatch.setattr(
        menu_template,
        "get_starter_template",
        lambda _key: entry,
    )
    monkeypatch.setattr(
        menu_template,
        "prepare_starter_template_install",
        lambda request: captured.append(("prepare", request)) or prepared,
    )
    monkeypatch.setattr(
        menu_template,
        "commit_starter_template_install",
        lambda value: captured.append(("commit", value)) or result,
    )

    answers = iter(("9", "2", "1", "INSTALL", "", "B", "B"))
    monkeypatch.setattr(
        "builtins.input",
        lambda _prompt="": next(answers),
    )
    menu_template.launch_template_library_menu(_state())
    assert [kind for kind, _ in captured] == ["prepare", "commit"]


def test_starter_install_cancel_writes_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    status = SimpleNamespace(
        starter_key="think_pair_share",
        family="discussion",
        display_name="Think-Pair-Share Quick Sheet",
        template_id="starter-think-pair-share",
        template_version_id="starter-think-pair-share-v1",
        page_count=1,
        orientation="portrait",
        installation_state="missing",
    )
    entry = SimpleNamespace(
        starter_key="think_pair_share",
        family="discussion",
        display_name="Think-Pair-Share Quick Sheet",
        purpose="Purpose",
        description="Description",
        template_id="starter-think-pair-share",
        template_version_id="starter-think-pair-share-v1",
        artifact_category="discussion_record",
        page_count=1,
        orientation="portrait",
        default_privacy_classification="group_and_teacher",
        suggested_audience_kinds=("group",),
        suggested_activity_type_keys=(),
        default_authorship_mode="collective_group_author",
        default_subject_kind="concord_group",
        rendering_specification_reference=(
            "starter-think-pair-share-layout-v1"
        ),
        rendering_sha256=lambda: "a" * 64,
    )
    prepared = SimpleNamespace(entry=entry, initial_state="missing")
    committed: list[object] = []
    monkeypatch.setattr(
        menu_template,
        "list_starter_template_statuses",
        lambda: (status,),
    )
    monkeypatch.setattr(
        menu_template,
        "get_starter_template",
        lambda _key: entry,
    )
    monkeypatch.setattr(
        menu_template,
        "prepare_starter_template_install",
        lambda request: prepared,
    )
    monkeypatch.setattr(
        menu_template,
        "commit_starter_template_install",
        lambda value: committed.append(value),
    )

    answers = iter(("9", "2", "1", "", "B", "B"))
    monkeypatch.setattr(
        "builtins.input",
        lambda _prompt="": next(answers),
    )
    menu_template.launch_template_library_menu(_state())
    assert committed == []
