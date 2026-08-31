"""Install Concord/Core wheels in isolation and smoke-test starter workflows."""

from __future__ import annotations

import argparse
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


def _run(command: list[str], cwd: Path) -> None:
    subprocess.run(
        command,
        cwd=cwd,
        check=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )


def _smoke_code() -> str:
    """Return the installed-only representative starter acceptance program."""
    return textwrap.dedent(
        r'''
        from __future__ import annotations

        import os
        import tempfile
        from datetime import datetime, timezone
        from importlib import metadata
        from pathlib import Path
        from unittest.mock import patch

        import concord
        import pds_core
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

        from concord.academic_result_manifest_generation import (
            GenerateAcademicResultManifestRequest,
            generate_academic_result_manifest,
        )
        from concord.academic_result_publication import (
            publish_concord_academic_results,
        )
        from concord.academic_result_reader import (
            lookup_academic_result_score,
            read_academic_result_manifest,
        )
        from concord.academic_work_registration import (
            register_concord_academic_work,
        )
        from concord.menu_context import MenuSessionContext
        from concord.menu_guided_activity import launch_guided_activity_menu
        from concord.models import (
            EffectiveContext,
            EvidenceReference,
            PlannedGroup,
            PrivacyPolicy,
            ScoreTargetReference,
            ScoringScaleLevel,
            SubjectReference,
        )
        from concord.routing.scan_intake import route_scan_sources
        from concord.starter_templates import get_starter_template
        from concord.storage import load_current_record_graph
        from concord.workflows import (
            AddArtifactReviewRequest,
            AddScoreRequest,
            ApplyGroupPlanRequest,
            ApproveGroupPlanRequest,
            AssembleArtifactRequest,
            CreateActivityContextRequest,
            CreateCriterionSetRequest,
            CreateManualGroupPlanRequest,
            CreateRandomGroupPlanRequest,
            CreateScoringScaleRequest,
            CreateSignalGroupPlanRequest,
            CriterionSpec,
            PrepareGroupPlanApplicationRequest,
            PreparePacketInstantiationRequest,
            PrepareStarterTemplateInstallRequest,
            PreviewGroupPlanRequest,
            RenderPacketGenerationRequest,
            ScoreEvidenceLinkSpec,
            SelectActivityCriterionSetsRequest,
            WorkflowActor,
            add_artifact_review,
            add_score,
            apply_group_plan,
            approve_group_plan,
            assemble_returned_artifact,
            commit_packet_instantiation,
            commit_starter_template_install,
            create_activity_context,
            create_criterion_set,
            create_manual_group_plan,
            create_random_group_plan,
            create_scoring_scale,
            create_signal_group_plan,
            list_activities,
            list_groups,
            list_memberships,
            list_sessions,
            prepare_group_plan_application,
            prepare_packet_instantiation,
            prepare_starter_template_install,
            preview_group_plan,
            render_packet_generation,
            select_activity_criterion_sets,
            show_activity,
        )
        from concord.workflows.packet import (
            PreparePacketFromTemplateRequest,
            commit_packet_from_template,
            prepare_packet_from_template,
        )


        def stage(name: str) -> None:
            print(f"issue70 seminar: {name}: PASS", flush=True)


        def project_stage(name: str) -> None:
            print(f"issue70 project: {name}: PASS", flush=True)


        def peer_stage(name: str) -> None:
            print(f"issue70 peer review: {name}: PASS", flush=True)


        def assert_private_absent(value: object, tokens: tuple[str, ...]) -> None:
            rendered = (
                value
                if isinstance(value, bytes)
                else repr(value).encode("utf-8")
            )
            for token in tokens:
                assert token.encode("utf-8") not in rendered


        def require_installed(module: object, distribution: str) -> None:
            origin = Path(getattr(module, "__file__")).resolve()
            lowered = str(origin).casefold()
            if "site-packages" not in lowered:
                raise AssertionError(
                    f"{distribution} did not import from isolated "
                    f"site-packages: {origin}"
                )


        assert metadata.version("pds-core") == "0.6.3"
        assert metadata.version("pds-concord") == "0.3.0"
        require_installed(pds_core, "pds-core")
        require_installed(concord, "pds-concord")
        requirements = tuple(metadata.requires("pds-concord") or ())
        forbidden = ("meridian", "paper-data-suite")
        assert not any(
            name in requirement.casefold()
            for requirement in requirements
            for name in forbidden
        )
        stage("installed provenance")

        with tempfile.TemporaryDirectory(prefix="concord-issue70-seminar-") as raw:
            root = ensure_workspace_root(Path(raw) / "workspace")
            os.environ["PDS_WORKSPACE_ROOT"] = str(root)
            class_id = "class-issue70"
            class_metadata = create_class_metadata(
                class_id,
                "2026-2027",
                created_at=datetime(2026, 8, 30, tzinfo=timezone.utc),
            )
            write_class_metadata_for_class(root, class_metadata)
            roster = create_roster(
                class_id,
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
                        "first_name": "Blake",
                        "period": "1",
                    },
                    {
                        "student_id": "student-3",
                        "last_name": "Three",
                        "first_name": "Casey",
                        "period": "1",
                    },
                    {
                        "student_id": "student-4",
                        "last_name": "Four",
                        "first_name": "Drew",
                        "period": "1",
                    },
                ),
            )
            write_class_roster(root, roster)
            actor = WorkflowActor(
                actor_id="teacher-issue70",
                display_label="Synthetic Teacher",
                role_label="teacher",
            )
            state = MenuSessionContext(actor=actor)
            guided_inputs = (
                "1",  # start fresh
                "1",  # exact synthetic Core class
                "Issue 70 Seminar",
                "1",  # discussion / seminar
                "4",  # local classroom criteria
                "",   # optional description
                "",   # default first-session label
                "CREATE",
                "2",  # finish for now; later stages use public services
            )
            with patch("builtins.input", side_effect=guided_inputs):
                launch_guided_activity_menu(state)

            activities = list_activities(workspace_root=root, class_id=class_id)
            assert len(activities) == 1
            activity = activities[0]
            assert activity.title == "Issue 70 Seminar"
            assert activity.scoring_orientation == "local_criteria_only"
            sessions = list_sessions(
                class_id,
                activity.activity_id,
                workspace_root=root,
            )
            assert len(sessions) == 1
            session_id = sessions[0].session_id
            activity_id = activity.activity_id
            work = ModuleWorkRef("concord", class_id, activity_id)
            stage("guided Activity setup")

            context = EffectiveContext(
                activity_id=activity_id,
                session_ids=(session_id,),
            )
            manual = create_manual_group_plan(
                CreateManualGroupPlanRequest(
                    class_id=class_id,
                    activity_id=activity_id,
                    group_plan_id="plan-seminar-issue70",
                    expected_snapshot_revision=activity.snapshot_revision,
                    actor=actor,
                    proposed_groups=(
                        PlannedGroup(
                            planned_group_key="plan-a",
                            label="Seminar Group A",
                            student_ids=("student-1", "student-2"),
                            effective_context=context,
                        ),
                        PlannedGroup(
                            planned_group_key="plan-b",
                            label="Seminar Group B",
                            student_ids=("student-3", "student-4"),
                            effective_context=context,
                        ),
                    ),
                    target_group_count=2,
                ),
                workspace_root=root,
            )
            assert manual.status == "draft"
            assert not list_groups(class_id, activity_id, workspace_root=root)
            assert not list_memberships(class_id, activity_id, workspace_root=root)

            previewed = preview_group_plan(
                PreviewGroupPlanRequest(
                    class_id=class_id,
                    activity_id=activity_id,
                    group_plan_id=manual.group_plan_id,
                    expected_snapshot_revision=manual.commit.snapshot_revision,
                    actor=actor,
                ),
                workspace_root=root,
            )
            assert previewed.plan.status == "previewed"
            assert not list_groups(class_id, activity_id, workspace_root=root)

            approved = approve_group_plan(
                ApproveGroupPlanRequest(
                    class_id=class_id,
                    activity_id=activity_id,
                    group_plan_id=manual.group_plan_id,
                    expected_snapshot_revision=previewed.summary.snapshot_revision,
                    actor=actor,
                ),
                workspace_root=root,
            )
            assert approved.status == "approved"
            assert not list_groups(class_id, activity_id, workspace_root=root)

            application_preview = prepare_group_plan_application(
                PrepareGroupPlanApplicationRequest(
                    class_id=class_id,
                    activity_id=activity_id,
                    group_plan_id=manual.group_plan_id,
                    application_id="apply-seminar-issue70",
                ),
                workspace_root=root,
            )
            assert application_preview.group_count == 2
            assert application_preview.membership_count == 4
            assert application_preview.unresolved_count == 0
            assert not list_groups(class_id, activity_id, workspace_root=root)

            applied = apply_group_plan(
                ApplyGroupPlanRequest(
                    class_id=class_id,
                    activity_id=activity_id,
                    group_plan_id=manual.group_plan_id,
                    application_id=application_preview.application_id,
                    application_digest=application_preview.application_digest,
                    expected_snapshot_revision=(
                        application_preview.expected_snapshot_revision
                    ),
                    actor=actor,
                ),
                workspace_root=root,
            )
            assert applied.status == "applied"
            assert applied.group_count == 2
            assert applied.membership_count == 4
            assert len(list_groups(class_id, activity_id, workspace_root=root)) == 2
            assert (
                len(
                    list_memberships(
                        class_id, activity_id, workspace_root=root
                    )
                )
                == 4
            )
            group_ids = frozenset(applied.group_ids)
            stage("GroupPlan approval and application")

            starter = get_starter_template("socratic_seminar")
            seminar_page_count = starter.page_count
            assert seminar_page_count > 0
            assert "participant" in starter.suggested_audience_kinds
            assert starter.default_authorship_mode == "individual_author"
            assert starter.default_subject_kind == "core_student"
            starter_prepared = prepare_starter_template_install(
                PrepareStarterTemplateInstallRequest(
                    starter_key=starter.starter_key,
                    actor=actor,
                ),
                workspace_root=root,
            )
            starter_result = commit_starter_template_install(
                starter_prepared,
                workspace_root=root,
            )
            assert starter_result.outcome == "installed"
            assert starter_result.template_id == starter.template_id
            assert starter_result.template_version_id == starter.template_version_id

            packet_prepared = prepare_packet_from_template(
                PreparePacketFromTemplateRequest(
                    packet_definition_id="packet-seminar-issue70",
                    packet_version_id="packet-seminar-issue70-v1",
                    packet_component_id="component-seminar-issue70",
                    name="Issue 70 Seminar Packet",
                    purpose="Representative installed seminar acceptance.",
                    template_id=starter.template_id,
                    template_version_id=starter.template_version_id,
                    audience_kind="participant",
                    actor=actor,
                ),
                workspace_root=root,
            )
            packet_result = commit_packet_from_template(
                packet_prepared,
                workspace_root=root,
            )
            assert packet_result.status == "active"
            stage("installed starter and Packet selection")

            prepared_generation = prepare_packet_instantiation(
                PreparePacketInstantiationRequest(
                    class_id=class_id,
                    activity_id=activity_id,
                    session_id=session_id,
                    packet_definition_id="packet-seminar-issue70",
                    packet_version_id="packet-seminar-issue70-v1",
                    actor=actor,
                ),
                workspace_root=root,
            )
            assert prepared_generation.ready_for_commit
            assert prepared_generation.packet_instance_count == 4
            assert prepared_generation.artifact_count == 4
            assert prepared_generation.page_count == 4 * seminar_page_count
            assert prepared_generation.route_count == 4 * seminar_page_count
            planned_students = {
                target.target_context.participant_reference.participant_id
                for target in prepared_generation.target_plans
                if target.target_context.participant_reference is not None
            }
            assert planned_students == {
                "student-1",
                "student-2",
                "student-3",
                "student-4",
            }

            committed_generation = commit_packet_instantiation(
                prepared_generation,
                workspace_root=root,
                generation_id="generation-seminar-issue70",
            )
            assert len(committed_generation.packet_instance_ids) == 4
            assert len(committed_generation.artifact_instance_ids) == 4
            assert len(committed_generation.artifact_page_ids) == 4 * seminar_page_count
            assert len(committed_generation.route_ids) == 4 * seminar_page_count
            assert committed_generation.routes_expected == 4 * seminar_page_count
            assert committed_generation.routes_verified == 4 * seminar_page_count

            graph = load_current_record_graph(root, work).graph
            packet_instances = tuple(
                item
                for item in graph.packet_instances
                if item.generation_id == "generation-seminar-issue70"
            )
            assert len(packet_instances) == 4
            artifact_by_student: dict[str, str] = {}
            group_by_student: dict[str, str] = {}
            for packet_instance in packet_instances:
                target = packet_instance.target_context
                assert target.audience_kind == "participant"
                assert target.participant_reference is not None
                assert target.participant_reference.participant_kind == "core_student"
                assert target.participant_reference.owning_system == "core"
                assert target.group_id in group_ids
                assert len(packet_instance.artifact_bindings) == 1
                student_id = target.participant_reference.participant_id
                artifact_by_student[student_id] = (
                    packet_instance.artifact_bindings[0].artifact_instance_id
                )
                assert target.group_id is not None
                group_by_student[student_id] = target.group_id
            assert set(artifact_by_student) == planned_students
            assert len(set(artifact_by_student.values())) == 4
            assert group_by_student["student-1"] == group_by_student["student-2"]
            assert group_by_student["student-3"] == group_by_student["student-4"]
            assert group_by_student["student-1"] != group_by_student["student-3"]
            stage("participant Packet instantiation")

            rendered = render_packet_generation(
                RenderPacketGenerationRequest(
                    class_id=class_id,
                    activity_id=activity_id,
                    generation_id="generation-seminar-issue70",
                    actor=actor,
                ),
                workspace_root=root,
            )
            assert len(rendered.packets) == 4
            assert rendered.page_count == 4 * seminar_page_count
            assert rendered.route_count == 4 * seminar_page_count
            route_ids = set(committed_generation.route_ids)
            decoded_route_ids: set[str] = set()
            pdf_paths: list[Path] = []
            for packet in rendered.packets:
                assert packet.output_path.is_file()
                assert packet.page_count == seminar_page_count
                assert packet.route_count == seminar_page_count
                assert len(packet.payloads) == seminar_page_count
                pdf_paths.append(packet.output_path)
                for payload in packet.payloads:
                    locator = parse_pds2_payload(payload)
                    assert locator.module_id == "concord"
                    assert locator.class_id == class_id
                    assert locator.work_id == activity_id
                    assert locator.route_id in route_ids
                    decoded_route_ids.add(locator.route_id)
            assert decoded_route_ids == route_ids
            stage("real PDF and PDS2 rendering")

            returned = route_scan_sources(pdf_paths, workspace_root=root)
            assert returned.dispatched_count == 4 * seminar_page_count
            assert returned.failure_count == 0
            observed_routes: set[str] = set()
            observed_pages: set[str] = set()
            retained_scan_ids: set[str] = set()
            for source in returned.sources:
                assert source.source_error is None
                assert source.retained_source is not None
                retained_scan_ids.add(source.retained_source.source_scan_id)
                assert len(source.pages) == seminar_page_count
                for page in source.pages:
                    assert page.status == "dispatched"
                    assert page.locator is not None
                    assert page.locator.module_id == "concord"
                    assert page.locator.class_id == class_id
                    assert page.locator.work_id == activity_id
                    assert page.locator.route_id in route_ids
                    observed_routes.add(page.locator.route_id)
                    dispatch = page.module_result
                    assert dispatch is not None
                    assert dispatch.route_id == page.locator.route_id
                    assert dispatch.artifact_instance_id in artifact_by_student.values()
                    assert (
                        dispatch.artifact_page_id
                        in committed_generation.artifact_page_ids
                    )
                    observed_pages.add(dispatch.artifact_page_id)
            assert observed_routes == route_ids
            assert observed_pages == set(committed_generation.artifact_page_ids)
            assert len(retained_scan_ids) == 4

            graph = load_current_record_graph(root, work).graph
            assert len(graph.scan_references) == 4 * seminar_page_count
            returned_pages = {
                item.artifact_page_id
                for item in graph.artifact_pages
                if item.artifact_page_id in committed_generation.artifact_page_ids
                and item.page_status == "returned"
            }
            assert returned_pages == set(committed_generation.artifact_page_ids)
            for artifact_id in artifact_by_student.values():
                artifact = next(
                    item
                    for item in graph.artifact_instances
                    if item.artifact_instance_id == artifact_id
                )
                assert artifact.artifact_status == "returned"
            stage("production rasterization, Core retention, and dispatch")

            for student_id, artifact_id in sorted(artifact_by_student.items()):
                assembled = assemble_returned_artifact(
                    AssembleArtifactRequest(
                        class_id=class_id,
                        activity_id=activity_id,
                        artifact_instance_id=artifact_id,
                        expected_snapshot_revision=show_activity(
                            class_id,
                            activity_id,
                            workspace_root=root,
                        ).summary.snapshot_revision,
                        actor=actor,
                    ),
                    workspace_root=root,
                )
                assert assembled.page_count == seminar_page_count
                assert assembled.output_path.is_file()
                assert assembled.manifest_path.is_file()
                assert assembled.artifact_instance_id == artifact_id
                assert student_id in artifact_by_student
            stage("Artifact assembly")

            privacy = PrivacyPolicy(classification="teacher_and_subjects")
            for index, (student_id, artifact_id) in enumerate(
                sorted(artifact_by_student.items()),
                start=1,
            ):
                review = add_artifact_review(
                    AddArtifactReviewRequest(
                        class_id=class_id,
                        activity_id=activity_id,
                        artifact_instance_id=artifact_id,
                        artifact_review_id=f"review-seminar-{index}",
                        readability_judgment="readable",
                        page_completeness_judgment="complete",
                        filing_judgment="correct",
                        author_judgment="confirmed",
                        subject_judgment="confirmed",
                        privacy_judgment="teacher_and_subjects",
                        relevance_judgment="relevant",
                        moderation_requirement="not_required",
                        scoring_readiness="ready",
                        review_outcome="ready",
                        privacy_policy=privacy,
                        expected_snapshot_revision=show_activity(
                            class_id,
                            activity_id,
                            workspace_root=root,
                        ).summary.snapshot_revision,
                        actor=actor,
                    ),
                    workspace_root=root,
                )
                assert review.artifact_review_id == f"review-seminar-{index}"
                assert student_id in planned_students
            stage("explicit Artifact review")

            scale = create_scoring_scale(
                CreateScoringScaleRequest(
                    class_id=class_id,
                    activity_id=activity_id,
                    scoring_scale_id="scale-seminar-issue70",
                    lineage_id="scale-seminar-issue70-lineage",
                    name="Seminar Participation",
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
                    expected_snapshot_revision=show_activity(
                        class_id,
                        activity_id,
                        workspace_root=root,
                    ).summary.snapshot_revision,
                    actor=actor,
                    intended_use="Synthetic issue #70 acceptance only.",
                ),
                workspace_root=root,
            )
            criterion_set = create_criterion_set(
                CreateCriterionSetRequest(
                    class_id=class_id,
                    activity_id=activity_id,
                    criterion_set_id="criteria-seminar-issue70",
                    lineage_id="criteria-seminar-issue70-lineage",
                    name="Seminar Criteria",
                    purpose="Synthetic issue #70 acceptance only.",
                    revision=1,
                    scope="activity_specific",
                    criterion_set_kind="local",
                    criteria=(
                        CriterionSpec(
                            criterion_id="criterion-seminar-participation",
                            key="seminar-participation",
                            label="Seminar participation",
                            definition="Synthetic acceptance criterion.",
                            criterion_kind="local",
                            supported_target_kinds=("core_student",),
                            default_scoring_scale_id="scale-seminar-issue70",
                        ),
                    ),
                    status="active",
                    expected_snapshot_revision=scale.commit.snapshot_revision,
                    actor=actor,
                ),
                workspace_root=root,
            )
            selected = select_activity_criterion_sets(
                SelectActivityCriterionSetsRequest(
                    class_id=class_id,
                    activity_id=activity_id,
                    criterion_set_ids=("criteria-seminar-issue70",),
                    expected_snapshot_revision=criterion_set.commit.snapshot_revision,
                    actor=actor,
                ),
                workspace_root=root,
            )
            assert selected.criterion_set_ids == ("criteria-seminar-issue70",)

            score_ids: list[str] = []
            for index, (student_id, artifact_id) in enumerate(
                sorted(artifact_by_student.items()),
                start=1,
            ):
                subject = SubjectReference(
                    subject_kind="core_student",
                    subject_id=student_id,
                    owning_system="core",
                )
                evidence = EvidenceReference(
                    evidence_kind="artifact_instance",
                    owning_system="concord",
                    record_id=artifact_id,
                    subject_context=(subject,),
                    moderation_requirement="not_required",
                )
                score_id = f"score-seminar-{index}"
                score = add_score(
                    AddScoreRequest(
                        class_id=class_id,
                        activity_id=activity_id,
                        score_record_id=score_id,
                        target_reference=ScoreTargetReference(
                            target_kind="core_student",
                            target_id=student_id,
                            owning_system="core",
                        ),
                        criterion_id="criterion-seminar-participation",
                        scoring_scale_id="scale-seminar-issue70",
                        disposition="scored",
                        basis="linked_evidence",
                        privacy_policy=privacy,
                        expected_snapshot_revision=show_activity(
                            class_id,
                            activity_id,
                            workspace_root=root,
                        ).summary.snapshot_revision,
                        actor=actor,
                        session_id=session_id,
                        value="meets",
                        evidence_links=(
                            ScoreEvidenceLinkSpec(
                                score_evidence_link_id=f"link-seminar-{index}",
                                evidence_reference=evidence,
                                relevance_description=(
                                    "Synthetic returned seminar artifact."
                                ),
                                subject_context=(subject,),
                            ),
                        ),
                    ),
                    workspace_root=root,
                )
                assert score.score_record_id == score_id
                score_ids.append(score_id)
            stage("explicit Score recording")

            registration = register_concord_academic_work(
                root,
                class_id,
                activity_id,
                academic_intent="formative",
                lifecycle="active",
            )
            assert registration.registration.registration_revision == 1
            manifest_request = GenerateAcademicResultManifestRequest(
                class_id=class_id,
                activity_id=activity_id,
                expected_snapshot_revision=show_activity(
                    class_id,
                    activity_id,
                    workspace_root=root,
                ).summary.snapshot_revision,
                actor=actor,
                revision_reason="initial",
            )
            generated = generate_academic_result_manifest(
                manifest_request,
                workspace_root=root,
            )
            assert generated.disposition == "created"
            assert generated.revision == 1
            assert len(generated.manifest.scores) == 4
            public_before_publish = read_academic_result_manifest(generated.content)
            for score_id in score_ids:
                public_score = lookup_academic_result_score(
                    public_before_publish,
                    score_id,
                )
                assert public_score.score_record_id == score_id
                assert public_score.disposition == "scored"
                assert public_score.value == "meets"

            publication = publish_concord_academic_results(
                manifest_request,
                workspace_root=root,
            )
            assert publication.disposition == "created"
            assert publication.compatibility.compatible
            assert publication.publication.work == work
            assert publication.publication.record_set_revision == generated.revision
            assert publication.publication.manifest_digest == generated.sha256
            public_after_publish = read_academic_result_manifest(
                publication.manifest_generation.content
            )
            assert public_after_publish == public_before_publish
            for score_id in score_ids:
                assert lookup_academic_result_score(
                    public_after_publish,
                    score_id,
                ).score_record_id == score_id
            stage("Academic Work, manifest, publication, and public readback")

            final_graph = load_current_record_graph(root, work).graph
            assert len(final_graph.groups) == 2
            assert len(final_graph.memberships) == 4
            assert len(final_graph.packet_instances) == 4
            assert len(final_graph.artifact_instances) == 4
            assert len(final_graph.artifact_pages) == 4 * seminar_page_count
            assert len(final_graph.scan_references) == 4 * seminar_page_count
            assert len(final_graph.artifact_reviews) == 4
            assert len(final_graph.score_records) == 4
            assert not any(
                module_name.startswith("meridian")
                for module_name in tuple(__import__("sys").modules)
            )
            stage("seminar workflow complete")

            # Representative group-project workflow. The signal metadata is deliberately
            # sentinel-like so accidental downstream leakage is mechanically visible.
            project_activity_id = "activity-project-issue70"
            project_session_id = "session-project-issue70"
            project_created = create_activity_context(
                CreateActivityContextRequest(
                    class_id=class_id,
                    activity_id=project_activity_id,
                    title="Issue 70 Group Project",
                    activity_type="project",
                    scoring_orientation="local_criteria_only",
                    session_id=project_session_id,
                    actor=actor,
                    activity_status="active",
                    session_status="active",
                    session_label="Project Session",
                ),
                workspace_root=root,
            )
            project_work = ModuleWorkRef("concord", class_id, project_activity_id)
            project_context = EffectiveContext(
                activity_id=project_activity_id,
                session_ids=(project_session_id,),
            )
            private_signal_set_id = "issue70-private-signal-set"
            private_dimension_id = "issue70-private-proficiency-band"
            private_source_module = "issue70_private_producer"
            private_snapshot_id = "issue70-private-snapshot"
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
            write_grouping_signal(root, signal)
            private_canonical_digest = calculate_grouping_signal_digest(signal)
            private_tokens = (
                private_signal_set_id,
                private_dimension_id,
                private_source_module,
                private_snapshot_id,
                private_snapshot_digest,
                private_canonical_digest,
            )
            signal_plan = create_signal_group_plan(
                CreateSignalGroupPlanRequest(
                    class_id=class_id,
                    activity_id=project_activity_id,
                    group_plan_id="plan-project-issue70",
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
                workspace_root=root,
            )
            assert signal_plan.strategy == "similar_signal"
            assert signal_plan.group_count == 2
            assert signal_plan.assigned_student_count == 4
            assert signal_plan.unresolved_student_count == 0
            assert signal_plan.signal_set_id == private_signal_set_id
            assert signal_plan.signal_set_digest == private_canonical_digest
            assert signal_plan.dimension_id == private_dimension_id
            assert not list_groups(class_id, project_activity_id, workspace_root=root)
            assert not list_memberships(
                class_id,
                project_activity_id,
                workspace_root=root,
            )
            project_previewed = preview_group_plan(
                PreviewGroupPlanRequest(
                    class_id=class_id,
                    activity_id=project_activity_id,
                    group_plan_id=signal_plan.mutation.group_plan_id,
                    expected_snapshot_revision=(
                        signal_plan.mutation.commit.snapshot_revision
                    ),
                    actor=actor,
                ),
                workspace_root=root,
            )
            assert project_previewed.plan.status == "previewed"
            assert project_previewed.plan.source_signal_set_id == private_signal_set_id
            assert (
                project_previewed.plan.source_signal_set_digest
                == private_canonical_digest
            )
            assert (
                project_previewed.plan.source_signal_dimension_id
                == private_dimension_id
            )
            project_approved = approve_group_plan(
                ApproveGroupPlanRequest(
                    class_id=class_id,
                    activity_id=project_activity_id,
                    group_plan_id=signal_plan.mutation.group_plan_id,
                    expected_snapshot_revision=(
                        project_previewed.summary.snapshot_revision
                    ),
                    actor=actor,
                ),
                workspace_root=root,
            )
            assert project_approved.status == "approved"
            project_application = prepare_group_plan_application(
                PrepareGroupPlanApplicationRequest(
                    class_id=class_id,
                    activity_id=project_activity_id,
                    group_plan_id=signal_plan.mutation.group_plan_id,
                    application_id="apply-project-issue70",
                    fallback_effective_context=project_context,
                ),
                workspace_root=root,
            )
            assert project_application.group_count == 2
            assert project_application.membership_count == 4
            assert project_application.unresolved_count == 0
            project_applied = apply_group_plan(
                ApplyGroupPlanRequest(
                    class_id=class_id,
                    activity_id=project_activity_id,
                    group_plan_id=signal_plan.mutation.group_plan_id,
                    application_id=project_application.application_id,
                    application_digest=project_application.application_digest,
                    expected_snapshot_revision=(
                        project_application.expected_snapshot_revision
                    ),
                    actor=actor,
                    fallback_effective_context=project_context,
                ),
                workspace_root=root,
            )
            assert project_applied.status == "applied"
            assert project_applied.group_count == 2
            assert project_applied.membership_count == 4
            project_group_ids = frozenset(project_applied.group_ids)
            project_graph = load_current_record_graph(root, project_work).graph
            applied_plan = next(
                plan
                for plan in project_graph.group_plans
                if plan.group_plan_id == signal_plan.mutation.group_plan_id
            )
            assert applied_plan.source_signal_set_id == private_signal_set_id
            assert applied_plan.source_signal_set_digest == private_canonical_digest
            assert applied_plan.source_signal_dimension_id == private_dimension_id
            for record in (*project_graph.groups, *project_graph.memberships):
                assert_private_absent(record, private_tokens)
            project_stage("signal-backed GroupPlan approval and privacy boundary")

            project_starter = get_starter_template("project_plan")
            project_page_count = project_starter.page_count
            assert project_page_count > 0
            assert project_starter.suggested_audience_kinds == ("group",)
            assert project_starter.default_authorship_mode == "collective_group_author"
            assert project_starter.default_subject_kind == "concord_group"
            project_starter_result = commit_starter_template_install(
                prepare_starter_template_install(
                    PrepareStarterTemplateInstallRequest(
                        starter_key=project_starter.starter_key,
                        actor=actor,
                    ),
                    workspace_root=root,
                ),
                workspace_root=root,
            )
            assert project_starter_result.outcome == "installed"
            project_packet = commit_packet_from_template(
                prepare_packet_from_template(
                    PreparePacketFromTemplateRequest(
                        packet_definition_id="packet-project-issue70",
                        packet_version_id="packet-project-issue70-v1",
                        packet_component_id="component-project-issue70",
                        name="Issue 70 Project Packet",
                        purpose="Representative installed group-project acceptance.",
                        template_id=project_starter.template_id,
                        template_version_id=project_starter.template_version_id,
                        audience_kind="group",
                        actor=actor,
                    ),
                    workspace_root=root,
                ),
                workspace_root=root,
            )
            assert project_packet.status == "active"
            project_prepared_generation = prepare_packet_instantiation(
                PreparePacketInstantiationRequest(
                    class_id=class_id,
                    activity_id=project_activity_id,
                    session_id=project_session_id,
                    packet_definition_id="packet-project-issue70",
                    packet_version_id="packet-project-issue70-v1",
                    actor=actor,
                ),
                workspace_root=root,
            )
            assert project_prepared_generation.ready_for_commit
            assert project_prepared_generation.packet_instance_count == 2
            assert project_prepared_generation.artifact_count == 2
            assert project_prepared_generation.page_count == 2 * project_page_count
            assert project_prepared_generation.route_count == 2 * project_page_count
            assert_private_absent(project_prepared_generation, private_tokens)
            project_committed_generation = commit_packet_instantiation(
                project_prepared_generation,
                workspace_root=root,
                generation_id="generation-project-issue70",
            )
            assert len(project_committed_generation.packet_instance_ids) == 2
            assert len(project_committed_generation.artifact_instance_ids) == 2
            assert len(project_committed_generation.artifact_page_ids) == (
                2 * project_page_count
            )
            assert len(project_committed_generation.route_ids) == 2 * project_page_count

            project_graph = load_current_record_graph(root, project_work).graph
            project_packet_instances = tuple(
                item
                for item in project_graph.packet_instances
                if item.generation_id == "generation-project-issue70"
            )
            assert len(project_packet_instances) == 2
            artifact_by_group: dict[str, str] = {}
            for packet_instance in project_packet_instances:
                target = packet_instance.target_context
                assert target.audience_kind == "group"
                assert target.group_id in project_group_ids
                assert target.participant_reference is None
                assert len(packet_instance.artifact_bindings) == 1
                assert target.group_id is not None
                artifact_by_group[target.group_id] = (
                    packet_instance.artifact_bindings[0].artifact_instance_id
                )
                assert_private_absent(packet_instance, private_tokens)
            assert set(artifact_by_group) == project_group_ids
            assert len(set(artifact_by_group.values())) == 2
            project_stage("group Packet instantiation")

            project_rendered = render_packet_generation(
                RenderPacketGenerationRequest(
                    class_id=class_id,
                    activity_id=project_activity_id,
                    generation_id="generation-project-issue70",
                    actor=actor,
                ),
                workspace_root=root,
            )
            assert len(project_rendered.packets) == 2
            assert project_rendered.page_count == 2 * project_page_count
            assert project_rendered.route_count == 2 * project_page_count
            project_route_ids = set(project_committed_generation.route_ids)
            project_decoded_route_ids: set[str] = set()
            project_pdf_paths: list[Path] = []
            for packet in project_rendered.packets:
                assert packet.output_path.is_file()
                assert packet.page_count == project_page_count
                assert packet.route_count == project_page_count
                assert len(packet.payloads) == project_page_count
                project_pdf_paths.append(packet.output_path)
                assert_private_absent(packet.output_path.read_bytes(), private_tokens)
                for payload in packet.payloads:
                    assert_private_absent(payload, private_tokens)
                    locator = parse_pds2_payload(payload)
                    assert locator.module_id == "concord"
                    assert locator.class_id == class_id
                    assert locator.work_id == project_activity_id
                    assert locator.route_id in project_route_ids
                    project_decoded_route_ids.add(locator.route_id)
            assert project_decoded_route_ids == project_route_ids
            project_stage("real group PDF and PDS2 rendering without signal leakage")

            project_returned = route_scan_sources(
                project_pdf_paths,
                workspace_root=root,
            )
            assert project_returned.dispatched_count == 2 * project_page_count
            assert project_returned.failure_count == 0
            assert_private_absent(project_returned, private_tokens)
            project_observed_routes: set[str] = set()
            project_observed_pages: set[str] = set()
            for source in project_returned.sources:
                assert source.source_error is None
                assert source.retained_source is not None
                assert len(source.pages) == project_page_count
                for page in source.pages:
                    assert page.status == "dispatched"
                    assert page.locator is not None
                    assert page.locator.work_id == project_activity_id
                    assert page.locator.route_id in project_route_ids
                    project_observed_routes.add(page.locator.route_id)
                    dispatch = page.module_result
                    assert dispatch is not None
                    assert dispatch.route_id == page.locator.route_id
                    assert dispatch.artifact_instance_id in artifact_by_group.values()
                    assert (
                        dispatch.artifact_page_id
                        in project_committed_generation.artifact_page_ids
                    )
                    project_observed_pages.add(dispatch.artifact_page_id)
            assert project_observed_routes == project_route_ids
            assert project_observed_pages == set(
                project_committed_generation.artifact_page_ids
            )
            project_stage("production return, retention, and dispatch")

            for group_id, artifact_id in sorted(artifact_by_group.items()):
                assembled = assemble_returned_artifact(
                    AssembleArtifactRequest(
                        class_id=class_id,
                        activity_id=project_activity_id,
                        artifact_instance_id=artifact_id,
                        expected_snapshot_revision=show_activity(
                            class_id,
                            project_activity_id,
                            workspace_root=root,
                        ).summary.snapshot_revision,
                        actor=actor,
                    ),
                    workspace_root=root,
                )
                assert assembled.page_count == project_page_count
                assert assembled.output_path.is_file()
                assert assembled.manifest_path.is_file()
                assert_private_absent(
                    assembled.output_path.read_bytes(),
                    private_tokens,
                )
                assert_private_absent(
                    assembled.manifest_path.read_bytes(),
                    private_tokens,
                )
                assert group_id in project_group_ids
            project_stage("Artifact assembly without signal leakage")

            project_privacy = PrivacyPolicy(classification="group_and_teacher")
            for index, (group_id, artifact_id) in enumerate(
                sorted(artifact_by_group.items()),
                start=1,
            ):
                review = add_artifact_review(
                    AddArtifactReviewRequest(
                        class_id=class_id,
                        activity_id=project_activity_id,
                        artifact_instance_id=artifact_id,
                        artifact_review_id=f"review-project-{index}",
                        readability_judgment="readable",
                        page_completeness_judgment="complete",
                        filing_judgment="correct",
                        author_judgment="confirmed",
                        subject_judgment="confirmed",
                        privacy_judgment="group_and_teacher",
                        relevance_judgment="relevant",
                        moderation_requirement="not_required",
                        scoring_readiness="ready",
                        review_outcome="ready",
                        privacy_policy=project_privacy,
                        expected_snapshot_revision=show_activity(
                            class_id,
                            project_activity_id,
                            workspace_root=root,
                        ).summary.snapshot_revision,
                        actor=actor,
                    ),
                    workspace_root=root,
                )
                assert review.artifact_review_id == f"review-project-{index}"
                assert group_id in project_group_ids
            project_stage("explicit group Artifact review")

            project_scale = create_scoring_scale(
                CreateScoringScaleRequest(
                    class_id=class_id,
                    activity_id=project_activity_id,
                    scoring_scale_id="scale-project-issue70",
                    lineage_id="scale-project-issue70-lineage",
                    name="Project Collaboration",
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
                    expected_snapshot_revision=show_activity(
                        class_id,
                        project_activity_id,
                        workspace_root=root,
                    ).summary.snapshot_revision,
                    actor=actor,
                    intended_use="Synthetic issue #70 acceptance only.",
                ),
                workspace_root=root,
            )
            project_criterion_set = create_criterion_set(
                CreateCriterionSetRequest(
                    class_id=class_id,
                    activity_id=project_activity_id,
                    criterion_set_id="criteria-project-issue70",
                    lineage_id="criteria-project-issue70-lineage",
                    name="Project Criteria",
                    purpose="Synthetic issue #70 acceptance only.",
                    revision=1,
                    scope="activity_specific",
                    criterion_set_kind="local",
                    criteria=(
                        CriterionSpec(
                            criterion_id="criterion-project-collaboration",
                            key="project-collaboration",
                            label="Project collaboration",
                            definition="Synthetic group acceptance criterion.",
                            criterion_kind="local",
                            supported_target_kinds=("concord_group",),
                            default_scoring_scale_id="scale-project-issue70",
                        ),
                    ),
                    status="active",
                    expected_snapshot_revision=project_scale.commit.snapshot_revision,
                    actor=actor,
                ),
                workspace_root=root,
            )
            project_selected = select_activity_criterion_sets(
                SelectActivityCriterionSetsRequest(
                    class_id=class_id,
                    activity_id=project_activity_id,
                    criterion_set_ids=("criteria-project-issue70",),
                    expected_snapshot_revision=(
                        project_criterion_set.commit.snapshot_revision
                    ),
                    actor=actor,
                ),
                workspace_root=root,
            )
            assert project_selected.criterion_set_ids == ("criteria-project-issue70",)

            project_score_ids: list[str] = []
            for index, (group_id, artifact_id) in enumerate(
                sorted(artifact_by_group.items()),
                start=1,
            ):
                group_subject = SubjectReference(
                    subject_kind="concord_group",
                    subject_id=group_id,
                    owning_system="concord",
                )
                project_evidence = EvidenceReference(
                    evidence_kind="artifact_instance",
                    owning_system="concord",
                    record_id=artifact_id,
                    subject_context=(group_subject,),
                    moderation_requirement="not_required",
                )
                project_score_id = f"score-project-{index}"
                project_score = add_score(
                    AddScoreRequest(
                        class_id=class_id,
                        activity_id=project_activity_id,
                        score_record_id=project_score_id,
                        target_reference=ScoreTargetReference(
                            target_kind="concord_group",
                            target_id=group_id,
                            owning_system="concord",
                        ),
                        criterion_id="criterion-project-collaboration",
                        scoring_scale_id="scale-project-issue70",
                        disposition="scored",
                        basis="linked_evidence",
                        privacy_policy=project_privacy,
                        expected_snapshot_revision=show_activity(
                            class_id,
                            project_activity_id,
                            workspace_root=root,
                        ).summary.snapshot_revision,
                        actor=actor,
                        session_id=project_session_id,
                        value="meets",
                        evidence_links=(
                            ScoreEvidenceLinkSpec(
                                score_evidence_link_id=f"link-project-{index}",
                                evidence_reference=project_evidence,
                                relevance_description=(
                                    "Synthetic returned group project artifact."
                                ),
                                subject_context=(group_subject,),
                            ),
                        ),
                    ),
                    workspace_root=root,
                )
                assert project_score.score_record_id == project_score_id
                assert_private_absent(project_score, private_tokens)
                project_score_ids.append(project_score_id)
            project_stage("explicit group Score recording")

            project_registration = register_concord_academic_work(
                root,
                class_id,
                project_activity_id,
                academic_intent="formative",
                lifecycle="active",
            )
            assert project_registration.registration.registration_revision == 1
            project_manifest_request = GenerateAcademicResultManifestRequest(
                class_id=class_id,
                activity_id=project_activity_id,
                expected_snapshot_revision=show_activity(
                    class_id,
                    project_activity_id,
                    workspace_root=root,
                ).summary.snapshot_revision,
                actor=actor,
                revision_reason="initial",
            )
            project_generated = generate_academic_result_manifest(
                project_manifest_request,
                workspace_root=root,
            )
            assert project_generated.disposition == "created"
            assert project_generated.revision == 1
            assert len(project_generated.manifest.scores) == 2
            assert_private_absent(project_generated.content, private_tokens)
            project_public_before = read_academic_result_manifest(
                project_generated.content
            )
            for score_id in project_score_ids:
                public_score = lookup_academic_result_score(
                    project_public_before,
                    score_id,
                )
                assert public_score.score_record_id == score_id
                assert public_score.value == "meets"
            project_publication = publish_concord_academic_results(
                project_manifest_request,
                workspace_root=root,
            )
            assert project_publication.disposition == "created"
            assert project_publication.compatibility.compatible
            assert project_publication.publication.work == project_work
            assert_private_absent(
                project_publication.manifest_generation.content,
                private_tokens,
            )
            project_public_after = read_academic_result_manifest(
                project_publication.manifest_generation.content
            )
            assert project_public_after == project_public_before

            project_final_graph = load_current_record_graph(root, project_work).graph
            downstream_records = (
                *project_final_graph.groups,
                *project_final_graph.memberships,
                *project_final_graph.packet_instances,
                *project_final_graph.artifact_instances,
                *project_final_graph.artifact_pages,
                *project_final_graph.scan_references,
                *project_final_graph.artifact_reviews,
                *project_final_graph.score_records,
            )
            for record in downstream_records:
                assert_private_absent(record, private_tokens)
            assert len(project_final_graph.groups) == 2
            assert len(project_final_graph.memberships) == 4
            assert len(project_final_graph.packet_instances) == 2
            assert len(project_final_graph.artifact_instances) == 2
            assert len(project_final_graph.artifact_pages) == 2 * project_page_count
            assert len(project_final_graph.scan_references) == 2 * project_page_count
            assert len(project_final_graph.artifact_reviews) == 2
            assert len(project_final_graph.score_records) == 2
            assert not any(
                module_name.startswith("meridian")
                for module_name in tuple(__import__("sys").modules)
            )
            project_stage(
                "group-project workflow complete with privacy sentinel intact"
            )


            # Representative participant peer-review workflow. This intentionally uses
            # deterministic random planning so the third case is signal-free while still
            # proving the full proposal -> approval -> canonical application boundary.
            peer_activity_id = "activity-peer-review-issue70"
            peer_session_id = "session-peer-review-issue70"
            peer_created = create_activity_context(
                CreateActivityContextRequest(
                    class_id=class_id,
                    activity_id=peer_activity_id,
                    title="Issue 70 Peer Review",
                    activity_type="project",
                    scoring_orientation="local_criteria_only",
                    session_id=peer_session_id,
                    actor=actor,
                    activity_status="active",
                    session_status="active",
                    session_label="Peer Review Session",
                ),
                workspace_root=root,
            )
            peer_work = ModuleWorkRef("concord", class_id, peer_activity_id)
            peer_context = EffectiveContext(
                activity_id=peer_activity_id,
                session_ids=(peer_session_id,),
            )
            random_plan = create_random_group_plan(
                CreateRandomGroupPlanRequest(
                    class_id=class_id,
                    activity_id=peer_activity_id,
                    group_plan_id="plan-peer-review-issue70",
                    expected_snapshot_revision=peer_created.commit.snapshot_revision,
                    actor=actor,
                    seed="issue70-peer-review-seed",
                    target_group_count=2,
                ),
                workspace_root=root,
            )
            assert random_plan.group_count == 2
            assert random_plan.assigned_student_count == 4
            assert random_plan.group_sizes == (2, 2)
            assert not list_groups(class_id, peer_activity_id, workspace_root=root)
            assert not list_memberships(
                class_id,
                peer_activity_id,
                workspace_root=root,
            )
            peer_previewed = preview_group_plan(
                PreviewGroupPlanRequest(
                    class_id=class_id,
                    activity_id=peer_activity_id,
                    group_plan_id=random_plan.mutation.group_plan_id,
                    expected_snapshot_revision=(
                        random_plan.mutation.commit.snapshot_revision
                    ),
                    actor=actor,
                ),
                workspace_root=root,
            )
            assert peer_previewed.plan.status == "previewed"
            assert peer_previewed.plan.strategy == "random"
            assert peer_previewed.plan.seed == "issue70-peer-review-seed"
            assert peer_previewed.plan.source_signal_set_id is None
            assert peer_previewed.plan.source_signal_set_digest is None
            assert peer_previewed.plan.source_signal_dimension_id is None
            peer_approved = approve_group_plan(
                ApproveGroupPlanRequest(
                    class_id=class_id,
                    activity_id=peer_activity_id,
                    group_plan_id=random_plan.mutation.group_plan_id,
                    expected_snapshot_revision=(
                        peer_previewed.summary.snapshot_revision
                    ),
                    actor=actor,
                ),
                workspace_root=root,
            )
            assert peer_approved.status == "approved"
            peer_application = prepare_group_plan_application(
                PrepareGroupPlanApplicationRequest(
                    class_id=class_id,
                    activity_id=peer_activity_id,
                    group_plan_id=random_plan.mutation.group_plan_id,
                    application_id="apply-peer-review-issue70",
                    fallback_effective_context=peer_context,
                ),
                workspace_root=root,
            )
            assert peer_application.group_count == 2
            assert peer_application.membership_count == 4
            assert peer_application.unresolved_count == 0
            assert not list_groups(class_id, peer_activity_id, workspace_root=root)
            peer_applied = apply_group_plan(
                ApplyGroupPlanRequest(
                    class_id=class_id,
                    activity_id=peer_activity_id,
                    group_plan_id=random_plan.mutation.group_plan_id,
                    application_id=peer_application.application_id,
                    application_digest=peer_application.application_digest,
                    expected_snapshot_revision=(
                        peer_application.expected_snapshot_revision
                    ),
                    actor=actor,
                    fallback_effective_context=peer_context,
                ),
                workspace_root=root,
            )
            assert peer_applied.status == "applied"
            assert peer_applied.group_count == 2
            assert peer_applied.membership_count == 4
            peer_group_ids = frozenset(peer_applied.group_ids)
            assert len(peer_group_ids) == 2
            peer_stage("random GroupPlan approval and application")

            peer_starter = get_starter_template("peer_review_writing")
            peer_page_count = peer_starter.page_count
            assert peer_page_count > 0
            assert "participant" in peer_starter.suggested_audience_kinds
            assert peer_starter.default_authorship_mode == "individual_author"
            assert peer_starter.default_subject_kind == "core_student"
            peer_starter_prepared = prepare_starter_template_install(
                PrepareStarterTemplateInstallRequest(
                    starter_key=peer_starter.starter_key,
                    actor=actor,
                ),
                workspace_root=root,
            )
            peer_starter_result = commit_starter_template_install(
                peer_starter_prepared,
                workspace_root=root,
            )
            assert peer_starter_result.outcome == "installed"
            assert peer_starter_result.template_id == peer_starter.template_id
            assert (
                peer_starter_result.template_version_id
                == peer_starter.template_version_id
            )
            peer_packet_prepared = prepare_packet_from_template(
                PreparePacketFromTemplateRequest(
                    packet_definition_id="packet-peer-review-issue70",
                    packet_version_id="packet-peer-review-issue70-v1",
                    packet_component_id="component-peer-review-issue70",
                    name="Issue 70 Peer Review Packet",
                    purpose="Representative installed peer-review acceptance.",
                    template_id=peer_starter.template_id,
                    template_version_id=peer_starter.template_version_id,
                    audience_kind="participant",
                    actor=actor,
                ),
                workspace_root=root,
            )
            peer_packet_result = commit_packet_from_template(
                peer_packet_prepared,
                workspace_root=root,
            )
            assert peer_packet_result.status == "active"

            peer_prepared_generation = prepare_packet_instantiation(
                PreparePacketInstantiationRequest(
                    class_id=class_id,
                    activity_id=peer_activity_id,
                    session_id=peer_session_id,
                    packet_definition_id="packet-peer-review-issue70",
                    packet_version_id="packet-peer-review-issue70-v1",
                    actor=actor,
                ),
                workspace_root=root,
            )
            assert peer_prepared_generation.ready_for_commit
            assert peer_prepared_generation.packet_instance_count == 4
            assert peer_prepared_generation.artifact_count == 4
            assert peer_prepared_generation.page_count == 4 * peer_page_count
            assert peer_prepared_generation.route_count == 4 * peer_page_count
            peer_planned_students = {
                target.target_context.participant_reference.participant_id
                for target in peer_prepared_generation.target_plans
                if target.target_context.participant_reference is not None
            }
            assert peer_planned_students == {
                "student-1",
                "student-2",
                "student-3",
                "student-4",
            }
            peer_committed_generation = commit_packet_instantiation(
                peer_prepared_generation,
                workspace_root=root,
                generation_id="generation-peer-review-issue70",
            )
            assert len(peer_committed_generation.packet_instance_ids) == 4
            assert len(peer_committed_generation.artifact_instance_ids) == 4
            assert (
                len(peer_committed_generation.artifact_page_ids)
                == 4 * peer_page_count
            )
            assert len(peer_committed_generation.route_ids) == 4 * peer_page_count

            peer_graph = load_current_record_graph(root, peer_work).graph
            peer_packet_instances = tuple(
                item
                for item in peer_graph.packet_instances
                if item.generation_id == "generation-peer-review-issue70"
            )
            assert len(peer_packet_instances) == 4
            peer_artifact_by_student: dict[str, str] = {}
            peer_group_by_student: dict[str, str] = {}
            for packet_instance in peer_packet_instances:
                target = packet_instance.target_context
                assert target.audience_kind == "participant"
                assert target.participant_reference is not None
                assert target.participant_reference.participant_kind == "core_student"
                assert target.participant_reference.owning_system == "core"
                assert target.group_id in peer_group_ids
                assert len(packet_instance.artifact_bindings) == 1
                student_id = target.participant_reference.participant_id
                peer_artifact_by_student[student_id] = (
                    packet_instance.artifact_bindings[0].artifact_instance_id
                )
                assert target.group_id is not None
                peer_group_by_student[student_id] = target.group_id
            assert set(peer_artifact_by_student) == peer_planned_students
            assert len(set(peer_artifact_by_student.values())) == 4
            assert sorted(
                tuple(peer_group_by_student.values()).count(group_id)
                for group_id in peer_group_ids
            ) == [2, 2]
            peer_stage("participant peer-review Packet instantiation")

            peer_rendered = render_packet_generation(
                RenderPacketGenerationRequest(
                    class_id=class_id,
                    activity_id=peer_activity_id,
                    generation_id="generation-peer-review-issue70",
                    actor=actor,
                ),
                workspace_root=root,
            )
            assert len(peer_rendered.packets) == 4
            assert peer_rendered.page_count == 4 * peer_page_count
            assert peer_rendered.route_count == 4 * peer_page_count
            peer_route_ids = set(peer_committed_generation.route_ids)
            peer_decoded_route_ids: set[str] = set()
            peer_pdf_paths: list[Path] = []
            for packet in peer_rendered.packets:
                assert packet.output_path.is_file()
                assert packet.page_count == peer_page_count
                assert packet.route_count == peer_page_count
                assert len(packet.payloads) == peer_page_count
                peer_pdf_paths.append(packet.output_path)
                for payload in packet.payloads:
                    locator = parse_pds2_payload(payload)
                    assert locator.module_id == "concord"
                    assert locator.class_id == class_id
                    assert locator.work_id == peer_activity_id
                    assert locator.route_id in peer_route_ids
                    peer_decoded_route_ids.add(locator.route_id)
            assert peer_decoded_route_ids == peer_route_ids
            peer_stage("real peer-review PDF and PDS2 rendering")

            peer_returned = route_scan_sources(peer_pdf_paths, workspace_root=root)
            assert peer_returned.dispatched_count == 4 * peer_page_count
            assert peer_returned.failure_count == 0
            peer_observed_routes: set[str] = set()
            peer_observed_pages: set[str] = set()
            peer_retained_scan_ids: set[str] = set()
            for source in peer_returned.sources:
                assert source.source_error is None
                assert source.retained_source is not None
                peer_retained_scan_ids.add(source.retained_source.source_scan_id)
                assert len(source.pages) == peer_page_count
                for page in source.pages:
                    assert page.status == "dispatched"
                    assert page.locator is not None
                    assert page.locator.module_id == "concord"
                    assert page.locator.class_id == class_id
                    assert page.locator.work_id == peer_activity_id
                    assert page.locator.route_id in peer_route_ids
                    peer_observed_routes.add(page.locator.route_id)
                    dispatch = page.module_result
                    assert dispatch is not None
                    assert dispatch.route_id == page.locator.route_id
                    assert (
                        dispatch.artifact_instance_id
                        in peer_artifact_by_student.values()
                    )
                    assert (
                        dispatch.artifact_page_id
                        in peer_committed_generation.artifact_page_ids
                    )
                    peer_observed_pages.add(dispatch.artifact_page_id)
            assert peer_observed_routes == peer_route_ids
            assert peer_observed_pages == set(
                peer_committed_generation.artifact_page_ids
            )
            assert len(peer_retained_scan_ids) == 4
            peer_stage("production peer-review return, retention, and dispatch")

            for student_id, artifact_id in sorted(peer_artifact_by_student.items()):
                assembled = assemble_returned_artifact(
                    AssembleArtifactRequest(
                        class_id=class_id,
                        activity_id=peer_activity_id,
                        artifact_instance_id=artifact_id,
                        expected_snapshot_revision=show_activity(
                            class_id,
                            peer_activity_id,
                            workspace_root=root,
                        ).summary.snapshot_revision,
                        actor=actor,
                    ),
                    workspace_root=root,
                )
                assert assembled.page_count == peer_page_count
                assert assembled.output_path.is_file()
                assert assembled.manifest_path.is_file()
                assert assembled.artifact_instance_id == artifact_id
                assert student_id in peer_planned_students
            peer_stage("peer-review Artifact assembly")

            peer_privacy = PrivacyPolicy(classification="teacher_and_subjects")
            for index, (student_id, artifact_id) in enumerate(
                sorted(peer_artifact_by_student.items()),
                start=1,
            ):
                review = add_artifact_review(
                    AddArtifactReviewRequest(
                        class_id=class_id,
                        activity_id=peer_activity_id,
                        artifact_instance_id=artifact_id,
                        artifact_review_id=f"review-peer-{index}",
                        readability_judgment="readable",
                        page_completeness_judgment="complete",
                        filing_judgment="correct",
                        author_judgment="confirmed",
                        subject_judgment="confirmed",
                        privacy_judgment="teacher_and_subjects",
                        relevance_judgment="relevant",
                        moderation_requirement="not_required",
                        scoring_readiness="ready",
                        review_outcome="ready",
                        privacy_policy=peer_privacy,
                        expected_snapshot_revision=show_activity(
                            class_id,
                            peer_activity_id,
                            workspace_root=root,
                        ).summary.snapshot_revision,
                        actor=actor,
                    ),
                    workspace_root=root,
                )
                assert review.artifact_review_id == f"review-peer-{index}"
                assert student_id in peer_planned_students
            peer_stage("explicit peer-review Artifact review")

            peer_scale = create_scoring_scale(
                CreateScoringScaleRequest(
                    class_id=class_id,
                    activity_id=peer_activity_id,
                    scoring_scale_id="scale-peer-review-issue70",
                    lineage_id="scale-peer-review-issue70-lineage",
                    name="Peer Review Quality",
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
                    expected_snapshot_revision=show_activity(
                        class_id,
                        peer_activity_id,
                        workspace_root=root,
                    ).summary.snapshot_revision,
                    actor=actor,
                    intended_use="Synthetic issue #70 acceptance only.",
                ),
                workspace_root=root,
            )
            peer_criterion_set = create_criterion_set(
                CreateCriterionSetRequest(
                    class_id=class_id,
                    activity_id=peer_activity_id,
                    criterion_set_id="criteria-peer-review-issue70",
                    lineage_id="criteria-peer-review-issue70-lineage",
                    name="Peer Review Criteria",
                    purpose="Synthetic issue #70 acceptance only.",
                    revision=1,
                    scope="activity_specific",
                    criterion_set_kind="local",
                    criteria=(
                        CriterionSpec(
                            criterion_id="criterion-peer-review-quality",
                            key="peer-review-quality",
                            label="Peer review quality",
                            definition="Synthetic peer-review acceptance criterion.",
                            criterion_kind="local",
                            supported_target_kinds=("core_student",),
                            default_scoring_scale_id="scale-peer-review-issue70",
                        ),
                    ),
                    status="active",
                    expected_snapshot_revision=peer_scale.commit.snapshot_revision,
                    actor=actor,
                ),
                workspace_root=root,
            )
            peer_selected = select_activity_criterion_sets(
                SelectActivityCriterionSetsRequest(
                    class_id=class_id,
                    activity_id=peer_activity_id,
                    criterion_set_ids=("criteria-peer-review-issue70",),
                    expected_snapshot_revision=(
                        peer_criterion_set.commit.snapshot_revision
                    ),
                    actor=actor,
                ),
                workspace_root=root,
            )
            assert peer_selected.criterion_set_ids == (
                "criteria-peer-review-issue70",
            )

            peer_score_ids: list[str] = []
            for index, (student_id, artifact_id) in enumerate(
                sorted(peer_artifact_by_student.items()),
                start=1,
            ):
                peer_subject = SubjectReference(
                    subject_kind="core_student",
                    subject_id=student_id,
                    owning_system="core",
                )
                peer_evidence = EvidenceReference(
                    evidence_kind="artifact_instance",
                    owning_system="concord",
                    record_id=artifact_id,
                    subject_context=(peer_subject,),
                    moderation_requirement="not_required",
                )
                peer_score_id = f"score-peer-{index}"
                peer_score = add_score(
                    AddScoreRequest(
                        class_id=class_id,
                        activity_id=peer_activity_id,
                        score_record_id=peer_score_id,
                        target_reference=ScoreTargetReference(
                            target_kind="core_student",
                            target_id=student_id,
                            owning_system="core",
                        ),
                        criterion_id="criterion-peer-review-quality",
                        scoring_scale_id="scale-peer-review-issue70",
                        disposition="scored",
                        basis="linked_evidence",
                        privacy_policy=peer_privacy,
                        expected_snapshot_revision=show_activity(
                            class_id,
                            peer_activity_id,
                            workspace_root=root,
                        ).summary.snapshot_revision,
                        actor=actor,
                        session_id=peer_session_id,
                        value="meets",
                        evidence_links=(
                            ScoreEvidenceLinkSpec(
                                score_evidence_link_id=f"link-peer-{index}",
                                evidence_reference=peer_evidence,
                                relevance_description=(
                                    "Synthetic returned peer-review artifact."
                                ),
                                subject_context=(peer_subject,),
                            ),
                        ),
                    ),
                    workspace_root=root,
                )
                assert peer_score.score_record_id == peer_score_id
                peer_score_ids.append(peer_score_id)
            peer_stage("explicit peer-review Score recording")

            peer_registration = register_concord_academic_work(
                root,
                class_id,
                peer_activity_id,
                academic_intent="formative",
                lifecycle="active",
            )
            assert peer_registration.registration.registration_revision == 1
            peer_manifest_request = GenerateAcademicResultManifestRequest(
                class_id=class_id,
                activity_id=peer_activity_id,
                expected_snapshot_revision=show_activity(
                    class_id,
                    peer_activity_id,
                    workspace_root=root,
                ).summary.snapshot_revision,
                actor=actor,
                revision_reason="initial",
            )
            peer_generated = generate_academic_result_manifest(
                peer_manifest_request,
                workspace_root=root,
            )
            assert peer_generated.disposition == "created"
            assert peer_generated.revision == 1
            assert len(peer_generated.manifest.scores) == 4
            peer_public_before = read_academic_result_manifest(
                peer_generated.content
            )
            for score_id in peer_score_ids:
                public_score = lookup_academic_result_score(
                    peer_public_before,
                    score_id,
                )
                assert public_score.score_record_id == score_id
                assert public_score.disposition == "scored"
                assert public_score.value == "meets"
            peer_publication = publish_concord_academic_results(
                peer_manifest_request,
                workspace_root=root,
            )
            assert peer_publication.disposition == "created"
            assert peer_publication.compatibility.compatible
            assert peer_publication.publication.work == peer_work
            assert (
                peer_publication.publication.record_set_revision
                == peer_generated.revision
            )
            assert (
                peer_publication.publication.manifest_digest
                == peer_generated.sha256
            )
            peer_public_after = read_academic_result_manifest(
                peer_publication.manifest_generation.content
            )
            assert peer_public_after == peer_public_before
            for score_id in peer_score_ids:
                assert lookup_academic_result_score(
                    peer_public_after,
                    score_id,
                ).score_record_id == score_id

            peer_final_graph = load_current_record_graph(root, peer_work).graph
            assert len(peer_final_graph.groups) == 2
            assert len(peer_final_graph.memberships) == 4
            assert len(peer_final_graph.packet_instances) == 4
            assert len(peer_final_graph.artifact_instances) == 4
            assert len(peer_final_graph.artifact_pages) == 4 * peer_page_count
            assert len(peer_final_graph.scan_references) == 4 * peer_page_count
            assert len(peer_final_graph.artifact_reviews) == 4
            assert len(peer_final_graph.score_records) == 4
            assert not any(
                module_name.startswith("meridian")
                for module_name in tuple(__import__("sys").modules)
            )
            peer_stage("peer-review workflow complete")
        '''
    )


def smoke(concord_wheel: Path, core_wheel: Path) -> None:
    """Run the starter workflow scenario in one fresh standalone environment."""
    if not concord_wheel.is_file():
        raise FileNotFoundError(concord_wheel)
    if not core_wheel.is_file():
        raise FileNotFoundError(core_wheel)

    with tempfile.TemporaryDirectory(prefix="concord-starter-wheel-") as raw:
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
        smoke_path = work / "starter_workflows_smoke.py"
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
