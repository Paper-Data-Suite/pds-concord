"""Student-scoped PDF rendering for reviewed Concord feedback."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

from PIL import Image, ImageDraw, ImageFont

from concord.generated_paths import (
    ConcordGeneratedPathError,
    validate_human_readable_output_filename,
)
from concord.routing.starter_layout_pdf import starter_images_to_pdf
from concord.workflows.errors import ConcordWorkflowValidationError
from concord.workflows.student_feedback import (
    STUDENT_FEEDBACK_BOUNDARY_STATEMENT,
    StudentFeedbackProjection,
    StudentFeedbackResult,
)
from concord.workflows.student_feedback_distribution_rendering import (
    StudentFeedbackRenderInput,
)

STUDENT_FEEDBACK_PDF_MEDIA_TYPE: Final[str] = "application/pdf"
_PDF_CREATED_AT: Final[str] = "2000-01-01T00:00:00+00:00"
_PAGE_SIZE: Final[tuple[int, int]] = (1275, 1650)
_MARGIN_X: Final[int] = 82
_MARGIN_TOP: Final[int] = 72
_MARGIN_BOTTOM: Final[int] = 70
_HEADER_BOTTOM: Final[int] = 168
_CONTENT_BOTTOM: Final[int] = _PAGE_SIZE[1] - _MARGIN_BOTTOM
_CELL_PAD_X: Final[int] = 10
_CELL_PAD_Y: Final[int] = 7
_ALLOWED_DISPOSITIONS: Final[frozenset[str]] = frozenset(
    {
        "scored",
        "insufficient_evidence",
        "absent",
        "excused",
        "not_observed",
        "not_applicable",
        "deferred",
    }
)

Font = ImageFont.FreeTypeFont | ImageFont.ImageFont


def _font(size: int) -> Font:
    return ImageFont.load_default(size=size)


_TITLE_FONT = _font(24)
_HEADING_FONT = _font(22)
_BODY_FONT = _font(17)
_SMALL_FONT = _font(14)
_TABLE_FONT = _font(15)
_TABLE_HEADER_FONT = _font(15)


@dataclass(frozen=True, slots=True, kw_only=True)
class RenderedStudentFeedbackPdf:
    """One in-memory student-scoped PDF artifact."""

    filename: str
    media_type: str
    content: bytes
    page_count: int


def _line_height(font: Font) -> int:
    box = font.getbbox("Ag")
    return max(1, int(box[3] - box[1] + 5))


def _split_long_token(
    draw: ImageDraw.ImageDraw,
    token: str,
    font: Font,
    max_width: int,
) -> list[str]:
    if draw.textlength(token, font=font) <= max_width:
        return [token]
    result: list[str] = []
    current = ""
    for character in token:
        candidate = current + character
        if current and draw.textlength(candidate, font=font) > max_width:
            result.append(current)
            current = character
        else:
            current = candidate
    if current:
        result.append(current)
    return result or [""]


def _wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: Font,
    max_width: int,
) -> list[str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    result: list[str] = []
    for paragraph in normalized.split("\n"):
        if not paragraph:
            result.append("")
            continue
        words: list[str] = []
        for word in paragraph.split():
            words.extend(_split_long_token(draw, word, font, max_width))
        if not words:
            result.append("")
            continue
        current = words[0]
        for word in words[1:]:
            candidate = current + " " + word
            if draw.textlength(candidate, font=font) <= max_width:
                current = candidate
            else:
                result.append(current)
                current = word
        result.append(current)
    return result or [""]


def _scalar(value: object) -> str:
    if value is None:
        return "-"
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _result_text(result: StudentFeedbackResult) -> str:
    if result.disposition not in _ALLOWED_DISPOSITIONS:
        raise ConcordWorkflowValidationError(
            "Student feedback PDF encountered an unsupported Score disposition."
        )
    if result.disposition != "scored":
        if result.value is not None or result.value_label is not None:
            raise ConcordWorkflowValidationError(
                "Student feedback PDF non-score result must not carry a Scale value."
            )
        return result.disposition
    if result.value is None or result.value_label is None:
        raise ConcordWorkflowValidationError(
            "Student feedback PDF scored result requires a Scale value and label."
        )
    return f"{_scalar(result.value)} - {result.value_label}"


def _validate_render_input(render_input: StudentFeedbackRenderInput) -> None:
    try:
        validate_human_readable_output_filename(render_input.filename)
    except ConcordGeneratedPathError as error:
        raise ConcordWorkflowValidationError(
            "Student feedback PDF requires a valid planned feedback filename."
        ) from error

    projection = render_input.projection
    if projection.current_score_count <= 0:
        raise ConcordWorkflowValidationError(
            "Student feedback PDF requires distributable current feedback."
        )
    if projection.boundary_statement != STUDENT_FEEDBACK_BOUNDARY_STATEMENT:
        raise ConcordWorkflowValidationError(
            "Student feedback PDF requires the exact student-feedback boundary."
        )
    for result in projection.results:
        _result_text(result)


class _FeedbackPainter:
    def __init__(self, projection: StudentFeedbackProjection) -> None:
        self.projection = projection
        self.images: list[Image.Image] = []
        self.image: Image.Image
        self.draw: ImageDraw.ImageDraw
        self.y = _HEADER_BOTTOM
        self._new_page()

    def _new_page(self) -> None:
        image = Image.new("RGB", _PAGE_SIZE, "white")
        self.images.append(image)
        self.image = image
        self.draw = ImageDraw.Draw(image)
        page_number = len(self.images)

        self.draw.text(
            (_MARGIN_X, _MARGIN_TOP),
            "Student Feedback",
            fill="black",
            font=_TITLE_FONT,
        )
        page_label = f"Page {page_number}"
        label_width = int(self.draw.textlength(page_label, font=_SMALL_FONT))
        self.draw.text(
            (_PAGE_SIZE[0] - _MARGIN_X - label_width, _MARGIN_TOP),
            page_label,
            fill="black",
            font=_SMALL_FONT,
        )
        self._header_text(
            self.projection.student_display_name,
            top=_MARGIN_TOP + 38,
        )
        self._header_text(
            self.projection.activity_title,
            top=_MARGIN_TOP + 66,
        )
        self.draw.line(
            (
                _MARGIN_X,
                _HEADER_BOTTOM - 18,
                _PAGE_SIZE[0] - _MARGIN_X,
                _HEADER_BOTTOM - 18,
            ),
            fill="black",
            width=2,
        )
        self.y = _HEADER_BOTTOM

    def _header_text(self, text: str, *, top: int) -> None:
        available = _PAGE_SIZE[0] - (2 * _MARGIN_X) - 170
        lines = _wrap_text(self.draw, text, _SMALL_FONT, available)
        display = lines[0]
        if len(lines) > 1:
            display += "..."
        self.draw.text(
            (_MARGIN_X, top),
            display,
            fill="black",
            font=_SMALL_FONT,
        )

    def _ensure(self, height: int) -> None:
        if self.y + height > _CONTENT_BOTTOM:
            self._new_page()

    def gap(self, pixels: int = 12) -> None:
        if self.y + pixels <= _CONTENT_BOTTOM:
            self.y += pixels

    def heading(self, text: str) -> None:
        lines = _wrap_text(
            self.draw,
            text,
            _HEADING_FONT,
            _PAGE_SIZE[0] - (2 * _MARGIN_X),
        )
        height = _line_height(_HEADING_FONT)
        for line in lines:
            self._ensure(height)
            self.draw.text(
                (_MARGIN_X, self.y),
                line,
                fill="black",
                font=_HEADING_FONT,
            )
            self.y += height
        self.gap(10)

    def paragraph(
        self,
        text: str,
        *,
        font: Font = _BODY_FONT,
        after: int = 9,
    ) -> None:
        lines = _wrap_text(
            self.draw,
            text,
            font,
            _PAGE_SIZE[0] - (2 * _MARGIN_X),
        )
        height = _line_height(font)
        for line in lines:
            self._ensure(height)
            self.draw.text(
                (_MARGIN_X, self.y),
                line,
                fill="black",
                font=font,
            )
            self.y += height
        self.gap(after)

    def key_values(self, values: Sequence[tuple[str, str]]) -> None:
        for label, value in values:
            self.paragraph(
                f"{label}: {value}",
                font=_BODY_FONT,
                after=4,
            )
        self.gap(6)

    def _table_header(
        self,
        headers: Sequence[str],
        widths: Sequence[int],
    ) -> None:
        wrapped = [
            _wrap_text(self.draw, header, _TABLE_HEADER_FONT, width - 20)
            for header, width in zip(headers, widths, strict=True)
        ]
        line_height = _line_height(_TABLE_HEADER_FONT)
        height = max(len(lines) for lines in wrapped) * line_height + 14
        self._ensure(height)
        x = _MARGIN_X
        for lines, width in zip(wrapped, widths, strict=True):
            self.draw.rectangle(
                (x, self.y, x + width, self.y + height),
                fill=(235, 235, 235),
                outline="black",
                width=1,
            )
            y = self.y + _CELL_PAD_Y
            for line in lines:
                self.draw.text(
                    (x + _CELL_PAD_X, y),
                    line,
                    fill="black",
                    font=_TABLE_HEADER_FONT,
                )
                y += line_height
            x += width
        self.y += height

    def table(
        self,
        headers: Sequence[str],
        rows: Sequence[Sequence[str]],
        ratios: Sequence[int],
    ) -> None:
        available = _PAGE_SIZE[0] - (2 * _MARGIN_X)
        ratio_total = sum(ratios)
        widths = [available * ratio // ratio_total for ratio in ratios]
        widths[-1] += available - sum(widths)
        self._table_header(headers, widths)
        line_height = _line_height(_TABLE_FONT)

        for row in rows:
            wrapped = [
                _wrap_text(self.draw, str(cell), _TABLE_FONT, width - 20)
                for cell, width in zip(row, widths, strict=True)
            ]
            max_lines = max(1, max(len(lines) for lines in wrapped))
            offset = 0
            while offset < max_lines:
                remaining = _CONTENT_BOTTOM - self.y
                max_chunk = (remaining - (2 * _CELL_PAD_Y)) // line_height
                if max_chunk < 1:
                    self._new_page()
                    self._table_header(headers, widths)
                    continue
                chunk = min(max_chunk, max_lines - offset)
                height = chunk * line_height + (2 * _CELL_PAD_Y)
                x = _MARGIN_X
                for lines, width in zip(wrapped, widths, strict=True):
                    self.draw.rectangle(
                        (x, self.y, x + width, self.y + height),
                        outline="black",
                        width=1,
                    )
                    y = self.y + _CELL_PAD_Y
                    for line in lines[offset : offset + chunk]:
                        self.draw.text(
                            (x + _CELL_PAD_X, y),
                            line,
                            fill="black",
                            font=_TABLE_FONT,
                        )
                        y += line_height
                    x += width
                self.y += height
                offset += chunk
                if offset < max_lines:
                    self._new_page()
                    self._table_header(headers, widths)
        self.gap(14)

    def close(self) -> tuple[Image.Image, ...]:
        return tuple(self.images)


def _feedback_images(
    projection: StudentFeedbackProjection,
) -> tuple[Image.Image, ...]:
    painter = _FeedbackPainter(projection)
    painter.heading(projection.student_display_name)
    metadata = [("Activity", projection.activity_title)]
    if projection.class_label is not None:
        metadata.append(("Class", projection.class_label))
    painter.key_values(metadata)

    painter.heading("Current Activity Feedback")
    rows = tuple(
        (
            result.criterion_label,
            result.scoring_scale_name,
            _result_text(result),
        )
        for result in projection.results
    )
    painter.table(
        ("Criterion", "Scoring Scale", "Current result"),
        rows,
        (5, 4, 3),
    )

    painter.heading("About This Feedback")
    painter.paragraph(projection.boundary_statement)
    return painter.close()


def render_student_feedback_pdf(
    render_input: StudentFeedbackRenderInput,
) -> RenderedStudentFeedbackPdf:
    """Render one reviewed share-safe projection to in-memory PDF bytes."""
    if not isinstance(render_input, StudentFeedbackRenderInput):
        raise ConcordWorkflowValidationError(
            "Student feedback PDF requires a planned render input."
        )
    _validate_render_input(render_input)

    images = _feedback_images(render_input.projection)
    page_count = len(images)
    try:
        content = starter_images_to_pdf(
            images,
            created_at=_PDF_CREATED_AT,
        )
    except Exception as error:
        raise ConcordWorkflowValidationError(
            f"Could not render student feedback PDF: {error}"
        ) from error
    finally:
        for image in images:
            image.close()

    if not content.startswith(b"%PDF"):
        raise ConcordWorkflowValidationError(
            "Student feedback renderer did not produce PDF bytes."
        )
    return RenderedStudentFeedbackPdf(
        filename=render_input.filename,
        media_type=STUDENT_FEEDBACK_PDF_MEDIA_TYPE,
        content=content,
        page_count=page_count,
    )


__all__ = [
    "STUDENT_FEEDBACK_PDF_MEDIA_TYPE",
    "RenderedStudentFeedbackPdf",
    "render_student_feedback_pdf",
]
