from __future__ import annotations

from pathlib import Path

TASK_SMOKE = Path("scripts/smoke_test_task_oriented_activity_menu_wheel.py")
PACKAGE_CHECK = Path("scripts/check_package.py")
VALIDATOR = Path("scripts/validate_repository.py")


def test_issue104_installed_task_menu_uses_real_attention_path() -> None:
    source = TASK_SMOKE.read_text(encoding="utf-8")
    assert "issues #66/#104" in source
    assert "create_group_plan(" in source
    assert '"Attention"' in source
    assert '"Group plans still need preparation"' in source
    assert '"A. Open next action"' in source
    assert "fingerprint(root) == before" in source
    assert '"show_activity",\n                    lambda' not in source


def test_issue104_activity_read_module_is_required_in_candidate_wheel() -> None:
    source = PACKAGE_CHECK.read_text(encoding="utf-8")
    assert '"concord/workflows/activity_read.py"' in source


def test_issue104_uses_existing_shared_installed_qualification_boundaries() -> None:
    source = VALIDATOR.read_text(encoding="utf-8")
    assert "scripts/smoke_test_feature_wheels.py" in source
    assert "installed-wheel smoke: shared feature scenarios" in source
    assert "scripts/smoke_test_attention_provider_wheel.py" in source
    assert "installed-wheel smoke: module operations" in source
