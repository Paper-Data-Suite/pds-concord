"""Read-only teacher-facing depiction of authoritative Core Standards identities."""

from __future__ import annotations

from dataclasses import dataclass

from pds_core.standards import StandardsLibrary


@dataclass(frozen=True, slots=True)
class StandardDisplay:
    """Presentation metadata for one durable Standard identity."""

    standard_id: str
    label: str
    code: str | None
    short_name: str | None


@dataclass(frozen=True, slots=True)
class StandardsProfileDisplay:
    """Presentation metadata for one durable Standards Profile identity."""

    profile_id: str
    label: str
    title: str | None


def format_standard_display_label(
    standard_id: str,
    *,
    code: str | None,
    short_name: str | None,
) -> str:
    """Prefer Core code/short name while preserving durable ID as fallback."""
    if code is None:
        return standard_id
    if short_name is None or short_name == code:
        return code
    return f"{code} — {short_name}"


def resolve_standard_display(
    standard_id: str,
    standards_library: StandardsLibrary | None,
) -> StandardDisplay:
    """Resolve presentation metadata without changing the durable identity."""
    definition = None
    if standards_library is not None:
        definition = next(
            (
                item
                for item in standards_library.standards
                if item.standard_id == standard_id
            ),
            None,
        )
    code = None if definition is None else definition.code
    short_name = None if definition is None else definition.short_name
    return StandardDisplay(
        standard_id=standard_id,
        label=format_standard_display_label(
            standard_id,
            code=code,
            short_name=short_name,
        ),
        code=code,
        short_name=short_name,
    )


def resolve_profile_display(
    profile_id: str,
    standards_library: StandardsLibrary | None,
) -> StandardsProfileDisplay:
    """Prefer the Core Profile title while retaining exact ID as fallback."""
    profile = None
    if standards_library is not None:
        profile = next(
            (
                item
                for item in standards_library.profiles
                if item.profile_id == profile_id
            ),
            None,
        )
    title = None if profile is None else profile.title
    return StandardsProfileDisplay(
        profile_id=profile_id,
        label=title or profile_id,
        title=title,
    )


__all__ = [
    "StandardDisplay",
    "StandardsProfileDisplay",
    "format_standard_display_label",
    "resolve_profile_display",
    "resolve_standard_display",
]
