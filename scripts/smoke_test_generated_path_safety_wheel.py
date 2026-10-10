"""Installed-wheel qualification for Concord Issue #124 generated paths."""

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
    "9ace75f17b23b7f0ed6a709d531af5120db43d0325b4148d26f2d6ba1d4b3c18"
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
        from PIL import Image
        from pds_core.class_metadata import (
            create_class_metadata,
            write_class_metadata_for_class,
        )
        from pds_core.classes import write_class_roster
        from pds_core.pds2 import parse_pds2_payload
        from pds_core.rosters import create_roster
        from pds_core.route_registrations import resolve_route_registration
        from pds_core.routing_models import ModuleWorkRef
        from pds_core.scan_retention import RetainedSourceScan, retain_source_scan
        from pds_core.scan_routes import (
            RETAINED_SOURCE_FILENAME_MAX_LENGTH,
            SOURCE_SCAN_ID_MAX_LENGTH,
            build_retained_source_filename,
            retained_source_scan_path,
        )
        from pds_core.workspace import ensure_workspace_root

        from concord.academic_result_manifest_generation import (
            GenerateAcademicResultManifestRequest,
            generate_academic_result_manifest,
        )
        from concord.academic_work_registration import (
            register_concord_academic_work,
        )
        from concord.generated_paths import (
            validate_generated_output_filename,
        )
        from concord.models import (
            PrivacyPolicy,
            ScoreTargetReference,
            ScoringScaleLevel,
        )
        from concord.storage import load_current_record_graph
        from concord.workflows import (
            AddScoreRequest,
            AssembleArtifactRequest,
            CreateActivityContextRequest,
            CreateCriterionSetRequest,
            CreateScoringScaleRequest,
            CriterionSpec,
            PreparePacketInstantiationRequest,
            PrepareStarterTemplateInstallRequest,
            RenderPacketInstanceRequest,
            SelectActivityCriterionSetsRequest,
            WorkflowActor,
            add_score,
            assemble_returned_artifact,
            commit_packet_instantiation,
            commit_starter_template_install,
            create_activity_context,
            create_criterion_set,
            create_scoring_scale,
            prepare_packet_instantiation,
            prepare_starter_template_install,
            render_packet_instance,
            select_activity_criterion_sets,
        )
        from concord.workflows.artifact_page import handle_concord_route
        from concord.workflows.packet import (
            PreparePacketFromTemplateRequest,
            commit_packet_from_template,
            prepare_packet_from_template,
        )

        LEGACY_CONTENT = (
            b"%PDF-1.4\n"
            b"issue226 legacy retained source fixture\n"
            b"%%EOF\n"
        )
        LEGACY_SOURCE_FILENAME = (
            "issue216_physical_regression_scan_with_deliberately_long_"
            "source_filename_for_diagnostic_testing.pdf"
        )
        LEGACY_RETAINED_FILENAME = (
            "20260930T031838064717Z__"
            "issue216_physical_regression_scan_with_deliberately_long_"
            "source_filename_for_diagnostic_testing__32cb9cc32500.pdf"
        )
        LEGACY_SOURCE_SCAN_ID = (
            "scan_20260930T031838064717Z__"
            "issue216_physical_regression_scan_with_deliberately_long_"
            "source_filename_for_diagnostic_testing__32cb9cc32500"
        )
        LEGACY_SHA256 = (
            "32cb9cc325003c1aa767fb08398e11f1481eed7e6e1d995101c768ab819151d7"
        )
        LEGACY_RELATIVE_PATH = (
            "scans/source/2026-09-30/" + LEGACY_RETAINED_FILENAME
        )


        def stage(name: str) -> None:
            print(f"issue124 installed wheel: {name}: PASS", flush=True)


        def require_installed(module: object, distribution: str) -> None:
            origin = Path(getattr(module, "__file__")).resolve()
            if "site-packages" not in str(origin).casefold():
                raise AssertionError(
                    f"{distribution} did not import from isolated "
                    f"site-packages: {origin}"
                )


        def clock() -> datetime:
            return datetime(2026, 10, 2, 23, 0, tzinfo=timezone.utc)


        def actor() -> WorkflowActor:
            return WorkflowActor(
                actor_id="teacher_issue124_installed",
                display_label="Synthetic Installed-Wheel Teacher",
                role_label="teacher",
            )


        def deep_workspace(base: Path) -> Path:
            candidate = base / "w"
            while len(str(candidate)) < 119:
                candidate = candidate / "d"
            candidate.mkdir(parents=True)
            assert 119 <= len(str(candidate)) <= 120
            return ensure_workspace_root(candidate)


        def setup_packet(
            root: Path,
            *,
            class_id: str,
            activity_id: str,
            session_id: str,
            student_id: str,
            suffix: str,
        ):
            write_class_metadata_for_class(
                root,
                create_class_metadata(
                    class_id,
                    "2026-2027",
                    created_at=clock(),
                ),
            )
            write_class_roster(
                root,
                create_roster(
                    class_id,
                    (
                        {
                            "student_id": student_id,
                            "last_name": "Student",
                            "first_name": "Synthetic",
                            "period": "1",
                        },
                    ),
                ),
            )
            created = create_activity_context(
                CreateActivityContextRequest(
                    class_id=class_id,
                    activity_id=activity_id,
                    title=f"Issue 124 {suffix}",
                    activity_type="project",
                    scoring_orientation="local_criteria_only",
                    session_id=session_id,
                    actor=actor(),
                    activity_status="active",
                    session_status="active",
                    session_label="Issue 124",
                ),
                workspace_root=root,
                clock=clock,
            )
            scale = create_scoring_scale(
                CreateScoringScaleRequest(
                    class_id=class_id,
                    activity_id=activity_id,
                    scoring_scale_id=f"scale_{suffix}",
                    lineage_id=f"scale_lineage_{suffix}",
                    name=f"Issue 124 {suffix} Scale",
                    revision=1,
                    scale_type="teacher_defined",
                    levels=(
                        ScoringScaleLevel(
                            value=1,
                            label="Observed",
                            meaning="Synthetic installed acceptance level.",
                        ),
                    ),
                    status="active",
                    expected_snapshot_revision=(
                        created.commit.snapshot_revision
                    ),
                    actor=actor(),
                ),
                workspace_root=root,
                clock=clock,
            )
            criterion_set = create_criterion_set(
                CreateCriterionSetRequest(
                    class_id=class_id,
                    activity_id=activity_id,
                    criterion_set_id=f"criterion_set_{suffix}",
                    lineage_id=f"criterion_set_lineage_{suffix}",
                    name=f"Issue 124 {suffix} Criteria",
                    purpose="Installed generated-path qualification.",
                    revision=1,
                    scope="activity_specific",
                    criterion_set_kind="local",
                    criteria=(
                        CriterionSpec(
                            criterion_id=f"criterion_{suffix}",
                            key="path_qualification",
                            label="Path qualification",
                            definition=(
                                "Synthetic local criterion for installed "
                                "manifest qualification."
                            ),
                            criterion_kind="local",
                            supported_target_kinds=("core_student",),
                            default_scoring_scale_id=f"scale_{suffix}",
                        ),
                    ),
                    status="active",
                    expected_snapshot_revision=(
                        scale.commit.snapshot_revision
                    ),
                    actor=actor(),
                ),
                workspace_root=root,
                clock=clock,
            )
            selected = select_activity_criterion_sets(
                SelectActivityCriterionSetsRequest(
                    class_id=class_id,
                    activity_id=activity_id,
                    criterion_set_ids=(f"criterion_set_{suffix}",),
                    expected_snapshot_revision=(
                        criterion_set.commit.snapshot_revision
                    ),
                    actor=actor(),
                ),
                workspace_root=root,
                clock=clock,
            )
            add_score(
                AddScoreRequest(
                    class_id=class_id,
                    activity_id=activity_id,
                    score_record_id=f"score_{suffix}",
                    target_reference=ScoreTargetReference(
                        target_kind="core_student",
                        target_id=student_id,
                        owning_system="core",
                    ),
                    criterion_id=f"criterion_{suffix}",
                    scoring_scale_id=f"scale_{suffix}",
                    disposition="scored",
                    value=1,
                    basis="professional_judgment",
                    rationale="Synthetic installed path qualification Score.",
                    privacy_policy=PrivacyPolicy(
                        classification="teacher_restricted"
                    ),
                    expected_snapshot_revision=(
                        selected.commit.snapshot_revision
                    ),
                    actor=actor(),
                    session_id=session_id,
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
            prepared_packet = prepare_packet_from_template(
                PreparePacketFromTemplateRequest(
                    packet_definition_id=f"packet_{suffix}",
                    packet_version_id=f"packet_version_{suffix}",
                    packet_component_id=f"component_{suffix}",
                    name=f"Issue 124 {suffix} Packet",
                    purpose="Installed generated-path qualification.",
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
            prepared = prepare_packet_instantiation(
                PreparePacketInstantiationRequest(
                    class_id=class_id,
                    activity_id=activity_id,
                    session_id=session_id,
                    packet_definition_id=f"packet_{suffix}",
                    packet_version_id=f"packet_version_{suffix}",
                    actor=actor(),
                ),
                workspace_root=root,
                clock=clock,
            )
            committed = commit_packet_instantiation(
                prepared,
                workspace_root=root,
                generation_id=f"generation_{suffix}",
                clock=clock,
            )
            assert len(committed.packet_instance_ids) == 1
            rendered = render_packet_instance(
                RenderPacketInstanceRequest(
                    class_id=class_id,
                    activity_id=activity_id,
                    packet_instance_id=committed.packet_instance_ids[0],
                    actor=actor(),
                ),
                workspace_root=root,
            )
            assert len(rendered.payloads) == 1
            return created, rendered


        def route_retained(root: Path, payload: str, retained: RetainedSourceScan):
            locator = parse_pds2_payload(payload)
            resolution = resolve_route_registration(root, locator)
            return handle_concord_route(resolution, retained, 1)


        require_installed(pds_core, "pds-core")
        require_installed(concord, "pds-concord")
        assert metadata.version("pds-core") == "0.6.5"
        assert metadata.version("pds-concord") == "0.3.1"
        stage("isolated installed provenance")

        with tempfile.TemporaryDirectory(
            prefix="concord-issue124-installed-"
        ) as raw:
            base = Path(raw)
            root = deep_workspace(base / "deep")
            class_id = "class_issue124_deep"
            activity_id = "activity_issue124_deep"
            session_id = "session_issue124_deep"
            _, rendered = setup_packet(
                root,
                class_id=class_id,
                activity_id=activity_id,
                session_id=session_id,
                student_id="student_issue124",
                suffix="issue124_deep",
            )

            assert rendered.output_path.is_file()
            assert rendered.output_path.read_bytes().startswith(b"%PDF")
            assert rendered.output_path.parent.name == "packets"
            assert rendered.output_path.name.startswith("cgo_")
            assert len(rendered.output_path.name) == 32
            assert (
                validate_generated_output_filename(rendered.output_path.name)
                == rendered.output_path.name
            )
            replay = render_packet_instance(
                RenderPacketInstanceRequest(
                    class_id=class_id,
                    activity_id=activity_id,
                    packet_instance_id=rendered.packet_instance_id,
                    actor=actor(),
                ),
                workspace_root=root,
            )
            assert replay.replayed
            assert replay.output_path == rendered.output_path
            assert replay.output_sha256 == rendered.output_sha256
            stage("deep bounded Packet render and replay")

            external = base / "external"
            external.mkdir()
            source_name = (
                "scanner_export_with_deliberately_long_original_name_" * 3
                + ".png"
            )
            source = external / source_name
            Image.new("RGB", (100, 140), (30, 60, 90)).save(source)
            source_bytes = source.read_bytes()
            retained = retain_source_scan(
                root,
                source,
                intake_timestamp=clock(),
            )
            assert retained.source_filename == source.name
            assert retained.source_sha256 == hashlib.sha256(
                source_bytes
            ).hexdigest()
            assert retained.retained_source_path.read_bytes() == source_bytes
            assert (
                len(retained.retained_source_path.name)
                <= RETAINED_SOURCE_FILENAME_MAX_LENGTH
            )
            assert len(retained.source_scan_id) <= SOURCE_SCAN_ID_MAX_LENGTH
            assert source.stem not in retained.retained_source_path.name
            assert retained.retained_source_path.is_relative_to(root)
            stage("Core 0.6.5 bounded retained-source writer")

            routed = route_retained(root, rendered.payloads[0], retained)
            work = ModuleWorkRef("concord", class_id, activity_id)
            returned = load_current_record_graph(root, work)
            scan = next(
                item
                for item in returned.graph.scan_references
                if item.scan_reference_id == routed.scan_reference_id
            )
            assert scan.source_scan_id == retained.source_scan_id
            assert (
                scan.retained_source_relative_path
                == retained.retained_source_relative_path
            )
            assert scan.retained_source_sha256 == retained.source_sha256

            assembled = assemble_returned_artifact(
                AssembleArtifactRequest(
                    class_id=class_id,
                    activity_id=activity_id,
                    artifact_instance_id=routed.artifact_instance_id,
                    expected_snapshot_revision=returned.snapshot_revision,
                    actor=actor(),
                ),
                workspace_root=root,
                clock=clock,
            )
            assert assembled.output_path.is_file()
            assert assembled.manifest_path.is_file()
            assert assembled.output_path.name == "artifact.pdf"
            assert assembled.manifest_path.name == "manifest.json"
            assert assembled.assembly_id.startswith("assembly_")
            assert len(assembled.assembly_id) == len("assembly_") + 32
            stage("deep retained-Artifact assembly")

            register_concord_academic_work(
                root,
                class_id,
                activity_id,
                academic_intent="formative",
                lifecycle="active",
            )
            current = load_current_record_graph(root, work)
            manifest = generate_academic_result_manifest(
                GenerateAcademicResultManifestRequest(
                    class_id=class_id,
                    activity_id=activity_id,
                    expected_snapshot_revision=current.snapshot_revision,
                    actor=actor(),
                    revision_reason="initial",
                ),
                workspace_root=root,
                clock=clock,
            )
            assert manifest.disposition == "created"
            assert manifest.revision == 1
            assert manifest.path.is_file()
            assert manifest.path.name == "1.json"
            assert manifest.path.read_bytes() == manifest.content
            assert manifest.relative_path.endswith(
                "/exports/manifests/academic_results/1.json"
            )
            manifest_replay = generate_academic_result_manifest(
                GenerateAcademicResultManifestRequest(
                    class_id=class_id,
                    activity_id=activity_id,
                    expected_snapshot_revision=current.snapshot_revision,
                    actor=actor(),
                    revision_reason="initial",
                ),
                workspace_root=root,
                clock=clock,
            )
            assert manifest_replay.disposition == "existing"
            assert manifest_replay.path == manifest.path
            assert manifest_replay.content == manifest.content
            stage("deep immutable Academic Result Manifest")

            legacy_root = ensure_workspace_root(base / "legacy_workspace")
            legacy_class = "class_issue124_legacy"
            legacy_activity = "activity_issue124_legacy"
            _, legacy_rendered = setup_packet(
                legacy_root,
                class_id=legacy_class,
                activity_id=legacy_activity,
                session_id="session_issue124_legacy",
                student_id="student_issue124_legacy",
                suffix="issue124_legacy",
            )

            assert hashlib.sha256(LEGACY_CONTENT).hexdigest() == LEGACY_SHA256
            assert (
                len(LEGACY_RETAINED_FILENAME)
                > RETAINED_SOURCE_FILENAME_MAX_LENGTH
            )
            assert len(LEGACY_SOURCE_SCAN_ID) > SOURCE_SCAN_ID_MAX_LENGTH
            legacy_path = retained_source_scan_path(
                legacy_root,
                intake_date="2026-09-30",
                retained_filename=LEGACY_RETAINED_FILENAME,
            )
            legacy_path.parent.mkdir(parents=True, exist_ok=True)
            legacy_path.write_bytes(LEGACY_CONTENT)
            legacy_retained = RetainedSourceScan(
                source_scan_id=LEGACY_SOURCE_SCAN_ID,
                source_filename=LEGACY_SOURCE_FILENAME,
                source_sha256=LEGACY_SHA256,
                retained_source_path=legacy_path,
                retained_source_relative_path=LEGACY_RELATIVE_PATH,
                intake_timestamp=datetime.fromisoformat(
                    "2026-09-30T03:18:38.064717+00:00"
                ),
                intake_date=date(2026, 9, 30),
            )
            bounded_legacy_name = build_retained_source_filename(
                intake_timestamp=legacy_retained.intake_timestamp,
                original_filename=legacy_retained.source_filename,
                sha256_hex=legacy_retained.source_sha256,
            )
            assert bounded_legacy_name != LEGACY_RETAINED_FILENAME
            assert not (legacy_path.parent / bounded_legacy_name).exists()

            legacy_routed = route_retained(
                legacy_root,
                legacy_rendered.payloads[0],
                legacy_retained,
            )
            legacy_work = ModuleWorkRef(
                "concord",
                legacy_class,
                legacy_activity,
            )
            legacy_graph = load_current_record_graph(
                legacy_root,
                legacy_work,
            )
            legacy_scan = next(
                item
                for item in legacy_graph.graph.scan_references
                if item.scan_reference_id == legacy_routed.scan_reference_id
            )
            assert legacy_scan.source_scan_id == LEGACY_SOURCE_SCAN_ID
            assert (
                legacy_scan.retained_source_relative_path
                == LEGACY_RELATIVE_PATH
            )
            assert legacy_scan.retained_source_sha256 == LEGACY_SHA256
            assert legacy_path.read_bytes() == LEGACY_CONTENT
            assert not (legacy_path.parent / bounded_legacy_name).exists()

            legacy_replay = route_retained(
                legacy_root,
                legacy_rendered.payloads[0],
                legacy_retained,
            )
            assert legacy_replay.replayed
            assert (
                legacy_replay.scan_reference_id
                == legacy_routed.scan_reference_id
            )
            stage("legacy Core 0.6 retained provenance without migration")

        print("Issue #124 isolated installed-wheel acceptance: PASS", flush=True)
        """
    )


def smoke(concord_wheel: Path, core_wheel: Path) -> None:
    """Exercise Issue #124 using only isolated installed wheel imports."""
    if not concord_wheel.is_file():
        raise FileNotFoundError(concord_wheel)
    if not core_wheel.is_file():
        raise FileNotFoundError(core_wheel)
    core_sha = _sha256(core_wheel)
    if core_sha != EXPECTED_CORE_SHA256:
        raise RuntimeError(
            "Issue #124 requires the exact released Core 0.6.5 qualification wheel."
        )

    print(f"Issue #124 candidate wheel SHA-256: {_sha256(concord_wheel)}", flush=True)
    print(f"Issue #124 Core wheel SHA-256: {core_sha}", flush=True)

    with tempfile.TemporaryDirectory(prefix="concord-issue124-wheel-") as raw:
        work = Path(raw)
        env_root = work / "venv"
        venv.EnvBuilder(with_pip=True).create(env_root)
        python = _python(env_root)
        _run([str(python), "-m", "pip", "install", str(core_wheel.resolve())], work)
        _run([str(python), "-m", "pip", "install", str(concord_wheel.resolve())], work)
        _run([str(python), "-m", "pip", "check"], work)

        smoke_path = work / "issue124_installed_acceptance.py"
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
