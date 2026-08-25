from __future__ import annotations

import json
from pathlib import Path

import pytest
from pds_core.routing_models import ModuleRecordRef

from concord.cli_app.main import EXIT_CONFLICT, EXIT_OK, main
from concord.models import PacketAudienceIntent, PacketComponent
from concord.packet_serialization import dataclass_to_dict
from concord.packet_storage import load_current_packet


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


def _authoring_bytes(
    *,
    include_definition: bool,
    version_label: str,
    record_id: str,
) -> bytes:
    return (
        json.dumps(
            {
                "schema_version": "concord_packet_authoring_v1",
                "definition": (
                    {
                        "name": "CLI Packet",
                        "purpose": "Exercise reusable Packet CLI workflows.",
                        "description": "Synthetic issue #60 CLI fixture.",
                    }
                    if include_definition
                    else None
                ),
                "version": {
                    "version_label": version_label,
                    "components": [dataclass_to_dict(_component(record_id))],
                    "rendering_rules": {
                        "preserve_component_order": True,
                        "start_each_component_on_new_page": False,
                        "copy_collation": "component_major",
                        "target_order": "stable_identity",
                    },
                },
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _actor() -> tuple[str, ...]:
    return ("--actor-id", "teacher-1")


def _expected(revision: int) -> tuple[str, ...]:
    return ("--expected-snapshot", str(revision))


def test_packet_list_is_read_only_for_absent_workspace(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "absent"
    assert main(
        (
            "packet",
            "list",
            "--workspace-root",
            str(root),
        )
    ) == EXIT_OK
    assert "No reusable Concord Packets" in capsys.readouterr().out
    assert not root.exists()


def test_packet_cli_full_management_sequence(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "workspace"
    create_authoring = tmp_path / "create.json"
    create_authoring.write_bytes(
        _authoring_bytes(
            include_definition=True,
            version_label="v1",
            record_id="submission-1",
        )
    )

    assert main(
        (
            "packet",
            "create",
            "--workspace-root",
            str(root),
            *_actor(),
            "--packet-definition-id",
            "packet-cli",
            "--packet-version-id",
            "packet-cli-v1",
            "--authoring-file",
            str(create_authoring),
            "--activate",
        )
    ) == EXIT_OK
    output = capsys.readouterr().out
    assert "Packet: packet-cli" in output
    assert "Snapshot: 1" in output
    assert "Current Version: packet-cli-v1" in output

    assert main(
        (
            "packet",
            "list",
            "--workspace-root",
            str(root),
        )
    ) == EXIT_OK
    assert "packet-cli: CLI Packet" in capsys.readouterr().out

    assert main(
        (
            "packet",
            "show",
            "--workspace-root",
            str(root),
            "--packet-definition-id",
            "packet-cli",
        )
    ) == EXIT_OK
    output = capsys.readouterr().out
    assert "Purpose: Exercise reusable Packet CLI workflows." in output
    assert "Versions: 1" in output
    assert "Head Components: 1" in output

    revise_authoring = tmp_path / "revise.json"
    revise_authoring.write_bytes(
        _authoring_bytes(
            include_definition=False,
            version_label="v2",
            record_id="submission-2",
        )
    )
    assert main(
        (
            "packet",
            "revise",
            "--workspace-root",
            str(root),
            *_actor(),
            *_expected(1),
            "--packet-definition-id",
            "packet-cli",
            "--packet-version-id",
            "packet-cli-v2",
            "--authoring-file",
            str(revise_authoring),
        )
    ) == EXIT_OK
    output = capsys.readouterr().out
    assert "Snapshot: 2" in output
    assert "Current Version: packet-cli-v1" in output
    assert "Head Version: packet-cli-v2" in output

    assert main(
        (
            "packet",
            "version-list",
            "--workspace-root",
            str(root),
            "--packet-definition-id",
            "packet-cli",
        )
    ) == EXIT_OK
    output = capsys.readouterr().out
    assert "packet-cli-v1 [active]" in output
    assert "packet-cli-v2 [draft]" in output

    assert main(
        (
            "packet",
            "version-show",
            "--workspace-root",
            str(root),
            "--packet-definition-id",
            "packet-cli",
            "--packet-version-id",
            "packet-cli-v2",
        )
    ) == EXIT_OK
    output = capsys.readouterr().out
    assert "Revision Sequence: 2" in output
    assert "external=quillan:submission:submission-2@1" in output

    assert main(
        (
            "packet",
            "activate",
            "--workspace-root",
            str(root),
            *_actor(),
            *_expected(2),
            "--packet-definition-id",
            "packet-cli",
            "--packet-version-id",
            "packet-cli-v2",
        )
    ) == EXIT_OK
    assert "Snapshot: 3" in capsys.readouterr().out

    v3_authoring = tmp_path / "v3.json"
    v3_authoring.write_bytes(
        _authoring_bytes(
            include_definition=False,
            version_label="v3",
            record_id="submission-3",
        )
    )
    assert main(
        (
            "packet",
            "revise",
            "--workspace-root",
            str(root),
            *_actor(),
            *_expected(3),
            "--packet-definition-id",
            "packet-cli",
            "--packet-version-id",
            "packet-cli-v3",
            "--authoring-file",
            str(v3_authoring),
        )
    ) == EXIT_OK
    assert "Snapshot: 4" in capsys.readouterr().out

    assert main(
        (
            "packet",
            "retire-version",
            "--workspace-root",
            str(root),
            *_actor(),
            *_expected(4),
            "--packet-definition-id",
            "packet-cli",
            "--packet-version-id",
            "packet-cli-v3",
        )
    ) == EXIT_OK
    assert "Snapshot: 5" in capsys.readouterr().out

    assert main(
        (
            "packet",
            "update",
            "--workspace-root",
            str(root),
            *_actor(),
            *_expected(5),
            "--packet-definition-id",
            "packet-cli",
            "--name",
            "Renamed CLI Packet",
            "--clear-description",
        )
    ) == EXIT_OK
    assert "Snapshot: 6" in capsys.readouterr().out

    assert main(
        (
            "packet",
            "retire",
            "--workspace-root",
            str(root),
            *_actor(),
            *_expected(6),
            "--packet-definition-id",
            "packet-cli",
        )
    ) == EXIT_OK
    assert "Snapshot: 7" in capsys.readouterr().out

    loaded = load_current_packet(root, "packet-cli")
    assert loaded.definition.status == "retired"
    assert loaded.definition.name == "Renamed CLI Packet"
    assert loaded.definition.description is None
    assert loaded.current_packet_version_id is None
    assert loaded.head_packet_version_id == "packet-cli-v3"
    assert tuple(item.status for item in loaded.versions) == (
        "superseded",
        "retired",
        "retired",
    )


def test_packet_cli_stale_expected_snapshot_is_conflict(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "workspace"
    authoring = tmp_path / "create.json"
    authoring.write_bytes(
        _authoring_bytes(
            include_definition=True,
            version_label="v1",
            record_id="submission-1",
        )
    )
    assert main(
        (
            "packet",
            "create",
            "--workspace-root",
            str(root),
            *_actor(),
            "--packet-definition-id",
            "packet-cli",
            "--packet-version-id",
            "packet-cli-v1",
            "--authoring-file",
            str(authoring),
        )
    ) == EXIT_OK
    capsys.readouterr()

    assert main(
        (
            "packet",
            "update",
            "--workspace-root",
            str(root),
            *_actor(),
            *_expected(99),
            "--packet-definition-id",
            "packet-cli",
            "--name",
            "Stale update",
        )
    ) == EXIT_CONFLICT
    assert "Conflict:" in capsys.readouterr().err
