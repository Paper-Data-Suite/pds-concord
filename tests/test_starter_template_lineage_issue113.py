from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path

import pytest

from concord.models import ActorReference, Provenance
from concord.starter_templates.catalog import get_starter_template
from concord.starter_templates.lineage import (
    STARTER_LINEAGE_CONFLICT,
    STARTER_LINEAGE_CURRENT,
    STARTER_LINEAGE_MISSING,
    STARTER_LINEAGE_UPGRADE_AVAILABLE,
    PackagedStarterTemplateLineage,
    PackagedStarterTemplateVersion,
    StarterTemplateLineageConflictError,
    commit_packaged_starter_lineage_reconciliation,
    inspect_packaged_starter_lineage,
    prepare_packaged_starter_lineage_reconciliation,
)
from concord.template_storage import (
    create_successor_template_version,
    create_template_library,
    load_template_rendering_specification,
    load_template_snapshot,
    retire_template,
    update_template_definition,
)


def _provenance(note: str) -> Provenance:
    return Provenance(
        actor=ActorReference(
            actor_kind="authorized_adult",
            actor_id="teacher-1",
            owning_system="concord",
        ),
        timestamp="2026-09-19T13:00:00-04:00",
        source_kind="imported",
        application_version="0.3.0",
        note=note,
    )


def _lineage() -> PackagedStarterTemplateLineage:
    entry = get_starter_template("think_pair_share")
    definition, v1 = entry.build_template_records(
        created_provenance=_provenance("Synthetic package v1."),
        status="active",
    )
    v1_bytes = entry.rendering_specification_bytes()
    v2_bytes = b"synthetic-package-v2-rendering\n"
    v2 = replace(
        v1,
        template_version_id="starter-think-pair-share-v2",
        version_label="Synthetic package v2",
        revision_sequence=2,
        rendering_specification_reference=(
            "starter-think-pair-share-layout-v2"
        ),
        rendering_specification_sha256=hashlib.sha256(v2_bytes).hexdigest(),
        supersedes_template_version_id=v1.template_version_id,
        created_provenance=_provenance("Synthetic package v2."),
    )
    return PackagedStarterTemplateLineage(
        starter_key=entry.starter_key,
        definition=definition,
        versions=(
            PackagedStarterTemplateVersion(
                version=v1,
                rendering_specification=v1_bytes,
            ),
            PackagedStarterTemplateVersion(
                version=v2,
                rendering_specification=v2_bytes,
            ),
        ),
    )


def _empty_workspace(tmp_path: Path) -> Path:
    root = tmp_path / "workspace"
    root.mkdir()
    return root


def _install_only_v1(
    root: Path,
    lineage: PackagedStarterTemplateLineage,
):
    first = lineage.versions[0]
    return create_template_library(
        root,
        definition=lineage.definition,
        initial_version=first.version,
        rendering_specification=first.rendering_specification,
    )


def test_absent_lineage_is_missing_and_prepare_is_read_only(
    tmp_path: Path,
) -> None:
    root = _empty_workspace(tmp_path)
    lineage = _lineage()

    inspection = inspect_packaged_starter_lineage(root, lineage)
    assert inspection.state == STARTER_LINEAGE_MISSING
    assert inspection.loaded is None

    prepared = prepare_packaged_starter_lineage_reconciliation(root, lineage)
    assert prepared.initial_state == STARTER_LINEAGE_MISSING
    assert tuple(root.iterdir()) == ()


def test_fresh_reconciliation_installs_v1_then_v2_without_rewriting_history(
    tmp_path: Path,
) -> None:
    root = _empty_workspace(tmp_path)
    lineage = _lineage()

    result = commit_packaged_starter_lineage_reconciliation(
        prepare_packaged_starter_lineage_reconciliation(root, lineage),
        workspace_root=root,
    )

    assert result.outcome == "installed"
    loaded = result.loaded
    assert tuple(item.template_version_id for item in loaded.versions) == (
        "starter-think-pair-share-v1",
        "starter-think-pair-share-v2",
    )
    assert tuple(item.status for item in loaded.versions) == (
        "superseded",
        "active",
    )
    assert (
        loaded.current_template_version_id
        == "starter-think-pair-share-v2"
    )
    assert (
        load_template_rendering_specification(
            root,
            lineage.template_id,
            "starter-think-pair-share-v1",
        )
        == lineage.versions[0].rendering_specification
    )

    original_snapshot, _ = load_template_snapshot(
        root,
        lineage.template_id,
        1,
    )
    assert (
        original_snapshot.current_template_version_id
        == "starter-think-pair-share-v1"
    )


def test_exact_v1_workspace_is_upgrade_available_then_v2_becomes_current(
    tmp_path: Path,
) -> None:
    root = _empty_workspace(tmp_path)
    lineage = _lineage()
    before = _install_only_v1(root, lineage)

    inspection = inspect_packaged_starter_lineage(root, lineage)
    assert inspection.state == STARTER_LINEAGE_UPGRADE_AVAILABLE
    assert inspection.matched_version_count == 1

    result = commit_packaged_starter_lineage_reconciliation(
        prepare_packaged_starter_lineage_reconciliation(root, lineage),
        workspace_root=root,
    )

    assert result.outcome == "upgraded"
    assert result.loaded.snapshot_revision > before.snapshot_revision
    assert tuple(item.status for item in result.loaded.versions) == (
        "superseded",
        "active",
    )


