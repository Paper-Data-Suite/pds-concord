from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest
from pds_core.routing_models import ModuleRecordRef

import concord.packet_storage as packet_storage_module
from concord.models import (
    ActorReference,
    PacketAudienceIntent,
    PacketComponent,
    PacketDefinition,
    PacketRenderingRules,
    PacketVersion,
    PrivacyPolicy,
    Provenance,
    TemplateCompatibility,
    TemplateDefinition,
    TemplatePageDefinition,
    TemplateRenderingInput,
    TemplateResponseRegion,
    TemplateVersion,
)
from concord.packet_serialization import (
    PacketSerializationError,
    packet_from_json_bytes,
    packet_to_json_bytes,
)
from concord.packet_storage import (
    PacketStorageConflictError,
    PacketStorageDependencyError,
    PacketStorageIntegrityError,
    PacketStoragePartialSuccessError,
    PacketStorageWriteError,
    activate_packet_version,
    create_packet_library,
    create_successor_packet_version,
    list_packet_ids,
    list_packet_versions,
    load_current_packet,
    load_current_packet_version,
    load_packet_snapshot,
    load_packet_version,
    retire_packet,
    retire_packet_version,
    update_packet_definition,
)
from concord.packet_storage_paths import (
    packet_current_path,
    packet_library_root,
    packet_record_revision_path,
    packet_snapshot_path,
    packet_write_lock_path,
)
from concord.template_storage import (
    activate_template_version,
    create_successor_template_version,
    create_template_library,
    retire_template,
)


def _workspace(tmp_path: Path) -> Path:
    root = tmp_path / "workspace"
    root.mkdir()
    return root


def _provenance() -> Provenance:
    return Provenance(
        actor=ActorReference(
            actor_kind="authorized_adult",
            actor_id="teacher-1",
            owning_system="concord",
        ),
        timestamp="2026-08-24T23:30:00-04:00",
        source_kind="manual",
        application_version="0.3.0.dev0",
    )


def _rendering_bytes() -> bytes:
    return b"packet-storage-template-rendering-v1\n"


def _template_definition(
    *,
    status: str,
    template_id: str = "template-1",
    name: str = "Group Notes",
) -> TemplateDefinition:
    return TemplateDefinition(
        template_id=template_id,
        name=name,
        purpose="Synthetic Packet dependency.",
        artifact_category="discussion_record",
        status=status,
        created_provenance=_provenance(),
    )


def _template_version(
    *,
    status: str,
    template_id: str = "template-1",
    template_version_id: str = "template-version-1",
    audiences: tuple[str, ...] = ("group",),
) -> TemplateVersion:
    digest = hashlib.sha256(_rendering_bytes()).hexdigest()
    inputs = (
        TemplateRenderingInput(
            input_key="route-payload",
            label="PDS2 route payload",
            source_kind="pds2_route_payload",
            value_kind="text",
            required=True,
        ),
        TemplateRenderingInput(
            input_key="human-fallback",
            label="Human fallback",
            source_kind="human_fallback",
            value_kind="text",
            required=True,
        ),
    )
    page = TemplatePageDefinition(
        page_key="page-1",
        sequence=1,
        page_kind="primary",
        return_expected=True,
        route_required=True,
        rendering_input_keys=("route-payload", "human-fallback"),
        response_regions=(
            TemplateResponseRegion(
                region_key="notes",
                label="Notes",
                region_kind="free_response",
                required=False,
            ),
        ),
        route_payload_input_key="route-payload",
        human_fallback_input_key="human-fallback",
    )
    return TemplateVersion(
        template_version_id=template_version_id,
        template_id=template_id,
        version_label="v1",
        revision_sequence=1,
        rendering_contract_version="concord-template-rendering-v1",
        rendering_specification_reference=f"{template_id}-rendering-v1",
        rendering_specification_sha256=digest,
        artifact_category="discussion_record",
        page_manifest=(page,),
        rendering_inputs=inputs,
        default_expected_return_status="returned_expected",
        default_privacy_policy=PrivacyPolicy(
            classification="teacher_restricted"
        ),
        compatibility=TemplateCompatibility(
            audience_kinds=audiences,
            activity_type_keys=("socratic_seminar",),
            scoring_orientations=("evidence_only",),
            criterion_kinds=("local",),
        ),
        created_provenance=_provenance(),
        status=status,
    )


