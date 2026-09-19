from __future__ import annotations

import hashlib
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest

from concord.starter_templates.catalog import (
    StarterTemplateCatalogEntry,
    get_starter_template,
    list_starter_templates,
)
from concord.starter_templates.catalog_lineage import (
    build_starter_template_lineage,
)
from concord.starter_templates.lineage import (
    PackagedStarterTemplateLineage,
    PackagedStarterTemplateVersion,
)
from concord.template_storage import load_current_template
from concord.workflows import starter_template as starter_workflow
from concord.workflows.context import provenance
from concord.workflows.models import WorkflowActor
from concord.workflows.starter_template import (
    STARTER_INSTALLATION_ALREADY_INSTALLED,
    STARTER_INSTALLATION_UPGRADE_AVAILABLE,
    PrepareStarterTemplateInstallAllRequest,
    PrepareStarterTemplateInstallRequest,
    commit_starter_template_install,
    commit_starter_template_install_all,
    get_starter_template_status,
    list_starter_template_statuses,
    prepare_starter_template_install,
    prepare_starter_template_install_all,
)


def _actor() -> WorkflowActor:
    return WorkflowActor(actor_id="teacher-1", display_label="Teacher")


def _clock() -> datetime:
    return datetime(2026, 9, 19, 17, 30, tzinfo=timezone.utc)


def _synthetic_v2_lineage(
    entry: StarterTemplateCatalogEntry,
    *,
    created_provenance,
) -> PackagedStarterTemplateLineage:
    v1_lineage = build_starter_template_lineage(
        entry,
        created_provenance=created_provenance,
    )
    v1 = v1_lineage.versions[0].version
    v2_bytes = b"issue-113-synthetic-v2-rendering\n"
    v2 = replace(
        v1,
        template_version_id=f"{entry.template_id}-v2",
        version_label="Synthetic v2",
        revision_sequence=2,
        rendering_specification_reference=f"{entry.template_id}-layout-v2",
        rendering_specification_sha256=hashlib.sha256(v2_bytes).hexdigest(),
        supersedes_template_version_id=v1.template_version_id,
    )
    return PackagedStarterTemplateLineage(
        starter_key=entry.starter_key,
        definition=v1_lineage.definition,
        versions=(
            v1_lineage.versions[0],
            PackagedStarterTemplateVersion(
                version=v2,
                rendering_specification=v2_bytes,
            ),
        ),
    )


def test_all_real_catalog_entries_remain_single_version_v1() -> None:
    created = provenance(_actor(), clock=_clock, source_kind="imported")

    for entry in list_starter_templates():
        lineage = build_starter_template_lineage(
            entry,
            created_provenance=created,
        )
        assert lineage.template_id == entry.template_id
        assert len(lineage.versions) == 1
        packaged = lineage.versions[0]
        assert packaged.version.template_version_id == entry.template_version_id
        assert packaged.version.revision_sequence == 1
        assert packaged.version.supersedes_template_version_id is None
        assert packaged.rendering_specification == (
            entry.rendering_specification_bytes()
        )


