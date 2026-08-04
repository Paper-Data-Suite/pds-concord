"""Stable, deterministic diagnostics for Concord record graphs."""

from __future__ import annotations

from dataclasses import dataclass

from concord.models.common import ConcordRecordReference


@dataclass(frozen=True, slots=True, kw_only=True)
class ValidationIssue:
    code: str
    message: str
    record_kind: str | None = None
    record_id: str | None = None
    field_path: tuple[str | int, ...] = ()
    related_references: tuple[ConcordRecordReference, ...] = ()

    @property
    def sort_key(self) -> tuple[object, ...]:
        return (
            self.record_kind or "",
            self.record_id or "",
            tuple(str(part) for part in self.field_path),
            self.code,
            self.message,
        )


class ConcordRecordGraphError(ValueError):
    """Raised with all issues found in an immutable record graph."""

    def __init__(self, issues: tuple[ValidationIssue, ...]) -> None:
        self.issues = issues
        super().__init__(f"Concord record graph has {len(issues)} validation issue(s).")
