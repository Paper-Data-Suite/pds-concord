"""#151 Slice 4: graph-backed return gates for attribution confirmations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import pytest

import concord.workflows.artifact_attribution as writer
import concord.workflows.artifact_attribution_review as review
from concord.workflows.artifact_attribution import (
    BatchConfirmArtifactAttributionRequest,
)
from concord.workflows.artifact_confirmation_gate import (
    require_confirmable_return,
    return_evidence_confirmable,
)
from concord.workflows.errors import ConcordWorkflowConflictError
from concord.workflows.models import WorkflowActor


@dataclass(frozen=True)
class Author:
    artifact_author_id: str = "author-s4"
    artifact_instance_id: str = "artifact-s4"
    attribution_status: str = "proposed"
    supersedes_artifact_author_id: str | None = None
    authorship_mode: str = "individual_author"
    represented_group_id: str | None = None
    role_assignment_id: str | None = None
    representation_status: str | None = None
    author_reference: None = None


@dataclass(frozen=True)
class Subject:
    artifact_subject_id: str = "subject-s4"
    artifact_instance_id: str = "artifact-s4"
    confirmation_status: str = "proposed"
    supersedes_artifact_subject_id: str | None = None
    subject_role: str = "general_subject"
    criterion_id: str | None = None
    subject_reference: object = None


def graph(
    *,
    expected: str = "returned_expected",
    required: tuple[bool, ...] = (True, True),
    routed: tuple[int, ...] = (),
    wrong_route: bool = False,
    wrong_activity: bool = False,
) -> SimpleNamespace:
    artifact = SimpleNamespace(
        artifact_instance_id="artifact-s4",
        activity_id="activity-s4",
        expected_return_status=expected,
        template_version_id="template-s4",
        artifact_category="student_work",
        group_id=None,
        session_id=None,
        page_ids=tuple(f"page-{index}" for index in range(len(required))),
    )
    pages = tuple(
        SimpleNamespace(
            artifact_page_id=f"page-{i}",
            artifact_instance_id="artifact-s4",
            route_id=f"route-{i}" if flag else None,
            return_expected=flag,
            page_status="returned" if i in routed else "generated",
        )
        for i, flag in enumerate(required)
    )
    scans = tuple(
        SimpleNamespace(
            scan_reference_id=f"scan-{j}-{i}",
            artifact_page_id=f"page-{i}",
            activity_id="wrong-activity" if wrong_activity else "activity-s4",
            route_id="wrong-route" if wrong_route else f"route-{i}",
        )
        for j, i in enumerate(routed)
    )
    return SimpleNamespace(
        artifact_instances=(artifact,),
        artifact_pages=pages,
        scan_references=scans,
        artifact_authors=(Author(),),
        artifact_subjects=(
            Subject(
                subject_reference=SimpleNamespace(
                    subject_kind="external_record", owning_system="other"
                ),
            ),
        ),
    )


@pytest.mark.parametrize(
    ("routed", "allowed"),
    (((), False), ((0,), False), ((1,), False), ((0, 1), True), ((0, 0, 1), True)),
)
def test_all_required_paper_pages_must_be_routed(
    routed: tuple[int, ...], allowed: bool
) -> None:
    data = graph(routed=routed)
    assert return_evidence_confirmable(data.artifact_instances[0], data) is allowed


def test_nonreturn_observation_is_independently_confirmable() -> None:
    data = graph(expected="return_not_expected", required=(False,))
    require_confirmable_return(data.artifact_instances[0], data)


def test_optional_return_without_routed_pages_is_not_false_paper_evidence() -> None:
    data = graph(expected="returned_optional", required=(False,))
    assert not return_evidence_confirmable(data.artifact_instances[0], data)


@pytest.mark.parametrize("wrong_field", ("wrong_route", "wrong_activity"))
def test_wrong_route_or_activity_fails_closed(wrong_field: str) -> None:
    data = graph(routed=(0, 1), **{wrong_field: True})
    with pytest.raises(ConcordWorkflowConflictError):
        require_confirmable_return(data.artifact_instances[0], data)


def test_missing_canonical_page_fails_closed() -> None:
    data = graph(routed=(0, 1))
    data.artifact_pages = data.artifact_pages[:1]
    with pytest.raises(ConcordWorkflowConflictError):
        require_confirmable_return(data.artifact_instances[0], data)


@pytest.mark.parametrize("status", ("proposed", "disputed", "unknown"))
def test_pre_return_author_proposals_and_disputes_still_validate(
    status: str,
) -> None:
    data = graph()
    candidate = Author(attribution_status=status)
    writer._validate_author_semantics(
        Path("synthetic"), "class-s4", data, data.artifact_instances[0], candidate
    )


@pytest.mark.parametrize("target", ("author", "subject"))
def test_confirmed_advanced_validator_blocks_missing_returns(target: str) -> None:
    data = graph()
    artifact = data.artifact_instances[0]
    if target == "author":
        candidate = Author(attribution_status="confirmed")
        with pytest.raises(ConcordWorkflowConflictError):
            writer._validate_author_semantics(
                Path("synthetic"), "class-s4", data, artifact, candidate
            )
    else:
        candidate = Subject(
            confirmation_status="confirmed",
            subject_reference=SimpleNamespace(
                subject_kind="external_record", owning_system="other"
            ),
        )
        with pytest.raises(ConcordWorkflowConflictError):
            writer._validate_subject_semantics(
                Path("synthetic"), "class-s4", data, artifact, candidate
            )


@pytest.mark.parametrize("kind", ("author", "subject"))
def test_review_never_offers_unreturned_confirmation_candidate(
    kind: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = graph()
    monkeypatch.setattr(review, "_author_display_label", lambda *_a: "Student")
    monkeypatch.setattr(review, "_subject_display_label", lambda *_a: "Subject")
    if kind == "author":
        item = review._author_review_item(
            Path("synthetic"),
            "class-s4",
            "activity-s4",
            data,
            data.artifact_authors[0],
        )
    else:
        item = review._subject_review_item(
            Path("synthetic"),
            "class-s4",
            "activity-s4",
            data,
            data.artifact_subjects[0],
        )
    assert item.disposition == "exception"
    assert item.exception_code == "return_evidence_pending"


def test_routed_review_can_offer_both_independent_relations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = graph(routed=(0, 1))
    monkeypatch.setattr(review, "_author_display_label", lambda *_a: "Student")
    monkeypatch.setattr(review, "_subject_display_label", lambda *_a: "Subject")
    monkeypatch.setattr(review, "_validate_author_semantics", lambda *_a: None)
    monkeypatch.setattr(review, "_validate_subject_semantics", lambda *_a: None)
    monkeypatch.setattr(review, "_ensure_author_not_duplicate", lambda *_a, **_k: None)
    monkeypatch.setattr(review, "_ensure_subject_not_duplicate", lambda *_a, **_k: None)
    a = review._author_review_item(
        Path("synthetic"), "class-s4", "activity-s4", data, data.artifact_authors[0]
    )
    b = review._subject_review_item(
        Path("synthetic"), "class-s4", "activity-s4", data, data.artifact_subjects[0]
    )
    assert a.disposition == b.disposition == "candidate"


def test_batch_blocks_mixed_selection_atomically_before_commit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # First Artifact has routed returns, second does not. All-or-nothing.
    data = graph(routed=(0, 1))
    unreturned = graph().artifact_instances[0]
    unreturned.artifact_instance_id = "unreturned-s4"
    other_author = Author(
        artifact_author_id="author-unreturned", artifact_instance_id="unreturned-s4"
    )
    data.artifact_instances = (*data.artifact_instances, unreturned)
    data.artifact_authors = (*data.artifact_authors, other_author)
    # Change the second Artifact's pages so its return is absent while first
    # Artifact's pages still belong only to its own identity.
    data.artifact_pages = (
        *data.artifact_pages,
        SimpleNamespace(
            artifact_page_id="pending-page",
            artifact_instance_id="unreturned-s4",
            route_id="pending-route",
            return_expected=True,
        ),
    )
    unreturned.page_ids = ("pending-page",)
    monkeypatch.setattr(
        writer,
        "ensure_mutating_workspace_root",
        lambda _p: SimpleNamespace(root=tmp_path, created=False),
    )
    monkeypatch.setattr(writer, "require_core_class", lambda *_a: None)
    monkeypatch.setattr(writer, "load_graph", lambda *_a, **_k: (data, 7, "a" * 64))
    monkeypatch.setattr(writer, "_validate_author_semantics", lambda *_a: None)
    monkeypatch.setattr(writer, "_ensure_author_not_duplicate", lambda *_a, **_k: None)
    commits: list[object] = []
    monkeypatch.setattr(
        writer, "commit_record_batch", lambda *_a, **_k: commits.append(1)
    )
    request = BatchConfirmArtifactAttributionRequest(
        class_id="class-s4",
        activity_id="activity-s4",
        expected_snapshot_revision=7,
        actor=WorkflowActor(
            actor_id="actor-s4", display_label="Teacher", role_label="teacher"
        ),
        artifact_author_ids=("author-s4", "author-unreturned"),
    )
    with pytest.raises(ConcordWorkflowConflictError):
        writer.batch_confirm_artifact_attribution(request, workspace_root=tmp_path)
    assert commits == []
