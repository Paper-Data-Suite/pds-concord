from __future__ import annotations

import hashlib
from dataclasses import replace
from datetime import datetime, timezone

import pytest

from concord.starter_templates.catalog import get_starter_template
from concord.template_storage import (
    create_template_library,
    list_template_ids,
    load_current_template,
    retire_template,
    update_template_definition,
)
from concord.workflows.context import provenance
from concord.workflows.errors import ConcordWorkflowConflictError
from concord.workflows.models import WorkflowActor
from concord.workflows.starter_template import (
    STARTER_INSTALLATION_ALREADY_INSTALLED,
    STARTER_INSTALLATION_CONFLICT,
    STARTER_INSTALLATION_MISSING,
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
    return datetime(2026, 8, 25, 17, 30, tzinfo=timezone.utc)


def test_status_listing_and_prepare_are_read_only(tmp_path) -> None:
    workspace = tmp_path / "workspace"

    statuses = list_starter_template_statuses(workspace_root=workspace)
    assert len(statuses) == 30
    assert all(
        item.installation_state == STARTER_INSTALLATION_MISSING
        for item in statuses
    )
    assert not workspace.exists()

    prepared = prepare_starter_template_install(
        PrepareStarterTemplateInstallRequest(
            starter_key="think_pair_share",
            actor=_actor(),
        ),
        workspace_root=workspace,
        clock=_clock,
    )
    assert prepared.initial_state == STARTER_INSTALLATION_MISSING
    assert prepared.definition is not None
    assert prepared.version is not None
    assert prepared.definition.status == "active"
    assert prepared.version.status == "active"
    assert prepared.definition.created_provenance.source_kind == "imported"
    assert not workspace.exists()


def test_install_one_uses_canonical_template_storage(tmp_path) -> None:
    workspace = tmp_path / "workspace"
    prepared = prepare_starter_template_install(
        PrepareStarterTemplateInstallRequest(
            starter_key="think_pair_share",
            actor=_actor(),
        ),
        workspace_root=workspace,
        clock=_clock,
    )

    result = commit_starter_template_install(
        prepared,
        workspace_root=workspace,
    )

    assert result.outcome == "installed"
    assert result.workspace_created is True
    assert list_template_ids(workspace) == ("starter-think-pair-share",)
    loaded = load_current_template(workspace, result.template_id)
    assert loaded.definition.status == "active"
    assert loaded.current_template_version_id == result.template_version_id
    assert loaded.head_template_version_id == result.template_version_id
    assert loaded.current_version is not None
    assert (
        loaded.current_version.rendering_specification_sha256
        == get_starter_template("think_pair_share").rendering_sha256()
    )


def test_repeated_exact_install_is_idempotent(tmp_path) -> None:
    workspace = tmp_path / "workspace"
    request = PrepareStarterTemplateInstallRequest(
        starter_key="venn_comparison",
        actor=_actor(),
    )
    first = commit_starter_template_install(
        prepare_starter_template_install(
            request,
            workspace_root=workspace,
            clock=_clock,
        ),
        workspace_root=workspace,
    )

    prepared = prepare_starter_template_install(
        request,
        workspace_root=workspace,
        clock=_clock,
    )
    assert prepared.initial_state == STARTER_INSTALLATION_ALREADY_INSTALLED
    assert prepared.definition is None
    assert prepared.version is None

    replay = commit_starter_template_install(
        prepared,
        workspace_root=workspace,
    )
    assert replay.outcome == STARTER_INSTALLATION_ALREADY_INSTALLED
    assert replay.snapshot_revision == first.snapshot_revision
    assert replay.snapshot_sha256 == first.snapshot_sha256


def test_teacher_metadata_revision_is_not_reset_by_reinstall(tmp_path) -> None:
    workspace = tmp_path / "workspace"
    request = PrepareStarterTemplateInstallRequest(
        starter_key="project_plan",
        actor=_actor(),
    )
    commit_starter_template_install(
        prepare_starter_template_install(
            request,
            workspace_root=workspace,
            clock=_clock,
        ),
        workspace_root=workspace,
    )
    loaded = load_current_template(workspace, "starter-project-plan")
    revised = replace(loaded.definition, name="My Project Planner")
    update_template_definition(
        workspace,
        loaded.definition.template_id,
        definition=revised,
        expected_snapshot_revision=loaded.snapshot_revision,
        operation_provenance=provenance(_actor(), clock=_clock),
    )

    status = get_starter_template_status(
        "project_plan",
        workspace_root=workspace,
    )
    assert status.installation_state == STARTER_INSTALLATION_ALREADY_INSTALLED
    replay = commit_starter_template_install(
        prepare_starter_template_install(
            request,
            workspace_root=workspace,
            clock=_clock,
        ),
        workspace_root=workspace,
    )
    assert replay.outcome == STARTER_INSTALLATION_ALREADY_INSTALLED
    assert (
        load_current_template(workspace, "starter-project-plan").definition.name
        == "My Project Planner"
    )


def test_retired_exact_starter_is_not_silently_reopened(tmp_path) -> None:
    workspace = tmp_path / "workspace"
    request = PrepareStarterTemplateInstallRequest(
        starter_key="team_health_check",
        actor=_actor(),
    )
    commit_starter_template_install(
        prepare_starter_template_install(
            request,
            workspace_root=workspace,
            clock=_clock,
        ),
        workspace_root=workspace,
    )
    loaded = load_current_template(workspace, "starter-team-health-check")
    retired = retire_template(
        workspace,
        loaded.definition.template_id,
        expected_snapshot_revision=loaded.snapshot_revision,
        operation_provenance=provenance(_actor(), clock=_clock),
    )
    assert retired.definition.status == "retired"

    status = get_starter_template_status(
        "team_health_check",
        workspace_root=workspace,
    )
    assert status.installation_state == STARTER_INSTALLATION_ALREADY_INSTALLED
    replay = commit_starter_template_install(
        prepare_starter_template_install(
            request,
            workspace_root=workspace,
            clock=_clock,
        ),
        workspace_root=workspace,
    )
    assert replay.outcome == STARTER_INSTALLATION_ALREADY_INSTALLED
    assert (
        load_current_template(workspace, "starter-team-health-check")
        .definition.status
        == "retired"
    )


def test_incompatible_existing_identity_is_explicit_conflict(tmp_path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    entry = get_starter_template("comparison_matrix")
    created = provenance(_actor(), clock=_clock, source_kind="imported")
    definition, version = entry.build_template_records(
        created_provenance=created,
        status="active",
    )
    collision_bytes = b"incompatible-rendering-specification\n"
    collision = replace(
        version,
        rendering_specification_reference="collision-layout",
        rendering_specification_sha256=hashlib.sha256(
            collision_bytes
        ).hexdigest(),
    )
    create_template_library(
        workspace,
        definition=definition,
        initial_version=collision,
        rendering_specification=collision_bytes,
    )

    status = get_starter_template_status(
        "comparison_matrix",
        workspace_root=workspace,
    )
    assert status.installation_state == STARTER_INSTALLATION_CONFLICT
    with pytest.raises(ConcordWorkflowConflictError, match="incompatible"):
        prepare_starter_template_install(
            PrepareStarterTemplateInstallRequest(
                starter_key="comparison_matrix",
                actor=_actor(),
            ),
            workspace_root=workspace,
            clock=_clock,
        )


def test_install_all_installs_thirty_and_replays_idempotently(tmp_path) -> None:
    workspace = tmp_path / "workspace"
    request = PrepareStarterTemplateInstallAllRequest(actor=_actor())

    prepared = prepare_starter_template_install_all(
        request,
        workspace_root=workspace,
        clock=_clock,
    )
    assert len(prepared.items) == 30
    assert all(
        item.initial_state == STARTER_INSTALLATION_MISSING
        for item in prepared.items
    )
    assert not workspace.exists()

    result = commit_starter_template_install_all(
        prepared,
        workspace_root=workspace,
    )
    assert len(result.results) == 30
    assert result.installed_count == 30
    assert result.already_installed_count == 0
    assert len(list_template_ids(workspace)) == 30

    replay = commit_starter_template_install_all(
        prepare_starter_template_install_all(
            request,
            workspace_root=workspace,
            clock=_clock,
        ),
        workspace_root=workspace,
    )
    assert replay.installed_count == 0
    assert replay.already_installed_count == 30
    assert len(list_template_ids(workspace)) == 30


def test_install_all_preflights_conflicts_before_any_new_install(tmp_path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    entry = get_starter_template("discussion_map")
    created = provenance(_actor(), clock=_clock, source_kind="imported")
    definition, version = entry.build_template_records(
        created_provenance=created,
        status="active",
    )
    collision_bytes = b"collision\n"
    collision = replace(
        version,
        rendering_specification_reference="collision-layout",
        rendering_specification_sha256=hashlib.sha256(
            collision_bytes
        ).hexdigest(),
    )
    create_template_library(
        workspace,
        definition=definition,
        initial_version=collision,
        rendering_specification=collision_bytes,
    )

    with pytest.raises(ConcordWorkflowConflictError, match="discussion_map"):
        prepare_starter_template_install_all(
            PrepareStarterTemplateInstallAllRequest(actor=_actor()),
            workspace_root=workspace,
            clock=_clock,
        )
    assert list_template_ids(workspace) == (entry.template_id,)
