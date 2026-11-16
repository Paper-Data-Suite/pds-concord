"""#148 Slice 4A: one final integrated lane, isolated synthetic wheel smoke."""

from __future__ import annotations

import ast
from pathlib import Path

from scripts import smoke_test_issue148_teacher_attribution_wheel as smoke

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "tests/fixtures/issue148/installed_attribution_stage.py"


def test_installed_acceptance_is_in_complete_validation_lane() -> None:
    code = (ROOT / "scripts/validate_repository.py").read_text(encoding="utf-8")
    assert code.count("scripts/smoke_test_issue148_teacher_attribution_wheel.py") == 1
    assert code.index("scripts/smoke_test_issue148_teacher_attribution_wheel.py") > (
        code.index("scripts/smoke_test_attention_provider_wheel.py")
    )
    assert '"--allow-dirty"' in code  # existing guarded candidate validation API


def test_stages_are_valid_python_without_repository_path_injection() -> None:
    code = STAGE.read_text(encoding="utf-8")
    ast.parse(code, filename=STAGE.name)
    assert "from concord.menu_context import new_menu_session" in code
    assert "get_workspace_config_path().exists()" in code
    assert 'metadata.version("pds-meridian")' not in code
    assert "PDS_148_TEST_CONFIG_HOME" in code
    assert "actor.created_provenance" not in code
    assert "created_provenance.actor" in code


def test_smoke_environment_and_three_fresh_processes() -> None:
    assert smoke.STAGE == STAGE
    source = ROOT / "scripts/smoke_test_issue148_teacher_attribution_wheel.py"
    text = source.read_text(encoding="utf-8")
    assert '"PYTHONPATH"' in text
    assert '"PYTHONNOUSERSITE": "1"' in text
    assert '"-I"' in text
    assert '("setup", "author", "relaunch")' in text
    assert "venv.EnvBuilder(with_pip=True)" in text
    assert "shutil.copyfile(STAGE, stage)" in text
