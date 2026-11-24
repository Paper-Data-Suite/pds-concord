"""#152 Slice 1K4: stale replay cannot duplicate a durable routine Score."""

from __future__ import annotations

from pathlib import Path

import pytest
from pds_core.routing_models import ModuleWorkRef
from test_issue142_slice6b_real_score_continuation import (
    ACTIVITY,
    ACTOR,
    CLASS,
    _first_score,
    _setup_reviewed,
)

from concord.storage import list_work_snapshots, load_current_record_graph
from concord.storage_errors import ConcordStorageConflictError
from concord.workflows.artifact_routine_scoring_execution import (
    record_prepared_routine_score,
)


def test_committed_preview_replay_preserves_exact_score_and_link(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, standards = _setup_reviewed(tmp_path, monkeypatch)
    work = ModuleWorkRef("concord", CLASS, ACTIVITY)
    before = list_work_snapshots(root, work)
    result = _first_score(root, monkeypatch)
    committed = list_work_snapshots(root, work)
    graph = load_current_record_graph(root, work, standards_library=standards).graph
    assert len(committed) == len(before) + 1
    (score,) = graph.score_records
    (link,) = graph.score_evidence_links
    assert score.score_record_id == result.mutation.score_record_id
    assert (link.score_evidence_link_id,) == result.mutation.score_evidence_link_ids
    assert link.score_record_id == score.score_record_id
    assert link.evidence_reference == result.preview.evidence.evidence_reference

    # Simulate resubmission of the old confirmed preview, not process termination
    # or power loss. The actual canonical storage CAS must reject the write.
    with pytest.raises(ConcordStorageConflictError, match="expected snapshot"):
        record_prepared_routine_score(
            result.preview,
            actor=ACTOR,
            workspace_root=root,
            standards_library=standards,
        )
    assert list_work_snapshots(root, work) == committed
    assert (
        load_current_record_graph(root, work, standards_library=standards).graph
        == graph
    )
