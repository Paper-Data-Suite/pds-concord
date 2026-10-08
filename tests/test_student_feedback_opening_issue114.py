
from __future__ import annotations

from pathlib import Path

import pytest
from pds_core.local_open import LocalOpenError

import concord.workflows.student_feedback_distribution_opening as opening
import concord.workflows.student_feedback_distribution_storage as storage
from concord.workflows import (
    FEEDBACK_AVAILABILITY_DISTRIBUTABLE,
    FEEDBACK_PRINT_FILENAME,
    FEEDBACK_SELECTION_ALL,
    SCORE_ANALYSIS_BASIS,
    STUDENT_FEEDBACK_BOUNDARY_STATEMENT,
    STUDENT_FEEDBACK_PREPARATION_SCOPE,
    StudentFeedbackProjection,
    StudentFeedbackResult,
    StudentFeedbackRosterEntry,
    StudentFeedbackRosterPreparation,
    execute_student_feedback_distribution,
    open_student_feedback_distribution_directory,
    open_student_feedback_distribution_print_pdf,
    prepare_student_feedback_distribution_plan,
    preview_student_feedback_distribution,
)
from concord.workflows.errors import (
    ConcordWorkflowOpenError,
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


def _installed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
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
    plan = prepare_student_feedback_distribution_plan(
        preview,
        destination=tmp_path / "feedback",
    )
    monkeypatch.setattr(
        storage,
        "require_student_feedback_plan_current",
        lambda *args, **kwargs: plan,
    )
    installed = execute_student_feedback_distribution(
        plan,
        confirmation="PREPARE",
        workspace_root=tmp_path / "workspace",
        created_at="2026-10-08T05:45:00+00:00",
    )
    return plan, installed


def test_open_directory_verifies_before_core_local_open(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan, installed = _installed(tmp_path, monkeypatch)
    calls: list[Path] = []

    def fake_open(path: str | Path) -> Path:
        resolved = Path(path)
        calls.append(resolved)
        return resolved

    monkeypatch.setattr(opening, "open_local_path", fake_open)

    verified = open_student_feedback_distribution_directory(
        installed.directory,
        expected_plan_digest=plan.plan_digest,
        expected_package_digest=installed.verification.package_digest,
    )

    assert verified == installed.verification
    assert calls == [installed.directory]


def test_open_print_pdf_passes_only_fixed_verified_class_pdf(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan, installed = _installed(tmp_path, monkeypatch)
    calls: list[Path] = []

    def fake_open(path: str | Path) -> Path:
        resolved = Path(path)
        calls.append(resolved)
        return resolved

    monkeypatch.setattr(opening, "open_local_path", fake_open)

    verified = open_student_feedback_distribution_print_pdf(
        installed.directory,
        expected_plan_digest=plan.plan_digest,
        expected_package_digest=installed.verification.package_digest,
    )

    assert verified == installed.verification
    assert calls == [installed.directory / FEEDBACK_PRINT_FILENAME]


def test_tampered_package_is_rejected_before_any_open(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, installed = _installed(tmp_path, monkeypatch)
    student_pdf = next(
        path
        for path in installed.directory.glob("*.pdf")
        if path.name != FEEDBACK_PRINT_FILENAME
    )
    student_pdf.write_bytes(student_pdf.read_bytes() + b"tampered")
    calls: list[Path] = []

    monkeypatch.setattr(
        opening,
        "open_local_path",
        lambda path: calls.append(Path(path)),
    )

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="digest does not match",
    ):
        open_student_feedback_distribution_directory(installed.directory)

    assert calls == []


def test_unexpected_file_is_rejected_before_class_pdf_open(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, installed = _installed(tmp_path, monkeypatch)
    (installed.directory / "unexpected.txt").write_bytes(b"not managed")
    calls: list[Path] = []

    monkeypatch.setattr(
        opening,
        "open_local_path",
        lambda path: calls.append(Path(path)),
    )

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="managed file set is not exact",
    ):
        open_student_feedback_distribution_print_pdf(installed.directory)

    assert calls == []


@pytest.mark.parametrize(
    "open_function",
    (
        open_student_feedback_distribution_directory,
        open_student_feedback_distribution_print_pdf,
    ),
)
def test_core_open_failure_does_not_modify_verified_package(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    open_function,
) -> None:
    _, installed = _installed(tmp_path, monkeypatch)
    before = {
        path.name: path.read_bytes()
        for path in installed.directory.iterdir()
    }

    def fail_open(path: str | Path) -> Path:
        raise LocalOpenError(f"simulated viewer failure: {path}")

    monkeypatch.setattr(opening, "open_local_path", fail_open)

    with pytest.raises(
        ConcordWorkflowOpenError,
        match="system could not open",
    ):
        open_function(installed.directory)

    after = {
        path.name: path.read_bytes()
        for path in installed.directory.iterdir()
    }
    assert after == before


def test_opening_module_uses_only_core_local_open_boundary() -> None:
    source = Path(
        "concord/workflows/student_feedback_distribution_opening.py"
    ).read_text(encoding="utf-8")

    assert "from pds_core.local_open import LocalOpenError, open_local_path" in source
    assert "os.startfile" not in source
    assert "subprocess" not in source
    assert "xdg-open" not in source
    assert "verify_student_feedback_distribution_directory" in source
    assert "FEEDBACK_PRINT_FILENAME" in source
