"Deterministic printable rendering for concord_starter_layout_v1."

from __future__ import annotations

import io
import math
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TypeAlias

import qrcode
from PIL import Image, ImageDraw, ImageFont

from concord.starter_templates.layout import (
    StarterLayoutDocument,
    StarterLayoutPage,
    StarterLayoutSection,
)

RenderScalar: TypeAlias = str | int | bool
Font: TypeAlias = ImageFont.FreeTypeFont | ImageFont.ImageFont

_DPI = 150
_LETTER_PORTRAIT = (1275, 1650)
_LETTER_LANDSCAPE = (1650, 1275)
_MARGIN_X = 72
_MARGIN_TOP = 58
_MARGIN_BOTTOM = 58
_SECTION_GAP = 14
_QR_SIZE = 190


class StarterPdfRenderError(ValueError):
    """A bounded starter layout cannot be rendered safely."""


@dataclass(frozen=True, slots=True, kw_only=True)
class StarterPageRenderContext:
    page_key: str
    values: tuple[tuple[str, RenderScalar], ...]

    def __post_init__(self) -> None:
        if not isinstance(self.page_key, str) or not self.page_key:
            raise StarterPdfRenderError("page_key must be a non-empty string.")
        keys = tuple(item[0] for item in self.values)
        if any(not isinstance(key, str) or not key for key in keys):
            raise StarterPdfRenderError(
                "rendering context keys must be non-empty strings."
            )
        if len(set(keys)) != len(keys):
            raise StarterPdfRenderError(
                "rendering context must not duplicate an input key."
            )
        if any(not isinstance(value, (str, int, bool)) for _, value in self.values):
            raise StarterPdfRenderError(
                "rendering context values must be JSON scalar strings, "
                "integers, or booleans."
            )

    def as_dict(self) -> dict[str, RenderScalar]:
        return dict(self.values)


def render_starter_layout_images(
    layout: StarterLayoutDocument,
    contexts: tuple[StarterPageRenderContext, ...],
) -> tuple[Image.Image, ...]:
    """Render every exact layout page into a copier-friendly RGB sheet."""
    if not isinstance(layout, StarterLayoutDocument):
        raise StarterPdfRenderError("layout must be StarterLayoutDocument.")
    if len(contexts) != len(layout.pages):
        raise StarterPdfRenderError(
            "rendering contexts must match the exact Template page count."
        )
    by_key = {item.page_key: item for item in contexts}
    if len(by_key) != len(contexts):
        raise StarterPdfRenderError(
            "rendering contexts must not duplicate page_key."
        )
    images: list[Image.Image] = []
    for page in layout.pages:
        context = by_key.get(page.page_key)
        if context is None:
            raise StarterPdfRenderError(
                f"missing rendering context for page {page.page_key}."
            )
        images.append(_render_page(page, context.as_dict()))
    return tuple(images)


def starter_images_to_pdf(
    images: tuple[Image.Image, ...],
    *,
    created_at: str,
) -> bytes:
    """Serialize exact rendered sheets to a deterministic PDF byte stream."""
    if not images:
        raise StarterPdfRenderError("PDF rendering requires at least one page.")
    try:
        timestamp = datetime.fromisoformat(created_at)
    except ValueError as error:
        raise StarterPdfRenderError(
            "created_at must be an ISO datetime."
        ) from error
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise StarterPdfRenderError(
            "created_at must include an explicit UTC offset."
        )
    canonical_time = timestamp.astimezone(timezone.utc).timetuple()
    stream = io.BytesIO()
    images[0].save(
        stream,
        "PDF",
        save_all=True,
        append_images=list(images[1:]),
        resolution=float(_DPI),
        creationDate=canonical_time,
        modDate=canonical_time,
    )
    return stream.getvalue()


def render_starter_layout_pdf(
    layout: StarterLayoutDocument,
    contexts: tuple[StarterPageRenderContext, ...],
    *,
    created_at: str,
) -> bytes:
    """Render one exact starter layout directly to deterministic PDF bytes."""
    return starter_images_to_pdf(
        render_starter_layout_images(layout, contexts),
        created_at=created_at,
    )