def _install_template(
    root: Path,
    *,
    status: str,
    template_id: str = "template-1",
    audiences: tuple[str, ...] = ("group",),
) -> None:
    create_template_library(
        root,
        definition=_template_definition(
            status=status,
            template_id=template_id,
        ),
        initial_version=_template_version(
            status=status,
            template_id=template_id,
            audiences=audiences,
        ),
        rendering_specification=_rendering_bytes(),
    )


def _packet_definition(
    *,
    status: str = "draft",
    packet_id: str = "packet-1",
    name: str = "Seminar Packet",
) -> PacketDefinition:
    return PacketDefinition(
        packet_definition_id=packet_id,
        name=name,
        purpose="Synthetic reusable Packet.",
        status=status,
        created_provenance=_provenance(),
        description="Packet storage test.",
    )


def _template_component(
    *,
    template_id: str = "template-1",
    template_version_id: str = "template-version-1",
    audience: str = "group",
) -> PacketComponent:
    return PacketComponent(
        packet_component_id="component-1",
        sequence=1,
        component_kind="concord_template",
        template_id=template_id,
        template_version_id=template_version_id,
        copies_per_target=1,
        audience_intent=PacketAudienceIntent(
            audience_kind=audience,
        ),
        requirement_level="required",
    )


def _external_component() -> PacketComponent:
    return PacketComponent(
        packet_component_id="component-external",
        sequence=1,
        component_kind="external_component",
        external_reference=ModuleRecordRef(
            module_id="quillan",
            record_kind="submission",
            record_id="submission-1",
            contract_version="1",
        ),
        copies_per_target=1,
        audience_intent=PacketAudienceIntent(
            audience_kind="participant",
        ),
        requirement_level="recommended",
    )


def _packet_version(
    *,
    status: str = "draft",
    packet_id: str = "packet-1",
    packet_version_id: str = "packet-version-1",
    component: PacketComponent | None = None,
) -> PacketVersion:
    return PacketVersion(
        packet_version_id=packet_version_id,
        packet_definition_id=packet_id,
        version_label="v1",
        revision_sequence=1,
        components=(component or _template_component(),),
        rendering_rules=PacketRenderingRules(),
        created_provenance=_provenance(),
        status=status,
    )


