
from __future__ import annotations

from pathlib import Path

import pytest

import concord.workflows.student_feedback_distribution_storage as storage
from concord.workflows import (
    FEEDBACK_AVAILABILITY_DISTRIBUTABLE,
    FEEDBACK_AVAILABILITY_NONE,
    FEEDBACK_SELECTION_ALL,
    SCORE_ANALYSIS_BASIS,
    STUDENT_FEEDBACK_BOUNDARY_STATEMENT,
    STUDENT_FEEDBACK_INSTALL_ACTION_INSTALLED,
    STUDENT_FEEDBACK_INSTALL_ACTION_REUSED,
    STUDENT_FEEDBACK_PREPARATION_SCOPE,
    InstalledStudentFeedbackDistribution,
    StudentFeedbackDistributionInstallError,
    StudentFeedbackProjection,
    StudentFeedbackResult,
    StudentFeedbackRosterEntry,
    StudentFeedbackRosterPreparation,
    install_staged_student_feedback_distribution,
    prepare_student_feedback_distribution_plan,
    preview_student_feedback_distribution,
    render_student_feedback_distribution_package,
    stage_student_feedback_distribution,
    verify_student_feedback_distribution_directory,
)
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowValidationError,
)


def _projection(name: str) -> StudentFeedbackProjection:
    return StudentFeedbackProjection(
        student_display_name=name,
        activity_title="Memoir Revision",
        class_label="English 12 - Period 2",
        boundary_statement=STUDENT_FEEDBACK_BOUNDARY_STATEMENT,
        results=(
            StudentFeedbackResult(
                criterion_label="Use of Evidence",
                scoring_scale_name="Four Levels",
                disposition="scored",
                value=3,
                value_label="Meeting",
            ),
        ),
    )


def _plan(tmp_path: Path):
    preparation = StudentFeedbackRosterPreparation(
        class_id="class-1",
        activity_id="activity-1",
        activity_title="Memoir Revision",
        snapshot_revision=10,
        snapshot_sha256="b" * 64,
        score_basis=SCORE_ANALYSIS_BASIS,
        sharing_scope=STUDENT_FEEDBACK_PREPARATION_SCOPE,
        entries=(
            StudentFeedbackRosterEntry(
                student_id="student-private-001",
                student_display_name="Jane Doe",
                availability=FEEDBACK_AVAILABILITY_DISTRIBUTABLE,
                projection=_projection("Jane Doe"),
            ),
            StudentFeedbackRosterEntry(
                student_id="student-private-002",
                student_display_name="John Smith",
                availability=FEEDBACK_AVAILABILITY_NONE,
                projection=StudentFeedbackProjection(
                    student_display_name="John Smith",
                    activity_title="Memoir Revision",
                    class_label="English 12 - Period 2",
                    boundary_statement=STUDENT_FEEDBACK_BOUNDARY_STATEMENT,
                    results=(),
                ),
            ),
            StudentFeedbackRosterEntry(
                student_id="student-private-003",
                student_display_name="Alex Rivera",
                availability=FEEDBACK_AVAILABILITY_DISTRIBUTABLE,
                projection=_projection("Alex Rivera"),
            ),
        ),
    )
    preview = preview_student_feedback_distribution(
        preparation,
        selection_mode=FEEDBACK_SELECTION_ALL,
    )
    return prepare_student_feedback_distribution_plan(
        preview,
        destination=tmp_path / "feedback",
        authorize_available_only=True,
    )


def _stage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    plan = _plan(tmp_path)
    package = render_student_feedback_distribution_package(
        plan,
        created_at="2026-10-08T05:15:00+00:00",
    )
    monkeypatch.setattr(
        storage,
        "require_student_feedback_plan_current",
        lambda *args, **kwargs: plan,
    )
    staged = stage_student_feedback_distribution(
        plan,
        package,
        workspace_root=tmp_path / "workspace",
    )
    return plan, package, staged


