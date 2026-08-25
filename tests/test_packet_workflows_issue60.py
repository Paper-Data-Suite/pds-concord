from __future__ import annotations

import json
from pathlib import Path

import pytest
from pds_core.routing_models import ModuleRecordRef

from concord.models import PacketAudienceIntent, PacketComponent
from concord.packet_authoring import (
    PACKET_AUTHORING_SCHEMA,
    PacketAuthoringConflictError,
    PacketAuthoringError,
    load_packet_authoring_source,
    verify_prepared_packet_source,
)
from concord.workflows import (
    PreparePacketActivationRequest,
    PreparePacketCreateRequest,
    PreparePacketRetireRequest,
    PreparePacketRetireVersionRequest,
    PreparePacketRevisionRequest,
    PreparePacketUpdateRequest,
    WorkflowActor,
    commit_packet_activation,
    commit_packet_create,
    commit_packet_retire,
    commit_packet_retire_version,
    commit_packet_revision,
    commit_packet_update,
    get_packet,
    list_packets,
    prepare_packet_activation,
    prepare_packet_create,
    prepare_packet_retire,
    prepare_packet_retire_version,
    prepare_packet_revision,
    prepare_packet_update,
)
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowValidationError,
)


def _workspace(tmp_path: Path) -> Path:
    root = tmp_path / "workspace"
    root.mkdir()
    return root


def _actor() -> WorkflowActor:
    return WorkflowActor(actor_id="teacher-1")


def _component(record_id: str = "submission-1") -> PacketComponent:
    return PacketComponent(
        packet_component_id="component-1",
        sequence=1,
        component_kind="external_component",
        external_reference=ModuleRecordRef(
            module_id="quillan",
            record_kind="submission",
            record_id=record_id,
            contract_version="1",
        ),
        copies_per_target=1,
        audience_intent=PacketAudienceIntent(
            audience_kind="participant",
        ),
        requirement_level="recommended",
    )


def _authoring_mapping(
    *,
    include_definition: bool,
    version_label: str = "v1",
    record_id: str = "submission-1",
) -> dict[str, object]:
    component = _component(record_id)
    return {
        "schema_version": PACKET_AUTHORING_SCHEMA,
        "definition": (
            {
                "name": "Seminar Packet",
                "purpose": "Coordinate reusable seminar materials.",
                "description": "Synthetic Packet.",
            }
            if include_definition
            else None
        ),
        "version": {
            "version_label": version_label,
            "components": [
                {
                    "packet_component_id": component.packet_component_id,
                    "sequence": component.sequence,
                    "component_kind": component.component_kind,
                    "copies_per_target": component.copies_per_target,
                    "audience_intent": {
                        "audience_kind": "participant",
                        "role_keys": [],
                    },
                    "requirement_level": component.requirement_level,
                    "template_id": None,
                    "template_version_id": None,
                    "external_reference": {
                        "module_id": "quillan",
                        "record_kind": "submission",
                        "record_id": record_id,
                        "contract_version": "1",
                    },
                    "condition": None,
                    "label": None,
                }
            ],
            "rendering_rules": {
                "preserve_component_order": True,
                "start_each_component_on_new_page": False,
                "copy_collation": "component_major",
                "target_order": "stable_identity",
            },
        },
    }


