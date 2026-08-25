"""Strict non-executable layout contract for packaged starter Templates."""

from __future__ import annotations

import re
from dataclasses import dataclass

from concord.template_serialization import (
    TemplateSerializationError,
    canonical_json_bytes,
    dataclass_from_dict,
    dataclass_to_dict,
    strict_json_loads,
)

STARTER_LAYOUT_SCHEMA = "concord_starter_layout_v1"
STARTER_PAPER_SIZES = frozenset({"letter"})
STARTER_ORIENTATIONS = frozenset({"portrait", "landscape"})
STARTER_SECTION_KINDS = frozenset(
    {
        "instructions",
        "response_box",
        "table",
        "diagram",
        "selection",
        "signature",
    }
)
STARTER_REGION_KINDS = frozenset(
    {
        "free_response",
        "structured_entry",
        "selection",
        "table",
        "drawing",
        "annotation",
        "teacher_observation",
    }
)
STARTER_DIAGRAM_KINDS = frozenset(
    {
        "venn",
        "concept_map",
        "annotation_canvas",
        "process_flow",
    }
)
STARTER_HEADER_INPUT_KEYS = frozenset(
    {
        "activity_title",
        "session_label",
        "group_label",
        "participant_display_label",
        "current_date",
        "teacher_prompt",
    }
)
_LOCAL_KEY = re.compile(r"^[a-z][a-z0-9_]*$")


class StarterLayoutError(ValueError):
    """A packaged starter layout is invalid or noncanonical."""


def _text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StarterLayoutError(f"{field_name} must be a non-empty string.")
    if value != value.strip():
        raise StarterLayoutError(
            f"{field_name} must not contain surrounding whitespace."
        )
    return value


