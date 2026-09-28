"""Run Issue #107 routine Artifact Review from isolated installed wheels."""

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

        import contextlib
        import hashlib
        import io
        import tempfile
        from datetime import date, datetime, timezone
        from importlib import metadata
        from pathlib import Path
        from unittest.mock import patch

        import concord
        import concord.menu_artifact as artifact_menu
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
        from pds_core.workspace import ensure_workspace_root

        from concord.menu_context import MenuSessionContext
        from concord.models import (
            ParticipantReference,
            PrivacyPolicy,
            SubjectReference,
        )
        from concord.storage import load_current_record_graph
        from concord.workflows import (
            AddArtifactAuthorRequest,
            AddArtifactSubjectRequest,
            ArtifactPagePlan,
            AssembleArtifactRequest,
            CreateActivityContextRequest,
            PrepareArtifactPagesRequest,
            WorkflowActor,
            add_artifact_author,
            add_artifact_subject,
            assemble_returned_artifact,
            create_activity_context,
            inspect_artifact_routine_review,
            inspect_next_artifact_review,
            list_artifacts,
            prepare_artifact_pages,
            record_routine_artifact_review,
            show_activity,
        )
        from concord.workflows.artifact_page import handle_concord_route

        CLASS_ID = "class-issue107-installed"
        ACTIVITY_ID = "activity-issue107-installed"


        def stage(name: str) -> None:
            print(f"issue107 installed wheel: {name}: PASS", flush=True)


        def require_installed(module: object, distribution: str) -> None:
            origin = Path(getattr(module, "__file__")).resolve()
            if "site-packages" not in str(origin).casefold():
                raise AssertionError(
                    f"{distribution} did not import from isolated site-packages: "
                    f"{origin}"
                )


        def clock() -> datetime:
            return datetime(2026, 9, 27, 2, 30, tzinfo=timezone.utc)


        def actor() -> WorkflowActor:
            return WorkflowActor(
                actor_id="teacher-issue107-installed",
                display_label="Synthetic Installed Review Teacher",
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


        require_installed(pds_core, "pds-core")
        require_installed(concord, "pds-concord")
        assert metadata.version("pds-core") == "0.6.3"
        assert metadata.version("pds-concord") == "0.3.0"
        stage("isolated installed provenance")

        with tempfile.TemporaryDirectory(
            prefix="concord-issue107-installed-"
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

            teacher = actor()
            state = MenuSessionContext(actor=teacher)
            created = create_activity_context(
                CreateActivityContextRequest(
                    class_id=CLASS_ID,
                    activity_id=ACTIVITY_ID,
                    title="Issue 107 Installed Routine Review",
                    activity_type="project",
                    scoring_orientation="evidence_only",
                    session_id="session-issue107-installed",
                    actor=teacher,
                    activity_status="active",
                    session_status="active",
                ),
                workspace_root=root,
                clock=clock,
            )
            revision = created.commit.snapshot_revision

            for index in (1, 2):
                artifact_id = f"artifact-{index}"
                prepared = prepare_artifact_pages(
                    PrepareArtifactPagesRequest(
                        class_id=CLASS_ID,
                        activity_id=ACTIVITY_ID,
                        artifact_instance_id=artifact_id,
                        template_version_id="template-issue107-installed",
                        artifact_category="observation",
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
                    ),
                    workspace_root=root,
                    clock=clock,
                )
                revision = prepared.commit.snapshot_revision

                retained_path = (
                    root
                    / "scans"
                    / "source"
                    / "2026-09-27"
                    / f"issue107-returned-{index}.png"
                )
                retained_path.parent.mkdir(parents=True, exist_ok=True)
                Image.new("RGB", (120, 160), (40 + index, 80, 120)).save(
                    retained_path
                )
                retained = RetainedSourceScan(
                    source_scan_id=f"scan-issue107-{index}",
                    source_filename=retained_path.name,
                    source_sha256=hashlib.sha256(
                        retained_path.read_bytes()
                    ).hexdigest(),
                    retained_source_path=retained_path,
                    retained_source_relative_path=retained_path.relative_to(
                        root
                    ).as_posix(),
                    intake_timestamp=clock(),
                    intake_date=date(2026, 9, 27),
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
                    clock=clock,
                )
                assert assembled.output_path.is_file()

                current = load_current_record_graph(
                    root,
                    ModuleWorkRef("concord", CLASS_ID, ACTIVITY_ID),
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
                    clock=clock,
                )
                revision = subject_result.commit.snapshot_revision

            work = ModuleWorkRef("concord", CLASS_ID, ACTIVITY_ID)
            before = load_current_record_graph(root, work)
            assert len(before.graph.artifact_instances) == 2
            assert len(before.graph.artifact_authors) == 2
            assert len(before.graph.artifact_subjects) == 2
            assert not before.graph.artifact_reviews
            assert not before.graph.moderation_records
            assert not before.graph.score_records

            attribution_before = (
                tuple(before.graph.artifact_authors),
                tuple(before.graph.artifact_subjects),
            )
            artifacts_before = tuple(before.graph.artifact_instances)
            stage("synthetic assembled and attributed fixture")

            first = inspect_next_artifact_review(
                CLASS_ID,
                ACTIVITY_ID,
                workspace_root=root,
            )
            assert first is not None
            assert first.artifact.artifact_instance_id == "artifact-1"
            first_context = inspect_artifact_routine_review(
                CLASS_ID,
                ACTIVITY_ID,
                "artifact-1",
                workspace_root=root,
            )
            assert first_context.eligibility.quick_review_eligible
            stage("canonical first Review and Quick eligibility")

            real_show_activity = show_activity
            real_list_artifacts = list_artifacts
            real_inspect_next = inspect_next_artifact_review
            real_inspect_routine = inspect_artifact_routine_review
            real_record_routine = record_routine_artifact_review

            def latest_bound(_activity: object) -> object:
                return real_show_activity(
                    CLASS_ID,
                    ACTIVITY_ID,
                    workspace_root=root,
                ).summary

            def list_bound(class_id: str, activity_id: str) -> object:
                return real_list_artifacts(
                    class_id,
                    activity_id,
                    workspace_root=root,
                )

            def next_bound(class_id: str, activity_id: str) -> object:
                return real_inspect_next(
                    class_id,
                    activity_id,
                    workspace_root=root,
                )

            def inspect_bound(
                class_id: str,
                activity_id: str,
                artifact_id: str,
            ) -> object:
                return real_inspect_routine(
                    class_id,
                    activity_id,
                    artifact_id,
                    workspace_root=root,
                )

            def record_bound(
                context: object,
                values: object,
                *,
                actor: object,
            ) -> object:
                return real_record_routine(
                    context,
                    values,
                    actor=actor,
                    workspace_root=root,
                    clock=clock,
                )

            def choose(
                _title: str,
                values: object,
                _labels: object,
                **_kwargs: object,
            ) -> object:
                options = tuple(values)
                if "continue" in options:
                    return "continue"
                if "ready" in options:
                    return "ready"
                raise AssertionError(f"unexpected installed selector: {options!r}")

            confirmations: list[tuple[str, tuple[str, ...]]] = []

            def confirm(
                title: str,
                expected: str,
                lines: object,
            ) -> bool:
                assert title == "Quick Artifact Review"
                assert expected == "REVIEW"
                exact = tuple(str(line) for line in lines)
                rendered = "\n".join(exact)
                for phrase in (
                    "Readability: readable",
                    "Page completeness: complete",
                    "Filing: correct",
                    "Author judgment: confirmed",
                    "Subject judgment: confirmed",
                    "Evidence privacy: teacher_restricted",
                    "Relevance: relevant",
                    "Moderation requirement: not_required",
                    "Scoring readiness: ready",
                    "Outcome: ready",
                    "Review privacy: teacher_restricted",
                ):
                    assert phrase in rendered
                confirmations.append((expected, exact))
                return True

            result_lines: list[str] = []

            def show_result(title: str, lines: object) -> None:
                result_lines.append(title)
                result_lines.extend(str(line) for line in lines)

            activity = real_show_activity(
                CLASS_ID,
                ACTIVITY_ID,
                workspace_root=root,
            ).summary
            with (
                patch.object(artifact_menu, "_latest", latest_bound),
                patch.object(artifact_menu, "list_artifacts", list_bound),
                patch.object(
                    artifact_menu,
                    "inspect_next_artifact_review",
                    next_bound,
                ),
                patch.object(
                    artifact_menu,
                    "inspect_artifact_routine_review",
                    inspect_bound,
                ),
                patch.object(
                    artifact_menu,
                    "record_routine_artifact_review",
                    record_bound,
                ),
                patch.object(artifact_menu, "select_one", choose),
                patch.object(artifact_menu, "confirm_write", confirm),
                patch.object(artifact_menu, "show_result", show_result),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                artifact_menu._review_next(activity, state)

            assert len(confirmations) == 2
            assert any(
                "No assembled Artifact is currently awaiting its first Review."
                in line
                for line in result_lines
            )
            stage("two sequential explicit teacher REVIEW confirmations")

            after = load_current_record_graph(root, work)
            assert len(after.graph.artifact_reviews) == 2
            assert tuple(after.graph.artifact_authors) == attribution_before[0]
            assert tuple(after.graph.artifact_subjects) == attribution_before[1]
            assert tuple(after.graph.artifact_instances) == artifacts_before
            assert not after.graph.moderation_records
            assert not after.graph.score_records

            by_artifact = {
                item.artifact_instance_id: item
                for item in after.graph.artifact_reviews
            }
            assert set(by_artifact) == {"artifact-1", "artifact-2"}
            for review in by_artifact.values():
                assert review.readability_judgment == "readable"
                assert review.page_completeness_judgment == "complete"
                assert review.filing_judgment == "correct"
                assert review.author_judgment == "confirmed"
                assert review.subject_judgment == "confirmed"
                assert review.relevance_judgment == "relevant"
                assert review.moderation_requirement == "not_required"
                assert review.scoring_readiness == "ready"
                assert review.review_outcome == "ready"
            assert (
                inspect_next_artifact_review(
                    CLASS_ID,
                    ACTIVITY_ID,
                    workspace_root=root,
                )
                is None
            )
            stage("Review-only canonical mutation and Review-next termination")

            detailed_calls: list[str] = []
            answers = iter(("5", "b"))
            with (
                patch(
                    "builtins.input",
                    side_effect=lambda _prompt="": next(answers),
                ),
                patch.object(artifact_menu, "clear_screen", lambda: None),
                patch.object(artifact_menu, "print_menu_header", lambda _title: None),
                patch.object(artifact_menu, "print_navigation", lambda: None),
                patch.object(
                    artifact_menu,
                    "_record_review",
                    lambda selected, _state: detailed_calls.append(
                        selected.activity_id
                    ),
                ),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                artifact_menu._launch_review_menu(activity, state)
            assert detailed_calls == [ACTIVITY_ID]
            stage("Detailed Review path remains reachable")

        print("Issue #107 isolated installed-wheel acceptance: PASS", flush=True)
        """
    )


def smoke(concord_wheel: Path, core_wheel: Path) -> None:
    """Exercise Issue #107 using only isolated installed wheel imports."""
    if not concord_wheel.is_file():
        raise FileNotFoundError(concord_wheel)
    if not core_wheel.is_file():
        raise FileNotFoundError(core_wheel)
    core_sha = _sha256(core_wheel)
    if core_sha != EXPECTED_CORE_SHA256:
        raise RuntimeError(
            "Issue #107 requires the exact released Core 0.6.3 qualification wheel."
        )

    print(f"Issue #107 candidate wheel SHA-256: {_sha256(concord_wheel)}", flush=True)
    print(f"Issue #107 Core wheel SHA-256: {core_sha}", flush=True)

    with tempfile.TemporaryDirectory(prefix="concord-issue107-wheel-") as raw:
        work = Path(raw)
        env_root = work / "venv"
        venv.EnvBuilder(with_pip=True).create(env_root)
        python = _python(env_root)
        _run([str(python), "-m", "pip", "install", str(core_wheel.resolve())], work)
        _run([str(python), "-m", "pip", "install", str(concord_wheel.resolve())], work)
        _run([str(python), "-m", "pip", "check"], work)

        smoke_path = work / "issue107_installed_acceptance.py"
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