def _write_authoring(
    path: Path,
    *,
    include_definition: bool,
    version_label: str = "v1",
    record_id: str = "submission-1",
) -> None:
    path.write_bytes(
        (
            json.dumps(
                _authoring_mapping(
                    include_definition=include_definition,
                    version_label=version_label,
                    record_id=record_id,
                ),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")
    )


def test_packet_authoring_is_strict_and_source_fingerprinted(
    tmp_path: Path,
) -> None:
    source = tmp_path / "packet.json"
    _write_authoring(source, include_definition=True)
    document, prepared = load_packet_authoring_source(source)
    assert document.definition is not None
    assert document.version.version_label == "v1"
    assert document.version.components == (_component(),)
    assert verify_prepared_packet_source(
        prepared,
        description="Packet authoring file",
    ).endswith(b"\n")

    source.write_bytes(source.read_bytes() + b" ")
    with pytest.raises(PacketAuthoringConflictError, match="changed"):
        verify_prepared_packet_source(
            prepared,
            description="Packet authoring file",
        )


def test_packet_authoring_rejects_unknown_fields(tmp_path: Path) -> None:
    source = tmp_path / "packet.json"
    mapping = _authoring_mapping(include_definition=True)
    mapping["unexpected"] = True
    source.write_bytes(
        (
            json.dumps(mapping, sort_keys=True, separators=(",", ":"))
            + "\n"
        ).encode()
    )
    with pytest.raises(PacketAuthoringError, match="unknown field"):
        load_packet_authoring_source(source)


def test_prepare_create_is_side_effect_free_and_commit_creates_library(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    source = tmp_path / "packet.json"
    _write_authoring(source, include_definition=True)

    prepared = prepare_packet_create(
        PreparePacketCreateRequest(
            packet_definition_id="packet-1",
            packet_version_id="packet-version-1",
            authoring_file=source,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    assert not (root / "shared").exists()

    result = commit_packet_create(prepared, workspace_root=root)
    assert result.packet_definition_id == "packet-1"
    assert result.snapshot_revision == 1
    assert result.current_packet_version_id is None
    assert get_packet("packet-1", workspace_root=root).summary.component_count == 1


def test_prepare_create_requires_definition_metadata(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    source = tmp_path / "packet.json"
    _write_authoring(source, include_definition=False)
    with pytest.raises(
        ConcordWorkflowValidationError,
        match="requires authoring definition",
    ):
        prepare_packet_create(
            PreparePacketCreateRequest(
                packet_definition_id="packet-1",
                packet_version_id="packet-version-1",
                authoring_file=source,
                actor=_actor(),
            ),
            workspace_root=root,
        )


def test_commit_rejects_authoring_change_after_prepare(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    source = tmp_path / "packet.json"
    _write_authoring(source, include_definition=True)
    prepared = prepare_packet_create(
        PreparePacketCreateRequest(
            packet_definition_id="packet-1",
            packet_version_id="packet-version-1",
            authoring_file=source,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    _write_authoring(
        source,
        include_definition=True,
        record_id="submission-2",
    )
    with pytest.raises(ConcordWorkflowConflictError, match="changed"):
        commit_packet_create(prepared, workspace_root=root)
    assert list_packets(workspace_root=root) == ()


def test_revision_prepare_and_commit_use_exact_snapshot(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    source = tmp_path / "packet-v1.json"
    _write_authoring(source, include_definition=True)
    created = commit_packet_create(
        prepare_packet_create(
            PreparePacketCreateRequest(
                packet_definition_id="packet-1",
                packet_version_id="packet-version-1",
                authoring_file=source,
                actor=_actor(),
            ),
            workspace_root=root,
        ),
        workspace_root=root,
    )

    revision_source = tmp_path / "packet-v2.json"
    _write_authoring(
        revision_source,
        include_definition=False,
        version_label="v2",
        record_id="submission-2",
    )
    prepared = prepare_packet_revision(
        PreparePacketRevisionRequest(
            packet_definition_id="packet-1",
            packet_version_id="packet-version-2",
            authoring_file=revision_source,
            expected_snapshot_revision=created.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    revised = commit_packet_revision(prepared, workspace_root=root)
    assert revised.snapshot_revision == 2
    assert revised.head_packet_version_id == "packet-version-2"
    assert revised.current_packet_version_id is None


def test_activation_update_retire_workflow_round_trip(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    source = tmp_path / "packet-v1.json"
    _write_authoring(source, include_definition=True)
    created = commit_packet_create(
        prepare_packet_create(
            PreparePacketCreateRequest(
                packet_definition_id="packet-1",
                packet_version_id="packet-version-1",
                authoring_file=source,
                actor=_actor(),
            ),
            workspace_root=root,
        ),
        workspace_root=root,
    )
    activated = commit_packet_activation(
        prepare_packet_activation(
            PreparePacketActivationRequest(
                packet_definition_id="packet-1",
                packet_version_id="packet-version-1",
                expected_snapshot_revision=created.snapshot_revision,
                actor=_actor(),
            ),
            workspace_root=root,
        ),
        workspace_root=root,
    )
    assert activated.current_packet_version_id == "packet-version-1"

    updated = commit_packet_update(
        prepare_packet_update(
            PreparePacketUpdateRequest(
                packet_definition_id="packet-1",
                name="Updated Packet",
                purpose="Updated purpose.",
                description=None,
                expected_snapshot_revision=activated.snapshot_revision,
                actor=_actor(),
            ),
            workspace_root=root,
        ),
        workspace_root=root,
    )
    assert get_packet(
        "packet-1",
        workspace_root=root,
    ).definition.name == "Updated Packet"

    retired = commit_packet_retire(
        prepare_packet_retire(
            PreparePacketRetireRequest(
                packet_definition_id="packet-1",
                expected_snapshot_revision=updated.snapshot_revision,
                actor=_actor(),
            ),
            workspace_root=root,
        ),
        workspace_root=root,
    )
    assert retired.status == "retired"
    assert retired.current_packet_version_id is None


def test_retire_draft_successor_through_workflow(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    source = tmp_path / "packet-v1.json"
    _write_authoring(source, include_definition=True)
    created = commit_packet_create(
        prepare_packet_create(
            PreparePacketCreateRequest(
                packet_definition_id="packet-1",
                packet_version_id="packet-version-1",
                authoring_file=source,
                actor=_actor(),
            ),
            workspace_root=root,
        ),
        workspace_root=root,
    )
    revision_source = tmp_path / "packet-v2.json"
    _write_authoring(
        revision_source,
        include_definition=False,
        version_label="v2",
        record_id="submission-2",
    )
    revised = commit_packet_revision(
        prepare_packet_revision(
            PreparePacketRevisionRequest(
                packet_definition_id="packet-1",
                packet_version_id="packet-version-2",
                authoring_file=revision_source,
                expected_snapshot_revision=created.snapshot_revision,
                actor=_actor(),
            ),
            workspace_root=root,
        ),
        workspace_root=root,
    )
    retired = commit_packet_retire_version(
        prepare_packet_retire_version(
            PreparePacketRetireVersionRequest(
                packet_definition_id="packet-1",
                packet_version_id="packet-version-2",
                expected_snapshot_revision=revised.snapshot_revision,
                actor=_actor(),
            ),
            workspace_root=root,
        ),
        workspace_root=root,
    )
    detail = get_packet("packet-1", workspace_root=root)
    assert retired.snapshot_revision == 3
    assert detail.versions[-1].status == "retired"


def test_list_packets_is_deterministic_and_read_only(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    assert list_packets(workspace_root=root) == ()
    assert not (root / "shared").exists()
