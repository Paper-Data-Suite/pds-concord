
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

import concord.workflows.student_feedback_distribution_storage as storage
from concord.workflows import (
    FEEDBACK_AVAILABILITY_DISTRIBUTABLE,
    FEEDBACK_AVAILABILITY_NONE,
    FEEDBACK_INDEX_FILENAME,
    FEEDBACK_MANIFEST_FILENAME,
    FEEDBACK_PRINT_FILENAME,
    FEEDBACK_SELECTION_ALL,
    SCORE_ANALYSIS_BASIS,
    STUDENT_FEEDBACK_BOUNDARY_STATEMENT,
    STUDENT_FEEDBACK_PREPARATION_SCOPE,
    StudentFeedbackDistributionStagingError,
    StudentFeedbackProjection,
    StudentFeedbackResult,
    StudentFeedbackRosterEntry,
    StudentFeedbackRosterPreparation,
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


def _projection(
    name: str,
    *,
    value: int | None = 3,
    disposition: str = "scored",
    label: str | None = "Meeting",
) -> StudentFeedbackProjection:
    return StudentFeedbackProjection(
        student_display_name=name,
        activity_title="Memoir Revision",
        class_label="English 12 - Period 2",
        boundary_statement=STUDENT_FEEDBACK_BOUNDARY_STATEMENT,
        results=(
            StudentFeedbackResult(
                criterion_label="Use of Evidence",
                scoring_scale_name="Four Levels",
                disposition=disposition,
                value=value,
                value_label=label,
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
                projection=_projection(
                    "Alex Rivera",
                    value=None,
                    disposition="absent",
                    label=None,
                ),
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


def _package(plan):
    return render_student_feedback_distribution_package(
        plan,
        created_at="2026-10-08T04:45:00+00:00",
    )


def _stage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    plan = _plan(tmp_path)
    package = _package(plan)
    calls = 0

    def exact_current(*args: object, **kwargs: object) -> object:
        nonlocal calls
        calls += 1
        assert not any(
            path.name.startswith(".concord-feedback-staging-")
            for path in tmp_path.iterdir()
        )
        return plan

    monkeypatch.setattr(
        storage,
        "require_student_feedback_plan_current",
        exact_current,
    )
    staged = stage_student_feedback_distribution(
        plan,
        package,
        workspace_root=tmp_path / "workspace",
    )
    assert calls == 1
    return plan, package, staged


def test_stage_writes_private_sibling_and_verifies_exact_package(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan, package, staged = _stage(tmp_path, monkeypatch)

    assert staged.directory.parent == plan.destination.parent
    assert staged.directory.name.startswith(".concord-feedback-staging-")
    assert staged.directory != plan.destination
    assert not plan.destination.exists()
    assert staged.verification.plan_digest == plan.plan_digest
    assert staged.verification.package_digest == package.package_digest
    assert staged.verification.managed_filenames == plan.output_filenames
    assert set(path.name for path in staged.directory.iterdir()) == set(
        plan.output_filenames
    )


def test_read_only_verifier_accepts_verified_stage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan, package, staged = _stage(tmp_path, monkeypatch)
    before = {
        path.name: path.read_bytes()
        for path in staged.directory.iterdir()
    }

    verified = verify_student_feedback_distribution_directory(
        staged.directory,
        expected_plan_digest=plan.plan_digest,
        expected_package_digest=package.package_digest,
    )

    after = {
        path.name: path.read_bytes()
        for path in staged.directory.iterdir()
    }
    assert verified == staged.verification
    assert before == after


@pytest.mark.parametrize(
    "filename",
    (
        FEEDBACK_INDEX_FILENAME,
        FEEDBACK_PRINT_FILENAME,
    ),
)
def test_verifier_rejects_missing_managed_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    filename: str,
) -> None:
    _, _, staged = _stage(tmp_path, monkeypatch)
    (staged.directory / filename).unlink()

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="managed file set is not exact",
    ):
        verify_student_feedback_distribution_directory(staged.directory)


def test_verifier_rejects_changed_student_pdf(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan, _, staged = _stage(tmp_path, monkeypatch)
    student_path = staged.directory / plan.students[0].filename
    student_path.write_bytes(student_path.read_bytes() + b"tamper")

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="file digest does not match",
    ):
        verify_student_feedback_distribution_directory(staged.directory)


def test_verifier_rejects_unexpected_package_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, _, staged = _stage(tmp_path, monkeypatch)
    (staged.directory / "notes.txt").write_text("not managed", encoding="utf-8")

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="managed file set is not exact",
    ):
        verify_student_feedback_distribution_directory(staged.directory)


def test_verifier_rejects_manifest_field_injection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, _, staged = _stage(tmp_path, monkeypatch)
    manifest_path = staged.directory / FEEDBACK_MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["student_id"] = "student-private-001"
    manifest_path.write_text(
        json.dumps(manifest, sort_keys=True),
        encoding="utf-8",
    )

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="manifest fields do not match",
    ):
        verify_student_feedback_distribution_directory(staged.directory)


def test_verifier_rejects_nonlocal_index_even_with_updated_integrity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, _, staged = _stage(tmp_path, monkeypatch)
    index_path = staged.directory / FEEDBACK_INDEX_FILENAME
    index = index_path.read_text(encoding="utf-8")
    index = index.replace(
        'href="Jane-Doe-Feedback',
        'href="https://example.invalid/Jane-Doe-Feedback',
        1,
    )
    index_path.write_bytes(index.encode("utf-8"))

    manifest_path = staged.directory / FEEDBACK_MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["feedback_index"]["sha256"] = hashlib.sha256(
        index.encode("utf-8")
    ).hexdigest()
    digest_payload = dict(manifest)
    digest_payload.pop("package_digest")
    canonical = (
        json.dumps(
            digest_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    manifest["package_digest"] = hashlib.sha256(canonical).hexdigest()
    manifest_path.write_text(
        (
            json.dumps(
                manifest,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
            + "\n"
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="nonlocal dependency",
    ):
        verify_student_feedback_distribution_directory(staged.directory)


def test_currentness_failure_occurs_before_staging_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan(tmp_path)
    package = _package(plan)

    def stale(*args: object, **kwargs: object) -> object:
        assert not any(
            path.name.startswith(".concord-feedback-staging-")
            for path in tmp_path.iterdir()
        )
        raise ConcordWorkflowConflictError("stale reviewed plan")

    monkeypatch.setattr(
        storage,
        "require_student_feedback_plan_current",
        stale,
    )

    with pytest.raises(ConcordWorkflowConflictError, match="stale"):
        stage_student_feedback_distribution(
            plan,
            package,
            workspace_root=tmp_path / "workspace",
        )

    assert not plan.destination.exists()
    assert not any(
        path.name.startswith(".concord-feedback-staging-")
        for path in tmp_path.iterdir()
    )


def test_write_failure_cleans_staging_best_effort(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan(tmp_path)
    package = _package(plan)
    monkeypatch.setattr(
        storage,
        "require_student_feedback_plan_current",
        lambda *args, **kwargs: plan,
    )
    real_write = storage._write_staging_file
    calls = 0

    def fail_second(path: Path, content: bytes) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise StudentFeedbackDistributionStagingError("simulated write failure")
        real_write(path, content)

    monkeypatch.setattr(storage, "_write_staging_file", fail_second)

    with pytest.raises(
        StudentFeedbackDistributionStagingError,
        match="simulated write failure",
    ):
        stage_student_feedback_distribution(
            plan,
            package,
            workspace_root=tmp_path / "workspace",
        )

    assert not plan.destination.exists()
    assert not any(
        path.name.startswith(".concord-feedback-staging-")
        for path in tmp_path.iterdir()
    )


def test_verifier_rejects_symlink_managed_file_where_supported(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan, _, staged = _stage(tmp_path, monkeypatch)
    student_path = staged.directory / plan.students[0].filename
    target = tmp_path / "external.pdf"
    target.write_bytes(student_path.read_bytes())
    student_path.unlink()
    try:
        student_path.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation is unavailable on this platform")

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="symlink",
    ):
        verify_student_feedback_distribution_directory(staged.directory)


def test_staging_parent_guard_rejects_missing_parent(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    changed = plan.__class__(
        schema_version=plan.schema_version,
        class_id=plan.class_id,
        activity_id=plan.activity_id,
        activity_title=plan.activity_title,
        expected_snapshot_revision=plan.expected_snapshot_revision,
        expected_snapshot_sha256=plan.expected_snapshot_sha256,
        selection_mode=plan.selection_mode,
        available_only_authorized=plan.available_only_authorized,
        destination=tmp_path / "missing" / "feedback",
        roster_student_ids=plan.roster_student_ids,
        requested_student_ids=plan.requested_student_ids,
        no_feedback_student_ids=plan.no_feedback_student_ids,
        unresolved_student_ids=plan.unresolved_student_ids,
        students=plan.students,
        output_filenames=plan.output_filenames,
        plan_digest=plan.plan_digest,
    )

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="existing safe directory",
    ):
        storage._require_staging_parent(changed)
