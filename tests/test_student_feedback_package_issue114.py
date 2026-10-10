
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pypdfium2 as pdfium
import pytest

from concord.workflows import (
    FEEDBACK_AVAILABILITY_DISTRIBUTABLE,
    FEEDBACK_AVAILABILITY_NONE,
    FEEDBACK_INDEX_FILENAME,
    FEEDBACK_MANIFEST_FILENAME,
    FEEDBACK_PRINT_FILENAME,
    FEEDBACK_SELECTION_ALL,
    SCORE_ANALYSIS_BASIS,
    STUDENT_FEEDBACK_AUDIENCE_STAFF,
    STUDENT_FEEDBACK_AUDIENCE_STUDENT,
    STUDENT_FEEDBACK_BOUNDARY_STATEMENT,
    STUDENT_FEEDBACK_MANIFEST_SCHEMA_VERSION,
    STUDENT_FEEDBACK_ORDERING_RULE,
    STUDENT_FEEDBACK_PREPARATION_SCOPE,
    StudentFeedbackProjection,
    StudentFeedbackResult,
    StudentFeedbackRosterEntry,
    StudentFeedbackRosterPreparation,
    prepare_student_feedback_distribution_plan,
    preview_student_feedback_distribution,
    render_student_feedback_distribution_package,
    student_feedback_projection_sha256,
)
from concord.workflows.errors import ConcordWorkflowValidationError


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


def _render(tmp_path: Path):
    plan = _plan(tmp_path)
    package = render_student_feedback_distribution_package(
        plan,
        created_at="2026-10-08T00:30:00-04:00",
    )
    return plan, package


def _files(package):
    return {item.filename: item for item in package.files}


def test_package_contains_exact_reviewed_output_set_and_audiences(
    tmp_path: Path,
) -> None:
    plan, package = _render(tmp_path)

    assert tuple(item.filename for item in package.files) == plan.output_filenames
    assert package.schema_version == STUDENT_FEEDBACK_MANIFEST_SCHEMA_VERSION
    assert package.plan_digest == plan.plan_digest
    assert len(package.package_digest) == 64

    files = _files(package)
    for student in plan.students:
        assert files[student.filename].audience_scope == (
            STUDENT_FEEDBACK_AUDIENCE_STUDENT
        )
    for filename in (
        FEEDBACK_PRINT_FILENAME,
        FEEDBACK_INDEX_FILENAME,
        FEEDBACK_MANIFEST_FILENAME,
    ):
        assert files[filename].audience_scope == STUDENT_FEEDBACK_AUDIENCE_STAFF

    assert not plan.destination.exists()


def test_combined_pdf_is_valid_and_matches_ordered_student_page_total(
    tmp_path: Path,
) -> None:
    plan, package = _render(tmp_path)
    files = _files(package)

    individual_pages = sum(
        files[item.filename].page_count or 0
        for item in plan.students
    )
    combined = files[FEEDBACK_PRINT_FILENAME]

    assert combined.content.startswith(b"%PDF")
    assert combined.page_count == individual_pages

    document = pdfium.PdfDocument(combined.content)
    try:
        assert len(document) == individual_pages
    finally:
        document.close()


def test_feedback_index_is_static_relative_and_selected_only(
    tmp_path: Path,
) -> None:
    plan, package = _render(tmp_path)
    index = _files(package)[FEEDBACK_INDEX_FILENAME].content.decode("utf-8")

    assert "Jane Doe" in index
    assert "Alex Rivera" in index
    assert "John Smith" not in index
    for student in plan.students:
        assert f'href="{student.filename}"' in index

    lowered = index.casefold()
    assert "http://" not in lowered
    assert "https://" not in lowered
    assert "javascript:" not in lowered
    assert "<script" not in lowered
    assert "file://" not in lowered
    assert "student-private-" not in index
    assert str(tmp_path) not in index


