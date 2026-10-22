"""Issue #140 Slice 3D: Review/Moderation successor guards and pre-return refusals.

Only fabricated Core classes and a disposable Concord workspace are used.
Passing baseline witnesses do not mean the production defects are repaired.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from issue140_slice2_fixtures import ACTIVITY_ID, ACTOR, SOURCE_CLASS, build_workspace
from pds_core.routing_models import ModuleWorkRef

import concord.menu_artifact as artifact_menu
import concord.menu_artifact_scoring as score_menu
from concord.models import EvidenceReference, PrivacyPolicy
from concord.storage import list_work_snapshots, load_current_record_graph
from concord.workflows import show_activity
from concord.workflows.artifact_page import (
    ArtifactPagePlan,
    PrepareArtifactPagesRequest,
    prepare_artifact_pages,
)
from concord.workflows.artifact_review import replace_artifact_review
from concord.workflows.artifact_routine_review import inspect_artifact_routine_review
from concord.workflows.artifact_routine_scoring import inspect_artifact_routine_scoring
from concord.workflows.errors import ConcordWorkflowNotFoundError
from concord.workflows.moderation import replace_moderation_record

MISSING_REVIEW = "issue140-3d-review-not-created"
MISSING_MODERATION = "issue140-3d-moderation-not-created"
PLANNED_ARTIFACT = "issue140-3d-unreturned-artifact"
PLANNED_PAGE = "issue140-3d-unreturned-page"


def _work() -> ModuleWorkRef:
    return ModuleWorkRef("concord", SOURCE_CLASS, ACTIVITY_ID)


def _replacement_witness(
    kind: str,
    activity: Any,
    root: Path,
    monkeypatch: pytest.MonkeyPatch,
    captured: list[Any],
    *,
    approve: bool = True,
) -> None:
    """Drive the real menu handler and real service; adapt only local input/root."""
    state = artifact_menu.MenuSessionContext(actor=ACTOR)
    evidence = EvidenceReference(
        evidence_kind="artifact_instance",
        owning_system="concord",
        record_id="issue140-3d-absent-evidence",
    )
    selected_review = SimpleNamespace(artifact_review_id=MISSING_REVIEW)
    selected_moderation = SimpleNamespace(
        moderation_record_id=MISSING_MODERATION,
        evidence_reference=evidence,
        target_subject_references=(),
    )
    monkeypatch.setattr(artifact_menu, "_latest", lambda _activity: activity)
    monkeypatch.setattr(artifact_menu, "_review_label", lambda _item: "Absent Review")
    monkeypatch.setattr(
        artifact_menu, "_moderation_label", lambda _item: "Absent Moderation"
    )
    monkeypatch.setattr(
        artifact_menu, "list_artifact_reviews", lambda *a, **kw: (selected_review,)
    )
    monkeypatch.setattr(
        artifact_menu,
        "list_moderation_records",
        lambda *a, **kw: (selected_moderation,),
    )
    monkeypatch.setattr(
        artifact_menu, "select_one", lambda _title, choices, labels, **kw: choices[0]
    )

    def answer(_title: str, label: str, **_kwargs: Any) -> str:
        if label == "Correction ID":
            return "issue140-3d-correction"
        if label == "Reason":
            return "Synthetic replacement guard witness"
        return "issue140-3d-successor"

    monkeypatch.setattr(artifact_menu, "prompt_text", answer)
    monkeypatch.setattr(artifact_menu, "confirm_write", lambda *a, **kw: approve)
    monkeypatch.setattr(
        artifact_menu,
        "show_result",
        lambda *a, **kw: pytest.fail("Guarded replacement unexpectedly succeeded"),
    )
    monkeypatch.setattr(
        artifact_menu,
        "_review_values",
        lambda: (
            "readable",
            "complete",
            "correct",
            "unknown",
            "unresolved",
            "teacher_restricted",
            "relevant",
            "not_required",
            "not_ready",
            "awaiting_additional_evidence",
            "Synthetic review judgment placeholder (not recorded)",
            PrivacyPolicy(classification="teacher_restricted"),
        ),
    )
    monkeypatch.setattr(
        artifact_menu,
        "_moderation_values",
        lambda: (
            "not_used_for_scoring",
            "not_be_used_for_scoring",
            "Synthetic moderation placeholder (not recorded)",
            None,
            PrivacyPolicy(classification="teacher_restricted"),
        ),
    )

    if kind == "review":
        service = replace_artifact_review
        service_name = "replace_artifact_review"
        handler = artifact_menu._replace_review
    elif kind == "moderation":
        service = replace_moderation_record
        service_name = "replace_moderation_record"
        handler = artifact_menu._replace_moderation
    else:
        raise AssertionError(f"Unknown replacement kind: {kind}")

    def actual_service(request: Any) -> Any:
        captured.append(request)
        return service(request, workspace_root=root)

    monkeypatch.setattr(artifact_menu, service_name, actual_service)
    handler(activity, state)


@pytest.mark.parametrize("kind", ("review", "moderation"))
def test_mixed_successor_menu_guard_precedes_missing_predecessor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    fixture = build_workspace(tmp_path, orientation="mixed")
    activity = show_activity(
        SOURCE_CLASS, ACTIVITY_ID, workspace_root=fixture.root
    ).summary
    graph_before = load_current_record_graph(
        fixture.root, _work(), standards_library=fixture.standards
    ).graph
    snapshots_before = list_work_snapshots(fixture.root, _work())
    captured: list[Any] = []
    with pytest.raises(
        Exception, match="standards_library is required for this Activity"
    ):
        _replacement_witness(kind, activity, fixture.root, monkeypatch, captured)
    assert len(captured) == 1
    assert captured[0].class_id == SOURCE_CLASS
    assert captured[0].activity_id == ACTIVITY_ID
    assert captured[0].expected_snapshot_revision == activity.snapshot_revision

    service = replace_artifact_review if kind == "review" else replace_moderation_record
    missing_id = MISSING_REVIEW if kind == "review" else MISSING_MODERATION
    expected_message = (
        "Artifact Review is not available: "
        if kind == "review"
        else "Moderation Record is not available: "
    ) + missing_id
    with pytest.raises(ConcordWorkflowNotFoundError) as error:
        service(
            captured[0],
            workspace_root=fixture.root,
            standards_library=fixture.standards,
        )
    assert str(error.value) == expected_message
    assert list_work_snapshots(fixture.root, _work()) == snapshots_before
    assert (
        load_current_record_graph(
            fixture.root, _work(), standards_library=fixture.standards
        ).graph
        == graph_before
    )


@pytest.mark.parametrize("kind", ("review", "moderation"))
def test_neutral_successor_menu_reaches_identity_without_standards(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    fixture = build_workspace(tmp_path, orientation="evidence_only")
    activity = show_activity(
        SOURCE_CLASS, ACTIVITY_ID, workspace_root=fixture.root
    ).summary
    snapshots_before = list_work_snapshots(fixture.root, _work())
    captured: list[Any] = []
    with pytest.raises(ConcordWorkflowNotFoundError) as error:
        _replacement_witness(kind, activity, fixture.root, monkeypatch, captured)
    assert len(captured) == 1
    assert "is not available:" in str(error.value)
    assert "standards_library" not in str(error.value)
    assert list_work_snapshots(fixture.root, _work()) == snapshots_before


@pytest.mark.parametrize("kind", ("review", "moderation"))
def test_cancel_successor_menu_never_calls_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    fixture = build_workspace(tmp_path, orientation="mixed")
    activity = show_activity(
        SOURCE_CLASS, ACTIVITY_ID, workspace_root=fixture.root
    ).summary
    snapshots_before = list_work_snapshots(fixture.root, _work())
    captured: list[Any] = []
    _replacement_witness(
        kind, activity, fixture.root, monkeypatch, captured, approve=False
    )
    assert captured == []
    assert list_work_snapshots(fixture.root, _work()) == snapshots_before


@pytest.mark.parametrize("orientation", ("mixed", "evidence_only"))
def test_planned_unreturned_artifact_blocks_quick_review_and_routine_score(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, orientation: str
) -> None:
    fixture = build_workspace(tmp_path, orientation=orientation)
    activity = show_activity(
        SOURCE_CLASS, ACTIVITY_ID, workspace_root=fixture.root
    ).summary
    prepared = prepare_artifact_pages(
        PrepareArtifactPagesRequest(
            class_id=SOURCE_CLASS,
            activity_id=ACTIVITY_ID,
            artifact_instance_id=PLANNED_ARTIFACT,
            template_version_id="issue140-3d-synthetic-template",
            artifact_category="student_work",
            expected_snapshot_revision=activity.snapshot_revision,
            actor=ACTOR,
            privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
            pages=(
                ArtifactPagePlan(
                    page_number=1,
                    artifact_page_id=PLANNED_PAGE,
                    return_expected=True,
                    route_required=False,
                ),
            ),
        ),
        workspace_root=fixture.root,
        standards_library=(fixture.standards if orientation == "mixed" else None),
    )
    assert prepared.routes_expected == 0
    assert prepared.routes_verified == 0
    latest = show_activity(
        SOURCE_CLASS, ACTIVITY_ID, workspace_root=fixture.root
    ).summary
    before = list_work_snapshots(fixture.root, _work())
    graph = load_current_record_graph(
        fixture.root,
        _work(),
        standards_library=fixture.standards if orientation == "mixed" else None,
    ).graph
    assert len(graph.artifact_instances) == 1
    assert graph.artifact_instances[0].artifact_status == "planned"
    assert len(graph.artifact_pages) == 1
    assert graph.artifact_pages[0].page_status == "planned"
    assert graph.scan_references == ()
    assert graph.artifact_reviews == ()
    assert graph.score_records == ()
    assert graph.score_evidence_links == ()

    review_context = inspect_artifact_routine_review(
        SOURCE_CLASS, ACTIVITY_ID, PLANNED_ARTIFACT, workspace_root=fixture.root
    )
    assert not review_context.eligibility.quick_review_eligible
    scoring_context = inspect_artifact_routine_scoring(
        SOURCE_CLASS, ACTIVITY_ID, PLANNED_ARTIFACT, workspace_root=fixture.root
    )
    assert not scoring_context.eligibility.routine_scoring_eligible
    assert any(
        "Review" in reason for reason in scoring_context.eligibility.exception_reasons
    )

    review_notices: list[tuple[str, tuple[str, ...]]] = []
    monkeypatch.setattr(artifact_menu, "select_one", lambda *a, **kw: "continue")
    monkeypatch.setattr(
        artifact_menu,
        "inspect_artifact_routine_review",
        lambda c, a, i: inspect_artifact_routine_review(
            c, a, i, workspace_root=fixture.root
        ),
    )
    monkeypatch.setattr(
        artifact_menu,
        "show_result",
        lambda title, lines: review_notices.append((title, tuple(lines))),
    )
    monkeypatch.setattr(
        artifact_menu,
        "confirm_write",
        lambda *a, **kw: pytest.fail("Unreturned work cannot enter Review write"),
    )
    monkeypatch.setattr(
        artifact_menu,
        "record_routine_artifact_review",
        lambda *a, **kw: pytest.fail("No quick Review on planned evidence"),
    )
    outcome = artifact_menu._quick_review_selected(
        latest,
        SimpleNamespace(artifact_instance_id=PLANNED_ARTIFACT),
        artifact_menu.MenuSessionContext(actor=ACTOR),
    )
    assert outcome is False
    assert any(
        "Quick Review is not available" in " ".join(lines)
        for _, lines in review_notices
    )

    score_notices: list[tuple[str, tuple[str, ...]]] = []
    monkeypatch.setattr(score_menu, "_current_activity", lambda _activity: latest)
    monkeypatch.setattr(
        score_menu,
        "inspect_artifact_routine_scoring",
        lambda c, a, i: inspect_artifact_routine_scoring(
            c, a, i, workspace_root=fixture.root
        ),
    )
    monkeypatch.setattr(
        score_menu,
        "show_result",
        lambda title, lines: score_notices.append((title, tuple(lines))),
    )
    monkeypatch.setattr(
        score_menu,
        "_choose_target",
        lambda *a, **kw: pytest.fail("Unreturned work cannot choose Score target"),
    )
    monkeypatch.setattr(
        score_menu,
        "record_prepared_routine_score",
        lambda *a, **kw: pytest.fail("No Score on planned work"),
    )
    monkeypatch.setattr(
        score_menu,
        "confirm_write",
        lambda *a, **kw: pytest.fail("No Score confirmation on planned work"),
    )
    score_result = score_menu._record_selected_artifact_score(
        latest, PLANNED_ARTIFACT, score_menu.MenuSessionContext(actor=ACTOR)
    )
    assert score_result is None
    assert any(
        "Routine scoring is not available" in " ".join(lines)
        for _, lines in score_notices
    )
    assert list_work_snapshots(fixture.root, _work()) == before
    after = load_current_record_graph(
        fixture.root,
        _work(),
        standards_library=fixture.standards if orientation == "mixed" else None,
    ).graph
    assert after == graph
    assert after.score_records == ()
    assert after.score_evidence_links == ()
