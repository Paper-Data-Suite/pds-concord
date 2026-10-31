"""#142 Slice 5A: Quick Review's pinned authority and no-Score separation.

Only disposable synthetic Core/Concord workspaces are used. The observed
Artifact has not been returned or assembled; no test claims a real ready Review
or records a Score. A synthetic service spy checks the final call boundary.
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
    _activity,
    _fixture,
    _work,
)

import concord.menu_artifact as menu
import concord.menu_artifact_write_context as authority
from concord.storage import list_work_snapshots
from concord.workflows.artifact_routine_review import (
    ArtifactRoutineReviewEligibility,
)


def _selected(root: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Any, Any]:
    monkeypatch.setattr(
        menu,
        "select_one",
        lambda title, items, labels, **kw: (
            "continue" if title == "Quick Artifact Review - Evidence" else items[0]
        ),
    )
    current = _activity(root)
    write_preview = authority.begin_artifact_write_context(
        current, operation="Synthetic Quick Review selection"
    )
    artifact = menu._choose_artifact(
        current,
        title="Synthetic Quick Review refusal",
        write_context=write_preview,
    )
    return current, artifact


def _fake_eligible_context(
    root: Path,
    current: Any,
    artifact: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real = menu.inspect_artifact_routine_review

    def inspect(*args: Any, **kwargs: Any) -> Any:
        context = real(*args, **kwargs)
        assert kwargs.get("workspace_root") == root
        assert not context.eligibility.quick_review_eligible
        return replace(
            context,
            eligibility=ArtifactRoutineReviewEligibility(
                quick_review_eligible=True,
                exception_reasons=(),
            ),
            first_review_pending=True,
        )

    monkeypatch.setattr(menu, "inspect_artifact_routine_review", inspect)


@pytest.mark.parametrize(
    "orientation", ("mixed", "standards_based", "evidence_only", "local_criteria_only")
)
def test_unreturned_work_never_enters_quick_review_or_score(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, orientation: str
) -> None:
    root = _fixture(tmp_path, monkeypatch, orientation)
    current, artifact = _selected(root, monkeypatch)
    before = list_work_snapshots(root, _work())
    monkeypatch.setattr(
        menu,
        "record_routine_artifact_review",
        lambda *args, **kwargs: pytest.fail(
            "Unreturned work must not record routine Review"
        ),
    )
    monkeypatch.setattr(
        menu,
        "confirm_write",
        lambda *args, **kwargs: pytest.fail(
            "Ineligible work must not reach a ready Review confirmation"
        ),
    )
    result = menu._quick_review_selected(
        current, artifact, menu.MenuSessionContext(actor=ACTOR)
    )
    assert result is False
    assert list_work_snapshots(root, _work()) == before


@pytest.mark.parametrize("orientation", ("mixed", "evidence_only"))
def test_guarded_commit_call_uses_conditional_canonical_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, orientation: str
) -> None:
    root = _fixture(tmp_path, monkeypatch, orientation)
    current, artifact = _selected(root, monkeypatch)
    _fake_eligible_context(root, current, artifact, monkeypatch)
    before = list_work_snapshots(root, _work())
    observed: list[tuple[Any, Any, dict[str, Any]]] = []

    def capture(context: Any, values: Any, **kwargs: Any) -> Any:
        observed.append((context, values, kwargs))
        return SimpleNamespace(
            artifact_review_id="synthetic-call-only-not-persisted",
            commit=SimpleNamespace(snapshot_revision=context.snapshot_revision + 1),
        )

    monkeypatch.setattr(menu, "record_routine_artifact_review", capture)
    result = menu._quick_review_selected(
        current, artifact, menu.MenuSessionContext(actor=ACTOR)
    )
    assert result is True
    assert len(observed) == 1
    context, values, kwargs = observed[0]
    assert context.snapshot_revision == current.snapshot_revision
    assert context.artifact.artifact_instance_id == artifact.artifact_instance_id
    assert values.scoring_readiness == "ready"
    assert kwargs["workspace_root"] == root
    assert kwargs["actor"] == ACTOR
    assert ("standards_library" in kwargs) == (orientation == "mixed")
    assert list_work_snapshots(root, _work()) == before


def test_cancellation_is_exact_no_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _fixture(tmp_path, monkeypatch, "mixed")
    current, artifact = _selected(root, monkeypatch)
    _fake_eligible_context(root, current, artifact, monkeypatch)
    before = list_work_snapshots(root, _work())
    monkeypatch.setattr(menu, "confirm_write", lambda *a, **kw: False)
    monkeypatch.setattr(
        menu,
        "record_routine_artifact_review",
        lambda *a, **kw: pytest.fail("Cancellation must never reach Review storage"),
    )
    assert not menu._quick_review_selected(
        current, artifact, menu.MenuSessionContext(actor=ACTOR)
    )
    assert list_work_snapshots(root, _work()) == before


def test_stale_selected_artifact_is_rejected_before_evidence_prompt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _fixture(tmp_path, monkeypatch, "mixed")
    current, artifact = _selected(root, monkeypatch)
    stale = replace(artifact, snapshot_revision=artifact.snapshot_revision + 1)
    before = list_work_snapshots(root, _work())
    with pytest.raises(Exception, match="Selected Artifact changed"):
        menu._quick_review_selected(
            current, stale, menu.MenuSessionContext(actor=ACTOR)
        )
    assert list_work_snapshots(root, _work()) == before


def test_workspace_switch_after_confirmation_blocks_quick_review(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _fixture(tmp_path, monkeypatch, "mixed")
    current, artifact = _selected(root, monkeypatch)
    _fake_eligible_context(root, current, artifact, monkeypatch)
    foreign = build_workspace(tmp_path / "foreign", orientation="mixed")
    original_snapshots = list_work_snapshots(root, _work())
    foreign_snapshots = list_work_snapshots(
        foreign.root,
        ModuleWorkRef("concord", current.class_id, current.activity_id),
    )

    def swap_workspace(*args: Any, **kwargs: Any) -> bool:
        monkeypatch.setattr(
            authority,
            "resolve_read_workspace_root",
            lambda explicit=None: (
                foreign.root if explicit is None else Path(explicit)
            ),
        )
        return True

    monkeypatch.setattr(menu, "confirm_write", swap_workspace)
    monkeypatch.setattr(
        menu,
        "record_routine_artifact_review",
        lambda *a, **kw: pytest.fail("Workspace drift must block write"),
    )
    with pytest.raises(Exception, match="workspace has changed"):
        menu._quick_review_selected(
            current, artifact, menu.MenuSessionContext(actor=ACTOR)
        )
    assert list_work_snapshots(root, _work()) == original_snapshots
    assert list_work_snapshots(foreign.root, _work()) == foreign_snapshots
