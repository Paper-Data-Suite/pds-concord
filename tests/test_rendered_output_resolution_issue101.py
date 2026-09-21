from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.classes import write_class_roster
from pds_core.local_open import LocalOpenError
from pds_core.rosters import create_roster
from pds_core.routing_models import ModuleWorkRef
from pds_core.workspace import ensure_workspace_root

from concord.models import (
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
    ConcordWorkflowOpenError,
    CreateActivityContextRequest,
    CreateGroupWithMembersRequest,
    GroupMemberSpec,
    PreparePacketInstantiationRequest,
    PrepareStarterTemplateInstallRequest,
    RenderPacketInstanceRequest,
    ResolvedRenderedPacketOutput,
    WorkflowActor,
    commit_packet_instantiation,
    commit_starter_template_install,
    create_activity_context,
    create_group_with_members,
    open_rendered_packet_output,
    open_rendered_packet_output_directory,
    prepare_packet_instantiation,
    prepare_starter_template_install,
    render_packet_instance,
    resolve_rendered_packet_output,
)
from concord.workflows.context import provenance
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowNotFoundError,
    ConcordWorkflowValidationError,
)
from concord.workflows.rendered_output import _safe_rendered_packet_path


def _clock() -> datetime:
    return datetime(2026, 9, 21, 4, 30, tzinfo=timezone.utc)


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
    activity = create_activity_context(
        CreateActivityContextRequest(
            class_id="class-1",
            activity_id="activity-1",
            title="Issue 101 Output Resolution",
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
            expected_snapshot_revision=activity.commit.snapshot_revision,
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


def _installed_packet(root: Path):
    entry = next(
        item
        for item in list_starter_templates()
        if item.orientation == "landscape"
        and "group" in item.suggested_audience_kinds
        and (
            not item.suggested_activity_type_keys
            or "project" in item.suggested_activity_type_keys
        )
    )
    installed = commit_starter_template_install(
        prepare_starter_template_install(
            PrepareStarterTemplateInstallRequest(
                starter_key=entry.starter_key,
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
        name="Issue 101 Packet",
        purpose="Exercise exact read-only rendered-output resolution.",
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
                packet_component_id="component-1",
                sequence=1,
                component_kind="concord_template",
                template_id=installed.template_id,
                template_version_id=installed.template_version_id,
                copies_per_target=1,
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
    prepared = prepare_packet_instantiation(
        PreparePacketInstantiationRequest(
            class_id="class-1",
            activity_id="activity-1",
            session_id="session-1",
            packet_definition_id=definition.packet_definition_id,
            packet_version_id=version.packet_version_id,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=_clock,
    )
    return commit_packet_instantiation(
        prepared,
        workspace_root=root,
        clock=_clock,
    )


def _rendered_packet(root: Path):
    committed = _installed_packet(root)
    packet_id = committed.packet_instance_ids[0]
    rendered = render_packet_instance(
        RenderPacketInstanceRequest(
            class_id="class-1",
            activity_id="activity-1",
            packet_instance_id=packet_id,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    return packet_id, rendered


def test_resolve_rendered_packet_output_verifies_exact_pdf_without_mutation(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    packet_id, rendered = _rendered_packet(root)
    work = ModuleWorkRef("concord", "class-1", "activity-1")
    before = load_current_record_graph(root, work)
    before_bytes = rendered.output_path.read_bytes()

    resolved = resolve_rendered_packet_output(
        "class-1",
        "activity-1",
        packet_id,
        workspace_root=root,
    )

    assert isinstance(resolved, ResolvedRenderedPacketOutput)
    assert resolved.work == work
    assert resolved.packet_instance_id == packet_id
    assert resolved.generation_id == rendered.generation_id
    assert resolved.output_path == rendered.output_path
    assert resolved.output_directory == rendered.output_path.parent
    assert resolved.output_sha256 == rendered.output_sha256
    assert resolved.page_count == rendered.page_count
    assert resolved.route_count == rendered.route_count
    assert resolved.output_path.read_bytes() == before_bytes

    after = load_current_record_graph(root, work)
    assert after.snapshot_revision == before.snapshot_revision
    assert after.snapshot_sha256 == before.snapshot_sha256


def test_resolve_rendered_packet_output_rejects_packet_not_yet_generated(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    committed = _installed_packet(root)
    packet_id = committed.packet_instance_ids[0]

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="not ready to open.*Render / reprint",
    ):
        resolve_rendered_packet_output(
            "class-1",
            "activity-1",
            packet_id,
            workspace_root=root,
        )

    expected = (
        root
        / "classes"
        / "class-1"
        / "modules"
        / "concord"
        / "work"
        / "activity-1"
        / "rendered"
        / "packets"
        / f"{packet_id}.pdf"
    )
    assert not expected.exists()


def test_resolve_rendered_packet_output_missing_file_fails_without_repair(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    packet_id, rendered = _rendered_packet(root)
    work = ModuleWorkRef("concord", "class-1", "activity-1")
    before = load_current_record_graph(root, work)
    rendered.output_path.unlink()

    with pytest.raises(
        ConcordWorkflowNotFoundError,
        match="rendered Packet is missing.*Render / reprint",
    ):
        resolve_rendered_packet_output(
            "class-1",
            "activity-1",
            packet_id,
            workspace_root=root,
        )

    assert not rendered.output_path.exists()
    after = load_current_record_graph(root, work)
    assert after.snapshot_revision == before.snapshot_revision
    assert after.snapshot_sha256 == before.snapshot_sha256


def test_resolve_rendered_packet_output_rejects_tampered_bytes(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    packet_id, rendered = _rendered_packet(root)
    work = ModuleWorkRef("concord", "class-1", "activity-1")
    before = load_current_record_graph(root, work)
    rendered.output_path.write_bytes(b"tampered rendered output")

    with pytest.raises(
        ConcordWorkflowConflictError,
        match="does not match Concord's recorded output",
    ):
        resolve_rendered_packet_output(
            "class-1",
            "activity-1",
            packet_id,
            workspace_root=root,
        )

    assert rendered.output_path.read_bytes() == b"tampered rendered output"
    after = load_current_record_graph(root, work)
    assert after.snapshot_revision == before.snapshot_revision
    assert after.snapshot_sha256 == before.snapshot_sha256


def test_rendered_packet_path_rejects_escape_and_non_pdf(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    work = ModuleWorkRef("concord", "class-1", "activity-1")

    with pytest.raises(ConcordWorkflowValidationError, match="safe Concord"):
        _safe_rendered_packet_path(root, work, "rendered/packets/../escape.pdf")
    with pytest.raises(
        ConcordWorkflowValidationError,
        match="beneath rendered/packets",
    ):
        _safe_rendered_packet_path(root, work, "rendered/other/output.pdf")
    with pytest.raises(ConcordWorkflowValidationError, match="must be a PDF"):
        _safe_rendered_packet_path(root, work, "rendered/packets/output.txt")


def test_resolve_rendered_packet_output_rejects_symlinked_pdf(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    packet_id, rendered = _rendered_packet(root)
    original_bytes = rendered.output_path.read_bytes()
    backing = rendered.output_path.with_name("backing.pdf")
    backing.write_bytes(original_bytes)
    rendered.output_path.unlink()
    try:
        rendered.output_path.symlink_to(backing.name)
    except OSError as error:
        pytest.skip(f"filesystem cannot create output symlink: {error}")

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="symbolic link or junction",
    ):
        resolve_rendered_packet_output(
            "class-1",
            "activity-1",
            packet_id,
            workspace_root=root,
        )


def test_open_rendered_packet_output_delegates_only_after_verification(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _workspace(tmp_path)
    packet_id, rendered = _rendered_packet(root)
    work = ModuleWorkRef("concord", "class-1", "activity-1")
    before = load_current_record_graph(root, work)
    opened: list[Path] = []

    def _open(path: str | Path) -> Path:
        resolved = Path(path).resolve(strict=False)
        opened.append(resolved)
        return resolved

    monkeypatch.setattr(
        "concord.workflows.rendered_output.open_local_path",
        _open,
    )

    resolved = open_rendered_packet_output(
        "class-1",
        "activity-1",
        packet_id,
        workspace_root=root,
    )

    assert resolved.output_path == rendered.output_path
    assert opened == [rendered.output_path.resolve(strict=False)]
    after = load_current_record_graph(root, work)
    assert after.snapshot_revision == before.snapshot_revision
    assert after.snapshot_sha256 == before.snapshot_sha256


def test_open_rendered_packet_output_translates_core_open_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _workspace(tmp_path)
    packet_id, _ = _rendered_packet(root)
    work = ModuleWorkRef("concord", "class-1", "activity-1")
    before = load_current_record_graph(root, work)

    def _fail_open(path: str | Path) -> Path:
        del path
        raise LocalOpenError("synthetic local viewer failure")

    monkeypatch.setattr(
        "concord.workflows.rendered_output.open_local_path",
        _fail_open,
    )

    with pytest.raises(
        ConcordWorkflowOpenError,
        match="verified the rendered Packet.*default application",
    ) as caught:
        open_rendered_packet_output(
            "class-1",
            "activity-1",
            packet_id,
            workspace_root=root,
        )

    assert isinstance(caught.value.__cause__, LocalOpenError)
    after = load_current_record_graph(root, work)
    assert after.snapshot_revision == before.snapshot_revision
    assert after.snapshot_sha256 == before.snapshot_sha256


def test_open_rendered_packet_output_directory_uses_verified_existing_folder(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _workspace(tmp_path)
    packet_id, rendered = _rendered_packet(root)
    work = ModuleWorkRef("concord", "class-1", "activity-1")
    before = load_current_record_graph(root, work)
    opened: list[Path] = []

    def _open(path: str | Path) -> Path:
        resolved = Path(path).resolve(strict=False)
        opened.append(resolved)
        return resolved

    monkeypatch.setattr(
        "concord.workflows.rendered_output.open_local_path",
        _open,
    )

    resolved = open_rendered_packet_output_directory(
        "class-1",
        "activity-1",
        packet_id,
        workspace_root=root,
    )

    assert resolved.output_directory == rendered.output_path.parent
    assert opened == [rendered.output_path.parent.resolve(strict=False)]
    after = load_current_record_graph(root, work)
    assert after.snapshot_revision == before.snapshot_revision
    assert after.snapshot_sha256 == before.snapshot_sha256


def test_open_rendered_packet_output_never_delegates_tampered_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _workspace(tmp_path)
    packet_id, rendered = _rendered_packet(root)
    opened: list[Path] = []

    def _open(path: str | Path) -> Path:
        resolved = Path(path).resolve(strict=False)
        opened.append(resolved)
        return resolved

    monkeypatch.setattr(
        "concord.workflows.rendered_output.open_local_path",
        _open,
    )
    rendered.output_path.write_bytes(b"tampered before local open")

    with pytest.raises(
        ConcordWorkflowConflictError,
        match="does not match Concord's recorded output",
    ):
        open_rendered_packet_output(
            "class-1",
            "activity-1",
            packet_id,
            workspace_root=root,
        )

    assert opened == []


def test_open_rendered_packet_output_directory_does_not_create_missing_folder(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _workspace(tmp_path)
    packet_id, rendered = _rendered_packet(root)
    opened: list[Path] = []
    packet_dir = rendered.output_path.parent
    rendered.output_path.unlink()
    packet_dir.rmdir()

    def _open(path: str | Path) -> Path:
        resolved = Path(path).resolve(strict=False)
        opened.append(resolved)
        return resolved

    monkeypatch.setattr(
        "concord.workflows.rendered_output.open_local_path",
        _open,
    )

    with pytest.raises(
        ConcordWorkflowNotFoundError,
        match="rendered Packet is missing.*Render / reprint",
    ):
        open_rendered_packet_output_directory(
            "class-1",
            "activity-1",
            packet_id,
            workspace_root=root,
        )

    assert not packet_dir.exists()
    assert opened == []
