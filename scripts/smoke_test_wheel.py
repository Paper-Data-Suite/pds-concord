"""Install built wheels in isolation and smoke-test outside the checkout."""

from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
import textwrap
import venv
import zipfile
from email.parser import BytesParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run(
    command: list[str],
    cwd: Path,
    *,
    env: dict[str, str] | None = None,
    input_text: str | None = None,
) -> None:
    subprocess.run(
        command,
        cwd=cwd,
        check=True,
        input=input_text,
        text=True,
        env={
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
            **({} if env is None else env),
        },
    )


def _wheel_version(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        names = tuple(
            name for name in archive.namelist() if name.endswith(".dist-info/METADATA")
        )
        if len(names) != 1:
            raise RuntimeError("Concord wheel must contain exactly one METADATA file.")
        value = BytesParser().parsebytes(archive.read(names[0]))["Version"]
    if not value:
        raise RuntimeError("Concord wheel metadata does not declare a version.")
    return value


def _workflow_smoke_code() -> str:
    return textwrap.dedent(
        """
        from datetime import datetime, timezone
        from importlib.metadata import entry_points
        from pathlib import Path
        import hashlib
        import tempfile

        import concord
        from pds_core.class_metadata import (
            create_class_metadata,
            write_class_metadata_for_class,
        )
        from pds_core.classes import write_class_roster
        from pds_core.module_profiles import (
            build_module_registry,
            discover_module_profiles,
        )
        from pds_core.rosters import create_roster
        from pds_core.workspace import ensure_workspace_root

        from concord.models import (
            EffectiveContext,
            EvidenceReference,
            ParticipantReference,
            PrivacyPolicy,
            ScoreTargetReference,
            ScoringScaleLevel,
            SubjectReference,
        )
        from concord.pds_module import get_module_profile
        from concord.routing.rendering import (
            RenderArtifactPagesRequest,
            render_artifact_pages,
        )
        from concord.routing.scan_intake import route_scan_sources
        from concord.storage import (
            list_record_revisions,
            load_current_record_graph,
            load_work_snapshot,
        )
        from concord.storage_catalog import rebuild_catalog, query_catalog_records
        from concord.workflows import (
            AddArtifactAuthorRequest,
            AddArtifactReviewRequest,
            AddArtifactSubjectRequest,
            AddModerationRecordRequest,
            AddMembershipsRequest,
            AddScoreRequest,
            AssembleArtifactRequest,
            CreateActivityContextRequest,
            CreateCriterionSetRequest,
            CreateGroupRequest,
            CreateScoringScaleRequest,
            CriterionSpec,
            GroupMemberSpec,
            SelectActivityCriterionSetsRequest,
            UpdateSessionRequest,
            WorkflowActor,
            add_artifact_author,
            add_artifact_review,
            add_artifact_subject,
            add_memberships,
            add_moderation_record,
            add_score,
            assess_moderation_requirement,
            assemble_returned_artifact,
            create_activity_context,
            create_criterion_set,
            create_group,
            create_scoring_scale,
            current_artifact_review,
            list_applicable_moderation_records,
            select_activity_criterion_sets,
            update_session,
        )
        from concord.workflows.artifact_page import (
            ArtifactPagePlan,
            PrepareArtifactPagesRequest,
            prepare_artifact_pages,
        )

        package_root = Path(concord.__file__).resolve().parent
        package_files_before = {
            path.relative_to(package_root)
            for path in package_root.rglob("*")
            if path.is_file()
        }

        with tempfile.TemporaryDirectory(prefix="concord-installed-workflow-") as raw:
            root = ensure_workspace_root(Path(raw) / "workspace")
            metadata = create_class_metadata(
                "class-smoke",
                "2026-2027",
                created_at=datetime(2026, 8, 10, tzinfo=timezone.utc),
            )
            write_class_metadata_for_class(root, metadata)
            roster = create_roster(
                "class-smoke",
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
                        "first_name": "Blair",
                        "period": "1",
                    },
                ),
            )
            write_class_roster(root, roster)
            actor = WorkflowActor(actor_id="actor-smoke")
            created = create_activity_context(
                CreateActivityContextRequest(
                    class_id="class-smoke",
                    activity_id="activity-smoke",
                    title="Synthetic smoke activity",
                    activity_type="project",
                    scoring_orientation="local_criteria_only",
                    session_id="session-smoke",
                    actor=actor,
                    activity_status="active",
                    session_status="active",
                ),
                workspace_root=root,
            )
            group = create_group(
                CreateGroupRequest(
                    class_id="class-smoke",
                    activity_id="activity-smoke",
                    group_id="group-smoke",
                    label="Synthetic Group",
                    status="active",
                    expected_snapshot_revision=created.commit.snapshot_revision,
                    actor=actor,
                ),
                workspace_root=root,
            )
            context = EffectiveContext(
                activity_id="activity-smoke",
                session_ids=("session-smoke",),
            )
            memberships = add_memberships(
                AddMembershipsRequest(
                    class_id="class-smoke",
                    activity_id="activity-smoke",
                    group_id="group-smoke",
                    members=(
                        GroupMemberSpec(
                            membership_id="membership-1",
                            student_id="student-1",
                            effective_context=context,
                        ),
                        GroupMemberSpec(
                            membership_id="membership-2",
                            student_id="student-2",
                            effective_context=context,
                        ),
                    ),
                    expected_snapshot_revision=group.commit.snapshot_revision,
                    actor=actor,
                ),
                workspace_root=root,
            )
            revised = update_session(
                UpdateSessionRequest(
                    class_id="class-smoke",
                    activity_id="activity-smoke",
                    session_id="session-smoke",
                    expected_snapshot_revision=memberships.commit.snapshot_revision,
                    actor=actor,
                    notes="Synthetic installed-wheel revision.",
                ),
                workspace_root=root,
            )
            prepared = prepare_artifact_pages(
                PrepareArtifactPagesRequest(
                    class_id="class-smoke",
                    activity_id="activity-smoke",
                    artifact_instance_id="artifact-smoke",
                    template_version_id="template-smoke",
                    artifact_category="observation",
                    expected_snapshot_revision=revised.commit.snapshot_revision,
                    actor=actor,
                    pages=(
                        ArtifactPagePlan(
                            page_number=1,
                            artifact_page_id="artifact-page-smoke",
                        ),
                    ),
                    privacy_policy=PrivacyPolicy(
                        classification="teacher_restricted"
                    ),
                ),
                workspace_root=root,
            )
            profiles = discover_module_profiles()
            concord_profiles = tuple(
                profile for profile in profiles if profile.module_id == "concord"
            )
            assert len(concord_profiles) == 1
            assert concord_profiles[0] == get_module_profile()
            rendered = render_artifact_pages(
                RenderArtifactPagesRequest(
                    class_id="class-smoke",
                    activity_id="activity-smoke",
                    artifact_instance_id="artifact-smoke",
                    expected_snapshot_revision=prepared.commit.snapshot_revision,
                    actor=actor,
                ),
                workspace_root=root,
            )
            registry = build_module_registry(
                explicit_profiles=(get_module_profile(),),
                discover_installed=False,
            )
            routed = route_scan_sources(
                (rendered.output_path,),
                workspace_root=root,
                registry=registry,
            )
            assert routed.dispatched_count == 1
            assert routed.failure_count == 0
            loaded = load_current_record_graph(root, created.commit.work)
            first_snapshot, _ = load_work_snapshot(root, created.commit.work, 1)
            assert loaded.snapshot_revision == 7
            assert len(loaded.graph.groups) == 1
            assert len(loaded.graph.memberships) == 2
            assert len(loaded.graph.artifact_instances) == 1
            assert len(loaded.graph.artifact_pages) == 1
            assert len(loaded.graph.scan_references) == 1
            assert loaded.graph.artifact_pages[0].page_status == "returned"
            assert loaded.graph.artifact_instances[0].artifact_status == "returned"
            assert not loaded.graph.artifact_authors
            assert not loaded.graph.artifact_subjects
            assembled = assemble_returned_artifact(
                AssembleArtifactRequest(
                    class_id="class-smoke",
                    activity_id="activity-smoke",
                    artifact_instance_id="artifact-smoke",
                    expected_snapshot_revision=loaded.snapshot_revision,
                    actor=actor,
                ),
                workspace_root=root,
            )
            assert assembled.output_path.is_file()
            assert assembled.manifest_path.is_file()
            author = add_artifact_author(
                AddArtifactAuthorRequest(
                    class_id="class-smoke",
                    activity_id="activity-smoke",
                    artifact_instance_id="artifact-smoke",
                    artifact_author_id="author-smoke",
                    author_reference=ParticipantReference(
                        participant_kind="core_student",
                        participant_id="student-1",
                        owning_system="core",
                    ),
                    authorship_mode="observer",
                    attribution_status="confirmed",
                    attribution_source="teacher",
                    expected_snapshot_revision=loaded.snapshot_revision,
                    actor=actor,
                ),
                workspace_root=root,
            )
            subject = add_artifact_subject(
                AddArtifactSubjectRequest(
                    class_id="class-smoke",
                    activity_id="activity-smoke",
                    artifact_instance_id="artifact-smoke",
                    artifact_subject_id="subject-smoke",
                    subject_reference=SubjectReference(
                        subject_kind="core_student",
                        subject_id="student-2",
                        owning_system="core",
                    ),
                    subject_role="observed_participant",
                    confirmation_status="confirmed",
                    assignment_source="teacher",
                    expected_snapshot_revision=author.commit.snapshot_revision,
                    actor=actor,
                ),
                workspace_root=root,
            )
            loaded = load_current_record_graph(root, created.commit.work)
            assert loaded.snapshot_revision == subject.commit.snapshot_revision
            assert len(loaded.graph.artifact_authors) == 1
            assert len(loaded.graph.artifact_subjects) == 1
            assert not loaded.graph.artifact_reviews
            assert not loaded.graph.moderation_records
            assert not loaded.graph.score_records
            assert not loaded.graph.score_evidence_links

            artifacts_before_review = loaded.graph.artifact_instances
            pages_before_review = loaded.graph.artifact_pages
            scans_before_review = loaded.graph.scan_references
            authors_before_review = loaded.graph.artifact_authors
            subjects_before_review = loaded.graph.artifact_subjects
            retained_path = root / scans_before_review[0].retained_source_relative_path
            retained_digest = hashlib.sha256(retained_path.read_bytes()).hexdigest()

            review = add_artifact_review(
                AddArtifactReviewRequest(
                    class_id="class-smoke",
                    activity_id="activity-smoke",
                    artifact_instance_id="artifact-smoke",
                    artifact_review_id="review-smoke",
                    readability_judgment="readable",
                    page_completeness_judgment="complete",
                    filing_judgment="correct",
                    author_judgment="confirmed",
                    subject_judgment="confirmed",
                    privacy_judgment="teacher_restricted",
                    relevance_judgment="relevant",
                    moderation_requirement="required",
                    scoring_readiness="not_ready",
                    review_outcome="moderation_required",
                    notes="Synthetic installed-wheel Review.",
                    privacy_policy=PrivacyPolicy(
                        classification="teacher_restricted"
                    ),
                    expected_snapshot_revision=subject.commit.snapshot_revision,
                    actor=actor,
                ),
                workspace_root=root,
            )
            evidence = EvidenceReference(
                evidence_kind="artifact_instance",
                owning_system="concord",
                record_id="artifact-smoke",
                moderation_requirement="not_required",
            )
            subject_context = (
                SubjectReference(
                    subject_kind="core_student",
                    subject_id="student-2",
                    owning_system="core",
                ),
            )
            requirement = assess_moderation_requirement(
                "class-smoke",
                "activity-smoke",
                evidence,
                subject_context=subject_context,
                workspace_root=root,
            )
            assert requirement.required
            assert requirement.artifact_review_requires_moderation
            assert not requirement.evidence_reference_requires_moderation

            moderation = add_moderation_record(
                AddModerationRecordRequest(
                    class_id="class-smoke",
                    activity_id="activity-smoke",
                    moderation_record_id="moderation-smoke",
                    target_evidence_reference=evidence,
                    target_subject_references=subject_context,
                    status="accepted_with_qualification",
                    permitted_use="support_named_subject",
                    rationale="Synthetic installed-wheel Moderation.",
                    qualification="Use only for the named Subject.",
                    privacy_policy=PrivacyPolicy(
                        classification="teacher_restricted"
                    ),
                    expected_snapshot_revision=review.commit.snapshot_revision,
                    actor=actor,
                ),
                workspace_root=root,
            )
            applicable = list_applicable_moderation_records(
                "class-smoke",
                "activity-smoke",
                evidence,
                subject_context=subject_context,
                workspace_root=root,
            )
            assert [item.moderation_record_id for item in applicable] == [
                "moderation-smoke"
            ]
            current_review = current_artifact_review(
                "class-smoke",
                "activity-smoke",
                "artifact-smoke",
                workspace_root=root,
            )
            assert current_review is not None
            assert current_review.artifact_review_id == "review-smoke"

            loaded = load_current_record_graph(root, created.commit.work)
            assert loaded.snapshot_revision == moderation.commit.snapshot_revision
            assert loaded.graph.artifact_instances == artifacts_before_review
            assert loaded.graph.artifact_pages == pages_before_review
            assert loaded.graph.scan_references == scans_before_review
            assert loaded.graph.artifact_authors == authors_before_review
            assert loaded.graph.artifact_subjects == subjects_before_review
            assert len(loaded.graph.artifact_reviews) == 1
            assert len(loaded.graph.moderation_records) == 1
            assert not loaded.graph.score_records
            assert not loaded.graph.score_evidence_links
            assert hashlib.sha256(retained_path.read_bytes()).hexdigest() == (
                retained_digest
            )
            assert loaded.graph.artifact_pages[0].route_id == (
                prepared.pages[0].route_id
            )
            assert assembled.output_path.is_file()

            scale = create_scoring_scale(
                CreateScoringScaleRequest(
                    class_id="class-smoke",
                    activity_id="activity-smoke",
                    scoring_scale_id="scale-smoke",
                    lineage_id="scale-lineage-smoke",
                    name="Synthetic smoke scale",
                    revision=1,
                    scale_type="ordinal",
                    levels=(
                        ScoringScaleLevel(
                            value=1,
                            label="Beginning",
                            meaning="Beginning synthetic evidence.",
                            position=1,
                        ),
                        ScoringScaleLevel(
                            value=2,
                            label="Developing",
                            meaning="Developing synthetic evidence.",
                            position=2,
                        ),
                        ScoringScaleLevel(
                            value=3,
                            label="Secure",
                            meaning="Secure synthetic evidence.",
                            position=3,
                        ),
                    ),
                    status="active",
                    expected_snapshot_revision=moderation.commit.snapshot_revision,
                    actor=actor,
                ),
                workspace_root=root,
            )
            criterion_set = create_criterion_set(
                CreateCriterionSetRequest(
                    class_id="class-smoke",
                    activity_id="activity-smoke",
                    criterion_set_id="criterion-set-smoke",
                    lineage_id="criterion-lineage-smoke",
                    name="Synthetic smoke criteria",
                    purpose="Exercise installed-wheel Score persistence.",
                    revision=1,
                    scope="activity_specific",
                    criterion_set_kind="local",
                    criteria=(
                        CriterionSpec(
                            criterion_id="criterion-smoke",
                            key="collaboration",
                            label="Collaboration",
                            definition="Coordinates the synthetic group work.",
                            criterion_kind="local",
                            supported_target_kinds=("concord_group",),
                            default_scoring_scale_id="scale-smoke",
                        ),
                    ),
                    status="active",
                    expected_snapshot_revision=scale.commit.snapshot_revision,
                    actor=actor,
                ),
                workspace_root=root,
            )
            selected_sets = select_activity_criterion_sets(
                SelectActivityCriterionSetsRequest(
                    class_id="class-smoke",
                    activity_id="activity-smoke",
                    criterion_set_ids=("criterion-set-smoke",),
                    expected_snapshot_revision=(
                        criterion_set.commit.snapshot_revision
                    ),
                    actor=actor,
                ),
                workspace_root=root,
            )
            score = add_score(
                AddScoreRequest(
                    class_id="class-smoke",
                    activity_id="activity-smoke",
                    score_record_id="score-group-smoke",
                    target_reference=ScoreTargetReference(
                        target_kind="concord_group",
                        target_id="group-smoke",
                        owning_system="concord",
                    ),
                    criterion_id="criterion-smoke",
                    scoring_scale_id="scale-smoke",
                    disposition="scored",
                    value=3,
                    basis="professional_judgment",
                    rationale=(
                        "Synthetic installed-wheel teacher judgment for the "
                        "Group target only."
                    ),
                    privacy_policy=PrivacyPolicy(
                        classification="group_and_teacher"
                    ),
                    expected_snapshot_revision=(
                        selected_sets.commit.snapshot_revision
                    ),
                    actor=actor,
                ),
                workspace_root=root,
            )
            loaded = load_current_record_graph(root, created.commit.work)
            assert loaded.snapshot_revision == score.commit.snapshot_revision
            assert len(loaded.graph.scoring_scales) == 1
            assert len(loaded.graph.criterion_sets) == 1
            assert len(loaded.graph.criteria) == 1
            assert len(loaded.graph.score_records) == 1
            installed_score = loaded.graph.score_records[0]
            assert installed_score.score_record_id == "score-group-smoke"
            assert installed_score.target_reference.target_kind == "concord_group"
            assert installed_score.target_reference.target_id == "group-smoke"
            assert installed_score.value == 3
            assert installed_score.moderation_complete
            assert not loaded.graph.score_evidence_links
            assert not any(
                item.target_reference.target_kind == "core_student"
                for item in loaded.graph.score_records
            )
            assert loaded.graph.artifact_instances == artifacts_before_review
            assert loaded.graph.artifact_pages == pages_before_review
            assert loaded.graph.scan_references == scans_before_review
            assert loaded.graph.artifact_authors == authors_before_review
            assert loaded.graph.artifact_subjects == subjects_before_review

            publication_entries = tuple(
                entry
                for entry in entry_points(
                    group="paper_data_suite.publication_producers"
                )
                if entry.name == "concord"
            )
            assert len(publication_entries) == 1
            assert first_snapshot.snapshot_revision == 1
            assert list_record_revisions(
                root,
                created.commit.work,
                "session",
                "session-smoke",
            ) == (1, 2)
            rebuild_catalog(root, created.commit.work)
            current = query_catalog_records(
                root, created.commit.work, state="current"
            )
            historical = query_catalog_records(
                root, created.commit.work, snapshot_revision=1
            )
            assert len(current) == 16 and historical

        package_files_after = {
            path.relative_to(package_root)
            for path in package_root.rglob("*")
            if path.is_file()
        }
        assert package_files_after == package_files_before
        """
    )


def _reader_smoke_code() -> str:
    return textwrap.dedent(
        """
        import sys
        from datetime import datetime, timezone

        from pds_core.routing_models import ModuleRecordRef, ModuleWorkRef

        from concord.academic_result_artifacts import (
            AcademicResultArtifactAuthorizationDecision,
            AuthorizedAcademicResultArtifact,
            read_authorized_academic_result_artifact,
        )
        from concord.academic_result_manifest import (
            ACADEMIC_RESULT_MANIFEST_CONTRACT_VERSION,
            ACADEMIC_RESULT_MANIFEST_RECORD_TYPE,
            AcademicResultManifest,
            ActivityContextProjection,
            CriterionProjection,
            CriterionSetProjection,
            ManifestProjection,
            ManifestRecordSet,
            PrivacyProjection,
            PublicActor,
            ScaleLevelProjection,
            ScoreProjection,
            ScoringScaleProjection,
            TargetReferenceProjection,
            academic_result_manifest_to_bytes,
            with_semantic_projection_digest,
        )
        from concord.academic_result_reader import (
            list_academic_result_scores_for_target,
            lookup_academic_result_criterion,
            lookup_academic_result_scale_level,
            lookup_academic_result_score,
            lookup_academic_result_scoring_scale,
            read_academic_result_manifest,
            validate_academic_result_manifest,
        )

        actor = PublicActor(
            actor_kind="authorized_adult",
            actor_id="teacher-smoke",
            owning_system="concord",
        )
        work = ModuleWorkRef("concord", "class-smoke", "activity-smoke")
        target = TargetReferenceProjection(
            target_kind="concord_group",
            target_id="group-smoke",
            owning_system="concord",
            contract_version=None,
        )
        criterion_set = CriterionSetProjection(
            criterion_set_id="set-smoke",
            lineage_id="set-lineage-smoke",
            revision=1,
            criterion_set_kind="local",
            scope="activity_specific",
            criterion_ids=("criterion-smoke",),
            status="active",
            supersedes_criterion_set_id=None,
            standards_profile_id=None,
        )
        criterion = CriterionProjection(
            criterion_id="criterion-smoke",
            criterion_set_id="set-smoke",
            key="collaboration",
            label="Collaboration",
            definition="Synthetic installed reader criterion.",
            criterion_kind="local",
            supported_target_kinds=("concord_group",),
            status="active",
            standard_id=None,
            alignment_standard_ids=(),
            default_scoring_scale_id="scale-smoke",
        )
        scale = ScoringScaleProjection(
            scoring_scale_id="scale-smoke",
            lineage_id="scale-lineage-smoke",
            name="Type-sensitive smoke scale",
            revision=1,
            scale_type="teacher_defined",
            levels=(
                ScaleLevelProjection(
                    value=1,
                    label="Integer",
                    meaning="Integer one.",
                    position=None,
                    description=None,
                ),
                ScaleLevelProjection(
                    value=1.0,
                    label="Float",
                    meaning="Float one.",
                    position=None,
                    description=None,
                ),
                ScaleLevelProjection(
                    value="1",
                    label="Text",
                    meaning="Text one.",
                    position=None,
                    description=None,
                ),
                ScaleLevelProjection(
                    value=True,
                    label="Boolean",
                    meaning="Boolean true.",
                    position=None,
                    description=None,
                ),
            ),
            status="active",
            supersedes_scoring_scale_id=None,
        )
        score = ScoreProjection(
            score_record_id="score-smoke",
            activity_id="activity-smoke",
            session_id=None,
            target_reference=target,
            criterion_id="criterion-smoke",
            score_kind="local",
            standard_id=None,
            scoring_scale_id="scale-smoke",
            disposition="scored",
            value=True,
            basis="professional_judgment",
            scorer=actor,
            scored_at=datetime(2026, 8, 15, 17, 0, tzinfo=timezone.utc),
            moderation_complete=True,
            status_reason=None,
            supersedes_score_record_id=None,
            current_state="current",
        )
        candidate = AcademicResultManifest(
            record_type=ACADEMIC_RESULT_MANIFEST_RECORD_TYPE,
            contract_version=ACADEMIC_RESULT_MANIFEST_CONTRACT_VERSION,
            producer_module_id="concord",
            generated_at=datetime(2026, 8, 15, 17, 5, tzinfo=timezone.utc),
            record_set=ManifestRecordSet("academic_results", 1),
            work=work,
            source_activity=ModuleRecordRef(
                module_id="concord",
                record_kind="activity",
                record_id="activity-smoke",
                contract_version="concord_activity_v1",
            ),
            projection=ManifestProjection(
                source_snapshot_revision=1,
                projection_digest_algorithm="sha256",
                projection_digest="0" * 64,
                generated_by=actor,
                revision_reason="initial",
            ),
            activity_context=ActivityContextProjection(
                activity_id="activity-smoke",
                class_id="class-smoke",
                title="Synthetic installed reader Activity",
                scoring_orientation="local_criteria_only",
                standards_profile_id=None,
                focus_standard_ids=(),
                criterion_set_ids=("set-smoke",),
            ),
            criterion_sets=(criterion_set,),
            criteria=(criterion,),
            scoring_scales=(scale,),
            scores=(score,),
            score_evidence_links=(),
            moderation_records=(),
            standards_result_projection=(),
            privacy=PrivacyProjection(
                classification="teacher_restricted",
                audience_references=(),
                policy_reference=None,
                inherited_from=None,
            ),
        )
        manifest = with_semantic_projection_digest(candidate)
        raw = academic_result_manifest_to_bytes(manifest)
        restored = read_academic_result_manifest(raw)
        assert restored == manifest
        assert validate_academic_result_manifest(restored) is restored
        assert lookup_academic_result_criterion(
            restored, "criterion-smoke"
        ) == criterion
        assert lookup_academic_result_scoring_scale(
            restored, "scale-smoke"
        ) == scale
        assert lookup_academic_result_scale_level(
            restored, "scale-smoke", 1
        ).label == "Integer"
        assert lookup_academic_result_scale_level(
            restored, "scale-smoke", 1.0
        ).label == "Float"
        assert lookup_academic_result_scale_level(
            restored, "scale-smoke", "1"
        ).label == "Text"
        assert lookup_academic_result_scale_level(
            restored, "scale-smoke", True
        ).label == "Boolean"
        assert lookup_academic_result_score(restored, "score-smoke") == score
        assert list_academic_result_scores_for_target(restored, target) == (score,)

        decision = AcademicResultArtifactAuthorizationDecision("allowed")
        assert decision.status == "allowed"
        assert AuthorizedAcademicResultArtifact.__module__ == (
            "concord.academic_result_artifacts"
        )
        assert callable(read_authorized_academic_result_artifact)

        forbidden = {"scoreform", "quillan", "portia", "meridian", "vitrine"}
        loaded = {name.split(".")[0].lower() for name in sys.modules}
        assert forbidden.isdisjoint(loaded)
        """
    )


def smoke_test(concord_wheel: Path, core_wheel: Path) -> None:
    """Install exact local wheels and exercise read-only, menu, and workflow paths."""
    with tempfile.TemporaryDirectory(prefix="pds-concord-smoke-") as raw_temp:
        root = Path(raw_temp)
        environment = root / "venv"
        outside = root / "outside"
        outside.mkdir()
        venv.EnvBuilder(with_pip=True).create(environment)
        scripts = environment / ("Scripts" if os.name == "nt" else "bin")
        python = scripts / ("python.exe" if os.name == "nt" else "python")
        concord = scripts / ("concord.exe" if os.name == "nt" else "concord")
        _run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "Pillow>=11,<13",
                "qrcode>=8,<9",
                "pypdfium2>=4.30,<5",
                "zxing-cpp>=2.3,<3",
            ],
            outside,
        )
        _run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--no-index",
                "--no-deps",
                str(core_wheel.resolve()),
                str(concord_wheel.resolve()),
            ],
            outside,
        )
        _run(
            [
                str(python),
                "-c",
                (
                    "import importlib.metadata as m, concord, pds_core; "
                    "assert concord.__version__ == m.version('pds-concord'); "
                    "assert m.version('pds-core') == '0.6.0'"
                ),
            ],
            outside,
        )

        profile_workspace = root / "publication-profile-workspace"
        profile_env = {"PDS_WORKSPACE_ROOT": str(profile_workspace)}
        _run(
            [
                str(python),
                "-c",
                textwrap.dedent(
                    """
                    import sys
                    from pds_core.publication_compatibility import (
                        discover_publication_producer_profiles,
                        validate_publication_producer_profile,
                    )

                    profiles = discover_publication_producer_profiles()
                    assert len(profiles) == 1
                    profile = profiles[0]
                    assert validate_publication_producer_profile(profile) == profile
                    assert profile.module_id == "concord"
                    assert profile.display_name == "Concord"
                    assert (
                        profile.supported_core_publication_schema_versions
                        == frozenset({"1"})
                    )
                    assert (
                        profile.supported_academic_work_contract_versions
                        == frozenset({"concord_academic_work_v1"})
                    )
                    assert len(profile.publication_contracts) == 1
                    contract = profile.publication_contracts[0]
                    assert contract.publication_kind == "academic_result_set"
                    assert (
                        contract.manifest_contract_versions
                        == frozenset({"concord_academic_result_manifest_v1"})
                    )
                    assert contract.supported_capabilities == frozenset(
                        {
                            "criterion_scores",
                            "moderated_scores",
                            "standards_ratings",
                        }
                    )
                    assert contract.allows_missing_source_record is False
                    assert len(contract.source_record_contracts) == 1
                    source = contract.source_record_contracts[0]
                    assert source.record_kind == "activity"
                    assert source.contract_versions == frozenset(
                        {"concord_activity_v1"}
                    )
                    assert source.allows_unversioned is False
                    forbidden = {
                        "scoreform",
                        "quillan",
                        "portia",
                        "meridian",
                        "vitrine",
                    }
                    loaded = {name.split(".")[0].lower() for name in sys.modules}
                    assert forbidden.isdisjoint(loaded)
                    """
                ),
            ],
            outside,
            env=profile_env,
        )
        if profile_workspace.exists():
            raise RuntimeError(
                "Publication-profile discovery unexpectedly created a workspace."
            )

        reader_workspace = root / "reader-workspace"
        reader_env = {"PDS_WORKSPACE_ROOT": str(reader_workspace)}
        _run([str(python), "-c", _reader_smoke_code()], outside, env=reader_env)
        if reader_workspace.exists():
            raise RuntimeError(
                "Public reader smoke unexpectedly created a workspace."
            )

        absent_workspace = root / "read-only-workspace"
        read_only_env = {"PDS_WORKSPACE_ROOT": str(absent_workspace)}
        for command in (
            [str(concord), "--help"],
            [str(concord), "--version"],
            [str(python), "-m", "concord", "--help"],
            [str(python), "-m", "concord", "--version"],
        ):
            _run(command, outside, env=read_only_env)
        if absent_workspace.exists():
            raise RuntimeError("Read-only CLI smoke unexpectedly created a workspace.")

        for command in (
            [str(concord)],
            [str(concord), "menu"],
            [str(python), "-m", "concord"],
        ):
            _run(command, outside, env=read_only_env, input_text="q\n")
        if absent_workspace.exists():
            raise RuntimeError("Quit-only menu smoke unexpectedly created a workspace.")

        _run([str(python), "-c", _workflow_smoke_code()], outside)

        producer_workspace = root / "producer-acceptance-workspace"
        producer_workspace.mkdir()
        _run(
            [
                str(python),
                str(ROOT / "scripts" / "verify_installed_producer_acceptance.py"),
                "--workspace",
                str(producer_workspace),
                "--repository",
                str(ROOT),
                "--version",
                _wheel_version(concord_wheel),
                "--expected-core-version",
                "0.6.0",
            ],
            outside,
        )


def main() -> int:
    """Run an isolated smoke test for local Concord and Core wheels."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("concord_wheel", type=Path)
    parser.add_argument("core_wheel", type=Path)
    args = parser.parse_args()
    smoke_test(args.concord_wheel, args.core_wheel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
