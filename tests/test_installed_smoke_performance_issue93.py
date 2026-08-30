from __future__ import annotations

from pathlib import Path

from scripts import smoke_test_feature_wheels as feature_smokes


def test_issue93_shared_feature_smoke_reuses_existing_scenario_sources() -> None:
    assert tuple(label for label, _, _ in feature_smokes.SCENARIOS) == (
        "Activity copying",
        "reusable presets",
        "guided Activity",
        "task-oriented menu",
        "starter workflows",
    )
    assert tuple(filename for _, filename, _ in feature_smokes.SCENARIOS) == (
        "activity_copying_smoke.py",
        "reusable_presets_smoke.py",
        "guided_activity_smoke.py",
        "task_oriented_activity_menu_smoke.py",
        "starter_workflows_smoke.py",
    )
    assert tuple(script for _, _, script in feature_smokes.SCENARIOS) == (
        "scripts/smoke_test_activity_copying_wheel.py",
        "scripts/smoke_test_reusable_presets_wheel.py",
        "scripts/smoke_test_guided_activity_wheel.py",
        "scripts/smoke_test_task_oriented_activity_menu_wheel.py",
        "scripts/smoke_test_starter_workflows_wheel.py",
    )


def test_issue93_shared_feature_smoke_has_one_environment_install_boundary() -> None:
    source = Path(feature_smokes.__file__).read_text(encoding="utf-8")
    assert source.count("venv.EnvBuilder(with_pip=True).create(env_root)") == 1
    assert source.count('"pip", "install"') == 2
    assert source.count('"pip", "check"') == 1
    assert '[str(python), "-I", str(smoke_path)]' in source
    assert "runpy.run_path" in source


def test_issue93_repository_validator_batches_only_feature_smokes() -> None:
    source = Path("scripts/validate_repository.py").read_text(encoding="utf-8")
    assert "scripts/smoke_test_feature_wheels.py" in source
    assert "installed-wheel smoke: shared feature scenarios" in source

    for removed_direct_call in (
        "scripts/smoke_test_activity_copying_wheel.py",
        "scripts/smoke_test_reusable_presets_wheel.py",
        "scripts/smoke_test_guided_activity_wheel.py",
        "scripts/smoke_test_task_oriented_activity_menu_wheel.py",
        "scripts/smoke_test_starter_workflows_wheel.py",
    ):
        assert removed_direct_call not in source

    # These retain separate isolation because they qualify additional boundaries.
    assert "scripts/smoke_test_wheel.py" in source
    assert "scripts/smoke_test_attention_provider_wheel.py" in source
