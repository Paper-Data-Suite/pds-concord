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


def test_integrated_fixture_declares_publication_expectations() -> None:
    fixture = _load(FIXTURES / "standards_activity.json")
    expected = fixture["expected_academic_result_manifest_projection"]
    assert isinstance(expected, dict)
    assert expected["contract_version"] == "concord_academic_result_manifest_v1"
    assert expected["record_type"] == "concord_academic_result_manifest"
    work = expected["work"]
    assert isinstance(work, dict)
    assert work == {
        "module_id": "concord",
        "class_id": "class-1",
        "work_id": "standards-activity",
    }
    assert expected["expected_capabilities"] == [
        "criterion_scores",
        "moderated_scores",
        "standards_ratings",
    ]
    assert expected["score_projection"] == [
        {"score_record_id": "score-standard-1", "current_state": "superseded"},
        {"score_record_id": "score-standard-2", "current_state": "current"},
        {
            "score_record_id": "score-group-1",
            "current_state": "current",
            "target_kind": "concord_group",
        },
        {
            "score_record_id": "score-group-nonscore",
            "current_state": "current",
            "disposition": "not_observed",
            "value_present": False,
        },
    ]
    assert expected["standards_result_score_ids"] == [
        "score-standard-1",
        "score-standard-2",
    ]
    lineage = expected["external_evidence_lineage_examples"]
    assert isinstance(lineage, list)
    assert len(lineage) == 2
    assert all(isinstance(item, dict) for item in lineage)
    assert {
        item["owning_system"]
        for item in lineage
        if isinstance(item, dict)
    } == {"scoreform", "quillan"}
    values = expected["type_sensitive_scale_values"]
    assert isinstance(values, list)
    assert [type(value) for value in values] == [int, float, str, bool]
    excluded = expected["private_fields_excluded"]
    assert isinstance(excluded, list)
    assert "score_record.rationale" in excluded
    assert "status_reason.note" in excluded
    assert "moderation_record.rationale" in excluded
    assert "evidence_locator.note" in excluded
    policy = expected["downstream_policy_excluded"]
    assert isinstance(policy, list)
    assert {"grade", "proficiency", "mastery"} <= set(policy)


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
        "scan_reference": "scan_references",
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

def test_integrated_fixture_declares_issue32_artifact_reader_proof() -> None:
    fixture = _load(FIXTURES / "standards_activity.json")
    proof = fixture["artifact_reader_proof"]
    assert isinstance(proof, dict)
    assert proof["artifact_instance_link_id"] == "link-1"
    assert proof["artifact_page_link_id"] == "link-page-1"
    moderation_ids = {
        item["body"]["moderation_record_id"]
        for item in fixture["records"]
        if isinstance(item, dict)
        and item.get("record_kind") == "moderation_record"
    }
    assert "moderation-page-1" in moderation_ids
    assert proof["type_sensitive_scale_id"] == "scale-typed"
    assert proof["retained_source_relative_path"] == (
        "scans/source/2026-08-15/standards-page-1.png"
    )
    assert len(proof["retained_source_sha256"]) == 64

    records = fixture["records"]
    assert isinstance(records, list)
    kinds = [item["record_kind"] for item in records if isinstance(item, dict)]
    assert "scan_reference" in kinds
    links = [
        item["body"]
        for item in records
        if isinstance(item, dict) and item.get("record_kind") == "score_evidence_link"
    ]
    assert {item["score_evidence_link_id"] for item in links} >= {
        "link-1",
        "link-page-1",
        "link-scoreform-1",
        "link-quillan-1",
    }
    scales = [
        item["body"]
        for item in records
        if isinstance(item, dict) and item.get("record_kind") == "scoring_scale"
    ]
    typed = next(item for item in scales if item["scoring_scale_id"] == "scale-typed")
    values = [level["value"] for level in typed["levels"]]
    assert [type(value) for value in values] == [int, float, str, bool]