def test_packet_body_serialization_is_canonical_and_strict() -> None:
    version = _packet_version(component=_external_component())
    data = packet_to_json_bytes(version)
    assert data.endswith(b"\n")
    assert packet_from_json_bytes("packet_version", data) == version

    mapping = json.loads(data)
    mapping["unknown"] = True
    invalid = (
        json.dumps(mapping, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()
    with pytest.raises(PacketSerializationError, match="unknown field"):
        packet_from_json_bytes("packet_version", invalid)


def test_packet_body_serialization_rejects_duplicate_json_keys() -> None:
    definition = packet_to_json_bytes(_packet_definition()).decode()
    duplicated = definition.replace(
        '{"created_provenance":',
        '{"packet_definition_id":"duplicate","created_provenance":',
        1,
    ).encode()
    with pytest.raises(PacketSerializationError, match="duplicate"):
        packet_from_json_bytes("packet_definition", duplicated)


@pytest.mark.parametrize("status", ("draft", "active"))
def test_initial_packet_creation_and_exact_reload(
    tmp_path: Path,
    status: str,
) -> None:
    root = _workspace(tmp_path)
    _install_template(root, status=status)
    definition = _packet_definition(status=status)
    version = _packet_version(status=status)

    loaded = create_packet_library(
        root,
        definition=definition,
        initial_version=version,
    )

    assert loaded.definition == definition
    assert loaded.versions == (version,)
    assert loaded.snapshot_revision == 1
    assert loaded.head_packet_version_id == version.packet_version_id
    assert loaded.current_packet_version_id == (
        version.packet_version_id if status == "active" else None
    )
    assert load_current_packet(root, definition.packet_definition_id) == loaded
    assert list_packet_versions(
        root,
        definition.packet_definition_id,
    ) == (version,)
    assert load_packet_version(
        root,
        definition.packet_definition_id,
        version.packet_version_id,
    ) == version
    assert load_current_packet_version(
        root,
        definition.packet_definition_id,
    ) == (version if status == "active" else None)


def test_creation_uses_workspace_level_shared_concord_namespace(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    create_packet_library(
        root,
        definition=_packet_definition(),
        initial_version=_packet_version(component=_external_component()),
    )

    expected = root / "shared" / "concord" / "packets" / "packet-1"
    assert packet_library_root(root) == (
        root / "shared" / "concord" / "packets"
    )
    assert expected.is_dir()
    assert not (root / "classes").exists()


def test_read_only_empty_listing_writes_nothing(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    assert list_packet_ids(root) == ()
    assert not (root / "shared").exists()


def test_listing_is_deterministic_by_casefolded_name_then_id(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    create_packet_library(
        root,
        definition=_packet_definition(
            packet_id="packet-z",
            name="alpha",
        ),
        initial_version=_packet_version(
            packet_id="packet-z",
            packet_version_id="packet-version-z",
            component=_external_component(),
        ),
    )
    create_packet_library(
        root,
        definition=_packet_definition(
            packet_id="packet-a",
            name="Alpha",
        ),
        initial_version=_packet_version(
            packet_id="packet-a",
            packet_version_id="packet-version-a",
            component=_external_component(),
        ),
    )
    assert list_packet_ids(root) == ("packet-a", "packet-z")


def test_draft_packet_may_reference_draft_template(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    _install_template(root, status="draft")
    loaded = create_packet_library(
        root,
        definition=_packet_definition(status="draft"),
        initial_version=_packet_version(status="draft"),
    )
    assert loaded.current_packet_version_id is None


def test_active_packet_rejects_draft_template_dependency(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    _install_template(root, status="draft")
    with pytest.raises(
        PacketStorageDependencyError,
        match="active or superseded",
    ):
        create_packet_library(
            root,
            definition=_packet_definition(status="active"),
            initial_version=_packet_version(status="active"),
        )
    assert not (root / "shared" / "concord" / "packets").exists()


def test_packet_rejects_missing_exact_template_version(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    _install_template(root, status="active")
    with pytest.raises(
        PacketStorageDependencyError,
        match="Template Version not found",
    ):
        create_packet_library(
            root,
            definition=_packet_definition(),
            initial_version=_packet_version(
                component=_template_component(
                    template_version_id="missing-version",
                )
            ),
        )


def test_packet_rejects_reusable_template_audience_conflict(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    _install_template(
        root,
        status="active",
        audiences=("group",),
    )
    with pytest.raises(
        PacketStorageDependencyError,
        match="audience is incompatible",
    ):
        create_packet_library(
            root,
            definition=_packet_definition(),
            initial_version=_packet_version(
                component=_template_component(audience="teacher")
            ),
        )


def test_external_component_needs_no_sibling_runtime_or_record(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    loaded = create_packet_library(
        root,
        definition=_packet_definition(status="active"),
        initial_version=_packet_version(
            status="active",
            component=_external_component(),
        ),
    )
    reference = loaded.current_version.components[0].external_reference
    assert reference == ModuleRecordRef(
        module_id="quillan",
        record_kind="submission",
        record_id="submission-1",
        contract_version="1",
    )


def test_historical_packet_read_does_not_reresolve_template_status(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    _install_template(root, status="active")
    create_packet_library(
        root,
        definition=_packet_definition(status="draft"),
        initial_version=_packet_version(status="draft"),
    )
    retire_template(
        root,
        "template-1",
        expected_snapshot_revision=1,
        operation_provenance=_provenance(),
    )
    loaded = load_current_packet(root, "packet-1")
    assert loaded.head_version.components[0].template_version_id == (
        "template-version-1"
    )


def test_duplicate_packet_identity_conflicts(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    definition = _packet_definition()
    version = _packet_version(component=_external_component())
    create_packet_library(
        root,
        definition=definition,
        initial_version=version,
    )
    with pytest.raises(PacketStorageConflictError, match="already exists"):
        create_packet_library(
            root,
            definition=definition,
            initial_version=version,
        )


def test_record_digest_tampering_fails_closed(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    definition = _packet_definition()
    version = _packet_version(component=_external_component())
    create_packet_library(
        root,
        definition=definition,
        initial_version=version,
    )
    path = packet_record_revision_path(
        root,
        definition.packet_definition_id,
        "packet_version",
        version.packet_version_id,
        1,
    )
    data = json.loads(path.read_text(encoding="utf-8"))
    data["operation"] = "tampered"
    path.write_bytes(
        (
            json.dumps(data, sort_keys=True, separators=(",", ":")) + "\n"
        ).encode("utf-8")
    )
    with pytest.raises(PacketStorageIntegrityError, match="digest mismatch"):
        load_current_packet(root, definition.packet_definition_id)


def test_current_pointer_digest_tampering_fails_closed(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    definition = _packet_definition()
    version = _packet_version(component=_external_component())
    create_packet_library(
        root,
        definition=definition,
        initial_version=version,
    )
    path = packet_current_path(root, definition.packet_definition_id)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["snapshot_sha256"] = "0" * 64
    path.write_bytes(
        (
            json.dumps(data, sort_keys=True, separators=(",", ":")) + "\n"
        ).encode("utf-8")
    )
    with pytest.raises(PacketStorageIntegrityError, match="digest mismatch"):
        load_current_packet(root, definition.packet_definition_id)


def test_snapshot_one_is_exact_and_has_no_predecessor(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    definition = _packet_definition()
    version = _packet_version(component=_external_component())
    create_packet_library(
        root,
        definition=definition,
        initial_version=version,
    )
    snapshot, digest = load_packet_snapshot(
        root,
        definition.packet_definition_id,
        1,
    )
    assert snapshot.snapshot_revision == 1
    assert snapshot.previous_snapshot_revision is None
    assert snapshot.previous_snapshot_sha256 is None
    assert digest == hashlib.sha256(
        packet_snapshot_path(
            root,
            definition.packet_definition_id,
            1,
        ).read_bytes()
    ).hexdigest()


def _packet_successor(
    *,
    component: PacketComponent | None = None,
    packet_version_id: str = "packet-version-2",
) -> PacketVersion:
    return replace(
        _packet_version(status="active"),
        packet_version_id=packet_version_id,
        version_label="v2",
        revision_sequence=2,
        components=(component or _template_component(),),
        status="draft",
        supersedes_packet_version_id="packet-version-1",
        created_provenance=replace(
            _provenance(),
            timestamp="2026-08-24T23:40:00-04:00",
        ),
    )


def test_successor_is_draft_head_without_changing_current(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    _install_template(root, status="active")
    initial = create_packet_library(
        root,
        definition=_packet_definition(status="active"),
        initial_version=_packet_version(status="active"),
    )
    successor = _packet_successor()
    updated = create_successor_packet_version(
        root,
        "packet-1",
        successor=successor,
        expected_snapshot_revision=initial.snapshot_revision,
        operation_provenance=_provenance(),
    )
    assert updated.snapshot_revision == 2
    assert updated.current_packet_version_id == "packet-version-1"
    assert updated.head_packet_version_id == "packet-version-2"
    assert updated.versions == (
        _packet_version(status="active"),
        successor,
    )


def test_successor_rejects_stale_snapshot_and_non_head_lineage(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    _install_template(root, status="active")
    initial = create_packet_library(
        root,
        definition=_packet_definition(status="active"),
        initial_version=_packet_version(status="active"),
    )
    successor = _packet_successor()
    updated = create_successor_packet_version(
        root,
        "packet-1",
        successor=successor,
        expected_snapshot_revision=initial.snapshot_revision,
        operation_provenance=_provenance(),
    )
    with pytest.raises(PacketStorageConflictError, match="expected Packet"):
        update_packet_definition(
            root,
            "packet-1",
            definition=replace(
                updated.definition,
                name="Stale writer",
            ),
            expected_snapshot_revision=1,
            operation_provenance=_provenance(),
        )

    bad = replace(
        successor,
        packet_version_id="packet-version-3",
        revision_sequence=4,
        supersedes_packet_version_id="packet-version-2",
    )
    with pytest.raises(PacketStorageWriteError, match="head \\+ 1"):
        create_successor_packet_version(
            root,
            "packet-1",
            successor=bad,
            expected_snapshot_revision=updated.snapshot_revision,
            operation_provenance=_provenance(),
        )


def test_activation_supersedes_previous_current_and_promotes_definition(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    _install_template(root, status="active")
    initial = create_packet_library(
        root,
        definition=_packet_definition(status="active"),
        initial_version=_packet_version(status="active"),
    )
    revised = create_successor_packet_version(
        root,
        "packet-1",
        successor=_packet_successor(),
        expected_snapshot_revision=initial.snapshot_revision,
        operation_provenance=_provenance(),
    )
    activated = activate_packet_version(
        root,
        "packet-1",
        "packet-version-2",
        expected_snapshot_revision=revised.snapshot_revision,
        operation_provenance=_provenance(),
    )
    assert activated.snapshot_revision == 3
    assert activated.current_packet_version_id == "packet-version-2"
    assert activated.head_packet_version_id == "packet-version-2"
    assert [item.status for item in activated.versions] == [
        "superseded",
        "active",
    ]


def test_activation_reresolves_and_blocks_draft_template_dependency(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    _install_template(root, status="active", template_id="template-1")
    _install_template(root, status="draft", template_id="template-2")
    initial = create_packet_library(
        root,
        definition=_packet_definition(status="active"),
        initial_version=_packet_version(status="active"),
    )
    successor = _packet_successor(
        component=_template_component(
            template_id="template-2",
            template_version_id="template-version-1",
        )
    )
    revised = create_successor_packet_version(
        root,
        "packet-1",
        successor=successor,
        expected_snapshot_revision=initial.snapshot_revision,
        operation_provenance=_provenance(),
    )
    with pytest.raises(
        PacketStorageDependencyError,
        match="active or superseded",
    ):
        activate_packet_version(
            root,
            "packet-1",
            "packet-version-2",
            expected_snapshot_revision=revised.snapshot_revision,
            operation_provenance=_provenance(),
        )
    assert load_current_packet(root, "packet-1").snapshot_revision == 2

    activate_template_version(
        root,
        "template-2",
        "template-version-1",
        expected_snapshot_revision=1,
        operation_provenance=_provenance(),
    )
    activated = activate_packet_version(
        root,
        "packet-1",
        "packet-version-2",
        expected_snapshot_revision=2,
        operation_provenance=_provenance(),
    )
    assert activated.current_packet_version_id == "packet-version-2"


def test_active_packet_may_pin_superseded_template_version(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    _install_template(root, status="active")
    template_successor = replace(
        _template_version(status="active"),
        template_version_id="template-version-2",
        version_label="v2",
        revision_sequence=2,
        status="draft",
        supersedes_template_version_id="template-version-1",
        created_provenance=replace(
            _provenance(),
            timestamp="2026-08-24T23:41:00-04:00",
        ),
    )
    revised_template = create_successor_template_version(
        root,
        "template-1",
        successor=template_successor,
        rendering_specification=_rendering_bytes(),
        expected_snapshot_revision=1,
        operation_provenance=_provenance(),
    )
    activate_template_version(
        root,
        "template-1",
        "template-version-2",
        expected_snapshot_revision=revised_template.snapshot_revision,
        operation_provenance=_provenance(),
    )
    loaded = create_packet_library(
        root,
        definition=_packet_definition(status="active"),
        initial_version=_packet_version(status="active"),
    )
    assert loaded.current_version is not None
    assert (
        loaded.current_version.components[0].template_version_id
        == "template-version-1"
    )


def test_definition_update_is_revisioned_and_exact_noop_is_not(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    initial = create_packet_library(
        root,
        definition=_packet_definition(),
        initial_version=_packet_version(component=_external_component()),
    )
    changed_definition = replace(
        initial.definition,
        name="Updated Seminar Packet",
    )
    changed = update_packet_definition(
        root,
        "packet-1",
        definition=changed_definition,
        expected_snapshot_revision=1,
        operation_provenance=_provenance(),
    )
    assert changed.snapshot_revision == 2
    assert changed.definition.name == "Updated Seminar Packet"

    no_op = update_packet_definition(
        root,
        "packet-1",
        definition=changed.definition,
        expected_snapshot_revision=2,
        operation_provenance=_provenance(),
    )
    assert no_op.snapshot_revision == 2


def test_retire_draft_version_then_whole_packet_preserves_history(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    _install_template(root, status="active")
    initial = create_packet_library(
        root,
        definition=_packet_definition(status="active"),
        initial_version=_packet_version(status="active"),
    )
    revised = create_successor_packet_version(
        root,
        "packet-1",
        successor=_packet_successor(),
        expected_snapshot_revision=initial.snapshot_revision,
        operation_provenance=_provenance(),
    )
    retired_version = retire_packet_version(
        root,
        "packet-1",
        "packet-version-2",
        expected_snapshot_revision=revised.snapshot_revision,
        operation_provenance=_provenance(),
    )
    assert retired_version.snapshot_revision == 3
    assert retired_version.current_packet_version_id == "packet-version-1"
    assert retired_version.head_packet_version_id == "packet-version-2"
    assert retired_version.versions[1].status == "retired"

    retired = retire_packet(
        root,
        "packet-1",
        expected_snapshot_revision=retired_version.snapshot_revision,
        operation_provenance=_provenance(),
    )
    assert retired.snapshot_revision == 4
    assert retired.definition.status == "retired"
    assert retired.current_packet_version_id is None
    assert retired.head_packet_version_id == "packet-version-2"
    assert [item.status for item in retired.versions] == [
        "retired",
        "retired",
    ]
    assert load_packet_snapshot(root, "packet-1", 1)[0].snapshot_revision == 1


def test_active_current_version_cannot_be_retired_independently(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    create_packet_library(
        root,
        definition=_packet_definition(status="active"),
        initial_version=_packet_version(
            status="active",
            component=_external_component(),
        ),
    )
    with pytest.raises(PacketStorageConflictError, match="active current"):
        retire_packet_version(
            root,
            "packet-1",
            "packet-version-1",
            expected_snapshot_revision=1,
            operation_provenance=_provenance(),
        )


def test_packet_write_lock_collision_is_explicit(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    loaded = create_packet_library(
        root,
        definition=_packet_definition(),
        initial_version=_packet_version(component=_external_component()),
    )
    lock = packet_write_lock_path(root, "packet-1")
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_bytes(b"occupied")
    with pytest.raises(PacketStorageConflictError, match="write lock"):
        update_packet_definition(
            root,
            "packet-1",
            definition=replace(loaded.definition, name="Blocked"),
            expected_snapshot_revision=1,
            operation_provenance=_provenance(),
        )


def test_orphan_snapshot_blocks_mutation(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    loaded = create_packet_library(
        root,
        definition=_packet_definition(),
        initial_version=_packet_version(component=_external_component()),
    )
    packet_snapshot_path(root, "packet-1", 2).write_bytes(b"orphan")
    with pytest.raises(
        PacketStorageIntegrityError,
        match="noncontiguous or contains orphans",
    ):
        update_packet_definition(
            root,
            "packet-1",
            definition=replace(loaded.definition, name="Blocked"),
            expected_snapshot_revision=1,
            operation_provenance=_provenance(),
        )


def test_lock_cleanup_failure_reports_partial_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _workspace(tmp_path)
    loaded = create_packet_library(
        root,
        definition=_packet_definition(),
        initial_version=_packet_version(component=_external_component()),
    )

    def fail_release(path: Path) -> OSError:
        return OSError(f"synthetic cleanup failure: {path}")

    monkeypatch.setattr(
        packet_storage_module,
        "_release_packet_lock",
        fail_release,
    )
    with pytest.raises(PacketStoragePartialSuccessError) as caught:
        update_packet_definition(
            root,
            "packet-1",
            definition=replace(loaded.definition, name="Published"),
            expected_snapshot_revision=1,
            operation_provenance=_provenance(),
        )
    assert caught.value.pointer_published is True
    assert caught.value.snapshot_revision == 2
    assert load_current_packet(root, "packet-1").definition.name == "Published"
