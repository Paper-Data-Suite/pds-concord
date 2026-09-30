"""Run Issue #108 routine Artifact scoring from isolated installed wheels."""

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
        from pds_core.scan_retention import RetainedSourceScan
        from pds_core.standards import (
            StandardDefinition,
            StandardsLibrary,
            StandardsProfile,
        )
        from pds_core.workspace import ensure_workspace_root

        from concord.models import (
            ParticipantReference,
            PrivacyPolicy,
            ScoringScaleLevel,
            SubjectReference,
        )
        from concord.storage import load_current_record_graph
        from concord.workflows import (
            AddArtifactAuthorRequest,
            AddArtifactReviewRequest,
            AddArtifactSubjectRequest,
            ArtifactPagePlan,
            AssembleArtifactRequest,
            ContinuedRoutineScorePreparationRequest,
            CreateActivityContextRequest,
            CreateCriterionSetRequest,
            CreateScoringScaleRequest,
            CriterionSpec,
            PrepareArtifactPagesRequest,
            RoutineScorePreparationRequest,
            SelectActivityCriterionSetsRequest,
            WorkflowActor,
            add_artifact_author,
            add_artifact_review,
            add_artifact_subject,
            assemble_returned_artifact,
            create_activity_context,
            create_criterion_set,
            create_scoring_scale,
            inspect_artifact_routine_scoring,
            inspect_next_score_ready_artifact,
            prepare_artifact_pages,
            prepare_next_routine_score_preview,
            prepare_routine_score_preview,
            record_prepared_routine_score,
            reload_routine_scoring_after_score,
            routine_criteria_for_target,
            routine_scale_options,
            routine_subject_context_options,
            routine_target_options,
            select_activity_criterion_sets,
        )
        from concord.workflows.artifact_page import handle_concord_route

        CLASS_ID = "class-issue108-installed"
        ACTIVITY_ID = "activity-issue108-installed"
        SESSION_ID = "session-issue108-installed"
        SCALE_ID = "scale-issue108-installed"
        SET_ID = "criterion-set-issue108-installed"
        STANDARD_CRITERION_ID = "criterion-standard"
        LOCAL_CRITERION_ID = "criterion-local"


        def stage(name: str) -> None:
            print(f"issue108 installed wheel: {name}: PASS", flush=True)


        def require_installed(module: object, distribution: str) -> None:
            origin = Path(getattr(module, "__file__")).resolve()
            if "site-packages" not in str(origin).casefold():
                raise AssertionError(
                    f"{distribution} did not import from isolated site-packages: "
                    f"{origin}"
                )


        def clock() -> datetime:
            return datetime(2026, 9, 29, 23, 30, tzinfo=timezone.utc)


        def actor() -> WorkflowActor:
            return WorkflowActor(
                actor_id="teacher-issue108-installed",
                display_label="Synthetic Installed Scoring Teacher",
                role_label="teacher",
            )


        def student_author(student_id: str) -> ParticipantReference:
            return ParticipantReference(
                participant_kind="core_student",
                participant_id=student_id,
                owning_system="core",
            )


        def student_subject(student_id: str) -> SubjectReference:
            return SubjectReference(
                subject_kind="core_student",
                subject_id=student_id,
                owning_system="core",
            )


        def standards() -> StandardsLibrary:
            return StandardsLibrary(
                standards=(
                    StandardDefinition(
                        standard_id="standard-issue108",
                        code="SYN.108",
                        source="synthetic",
                        short_name="Synthetic Issue 108 standard",
                        description=(
                            "Synthetic installed-wheel qualification standard."
                        ),
                        available_modules=("concord",),
                    ),
                ),
                profiles=(
                    StandardsProfile(
                        profile_id="profile-issue108",
                        standards=("standard-issue108",),
                        title="Synthetic Issue 108 profile",
                    ),
                ),
            )


        require_installed(pds_core, "pds-core")
        require_installed(concord, "pds-concord")
        assert metadata.version("pds-core") == "0.6.3"
        assert metadata.version("pds-concord") == "0.3.0"
        stage("isolated installed provenance")

        with tempfile.TemporaryDirectory(
            prefix="concord-issue108-installed-"
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
                            "last_name": "Student1",
                            "first_name": "Synthetic",
                            "period": "1",
                        },
                        {
                            "student_id": "student-2",
                            "last_name": "Student2",
                            "first_name": "Synthetic",
                            "period": "1",
                        },
                    ),
                ),
            )
            library = standards()
            teacher = actor()

            created = create_activity_context(
                CreateActivityContextRequest(
                    class_id=CLASS_ID,
                    activity_id=ACTIVITY_ID,
                    title="Issue 108 Installed Routine Scoring",
                    activity_type="project",
                    scoring_orientation="mixed",
                    standards_profile_id="profile-issue108",
                    focus_standard_ids=("standard-issue108",),
                    session_id=SESSION_ID,
                    actor=teacher,
                    activity_status="active",
                    session_status="active",
                ),
                workspace_root=root,
                standards_library=library,
                clock=clock,
            )
            scale = create_scoring_scale(
                CreateScoringScaleRequest(
                    class_id=CLASS_ID,
                    activity_id=ACTIVITY_ID,
                    scoring_scale_id=SCALE_ID,
                    lineage_id="scale-lineage-issue108",
                    name="Issue 108 four-level scale",
                    revision=1,
                    scale_type="ordinal",
                    levels=(
                        ScoringScaleLevel(
                            value=1,
                            label="Beginning",
                            meaning="Beginning evidence",
                            position=1,
                        ),
                        ScoringScaleLevel(
                            value=2,
                            label="Developing",
                            meaning="Developing evidence",
                            position=2,
                        ),
                        ScoringScaleLevel(
                            value=3,
                            label="Meeting",
                            meaning="Meeting the criterion",
                            position=3,
                        ),
                        ScoringScaleLevel(
                            value=4,
                            label="Exceeding",
                            meaning="Exceeding the criterion",
                            position=4,
                        ),
                    ),
                    status="active",
                    expected_snapshot_revision=(
                        created.commit.snapshot_revision
                    ),
                    actor=teacher,
                ),
                workspace_root=root,
                standards_library=library,
                clock=clock,
            )
            criterion_set = create_criterion_set(
                CreateCriterionSetRequest(
                    class_id=CLASS_ID,
                    activity_id=ACTIVITY_ID,
                    criterion_set_id=SET_ID,
                    lineage_id="criterion-lineage-issue108",
                    name="Issue 108 criteria",
                    purpose="Installed routine scoring qualification.",
                    revision=1,
                    scope="activity_specific",
                    criterion_set_kind="mixed",
                    criteria=(
                        CriterionSpec(
                            criterion_id=STANDARD_CRITERION_ID,
                            key="evidence",
                            label="Uses evidence",
                            definition="Uses evidence effectively.",
                            criterion_kind="standard_backed",
                            standard_id="standard-issue108",
                            supported_target_kinds=("core_student",),
                            default_scoring_scale_id=SCALE_ID,
                        ),
                        CriterionSpec(
                            criterion_id=LOCAL_CRITERION_ID,
                            key="reasoning",
                            label="Explains reasoning",
                            definition="Explains reasoning clearly.",
                            criterion_kind="local",
                            supported_target_kinds=("core_student",),
                            default_scoring_scale_id=SCALE_ID,
                        ),
                    ),
                    status="active",
                    standards_profile_id="profile-issue108",
                    expected_snapshot_revision=(
                        scale.commit.snapshot_revision
                    ),
                    actor=teacher,
                ),
                workspace_root=root,
                standards_library=library,
                clock=clock,
            )
            selected = select_activity_criterion_sets(
                SelectActivityCriterionSetsRequest(
                    class_id=CLASS_ID,
                    activity_id=ACTIVITY_ID,
                    criterion_set_ids=(SET_ID,),
                    expected_snapshot_revision=(
                        criterion_set.commit.snapshot_revision
                    ),
                    actor=teacher,
                ),
                workspace_root=root,
                standards_library=library,
                clock=clock,
            )
            revision = selected.commit.snapshot_revision
            stage("Activity scoring setup with valid default Scale")

            for index in (1, 2):
                artifact_id = f"artifact-{index}"
                prepared = prepare_artifact_pages(
                    PrepareArtifactPagesRequest(
                        class_id=CLASS_ID,
                        activity_id=ACTIVITY_ID,
                        artifact_instance_id=artifact_id,
                        template_version_id="template-issue108-installed",
                        artifact_category="student_work",
                        expected_snapshot_revision=revision,
                        actor=teacher,
                        pages=(
                            ArtifactPagePlan(
                                page_number=1,
                                artifact_page_id=f"page-{index}",
                            ),
                        ),
                        privacy_policy=PrivacyPolicy(
                            classification="teacher_restricted"
                        ),
                        session_id=SESSION_ID,
                    ),
                    workspace_root=root,
                    standards_library=library,
                    clock=clock,
                )

                retained_path = (
                    root
                    / "scans"
                    / "source"
                    / "2026-09-29"
                    / f"issue108-returned-{index}.png"
                )
                retained_path.parent.mkdir(parents=True, exist_ok=True)
                Image.new(
                    "RGB",
                    (120, 160),
                    (50 + index, 90, 130),
                ).save(retained_path)
                retained = RetainedSourceScan(
                    source_scan_id=f"scan-issue108-{index}",
                    source_filename=retained_path.name,
                    source_sha256=hashlib.sha256(
                        retained_path.read_bytes()
                    ).hexdigest(),
                    retained_source_path=retained_path,
                    retained_source_relative_path=retained_path.relative_to(
                        root
                    ).as_posix(),
                    intake_timestamp=clock(),
                    intake_date=date(2026, 9, 29),
                )
                payload = prepared.pages[0].pds2_payload
                assert payload is not None
                locator = parse_pds2_payload(payload)
                resolution = resolve_route_registration(root, locator)
                routed = handle_concord_route(resolution, retained, 1)
                assert routed.artifact_instance_id == artifact_id

                returned = load_current_record_graph(
                    root,
                    ModuleWorkRef("concord", CLASS_ID, ACTIVITY_ID),
                    standards_library=library,
                )
                assembled = assemble_returned_artifact(
                    AssembleArtifactRequest(
                        class_id=CLASS_ID,
                        activity_id=ACTIVITY_ID,
                        artifact_instance_id=artifact_id,
                        expected_snapshot_revision=returned.snapshot_revision,
                        actor=teacher,
                    ),
                    workspace_root=root,
                    standards_library=library,
                    clock=clock,
                )
                assert assembled.output_path.is_file()

                current = load_current_record_graph(
                    root,
                    ModuleWorkRef("concord", CLASS_ID, ACTIVITY_ID),
                    standards_library=library,
                )
                author_result = add_artifact_author(
                    AddArtifactAuthorRequest(
                        class_id=CLASS_ID,
                        activity_id=ACTIVITY_ID,
                        artifact_instance_id=artifact_id,
                        artifact_author_id=f"author-{index}",
                        author_reference=student_author(f"student-{index}"),
                        authorship_mode="individual_author",
                        attribution_status="confirmed",
                        attribution_source="teacher",
                        expected_snapshot_revision=current.snapshot_revision,
                        actor=teacher,
                    ),
                    workspace_root=root,
                    standards_library=library,
                    clock=clock,
                )
                subject_result = add_artifact_subject(
                    AddArtifactSubjectRequest(
                        class_id=CLASS_ID,
                        activity_id=ACTIVITY_ID,
                        artifact_instance_id=artifact_id,
                        artifact_subject_id=f"subject-{index}",
                        subject_reference=student_subject(f"student-{index}"),
                        subject_role="observed_participant",
                        confirmation_status="confirmed",
                        assignment_source="teacher",
                        expected_snapshot_revision=(
                            author_result.commit.snapshot_revision
                        ),
                        actor=teacher,
                    ),
                    workspace_root=root,
                    standards_library=library,
                    clock=clock,
                )
                reviewed = add_artifact_review(
                    AddArtifactReviewRequest(
                        class_id=CLASS_ID,
                        activity_id=ACTIVITY_ID,
                        artifact_instance_id=artifact_id,
                        artifact_review_id=f"review-{index}",
                        readability_judgment="readable",
                        page_completeness_judgment="complete",
                        filing_judgment="correct",
                        author_judgment="confirmed",
                        subject_judgment="confirmed",
                        privacy_judgment="teacher_restricted",
                        relevance_judgment="relevant",
                        moderation_requirement="not_required",
                        scoring_readiness="ready",
                        review_outcome="ready",
                        privacy_policy=PrivacyPolicy(
                            classification="teacher_restricted"
                        ),
                        expected_snapshot_revision=(
                            subject_result.commit.snapshot_revision
                        ),
                        actor=teacher,
                    ),
                    workspace_root=root,
                    standards_library=library,
                    clock=clock,
                )
                revision = reviewed.commit.snapshot_revision

            work = ModuleWorkRef("concord", CLASS_ID, ACTIVITY_ID)
            before = load_current_record_graph(
                root,
                work,
                standards_library=library,
            )
            reviews_before = tuple(before.graph.artifact_reviews)
            authors_before = tuple(before.graph.artifact_authors)
            subjects_before = tuple(before.graph.artifact_subjects)
            artifacts_before = tuple(before.graph.artifact_instances)
            moderation_before = tuple(before.graph.moderation_records)
            assert len(reviews_before) == 2
            assert not before.graph.score_records
            assert not before.graph.score_evidence_links
            stage("assembled attributed reviewed Artifact fixtures")

            context = inspect_artifact_routine_scoring(
                CLASS_ID,
                ACTIVITY_ID,
                "artifact-1",
                workspace_root=root,
            )
            assert context.eligibility.routine_scoring_eligible

            target_options = routine_target_options(context)
            target = next(
                item.target_reference
                for item in target_options.candidates
                if item.target_reference.target_kind == "core_student"
                and item.target_reference.target_id == "student-1"
            )
            criteria = routine_criteria_for_target(context, target)
            assert {item.criterion_id for item in criteria} == {
                STANDARD_CRITERION_ID,
                LOCAL_CRITERION_ID,
            }
            scale_options = routine_scale_options(
                context,
                target,
                STANDARD_CRITERION_ID,
            )
            assert scale_options.default_scale_status == "valid"
            assert scale_options.default_scale is not None
            assert scale_options.default_scale.scoring_scale_id == SCALE_ID
            subjects = routine_subject_context_options(
                context,
                target,
                STANDARD_CRITERION_ID,
            )
            assert subjects == (student_subject("student-1"),)
            stage(
                "explicit target Criterion default-Scale and Subject choices"
            )

            first_preview = prepare_routine_score_preview(
                context,
                RoutineScorePreparationRequest(
                    target_reference=target,
                    criterion_id=STANDARD_CRITERION_ID,
                    scoring_scale_id=SCALE_ID,
                    value=3,
                    session_id=SESSION_ID,
                    subject_context=subjects,
                    significance="primary",
                ),
            )
            assert first_preview.artifact_instance_id == "artifact-1"
            assert first_preview.value == 3
            assert first_preview.basis == "linked_evidence"
            assert first_preview.disposition == "scored"
            assert (
                first_preview.evidence.evidence_reference.record_id
                == "artifact-1"
            )
            assert (
                first_preview.evidence.relevance_description
                == "Returned Artifact evidence for this Score."
            )
            assert not first_preview.existing_current_score_ids

            first_result = record_prepared_routine_score(
                first_preview,
                actor=teacher,
                workspace_root=root,
                standards_library=library,
                clock=clock,
            )
            assert first_result.score_record_id.startswith("score-")
            assert len(first_result.score_evidence_link_ids) == 1
            assert first_result.score_evidence_link_ids[0].startswith(
                "score-link-"
            )
            stage("first explicit routine SCORE")

            continuation = reload_routine_scoring_after_score(
                first_preview,
                first_result,
                workspace_root=root,
            )
            assert continuation.target_context_retained
            assert continuation.session_context_retained
            assert continuation.retained_target_reference == target
            assert continuation.retained_session_id == SESSION_ID
            assert continuation.context.snapshot_revision >= (
                first_result.commit.snapshot_revision
            )

            next_subjects = routine_subject_context_options(
                continuation.context,
                target,
                LOCAL_CRITERION_ID,
            )
            second_preview = prepare_next_routine_score_preview(
                continuation,
                ContinuedRoutineScorePreparationRequest(
                    criterion_id=LOCAL_CRITERION_ID,
                    scoring_scale_id=SCALE_ID,
                    value=4,
                    subject_context=next_subjects,
                    significance="primary",
                ),
            )
            assert second_preview.criterion_id == LOCAL_CRITERION_ID
            assert second_preview.value == 4
            assert second_preview.snapshot_revision > (
                first_preview.snapshot_revision
            )
            second_result = record_prepared_routine_score(
                second_preview,
                actor=teacher,
                workspace_root=root,
                standards_library=library,
                clock=clock,
            )
            assert second_result.commit.snapshot_revision > (
                first_result.commit.snapshot_revision
            )
            stage("two sequential explicit Scores with canonical reload")

            next_item = inspect_next_score_ready_artifact(
                CLASS_ID,
                ACTIVITY_ID,
                after_artifact_instance_id="artifact-1",
                minimum_snapshot_revision=(
                    second_result.commit.snapshot_revision
                ),
                workspace_root=root,
            )
            assert next_item is not None
            assert next_item.artifact.artifact_instance_id == "artifact-2"
            stage(
                "deterministic navigation to another score-ready Artifact"
            )

            after = load_current_record_graph(
                root,
                work,
                standards_library=library,
            )
            assert len(after.graph.score_records) == 2
            assert len(after.graph.score_evidence_links) == 2
            assert tuple(after.graph.artifact_reviews) == reviews_before
            assert tuple(after.graph.artifact_authors) == authors_before
            assert tuple(after.graph.artifact_subjects) == subjects_before
            assert tuple(after.graph.artifact_instances) == artifacts_before
            assert tuple(after.graph.moderation_records) == moderation_before

            scores = tuple(after.graph.score_records)
            assert {item.criterion_id for item in scores} == {
                STANDARD_CRITERION_ID,
                LOCAL_CRITERION_ID,
            }
            assert {
                item.target_reference.target_id for item in scores
            } == {"student-1"}
            assert {item.value for item in scores} == {3, 4}
            assert {item.basis for item in scores} == {"linked_evidence"}
            assert {
                item.evidence_reference.record_id
                for item in after.graph.score_evidence_links
            } == {"artifact-1"}
            assert not after.graph.correction_records
            stage("Score-only canonical mutation boundaries")

            from concord import menu_scoring

            assert callable(menu_scoring.launch_score_menu)
            stage("Advanced Score recording remains reachable")

        print(
            "Issue #108 isolated installed-wheel acceptance: PASS",
            flush=True,
        )
        """
    )


def smoke(concord_wheel: Path, core_wheel: Path) -> None:
    """Exercise Issue #108 using only isolated installed wheel imports."""
    if not concord_wheel.is_file():
        raise FileNotFoundError(concord_wheel)
    if not core_wheel.is_file():
        raise FileNotFoundError(core_wheel)
    core_sha = _sha256(core_wheel)
    if core_sha != EXPECTED_CORE_SHA256:
        raise RuntimeError(
            "Issue #108 requires the exact released Core 0.6.3 qualification wheel."
        )

    print(
        f"Issue #108 candidate wheel SHA-256: {_sha256(concord_wheel)}",
        flush=True,
    )
    print(f"Issue #108 Core wheel SHA-256: {core_sha}", flush=True)

    with tempfile.TemporaryDirectory(prefix="concord-issue108-wheel-") as raw:
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

        smoke_path = work / "issue108_installed_acceptance.py"
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
