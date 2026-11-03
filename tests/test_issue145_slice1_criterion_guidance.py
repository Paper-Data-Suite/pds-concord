"""Issue #145 Slice 1: pure Criterion drafts and canonical Core displays."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

import pytest
from pds_core.standards import StandardDefinition, StandardsLibrary, StandardsProfile

from concord.criterion_guidance import (
    TARGET_CHOICES,
    CriterionDraft,
    CriterionSetDraft,
    GuidedCriterionInputError,
    add_criterion,
    criterion_specs,
    describe_draft,
    focus_standard_choices,
    move_criterion,
    remove_criterion,
    replace_criterion,
    target_choice,
    validate_draft,
)
from concord.models import ConcordModelError
from concord.workflows.context import provenance
from concord.workflows.models import WorkflowActor

FOCUS = "SL.PE.11-12.1"
ALIGNMENT = "RL.CS.11-12.4"
PROFILE = "english-12-synthetic"


def _library(*, inactive: bool = False, deprecated: bool = False) -> StandardsLibrary:
    return StandardsLibrary(
        standards=(
            StandardDefinition(
                standard_id=FOCUS,
                code=FOCUS,
                source="Synthetic NJ ELA",
                short_name="Discussion participation",
                description="Use evidence while participating in a discussion.",
                active=not inactive,
                tags=("deprecated",) if deprecated else (),
            ),
            StandardDefinition(
                standard_id=ALIGNMENT,
                code=ALIGNMENT,
                source="Synthetic NJ ELA",
                short_name="Text analysis",
                description="Analyze language and textual structure.",
            ),
        ),
        profiles=(
            StandardsProfile(
                profile_id=PROFILE,
                standards=(FOCUS, ALIGNMENT),
            ),
        ),
    )


def _item(*, local: bool = False) -> CriterionDraft:
    if local:
        return CriterionDraft(
            key="cluster-analysis",
            label="Collaborative Textual Analysis",
            definition="Evaluate the Cluster's shared textual analysis.",
            criterion_kind="local",
            supported_target_kinds=("concord_group",),
        )
    return CriterionDraft(
        key="discussion-participation",
        label="Discussion Participation",
        definition="Evaluate individual discussion participation.",
        criterion_kind="standard_backed",
        supported_target_kinds=("core_student",),
        standard_id=FOCUS,
        alignment_standard_ids=(ALIGNMENT,),
        default_scoring_scale_id="four-level-native-scale",
    )


def _draft() -> CriterionSetDraft:
    return CriterionSetDraft(
        name="Synthetic Jíbara Discussion Assessment",
        purpose="Assess discussion and collaboration independently.",
        criterion_set_kind="mixed",
        criteria=(_item(), _item(local=True)),
    )


def _validate(
    draft: CriterionSetDraft,
    *,
    orientation: str = "mixed",
    library: StandardsLibrary | None = None,
    focus: tuple[str, ...] = (FOCUS,),
    profile: str | None = PROFILE,
) -> None:
    validate_draft(
        draft,
        activity_scoring_orientation=orientation,
        standards_profile_id=profile,
        focus_standard_ids=focus,
        standards_library=_library() if library is None else library,
        created_provenance=provenance(
            WorkflowActor(actor_id="synthetic-teacher"),
            clock=lambda: datetime(2026, 11, 1, 12, tzinfo=timezone.utc),
        ),
    )


def test_native_core_focus_display_uses_real_definition_not_an_invented_label() -> None:
    choices = focus_standard_choices(_library(), PROFILE, (FOCUS,))
    assert len(choices) == 1
    assert choices[0].standard_id == FOCUS
    assert choices[0].code == FOCUS
    assert choices[0].short_name == "Discussion participation"
    assert choices[0].label == "SL.PE.11-12.1 — Discussion participation"
    assert "Use evidence" in choices[0].description


def test_target_labels_preserve_all_five_canonical_kinds() -> None:
    assert tuple(item.value for item in TARGET_CHOICES) == (
        "core_student", "concord_group", "concord_session",
        "concord_activity", "concord_artifact_instance",
    )
    assert target_choice("core_student").label == "Individual student"
    assert target_choice("concord_group").label == "Cluster Group"
    with pytest.raises(GuidedCriterionInputError, match="Unsupported"):
        target_choice("whole_class_student_score")


def test_synthetic_mixed_rubric_is_readonly_and_has_complete_preview() -> None:
    draft = _draft()
    _validate(draft)
    descriptions = describe_draft(
        draft, focus_choices=focus_standard_choices(_library(), PROFILE, (FOCUS,))
    )
    text = "\n".join(descriptions)
    assert "Individual student" in text and "Cluster Group" in text
    assert FOCUS in text
    assert "Local — no governing Standard" in text
    assert "four-level-native-scale" in text
    assert "not a saved preset" in text
    assert "no Criterion Set" in text
    assert "No Scores, Grades" in text
    assert draft.criteria[0].standard_id == FOCUS


def test_add_edit_move_and_remove_do_not_mutate_prior_draft() -> None:
    original = replace(_draft(), criteria=(_item(),))
    added = add_criterion(original, _item(local=True))
    assert len(original.criteria) == 1 and len(added.criteria) == 2
    updated = replace_criterion(
        added, 0, replace(added.criteria[0], label="Edited Discussion")
    )
    assert original.criteria[0].label == "Discussion Participation"
    assert updated.criteria[0].label == "Edited Discussion"
    moved = move_criterion(updated, 1, 0)
    assert moved.criteria[0].key == "cluster-analysis"
    assert move_criterion(moved, 0, 0) is moved
    removed = remove_criterion(moved, 0)
    assert len(removed.criteria) == 1
    assert removed.criteria[0].label == "Edited Discussion"
    _validate(removed)


@pytest.mark.parametrize("index", [-1, 2, True, 1.5])
def test_draft_index_refuses_out_of_range_and_nonintegers(index: object) -> None:
    with pytest.raises(GuidedCriterionInputError, match="position"):
        remove_criterion(replace(_draft(), criteria=(_item(),)), index)


def test_canonical_spec_conversion_preserves_every_field_and_order() -> None:
    draft = _draft()
    specs = criterion_specs(draft, ("criterion-a", "criterion-b"))
    assert tuple(item.key for item in specs) == (
        "discussion-participation", "cluster-analysis"
    )
    assert specs[0].standard_id == FOCUS
    assert specs[0].alignment_standard_ids == (ALIGNMENT,)
    assert specs[0].default_scoring_scale_id == "four-level-native-scale"
    assert specs[1].standard_id is None
    assert specs[1].supported_target_kinds == ("concord_group",)
    with pytest.raises(GuidedCriterionInputError, match="one new Criterion ID"):
        criterion_specs(draft, ("criterion-a",))
    with pytest.raises(GuidedCriterionInputError, match="unique"):
        criterion_specs(draft, ("criterion-a", "criterion-a"))


@pytest.mark.parametrize("inactive,deprecated", [(True, False), (False, True)])
def test_inactive_or_deprecated_focus_refuses(inactive: bool, deprecated: bool) -> None:
    with pytest.raises(GuidedCriterionInputError, match="inactive or deprecated"):
        focus_standard_choices(
            _library(inactive=inactive, deprecated=deprecated), PROFILE, (FOCUS,)
        )


def test_missing_profile_or_outside_profile_refuses() -> None:
    with pytest.raises(GuidedCriterionInputError, match="profile/Focus"):
        focus_standard_choices(_library(), "missing", (FOCUS,))
    with pytest.raises(GuidedCriterionInputError, match="profile/Focus"):
        focus_standard_choices(_library(), PROFILE, ("outside-profile",))


def test_governing_standard_must_be_activity_focus() -> None:
    with pytest.raises(GuidedCriterionInputError, match="Activity's Focus"):
        _validate(_draft(), focus=(ALIGNMENT,))


def test_standard_and_local_kinds_respect_activity_orientation() -> None:
    with pytest.raises(GuidedCriterionInputError, match="does not permit standards"):
        _validate(_draft(), orientation="local_criteria_only")
    with pytest.raises(GuidedCriterionInputError, match="does not permit local"):
        _validate(_draft(), orientation="standards_based")
    with pytest.raises(GuidedCriterionInputError, match="Evidence-only"):
        _validate(_draft(), orientation="evidence_only")
    local = replace(
        _draft(), criterion_set_kind="local", criteria=(_item(local=True),)
    )
    _validate(local, orientation="local_criteria_only", profile=None, focus=())


def test_missing_canonical_standards_library_is_explicit_refusal() -> None:
    with pytest.raises(GuidedCriterionInputError, match="canonical Core Standards"):
        validate_draft(
            _draft(),
            activity_scoring_orientation="mixed",
            standards_profile_id=PROFILE,
            focus_standard_ids=(FOCUS,),
            standards_library=None,
            created_provenance=provenance(WorkflowActor(actor_id="synthetic-teacher")),
        )


def test_invalid_alignment_must_not_be_silently_rewritten() -> None:
    bad = replace(_item(), alignment_standard_ids=("outside-profile",))
    with pytest.raises(GuidedCriterionInputError, match="Alignment Standard"):
        _validate(replace(_draft(), criteria=(bad, _item(local=True))))


def test_duplicate_keys_refuse_without_writing() -> None:
    duplicate = replace(_item(local=True), key=_item().key)
    with pytest.raises(GuidedCriterionInputError, match="unique"):
        _validate(replace(_draft(), criteria=(_item(), duplicate)))


def test_invalid_target_reaches_canonical_concord_validator() -> None:
    bad = replace(_item(local=True), supported_target_kinds=("core_person",))
    with pytest.raises(ConcordModelError, match="supported_target_kinds"):
        _validate(replace(_draft(), criteria=(_item(), bad)))


def test_empty_rubric_refuses_without_persistence() -> None:
    with pytest.raises(GuidedCriterionInputError, match="at least one"):
        _validate(replace(_draft(), criteria=()))


def test_set_kind_and_criterion_kinds_must_be_consistent() -> None:
    with pytest.raises(GuidedCriterionInputError, match="standards-backed rubric"):
        _validate(replace(_draft(), criterion_set_kind="standard_backed"))
    with pytest.raises(GuidedCriterionInputError, match="local rubric"):
        _validate(replace(_draft(), criterion_set_kind="local"))
