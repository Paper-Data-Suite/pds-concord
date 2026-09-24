"""Run Issue #105 returned-Artifact evidence opening from installed wheels."""

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
        from datetime import date, datetime, timezone
        from importlib import metadata
        from pathlib import Path

        import concord
        import pds_core
        import concord.workflows.artifact_evidence_opening as opening_module
        from PIL import Image
        from pds_core.class_metadata import (
            create_class_metadata,
            write_class_metadata_for_class,
        )
        from pds_core.local_open import LocalOpenError
        from pds_core.pds2 import parse_pds2_payload
        from pds_core.route_registrations import resolve_route_registration
        from pds_core.routing_models import ModuleWorkRef
        from pds_core.scan_retention import RetainedSourceScan
        from pds_core.workspace import ensure_workspace_root

        from concord.models import PrivacyPolicy
        from concord.storage import load_current_record_graph
        from concord.workflows import (
            ArtifactAssemblyIntegrityError,
            AssembleArtifactRequest,
            ConcordWorkflowConflictError,
            ConcordWorkflowOpenError,
            CreateActivityContextRequest,
            WorkflowActor,
            assemble_returned_artifact,
            create_activity_context,
            open_returned_artifact_evidence,
            resolve_returned_artifact_assembly,
        )
        from concord.workflows.artifact_page import (
            ArtifactPagePlan,
            PrepareArtifactPagesRequest,
            handle_concord_route,
            prepare_artifact_pages,
        )

        CLASS_ID = "class-issue105-installed"
        ACTIVITY_ID = "activity-issue105-installed"
        ARTIFACT_ID = "artifact-issue105-installed"


        def stage(name: str) -> None:
            print(f"issue105 installed wheel: {name}: PASS", flush=True)


        def require_installed(module: object, distribution: str) -> None:
            origin = Path(getattr(module, "__file__")).resolve()
            if "site-packages" not in str(origin).casefold():
                raise AssertionError(
                    f"{distribution} did not import from isolated "
                    f"site-packages: {origin}"
                )


        def clock() -> datetime:
            return datetime(2026, 9, 23, 23, 0, tzinfo=timezone.utc)


        def actor() -> WorkflowActor:
            return WorkflowActor(
                actor_id="teacher-issue105-installed",
                display_label="Synthetic Installed-Wheel Teacher",
                role_label="teacher",
            )


        require_installed(pds_core, "pds-core")
        require_installed(concord, "pds-concord")
        assert metadata.version("pds-core") == "0.6.3"
        assert metadata.version("pds-concord") == "0.3.0"
        stage("isolated installed provenance")

        with tempfile.TemporaryDirectory(
            prefix="concord-issue105-installed-"
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
            created = create_activity_context(
                CreateActivityContextRequest(
                    class_id=CLASS_ID,
                    activity_id=ACTIVITY_ID,
                    title="Issue 105 Installed Evidence Opening",
                    activity_type="project",
                    scoring_orientation="evidence_only",
                    session_id="session-issue105-installed",
                    actor=actor(),
                    activity_status="active",
                    session_status="active",
                ),
                workspace_root=root,
                clock=clock,
            )
            prepared = prepare_artifact_pages(
                PrepareArtifactPagesRequest(
                    class_id=CLASS_ID,
                    activity_id=ACTIVITY_ID,
                    artifact_instance_id=ARTIFACT_ID,
                    template_version_id="template-issue105-installed",
                    artifact_category="observation",
                    expected_snapshot_revision=created.commit.snapshot_revision,
                    actor=actor(),
                    pages=(
                        ArtifactPagePlan(
                            page_number=1,
                            artifact_page_id="page-issue105-installed",
                        ),
                    ),
                    privacy_policy=PrivacyPolicy(
                        classification="teacher_restricted"
                    ),
                ),
                workspace_root=root,
                clock=clock,
            )
            stage("real Artifact Page preparation")

            retained_path = (
                root
                / "scans"
                / "source"
                / "2026-09-23"
                / "issue105-returned.png"
            )
            retained_path.parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (100, 140), (40, 80, 120)).save(retained_path)
            retained = RetainedSourceScan(
                source_scan_id="scan-issue105-installed",
                source_filename=retained_path.name,
                source_sha256=hashlib.sha256(
                    retained_path.read_bytes()
                ).hexdigest(),
                retained_source_path=retained_path,
                retained_source_relative_path=retained_path.relative_to(
                    root
                ).as_posix(),
                intake_timestamp=clock(),
                intake_date=date(2026, 9, 23),
            )
            payload = prepared.pages[0].pds2_payload
            assert payload is not None
            locator = parse_pds2_payload(payload)
            resolution = resolve_route_registration(root, locator)
            routed = handle_concord_route(resolution, retained, 1)
            assert routed.artifact_instance_id == ARTIFACT_ID
            stage("real retained return and ScanReference")

            work = ModuleWorkRef("concord", CLASS_ID, ACTIVITY_ID)
            returned = load_current_record_graph(root, work)
            assembled = assemble_returned_artifact(
                AssembleArtifactRequest(
                    class_id=CLASS_ID,
                    activity_id=ACTIVITY_ID,
                    artifact_instance_id=ARTIFACT_ID,
                    expected_snapshot_revision=returned.snapshot_revision,
                    actor=actor(),
                ),
                workspace_root=root,
                clock=clock,
            )
            assert assembled.output_path.is_file()
            assert assembled.manifest_path.is_file()
            original_pdf = assembled.output_path.read_bytes()
            original_manifest = assembled.manifest_path.read_bytes()
            assert original_pdf.startswith(b"%PDF")
            stage("exact returned-Artifact assembly")

            canonical_before = load_current_record_graph(root, work)
            assert not canonical_before.graph.artifact_reviews
            assert not canonical_before.graph.moderation_records
            assert not canonical_before.graph.score_records

            resolved = resolve_returned_artifact_assembly(
                CLASS_ID,
                ACTIVITY_ID,
                ARTIFACT_ID,
                expected_snapshot_revision=canonical_before.snapshot_revision,
                workspace_root=root,
            )
            assert resolved.output_path == assembled.output_path
            assert resolved.manifest_path == assembled.manifest_path
            assert resolved.output_sha256 == assembled.output_sha256
            assert resolved.page_count == 1
            stage("exact verified evidence resolution")

            opened: list[Path] = []

            def fake_open(path: str | Path) -> Path:
                exact = Path(path)
                opened.append(exact)
                return exact

            opening_module.open_local_path = fake_open
            opened_result = open_returned_artifact_evidence(
                CLASS_ID,
                ACTIVITY_ID,
                ARTIFACT_ID,
                expected_snapshot_revision=canonical_before.snapshot_revision,
                workspace_root=root,
            )
            assert opened_result.output_path == assembled.output_path
            assert opened == [assembled.output_path]

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
            assert not canonical_after_open.graph.artifact_reviews
            assert not canonical_after_open.graph.moderation_records
            assert not canonical_after_open.graph.score_records
            stage("fake local opener and canonical nonmutation")

            opened.clear()
            try:
                open_returned_artifact_evidence(
                    CLASS_ID,
                    ACTIVITY_ID,
                    ARTIFACT_ID,
                    expected_snapshot_revision=(
                        canonical_before.snapshot_revision - 1
                    ),
                    workspace_root=root,
                )
            except ConcordWorkflowConflictError:
                pass
            else:
                raise AssertionError("stale teacher selection was opened")
            assert opened == []
            stage("stale selection rejected before viewer launch")

            assembled.output_path.write_bytes(
                original_pdf + b"\nissue105-installed-tamper"
            )
            opened.clear()
            try:
                open_returned_artifact_evidence(
                    CLASS_ID,
                    ACTIVITY_ID,
                    ARTIFACT_ID,
                    expected_snapshot_revision=canonical_before.snapshot_revision,
                    workspace_root=root,
                )
            except ArtifactAssemblyIntegrityError:
                pass
            else:
                raise AssertionError("tampered returned Artifact was opened")
            assert opened == []
            assert assembled.output_path.read_bytes().endswith(
                b"issue105-installed-tamper"
            )
            stage("tampered assembly rejected without repair")

            assembled.output_path.write_bytes(original_pdf)
            assembled.manifest_path.unlink()
            opened.clear()
            try:
                open_returned_artifact_evidence(
                    CLASS_ID,
                    ACTIVITY_ID,
                    ARTIFACT_ID,
                    expected_snapshot_revision=canonical_before.snapshot_revision,
                    workspace_root=root,
                )
            except ArtifactAssemblyIntegrityError:
                pass
            else:
                raise AssertionError("missing assembly manifest was opened")
            assert opened == []
            assert not assembled.manifest_path.exists()
            stage("missing manifest rejected without regeneration")

            assembled.manifest_path.write_bytes(original_manifest)

            def fail_open(path: str | Path) -> Path:
                del path
                raise LocalOpenError("synthetic installed viewer failure")

            opening_module.open_local_path = fail_open
            try:
                open_returned_artifact_evidence(
                    CLASS_ID,
                    ACTIVITY_ID,
                    ARTIFACT_ID,
                    expected_snapshot_revision=canonical_before.snapshot_revision,
                    workspace_root=root,
                )
            except ConcordWorkflowOpenError as error:
                assert isinstance(error.__cause__, LocalOpenError)
            else:
                raise AssertionError("viewer launch failure was not translated")
            stage("viewer failure translated after verification")

            canonical_final = load_current_record_graph(root, work)
            assert (
                canonical_final.snapshot_revision
                == canonical_before.snapshot_revision
            )
            assert canonical_final.snapshot_sha256 == canonical_before.snapshot_sha256
            assert canonical_final.graph == canonical_before.graph
            stage("all Open failure paths preserve canonical state")

        print("Issue #105 isolated installed-wheel acceptance: PASS", flush=True)
        """
    )


def smoke(concord_wheel: Path, core_wheel: Path) -> None:
    """Exercise Issue #105 using only isolated installed wheel imports."""
    if not concord_wheel.is_file():
        raise FileNotFoundError(concord_wheel)
    if not core_wheel.is_file():
        raise FileNotFoundError(core_wheel)
    core_sha = _sha256(core_wheel)
    if core_sha != EXPECTED_CORE_SHA256:
        raise RuntimeError(
            "Issue #105 requires the exact released Core 0.6.3 qualification wheel."
        )

    print(f"Issue #105 candidate wheel SHA-256: {_sha256(concord_wheel)}", flush=True)
    print(f"Issue #105 Core wheel SHA-256: {core_sha}", flush=True)

    with tempfile.TemporaryDirectory(prefix="concord-issue105-wheel-") as raw:
        work = Path(raw)
        env_root = work / "venv"
        venv.EnvBuilder(with_pip=True).create(env_root)
        python = _python(env_root)
        _run([str(python), "-m", "pip", "install", str(core_wheel.resolve())], work)
        _run([str(python), "-m", "pip", "install", str(concord_wheel.resolve())], work)
        _run([str(python), "-m", "pip", "check"], work)

        smoke_path = work / "issue105_installed_acceptance.py"
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
