"""#142 Slice 5B2: Score continuation remains pinned across a new snapshot.

All Core/Concord records are synthetic under pytest tmp_path. A separate,
non-scoring administrative Review can advance the test snapshot; positive
Score mutation coverage is a service spy, never fabricated returned work.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from issue140_slice2_fixtures import ACTOR, build_workspace
from pds_core.standards import write_workspace_standards_library
from test_issue142_slice4a_first_review_moderation import (
    ARTIFACT_ID,
    _activity,
    _fixture,
    _work,
)

import concord.menu_artifact as artifact_menu
import concord.menu_artifact_scoring as scoring
import concord.menu_artifact_write_context as authority
from concord.storage import list_work_snapshots
from concord.workflows.artifact_routine_scoring import (
    ArtifactRoutineScoringEligibility,
    inspect_artifact_routine_scoring,
)


def _advance_administrative_snapshot(root: Path) -> None:
    """Genuine non-scoring synthetic write, never presented as a Score."""
    artifact_menu._record_review(
        _activity(root), artifact_menu.MenuSessionContext(actor=ACTOR)
    )


def _original_context(root: Path) -> authority.ArtifactWriteContext:
    return authority.begin_artifact_write_context(
        _activity(root), operation="Synthetic Score continuation anchor"
    )


def _post_review_context(root: Path) -> Any:
    context = inspect_artifact_routine_scoring(
        _activity(root).class_id,
        _activity(root).activity_id,
        ARTIFACT_ID,
        workspace_root=root,
    )
    assert not context.eligibility.routine_scoring_eligible
    return replace(
        context,
        eligibility=ArtifactRoutineScoringEligibility(
            routine_scoring_eligible=True,
            exception_reasons=(),
        ),
    )


def _continuation(context: Any, *, duplicate: bool = False) -> Any:
    return SimpleNamespace(
        context=context,
        retained_target_reference=object(),
        session_context_retained=True,
        dropped_context_reasons=(),
        available_criteria=(
            SimpleNamespace(
                criterion_id="synthetic-other-criterion",
                criterion_kind="rubric",
                label="Synthetic Other Criterion",
            ),
        ),
        completed_criterion_id="synthetic-earlier-criterion",
    )


def _select_next_preview(
    monkeypatch: pytest.MonkeyPatch,
    *,
    current: Any,
    duplicates: tuple[str, ...] = (),
    stale: bool = False,
) -> None:
    monkeypatch.setattr(
        scoring, "select_one", lambda title, items, labels, **kw: items[0]
    )
    monkeypatch.setattr(
        scoring, "_choose_scale", lambda *a: SimpleNamespace(scoring_scale_id="scale")
    )
    monkeypatch.setattr(scoring, "_choose_level", lambda *a: SimpleNamespace(value=3))
    monkeypatch.setattr(scoring, "_choose_subject_context", lambda *a: ())
    monkeypatch.setattr(scoring, "_choose_relevance", lambda: "Synthetic observation")
    monkeypatch.setattr(scoring, "_preview_lines", lambda *a: ("Synthetic spy",))

    def make_preview(continuation: Any, request: Any) -> Any:
        assert request.criterion_id == "synthetic-other-criterion"
        return SimpleNamespace(
            snapshot_revision=current.snapshot_revision + (1 if stale else 0),
            snapshot_sha256=current.snapshot_sha256,
            artifact_instance_id=ARTIFACT_ID,
            existing_current_score_ids=duplicates,
        )

    monkeypatch.setattr(scoring, "prepare_next_routine_score_preview", make_preview)
    monkeypatch.setattr(scoring, "show_result", lambda *a, **kw: None)


@pytest.mark.parametrize("orientation", ("mixed", "evidence_only"))
def test_post_score_authority_rebases_on_new_snapshot_without_reusing_old_revision(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, orientation: str
) -> None:
    root = _fixture(tmp_path, monkeypatch, orientation)
    old = _original_context(root)
    _advance_administrative_snapshot(root)
    fresh = scoring._refresh_score_continuation_authority(
        old, operation="Synthetic post-Score refresh"
    )
    assert fresh.root == old.root
    assert fresh.snapshot_revision == old.snapshot_revision + 1
    assert fresh.snapshot_sha256 != old.snapshot_sha256
    assert fresh.active_workspace_binding == old.active_workspace_binding
    assert (fresh.standards_library is not None) == (orientation == "mixed")


def test_post_score_authority_refuses_changed_active_workspace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _fixture(tmp_path, monkeypatch, "mixed")
    old = _original_context(root)
    _advance_administrative_snapshot(root)
    foreign = build_workspace(tmp_path / "foreign", orientation="mixed")
    write_workspace_standards_library(foreign.root, foreign.standards)
    original_snapshots = list_work_snapshots(root, _work())
    foreign_snapshots = list_work_snapshots(foreign.root, _work())
    monkeypatch.setattr(
        authority,
        "resolve_read_workspace_root",
        lambda explicit=None: foreign.root if explicit is None else Path(explicit),
    )
    with pytest.raises(Exception, match="workspace changed"):
        scoring._refresh_score_continuation_authority(
            old, operation="Synthetic post-Score refresh"
        )
    assert list_work_snapshots(root, _work()) == original_snapshots
    assert list_work_snapshots(foreign.root, _work()) == foreign_snapshots


def test_post_score_authority_rejects_stale_continuation_projection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _fixture(tmp_path, monkeypatch, "mixed")
    old = _original_context(root)
    _advance_administrative_snapshot(root)
    fresh = _activity(root)
    with pytest.raises(Exception, match="continuation snapshot changed"):
        scoring._refresh_score_continuation_authority(
            old,
            operation="Synthetic stale continuation",
            snapshot_revision=fresh.snapshot_revision - 1,
        )


@pytest.mark.parametrize(
    "orientation", ("mixed", "standards_based", "evidence_only", "local_criteria_only")
)
def test_next_criterion_spy_receives_new_snapshot_and_canonical_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, orientation: str
) -> None:
    root = _fixture(tmp_path, monkeypatch, orientation)
    previous = _original_context(root)
    _advance_administrative_snapshot(root)
    context = _post_review_context(root)
    _select_next_preview(monkeypatch, current=context)
    monkeypatch.setattr(scoring, "confirm_write", lambda *a, **kw: True)
    captured: list[tuple[Any, dict[str, Any]]] = []

    def spy(preview: Any, **kwargs: Any) -> Any:
        captured.append((preview, kwargs))
        return SimpleNamespace(commit=SimpleNamespace(snapshot_revision=17))

    monkeypatch.setattr(scoring, "record_prepared_routine_score", spy)
    before = list_work_snapshots(root, _work())
    outcome = scoring._record_another_criterion(
        _activity(root),
        _continuation(context),
        scoring.MenuSessionContext(actor=ACTOR),
        origin_context=previous,
    )
    assert outcome is not None
    assert outcome.write_context is not None
    assert outcome.write_context.root == root
    assert outcome.write_context.snapshot_revision == context.snapshot_revision
    assert len(captured) == 1
    preview, kwargs = captured[0]
    assert preview.snapshot_revision == context.snapshot_revision
    assert kwargs["actor"] == ACTOR
    assert kwargs["workspace_root"] == root
    assert ("standards_library" in kwargs) == (
        orientation in {"mixed", "standards_based"}
    )
    assert list_work_snapshots(root, _work()) == before


def test_another_criterion_cancel_does_not_call_score_service(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _fixture(tmp_path, monkeypatch, "mixed")
    previous = _original_context(root)
    _advance_administrative_snapshot(root)
    context = _post_review_context(root)
    _select_next_preview(monkeypatch, current=context)
    monkeypatch.setattr(scoring, "confirm_write", lambda *a, **kw: False)
    monkeypatch.setattr(
        scoring,
        "record_prepared_routine_score",
        lambda *a, **kw: pytest.fail("Cancelled continuation wrote a Score"),
    )
    before = list_work_snapshots(root, _work())
    assert scoring._record_another_criterion(
        _activity(root), _continuation(context),
        scoring.MenuSessionContext(actor=ACTOR), origin_context=previous
    ) is None
    assert list_work_snapshots(root, _work()) == before


def test_another_criterion_duplicate_and_stale_previews_refuse_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _fixture(tmp_path, monkeypatch, "mixed")
    previous = _original_context(root)
    _advance_administrative_snapshot(root)
    context = _post_review_context(root)
    monkeypatch.setattr(scoring, "confirm_write", lambda *a, **kw: True)
    monkeypatch.setattr(
        scoring,
        "record_prepared_routine_score",
        lambda *a, **kw: pytest.fail("Invalid continuation wrote a Score"),
    )
    before = list_work_snapshots(root, _work())
    _select_next_preview(monkeypatch, current=context, duplicates=("current-score",))
    assert scoring._record_another_criterion(
        _activity(root), _continuation(context),
        scoring.MenuSessionContext(actor=ACTOR), origin_context=previous
    ) is None
    _select_next_preview(monkeypatch, current=context, stale=True)
    with pytest.raises(Exception, match="Another-Criterion preview"):
        scoring._record_another_criterion(
            _activity(root), _continuation(context),
            scoring.MenuSessionContext(actor=ACTOR), origin_context=previous
        )
    assert list_work_snapshots(root, _work()) == before


def test_another_criterion_without_original_authority_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _fixture(tmp_path, monkeypatch, "evidence_only")
    context = _post_review_context(root)
    with pytest.raises(Exception, match="no pinned workspace"):
        scoring._record_another_criterion(
            _activity(root), _continuation(context),
            scoring.MenuSessionContext(actor=ACTOR),
        )


def test_next_score_ready_work_uses_origin_root_and_latest_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _fixture(tmp_path, monkeypatch, "mixed")
    previous = _original_context(root)
    _advance_administrative_snapshot(root)
    current = _post_review_context(root)
    snapshots_before = list_work_snapshots(root, _work())
    seen: list[dict[str, Any]] = []
    monkeypatch.setattr(scoring, "clear_screen", lambda: None)
    monkeypatch.setattr(scoring, "print_menu_header", lambda *a: None)
    monkeypatch.setattr(scoring, "show_result", lambda *a, **kw: None)
    monkeypatch.setattr(scoring, "input", lambda *a: "n", raising=False)
    monkeypatch.setattr(scoring, "parse_menu_navigation", lambda raw: None)

    def inspect(*args: Any, **kwargs: Any) -> Any:
        seen.append(kwargs)
        return SimpleNamespace(artifact=SimpleNamespace(artifact_instance_id="other"))

    monkeypatch.setattr(scoring, "inspect_next_score_ready_artifact", inspect)
    scored = scoring._RoutineScoreMenuResult(
        preview=SimpleNamespace(),
        mutation=SimpleNamespace(
            commit=SimpleNamespace(snapshot_revision=current.snapshot_revision)
        ),
        write_context=previous,
    )
    action, payload = scoring._post_score_action(
        _activity(root), ARTIFACT_ID,
        _continuation(current), scored,
        scoring.MenuSessionContext(actor=ACTOR),
    )
    assert action == "next"
    assert payload == "other"
    assert len(seen) == 1
    assert seen[0]["workspace_root"] == root
    assert seen[0]["minimum_snapshot_revision"] == current.snapshot_revision
    assert list_work_snapshots(root, _work()) == snapshots_before
