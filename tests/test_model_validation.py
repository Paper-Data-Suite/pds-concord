from __future__ import annotations

from pds_core.routing_models import ModuleRecordRef

from concord.model_validation import ConcordRecordGraph, collect_record_graph_issues
from concord.models import Activity, ActorReference, Group, Provenance, Session


def _provenance() -> Provenance:
    return Provenance(
        actor=ActorReference(
            actor_kind="authorized_adult",
            actor_id="actor-1",
            owning_system="core",
        ),
        timestamp="2026-08-04T12:00:00-04:00",
        source_kind="manual",
    )


def _activity(activity_id: str = "activity-1") -> Activity:
    return Activity(
        activity_id=activity_id,
        class_reference=ModuleRecordRef(
            module_id="core", record_kind="class", record_id="class-1"
        ),
        title="Synthetic activity",
        activity_type="local:seminar",
        scoring_orientation="evidence_only",
        status="active",
        created_provenance=_provenance(),
    )


def test_valid_activity_session_graph() -> None:
    graph = ConcordRecordGraph(
        activities=(_activity(),),
        sessions=(
            Session(
                session_id="session-1",
                activity_id="activity-1",
                sequence=1,
                status="active",
                created_provenance=_provenance(),
            ),
        ),
    )
    assert collect_record_graph_issues(graph) == ()


def test_diagnostics_are_stable_and_sorted() -> None:
    graph = ConcordRecordGraph(activities=(_activity(),))
    issues = collect_record_graph_issues(graph)
    assert tuple(issue.code for issue in issues) == ("activity.session.required",)


def test_duplicate_session_sequence_and_group_cycle() -> None:
    sessions = tuple(
        Session(
            session_id=f"session-{index}",
            activity_id="activity-1",
            sequence=1,
            status="active",
            created_provenance=_provenance(),
        )
        for index in (1, 2)
    )
    groups = (
        Group(
            group_id="group-1",
            activity_id="activity-1",
            label="Group one",
            parent_group_id="group-2",
            status="active",
            created_provenance=_provenance(),
        ),
        Group(
            group_id="group-2",
            activity_id="activity-1",
            label="Group two",
            parent_group_id="group-1",
            status="active",
            created_provenance=_provenance(),
        ),
    )
    codes = {
        issue.code
        for issue in collect_record_graph_issues(
            ConcordRecordGraph(
                activities=(_activity(),), sessions=sessions, groups=groups
            )
        )
    }
    assert "session.sequence.duplicate" in codes
    assert "group.parent.cycle" in codes