def test_manifest_is_versioned_private_and_binds_managed_artifacts(
    tmp_path: Path,
) -> None:
    plan, package = _render(tmp_path)
    files = _files(package)
    raw = files[FEEDBACK_MANIFEST_FILENAME].content
    manifest = json.loads(raw)

    assert manifest["schema_version"] == STUDENT_FEEDBACK_MANIFEST_SCHEMA_VERSION
    assert manifest["created_at"] == "2026-10-08T04:30:00+00:00"
    assert manifest["concord_version"] == "0.3.1"
    assert manifest["source"] == {
        "class_id": "class-1",
        "activity_id": "activity-1",
        "activity_title": "Memoir Revision",
        "snapshot_revision": 10,
        "snapshot_sha256": "b" * 64,
    }
    assert manifest["selection_mode"] == FEEDBACK_SELECTION_ALL
    assert manifest["selected_count"] == 2
    assert manifest["no_feedback_count"] == 1
    assert manifest["unresolved_count"] == 0
    assert manifest["ordering_rule"] == STUDENT_FEEDBACK_ORDERING_RULE
    assert manifest["reviewed_plan_digest"] == plan.plan_digest
    assert manifest["package_digest"] == package.package_digest

    entries = manifest["entries"]
    assert [item["student_display_name"] for item in entries] == [
        "Jane Doe",
        "Alex Rivera",
    ]
    assert all(item["entry_identity"].startswith("cfd_") for item in entries)
    assert all(len(item["entry_identity"]) == 28 for item in entries)

    for student, entry in zip(plan.students, entries, strict=True):
        artifact = files[student.filename]
        assert entry["output_filename"] == student.filename
        assert entry["output_sha256"] == artifact.sha256
        assert entry["page_count"] == artifact.page_count
        assert entry["audience_scope"] == STUDENT_FEEDBACK_AUDIENCE_STUDENT
        assert entry["projection_sha256"] == (
            student_feedback_projection_sha256(student.projection)
        )

    assert manifest["combined_pdf"]["sha256"] == (
        files[FEEDBACK_PRINT_FILENAME].sha256
    )
    assert manifest["feedback_index"]["sha256"] == (
        files[FEEDBACK_INDEX_FILENAME].sha256
    )

    rendered_text = raw.decode("utf-8")
    assert "student-private-001" not in rendered_text
    assert "student-private-002" not in rendered_text
    assert "student-private-003" not in rendered_text
    assert "John Smith" not in rendered_text
    assert str(plan.destination) not in rendered_text


def test_all_managed_file_digests_match_exact_bytes(tmp_path: Path) -> None:
    _, package = _render(tmp_path)

    for item in package.files:
        assert item.sha256 == hashlib.sha256(item.content).hexdigest()


def test_projection_digest_is_semantic_and_deterministic() -> None:
    first = _projection("Jane Doe")
    same = _projection("Jane Doe")
    changed = _projection(
        "Jane Doe",
        value=4,
        label="Exceeding",
    )

    assert student_feedback_projection_sha256(first) == (
        student_feedback_projection_sha256(same)
    )
    assert student_feedback_projection_sha256(first) != (
        student_feedback_projection_sha256(changed)
    )


def test_exact_render_is_deterministic_for_same_plan_and_created_at(
    tmp_path: Path,
) -> None:
    plan = _plan(tmp_path)

    first = render_student_feedback_distribution_package(
        plan,
        created_at="2026-10-08T00:30:00-04:00",
    )
    second = render_student_feedback_distribution_package(
        plan,
        created_at="2026-10-08T04:30:00+00:00",
    )

    assert first.package_digest == second.package_digest
    assert tuple((item.filename, item.content) for item in first.files) == tuple(
        (item.filename, item.content) for item in second.files
    )


@pytest.mark.parametrize(
    "created_at",
    (
        "",
        "not-a-date",
        "2026-10-08T04:30:00",
    ),
)
def test_package_requires_offset_aware_created_at(
    tmp_path: Path,
    created_at: str,
) -> None:
    with pytest.raises(ConcordWorkflowValidationError, match="created_at"):
        render_student_feedback_distribution_package(
            _plan(tmp_path),
            created_at=created_at,
        )


def test_package_rendering_is_zero_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan(tmp_path)
    working = tmp_path / "working"
    working.mkdir()
    monkeypatch.chdir(working)

    render_student_feedback_distribution_package(
        plan,
        created_at="2026-10-08T04:30:00+00:00",
    )

    assert tuple(working.iterdir()) == ()
    assert not plan.destination.exists()


def test_aggregate_renderer_merges_pdf_pages_without_class_raster_cache() -> None:
    source = Path(
        "concord/workflows/student_feedback_distribution_package.py"
    ).read_text(encoding="utf-8")

    assert "import_pages" in source
    assert "Image.open" not in source
    assert "render(" not in source
    assert "convert(" not in source
