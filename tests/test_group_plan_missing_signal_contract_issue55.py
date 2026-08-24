from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

import pytest
from pds_core.routing_models import ModuleRecordRef

from concord.model_conversion import record_from_dict, record_to_dict
from concord.models import (
    ActorReference,
    ConcordModelError,
    GroupPlan,
    PlannedGroup,
    Provenance,
)


def _provenance(day: int = 1) -> Provenance:
    return Provenance(
        actor=ActorReference(
            actor_kind="authorized_adult",
            actor_id="teacher-1",
            owning_system="concord",
        ),
        timestamp=datetime(
            2026,
            8,
            day,
            15,
            0,
            tzinfo=timezone.utc,
        ).isoformat(),
        source_kind="manual",
        application_version="0.3.0.dev0",
    )


def _signal_plan(*, unresolved: tuple[str, ...] = ("student-3",)) -> GroupPlan:
    assigned = tuple(
        student_id
        for student_id in ("student-1", "student-2", "student-3")
        if student_id not in unresolved
    )
    return GroupPlan(
        group_plan_id="plan-1",
        activity_id="activity-1",
        class_reference=ModuleRecordRef(
            module_id="core",
            record_kind="class",
            record_id="class-1",
        ),
        strategy="similar_signal",
        status="draft",
        roster_student_ids=("student-1", "student-2", "student-3"),
        proposed_groups=(
            PlannedGroup(
                planned_group_key="similar-1",
                label="Group 1",
                student_ids=assigned,
            ),
        ),
        unresolved_student_ids=unresolved,
        target_group_count=1,
        source_signal_set_id="signal-1",
        source_signal_set_digest="a" * 64,
        source_signal_dimension_id="writing",
        created_provenance=_provenance(),
    )


def _approved(plan: GroupPlan) -> GroupPlan:
    return replace(
        plan,
        status="approved",
        previewed_provenance=_provenance(2),
        approved_provenance=_provenance(3),
    )


@pytest.mark.parametrize("disposition", ("manual", "random", "leave_unassigned"))
def test_signal_plan_accepts_each_structured_disposition(disposition: str) -> None:
    seed = "missing-seed" if disposition == "random" else None
    plan = replace(
        _signal_plan(),
        missing_signal_disposition=disposition,
        missing_signal_random_seed=seed,
        missing_signal_disposition_provenance=_provenance(4),
    )
    assert plan.missing_signal_disposition == disposition
    assert plan.missing_signal_random_seed == seed


def test_missing_signal_disposition_round_trips_as_native_state() -> None:
    plan = replace(
        _signal_plan(),
        missing_signal_disposition="leave_unassigned",
        missing_signal_disposition_provenance=_provenance(4),
    )
    payload = record_to_dict(plan)
    restored = record_from_dict("group_plan", payload)
    assert restored == plan
    assert payload["missing_signal_disposition"] == "leave_unassigned"
    assert "missing_signal_random_seed" not in payload
    assert "missing_signal_student_ids" not in payload
    assert "student_bands" not in payload


def test_disposition_is_restricted_to_signal_strategies_and_exact_binding() -> None:
    with pytest.raises(ConcordModelError, match="signal-dependent strategies"):
        replace(
            _signal_plan(),
            strategy="manual",
            source_signal_set_id=None,
            source_signal_set_digest=None,
            source_signal_dimension_id=None,
            missing_signal_disposition="manual",
            missing_signal_disposition_provenance=_provenance(4),
        )

    with pytest.raises(ConcordModelError, match="exact signal binding"):
        replace(
            _signal_plan(),
            source_signal_set_id=None,
            source_signal_set_digest=None,
            source_signal_dimension_id=None,
            missing_signal_disposition="manual",
            missing_signal_disposition_provenance=_provenance(4),
        )


def test_disposition_and_provenance_are_all_or_none() -> None:
    with pytest.raises(ConcordModelError, match="requires disposition provenance"):
        replace(
            _signal_plan(),
            missing_signal_disposition="manual",
        )

    with pytest.raises(ConcordModelError, match="requires a disposition"):
        replace(
            _signal_plan(),
            missing_signal_disposition_provenance=_provenance(4),
        )


def test_random_disposition_has_separate_explicit_seed_contract() -> None:
    with pytest.raises(ConcordModelError, match="requires an explicit seed"):
        replace(
            _signal_plan(),
            missing_signal_disposition="random",
            missing_signal_disposition_provenance=_provenance(4),
        )

    with pytest.raises(ConcordModelError, match="allowed only for random"):
        replace(
            _signal_plan(),
            missing_signal_disposition="manual",
            missing_signal_random_seed="unexpected",
            missing_signal_disposition_provenance=_provenance(4),
        )

    with pytest.raises(ConcordModelError, match="nonempty string"):
        replace(
            _signal_plan(),
            missing_signal_disposition="random",
            missing_signal_random_seed="",
            missing_signal_disposition_provenance=_provenance(4),
        )

    plan = replace(
        _signal_plan(),
        missing_signal_disposition="random",
        missing_signal_random_seed="missing-seed",
        missing_signal_disposition_provenance=_provenance(4),
    )
    assert plan.seed is None
    assert plan.missing_signal_random_seed == "missing-seed"


def test_invalid_disposition_is_rejected() -> None:
    with pytest.raises(ConcordModelError, match="missing_signal_disposition must be"):
        replace(
            _signal_plan(),
            missing_signal_disposition="automatic",
            missing_signal_disposition_provenance=_provenance(4),
        )


def test_approved_unresolved_requires_leave_unassigned_signal_disposition() -> None:
    with pytest.raises(ConcordModelError, match="leave_unassigned"):
        _approved(_signal_plan())

    for disposition in ("manual", "random"):
        plan = replace(
            _signal_plan(),
            missing_signal_disposition=disposition,
            missing_signal_random_seed=(
                "missing-seed" if disposition == "random" else None
            ),
            missing_signal_disposition_provenance=_provenance(4),
        )
        with pytest.raises(ConcordModelError, match="leave_unassigned"):
            _approved(plan)

    leave = replace(
        _signal_plan(),
        missing_signal_disposition="leave_unassigned",
        missing_signal_disposition_provenance=_provenance(4),
    )
    approved = _approved(leave)
    assert approved.unresolved_student_ids == ("student-3",)
    assert approved.missing_signal_disposition == "leave_unassigned"


def test_applied_unresolved_preserves_same_structural_exception() -> None:
    leave = replace(
        _signal_plan(),
        missing_signal_disposition="leave_unassigned",
        missing_signal_disposition_provenance=_provenance(4),
    )
    approved = _approved(leave)
    applied = replace(
        approved,
        status="applied",
        applied_provenance=_provenance(5),
        applied_application_id="apply-1",
        applied_application_digest="a" * 64,
    )
    assert applied.unresolved_student_ids == ("student-3",)


def test_resolved_manual_and_random_dispositions_are_structurally_approvable() -> None:
    resolved = _signal_plan(unresolved=())
    for disposition in ("manual", "random"):
        plan = replace(
            resolved,
            missing_signal_disposition=disposition,
            missing_signal_random_seed=(
                "missing-seed" if disposition == "random" else None
            ),
            missing_signal_disposition_provenance=_provenance(4),
        )
        assert _approved(plan).status == "approved"
