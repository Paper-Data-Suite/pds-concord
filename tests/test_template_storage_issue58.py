from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

from concord.models import (
    ActorReference,
    PrivacyPolicy,
    Provenance,
    TemplateCompatibility,
    TemplateDefinition,
    TemplatePageDefinition,
    TemplateRenderingInput,
    TemplateResponseRegion,
    TemplateVersion,
)
from concord.record_registry import RECORD_DESCRIPTORS
from concord.template_serialization import (
    TemplateSerializationError,
    template_from_json_bytes,
    template_to_json_bytes,
)
from concord.template_storage import (
    TemplateStorageConflictError,
    TemplateStorageIntegrityError,
    TemplateStorageNotFoundError,
    TemplateStorageWriteError,
    create_template_library,
    list_template_ids,
    list_template_versions,
    load_current_template,
    load_current_template_version,
    load_template_snapshot,
    load_template_version,
)
from concord.template_storage_paths import (
    template_current_path,
    template_library_root,
    template_record_revision_path,
    template_rendering_specification_path,
    template_snapshot_path,
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
        timestamp="2026-08-24T18:30:00-04:00",
        source_kind="manual",
        application_version="0.3.0.dev0",
    )


def _definition(
    *,
    status: str = "draft",
    template_id: str = "template-1",
) -> TemplateDefinition:
    return TemplateDefinition(
        template_id=template_id,
        name="Seminar Discussion Map",
        purpose="Capture collaborative seminar evidence.",
        artifact_category="discussion_record",
        status=status,
        created_provenance=_provenance(),
        description="Synthetic reusable Template.",
        owner_reference=ActorReference(
            actor_kind="authorized_adult",
            actor_id="teacher-1",
            owning_system="concord",
        ),
    )


def _rendering_bytes() -> bytes:
    return b"concord-template-rendering-v1\nsynthetic seminar form\n"


