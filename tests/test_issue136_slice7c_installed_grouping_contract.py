"""#136 Slice 7C: frozen installed-wheel teacher grouping acceptance contract."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "scripts/smoke_test_issue136_grouping_installed.py"
RUNNER = ROOT / "scripts/run_issue136_installed_acceptance.py"
VALIDATOR = ROOT / "scripts/validate_repository.py"


def test_issue136_installed_grouping_writes_real_services_outside_source() -> None:
    smoke = SMOKE.read_text(encoding="utf-8")
    ast.parse(smoke)
    for exact in (
        "metadata.version(distribution)",
        '"site-packages"',
        "not origin.is_relative_to(repo)",
        'scoring_orientation="mixed"',
        "plan_menu._create_manual(",
        "saved_menu.save_grouping_from_plan(",
        "saved_menu.use_saved_grouping(",
        "preview_group_plan(",
        "approve_group_plan(",
        "prepare_group_plan_application(",
        "apply_group_plan(",
        "application.membership_count == 29",
        "len(graph.groups) == 6 and len(graph.memberships) == 29",
        "assert not graph.score_records and not graph.score_evidence_links",
    ):
        assert exact in smoke, exact

    # A formatter can wrap long patch.object calls after the comma. Match
    # the syntax tree instead of assuming one particular source line layout.
    patches = {
        (call.args[0].id, call.args[1].value)
        for call in ast.walk(ast.parse(smoke))
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Attribute)
        and isinstance(call.func.value, ast.Name)
        and call.func.value.id == "patch"
        and call.func.attr == "object"
        and len(call.args) >= 2
        and isinstance(call.args[0], ast.Name)
        and isinstance(call.args[1], ast.Constant)
        and isinstance(call.args[1].value, str)
    }
    assert ("plan_menu", "_latest") in patches
    assert ("saved_menu", "prepare_save_grouping") in patches


def test_issue136_existing_isolated_install_runs_new_teacher_smoke() -> None:
    source = RUNNER.read_text(encoding="utf-8")
    ast.parse(source)
    for exact in (
        'EXPECTED_CONCORD_VERSION = "0.3.4"',
        'EXPECTED_CORE_VERSION = "0.6.6"',
        'environment.pop("PYTHONPATH", None)',
        "venv.EnvBuilder(with_pip=True)",
        '"-m", "pip", "check"',
        '"scripts" / "smoke_test_issue136_grouping_installed.py"',
        "grouping_smoke.read_bytes()",
        'str(python), "-I", str(grouping_path), str(repository)',
    ):
        assert exact in source, exact
    validator = VALIDATOR.read_text(encoding="utf-8")
    assert '"scripts/run_issue136_installed_acceptance.py"' in validator
    assert '"scripts/run_issue134_installed_acceptance.py"' not in validator
    # Older v0.3.3 verification is historical and stays byte-identical.
    historical = ROOT / "scripts/run_issue134_installed_acceptance.py"
    assert 'EXPECTED_CONCORD_VERSION = "0.3.3"' in historical.read_text(
        encoding="utf-8"
    )