def test_install_promotes_verified_stage_and_verifies_final_destination(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan, package, staged = _stage(tmp_path, monkeypatch)

    result = install_staged_student_feedback_distribution(plan, staged)

    assert isinstance(result, InstalledStudentFeedbackDistribution)
    assert result.action == STUDENT_FEEDBACK_INSTALL_ACTION_INSTALLED
    assert result.directory == plan.destination
    assert plan.destination.is_dir()
    assert not staged.directory.exists()
    assert result.verification.plan_digest == plan.plan_digest
    assert result.verification.package_digest == package.package_digest
    assert result.verification.managed_filenames == plan.output_filenames


def test_exact_existing_destination_is_reused_without_rewriting(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan, _, first_stage = _stage(tmp_path, monkeypatch)
    first = install_staged_student_feedback_distribution(plan, first_stage)
    before = {
        path.name: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in first.directory.iterdir()
    }

    _, _, second_stage = _stage(tmp_path, monkeypatch)
    result = install_staged_student_feedback_distribution(plan, second_stage)

    after = {
        path.name: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in result.directory.iterdir()
    }
    assert result.action == STUDENT_FEEDBACK_INSTALL_ACTION_REUSED
    assert result.directory == plan.destination
    assert not second_stage.directory.exists()
    assert before == after


def test_conflicting_existing_directory_is_not_overwritten(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan, _, staged = _stage(tmp_path, monkeypatch)
    plan.destination.mkdir()
    conflict = plan.destination / "keep.txt"
    conflict.write_bytes(b"existing unrelated content")

    with pytest.raises(
        ConcordWorkflowConflictError,
        match="already exists",
    ):
        install_staged_student_feedback_distribution(plan, staged)

    assert conflict.read_bytes() == b"existing unrelated content"
    assert not staged.directory.exists()


def test_tampered_existing_package_is_conflict_not_rewrite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan, _, first_stage = _stage(tmp_path, monkeypatch)
    installed = install_staged_student_feedback_distribution(plan, first_stage)
    student = installed.directory / plan.students[0].filename
    student.write_bytes(student.read_bytes() + b"tampered")
    tampered = student.read_bytes()

    _, _, second_stage = _stage(tmp_path, monkeypatch)

    with pytest.raises(ConcordWorkflowConflictError):
        install_staged_student_feedback_distribution(plan, second_stage)

    assert student.read_bytes() == tampered
    assert not second_stage.directory.exists()


def test_existing_file_destination_is_conflict_and_preserved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan, _, staged = _stage(tmp_path, monkeypatch)
    plan.destination.write_bytes(b"do not replace")

    with pytest.raises(ConcordWorkflowConflictError):
        install_staged_student_feedback_distribution(plan, staged)

    assert plan.destination.read_bytes() == b"do not replace"
    assert not staged.directory.exists()


def test_promotion_failure_never_creates_successful_destination(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan, _, staged = _stage(tmp_path, monkeypatch)

    def fail_promotion(_staging: Path, _destination: Path) -> None:
        raise OSError("simulated rename failure")

    monkeypatch.setattr(storage, "_promote_staging_directory", fail_promotion)

    with pytest.raises(
        StudentFeedbackDistributionInstallError,
        match="could not be promoted",
    ) as captured:
        install_staged_student_feedback_distribution(plan, staged)

    assert captured.value.destination_durable is False
    assert not plan.destination.exists()
    assert not staged.directory.exists()


def test_post_promotion_verification_failure_reports_partial_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan, _, staged = _stage(tmp_path, monkeypatch)
    real_verify = storage.verify_student_feedback_distribution_directory
    calls = 0

    def fail_final(*args: object, **kwargs: object):
        nonlocal calls
        calls += 1
        if calls == 1:
            return real_verify(*args, **kwargs)
        raise RuntimeError("simulated final verification failure")

    monkeypatch.setattr(
        storage,
        "verify_student_feedback_distribution_directory",
        fail_final,
    )

    with pytest.raises(
        StudentFeedbackDistributionInstallError,
        match="became durable",
    ) as captured:
        install_staged_student_feedback_distribution(plan, staged)

    assert captured.value.destination_durable is True
    assert plan.destination.is_dir()
    assert not staged.directory.exists()


def test_install_rejects_stage_from_wrong_parent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan, _, staged = _stage(tmp_path, monkeypatch)
    other = tmp_path / "elsewhere"
    other.mkdir()
    moved = other / staged.directory.name
    staged.directory.rename(moved)
    wrong = staged.__class__(
        directory=moved,
        verification=staged.verification.__class__(
            directory=moved,
            schema_version=staged.verification.schema_version,
            plan_digest=staged.verification.plan_digest,
            package_digest=staged.verification.package_digest,
            selected_count=staged.verification.selected_count,
            managed_filenames=staged.verification.managed_filenames,
            combined_page_count=staged.verification.combined_page_count,
        ),
    )

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="destination sibling",
    ):
        install_staged_student_feedback_distribution(plan, wrong)


def test_reused_destination_still_passes_independent_verification(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan, package, staged = _stage(tmp_path, monkeypatch)
    install_staged_student_feedback_distribution(plan, staged)

    verified = verify_student_feedback_distribution_directory(
        plan.destination,
        expected_plan_digest=plan.plan_digest,
        expected_package_digest=package.package_digest,
    )

    assert verified.managed_filenames == plan.output_filenames
