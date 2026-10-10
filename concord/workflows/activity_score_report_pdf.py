"""Readable paginated PDF rendering for Concord Activity Score reports."""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Final

from PIL import Image, ImageDraw, ImageFont

from concord.routing.starter_layout_pdf import starter_images_to_pdf
from concord.standards_display import format_standard_display_label
from concord.workflows.activity_score_report_output import (
    RenderedScoreAnalysisArtifact,
    RenderedScoreAnalysisReport,
    ScoreAnalysisReportOutputError,
)
from concord.workflows.activity_score_reports import (
    ActivityAnalysisReport,
    PreparedScoreAnalysisReport,
    TargetDetailReport,
)

PDF_MEDIA_TYPE: Final[str] = "application/pdf"
_PAGE_SIZE: Final[tuple[int, int]] = (1275, 1650)
_MARGIN_X: Final[int] = 82
_MARGIN_TOP: Final[int] = 72
_MARGIN_BOTTOM: Final[int] = 70
_HEADER_BOTTOM: Final[int] = 150
_CONTENT_BOTTOM: Final[int] = _PAGE_SIZE[1] - _MARGIN_BOTTOM
_CELL_PAD_X: Final[int] = 10
_CELL_PAD_Y: Final[int] = 7

Font = ImageFont.FreeTypeFont | ImageFont.ImageFont


def _font(size: int) -> Font:
    return ImageFont.load_default(size=size)


_SUBTITLE_FONT = _font(21)
_HEADING_FONT = _font(22)
_BODY_FONT = _font(17)
_SMALL_FONT = _font(14)
_TABLE_FONT = _font(14)
_TABLE_HEADER_FONT = _font(14)


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


def _result_text(
    disposition: str,
    value: object,
    value_label: str | None,
) -> str:
    if disposition != "scored":
        return disposition.replace("_", " ")
    rendered = _scalar(value)
    return rendered if value_label is None else f"{rendered} - {value_label}"


