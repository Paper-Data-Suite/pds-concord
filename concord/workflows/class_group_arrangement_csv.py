"""Optional, reviewed student_id,group CSV interchange for saved groupings.

No Activity state is written. The two-column format deliberately carries no
Group labels, unassigned students or empty groups; show this loss in previews.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path

from concord.class_group_arrangement_storage import (
    LoadedArrangement,
    create_arrangement,
    load_current_arrangement,
)
from concord.class_group_arrangements import (
    SavedArrangementGroup,
    SavedArrangementRevision,
)
from concord.group_plan_arrangement_csv import parse_arrangement_csv_bytes
from concord.workflows.context import (
    Clock,
    require_core_class,
    resolve_read_workspace_root,
    workflow_timestamp,
)
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowNotFoundError,
    ConcordWorkflowValidationError,
)
from concord.workflows.models import WorkflowActor
from concord.workflows.participants import load_required_roster

_MAX_CSV_BYTES = 2_000_000


@dataclass(frozen=True, slots=True, kw_only=True)
class CsvImportRequest:
    class_id: str
    arrangement_id: str
    name: str
    csv_path: str | Path
    actor: WorkflowActor
    acknowledge_unresolved: bool = False


@dataclass(frozen=True, slots=True, kw_only=True)
class PreparedCsvImport:
    class_id: str
    school_year: str
    arrangement_id: str
    name: str
    owner_actor_id: str
    groups: tuple[SavedArrangementGroup, ...]
    roster_student_ids: tuple[str, ...]
    unresolved_student_ids: tuple[str, ...]
    csv_sha256: str
    review_digest: str

    @property
    def assigned_count(self) -> int:
        return sum(len(group.student_ids) for group in self.groups)


@dataclass(frozen=True, slots=True, kw_only=True)
class CsvExportRequest:
    class_id: str
    arrangement_id: str
    expected_revision: int
    expected_sha256: str
    actor: WorkflowActor


@dataclass(frozen=True, slots=True, kw_only=True)
class PreparedCsvExport:
    class_id: str
    school_year: str
    arrangement_id: str
    arrangement_revision: int
    csv_bytes: bytes
    group_count: int
    assigned_count: int
    omitted_unresolved_count: int
    omitted_empty_group_count: int
    review_digest: str


def _root(workspace_root: str | Path | None) -> Path:
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError("Paper Data Suite workspace unavailable.")
    return root


def _actor(actor: WorkflowActor) -> str:
    if actor.actor_kind != "authorized_adult" or actor.owning_system != "concord":
        raise ConcordWorkflowValidationError(
            "CSV interchange requires an authorized Concord teacher actor."
        )
    return actor.actor_id


def _digest(data: dict[str, object]) -> str:
    return hashlib.sha256(
        json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _roster(root: Path, class_id: str) -> tuple[str, ...]:
    return tuple(
        sorted(
            student.student_id
            for student in load_required_roster(root, class_id).students
        )
    )


def prepare_csv_import(
    request: CsvImportRequest, *, workspace_root: str | Path | None = None
) -> PreparedCsvImport:
    """Validate existing local CSV against the entire exact Core class roster."""
    root = _root(workspace_root)
    owner = _actor(request.actor)
    metadata = require_core_class(root, request.class_id)
    path = Path(request.csv_path)
    if path.is_symlink() or not path.is_file():
        raise ConcordWorkflowValidationError("CSV input must be a regular local file.")
    try:
        if path.stat().st_size > _MAX_CSV_BYTES:
            raise ConcordWorkflowValidationError("CSV exceeds the 2 MB local limit.")
        raw = path.read_bytes()
    except OSError as exc:
        raise ConcordWorkflowValidationError("Cannot read the CSV file.") from exc
    if len(raw) > _MAX_CSV_BYTES:
        raise ConcordWorkflowValidationError("CSV exceeds the 2 MB local limit.")
    roster = _roster(root, request.class_id)
    parsed = parse_arrangement_csv_bytes(raw, roster_student_ids=roster)
    groups = tuple(
        SavedArrangementGroup(
            key=group.planned_group_key,
            label=group.planned_group_key,
            student_ids=group.student_ids,
        )
        for group in parsed.proposed_groups
    )
    candidate = SavedArrangementRevision(
        arrangement_id=request.arrangement_id,
        class_id=request.class_id,
        school_year=metadata.school_year,
        revision=1,
        name=request.name,
        owner_actor_id=owner,
        created_by_actor_id=owner,
        created_at=workflow_timestamp(),
        groups=groups,
        roster_student_ids=roster,
        unresolved_student_ids=parsed.unresolved_student_ids,
    )
    sha = hashlib.sha256(raw).hexdigest()
    digest = _digest(
        {
            "contract": "concord_saved_grouping_csv_import_v1",
            "class_id": candidate.class_id,
            "year": candidate.school_year,
            "arrangement_id": candidate.arrangement_id,
            "name": candidate.name,
            "actor_id": owner,
            "csv_sha256": sha,
            "roster": list(roster),
            "groups": [[g.key, list(g.student_ids)] for g in candidate.groups],
            "unresolved": list(parsed.unresolved_student_ids),
        }
    )
    return PreparedCsvImport(
        class_id=candidate.class_id,
        school_year=candidate.school_year,
        arrangement_id=candidate.arrangement_id,
        name=candidate.name,
        owner_actor_id=owner,
        groups=groups,
        roster_student_ids=roster,
        unresolved_student_ids=parsed.unresolved_student_ids,
        csv_sha256=sha,
        review_digest=digest,
    )


def import_csv_grouping(
    request: CsvImportRequest,
    *,
    review_digest: str,
    workspace_root: str | Path | None = None,
    clock: Clock | None = None,
) -> LoadedArrangement:
    """Re-review exact CSV/roster and create one independent library revision."""
    prepared = prepare_csv_import(request, workspace_root=workspace_root)
    if review_digest != prepared.review_digest:
        raise ConcordWorkflowConflictError(
            "CSV or Core roster changed; review import again before confirming."
        )
    if prepared.unresolved_student_ids and request.acknowledge_unresolved is not True:
        raise ConcordWorkflowConflictError(
            "Acknowledge students omitted from the CSV before importing."
        )
    revision = SavedArrangementRevision(
        arrangement_id=prepared.arrangement_id,
        class_id=prepared.class_id,
        school_year=prepared.school_year,
        revision=1,
        name=prepared.name,
        owner_actor_id=prepared.owner_actor_id,
        created_by_actor_id=prepared.owner_actor_id,
        created_at=workflow_timestamp(clock),
        groups=prepared.groups,
        roster_student_ids=prepared.roster_student_ids,
        unresolved_student_ids=prepared.unresolved_student_ids,
    )
    return create_arrangement(
        _root(workspace_root), revision, actor_id=prepared.owner_actor_id
    )


def prepare_csv_export(
    request: CsvExportRequest, *, workspace_root: str | Path | None = None
) -> PreparedCsvExport:
    """Export assignments only; labels, empty groups and unassigned are not in CSV."""
    root = _root(workspace_root)
    owner = _actor(request.actor)
    metadata = require_core_class(root, request.class_id)
    loaded = load_current_arrangement(
        root,
        class_id=request.class_id,
        school_year=metadata.school_year,
        arrangement_id=request.arrangement_id,
        actor_id=owner,
    )
    current = loaded.revision
    if (
        type(request.expected_revision) is not int
        or current.revision != request.expected_revision
        or loaded.sha256 != request.expected_sha256
    ):
        raise ConcordWorkflowConflictError(
            "Saved grouping changed; reload current revision before CSV export."
        )
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(("student_id", "group"))
    count = 0
    for group in current.groups:
        for student_id in sorted(group.student_ids):
            writer.writerow((student_id, group.key))
            count += 1
    if count == 0:
        raise ConcordWorkflowValidationError(
            "Grouping has no assigned students; cannot export useful CSV."
        )
    csv_bytes = output.getvalue().encode("utf-8")
    digest = _digest(
        {
            "contract": "concord_saved_grouping_csv_export_v1",
            "class_id": request.class_id,
            "school_year": metadata.school_year,
            "arrangement_id": current.arrangement_id,
            "revision": current.revision,
            "sha256": loaded.sha256,
            "actor": owner,
            "csv_sha256": hashlib.sha256(csv_bytes).hexdigest(),
        }
    )
    return PreparedCsvExport(
        class_id=current.class_id,
        school_year=current.school_year,
        arrangement_id=current.arrangement_id,
        arrangement_revision=current.revision,
        csv_bytes=csv_bytes,
        group_count=len(current.groups),
        assigned_count=count,
        omitted_unresolved_count=len(current.unresolved_student_ids),
        omitted_empty_group_count=sum(not g.student_ids for g in current.groups),
        review_digest=digest,
    )


def _safe_output(path: Path) -> None:
    """Only existing, nonlinked parent directories; never replace a destination."""
    if not path.name or not path.parent.is_dir():
        raise ConcordWorkflowValidationError("Export parent folder must exist.")
    for parent in (path.parent, *path.parent.parents):
        try:
            info = parent.lstat()
        except OSError as exc:
            raise ConcordWorkflowValidationError(
                "Export folder is unavailable."
            ) from exc
        if stat.S_ISLNK(info.st_mode) or bool(
            getattr(info, "st_file_attributes", 0)
            & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        ):
            raise ConcordWorkflowValidationError(
                "Export parent folder must not contain a link or junction."
            )
    if path.exists() or path.is_symlink():
        raise ConcordWorkflowConflictError(
            "CSV destination already exists; select a new file name."
        )


def export_csv_grouping(
    request: CsvExportRequest,
    *,
    output_path: str | Path,
    review_digest: str,
    workspace_root: str | Path | None = None,
) -> Path:
    """Use one explicitly selected file with exclusive-create, never overwrite."""
    prepared = prepare_csv_export(request, workspace_root=workspace_root)
    if review_digest != prepared.review_digest:
        raise ConcordWorkflowConflictError(
            "Saved grouping export preview changed; review it again."
        )
    target = Path(output_path)
    _safe_output(target)
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0)
    try:
        fd = os.open(target, flags, 0o600)
    except FileExistsError as exc:
        raise ConcordWorkflowConflictError("CSV destination already exists.") from exc
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(prepared.csv_bytes)
            stream.flush()
            os.fsync(stream.fileno())
    except OSError:
        try:
            target.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    return target


__all__ = [
    "CsvExportRequest",
    "CsvImportRequest",
    "PreparedCsvExport",
    "PreparedCsvImport",
    "export_csv_grouping",
    "import_csv_grouping",
    "prepare_csv_export",
    "prepare_csv_import",
]