def _render_page(
    page: StarterLayoutPage,
    values: dict[str, RenderScalar],
) -> Image.Image:
    size = (
        _LETTER_PORTRAIT
        if page.orientation == "portrait"
        else _LETTER_LANDSCAPE
    )
    image = Image.new("RGB", size, "white")
    draw = ImageDraw.Draw(image)
    title_font = ImageFont.load_default(size=30)
    meta_font = ImageFont.load_default(size=18)
    section_font = ImageFont.load_default(size=21)
    body_font = ImageFont.load_default(size=16)
    small_font = ImageFont.load_default(size=14)

    qr_payload = _string_value(values.get("pds2_route_payload"))
    human_fallback = _string_value(values.get("human_fallback"))
    qr_reserved = bool(qr_payload)
    header_right = size[0] - _MARGIN_X - (_QR_SIZE + 26 if qr_reserved else 0)

    title = _printable(page.title)
    _draw_wrapped(
        draw,
        (float(_MARGIN_X), float(_MARGIN_TOP)),
        title,
        title_font,
        header_right - _MARGIN_X,
        max_lines=2,
    )
    title_height = _line_height(title_font) * min(
        2,
        max(1, len(_wrap_text(draw, title, title_font, header_right - _MARGIN_X))),
    )

    meta_top = _MARGIN_TOP + title_height + 12
    metadata = [
        (key, _string_value(values.get(key)))
        for key in page.header_input_keys
        if key != "teacher_prompt" and _string_value(values.get(key))
    ]
    meta_height = _draw_metadata_grid(
        draw,
        metadata,
        left=_MARGIN_X,
        top=meta_top,
        right=header_right,
        font=meta_font,
    )

    prompt = _string_value(values.get("teacher_prompt"))
    prompt_top = meta_top + meta_height + (8 if meta_height else 0)
    prompt_height = 0
    if prompt:
        label = "Prompt / Topic:"
        draw.text(
            (_MARGIN_X, prompt_top),
            label,
            fill="black",
            font=small_font,
        )
        label_width = int(draw.textlength(label, font=small_font)) + 10
        prompt_lines = _wrap_text(
            draw,
            _printable(prompt),
            small_font,
            max(120, header_right - _MARGIN_X - label_width),
        )
        if len(prompt_lines) > 3:
            raise StarterPdfRenderError(
                f"teacher prompt overflows starter page {page.page_key}."
            )
        x = _MARGIN_X + label_width
        for index, line in enumerate(prompt_lines):
            draw.text(
                (x, prompt_top + index * _line_height(small_font)),
                line,
                fill="black",
                font=small_font,
            )
        prompt_height = max(
            _line_height(small_font),
            len(prompt_lines) * _line_height(small_font),
        )

    if qr_payload:
        _draw_qr(
            image,
            qr_payload,
            left=size[0] - _MARGIN_X - _QR_SIZE,
            top=_MARGIN_TOP,
        )

    header_bottom = max(
        _MARGIN_TOP + _QR_SIZE if qr_reserved else _MARGIN_TOP,
        prompt_top + prompt_height,
        meta_top + meta_height,
    )
    header_bottom += 16
    draw.line(
        (_MARGIN_X, header_bottom, size[0] - _MARGIN_X, header_bottom),
        fill="black",
        width=2,
    )

    footer_height = 42 if human_fallback else 18
    body_top = header_bottom + 16
    body_bottom = size[1] - _MARGIN_BOTTOM - footer_height
    if body_bottom - body_top < 300:
        raise StarterPdfRenderError(
            f"starter page {page.page_key} has insufficient writable area."
        )

    _draw_sections(
        draw,
        page.sections,
        left=_MARGIN_X,
        right=size[0] - _MARGIN_X,
        top=body_top,
        bottom=body_bottom,
        section_font=section_font,
        body_font=body_font,
        small_font=small_font,
    )

    if human_fallback:
        fallback = _printable(human_fallback)
        lines = _wrap_text(
            draw,
            "PDS2 fallback: " + fallback,
            small_font,
            size[0] - (2 * _MARGIN_X),
        )
        if len(lines) > 2:
            raise StarterPdfRenderError(
                f"human fallback overflows starter page {page.page_key}."
            )
        y = size[1] - _MARGIN_BOTTOM - len(lines) * _line_height(small_font)
        for line in lines:
            draw.text((_MARGIN_X, y), line, fill="black", font=small_font)
            y += _line_height(small_font)
    return image


