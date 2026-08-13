from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.classes import write_class_roster
from pds_core.rosters import create_roster
from pds_core.routing_models import ModuleWorkRef
from pds_core.workspace import ensure_workspace_root

from concord.cli_app.main import EXIT_CONFLICT, EXIT_OK, EXIT_USAGE, main
from concord.models import PrivacyPolicy
from concord.storage import load_current_record_graph
from concord.workflows import (
    ArtifactPagePlan,
    CreateActivityContextRequest,
    PrepareArtifactPagesRequest,
    WorkflowActor,
    create_activity_context,
    prepare_artifact_pages,
)


def _clock() -> datetime:
    return datetime(2026, 8, 12, 22, 30, tzinfo=timezone.utc)


def _work() -> ModuleWorkRef:
    return ModuleWorkRef(
        module_id="concord",
        class_id="class-1",
        work_id="activity-1",
    )


def _workspace(tmp_path: Path):
    root = ensure_workspace_root(tmp_path / "workspace")
    write_class_metadata_for_class(
        root,
        create_class_metadata("class-1", "2026-2027", created_at=_clock()),
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
    created = create_activity_context(
        CreateActivityContextRequest(
            class_id="class-1",
            activity_id="activity-1",
            title="Issue 29 CLI",
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
            expected_snapshot_revision=created.commit.snapshot_revision,
            actor=WorkflowActor(actor_id="teacher-1"),
            pages=(
                ArtifactPagePlan(
                    page_number=1,
                    artifact_page_id="page-1",
                    return_expected=False,
                    route_required=False,
                ),
            ),
            expected_return_status="return_not_expected",
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
        "--actor-label",
        "Synthetic Teacher",
        "--class-id",
        "class-1",
        "--activity-id",
        "activity-1",
    )


def _review_fields(
    *,
    outcome: str,
    readiness: str,
    moderation: str,
    notes: str | None = None,
) -> tuple[str, ...]:
    values = (
        "--readability-judgment",
        "readable",
        "--page-completeness-judgment",
        "complete",
        "--filing-judgment",
        "correct",
        "--author-judgment",
        "confirmed",
        "--subject-judgment",
        "confirmed",
        "--privacy-judgment",
        "teacher_restricted",
        "--relevance-judgment",
        "relevant",
        "--moderation-requirement",
        moderation,
        "--scoring-readiness",
        readiness,
        "--review-outcome",
        outcome,
    )
    return values if notes is None else (*values, "--notes", notes)


def test_review_add_list_show_and_replace_are_direct(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root, prepared = _workspace(tmp_path)
    revision = prepared.commit.snapshot_revision
    private_note = "Private teacher review note."

    assert main(
        (
            "artifact",
            "review",
            "add",
            *_common(root, revision),
            "--artifact-instance-id",
            "artifact-1",
            "--artifact-review-id",
            "review-1",
            *_review_fields(
                outcome="moderation_required",
                readiness="not_ready",
                moderation="required",
                notes=private_note,
            ),
        )
    ) == EXIT_OK
    revision += 1

    assert main(
        (
            "artifact",
            "review",
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
    assert "review-1" in output
    assert "moderation=required" in output
    assert private_note not in output

    assert main(
        (
            "artifact",
            "review",
            "show",
            "--workspace-root",
            str(root),
            "--class-id",
            "class-1",
            "--activity-id",
            "activity-1",
            "--artifact-review-id",
            "review-1",
        )
    ) == EXIT_OK
    output = capsys.readouterr().out
    assert "Artifact Review: review-1" in output
    assert private_note in output

    assert main(
        (
            "artifact",
            "review",
            "replace",
            *_common(root, revision),
            "--artifact-review-id",
            "review-1",
            "--replacement-artifact-review-id",
            "review-2",
            "--correction-id",
            "correction-review-cli",
            "--reason",
            "Moderation requirement was resolved.",
            *_review_fields(
                outcome="ready",
                readiness="ready",
                moderation="completed",
            ),
        )
    ) == EXIT_OK

    graph = load_current_record_graph(root, _work()).graph
    assert len(graph.artifact_reviews) == 2
    assert len(graph.correction_records) == 1
    assert graph.correction_records[0].correction_type == "review_correction"

    assert main(
        (
            "artifact",
            "review",
            "list",
            "--workspace-root",
            str(root),
            "--class-id",
            "class-1",
            "--activity-id",
            "activity-1",
        )
    ) == EXIT_OK
    current_output = capsys.readouterr().out
    assert "review-2" in current_output
    assert "review-1" not in current_output

    assert main(
        (
            "artifact",
            "review",
            "list",
            "--workspace-root",
            str(root),
            "--class-id",
            "class-1",
            "--activity-id",
            "activity-1",
            "--include-historical",
        )
    ) == EXIT_OK
    history_output = capsys.readouterr().out
    assert "review-1" in history_output
    assert "review-2" in history_output


def test_moderation_add_list_show_replace_and_private_rationale(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root, prepared = _workspace(tmp_path)
    revision = prepared.commit.snapshot_revision
    rationale = "Private moderation rationale."

    assert main(
        (
            "moderation",
            "add",
            *_common(root, revision),
            "--moderation-record-id",
            "moderation-1",
            "--evidence-kind",
            "artifact_instance",
            "--evidence-owner",
            "concord",
            "--evidence-record-id",
            "artifact-1",
            "--target-subject",
            "core_student,core,student-1",
            "--status",
            "accepted_with_qualification",
            "--permitted-use",
            "support_named_subject",
            "--rationale",
            rationale,
            "--qualification",
            "Use only for the named student.",
        )
    ) == EXIT_OK
    revision += 1

    assert main(
        (
            "moderation",
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
    assert "moderation-1" in output
    assert "support_named_subject" in output
    assert rationale not in output

    assert main(
        (
            "moderation",
            "show",
            "--workspace-root",
            str(root),
            "--class-id",
            "class-1",
            "--activity-id",
            "activity-1",
            "--moderation-record-id",
            "moderation-1",
        )
    ) == EXIT_OK
    output = capsys.readouterr().out
    assert rationale in output
    assert "core_student,core,student-1" in output

    assert main(
        (
            "moderation",
            "replace",
            *_common(root, revision),
            "--moderation-record-id",
            "moderation-1",
            "--replacement-moderation-record-id",
            "moderation-2",
            "--correction-id",
            "correction-moderation-cli",
            "--reason",
            "Additional corroboration changed the decision.",
            "--evidence-kind",
            "artifact_instance",
            "--evidence-owner",
            "concord",
            "--evidence-record-id",
            "artifact-1",
            "--target-subject",
            "core_student,core,student-1",
            "--status",
            "accepted",
            "--permitted-use",
            "support_named_subject",
            "--rationale",
            "Corroborated and accepted.",
        )
    ) == EXIT_OK

    graph = load_current_record_graph(root, _work()).graph
    assert len(graph.moderation_records) == 2
    assert len(graph.correction_records) == 1
    assert graph.correction_records[0].correction_type == "moderation_revision"


def test_external_evidence_cli_preserves_immutable_lineage(tmp_path: Path) -> None:
    root, prepared = _workspace(tmp_path)
    assert main(
        (
            "moderation",
            "add",
            *_common(root, prepared.commit.snapshot_revision),
            "--moderation-record-id",
            "moderation-scoreform",
            "--evidence-kind",
            "scoreform_result",
            "--evidence-owner",
            "scoreform",
            "--evidence-record-id",
            "result-1",
            "--evidence-contract-version",
            "scoreform-result-v1",
            "--immutable-source-version",
            "result-revision-7",
            "--status",
            "accepted",
            "--permitted-use",
            "corroborate_only",
            "--rationale",
            "External result may corroborate other evidence.",
        )
    ) == EXIT_OK
    graph = load_current_record_graph(root, _work()).graph
    reference = graph.moderation_records[0].target_evidence_reference
    assert reference.owning_system == "scoreform"
    assert reference.record_id == "result-1"
    assert reference.immutable_source_version == "result-revision-7"


def test_malformed_target_subject_is_usage_error(tmp_path: Path) -> None:
    root, prepared = _workspace(tmp_path)
    with pytest.raises(SystemExit) as caught:
        main(
            (
                "moderation",
                "add",
                *_common(root, prepared.commit.snapshot_revision),
                "--moderation-record-id",
                "moderation-bad",
                "--evidence-kind",
                "artifact_instance",
                "--evidence-owner",
                "concord",
                "--evidence-record-id",
                "artifact-1",
                "--target-subject",
                "core_student:student-1",
                "--status",
                "accepted",
                "--permitted-use",
                "corroborate_only",
                "--rationale",
                "Synthetic.",
            )
        )
    assert caught.value.code == EXIT_USAGE


def test_review_stale_snapshot_returns_conflict(tmp_path: Path) -> None:
    root, prepared = _workspace(tmp_path)
    assert main(
        (
            "artifact",
            "review",
            "add",
            *_common(root, prepared.commit.snapshot_revision - 1),
            "--artifact-instance-id",
            "artifact-1",
            "--artifact-review-id",
            "review-stale",
            *_review_fields(
                outcome="ready",
                readiness="ready",
                moderation="not_required",
            ),
        )
    ) == EXIT_CONFLICT


@pytest.mark.parametrize(
    "command",
    (
        ("artifact", "review", "add"),
        ("artifact", "review", "list"),
        ("artifact", "review", "show"),
        ("artifact", "review", "replace"),
        ("moderation", "add"),
        ("moderation", "list"),
        ("moderation", "show"),
        ("moderation", "replace"),
    ),
)
def test_issue29_command_help_is_read_only(
    command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    root = tmp_path / "absent-help"
    with pytest.raises(SystemExit) as caught:
        main((*command, "--workspace-root", str(root), "--help"))
    assert caught.value.code == EXIT_OK
    assert not root.exists()
