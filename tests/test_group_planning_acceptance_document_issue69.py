from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "v0.3.0-group-planning-acceptance.md"
DOC_INDEX = ROOT / "docs" / "README.md"
ACCEPTANCE = ROOT / "tests" / "test_group_planning_acceptance_issue69.py"


def test_issue69_document_freezes_repository_local_acceptance_boundary() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = (
        "**Status:** Implemented for issue #69",
        "tests/test_group_planning_acceptance_issue69.py",
        "GroupPlan != Group != GroupMembership",
        "draft\n    -> previewed\n    -> approved",
        "student_id,group",
        "deterministic random GroupPlan",
        "similar_signal",
        "mixed_signal",
        "calculate_grouping_signal_digest",
        "Core canonical signal digest != source.snapshot_digest",
        "missing signal != lowest band",
        "manual",
        "random",
        "leave_unassigned",
        "Concord  -X-> Meridian",
        "Optional real Meridian producer acceptance: deferred.",
        "Meridian #36",
        "Meridian #38",
        "Meridian #39",
        "Meridian #40",
        "no authentic stable Meridian-produced `grouping_signal_set_v1` snapshot",
        "Issue #69 does not add a parallel validator or a dedicated CI job.",
        "#70 — Build representative installed and physical starter-workflow acceptance",
    )
    for phrase in required:
        assert phrase in text, phrase


def test_issue69_document_is_indexed_and_matches_acceptance_guards() -> None:
    index = DOC_INDEX.read_text(encoding="utf-8")
    acceptance = ACCEPTANCE.read_text(encoding="utf-8")

    assert (
        "[`v0.3.0-group-planning-acceptance.md`]"
        "(v0.3.0-group-planning-acceptance.md)"
    ) in index

    required_acceptance_guards = (
        "test_package_metadata_keeps_meridian_outside_concord_dependencies",
        "test_importing_concord_workflows_does_not_attempt_meridian_import",
        'module_id="meridian"',
        "calculate_grouping_signal_digest",
        "test_similar_signal_plan_binds_core_digest_then_explicitly_applies",
        "test_mixed_signal_plan_binds_core_digest_then_explicitly_applies",
        "test_missing_signal_manual_resolution_requires_placement_then_applies",
        "test_missing_signal_random_places_only_missing_reproducibly_then_applies",
        "test_missing_signal_leave_unassigned_applies_without_missing_memberships",
    )
    for phrase in required_acceptance_guards:
        assert phrase in acceptance, phrase
