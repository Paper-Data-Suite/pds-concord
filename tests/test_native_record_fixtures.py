from __future__ import annotations

import json
from pathlib import Path

from concord.model_conversion import record_from_dict, record_to_dict
from concord.model_validation import ConcordRecordGraph, collect_record_graph_issues

FIXTURES = Path(__file__).parent / "fixtures" / "native_records"


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_all_native_record_fixtures_are_strict_and_privacy_safe() -> None:
    paths = tuple(sorted(FIXTURES.glob("*.json")))
    assert len(paths) == 6
    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert "@" not in text
        assert "C:\\" not in text
        assert isinstance(_load(path).get("expected_issue_codes"), list)


def test_valid_fixture_record_bodies_round_trip_exactly() -> None:
    for filename in ("evidence_only_activity.json", "standards_activity.json"):
        fixture = _load(FIXTURES / filename)
        records = fixture["records"]
        assert isinstance(records, list)
        for envelope in records:
            assert isinstance(envelope, dict)
            record = record_from_dict(envelope["record_kind"], envelope["body"])
            assert record_to_dict(record) == envelope["body"]


def test_integrated_fixture_keeps_semantic_identities_distinct() -> None:
    proof = _load(FIXTURES / "standards_activity.json")["semantic_proof"]
    assert isinstance(proof, dict)
    assert proof["author_id"] != proof["subject_id"]
    assert proof["route_target_id"] != proof["score_target_id"]
    assert proof["standard_score_criterion_id"] == "criterion-standard"
    assert proof["standard_score_scale_id"] == "scale-1"
    assert proof["non_score_disposition"] == "not_observed"
    assert proof["score_revision_predecessor_id"] == "score-standard-1"
    assert proof["group_score_creates_student_scores"] is False


def test_integrated_fixture_is_a_valid_record_graph() -> None:
    fixture = _load(FIXTURES / "standards_activity.json")
    records = fixture["records"]
    assert isinstance(records, list)
    collection_by_kind = {
        "activity": "activities",
        "session": "sessions",
        "group": "groups",
        "group_membership": "memberships",
        "role_assignment": "role_assignments",
        "responsibility_assignment": "responsibility_assignments",
        "artifact_instance": "artifact_instances",
        "artifact_page": "artifact_pages",
        "artifact_author": "artifact_authors",
        "artifact_subject": "artifact_subjects",
        "artifact_review": "artifact_reviews",
        "moderation_record": "moderation_records",
        "criterion_set": "criterion_sets",
        "criterion": "criteria",
        "scoring_scale": "scoring_scales",
        "score_record": "score_records",
        "score_evidence_link": "score_evidence_links",
        "correction": "correction_records",
    }
    collections: dict[str, list[object]] = {
        name: [] for name in collection_by_kind.values()
    }
    for envelope in records:
        assert isinstance(envelope, dict)
        kind = envelope["record_kind"]
        assert isinstance(kind, str)
        collections[collection_by_kind[kind]].append(
            record_from_dict(kind, envelope["body"])
        )
    graph = ConcordRecordGraph(
        **{name: tuple(values) for name, values in collections.items()}
    )
    assert collect_record_graph_issues(graph) == ()
