"""Installed-wheel qualification for Concord Issue #110 Packet generation rendering."""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import tempfile
import textwrap
import venv
from pathlib import Path

EXPECTED_CORE_SHA256 = (
    "48cea9317f2967bdc0f2d4c14349a56677c7c3f8211f0f33978ccb1a1c75859b"
)


def _python(venv_root: Path) -> Path:
    return (
        venv_root / "Scripts" / "python.exe"
        if os.name == "nt"
        else venv_root / "bin" / "python"
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run(command: list[str], cwd: Path) -> None:
    subprocess.run(
        command,
        cwd=cwd,
        check=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )


def _smoke_code() -> str:
    return textwrap.dedent(
        r"""
        from __future__ import annotations

        import contextlib
        import hashlib
        import io
        import tempfile
        from argparse import Namespace
        from datetime import datetime, timezone
        from importlib import metadata
        from pathlib import Path
        from unittest.mock import patch

        import concord
        import concord.menu_packet_generation as menu_packet_generation
        import concord.workflows.rendered_output as rendered_output_module
        import pds_core
        from pds_core.class_metadata import (
            create_class_metadata,
            write_class_metadata_for_class,
        )
        from pds_core.classes import write_class_roster
        from pds_core.pds2 import parse_pds2_payload
        from pds_core.rosters import create_roster
        from pds_core.route_registrations import load_route_registration
        from pds_core.routing_models import ModuleWorkRef
        from pds_core.workspace import ensure_workspace_root

        from concord.cli_app.handlers import packet_runtime
        from concord.menu_context import MenuSessionContext
        from concord.storage import load_current_record_graph
        from concord.workflows import (
            CreateActivityContextRequest,
            PreparePacketInstantiationRequest,
            PrepareStarterTemplateInstallRequest,
            RenderPacketGenerationRequest,
            WorkflowActor,
            commit_packet_instantiation,
            commit_starter_template_install,
            create_activity_context,
            list_packet_generations,
            open_rendered_packet_output,
            open_rendered_packet_output_directory,
            prepare_packet_instantiation,
            prepare_starter_template_install,
            render_packet_generation,
            show_activity,
        )
        from concord.workflows.packet import (
            PreparePacketFromTemplateRequest,
            commit_packet_from_template,
            prepare_packet_from_template,
        )

        CLASS_ID = "class-issue110-installed"
        ACTIVITY_ID = "activity-issue110-installed"
        SESSION_ID = "session-issue110-installed"
        GENERATION_ID = "generation-issue110-installed"


        def stage(name: str) -> None:
            print(f"issue110 installed wheel: {name}: PASS", flush=True)


        def require_installed(module: object, distribution: str) -> None:
            origin = Path(getattr(module, "__file__")).resolve()
            if "site-packages" not in str(origin).casefold():
                raise AssertionError(
                    f"{distribution} did not import from isolated "
                    f"site-packages: {origin}"
                )


        def clock() -> datetime:
            return datetime(2026, 10, 6, 22, 0, tzinfo=timezone.utc)


        def actor() -> WorkflowActor:
            return WorkflowActor(
                actor_id="teacher-issue110-installed",
                display_label="Synthetic Installed-Wheel Teacher",
                role_label="teacher",
            )


        def output_state(result):
            return {
                packet.packet_instance_id: (
                    packet.output_path,
                    packet.output_sha256,
                    packet.output_path.read_bytes(),
                    packet.payloads,
                )
                for packet in result.packets
            }


        def route_state(root: Path, result):
            return {
                packet.packet_instance_id: tuple(
                    load_route_registration(
                        root,
                        parse_pds2_payload(payload),
                    )
                    for payload in packet.payloads
                )
                for packet in result.packets
            }


        require_installed(pds_core, "pds-core")
        require_installed(concord, "pds-concord")
        assert metadata.version("pds-core") == "0.6.4"
        assert metadata.version("pds-concord") == "0.3.0"
        stage("isolated installed provenance")

        with tempfile.TemporaryDirectory(
            prefix="concord-issue110-installed-"
        ) as raw:
            root = ensure_workspace_root(Path(raw) / "workspace")
            write_class_metadata_for_class(
                root,
                create_class_metadata(
                    CLASS_ID,
                    "2026-2027",
                    created_at=clock(),
                ),
            )
            write_class_roster(
                root,
                create_roster(
                    CLASS_ID,
                    (
                        {
                            "student_id": "student-1",
                            "last_name": "One",
                            "first_name": "Alex",
                            "period": "1",
                        },
                        {
                            "student_id": "student-2",
                            "last_name": "Two",
                            "first_name": "Bailey",
                            "period": "1",
                        },
                        {
                            "student_id": "student-3",
                            "last_name": "Three",
                            "first_name": "Casey",
                            "period": "1",
                        },
                    ),
                ),
            )
            create_activity_context(
                CreateActivityContextRequest(
                    class_id=CLASS_ID,
                    activity_id=ACTIVITY_ID,
                    title="Issue 110 Installed Generation Rendering",
                    activity_type="project",
                    scoring_orientation="evidence_only",
                    session_id=SESSION_ID,
                    actor=actor(),
                    activity_status="active",
                    session_status="active",
                    session_label="Installed Session",
                ),
                workspace_root=root,
                clock=clock,
            )
            installed = commit_starter_template_install(
                prepare_starter_template_install(
                    PrepareStarterTemplateInstallRequest(
                        starter_key="think_pair_share",
                        actor=actor(),
                    ),
                    workspace_root=root,
                    clock=clock,
                ),
                workspace_root=root,
            )
            packet = prepare_packet_from_template(
                PreparePacketFromTemplateRequest(
                    packet_definition_id="packet-issue110-installed",
                    packet_version_id="packet-issue110-installed-v1",
                    packet_component_id="component-issue110-installed",
                    name="Issue 110 Installed Packet",
                    purpose="Exercise complete-generation rendering and reprint.",
                    template_id=installed.template_id,
                    template_version_id=installed.template_version_id,
                    audience_kind="participant",
                    actor=actor(),
                ),
                workspace_root=root,
                clock=clock,
            )
            commit_packet_from_template(
                packet,
                workspace_root=root,
            )
            prepared = prepare_packet_instantiation(
                PreparePacketInstantiationRequest(
                    class_id=CLASS_ID,
                    activity_id=ACTIVITY_ID,
                    session_id=SESSION_ID,
                    packet_definition_id="packet-issue110-installed",
                    packet_version_id="packet-issue110-installed-v1",
                    actor=actor(),
                ),
                workspace_root=root,
                clock=clock,
            )
            assert prepared.ready_for_commit
            assert prepared.packet_instance_count == 3
            committed = commit_packet_instantiation(
                prepared,
                workspace_root=root,
                generation_id=GENERATION_ID,
                clock=clock,
            )
            assert len(committed.packet_instance_ids) == 3
            stage("three-target generation preparation")

            before = list_packet_generations(
                CLASS_ID,
                ACTIVITY_ID,
                workspace_root=root,
            )
            assert len(before) == 1
            reviewed = before[0]
            assert reviewed.generation_id == GENERATION_ID
            assert reviewed.instance_count == 3
            assert reviewed.rendering_count == 3
            assert reviewed.generated_count == 0
            assert reviewed.routes_pending_count == 0

            work = ModuleWorkRef("concord", CLASS_ID, ACTIVITY_ID)
            source = load_current_record_graph(root, work)
            first = render_packet_generation(
                RenderPacketGenerationRequest(
                    class_id=CLASS_ID,
                    activity_id=ACTIVITY_ID,
                    generation_id=GENERATION_ID,
                    actor=actor(),
                    expected_snapshot_revision=reviewed.snapshot_revision,
                ),
                workspace_root=root,
            )
            assert len(first.packets) == 3
            assert all(packet.output_path.is_file() for packet in first.packets)
            assert all(
                packet.output_path.read_bytes().startswith(b"%PDF")
                for packet in first.packets
            )
            assert all(not packet.replayed for packet in first.packets)
            commit_revisions = {
                packet.commit.snapshot_revision
                for packet in first.packets
            }
            assert len(commit_revisions) == 1
            first_revision = next(iter(commit_revisions))
            assert first_revision == source.snapshot_revision + 1
            first_outputs = output_state(first)
            first_routes = route_state(root, first)
            stage("multi-target generation first render")

            after_first = list_packet_generations(
                CLASS_ID,
                ACTIVITY_ID,
                workspace_root=root,
            )
            assert len(after_first) == 1
            reviewed_reprint = after_first[0]
            assert reviewed_reprint.generated_count == 3
            assert reviewed_reprint.rendering_count == 0
            assert reviewed_reprint.instance_count == 3

            replay = render_packet_generation(
                RenderPacketGenerationRequest(
                    class_id=CLASS_ID,
                    activity_id=ACTIVITY_ID,
                    generation_id=GENERATION_ID,
                    actor=actor(),
                    expected_snapshot_revision=reviewed_reprint.snapshot_revision,
                ),
                workspace_root=root,
            )
            assert len(replay.packets) == 3
            assert all(packet.replayed for packet in replay.packets)
            assert all(not packet.output_installed for packet in replay.packets)
            assert all(packet.commit.no_op for packet in replay.packets)
            assert output_state(replay) == first_outputs
            assert route_state(root, replay) == first_routes
            after_reprint = load_current_record_graph(root, work)
            assert (
                after_reprint.snapshot_revision
                == reviewed_reprint.snapshot_revision
            )
            assert (
                after_reprint.snapshot_sha256
                == reviewed_reprint.snapshot_sha256
            )
            stage("complete-generation deterministic reprint")

            cli_output = io.StringIO()
            with contextlib.redirect_stdout(cli_output):
                rc = packet_runtime.handle_generation_render(
                    Namespace(
                        class_id=CLASS_ID,
                        activity_id=ACTIVITY_ID,
                        generation_id=GENERATION_ID,
                        actor_id=actor().actor_id,
                        actor_label=actor().display_label,
                        actor_role=actor().role_label,
                        workspace_root=str(root),
                    )
                )
            assert rc == 0
            rendered_cli = cli_output.getvalue()
            assert f"Generation: {GENERATION_ID}" in rendered_cli
            assert "Packet Instances: 3" in rendered_cli
            after_cli_outputs = {
                item.packet_instance_id: (
                    item.output_path,
                    item.output_sha256,
                    item.output_path.read_bytes(),
                    item.payloads,
                )
                for item in replay.packets
            }
            assert after_cli_outputs == first_outputs
            assert route_state(root, replay) == first_routes
            after_cli = load_current_record_graph(root, work)
            assert after_cli.snapshot_revision == after_reprint.snapshot_revision
            assert after_cli.snapshot_sha256 == after_reprint.snapshot_sha256
            stage("installed direct generation-render authority")

            activity = show_activity(
                CLASS_ID,
                ACTIVITY_ID,
                workspace_root=root,
            ).summary
            menu_output = io.StringIO()
            with (
                patch("builtins.input", return_value="B"),
                patch.object(
                    menu_packet_generation,
                    "clear_screen",
                    lambda: None,
                ),
                contextlib.redirect_stdout(menu_output),
            ):
                menu_packet_generation.launch_packet_generation_menu(
                    activity,
                    MenuSessionContext(actor=actor()),
                )
            rendered_menu = menu_output.getvalue()
            assert "4. Render / reprint a complete generation" in rendered_menu
            assert "5. Render / reprint one Packet Instance" in rendered_menu
            stage("installed teacher generation menu reachability")

            first_packet = replay.packets[0]
            opened: list[Path] = []

            def fake_open(path: str | Path) -> Path:
                exact = Path(path)
                opened.append(exact)
                return exact

            rendered_output_module.open_local_path = fake_open
            canonical_before_open = load_current_record_graph(root, work)
            opened_pdf = open_rendered_packet_output(
                CLASS_ID,
                ACTIVITY_ID,
                first_packet.packet_instance_id,
                workspace_root=root,
            )
            opened_folder = open_rendered_packet_output_directory(
                CLASS_ID,
                ACTIVITY_ID,
                first_packet.packet_instance_id,
                workspace_root=root,
            )
            assert opened_pdf.output_path == first_packet.output_path
            assert opened_folder.output_directory == first_packet.output_path.parent
            assert opened == [
                first_packet.output_path,
                first_packet.output_path.parent,
            ]
            canonical_after_open = load_current_record_graph(root, work)
            assert canonical_after_open.snapshot_revision == (
                canonical_before_open.snapshot_revision
            )
            assert canonical_after_open.snapshot_sha256 == (
                canonical_before_open.snapshot_sha256
            )
            assert route_state(root, replay) == first_routes
            stage("verified rendered-output opening reachability")

            for packet_id, (_, digest, data, payloads) in first_outputs.items():
                assert hashlib.sha256(data).hexdigest() == digest
                assert payloads
                assert packet_id in committed.packet_instance_ids
            stage("final output and route integrity")

        print("Issue #110 isolated installed-wheel acceptance: PASS", flush=True)
        """
    )


def smoke(concord_wheel: Path, core_wheel: Path) -> None:
    """Exercise Issue #110 using only isolated installed wheel imports."""
    if not concord_wheel.is_file():
        raise FileNotFoundError(concord_wheel)
    if not core_wheel.is_file():
        raise FileNotFoundError(core_wheel)

    core_sha = _sha256(core_wheel)
    if core_sha != EXPECTED_CORE_SHA256:
        raise RuntimeError(
            "Issue #110 requires the exact released Core 0.6.4 qualification wheel."
        )

    print(
        f"Issue #110 candidate wheel SHA-256: {_sha256(concord_wheel)}",
        flush=True,
    )
    print(
        f"Issue #110 Core wheel SHA-256: {core_sha}",
        flush=True,
    )

    with tempfile.TemporaryDirectory(
        prefix="concord-issue110-wheel-"
    ) as raw:
        work = Path(raw)
        env_root = work / "venv"
        venv.EnvBuilder(with_pip=True).create(env_root)
        python = _python(env_root)

        _run(
            [str(python), "-m", "pip", "install", str(core_wheel.resolve())],
            work,
        )
        _run(
            [str(python), "-m", "pip", "install", str(concord_wheel.resolve())],
            work,
        )
        _run([str(python), "-m", "pip", "check"], work)

        smoke_path = work / "issue110_installed_acceptance.py"
        smoke_path.write_text(_smoke_code(), encoding="utf-8")
        _run([str(python), "-I", str(smoke_path)], work)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("concord_wheel", type=Path)
    parser.add_argument("core_wheel", type=Path)
    args = parser.parse_args()
    smoke(args.concord_wheel, args.core_wheel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
