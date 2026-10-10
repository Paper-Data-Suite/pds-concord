"""Installed-wheel qualification for Concord Issue #114 feedback distribution."""

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

        import contextlib
        import hashlib
        import io
        import json
        import shutil
        import tempfile
        from dataclasses import replace
        from datetime import datetime, timezone
        from importlib import metadata
        from pathlib import Path
        from types import SimpleNamespace
        from unittest.mock import patch

        import concord
        import concord.menu_publication as publication_menu
        import concord.menu_student_feedback as feedback_menu
        import concord.workflows.activity_read as activity_read
        import concord.workflows.student_feedback_distribution as distribution
        import concord.workflows.student_feedback_distribution_opening as opening
        import pds_core
        import pypdfium2 as pdfium
        from pds_core.class_metadata import (
            create_class_metadata,
            write_class_metadata_for_class,
        )
        from pds_core.classes import write_class_roster
        from pds_core.rosters import create_roster
        from pds_core.routing_models import ModuleRecordRef, ModuleWorkRef
        from pds_core.workspace import ensure_workspace_root

        from concord.cli_app.main import EXIT_OK, main as cli_main
        from concord.menu_context import MenuSessionContext
        from concord.models import (
            Activity,
            ActorReference,
            ConcordRecordReference,
            CorrectionRecord,
            Criterion,
            CriterionSet,
            Group,
            PrivacyPolicy,
            Provenance,
            ScoreRecord,
            ScoreTargetReference,
            ScoringScale,
            ScoringScaleLevel,
            Session,
        )
        from concord.storage import commit_record_batch
        from concord.workflows import (
            FEEDBACK_AVAILABILITY_DISTRIBUTABLE,
            FEEDBACK_AVAILABILITY_NONE,
            FEEDBACK_SELECTION_ALL,
            STUDENT_FEEDBACK_INSTALL_ACTION_INSTALLED,
            STUDENT_FEEDBACK_INSTALL_ACTION_REUSED,
            execute_student_feedback_distribution,
            load_student_feedback_roster_preparation,
            open_student_feedback_distribution_directory,
            open_student_feedback_distribution_print_pdf,
            prepare_student_feedback_distribution_plan,
            preview_student_feedback_distribution,
            verify_student_feedback_distribution_directory,
        )
        from concord.workflows.activity_read import (
            activity_summary_from_context,
            load_activity_read_context,
        )
        from concord.workflows.errors import (
            ConcordWorkflowConflictError,
            ConcordWorkflowValidationError,
        )


        def stage(name: str) -> None:
            print(f"issue114 installed wheel: {name}: PASS", flush=True)


        def require_installed(module: object, distribution_name: str) -> None:
            raw = getattr(module, "__file__", None)
            if not isinstance(raw, str):
                raise AssertionError(
                    f"{distribution_name} package file is unavailable"
                )
            origin = Path(raw).resolve()
            if "site-packages" not in str(origin).casefold():
                raise AssertionError(
                    f"{distribution_name} did not import from isolated "
                    f"site-packages: {origin}"
                )


        def fingerprint(root: Path) -> tuple[tuple[str, str], ...]:
            rows = []
            for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
                if path.is_file():
                    rows.append(
                        (
                            path.relative_to(root).as_posix(),
                            hashlib.sha256(path.read_bytes()).hexdigest(),
                        )
                    )
            return tuple(rows)


        def actor() -> ActorReference:
            return ActorReference(
                actor_kind="authorized_adult",
                actor_id="teacher-issue114",
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


        def score(
            score_id: str,
            *,
            target_reference: ScoreTargetReference,
            value: int | None = 3,
            disposition: str = "scored",
            scored_at: str,
            supersedes: str | None = None,
        ) -> ScoreRecord:
            return ScoreRecord(
                score_record_id=score_id,
                activity_id="activity-1",
                target_reference=target_reference,
                criterion_id="criterion-1",
                score_kind="local",
                scoring_scale_id="scale-1",
                disposition=disposition,
                basis="professional_judgment",
                scorer=actor(),
                scored_at=scored_at,
                moderation_complete=disposition == "scored",
                privacy_policy=PrivacyPolicy(
                    classification="teacher_restricted"
                ),
                value=value,
                rationale="Teacher-only rationale must never be distributed.",
                supersedes_score_record_id=supersedes,
            )


        require_installed(concord, "pds-concord")
        require_installed(pds_core, "pds-core")
        assert metadata.version("pds-core") == "0.6.5"
        assert metadata.version("pds-concord") == "0.3.1"
        stage("isolated site-packages provenance and exact Core 0.6.5")

        with tempfile.TemporaryDirectory(
            prefix="concord-issue114-installed-"
        ) as raw:
            sandbox = Path(raw)
            root = ensure_workspace_root(sandbox / "workspace")
            exports = sandbox / "teacher-feedback"
            exports.mkdir()

            write_class_metadata_for_class(
                root,
                create_class_metadata(
                    "class-1",
                    "2026-2027",
                    created_at=datetime(2026, 10, 8, tzinfo=timezone.utc),
                ),
            )
            write_class_roster(
                root,
                create_roster(
                    "class-1",
                    (
                        {
                            "student_id": "student-private-001",
                            "last_name": "Smith",
                            "first_name": "Alex",
                            "period": "2",
                        },
                        {
                            "student_id": "student-private-002",
                            "last_name": "Smith",
                            "first_name": "Alex",
                            "period": "2",
                        },
                        {
                            "student_id": "student-private-003",
                            "last_name": (
                                "O'Connor-Williams-Santiago-Montgomery"
                            ),
                            "first_name": "Zoë",
                            "period": "2",
                        },
                        {
                            "student_id": "student-private-004",
                            "last_name": "NoFeedback",
                            "first_name": "Jordan",
                            "period": "2",
                        },
                    ),
                ),
            )

            work = ModuleWorkRef("concord", "class-1", "activity-1")
            created = provenance("2026-10-08T12:00:00+00:00")
            activity = Activity(
                activity_id="activity-1",
                class_reference=ModuleRecordRef(
                    module_id="core",
                    record_kind="class",
                    record_id="class-1",
                ),
                title="Memoir Revision",
                activity_type="project",
                scoring_orientation="local_criteria_only",
                status="active",
                created_provenance=created,
                criterion_set_ids=("criterion-set-1",),
            )
            session = Session(
                session_id="session-1",
                activity_id="activity-1",
                sequence=1,
                label="Conference",
                status="active",
                created_provenance=created,
            )
            group = Group(
                group_id="group-1",
                activity_id="activity-1",
                label="Table Group",
                status="active",
                created_provenance=created,
            )
            criterion_set = CriterionSet(
                criterion_set_id="criterion-set-1",
                lineage_id="criterion-set-lineage-1",
                name="Memoir Feedback",
                purpose="Synthetic Issue #114 qualification.",
                revision=1,
                scope="activity_specific",
                criterion_set_kind="local",
                criterion_ids=("criterion-1",),
                status="active",
                created_provenance=created,
            )
            criterion = Criterion(
                criterion_id="criterion-1",
                criterion_set_id="criterion-set-1",
                key="evidence",
                label="Use of Evidence",
                definition="Uses relevant evidence.",
                criterion_kind="local",
                supported_target_kinds=(
                    "core_student",
                    "concord_group",
                    "concord_session",
                ),
                status="active",
                created_provenance=created,
                default_scoring_scale_id="scale-1",
            )
            scale = ScoringScale(
                scoring_scale_id="scale-1",
                lineage_id="scale-lineage-1",
                name="Four Levels",
                revision=1,
                scale_type="ordinal",
                levels=(
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
                ),
                status="active",
                created_provenance=created,
            )
            old_score = score(
                "score-student-old",
                target_reference=target(
                    "core_student",
                    "student-private-001",
                ),
                value=2,
                scored_at="2026-10-08T12:10:00+00:00",
            )
            current_score = score(
                "score-student-current",
                target_reference=target(
                    "core_student",
                    "student-private-001",
                ),
                value=4,
                scored_at="2026-10-08T12:20:00+00:00",
                supersedes=old_score.score_record_id,
            )
            correction = CorrectionRecord(
                correction_id="correction-score-student",
                target_reference=ConcordRecordReference(
                    record_kind="score_record",
                    record_id=old_score.score_record_id,
                ),
                correction_type="score_revision",
                reason="Synthetic corrected judgment.",
                correcting_actor=actor(),
                corrected_at="2026-10-08T12:20:00+00:00",
                privacy_policy=PrivacyPolicy(
                    classification="teacher_restricted"
                ),
                replacement_reference=ConcordRecordReference(
                    record_kind="score_record",
                    record_id=current_score.score_record_id,
                ),
            )
            absent_score = score(
                "score-student-absent",
                target_reference=target(
                    "core_student",
                    "student-private-002",
                ),
                value=None,
                disposition="absent",
                scored_at="2026-10-08T12:21:00+00:00",
            )
            difficult_name_score = score(
                "score-student-difficult",
                target_reference=target(
                    "core_student",
                    "student-private-003",
                ),
                value=3,
                scored_at="2026-10-08T12:22:00+00:00",
            )
            group_score = score(
                "score-group",
                target_reference=target("concord_group", "group-1"),
                value=1,
                scored_at="2026-10-08T12:23:00+00:00",
            )
            session_score = score(
                "score-session",
                target_reference=target("concord_session", "session-1"),
                value=2,
                scored_at="2026-10-08T12:24:00+00:00",
            )
            initial = commit_record_batch(
                root,
                work,
                (
                    activity,
                    session,
                    group,
                    criterion_set,
                    criterion,
                    scale,
                    old_score,
                    current_score,
                    correction,
                    absent_score,
                    difficult_name_score,
                    group_score,
                    session_score,
                ),
                expected_snapshot_revision=None,
            )
            assert initial.snapshot_revision == 1
            stage("real canonical Activity Score history")

            counts = {"graph": 0, "roster": 0, "batch": 0}
            real_graph_load = activity_read.load_current_snapshot_graph
            real_roster_load = distribution.load_required_roster
            real_batch = distribution.target_score_detail_batch_from_context

            def counted_graph(*args: object, **kwargs: object):
                counts["graph"] += 1
                return real_graph_load(*args, **kwargs)

            def counted_roster(*args: object, **kwargs: object):
                counts["roster"] += 1
                return real_roster_load(*args, **kwargs)

            def counted_batch(*args: object, **kwargs: object):
                counts["batch"] += 1
                return real_batch(*args, **kwargs)

            activity_read.load_current_snapshot_graph = counted_graph
            distribution.load_required_roster = counted_roster
            distribution.target_score_detail_batch_from_context = counted_batch
            try:
                context = load_activity_read_context(root, work)
                preparation = load_student_feedback_roster_preparation(context)
            finally:
                activity_read.load_current_snapshot_graph = real_graph_load
                distribution.load_required_roster = real_roster_load
                distribution.target_score_detail_batch_from_context = real_batch

            assert counts == {"graph": 1, "roster": 1, "batch": 1}
            assert preparation.roster_count == 4
            assert preparation.distributable_count == 3
            assert preparation.no_feedback_count == 1
            assert preparation.unresolved_count == 0
            assert tuple(item.availability for item in preparation.entries) == (
                FEEDBACK_AVAILABILITY_DISTRIBUTABLE,
                FEEDBACK_AVAILABILITY_DISTRIBUTABLE,
                FEEDBACK_AVAILABILITY_DISTRIBUTABLE,
                FEEDBACK_AVAILABILITY_NONE,
            )
            assert preparation.entries[0].projection is not None
            assert preparation.entries[0].projection.results[0].value == 4
            assert preparation.entries[0].projection.results[0].value_label == (
                "Exceeding"
            )
            assert preparation.entries[1].projection is not None
            assert preparation.entries[1].projection.results[0].disposition == (
                "absent"
            )
            projected = repr(
                tuple(
                    item.projection
                    for item in preparation.entries
                    if item.projection is not None
                )
            )
            for forbidden in (
                "score-student-old",
                "score-student-current",
                "score-group",
                "score-session",
                "group-1",
                "session-1",
                "Teacher-only rationale",
            ):
                assert forbidden not in projected
            stage("one graph one roster current-head student-only projection")

            before_preview = fingerprint(root)
            preview = preview_student_feedback_distribution(
                preparation,
                selection_mode=FEEDBACK_SELECTION_ALL,
            )
            assert fingerprint(root) == before_preview
            assert preview.roster_count == 4
            assert preview.distributable_count == 3
            assert preview.no_feedback_count == 1
            assert preview.unresolved_count == 0
            assert preview.selected_for_output_count == 3
            assert preview.requires_available_only_decision
            assert tuple(
                item.student_id for item in preview.selected_entries
            ) == (
                "student-private-001",
                "student-private-002",
                "student-private-003",
            )
            stage("zero-write whole-class preview and explicit no-feedback")

            stale_destination = exports / "stale-plan"
            stale_plan = prepare_student_feedback_distribution_plan(
                preview,
                destination=stale_destination,
                authorize_available_only=True,
            )
            revised_activity = replace(
                context.activity,
                description="State advanced after preview.",
                updated_provenance=provenance(
                    "2026-10-08T12:30:00+00:00"
                ),
            )
            advanced = commit_record_batch(
                root,
                work,
                (revised_activity,),
                expected_snapshot_revision=context.snapshot_revision,
            )
            assert advanced.snapshot_revision == 2
            try:
                execute_student_feedback_distribution(
                    stale_plan,
                    confirmation="PREPARE",
                    workspace_root=root,
                    created_at="2026-10-08T12:31:00+00:00",
                )
            except ConcordWorkflowConflictError:
                pass
            else:
                raise AssertionError(
                    "stale feedback plan unexpectedly executed"
                )
            assert not stale_destination.exists()
            assert not tuple(exports.glob(".concord-feedback-staging-*"))
            stage("stale reviewed plan rejection before output mutation")

            fresh_context = load_activity_read_context(root, work)
            fresh_preparation = load_student_feedback_roster_preparation(
                fresh_context
            )
            fresh_preview = preview_student_feedback_distribution(
                fresh_preparation,
                selection_mode=FEEDBACK_SELECTION_ALL,
            )
            destination = exports / "current-feedback"
            plan = prepare_student_feedback_distribution_plan(
                fresh_preview,
                destination=destination,
                authorize_available_only=True,
            )
            assert len(plan.students) == 3
            filenames = tuple(item.filename for item in plan.students)
            assert len({name.casefold() for name in filenames}) == 3
            assert filenames[0] != filenames[1]
            for name in filenames:
                assert len(name.encode("utf-8")) <= 79
                for student_id in (
                    "student-private-001",
                    "student-private-002",
                    "student-private-003",
                    "student-private-004",
                ):
                    assert student_id not in name

            canonical_before = fingerprint(root)
            installed = execute_student_feedback_distribution(
                plan,
                confirmation="PREPARE",
                workspace_root=root,
                created_at="2026-10-08T12:40:00+00:00",
            )
            assert (
                installed.action
                == STUDENT_FEEDBACK_INSTALL_ACTION_INSTALLED
            )
            assert fingerprint(root) == canonical_before
            assert installed.directory == destination
            stage("external package creation without canonical mutation")

            verified = verify_student_feedback_distribution_directory(
                destination,
                expected_plan_digest=plan.plan_digest,
            )
            assert verified.managed_filenames == plan.output_filenames
            assert verified.selected_count == 3

            manifest_path = destination / "distribution-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            assert manifest["schema_version"] == (
                "concord_feedback_distribution_v1"
            )
            assert manifest["reviewed_plan_digest"] == plan.plan_digest
            assert manifest["selected_count"] == 3
            assert manifest["no_feedback_count"] == 1
            assert manifest["unresolved_count"] == 0
            assert [
                item["student_display_name"]
                for item in manifest["entries"]
            ] == [
                "Alex Smith",
                "Alex Smith",
                "Zoë O'Connor-Williams-Santiago-Montgomery",
            ]
            manifest_text = manifest_path.read_text(encoding="utf-8")
            index_text = (destination / "Feedback Index.html").read_text(
                encoding="utf-8"
            )
            for forbidden in (
                "student-private-001",
                "student-private-002",
                "student-private-003",
                "student-private-004",
                "score-student-old",
                "score-student-current",
                str(root),
            ):
                assert forbidden not in manifest_text
                assert forbidden not in index_text
            lowered_index = index_text.casefold()
            for forbidden in (
                "http://",
                "https://",
                "file://",
                "javascript:",
                "<script",
                "jordan nofeedback",
            ):
                assert forbidden not in lowered_index
            for entry in manifest["entries"]:
                expected_link = f'href="{entry["output_filename"]}"'
                assert expected_link in index_text

            individual_pages = 0
            for entry in manifest["entries"]:
                pdf_path = destination / entry["output_filename"]
                assert pdf_path.read_bytes().startswith(b"%PDF")
                document = pdfium.PdfDocument(pdf_path)
                try:
                    assert len(document) == entry["page_count"]
                    individual_pages += len(document)
                finally:
                    document.close()
                pdf_bytes = pdf_path.read_bytes()
                for student_id in (
                    b"student-private-001",
                    b"student-private-002",
                    b"student-private-003",
                    b"student-private-004",
                ):
                    assert student_id not in pdf_bytes

            combined = pdfium.PdfDocument(
                destination / "Print All Feedback.pdf"
            )
            try:
                assert len(combined) == individual_pages
                assert len(combined) == manifest["combined_pdf"]["page_count"]
            finally:
                combined.close()
            stage("manifest index filename and PDF package integrity")

            tampered = exports / "tampered-copy"
            shutil.copytree(destination, tampered)
            first_student_name = manifest["entries"][0]["output_filename"]
            tampered_student = tampered / first_student_name
            tampered_student.write_bytes(
                tampered_student.read_bytes() + b"tampered"
            )
            try:
                verify_student_feedback_distribution_directory(tampered)
            except ConcordWorkflowValidationError:
                pass
            else:
                raise AssertionError(
                    "tampered feedback package unexpectedly verified"
                )
            stage("tamper rejection")

            opened: list[Path] = []
            real_open = opening.open_local_path

            def fake_open(path: str | Path) -> Path:
                resolved = Path(path)
                opened.append(resolved)
                return resolved

            opening.open_local_path = fake_open
            try:
                open_student_feedback_distribution_directory(
                    destination,
                    expected_plan_digest=plan.plan_digest,
                )
                open_student_feedback_distribution_print_pdf(
                    destination,
                    expected_plan_digest=plan.plan_digest,
                )
            finally:
                opening.open_local_path = real_open
            assert opened == [
                destination,
                destination / "Print All Feedback.pdf",
            ]
            stage("verified Core local-open delegation")

            package_before = {
                path.name: (path.read_bytes(), path.stat().st_mtime_ns)
                for path in destination.iterdir()
            }
            second_revision = replace(
                fresh_context.activity,
                description="Source advanced after package creation.",
                updated_provenance=provenance(
                    "2026-10-08T12:50:00+00:00"
                ),
            )
            third = commit_record_batch(
                root,
                work,
                (second_revision,),
                expected_snapshot_revision=fresh_context.snapshot_revision,
            )
            assert third.snapshot_revision == 3
            after_source_advance = fingerprint(root)
            reused = execute_student_feedback_distribution(
                plan,
                confirmation="PREPARE",
                workspace_root=root,
                created_at="2099-01-01T00:00:00+00:00",
            )
            assert reused.action == STUDENT_FEEDBACK_INSTALL_ACTION_REUSED
            assert fingerprint(root) == after_source_advance
            package_after = {
                path.name: (path.read_bytes(), path.stat().st_mtime_ns)
                for path in destination.iterdir()
            }
            assert package_after == package_before
            stage("historical exact package reuse after source advance")

            cli_parent = sandbox / "cli-output"
            cli_parent.mkdir()
            cli_destination = cli_parent / "feedback"
            cli_stdout = io.StringIO()
            with contextlib.redirect_stdout(cli_stdout):
                result = cli_main(
                    (
                        "feedback",
                        "distribution-preview",
                        "--workspace-root",
                        str(root),
                        "--class-id",
                        "class-1",
                        "--activity-id",
                        "activity-1",
                        "--all-roster",
                        "--available-only",
                        "--destination",
                        str(cli_destination),
                    )
                )
            assert result == EXIT_OK
            cli_text = cli_stdout.getvalue()
            assert "Review digest:" in cli_text
            assert "Roster students: 4" in cli_text
            assert "Selected for distribution: 3" in cli_text
            assert "student-private-" not in cli_text
            assert fresh_context.snapshot_sha256 not in cli_text
            assert not cli_destination.exists()
            stage("installed direct CLI zero-write preview")

            latest_context = load_activity_read_context(root, work)
            summary = activity_summary_from_context(latest_context)
            menu_output = io.StringIO()
            responses = iter(("6", "b", "b"))
            with (
                patch(
                    "builtins.input",
                    side_effect=lambda _prompt="": next(responses),
                ),
                patch.object(
                    publication_menu,
                    "show_activity",
                    lambda *_args, **_kwargs: SimpleNamespace(
                        summary=summary
                    ),
                ),
                patch.object(publication_menu, "_root", lambda: root),
                patch.object(publication_menu, "clear_screen", lambda: None),
                patch.object(feedback_menu, "clear_screen", lambda: None),
                contextlib.redirect_stdout(menu_output),
            ):
                publication_menu.launch_share_results_menu(
                    summary,
                    MenuSessionContext(),
                )
            rendered_menu = menu_output.getvalue()
            assert (
                "6. Student feedback distribution (local package)"
                in rendered_menu
            )
            assert "Student Feedback Distribution" in rendered_menu
            assert (
                "1. Prepare feedback for all roster students"
                in rendered_menu
            )
            assert "5. Open a verified class print PDF" in rendered_menu
            stage("installed Activity Share menu reachability")

        print(
            "Issue #114 isolated installed-wheel acceptance: PASS",
            flush=True,
        )
        """
    )


def smoke(concord_wheel: Path, core_wheel: Path) -> None:
    """Exercise Issue #114 using only isolated installed wheel imports."""
    if not concord_wheel.is_file():
        raise FileNotFoundError(concord_wheel)
    if not core_wheel.is_file():
        raise FileNotFoundError(core_wheel)

    core_sha = _sha256(core_wheel)
    if core_sha != EXPECTED_CORE_SHA256:
        raise RuntimeError(
            "Issue #114 requires the exact released Core 0.6.5 "
            "qualification wheel."
        )

    print(
        f"Issue #114 candidate wheel SHA-256: {_sha256(concord_wheel)}",
        flush=True,
    )
    print(f"Issue #114 Core wheel SHA-256: {core_sha}", flush=True)

    with tempfile.TemporaryDirectory(prefix="concord-issue114-wheel-") as raw:
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

        smoke_path = work / "issue114_installed_acceptance.py"
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
