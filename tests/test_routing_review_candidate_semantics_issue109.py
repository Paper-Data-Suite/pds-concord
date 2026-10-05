from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from pds_core.routing_models import PDS2_SCHEMA, ModuleWorkRef, RouteLocator

import concord.routing.candidates as candidate_module
from concord.models import (
    ConcordRecordReference,
    ParticipantReference,
    SubjectReference,
)
from concord.routing.candidates import (
    ConcordRouteCandidate,
    project_activity_route_candidates,
)
from concord.routing.destinations import routing_destination_candidate_label


def _candidate(**overrides: Any) -> ConcordRouteCandidate:
    values: dict[str, Any] = {
        "locator": RouteLocator(
            PDS2_SCHEMA,
            ModuleWorkRef("concord", "class-1", "activity-1"),
            "route-1",
        ),
        "activity_id": "activity-1",
        "activity_title": "Peer Review",
        "artifact_instance_id": "artifact-1",
        "artifact_page_id": "page-1",
        "page_number": 1,
        "page_kind": "primary",
        "artifact_category": "student_work",
        "human_fallback": "Reviewer: Casey C. | Reviewee: Dana D.",
        "session_id": "session-1",
        "session_label": "Workshop Day",
        "group_id": None,
        "group_label": None,
        "replayed_occurrence": False,
    }
    values.update(overrides)
    return ConcordRouteCandidate(**values)


def test_destination_label_keeps_packet_target_author_and_subject_distinct() -> None:
    candidate = _candidate(
        packet_target_kind="participant",
        packet_target_label="Alex One",
        author_labels=("Alex One",),
        subject_labels=("Blair Two",),
    )
    label = routing_destination_candidate_label(candidate)
    assert "Packet target: Alex One" in label
    assert "Author: Alex One" in label
    assert "Subject: Blair Two" in label
    assert "Physical: Reviewer: Casey C. | Reviewee: Dana D." in label
    assert "Subject: Alex One" not in label
    assert "Author: Blair Two" not in label


def test_human_fallback_is_display_only_and_does_not_create_semantics() -> None:
    candidate = _candidate(human_fallback="Student: Alex O. | Subject: Blair T.")
    label = routing_destination_candidate_label(candidate)
    assert candidate.packet_target_label is None
    assert candidate.author_labels == ()
    assert candidate.subject_labels == ()
    assert "Packet target:" not in label
    assert "Author:" not in label
    assert label.endswith("Physical: Student: Alex O. | Subject: Blair T.")


def test_group_context_remains_independent_from_relationships() -> None:
    candidate = _candidate(
        group_id="group-blue",
        group_label="Group Blue",
        packet_target_kind="group",
        packet_target_label="Group Green",
        subject_labels=("Group Red",),
    )
    label = routing_destination_candidate_label(candidate)
    assert label.startswith("Group Blue — Packet target: Group Green")
    assert "Subject: Group Red" in label


