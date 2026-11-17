"""#150 Slice 0 source controls: preserve established authority and safe copying.

No real roster, classroom files or credentials are loaded by this test.
"""

from __future__ import annotations

import inspect

import concord.menu_guided_activity as guided_menu
import concord.workflows.activity_copy as copy_service
import concord.workflows.class_group_arrangements as arrangements


def test_existing_guided_path_uses_guarded_copy_and_fresh_session() -> None:
    source = inspect.getsource(guided_menu._create_from_activity)
    for statement in (
        "prepare_activity_copy(",
        "copy_activity(",
        "PrepareActivityCopyRequest(",
        "CopyActivityRequest(",
        "review_digest=prepared.review_digest",
        "first_session_id=session_id",
        "confirm_actor_write(",
        "_offer_after_creation(",
    ):
        assert statement in source


def test_activity_copy_is_create_only_and_excludes_prior_work() -> None:
    source = inspect.getsource(copy_service.copy_activity)
    prepare = inspect.getsource(copy_service.prepare_activity_copy)
    for invariant in (
        "expected_snapshot_revision=None",
        'status="draft"',
        'status="planned"',
        "criterion_set_ids=()",
        "external_reference_ids=()",
        "commit_record_batch(",
    ):
        assert invariant in source
    for invariant in (
        "_target_is_available(root, request)",
        "_validate_prepared_graph(",
        "_resolve_privacy(source.privacy_policy)",
    ):
        assert invariant in prepare
    excluded = copy_service._EXCLUDED_STATE
    assert any("Memberships" in item for item in excluded)
    assert any("Scores" in item for item in excluded)
    assert any("scans" in item for item in excluded)
    assert any("publications" in item for item in excluded)


def test_saved_grouping_reuse_cannot_cross_core_class_rosters() -> None:
    source = inspect.getsource(arrangements.prepare_reuse_grouping)
    for invariant in (
        "class_id=request.class_id",
        "target_class_id=request.class_id",
        "target_school_year=metadata.school_year",
        "target_student_ids=roster",
        "acknowledged_departed_student_ids",
        "expected_snapshot_revision",
        "acknowledge_existing_plans",
    ):
        assert invariant in source


def test_current_menu_only_uses_core_navigation_not_a_global_input_hook() -> None:
    source = inspect.getsource(guided_menu.launch_guided_activity_menu)
    assert "parse_menu_navigation(choice)" in source
    assert "navigation is NavigationChoice.BACK" in source
    assert "setattr(__builtins__" not in source
    assert "sys.stdin =" not in source
