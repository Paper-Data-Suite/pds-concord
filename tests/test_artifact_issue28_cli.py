from __future__ import annotations

import hashlib
from datetime import date, datetime, timezone
from pathlib import Path

import pytest
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
from PIL import Image

from concord.cli_app.main import EXIT_OK, EXIT_USAGE, main
from concord.models import PrivacyPolicy
from concord.storage import load_current_record_graph
from concord.workflows import (
    CreateActivityContextRequest,
    WorkflowActor,
    create_activity_context,
)
from concord.workflows.artifact_page import (
    ArtifactPagePlan,
    PrepareArtifactPagesRequest,
    handle_concord_route,
    prepare_artifact_pages,
)


def _clock() -> datetime:
    return datetime(2026, 8, 12, 18, 0, tzinfo=timezone.utc)


def _work() -> ModuleWorkRef:
    return ModuleWorkRef("concord", "class-1", "activity-1")


def _workspace(tmp_path: Path):
    root = ensure_workspace_root(tmp_path / "workspace")
    write_class_metadata_for_class(
        root, create_class_metadata("class-1", "2026-2027", created_at=_clock())
    )
    write_class_roster(
        root,
        create_roster(
            "class-1",
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
        ),
    )
    create_activity_context(
        CreateActivityContextRequest(
            class_id="class-1",
            activity_id="activity-1",
            title="Issue 28 CLI",
            activity_type="project",
            scoring_orientation="evidence_only",
            session_id="session-1",
            actor=WorkflowActor(actor_id="teacher-1"),
        ),
        workspace_root=root,
        clock=_clock,
    )
    prepared = prepare_artifact_pages(
        PrepareArtifactPagesRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            template_version_id="template-1",
            artifact_category="observation",
            expected_snapshot_revision=1,
            actor=WorkflowActor(actor_id="teacher-1"),
            pages=(ArtifactPagePlan(page_number=1, artifact_page_id="page-1"),),
            privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
        ),
        workspace_root=root,
        clock=_clock,
    )
    return root, prepared


def _common(root: Path, expected: int) -> tuple[str, ...]:
    return (
        "--workspace-root",
        str(root),
        "--expected-snapshot",
        str(expected),
        "--actor-id",
        "teacher-1",
        "--class-id",
        "class-1",
        "--activity-id",
        "activity-1",
    )


