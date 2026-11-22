"""#151 Slice 3: returned-work assembly must preflight before any actor/write.

Menu-only synthetic fixtures: no workspace, real scan, PDF opener or academic
mutation. The existing assembly writer and viewer tests remain independent.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import concord.menu_artifact as menu
from concord.menu_context import MenuSessionContext
from concord.workflows import ConcordWorkflowConflictError
from concord.workflows.artifact_assembly import AssemblyPageSelection
from concord.workflows.models import ActivitySummary


def _activity() -> ActivitySummary:
    return ActivitySummary(
        class_id="class-151-synthetic",
        activity_id="activity-151-synthetic",
        title="Synthetic Returned Seminar",
        status="active",
        scoring_orientation="mixed",
        session_count=1,
        group_count=6,
        snapshot_revision=19,
    )


def _choice() -> SimpleNamespace:
    return SimpleNamespace(
        label="Cluster Red | Session 1 | work 1 of 2",
        summary=SimpleNamespace(artifact_instance_id="artifact-151-exact"),
    )


def _item(stage: str) -> SimpleNamespace:
    return SimpleNamespace(
        artifact_instance_id="artifact-151-exact",
        stage=stage,
        stage_label=stage.replace("_", " "),
        routed_return_pages=0 if stage == "awaiting_return" else 1,
        required_return_pages=2,
        next_action="Route or review the missing page",
    )


def _arrange(
    monkeypatch: pytest.MonkeyPatch,
    stage: str,
) -> tuple[list[str], list[tuple[str, tuple[str, ...]]]]:
    calls: list[str] = []
    receipts: list[tuple[str, tuple[str, ...]]] = []
    monkeypatch.setattr(menu, "_latest", lambda _a: _activity())
    monkeypatch.setattr(menu, "_choose_artifact_choice", lambda *_a, **_kw: _choice())

    def inspect(class_id: str, activity_id: str, **kwargs: object) -> object:
        calls.append("inspect")
        assert class_id == "class-151-synthetic"
        assert activity_id == "activity-151-synthetic"
        assert kwargs == {"expected_snapshot_revision": 19}
        return SimpleNamespace(items=(_item(stage),))

    monkeypatch.setattr(menu, "inspect_teacher_collection_overview", inspect)
    monkeypatch.setattr(
        menu, "show_result", lambda title, lines: receipts.append((title, tuple(lines)))
    )
    return calls, receipts


@pytest.mark.parametrize(
    "stage",
    (
        "not_return_expected",
        "awaiting_return",
        "partially_returned",
        "needs_recovery",
    ),
)
def test_unready_evidence_cannot_reach_selection_actor_or_writer(
    monkeypatch: pytest.MonkeyPatch,
    stage: str,
) -> None:
    calls, receipts = _arrange(monkeypatch, stage)
    monkeypatch.setattr(
        menu, "_assembly_selections", lambda *_a: pytest.fail("early occurrences")
    )
    monkeypatch.setattr(
        menu, "confirm_actor_write", lambda *_a, **_kw: pytest.fail("early actor")
    )
    monkeypatch.setattr(
        menu, "assemble_returned_artifact", lambda *_a: pytest.fail("early assembly")
    )
    menu._assemble(_activity(), MenuSessionContext())
    assert calls == ["inspect"]
    assert len(receipts) == 1
    text = " ".join(receipts[0][1]).lower()
    assert "routed returned pages" in text
    assert "not tracked" in text
    assert "no assembly or evidence change" in text
    assert "artifact-151-exact" not in text


@pytest.mark.parametrize(
    "stage", ("ready_to_assemble", "choose_occurrences", "assembled")
)
def test_actionable_state_preserves_exact_writer_and_no_automatic_open(
    monkeypatch: pytest.MonkeyPatch,
    stage: str,
) -> None:
    calls, receipts = _arrange(monkeypatch, stage)
    selections = (
        AssemblyPageSelection(
            artifact_page_id="page-151-synthetic",
            scan_reference_id="scan-151-occurrence-b",
        ),
    )

    def choose(
        _activity: object, _artifact: object
    ) -> tuple[AssemblyPageSelection, ...]:
        calls.append("occurrences")
        return selections

    def actor(*_args: object, **_kwargs: object) -> object:
        calls.append("actor")
        return SimpleNamespace(actor_id="synthetic-teacher")

    def assemble(request: object) -> object:
        calls.append("assemble")
        assert request.class_id == "class-151-synthetic"
        assert request.activity_id == "activity-151-synthetic"
        assert request.artifact_instance_id == "artifact-151-exact"
        assert request.expected_snapshot_revision == 19
        assert request.selections == selections
        return SimpleNamespace(page_count=2, reused=(stage == "assembled"))

    monkeypatch.setattr(menu, "_assembly_selections", choose)
    monkeypatch.setattr(menu, "confirm_actor_write", actor)
    monkeypatch.setattr(menu, "assemble_returned_artifact", assemble)
    monkeypatch.setattr(
        menu,
        "open_returned_artifact_evidence",
        lambda *_a, **_kw: pytest.fail("viewer must be separate"),
    )
    menu._assemble(_activity(), MenuSessionContext())
    assert calls == ["inspect", "occurrences", "actor", "assemble"]
    assert len(receipts) == 1
    text = " ".join(receipts[0][1]).lower()
    assert "o. open returned work" in text
    assert "did not request a pdf viewer" in text
    assert ("reused" in text) == (stage == "assembled")


def test_canceled_actor_cannot_assemble(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls, receipts = _arrange(monkeypatch, "ready_to_assemble")
    monkeypatch.setattr(menu, "_assembly_selections", lambda *_a: ())
    monkeypatch.setattr(menu, "confirm_actor_write", lambda *_a, **_kw: None)
    monkeypatch.setattr(
        menu, "assemble_returned_artifact", lambda *_a: pytest.fail("canceled write")
    )
    menu._assemble(_activity(), MenuSessionContext())
    assert calls == ["inspect"]
    assert receipts == []


def test_stale_snapshot_stops_before_occurrence_or_actor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _arrange(monkeypatch, "ready_to_assemble")
    monkeypatch.setattr(
        menu,
        "inspect_teacher_collection_overview",
        lambda *_a, **_kw: (_ for _ in ()).throw(
            ConcordWorkflowConflictError("Synthetic stale snapshot")
        ),
    )
    monkeypatch.setattr(
        menu, "_assembly_selections", lambda *_a: pytest.fail("early occurrence")
    )
    monkeypatch.setattr(
        menu, "confirm_actor_write", lambda *_a, **_kw: pytest.fail("early actor")
    )
    with pytest.raises(ConcordWorkflowConflictError):
        menu._assemble(_activity(), MenuSessionContext())


def test_disappeared_artifact_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _arrange(monkeypatch, "ready_to_assemble")
    monkeypatch.setattr(
        menu,
        "inspect_teacher_collection_overview",
        lambda *_a, **_kw: SimpleNamespace(items=()),
    )
    monkeypatch.setattr(
        menu, "confirm_actor_write", lambda *_a, **_kw: pytest.fail("early actor")
    )
    with pytest.raises(ConcordWorkflowConflictError, match="changed"):
        menu._assemble(_activity(), MenuSessionContext())
