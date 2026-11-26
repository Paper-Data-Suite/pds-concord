from __future__ import annotations

from datetime import date, datetime, timedelta, timezone, tzinfo
from pathlib import Path

import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.classes import write_class_roster
from pds_core.pds2 import parse_pds2_payload
from pds_core.rosters import create_roster
from pds_core.route_registrations import load_route_registration
from pds_core.routing_models import ModuleWorkRef
from pds_core.workspace import ensure_workspace_root

import concord.workflows.packet_instantiation as preparation_module
import concord.workflows.packet_instantiation_commit as commit_module
from concord.menu_teacher_history import teacher_planned_date
from concord.model_conversion import record_to_dict
from concord.models import (
    ConcordRecordReference,
    EffectiveContext,
    PacketAudienceIntent,
    PacketComponent,
    PacketDefinition,
    PacketRenderingRules,
    PacketVersion,
)
from concord.packet_storage import create_packet_library
from concord.starter_templates.catalog import list_starter_templates
from concord.storage import load_current_record_graph
from concord.workflows import (
    ConcordWorkflowConflictError,
    ConcordWorkflowValidationError,
    CreateActivityContextRequest,
    CreateGroupWithMembersRequest,
    GroupMemberSpec,
    PacketInstantiationPartialSuccessError,
    PreparePacketInstantiationRequest,
    PrepareStarterTemplateInstallRequest,
    UpdateGroupRequest,
    WorkflowActor,
    commit_packet_instantiation,
    commit_starter_template_install,
    create_activity_context,
    create_group_with_members,
    prepare_packet_instantiation,
    prepare_starter_template_install,
    resume_packet_instantiation,
    update_group,
)
from concord.workflows.context import provenance


def _clock() -> datetime:
    return datetime(2026, 8, 25, 19, 15, tzinfo=timezone.utc)


def _actor() -> WorkflowActor:
    return WorkflowActor(
        actor_id="teacher-1",
        display_label="Synthetic Teacher",
        role_label="teacher",
    )


def _context() -> EffectiveContext:
    return EffectiveContext(
        activity_id="activity-1",
        session_ids=("session-1",),
    )


def _workspace(tmp_path: Path) -> Path:
    root = ensure_workspace_root(tmp_path / "workspace")
    write_class_metadata_for_class(
        root,
        create_class_metadata("class-1", "2026-2027", created_at=_clock()),
    )
    write_class_roster(
        root,
        create_roster(
            "class-1",
            (
                {
                    "student_id": "student-1",
                    "last_name": "One",
                    "first_name": "Alex",
                    "period": "1",
                },
            ),
        ),
    )
    created = create_activity_context(
        CreateActivityContextRequest(
            class_id="class-1",
            activity_id="activity-1",
            title="Synthetic Packet Activity",
            activity_type="project",
            scoring_orientation="evidence_only",
            session_id="session-1",
            actor=_actor(),
            activity_status="active",
            session_status="active",
            session_label="Session One",
        ),
        workspace_root=root,
        clock=_clock,
    )
    create_group_with_members(
        CreateGroupWithMembersRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_id="group-a",
            label="Group A",
            expected_snapshot_revision=created.commit.snapshot_revision,
            actor=_actor(),
            status="active",
            effective_context=_context(),
            members=(
                GroupMemberSpec(
                    membership_id="membership-1",
                    student_id="student-1",
                    effective_context=_context(),
                ),
            ),
        ),
        workspace_root=root,
        clock=_clock,
    )
    return root


def _group_starter_key() -> str:
    created = provenance(_actor(), clock=_clock, source_kind="imported")
    for entry in list_starter_templates():
        _, version = entry.build_template_records(
            created_provenance=created,
            status="active",
        )
        if "group" not in version.compatibility.audience_kinds:
            continue
        if (
            version.compatibility.activity_type_keys
            and "project" not in version.compatibility.activity_type_keys
        ):
            continue
        if (
            version.compatibility.scoring_orientations
            and "evidence_only" not in version.compatibility.scoring_orientations
        ):
            continue
        return entry.starter_key
    raise AssertionError("no compatible group starter Template found")


