"""#149 Slice 3: source-backed, read-only before-class facts.

Every record is synthetic. No Core roster, student file or scan is opened.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import concord.workflows.activity_lesson_readiness as lesson
from concord.workflows.errors import ConcordWorkflowValidationError


def _context(
    *,
    plans: tuple[object, ...] = (),
    packets: tuple[object, ...] = (),
    artifacts: tuple[object, ...] = (),
    pages: tuple[object, ...] = (),
    scans: tuple[object, ...] = (),
) -> SimpleNamespace:
    return SimpleNamespace(
        root=Path("synthetic-no-workspace-access"),
        work=SimpleNamespace(class_id="class-1", work_id="activity-1"),
        snapshot_revision=17,
        graph=SimpleNamespace(
            group_plans=plans,
            packet_instances=packets,
            artifact_instances=artifacts,
            artifact_pages=pages,
            scan_references=scans,
        ),
    )


def _artifact(
    id: str,
    *,
    expected: str = "returned_expected",
    status: str = "generated",
) -> SimpleNamespace:
    return SimpleNamespace(
        artifact_instance_id=id,
        activity_id="activity-1",
        page_ids=(f"page-{id}",),
        expected_return_status=expected,
        artifact_status=status,
    )


def test_applied_six_cluster_grouping_is_ready_with_optional_alternative(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        lesson, "_current_applied_plan_is_operational", lambda _ctx: True
    )
    plans = (
        SimpleNamespace(status="applied", proposed_groups=tuple(range(6))),
        SimpleNamespace(status="draft"),
    )
    context = _context(
        plans=plans,
        packets=tuple(SimpleNamespace(generation_status="generated") for _ in range(6)),
        artifacts=tuple(_artifact(f"blank-{i}") for i in range(6)),
    )
    result = lesson.inspect_lesson_readiness_from_context(context)
    assert result.plan_stage == "current_operational"
    assert result.operational_group_count == 6
    assert result.unused_proposal_count == 1
    assert result.pending_proposal_count == 0
    assert result.generated_packet_count == 6
    assert result.routed_return_artifact_count == 0
    assert result.expected_without_routed_return_count == 6
    assert result.snapshot_revision == 17


def test_applied_marker_without_current_roster_requires_inspection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        lesson, "_current_applied_plan_is_operational", lambda _ctx: False
    )
    context = _context(
        plans=(
            SimpleNamespace(status="applied", proposed_groups=tuple(range(6))),
            SimpleNamespace(status="draft"),
        )
    )
    result = lesson.inspect_lesson_readiness_from_context(context)
    assert result.plan_stage == "applied_needs_inspection"
    assert result.operational_group_count == 0
    assert result.unused_proposal_count == 0
    assert result.pending_proposal_count == 1


def test_pending_and_recovery_statuses_are_distinct() -> None:
    context = _context(
        packets=tuple(
            SimpleNamespace(generation_status=status)
            for status in (
                "planned",
                "rendering",
                "routes_pending",
                "failed",
                "generated",
                "cancelled",
            )
        )
    )
    report = lesson.inspect_lesson_readiness_from_context(context)
    assert report.plan_stage == "no_plan"
    assert report.pending_packet_count == 2
    assert report.recovery_packet_count == 2
    assert report.generated_packet_count == 1


def test_routed_return_uses_matching_page_not_artifact_status() -> None:
    a = _artifact("a", status="generated")
    b = _artifact("b", status="returned")
    page = SimpleNamespace(
        artifact_instance_id="a",
        artifact_page_id="page-a",
        return_expected=True,
        route_id="route-a",
    )
    scan = SimpleNamespace(
        artifact_page_id="page-a", activity_id="activity-1", route_id="route-a"
    )
    report = lesson.inspect_lesson_readiness_from_context(
        _context(artifacts=(a, b), pages=(page,), scans=(scan,))
    )
    assert report.routed_return_artifact_count == 1
    # 'returned' without a canonical routed page proves no returned source here.
    assert report.expected_without_routed_return_count == 1


def test_optional_return_is_not_a_required_missing_return() -> None:
    report = lesson.inspect_lesson_readiness_from_context(
        _context(
            artifacts=(
                _artifact("optional", expected="returned_optional"),
                _artifact("not-expected", expected="return_not_expected"),
                _artifact("cancelled", status="cancelled"),
            )
        )
    )
    assert report.optional_return_artifact_count == 1
    assert report.expected_without_routed_return_count == 0
    assert report.routed_return_artifact_count == 0


def test_foreign_scan_route_is_not_silently_accepted() -> None:
    artifact = _artifact("a")
    page = SimpleNamespace(
        artifact_instance_id="a",
        artifact_page_id="page-a",
        return_expected=True,
        route_id="route-a",
    )
    contradictory = SimpleNamespace(
        artifact_page_id="page-a", activity_id="activity-1", route_id="route-other"
    )
    with pytest.raises(ConcordWorkflowValidationError):
        lesson.inspect_lesson_readiness_from_context(
            _context(artifacts=(artifact,), pages=(page,), scans=(contradictory,))
        )
