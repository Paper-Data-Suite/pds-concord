"""Human-readable, explicitly qualified labels for teacher history menus."""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime


def teacher_version_line(label: str, revision: int, status: str) -> str:
    """Describe an immutable library version without displaying its record ID."""
    return f"Revision {revision}: {label} [{status.replace('_', ' ')}]"


def teacher_planned_date(value: str | None) -> str:
    """A planned date is not evidence of the creation or printing timestamp."""
    if value is None:
        return "Planned date not recorded"
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return "Planned date unavailable"
    if parsed.isoformat() != value:
        return "Planned date unavailable"
    return f"Planned {parsed.strftime('%b %d, %Y')}"


def teacher_recorded_instant(value: str | None, *, kind: str) -> str:
    """Display authoritative offset-aware creation time in teacher-local time."""
    if not value:
        return f"{kind} time not recorded"
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return f"{kind} time unavailable"
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return f"{kind} time zone not recorded"
    local = parsed.astimezone()
    stamp = local.strftime('%b %d, %Y at %I:%M %p %Z')
    return f"{kind} {stamp}"


def distinguish_equal_labels(
    labels: tuple[str, ...], *, noun: str
) -> tuple[str, ...]:
    """Disambiguate identical display lines without inventing chronology."""
    totals = Counter(labels)
    seen: Counter[str] = Counter()
    result: list[str] = []
    for label in labels:
        seen[label] += 1
        if totals[label] > 1:
            result.append(
                f"{label} | {noun} {seen[label]} of {totals[label]} "
                "(display order, not chronological)"
            )
        else:
            result.append(label)
    return tuple(result)
