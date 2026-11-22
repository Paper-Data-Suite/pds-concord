"""#151 Slice 0: synthetic RED witnesses for authoritative paper-return collection.

Deliberate strict xfails capture presently missing behavior, without writing a
workspace. They are *not* acceptance of the missing safety gate: repair slices
must remove xfail after the same test passes against the real owner path.

Non-return-expected observations are intentionally a different contract: #106
already confirms those without a physical return and this must remain allowed.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import pytest

import concord.menu_artifact as artifact_menu
import concord.workflows.artifact_attribution as attribution
import concord.workflows.artifact_attribution_review as attribution_review
from concord.menu_context import MenuSessionContext
from concord.workflows import (
    BatchConfirmArtifactAttributionRequest,
    ConcordWorkflowConflictError,
    ConcordWorkflowValidationError,
    WorkflowActor,
)
from concord.workflows.models import ActivitySummary


@dataclass(frozen=True)
class _ProposedAuthor:
    artifact_author_id: str = "author-151-synthetic"
    artifact_instance_id: str = "artifact-151-synthetic"
    attribution_status: str = "proposed"
    supersedes_artifact_author_id: str | None = None
    authorship_mode: str = "individual_author"
    represented_group_id: str | None = None
    role_assignment_id: str | None = None
    representation_status: str | None = None


def _synthetic_graph(*, return_expected: bool) -> SimpleNamespace:
    return SimpleNamespace(
        artifact_instances=(
            SimpleNamespace(
                artifact_instance_id="artifact-151-synthetic",
                activity_id="activity-151-synthetic",
                template_version_id="template-151-synthetic",
                artifact_category="observation",
                group_id=None,
                session_id="session-151-synthetic",
                artifact_status="generated",
                generation_status="completed",
                expected_return_status=(
                    "returned_expected" if return_expected else "return_not_expected"
                ),
                page_ids=("page-151-synthetic",),
            ),
        ),
        artifact_pages=(
            SimpleNamespace(
                artifact_page_id="page-151-synthetic",
                artifact_instance_id="artifact-151-synthetic",
                route_id="route-151-synthetic" if return_expected else None,
                page_status="generated",
                return_expected=return_expected,
            ),
        ),
        scan_references=(),
        artifact_authors=(_ProposedAuthor(),),
        artifact_subjects=(),
    )


def _review_proposals(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    return_expected: bool,
) -> attribution_review.ArtifactAttributionReview:
    graph = _synthetic_graph(return_expected=return_expected)
    monkeypatch.setattr(
        attribution_review, "resolve_read_workspace_root", lambda _root: tmp_path
    )
    monkeypatch.setattr(attribution_review, "require_core_class", lambda *_a: None)
    monkeypatch.setattr(
        attribution_review,
        "load_activity_read_context",
        lambda *_a: SimpleNamespace(
            graph=graph, snapshot_revision=7, snapshot_sha256="a" * 64
        ),
    )
    # Isolate the missing independent return gate from student-name resolution
    # and the already-tested semantic/duplicate association validators.
    monkeypatch.setattr(
        attribution_review,
        "_author_display_label",
        lambda *_a: "Synthetic Student",
    )
    monkeypatch.setattr(
        attribution_review, "_validate_author_semantics", lambda *_a: None
    )
    monkeypatch.setattr(
        attribution_review, "_ensure_author_not_duplicate", lambda *_a, **_k: None
    )
    return attribution_review.inspect_artifact_attribution_review(
        "class-151-synthetic", "activity-151-synthetic", workspace_root=tmp_path
    )


def test_return_expected_artifact_without_routed_evidence_is_not_confirmable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    review = _review_proposals(monkeypatch, tmp_path, return_expected=True)
    assert review.candidate_author_ids == ()
    assert any(
        item.disposition == "exception"
        for group in review.artifacts
        for item in group.authors
    )


def test_non_return_expected_observation_keeps_existing_confirmation_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    review = _review_proposals(monkeypatch, tmp_path, return_expected=False)
    assert review.candidate_author_ids == ("author-151-synthetic",)


def test_writer_rejects_pre_return_author_confirmation_before_any_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    graph = _synthetic_graph(return_expected=True)
    commits: list[object] = []
    monkeypatch.setattr(
        attribution,
        "ensure_mutating_workspace_root",
        lambda _root: SimpleNamespace(root=tmp_path, created=False),
    )
    monkeypatch.setattr(attribution, "require_core_class", lambda *_a: None)
    monkeypatch.setattr(
        attribution, "load_graph", lambda *_a, **_k: (graph, 7, "a" * 64)
    )
    monkeypatch.setattr(attribution, "_validate_author_semantics", lambda *_a: None)
    monkeypatch.setattr(
        attribution, "_ensure_author_not_duplicate", lambda *_a, **_k: None
    )

    def forbid_commit(*args: object, **kwargs: object) -> None:
        commits.append((args, kwargs))
        raise AssertionError("Unreturned paper attribution reached the commit owner")

    monkeypatch.setattr(attribution, "commit_record_batch", forbid_commit)
    request = BatchConfirmArtifactAttributionRequest(
        class_id="class-151-synthetic",
        activity_id="activity-151-synthetic",
        expected_snapshot_revision=7,
        actor=WorkflowActor(
            actor_id="teacher-151-synthetic",
            display_label="Synthetic Teacher",
            role_label="teacher",
        ),
        artifact_author_ids=("author-151-synthetic",),
    )
    with pytest.raises((ConcordWorkflowConflictError, ConcordWorkflowValidationError)):
        attribution.batch_confirm_artifact_attribution(request, workspace_root=tmp_path)
    assert commits == []


def test_collect_offers_scan_routing_from_the_current_activity(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    activity = ActivitySummary(
        class_id="class-151-synthetic",
        activity_id="activity-151-synthetic",
        title="Synthetic Return-Expected Seminar",
        status="active",
        scoring_orientation="mixed",
        session_count=1,
        group_count=6,
        snapshot_revision=7,
    )
    monkeypatch.setattr(artifact_menu, "clear_screen", lambda: None)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "b")
    artifact_menu.launch_collect_work_menu(activity, MenuSessionContext())
    rendered = capsys.readouterr().out.casefold()
    assert "route" in rendered and "scan" in rendered