def _draw_metadata_grid(
    draw: ImageDraw.ImageDraw,
    metadata: list[tuple[str, str]],
    *,
    left: int,
    top: int,
    right: int,
    font: Font,
) -> int:
    if not metadata:
        return 0
    label_names = {
        "activity_title": "Activity",
        "session_label": "Session",
        "group_label": "Group",
        "participant_display_label": "Participant",
        "current_date": "Date",
    }
    width = right - left
    columns = 2 if width >= 700 else 1
    column_width = width // columns
    rows = (len(metadata) + columns - 1) // columns
    line_height = _line_height(font)
    wrapped: list[tuple[int, int, list[str]]] = []
    row_line_counts = [1 for _ in range(rows)]

    for index, (key, value) in enumerate(metadata):
        row = index // columns
        column = index % columns
        label = label_names.get(key, key.replace("_", " ").title())
        cell_text = f"{label}: {_printable(value)}"
        lines = _wrap_text(draw, cell_text, font, column_width - 18)
        if len(lines) > 2:
            raise StarterPdfRenderError(
                f"header value for {key} exceeds two printable lines."
            )
        wrapped.append((row, column, lines))
        row_line_counts[row] = max(row_line_counts[row], len(lines))

    row_heights = [
        count * line_height + 8
        for count in row_line_counts
    ]
    row_tops: list[int] = []
    cursor = top
    for height in row_heights:
        row_tops.append(cursor)
        cursor += height

    for row, column, lines in wrapped:
        x = left + column * column_width
        y = row_tops[row]
        for line in lines:
            draw.text((x, y), line, fill="black", font=font)
            y += line_height

    return sum(row_heights)


def _section_min_height(
    draw: ImageDraw.ImageDraw,
    section: StarterLayoutSection,
    *,
    width: int,
    section_font: Font,
    body_font: Font,
    small_font: Font,
) -> int:
    inset = 12
    inner_width = width - 2 * inset
    header_height = _section_header_height(
        draw,
        section,
        width=inner_width,
        section_font=section_font,
        small_font=small_font,
    )
    height = 9 + header_height + 7

    height += _section_min_content_height(
        draw,
        section,
        width=inner_width,
        body_font=body_font,
        small_font=small_font,
    )
    return height + inset


def _section_header_height(
    draw: ImageDraw.ImageDraw,
    section: StarterLayoutSection,
    *,
    width: int,
    section_font: Font,
    small_font: Font,
) -> int:
    label = _printable(section.label)
    instructions = _printable(section.instructions or "")
    label_lines = _wrap_text(draw, label, section_font, width)
    if len(label_lines) > 2:
        raise StarterPdfRenderError(
            f"section label overflows {section.section_key}."
        )
    if not instructions:
        return len(label_lines) * _line_height(section_font)

    if len(label_lines) == 1:
        label_width = int(draw.textlength(label, font=section_font))
        instruction_width = max(20, width - label_width - 18)
        instruction_lines = _wrap_text(
            draw,
            instructions,
            small_font,
            instruction_width,
        )
        if len(instruction_lines) == 1:
            return max(
                _line_height(section_font),
                _line_height(small_font),
            )

    instruction_lines = _wrap_text(
        draw,
        instructions,
        small_font,
        width,
    )
    if len(instruction_lines) > 3:
        raise StarterPdfRenderError(
            f"section instructions overflow {section.section_key}."
        )
    return (
        len(label_lines) * _line_height(section_font)
        + 4
        + len(instruction_lines) * _line_height(small_font)
    )


