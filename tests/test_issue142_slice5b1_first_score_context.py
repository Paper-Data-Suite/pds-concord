"""#142 Slice 5B1: routine Score first-write authority with disposable fixtures.

A prepared, unreturned synthetic Artifact is always ineligible to Score.
Positive context-forwarding cases use a service spy, not a real Score commit.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from issue140_slice2_fixtures import ACTOR, build_workspace
from pds_core.routing_models import ModuleWorkRef
from test_issue142_slice4a_first_review_moderation import (
    ARTIFACT_ID,
    _activity,
    _fixture,
    _work,
)

import concord.menu_artifact_scoring as scoring
import concord.menu_artifact_write_context as authority
from concord.storage import list_work_snapshots
from concord.workflows.artifact_routine_scoring import (
    ArtifactRoutineScoringEligibility,
)


def _prepare(root: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    monkeypatch.setattr(scoring, "_current_activity", lambda _: _activity(root))
    monkeypatch.setattr(scoring, "show_result", lambda *a, **kw: None)
    return _activity(root)


def _spy_ready(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    original = scoring.inspect_artifact_routine_scoring

    def inspect(*args: Any, **kwargs: Any) -> Any:
        assert kwargs.get("workspace_root") == root
        context = original(*args, **kwargs)
        assert not context.eligibility.routine_scoring_eligible
        return replace(
            context,
            eligibility=ArtifactRoutineScoringEligibility(
                routine_scoring_eligible=True,
                exception_reasons=(),
            ),
        )

    monkeypatch.setattr(scoring, "inspect_artifact_routine_scoring", inspect)


def _spy_selection(
    monkeypatch: pytest.MonkeyPatch,
    *,
    existing: tuple[str, ...] = (),
    mismatch: bool = False,
) -> None:
    target = object()
    monkeypatch.setattr(scoring, "_choose_target", lambda *a: target)
    monkeypatch.setattr(
        scoring,
        "_choose_criterion",
        lambda *a: SimpleNamespace(criterion_id="synthetic-score-criterion"),
    )
    monkeypatch.setattr(
        scoring,
        "_choose_scale",
        lambda *a: SimpleNamespace(scoring_scale_id="synthetic-score-scale"),
    )
    monkeypatch.setattr(
        scoring, "_choose_level", lambda *a: SimpleNamespace(value=4)
    )
    monkeypatch.setattr(scoring, "_choose_session", lambda *a: None)
    monkeypatch.setattr(scoring, "_choose_subject_context", lambda *a: ())
    monkeypatch.setattr(scoring, "_choose_relevance", lambda: "Synthetic evidence")

    def preview(context: Any, request: Any) -> Any:
        assert request.value == 4
        return SimpleNamespace(
            existing_current_score_ids=existing,
            artifact_instance_id=(
                "wrong-artifact" if mismatch else context.artifact.artifact_instance_id
            ),
            snapshot_revision=context.snapshot_revision,
            snapshot_sha256=context.snapshot_sha256,
        )

    monkeypatch.setattr(scoring, "prepare_routine_score_preview", preview)
    monkeypatch.setattr(
        scoring, "_preview_lines", lambda *a: ("Synthetic call boundary only",)
    )


@pytest.mark.parametrize(
    "orientation", ("mixed", "standards_based", "evidence_only", "local_criteria_only")
)
def test_unreturned_artifact_cannot_enter_routine_scoring(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, orientation: str
) -> None:
    root = _fixture(tmp_path, monkeypatch, orientation)
    current = _prepare(root, monkeypatch)
    before = list_work_snapshots(root, _work())
    monkeypatch.setattr(
        scoring,
        "confirm_write",
        lambda *a, **kw: pytest.fail("Unreturned work reached Score confirmation"),
    )
    monkeypatch.setattr(
        scoring,
        "record_prepared_routine_score",
        lambda *a, **kw: pytest.fail("Unreturned work created a Score"),
    )
    assert scoring._record_selected_artifact_score(
        current, ARTIFACT_ID, scoring.MenuSessionContext(actor=ACTOR)
    ) is None
    assert list_work_snapshots(root, _work()) == before


@pytest.mark.parametrize(
    "orientation", ("mixed", "standards_based", "evidence_only", "local_criteria_only")
)
def test_spy_only_score_boundary_forwards_exact_canonical_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, orientation: str
) -> None:
    root = _fixture(tmp_path, monkeypatch, orientation)
    current = _prepare(root, monkeypatch)
    _spy_ready(root, monkeypatch)
    _spy_selection(monkeypatch)
    monkeypatch.setattr(scoring, "confirm_write", lambda *a, **kw: True)
    captured: list[tuple[Any, dict[str, Any]]] = []

    def spy(preview: Any, **kwargs: Any) -> Any:
        captured.append((preview, kwargs))
        return SimpleNamespace(commit=SimpleNamespace(snapshot_revision=7))

    monkeypatch.setattr(scoring, "record_prepared_routine_score", spy)
    before = list_work_snapshots(root, _work())
    outcome = scoring._record_selected_artifact_score(
        current, ARTIFACT_ID, scoring.MenuSessionContext(actor=ACTOR)
    )
    assert outcome is not None
    assert len(captured) == 1
    preview, kwargs = captured[0]
    assert preview.snapshot_revision == current.snapshot_revision
    assert kwargs["actor"] == ACTOR
    assert kwargs["workspace_root"] == root
    assert ("standards_library" in kwargs) == (
        orientation in {"mixed", "standards_based"}
    )
    assert list_work_snapshots(root, _work()) == before


def test_cancelled_score_is_exact_no_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _fixture(tmp_path, monkeypatch, "mixed")
    current = _prepare(root, monkeypatch)
    _spy_ready(root, monkeypatch)
    _spy_selection(monkeypatch)
    monkeypatch.setattr(scoring, "confirm_write", lambda *a, **kw: False)
    monkeypatch.setattr(
        scoring,
        "record_prepared_routine_score",
        lambda *a, **kw: pytest.fail("Cancelled Score would be written"),
    )
    before = list_work_snapshots(root, _work())
    assert scoring._record_selected_artifact_score(
        current, ARTIFACT_ID, scoring.MenuSessionContext(actor=ACTOR)
    ) is None
    assert list_work_snapshots(root, _work()) == before


def test_existing_current_score_refuses_duplicate_first_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _fixture(tmp_path, monkeypatch, "mixed")
    current = _prepare(root, monkeypatch)
    _spy_ready(root, monkeypatch)
    _spy_selection(monkeypatch, existing=("synthetic-current-score",))
    monkeypatch.setattr(
        scoring,
        "record_prepared_routine_score",
        lambda *a, **kw: pytest.fail("Parallel Score would be recorded"),
    )
    before = list_work_snapshots(root, _work())
    assert scoring._record_selected_artifact_score(
        current, ARTIFACT_ID, scoring.MenuSessionContext(actor=ACTOR)
    ) is None
    assert list_work_snapshots(root, _work()) == before


def test_mismatched_preview_artifact_never_reaches_score_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _fixture(tmp_path, monkeypatch, "mixed")
    current = _prepare(root, monkeypatch)
    _spy_ready(root, monkeypatch)
    _spy_selection(monkeypatch, mismatch=True)
    monkeypatch.setattr(scoring, "confirm_write", lambda *a, **kw: True)
    monkeypatch.setattr(
        scoring,
        "record_prepared_routine_score",
        lambda *a, **kw: pytest.fail("Wrong Artifact would be scored"),
    )
    before = list_work_snapshots(root, _work())
    with pytest.raises(Exception, match="Score preview does not match"):
        scoring._record_selected_artifact_score(
            current, ARTIFACT_ID, scoring.MenuSessionContext(actor=ACTOR)
        )
    assert list_work_snapshots(root, _work()) == before


def test_workspace_drift_after_confirmation_refuses_score_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _fixture(tmp_path, monkeypatch, "mixed")
    current = _prepare(root, monkeypatch)
    _spy_ready(root, monkeypatch)
    _spy_selection(monkeypatch)
    foreign = build_workspace(tmp_path / "foreign", orientation="mixed")
    before = list_work_snapshots(root, _work())
    foreign_before = list_work_snapshots(
        foreign.root, ModuleWorkRef("concord", current.class_id, current.activity_id)
    )

    def switch(*a: Any, **kw: Any) -> bool:
        monkeypatch.setattr(
            authority,
            "resolve_read_workspace_root",
            lambda explicit=None: (
                foreign.root if explicit is None else Path(explicit)
            ),
        )
        return True

    monkeypatch.setattr(scoring, "confirm_write", switch)
    monkeypatch.setattr(
        scoring,
        "record_prepared_routine_score",
        lambda *a, **kw: pytest.fail("Workspace drift reached Score storage"),
    )
    with pytest.raises(Exception, match="workspace has changed"):
        scoring._record_selected_artifact_score(
            current, ARTIFACT_ID, scoring.MenuSessionContext(actor=ACTOR)
        )
    assert list_work_snapshots(root, _work()) == before
    assert list_work_snapshots(foreign.root, _work()) == foreign_before


def test_stale_eligibility_snapshot_blocks_before_teacher_selection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _fixture(tmp_path, monkeypatch, "mixed")
    current = _prepare(root, monkeypatch)
    original = scoring.inspect_artifact_routine_scoring

    def altered(*a: Any, **kw: Any) -> Any:
        context = original(*a, **kw)
        return replace(context, snapshot_revision=context.snapshot_revision + 1)

    monkeypatch.setattr(scoring, "inspect_artifact_routine_scoring", altered)
    monkeypatch.setattr(
        scoring,
        "_choose_target",
        lambda *a: pytest.fail("Stale inspection reached Score selection"),
    )
    before = list_work_snapshots(root, _work())
    with pytest.raises(Exception, match="Score context changed"):
        scoring._record_selected_artifact_score(
            current, ARTIFACT_ID, scoring.MenuSessionContext(actor=ACTOR)
        )
    assert list_work_snapshots(root, _work()) == before
