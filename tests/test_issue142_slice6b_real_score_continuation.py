"""Issue #142 Slice 6B: genuine synthetic standards-backed Score integration.

Only pytest tmp_path workspaces and fabricated scan pixels are used.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pds_core.routing_models import ModuleWorkRef
from pds_core.standards import write_workspace_standards_library
from test_workflow_artifact_assembly import _file, _retained_image
from test_workflow_score_recording import _workspace as scoring_workspace

import concord.menu_artifact as review_menu
import concord.menu_artifact_scoring as scoring_menu
import concord.menu_artifact_write_context as authority
from concord.models import (
    ParticipantReference,
    PrivacyPolicy,
    ScoreTargetReference,
    SubjectReference,
)
from concord.storage import list_work_snapshots, load_current_record_graph
from concord.workflows import (
    AddArtifactAuthorRequest,
    AddArtifactSubjectRequest,
    ArtifactPagePlan,
    PrepareArtifactPagesRequest,
    add_artifact_author,
    add_artifact_subject,
    prepare_artifact_pages,
    show_activity,
)
from concord.workflows.artifact import list_artifacts
from concord.workflows.artifact_assembly import (
    AssembleArtifactRequest,
    assemble_returned_artifact,
)
from concord.workflows.artifact_routine_review import inspect_artifact_routine_review
from concord.workflows.artifact_routine_scoring import inspect_artifact_routine_scoring
from concord.workflows.artifact_routine_scoring_continuation import (
    reload_routine_scoring_after_score,
)
from concord.workflows.artifact_routine_scoring_execution import (
    record_prepared_routine_score,
)
from concord.workflows.artifact_routine_scoring_preparation import (
    ROUTINE_ARTIFACT_RELEVANCE_DESCRIPTION,
    RoutineScorePreparationRequest,
    prepare_routine_score_preview,
)
from concord.workflows.errors import ConcordWorkflowValidationError
from concord.workflows.models import WorkflowActor

CLASS = "class-1"
ACTIVITY = "activity-1"
ARTIFACT = "artifact-1"
ACTOR = WorkflowActor(actor_id="teacher-1")
WORK = ModuleWorkRef("concord", CLASS, ACTIVITY)


def _revision(root: Path) -> int:
    return show_activity(CLASS, ACTIVITY, workspace_root=root).summary.snapshot_revision


def _setup_reviewed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, object]:
    # Existing real Core setup: student roster, standard-backed and local
    # Criteria, an active Scale, and an explicitly selected Criterion Set.
    root, _initial_revision, standards = scoring_workspace(tmp_path)
    write_workspace_standards_library(root, standards)
    prepared = prepare_artifact_pages(
        PrepareArtifactPagesRequest(
            class_id=CLASS,
            activity_id=ACTIVITY,
            artifact_instance_id=ARTIFACT,
            template_version_id="slice6b-synthetic-template",
            artifact_category="observation",
            expected_snapshot_revision=_revision(root),
            actor=ACTOR,
            privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
            pages=(ArtifactPagePlan(page_number=1, artifact_page_id="page-1"),),
        ),
        workspace_root=root,
        standards_library=standards,
    )
    retained = _retained_image(
        root,
        scan_id="slice6b-fabricated-scan",
        filename="slice6b-fabricated-pixels.png",
        color=(40, 60, 80),
    )
    _file(root, prepared, 0, retained)
    assembled = assemble_returned_artifact(
        AssembleArtifactRequest(
            class_id=CLASS,
            activity_id=ACTIVITY,
            artifact_instance_id=ARTIFACT,
            expected_snapshot_revision=_revision(root),
            actor=ACTOR,
        ),
        workspace_root=root,
    )
    assert assembled.output_path.read_bytes().startswith(b"%PDF")
    add_artifact_author(
        AddArtifactAuthorRequest(
            class_id=CLASS,
            activity_id=ACTIVITY,
            artifact_instance_id=ARTIFACT,
            artifact_author_id="slice6b-author-1",
            author_reference=ParticipantReference(
                participant_kind="core_student",
                participant_id="student-1",
                owning_system="core",
            ),
            authorship_mode="individual_author",
            attribution_status="confirmed",
            attribution_source="teacher",
            expected_snapshot_revision=_revision(root),
            actor=ACTOR,
        ),
        workspace_root=root,
        standards_library=standards,
    )
    add_artifact_subject(
        AddArtifactSubjectRequest(
            class_id=CLASS,
            activity_id=ACTIVITY,
            artifact_instance_id=ARTIFACT,
            artifact_subject_id="slice6b-subject-1",
            subject_reference=SubjectReference(
                subject_kind="core_student",
                subject_id="student-2",
                owning_system="core",
            ),
            subject_role="observed_participant",
            confirmation_status="confirmed",
            assignment_source="teacher",
            expected_snapshot_revision=_revision(root),
            actor=ACTOR,
        ),
        workspace_root=root,
        standards_library=standards,
    )
    eligible = inspect_artifact_routine_review(
        CLASS, ACTIVITY, ARTIFACT, workspace_root=root
    )
    assert eligible.assembly_state == "assembled"
    assert eligible.eligibility.quick_review_eligible

    def resolver(explicit: str | Path | None = None) -> Path:
        return root if explicit is None else Path(explicit)
    monkeypatch.setattr(authority, "resolve_read_workspace_root", resolver)
    # Scoring labels must not consult the machine's default school workspace.
    monkeypatch.setattr(scoring_menu, "resolve_read_workspace_root", resolver)
    responses = iter(("continue", "ready"))
    monkeypatch.setattr(review_menu, "select_one", lambda *a, **kw: next(responses))
    monkeypatch.setattr(review_menu, "confirm_write", lambda *a, **kw: True)
    monkeypatch.setattr(review_menu, "show_result", lambda *a, **kw: None)
    activity = show_activity(CLASS, ACTIVITY, workspace_root=root).summary
    (artifact,) = list_artifacts(CLASS, ACTIVITY, workspace_root=root)
    assert review_menu._quick_review_selected(
        activity, artifact, review_menu.MenuSessionContext(actor=ACTOR)
    )
    review = inspect_artifact_routine_review(
        CLASS, ACTIVITY, ARTIFACT, workspace_root=root
    )
    assert review.current_review is not None
    assert review.current_review.scoring_readiness == "ready"
    return root, standards


def _first_score(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> scoring_menu._RoutineScoreMenuResult:
    monkeypatch.setattr(
        scoring_menu,
        "_current_activity",
        lambda _activity: show_activity(CLASS, ACTIVITY, workspace_root=root).summary,
    )
    monkeypatch.setattr(
        scoring_menu,
        "_choose_target",
        lambda *a: ScoreTargetReference(
            target_kind="core_student",
            target_id="student-1",
            owning_system="core",
        ),
    )
    monkeypatch.setattr(
        scoring_menu,
        "_choose_criterion",
        lambda context, _target: next(
            item for item in context.eligible_criteria
            if item.criterion_id == "criterion-standard"
        ),
    )
    monkeypatch.setattr(
        scoring_menu,
        "_choose_scale",
        lambda context, *_args: next(
            item for item in context.current_scoring_scales
            if item.scoring_scale_id == "scale-1"
        ),
    )
    monkeypatch.setattr(scoring_menu, "_choose_level", lambda scale: scale.levels[2])
    monkeypatch.setattr(scoring_menu, "_choose_session", lambda _context: None)
    monkeypatch.setattr(scoring_menu, "_choose_subject_context", lambda *a: ())
    monkeypatch.setattr(
        scoring_menu,
        "_choose_relevance",
        lambda: ROUTINE_ARTIFACT_RELEVANCE_DESCRIPTION,
    )
    monkeypatch.setattr(scoring_menu, "confirm_write", lambda *a, **kw: True)
    monkeypatch.setattr(scoring_menu, "show_result", lambda *a, **kw: None)
    result = scoring_menu._record_selected_artifact_score(
        show_activity(CLASS, ACTIVITY, workspace_root=root).summary,
        ARTIFACT,
        scoring_menu.MenuSessionContext(actor=ACTOR),
    )
    assert result is not None
    return result


def test_real_standard_backed_and_second_criterion_record_distinct_scores(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, standards = _setup_reviewed(tmp_path, monkeypatch)
    before = list_work_snapshots(root, WORK)
    context = inspect_artifact_routine_scoring(
        CLASS, ACTIVITY, ARTIFACT, workspace_root=root
    )
    assert context.eligibility.routine_scoring_eligible
    first = _first_score(root, monkeypatch)
    assert first.write_context is not None
    assert first.preview.criterion_id == "criterion-standard"
    assert first.preview.standard_id == "standard-1"
    assert first.preview.value == 3
    assert len(list_work_snapshots(root, WORK)) == len(before) + 1

    continuation = reload_routine_scoring_after_score(
        first.preview, first.mutation, workspace_root=root
    )
    assert continuation.context.snapshot_revision > first.preview.snapshot_revision
    assert continuation.retained_target_reference == first.preview.target_reference
    assert continuation.context.eligibility.routine_scoring_eligible
    monkeypatch.setattr(
        scoring_menu,
        "select_one",
        lambda _title, items, _labels, **kw: next(
            item for item in items if item.criterion_id == "criterion-local"
        ),
    )
    monkeypatch.setattr(scoring_menu, "_choose_level", lambda scale: scale.levels[3])
    second = scoring_menu._record_another_criterion(
        show_activity(CLASS, ACTIVITY, workspace_root=root).summary,
        continuation,
        scoring_menu.MenuSessionContext(actor=ACTOR),
        origin_context=first.write_context,
    )
    assert second is not None
    assert second.preview.criterion_id == "criterion-local"
    assert second.preview.standard_id is None
    assert second.preview.value == 4
    assert second.preview.snapshot_revision == first.mutation.commit.snapshot_revision
    assert (
        second.mutation.commit.snapshot_revision
        > first.mutation.commit.snapshot_revision
    )
    assert second.write_context is not None
    assert second.write_context.root == root
    assert len(list_work_snapshots(root, WORK)) == len(before) + 2

    graph = load_current_record_graph(
        root, WORK, standards_library=standards
    ).graph
    assert len(graph.score_records) == 2
    assert len(graph.score_evidence_links) == 2
    assert {item.criterion_id for item in graph.score_records} == {
        "criterion-standard", "criterion-local"
    }
    assert {
        item.evidence_reference.record_id for item in graph.score_evidence_links
    } == {ARTIFACT}


def test_real_duplicate_standard_score_cannot_create_parallel_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, standards = _setup_reviewed(tmp_path, monkeypatch)
    first = _first_score(root, monkeypatch)
    context = inspect_artifact_routine_scoring(
        CLASS, ACTIVITY, ARTIFACT, workspace_root=root
    )
    proposal = prepare_routine_score_preview(
        context,
        RoutineScorePreparationRequest(
            target_reference=first.preview.target_reference,
            criterion_id="criterion-standard",
            scoring_scale_id="scale-1",
            value=3,
            session_id=None,
            subject_context=(),
            relevance_description=ROUTINE_ARTIFACT_RELEVANCE_DESCRIPTION,
        ),
    )
    assert proposal.existing_current_score_ids
    revision = _revision(root)
    with pytest.raises(
        ConcordWorkflowValidationError, match="current Score already exists"
    ):
        record_prepared_routine_score(
            proposal,
            actor=ACTOR,
            workspace_root=root,
            standards_library=standards,
        )
    assert _revision(root) == revision
    assert len(load_current_record_graph(
        root, WORK, standards_library=standards
    ).graph.score_records) == 1