def _section_min_content_height(
    draw: ImageDraw.ImageDraw,
    section: StarterLayoutSection,
    *,
    width: int,
    body_font: Font,
    small_font: Font,
) -> int:
    if section.kind == "instructions":
        return 0
    if section.kind == "response_box":
        return 70
    if section.kind == "table":
        return max(86, _line_height(small_font) * 2 + 64)
    if section.kind == "signature":
        return 58
    if section.kind == "diagram":
        return 110
    if section.kind == "selection":
        checkbox = 20
        gap = 12
        option_gap = 24
        widths = [
            checkbox
            + gap
            + int(
                draw.textlength(
                    _printable(option),
                    font=body_font,
                )
            )
            for option in section.options
        ]
        if sum(widths) + option_gap * max(0, len(widths) - 1) <= width:
            return max(checkbox, _line_height(body_font)) + 8

        text_width = max(20, width - checkbox - gap)
        option_heights = [
            max(
                checkbox,
                len(
                    _wrap_text(
                        draw,
                        _printable(option),
                        body_font,
                        text_width,
                    )
                )
                * _line_height(body_font),
            )
            for option in section.options
        ]
        return (
            4
            + sum(option_heights)
            + 10 * max(0, len(option_heights) - 1)
        )
    raise StarterPdfRenderError(
        f"unsupported starter section kind: {section.kind}"
    )


def _draw_sections(
    draw: ImageDraw.ImageDraw,
    sections: tuple[StarterLayoutSection, ...],
    *,
    left: int,
    right: int,
    top: int,
    bottom: int,
    section_font: Font,
    body_font: Font,
    small_font: Font,
) -> None:
    total_gap = _SECTION_GAP * max(0, len(sections) - 1)
    available = bottom - top - total_gap
    total_weight = sum(item.weight for item in sections)
    if available <= 0 or total_weight <= 0:
        raise StarterPdfRenderError("starter sections have no printable area.")

    minimums = [
        _section_min_height(
            draw,
            section,
            width=right - left,
            section_font=section_font,
            body_font=body_font,
            small_font=small_font,
        )
        for section in sections
    ]
    minimum_total = sum(minimums)
    if minimum_total > available:
        raise StarterPdfRenderError(
            "starter sections cannot fit their minimum printable geometry."
        )

    remaining = available - minimum_total
    extras = [
        int(remaining * item.weight / total_weight)
        for item in sections
    ]
    extras[-1] += remaining - sum(extras)
    heights = [
        minimum + extra
        for minimum, extra in zip(minimums, extras, strict=True)
    ]

    y = top
    for section, height in zip(sections, heights, strict=True):
        _draw_section(
            draw,
            section,
            left=left,
            right=right,
            top=y,
            bottom=y + height,
            section_font=section_font,
            body_font=body_font,
            small_font=small_font,
        )
        y += height + _SECTION_GAP


