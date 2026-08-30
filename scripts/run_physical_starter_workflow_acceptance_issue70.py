"""Prepare and resume Concord issue #70 owner-only physical acceptance."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import venv
from pathlib import Path
from typing import Any, cast

EXPECTED_CORE_VERSION = "0.6.3"
EXPECTED_CORE_WHEEL = "pds_core-0.6.3-py3-none-any.whl"
EXPECTED_CORE_SHA256 = (
    "98d7596ce0eed26e4d56a17bbbbd644db3014259b56a45783a173fe8237af5e5"
)
EXPECTED_CONCORD_VERSION = "0.3.0.dev0"
RUN_METADATA = "run-metadata.json"
STATE_FILE = "physical-state.json"
EVIDENCE_FILE = "physical-evidence-summary.json"
COMMENT_FILE = "issue70-completion-comment.md"
PRINT_DIR = "print"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _python(venv_root: Path) -> Path:
    return (
        venv_root / "Scripts" / "python.exe"
        if os.name == "nt"
        else venv_root / "bin" / "python"
    )


def _run(command: list[str], cwd: Path) -> None:
    subprocess.run(
        command,
        cwd=cwd,
        check=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )


def _load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def _write_json(path: Path, value: dict[str, object]) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _json_string(value: dict[str, object], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item:
        raise RuntimeError(f"JSON state is missing string field: {key}")
    return item


def _json_int(value: dict[str, object], key: str) -> int:
    item = value.get(key)
    if isinstance(item, bool) or not isinstance(item, int):
        raise RuntimeError(f"JSON state is missing integer field: {key}")
    return item


def _json_strings(value: dict[str, object], key: str) -> tuple[str, ...]:
    item = value.get(key)
    if not isinstance(item, list) or not item:
        raise RuntimeError(f"JSON state is missing string-list field: {key}")
    if any(not isinstance(entry, str) or not entry for entry in item):
        raise RuntimeError(f"JSON state has invalid string-list field: {key}")
    return tuple(item)


def _json_cases(value: dict[str, object]) -> tuple[dict[str, object], ...]:
    raw = value.get("cases")
    if not isinstance(raw, list) or not raw:
        raise RuntimeError("physical state is missing cases")
    result: list[dict[str, object]] = []
    for item in raw:
        if not isinstance(item, dict):
            raise RuntimeError("physical state contains an invalid case")
        if any(not isinstance(key, str) for key in item):
            raise RuntimeError("physical state case contains a non-string key")
        result.append(cast(dict[str, object], item))
    return tuple(result)


def _git_head(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    value = result.stdout.strip()
    if result.returncode != 0 or len(value) != 40:
        raise RuntimeError(
            "could not determine final commit; run from a Git checkout at the "
            "exact merged commit"
        )
    return value


def _require_fresh_run_root(run_root: Path) -> None:
    if run_root.exists():
        if any(run_root.iterdir()):
            raise RuntimeError(
                f"physical acceptance run directory is not empty: {run_root}"
            )
    else:
        run_root.mkdir(parents=True)


def _script_path() -> Path:
    return Path(__file__).resolve()


def _prepare_public(args: argparse.Namespace) -> int:
    concord_wheel = Path(args.concord_wheel).resolve()
    core_wheel = Path(args.core_wheel).resolve()
    run_root = Path(args.run_root).resolve()
    for label, path in (("Concord wheel", concord_wheel), ("Core wheel", core_wheel)):
        if not path.is_file():
            raise RuntimeError(f"{label} does not exist: {path}")
    if core_wheel.name != EXPECTED_CORE_WHEEL:
        raise RuntimeError(
            f"Core wheel must be {EXPECTED_CORE_WHEEL}, got {core_wheel.name}"
        )
    core_sha256 = _sha256(core_wheel)
    if core_sha256 != EXPECTED_CORE_SHA256:
        raise RuntimeError(
            "Core wheel SHA-256 does not match the released issue #70 baseline"
        )
    concord_sha256 = _sha256(concord_wheel)
    _require_fresh_run_root(run_root)

    source_root = _script_path().parents[1]
    final_commit = _git_head(source_root)
    venv_root = run_root / "venv"
    venv.EnvBuilder(with_pip=True, clear=True).create(venv_root)
    python = _python(venv_root)
    _run([str(python), "-m", "pip", "install", str(core_wheel)], run_root)
    _run([str(python), "-m", "pip", "install", str(concord_wheel)], run_root)
    _run([str(python), "-m", "pip", "check"], run_root)

    metadata: dict[str, object] = {
        "schema_version": 1,
        "final_commit": final_commit,
        "concord_wheel_filename": concord_wheel.name,
        "concord_wheel_path": str(concord_wheel),
        "concord_wheel_byte_length": concord_wheel.stat().st_size,
        "concord_wheel_sha256": concord_sha256,
        "core_wheel_filename": core_wheel.name,
        "core_wheel_path": str(core_wheel),
        "core_wheel_byte_length": core_wheel.stat().st_size,
        "core_wheel_sha256": core_sha256,
        "venv_relative_path": "venv",
        "state_relative_path": STATE_FILE,
    }
    _write_json(run_root / RUN_METADATA, metadata)
    _run(
        [
            str(python),
            "-I",
            str(_script_path()),
            "_installed-prepare",
            str(run_root),
        ],
        run_root,
    )
    print("\nPhysical acceptance preparation complete.")
    print(f"Print every PDF under: {run_root / PRINT_DIR}")
    print("Physically write PDS70 and representative synthetic marks on each family.")
    print("Scan every printed page, then run the resume command with all scan paths.")
    return 0


def _resume_public(args: argparse.Namespace) -> int:
    run_root = Path(args.run_root).resolve()
    metadata = _load_json(run_root / RUN_METADATA)
    venv_relative = metadata.get("venv_relative_path")
    if not isinstance(venv_relative, str):
        raise RuntimeError("run metadata is missing venv_relative_path")
    python = _python(run_root / venv_relative)
    if not python.is_file():
        raise RuntimeError(f"physical acceptance venv is unavailable: {python}")
    scans = tuple(Path(value).resolve() for value in args.scan)
    if not scans:
        raise RuntimeError("at least one physical scan is required")
    for scan in scans:
        if not scan.is_file():
            raise RuntimeError(f"physical scan does not exist: {scan}")

    command = [
        str(python),
        "-I",
        str(_script_path()),
        "_installed-resume",
        str(run_root),
    ]
    for scan in scans:
        command.extend(("--scan", str(scan)))
    command.extend(("--tester", args.tester))
    command.extend(("--printer", args.printer))
    command.extend(("--printer-path", args.printer_path))
    command.extend(("--paper-size", args.paper_size))
    command.extend(("--print-scaling", args.print_scaling))
    command.extend(("--print-sides", args.print_sides))
    command.extend(("--print-color-mode", args.print_color_mode))
    command.extend(("--scanner", args.scanner))
    command.extend(("--scanner-path", args.scanner_path))
    command.extend(("--scan-dpi", str(args.scan_dpi)))
    command.extend(("--scan-color-mode", args.scan_color_mode))
    command.extend(("--scan-sides", args.scan_sides))
    command.extend(("--scan-adjustments", args.scan_adjustments))
    if args.physical_mark_confirmed:
        command.append("--physical-mark-confirmed")
    if args.visual_inspection_confirmed:
        command.append("--visual-inspection-confirmed")
    _run(command, run_root)
    print("\nTechnical physical-path execution completed.")
    print(f"Evidence summary: {run_root / EVIDENCE_FILE}")
    print(f"Issue-comment template: {run_root / COMMENT_FILE}")
    print(
        "The harness does not declare a physical PASS. Review the evidence and "
        "classify seminar, project, peer review, and overall acceptance manually."
    )
    return 0


def _require_installed(module: object, distribution: str) -> str:
    origin = Path(getattr(module, "__file__")).resolve()
    if "site-packages" not in str(origin).casefold():
        raise RuntimeError(
            f"{distribution} did not import from isolated site-packages: {origin}"
        )
    return str(origin)


def _installed_modules() -> dict[str, object]:
    from importlib import metadata

    import pds_core

    import concord

    if metadata.version("pds-core") != EXPECTED_CORE_VERSION:
        raise RuntimeError("installed pds-core version does not match issue #70")
    if metadata.version("pds-concord") != EXPECTED_CONCORD_VERSION:
        raise RuntimeError("installed pds-concord version does not match issue #70")
    requirements = tuple(metadata.requires("pds-concord") or ())
    forbidden = ("meridian", "paper-data-suite")
    if any(
        name in requirement.casefold()
        for requirement in requirements
        for name in forbidden
    ):
        raise RuntimeError("physical acceptance installed forbidden runtime dependency")
    return {
        "concord_origin": _require_installed(concord, "pds-concord"),
        "core_origin": _require_installed(pds_core, "pds-core"),
    }


def _actor() -> Any:
    from concord.workflows import WorkflowActor

    return WorkflowActor(
        actor_id="teacher-issue70-physical",
        display_label="Synthetic Teacher",
        role_label="teacher",
    )


def _current_revision(root: Path, class_id: str, activity_id: str) -> int:
    from concord.workflows import show_activity

    return show_activity(
        class_id,
        activity_id,
        workspace_root=root,
    ).summary.snapshot_revision


def _installed_prepare(run_root: Path) -> int:
    import shutil as installed_shutil
    from datetime import datetime, timezone
    from importlib import metadata

    from pds_core.class_metadata import (
        create_class_metadata,
        write_class_metadata_for_class,
    )
    from pds_core.classes import write_class_roster
    from pds_core.grouping_signal_storage import (
        calculate_grouping_signal_digest,
        write_grouping_signal,
    )
    from pds_core.grouping_signals import (
        GroupingSignalDimension,
        GroupingSignalSet,
        GroupingSignalSource,
        GroupingSignalStudentBand,
    )
    from pds_core.pds2 import parse_pds2_payload
    from pds_core.rosters import create_roster
    from pds_core.routing_models import ModuleWorkRef
    from pds_core.workspace import ensure_workspace_root

    from concord.models import EffectiveContext, PlannedGroup
    from concord.starter_templates import get_starter_template
    from concord.storage import load_current_record_graph
    from concord.workflows import (
        ApplyGroupPlanRequest,
        ApproveGroupPlanRequest,
        CreateActivityContextRequest,
        CreateManualGroupPlanRequest,
        CreateRandomGroupPlanRequest,
        CreateSignalGroupPlanRequest,
        PrepareGroupPlanApplicationRequest,
        PreparePacketInstantiationRequest,
        PrepareStarterTemplateInstallRequest,
        PreviewGroupPlanRequest,
        apply_group_plan,
        approve_group_plan,
        commit_packet_instantiation,
        commit_starter_template_install,
        create_activity_context,
        create_manual_group_plan,
        create_random_group_plan,
        create_signal_group_plan,
        prepare_group_plan_application,
        prepare_packet_instantiation,
        prepare_starter_template_install,
        preview_group_plan,
    )
    from concord.workflows.packet import (
        PreparePacketFromTemplateRequest,
        commit_packet_from_template,
        prepare_packet_from_template,
    )
    from concord.workflows.packet_rendering import (
        RenderPacketInstanceRequest,
        render_packet_instance,
    )

    installed = _installed_modules()
    outer = _load_json(run_root / RUN_METADATA)
    workspace = ensure_workspace_root(run_root / "workspace")
    os.environ["PDS_WORKSPACE_ROOT"] = str(workspace)
    print_root = run_root / PRINT_DIR
    print_root.mkdir()
    class_id = "class-issue70-physical"
    actor = _actor()

    write_class_metadata_for_class(
        workspace,
        create_class_metadata(
            class_id,
            "2026-2027",
            created_at=datetime(2026, 8, 30, tzinfo=timezone.utc),
        ),
    )
    write_class_roster(
        workspace,
        create_roster(
            class_id,
            tuple(
                {
                    "student_id": f"student-{index}",
                    "last_name": f"Synthetic{index}",
                    "first_name": f"Learner{index}",
                    "period": "1",
                }
                for index in range(1, 5)
            ),
        ),
    )

    cases: list[dict[str, object]] = []
    all_print_hashes: set[str] = set()
    all_artifact_ids: set[str] = set()
    all_page_ids: set[str] = set()
    all_route_ids: set[str] = set()

    def add_case(
        *,
        workflow: str,
        case_id: str,
        activity_id: str,
        session_id: str,
        target_kind: str,
        target_id: str,
        group_id: str,
        packet_instance: Any,
        private_tokens: tuple[str, ...] = (),
    ) -> None:
        work = ModuleWorkRef("concord", class_id, activity_id)
        graph = load_current_record_graph(workspace, work).graph
        if len(packet_instance.artifact_bindings) != 1:
            raise RuntimeError(f"{case_id} must bind exactly one Artifact")
        artifact_id = packet_instance.artifact_bindings[0].artifact_instance_id
        artifact = next(
            item
            for item in graph.artifact_instances
            if item.artifact_instance_id == artifact_id
        )
        rendered = render_packet_instance(
            RenderPacketInstanceRequest(
                class_id=class_id,
                activity_id=activity_id,
                packet_instance_id=packet_instance.packet_instance_id,
                actor=actor,
            ),
            workspace_root=workspace,
        )
        if rendered.page_count != len(artifact.page_ids):
            raise RuntimeError(f"{case_id} rendered unexpected page count")
        route_ids: list[str] = []
        for payload in rendered.payloads:
            locator = parse_pds2_payload(payload)
            if (
                locator.module_id != "concord"
                or locator.class_id != class_id
                or locator.work_id != activity_id
            ):
                raise RuntimeError(f"{case_id} rendered an unexpected PDS2 locator")
            route_ids.append(locator.route_id)
        if len(route_ids) != len(artifact.page_ids):
            raise RuntimeError(f"{case_id} PDS2/page cardinality does not match")
        data = rendered.output_path.read_bytes()
        for token in private_tokens:
            if token.encode("utf-8") in data:
                raise RuntimeError(f"{case_id} leaked planning provenance into PDF")
            if any(token in payload for payload in rendered.payloads):
                raise RuntimeError(f"{case_id} leaked planning provenance into PDS2")
        filename = f"PRINT-{case_id}.pdf"
        print_path = print_root / filename
        installed_shutil.copy2(rendered.output_path, print_path)
        print_hash = _sha256(print_path)
        if print_hash in all_print_hashes:
            raise RuntimeError("physical sample unexpectedly reused printable bytes")
        if artifact_id in all_artifact_ids:
            raise RuntimeError("physical sample unexpectedly reused Artifact identity")
        if any(page_id in all_page_ids for page_id in artifact.page_ids):
            raise RuntimeError(
                "physical sample unexpectedly reused ArtifactPage identity"
            )
        if any(route_id in all_route_ids for route_id in route_ids):
            raise RuntimeError("physical sample unexpectedly reused route identity")
        all_print_hashes.add(print_hash)
        all_artifact_ids.add(artifact_id)
        all_page_ids.update(artifact.page_ids)
        all_route_ids.update(route_ids)
        cases.append(
            {
                "case_id": case_id,
                "workflow": workflow,
                "activity_id": activity_id,
                "session_id": session_id,
                "target_kind": target_kind,
                "target_id": target_id,
                "group_id": group_id,
                "packet_instance_id": packet_instance.packet_instance_id,
                "artifact_instance_id": artifact_id,
                "artifact_page_ids": list(artifact.page_ids),
                "route_ids": sorted(route_ids),
                "page_count": rendered.page_count,
                "print_pdf_relative_path": f"{PRINT_DIR}/{filename}",
                "print_pdf_sha256": print_hash,
            }
        )

    # Seminar: manual signal-free planning; select one participant from each Group.
    seminar_activity_id = "activity-seminar-issue70-physical"
    seminar_session_id = "session-seminar-issue70-physical"
    seminar_created = create_activity_context(
        CreateActivityContextRequest(
            class_id=class_id,
            activity_id=seminar_activity_id,
            title="Issue 70 Physical Seminar",
            activity_type="socratic_seminar",
            scoring_orientation="local_criteria_only",
            session_id=seminar_session_id,
            actor=actor,
            activity_status="active",
            session_status="active",
            session_label="Physical Seminar Session",
        ),
        workspace_root=workspace,
    )
    seminar_context = EffectiveContext(
        activity_id=seminar_activity_id,
        session_ids=(seminar_session_id,),
    )
    seminar_plan = create_manual_group_plan(
        CreateManualGroupPlanRequest(
            class_id=class_id,
            activity_id=seminar_activity_id,
            group_plan_id="plan-seminar-issue70-physical",
            expected_snapshot_revision=seminar_created.commit.snapshot_revision,
            actor=actor,
            proposed_groups=(
                PlannedGroup(
                    planned_group_key="seminar-a",
                    label="Physical Seminar A",
                    student_ids=("student-1", "student-2"),
                    effective_context=seminar_context,
                ),
                PlannedGroup(
                    planned_group_key="seminar-b",
                    label="Physical Seminar B",
                    student_ids=("student-3", "student-4"),
                    effective_context=seminar_context,
                ),
            ),
            target_group_count=2,
        ),
        workspace_root=workspace,
    )
    seminar_preview = preview_group_plan(
        PreviewGroupPlanRequest(
            class_id=class_id,
            activity_id=seminar_activity_id,
            group_plan_id=seminar_plan.group_plan_id,
            expected_snapshot_revision=seminar_plan.commit.snapshot_revision,
            actor=actor,
        ),
        workspace_root=workspace,
    )
    seminar_approved = approve_group_plan(
        ApproveGroupPlanRequest(
            class_id=class_id,
            activity_id=seminar_activity_id,
            group_plan_id=seminar_plan.group_plan_id,
            expected_snapshot_revision=seminar_preview.summary.snapshot_revision,
            actor=actor,
        ),
        workspace_root=workspace,
    )
    if seminar_approved.status != "approved":
        raise RuntimeError("physical seminar GroupPlan approval failed")
    seminar_application = prepare_group_plan_application(
        PrepareGroupPlanApplicationRequest(
            class_id=class_id,
            activity_id=seminar_activity_id,
            group_plan_id=seminar_plan.group_plan_id,
            application_id="apply-seminar-issue70-physical",
            fallback_effective_context=seminar_context,
        ),
        workspace_root=workspace,
    )
    seminar_applied = apply_group_plan(
        ApplyGroupPlanRequest(
            class_id=class_id,
            activity_id=seminar_activity_id,
            group_plan_id=seminar_plan.group_plan_id,
            application_id=seminar_application.application_id,
            application_digest=seminar_application.application_digest,
            expected_snapshot_revision=seminar_application.expected_snapshot_revision,
            actor=actor,
            fallback_effective_context=seminar_context,
        ),
        workspace_root=workspace,
    )
    if seminar_applied.group_count != 2 or seminar_applied.membership_count != 4:
        raise RuntimeError("physical seminar GroupPlan application failed")
    seminar_starter = get_starter_template("socratic_seminar")
    commit_starter_template_install(
        prepare_starter_template_install(
            PrepareStarterTemplateInstallRequest(
                starter_key=seminar_starter.starter_key,
                actor=actor,
            ),
            workspace_root=workspace,
        ),
        workspace_root=workspace,
    )
    commit_packet_from_template(
        prepare_packet_from_template(
            PreparePacketFromTemplateRequest(
                packet_definition_id="packet-seminar-issue70-physical",
                packet_version_id="packet-seminar-issue70-physical-v1",
                packet_component_id="component-seminar-issue70-physical",
                name="Issue 70 Physical Seminar Packet",
                purpose="Owner-only physical acceptance.",
                template_id=seminar_starter.template_id,
                template_version_id=seminar_starter.template_version_id,
                audience_kind="participant",
                actor=actor,
            ),
            workspace_root=workspace,
        ),
        workspace_root=workspace,
    )
    seminar_generation = prepare_packet_instantiation(
        PreparePacketInstantiationRequest(
            class_id=class_id,
            activity_id=seminar_activity_id,
            session_id=seminar_session_id,
            packet_definition_id="packet-seminar-issue70-physical",
            packet_version_id="packet-seminar-issue70-physical-v1",
            actor=actor,
        ),
        workspace_root=workspace,
    )
    commit_packet_instantiation(
        seminar_generation,
        workspace_root=workspace,
        generation_id="generation-seminar-issue70-physical",
    )
    seminar_graph = load_current_record_graph(
        workspace,
        ModuleWorkRef("concord", class_id, seminar_activity_id),
    ).graph
    seminar_packets = {
        item.target_context.participant_reference.participant_id: item
        for item in seminar_graph.packet_instances
        if item.generation_id == "generation-seminar-issue70-physical"
        and item.target_context.participant_reference is not None
    }
    for student_id in ("student-1", "student-3"):
        packet = seminar_packets[student_id]
        group_id = packet.target_context.group_id
        if group_id is None or group_id not in seminar_applied.group_ids:
            raise RuntimeError("physical seminar sample lost canonical Group context")
        add_case(
            workflow="seminar",
            case_id=f"seminar-{student_id}",
            activity_id=seminar_activity_id,
            session_id=seminar_session_id,
            target_kind="core_student",
            target_id=student_id,
            group_id=group_id,
            packet_instance=packet,
        )

    # Group project: complete synthetic signal-backed planning; print both
    # canonical Group packets.
    project_activity_id = "activity-project-issue70-physical"
    project_session_id = "session-project-issue70-physical"
    project_created = create_activity_context(
        CreateActivityContextRequest(
            class_id=class_id,
            activity_id=project_activity_id,
            title="Issue 70 Physical Group Project",
            activity_type="project",
            scoring_orientation="local_criteria_only",
            session_id=project_session_id,
            actor=actor,
            activity_status="active",
            session_status="active",
            session_label="Physical Project Session",
        ),
        workspace_root=workspace,
    )
    project_context = EffectiveContext(
        activity_id=project_activity_id,
        session_ids=(project_session_id,),
    )
    private_signal_set_id = "issue70-physical-private-signal-set"
    private_dimension_id = "issue70-physical-private-band"
    private_source_module = "issue70_physical_private_producer"
    private_snapshot_id = "issue70-physical-private-snapshot"
    private_snapshot_digest = "7" * 64
    signal = GroupingSignalSet(
        schema_version="1",
        record_type="grouping_signal_set",
        signal_set_id=private_signal_set_id,
        class_id=class_id,
        created_at=datetime(2026, 8, 30, 12, 0, tzinfo=timezone.utc),
        source=GroupingSignalSource(
            kind="module_generated",
            module_id=private_source_module,
            snapshot_id=private_snapshot_id,
            snapshot_digest_algorithm="sha256",
            snapshot_digest=private_snapshot_digest,
        ),
        dimensions=(
            GroupingSignalDimension(
                dimension_id=private_dimension_id,
                band_count=4,
            ),
        ),
        student_bands=(
            GroupingSignalStudentBand(
                student_id="student-1",
                dimension_id=private_dimension_id,
                band=1,
            ),
            GroupingSignalStudentBand(
                student_id="student-2",
                dimension_id=private_dimension_id,
                band=1,
            ),
            GroupingSignalStudentBand(
                student_id="student-3",
                dimension_id=private_dimension_id,
                band=4,
            ),
            GroupingSignalStudentBand(
                student_id="student-4",
                dimension_id=private_dimension_id,
                band=4,
            ),
        ),
    )
    write_grouping_signal(workspace, signal)
    private_canonical_digest = calculate_grouping_signal_digest(signal)
    private_tokens = (
        private_signal_set_id,
        private_dimension_id,
        private_source_module,
        private_snapshot_id,
        private_snapshot_digest,
        private_canonical_digest,
    )
    project_plan = create_signal_group_plan(
        CreateSignalGroupPlanRequest(
            class_id=class_id,
            activity_id=project_activity_id,
            group_plan_id="plan-project-issue70-physical",
            strategy="similar_signal",
            signal_set_id=private_signal_set_id,
            dimension_id=private_dimension_id,
            expected_snapshot_revision=project_created.commit.snapshot_revision,
            actor=actor,
            target_group_count=2,
            expected_roster_student_ids=(
                "student-1",
                "student-2",
                "student-3",
                "student-4",
            ),
            expected_signal_set_digest=private_canonical_digest,
        ),
        workspace_root=workspace,
    )
    project_preview = preview_group_plan(
        PreviewGroupPlanRequest(
            class_id=class_id,
            activity_id=project_activity_id,
            group_plan_id=project_plan.mutation.group_plan_id,
            expected_snapshot_revision=project_plan.mutation.commit.snapshot_revision,
            actor=actor,
        ),
        workspace_root=workspace,
    )
    project_approved = approve_group_plan(
        ApproveGroupPlanRequest(
            class_id=class_id,
            activity_id=project_activity_id,
            group_plan_id=project_plan.mutation.group_plan_id,
            expected_snapshot_revision=project_preview.summary.snapshot_revision,
            actor=actor,
        ),
        workspace_root=workspace,
    )
    if project_approved.status != "approved":
        raise RuntimeError("physical project GroupPlan approval failed")
    project_application = prepare_group_plan_application(
        PrepareGroupPlanApplicationRequest(
            class_id=class_id,
            activity_id=project_activity_id,
            group_plan_id=project_plan.mutation.group_plan_id,
            application_id="apply-project-issue70-physical",
            fallback_effective_context=project_context,
        ),
        workspace_root=workspace,
    )
    project_applied = apply_group_plan(
        ApplyGroupPlanRequest(
            class_id=class_id,
            activity_id=project_activity_id,
            group_plan_id=project_plan.mutation.group_plan_id,
            application_id=project_application.application_id,
            application_digest=project_application.application_digest,
            expected_snapshot_revision=project_application.expected_snapshot_revision,
            actor=actor,
            fallback_effective_context=project_context,
        ),
        workspace_root=workspace,
    )
    if project_applied.group_count != 2 or project_applied.membership_count != 4:
        raise RuntimeError("physical project GroupPlan application failed")
    project_starter = get_starter_template("project_plan")
    commit_starter_template_install(
        prepare_starter_template_install(
            PrepareStarterTemplateInstallRequest(
                starter_key=project_starter.starter_key,
                actor=actor,
            ),
            workspace_root=workspace,
        ),
        workspace_root=workspace,
    )
    commit_packet_from_template(
        prepare_packet_from_template(
            PreparePacketFromTemplateRequest(
                packet_definition_id="packet-project-issue70-physical",
                packet_version_id="packet-project-issue70-physical-v1",
                packet_component_id="component-project-issue70-physical",
                name="Issue 70 Physical Project Packet",
                purpose="Owner-only physical acceptance.",
                template_id=project_starter.template_id,
                template_version_id=project_starter.template_version_id,
                audience_kind="group",
                actor=actor,
            ),
            workspace_root=workspace,
        ),
        workspace_root=workspace,
    )
    project_generation = prepare_packet_instantiation(
        PreparePacketInstantiationRequest(
            class_id=class_id,
            activity_id=project_activity_id,
            session_id=project_session_id,
            packet_definition_id="packet-project-issue70-physical",
            packet_version_id="packet-project-issue70-physical-v1",
            actor=actor,
        ),
        workspace_root=workspace,
    )
    commit_packet_instantiation(
        project_generation,
        workspace_root=workspace,
        generation_id="generation-project-issue70-physical",
    )
    project_graph = load_current_record_graph(
        workspace,
        ModuleWorkRef("concord", class_id, project_activity_id),
    ).graph
    project_packets = tuple(
        item
        for item in project_graph.packet_instances
        if item.generation_id == "generation-project-issue70-physical"
    )
    if len(project_packets) != 2:
        raise RuntimeError("physical project sample must contain both Group packets")
    for index, packet in enumerate(
        sorted(project_packets, key=lambda item: item.target_context.group_id or ""),
        start=1,
    ):
        group_id = packet.target_context.group_id
        if group_id is None or group_id not in project_applied.group_ids:
            raise RuntimeError("physical project packet lost canonical Group context")
        add_case(
            workflow="project",
            case_id=f"project-group-{index}",
            activity_id=project_activity_id,
            session_id=project_session_id,
            target_kind="concord_group",
            target_id=group_id,
            group_id=group_id,
            packet_instance=packet,
            private_tokens=private_tokens,
        )

    # Peer review: deterministic random signal-free planning; one participant per Group.
    peer_activity_id = "activity-peer-review-issue70-physical"
    peer_session_id = "session-peer-review-issue70-physical"
    peer_created = create_activity_context(
        CreateActivityContextRequest(
            class_id=class_id,
            activity_id=peer_activity_id,
            title="Issue 70 Physical Peer Review",
            activity_type="project",
            scoring_orientation="local_criteria_only",
            session_id=peer_session_id,
            actor=actor,
            activity_status="active",
            session_status="active",
            session_label="Physical Peer Review Session",
        ),
        workspace_root=workspace,
    )
    peer_context = EffectiveContext(
        activity_id=peer_activity_id,
        session_ids=(peer_session_id,),
    )
    peer_plan = create_random_group_plan(
        CreateRandomGroupPlanRequest(
            class_id=class_id,
            activity_id=peer_activity_id,
            group_plan_id="plan-peer-review-issue70-physical",
            expected_snapshot_revision=peer_created.commit.snapshot_revision,
            actor=actor,
            seed="issue70-physical-peer-review-seed",
            target_group_count=2,
        ),
        workspace_root=workspace,
    )
    peer_preview = preview_group_plan(
        PreviewGroupPlanRequest(
            class_id=class_id,
            activity_id=peer_activity_id,
            group_plan_id=peer_plan.mutation.group_plan_id,
            expected_snapshot_revision=peer_plan.mutation.commit.snapshot_revision,
            actor=actor,
        ),
        workspace_root=workspace,
    )
    peer_approved = approve_group_plan(
        ApproveGroupPlanRequest(
            class_id=class_id,
            activity_id=peer_activity_id,
            group_plan_id=peer_plan.mutation.group_plan_id,
            expected_snapshot_revision=peer_preview.summary.snapshot_revision,
            actor=actor,
        ),
        workspace_root=workspace,
    )
    if peer_approved.status != "approved":
        raise RuntimeError("physical peer-review GroupPlan approval failed")
    peer_application = prepare_group_plan_application(
        PrepareGroupPlanApplicationRequest(
            class_id=class_id,
            activity_id=peer_activity_id,
            group_plan_id=peer_plan.mutation.group_plan_id,
            application_id="apply-peer-review-issue70-physical",
            fallback_effective_context=peer_context,
        ),
        workspace_root=workspace,
    )
    peer_applied = apply_group_plan(
        ApplyGroupPlanRequest(
            class_id=class_id,
            activity_id=peer_activity_id,
            group_plan_id=peer_plan.mutation.group_plan_id,
            application_id=peer_application.application_id,
            application_digest=peer_application.application_digest,
            expected_snapshot_revision=peer_application.expected_snapshot_revision,
            actor=actor,
            fallback_effective_context=peer_context,
        ),
        workspace_root=workspace,
    )
    if peer_applied.group_count != 2 or peer_applied.membership_count != 4:
        raise RuntimeError("physical peer-review GroupPlan application failed")
    peer_starter = get_starter_template("peer_review_writing")
    commit_starter_template_install(
        prepare_starter_template_install(
            PrepareStarterTemplateInstallRequest(
                starter_key=peer_starter.starter_key,
                actor=actor,
            ),
            workspace_root=workspace,
        ),
        workspace_root=workspace,
    )
    commit_packet_from_template(
        prepare_packet_from_template(
            PreparePacketFromTemplateRequest(
                packet_definition_id="packet-peer-review-issue70-physical",
                packet_version_id="packet-peer-review-issue70-physical-v1",
                packet_component_id="component-peer-review-issue70-physical",
                name="Issue 70 Physical Peer Review Packet",
                purpose="Owner-only physical acceptance.",
                template_id=peer_starter.template_id,
                template_version_id=peer_starter.template_version_id,
                audience_kind="participant",
                actor=actor,
            ),
            workspace_root=workspace,
        ),
        workspace_root=workspace,
    )
    peer_generation = prepare_packet_instantiation(
        PreparePacketInstantiationRequest(
            class_id=class_id,
            activity_id=peer_activity_id,
            session_id=peer_session_id,
            packet_definition_id="packet-peer-review-issue70-physical",
            packet_version_id="packet-peer-review-issue70-physical-v1",
            actor=actor,
        ),
        workspace_root=workspace,
    )
    commit_packet_instantiation(
        peer_generation,
        workspace_root=workspace,
        generation_id="generation-peer-review-issue70-physical",
    )
    peer_graph = load_current_record_graph(
        workspace,
        ModuleWorkRef("concord", class_id, peer_activity_id),
    ).graph
    peer_packets = tuple(
        item
        for item in peer_graph.packet_instances
        if item.generation_id == "generation-peer-review-issue70-physical"
        and item.target_context.participant_reference is not None
    )
    packet_by_group: dict[str, Any] = {}
    for packet in sorted(
        peer_packets,
        key=lambda item: item.target_context.participant_reference.participant_id,
    ):
        group_id = packet.target_context.group_id
        if group_id is None or group_id not in peer_applied.group_ids:
            raise RuntimeError(
                "physical peer-review packet lost canonical Group context"
            )
        packet_by_group.setdefault(group_id, packet)
    if set(packet_by_group) != set(peer_applied.group_ids):
        raise RuntimeError("physical peer-review sample does not span both Groups")
    for index, (group_id, packet) in enumerate(
        sorted(packet_by_group.items()), start=1
    ):
        participant = packet.target_context.participant_reference
        if participant is None:
            raise RuntimeError("physical peer-review sample lost participant identity")
        add_case(
            workflow="peer_review",
            case_id=f"peer-group-{index}-{participant.participant_id}",
            activity_id=peer_activity_id,
            session_id=peer_session_id,
            target_kind="core_student",
            target_id=participant.participant_id,
            group_id=group_id,
            packet_instance=packet,
        )

    if len(cases) != 6:
        raise RuntimeError("issue #70 physical sample must contain exactly six packets")
    workflow_counts = {
        workflow: sum(case["workflow"] == workflow for case in cases)
        for workflow in ("seminar", "project", "peer_review")
    }
    if workflow_counts != {"seminar": 2, "project": 2, "peer_review": 2}:
        raise RuntimeError("issue #70 physical sample workflow cardinality is wrong")
    state: dict[str, object] = {
        "schema_version": 2,
        "status": "prepared_for_physical_return",
        "workspace_relative_path": "workspace",
        "class_id": class_id,
        "cases": cases,
        "workflow_counts": workflow_counts,
        "private_project_tokens": list(private_tokens),
        "installed_concord_version": metadata.version("pds-concord"),
        "installed_core_version": metadata.version("pds-core"),
        "installed_concord_origin": installed["concord_origin"],
        "installed_core_origin": installed["core_origin"],
        "concord_wheel_sha256": outer["concord_wheel_sha256"],
        "core_wheel_sha256": outer["core_wheel_sha256"],
    }
    _write_json(run_root / STATE_FILE, state)
    print("PREPARED issue #70 physical sample")
    for case in cases:
        print(
            f"{case['case_id']}: {run_root / str(case['print_pdf_relative_path'])}"
        )
    print("expected_packets=6")
    print(
        "expected_pages="
        + str(sum(_json_int(case, "page_count") for case in cases))
    )
    return 0


def _installed_resume(args: argparse.Namespace) -> int:
    import platform
    from datetime import datetime
    from importlib import metadata

    from pds_core.routing_models import ModuleWorkRef

    from concord.academic_result_manifest_generation import (
        GenerateAcademicResultManifestRequest,
        generate_academic_result_manifest,
    )
    from concord.academic_result_publication import publish_concord_academic_results
    from concord.academic_result_reader import (
        lookup_academic_result_score,
        read_academic_result_manifest,
    )
    from concord.academic_work_registration import register_concord_academic_work
    from concord.models import (
        EvidenceReference,
        PrivacyPolicy,
        ScoreTargetReference,
        ScoringScaleLevel,
        SubjectReference,
    )
    from concord.routing.scan_intake import (
        SUPPORTED_SCAN_EXTENSIONS,
        route_scan_sources,
    )
    from concord.storage import load_current_record_graph
    from concord.workflows import (
        AddArtifactReviewRequest,
        AddScoreRequest,
        AssembleArtifactRequest,
        ConcordRouteDispatchResult,
        CreateCriterionSetRequest,
        CreateScoringScaleRequest,
        CriterionSpec,
        ScoreEvidenceLinkSpec,
        SelectActivityCriterionSetsRequest,
        add_artifact_review,
        add_score,
        assemble_returned_artifact,
        create_criterion_set,
        create_scoring_scale,
        select_activity_criterion_sets,
    )

    run_root = Path(args.run_root).resolve()
    installed = _installed_modules()
    outer = _load_json(run_root / RUN_METADATA)
    state = _load_json(run_root / STATE_FILE)
    if state.get("status") != "prepared_for_physical_return":
        raise RuntimeError("physical acceptance state is not ready for resume")
    if not args.physical_mark_confirmed:
        raise RuntimeError(
            "resume requires --physical-mark-confirmed after handwriting PDS70 "
            "on representative paper from every starter family"
        )
    if not args.visual_inspection_confirmed:
        raise RuntimeError(
            "resume requires --visual-inspection-confirmed after inspecting at least "
            "one printed sample from seminar, project, and peer-review families"
        )
    workspace_relative = state.get("workspace_relative_path")
    if not isinstance(workspace_relative, str):
        raise RuntimeError("physical state is missing workspace path")
    workspace = run_root / workspace_relative
    os.environ["PDS_WORKSPACE_ROOT"] = str(workspace)
    class_id = _json_string(state, "class_id")
    cases = _json_cases(state)
    private_tokens = _json_strings(state, "private_project_tokens")
    scans = tuple(Path(value).resolve() for value in args.scan)
    if not scans:
        raise RuntimeError("at least one scan path is required")

    print_hashes = {
        _json_string(case, "print_pdf_sha256")
        for case in cases
    }
    scan_digests: dict[str, str] = {}
    for scan in scans:
        if scan.suffix.lower() not in SUPPORTED_SCAN_EXTENSIONS:
            raise RuntimeError(f"unsupported physical scan extension: {scan.suffix}")
        digest = _sha256(scan)
        if digest in print_hashes:
            raise RuntimeError(
                "physical scan bytes exactly equal generated printable bytes; an "
                "untouched generated PDF is not physical acceptance evidence"
            )
        scan_digests[scan.name] = digest

    route_to_case: dict[str, dict[str, object]] = {}
    expected_pages_by_case: dict[str, set[str]] = {}
    expected_routes_by_case: dict[str, set[str]] = {}
    total_expected_pages = 0
    for case in cases:
        case_id = _json_string(case, "case_id")
        artifact_id = _json_string(case, "artifact_instance_id")
        page_ids = set(_json_strings(case, "artifact_page_ids"))
        route_ids = set(_json_strings(case, "route_ids"))
        if len(page_ids) != len(route_ids) or len(page_ids) != _json_int(
            case, "page_count"
        ):
            raise RuntimeError(
                f"{case_id} persisted physical identity count is invalid"
            )
        expected_pages_by_case[case_id] = page_ids
        expected_routes_by_case[case_id] = route_ids
        total_expected_pages += len(page_ids)
        for route_id in route_ids:
            if route_id in route_to_case:
                raise RuntimeError("physical state contains duplicate route identity")
            route_to_case[route_id] = case

    actor = _actor()
    for activity_id in sorted({_json_string(case, "activity_id") for case in cases}):
        work = ModuleWorkRef("concord", class_id, activity_id)
        before = load_current_record_graph(workspace, work).graph
        if before.artifact_reviews or before.score_records:
            raise RuntimeError("physical resume requires pre-Review, pre-Score state")

    returned = route_scan_sources(scans, workspace_root=workspace)
    if returned.failure_count != 0 or returned.dispatched_count != total_expected_pages:
        raise RuntimeError(
            "physical scan did not dispatch every required sample page without failures"
        )
    observed_pages_by_case: dict[str, set[str]] = {
        case_id: set() for case_id in expected_pages_by_case
    }
    observed_routes_by_case: dict[str, set[str]] = {
        case_id: set() for case_id in expected_routes_by_case
    }
    retained_source_ids: set[str] = set()
    physical_source_page_count = 0
    for source in returned.sources:
        if source.source_error is not None or source.retained_source is None:
            raise RuntimeError("physical scan source was not retained successfully")
        retained_source_ids.add(source.retained_source.source_scan_id)
        physical_source_page_count += len(source.pages)
        for page in source.pages:
            if page.status != "dispatched" or page.locator is None:
                raise RuntimeError("physical scan page did not dispatch")
            matched_case = route_to_case.get(page.locator.route_id)
            if matched_case is None:
                raise RuntimeError("physical scan resolved an unexpected route")
            case_id = _json_string(matched_case, "case_id")
            activity_id = _json_string(matched_case, "activity_id")
            artifact_id = _json_string(matched_case, "artifact_instance_id")
            if (
                page.locator.module_id != "concord"
                or page.locator.class_id != class_id
                or page.locator.work_id != activity_id
            ):
                raise RuntimeError(f"{case_id} physical route escaped expected work")
            dispatch = page.module_result
            if not isinstance(dispatch, ConcordRouteDispatchResult):
                raise RuntimeError("physical scan returned an unexpected owner result")
            if dispatch.artifact_instance_id != artifact_id:
                raise RuntimeError(f"{case_id} physical route reached wrong Artifact")
            observed_routes_by_case[case_id].add(page.locator.route_id)
            observed_pages_by_case[case_id].add(dispatch.artifact_page_id)

    for case in cases:
        case_id = _json_string(case, "case_id")
        if observed_routes_by_case[case_id] != expected_routes_by_case[case_id]:
            raise RuntimeError(f"{case_id} physical route set is incomplete")
        if observed_pages_by_case[case_id] != expected_pages_by_case[case_id]:
            raise RuntimeError(f"{case_id} physical ArtifactPage set is incomplete")

    # Scan intake must not infer teacher judgment.
    for activity_id in sorted({_json_string(case, "activity_id") for case in cases}):
        work = ModuleWorkRef("concord", class_id, activity_id)
        graph = load_current_record_graph(workspace, work).graph
        if graph.artifact_reviews:
            raise RuntimeError("scan intake inferred Artifact Review state")
        if graph.score_records:
            raise RuntimeError("scan intake inferred Score state")

    # Assemble and explicitly review each physically returned Artifact.
    for index, case in enumerate(cases, start=1):
        case_id = _json_string(case, "case_id")
        activity_id = _json_string(case, "activity_id")
        artifact_id = _json_string(case, "artifact_instance_id")
        assembled = assemble_returned_artifact(
            AssembleArtifactRequest(
                class_id=class_id,
                activity_id=activity_id,
                artifact_instance_id=artifact_id,
                expected_snapshot_revision=_current_revision(
                    workspace, class_id, activity_id
                ),
                actor=actor,
            ),
            workspace_root=workspace,
        )
        if assembled.page_count != _json_int(case, "page_count"):
            raise RuntimeError(f"{case_id} physical Artifact assembly is incomplete")
        workflow = _json_string(case, "workflow")
        privacy_classification: Any = (
            "group_and_teacher" if workflow == "project" else "teacher_and_subjects"
        )
        privacy = PrivacyPolicy(classification=privacy_classification)
        review = add_artifact_review(
            AddArtifactReviewRequest(
                class_id=class_id,
                activity_id=activity_id,
                artifact_instance_id=artifact_id,
                artifact_review_id=f"review-issue70-physical-{index}",
                readability_judgment="readable",
                page_completeness_judgment="complete",
                filing_judgment="correct",
                author_judgment="confirmed",
                subject_judgment="confirmed",
                privacy_judgment=privacy_classification,
                relevance_judgment="relevant",
                moderation_requirement="not_required",
                scoring_readiness="ready",
                review_outcome="ready",
                privacy_policy=privacy,
                expected_snapshot_revision=_current_revision(
                    workspace, class_id, activity_id
                ),
                actor=actor,
                notes="Owner-only physical issue #70 synthetic acceptance.",
            ),
            workspace_root=workspace,
        )
        if review.artifact_review_id != f"review-issue70-physical-{index}":
            raise RuntimeError(f"{case_id} physical Review did not persist")

    workflow_specs: dict[str, dict[str, str]] = {
        "seminar": {
            "scale_id": "scale-seminar-issue70-physical",
            "scale_lineage": "scale-seminar-issue70-physical-lineage",
            "criterion_set_id": "criteria-seminar-issue70-physical",
            "criterion_lineage": "criteria-seminar-issue70-physical-lineage",
            "criterion_id": "criterion-seminar-issue70-physical",
            "criterion_key": "seminar-participation",
            "criterion_label": "Seminar participation",
            "target_kind": "core_student",
            "privacy": "teacher_and_subjects",
        },
        "project": {
            "scale_id": "scale-project-issue70-physical",
            "scale_lineage": "scale-project-issue70-physical-lineage",
            "criterion_set_id": "criteria-project-issue70-physical",
            "criterion_lineage": "criteria-project-issue70-physical-lineage",
            "criterion_id": "criterion-project-issue70-physical",
            "criterion_key": "project-collaboration",
            "criterion_label": "Project collaboration",
            "target_kind": "concord_group",
            "privacy": "group_and_teacher",
        },
        "peer_review": {
            "scale_id": "scale-peer-review-issue70-physical",
            "scale_lineage": "scale-peer-review-issue70-physical-lineage",
            "criterion_set_id": "criteria-peer-review-issue70-physical",
            "criterion_lineage": "criteria-peer-review-issue70-physical-lineage",
            "criterion_id": "criterion-peer-review-issue70-physical",
            "criterion_key": "peer-review-quality",
            "criterion_label": "Peer-review quality",
            "target_kind": "core_student",
            "privacy": "teacher_and_subjects",
        },
    }

    score_ids_by_workflow: dict[str, list[str]] = {
        "seminar": [],
        "project": [],
        "peer_review": [],
    }
    for workflow, spec in workflow_specs.items():
        workflow_cases = tuple(
            case for case in cases if _json_string(case, "workflow") == workflow
        )
        if len(workflow_cases) != 2:
            raise RuntimeError(f"{workflow} physical sample must contain two packets")
        activity_id = _json_string(workflow_cases[0], "activity_id")
        scale = create_scoring_scale(
            CreateScoringScaleRequest(
                class_id=class_id,
                activity_id=activity_id,
                scoring_scale_id=spec["scale_id"],
                lineage_id=spec["scale_lineage"],
                name=f"Issue 70 Physical {workflow} Scale",
                revision=1,
                scale_type="categorical",
                levels=(
                    ScoringScaleLevel(
                        value="developing",
                        label="Developing",
                        meaning="Synthetic developing level.",
                    ),
                    ScoringScaleLevel(
                        value="meets",
                        label="Meets",
                        meaning="Synthetic meets level.",
                    ),
                ),
                status="active",
                expected_snapshot_revision=_current_revision(
                    workspace, class_id, activity_id
                ),
                actor=actor,
                intended_use="Owner-only issue #70 physical acceptance.",
            ),
            workspace_root=workspace,
        )
        criteria = create_criterion_set(
            CreateCriterionSetRequest(
                class_id=class_id,
                activity_id=activity_id,
                criterion_set_id=spec["criterion_set_id"],
                lineage_id=spec["criterion_lineage"],
                name=f"Issue 70 Physical {workflow} Criteria",
                purpose="Owner-only issue #70 physical acceptance.",
                revision=1,
                scope="activity_specific",
                criterion_set_kind="local",
                criteria=(
                    CriterionSpec(
                        criterion_id=spec["criterion_id"],
                        key=spec["criterion_key"],
                        label=spec["criterion_label"],
                        definition="Synthetic physical acceptance criterion.",
                        criterion_kind="local",
                        supported_target_kinds=(cast(Any, spec["target_kind"]),),
                        default_scoring_scale_id=spec["scale_id"],
                    ),
                ),
                status="active",
                expected_snapshot_revision=scale.commit.snapshot_revision,
                actor=actor,
            ),
            workspace_root=workspace,
        )
        selected = select_activity_criterion_sets(
            SelectActivityCriterionSetsRequest(
                class_id=class_id,
                activity_id=activity_id,
                criterion_set_ids=(spec["criterion_set_id"],),
                expected_snapshot_revision=criteria.commit.snapshot_revision,
                actor=actor,
            ),
            workspace_root=workspace,
        )
        if selected.criterion_set_ids != (spec["criterion_set_id"],):
            raise RuntimeError(f"{workflow} physical Criterion Set was not selected")
        privacy_value: Any = spec["privacy"]
        target_kind: Any = spec["target_kind"]
        privacy = PrivacyPolicy(classification=privacy_value)
        for index, case in enumerate(workflow_cases, start=1):
            target_id = _json_string(case, "target_id")
            artifact_id = _json_string(case, "artifact_instance_id")
            session_id = _json_string(case, "session_id")
            if spec["target_kind"] == "concord_group":
                subject = SubjectReference(
                    subject_kind="concord_group",
                    subject_id=target_id,
                    owning_system="concord",
                )
                owning_system: Any = "concord"
            else:
                subject = SubjectReference(
                    subject_kind="core_student",
                    subject_id=target_id,
                    owning_system="core",
                )
                owning_system = "core"
            evidence = EvidenceReference(
                evidence_kind="artifact_instance",
                owning_system="concord",
                record_id=artifact_id,
                subject_context=(subject,),
                moderation_requirement="not_required",
            )
            score_id = f"score-{workflow}-issue70-physical-{index}"
            score = add_score(
                AddScoreRequest(
                    class_id=class_id,
                    activity_id=activity_id,
                    score_record_id=score_id,
                    target_reference=ScoreTargetReference(
                        target_kind=target_kind,
                        target_id=target_id,
                        owning_system=owning_system,
                    ),
                    criterion_id=spec["criterion_id"],
                    scoring_scale_id=spec["scale_id"],
                    disposition="scored",
                    basis="linked_evidence",
                    privacy_policy=privacy,
                    expected_snapshot_revision=_current_revision(
                        workspace, class_id, activity_id
                    ),
                    actor=actor,
                    session_id=session_id,
                    value="meets",
                    evidence_links=(
                        ScoreEvidenceLinkSpec(
                            score_evidence_link_id=(
                                f"link-{workflow}-issue70-physical-{index}"
                            ),
                            evidence_reference=evidence,
                            relevance_description=(
                                "Synthetic physically returned issue #70 Artifact."
                            ),
                            subject_context=(subject,),
                        ),
                    ),
                ),
                workspace_root=workspace,
            )
            if score.score_record_id != score_id:
                raise RuntimeError(f"{workflow} physical Score did not persist")
            score_ids_by_workflow[workflow].append(score_id)

    publication_summaries: dict[str, dict[str, object]] = {}
    for workflow, workflow_cases in (
        (
            name,
            tuple(case for case in cases if _json_string(case, "workflow") == name),
        )
        for name in ("seminar", "project", "peer_review")
    ):
        activity_id = _json_string(workflow_cases[0], "activity_id")
        work = ModuleWorkRef("concord", class_id, activity_id)
        registration = register_concord_academic_work(
            workspace,
            class_id,
            activity_id,
            academic_intent="formative",
            lifecycle="active",
        )
        if registration.registration.registration_revision != 1:
            raise RuntimeError(f"{workflow} Academic Work registration failed")
        manifest_request = GenerateAcademicResultManifestRequest(
            class_id=class_id,
            activity_id=activity_id,
            expected_snapshot_revision=_current_revision(
                workspace, class_id, activity_id
            ),
            actor=actor,
            revision_reason="initial",
        )
        generated = generate_academic_result_manifest(
            manifest_request,
            workspace_root=workspace,
        )
        public_before = read_academic_result_manifest(generated.content)
        for score_id in score_ids_by_workflow[workflow]:
            public_score = lookup_academic_result_score(public_before, score_id)
            if public_score.value != "meets" or public_score.disposition != "scored":
                raise RuntimeError(f"{workflow} public Score readback is incorrect")
        publication = publish_concord_academic_results(
            manifest_request,
            workspace_root=workspace,
        )
        if not publication.compatibility.compatible:
            raise RuntimeError(f"{workflow} physical publication is incompatible")
        if publication.publication.work != work:
            raise RuntimeError(f"{workflow} physical publication work is incorrect")
        public_after = read_academic_result_manifest(
            publication.manifest_generation.content
        )
        if public_after != public_before:
            raise RuntimeError(f"{workflow} publication changed public semantics")
        if workflow == "project":
            for token in private_tokens:
                encoded = token.encode("utf-8")
                if (
                    encoded in generated.content
                    or encoded in publication.manifest_generation.content
                ):
                    raise RuntimeError(
                        "project planning-only provenance leaked into result manifest"
                    )
                if token in repr(publication.publication):
                    raise RuntimeError(
                        "project planning-only provenance leaked into "
                        "Publication Record"
                    )
        publication_summaries[workflow] = {
            "manifest_digest": publication.publication.manifest_digest,
            "publication_id": publication.publication.publication_id,
            "publication_revision": publication.publication.record_set_revision,
            "score_record_ids": list(score_ids_by_workflow[workflow]),
        }

    # Re-check project downstream records after physical review/scoring/publication.
    project_case = next(
        case for case in cases if _json_string(case, "workflow") == "project"
    )
    project_work = ModuleWorkRef(
        "concord",
        class_id,
        _json_string(project_case, "activity_id"),
    )
    project_graph = load_current_record_graph(workspace, project_work).graph
    for record in (
        *project_graph.groups,
        *project_graph.memberships,
        *project_graph.packet_instances,
        *project_graph.artifact_instances,
        *project_graph.artifact_pages,
        *project_graph.scan_references,
        *project_graph.artifact_reviews,
        *project_graph.score_records,
    ):
        representation = repr(record)
        if any(token in representation for token in private_tokens):
            raise RuntimeError("project planning provenance leaked downstream")

    workflow_route_ids: dict[str, list[str]] = {}
    workflow_page_ids: dict[str, list[str]] = {}
    workflow_artifact_ids: dict[str, list[str]] = {}
    for workflow in ("seminar", "project", "peer_review"):
        workflow_cases = tuple(
            case for case in cases if _json_string(case, "workflow") == workflow
        )
        workflow_route_ids[workflow] = sorted(
            route_id
            for case in workflow_cases
            for route_id in observed_routes_by_case[_json_string(case, "case_id")]
        )
        workflow_page_ids[workflow] = sorted(
            page_id
            for case in workflow_cases
            for page_id in observed_pages_by_case[_json_string(case, "case_id")]
        )
        workflow_artifact_ids[workflow] = sorted(
            _json_string(case, "artifact_instance_id") for case in workflow_cases
        )

    evidence_summary: dict[str, object] = {
        "schema_version": 2,
        "technical_path": "COMPLETED",
        "owner_physical_classification_required": True,
        "physical_mark_confirmed": True,
        "visual_inspection_confirmed": True,
        "final_commit": outer["final_commit"],
        "concord_wheel_filename": outer["concord_wheel_filename"],
        "concord_wheel_byte_length": outer["concord_wheel_byte_length"],
        "concord_wheel_sha256": outer["concord_wheel_sha256"],
        "core_wheel_filename": outer["core_wheel_filename"],
        "core_wheel_byte_length": outer["core_wheel_byte_length"],
        "core_wheel_sha256": outer["core_wheel_sha256"],
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "installed_concord_version": metadata.version("pds-concord"),
        "installed_core_version": metadata.version("pds-core"),
        "installed_concord_origin": installed["concord_origin"],
        "installed_core_origin": installed["core_origin"],
        "tester": args.tester,
        "date_local_time": datetime.now().astimezone().isoformat(timespec="seconds"),
        "printer": args.printer,
        "printer_path": args.printer_path,
        "paper_size": args.paper_size,
        "print_scaling": args.print_scaling,
        "print_sides": args.print_sides,
        "print_color_mode": args.print_color_mode,
        "scanner": args.scanner,
        "scanner_path": args.scanner_path,
        "scan_dpi": args.scan_dpi,
        "scan_color_mode": args.scan_color_mode,
        "scan_sides": args.scan_sides,
        "scan_adjustments": args.scan_adjustments,
        "physical_scan_filenames_sha256": scan_digests,
        "physical_source_page_count": physical_source_page_count,
        "retained_source_scan_ids": sorted(retained_source_ids),
        "workflow_route_ids": workflow_route_ids,
        "workflow_artifact_ids": workflow_artifact_ids,
        "workflow_artifact_page_ids": workflow_page_ids,
        "workflow_publications": publication_summaries,
        "workflow_owner_classifications": {
            "seminar": "OWNER CLASSIFICATION REQUIRED",
            "project": "OWNER CLASSIFICATION REQUIRED",
            "peer_review": "OWNER CLASSIFICATION REQUIRED",
        },
        "overall_owner_classification": "OWNER CLASSIFICATION REQUIRED",
    }
    _write_json(run_root / EVIDENCE_FILE, evidence_summary)

    comment_lines = [
        "Issue #70 completion record",
        "",
        f"final commit: {outer['final_commit']}",
        f"Concord wheel: {outer['concord_wheel_filename']}",
        f"Concord wheel byte length: {outer['concord_wheel_byte_length']}",
        f"Concord wheel SHA-256: {outer['concord_wheel_sha256']}",
        f"Core wheel: {outer['core_wheel_filename']}",
        f"Core wheel SHA-256: {outer['core_wheel_sha256']}",
        f"Python/platform: {sys.version.split()[0]} / {platform.platform()}",
        "authoritative installed starter-workflow qualification: OWNER RECORD REQUIRED",
        "same wheel bytes used for installed + physical: OWNER CONFIRMATION REQUIRED",
        (
            f"physical tester/date: {args.tester} / "
            f"{evidence_summary['date_local_time']}"
        ),
        (
            f"printer/settings: {args.printer}; {args.printer_path}; "
            f"{args.paper_size}; {args.print_scaling}; {args.print_sides}; "
            f"{args.print_color_mode}"
        ),
        (
            f"scanner/settings: {args.scanner}; {args.scanner_path}; "
            f"{args.scan_dpi} DPI; {args.scan_color_mode}; {args.scan_sides}; "
            f"{args.scan_adjustments}"
        ),
        "physical visual inspection: OWNER CLASSIFICATION REQUIRED",
        "physical seminar: OWNER CLASSIFICATION REQUIRED",
        "physical group project: OWNER CLASSIFICATION REQUIRED",
        "physical peer review: OWNER CLASSIFICATION REQUIRED",
        (
            "retained source ids: " + ",".join(sorted(retained_source_ids))
        ),
        (
            "seminar route/artifact summary: routes="
            + ",".join(workflow_route_ids["seminar"])
            + "; artifacts="
            + ",".join(workflow_artifact_ids["seminar"])
        ),
        (
            "project route/artifact summary: routes="
            + ",".join(workflow_route_ids["project"])
            + "; artifacts="
            + ",".join(workflow_artifact_ids["project"])
        ),
        (
            "peer-review route/artifact summary: routes="
            + ",".join(workflow_route_ids["peer_review"])
            + "; artifacts="
            + ",".join(workflow_artifact_ids["peer_review"])
        ),
        (
            "publication ids: seminar="
            + str(publication_summaries["seminar"]["publication_id"])
            + "; project="
            + str(publication_summaries["project"]["publication_id"])
            + "; peer_review="
            + str(publication_summaries["peer_review"]["publication_id"])
        ),
        "physical acceptance: OWNER CLASSIFICATION REQUIRED",
        "READY FOR #71: NO",
    ]
    (run_root / COMMENT_FILE).write_text(
        "\n".join(comment_lines) + "\n",
        encoding="utf-8",
    )
    state["status"] = "technical_resume_completed"
    state["evidence_relative_path"] = EVIDENCE_FILE
    state["comment_relative_path"] = COMMENT_FILE
    _write_json(run_root / STATE_FILE, state)
    print("COMPLETED issue #70 technical physical return path")
    print(f"evidence={run_root / EVIDENCE_FILE}")
    print(f"comment_template={run_root / COMMENT_FILE}")
    print("owner_classification=REQUIRED_FOR_ALL_THREE_WORKFLOWS")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare/resume owner-only Concord issue #70 physical acceptance."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare")
    prepare.add_argument("concord_wheel", type=Path)
    prepare.add_argument("core_wheel", type=Path)
    prepare.add_argument("run_root", type=Path)

    resume = subparsers.add_parser("resume")
    resume.add_argument("run_root", type=Path)
    resume.add_argument("--scan", action="append", required=True)
    resume.add_argument("--physical-mark-confirmed", action="store_true")
    resume.add_argument("--visual-inspection-confirmed", action="store_true")
    resume.add_argument("--tester", required=True)
    resume.add_argument("--printer", required=True)
    resume.add_argument("--printer-path", default="unknown")
    resume.add_argument("--paper-size", required=True)
    resume.add_argument("--print-scaling", required=True)
    resume.add_argument(
        "--print-sides", choices=("simplex", "duplex"), required=True
    )
    resume.add_argument("--print-color-mode", required=True)
    resume.add_argument("--scanner", required=True)
    resume.add_argument("--scanner-path", default="unknown")
    resume.add_argument("--scan-dpi", type=int, required=True)
    resume.add_argument("--scan-color-mode", required=True)
    resume.add_argument(
        "--scan-sides", choices=("simplex", "duplex"), required=True
    )
    resume.add_argument("--scan-adjustments", default="none")

    internal_prepare = subparsers.add_parser("_installed-prepare")
    internal_prepare.add_argument("run_root", type=Path)

    internal_resume = subparsers.add_parser("_installed-resume")
    internal_resume.add_argument("run_root", type=Path)
    internal_resume.add_argument("--scan", action="append", required=True)
    internal_resume.add_argument("--physical-mark-confirmed", action="store_true")
    internal_resume.add_argument("--visual-inspection-confirmed", action="store_true")
    internal_resume.add_argument("--tester", required=True)
    internal_resume.add_argument("--printer", required=True)
    internal_resume.add_argument("--printer-path", required=True)
    internal_resume.add_argument("--paper-size", required=True)
    internal_resume.add_argument("--print-scaling", required=True)
    internal_resume.add_argument(
        "--print-sides", choices=("simplex", "duplex"), required=True
    )
    internal_resume.add_argument("--print-color-mode", required=True)
    internal_resume.add_argument("--scanner", required=True)
    internal_resume.add_argument("--scanner-path", required=True)
    internal_resume.add_argument("--scan-dpi", type=int, required=True)
    internal_resume.add_argument("--scan-color-mode", required=True)
    internal_resume.add_argument(
        "--scan-sides", choices=("simplex", "duplex"), required=True
    )
    internal_resume.add_argument("--scan-adjustments", required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.command == "prepare":
        return _prepare_public(args)
    if args.command == "resume":
        return _resume_public(args)
    if args.command == "_installed-prepare":
        return _installed_prepare(Path(args.run_root).resolve())
    if args.command == "_installed-resume":
        return _installed_resume(args)
    raise RuntimeError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
