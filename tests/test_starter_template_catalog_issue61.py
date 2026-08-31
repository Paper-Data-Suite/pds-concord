from __future__ import annotations

import json

import pytest

from concord.models import ActorReference, Provenance
from concord.starter_templates.catalog import (
    STARTER_TEMPLATE_COUNT,
    get_starter_template,
    list_starter_templates,
    validate_starter_catalog,
)
from concord.starter_templates.layout import (
    STARTER_LAYOUT_SCHEMA,
    StarterLayoutError,
    starter_layout_from_json_bytes,
    starter_layout_to_json_bytes,
)

EXPECTED_KEYS = (
    "think_pair_share",
    "socratic_seminar",
    "fishbowl_observer",
    "four_corners",
    "structured_academic_controversy",
    "save_last_word",
    "discussion_map",
    "talk_moves_observer",
    "jigsaw_expert",
    "reciprocal_reading",
    "collaborative_annotation",
    "gallery_walk",
    "see_think_wonder",
    "group_kwl",
    "venn_comparison",
    "comparison_matrix",
    "concept_map",
    "decision_matrix",
    "group_roles",
    "team_contract",
    "project_plan",
    "project_check_in",
    "peer_review_writing",
    "peer_review_presentation",
    "peer_design_code_review",
    "lab_investigation",
    "claim_evidence_reasoning",
    "collaborative_problem_solving",
    "collaborative_work_reflection",
    "team_health_check",
)


def _provenance() -> Provenance:
    return Provenance(
        actor=ActorReference(
            actor_kind="authorized_adult",
            actor_id="teacher-1",
            owning_system="concord",
        ),
        timestamp="2026-08-25T12:00:00-04:00",
        source_kind="system",
        application_version="0.3.0",
        note="Synthetic issue #61 catalog validation.",
    )


def test_catalog_contains_exact_approved_30_starters() -> None:
    items = list_starter_templates()
    assert STARTER_TEMPLATE_COUNT == 30
    assert len(items) == 30
    assert tuple(item.starter_key for item in items) == EXPECTED_KEYS
    assert tuple(item.catalog_order for item in items) == tuple(
        range(1, 31)
    )


def test_catalog_identity_and_asset_fields_are_unique() -> None:
    items = list_starter_templates()
    for field_name in (
        "starter_key",
        "template_id",
        "template_version_id",
        "rendering_specification_reference",
        "asset_name",
    ):
        values = tuple(getattr(item, field_name) for item in items)
        assert len(set(values)) == len(values)


def test_all_packaged_layouts_are_strict_canonical_json() -> None:
    for item in list_starter_templates():
        data = item.rendering_specification_bytes()
        assert data.endswith(b"\n")
        layout = starter_layout_from_json_bytes(data)
        assert layout.schema_version == STARTER_LAYOUT_SCHEMA
        assert starter_layout_to_json_bytes(layout) == data
        assert item.rendering_sha256()
        assert len(item.rendering_sha256()) == 64


def test_catalog_metadata_matches_packaged_layouts() -> None:
    for item in list_starter_templates():
        layout = item.layout()
        assert layout.paper_size == "letter"
        assert len(layout.pages) == item.page_count
        assert {page.orientation for page in layout.pages} == {
            item.orientation
        }
        assert tuple(page.sequence for page in layout.pages) == tuple(
            range(1, item.page_count + 1)
        )
        assert all(page.sections for page in layout.pages)


def test_every_starter_builds_valid_ordinary_template_records() -> None:
    provenance = _provenance()
    for item in list_starter_templates():
        definition, version = item.build_template_records(
            created_provenance=provenance
        )
        assert definition.template_id == item.template_id
        assert definition.status == "active"
        assert version.template_id == item.template_id
        assert version.template_version_id == item.template_version_id
        assert version.status == "active"
        assert version.revision_sequence == 1
        assert version.supersedes_template_version_id is None
        assert version.rendering_contract_version == STARTER_LAYOUT_SCHEMA
        assert (
            version.rendering_specification_reference
            == item.rendering_specification_reference
        )
        assert (
            version.rendering_specification_sha256
            == item.rendering_sha256()
        )
        assert len(version.page_manifest) == item.page_count
        assert all(page.return_expected for page in version.page_manifest)
        assert all(page.route_required for page in version.page_manifest)
        assert all(
            page.route_payload_input_key == "pds2_route_payload"
            for page in version.page_manifest
        )
        assert all(
            page.human_fallback_input_key == "human_fallback"
            for page in version.page_manifest
        )


def test_starter_template_response_regions_are_semantically_declared() -> None:
    provenance = _provenance()
    for item in list_starter_templates():
        _, version = item.build_template_records(
            created_provenance=provenance
        )
        regions = tuple(
            region
            for page in version.page_manifest
            for region in page.response_regions
        )
        assert regions
        keys = tuple(region.region_key for region in regions)
        assert len(set(keys)) == len(keys)


def test_layout_assets_do_not_embed_instance_owned_identities() -> None:
    forbidden = (
        b'"activity_id"',
        b'"session_id"',
        b'"group_id"',
        b'"student_id"',
        b'"packet_instance_id"',
        b'"artifact_instance_id"',
        b'"artifact_page_id"',
        b'"route_id"',
        b'"score_id"',
        b'"group_plan_id"',
        b'"signal_set_id"',
    )
    for item in list_starter_templates():
        data = item.rendering_specification_bytes()
        for token in forbidden:
            assert token not in data


def test_approved_special_cases_are_preserved() -> None:
    seminar = get_starter_template("socratic_seminar")
    assert seminar.page_count == 2
    assert seminar.suggested_activity_type_keys == (
        "socratic_seminar",
    )

    roles = get_starter_template("group_roles")
    roles_text = roles.rendering_specification_bytes().decode("utf-8")
    assert "facilitator" in roles_text
    assert "not canonical Role assignments" in roles_text

    team_health = get_starter_template("team_health_check")
    assert team_health.default_privacy_classification == (
        "teacher_restricted"
    )

    code_review = get_starter_template("peer_design_code_review")
    assert code_review.orientation == "landscape"

    lab = get_starter_template("lab_investigation")
    assert lab.artifact_category == "laboratory_record"
    assert lab.page_count == 2


def test_catalog_validator_accepts_packaged_catalog() -> None:
    validate_starter_catalog()


def test_layout_parser_rejects_unknown_fields() -> None:
    data = get_starter_template(
        "think_pair_share"
    ).rendering_specification_bytes()
    parsed = json.loads(data.decode("utf-8"))
    parsed["unexpected"] = True
    mutated = (
        json.dumps(
            parsed,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    with pytest.raises(StarterLayoutError):
        starter_layout_from_json_bytes(mutated)


def test_layout_parser_rejects_duplicate_object_keys() -> None:
    with pytest.raises(StarterLayoutError):
        starter_layout_from_json_bytes(
            b'{"schema_version":"concord_starter_layout_v1",'
            b'"schema_version":"concord_starter_layout_v1",'
            b'"paper_size":"letter","pages":[]}\n'
        )
