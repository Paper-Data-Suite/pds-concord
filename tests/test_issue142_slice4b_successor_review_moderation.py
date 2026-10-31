"""#142 Slice 4B: real Review/Moderation successors and immutable corrections.

Only fabricated Core rosters and non-return-expected observations in pytest tmp_path.
No scanned evidence, teacher judgment about student work, or Score is synthesized.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from issue140_slice2_fixtures import ACTOR, build_workspace
from pds_core.standards import load_workspace_standards_library
from test_issue142_slice4a_first_review_moderation import (
    _activity,
    _fixture,
    _graph,
    _invoke,
    _work,
)

import concord.menu_artifact as menu
import concord.menu_artifact_write_context as authority
from concord.storage import list_work_snapshots
from concord.workflows import UpdateActivityRequest, update_activity

REPLACEMENT_REVIEW = "issue142-synthetic-administrative-review-successor"
REPLACEMENT_MODERATION = "issue142-synthetic-moderation-successor"
CORRECTION_ID = "issue142-synthetic-successor-correction"


def _successor(kind: str, root: Path) -> None:
    handler = (
        menu._replace_review if kind == "review" else menu._replace_moderation
    )
    handler(_activity(root), menu.MenuSessionContext(actor=ACTOR))


def _prepare_successor(
    kind: str, root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _invoke(kind, root)
    answers = {
        "Replacement Review ID": REPLACEMENT_REVIEW,
        "Replacement Moderation ID": REPLACEMENT_MODERATION,
        "Correction ID": CORRECTION_ID,
        "Reason": "Synthetic correction record for administrative observation",
    }
    monkeypatch.setattr(
        menu,
        "prompt_text",
        lambda title, label, **kw: answers.get(
            label, "Synthetic administrative correction"
        ),
    )


@pytest.mark.parametrize("kind", ("review", "moderation"))
@pytest.mark.parametrize(
    "orientation",
    ("mixed", "standards_based", "evidence_only", "local_criteria_only"),
)
def test_successor_persists_immutable_predecessor_and_explicit_correction(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
    orientation: str,
) -> None:
    root = _fixture(tmp_path, monkeypatch, orientation)
    _prepare_successor(kind, root, monkeypatch)
    before = list_work_snapshots(root, _work())
    _successor(kind, root)
    assert len(list_work_snapshots(root, _work())) == len(before) + 1
    graph = _graph(root, orientation)
    assert graph.scan_references == ()
    assert graph.score_records == ()
    assert graph.score_evidence_links == ()
    assert graph.artifact_instances[0].expected_return_status == "return_not_expected"
    assert len(graph.correction_records) == 1
    correction = graph.correction_records[0]
    assert correction.correction_id == CORRECTION_ID
    assert correction.reason == (
        "Synthetic correction record for administrative observation"
    )
    if kind == "review":
        assert len(graph.artifact_reviews) == 2
        successor = next(
            item for item in graph.artifact_reviews
            if item.supersedes_artifact_review_id is not None
        )
        original = next(
            item for item in graph.artifact_reviews
            if item.artifact_review_id == successor.supersedes_artifact_review_id
        )
        assert successor.artifact_review_id == REPLACEMENT_REVIEW
        assert successor.supersedes_artifact_review_id == original.artifact_review_id
        assert original.scoring_readiness == successor.scoring_readiness == "not_ready"
        assert successor.review_outcome == "awaiting_additional_evidence"
        assert correction.correction_type == "review_correction"
        assert correction.target_reference.record_id == original.artifact_review_id
        assert correction.replacement_reference is not None
        assert correction.replacement_reference.record_id == (
            successor.artifact_review_id
        )
        assert graph.moderation_records == ()
    else:
        assert len(graph.moderation_records) == 2
        successor = next(
            item for item in graph.moderation_records
            if item.supersedes_moderation_record_id is not None
        )
        original = next(
            item for item in graph.moderation_records
            if item.moderation_record_id == successor.supersedes_moderation_record_id
        )
        assert successor.moderation_record_id == REPLACEMENT_MODERATION
        assert successor.supersedes_moderation_record_id == (
            original.moderation_record_id
        )
        assert successor.target_evidence_reference == original.target_evidence_reference
        assert successor.target_subject_references == original.target_subject_references
        assert successor.status == "not_used_for_scoring"
        assert successor.permitted_use == "not_be_used_for_scoring"
        assert correction.correction_type == "moderation_revision"
        assert correction.target_reference.record_id == original.moderation_record_id
        assert correction.replacement_reference is not None
        assert correction.replacement_reference.record_id == (
            successor.moderation_record_id
        )
        assert graph.artifact_reviews == ()


@pytest.mark.parametrize("kind", ("review", "moderation"))
def test_cancel_does_not_record_successor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    root = _fixture(tmp_path, monkeypatch, "mixed")
    _prepare_successor(kind, root, monkeypatch)
    before = list_work_snapshots(root, _work())
    monkeypatch.setattr(menu, "confirm_write", lambda *a, **kw: False)
    _successor(kind, root)
    assert list_work_snapshots(root, _work()) == before
    assert _graph(root, "mixed").correction_records == ()


@pytest.mark.parametrize("kind", ("review", "moderation"))
def test_stale_predecessor_selection_refuses_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    root = _fixture(tmp_path, monkeypatch, "mixed")
    _prepare_successor(kind, root, monkeypatch)
    before = list_work_snapshots(root, _work())
    label = "list_artifact_reviews" if kind == "review" else "list_moderation_records"
    real = getattr(menu, label)

    def stale(*args: Any, **kwargs: Any) -> Any:
        return tuple(
            replace(item, snapshot_revision=item.snapshot_revision + 1)
            for item in real(*args, **kwargs)
        )

    monkeypatch.setattr(menu, label, stale)
    with pytest.raises(Exception, match="Selected .* changed"):
        _successor(kind, root)
    assert list_work_snapshots(root, _work()) == before


@pytest.mark.parametrize("kind", ("review", "moderation"))
def test_workspace_switch_after_confirmation_rejects_both_workspaces(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    root = _fixture(tmp_path, monkeypatch, "mixed")
    _prepare_successor(kind, root, monkeypatch)
    foreign = build_workspace(tmp_path / "foreign", orientation="mixed")
    original_before = list_work_snapshots(root, _work())
    foreign_before = list_work_snapshots(foreign.root, _work())

    def switch(*args: Any, **kwargs: Any) -> bool:
        monkeypatch.setattr(
            authority,
            "resolve_read_workspace_root",
            lambda explicit=None: (
                foreign.root if explicit is None else Path(explicit)
            ),
        )
        return True

    monkeypatch.setattr(menu, "confirm_write", switch)
    with pytest.raises(Exception, match="workspace has changed"):
        _successor(kind, root)
    assert list_work_snapshots(root, _work()) == original_before
    assert list_work_snapshots(foreign.root, _work()) == foreign_before
    assert _graph(root, "mixed").correction_records == ()


@pytest.mark.parametrize("kind", ("review", "moderation"))
def test_concurrent_snapshot_change_refuses_successor_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    root = _fixture(tmp_path, monkeypatch, "mixed")
    _prepare_successor(kind, root, monkeypatch)
    before = list_work_snapshots(root, _work())

    def interleave(*args: Any, **kwargs: Any) -> bool:
        current = _activity(root)
        update_activity(
            UpdateActivityRequest(
                class_id=current.class_id,
                activity_id=current.activity_id,
                expected_snapshot_revision=current.snapshot_revision,
                actor=ACTOR,
                status="configured",
            ),
            workspace_root=root,
            standards_library=load_workspace_standards_library(root),
        )
        return True

    monkeypatch.setattr(menu, "confirm_write", interleave)
    with pytest.raises(Exception, match="snapshot changed after preview"):
        _successor(kind, root)
    assert len(list_work_snapshots(root, _work())) == len(before) + 1
    assert _graph(root, "mixed").correction_records == ()


@pytest.mark.parametrize("kind", ("review", "moderation"))
def test_historical_predecessor_cannot_be_revised_again(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    root = _fixture(tmp_path, monkeypatch, "mixed")
    _prepare_successor(kind, root, monkeypatch)
    _successor(kind, root)
    before = list_work_snapshots(root, _work())
    label = "list_artifact_reviews" if kind == "review" else "list_moderation_records"
    real = getattr(menu, label)

    def historical(*args: Any, **kwargs: Any) -> Any:
        return tuple(
            item for item in real(*args, **dict(kwargs, include_historical=True))
            if not item.is_current
        )

    monkeypatch.setattr(menu, label, historical)
    # Distinct successor/correction IDs ensure this checks the current-head guard.
    monkeypatch.setattr(
        menu,
        "prompt_text",
        lambda title, label, **kw: {
            "Replacement Review ID": REPLACEMENT_REVIEW + "-2",
            "Replacement Moderation ID": REPLACEMENT_MODERATION + "-2",
            "Correction ID": CORRECTION_ID + "-2",
            "Reason": "Synthetic historical-head rejection",
        }.get(label, "Synthetic second administrative correction"),
    )
    with pytest.raises(Exception, match="Historical .* cannot be replaced"):
        _successor(kind, root)
    assert list_work_snapshots(root, _work()) == before
    assert len(_graph(root, "mixed").correction_records) == 1
