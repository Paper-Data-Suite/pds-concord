"""Read-only, evidence-conservative before-class facts for one Concord Activity.

Concord owns lesson-stage facts. Core owns structural module readiness; neither
verified packet generation nor a planned Artifact proves physical distribution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeAlias

from concord.workflows.activity_attention import _current_applied_plan_is_operational
from concord.workflows.activity_read import ActivityReadContext
from concord.workflows.artifact_collection import _has_retained_return_reference

PlanStage: TypeAlias = Literal[
    "current_operational",
    "applied_needs_inspection",
    "proposals_only",
    "no_plan",
]


@dataclass(frozen=True, slots=True)
class LessonReadiness:
    """Privacy-minimal snapshot facts; never a grade or durable task."""

    snapshot_revision: int
    plan_stage: PlanStage
    operational_group_count: int
    unused_proposal_count: int
    pending_proposal_count: int
    generated_packet_count: int
    pending_packet_count: int
    recovery_packet_count: int
    routed_return_artifact_count: int
    expected_without_routed_return_count: int
    optional_return_artifact_count: int


def inspect_lesson_readiness_from_context(
    context: ActivityReadContext,
) -> LessonReadiness:
    """Project a single verified Concord graph without writes or inferred scans.

    A routed ScanReference is evidence that Concord has a record of a routed
    returned page, not that a physical source was opened and checked here.
    """
    graph = context.graph
    applied = tuple(plan for plan in graph.group_plans if plan.status == "applied")
    proposals = tuple(
        plan
        for plan in graph.group_plans
        if plan.status in {"draft", "previewed", "approved"}
    )
    if applied:
        if len(applied) == 1 and _current_applied_plan_is_operational(context):
            plan_stage: PlanStage = "current_operational"
            operational_group_count = len(applied[0].proposed_groups)
        else:
            plan_stage = "applied_needs_inspection"
            operational_group_count = 0
    elif proposals:
        plan_stage = "proposals_only"
        operational_group_count = 0
    else:
        plan_stage = "no_plan"
        operational_group_count = 0

    packets = graph.packet_instances
    generated_packets = sum(item.generation_status == "generated" for item in packets)
    pending_packets = sum(
        item.generation_status in {"planned", "rendering"} for item in packets
    )
    recovery_packets = sum(
        item.generation_status in {"routes_pending", "failed"} for item in packets
    )

    routed = 0
    expected_without_route = 0
    optional = 0
    for artifact in graph.artifact_instances:
        if artifact.artifact_status in {"cancelled", "archived", "superseded"}:
            continue
        if artifact.expected_return_status == "return_not_expected":
            continue
        has_routed_return = _has_retained_return_reference(artifact, graph, "not_ready")
        if has_routed_return:
            routed += 1
        elif artifact.expected_return_status == "returned_expected":
            expected_without_route += 1
        else:
            optional += 1

    return LessonReadiness(
        snapshot_revision=context.snapshot_revision,
        plan_stage=plan_stage,
        operational_group_count=operational_group_count,
        unused_proposal_count=len(proposals)
        if plan_stage == "current_operational"
        else 0,
        pending_proposal_count=len(proposals)
        if plan_stage != "current_operational"
        else 0,
        generated_packet_count=generated_packets,
        pending_packet_count=pending_packets,
        recovery_packet_count=recovery_packets,
        routed_return_artifact_count=routed,
        expected_without_routed_return_count=expected_without_route,
        optional_return_artifact_count=optional,
    )


__all__ = ["LessonReadiness", "PlanStage", "inspect_lesson_readiness_from_context"]
