from __future__ import annotations

from types import SimpleNamespace

import pytest

from concord import menu_template
from concord.menu_context import MenuSessionContext
from concord.menu_navigation import QuitPDS, ReturnToMainMenu
from concord.workflows.models import WorkflowActor


def _state() -> MenuSessionContext:
    return MenuSessionContext(
        actor=WorkflowActor(actor_id="teacher-1")
    )


def test_template_library_menu_lists_all_management_surfaces(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("builtins.input", lambda _prompt="": "B")
    menu_template.launch_template_library_menu(_state())
    output = capsys.readouterr().out
    assert "1. List / select Templates" in output
    assert "2. Create Template" in output
    assert "3. View Template and version history" in output
    assert "4. Create successor version" in output
    assert "5. Activate current version" in output
    assert "6. Update Template metadata" in output
    assert "7. Retire version" in output
    assert "8. Retire Template" in output


@pytest.mark.parametrize(
    ("key", "expected"),
    (("M", ReturnToMainMenu), ("Q", QuitPDS)),
)
def test_template_menu_navigation_unwinds(
    key: str,
    expected: type[BaseException],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("builtins.input", lambda _prompt="": key)
    with pytest.raises(expected):
        menu_template.launch_template_library_menu(_state())


def test_template_create_menu_requires_create_confirmation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepared = SimpleNamespace(
        definition=SimpleNamespace(
            template_id="template-1",
            name="Reusable Template",
        ),
        version=SimpleNamespace(
            template_version_id="version-1",
            version_label="v1",
            artifact_category="discussion_record",
            page_manifest=(object(),),
            default_expected_return_status="return_not_expected",
            default_privacy_policy=SimpleNamespace(
                classification="teacher_restricted"
            ),
            rendering_contract_version="rendering-v1",
            rendering_specification_reference="rendering-ref",
            status="draft",
        ),
        rendering_source=SimpleNamespace(sha256="a" * 64),
    )
    captured = []
    committed_result = SimpleNamespace(
        template_id="template-1",
        status="draft",
        snapshot_revision=1,
        snapshot_sha256="b" * 64,
        current_template_version_id=None,
        head_template_version_id="version-1",
        workspace_created=False,
    )
    monkeypatch.setattr(
        menu_template,
        "prepare_template_create",
        lambda request: captured.append(("prepare", request)) or prepared,
    )
    monkeypatch.setattr(
        menu_template,
        "commit_template_create",
        lambda value: (
            captured.append(("commit", value)) or committed_result
        ),
    )
    answers = iter(
        (
            "2",
            "template-1",
            "version-1",
            "authoring.json",
            "rendering.bin",
            "1",
            "CREATE",
            "",
            "B",
        )
    )
    monkeypatch.setattr(
        "builtins.input",
        lambda _prompt="": next(answers),
    )
    menu_template.launch_template_library_menu(_state())
    assert [kind for kind, _ in captured] == ["prepare", "commit"]


def test_template_create_menu_cancel_writes_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepared = SimpleNamespace(
        definition=SimpleNamespace(
            template_id="template-1",
            name="Reusable Template",
        ),
        version=SimpleNamespace(
            template_version_id="version-1",
            version_label="v1",
            artifact_category="discussion_record",
            page_manifest=(object(),),
            default_expected_return_status="return_not_expected",
            default_privacy_policy=SimpleNamespace(
                classification="teacher_restricted"
            ),
            rendering_contract_version="rendering-v1",
            rendering_specification_reference="rendering-ref",
            status="draft",
        ),
        rendering_source=SimpleNamespace(sha256="a" * 64),
    )
    committed = []
    monkeypatch.setattr(
        menu_template,
        "prepare_template_create",
        lambda request: prepared,
    )
    monkeypatch.setattr(
        menu_template,
        "commit_template_create",
        lambda value: committed.append(value),
    )
    answers = iter(
        (
            "2",
            "template-1",
            "version-1",
            "authoring.json",
            "rendering.bin",
            "1",
            "",
            "B",
        )
    )
    monkeypatch.setattr(
        "builtins.input",
        lambda _prompt="": next(answers),
    )
    menu_template.launch_template_library_menu(_state())
    assert committed == []


def test_main_menu_exposes_workspace_level_template_library(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from concord import menu

    answers = iter(("Q",))
    monkeypatch.setattr(
        "builtins.input",
        lambda _prompt="": next(answers),
    )
    assert menu.launch_menu() == 0
    output = capsys.readouterr().out
    assert "5. Template Library" in output
