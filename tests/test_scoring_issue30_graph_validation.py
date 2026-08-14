from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from concord.model_conversion import record_from_dict
from concord.model_validation import ConcordRecordGraph, collect_record_graph_issues
from concord.models import (
    ConcordRecordReference,
    CorrectionRecord,
    ScoreEvidenceLink,
    ScoreTargetReference,
    StatusReason,
)
from concord.record_registry import RECORD_DESCRIPTORS, descriptor_for_kind

FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "native_records"
    / "standards_activity.json"
)


def _fixture_graph() -> ConcordRecordGraph:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    collections: dict[str, list[object]] = {
        item.graph_collection: [] for item in RECORD_DESCRIPTORS
    }
    for entry in payload["records"]:
        descriptor = descriptor_for_kind(entry["record_kind"])
        collections[descriptor.graph_collection].append(
            record_from_dict(entry["record_kind"], entry["body"])
        )
    return ConcordRecordGraph(
        **{key: tuple(values) for key, values in collections.items()}
    )


def _codes(graph: ConcordRecordGraph) -> set[str]:
    return {item.code for item in collect_record_graph_issues(graph)}


def test_fixture_remains_valid_under_issue30_hardening() -> None:
    assert _codes(_fixture_graph()) == set()


def test_score_criterion_must_belong_to_activity_selected_set() -> None:
    graph = _fixture_graph()
    activity = replace(graph.activities[0], criterion_set_ids=())
    hardened = replace(graph, activities=(activity,))
    assert "score.criterion.not_selected" in _codes(hardened)


def test_score_successor_requires_exact_score_revision_audit() -> None:
    graph = _fixture_graph()
    hardened = replace(graph, correction_records=())
    assert "score.correction.missing" in _codes(hardened)


def test_score_correction_type_must_match_score_target() -> None:
    graph = _fixture_graph()
    correction = replace(
        graph.correction_records[0],
        correction_type="metadata_correction",
    )
    hardened = replace(graph, correction_records=(correction,))
    codes = _codes(hardened)
    assert "correction.type.target_mismatch" in codes
    assert "score.correction.missing" in codes


def test_score_successor_time_cannot_move_backwards() -> None:
    graph = _fixture_graph()
    scores = list(graph.score_records)
    successor_index = next(
        index
        for index, item in enumerate(scores)
        if item.score_record_id == "score-standard-2"
    )
    scores[successor_index] = replace(
        scores[successor_index],
        scored_at="2026-08-05T12:00:00-04:00",
    )
    hardened = replace(graph, score_records=tuple(scores))
    assert "score.supersession.time_backwards" in _codes(hardened)


def test_non_score_reason_must_match_disposition_when_present() -> None:
    graph = _fixture_graph()
    scores = list(graph.score_records)
    index = next(
        index
        for index, item in enumerate(scores)
        if item.score_record_id == "score-group-nonscore"
    )
    score = scores[index]
    scores[index] = replace(
        score,
        status_reason=StatusReason(
            reason_code="absent",
            recorded_by=score.scorer,
            recorded_at=score.scored_at,
        ),
    )
    hardened = replace(graph, score_records=tuple(scores))
    assert "score.status_reason.mismatch" in _codes(hardened)


def test_score_target_owner_must_match_target_kind() -> None:
    graph = _fixture_graph()
    scores = list(graph.score_records)
    index = next(
        index
        for index, item in enumerate(scores)
        if item.score_record_id == "score-group-1"
    )
    score = scores[index]
    scores[index] = replace(
        score,
        target_reference=ScoreTargetReference(
            target_kind="concord_group",
            target_id="group-1",
            owning_system="core",
        ),
    )
    hardened = replace(graph, score_records=tuple(scores))
    assert "score.target.owner_mismatch" in _codes(hardened)


def test_link_successor_must_preserve_parent_score() -> None:
    graph = _fixture_graph()
    predecessor = graph.score_evidence_links[0]
    successor = ScoreEvidenceLink(
        score_evidence_link_id="link-successor",
        score_record_id="score-group-1",
        evidence_reference=predecessor.evidence_reference,
        relevance_description="Synthetic administrative link correction.",
        status="active",
        created_provenance=predecessor.created_provenance,
        subject_context=predecessor.subject_context,
        significance=predecessor.significance,
        moderation_record_id=predecessor.moderation_record_id,
        supersedes_score_evidence_link_id=predecessor.score_evidence_link_id,
    )
    hardened = replace(
        graph,
        score_evidence_links=(*graph.score_evidence_links, successor),
    )
    assert "score_evidence.supersession.score_mismatch" in _codes(hardened)


def test_superseded_link_is_not_counted_as_current_active_evidence() -> None:
    graph = _fixture_graph()
    predecessor = graph.score_evidence_links[0]
    successor = ScoreEvidenceLink(
        score_evidence_link_id="link-successor",
        score_record_id=predecessor.score_record_id,
        evidence_reference=predecessor.evidence_reference,
        relevance_description="Synthetic administrative link correction.",
        status="active",
        created_provenance=predecessor.created_provenance,
        subject_context=predecessor.subject_context,
        significance=predecessor.significance,
        moderation_record_id=predecessor.moderation_record_id,
        supersedes_score_evidence_link_id=predecessor.score_evidence_link_id,
    )
    hardened = replace(
        graph,
        score_evidence_links=(*graph.score_evidence_links, successor),
    )
    codes = _codes(hardened)
    assert "score.evidence.source_duplicate" not in codes
    assert "score.evidence.required" not in codes


def test_definition_successor_must_preserve_lineage() -> None:
    graph = _fixture_graph()
    predecessor = graph.scoring_scales[0]
    successor = replace(
        predecessor,
        scoring_scale_id="scale-2",
        lineage_id="wrong-lineage",
        revision=2,
        supersedes_scoring_scale_id=predecessor.scoring_scale_id,
    )
    hardened = replace(
        graph,
        scoring_scales=(*graph.scoring_scales, successor),
    )
    assert "scoring_scale.lineage.mismatch" in _codes(hardened)


def test_historical_score_may_retain_historical_moderation() -> None:
    graph = _fixture_graph()
    predecessor = graph.moderation_records[0]
    successor = replace(
        predecessor,
        moderation_record_id="moderation-2",
        moderated_at="2026-08-05T13:30:00-04:00",
        supersedes_moderation_record_id=predecessor.moderation_record_id,
    )
    correction = CorrectionRecord(
        correction_id="moderation-correction-1",
        target_reference=ConcordRecordReference(
            record_kind="moderation_record",
            record_id=predecessor.moderation_record_id,
        ),
        correction_type="moderation_revision",
        reason="Synthetic moderation revision.",
        correcting_actor=predecessor.moderator,
        corrected_at="2026-08-05T13:30:00-04:00",
        privacy_policy=predecessor.privacy_policy,
        replacement_reference=ConcordRecordReference(
            record_kind="moderation_record",
            record_id=successor.moderation_record_id,
        ),
    )
    hardened = replace(
        graph,
        moderation_records=(*graph.moderation_records, successor),
        correction_records=(*graph.correction_records, correction),
    )
    codes = _codes(hardened)
    assert "moderation.current.required" not in codes
    assert "score.evidence.moderation_required" not in codes