def test_projection_uses_current_typed_relationships_not_fallback_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    work = ModuleWorkRef("concord", "class-1", "activity-1")
    page = SimpleNamespace(
        artifact_instance_id="artifact-1",
        artifact_page_id="page-1",
        page_number=1,
        page_kind="primary",
        route_required=True,
        route_id="route-1",
        human_fallback="Student: Casey C. | Subject: Dana D.",
    )
    artifact = SimpleNamespace(
        artifact_instance_id="artifact-1",
        artifact_category="student_work",
        session_id="session-1",
        group_id=None,
        packet_instance_id="packet-1",
    )
    session = SimpleNamespace(session_id="session-1", label="Workshop Day")
    activity = SimpleNamespace(activity_id="activity-1", title="Peer Review")
    old_author = SimpleNamespace(
        artifact_author_id="author-old",
        artifact_instance_id="artifact-1",
        author_reference=ParticipantReference(
            participant_kind="core_student",
            participant_id="student-old",
            owning_system="core",
        ),
        attribution_status="confirmed",
        supersedes_artifact_author_id=None,
    )
    current_author = SimpleNamespace(
        artifact_author_id="author-new",
        artifact_instance_id="artifact-1",
        author_reference=ParticipantReference(
            participant_kind="core_student",
            participant_id="student-reviewer",
            owning_system="core",
        ),
        attribution_status="confirmed",
        supersedes_artifact_author_id="author-old",
    )
    current_subject = SimpleNamespace(
        artifact_subject_id="subject-current",
        artifact_instance_id="artifact-1",
        subject_reference=SubjectReference(
            subject_kind="core_student",
            subject_id="student-reviewee",
            owning_system="core",
        ),
        confirmation_status="confirmed",
        supersedes_artifact_subject_id=None,
    )
    packet = SimpleNamespace(
        packet_instance_id="packet-1",
        artifact_bindings=(SimpleNamespace(artifact_instance_id="artifact-1"),),
        target_context=SimpleNamespace(
            audience_kind="participant",
            participant_reference=ParticipantReference(
                participant_kind="core_student",
                participant_id="student-reviewer",
                owning_system="core",
            ),
            group_id=None,
            actor_reference=None,
            activity_id="activity-1",
            role_key=None,
        ),
    )
    graph = SimpleNamespace(
        artifact_instances=(artifact,),
        artifact_pages=(page,),
        sessions=(session,),
        groups=(),
        activities=(activity,),
        packet_instances=(packet,),
        artifact_authors=(old_author, current_author),
        artifact_subjects=(current_subject,),
    )
    context = SimpleNamespace(
        root=Path("workspace"),
        work=work,
        graph=graph,
        activity=activity,
        snapshot_revision=4,
        snapshot_sha256="a" * 64,
    )
    locator = RouteLocator(PDS2_SCHEMA, work, "route-1")
    labels = {
        "student-old": "Old Author",
        "student-reviewer": "Alex One",
        "student-reviewee": "Blair Two",
    }
    monkeypatch.setattr(
        candidate_module,
        "participant_display_label",
        lambda _root, _class_id, reference: labels.get(reference.participant_id),
    )
    monkeypatch.setattr(
        candidate_module,
        "load_route_registration",
        lambda _root, _locator: SimpleNamespace(locator=locator),
    )
    monkeypatch.setattr(
        candidate_module,
        "validate_concord_route_target",
        lambda *_args, **_kwargs: SimpleNamespace(
            page=page,
            replay_scan_reference=None,
        ),
    )

    candidate = project_activity_route_candidates(context).candidates[0]
    assert candidate.packet_target_kind == "participant"
    assert candidate.packet_target_label == "Alex One"
    assert candidate.author_labels == ("Alex One",)
    assert candidate.subject_labels == ("Blair Two",)
    assert "Old Author" not in candidate.author_labels
    assert "Casey C." not in candidate.author_labels
    assert "Dana D." not in candidate.subject_labels
    assert candidate.human_fallback == "Student: Casey C. | Subject: Dana D."


def test_unconfirmed_typed_relationships_are_labeled_with_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    work = ModuleWorkRef("concord", "class-1", "activity-1")
    page = SimpleNamespace(
        artifact_instance_id="artifact-1",
        artifact_page_id="page-1",
        page_number=1,
        page_kind="primary",
        route_required=True,
        route_id="route-1",
        human_fallback="Concord activity-1 page 1",
    )
    artifact = SimpleNamespace(
        artifact_instance_id="artifact-1",
        artifact_category="observation",
        session_id=None,
        group_id=None,
        packet_instance_id=None,
    )
    activity = SimpleNamespace(activity_id="activity-1", title="Observation")
    graph = SimpleNamespace(
        artifact_instances=(artifact,),
        artifact_pages=(page,),
        sessions=(),
        groups=(),
        activities=(activity,),
        packet_instances=(),
        artifact_authors=(
            SimpleNamespace(
                artifact_author_id="author-1",
                artifact_instance_id="artifact-1",
                author_reference=ConcordRecordReference(
                    record_kind="activity",
                    record_id="activity-1",
                ),
                attribution_status="proposed",
                supersedes_artifact_author_id=None,
            ),
        ),
        artifact_subjects=(
            SimpleNamespace(
                artifact_subject_id="subject-1",
                artifact_instance_id="artifact-1",
                subject_reference=SubjectReference(
                    subject_kind="concord_activity",
                    subject_id="activity-1",
                    owning_system="concord",
                ),
                confirmation_status="disputed",
                supersedes_artifact_subject_id=None,
            ),
        ),
    )
    context = SimpleNamespace(
        root=Path("workspace"),
        work=work,
        graph=graph,
        activity=activity,
        snapshot_revision=1,
        snapshot_sha256="b" * 64,
    )
    locator = RouteLocator(PDS2_SCHEMA, work, "route-1")
    monkeypatch.setattr(
        candidate_module,
        "load_route_registration",
        lambda _root, _locator: SimpleNamespace(locator=locator),
    )
    monkeypatch.setattr(
        candidate_module,
        "validate_concord_route_target",
        lambda *_args, **_kwargs: SimpleNamespace(
            page=page,
            replay_scan_reference=None,
        ),
    )

    candidate = project_activity_route_candidates(context).candidates[0]
    assert candidate.author_labels == ("Observation (proposed)",)
    assert candidate.subject_labels == ("Observation (disputed)",)
