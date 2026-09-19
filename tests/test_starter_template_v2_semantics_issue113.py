from __future__ import annotations

from datetime import datetime, timezone

import pytest

from concord.models import (
    ActorReference,
    Provenance,
    TemplateSubjectResolutionExpectation,
)
from concord.starter_templates.catalog import (
    get_starter_template,
    list_starter_templates,
)
from concord.starter_templates.catalog_lineage import (
    RELATIONSHIP_AWARE_STARTER_KEYS,
    build_starter_template_lineage,
    current_packaged_template_version_id,
    relationship_v2_asset_name,
)
from concord.template_storage import (
    create_template_library,
    load_current_template,
    load_template_rendering_specification,
)
from concord.workflows.models import WorkflowActor
from concord.workflows.starter_template import (
    STARTER_INSTALLATION_ALREADY_INSTALLED,
    STARTER_INSTALLATION_UPGRADE_AVAILABLE,
    PrepareStarterTemplateInstallRequest,
    commit_starter_template_install,
    get_starter_template_status,
    prepare_starter_template_install,
)


def _provenance() -> Provenance:
    return Provenance(
        actor=ActorReference(
            actor_kind="authorized_adult",
            actor_id="teacher-1",
            owning_system="concord",
        ),
        timestamp="2026-09-19T13:00:00-04:00",
        source_kind="imported",
        application_version="0.3.0",
        note="Synthetic issue #113 starter-v2 semantics.",
    )


def _actor() -> WorkflowActor:
    return WorkflowActor(actor_id="teacher-1", display_label="Teacher")


def _clock() -> datetime:
    return datetime(2026, 9, 19, 17, 0, tzinfo=timezone.utc)


def _lineage(starter_key: str):
    entry = get_starter_template(starter_key)
    return build_starter_template_lineage(
        entry,
        created_provenance=_provenance(),
    )


def test_exactly_five_starters_have_relationship_aware_v2_lineages() -> None:
    assert RELATIONSHIP_AWARE_STARTER_KEYS == (
        "fishbowl_observer",
        "talk_moves_observer",
        "peer_review_writing",
        "peer_review_presentation",
        "peer_design_code_review",
    )
    affected = set(RELATIONSHIP_AWARE_STARTER_KEYS)

    for entry in list_starter_templates():
        lineage = build_starter_template_lineage(
            entry,
            created_provenance=_provenance(),
        )
        expected_count = 2 if entry.starter_key in affected else 1
        assert len(lineage.versions) == expected_count
        if expected_count == 1:
            assert current_packaged_template_version_id(entry) == (
                entry.template_version_id
            )
            assert relationship_v2_asset_name(entry) is None
        else:
            assert current_packaged_template_version_id(entry) == (
                f"{entry.template_id}-v2"
            )
            assert relationship_v2_asset_name(entry) is not None


@pytest.mark.parametrize(
    ("starter_key", "authorship_mode", "multiple_authors"),
    (
        ("fishbowl_observer", "observer", False),
        ("talk_moves_observer", "observer", False),
        ("peer_review_writing", "individual_author", True),
        ("peer_review_presentation", "individual_author", True),
        ("peer_design_code_review", "individual_author", False),
    ),
)
def test_v2_authorship_semantics(
    starter_key: str,
    authorship_mode: str,
    multiple_authors: bool,
) -> None:
    lineage = _lineage(starter_key)
    v1 = lineage.versions[0].version
    v2 = lineage.versions[1].version

    assert v2.template_version_id == f"{lineage.template_id}-v2"
    assert v2.version_label == "Starter v2"
    assert v2.revision_sequence == 2
    assert v2.supersedes_template_version_id == v1.template_version_id
    assert v2.status == "active"
    assert v2.default_authorship_expectation is not None
    assert (
        v2.default_authorship_expectation.authorship_mode
        == authorship_mode
    )
    assert (
        v2.default_authorship_expectation.multiple_allowed
        is multiple_authors
    )


@pytest.mark.parametrize(
    ("starter_key", "subject_kinds", "resolution_mode", "subject_role"),
    (
        (
            "fishbowl_observer",
            ("concord_session",),
            "session",
            "session_context",
        ),
        (
            "talk_moves_observer",
            ("concord_session",),
            "session",
            "session_context",
        ),
        (
            "peer_review_writing",
            ("core_student",),
            "explicit",
            "reviewed_subject",
        ),
        (
            "peer_review_presentation",
            ("concord_group", "core_student"),
            "explicit",
            "reviewed_subject",
        ),
        (
            "peer_design_code_review",
            ("concord_group", "core_student"),
            "explicit",
            "reviewed_subject",
        ),
    ),
)
def test_v2_subject_resolution_semantics(
    starter_key: str,
    subject_kinds: tuple[str, ...],
    resolution_mode: str,
    subject_role: str,
) -> None:
    expectation = _lineage(
        starter_key
    ).versions[1].version.default_subject_expectation
    assert isinstance(expectation, TemplateSubjectResolutionExpectation)
    assert expectation.subject_kinds == subject_kinds
    assert expectation.resolution_mode == resolution_mode
    assert expectation.subject_role == subject_role
    assert expectation.required is True
    assert expectation.multiple_allowed is False

    if resolution_mode == "explicit":
        assert expectation.allow_target_subject_match is False
    else:
        assert expectation.allow_target_subject_match is True