def _draw_section(
    draw: ImageDraw.ImageDraw,
    section: StarterLayoutSection,
    *,
    left: int,
    right: int,
    top: int,
    bottom: int,
    section_font: Font,
    body_font: Font,
    small_font: Font,
) -> None:
    draw.rectangle((left, top, right, bottom), outline="black", width=2)
    inset = 12
    x = left + inset
    y = top + 9
    width = right - left - 2 * inset
    label = _printable(section.label)
    instructions = _printable(section.instructions or "")
    label_lines = _wrap_text(draw, label, section_font, width)
    if len(label_lines) > 2:
        raise StarterPdfRenderError(
            f"section label overflows {section.section_key}."
        )

    inline_instructions = False
    if instructions and len(label_lines) == 1:
        label_width = int(draw.textlength(label, font=section_font))
        instruction_width = max(20, width - label_width - 18)
        instruction_lines = _wrap_text(
            draw,
            instructions,
            small_font,
            instruction_width,
        )
        inline_instructions = len(instruction_lines) == 1
    else:
        instruction_lines = []

    if inline_instructions:
        draw.text((x, y), label, fill="black", font=section_font)
        label_width = int(draw.textlength(label, font=section_font))
        draw.text(
            (x + label_width + 18, y + 2),
            instruction_lines[0],
            fill="black",
            font=small_font,
        )
        y += max(
            _line_height(section_font),
            _line_height(small_font),
        ) + 7
    else:
        label_count = _draw_wrapped(
            draw,
            (float(x), float(y)),
            label,
            section_font,
            width,
            max_lines=2,
        )
        y += label_count * _line_height(section_font) + 4
        if instructions:
            instruction_count = _draw_wrapped(
                draw,
                (float(x), float(y)),
                instructions,
                small_font,
                width,
                max_lines=3,
            )
            y += instruction_count * _line_height(small_font) + 7

    if section.kind == "instructions":
        return

    content_top = y
    content_bottom = bottom - inset
    if content_bottom - content_top < 26:
        raise StarterPdfRenderError(
            f"section {section.section_key} has no usable content area."
        )
    if section.kind == "response_box":
        _draw_ruled_area(
            draw,
            left=x,
            right=right - inset,
            top=content_top,
            bottom=content_bottom,
        )
        return
    if section.kind == "table":
        _draw_table(
            draw,
            section,
            left=x,
            right=right - inset,
            top=content_top,
            bottom=content_bottom,
            font=small_font,
        )
        return
    if section.kind == "selection":
        _draw_selection(
            draw,
            section,
            left=x,
            right=right - inset,
            top=content_top,
            bottom=content_bottom,
            font=body_font,
        )
        return
    if section.kind == "signature":
        _draw_signature(
            draw,
            left=x,
            right=right - inset,
            top=content_top,
            bottom=content_bottom,
            font=small_font,
        )
        return
    if section.kind == "diagram":
        _draw_diagram(
            draw,
            section,
            left=x,
            right=right - inset,
            top=content_top,
            bottom=content_bottom,
            font=small_font,
        )
        return
    raise StarterPdfRenderError(
        f"unsupported starter section kind: {section.kind}"
    )


def _draw_ruled_area(
    draw: ImageDraw.ImageDraw,
    *,
    left: int,
    right: int,
    top: int,
    bottom: int,
) -> None:
    spacing = 34
    y = top + spacing
    while y < bottom:
        draw.line((left, y, right, y), fill="black", width=1)
        y += spacing


def _draw_table(
    draw: ImageDraw.ImageDraw,
    section: StarterLayoutSection,
    *,
    left: int,
    right: int,
    top: int,
    bottom: int,
    font: Font,
) -> None:
    columns = section.columns
    column_width = (right - left) / len(columns)
    header_height = max(34, _line_height(font) + 12)
    draw.rectangle((left, top, right, bottom), outline="black", width=1)
    for index in range(1, len(columns)):
        x = int(left + index * column_width)
        draw.line((x, top, x, bottom), fill="black", width=1)
    draw.line(
        (left, top + header_height, right, top + header_height),
        fill="black",
        width=1,
    )
    for index, column in enumerate(columns):
        cell_left = int(left + index * column_width) + 7
        cell_right = int(left + (index + 1) * column_width) - 7
        lines = _wrap_text(
            draw,
            _printable(column),
            font,
            max(20, cell_right - cell_left),
        )
        if len(lines) > 2:
            raise StarterPdfRenderError(
                f"table column label overflows section {section.section_key}."
            )
        y = top + 6
        for line in lines:
            draw.text((cell_left, y), line, fill="black", font=font)
            y += _line_height(font)
    body_top = top + header_height
    row_height = 52
    y = body_top + row_height
    while y < bottom:
        draw.line((left, y, right, y), fill="black", width=1)
        y += row_height


