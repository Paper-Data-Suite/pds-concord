from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from concord.cli_app.main import EXIT_CONFLICT, EXIT_OK, main
from concord.models import (
    ActorReference,
    PrivacyPolicy,
    Provenance,
    TemplateCompatibility,
    TemplatePageDefinition,
    TemplateVersion,
)
from concord.template_serialization import (
    canonical_json_bytes,
    dataclass_to_dict,
)
from concord.template_storage import load_current_template


def _provenance() -> Provenance:
    return Provenance(
        actor=ActorReference(
            actor_kind="authorized_adult",
            actor_id="teacher-1",
            owning_system="concord",
        ),
        timestamp="2026-08-24T23:15:00+00:00",
        source_kind="manual",
        application_version="0.3.0.dev0",
    )


def _rendering(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _source_version(
    *,
    reference: str,
    rendering: bytes,
) -> TemplateVersion:
    return TemplateVersion(
        template_version_id="transport-only",
        template_id="transport-template",
        version_label="transport",
        revision_sequence=1,
        rendering_contract_version="concord-template-rendering-v1",
        rendering_specification_reference=reference,
        rendering_specification_sha256=_rendering(rendering),
        artifact_category="discussion_record",
        page_manifest=(
            TemplatePageDefinition(
                page_key="page-1",
                sequence=1,
                page_kind="primary",
                return_expected=False,
                route_required=False,
            ),
        ),
        rendering_inputs=(),
        default_expected_return_status="return_not_expected",
        default_privacy_policy=PrivacyPolicy(
            classification="teacher_restricted"
        ),
        compatibility=TemplateCompatibility(
            audience_kinds=("teacher",),
        ),
        created_provenance=_provenance(),
        status="draft",
    )


def _authoring_bytes(
    *,
    include_definition: bool,
    version_label: str,
    reference: str,
    rendering: bytes,
) -> bytes:
    source = _source_version(
        reference=reference,
        rendering=rendering,
    )
    return canonical_json_bytes(
        {
            "schema_version": "concord_template_authoring_v1",
            "artifact_category": "discussion_record",
            "definition": (
                {
                    "name": "CLI Template",
                    "purpose": "Exercise reusable Template CLI workflows.",
                    "description": "Synthetic issue #58 CLI fixture.",
                }
                if include_definition
                else None
            ),
            "version": {
                "version_label": version_label,
                "rendering_contract_version": (
                    source.rendering_contract_version
                ),
                "rendering_specification_reference": reference,
                "page_manifest": [
                    dataclass_to_dict(item)
                    for item in source.page_manifest
                ],
                "rendering_inputs": [],
                "default_expected_return_status": (
                    source.default_expected_return_status
                ),
                "default_privacy_policy": dataclass_to_dict(
                    source.default_privacy_policy
                ),
                "compatibility": dataclass_to_dict(
                    source.compatibility
                ),
                "default_authorship_expectation": None,
                "default_subject_expectation": None,
            },
        }
    )


def _actor() -> tuple[str, ...]:
    return ("--actor-id", "teacher-1")


def _expected(revision: int) -> tuple[str, ...]:
    return ("--expected-snapshot", str(revision))


def test_template_list_is_read_only_for_absent_workspace(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "absent"
    assert main(
        (
            "template",
            "list",
            "--workspace-root",
            str(root),
        )
    ) == EXIT_OK
    assert "No reusable Concord Templates" in capsys.readouterr().out
    assert not root.exists()


def test_template_cli_full_management_sequence(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "workspace"
    create_authoring = tmp_path / "create.json"
    create_rendering = tmp_path / "create.bin"
    create_rendering.write_bytes(b"rendering-v1")
    create_authoring.write_bytes(
        _authoring_bytes(
            include_definition=True,
            version_label="v1",
            reference="rendering-v1",
            rendering=create_rendering.read_bytes(),
        )
    )

    assert main(
        (
            "template",
            "create",
            "--workspace-root",
            str(root),
            *_actor(),
            "--template-id",
            "template-cli",
            "--template-version-id",
            "template-cli-v1",
            "--authoring-file",
            str(create_authoring),
            "--rendering-spec",
            str(create_rendering),
            "--activate",
        )
    ) == EXIT_OK
    output = capsys.readouterr().out
    assert "Template: template-cli" in output
    assert "Snapshot: 1" in output
    assert "Current Version: template-cli-v1" in output

    assert main(
        (
            "template",
            "list",
            "--workspace-root",
            str(root),
        )
    ) == EXIT_OK
    assert "template-cli: CLI Template" in capsys.readouterr().out

    assert main(
        (
            "template",
            "show",
            "--workspace-root",
            str(root),
            "--template-id",
            "template-cli",
        )
    ) == EXIT_OK
    output = capsys.readouterr().out
    assert "Purpose: Exercise reusable Template CLI workflows." in output
    assert "Versions: 1" in output

    revise_authoring = tmp_path / "revise.json"
    revise_rendering = tmp_path / "revise.bin"
    revise_rendering.write_bytes(b"rendering-v2")
    revise_authoring.write_bytes(
        _authoring_bytes(
            include_definition=False,
            version_label="v2",
            reference="rendering-v2",
            rendering=revise_rendering.read_bytes(),
        )
    )
    assert main(
        (
            "template",
            "revise",
            "--workspace-root",
            str(root),
            *_actor(),
            *_expected(1),
            "--template-id",
            "template-cli",
            "--template-version-id",
            "template-cli-v2",
            "--authoring-file",
            str(revise_authoring),
            "--rendering-spec",
            str(revise_rendering),
        )
    ) == EXIT_OK
    output = capsys.readouterr().out
    assert "Snapshot: 2" in output
    assert "Current Version: template-cli-v1" in output
    assert "Head Version: template-cli-v2" in output

    assert main(
        (
            "template",
            "version-list",
            "--workspace-root",
            str(root),
            "--template-id",
            "template-cli",
        )
    ) == EXIT_OK
    output = capsys.readouterr().out
    assert "template-cli-v1 [active]" in output
    assert "template-cli-v2 [draft]" in output

    assert main(
        (
            "template",
            "version-show",
            "--workspace-root",
            str(root),
            "--template-id",
            "template-cli",
            "--template-version-id",
            "template-cli-v2",
        )
    ) == EXIT_OK
    output = capsys.readouterr().out
    assert "Revision Sequence: 2" in output
    assert "Rendering Reference: rendering-v2" in output

    assert main(
        (
            "template",
            "activate",
            "--workspace-root",
            str(root),
            *_actor(),
            *_expected(2),
            "--template-id",
            "template-cli",
            "--template-version-id",
            "template-cli-v2",
        )
    ) == EXIT_OK
    assert "Snapshot: 3" in capsys.readouterr().out

    v3_authoring = tmp_path / "v3.json"
    v3_rendering = tmp_path / "v3.bin"
    v3_rendering.write_bytes(b"rendering-v3")
    v3_authoring.write_bytes(
        _authoring_bytes(
            include_definition=False,
            version_label="v3",
            reference="rendering-v3",
            rendering=v3_rendering.read_bytes(),
        )
    )
    assert main(
        (
            "template",
            "revise",
            "--workspace-root",
            str(root),
            *_actor(),
            *_expected(3),
            "--template-id",
            "template-cli",
            "--template-version-id",
            "template-cli-v3",
            "--authoring-file",
            str(v3_authoring),
            "--rendering-spec",
            str(v3_rendering),
        )
    ) == EXIT_OK
    assert "Snapshot: 4" in capsys.readouterr().out

    assert main(
        (
            "template",
            "retire-version",
            "--workspace-root",
            str(root),
            *_actor(),
            *_expected(4),
            "--template-id",
            "template-cli",
            "--template-version-id",
            "template-cli-v3",
        )
    ) == EXIT_OK
    assert "Snapshot: 5" in capsys.readouterr().out

    assert main(
        (
            "template",
            "update",
            "--workspace-root",
            str(root),
            *_actor(),
            *_expected(5),
            "--template-id",
            "template-cli",
            "--name",
            "Renamed CLI Template",
            "--clear-description",
        )
    ) == EXIT_OK
    assert "Snapshot: 6" in capsys.readouterr().out

    assert main(
        (
            "template",
            "retire",
            "--workspace-root",
            str(root),
            *_actor(),
            *_expected(6),
            "--template-id",
            "template-cli",
        )
    ) == EXIT_OK
    assert "Snapshot: 7" in capsys.readouterr().out

    loaded = load_current_template(root, "template-cli")
    assert loaded.definition.status == "retired"
    assert loaded.definition.name == "Renamed CLI Template"
    assert loaded.definition.description is None
    assert loaded.current_template_version_id is None
    assert loaded.head_template_version_id == "template-cli-v3"
    assert tuple(item.status for item in loaded.versions) == (
        "superseded",
        "retired",
        "retired",
    )


def test_template_cli_stale_expected_snapshot_is_conflict(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "workspace"
    authoring = tmp_path / "create.json"
    rendering = tmp_path / "create.bin"
    rendering.write_bytes(b"rendering")
    authoring.write_bytes(
        _authoring_bytes(
            include_definition=True,
            version_label="v1",
            reference="rendering-v1",
            rendering=rendering.read_bytes(),
        )
    )
    assert main(
        (
            "template",
            "create",
            "--workspace-root",
            str(root),
            *_actor(),
            "--template-id",
            "template-cli",
            "--template-version-id",
            "template-cli-v1",
            "--authoring-file",
            str(authoring),
            "--rendering-spec",
            str(rendering),
        )
    ) == EXIT_OK
    capsys.readouterr()

    assert main(
        (
            "template",
            "update",
            "--workspace-root",
            str(root),
            *_actor(),
            *_expected(99),
            "--template-id",
            "template-cli",
            "--name",
            "Stale update",
        )
    ) == EXIT_CONFLICT
    assert "Conflict:" in capsys.readouterr().err
