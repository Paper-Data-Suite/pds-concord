from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from concord.menu import _main_menu_once
from concord.menu_context import MenuSessionContext
from concord.menu_presets import launch_preset_library_menu
from concord.menu_responsibility import launch_responsibility_menu
from concord.menu_role import launch_role_menu
from concord.menu_scoring import _criterion_set_menu, _scale_menu, launch_scoring_menu
from concord.workflows import ActivitySummary


def _inputs(monkeypatch: pytest.MonkeyPatch, values: list[str]) -> None:
    iterator: Iterator[str] = iter(values)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(iterator))


def _activity() -> ActivitySummary:
    return ActivitySummary(
        class_id="class-1",
        activity_id="activity-1",
        title="Synthetic Preset Activity",
        status="draft",
        scoring_orientation="local_criteria_only",
        session_count=1,
        group_count=0,
        snapshot_revision=1,
    )


def _disable_clear(monkeypatch: pytest.MonkeyPatch, module: str) -> None:
    monkeypatch.setattr(f"{module}.clear_screen", lambda: None)


def test_main_menu_exposes_workspace_preset_library(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    called: list[MenuSessionContext] = []
    state = MenuSessionContext()
    _inputs(monkeypatch, ["7"])
    _disable_clear(monkeypatch, "concord.menu")
    monkeypatch.setattr(
        "concord.menu.launch_preset_library_menu",
        lambda received: called.append(received),
    )

    assert _main_menu_once(state)
    output = capsys.readouterr().out
    assert "7. Reusable Presets" in output
    assert called == [state]


def test_preset_library_hides_revision_mechanics_in_routine_menu(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _inputs(monkeypatch, ["b"])
    _disable_clear(monkeypatch, "concord.menu_presets")

    launch_preset_library_menu(MenuSessionContext())
    output = capsys.readouterr().out
    assert "Reusable Presets" in output
    assert "1. Roles" in output
    assert "2. Responsibilities" in output
    assert "3. Criterion Sets" in output
    assert "4. Scoring Scales" in output
    assert "lineage" not in output.casefold()
    assert "snapshot" not in output.casefold()
    assert "materializ" not in output.casefold()


def test_activity_menus_expose_save_as_preset_without_replacing_native_workflows(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    activity = _activity()
    state = MenuSessionContext()

    _inputs(monkeypatch, ["b"])
    _disable_clear(monkeypatch, "concord.menu_role")
    launch_role_menu(activity, state)
    role_output = capsys.readouterr().out
    assert "2. Assign a Role" in role_output
    assert "5. Save a Role as a Preset" in role_output

    _inputs(monkeypatch, ["b"])
    _disable_clear(monkeypatch, "concord.menu_responsibility")
    launch_responsibility_menu(activity, state)
    responsibility_output = capsys.readouterr().out
    assert "2. Assign a Responsibility" in responsibility_output
    assert "5. Save a Responsibility as a Preset" in responsibility_output

    _inputs(monkeypatch, ["b"])
    _disable_clear(monkeypatch, "concord.menu_scoring")
    _criterion_set_menu(activity, state)
    criterion_output = capsys.readouterr().out
    assert "1. Create Criterion Set" in criterion_output
    assert "5. Save Criterion Set as Preset" in criterion_output

    _inputs(monkeypatch, ["b"])
    _scale_menu(activity, state)
    scale_output = capsys.readouterr().out
    assert "1. Create Scoring Scale" in scale_output
    assert "4. Save Scoring Scale as Preset" in scale_output


def test_scoring_menu_presents_saved_setup_as_one_teacher_task(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _inputs(monkeypatch, ["b"])
    _disable_clear(monkeypatch, "concord.menu_scoring")
    monkeypatch.setattr(
        "concord.menu_scoring._latest",
        lambda activity: activity,
    )

    launch_scoring_menu(_activity(), MenuSessionContext())
    output = capsys.readouterr().out
    assert "1. Use Saved Scoring Setup" in output
    assert "2. Criterion Sets" in output
    assert "3. Scoring Scales" in output


def test_repository_qualification_requires_preset_docs_package_and_wheel_smoke(
) -> None:
    root = Path(__file__).resolve().parents[1]
    validator = (root / "scripts" / "validate_repository.py").read_text(
        encoding="utf-8"
    )
    feature_smokes = (root / "scripts" / "smoke_test_feature_wheels.py").read_text(
        encoding="utf-8"
    )
    package_check = (root / "scripts" / "check_package.py").read_text(
        encoding="utf-8"
    )
    documentation_check = (root / "scripts" / "check_documentation.py").read_text(
        encoding="utf-8"
    )
    docs_index = (root / "docs" / "README.md").read_text(encoding="utf-8")

    assert "scripts/smoke_test_feature_wheels.py" in validator
    assert "scripts/smoke_test_reusable_presets_wheel.py" in feature_smokes
    assert '"concord/cli_app/handlers/reusable_presets.py"' in package_check
    assert '"concord/menu_presets.py"' in package_check
    assert '"concord/reusable_preset_storage.py"' in package_check
    assert '"concord/reusable_presets.py"' in package_check
    assert '"concord/workflows/reusable_presets.py"' in package_check
    assert "REUSABLE_PRESETS_DOC" in documentation_check
    assert "v0.3.0-reusable-role-responsibility-scoring-presets.md" in docs_index
