"""Concord #143 Slice 1: native-compatible, Core-authorized preset identities.

The workspace fixtures in this file are entirely synthetic. No physical return,
Score, student grade, Suite launcher, or Meridian flow is implied by these tests.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
from pds_core.standards import StandardDefinition, StandardsLibrary, StandardsProfile
from pds_core.workspace import ensure_workspace_root

from concord.models import ConcordModelError
from concord.reusable_preset_storage import load_current_preset, preset_library_root
from concord.reusable_presets import CriterionPresetSpec, CriterionSetPresetRevision
from concord.workflows.errors import ConcordWorkflowValidationError
from concord.workflows.models import WorkflowActor
from concord.workflows.reusable_presets import (
    CreateCriterionSetPresetRequest,
    ReviseCriterionSetPresetRequest,
    create_criterion_set_preset,
    get_preset,
    get_preset_revision,
    revise_criterion_set_preset,
    validate_preset,
)

STANDARD = "SL.PE.11-12.1"
ALIGNMENT = "W.NW.11-12.3.D"
PROFILE = "njsls-ela:profile.2023:11-12"


def _actor() -> WorkflowActor:
    return WorkflowActor(actor_id="synthetic-teacher")


def _library(*, active_alignment: bool = True) -> StandardsLibrary:
    return StandardsLibrary(
        standards=(
            StandardDefinition(
                standard_id=STANDARD,
                code=STANDARD,
                source="synthetic-test",
                short_name="Discussion",
                description="Synthetic discussion participation standard.",
                available_modules=("concord",),
            ),
            StandardDefinition(
                standard_id=ALIGNMENT,
                code=ALIGNMENT,
                source="synthetic-test",
                short_name="Narrative alignment",
                description="Synthetic alignment standard.",
                active=active_alignment,
                available_modules=("concord",),
            ),
        ),
        profiles=(
            StandardsProfile(
                profile_id=PROFILE,
                standards=(STANDARD, ALIGNMENT),
                title="Synthetic NJSLS profile",
            ),
        ),
    )


def _spec() -> CriterionPresetSpec:
    return CriterionPresetSpec(
        key="discussion_participation",
        label="Individual discussion participation",
        definition="Use evidence and respond in discussion.",
        criterion_kind="standard_backed",
        supported_target_kinds=("core_student",),
        standard_id=STANDARD,
        alignment_standard_ids=(ALIGNMENT,),
    )


def _criteria() -> tuple[CriterionPresetSpec, ...]:
    return (
        _spec(),
        CriterionPresetSpec(
            key="collaborative_textual_analysis",
            label="Cluster collaborative textual analysis",
            definition="Collaborative analysis of text.",
            criterion_kind="local",
            supported_target_kinds=("concord_group",),
        ),
    )


def _request() -> CreateCriterionSetPresetRequest:
    return CreateCriterionSetPresetRequest(
        preset_id="mixed-discussion-preset",
        preset_revision_id="mixed-discussion-preset-v1",
        name="Synthetic discussion assessment",
        purpose="Reusable criterion definitions; not Scores.",
        criterion_set_kind="mixed",
        criteria=_criteria(),
        standards_profile_id=PROFILE,
        actor=_actor(),
    )


def test_dotted_criterion_standard_and_alignment_are_normalized() -> None:
    spec = replace(
        _spec(),
        standard_id=f"  {STANDARD}  ",
        alignment_standard_ids=(f" {ALIGNMENT} ",),
    )
    assert spec.standard_id == STANDARD
    assert spec.alignment_standard_ids == (ALIGNMENT,)
    assert spec.supported_target_kinds == ("core_student",)


def test_dotted_profile_is_normalized_without_affecting_native_ids() -> None:
    from concord.models import ActorReference, Provenance

    value = CriterionSetPresetRevision(
        preset_id="synthetic-preset",
        preset_revision_id="synthetic-preset-v1",
        revision=1,
        name="Synthetic criterion set",
        purpose="Test profile identity normalization",
        criterion_set_kind="mixed",
        criteria=_criteria(),
        status="active",
        created_provenance=Provenance(
            actor=ActorReference(
                actor_kind="authorized_adult",
                actor_id="teacher-synthetic",
                owning_system="concord",
            ),
            timestamp="2026-10-31T12:00:00-04:00",
            source_kind="manual",
        ),
        standards_profile_id=f" {PROFILE} ",
    )
    assert value.standards_profile_id == PROFILE
    assert value.preset_id == "synthetic-preset"


@pytest.mark.parametrize("bad", ["", " ", "\t", "\n", 4, None])
def test_standard_backed_criterion_rejects_blank_nontext_or_missing_id(
    bad: object,
) -> None:
    with pytest.raises(ConcordModelError):
        replace(_spec(), standard_id=bad)  # type: ignore[arg-type]


@pytest.mark.parametrize("bad", ["", "  ", 7, None])
def test_alignment_rejects_blank_or_nonstring_members(bad: object) -> None:
    with pytest.raises(ConcordModelError):
        replace(_spec(), alignment_standard_ids=(bad,))  # type: ignore[arg-type]


def test_alignment_rejects_duplicates_after_normalization() -> None:
    with pytest.raises(ConcordModelError, match="duplicates"):
        replace(
            _spec(),
            alignment_standard_ids=(ALIGNMENT, f" {ALIGNMENT} "),
        )


def test_profile_rejects_invalid_text() -> None:
    from concord.models import ActorReference, Provenance

    value = CriterionSetPresetRevision(
        preset_id="profile-test",
        preset_revision_id="profile-test-v1",
        revision=1,
        name="Synthetic",
        purpose="Verify profile validation",
        criterion_set_kind="standard_backed",
        criteria=(_spec(),),
        status="active",
        created_provenance=Provenance(
            actor=ActorReference(
                actor_kind="authorized_adult",
                actor_id="teacher-synthetic",
                owning_system="concord",
            ),
            timestamp="2026-10-31T12:00:00-04:00",
            source_kind="manual",
        ),
        standards_profile_id=PROFILE,
    )
    for bad in ("", "  ", 5):
        with pytest.raises(ConcordModelError):
            replace(value, standards_profile_id=bad)  # type: ignore[arg-type]


def test_nonstandards_preset_internal_ids_stay_routing_safe() -> None:
    with pytest.raises(ConcordModelError):
        replace(_spec(), key="discussion.participation")
    with pytest.raises(ConcordModelError):
        replace(
            _spec(),
            default_scoring_scale_preset_id="scale.preset",
            default_scoring_scale_preset_revision_id="scale-preset-v1",
        )


def test_local_criterion_still_forbids_governing_standard() -> None:
    with pytest.raises(ConcordModelError, match="forbids standard_id"):
        replace(_criteria()[1], standard_id=STANDARD)


def test_create_validate_revise_load_round_trip_preserves_exact_core_ids(
    tmp_path: Path,
) -> None:
    root = ensure_workspace_root(tmp_path / "synthetic")
    library = _library()
    created = create_criterion_set_preset(
        _request(), workspace_root=root, standards_library=library
    )
    assert created.revision == 1
    current = get_preset(
        "criterion_set", "mixed-discussion-preset", workspace_root=root
    )
    assert isinstance(current, CriterionSetPresetRevision)
    assert current.standards_profile_id == PROFILE
    assert tuple(item.key for item in current.criteria) == (
        "discussion_participation", "collaborative_textual_analysis"
    )
    assert current.criteria[0].standard_id == STANDARD
    assert current.criteria[0].alignment_standard_ids == (ALIGNMENT,)
    assert current.criteria[1].standard_id is None
    assert current.criteria[1].supported_target_kinds == ("concord_group",)
    assert validate_preset(
        "criterion_set", "mixed-discussion-preset",
        workspace_root=root, standards_library=library
    ).revision == 1

    updated = revise_criterion_set_preset(
        ReviseCriterionSetPresetRequest(
            preset_id="mixed-discussion-preset",
            preset_revision_id="mixed-discussion-preset-v2",
            expected_revision=1,
            name="Synthetic discussion assessment v2",
            purpose="Same standard and group contracts",
            criterion_set_kind="mixed",
            criteria=_criteria(),
            standards_profile_id=PROFILE,
            actor=_actor(),
        ),
        workspace_root=root,
        standards_library=library,
    )
    assert updated.revision == 2
    v1 = get_preset_revision(
        "criterion_set", "mixed-discussion-preset", "mixed-discussion-preset-v1",
        workspace_root=root,
    )
    v2 = load_current_preset(root, "criterion_set", "mixed-discussion-preset").current
    assert isinstance(v1, CriterionSetPresetRevision)
    assert isinstance(v2, CriterionSetPresetRevision)
    assert v1.standards_profile_id == v2.standards_profile_id == PROFILE
    assert v1.criteria[0].standard_id == v2.criteria[0].standard_id == STANDARD
    assert v2.criteria[0].alignment_standard_ids == (ALIGNMENT,)
    assert v1.revision == 1 and v2.revision == 2
    assert v2.supersedes_preset_revision_id == v1.preset_revision_id


@pytest.mark.parametrize(
    "mode", ["missing_library", "wrong_profile", "unknown_id", "inactive_alignment"]
)
def test_invalid_core_context_rejects_before_library_write(
    tmp_path: Path, mode: str
) -> None:
    root = ensure_workspace_root(tmp_path / "synthetic")
    library = _library(active_alignment=mode != "inactive_alignment")
    request = _request()
    if mode == "wrong_profile":
        request = replace(request, standards_profile_id="missing:profile.2023")
    if mode == "unknown_id":
        request = replace(
            request,
            criteria=(replace(_spec(), standard_id="SL.PE.11-12.999"), _criteria()[1]),
        )
    with pytest.raises(ConcordWorkflowValidationError):
        create_criterion_set_preset(
            request, workspace_root=root,
            standards_library=None if mode == "missing_library" else library,
        )
    assert not preset_library_root(root).exists()