def test_existing_v1_identity_semantics_and_rendering_are_unchanged() -> None:
    for starter_key in RELATIONSHIP_AWARE_STARTER_KEYS:
        entry = get_starter_template(starter_key)
        lineage = _lineage(starter_key)
        definition, expected_v1 = entry.build_template_records(
            created_provenance=_provenance(),
            status="active",
        )

        assert lineage.definition == definition
        assert lineage.versions[0].version == expected_v1
        assert (
            lineage.versions[0].rendering_specification
            == entry.rendering_specification_bytes()
        )


def test_v2_rendering_uses_separate_canonical_package_assets() -> None:
    for starter_key in RELATIONSHIP_AWARE_STARTER_KEYS:
        entry = get_starter_template(starter_key)
        asset_name = relationship_v2_asset_name(entry)
        assert asset_name is not None
        assert asset_name != entry.asset_name
        assert asset_name.endswith("_v2.json")

        lineage = _lineage(starter_key)
        v1 = lineage.versions[0]
        v2 = lineage.versions[1]
        assert (
            v2.version.rendering_specification_reference
            == f"{entry.template_id}-layout-v2"
        )
        assert v2.version.rendering_specification_reference != (
            v1.version.rendering_specification_reference
        )
        # Slice 5 intentionally keeps the printable layout unchanged while
        # freezing the corrected relationship semantics in a new Version.
        assert v2.rendering_specification == v1.rendering_specification


def test_socratic_seminar_remains_exact_v1_only() -> None:
    entry = get_starter_template("socratic_seminar")
    lineage = _lineage("socratic_seminar")
    assert len(lineage.versions) == 1
    assert lineage.current_version.version.template_version_id == (
        entry.template_version_id
    )


def test_fresh_affected_install_establishes_v1_then_active_v2(tmp_path) -> None:
    workspace = tmp_path / "workspace"
    request = PrepareStarterTemplateInstallRequest(
        starter_key="peer_review_writing",
        actor=_actor(),
    )

    prepared = prepare_starter_template_install(
        request,
        workspace_root=workspace,
        clock=_clock,
    )
    assert prepared.lineage is not None
    assert len(prepared.lineage.versions) == 2
    result = commit_starter_template_install(
        prepared,
        workspace_root=workspace,
    )

    assert result.outcome == "installed"
    assert result.template_version_id == "starter-peer-review-writing-v2"
    loaded = load_current_template(
        workspace,
        "starter-peer-review-writing",
    )
    assert tuple(version.status for version in loaded.versions) == (
        "superseded",
        "active",
    )
    assert loaded.current_template_version_id == (
        "starter-peer-review-writing-v2"
    )

    entry = get_starter_template("peer_review_writing")
    assert load_template_rendering_specification(
        workspace,
        entry.template_id,
        entry.template_version_id,
    ) == entry.rendering_specification_bytes()


def test_exact_v1_workspace_reports_upgrade_then_activates_v2(tmp_path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    entry = get_starter_template("fishbowl_observer")
    definition, v1 = entry.build_template_records(
        created_provenance=_provenance(),
        status="active",
    )
    create_template_library(
        workspace,
        definition=definition,
        initial_version=v1,
        rendering_specification=entry.rendering_specification_bytes(),
    )

    status = get_starter_template_status(
        entry.starter_key,
        workspace_root=workspace,
    )
    assert status.installation_state == STARTER_INSTALLATION_UPGRADE_AVAILABLE
    assert status.template_version_id == "starter-fishbowl-observer-v2"

    result = commit_starter_template_install(
        prepare_starter_template_install(
            PrepareStarterTemplateInstallRequest(
                starter_key=entry.starter_key,
                actor=_actor(),
            ),
            workspace_root=workspace,
            clock=_clock,
        ),
        workspace_root=workspace,
    )
    assert result.outcome == "upgraded"
    assert result.template_version_id == "starter-fishbowl-observer-v2"

    replay = get_starter_template_status(
        entry.starter_key,
        workspace_root=workspace,
    )
    assert (
        replay.installation_state
        == STARTER_INSTALLATION_ALREADY_INSTALLED
    )
