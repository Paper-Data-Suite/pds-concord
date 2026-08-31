from __future__ import annotations

from datetime import datetime, timezone

from concord.model_conversion import record_to_dict
from concord.models import (
    ActorReference,
    EffectiveContext,
    Group,
    GroupMembership,
    ParticipantReference,
    Provenance,
)

_FORBIDDEN_PLANNING_KEYS = {
    "source_signal_set_id",
    "source_signal_set_digest",
    "source_signal_dimension_id",
    "band",
    "student_bands",
    "missing_signal_disposition",
    "missing_signal_random_seed",
    "missing_signal_disposition_provenance",
    "seed",
    "target_group_size",
    "target_group_count",
    "strategy",
    "planned_group_key",
    "applied_application_id",
    "applied_application_digest",
}


def _provenance() -> Provenance:
    return Provenance(
        actor=ActorReference(
            actor_kind="authorized_adult",
            actor_id="teacher-1",
            owning_system="concord",
        ),
        timestamp=datetime(
            2026,
            8,
            24,
            17,
            0,
            tzinfo=timezone.utc,
        ).isoformat(),
        source_kind="manual",
        application_version="0.3.0",
    )


def test_canonical_group_application_records_exclude_planning_and_signal_state(
) -> None:
    context = EffectiveContext(
        activity_id="activity-1",
        session_ids=("session-1",),
    )
    group = Group(
        group_id="group-application-test",
        activity_id="activity-1",
        label="Group 1",
        status="planned",
        created_provenance=_provenance(),
        effective_context=context,
    )
    membership = GroupMembership(
        membership_id="membership-application-test",
        group_id=group.group_id,
        participant_reference=ParticipantReference(
            participant_kind="core_student",
            participant_id="student-1",
            owning_system="core",
        ),
        effective_context=context,
        status="active",
        created_provenance=_provenance(),
    )

    for payload in (record_to_dict(group), record_to_dict(membership)):
        assert _FORBIDDEN_PLANNING_KEYS.isdisjoint(payload)
        serialized = repr(payload)
        assert "similar_signal" not in serialized
        assert "mixed_signal" not in serialized
        assert "leave_unassigned" not in serialized
        assert "meridian" not in serialized.casefold()