def test_artifact_list_and_show_are_direct_read_surfaces(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root, _ = _workspace(tmp_path)
    assert main(
        (
            "artifact",
            "list",
            "--workspace-root",
            str(root),
            "--class-id",
            "class-1",
            "--activity-id",
            "activity-1",
        )
    ) == EXIT_OK
    output = capsys.readouterr().out
    assert "artifact-1" in output
    assert "authors=0" in output
    assert "subjects=0" in output

    assert main(
        (
            "artifact",
            "show",
            "--workspace-root",
            str(root),
            "--class-id",
            "class-1",
            "--activity-id",
            "activity-1",
            "--artifact-instance-id",
            "artifact-1",
        )
    ) == EXIT_OK
    output = capsys.readouterr().out
    assert "Artifact: artifact-1" in output
    assert "Privacy: teacher_restricted" in output


def test_artifact_list_does_not_create_absent_workspace(tmp_path: Path) -> None:
    root = tmp_path / "absent"
    assert main(
        (
            "artifact",
            "list",
            "--workspace-root",
            str(root),
            "--class-id",
            "class-1",
            "--activity-id",
            "activity-1",
        )
    ) == EXIT_OK
    assert not root.exists()


def test_unknown_author_cli_requires_no_fake_identity(tmp_path: Path) -> None:
    root, prepared = _workspace(tmp_path)
    assert main(
        (
            "artifact",
            "author",
            "add",
            *_common(root, prepared.commit.snapshot_revision),
            "--artifact-instance-id",
            "artifact-1",
            "--artifact-author-id",
            "author-unknown",
            "--author-kind",
            "unknown",
            "--authorship-mode",
            "unknown",
            "--attribution-status",
            "unknown",
            "--attribution-source",
            "unknown",
        )
    ) == EXIT_OK
    graph = load_current_record_graph(root, _work()).graph
    unknown = next(
        item
        for item in graph.artifact_authors
        if item.artifact_author_id == "author-unknown"
    )
    assert unknown.author_reference is None


def test_student_author_subject_update_and_replacement_cli(tmp_path: Path) -> None:
    root, prepared = _workspace(tmp_path)
    revision = prepared.commit.snapshot_revision
    assert main(
        (
            "artifact",
            "author",
            "add",
            *_common(root, revision),
            "--artifact-instance-id",
            "artifact-1",
            "--artifact-author-id",
            "author-1",
            "--author-kind",
            "core_student",
            "--author-id",
            "student-1",
            "--authorship-mode",
            "observer",
        )
    ) == EXIT_OK
    revision += 1
    assert main(
        (
            "artifact",
            "subject",
            "add",
            *_common(root, revision),
            "--artifact-instance-id",
            "artifact-1",
            "--artifact-subject-id",
            "subject-1",
            "--subject-kind",
            "core_student",
            "--subject-id",
            "student-2",
            "--subject-role",
            "observed_participant",
        )
    ) == EXIT_OK
    revision += 1
    assert main(
        (
            "artifact",
            "author",
            "update",
            *_common(root, revision),
            "--artifact-author-id",
            "author-1",
            "--attribution-status",
            "disputed",
        )
    ) == EXIT_OK
    revision += 1
    assert main(
        (
            "artifact",
            "subject",
            "replace",
            *_common(root, revision),
            "--artifact-subject-id",
            "subject-1",
            "--replacement-artifact-subject-id",
            "subject-2",
            "--correction-id",
            "correction-subject-1",
            "--reason",
            "Teacher corrected the observed participant.",
            "--subject-kind",
            "core_student",
            "--subject-id",
            "student-1",
            "--subject-role",
            "observed_participant",
        )
    ) == EXIT_OK
    graph = load_current_record_graph(root, _work()).graph
    assert len(graph.artifact_authors) == 1
    assert len(graph.artifact_subjects) == 2
    assert len(graph.correction_records) == 1


def test_author_conditional_syntax_is_usage_error(tmp_path: Path) -> None:
    root, prepared = _workspace(tmp_path)
    with pytest.raises(SystemExit) as caught:
        main(
            (
                "artifact",
                "author",
                "add",
                *_common(root, prepared.commit.snapshot_revision),
                "--artifact-instance-id",
                "artifact-1",
                "--artifact-author-id",
                "author-bad",
                "--author-kind",
                "unknown",
                "--author-id",
                "student-1",
                "--authorship-mode",
                "unknown",
            )
        )
    assert caught.value.code == EXIT_USAGE


def test_direct_assembly_uses_exact_scan_lineage(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root, prepared = _workspace(tmp_path)
    path = root / "scans" / "source" / "2026-08-12" / "returned.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (80, 120), (20, 30, 40)).save(path)
    retained = RetainedSourceScan(
        source_scan_id="scan-cli",
        source_filename="returned.png",
        source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        retained_source_path=path,
        retained_source_relative_path=path.relative_to(root).as_posix(),
        intake_timestamp=_clock(),
        intake_date=date(2026, 8, 12),
    )
    locator = parse_pds2_payload(prepared.pages[0].pds2_payload or "")
    filed = handle_concord_route(
        resolve_route_registration(root, locator),
        retained,
        1,
    )
    assert main(
        (
            "artifact",
            "assemble",
            *_common(root, filed.snapshot_revision),
            "--artifact-instance-id",
            "artifact-1",
        )
    ) == EXIT_OK
    output = capsys.readouterr().out
    assert "Assembly: assembly_" in output
    assert "Output SHA-256:" in output
def test_direct_author_subject_read_and_remaining_mutation_commands(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root, prepared = _workspace(tmp_path)
    revision = prepared.commit.snapshot_revision
    assert main(
        (
            "artifact",
            "author",
            "add",
            *_common(root, revision),
            "--artifact-instance-id",
            "artifact-1",
            "--artifact-author-id",
            "author-before",
            "--author-kind",
            "core_student",
            "--author-id",
            "student-1",
            "--authorship-mode",
            "observer",
        )
    ) == EXIT_OK
    revision += 1
    assert main(
        (
            "artifact",
            "author",
            "list",
            "--workspace-root",
            str(root),
            "--class-id",
            "class-1",
            "--activity-id",
            "activity-1",
            "--artifact-instance-id",
            "artifact-1",
        )
    ) == EXIT_OK
    assert "author-before" in capsys.readouterr().out
    assert main(
        (
            "artifact",
            "author",
            "show",
            "--workspace-root",
            str(root),
            "--class-id",
            "class-1",
            "--activity-id",
            "activity-1",
            "--artifact-author-id",
            "author-before",
        )
    ) == EXIT_OK
    assert "Completed by: Alex One" in capsys.readouterr().out
    assert main(
        (
            "artifact",
            "author",
            "replace",
            *_common(root, revision),
            "--artifact-author-id",
            "author-before",
            "--replacement-artifact-author-id",
            "author-after",
            "--correction-id",
            "correction-author-cli",
            "--reason",
            "Correct observer identity.",
            "--author-kind",
            "core_student",
            "--author-id",
            "student-2",
            "--authorship-mode",
            "observer",
        )
    ) == EXIT_OK
    revision += 1
    assert main(
        (
            "artifact",
            "subject",
            "add",
            *_common(root, revision),
            "--artifact-instance-id",
            "artifact-1",
            "--artifact-subject-id",
            "subject-cli",
            "--subject-kind",
            "core_student",
            "--subject-id",
            "student-1",
            "--subject-role",
            "observed_participant",
            "--confirmation-status",
            "proposed",
        )
    ) == EXIT_OK
    revision += 1
    assert main(
        (
            "artifact",
            "subject",
            "list",
            "--workspace-root",
            str(root),
            "--class-id",
            "class-1",
            "--activity-id",
            "activity-1",
        )
    ) == EXIT_OK
    assert "subject-cli" in capsys.readouterr().out
    assert main(
        (
            "artifact",
            "subject",
            "show",
            "--workspace-root",
            str(root),
            "--class-id",
            "class-1",
            "--activity-id",
            "activity-1",
            "--artifact-subject-id",
            "subject-cli",
        )
    ) == EXIT_OK
    assert "Artifact concerns: Alex One" in capsys.readouterr().out
    assert main(
        (
            "artifact",
            "subject",
            "update",
            *_common(root, revision),
            "--artifact-subject-id",
            "subject-cli",
            "--confirmation-status",
            "unresolved",
        )
    ) == EXIT_OK


@pytest.mark.parametrize(
    "command",
    (
        ("artifact", "list"),
        ("artifact", "show"),
        ("artifact", "assemble"),
        ("artifact", "author", "add"),
        ("artifact", "author", "list"),
        ("artifact", "author", "show"),
        ("artifact", "author", "update"),
        ("artifact", "author", "replace"),
        ("artifact", "subject", "add"),
        ("artifact", "subject", "list"),
        ("artifact", "subject", "show"),
        ("artifact", "subject", "update"),
        ("artifact", "subject", "replace"),
    ),
)
def test_issue28_direct_command_help_is_read_only(
    command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    root = tmp_path / "absent-help"
    with pytest.raises(SystemExit) as caught:
        main((*command, "--workspace-root", str(root), "--help"))
    assert caught.value.code == EXIT_OK
    assert not root.exists()
