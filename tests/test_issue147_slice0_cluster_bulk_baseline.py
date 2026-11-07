"""#147 failing-before witnesses for manual GroupPlan Cluster-first bulk placement.

The four XFAILs are intentional missing-feature evidence. They must be
converted into positive acceptance tests by their owning later slices, not
papered over with fake service implementations.
"""

from __future__ import annotations

import importlib.util
import inspect
from types import SimpleNamespace

import pytest

import concord.menu_group_plan as plan_menu
import concord.menu_prompts as prompts
import concord.workflows.group_plan_manual as manual
from concord.cli import build_parser
from concord.menu_context import MenuSessionContext


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="#147 baseline: planned-Cluster menu has no bulk student action",
)
def test_cluster_first_menu_exposes_bulk_action(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Exercise the real planned-group menu dispatch without creating records."""
    detail = SimpleNamespace(
        plan=SimpleNamespace(group_plan_id="plan-1", status="draft"),
    )
    monkeypatch.setattr(plan_menu, "show_group_plan", lambda *_a: detail)
    monkeypatch.setattr(plan_menu, "clear_screen", lambda: None)
    monkeypatch.setattr(plan_menu, "print_menu_header", lambda *_a: None)
    monkeypatch.setattr(plan_menu, "print_navigation", lambda: None)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "b")

    plan_menu._planned_group_menu(
        SimpleNamespace(class_id="class-1", activity_id="activity-1"),
        "plan-1",
        MenuSessionContext(),
    )
    assert "Manage students in this planned Cluster (bulk)" in (
        capsys.readouterr().out
    )


def test_bulk_prepare_and_commit_service_is_not_yet_exposed() -> None:
    assert callable(getattr(manual, "prepare_bulk_planned_group_edit", None))
    assert callable(getattr(manual, "commit_bulk_planned_group_edit", None))


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="#147 baseline: no Cluster-local page/all scoped bulk selector",
)
def test_bulk_selector_with_distinct_page_and_all_scope_is_missing() -> None:
    # Slice 2 may implement this as a narrow module; DO NOT reinterpret
    # menu_prompts.select_many(A), which already means every eligible item.
    assert importlib.util.find_spec("concord.menu_group_plan_bulk") is not None


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="#147 baseline: no direct CLI batch-preview/batch-commit commands",
)
def test_direct_cli_batch_review_and_commit_are_not_registered() -> None:
    parser = build_parser()
    for command in ("batch-place-preview", "batch-place"):
        with pytest.raises(SystemExit) as result:
            parser.parse_args(("group-plan", command, "--help"))
        assert result.value.code == 0


def test_existing_manual_placement_is_student_first() -> None:
    source = inspect.getsource(plan_menu._place_student)
    assert source.index("choose_student(") < source.index(
        "_select_planned_group("
    )
    assert "place_student_in_plan(" in source


def test_existing_service_checks_exact_snapshot_and_core_roster() -> None:
    source = inspect.getsource(manual._load_targeted_edit)
    assert "_require_expected_snapshot(" in source
    assert "_require_editable(" in source
    assert "_roster_student_ids(" in source
    assert "current_roster != detail.plan.roster_student_ids" in source


def test_existing_proposal_replacement_uses_one_canonical_service() -> None:
    source = inspect.getsource(manual._replace_preserving_origin)
    assert source.count("replace_group_plan_proposal(") == 1
    assert "expected_snapshot_revision=detail.summary.snapshot_revision" in source
    assert "standards_library=standards_library" in source


def test_shared_select_many_all_choice_is_global_not_page_only() -> None:
    source = inspect.getsource(prompts.select_many)
    assert "selected = set(range(len(items)))" in source
    assert 'if normalized == "a"' in source