def _install_and_packet(root: Path) -> None:
    starter = commit_starter_template_install(
        prepare_starter_template_install(
            PrepareStarterTemplateInstallRequest(
                starter_key=_group_starter_key(),
                actor=_actor(),
            ),
            workspace_root=root,
            clock=_clock,
        ),
        workspace_root=root,
    )
    created = provenance(_actor(), clock=_clock, source_kind="manual")
    definition = PacketDefinition(
        packet_definition_id="packet-1",
        name="Synthetic Packet",
        purpose="Exercise durable Packet instantiation.",
        status="active",
        created_provenance=created,
    )
    version = PacketVersion(
        packet_version_id="packet-version-1",
        packet_definition_id=definition.packet_definition_id,
        version_label="v1",
        revision_sequence=1,
        components=(
            PacketComponent(
                packet_component_id="component-group",
                sequence=1,
                component_kind="concord_template",
                template_id=starter.template_id,
                template_version_id=starter.template_version_id,
                copies_per_target=2,
                audience_intent=PacketAudienceIntent(audience_kind="group"),
                requirement_level="required",
            ),
        ),
        rendering_rules=PacketRenderingRules(),
        created_provenance=created,
        status="active",
    )
    create_packet_library(
        root,
        definition=definition,
        initial_version=version,
    )


def _prepared(root: Path):
    return prepare_packet_instantiation(
        PreparePacketInstantiationRequest(
            class_id="class-1",
            activity_id="activity-1",
            session_id="session-1",
            packet_definition_id="packet-1",
            packet_version_id="packet-version-1",
            actor=_actor(),
        ),
        workspace_root=root,
        clock=_clock,
    )


