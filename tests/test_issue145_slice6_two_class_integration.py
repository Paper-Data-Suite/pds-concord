"""#145 Slice 6: service-backed, synthetic two-class assessment qualification.

Every durable write is isolated under pytest ``tmp_path``. No classroom data,
real Core roster, student Score, evidence, or publication is used here.
"""

from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path

import pytest
from pds_core.standards import StandardsLibrary
from test_issue143_slice2_native_preset_save import (
    ACTIVITY,
    ALIGNMENT,
    CLASS,
    PROFILE,
    SCALE,
    SET,
    STANDARD,
    _actor,
    _clock,
    _fixture,
    _request,
    _save_scale,
    _work,
)
from test_issue143_slice3_cross_class_materialization import (
    TARGET_ACTIVITY,
    TARGET_CLASS,
    TARGET_CRITERION_GROUP,
    TARGET_CRITERION_STUDENT,
    TARGET_SCALE,
    TARGET_SET,
    _apply_request,
    _check_materialized,
    _graph,
    _target,
    _target_work,
)

from concord.criterion_guidance import criterion_specs, validate_draft
from concord.criterion_preset_guidance import (
    assess_native_defaults,
    matches_native_scale,
    scale_mapping_receipt,
)
from concord.criterion_revision_guidance import (
    describe_native_criterion_set,
    project_native_criterion_set,
)
from concord.reusable_presets import (
    CriterionSetPresetRevision,
    ScoringScalePresetRevision,
)
from concord.storage import list_work_snapshots
from concord.workflows.context import provenance
from concord.workflows.criterion_sets import (
    SelectActivityCriterionSetsRequest,
    read_activity_criterion_set_selection,
    select_activity_criterion_sets,
    show_criterion_set,
)
from concord.workflows.errors import ConcordWorkflowConflictError
from concord.workflows.reusable_presets import (
    get_preset,
    materialize_scoring_setup,
    prepare_criterion_set_preset_from_activity,
    prepare_scoring_setup,
    save_criterion_set_preset_from_activity,
)
from concord.workflows.scoring_scales import show_scoring_scale


def _fingerprint(root: Path) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted(
            (
                path.relative_to(root).as_posix(),
                hashlib.sha256(path.read_bytes()).hexdigest(),
            )
            for path in root.rglob("*")
            if path.is_file()
        )
    )


