from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.route_registrations import load_route_registration
from pds_core.routing_models import ModuleWorkRef, RouteRegistration
from pds_core.workspace import ensure_workspace_root

import concord.routing.candidates as candidate_module
from concord.models import PrivacyPolicy
from concord.routing.candidates import list_activity_route_candidates
from concord.workflows.activity import create_activity_context
from concord.workflows.artifact_page import (
    ArtifactPagePlan,
    PrepareArtifactPagesRequest,
    prepare_artifact_pages,
)
from concord.workflows.models import CreateActivityContextRequest, WorkflowActor


def _workspace(tmp_path: Path) -> Path:
    root = ensure_workspace_root(tmp_path / "workspace")
    metadata = create_class_metadata(
        "class-1",
        "2026-2027",
        created_at=datetime(2026, 10, 4, tzinfo=timezone.utc),
    )
    write_class_metadata_for_class(root, metadata)
    return root


def _prepare_two_routes(root: Path) -> ModuleWorkRef:
    actor = WorkflowActor(actor_id="teacher-1")
    activity = create_activity_context(
        CreateActivityContextRequest(
            class_id="class-1",
            activity_id="activity-1",
            title="Routing Review Activity",
            activity_type="project",
            scoring_orientation="evidence_only",
            session_id="session-1",
            actor=actor,
        ),
        workspace_root=root,
    )
    first = prepare_artifact_pages(
        PrepareArtifactPagesRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-a",
            template_version_id="template-1",
            artifact_category="student_work",
            expected_snapshot_revision=activity.commit.snapshot_revision,
            actor=actor,
            pages=(ArtifactPagePlan(page_number=1, artifact_page_id="page-a"),),
            privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
            session_id="session-1",
        ),
        workspace_root=root,
    )
    prepare_artifact_pages(
        PrepareArtifactPagesRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-b",
            template_version_id="template-1",
            artifact_category="observation",
            expected_snapshot_revision=first.commit.snapshot_revision,
            actor=actor,
            pages=(ArtifactPagePlan(page_number=1, artifact_page_id="page-b"),),
            privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
            session_id="session-1",
        ),
        workspace_root=root,
    )
    return ModuleWorkRef("concord", "class-1", "activity-1")


def _fingerprint(root: Path) -> tuple[tuple[str, str], ...]:
    values: list[tuple[str, str]] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        values.append(
            (
                path.relative_to(root).as_posix(),
                hashlib.sha256(path.read_bytes()).hexdigest(),
            )
        )
    return tuple(values)


def test_candidate_projection_loads_one_activity_graph_and_is_zero_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _workspace(tmp_path)
    work = _prepare_two_routes(root)
    before = _fingerprint(root)
    original = candidate_module.load_activity_read_context
    calls = 0

    def counted(*args: Any, **kwargs: Any) -> Any:
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(candidate_module, "load_activity_read_context", counted)
    projected = list_activity_route_candidates(work, workspace_root=root)

    assert calls == 1
    assert _fingerprint(root) == before
    assert projected.work == work
    assert projected.activity_title == "Routing Review Activity"
    assert projected.diagnostics == ()
    assert {item.artifact_page_id for item in projected.candidates} == {
        "page-a",
        "page-b",
    }
    assert all(item.locator.work == work for item in projected.candidates)
    assert all(item.session_id == "session-1" for item in projected.candidates)
    assert all(item.replayed_occurrence is False for item in projected.candidates)


def test_candidate_is_bound_to_loaded_registration_not_display_text(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    work = _prepare_two_routes(root)
    projected = list_activity_route_candidates(work, workspace_root=root)

    for candidate in projected.candidates:
        registration = load_route_registration(root, candidate.locator)
        assert registration.locator == candidate.locator
        assert registration.target.record_id == candidate.artifact_page_id
        assert registration.module_details["artifact_instance_id"] == (
            candidate.artifact_instance_id
        )
        assert registration.module_details["page_number"] == candidate.page_number
        assert registration.human_fallback == candidate.human_fallback


def test_contradictory_registration_is_diagnostic_not_candidate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _workspace(tmp_path)
    work = _prepare_two_routes(root)
    original = candidate_module.load_route_registration
    poisoned = False

    def load_with_one_bad_page(*args: Any, **kwargs: Any) -> RouteRegistration:
        nonlocal poisoned
        registration = original(*args, **kwargs)
        if not poisoned:
            poisoned = True
            details = registration.module_details
            details["page_number"] = int(details["page_number"]) + 9
            return RouteRegistration(
                schema_version=registration.schema_version,
                locator=registration.locator,
                target=registration.target,
                created_at=registration.created_at,
                status=registration.status,
                human_fallback=registration.human_fallback,
                module_details=details,
            )
        return registration

    monkeypatch.setattr(
        candidate_module,
        "load_route_registration",
        load_with_one_bad_page,
    )
    projected = list_activity_route_candidates(work, workspace_root=root)

    assert len(projected.candidates) == 1
    assert len(projected.diagnostics) == 1
    assert projected.diagnostics[0].reason == "route_inconsistent_or_ineligible"
    assert "page number" in projected.diagnostics[0].detail.lower()


def test_human_fallback_contradiction_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _workspace(tmp_path)
    work = _prepare_two_routes(root)
    original = candidate_module.load_route_registration
    poisoned = False

    def load_with_bad_fallback(*args: Any, **kwargs: Any) -> RouteRegistration:
        nonlocal poisoned
        registration = original(*args, **kwargs)
        if not poisoned:
            poisoned = True
            return RouteRegistration(
                schema_version=registration.schema_version,
                locator=registration.locator,
                target=registration.target,
                created_at=registration.created_at,
                status=registration.status,
                human_fallback="Contradictory physical fallback",
                module_details=registration.module_details,
            )
        return registration

    monkeypatch.setattr(
        candidate_module,
        "load_route_registration",
        load_with_bad_fallback,
    )
    projected = list_activity_route_candidates(work, workspace_root=root)

    assert len(projected.candidates) == 1
    assert len(projected.diagnostics) == 1
    assert "fallback" in projected.diagnostics[0].detail.lower()