class _ReportPainter:
    def __init__(self, *, report_title: str, activity_title: str) -> None:
        self.report_title = report_title
        self.activity_title = activity_title
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
            self.report_title,
            fill="black",
            font=_SUBTITLE_FONT,
        )
        activity_lines = _wrap_text(
            self.draw,
            self.activity_title,
            _SMALL_FONT,
            _PAGE_SIZE[0] - (2 * _MARGIN_X) - 160,
        )
        activity = activity_lines[0]
        if len(activity_lines) > 1:
            activity += "..."
        self.draw.text(
            (_MARGIN_X, _MARGIN_TOP + 36),
            activity,
            fill="black",
            font=_SMALL_FONT,
        )
        page_label = f"Page {page_number}"
        label_width = int(self.draw.textlength(page_label, font=_SMALL_FONT))
        self.draw.text(
            (_PAGE_SIZE[0] - _MARGIN_X - label_width, _MARGIN_TOP),
            page_label,
            fill="black",
            font=_SMALL_FONT,
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
        line_height = _line_height(_HEADING_FONT)
        for line in lines:
            self._ensure(line_height)
            self.draw.text(
                (_MARGIN_X, self.y),
                line,
                fill="black",
                font=_HEADING_FONT,
            )
            self.y += line_height
        self.gap(12)

    def paragraph(
        self,
        text: str,
        *,
        font: Font = _BODY_FONT,
        indent: int = 0,
        after: int = 9,
    ) -> None:
        width = _PAGE_SIZE[0] - (2 * _MARGIN_X) - indent
        lines = _wrap_text(self.draw, text, font, width)
        line_height = _line_height(font)
        for line in lines:
            self._ensure(line_height)
            self.draw.text(
                (_MARGIN_X + indent, self.y),
                line,
                fill="black",
                font=font,
            )
            self.y += line_height
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
                remaining_height = _CONTENT_BOTTOM - self.y
                max_chunk = (
                    remaining_height - (2 * _CELL_PAD_Y)
                ) // line_height
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


def _activity_images(payload: ActivityAnalysisReport) -> tuple[Image.Image, ...]:
    painter = _ReportPainter(
        report_title="Concord Activity Score Analysis",
        activity_title=payload.activity_title,
    )
    standard_labels = {
        item.standard_id: format_standard_display_label(
            item.standard_id,
            code=item.standard_code,
            short_name=item.standard_short_name,
        )
        for item in payload.standard_analyses
    }
    painter.heading(payload.activity_title)
    painter.key_values(
        (
            ("Class", payload.metadata.class_id),
            ("Activity ID", payload.metadata.activity_id),
            ("Generated", payload.metadata.generated_at),
            ("Score basis", payload.metadata.score_basis),
            ("Current Score records", str(payload.current_score_count)),
        )
    )

    painter.heading("Activity Overview")
    target_rows = tuple(
        (item.target_kind, str(item.score_count))
        for item in payload.target_kind_counts
    )
    if not target_rows:
        target_rows = (("No represented target kind", "0"),)
    painter.table(
        ("Target kind", "Current Score records"),
        target_rows,
        (3, 2),
    )
    painter.key_values(
        (
            ("Criteria represented", str(payload.represented_criterion_count)),
            (
                "Scoring Scales represented",
                str(payload.represented_scoring_scale_count),
            ),
        )
    )

    painter.heading("Criterion Analysis")
    if not payload.criterion_analyses:
        painter.paragraph("No current Criterion Score records are represented.")
    for criterion in payload.criterion_analyses:
        painter.paragraph(
            criterion.criterion_label,
            font=_SUBTITLE_FONT,
            after=4,
        )
        painter.paragraph(
            (
                f"Criterion ID: {criterion.criterion_id} | "
                f"Kind: {criterion.criterion_kind} | "
                f"Current judgments: {criterion.current_judgment_count}"
            ),
            font=_SMALL_FONT,
            after=8,
        )
        if criterion.standard_id is not None:
            painter.paragraph(
                "Standard: "
                + standard_labels.get(
                    criterion.standard_id,
                    criterion.standard_id,
                ),
                font=_SMALL_FONT,
                after=8,
            )
        for item in criterion.slices:
            painter.paragraph(
                (
                    f"{item.target_kind} | {item.scoring_scale_name} "
                    f"(rev {item.scoring_scale_revision}) | "
                    f"{item.current_judgment_count} current judgment(s)"
                ),
                font=_BODY_FONT,
                after=5,
            )
            value_rows = tuple(
                (
                    f"{_scalar(value.value)} - {value.label}",
                    str(value.count),
                    str(value.denominator),
                    f"{value.percentage}%",
                )
                for value in item.value_distributions
            )
            if value_rows:
                painter.table(
                    ("Scale value", "Count", "Scored denom.", "Percent"),
                    value_rows,
                    (5, 2, 2, 2),
                )
            disposition_rows = tuple(
                (
                    value.disposition.replace("_", " "),
                    str(value.count),
                    str(value.denominator),
                    f"{value.percentage}%",
                )
                for value in item.disposition_distributions
            )
            if disposition_rows:
                painter.table(
                    ("Disposition", "Count", "Current denom.", "Percent"),
                    disposition_rows,
                    (5, 2, 2, 2),
                )

    if payload.standard_analyses:
        painter.heading("Standards / Criterion View")
        rows = tuple(
            (
                format_standard_display_label(
                    standard.standard_id,
                    code=standard.standard_code,
                    short_name=standard.standard_short_name,
                ),
                criterion.criterion_label,
                item.target_kind,
                (
                    f"{item.scoring_scale_name} "
                    f"(rev {item.scoring_scale_revision})"
                ),
                str(item.current_judgment_count),
            )
            for standard in payload.standard_analyses
            for criterion in standard.criteria
            for item in criterion.slices
        )
        painter.table(
            ("Standard", "Criterion", "Target", "Scale", "Current"),
            rows,
            (3, 4, 2, 3, 1),
        )

    painter.heading("Report Boundary")
    for statement in payload.boundary_statements:
        painter.paragraph(statement)
    return painter.close()


def _target_images(payload: TargetDetailReport) -> tuple[Image.Image, ...]:
    detail = payload.target_detail
    painter = _ReportPainter(
        report_title="Concord Target Detail",
        activity_title=payload.activity_title,
    )
    painter.heading(detail.target_label)
    painter.key_values(
        (
            ("Activity", payload.activity_title),
            ("Class", payload.metadata.class_id),
            ("Target kind", detail.target_reference.target_kind),
            ("Generated", payload.metadata.generated_at),
            ("Score basis", payload.metadata.score_basis),
            ("Current Score records", str(detail.current_score_count)),
        )
    )

    painter.heading("Current Criterion Scores")
    rows = tuple(
        (
            item.criterion_label,
            f"{item.scoring_scale_name} (rev {item.scoring_scale_revision})",
            _result_text(item.disposition, item.value, item.value_label),
            item.scored_at,
        )
        for item in detail.results
    )
    if rows:
        painter.table(
            ("Criterion", "Scale", "Result", "Recorded"),
            rows,
            (4, 3, 3, 3),
        )
    else:
        painter.paragraph("No current Score records are recorded for this target.")

    painter.heading("Report Boundary")
    for statement in payload.boundary_statements:
        painter.paragraph(statement)
    return painter.close()


def render_score_analysis_report_pdf(
    prepared: PreparedScoreAnalysisReport,
) -> RenderedScoreAnalysisReport:
    """Render one prepared descriptive report as a readable paginated PDF."""
    if prepared.report_format != "pdf":
        raise ScoreAnalysisReportOutputError(
            "PDF rendering requires a prepared PDF report."
        )

    payload = prepared.payload
    if isinstance(payload, ActivityAnalysisReport):
        images = _activity_images(payload)
        filename = "activity_analysis.pdf"
        created_at = payload.metadata.generated_at
    elif isinstance(payload, TargetDetailReport):
        images = _target_images(payload)
        filename = "target_detail.pdf"
        created_at = payload.metadata.generated_at
    else:
        raise ScoreAnalysisReportOutputError(
            "Prepared report payload is unsupported."
        )

    try:
        content = starter_images_to_pdf(images, created_at=created_at)
    except Exception as error:
        raise ScoreAnalysisReportOutputError(
            f"Could not render Score Analysis PDF: {error}"
        ) from error
    finally:
        for image in images:
            image.close()

    if not content.startswith(b"%PDF"):
        raise ScoreAnalysisReportOutputError(
            "Score Analysis PDF renderer did not produce PDF bytes."
        )
    return RenderedScoreAnalysisReport(
        report_scope=prepared.report_scope,
        report_format="pdf",
        artifacts=(
            RenderedScoreAnalysisArtifact(
                filename=filename,
                media_type=PDF_MEDIA_TYPE,
                content=content,
            ),
        ),
    )


__all__ = [
    "PDF_MEDIA_TYPE",
    "render_score_analysis_report_pdf",
]
