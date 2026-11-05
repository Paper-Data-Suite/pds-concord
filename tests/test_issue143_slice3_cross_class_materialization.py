"""#143 Slice 3: saved mixed Criterion/Scale -> distinct synthetic Core class.

All writes are inside pytest's temporary workspace. No real teacher data,
student Scores, returned evidence, Suite, Core modifications or publication.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.routing_models import ModuleWorkRef
from pds_core.standards import StandardsLibrary, StandardsProfile
from test_issue143_slice2_native_preset_save import (
    ALIGNMENT,
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

from concord import menu_scoring
from concord.menu_context import MenuSessionContext
from concord.models import ScoringScaleLevel
from concord.storage import list_work_snapshots, load_current_record_graph
from concord.workflows.activity import create_activity_context, show_activity
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowValidationError,
)
from concord.workflows.models import (
    CreateActivityContextRequest,
    CreateSessionRequest,
)
from concord.workflows.reusable_presets import (
    CreateScoringScalePresetRequest,
    CriterionTargetIdentity,
    MaterializeScoringSetupRequest,
    create_scoring_scale_preset,
    get_preset,
    get_preset_revision,
    list_presets,
    materialize_scoring_setup,
    prepare_criterion_set_preset_from_activity,
    prepare_scoring_setup,
    save_criterion_set_preset_from_activity,
)
from concord.workflows.session import create_session

TARGET_CLASS = "synthetic-class-p4"
TARGET_ACTIVITY = "synthetic-discussion-p4"
TARGET_SET = "fresh-criterion-set-p4"
TARGET_SCALE = "fresh-scale-p4"
TARGET_CRITERION_STUDENT = "fresh-student-criterion-p4"
TARGET_CRITERION_GROUP = "fresh-group-criterion-p4"


def _target_work() -> ModuleWorkRef:
    return ModuleWorkRef(
        module_id="concord", class_id=TARGET_CLASS, work_id=TARGET_ACTIVITY
    )


def _target(
    root: Path,
    library: StandardsLibrary,
    *,
    profile_id: str = PROFILE,
    focus: tuple[str, ...] = (STANDARD, ALIGNMENT),
) -> int:
    write_class_metadata_for_class(
        root,
        create_class_metadata(TARGET_CLASS, "2026-2027", created_at=_clock()),
    )
    created = create_activity_context(
        CreateActivityContextRequest(
            class_id=TARGET_CLASS,
            activity_id=TARGET_ACTIVITY,
            title="Independent synthetic Period 4 discussion",
            activity_type="project",
            scoring_orientation="mixed",
            session_id="synthetic-session-p4",
            actor=_actor(),
            standards_profile_id=profile_id,
            focus_standard_ids=focus,
        ),
        workspace_root=root,
        standards_library=library,
        clock=_clock,
    )
    return created.commit.snapshot_revision


def _save_source(
    root: Path, library: StandardsLibrary, revision: int, *, recommend: bool
) -> None:
    _save_scale(root, library, revision)
    request = _request(revision, recommend_scale=recommend)
    prepared = prepare_criterion_set_preset_from_activity(
        request, workspace_root=root, standards_library=library, clock=_clock
    )
    save_criterion_set_preset_from_activity(
        request,
        review_digest=prepared.review_digest,
        workspace_root=root,
        standards_library=library,
        clock=_clock,
    )


def _apply_request(
    revision: int,
    *,
    scale: str | None = "saved-four-level",
    scale_revision: str | None = "saved-four-level-v1",
) -> MaterializeScoringSetupRequest:
    return MaterializeScoringSetupRequest(
        criterion_preset_id="saved-discussion-assessment",
        criterion_preset_revision_id="saved-discussion-assessment-v1",
        class_id=TARGET_CLASS,
        activity_id=TARGET_ACTIVITY,
        criterion_set_id=TARGET_SET,
        criterion_set_lineage_id="fresh-criterion-set-lineage-p4",
        criterion_ids=(
            CriterionTargetIdentity(
                criterion_key="discussion_participation",
                criterion_id=TARGET_CRITERION_STUDENT,
            ),
            CriterionTargetIdentity(
                criterion_key="collaborative_textual_analysis",
                criterion_id=TARGET_CRITERION_GROUP,
            ),
        ),
        expected_snapshot_revision=revision,
        actor=_actor(),
        scoring_scale_preset_id=scale,
        scoring_scale_preset_revision_id=scale_revision,
        scoring_scale_id=TARGET_SCALE if scale else None,
        scoring_scale_lineage_id="fresh-scale-lineage-p4" if scale else None,
    )


def _graph(root: Path, library: StandardsLibrary, work: ModuleWorkRef):
    return load_current_record_graph(
        root, work, standards_library=library
    ).graph


def _no_target_write(
    root: Path,
    library: StandardsLibrary,
    before_snapshots: tuple[object, ...],
    before_graph: object,
) -> None:
    assert tuple(list_work_snapshots(root, _target_work())) == before_snapshots
    assert _graph(root, library, _target_work()) == before_graph


def _check_materialized(
    root: Path,
    library: StandardsLibrary,
    *,
    scale_id: str | None,
    expected_scale_levels: tuple[ScoringScaleLevel, ...] | None,
) -> None:
    target = _graph(root, library, _target_work())
    source = _graph(root, library, _work())
    assert len(target.criterion_sets) == 1
    assert len(target.criteria) == 2
    assert target.activities[0].criterion_set_ids == (TARGET_SET,)
    criterion_set = target.criterion_sets[0]
    assert criterion_set.criterion_set_id == TARGET_SET
    assert criterion_set.standards_profile_id == PROFILE
    assert criterion_set.criterion_set_kind == "mixed"
    assert criterion_set.criterion_ids == (
        TARGET_CRITERION_STUDENT, TARGET_CRITERION_GROUP
    )
    # Record graphs do not promise Criterion tuple ordering. The native Set's
    # criterion_ids above is the authoritative ordering; look up records by ID.
    criteria_by_id = {item.criterion_id: item for item in target.criteria}
    assert len(criteria_by_id) == 2
    first = criteria_by_id[TARGET_CRITERION_STUDENT]
    second = criteria_by_id[TARGET_CRITERION_GROUP]
    assert first.criterion_id == TARGET_CRITERION_STUDENT
    assert first.criterion_kind == "standard_backed"
    assert first.standard_id == STANDARD
    assert first.alignment_standard_ids == (ALIGNMENT,)
    assert first.supported_target_kinds == ("core_student",)
    assert second.criterion_id == TARGET_CRITERION_GROUP
    assert second.criterion_kind == "local"
    assert second.standard_id is None
    assert second.supported_target_kinds == ("concord_group",)
    assert (first.default_scoring_scale_id, second.default_scoring_scale_id) == (
        scale_id, scale_id
    )
    assert len(target.scoring_scales) == (1 if scale_id else 0)
    if expected_scale_levels is not None:
        assert target.scoring_scales[0].scoring_scale_id == scale_id
        assert target.scoring_scales[0].levels == expected_scale_levels
        assert target.scoring_scales[0].scale_type == "ordinal"
    assert target.score_records == ()
    assert target.score_evidence_links == ()
    assert source.score_records == ()
    assert source.score_evidence_links == ()
    assert source.criterion_sets[0].criterion_set_id == SET
    assert source.scoring_scales[0].scoring_scale_id == SCALE
    assert all(item.criterion_id not in {x.criterion_id for x in source.criteria}
               for item in target.criteria)


def test_second_class_recommended_scale_keeps_exact_four_levels_and_targets(
    tmp_path: Path,
) -> None:
    root, library, source_revision = _fixture(tmp_path)
    source_before = tuple(list_work_snapshots(root, _work()))
    source_graph_before = _graph(root, library, _work())
    _save_source(root, library, source_revision, recommend=True)
    target_revision = _target(root, library)
    request = _apply_request(target_revision)
    before = tuple(list_work_snapshots(root, _target_work()))
    prepared = prepare_scoring_setup(
        request, workspace_root=root, standards_library=library, clock=_clock
    )
    assert prepared.criterion_count == 2
    assert prepared.standards_profile_id == PROFILE
    assert prepared.recommended_scoring_scale_preset_id == "saved-four-level"
    assert prepared.scoring_scale_preset_name == "Four-Level Standards Proficiency"
    assert tuple(list_work_snapshots(root, _target_work())) == before
    receipt = materialize_scoring_setup(
        request,
        review_digest=prepared.review_digest,
        workspace_root=root,
        standards_library=library,
        clock=_clock,
    )
    assert receipt.commit.snapshot_revision == target_revision + 1
    assert len(list_work_snapshots(root, _target_work())) == len(before) + 1
    assert receipt.criterion_set_id == TARGET_SET
    assert receipt.criterion_ids == (
        TARGET_CRITERION_STUDENT, TARGET_CRITERION_GROUP
    )
    assert receipt.scoring_scale_id == TARGET_SCALE
    source_scale = source_graph_before.scoring_scales[0]
    _check_materialized(
        root, library, scale_id=TARGET_SCALE,
        expected_scale_levels=source_scale.levels,
    )
    assert tuple(list_work_snapshots(root, _work())) == source_before
    assert _graph(root, library, _work()) == source_graph_before


def test_second_class_can_choose_an_explicit_alternate_saved_scale(
    tmp_path: Path,
) -> None:
    root, library, source_revision = _fixture(tmp_path)
    _save_source(root, library, source_revision, recommend=True)
    target_revision = _target(root, library)
    alternate_levels = (
        ScoringScaleLevel(
            value="developing", label="Developing", meaning="Needs evidence", position=1
        ),
        ScoringScaleLevel(
            value="meeting", label="Meeting", meaning="Has evidence", position=2
        ),
    )
    create_scoring_scale_preset(
        CreateScoringScalePresetRequest(
            preset_id="alternate-saved-scale",
            preset_revision_id="alternate-saved-scale-v1",
            name="Alternate two-level scale",
            scale_type="ordinal",
            levels=alternate_levels,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=_clock,
    )
    request = _apply_request(
        target_revision,
        scale="alternate-saved-scale",
        scale_revision="alternate-saved-scale-v1",
    )
    prepared = prepare_scoring_setup(
        request, workspace_root=root, standards_library=library
    )
    assert prepared.recommended_scoring_scale_preset_id == "saved-four-level"
    assert prepared.scoring_scale_preset_name == "Alternate two-level scale"
    materialize_scoring_setup(
        request, review_digest=prepared.review_digest,
        workspace_root=root, standards_library=library,
    )
    _check_materialized(
        root, library, scale_id=TARGET_SCALE, expected_scale_levels=alternate_levels
    )


def test_no_recommendation_allows_no_new_scale_or_default(
    tmp_path: Path,
) -> None:
    root, library, source_revision = _fixture(tmp_path)
    _save_source(root, library, source_revision, recommend=False)
    target_revision = _target(root, library)
    request = _apply_request(target_revision, scale=None, scale_revision=None)
    prepared = prepare_scoring_setup(
        request, workspace_root=root, standards_library=library
    )
    assert prepared.recommended_scoring_scale_preset_id is None
    assert prepared.scoring_scale_preset_name is None
    receipt = materialize_scoring_setup(
        request, review_digest=prepared.review_digest,
        workspace_root=root, standards_library=library,
    )
    assert receipt.scoring_scale_id is None
    _check_materialized(root, library, scale_id=None, expected_scale_levels=None)


def test_recommended_scale_cannot_be_silently_omitted(tmp_path: Path) -> None:
    root, library, source_revision = _fixture(tmp_path)
    _save_source(root, library, source_revision, recommend=True)
    target_revision = _target(root, library)
    request = _apply_request(target_revision, scale=None, scale_revision=None)
    before = tuple(list_work_snapshots(root, _target_work()))
    graph_before = _graph(root, library, _target_work())
    with pytest.raises(ConcordWorkflowValidationError, match="recommends"):
        prepare_scoring_setup(
            request, workspace_root=root, standards_library=library
        )
    _no_target_write(root, library, before, graph_before)


@pytest.mark.parametrize("failure", ("bad_focus", "bad_profile"))
def test_wrong_focus_or_profile_rejected_without_target_write(
    tmp_path: Path, failure: str
) -> None:
    root, library, source_revision = _fixture(tmp_path)
    _save_source(root, library, source_revision, recommend=True)
    if failure == "bad_profile":
        library = replace(
            library,
            profiles=(*library.profiles, StandardsProfile(
                profile_id="synthetic-other-profile", standards=(STANDARD, ALIGNMENT)
            )),
        )
    target_revision = _target(
        root, library,
        profile_id="synthetic-other-profile" if failure == "bad_profile" else PROFILE,
        focus=(STANDARD, ALIGNMENT) if failure == "bad_profile" else (ALIGNMENT,),
    )
    request = _apply_request(target_revision)
    before = tuple(list_work_snapshots(root, _target_work()))
    graph_before = _graph(root, library, _target_work())
    with pytest.raises(ConcordWorkflowValidationError, match="profile|Focus"):
        prepare_scoring_setup(
            request, workspace_root=root, standards_library=library
        )
    _no_target_write(root, library, before, graph_before)


@pytest.mark.parametrize(
    "failure", ("duplicate_keys", "missing_key", "unpaired_scale", "bad_digest")
)
def test_invalid_identity_or_review_is_zero_write(
    tmp_path: Path, failure: str
) -> None:
    root, library, source_revision = _fixture(tmp_path)
    _save_source(root, library, source_revision, recommend=True)
    revision = _target(root, library)
    request = _apply_request(revision)
    if failure == "duplicate_keys":
        request = replace(request, criterion_ids=(request.criterion_ids[0],) * 2)
    elif failure == "missing_key":
        request = replace(request, criterion_ids=(request.criterion_ids[0],))
    elif failure == "unpaired_scale":
        request = replace(request, scoring_scale_preset_revision_id=None)
    before = tuple(list_work_snapshots(root, _target_work()))
    graph_before = _graph(root, library, _target_work())
    if failure == "bad_digest":
        prepared = prepare_scoring_setup(
            request, workspace_root=root, standards_library=library
        )
        with pytest.raises(ConcordWorkflowConflictError, match="stale"):
            materialize_scoring_setup(
                request, review_digest="0" * 64,
                workspace_root=root, standards_library=library,
            )
        assert prepared.review_digest != "0" * 64
    else:
        with pytest.raises(ConcordWorkflowValidationError):
            prepare_scoring_setup(
                request, workspace_root=root, standards_library=library
            )
    _no_target_write(root, library, before, graph_before)



def test_changed_target_snapshot_after_preview_requires_fresh_review(
    tmp_path: Path,
) -> None:
    root, library, source_revision = _fixture(tmp_path)
    _save_source(root, library, source_revision, recommend=True)
    revision = _target(root, library)
    request = _apply_request(revision)
    prepared = prepare_scoring_setup(
        request, workspace_root=root, standards_library=library
    )
    changed = create_session(
        CreateSessionRequest(
            class_id=TARGET_CLASS,
            activity_id=TARGET_ACTIVITY,
            session_id="new-session-after-preview",
            sequence=2,
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
        standards_library=library,
    )
    assert changed.commit.snapshot_revision == revision + 1
    before = tuple(list_work_snapshots(root, _target_work()))
    graph_before = _graph(root, library, _target_work())
    with pytest.raises(ConcordWorkflowConflictError):
        materialize_scoring_setup(
            request, review_digest=prepared.review_digest,
            workspace_root=root, standards_library=library,
        )
    _no_target_write(root, library, before, graph_before)


def test_same_target_duplicate_materialization_is_zero_write(tmp_path: Path) -> None:
    root, library, source_revision = _fixture(tmp_path)
    _save_source(root, library, source_revision, recommend=True)
    revision = _target(root, library)
    request = _apply_request(revision)
    prepared = prepare_scoring_setup(
        request, workspace_root=root, standards_library=library
    )
    materialize_scoring_setup(
        request, review_digest=prepared.review_digest,
        workspace_root=root, standards_library=library,
    )
    before = tuple(list_work_snapshots(root, _target_work()))
    graph_before = _graph(root, library, _target_work())
    with pytest.raises((ConcordWorkflowConflictError, ConcordWorkflowValidationError)):
        materialize_scoring_setup(
            request, review_digest=prepared.review_digest,
            workspace_root=root, standards_library=library,
        )
    _no_target_write(root, library, before, graph_before)


def _wire_menu(
    monkeypatch: pytest.MonkeyPatch,
    root: Path,
    library: StandardsLibrary,
    *,
    approve: bool,
    outcomes: list[tuple[str, tuple[str, ...]]],
) -> None:
    monkeypatch.setattr(
        menu_scoring, "_latest",
        lambda _summary: show_activity(
            TARGET_CLASS, TARGET_ACTIVITY, workspace_root=root
        ).summary,
    )
    monkeypatch.setattr(menu_scoring, "_library", lambda: library)
    monkeypatch.setattr(
        menu_scoring, "list_presets",
        lambda kind, **kwargs: list_presets(kind, workspace_root=root, **kwargs),
    )
    monkeypatch.setattr(
        menu_scoring, "get_preset",
        lambda kind, preset_id, **kwargs: get_preset(
            kind, preset_id, workspace_root=root, **kwargs
        ),
    )
    monkeypatch.setattr(
        menu_scoring, "get_preset_revision",
        lambda kind, preset_id, revision_id, **kwargs: get_preset_revision(
            kind, preset_id, revision_id, workspace_root=root, **kwargs
        ),
    )
    monkeypatch.setattr(
        menu_scoring, "prepare_scoring_setup",
        lambda request, **kwargs: prepare_scoring_setup(
            request, workspace_root=root, **kwargs
        ),
    )
    monkeypatch.setattr(
        menu_scoring, "materialize_scoring_setup",
        lambda request, **kwargs: materialize_scoring_setup(
            request, workspace_root=root, **kwargs
        ),
    )
    monkeypatch.setattr(
        menu_scoring, "select_one", lambda _title, vals, *_a, **_k: vals[-1]
    )
    monkeypatch.setattr(menu_scoring, "confirm_write", lambda *_a, **_k: approve)
    monkeypatch.setattr("builtins.input", lambda _prompt: "1")
    monkeypatch.setattr(menu_scoring, "clear_screen", lambda: None)
    monkeypatch.setattr(
        menu_scoring,
        "show_result",
        lambda title, lines: outcomes.append((title, tuple(lines))),
    )
    monkeypatch.setattr(
        menu_scoring, "_handle_error",
        lambda _summary, error: pytest.fail(f"Menu materialization failed: {error}"),
    )


@pytest.mark.parametrize("approve", (True, False))
def test_actual_teacher_menu_materializes_or_cancels_with_zero_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, approve: bool
) -> None:
    root, library, source_revision = _fixture(tmp_path)
    _save_source(root, library, source_revision, recommend=True)
    _target(root, library)
    before = tuple(list_work_snapshots(root, _target_work()))
    source_before = tuple(list_work_snapshots(root, _work()))
    target_graph_before = _graph(root, library, _target_work())
    outcomes: list[tuple[str, tuple[str, ...]]] = []
    _wire_menu(monkeypatch, root, library, approve=approve, outcomes=outcomes)
    menu_scoring._use_saved_scoring_setup(
        show_activity(TARGET_CLASS, TARGET_ACTIVITY, workspace_root=root).summary,
        MenuSessionContext(actor=_actor()),
    )
    current = _graph(root, library, _target_work())
    if approve:
        assert len(list_work_snapshots(root, _target_work())) == len(before) + 1
        assert current.score_records == ()
        assert current.score_evidence_links == ()
        assert len(current.criterion_sets) == 1
        assert len(current.criteria) == 2
        assert len(current.scoring_scales) == 1
        # The graph's record tuple is not ordered by the Criterion Set.
        by_key = {item.key: item for item in current.criteria}
        assert set(by_key) == {
            "discussion_participation", "collaborative_textual_analysis"
        }
        assert by_key["discussion_participation"].standard_id == STANDARD
        assert by_key["collaborative_textual_analysis"].supported_target_kinds == (
            "concord_group",
        )
        assert any(title == "Scoring Setup Added" for title, _ in outcomes)
    else:
        _no_target_write(root, library, before, target_graph_before)
        # The #145 teacher-first menu now shows an exact, read-only preset
        # preview even when the subsequent USE confirmation is declined.
        assert [title for title, _ in outcomes] == [
            "Saved Assessment — Read-only Preview",
        ]
        assert any(
            "No Activity configuration, Scores, or evidence changed." in lines
            for title, lines in outcomes
            if title == "Saved Assessment — Read-only Preview"
        )
    assert tuple(list_work_snapshots(root, _work())) == source_before
