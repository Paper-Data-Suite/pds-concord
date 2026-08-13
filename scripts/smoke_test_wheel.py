"""Install built wheels in isolation and smoke-test outside the checkout."""

from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
import textwrap
import venv
from pathlib import Path


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
            AssembleArtifactRequest,
            CreateActivityContextRequest,
            CreateGroupRequest,
            GroupMemberSpec,
            UpdateSessionRequest,
            WorkflowActor,
            add_artifact_author,
            add_artifact_review,
            add_artifact_subject,
            add_memberships,
            add_moderation_record,
            assess_moderation_requirement,
            assemble_returned_artifact,
            create_activity_context,
            create_group,
            current_artifact_review,
            list_applicable_moderation_records,
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
                    scoring_orientation="evidence_only",
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
            assert not any(
                entry.name == "concord"
                for entry in entry_points(
                    group="paper_data_suite.publication_producers"
                )
            )
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
            assert len(current) == 12 and historical

        package_files_after = {
            path.relative_to(package_root)
            for path in package_root.rglob("*")
            if path.is_file()
        }
        assert package_files_after == package_files_before
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
