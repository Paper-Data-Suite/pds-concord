"""Human-readable, provenance-based scan and assembly chronology labels."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol, Sequence, TypeVar


class RoutedOccurrence(Protocol):
    @property
    def routed_at(self) -> str | None: ...

    @property
    def source_page_number(self) -> int: ...

    @property
    def scan_reference_id(self) -> str: ...


T = TypeVar("T", bound=RoutedOccurrence)


def instant(value: str | None) -> datetime | None:
    """Read a recorded aware instant; never infer time from IDs or filenames."""
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None
    if dt.tzinfo is None or dt.utcoffset() is None:
        return None
    return dt.astimezone(timezone.utc)


def display_recorded_time(value: str | None) -> str:
    parsed = instant(value)
    if parsed is None:
        return "time not recorded"
    return parsed.astimezone().strftime("%b %d, %Y at %I:%M %p %Z")


def ordered_occurrences(items: Sequence[T]) -> tuple[T, ...]:
    """Newest routed first, with stable non-chronological tie-breaking."""
    return tuple(
        sorted(
            items,
            key=lambda item: (
                instant(item.routed_at)
                or datetime.min.replace(tzinfo=timezone.utc),
                item.scan_reference_id,
            ),
            reverse=True,
        )
    )


def occurrence_labels(items: Sequence[RoutedOccurrence]) -> tuple[str, ...]:
    """Labels for a single returned Page; tied timestamps are not ordered truth."""
    ordered = ordered_occurrences(items)
    times = [instant(item.routed_at) for item in ordered]
    labels: list[str] = []
    for index, item in enumerate(ordered):
        timestamp = times[index]
        if timestamp is None:
            status = "chronology uncertain"
        elif times.count(timestamp) > 1:
            status = "same recorded time; order uncertain"
        elif index == 0:
            status = "most recently routed"
        else:
            status = "earlier retained occurrence"
        labels.append(
            f"Routed {display_recorded_time(item.routed_at)} "
            f"({status}); source page {item.source_page_number}"
        )
    return tuple(labels)


__all__ = [
    "display_recorded_time",
    "instant",
    "occurrence_labels",
    "ordered_occurrences",
]