def test_existing_v1_install_all_behavior_is_unchanged(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    request = PrepareStarterTemplateInstallAllRequest(actor=_actor())

    first = commit_starter_template_install_all(
        prepare_starter_template_install_all(
            request,
            workspace_root=workspace,
            clock=_clock,
        ),
        workspace_root=workspace,
    )
    assert first.installed_count == 30
    assert first.upgraded_count == 0
    assert first.already_installed_count == 0

    statuses = list_starter_template_statuses(workspace_root=workspace)
    assert len(statuses) == 30
    assert all(
        item.installation_state == STARTER_INSTALLATION_ALREADY_INSTALLED
        for item in statuses
    )

    replay = commit_starter_template_install_all(
        prepare_starter_template_install_all(
            request,
            workspace_root=workspace,
            clock=_clock,
        ),
        workspace_root=workspace,
    )
    assert replay.installed_count == 0
    assert replay.upgraded_count == 0
    assert replay.already_installed_count == 30


def test_existing_installer_reports_and_commits_future_package_upgrade(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    entry = get_starter_template("think_pair_share")
    request = PrepareStarterTemplateInstallRequest(
        starter_key=entry.starter_key,
        actor=_actor(),
    )

    installed = commit_starter_template_install(
        prepare_starter_template_install(
            request,
            workspace_root=workspace,
            clock=_clock,
        ),
        workspace_root=workspace,
    )
    assert installed.outcome == "installed"
    assert installed.template_version_id == entry.template_version_id

    real_builder = build_starter_template_lineage

    def build_with_v2(
        candidate: StarterTemplateCatalogEntry,
        *,
        created_provenance,
    ) -> PackagedStarterTemplateLineage:
        if candidate.starter_key == entry.starter_key:
            return _synthetic_v2_lineage(
                candidate,
                created_provenance=created_provenance,
            )
        return real_builder(
            candidate,
            created_provenance=created_provenance,
        )

    monkeypatch.setattr(
        starter_workflow,
        "build_starter_template_lineage",
        build_with_v2,
    )
    monkeypatch.setattr(
        starter_workflow,
        "current_packaged_template_version_id",
        lambda candidate: (
            f"{candidate.template_id}-v2"
            if candidate.starter_key == entry.starter_key
            else candidate.template_version_id
        ),
    )

    status = get_starter_template_status(
        entry.starter_key,
        workspace_root=workspace,
    )
    assert status.installation_state == STARTER_INSTALLATION_UPGRADE_AVAILABLE
    assert status.template_version_id == f"{entry.template_id}-v2"

    prepared = prepare_starter_template_install(
        request,
        workspace_root=workspace,
        clock=_clock,
    )
    assert prepared.initial_state == STARTER_INSTALLATION_UPGRADE_AVAILABLE
    assert prepared.definition is None
    assert prepared.version is None
    assert prepared.lineage is not None

    result = commit_starter_template_install(
        prepared,
        workspace_root=workspace,
    )
    assert result.outcome == "upgraded"
    assert result.template_version_id == f"{entry.template_id}-v2"

    loaded = load_current_template(workspace, entry.template_id)
    assert tuple(item.status for item in loaded.versions) == (
        "superseded",
        "active",
    )
    assert loaded.current_template_version_id == f"{entry.template_id}-v2"


def test_install_all_counts_future_upgrade_separately(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    initial_request = PrepareStarterTemplateInstallAllRequest(actor=_actor())
    commit_starter_template_install_all(
        prepare_starter_template_install_all(
            initial_request,
            workspace_root=workspace,
            clock=_clock,
        ),
        workspace_root=workspace,
    )

    target = get_starter_template("talk_moves_observer")
    real_builder = build_starter_template_lineage

    def build_with_one_v2(
        candidate: StarterTemplateCatalogEntry,
        *,
        created_provenance,
    ) -> PackagedStarterTemplateLineage:
        if candidate.starter_key == target.starter_key:
            return _synthetic_v2_lineage(
                candidate,
                created_provenance=created_provenance,
            )
        return real_builder(
            candidate,
            created_provenance=created_provenance,
        )

    monkeypatch.setattr(
        starter_workflow,
        "build_starter_template_lineage",
        build_with_one_v2,
    )

    prepared = prepare_starter_template_install_all(
        initial_request,
        workspace_root=workspace,
        clock=_clock,
    )
    assert sum(
        item.initial_state == STARTER_INSTALLATION_UPGRADE_AVAILABLE
        for item in prepared.items
    ) == 1

    result = commit_starter_template_install_all(
        prepared,
        workspace_root=workspace,
    )
    assert result.installed_count == 0
    assert result.upgraded_count == 1
    assert result.already_installed_count == 29