def test_commit_publishes_one_native_generation_then_reconciles_routes(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    _install_and_packet(root)
    prepared = _prepared(root)
    result = commit_packet_instantiation(
        prepared,
        workspace_root=root,
        clock=_clock,
    )

    assert not result.replayed
    assert result.routes_verified == result.routes_expected
    assert result.routes_expected >= 2
    assert len(result.packet_instance_ids) == 1
    assert len(result.artifact_instance_ids) == 2
    assert result.lifecycle_commit is not None

    work = ModuleWorkRef("concord", "class-1", "activity-1")
    graph = load_current_record_graph(root, work).graph
    packet = graph.packet_instances[0]
    assert packet.generation_status == "rendering"
    assert packet.review_digest == prepared.review_digest
    assert packet.generation_date == "2026-08-25"
    assert len(packet.artifact_bindings) == 2
    assert all(
        binding.rendering_values for binding in packet.artifact_bindings
    )
    assert all(
        value.source_kind not in {"pds2_route_payload", "human_fallback"}
        for binding in packet.artifact_bindings
        for value in binding.rendering_values
    )

    assert len(graph.artifact_instances) == 2
    assert all(
        item.packet_instance_id == packet.packet_instance_id
        for item in graph.artifact_instances
    )
    assert graph.artifact_authors
    assert all(item.attribution_status == "proposed" for item in graph.artifact_authors)
    assert all(item.attribution_source == "system" for item in graph.artifact_authors)
    assert all(
        isinstance(item.author_reference, ConcordRecordReference)
        for item in graph.artifact_authors
    )
    assert graph.artifact_subjects
    assert all(
        item.confirmation_status == "proposed" for item in graph.artifact_subjects
    )

    for committed_page in result.pages:
        if committed_page.route_id is None:
            assert committed_page.pds2_payload is None
            continue
        assert committed_page.pds2_payload is not None
        locator = parse_pds2_payload(committed_page.pds2_payload)
        registration = load_route_registration(root, locator)
        assert registration.target.record_kind == "artifact_page"
        assert registration.target.record_id == committed_page.artifact_page_id
        page = next(
            item
            for item in graph.artifact_pages
            if item.artifact_page_id == committed_page.artifact_page_id
        )
        assert page.human_fallback == registration.human_fallback
        assert "Class: class-1" in registration.human_fallback
        assert "Student:" not in registration.human_fallback
        assert "Alex" not in registration.human_fallback
        assert set(registration.module_details) == {
            "activity_id",
            "artifact_instance_id",
            "artifact_page_id",
            "page_number",
        }
        serialized = str(registration.module_details)
        assert "packet" not in serialized
        assert "template" not in serialized
        assert "student" not in serialized

    native_packet = str(record_to_dict(packet))
    for forbidden in (
        "group_plan_id",
        "signal_set_id",
        "dimension_id",
        "target_group_size",
        "target_group_count",
    ):
        assert forbidden not in native_packet


def test_resume_is_idempotent_and_reuses_all_durable_identities(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    _install_and_packet(root)
    first = commit_packet_instantiation(
        _prepared(root),
        workspace_root=root,
        clock=_clock,
    )
    work = ModuleWorkRef("concord", "class-1", "activity-1")
    before = load_current_record_graph(root, work)

    replay = resume_packet_instantiation(
        "class-1",
        "activity-1",
        first.generation_id,
        workspace_root=root,
    )
    after = load_current_record_graph(root, work)

    assert replay.replayed
    assert replay.packet_instance_ids == first.packet_instance_ids
    assert replay.artifact_instance_ids == first.artifact_instance_ids
    assert replay.artifact_page_ids == first.artifact_page_ids
    assert replay.route_ids == first.route_ids
    assert replay.routes_verified == replay.routes_expected
    assert replay.lifecycle_commit is not None
    assert replay.lifecycle_commit.no_op
    assert after.snapshot_revision == before.snapshot_revision
    assert after.snapshot_sha256 == before.snapshot_sha256


def test_new_review_creates_fresh_generation_and_route_identities(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    _install_and_packet(root)
    first = commit_packet_instantiation(
        _prepared(root),
        workspace_root=root,
        clock=_clock,
    )
    second = commit_packet_instantiation(
        _prepared(root),
        workspace_root=root,
        clock=_clock,
    )
    assert second.generation_id != first.generation_id
    assert set(second.packet_instance_ids).isdisjoint(first.packet_instance_ids)
    assert set(second.artifact_instance_ids).isdisjoint(first.artifact_instance_ids)
    assert set(second.artifact_page_ids).isdisjoint(first.artifact_page_ids)
    assert set(second.route_ids).isdisjoint(first.route_ids)


def test_stale_preview_fails_before_native_generation_mutation(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    _install_and_packet(root)
    prepared = _prepared(root)
    updated = update_group(
        UpdateGroupRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_id="group-a",
            expected_snapshot_revision=prepared.activity_snapshot_revision,
            actor=_actor(),
            label="Changed Group A",
        ),
        workspace_root=root,
        clock=_clock,
    )
    with pytest.raises(
        ConcordWorkflowConflictError,
        match="stale",
    ):
        commit_packet_instantiation(
            prepared,
            workspace_root=root,
            clock=_clock,
        )
    graph = load_current_record_graph(root, updated.commit.work).graph
    assert graph.packet_instances == ()


def test_route_failure_is_partial_success_and_resume_reuses_native_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _workspace(tmp_path)
    _install_and_packet(root)
    prepared = _prepared(root)

    def fail_route(*args: object, **kwargs: object) -> None:
        raise RuntimeError("synthetic route failure")

    monkeypatch.setattr(
        commit_module,
        "reconcile_concord_route_registration",
        fail_route,
    )
    with pytest.raises(PacketInstantiationPartialSuccessError) as raised:
        commit_packet_instantiation(
            prepared,
            workspace_root=root,
            clock=_clock,
        )
    error = raised.value
    assert error.stage == "route_reconciliation"
    assert error.result.routes_verified == 0
    generation_id = error.result.generation_id
    page_ids = error.result.artifact_page_ids
    route_ids = error.result.route_ids

    monkeypatch.undo()
    resumed = resume_packet_instantiation(
        "class-1",
        "activity-1",
        generation_id,
        workspace_root=root,
    )
    assert resumed.artifact_page_ids == page_ids
    assert resumed.route_ids == route_ids
    assert resumed.routes_verified == resumed.routes_expected

    graph = load_current_record_graph(
        root,
        ModuleWorkRef("concord", "class-1", "activity-1"),
    ).graph
    packets = [
        item for item in graph.packet_instances if item.generation_id == generation_id
    ]
    assert packets
    assert all(item.generation_status == "rendering" for item in packets)


def test_lifecycle_failure_preserves_routes_and_is_resumable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _workspace(tmp_path)
    _install_and_packet(root)
    prepared = _prepared(root)
    real_commit = commit_module.commit_record_batch
    calls = 0

    def fail_second_commit(*args: object, **kwargs: object):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("synthetic lifecycle failure")
        return real_commit(*args, **kwargs)

    monkeypatch.setattr(commit_module, "commit_record_batch", fail_second_commit)
    with pytest.raises(PacketInstantiationPartialSuccessError) as raised:
        commit_packet_instantiation(
            prepared,
            workspace_root=root,
            clock=_clock,
        )
    error = raised.value
    assert error.stage == "lifecycle_transition"
    assert error.result.routes_verified == error.result.routes_expected
    generation_id = error.result.generation_id
    original_pages = error.result.artifact_page_ids
    original_routes = error.result.route_ids

    monkeypatch.undo()
    resumed = resume_packet_instantiation(
        "class-1",
        "activity-1",
        generation_id,
        workspace_root=root,
    )
    assert resumed.artifact_page_ids == original_pages
    assert resumed.route_ids == original_routes
    assert resumed.routes_verified == resumed.routes_expected


def _freeze_host_clock(
    monkeypatch: pytest.MonkeyPatch,
    instant: datetime,
    offset_hours: int,
) -> None:
    # Represent the host offset at the specified instant. This is portable to
    # Windows without an external IANA timezone database.
    local_zone = timezone(timedelta(hours=offset_hours))

    class FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz: tzinfo | None = None) -> datetime:
            assert tz is timezone.utc
            return cls.fromtimestamp(instant.timestamp(), tz=tz)

        def astimezone(self, tz: tzinfo | None = None) -> datetime:
            return super().astimezone(local_zone if tz is None else tz)

    monkeypatch.setattr(preparation_module, "datetime", FrozenDateTime)


@pytest.mark.parametrize(
    ("utc", "offset_hours", "expected"),
    [
        ("2026-10-20T01:00:00+00:00", -4, "2026-10-19"),
        ("2026-10-20T03:59:59+00:00", -4, "2026-10-19"),
        ("2026-10-20T04:00:00+00:00", -4, "2026-10-20"),
        ("2026-03-08T06:59:59+00:00", -5, "2026-03-08"),
        ("2026-03-08T07:00:00+00:00", -4, "2026-03-08"),
        ("2026-11-01T05:59:59+00:00", -4, "2026-11-01"),
        ("2026-11-01T06:00:00+00:00", -5, "2026-11-01"),
        ("2026-10-19T15:00:00+00:00", 9, "2026-10-20"),
    ],
    ids=[
        "ny-evening-rollover",
        "ny-before-midnight",
        "ny-midnight",
        "ny-spring-before",
        "ny-spring-after",
        "ny-fall-before",
        "ny-fall-after",
        "tokyo-midnight",
    ],
)
def test_issue153_default_generation_date_uses_host_calendar(
    monkeypatch: pytest.MonkeyPatch,
    utc: str,
    offset_hours: int,
    expected: str,
) -> None:
    _freeze_host_clock(monkeypatch, datetime.fromisoformat(utc), offset_hours)
    assert preparation_module._generation_date(None) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("2026-10-20T01:00:00+00:00", "2026-10-20"),
        ("2026-10-19T21:00:00-04:00", "2026-10-19"),
        ("2026-10-20T00:00:00+14:00", "2026-10-20"),
    ],
)
def test_issue153_explicit_clock_preserves_supplied_calendar_date(
    value: str, expected: str
) -> None:
    assert (
        preparation_module._generation_date(lambda: datetime.fromisoformat(value))
        == expected
    )


