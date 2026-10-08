from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pypdfium2 as pdfium
import pytest
from PIL import ImageDraw

from concord.generated_paths import build_human_readable_output_filename
from concord.workflows import (
    STUDENT_FEEDBACK_BOUNDARY_STATEMENT,
    STUDENT_FEEDBACK_PDF_MEDIA_TYPE,
    RenderedStudentFeedbackPdf,
    StudentFeedbackProjection,
    StudentFeedbackRenderInput,
    StudentFeedbackResult,
    render_student_feedback_pdf,
)
from concord.workflows.errors import ConcordWorkflowValidationError


def _filename(name: str = "Jane Doe") -> str:
    return build_human_readable_output_filename(
        display_label=f"{name} - Feedback",
        domain="student-feedback",
        identity_parts=("class-1", "activity-1", name),
        extension=".pdf",
    )


def _projection(
    name: str = "Jane Doe",
    *,
    results: tuple[StudentFeedbackResult, ...] | None = None,
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
                disposition="scored",
                value=3,
                value_label="Meeting",
            ),
        )
        if results is None
        else results,
    )


def _input(
    name: str = "Jane Doe",
    *,
    results: tuple[StudentFeedbackResult, ...] | None = None,
) -> StudentFeedbackRenderInput:
    return StudentFeedbackRenderInput(
        filename=_filename(name),
        projection=_projection(name, results=results),
    )


def test_student_feedback_pdf_is_valid_and_deterministic() -> None:
    render_input = _input()

    first = render_student_feedback_pdf(render_input)
    second = render_student_feedback_pdf(render_input)

    assert isinstance(first, RenderedStudentFeedbackPdf)
    assert first.filename == render_input.filename
    assert first.media_type == STUDENT_FEEDBACK_PDF_MEDIA_TYPE
    assert first.content.startswith(b"%PDF")
    assert first.content == second.content
    assert first.page_count == second.page_count == 1

    document = pdfium.PdfDocument(first.content)
    try:
        assert len(document) == first.page_count
    finally:
        document.close()


def test_rendered_text_preserves_exact_scored_semantics_and_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[str] = []
    original = ImageDraw.ImageDraw.text

    def tracking_text(
        draw: ImageDraw.ImageDraw,
        xy: object,
        text: object,
        *args: object,
        **kwargs: object,
    ) -> object:
        seen.append(str(text))
        return original(draw, xy, text, *args, **kwargs)

    monkeypatch.setattr(ImageDraw.ImageDraw, "text", tracking_text)

    render_student_feedback_pdf(_input())

    assert "Jane Doe" in seen
    assert "Memoir Revision" in seen
    assert "English 12 - Period 2" in " ".join(seen)
    assert "Use of Evidence" in seen
    assert "Four Levels" in seen
    assert "3 - Meeting" in seen
    assert STUDENT_FEEDBACK_BOUNDARY_STATEMENT in seen


def test_non_score_dispositions_render_as_exact_disposition_tokens(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dispositions = (
        "insufficient_evidence",
        "absent",
        "excused",
        "not_observed",
        "not_applicable",
        "deferred",
    )
    results = tuple(
        StudentFeedbackResult(
            criterion_label=f"Criterion {index}",
            scoring_scale_name="Four Levels",
            disposition=disposition,
            value=None,
            value_label=None,
        )
        for index, disposition in enumerate(dispositions, start=1)
    )
    seen: list[str] = []
    original = ImageDraw.ImageDraw.text

    def tracking_text(
        draw: ImageDraw.ImageDraw,
        xy: object,
        text: object,
        *args: object,
        **kwargs: object,
    ) -> object:
        seen.append(str(text))
        return original(draw, xy, text, *args, **kwargs)

    monkeypatch.setattr(ImageDraw.ImageDraw, "text", tracking_text)

    render_student_feedback_pdf(_input(results=results))

    for disposition in dispositions:
        assert disposition in seen


def test_individual_render_path_has_no_peer_or_raw_identity_surface(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[str] = []
    original = ImageDraw.ImageDraw.text

    def tracking_text(
        draw: ImageDraw.ImageDraw,
        xy: object,
        text: object,
        *args: object,
        **kwargs: object,
    ) -> object:
        seen.append(str(text))
        return original(draw, xy, text, *args, **kwargs)

    monkeypatch.setattr(ImageDraw.ImageDraw, "text", tracking_text)

    rendered = render_student_feedback_pdf(_input("Jane Doe"))
    visible = "\n".join(seen)

    assert "Jane Doe" in visible
    assert "Alex Rivera" not in visible
    assert "student-private-001" not in visible
    assert "score-record-1" not in visible
    assert "criterion-1" not in visible
    assert "scale-1" not in visible
    assert "snapshot" not in visible.casefold()
    assert rendered.filename == _filename("Jane Doe")


def test_many_feedback_rows_paginate_without_changing_order() -> None:
    results = tuple(
        StudentFeedbackResult(
            criterion_label=f"Criterion {index:02d} " + ("detail " * 8),
            scoring_scale_name="Four Levels",
            disposition="scored",
            value=3,
            value_label="Meeting",
        )
        for index in range(1, 61)
    )

    rendered = render_student_feedback_pdf(_input(results=results))

    assert rendered.page_count > 1
    document = pdfium.PdfDocument(rendered.content)
    try:
        assert len(document) == rendered.page_count
    finally:
        document.close()


def test_renderer_rejects_no_feedback_and_changed_boundary() -> None:
    empty = _input(results=())
    with pytest.raises(
        ConcordWorkflowValidationError,
        match="requires distributable",
    ):
        render_student_feedback_pdf(empty)

    changed = replace(
        _input(),
        projection=replace(
            _input().projection,
            boundary_statement="This is a Grade report.",
        ),
    )
    with pytest.raises(
        ConcordWorkflowValidationError,
        match="exact student-feedback boundary",
    ):
        render_student_feedback_pdf(changed)


def test_renderer_rejects_invalid_score_shape_and_disposition() -> None:
    invalid_scored = _input(
        results=(
            StudentFeedbackResult(
                criterion_label="Use of Evidence",
                scoring_scale_name="Four Levels",
                disposition="scored",
                value=None,
                value_label=None,
            ),
        )
    )
    with pytest.raises(ConcordWorkflowValidationError, match="requires a Scale"):
        render_student_feedback_pdf(invalid_scored)

    unknown = _input(
        results=(
            StudentFeedbackResult(
                criterion_label="Use of Evidence",
                scoring_scale_name="Four Levels",
                disposition="mystery",
                value=None,
                value_label=None,
            ),
        )
    )
    with pytest.raises(ConcordWorkflowValidationError, match="unsupported"):
        render_student_feedback_pdf(unknown)


def test_pdf_renderer_source_excludes_teacher_local_fields() -> None:
    source = Path(
        "concord/workflows/student_feedback_distribution_pdf.py"
    ).read_text(encoding="utf-8")

    for forbidden in (
        "score_record_id",
        "student_id",
        "criterion_id",
        "scoring_scale_id",
        "session_id",
        "snapshot_sha256",
        "snapshot_revision",
        "rationale",
        "evidence_link",
        "retained_evidence",
        "raw_evidence",
        "moderation",
        "target_score_detail",
    ):
        assert forbidden not in source