def test_complete_package_lineage_replays_without_writes(tmp_path: Path) -> None:
    root = _empty_workspace(tmp_path)
    lineage = _lineage()
    first = commit_packaged_starter_lineage_reconciliation(
        prepare_packaged_starter_lineage_reconciliation(root, lineage),
        workspace_root=root,
    )

    prepared = prepare_packaged_starter_lineage_reconciliation(root, lineage)
    assert prepared.initial_state == STARTER_LINEAGE_CURRENT
    replay = commit_packaged_starter_lineage_reconciliation(
        prepared,
        workspace_root=root,
    )

    assert replay.outcome == "already_current"
    assert replay.loaded.snapshot_revision == first.loaded.snapshot_revision
    assert replay.loaded.snapshot_sha256 == first.loaded.snapshot_sha256


def test_interrupted_exact_draft_successor_is_recovered_by_activation(
    tmp_path: Path,
) -> None:
    root = _empty_workspace(tmp_path)
    lineage = _lineage()
    v1_loaded = _install_only_v1(root, lineage)
    packaged_v2 = lineage.versions[1]
    draft_v2 = replace(packaged_v2.version, status="draft")

    partial = create_successor_template_version(
        root,
        lineage.template_id,
        successor=draft_v2,
        rendering_specification=packaged_v2.rendering_specification,
        expected_snapshot_revision=v1_loaded.snapshot_revision,
        operation_provenance=draft_v2.created_provenance,
    )
    assert partial.head_version.status == "draft"
    assert partial.current_template_version_id == v1_loaded.head_template_version_id

    inspection = inspect_packaged_starter_lineage(root, lineage)
    assert inspection.state == STARTER_LINEAGE_UPGRADE_AVAILABLE
    result = commit_packaged_starter_lineage_reconciliation(
        prepare_packaged_starter_lineage_reconciliation(root, lineage),
        workspace_root=root,
    )
    assert result.outcome == "upgraded"
    assert result.loaded.head_version.status == "active"


def test_teacher_authored_successor_fails_closed(tmp_path: Path) -> None:
    root = _empty_workspace(tmp_path)
    lineage = _lineage()
    loaded = _install_only_v1(root, lineage)
    package_v2 = lineage.versions[1].version
    teacher_bytes = b"teacher-owned-successor\n"
    teacher_v2 = replace(
        package_v2,
        template_version_id="teacher-owned-successor-v2",
        rendering_specification_reference="teacher-owned-layout-v2",
        rendering_specification_sha256=hashlib.sha256(
            teacher_bytes
        ).hexdigest(),
        status="draft",
    )
    create_successor_template_version(
        root,
        lineage.template_id,
        successor=teacher_v2,
        rendering_specification=teacher_bytes,
        expected_snapshot_revision=loaded.snapshot_revision,
        operation_provenance=teacher_v2.created_provenance,
    )

    inspection = inspect_packaged_starter_lineage(root, lineage)
    assert inspection.state == STARTER_LINEAGE_CONFLICT
    with pytest.raises(StarterTemplateLineageConflictError):
        prepare_packaged_starter_lineage_reconciliation(root, lineage)


def test_retired_exact_v1_is_not_auto_upgraded(tmp_path: Path) -> None:
    root = _empty_workspace(tmp_path)
    lineage = _lineage()
    loaded = _install_only_v1(root, lineage)
    retire_template(
        root,
        lineage.template_id,
        expected_snapshot_revision=loaded.snapshot_revision,
        operation_provenance=_provenance("Teacher retired starter."),
    )

    inspection = inspect_packaged_starter_lineage(root, lineage)
    assert inspection.state == STARTER_LINEAGE_CONFLICT
    assert inspection.reason is not None
    assert "retired" in inspection.reason


def test_retired_complete_package_lineage_is_respected_as_current(
    tmp_path: Path,
) -> None:
    root = _empty_workspace(tmp_path)
    lineage = _lineage()
    installed = commit_packaged_starter_lineage_reconciliation(
        prepare_packaged_starter_lineage_reconciliation(root, lineage),
        workspace_root=root,
    )
    retired = retire_template(
        root,
        lineage.template_id,
        expected_snapshot_revision=installed.loaded.snapshot_revision,
        operation_provenance=_provenance("Teacher retired complete starter."),
    )

    inspection = inspect_packaged_starter_lineage(root, lineage)
    assert inspection.state == STARTER_LINEAGE_CURRENT
    assert inspection.loaded is not None
    assert inspection.loaded.snapshot_revision == retired.snapshot_revision


def test_upgrade_commit_rejects_stale_snapshot_even_for_metadata_only_change(
    tmp_path: Path,
) -> None:
    root = _empty_workspace(tmp_path)
    lineage = _lineage()
    loaded = _install_only_v1(root, lineage)
    prepared = prepare_packaged_starter_lineage_reconciliation(root, lineage)

    revised = replace(loaded.definition, name="Teacher Custom Name")
    update_template_definition(
        root,
        lineage.template_id,
        definition=revised,
        expected_snapshot_revision=loaded.snapshot_revision,
        operation_provenance=_provenance("Teacher metadata edit."),
    )

    with pytest.raises(
        StarterTemplateLineageConflictError,
        match="snapshot changed",
    ):
        commit_packaged_starter_lineage_reconciliation(
            prepared,
            workspace_root=root,
        )


def test_exact_package_v1_bytes_remain_available_after_upgrade(
    tmp_path: Path,
) -> None:
    root = _empty_workspace(tmp_path)
    lineage = _lineage()
    _install_only_v1(root, lineage)
    before_bytes = load_template_rendering_specification(
        root,
        lineage.template_id,
        lineage.versions[0].version.template_version_id,
    )

    commit_packaged_starter_lineage_reconciliation(
        prepare_packaged_starter_lineage_reconciliation(root, lineage),
        workspace_root=root,
    )

    after_bytes = load_template_rendering_specification(
        root,
        lineage.template_id,
        lineage.versions[0].version.template_version_id,
    )
    assert after_bytes == before_bytes
    assert after_bytes == lineage.versions[0].rendering_specification