def _draw_selection(
    draw: ImageDraw.ImageDraw,
    section: StarterLayoutSection,
    *,
    left: int,
    right: int,
    top: int,
    bottom: int,
    font: Font,
) -> None:
    checkbox = 20
    gap = 12
    option_gap = 24
    printable_options = [_printable(option) for option in section.options]
    widths = [
        checkbox + gap + int(draw.textlength(option, font=font))
        for option in printable_options
    ]
    total_width = sum(widths) + option_gap * max(0, len(widths) - 1)

    if total_width <= right - left:
        height = max(checkbox, _line_height(font))
        if top + 4 + height > bottom:
            raise StarterPdfRenderError(
                f"selection options overflow section {section.section_key}."
            )
        x = left
        y = top + 4
        for option, width in zip(
            printable_options,
            widths,
            strict=True,
        ):
            draw.rectangle(
                (x, y, x + checkbox, y + checkbox),
                outline="black",
                width=2,
            )
            draw.text(
                (x + checkbox + gap, y),
                option,
                fill="black",
                font=font,
            )
            x += width + option_gap
        return

    y = top + 4
    max_width = right - left - checkbox - gap
    for option in printable_options:
        lines = _wrap_text(draw, option, font, max_width)
        height = max(checkbox, len(lines) * _line_height(font))
        if y + height > bottom:
            raise StarterPdfRenderError(
                f"selection options overflow section {section.section_key}."
            )
        draw.rectangle(
            (left, y, left + checkbox, y + checkbox),
            outline="black",
            width=2,
        )
        text_y = y
        for line in lines:
            draw.text(
                (left + checkbox + gap, text_y),
                line,
                fill="black",
                font=font,
            )
            text_y += _line_height(font)
        y += height + 10


def _draw_signature(
    draw: ImageDraw.ImageDraw,
    *,
    left: int,
    right: int,
    top: int,
    bottom: int,
    font: Font,
) -> None:
    available = bottom - top
    if available < 50:
        raise StarterPdfRenderError("signature area is too small.")
    first_y = top + available // 3
    second_y = top + (2 * available) // 3
    draw.line((left, first_y, right, first_y), fill="black", width=1)
    draw.text(
        (left, first_y + 4),
        "Signature / Name",
        fill="black",
        font=font,
    )
    draw.line((left, second_y, right, second_y), fill="black", width=1)
    draw.text((left, second_y + 4), "Date / Note", fill="black", font=font)


def _draw_diagram(
    draw: ImageDraw.ImageDraw,
    section: StarterLayoutSection,
    *,
    left: int,
    right: int,
    top: int,
    bottom: int,
    font: Font,
) -> None:
    kind = section.diagram_kind
    if kind == "venn":
        _draw_venn(draw, left, right, top, bottom)
    elif kind == "concept_map":
        _draw_concept_map(draw, left, right, top, bottom)
    elif kind == "annotation_canvas":
        _draw_annotation_canvas(draw, left, right, top, bottom, font)
    elif kind == "process_flow":
        _draw_process_flow(draw, left, right, top, bottom)
    else:
        raise StarterPdfRenderError(
            f"unsupported starter diagram kind: {kind}"
        )


