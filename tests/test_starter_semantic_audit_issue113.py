from __future__ import annotations

from concord.models import (
    ActorReference,
    Provenance,
    TemplateSubjectExpectation,
    TemplateSubjectResolutionExpectation,
)
from concord.starter_templates.catalog import list_starter_templates
from concord.starter_templates.catalog_lineage import (
    RELATIONSHIP_AWARE_STARTER_KEYS,
    build_starter_template_lineage,
)

STARTER_RELATIONSHIP_AUDIT = (
    ("think_pair_share", "self_participant"),
    ("socratic_seminar", "self_participant"),
    ("fishbowl_observer", "observer"),
    ("four_corners", "self_participant"),
    ("structured_academic_controversy", "group"),
    ("save_last_word", "self_participant"),
    ("discussion_map", "group"),
    ("talk_moves_observer", "observer"),
    ("jigsaw_expert", "self_participant"),
    ("reciprocal_reading", "group"),
    ("collaborative_annotation", "group"),
    ("gallery_walk", "self_participant"),
    ("see_think_wonder", "self_participant"),
    ("group_kwl", "group"),
    ("venn_comparison", "group"),
    ("comparison_matrix", "group"),
    ("concept_map", "group"),
    ("decision_matrix", "group"),
    ("group_roles", "group"),
    ("team_contract", "group"),
    ("project_plan", "group"),
    ("project_check_in", "group"),
    ("peer_review_writing", "explicit_peer_subject"),
    ("peer_review_presentation", "explicit_peer_subject"),
    ("peer_design_code_review", "explicit_peer_subject"),
    ("lab_investigation", "group"),
    ("claim_evidence_reasoning", "group"),
    ("collaborative_problem_solving", "group"),
    ("collaborative_work_reflection", "self_participant"),
    ("team_health_check", "self_participant"),
)


def _provenance() -> Provenance:
    return Provenance(
        actor=ActorReference(
            actor_kind="authorized_adult",
            actor_id="teacher-1",
            owning_system="concord",
        ),
        timestamp="2026-09-20T02:00:00+00:00",
        source_kind="imported",
        application_version="0.3.0",
        note="Synthetic issue #113 exhaustive starter semantic audit.",
    )


def test_all_30_starters_are_classified_exactly_once() -> None:
    entries = list_starter_templates()
    audited_keys = tuple(key for key, _ in STARTER_RELATIONSHIP_AUDIT)

    assert len(STARTER_RELATIONSHIP_AUDIT) == 30
    assert len(set(audited_keys)) == 30
    assert audited_keys == tuple(item.starter_key for item in entries)

    classifications = tuple(kind for _, kind in STARTER_RELATIONSHIP_AUDIT)
    assert classifications.count("self_participant") == 9
    assert classifications.count("group") == 16
    assert classifications.count("observer") == 2
    assert classifications.count("explicit_peer_subject") == 3


def test_audit_matches_exact_package_current_relationship_semantics() -> None:
    by_key = {item.starter_key: item for item in list_starter_templates()}
    affected = {
        key
        for key, classification in STARTER_RELATIONSHIP_AUDIT
        if classification in {"observer", "explicit_peer_subject"}
    }
    assert affected == set(RELATIONSHIP_AWARE_STARTER_KEYS)

    for starter_key, classification in STARTER_RELATIONSHIP_AUDIT:
        lineage = build_starter_template_lineage(
            by_key[starter_key],
            created_provenance=_provenance(),
        )
        current = lineage.current_version.version
        authorship = current.default_authorship_expectation
        subject = current.default_subject_expectation

        assert authorship is not None
        if classification == "self_participant":
            assert len(lineage.versions) == 1
            assert authorship.authorship_mode == "individual_author"
            assert isinstance(subject, TemplateSubjectExpectation)
            assert subject.subject_kind == "core_student"
        elif classification == "group":
            assert len(lineage.versions) == 1
            assert authorship.authorship_mode == "collective_group_author"
            assert isinstance(subject, TemplateSubjectExpectation)
            assert subject.subject_kind == "concord_group"
        elif classification == "observer":
            assert len(lineage.versions) == 2
            assert authorship.authorship_mode == "observer"
            assert isinstance(subject, TemplateSubjectResolutionExpectation)
            assert subject.subject_kinds == ("concord_session",)
            assert subject.resolution_mode == "session"
            assert subject.subject_role == "session_context"
        else:
            assert classification == "explicit_peer_subject"
            assert len(lineage.versions) == 2
            assert authorship.authorship_mode == "individual_author"
            assert isinstance(subject, TemplateSubjectResolutionExpectation)
            assert subject.resolution_mode == "explicit"
            assert subject.subject_role == "reviewed_subject"
            assert subject.allow_target_subject_match is False


def test_socratic_seminar_remains_self_prep_and_reflection() -> None:
    classification = dict(STARTER_RELATIONSHIP_AUDIT)["socratic_seminar"]
    assert classification == "self_participant"

    entry = next(
        item
        for item in list_starter_templates()
        if item.starter_key == "socratic_seminar"
    )
    lineage = build_starter_template_lineage(
        entry,
        created_provenance=_provenance(),
    )
    assert len(lineage.versions) == 1
    subject = lineage.current_version.version.default_subject_expectation
    assert isinstance(subject, TemplateSubjectExpectation)
    assert subject.subject_kind == "core_student"
