"""Installed-wheel qualification for Concord Issue #123 Score analysis."""

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
        import json
        import tempfile
        from datetime import datetime, timezone
        from importlib import metadata
        from pathlib import Path

        import concord
        import pds_core
        import pypdfium2 as pdfium
        from pds_core.routing_models import ModuleRecordRef, ModuleWorkRef
        from pds_core.standards import StandardDefinition, StandardsLibrary
        from pds_core.workspace import ensure_workspace_root

        from concord.generated_paths import (
            build_human_readable_output_filename,
            validate_generated_output_token,
            validate_human_readable_output_filename,
        )
        from concord.model_validation import (
            ConcordRecordGraph,
            validate_record_graph,
        )
        from concord.models import (
            Activity,
            ActorReference,
            ArtifactInstance,
            ArtifactPage,
            ConcordRecordReference,
            CorrectionRecord,
            Criterion,
            CriterionSet,
            EvidenceReference,
            Group,
            PrivacyPolicy,
            Provenance,
            ScoreEvidenceLink,
            ScoreRecord,
            ScoreTargetReference,
            ScoringScale,
            ScoringScaleLevel,
            Session,
        )
        from concord.pds_operations import get_module_operations_profile
        from concord.pds_publication import get_publication_producer_profile
        from concord.storage_paths import work_root
        from concord.workflows import (
            CURRENT_HEAD_BOUNDARY_STATEMENT,
            REPORT_BOUNDARY_STATEMENT,
            STANDARDS_BOUNDARY_STATEMENT,
            TARGET_LOCAL_BOUNDARY_STATEMENT,
            activity_score_analysis_from_context,
            execute_prepared_score_analysis_report,
            prepare_activity_analysis_report,
            prepare_target_detail_report,
            score_history_analysis_from_context,
            target_score_detail_from_context,
        )
        from concord.workflows.activity_read import ActivityReadContext

        LONG_ACTIVITY = ("Activity " + ("Long Activity Title " * 20)).strip()
        LONG_GROUP = ("Group " + ("Long Group Label " * 20)).strip()
        LONG_STUDENT = ("Student " + ("Readable Student Name " * 20)).strip()
        LONG_CRITERION = ("Criterion " + ("Long Criterion Label " * 20)).strip()
        LONG_SCALE = ("Scale " + ("Long Scale Label " * 20)).strip()
        LONG_STANDARD = ("SYN.1-" + ("Long Standard Label " * 20)).strip()


        def stage(name: str) -> None:
            print(f"issue123 installed wheel: {name}: PASS", flush=True)


        def require_installed(module: object, distribution: str) -> None:
            raw = getattr(module, "__file__", None)
            if not isinstance(raw, str):
                raise AssertionError(f"{distribution} package file is unavailable")
            origin = Path(raw).resolve()
            if "site-packages" not in str(origin).casefold():
                raise AssertionError(
                    f"{distribution} did not import from isolated "
                    f"site-packages: {origin}"
                )


        def actor() -> ActorReference:
            return ActorReference(
                actor_kind="authorized_adult",
                actor_id="teacher_issue123",
                owning_system="concord",
                display_label_snapshot="Synthetic Qualification Teacher",
            )


        def provenance(timestamp: str) -> Provenance:
            return Provenance(
                actor=actor(),
                timestamp=timestamp,
                source_kind="manual",
            )


        def target(kind: str, record_id: str) -> ScoreTargetReference:
            return ScoreTargetReference(
                target_kind=kind,
                target_id=record_id,
                owning_system=("core" if kind == "core_student" else "concord"),
            )


        def make_score(
            score_id: str,
            *,
            target_reference: ScoreTargetReference,
            criterion_id: str,
            standard_id: str | None,
            scale_id: str,
            value: int | None = 3,
            disposition: str = "scored",
            basis: str = "professional_judgment",
            scored_at: str = "2026-10-04T13:30:00+00:00",
            supersedes: str | None = None,
        ) -> ScoreRecord:
            return ScoreRecord(
                score_record_id=score_id,
                activity_id="activity-1",
                target_reference=target_reference,
                criterion_id=criterion_id,
                score_kind=(
                    "standard_backed" if standard_id is not None else "local"
                ),
                standard_id=standard_id,
                scoring_scale_id=scale_id,
                disposition=disposition,
                value=value,
                basis=basis,
                scorer=actor(),
                scored_at=scored_at,
                rationale="Synthetic installed qualification judgment.",
                moderation_complete=disposition == "scored",
                privacy_policy=PrivacyPolicy(
                    classification="teacher_restricted"
                ),
                supersedes_score_record_id=supersedes,
            )


        def fingerprints(root: Path, excluded: Path) -> dict[str, str]:
            result: dict[str, str] = {}
            for path in sorted(item for item in root.rglob("*") if item.is_file()):
                if path.is_relative_to(excluded):
                    continue
                result[path.relative_to(root).as_posix()] = hashlib.sha256(
                    path.read_bytes()
                ).hexdigest()
            return result


        require_installed(pds_core, "pds-core")
        require_installed(concord, "pds-concord")
        assert metadata.version("pds-core") == "0.6.5"
        assert metadata.version("pds-concord") == "0.3.1"
        stage("isolated installed provenance")

        publication = get_publication_producer_profile()
        operations = get_module_operations_profile()
        assert publication.module_id == "concord"
        assert operations.module_id == "concord"
        assert operations.attention_provider is not None
        assert operations.readiness_provider is not None
        stage("publication and module-operations providers")

        with tempfile.TemporaryDirectory(
            prefix="concord-issue123-installed-"
        ) as raw:
            root = ensure_workspace_root(Path(raw) / "workspace")
            work = ModuleWorkRef("concord", "class-1", "activity-1")
            managed_work = work_root(root, work)
            managed_work.mkdir(parents=True, exist_ok=True)

            activity = Activity(
                activity_id="activity-1",
                class_reference=ModuleRecordRef(
                    module_id="core",
                    record_kind="class",
                    record_id="class-1",
                ),
                title=LONG_ACTIVITY,
                activity_type="project",
                scoring_orientation="mixed",
                status="active",
                created_provenance=provenance(
                    "2026-10-04T12:00:00+00:00"
                ),
                standards_profile_id="profile-1",
                focus_standard_ids=("standard-1",),
                criterion_set_ids=("criterion-set-1",),
            )
            session = Session(
                session_id="session-1",
                activity_id=activity.activity_id,
                sequence=1,
                label="Session One",
                status="active",
                created_provenance=provenance(
                    "2026-10-04T12:01:00+00:00"
                ),
            )
            group = Group(
                group_id="group-1",
                activity_id=activity.activity_id,
                label=LONG_GROUP,
                status="active",
                created_provenance=provenance(
                    "2026-10-04T12:02:00+00:00"
                ),
            )
            artifact = ArtifactInstance(
                artifact_instance_id="artifact-1",
                template_version_id="template-version-1",
                activity_id=activity.activity_id,
                artifact_category="student_work",
                generation_status="completed",
                expected_return_status="returned_optional",
                artifact_status="completed",
                privacy_policy=PrivacyPolicy(
                    classification="teacher_restricted"
                ),
                page_ids=("page-1",),
                created_provenance=provenance(
                    "2026-10-04T12:03:00+00:00"
                ),
            )
            page = ArtifactPage(
                artifact_page_id="page-1",
                artifact_instance_id=artifact.artifact_instance_id,
                page_number=1,
                page_kind="primary",
                return_expected=False,
                route_required=False,
                page_status="returned",
                created_provenance=provenance(
                    "2026-10-04T12:04:00+00:00"
                ),
            )
            levels = (
                ScoringScaleLevel(
                    value=1,
                    label="Beginning",
                    meaning="Beginning evidence.",
                    position=1,
                ),
                ScoringScaleLevel(
                    value=2,
                    label="Developing",
                    meaning="Developing evidence.",
                    position=2,
                ),
                ScoringScaleLevel(
                    value=3,
                    label="Meeting",
                    meaning="Meeting evidence.",
                    position=3,
                ),
                ScoringScaleLevel(
                    value=4,
                    label="Exceeding",
                    meaning="Exceeding evidence.",
                    position=4,
                ),
            )
            scale_v1 = ScoringScale(
                scoring_scale_id="scale-v1",
                lineage_id="scale-lineage-1",
                name=LONG_SCALE + " v1",
                revision=1,
                scale_type="ordinal",
                levels=levels,
                status="superseded",
                created_provenance=provenance(
                    "2026-10-04T12:05:00+00:00"
                ),
            )
            scale_v2 = ScoringScale(
                scoring_scale_id="scale-v2",
                lineage_id="scale-lineage-1",
                name=LONG_SCALE + " v2",
                revision=2,
                scale_type="ordinal",
                levels=levels,
                status="active",
                created_provenance=provenance(
                    "2026-10-04T12:06:00+00:00"
                ),
                supersedes_scoring_scale_id=scale_v1.scoring_scale_id,
            )
            criterion_set = CriterionSet(
                criterion_set_id="criterion-set-1",
                lineage_id="criterion-set-lineage-1",
                name="Synthetic Mixed Criteria",
                purpose="Issue 123 installed qualification.",
                revision=1,
                scope="activity_specific",
                criterion_set_kind="mixed",
                criterion_ids=("criterion-standard", "criterion-local"),
                status="active",
                created_provenance=provenance(
                    "2026-10-04T12:07:00+00:00"
                ),
                standards_profile_id="profile-1",
            )
            standard_criterion = Criterion(
                criterion_id="criterion-standard",
                criterion_set_id=criterion_set.criterion_set_id,
                key="standard_reasoning",
                label=LONG_CRITERION + " standard",
                definition="Synthetic standard-backed Criterion.",
                criterion_kind="standard_backed",
                supported_target_kinds=("core_student",),
                status="active",
                created_provenance=provenance(
                    "2026-10-04T12:08:00+00:00"
                ),
                standard_id="standard-1",
                default_scoring_scale_id=scale_v2.scoring_scale_id,
            )
            local_criterion = Criterion(
                criterion_id="criterion-local",
                criterion_set_id=criterion_set.criterion_set_id,
                key="local_process",
                label=LONG_CRITERION + " local",
                definition="Synthetic local Criterion.",
                criterion_kind="local",
                supported_target_kinds=(
                    "core_student",
                    "concord_group",
                    "concord_artifact_instance",
                    "concord_session",
                    "concord_activity",
                ),
                status="active",
                created_provenance=provenance(
                    "2026-10-04T12:09:00+00:00"
                ),
                default_scoring_scale_id=scale_v2.scoring_scale_id,
            )

            student = target("core_student", "student-1")
            student_two = target("core_student", "student-2")
            group_target = target("concord_group", group.group_id)
            artifact_target = target(
                "concord_artifact_instance",
                artifact.artifact_instance_id,
            )
            session_target = target("concord_session", session.session_id)
            activity_target = target("concord_activity", activity.activity_id)

            predecessor = make_score(
                "score-student-old",
                target_reference=student,
                criterion_id=standard_criterion.criterion_id,
                standard_id="standard-1",
                scale_id=scale_v1.scoring_scale_id,
                value=2,
                scored_at="2026-10-04T12:30:00+00:00",
            )
            successor = make_score(
                "score-student-current",
                target_reference=student,
                criterion_id=standard_criterion.criterion_id,
                standard_id="standard-1",
                scale_id=scale_v2.scoring_scale_id,
                value=4,
                basis="mixed_basis",
                scored_at="2026-10-04T12:40:00+00:00",
                supersedes=predecessor.score_record_id,
            )
            student_two_score = make_score(
                "score-student-two",
                target_reference=student_two,
                criterion_id=standard_criterion.criterion_id,
                standard_id="standard-1",
                scale_id=scale_v2.scoring_scale_id,
                value=3,
            )
            group_score = make_score(
                "score-group",
                target_reference=group_target,
                criterion_id=local_criterion.criterion_id,
                standard_id=None,
                scale_id=scale_v2.scoring_scale_id,
                value=2,
            )
            artifact_score = make_score(
                "score-artifact",
                target_reference=artifact_target,
                criterion_id=local_criterion.criterion_id,
                standard_id=None,
                scale_id=scale_v2.scoring_scale_id,
                disposition="deferred",
                value=None,
            )
            session_score = make_score(
                "score-session",
                target_reference=session_target,
                criterion_id=local_criterion.criterion_id,
                standard_id=None,
                scale_id=scale_v2.scoring_scale_id,
                value=3,
            )
            activity_score = make_score(
                "score-activity",
                target_reference=activity_target,
                criterion_id=local_criterion.criterion_id,
                standard_id=None,
                scale_id=scale_v2.scoring_scale_id,
                value=4,
            )
            evidence_link = ScoreEvidenceLink(
                score_evidence_link_id="score-evidence-1",
                score_record_id=successor.score_record_id,
                evidence_reference=EvidenceReference(
                    evidence_kind="artifact_instance",
                    owning_system="concord",
                    record_id=artifact.artifact_instance_id,
                ),
                relevance_description="Synthetic Evidence Link.",
                status="active",
                created_provenance=provenance(
                    "2026-10-04T12:41:00+00:00"
                ),
            )
            correction = CorrectionRecord(
                correction_id="correction-1",
                target_reference=ConcordRecordReference(
                    record_kind="score_record",
                    record_id=predecessor.score_record_id,
                ),
                correction_type="score_revision",
                reason="Synthetic corrected judgment.",
                correcting_actor=actor(),
                corrected_at="2026-10-04T12:40:00+00:00",
                privacy_policy=PrivacyPolicy(
                    classification="teacher_restricted"
                ),
                replacement_reference=ConcordRecordReference(
                    record_kind="score_record",
                    record_id=successor.score_record_id,
                ),
            )

            graph = ConcordRecordGraph(
                activities=(activity,),
                sessions=(session,),
                groups=(group,),
                artifact_instances=(artifact,),
                artifact_pages=(page,),
                criterion_sets=(criterion_set,),
                criteria=(standard_criterion, local_criterion),
                scoring_scales=(scale_v1, scale_v2),
                score_records=(
                    predecessor,
                    successor,
                    student_two_score,
                    group_score,
                    artifact_score,
                    session_score,
                    activity_score,
                ),
                score_evidence_links=(evidence_link,),
                correction_records=(correction,),
            )
            validate_record_graph(graph)
            stage("validated synthetic graph with Evidence Link")

            context = ActivityReadContext(
                root=root,
                work=work,
                snapshot_revision=17,
                snapshot_sha256="a" * 64,
                graph=graph,
                activity=activity,
            )
            library = StandardsLibrary(
                standards=(
                    StandardDefinition(
                        standard_id="standard-1",
                        code=LONG_STANDARD,
                        source="synthetic",
                        short_name="Synthetic Standard",
                        description="Synthetic Core Standard definition.",
                    ),
                )
            )
            analysis = activity_score_analysis_from_context(
                context,
                standards_library=library,
            )
            assert analysis.current_score_count == 6
            assert tuple(
                (item.target_kind, item.score_count)
                for item in analysis.target_kind_counts
            ) == (
                ("core_student", 2),
                ("concord_group", 1),
                ("concord_artifact_instance", 1),
                ("concord_session", 1),
                ("concord_activity", 1),
            )
            assert "score-student-old" not in {
                item.score_record_id for item in analysis.current_scores
            }
            assert analysis.standard_analyses[0].standard_label == LONG_STANDARD
            standard_analysis = next(
                item
                for item in analysis.criterion_analyses
                if item.criterion_id == standard_criterion.criterion_id
            )
            standard_slice = standard_analysis.slices[0]
            assert tuple(
                (
                    item.value,
                    item.count,
                    item.denominator,
                    item.percentage,
                )
                for item in standard_slice.value_distributions
            ) == ((3, 1, 2, "50.0"), (4, 1, 2, "50.0"))
            local_analysis = next(
                item
                for item in analysis.criterion_analyses
                if item.criterion_id == local_criterion.criterion_id
            )
            artifact_slice = next(
                item
                for item in local_analysis.slices
                if item.target_kind == "concord_artifact_instance"
            )
            assert tuple(
                (
                    item.disposition,
                    item.count,
                    item.denominator,
                    item.percentage,
                )
                for item in artifact_slice.disposition_distributions
            ) == (("deferred", 1, 1, "100.0"),)
            stage("overview distributions standards and target kinds")

            student_detail = target_score_detail_from_context(
                context,
                student,
                target_label_resolver=lambda _: LONG_STUDENT,
            )
            group_detail = target_score_detail_from_context(
                context,
                group_target,
            )
            assert student_detail.current_score_count == 1
            assert student_detail.results[0].value == 4
            assert group_detail.target_label == LONG_GROUP
            assert group_detail.current_score_count == 1
            stage("student and Group Target Detail")

            history = score_history_analysis_from_context(
                context,
                target_label_resolver=lambda item: (
                    LONG_STUDENT if item == student else None
                ),
            )
            lineage = next(
                item
                for item in history.lineages
                if item.root_score_record_id == predecessor.score_record_id
            )
            assert lineage.revision_count == 2
            assert lineage.current_score_record_id == successor.score_record_id
            assert tuple(item.value for item in lineage.revisions) == (2, 4)
            assert lineage.revisions[1].correction_reason == (
                "Synthetic corrected judgment."
            )
            stage("explicit Score history")

            exports_root = managed_work / "exports"
            before_files = fingerprints(root, exports_root)
            before_graph = context.graph
            fixed_clock = lambda: datetime(
                2026,
                10,
                4,
                14,
                0,
                tzinfo=timezone.utc,
            )
            activity_reports = {
                fmt: prepare_activity_analysis_report(
                    context,
                    report_format=fmt,
                    standards_library=library,
                    clock=fixed_clock,
                )
                for fmt in ("json", "csv", "pdf")
            }
            assert len(
                {item.package_token for item in activity_reports.values()}
            ) == 1
            package_token = activity_reports["pdf"].package_token
            assert validate_generated_output_token(package_token) == package_token
            assert len(package_token) == 28
            for value in (
                LONG_ACTIVITY,
                LONG_CRITERION,
                LONG_SCALE,
                LONG_STANDARD,
            ):
                assert value not in str(activity_reports["pdf"].package_path)

            installed_activity = {
                fmt: execute_prepared_score_analysis_report(prepared)
                for fmt, prepared in activity_reports.items()
            }
            assert {
                path.name
                for result in installed_activity.values()
                for path in result.output_paths
            } == {
                "report.json",
                "activity_overview.csv",
                "criterion_distributions.csv",
                "score_dispositions.csv",
                "standards_criteria.csv",
                "activity_analysis.pdf",
            }
            activity_json = json.loads(
                activity_reports["json"].output_paths[0].read_text(
                    encoding="utf-8"
                )
            )
            assert activity_json["schema_version"] == (
                "concord_activity_score_analysis_v1"
            )
            statements = activity_json["report_boundary"]["statements"]
            assert REPORT_BOUNDARY_STATEMENT in statements
            assert CURRENT_HEAD_BOUNDARY_STATEMENT in statements
            assert STANDARDS_BOUNDARY_STATEMENT in statements
            activity_pdf = pdfium.PdfDocument(
                activity_reports["pdf"].output_paths[0]
            )
            try:
                assert len(activity_pdf) >= 1
            finally:
                activity_pdf.close()
            stage("Activity JSON CSV PDF exports")

            target_reports = {
                fmt: prepare_target_detail_report(
                    context,
                    student,
                    report_format=fmt,
                    target_label_resolver=lambda _: LONG_STUDENT,
                    clock=fixed_clock,
                )
                for fmt in ("json", "pdf")
            }
            for prepared in target_reports.values():
                assert LONG_STUDENT not in str(prepared.package_path)
                assert student.target_id not in prepared.package_path.name
            installed_target = {
                fmt: execute_prepared_score_analysis_report(prepared)
                for fmt, prepared in target_reports.items()
            }
            assert {
                path.name
                for result in installed_target.values()
                for path in result.output_paths
            } == {"report.json", "target_detail.pdf"}
            target_json = json.loads(
                target_reports["json"].output_paths[0].read_text(
                    encoding="utf-8"
                )
            )
            assert target_json["target_detail"]["target_display"] == LONG_STUDENT
            assert TARGET_LOCAL_BOUNDARY_STATEMENT in (
                target_json["report_boundary"]["statements"]
            )
            target_pdf = pdfium.PdfDocument(
                target_reports["pdf"].output_paths[0]
            )
            try:
                assert len(target_pdf) >= 1
            finally:
                target_pdf.close()
            stage("Target Detail JSON and PDF exports")

            readable_one = build_human_readable_output_filename(
                display_label=LONG_STUDENT,
                extension=".pdf",
                domain="score-analysis-readable",
                identity_parts=("class-1", "activity-1", "student-1"),
            )
            readable_two = build_human_readable_output_filename(
                display_label=LONG_STUDENT,
                extension=".pdf",
                domain="score-analysis-readable",
                identity_parts=("class-1", "activity-1", "student-2"),
            )
            assert (
                validate_human_readable_output_filename(readable_one)
                == readable_one
            )
            assert len(readable_one.encode("utf-8")) <= 79
            assert "student-1" not in readable_one
            assert readable_one != readable_two
            stage("shared human-readable filename boundary")

            assert context.graph == before_graph
            assert fingerprints(root, exports_root) == before_files
            assert not (managed_work / "state").exists()
            stage("canonical and publication nonmutation")

        print(
            "Issue #123 isolated installed-wheel acceptance: PASS",
            flush=True,
        )
        """
    )


def smoke(concord_wheel: Path, core_wheel: Path) -> None:
    """Exercise Issue #123 using only isolated installed wheel imports."""
    if not concord_wheel.is_file():
        raise FileNotFoundError(concord_wheel)
    if not core_wheel.is_file():
        raise FileNotFoundError(core_wheel)
    core_sha = _sha256(core_wheel)
    if core_sha != EXPECTED_CORE_SHA256:
        raise RuntimeError(
            "Issue #123 requires the exact released Core 0.6.5 "
            "qualification wheel."
        )

    print(
        f"Issue #123 candidate wheel SHA-256: {_sha256(concord_wheel)}",
        flush=True,
    )
    print(f"Issue #123 Core wheel SHA-256: {core_sha}", flush=True)

    with tempfile.TemporaryDirectory(prefix="concord-issue123-wheel-") as raw:
        work = Path(raw)
        env_root = work / "venv"
        venv.EnvBuilder(with_pip=True).create(env_root)
        python = _python(env_root)
        _run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                str(core_wheel.resolve()),
            ],
            work,
        )
        _run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                str(concord_wheel.resolve()),
            ],
            work,
        )
        _run([str(python), "-m", "pip", "check"], work)

        smoke_path = work / "issue123_installed_acceptance.py"
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
