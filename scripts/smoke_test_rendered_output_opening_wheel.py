"""Run Issue #101 rendered-output opening acceptance from installed wheels."""

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
    "98d7596ce0eed26e4d56a17bbbbd644db3014259b56a45783a173fe8237af5e5"
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

        import hashlib
        import tempfile
        from datetime import datetime, timezone
        from importlib import metadata
        from pathlib import Path

        import concord
        import pds_core
        import concord.workflows.rendered_output as rendered_output_module
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

        from concord.storage import load_current_record_graph
        from concord.workflows import (
            CreateActivityContextRequest,
            PreparePacketInstantiationRequest,
            PrepareStarterTemplateInstallRequest,
            RenderPacketInstanceRequest,
            WorkflowActor,
            commit_packet_instantiation,
            commit_starter_template_install,
            create_activity_context,
            open_rendered_packet_output,
            open_rendered_packet_output_directory,
            prepare_packet_instantiation,
            prepare_starter_template_install,
            render_packet_instance,
            resolve_rendered_packet_output,
        )
        from concord.workflows.errors import (
            ConcordWorkflowConflictError,
            ConcordWorkflowNotFoundError,
        )
        from concord.workflows.packet import (
            PreparePacketFromTemplateRequest,
            commit_packet_from_template,
            prepare_packet_from_template,
        )

        CLASS_ID = "class-issue101-installed"
        ACTIVITY_ID = "activity-issue101-installed"
        SESSION_ID = "session-issue101-installed"


        def stage(name: str) -> None:
            print(f"issue101 installed wheel: {name}: PASS", flush=True)


        def require_installed(module: object, distribution: str) -> None:
            origin = Path(getattr(module, "__file__")).resolve()
            if "site-packages" not in str(origin).casefold():
                raise AssertionError(
                    f"{distribution} did not import from isolated "
                    f"site-packages: {origin}"
                )


        def clock() -> datetime:
            return datetime(2026, 9, 21, 15, 0, tzinfo=timezone.utc)


        def actor() -> WorkflowActor:
            return WorkflowActor(
                actor_id="teacher-issue101-installed",
                display_label="Synthetic Installed-Wheel Teacher",
                role_label="teacher",
            )


        require_installed(pds_core, "pds-core")
        require_installed(concord, "pds-concord")
        assert metadata.version("pds-core") == "0.6.3"
        assert metadata.version("pds-concord") == "0.3.0"
        stage("isolated installed provenance")

        with tempfile.TemporaryDirectory(
            prefix="concord-issue101-installed-"
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
                    ),
                ),
            )
            created = create_activity_context(
                CreateActivityContextRequest(
                    class_id=CLASS_ID,
                    activity_id=ACTIVITY_ID,
                    title="Issue 101 Installed Output Opening",
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
            assert created.commit.snapshot_revision >= 1

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
            prepared_packet = prepare_packet_from_template(
                PreparePacketFromTemplateRequest(
                    packet_definition_id="packet-issue101-installed",
                    packet_version_id="packet-issue101-installed-v1",
                    packet_component_id="component-issue101-installed",
                    name="Issue 101 Installed Packet",
                    purpose="Exercise exact installed rendered-output opening.",
                    template_id=installed.template_id,
                    template_version_id=installed.template_version_id,
                    audience_kind="participant",
                    actor=actor(),
                ),
                workspace_root=root,
                clock=clock,
            )
            commit_packet_from_template(
                prepared_packet,
                workspace_root=root,
            )
            stage("starter and reusable Packet setup")

            prepared = prepare_packet_instantiation(
                PreparePacketInstantiationRequest(
                    class_id=CLASS_ID,
                    activity_id=ACTIVITY_ID,
                    session_id=SESSION_ID,
                    packet_definition_id="packet-issue101-installed",
                    packet_version_id="packet-issue101-installed-v1",
                    actor=actor(),
                ),
                workspace_root=root,
                clock=clock,
            )
            assert prepared.ready_for_commit
            assert prepared.packet_instance_count == 1
            committed = commit_packet_instantiation(
                prepared,
                workspace_root=root,
                generation_id="generation-issue101-installed",
                clock=clock,
            )
            assert len(committed.packet_instance_ids) == 1
            packet_instance_id = committed.packet_instance_ids[0]
            assert committed.routes_verified == committed.routes_expected
            stage("real Packet instantiation and PDS2 routes")

            rendered = render_packet_instance(
                RenderPacketInstanceRequest(
                    class_id=CLASS_ID,
                    activity_id=ACTIVITY_ID,
                    packet_instance_id=packet_instance_id,
                    actor=actor(),
                ),
                workspace_root=root,
            )
            original_bytes = rendered.output_path.read_bytes()
            assert original_bytes.startswith(b"%PDF")
            assert hashlib.sha256(original_bytes).hexdigest() == (
                rendered.output_sha256
            )
            work = ModuleWorkRef("concord", CLASS_ID, ACTIVITY_ID)
            canonical_before = load_current_record_graph(root, work)
            routes_before = tuple(
                load_route_registration(
                    root,
                    parse_pds2_payload(payload),
                )
                for payload in rendered.payloads
            )
            stage("real PDF rendering")

            resolved = resolve_rendered_packet_output(
                CLASS_ID,
                ACTIVITY_ID,
                packet_instance_id,
                workspace_root=root,
            )
            assert resolved.output_path == rendered.output_path
            assert resolved.output_sha256 == rendered.output_sha256
            assert resolved.page_count == rendered.page_count
            assert resolved.route_count == rendered.route_count
            stage("exact output path and SHA-256 resolution")

            opened: list[Path] = []

            def fake_open(path: str | Path) -> Path:
                exact = Path(path)
                opened.append(exact)
                return exact

            rendered_output_module.open_local_path = fake_open

            opened_pdf = open_rendered_packet_output(
                CLASS_ID,
                ACTIVITY_ID,
                packet_instance_id,
                workspace_root=root,
            )
            opened_folder = open_rendered_packet_output_directory(
                CLASS_ID,
                ACTIVITY_ID,
                packet_instance_id,
                workspace_root=root,
            )
            assert opened_pdf.output_path == rendered.output_path
            assert opened_folder.output_directory == rendered.output_path.parent
            assert opened == [
                rendered.output_path,
                rendered.output_path.parent,
            ]

            canonical_after_open = load_current_record_graph(root, work)
            assert (
                canonical_after_open.snapshot_revision
                == canonical_before.snapshot_revision
            )
            assert (
                canonical_after_open.snapshot_sha256
                == canonical_before.snapshot_sha256
            )
            assert canonical_after_open.graph == canonical_before.graph
            routes_after_open = tuple(
                load_route_registration(
                    root,
                    parse_pds2_payload(payload),
                )
                for payload in rendered.payloads
            )
            assert routes_after_open == routes_before
            stage("fake local opener and canonical nonmutation")

            rendered.output_path.write_bytes(
                original_bytes + b"\nissue101-installed-tamper"
            )
            opened.clear()
            try:
                open_rendered_packet_output(
                    CLASS_ID,
                    ACTIVITY_ID,
                    packet_instance_id,
                    workspace_root=root,
                )
            except ConcordWorkflowConflictError:
                pass
            else:
                raise AssertionError("tampered rendered output was opened")
            assert opened == []
            assert rendered.output_path.read_bytes().endswith(
                b"issue101-installed-tamper"
            )
            canonical_after_tamper = load_current_record_graph(root, work)
            assert (
                canonical_after_tamper.snapshot_revision
                == canonical_before.snapshot_revision
            )
            assert (
                canonical_after_tamper.snapshot_sha256
                == canonical_before.snapshot_sha256
            )
            stage("tampered output rejected without repair")

            rendered.output_path.write_bytes(original_bytes)
            assert hashlib.sha256(rendered.output_path.read_bytes()).hexdigest() == (
                rendered.output_sha256
            )
            rendered.output_path.unlink()
            opened.clear()
            try:
                open_rendered_packet_output(
                    CLASS_ID,
                    ACTIVITY_ID,
                    packet_instance_id,
                    workspace_root=root,
                )
            except ConcordWorkflowNotFoundError:
                pass
            else:
                raise AssertionError("missing rendered output was opened")
            assert opened == []
            assert not rendered.output_path.exists()
            canonical_after_missing = load_current_record_graph(root, work)
            assert (
                canonical_after_missing.snapshot_revision
                == canonical_before.snapshot_revision
            )
            assert (
                canonical_after_missing.snapshot_sha256
                == canonical_before.snapshot_sha256
            )
            routes_after_missing = tuple(
                load_route_registration(
                    root,
                    parse_pds2_payload(payload),
                )
                for payload in rendered.payloads
            )
            assert routes_after_missing == routes_before
            assert not rendered.output_path.exists()
            stage("missing output rejected without regeneration")

        print("Issue #101 isolated installed-wheel acceptance: PASS", flush=True)
        """
    )


def smoke(concord_wheel: Path, core_wheel: Path) -> None:
    """Exercise Issue #101 using only isolated installed wheel imports."""
    if not concord_wheel.is_file():
        raise FileNotFoundError(concord_wheel)
    if not core_wheel.is_file():
        raise FileNotFoundError(core_wheel)
    core_sha = _sha256(core_wheel)
    if core_sha != EXPECTED_CORE_SHA256:
        raise RuntimeError(
            "Issue #101 requires the exact released Core 0.6.3 qualification wheel."
        )

    print(f"Issue #101 candidate wheel SHA-256: {_sha256(concord_wheel)}", flush=True)
    print(f"Issue #101 Core wheel SHA-256: {core_sha}", flush=True)

    with tempfile.TemporaryDirectory(prefix="concord-issue101-wheel-") as raw:
        work = Path(raw)
        env_root = work / "venv"
        venv.EnvBuilder(with_pip=True).create(env_root)
        python = _python(env_root)
        _run([str(python), "-m", "pip", "install", str(core_wheel.resolve())], work)
        _run([str(python), "-m", "pip", "install", str(concord_wheel.resolve())], work)
        _run([str(python), "-m", "pip", "check"], work)

        smoke_path = work / "issue101_installed_acceptance.py"
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
