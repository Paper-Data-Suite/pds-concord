"""#152 Slice 1I: durable, teacher-readable routine Score receipts."""

from __future__ import annotations

from types import SimpleNamespace
from typing import cast

import pytest

import concord.menu_artifact_scoring as menu
from concord.workflows.score_recording import ScoreMutationResult


def _mutation(
    *, links: int = 1, no_op: bool = False,
) -> ScoreMutationResult:
    return cast(
        ScoreMutationResult,
        SimpleNamespace(
            score_record_id="private-score-record-id",
            score_evidence_link_ids=tuple(
                f"private-link-{i}" for i in range(links)
            ),
            commit=SimpleNamespace(snapshot_revision=31, no_op=no_op),
        ),
    )


def _decision(*, group: bool = False) -> tuple[str, ...]:
    return (
        "Activity: Synthetic literary discussion",
        "Artifact: this reviewed Artifact",
        "Target: Cluster A — group" if group else "Target: Alex Example — student",
        "Criterion: Textual analysis",
        "Scale: Four-level rubric",
        "Value: 3 — Meets expectations",
        "Disposition: scored",
        "Basis: linked_evidence",
        "Evidence: this reviewed Artifact",
        "Session: No separate Score Session context",
        "Review provenance (preview only): explicit current Artifact Review",
        *(("GROUP SCORE WARNING:",) if group else ()),
    )


def test_receipt_contains_exact_confirmed_teacher_labels_and_link_count() -> None:
    lines = menu._routine_score_receipt_lines(_decision(), _mutation())
    assert lines[0].startswith("Teacher-authorized Score")
    assert "Target: Alex Example — student" in lines
    assert "Criterion: Textual analysis" in lines
    assert "Scale: Four-level rubric" in lines
    assert "Value: 3 — Meets expectations" in lines
    assert "Disposition: scored" in lines
    assert "Basis: linked_evidence" in lines
    assert "Evidence: this reviewed Artifact" in lines
    assert "Native Artifact Evidence Links: 1" in lines
    assert "Snapshot: 31" in lines
    assert any("not a Grade or a Meridian publication" in item for item in lines)
    assert not any("private-" in item for item in lines)


def test_cluster_receipt_repeats_no_student_score_warning() -> None:
    lines = menu._routine_score_receipt_lines(
        _decision(group=True), _mutation()
    )
    assert "Target: Cluster A — group" in lines
    assert "Group Score only: no individual student Scores were created." in lines


@pytest.mark.parametrize(
    ("links", "no_op"),
    ((0, False), (2, False), (1, True)),
)
def test_ambiguous_write_result_never_claims_complete_score(
    links: int, no_op: bool,
) -> None:
    lines = menu._routine_score_receipt_lines(
        _decision(), _mutation(links=links, no_op=no_op)
    )
    assert lines[0] == (
        "Score write outcome requires verification; do not submit again."
    )
    assert f"Reported native Artifact Evidence Links: {links}" in lines
    assert "Snapshot: 31" in lines
    assert any("Open View Scores" in line for line in lines)
    assert not any("Score recorded." in line for line in lines)


@pytest.mark.parametrize(
    "typed_value",
    ("true — Yes", '"3" — Category three', "3 — Three"),
)
def test_receipt_preserves_native_typed_scale_text(
    typed_value: str,
) -> None:
    original = _decision()
    chosen = tuple(
        f"Value: {typed_value}" if line.startswith("Value: ") else line
        for line in original
    )
    receipt = menu._routine_score_receipt_lines(chosen, _mutation())
    assert f"Value: {typed_value}" in receipt
