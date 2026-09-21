"""Run Issue #113 relationship acceptance from isolated installed wheels."""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import tempfile
import textwrap
import venv
from pathlib import Path


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
    """Return the installed-only Issue #113 acceptance program."""
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
        from pds_core.class_metadata import (
            create_class_metadata,
            write_class_metadata_for_class,
        )
        from pds_core.classes import write_class_roster
        from pds_core.module_profiles import build_module_registry
        from pds_core.pds2 import parse_pds2_payload
        from pds_core.rosters import create_roster
        from pds_core.route_registrations import load_route_registration
        from pds_core.routing_models import ModuleWorkRef
        from pds_core.workspace import ensure_workspace_root

        from concord.models import (
            EffectiveContext,
            PacketAudienceIntent,
            PacketComponent,
            PacketDefinition,
            PacketRenderingRules,
            PacketVersion,
            ParticipantReference,
            SubjectReference,
        )
        from concord.packet_storage import create_packet_library, load_current_packet
        from concord.pds_module import get_module_profile
        from concord.routing.scan_intake import route_scan_sources
        from concord.starter_templates.catalog import get_starter_template
        from concord.storage import load_current_record_graph
        from concord.template_storage import (
            create_template_library,
            load_current_template,
        )
        from concord.workflows import (
            CreateActivityContextRequest,
            CreateGroupWithMembersRequest,
            GroupMemberSpec,
            GroupRoleSpec,
            PacketSubjectBinding,
            PreparePacketInstantiationRequest,
            PrepareStarterTemplateInstallRequest,
            RenderPacketInstanceRequest,
            WorkflowActor,
            commit_packet_instantiation,
            commit_starter_template_install,
            core_student_participant,
            create_activity_context,
            create_group_with_members,
            prepare_packet_instantiation,
            prepare_starter_template_install,
            render_packet_instance,
        )
        from concord.workflows.context import provenance

        CLASS_ID = "english12-p2"
        ACTIVITY_ID = "activity-issue113"
        SESSION_ID = "session-issue113"
        REVIEWER_ID = "student-1"
        REVIEWEE_ID = "student-2"
        ROLE_ID = "role-observer"
        TARGET_KEY = "role:role-observer"
        STARTER_KEY = "peer_review_writing"


        def stage(name: str) -> None:
            print(f"issue113 installed wheel: {name}: PASS", flush=True)


        def require_installed(module: object, distribution: str) -> None:
            origin = Path(getattr(module, "__file__")).resolve()
            if "site-packages" not in str(origin).casefold():
                raise AssertionError(
                    f"{distribution} did not import from isolated "
                    f"site-packages: {origin}"
                )


        def clock() -> datetime:
            return datetime(2026, 9, 20, 20, 0, tzinfo=timezone.utc)


        def actor() -> WorkflowActor:
            return WorkflowActor(
                actor_id="teacher-issue113-installed",
                display_label="Synthetic Installed-Wheel Teacher",
                role_label="teacher",
            )


        def context() -> EffectiveContext:
            return EffectiveContext(
                activity_id=ACTIVITY_ID,
                session_ids=(SESSION_ID,),
            )


        def student_subject(student_id: str) -> SubjectReference:
            return SubjectReference(
                subject_kind="core_student",
                subject_id=student_id,
                owning_system="core",
            )


        def make_workspace(parent: Path, label: str) -> Path:
            root = ensure_workspace_root(parent / label / "workspace")
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
                            "student_id": REVIEWER_ID,
                            "last_name": "Montgomery-Williams",
                            "first_name": "Alexandria",
                            "period": "2",
                        },
                        {
                            "student_id": REVIEWEE_ID,
                            "last_name": "Van-Der-Meer-Santiago",
                            "first_name": "Christopher",
                            "period": "2",
                        },
                    ),
                ),
            )
            created = create_activity_context(
                CreateActivityContextRequest(
                    class_id=CLASS_ID,
                    activity_id=ACTIVITY_ID,
                    title="Installed Relationship Review",
                    activity_type="socratic_seminar",
                    scoring_orientation="evidence_only",
                    session_id=SESSION_ID,
                    actor=actor(),
                    activity_status="active",
                    session_status="active",
                    session_label="Installed Review Session",
                ),
                workspace_root=root,
                clock=clock,
            )
            create_group_with_members(
                CreateGroupWithMembersRequest(
                    class_id=CLASS_ID,
                    activity_id=ACTIVITY_ID,
                    group_id="group-reviewers",
                    label="Reviewers",
                    expected_snapshot_revision=created.commit.snapshot_revision,
                    actor=actor(),
                    status="active",
                    effective_context=context(),
                    members=(
                        GroupMemberSpec(
                            membership_id="membership-reviewer",
                            student_id=REVIEWER_ID,
                            effective_context=context(),
                        ),
                    ),
                    roles=(
                        GroupRoleSpec(
                            role_assignment_id=ROLE_ID,
                            participant_reference=core_student_participant(
                                root,
                                CLASS_ID,
                                REVIEWER_ID,
                            ),
                            role_key="observer",
                            effective_context=context(),
                            membership_id="membership-reviewer",
                        ),
                    ),
                ),
                workspace_root=root,
                clock=clock,
            )
            return root


        def create_packet(
            root: Path,
            *,
            template_id: str,
            template_version_id: str,
            packet_id: str,
            packet_version_id: str,
            component_id: str,
            purpose: str,
        ) -> None:
            created = provenance(actor(), clock=clock, source_kind="manual")
            definition = PacketDefinition(
                packet_definition_id=packet_id,
                name="Issue 113 Installed-Wheel Packet",
                purpose=purpose,
                status="active",
                created_provenance=created,
            )
            version = PacketVersion(
                packet_version_id=packet_version_id,
                packet_definition_id=packet_id,
                version_label="v1",
                revision_sequence=1,
                components=(
                    PacketComponent(
                        packet_component_id=component_id,
                        sequence=1,
                        component_kind="concord_template",
                        template_id=template_id,
                        template_version_id=template_version_id,
                        copies_per_target=1,
                        audience_intent=PacketAudienceIntent(
                            audience_kind="role",
                            role_keys=("observer",),
                        ),
                        requirement_level="required",
                    ),
                ),
                rendering_rules=PacketRenderingRules(),
                created_provenance=created,
                status="active",
            )
            create_packet_library(
                root,
                definition=definition,
                initial_version=version,
            )


        def request(
            *,
            packet_id: str,
            packet_version_id: str,
            component_id: str,
            reviewed_subject: SubjectReference | None = None,
        ) -> PreparePacketInstantiationRequest:
            bindings = ()
            if reviewed_subject is not None:
                bindings = (
                    PacketSubjectBinding(
                        packet_component_id=component_id,
                        target_key=TARGET_KEY,
                        subject_reference=reviewed_subject,
                    ),
                )
            return PreparePacketInstantiationRequest(
                class_id=CLASS_ID,
                activity_id=ACTIVITY_ID,
                session_id=SESSION_ID,
                packet_definition_id=packet_id,
                packet_version_id=packet_version_id,
                actor=actor(),
                subject_bindings=bindings,
            )


        def render_only_packet(root: Path, generation_id: str):
            graph = load_current_record_graph(
                root,
                ModuleWorkRef("concord", CLASS_ID, ACTIVITY_ID),
            ).graph
            packets = tuple(
                item
                for item in graph.packet_instances
                if item.generation_id == generation_id
            )
            assert len(packets) == 1
            return render_packet_instance(
                RenderPacketInstanceRequest(
                    class_id=CLASS_ID,
                    activity_id=ACTIVITY_ID,
                    packet_instance_id=packets[0].packet_instance_id,
                    actor=actor(),
                ),
                workspace_root=root,
            )


        require_installed(pds_core, "pds-core")
        require_installed(concord, "pds-concord")
        assert metadata.version("pds-core") == "0.6.3"
        assert metadata.version("pds-concord") == "0.3.0"
        stage("isolated installed provenance")

        with tempfile.TemporaryDirectory(
            prefix="concord-issue113-installed-"
        ) as raw:
            base = Path(raw)

            fresh = make_workspace(base, "fresh-v2")
            entry = get_starter_template(STARTER_KEY)
            fresh_install = commit_starter_template_install(
                prepare_starter_template_install(
                    PrepareStarterTemplateInstallRequest(
                        starter_key=STARTER_KEY,
                        actor=actor(),
                    ),
                    workspace_root=fresh,
                    clock=clock,
                ),
                workspace_root=fresh,
            )
            assert fresh_install.outcome == "installed"
            assert fresh_install.template_version_id != entry.template_version_id

            fresh_library = load_current_template(fresh, entry.template_id)
            assert tuple(item.status for item in fresh_library.versions) == (
                "superseded",
                "active",
            )
            assert tuple(
                item.template_version_id for item in fresh_library.versions
            ) == (
                entry.template_version_id,
                fresh_install.template_version_id,
            )
            assert (
                fresh_library.current_template_version_id
                == fresh_install.template_version_id
            )
            stage("fresh affected starter installs v1 plus active v2")

            create_packet(
                fresh,
                template_id=fresh_install.template_id,
                template_version_id=fresh_install.template_version_id,
                packet_id="packet-current",
                packet_version_id="packet-current-v1",
                component_id="component-current",
                purpose="Exercise installed package-current relationship semantics.",
            )
            reviewee = student_subject(REVIEWEE_ID)
            prepared = prepare_packet_instantiation(
                request(
                    packet_id="packet-current",
                    packet_version_id="packet-current-v1",
                    component_id="component-current",
                    reviewed_subject=reviewee,
                ),
                workspace_root=fresh,
                clock=clock,
            )
            assert prepared.ready_for_commit
            assert len(prepared.target_plans) == 1
            planned = prepared.target_plans[0].artifacts[0]
            assert planned.template_version_id == fresh_install.template_version_id
            assert planned.authorship_mode == "individual_author"
            assert planned.proposed_author_reference == ParticipantReference(
                participant_kind="core_student",
                participant_id=REVIEWER_ID,
                owning_system="core",
            )
            assert planned.proposed_subject_reference == reviewee
            assert planned.proposed_subject_role == "reviewed_subject"
            stage("explicit peer-review Subject mapping and preview")

            committed = commit_packet_instantiation(
                prepared,
                workspace_root=fresh,
                generation_id="generation-current",
                clock=clock,
            )
            assert committed.artifact_instance_ids
            assert committed.pages
            assert committed.routes_verified == len(committed.pages)

            work = ModuleWorkRef("concord", CLASS_ID, ACTIVITY_ID)
            generated = load_current_record_graph(fresh, work).graph
            assert len(generated.artifact_authors) == 1
            generated_author = generated.artifact_authors[0]
            assert isinstance(
                generated_author.author_reference,
                ParticipantReference,
            )
            assert (
                generated_author.author_reference.participant_id
                == REVIEWER_ID
            )
            assert generated_author.attribution_status == "proposed"
            assert len(generated.artifact_subjects) == 1
            generated_subject = generated.artifact_subjects[0]
            assert generated_subject.subject_reference == reviewee
            assert generated_subject.subject_role == "reviewed_subject"
            assert generated_subject.confirmation_status == "proposed"
            stage("Packet commit and Author/Subject inspection")

            rendered = render_only_packet(fresh, "generation-current")
            assert rendered.output_path.is_file()
            rendered_bytes = rendered.output_path.read_bytes()
            assert rendered_bytes.startswith(b"%PDF")
            assert hashlib.sha256(rendered_bytes).hexdigest() == (
                rendered.output_sha256
            )
            assert len(rendered.payloads) == len(committed.pages)

            for payload in rendered.payloads:
                locator = parse_pds2_payload(payload)
                registration = load_route_registration(fresh, locator)
                assert set(registration.module_details) == {
                    "activity_id",
                    "artifact_instance_id",
                    "artifact_page_id",
                    "page_number",
                }
                assert registration.human_fallback is not None
                assert "Reviewer: Alexandria M." in (
                    registration.human_fallback
                )
                assert "Reviewee: Christopher V." in (
                    registration.human_fallback
                )
                assert REVIEWER_ID not in registration.human_fallback
                assert REVIEWEE_ID not in registration.human_fallback
            stage("real PDF render and PDS2 route verification")

            registry = build_module_registry(
                explicit_profiles=(get_module_profile(),),
                discover_installed=False,
            )
            routed = route_scan_sources(
                (rendered.output_path,),
                workspace_root=fresh,
                registry=registry,
            )
            assert routed.failure_count == 0
            assert routed.dispatched_count == len(committed.pages)

            returned = load_current_record_graph(fresh, work).graph
            assert len(returned.scan_references) == len(committed.pages)
            assert {page.page_status for page in returned.artifact_pages} == {
                "returned"
            }
            assert returned.artifact_authors == generated.artifact_authors
            assert returned.artifact_subjects == generated.artifact_subjects
            stage("returned scan routing preserves relationship attribution")

            historical = make_workspace(base, "historical-v1")
            historical_entry = get_starter_template(STARTER_KEY)
            created = provenance(actor(), clock=clock, source_kind="manual")
            definition, v1 = historical_entry.build_template_records(
                created_provenance=created,
                status="active",
            )
            create_template_library(
                historical,
                definition=definition,
                initial_version=v1,
                rendering_specification=(
                    historical_entry.rendering_specification_bytes()
                ),
            )
            create_packet(
                historical,
                template_id=historical_entry.template_id,
                template_version_id=v1.template_version_id,
                packet_id="packet-historical",
                packet_version_id="packet-historical-v1",
                component_id="component-historical",
                purpose="Exercise installed historical v1 replay.",
            )

            historical_prepared = prepare_packet_instantiation(
                request(
                    packet_id="packet-historical",
                    packet_version_id="packet-historical-v1",
                    component_id="component-historical",
                ),
                workspace_root=historical,
                clock=clock,
            )
            assert historical_prepared.ready_for_commit
            historical_plan = historical_prepared.target_plans[0].artifacts[0]
            assert historical_plan.template_version_id == v1.template_version_id
            assert historical_plan.proposed_subject_reference == student_subject(
                REVIEWER_ID
            )
            assert historical_plan.proposed_subject_role == "observed_participant"

            commit_packet_instantiation(
                historical_prepared,
                workspace_root=historical,
                generation_id="generation-historical",
                clock=clock,
            )
            first_render = render_only_packet(
                historical,
                "generation-historical",
            )
            first_bytes = first_render.output_path.read_bytes()
            first_sha = first_render.output_sha256
            first_payloads = first_render.payloads
            historical_work = ModuleWorkRef(
                "concord",
                CLASS_ID,
                ACTIVITY_ID,
            )
            before_upgrade = load_current_record_graph(
                historical,
                historical_work,
            )
            original_routes = tuple(
                load_route_registration(
                    historical,
                    parse_pds2_payload(payload),
                )
                for payload in first_payloads
            )
            stage("historical v1 generation and render")

            upgrade = commit_starter_template_install(
                prepare_starter_template_install(
                    PrepareStarterTemplateInstallRequest(
                        starter_key=STARTER_KEY,
                        actor=actor(),
                    ),
                    workspace_root=historical,
                    clock=clock,
                ),
                workspace_root=historical,
            )
            assert upgrade.outcome == "upgraded"
            assert upgrade.template_version_id != v1.template_version_id

            upgraded_library = load_current_template(
                historical,
                historical_entry.template_id,
            )
            assert tuple(
                item.template_version_id
                for item in upgraded_library.versions
            ) == (
                v1.template_version_id,
                upgrade.template_version_id,
            )
            assert tuple(item.status for item in upgraded_library.versions) == (
                "superseded",
                "active",
            )
            historical_packet = load_current_packet(
                historical,
                "packet-historical",
            )
            assert (
                historical_packet.head_version.components[0].template_version_id
                == v1.template_version_id
            )
            after_upgrade = load_current_record_graph(
                historical,
                historical_work,
            )
            assert after_upgrade == before_upgrade
            stage("packaged v1 to v2 upgrade without Packet rewrite")

            replay = render_only_packet(
                historical,
                "generation-historical",
            )
            assert replay.replayed
            assert replay.payloads == first_payloads
            assert replay.output_sha256 == first_sha
            assert replay.output_path.read_bytes() == first_bytes
            replay_routes = tuple(
                load_route_registration(
                    historical,
                    parse_pds2_payload(payload),
                )
                for payload in replay.payloads
            )
            assert replay_routes == original_routes
            stage("historical v1 byte-for-byte replay after upgrade")

        print("Issue #113 isolated installed-wheel acceptance: PASS", flush=True)
        """
    )


def smoke(concord_wheel: Path, core_wheel: Path) -> None:
    """Exercise Issue #113 using only isolated installed wheel imports."""
    if not concord_wheel.is_file():
        raise FileNotFoundError(concord_wheel)
    if not core_wheel.is_file():
        raise FileNotFoundError(core_wheel)

    print(
        f"Issue #113 candidate wheel SHA-256: {_sha256(concord_wheel)}",
        flush=True,
    )
    print(
        f"Issue #113 Core wheel SHA-256: {_sha256(core_wheel)}",
        flush=True,
    )

    with tempfile.TemporaryDirectory(
        prefix="concord-issue113-wheel-"
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

        smoke_path = work / "issue113_installed_acceptance.py"
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