def _version(
    *,
    status: str = "draft",
    template_id: str = "template-1",
    template_version_id: str = "template-version-1",
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
        TemplateRenderingInput(
            input_key="group-label",
            label="Group label",
            source_kind="group_label",
            value_kind="text",
            required=True,
            max_length=80,
        ),
    )
    page = TemplatePageDefinition(
        page_key="page-1",
        sequence=1,
        page_kind="primary",
        return_expected=True,
        route_required=True,
        rendering_input_keys=(
            "route-payload",
            "human-fallback",
            "group-label",
        ),
        response_regions=(
            TemplateResponseRegion(
                region_key="notes",
                label="Discussion notes",
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
        rendering_specification_reference="seminar-form-v1",
        rendering_specification_sha256=digest,
        artifact_category="discussion_record",
        page_manifest=(page,),
        rendering_inputs=inputs,
        default_expected_return_status="returned_expected",
        default_privacy_policy=PrivacyPolicy(
            classification="teacher_restricted"
        ),
        compatibility=TemplateCompatibility(
            audience_kinds=("group",),
            activity_type_keys=("socratic_seminar",),
            scoring_orientations=("evidence_only",),
            criterion_kinds=("local",),
        ),
        created_provenance=_provenance(),
        status=status,
    )


def test_template_body_serialization_is_canonical_and_strict() -> None:
    version = _version()
    data = template_to_json_bytes(version)
    assert data.endswith(b"\n")
    assert template_from_json_bytes("template_version", data) == version

    mapping = json.loads(data)
    mapping["unknown"] = True
    invalid = (
        json.dumps(mapping, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()
    with pytest.raises(TemplateSerializationError, match="unknown field"):
        template_from_json_bytes("template_version", invalid)


def test_template_body_serialization_rejects_duplicate_json_keys() -> None:
    definition = template_to_json_bytes(_definition()).decode()
    duplicated = definition.replace(
        '{"artifact_category":',
        '{"template_id":"duplicate","artifact_category":',
        1,
    ).encode()
    with pytest.raises(TemplateSerializationError, match="duplicate"):
        template_from_json_bytes("template_definition", duplicated)


@pytest.mark.parametrize("active", (False, True))
def test_initial_template_creation_and_exact_reload(
    tmp_path: Path,
    active: bool,
) -> None:
    root = _workspace(tmp_path)
    status = "active" if active else "draft"
    definition = _definition(status=status)
    version = _version(status=status)

    loaded = create_template_library(
        root,
        definition=definition,
        initial_version=version,
        rendering_specification=_rendering_bytes(),
    )

    assert loaded.definition == definition
    assert loaded.versions == (version,)
    assert loaded.snapshot_revision == 1
    assert loaded.head_template_version_id == version.template_version_id
    assert loaded.current_template_version_id == (
        version.template_version_id if active else None
    )
    assert load_current_template(root, definition.template_id) == loaded
    assert list_template_versions(root, definition.template_id) == (version,)
    assert load_template_version(
        root,
        definition.template_id,
        version.template_version_id,
    ) == version
    assert load_current_template_version(root, definition.template_id) == (
        version if active else None
    )

    asset = template_rendering_specification_path(
        root,
        definition.template_id,
        version.rendering_specification_reference,
    )
    assert asset.read_bytes() == _rendering_bytes()


def test_creation_uses_workspace_level_shared_concord_namespace(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    create_template_library(
        root,
        definition=_definition(),
        initial_version=_version(),
        rendering_specification=_rendering_bytes(),
    )

    expected = root / "shared" / "concord" / "templates" / "template-1"
    assert template_library_root(root) == (
        root / "shared" / "concord" / "templates"
    )
    assert expected.is_dir()
    assert not (root / "classes").exists()


def test_read_only_empty_listing_writes_nothing(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    before = tuple(root.rglob("*"))
    assert list_template_ids(root) == ()
    assert tuple(root.rglob("*")) == before


def test_template_listing_is_teacher_facing_and_deterministic(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    for template_id, name in (
        ("template-z", "Alpha"),
        ("template-a", "Zulu"),
    ):
        definition = replace(
            _definition(template_id=template_id),
            name=name,
        )
        version = _version(
            template_id=template_id,
            template_version_id=f"{template_id}-version-1",
        )
        create_template_library(
            root,
            definition=definition,
            initial_version=version,
            rendering_specification=_rendering_bytes(),
        )
    assert list_template_ids(root) == ("template-z", "template-a")


def test_initial_creation_rejects_digest_or_identity_mismatch(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    with pytest.raises(TemplateStorageWriteError, match="do not match"):
        create_template_library(
            root,
            definition=_definition(),
            initial_version=replace(
                _version(),
                rendering_specification_sha256="0" * 64,
            ),
            rendering_specification=_rendering_bytes(),
        )

    with pytest.raises(TemplateStorageWriteError, match="share template_id"):
        create_template_library(
            root,
            definition=_definition(),
            initial_version=_version(template_id="other-template"),
            rendering_specification=_rendering_bytes(),
        )


def test_initial_create_is_create_only(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    create_template_library(
        root,
        definition=_definition(),
        initial_version=_version(),
        rendering_specification=_rendering_bytes(),
    )
    with pytest.raises(TemplateStorageConflictError):
        create_template_library(
            root,
            definition=_definition(),
            initial_version=_version(),
            rendering_specification=_rendering_bytes(),
        )


def test_current_pointer_is_digest_bound_to_snapshot(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    create_template_library(
        root,
        definition=_definition(),
        initial_version=_version(),
        rendering_specification=_rendering_bytes(),
    )
    path = template_current_path(root, "template-1")
    value = json.loads(path.read_text(encoding="utf-8"))
    value["snapshot_sha256"] = "0" * 64
    path.write_bytes(
        (
            json.dumps(
                value,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")
    )
    with pytest.raises(TemplateStorageIntegrityError, match="digest mismatch"):
        load_current_template(root, "template-1")


def test_record_body_tampering_is_detected(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    create_template_library(
        root,
        definition=_definition(),
        initial_version=_version(),
        rendering_specification=_rendering_bytes(),
    )
    path = template_record_revision_path(
        root,
        "template-1",
        "template_definition",
        "template-1",
        1,
    )
    value = json.loads(path.read_text(encoding="utf-8"))
    value["body"]["name"] = "Tampered"
    path.write_bytes(
        (
            json.dumps(
                value,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")
    )
    with pytest.raises(
        TemplateStorageIntegrityError,
        match="record digest mismatch",
    ):
        load_current_template(root, "template-1")


def test_rendering_asset_tampering_is_detected(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    create_template_library(
        root,
        definition=_definition(),
        initial_version=_version(),
        rendering_specification=_rendering_bytes(),
    )
    path = template_rendering_specification_path(
        root,
        "template-1",
        "seminar-form-v1",
    )
    path.write_bytes(b"tampered")
    with pytest.raises(TemplateStorageIntegrityError, match="digest mismatch"):
        load_current_template(root, "template-1")


def test_snapshot_chain_and_exact_snapshot_are_verified(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    loaded = create_template_library(
        root,
        definition=_definition(),
        initial_version=_version(),
        rendering_specification=_rendering_bytes(),
    )
    snapshot, digest = load_template_snapshot(root, "template-1", 1)
    assert snapshot.snapshot_revision == 1
    assert digest == loaded.snapshot_sha256

    path = template_snapshot_path(root, "template-1", 1)
    value = json.loads(path.read_text(encoding="utf-8"))
    value["head_template_version_id"] = "other-version"
    path.write_text(
        json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(TemplateStorageIntegrityError):
        load_current_template(root, "template-1")


def test_missing_exact_version_is_not_found(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    create_template_library(
        root,
        definition=_definition(),
        initial_version=_version(),
        rendering_specification=_rendering_bytes(),
    )
    with pytest.raises(TemplateStorageNotFoundError):
        load_template_version(root, "template-1", "missing-version")


def test_templates_remain_outside_activity_native_registry() -> None:
    registered = {item.model_type for item in RECORD_DESCRIPTORS}
    assert TemplateDefinition not in registered
    assert TemplateVersion not in registered


def test_no_activity_or_route_side_effects(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    create_template_library(
        root,
        definition=_definition(),
        initial_version=_version(),
        rendering_specification=_rendering_bytes(),
    )
    assert not (root / "classes").exists()
    assert tuple(root.rglob("routes")) == ()


def _successor(
    *,
    template_version_id: str = "template-version-2",
    rendering_bytes: bytes = b"concord-template-rendering-v2\nsuccessor\n",
) -> tuple[TemplateVersion, bytes]:
    digest = hashlib.sha256(rendering_bytes).hexdigest()
    previous = _version(status="active")
    version = replace(
        previous,
        template_version_id=template_version_id,
        version_label="v2",
        revision_sequence=2,
        rendering_specification_reference="seminar-form-v2",
        rendering_specification_sha256=digest,
        status="draft",
        supersedes_template_version_id="template-version-1",
        created_provenance=replace(
            _provenance(),
            timestamp="2026-08-24T18:45:00-04:00",
        ),
    )
    return version, rendering_bytes


def test_successor_is_draft_head_without_changing_current(
    tmp_path: Path,
) -> None:
    from concord.template_storage import create_successor_template_version

    root = _workspace(tmp_path)
    initial = create_template_library(
        root,
        definition=_definition(status="active"),
        initial_version=_version(status="active"),
        rendering_specification=_rendering_bytes(),
    )
    successor, rendering = _successor()
    updated = create_successor_template_version(
        root,
        "template-1",
        successor=successor,
        rendering_specification=rendering,
        expected_snapshot_revision=initial.snapshot_revision,
        operation_provenance=_provenance(),
    )
    assert updated.snapshot_revision == 2
    assert updated.current_template_version_id == "template-version-1"
    assert updated.head_template_version_id == "template-version-2"
    assert updated.versions == (_version(status="active"), successor)


def test_successor_rejects_stale_snapshot_and_branch(tmp_path: Path) -> None:
    from concord.template_storage import (
        TemplateStorageConflictError,
        create_successor_template_version,
    )

    root = _workspace(tmp_path)
    initial = create_template_library(
        root,
        definition=_definition(status="active"),
        initial_version=_version(status="active"),
        rendering_specification=_rendering_bytes(),
    )
    successor, rendering = _successor()
    current = create_successor_template_version(
        root,
        "template-1",
        successor=successor,
        rendering_specification=rendering,
        expected_snapshot_revision=initial.snapshot_revision,
        operation_provenance=_provenance(),
    )
    with pytest.raises(
        TemplateStorageConflictError,
        match="expected Template snapshot",
    ):
        create_successor_template_version(
            root,
            "template-1",
            successor=replace(
                successor,
                template_version_id="template-version-3",
                revision_sequence=3,
                supersedes_template_version_id="template-version-2",
            ),
            rendering_specification=rendering,
            expected_snapshot_revision=1,
            operation_provenance=_provenance(),
        )

    branch, branch_bytes = _successor(template_version_id="branch-version")
    with pytest.raises(TemplateStorageWriteError, match=r"head \+ 1"):
        create_successor_template_version(
            root,
            "template-1",
            successor=branch,
            rendering_specification=branch_bytes,
            expected_snapshot_revision=current.snapshot_revision,
            operation_provenance=_provenance(),
        )


def test_activation_supersedes_previous_current_atomically(
    tmp_path: Path,
) -> None:
    from concord.template_storage import (
        activate_template_version,
        create_successor_template_version,
    )

    root = _workspace(tmp_path)
    initial = create_template_library(
        root,
        definition=_definition(status="active"),
        initial_version=_version(status="active"),
        rendering_specification=_rendering_bytes(),
    )
    successor, rendering = _successor()
    revised = create_successor_template_version(
        root,
        "template-1",
        successor=successor,
        rendering_specification=rendering,
        expected_snapshot_revision=initial.snapshot_revision,
        operation_provenance=_provenance(),
    )
    active = activate_template_version(
        root,
        "template-1",
        "template-version-2",
        expected_snapshot_revision=revised.snapshot_revision,
        operation_provenance=_provenance(),
    )
    assert active.snapshot_revision == 3
    assert active.current_template_version_id == "template-version-2"
    assert active.head_template_version_id == "template-version-2"
    assert tuple(item.status for item in active.versions) == (
        "superseded",
        "active",
    )


def test_activation_of_non_head_is_rejected(tmp_path: Path) -> None:
    from concord.template_storage import (
        TemplateStorageConflictError,
        activate_template_version,
        create_successor_template_version,
    )

    root = _workspace(tmp_path)
    initial = create_template_library(
        root,
        definition=_definition(status="active"),
        initial_version=_version(status="active"),
        rendering_specification=_rendering_bytes(),
    )
    successor, rendering = _successor()
    revised = create_successor_template_version(
        root,
        "template-1",
        successor=successor,
        rendering_specification=rendering,
        expected_snapshot_revision=initial.snapshot_revision,
        operation_provenance=_provenance(),
    )
    with pytest.raises(TemplateStorageConflictError, match="lineage head"):
        activate_template_version(
            root,
            "template-1",
            "template-version-1",
            expected_snapshot_revision=revised.snapshot_revision,
            operation_provenance=_provenance(),
        )


def test_definition_metadata_revision_and_exact_noop(tmp_path: Path) -> None:
    from concord.template_storage import update_template_definition

    root = _workspace(tmp_path)
    initial = create_template_library(
        root,
        definition=_definition(),
        initial_version=_version(),
        rendering_specification=_rendering_bytes(),
    )
    changed_definition = replace(
        initial.definition,
        name="Updated Seminar Discussion Map",
        description=None,
    )
    changed = update_template_definition(
        root,
        "template-1",
        definition=changed_definition,
        expected_snapshot_revision=initial.snapshot_revision,
        operation_provenance=_provenance(),
    )
    assert changed.snapshot_revision == 2
    assert changed.definition == changed_definition

    noop = update_template_definition(
        root,
        "template-1",
        definition=changed_definition,
        expected_snapshot_revision=changed.snapshot_revision,
        operation_provenance=_provenance(),
    )
    assert noop.snapshot_revision == 2


def test_definition_update_cannot_change_immutable_fields(
    tmp_path: Path,
) -> None:
    from concord.template_storage import update_template_definition

    root = _workspace(tmp_path)
    initial = create_template_library(
        root,
        definition=_definition(),
        initial_version=_version(),
        rendering_specification=_rendering_bytes(),
    )
    with pytest.raises(TemplateStorageWriteError, match="only name"):
        update_template_definition(
            root,
            "template-1",
            definition=replace(
                initial.definition,
                artifact_category="project_record",
            ),
            expected_snapshot_revision=initial.snapshot_revision,
            operation_provenance=_provenance(),
        )


def test_retire_noncurrent_draft_version_preserves_history(
    tmp_path: Path,
) -> None:
    from concord.template_storage import (
        create_successor_template_version,
        retire_template_version,
    )

    root = _workspace(tmp_path)
    initial = create_template_library(
        root,
        definition=_definition(status="active"),
        initial_version=_version(status="active"),
        rendering_specification=_rendering_bytes(),
    )
    successor, rendering = _successor()
    revised = create_successor_template_version(
        root,
        "template-1",
        successor=successor,
        rendering_specification=rendering,
        expected_snapshot_revision=initial.snapshot_revision,
        operation_provenance=_provenance(),
    )
    retired = retire_template_version(
        root,
        "template-1",
        "template-version-2",
        expected_snapshot_revision=revised.snapshot_revision,
        operation_provenance=_provenance(),
    )
    assert retired.current_template_version_id == "template-version-1"
    assert retired.head_template_version_id == "template-version-2"
    assert tuple(item.status for item in retired.versions) == (
        "active",
        "retired",
    )
    assert load_template_version(
        root,
        "template-1",
        "template-version-2",
    ).status == "retired"


def test_current_version_cannot_be_retired_independently(
    tmp_path: Path,
) -> None:
    from concord.template_storage import (
        TemplateStorageConflictError,
        retire_template_version,
    )

    root = _workspace(tmp_path)
    initial = create_template_library(
        root,
        definition=_definition(status="active"),
        initial_version=_version(status="active"),
        rendering_specification=_rendering_bytes(),
    )
    with pytest.raises(TemplateStorageConflictError, match="cannot be retired"):
        retire_template_version(
            root,
            "template-1",
            "template-version-1",
            expected_snapshot_revision=initial.snapshot_revision,
            operation_provenance=_provenance(),
        )


def test_whole_template_retirement_is_nondestructive(tmp_path: Path) -> None:
    from concord.template_storage import retire_template

    root = _workspace(tmp_path)
    initial = create_template_library(
        root,
        definition=_definition(status="active"),
        initial_version=_version(status="active"),
        rendering_specification=_rendering_bytes(),
    )
    retired = retire_template(
        root,
        "template-1",
        expected_snapshot_revision=initial.snapshot_revision,
        operation_provenance=_provenance(),
    )
    assert retired.snapshot_revision == 2
    assert retired.definition.status == "retired"
    assert retired.current_template_version_id is None
    assert retired.head_template_version_id == "template-version-1"
    assert retired.versions[0].status == "retired"
    asset = template_rendering_specification_path(
        root,
        "template-1",
        "seminar-form-v1",
    )
    assert asset.read_bytes() == _rendering_bytes()


def test_orphan_snapshot_blocks_mutation(tmp_path: Path) -> None:
    from concord.template_storage import update_template_definition

    root = _workspace(tmp_path)
    initial = create_template_library(
        root,
        definition=_definition(),
        initial_version=_version(),
        rendering_specification=_rendering_bytes(),
    )
    orphan = template_snapshot_path(root, "template-1", 2)
    orphan.write_bytes(
        template_snapshot_path(root, "template-1", 1).read_bytes()
    )
    with pytest.raises(
        TemplateStorageIntegrityError,
        match="noncontiguous or contains orphans",
    ):
        update_template_definition(
            root,
            "template-1",
            definition=replace(initial.definition, name="Changed"),
            expected_snapshot_revision=initial.snapshot_revision,
            operation_provenance=_provenance(),
        )


def test_write_lock_conflict_fails_closed(tmp_path: Path) -> None:
    from concord.template_storage import (
        TemplateStorageConflictError,
        update_template_definition,
    )
    from concord.template_storage_paths import template_write_lock_path

    root = _workspace(tmp_path)
    initial = create_template_library(
        root,
        definition=_definition(),
        initial_version=_version(),
        rendering_specification=_rendering_bytes(),
    )
    lock = template_write_lock_path(root, "template-1")
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_bytes(b"existing lock")
    with pytest.raises(TemplateStorageConflictError, match="write lock"):
        update_template_definition(
            root,
            "template-1",
            definition=replace(initial.definition, name="Changed"),
            expected_snapshot_revision=initial.snapshot_revision,
            operation_provenance=_provenance(),
        )


def _authoring_document_bytes(
    *,
    include_definition: bool,
    version_label: str = "v1",
    rendering_reference: str = "seminar-form-v1",
) -> bytes:
    from concord.template_serialization import (
        canonical_json_bytes,
        template_to_dict,
    )

    source_version = _version()
    version_mapping = template_to_dict(source_version)
    authoring = {
        "schema_version": "concord_template_authoring_v1",
        "artifact_category": "discussion_record",
        "definition": (
            {
                "name": "Seminar Discussion Map",
                "purpose": "Capture collaborative seminar evidence.",
                "description": "Synthetic reusable Template.",
            }
            if include_definition
            else None
        ),
        "version": {
            "version_label": version_label,
            "rendering_contract_version": (
                source_version.rendering_contract_version
            ),
            "rendering_specification_reference": rendering_reference,
            "page_manifest": version_mapping["page_manifest"],
            "rendering_inputs": version_mapping["rendering_inputs"],
            "default_expected_return_status": (
                source_version.default_expected_return_status
            ),
            "default_privacy_policy": (
                version_mapping["default_privacy_policy"]
            ),
            "compatibility": version_mapping["compatibility"],
            "default_authorship_expectation": None,
            "default_subject_expectation": None,
        },
    }
    return canonical_json_bytes(authoring)


def test_prepare_commit_template_create_uses_strict_authoring(
    tmp_path: Path,
) -> None:
    from concord.workflows.models import WorkflowActor
    from concord.workflows.template import (
        PrepareTemplateCreateRequest,
        commit_template_create,
        prepare_template_create,
    )

    root = _workspace(tmp_path)
    authoring = tmp_path / "template-authoring.json"
    rendering = tmp_path / "rendering.bin"
    authoring.write_bytes(
        _authoring_document_bytes(include_definition=True)
    )
    rendering.write_bytes(_rendering_bytes())
    prepared = prepare_template_create(
        PrepareTemplateCreateRequest(
            template_id="workflow-template",
            template_version_id="workflow-version-1",
            authoring_file=authoring,
            rendering_specification=rendering,
            actor=WorkflowActor(actor_id="teacher-1"),
            activate=False,
        ),
        workspace_root=root,
    )
    assert prepared.definition.status == "draft"
    assert prepared.version.status == "draft"
    assert prepared.version.revision_sequence == 1
    result = commit_template_create(prepared, workspace_root=root)
    assert result.template_id == "workflow-template"
    assert result.snapshot_revision == 1
    assert result.current_template_version_id is None


def test_template_create_detects_rendering_change_after_prepare(
    tmp_path: Path,
) -> None:
    from concord.workflows.errors import ConcordWorkflowConflictError
    from concord.workflows.models import WorkflowActor
    from concord.workflows.template import (
        PrepareTemplateCreateRequest,
        commit_template_create,
        prepare_template_create,
    )

    root = _workspace(tmp_path)
    authoring = tmp_path / "template-authoring.json"
    rendering = tmp_path / "rendering.bin"
    authoring.write_bytes(
        _authoring_document_bytes(include_definition=True)
    )
    rendering.write_bytes(_rendering_bytes())
    prepared = prepare_template_create(
        PrepareTemplateCreateRequest(
            template_id="workflow-template",
            template_version_id="workflow-version-1",
            authoring_file=authoring,
            rendering_specification=rendering,
            actor=WorkflowActor(actor_id="teacher-1"),
        ),
        workspace_root=root,
    )
    rendering.write_bytes(b"changed after preview")
    with pytest.raises(
        ConcordWorkflowConflictError,
        match="changed after preparation",
    ):
        commit_template_create(prepared, workspace_root=root)
    assert list_template_ids(root) == ()


def test_template_create_detects_authoring_change_after_prepare(
    tmp_path: Path,
) -> None:
    from concord.workflows.errors import ConcordWorkflowConflictError
    from concord.workflows.models import WorkflowActor
    from concord.workflows.template import (
        PrepareTemplateCreateRequest,
        commit_template_create,
        prepare_template_create,
    )

    root = _workspace(tmp_path)
    authoring = tmp_path / "template-authoring.json"
    rendering = tmp_path / "rendering.bin"
    authoring.write_bytes(
        _authoring_document_bytes(include_definition=True)
    )
    rendering.write_bytes(_rendering_bytes())
    prepared = prepare_template_create(
        PrepareTemplateCreateRequest(
            template_id="workflow-template",
            template_version_id="workflow-version-1",
            authoring_file=authoring,
            rendering_specification=rendering,
            actor=WorkflowActor(actor_id="teacher-1"),
        ),
        workspace_root=root,
    )
    authoring.write_bytes(
        _authoring_document_bytes(
            include_definition=True,
            version_label="changed",
        )
    )
    with pytest.raises(
        ConcordWorkflowConflictError,
        match="changed after preparation",
    ):
        commit_template_create(prepared, workspace_root=root)


def test_prepare_commit_revision_then_activation(tmp_path: Path) -> None:
    from concord.workflows.models import WorkflowActor
    from concord.workflows.template import (
        PrepareTemplateActivationRequest,
        PrepareTemplateRevisionRequest,
        commit_template_activation,
        commit_template_revision,
        prepare_template_activation,
        prepare_template_revision,
    )

    root = _workspace(tmp_path)
    initial = create_template_library(
        root,
        definition=_definition(status="active"),
        initial_version=_version(status="active"),
        rendering_specification=_rendering_bytes(),
    )
    authoring = tmp_path / "revision-authoring.json"
    rendering = tmp_path / "rendering-v2.bin"
    authoring.write_bytes(
        _authoring_document_bytes(
            include_definition=False,
            version_label="v2",
            rendering_reference="seminar-form-v2",
        )
    )
    rendering.write_bytes(b"rendering-v2")
    actor = WorkflowActor(actor_id="teacher-1")
    prepared_revision = prepare_template_revision(
        PrepareTemplateRevisionRequest(
            template_id="template-1",
            template_version_id="template-version-2",
            authoring_file=authoring,
            rendering_specification=rendering,
            expected_snapshot_revision=initial.snapshot_revision,
            actor=actor,
        ),
        workspace_root=root,
    )
    revised = commit_template_revision(
        prepared_revision,
        workspace_root=root,
    )
    assert revised.snapshot_revision == 2
    assert revised.current_template_version_id == "template-version-1"
    assert revised.head_template_version_id == "template-version-2"

    prepared_activation = prepare_template_activation(
        PrepareTemplateActivationRequest(
            template_id="template-1",
            template_version_id="template-version-2",
            expected_snapshot_revision=revised.snapshot_revision,
            actor=actor,
        ),
        workspace_root=root,
    )
    activated = commit_template_activation(
        prepared_activation,
        workspace_root=root,
    )
    assert activated.snapshot_revision == 3
    assert activated.current_template_version_id == "template-version-2"


def test_template_workflow_metadata_update_and_retirement(
    tmp_path: Path,
) -> None:
    from concord.workflows.models import WorkflowActor
    from concord.workflows.template import (
        PrepareTemplateRetireRequest,
        PrepareTemplateUpdateRequest,
        commit_template_retire,
        commit_template_update,
        prepare_template_retire,
        prepare_template_update,
    )

    root = _workspace(tmp_path)
    initial = create_template_library(
        root,
        definition=_definition(status="active"),
        initial_version=_version(status="active"),
        rendering_specification=_rendering_bytes(),
    )
    actor = WorkflowActor(actor_id="teacher-1")
    prepared_update = prepare_template_update(
        PrepareTemplateUpdateRequest(
            template_id="template-1",
            name="Renamed Template",
            purpose="Updated purpose.",
            description=None,
            expected_snapshot_revision=initial.snapshot_revision,
            actor=actor,
        ),
        workspace_root=root,
    )
    updated = commit_template_update(
        prepared_update,
        workspace_root=root,
    )
    assert updated.snapshot_revision == 2
    assert load_current_template(root, "template-1").definition.name == (
        "Renamed Template"
    )

    prepared_retire = prepare_template_retire(
        PrepareTemplateRetireRequest(
            template_id="template-1",
            expected_snapshot_revision=updated.snapshot_revision,
            actor=actor,
        ),
        workspace_root=root,
    )
    retired = commit_template_retire(
        prepared_retire,
        workspace_root=root,
    )
    assert retired.snapshot_revision == 3
    assert retired.status == "retired"
    assert retired.current_template_version_id is None


def test_template_workflow_read_only_listing_writes_nothing(
    tmp_path: Path,
) -> None:
    from concord.workflows.template import list_templates

    root = _workspace(tmp_path)
    before = tuple(root.rglob("*"))
    assert list_templates(workspace_root=root) == ()
    assert tuple(root.rglob("*")) == before

def test_template_revision_detects_authoring_change_after_prepare(
    tmp_path: Path,
) -> None:
    from concord.workflows.errors import ConcordWorkflowConflictError
    from concord.workflows.models import WorkflowActor
    from concord.workflows.template import (
        PrepareTemplateRevisionRequest,
        commit_template_revision,
        prepare_template_revision,
    )

    root = _workspace(tmp_path)
    initial = create_template_library(
        root,
        definition=_definition(status="active"),
        initial_version=_version(status="active"),
        rendering_specification=_rendering_bytes(),
    )
    authoring = tmp_path / "revision-authoring.json"
    rendering = tmp_path / "rendering-v2.bin"
    authoring.write_bytes(
        _authoring_document_bytes(
            include_definition=False,
            version_label="v2",
            rendering_reference="seminar-form-v2",
        )
    )
    rendering.write_bytes(b"rendering-v2")
    prepared = prepare_template_revision(
        PrepareTemplateRevisionRequest(
            template_id="template-1",
            template_version_id="template-version-2",
            authoring_file=authoring,
            rendering_specification=rendering,
            expected_snapshot_revision=initial.snapshot_revision,
            actor=WorkflowActor(actor_id="teacher-1"),
        ),
        workspace_root=root,
    )
    authoring.write_bytes(
        _authoring_document_bytes(
            include_definition=False,
            version_label="changed-after-prepare",
            rendering_reference="seminar-form-v2",
        )
    )
    with pytest.raises(
        ConcordWorkflowConflictError,
        match="changed after preparation",
    ):
        commit_template_revision(prepared, workspace_root=root)
    current = load_current_template(root, "template-1")
    assert current.snapshot_revision == 1
    assert current.head_template_version_id == "template-version-1"
