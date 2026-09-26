"""Run Issue #106 attribution batching from isolated installed wheels."""

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
        import io
        import tempfile
        from datetime import datetime, timezone
        from importlib import metadata
        from pathlib import Path
        from types import SimpleNamespace
        from unittest.mock import patch

        import concord
        import concord.menu_artifact as artifact_menu
        import pds_core
        from pds_core.class_metadata import (
            create_class_metadata,
            write_class_metadata_for_class,
        )
        from pds_core.classes import write_class_roster
        from pds_core.rosters import create_roster
        from pds_core.routing_models import ModuleWorkRef
        from pds_core.workspace import ensure_workspace_root

        from concord.menu_context import MenuSessionContext
        from concord.models import ParticipantReference, PrivacyPolicy, SubjectReference
        from concord.storage import load_current_record_graph
        from concord.workflows import (
            AddArtifactAuthorRequest,
            AddArtifactSubjectRequest,
            ArtifactPagePlan,
            CreateActivityContextRequest,
            PrepareArtifactPagesRequest,
            WorkflowActor,
            add_artifact_author,
            add_artifact_subject,
            add_artifact_subjects,
            batch_confirm_artifact_attribution,
            create_activity_context,
            inspect_artifact_attribution_review,
            list_artifact_subjects,
            list_artifacts,
            prepare_artifact_pages,
            show_activity,
        )

        CLASS_ID = "class-issue106-installed"
        ACTIVITY_ID = "activity-issue106-installed"


        def stage(name: str) -> None:
            print(f"issue106 installed wheel: {name}: PASS", flush=True)


        def require_installed(module: object, distribution: str) -> None:
            origin = Path(getattr(module, "__file__")).resolve()
            if "site-packages" not in str(origin).casefold():
                raise AssertionError(
                    f"{distribution} did not import from isolated site-packages: "
                    f"{origin}"
                )


        def clock() -> datetime:
            return datetime(2026, 9, 24, 23, 30, tzinfo=timezone.utc)


        def actor() -> WorkflowActor:
            return WorkflowActor(
                actor_id="teacher-issue106-installed",
                display_label="Synthetic Installed Attribution Teacher",
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
            prefix="concord-issue106-installed-"
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
                    tuple(
                        {
                            "student_id": f"student-{index}",
                            "last_name": f"Student{index}",
                            "first_name": "Synthetic",
                            "period": "1",
                        }
                        for index in range(1, 5)
                    ),
                ),
            )
            teacher = actor()
            state = MenuSessionContext(actor=teacher)
            created = create_activity_context(
                CreateActivityContextRequest(
                    class_id=CLASS_ID,
                    activity_id=ACTIVITY_ID,
                    title="Issue 106 Installed Attribution",
                    activity_type="project",
                    scoring_orientation="evidence_only",
                    session_id="session-issue106-installed",
                    actor=teacher,
                    activity_status="active",
                    session_status="active",
                ),
                workspace_root=root,
                clock=clock,
            )
            revision = created.commit.snapshot_revision
            for index in (1, 2):
                prepared = prepare_artifact_pages(
                    PrepareArtifactPagesRequest(
                        class_id=CLASS_ID,
                        activity_id=ACTIVITY_ID,
                        artifact_instance_id=f"artifact-{index}",
                        template_version_id="template-issue106-installed",
                        artifact_category="observation",
                        expected_snapshot_revision=revision,
                        actor=teacher,
                        expected_return_status="return_not_expected",
                        privacy_policy=PrivacyPolicy(
                            classification="teacher_restricted"
                        ),
                        pages=(
                            ArtifactPagePlan(
                                page_number=1,
                                page_kind="observation",
                                return_expected=False,
                                route_required=False,
                            ),
                        ),
                    ),
                    workspace_root=root,
                    clock=clock,
                )
                revision = prepared.commit.snapshot_revision

            for artifact_id, student_id in (
                ("artifact-1", "student-1"),
                ("artifact-2", "student-2"),
            ):
                author = add_artifact_author(
                    AddArtifactAuthorRequest(
                        class_id=CLASS_ID,
                        activity_id=ACTIVITY_ID,
                        artifact_instance_id=artifact_id,
                        artifact_author_id=f"author-{artifact_id}",
                        author_reference=student_author(student_id),
                        authorship_mode="individual_author",
                        attribution_status="proposed",
                        attribution_source="teacher",
                        expected_snapshot_revision=revision,
                        actor=teacher,
                    ),
                    workspace_root=root,
                    clock=clock,
                )
                revision = author.commit.snapshot_revision
                subject = add_artifact_subject(
                    AddArtifactSubjectRequest(
                        class_id=CLASS_ID,
                        activity_id=ACTIVITY_ID,
                        artifact_instance_id=artifact_id,
                        artifact_subject_id=f"subject-{artifact_id}",
                        subject_reference=student_subject(student_id),
                        subject_role="observed_participant",
                        confirmation_status="proposed",
                        assignment_source="teacher",
                        expected_snapshot_revision=revision,
                        actor=teacher,
                    ),
                    workspace_root=root,
                    clock=clock,
                )
                revision = subject.commit.snapshot_revision

            unresolved = add_artifact_subject(
                AddArtifactSubjectRequest(
                    class_id=CLASS_ID,
                    activity_id=ACTIVITY_ID,
                    artifact_instance_id="artifact-2",
                    artifact_subject_id="subject-unresolved-installed",
                    subject_reference=student_subject("student-3"),
                    subject_role="observed_participant",
                    confirmation_status="unresolved",
                    assignment_source="teacher",
                    expected_snapshot_revision=revision,
                    actor=teacher,
                ),
                workspace_root=root,
                clock=clock,
            )
            revision = unresolved.commit.snapshot_revision
            stage("synthetic attribution fixture")

            activity = show_activity(
                CLASS_ID,
                ACTIVITY_ID,
                workspace_root=root,
            ).summary
            work = ModuleWorkRef(
                module_id="concord",
                class_id=CLASS_ID,
                work_id=ACTIVITY_ID,
            )
            before_review = load_current_record_graph(root, work)

            real_inspect = inspect_artifact_attribution_review
            real_batch = batch_confirm_artifact_attribution

            def inspect_bound(class_id: str, activity_id: str) -> object:
                return real_inspect(
                    class_id,
                    activity_id,
                    workspace_root=root,
                )

            def batch_bound(request: object) -> object:
                return real_batch(request, workspace_root=root)

            def show_result(title: str, lines: object) -> None:
                print(title)
                for line in lines:
                    print(line)

            responses = iter(("a", "CONFIRM", "b"))
            output = io.StringIO()
            with (
                patch(
                    "builtins.input",
                    side_effect=lambda _prompt="": next(responses),
                ),
                patch.object(artifact_menu, "clear_screen", lambda: None),
                patch.object(
                    artifact_menu,
                    "inspect_artifact_attribution_review",
                    inspect_bound,
                ),
                patch.object(
                    artifact_menu,
                    "batch_confirm_artifact_attribution",
                    batch_bound,
                ),
                patch.object(artifact_menu, "show_result", show_result),
                contextlib.redirect_stdout(output),
            ):
                artifact_menu._launch_attribution_review_menu(activity, state)

            rendered = output.getvalue()
            assert "Review Attribution" in rendered
            assert "Authors: 2" in rendered
            assert "Subjects: 2" in rendered
            assert "Needs individual attention: 1" in rendered
            assert "A. Confirm all straightforward proposals" in rendered
            assert "S. Select multiple proposals" in rendered
            assert "C. Create several relationships" in rendered
            assert "E. Review / edit attribution in Advanced tools" in rendered
            assert "Authors: 0" in rendered
            assert "Subjects: 0" in rendered

            after_review = load_current_record_graph(
                root,
                work,
            )
            assert after_review.snapshot_revision == revision + 1
            assert all(
                item.attribution_status == "confirmed"
                for item in after_review.graph.artifact_authors
            )
            by_subject = {
                item.artifact_subject_id: item
                for item in after_review.graph.artifact_subjects
            }
            assert by_subject["subject-artifact-1"].confirmation_status == "confirmed"
            assert by_subject["subject-artifact-2"].confirmation_status == "confirmed"
            assert (
                by_subject["subject-unresolved-installed"].confirmation_status
                == "unresolved"
            )
            stage("teacher confirm-all batch with visible exception")

            advanced_calls = []
            advanced_answers = iter(("1", "2", "b"))
            with (
                patch(
                    "builtins.input",
                    side_effect=lambda _prompt="": next(advanced_answers),
                ),
                patch.object(artifact_menu, "clear_screen", lambda: None),
                patch.object(
                    artifact_menu,
                    "_launch_author_menu",
                    lambda selected, _state: advanced_calls.append(
                        f"author:{selected.activity_id}"
                    ),
                ),
                patch.object(
                    artifact_menu,
                    "_launch_subject_menu",
                    lambda selected, _state: advanced_calls.append(
                        f"subject:{selected.activity_id}"
                    ),
                ),
            ):
                artifact_menu._launch_advanced_attribution_menu(activity, state)
            assert advanced_calls == [
                f"author:{ACTIVITY_ID}",
                f"subject:{ACTIVITY_ID}",
            ]
            stage("advanced attribution tools reachable")

            current_activity = show_activity(
                CLASS_ID,
                ACTIVITY_ID,
                workspace_root=root,
            ).summary
            selected_artifact = next(
                item
                for item in list_artifacts(
                    CLASS_ID,
                    ACTIVITY_ID,
                    workspace_root=root,
                )
                if item.artifact_instance_id == "artifact-1"
            )
            selected_students = (
                SimpleNamespace(student_id="student-3"),
                SimpleNamespace(student_id="student-4"),
            )
            add_tokens = []
            real_multi_subject = add_artifact_subjects

            def multi_subject_bound(request: object) -> object:
                return real_multi_subject(request, workspace_root=root)

            def confirm_add(
                _title: str,
                expected: str,
                _lines: object,
            ) -> bool:
                add_tokens.append(expected)
                return True

            with (
                patch.object(
                    artifact_menu,
                    "_latest",
                    lambda _selected: current_activity,
                ),
                patch.object(
                    artifact_menu,
                    "_choose_artifact",
                    lambda *_args, **_kwargs: selected_artifact,
                ),
                patch.object(
                    artifact_menu,
                    "_require_workspace",
                    lambda: root,
                ),
                patch.object(
                    artifact_menu,
                    "choose_students",
                    lambda *_args, **_kwargs: selected_students,
                ),
                patch.object(
                    artifact_menu,
                    "_routine_multi_subject_role",
                    lambda: "general_subject",
                ),
                patch.object(
                    artifact_menu,
                    "_routine_add_status",
                    lambda **_kwargs: "confirmed",
                ),
                patch.object(
                    artifact_menu,
                    "prompt_text",
                    lambda *_args, **_kwargs: None,
                ),
                patch.object(artifact_menu, "confirm_write", confirm_add),
                patch.object(
                    artifact_menu,
                    "add_artifact_subjects",
                    multi_subject_bound,
                ),
                patch.object(artifact_menu, "show_result", show_result),
            ):
                artifact_menu._add_multiple_subjects(activity, state)

            assert add_tokens == ["ADD"]
            subjects = list_artifact_subjects(
                CLASS_ID,
                ACTIVITY_ID,
                artifact_instance_id="artifact-1",
                workspace_root=root,
            )
            added_students = {
                item.subject_reference.subject_id
                for item in subjects
                if item.subject_role == "general_subject"
            }
            assert added_students == {"student-3", "student-4"}
            stage("teacher multi-Subject add")

        print("Issue #106 isolated installed-wheel acceptance: PASS", flush=True)
        """
    )


def smoke(concord_wheel: Path, core_wheel: Path) -> None:
    """Exercise Issue #106 using only isolated installed wheel imports."""
    if not concord_wheel.is_file():
        raise FileNotFoundError(concord_wheel)
    if not core_wheel.is_file():
        raise FileNotFoundError(core_wheel)
    core_sha = _sha256(core_wheel)
    if core_sha != EXPECTED_CORE_SHA256:
        raise RuntimeError(
            "Issue #106 requires the exact released Core 0.6.3 qualification wheel."
        )

    print(f"Issue #106 candidate wheel SHA-256: {_sha256(concord_wheel)}", flush=True)
    print(f"Issue #106 Core wheel SHA-256: {core_sha}", flush=True)

    with tempfile.TemporaryDirectory(prefix="concord-issue106-wheel-") as raw:
        work = Path(raw)
        env_root = work / "venv"
        venv.EnvBuilder(with_pip=True).create(env_root)
        python = _python(env_root)
        _run([str(python), "-m", "pip", "install", str(core_wheel.resolve())], work)
        _run([str(python), "-m", "pip", "install", str(concord_wheel.resolve())], work)
        _run([str(python), "-m", "pip", "check"], work)

        smoke_path = work / "issue106_installed_acceptance.py"
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