def _venn_circle_bounds(
    left: int,
    right: int,
    top: int,
    bottom: int,
) -> tuple[tuple[int, int, int, int], tuple[int, int, int, int]]:
    width = right - left
    height = bottom - top
    padding_x = max(12, width // 28)
    padding_y = max(12, height // 18)
    usable_width = max(120, width - 2 * padding_x)
    usable_height = max(120, height - 2 * padding_y)

    radius = int(min(usable_height / 2.1, usable_width / 3.05))
    center_gap = int(radius * 1.05)
    cy = top + height // 2
    midpoint = left + width // 2
    first_cx = midpoint - center_gap // 2
    second_cx = midpoint + center_gap // 2

    first = (
        first_cx - radius,
        cy - radius,
        first_cx + radius,
        cy + radius,
    )
    second = (
        second_cx - radius,
        cy - radius,
        second_cx + radius,
        cy + radius,
    )
    return first, second


def _draw_venn(
    draw: ImageDraw.ImageDraw,
    left: int,
    right: int,
    top: int,
    bottom: int,
) -> None:
    for bounds in _venn_circle_bounds(left, right, top, bottom):
        draw.ellipse(bounds, outline="black", width=2)


def _draw_concept_map(
    draw: ImageDraw.ImageDraw,
    left: int,
    right: int,
    top: int,
    bottom: int,
) -> None:
    width = right - left
    height = bottom - top
    cx = left + width // 2
    cy = top + height // 2
    center_w = max(120, width // 5)
    center_h = max(54, height // 5)
    center = (
        cx - center_w // 2,
        cy - center_h // 2,
        cx + center_w // 2,
        cy + center_h // 2,
    )
    box_w = max(120, width // 5)
    box_h = max(50, height // 6)
    boxes = (
        (left + 10, top + 10, left + 10 + box_w, top + 10 + box_h),
        (right - 10 - box_w, top + 10, right - 10, top + 10 + box_h),
        (
            left + 10,
            bottom - 10 - box_h,
            left + 10 + box_w,
            bottom - 10,
        ),
        (
            right - 10 - box_w,
            bottom - 10 - box_h,
            right - 10,
            bottom - 10,
        ),
    )

    for box in boxes:
        bx = (box[0] + box[2]) // 2
        by = (box[1] + box[3]) // 2
        start_x, start_y = _ellipse_boundary_point(center, (bx, by))
        end_x, end_y = _rectangle_boundary_point(box, (cx, cy))
        draw.line((start_x, start_y, end_x, end_y), fill="black", width=1)

    draw.ellipse(center, outline="black", width=2)
    for box in boxes:
        draw.rectangle(box, outline="black", width=2)



def _ellipse_boundary_point(
    bounds: tuple[int, int, int, int],
    target: tuple[int, int],
) -> tuple[int, int]:
    center_x = (bounds[0] + bounds[2]) / 2.0
    center_y = (bounds[1] + bounds[3]) / 2.0
    radius_x = max(1.0, (bounds[2] - bounds[0]) / 2.0)
    radius_y = max(1.0, (bounds[3] - bounds[1]) / 2.0)
    delta_x = target[0] - center_x
    delta_y = target[1] - center_y
    if delta_x == 0 and delta_y == 0:
        return round(center_x), round(center_y)
    scale = 1.0 / math.sqrt(
        (delta_x * delta_x) / (radius_x * radius_x)
        + (delta_y * delta_y) / (radius_y * radius_y)
    )
    return (
        round(center_x + delta_x * scale),
        round(center_y + delta_y * scale),
    )



def _rectangle_boundary_point(
    bounds: tuple[int, int, int, int],
    target: tuple[int, int],
) -> tuple[int, int]:
    center_x = (bounds[0] + bounds[2]) / 2.0
    center_y = (bounds[1] + bounds[3]) / 2.0
    delta_x = target[0] - center_x
    delta_y = target[1] - center_y
    if delta_x == 0 and delta_y == 0:
        return round(center_x), round(center_y)

    scales: list[float] = []
    if delta_x > 0:
        scales.append((bounds[2] - center_x) / delta_x)
    elif delta_x < 0:
        scales.append((bounds[0] - center_x) / delta_x)
    if delta_y > 0:
        scales.append((bounds[3] - center_y) / delta_y)
    elif delta_y < 0:
        scales.append((bounds[1] - center_y) / delta_y)

    positive = [value for value in scales if value > 0]
    if not positive:
        return round(center_x), round(center_y)
    scale = min(positive)
    return (
        round(center_x + delta_x * scale),
        round(center_y + delta_y * scale),
    )


def _draw_annotation_canvas(
    draw: ImageDraw.ImageDraw,
    left: int,
    right: int,
    top: int,
    bottom: int,
    font: Font,
) -> None:
    split = left + int((right - left) * 0.70)
    draw.rectangle((left, top, right, bottom), outline="black", width=1)
    draw.line((split, top, split, bottom), fill="black", width=1)
    draw.text((left + 8, top + 7), "Text / Source", fill="black", font=font)
    draw.text(
        (split + 8, top + 7),
        "Notes / Connections",
        fill="black",
        font=font,
    )


def _draw_process_flow(
    draw: ImageDraw.ImageDraw,
    left: int,
    right: int,
    top: int,
    bottom: int,
) -> None:
    width = right - left
    height = bottom - top
    horizontal = width >= height * 1.35
    count = 4
    if horizontal:
        gap = max(24, width // 25)
        box_w = (width - gap * (count - 1)) // count
        box_h = max(52, int(height * 0.62))
        y = top + (height - box_h) // 2
        boxes = []
        for index in range(count):
            x = left + index * (box_w + gap)
            boxes.append((x, y, x + box_w, y + box_h))
        for index, box in enumerate(boxes):
            draw.rectangle(box, outline="black", width=2)
            if index < len(boxes) - 1:
                x1 = box[2]
                x2 = boxes[index + 1][0]
                cy = (box[1] + box[3]) // 2
                _draw_arrow(draw, x1 + 3, cy, x2 - 3, cy)
    else:
        gap = max(16, height // 30)
        box_h = (height - gap * (count - 1)) // count
        box_w = max(120, int(width * 0.72))
        x = left + (width - box_w) // 2
        boxes = []
        for index in range(count):
            y = top + index * (box_h + gap)
            boxes.append((x, y, x + box_w, y + box_h))
        for index, box in enumerate(boxes):
            draw.rectangle(box, outline="black", width=2)
            if index < len(boxes) - 1:
                y1 = box[3]
                y2 = boxes[index + 1][1]
                cx = (box[0] + box[2]) // 2
                _draw_arrow(draw, cx, y1 + 3, cx, y2 - 3)


def _draw_arrow(
    draw: ImageDraw.ImageDraw,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
) -> None:
    draw.line((x1, y1, x2, y2), fill="black", width=2)
    if abs(x2 - x1) >= abs(y2 - y1):
        direction = 1 if x2 >= x1 else -1
        draw.polygon(
            (
                (x2, y2),
                (x2 - direction * 10, y2 - 6),
                (x2 - direction * 10, y2 + 6),
            ),
            fill="black",
        )
    else:
        direction = 1 if y2 >= y1 else -1
        draw.polygon(
            (
                (x2, y2),
                (x2 - 6, y2 - direction * 10),
                (x2 + 6, y2 - direction * 10),
            ),
            fill="black",
        )


def _draw_qr(
    image: Image.Image,
    payload: str,
    *,
    left: int,
    top: int,
) -> None:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=3,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    rendered = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    rendered = rendered.resize(
        (_QR_SIZE, _QR_SIZE),
        resample=Image.Resampling.NEAREST,
    )
    image.paste(rendered, (left, top))


def _draw_wrapped(
    draw: ImageDraw.ImageDraw,
    position: tuple[float, float],
    text: str,
    font: Font,
    max_width: int,
    *,
    max_lines: int,
) -> int:
    lines = _wrap_text(draw, text, font, max_width)
    if len(lines) > max_lines:
        raise StarterPdfRenderError("text would clip in a bounded printable region.")
    x, y = position
    for line in lines:
        draw.text((x, y), line, fill="black", font=font)
        y += _line_height(font)
    return max(1, len(lines))


def _wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: Font,
    max_width: int,
) -> list[str]:
    normalized = _printable(text).replace("\r\n", "\n").replace("\r", "\n")
    if not normalized:
        return [""]
    lines: list[str] = []
    for paragraph in normalized.split("\n"):
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        current = words[0]
        if draw.textlength(current, font=font) > max_width:
            raise StarterPdfRenderError("one word exceeds the printable text width.")
        for word in words[1:]:
            candidate = current + " " + word
            if draw.textlength(candidate, font=font) <= max_width:
                current = candidate
                continue
            lines.append(current)
            current = word
            if draw.textlength(current, font=font) > max_width:
                raise StarterPdfRenderError(
                    "one word exceeds the printable text width."
                )
        lines.append(current)
    return lines


def _line_height(font: Font) -> int:
    box = font.getbbox("Ag")
    return int(max(1, box[3] - box[1] + 4))


def _string_value(value: RenderScalar | None) -> str:
    return "" if value is None else str(value)


def _printable(value: str) -> str:
    replacements = {
        "\u2013": "-",
        "\u2014": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2026": "...",
        "\u00a0": " ",
        "\u00d7": "x",
        "\u2192": "->",
        "\u2022": "*",
    }
    normalized = value
    for old, new in replacements.items():
        normalized = normalized.replace(old, new)
    return unicodedata.normalize("NFKD", normalized).encode(
        "ascii", "ignore"
    ).decode("ascii")


__all__ = [
    "StarterPageRenderContext",
    "StarterPdfRenderError",
    "render_starter_layout_images",
    "render_starter_layout_pdf",
    "starter_images_to_pdf",
]