@pytest.mark.parametrize(
    "value",
    (datetime(2026, 10, 19, 21), date(2026, 10, 19)),
)
def test_issue153_invalid_clock_remains_rejected(value: object) -> None:
    with pytest.raises(ConcordWorkflowValidationError, match="workflow clock"):
        preparation_module._generation_date(lambda: value)  # type: ignore[arg-type]


def test_issue153_historical_date_only_label_is_not_reinterpreted() -> None:
    assert teacher_planned_date("2026-10-19") == "Planned Oct 19, 2026"
    assert teacher_planned_date("2026-10-20") == "Planned Oct 20, 2026"
    assert (
        teacher_planned_date("2026-10-20T01:00:00+00:00")
        == "Planned date unavailable"
    )


def test_issue153_reviewed_local_date_survives_commit_after_midnight(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _workspace(tmp_path)
    _install_and_packet(root)
    request = _prepared(root).request
    evening = datetime(2026, 10, 20, 1, tzinfo=timezone.utc)
    after_midnight = datetime(2026, 10, 20, 5, tzinfo=timezone.utc)

    with monkeypatch.context() as scoped:
        _freeze_host_clock(scoped, evening, -4)
        prepared = prepare_packet_instantiation(request, workspace_root=root)

    assert prepared.ready_for_commit
    assert prepared.generation_date == "2026-10-19"
    planned_dates = [
        item.value
        for target in prepared.target_plans
        for artifact in target.artifacts
        for item in artifact.rendering_inputs
        if item.source_kind == "current_date"
    ]
    assert planned_dates
    assert set(planned_dates) == {"2026-10-19"}

    result = commit_packet_instantiation(
        prepared,
        workspace_root=root,
        clock=lambda: after_midnight,
    )
    graph = load_current_record_graph(
        root, ModuleWorkRef("concord", "class-1", "activity-1")
    ).graph
    packet = next(
        item for item in graph.packet_instances
        if item.packet_instance_id in result.packet_instance_ids
    )
    assert packet.generation_date == prepared.generation_date
    assert packet.review_digest == prepared.review_digest
    assert packet.created_provenance.timestamp == after_midnight.isoformat()
    durable_dates = [
        item.value
        for binding in packet.artifact_bindings
        for item in binding.rendering_values
        if item.source_kind == "current_date"
    ]
    assert durable_dates == planned_dates