def _select_source(root: Path, library: StandardsLibrary, revision: int) -> int:
    """Select the exact existing native set, not a regenerated definition."""
    result = select_activity_criterion_sets(
        SelectActivityCriterionSetsRequest(
            class_id=CLASS,
            activity_id=ACTIVITY,
            criterion_set_ids=(SET,),
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
        standards_library=library,
        clock=_clock,
    )
    observed = read_activity_criterion_set_selection(
        CLASS, ACTIVITY, workspace_root=root, standards_library=library
    )
    assert observed.criterion_set_ids == (SET,)
    assert observed.snapshot_revision == result.commit.snapshot_revision
    return observed.snapshot_revision


def test_two_class_jibara_guided_projection_and_exact_reuse(
    tmp_path: Path,
) -> None:
    root, library, initial = _fixture(tmp_path)
    selection_revision = _select_source(root, library, initial)
    source_snapshot = read_activity_criterion_set_selection(
        CLASS, ACTIVITY, workspace_root=root, standards_library=library
    )
    detail = show_criterion_set(
        CLASS, ACTIVITY, SET, workspace_root=root, standards_library=library
    )
    review = project_native_criterion_set(detail, source_snapshot)
    assert review.is_current and review.is_selected
    assert review.selected_position == 1
    assert review.draft.criterion_set_kind == "mixed"
    assert tuple(item.key for item in review.draft.criteria) == (
        "discussion_participation", "collaborative_textual_analysis"
    )
    assert review.draft.criteria[0].standard_id == STANDARD
    assert review.draft.criteria[0].alignment_standard_ids == (ALIGNMENT,)
    assert review.draft.criteria[1].standard_id is None
    assert review.draft.criteria[0].supported_target_kinds == ("core_student",)
    assert review.draft.criteria[1].supported_target_kinds == ("concord_group",)
    preview = describe_native_criterion_set(review, standards_library=library)
    assert any(STANDARD in line for line in preview)
    assert any("Cluster Group" in line for line in preview)
    assert any("Read only" in line for line in preview)

    # The pure #145 draft adapter must preserve all reusable meanings without a
    # native write or leaking predecessor Criterion identities.
    criteria = criterion_specs(
        review.draft, ("preview-individual", "preview-group")
    )
    assert tuple(item.criterion_id for item in criteria) == (
        "preview-individual", "preview-group"
    )
    assert criteria[0].default_scoring_scale_id == SCALE
    validate_draft(
        review.draft,
        activity_scoring_orientation="mixed",
        standards_profile_id=PROFILE,
        focus_standard_ids=(STANDARD, ALIGNMENT),
        standards_library=library,
        created_provenance=provenance(_actor(), clock=_clock),
    )

    _save_scale(root, library, selection_revision)
    native_scale = show_scoring_scale(
        CLASS, ACTIVITY, SCALE, workspace_root=root, standards_library=library
    )
    saved_scale = get_preset(
        "scoring_scale", "saved-four-level", workspace_root=root
    )
    assert isinstance(saved_scale, ScoringScalePresetRevision)
    assert matches_native_scale(native_scale, saved_scale)
    assert not matches_native_scale(
        native_scale,
        replace(saved_scale, levels=(
            replace(saved_scale.levels[0], label="Tampered"),
            *saved_scale.levels[1:],
        )),
    )
    assessment = assess_native_defaults(detail.criteria)
    assert assessment.default_ids == (SCALE,)
    assert assessment.native_scale_id == SCALE
    receipt_lines = scale_mapping_receipt(
        assessment,
        preset_id="saved-four-level",
        preset_revision_id="saved-four-level-v1",
    )
    assert any("saved-four-level-v1" in line for line in receipt_lines)

    source_before = _graph(root, library, _work())
    source_snapshots = tuple(list_work_snapshots(root, _work()))
    save_request = _request(selection_revision)
    save_review = prepare_criterion_set_preset_from_activity(
        save_request, workspace_root=root, standards_library=library, clock=_clock
    )
    assert "Activity-native Criterion identities" in save_review.excluded_state
    assert "all Scores and Score Evidence Links" in save_review.excluded_state
    saved_result = save_criterion_set_preset_from_activity(
        save_request,
        review_digest=save_review.review_digest,
        workspace_root=root,
        standards_library=library,
        clock=_clock,
    )
    assert saved_result.preset_revision_id == "saved-discussion-assessment-v1"
    reusable = get_preset(
        "criterion_set", "saved-discussion-assessment", workspace_root=root
    )
    assert isinstance(reusable, CriterionSetPresetRevision)
    assert tuple(item.key for item in reusable.criteria) == (
        "discussion_participation", "collaborative_textual_analysis"
    )
    assert reusable.criteria[0].default_scoring_scale_preset_revision_id == (
        "saved-four-level-v1"
    )
    assert not hasattr(reusable, "score_records")
    assert tuple(list_work_snapshots(root, _work())) == source_snapshots
    assert _graph(root, library, _work()) == source_before

    destination_revision = _target(root, library)
    target_before = tuple(list_work_snapshots(root, _target_work()))
    target_request = _apply_request(destination_revision)
    prepared = prepare_scoring_setup(
        target_request, workspace_root=root, standards_library=library, clock=_clock
    )
    assert prepared.criterion_count == 2
    assert prepared.recommended_scoring_scale_preset_id == "saved-four-level"
    assert tuple(list_work_snapshots(root, _target_work())) == target_before
    materialized = materialize_scoring_setup(
        target_request,
        review_digest=prepared.review_digest,
        workspace_root=root,
        standards_library=library,
        clock=_clock,
    )
    assert materialized.criterion_set_id == TARGET_SET
    assert materialized.scoring_scale_id == TARGET_SCALE
    assert materialized.criterion_ids == (
        TARGET_CRITERION_STUDENT, TARGET_CRITERION_GROUP
    )
    _check_materialized(
        root, library, scale_id=TARGET_SCALE,
        expected_scale_levels=source_before.scoring_scales[0].levels,
    )
    destination = _graph(root, library, _target_work())
    assert [type(x.value) for x in destination.scoring_scales[0].levels] == [
        int, int, int, int
    ]
    assert [x.value for x in destination.scoring_scales[0].levels] == [1, 2, 3, 4]
    assert destination.activities[0].criterion_set_ids == (TARGET_SET,)
    assert destination.score_records == ()
    assert destination.score_evidence_links == ()
    assert tuple(list_work_snapshots(root, _work())) == source_snapshots
    assert _graph(root, library, _work()) == source_before
    assert TARGET_CLASS != CLASS and TARGET_ACTIVITY != ACTIVITY


def test_stale_review_digest_is_byte_exact_zero_write(
    tmp_path: Path,
) -> None:
    root, library, revision = _fixture(tmp_path)
    selected_revision = _select_source(root, library, revision)
    _save_scale(root, library, selected_revision)
    request = _request(selected_revision)
    prepared = prepare_criterion_set_preset_from_activity(
        request, workspace_root=root, standards_library=library, clock=_clock
    )
    assert prepared.review_digest != "0" * 64
    before = _fingerprint(root)
    with pytest.raises(ConcordWorkflowConflictError, match="stale"):
        save_criterion_set_preset_from_activity(
            request,
            review_digest="0" * 64,
            workspace_root=root,
            standards_library=library,
            clock=_clock,
        )
    assert _fingerprint(root) == before
    observed = read_activity_criterion_set_selection(
        CLASS, ACTIVITY, workspace_root=root, standards_library=library
    )
    assert observed.criterion_set_ids == (SET,)
    assert observed.snapshot_revision == selected_revision


def test_second_class_stale_materialization_refuses_without_bytes_changed(
    tmp_path: Path,
) -> None:
    root, library, initial = _fixture(tmp_path)
    selected_revision = _select_source(root, library, initial)
    _save_scale(root, library, selected_revision)
    save = _request(selected_revision)
    prepared_save = prepare_criterion_set_preset_from_activity(
        save, workspace_root=root, standards_library=library, clock=_clock
    )
    save_criterion_set_preset_from_activity(
        save,
        review_digest=prepared_save.review_digest,
        workspace_root=root,
        standards_library=library,
        clock=_clock,
    )
    destination_revision = _target(root, library)
    request = _apply_request(destination_revision)
    prepared_target = prepare_scoring_setup(
        request, workspace_root=root, standards_library=library, clock=_clock
    )
    before = _fingerprint(root)
    with pytest.raises(ConcordWorkflowConflictError, match="stale"):
        materialize_scoring_setup(
            request,
            review_digest="0" * 64,
            workspace_root=root,
            standards_library=library,
            clock=_clock,
        )
    assert prepared_target.review_digest != "0" * 64
    assert _fingerprint(root) == before
    assert _graph(root, library, _target_work()).criterion_sets == ()


def test_selected_source_is_not_modified_by_reusable_save(
    tmp_path: Path,
) -> None:
    root, library, initial = _fixture(tmp_path)
    selected_revision = _select_source(root, library, initial)
    before = tuple(list_work_snapshots(root, _work()))
    graph_before = _graph(root, library, _work())
    save = _request(selected_revision, recommend_scale=False)
    preview = prepare_criterion_set_preset_from_activity(
        save, workspace_root=root, standards_library=library, clock=_clock
    )
    assert "Activity-native default Scoring Scale references" in (
        preview.excluded_state
    )
    save_criterion_set_preset_from_activity(
        save, review_digest=preview.review_digest,
        workspace_root=root, standards_library=library, clock=_clock
    )
    preset = get_preset(
        "criterion_set", "saved-discussion-assessment", workspace_root=root
    )
    assert isinstance(preset, CriterionSetPresetRevision)
    assert all(
        criterion.default_scoring_scale_preset_id is None
        for criterion in preset.criteria
    )
    assert tuple(list_work_snapshots(root, _work())) == before
    assert _graph(root, library, _work()) == graph_before
    dest_revision = _target(root, library)
    request = _apply_request(
        dest_revision, scale=None, scale_revision=None
    )
    proposed = prepare_scoring_setup(
        request, workspace_root=root, standards_library=library, clock=_clock
    )
    assert proposed.recommended_scoring_scale_preset_id is None
    materialized = materialize_scoring_setup(
        request,
        review_digest=proposed.review_digest,
        workspace_root=root,
        standards_library=library,
        clock=_clock,
    )
    assert materialized.scoring_scale_id is None
    assert _graph(root, library, _target_work()).scoring_scales == ()
