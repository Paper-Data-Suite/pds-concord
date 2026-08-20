"""Strict direct-arrangement CSV parsing for Concord GroupPlan authoring."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from pathlib import Path

from pds_core.identifiers import IdentifierValidationError, validate_identifier

from concord.models import PlannedGroup
from concord.workflows.errors import ConcordWorkflowValidationError

_EXPECTED_HEADER = ("student_id", "group")


class ArrangementCsvValidationError(ConcordWorkflowValidationError):
    """Raised when a direct arrangement CSV cannot be normalized safely."""


@dataclass(frozen=True, slots=True, kw_only=True)
class ArrangementCsvResult:
    """Deterministic normalized proposal derived from one arrangement CSV."""

    proposed_groups: tuple[PlannedGroup, ...]
    unresolved_student_ids: tuple[str, ...]
    data_row_count: int
    assigned_student_count: int

    @property
    def proposed_group_count(self) -> int:
        return len(self.proposed_groups)

    @property
    def unresolved_student_count(self) -> int:
        return len(self.unresolved_student_ids)


def _validate_identifier_at_row(value: str, field_name: str, row_number: int) -> str:
    try:
        return validate_identifier(value, field_name)
    except IdentifierValidationError as error:
        raise ArrangementCsvValidationError(f"row {row_number}: {error}") from error


def parse_arrangement_csv_text(
    text: str,
    *,
    roster_student_ids: tuple[str, ...],
) -> ArrangementCsvResult:
    """Parse exact ``student_id,group`` CSV text against one Core roster."""

    if not isinstance(text, str):
        raise TypeError("text must be a string.")

    roster = set(roster_student_ids)
    stream = io.StringIO(text, newline="")
    reader = csv.reader(stream, strict=True)

    header: list[str] | None = None
    try:
        for row in reader:
            if not row:
                continue
            header = row
            break
    except csv.Error as error:
        raise ArrangementCsvValidationError(
            f"row {reader.line_num}: malformed CSV: {error}"
        ) from error

    if header is None or tuple(header) != _EXPECTED_HEADER:
        raise ArrangementCsvValidationError("expected header: student_id,group")

    students_seen: dict[str, int] = {}
    groups: dict[str, list[str]] = {}
    data_row_count = 0

    try:
        for row in reader:
            row_number = reader.line_num
            if not row:
                continue
            if len(row) != 2:
                raise ArrangementCsvValidationError(
                    f"row {row_number}: expected exactly 2 columns"
                )

            student_id, group_token = row
            if student_id == "":
                raise ArrangementCsvValidationError(
                    f"row {row_number}: student_id must not be empty"
                )
            if group_token == "":
                raise ArrangementCsvValidationError(
                    f"row {row_number}: group must not be empty"
                )

            student_id = _validate_identifier_at_row(
                student_id,
                "student_id",
                row_number,
            )
            group_token = _validate_identifier_at_row(
                group_token,
                "group",
                row_number,
            )

            if student_id not in roster:
                raise ArrangementCsvValidationError(
                    f'row {row_number}: student_id "{student_id}" is not in Core roster'
                )
            if student_id in students_seen:
                raise ArrangementCsvValidationError(
                    f'row {row_number}: duplicate student_id "{student_id}"'
                )

            students_seen[student_id] = row_number
            groups.setdefault(group_token, []).append(student_id)
            data_row_count += 1
    except csv.Error as error:
        raise ArrangementCsvValidationError(
            f"row {reader.line_num}: malformed CSV: {error}"
        ) from error

    if data_row_count == 0:
        raise ArrangementCsvValidationError(
            "arrangement CSV must contain at least one data row"
        )

    proposed_groups = tuple(
        PlannedGroup(
            planned_group_key=group_token,
            label=group_token,
            student_ids=tuple(student_ids),
        )
        for group_token, student_ids in sorted(groups.items())
    )
    unresolved = tuple(sorted(roster - set(students_seen)))
    return ArrangementCsvResult(
        proposed_groups=proposed_groups,
        unresolved_student_ids=unresolved,
        data_row_count=data_row_count,
        assigned_student_count=len(students_seen),
    )


def parse_arrangement_csv_bytes(
    data: bytes,
    *,
    roster_student_ids: tuple[str, ...],
) -> ArrangementCsvResult:
    """Decode UTF-8/UTF-8-BOM input and parse a direct arrangement CSV."""

    if not isinstance(data, bytes):
        raise TypeError("data must be bytes.")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ArrangementCsvValidationError(
            "arrangement CSV must be valid UTF-8"
        ) from error
    return parse_arrangement_csv_text(text, roster_student_ids=roster_student_ids)


def parse_arrangement_csv_file(
    path: str | Path,
    *,
    roster_student_ids: tuple[str, ...],
) -> ArrangementCsvResult:
    """Read and parse an arrangement CSV without persisting its source path."""

    try:
        data = Path(path).read_bytes()
    except OSError as error:
        raise ArrangementCsvValidationError(
            "unable to read arrangement CSV"
        ) from error
    return parse_arrangement_csv_bytes(data, roster_student_ids=roster_student_ids)