def _optional_text(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    return _text(value, field_name)


def _key(value: object, field_name: str) -> str:
    text = _text(value, field_name)
    if _LOCAL_KEY.fullmatch(text) is None:
        raise StarterLayoutError(
            f"{field_name} must be a lowercase local key using underscores."
        )
    return text


def _positive(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise StarterLayoutError(f"{field_name} must be a positive integer.")
    return value


@dataclass(frozen=True, slots=True, kw_only=True)
class StarterLayoutSection:
    """One bounded visual section on a starter paper page."""

    section_key: str
    kind: str
    label: str
    weight: int = 1
    instructions: str | None = None
    region_key: str | None = None
    region_kind: str | None = None
    required: bool = False
    columns: tuple[str, ...] = ()
    options: tuple[str, ...] = ()
    diagram_kind: str | None = None

    def __post_init__(self) -> None:
        _key(self.section_key, "section_key")
        kind = _text(self.kind, "kind")
        if kind not in STARTER_SECTION_KINDS:
            raise StarterLayoutError(
                "kind must be one of "
                + ", ".join(sorted(STARTER_SECTION_KINDS))
                + "."
            )
        _text(self.label, "label")
        _positive(self.weight, "weight")
        _optional_text(self.instructions, "instructions")
        if not isinstance(self.required, bool):
            raise StarterLayoutError("required must be a boolean.")
        columns = tuple(_text(item, "columns[]") for item in self.columns)
        options = tuple(_text(item, "options[]") for item in self.options)
        object.__setattr__(self, "columns", columns)
        object.__setattr__(self, "options", options)

        if kind == "instructions":
            if self.region_key is not None or self.region_kind is not None:
                raise StarterLayoutError(
                    "instruction sections must not declare response regions."
                )
            if self.instructions is None:
                raise StarterLayoutError(
                    "instruction sections require instructions text."
                )
        else:
            if self.region_key is None or self.region_kind is None:
                raise StarterLayoutError(
                    "writable sections require region_key and region_kind."
                )
            _key(self.region_key, "region_key")
            region_kind = _text(self.region_kind, "region_kind")
            if region_kind not in STARTER_REGION_KINDS:
                raise StarterLayoutError(
                    "region_kind must be a supported Template response kind."
                )

        if kind == "table" and len(columns) < 2:
            raise StarterLayoutError(
                "table sections require at least two column labels."
            )
        if kind != "table" and columns:
            raise StarterLayoutError(
                "only table sections may declare column labels."
            )
        if kind == "selection" and len(options) < 2:
            raise StarterLayoutError(
                "selection sections require at least two options."
            )
        if kind != "selection" and options:
            raise StarterLayoutError(
                "only selection sections may declare options."
            )
        if kind == "diagram":
            if self.diagram_kind not in STARTER_DIAGRAM_KINDS:
                raise StarterLayoutError(
                    "diagram sections require a supported diagram_kind."
                )
        elif self.diagram_kind is not None:
            raise StarterLayoutError(
                "only diagram sections may declare diagram_kind."
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class StarterLayoutPage:
    """One deterministic US-Letter starter layout page."""

    page_key: str
    sequence: int
    title: str
    orientation: str
    header_input_keys: tuple[str, ...]
    sections: tuple[StarterLayoutSection, ...]

    def __post_init__(self) -> None:
        _key(self.page_key, "page_key")
        _positive(self.sequence, "sequence")
        _text(self.title, "title")
        if self.orientation not in STARTER_ORIENTATIONS:
            raise StarterLayoutError(
                "orientation must be portrait or landscape."
            )
        inputs = tuple(self.header_input_keys)
        if len(set(inputs)) != len(inputs):
            raise StarterLayoutError(
                "header_input_keys must not contain duplicates."
            )
        for key in inputs:
            if key not in STARTER_HEADER_INPUT_KEYS:
                raise StarterLayoutError(
                    f"unsupported header input key: {key}"
                )
        object.__setattr__(self, "header_input_keys", inputs)

        sections = tuple(self.sections)
        if not sections:
            raise StarterLayoutError("starter pages require sections.")
        if any(
            not isinstance(item, StarterLayoutSection)
            for item in sections
        ):
            raise StarterLayoutError(
                "sections must contain StarterLayoutSection values."
            )
        section_keys = tuple(item.section_key for item in sections)
        if len(set(section_keys)) != len(section_keys):
            raise StarterLayoutError(
                "section_key values must be unique within a page."
            )
        object.__setattr__(self, "sections", sections)


@dataclass(frozen=True, slots=True, kw_only=True)
class StarterLayoutDocument:
    """One complete non-executable starter rendering specification."""

    schema_version: str
    paper_size: str
    pages: tuple[StarterLayoutPage, ...]

    def __post_init__(self) -> None:
        if self.schema_version != STARTER_LAYOUT_SCHEMA:
            raise StarterLayoutError(
                f"schema_version must be {STARTER_LAYOUT_SCHEMA!r}."
            )
        if self.paper_size not in STARTER_PAPER_SIZES:
            raise StarterLayoutError("paper_size must be letter.")
        pages = tuple(self.pages)
        if not pages:
            raise StarterLayoutError("starter layout requires at least one page.")
        if any(not isinstance(item, StarterLayoutPage) for item in pages):
            raise StarterLayoutError(
                "pages must contain StarterLayoutPage values."
            )
        pages = tuple(sorted(pages, key=lambda item: item.sequence))
        sequences = tuple(item.sequence for item in pages)
        if sequences != tuple(range(1, len(pages) + 1)):
            raise StarterLayoutError(
                "page sequences must form contiguous 1..N order."
            )
        page_keys = tuple(item.page_key for item in pages)
        if len(set(page_keys)) != len(page_keys):
            raise StarterLayoutError("page_key values must be unique.")
        region_keys = [
            section.region_key
            for page in pages
            for section in page.sections
            if section.region_key is not None
        ]
        if len(set(region_keys)) != len(region_keys):
            raise StarterLayoutError(
                "region_key values must be unique across a starter layout."
            )
        object.__setattr__(self, "pages", pages)


def starter_layout_to_json_bytes(layout: StarterLayoutDocument) -> bytes:
    """Serialize one starter layout as canonical JSON bytes."""
    if not isinstance(layout, StarterLayoutDocument):
        raise StarterLayoutError(
            "layout must be StarterLayoutDocument."
        )
    try:
        return canonical_json_bytes(dataclass_to_dict(layout))
    except TemplateSerializationError as error:
        raise StarterLayoutError(str(error)) from error


def starter_layout_from_json_bytes(data: bytes) -> StarterLayoutDocument:
    """Load one strict packaged layout and require canonical encoding."""
    try:
        parsed = strict_json_loads(
            data,
            description="starter Template layout",
        )
        layout = dataclass_from_dict(StarterLayoutDocument, parsed)
    except (TemplateSerializationError, ValueError) as error:
        raise StarterLayoutError(str(error)) from error
    if starter_layout_to_json_bytes(layout) != data:
        raise StarterLayoutError(
            "starter Template layout is not canonical JSON."
        )
    return layout


__all__ = [
    "STARTER_LAYOUT_SCHEMA",
    "StarterLayoutDocument",
    "StarterLayoutError",
    "StarterLayoutPage",
    "StarterLayoutSection",
    "starter_layout_from_json_bytes",
    "starter_layout_to_json_bytes",
]
