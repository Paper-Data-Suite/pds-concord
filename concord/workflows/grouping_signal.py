"""Core-backed grouping-signal discovery, diagnostics, selection, and import."""

from __future__ import annotations

import stat
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from pds_core.grouping_signal_csv import (
    GroupingSignalCsvDocument,
    GroupingSignalCsvError,
    grouping_signal_csv_to_signal_set,
    parse_grouping_signal_csv,
)
from pds_core.grouping_signal_diagnostics import (
    GroupingSignalDiagnosticReport,
    GroupingSignalDiagnosticsError,
    GroupingSignalDimensionDiagnostics,
    diagnose_grouping_signal,
)
from pds_core.grouping_signal_storage import (
    GROUPING_SIGNAL_DIGEST_ALGORITHM,
    GroupingSignalConflictError,
    GroupingSignalNotFoundError,
    GroupingSignalStorageError,
    StoredGroupingSignal,
    calculate_grouping_signal_digest,
    list_grouping_signal_ids,
    load_grouping_signal,
    write_grouping_signal,
)
from pds_core.grouping_signals import GroupingSignalDimension, GroupingSignalSet
from pds_core.workspace import WorkspaceRootError

from concord.workflows.context import require_core_class, resolve_read_workspace_root
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowNotFoundError,
    ConcordWorkflowValidationError,
)


@dataclass(frozen=True, slots=True)
class GroupingSignalSummary:
    """Privacy-bounded identity and provenance for one exact Core signal."""

    class_id: str
    signal_set_id: str
    created_at: datetime
    source_kind: str
    source_module_id: str | None
    digest_algorithm: str
    digest: str
    dimension_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class GroupingSignalInspection:
    """Exact stored signal plus current Core roster diagnostics."""

    summary: GroupingSignalSummary
    stored: StoredGroupingSignal
    diagnostics: GroupingSignalDiagnosticReport


@dataclass(frozen=True, slots=True)
class GroupingSignalDimensionSelection:
    """Exact signal/digest/dimension handoff for later Concord planning."""

    inspection: GroupingSignalInspection
    dimension: GroupingSignalDimension
    dimension_diagnostics: GroupingSignalDimensionDiagnostics

    @property
    def class_id(self) -> str:
        return self.inspection.summary.class_id

    @property
    def signal_set_id(self) -> str:
        return self.inspection.summary.signal_set_id

    @property
    def digest(self) -> str:
        return self.inspection.summary.digest

    @property
    def dimension_id(self) -> str:
        return self.dimension.dimension_id


@dataclass(frozen=True, slots=True)
class GroupingSignalCsvSourceInspection:
    """Structurally validated CSV metadata before standalone conversion."""

    representation_scope: str
    requires_new_identity: bool
    signal_set_id: str
    class_id: str
    created_at: datetime
    source_kind: str
    source_module_id: str | None
    dimension_id: str
    band_count: int


@dataclass(frozen=True, slots=True, kw_only=True)
class ImportGroupingSignalCsvRequest:
    """Explicit teacher-selected Core grouping-signal CSV import."""

    class_id: str
    csv_path: str | Path
    new_signal_set_id: str | None = None
    new_created_at: datetime | None = None
    expected_signal_digest: str | None = None


@dataclass(frozen=True, slots=True)
class GroupingSignalImportPreview:
    """Fully validated, read-only candidate awaiting explicit import."""

    requested_class_id: str
    representation_scope: str
    signal: GroupingSignalSet
    digest_algorithm: str
    digest: str
    diagnostics: GroupingSignalDiagnosticReport

    @property
    def dimension(self) -> GroupingSignalDimension:
        return self.signal.dimensions[0]


@dataclass(frozen=True, slots=True)
class GroupingSignalImportResult:
    """Immutable Core write result for one fully validated CSV candidate."""

    preview: GroupingSignalImportPreview
    disposition: str
    stored: StoredGroupingSignal


def _required_root(workspace_root: str | Path | None) -> Path:
    try:
        root = resolve_read_workspace_root(workspace_root)
    except WorkspaceRootError as error:
        raise ConcordWorkflowValidationError(str(error)) from error
    if root is None:
        raise ConcordWorkflowNotFoundError(
            "Paper Data Suite workspace does not exist."
        )
    return root


def _summary(stored: StoredGroupingSignal) -> GroupingSignalSummary:
    signal = stored.signal
    return GroupingSignalSummary(
        class_id=signal.class_id,
        signal_set_id=signal.signal_set_id,
        created_at=signal.created_at,
        source_kind=signal.source.kind,
        source_module_id=signal.source.module_id,
        digest_algorithm=stored.digest_algorithm,
        digest=stored.digest,
        dimension_ids=tuple(item.dimension_id for item in signal.dimensions),
    )


def _load_exact_signal(
    root: Path,
    class_id: str,
    signal_set_id: str,
) -> StoredGroupingSignal:
    try:
        return load_grouping_signal(root, class_id, signal_set_id)
    except GroupingSignalNotFoundError as error:
        raise ConcordWorkflowNotFoundError(
            "Core grouping signal is not available: "
            f"class_id={class_id!r}, signal_set_id={signal_set_id!r}."
        ) from error
    except GroupingSignalStorageError as error:
        raise ConcordWorkflowValidationError(
            "Core grouping-signal storage failed strict integrity validation: "
            f"{error}"
        ) from error


def _diagnose_signal(
    root: Path,
    signal: GroupingSignalSet,
    class_id: str,
) -> GroupingSignalDiagnosticReport:
    try:
        return diagnose_grouping_signal(
            root,
            signal,
            expected_class_id=class_id,
        )
    except GroupingSignalDiagnosticsError as error:
        raise ConcordWorkflowValidationError(
            f"Core grouping-signal diagnostics failed: {error}"
        ) from error


def _diagnose(
    root: Path,
    stored: StoredGroupingSignal,
    class_id: str,
) -> GroupingSignalDiagnosticReport:
    return _diagnose_signal(root, stored.signal, class_id)


def _read_import_bytes(csv_path: str | Path) -> bytes:
    try:
        path = Path(csv_path)
    except TypeError as error:
        raise ConcordWorkflowValidationError(
            "Grouping-signal CSV path must be path-like."
        ) from error

    try:
        metadata = path.stat(follow_symlinks=False)
    except FileNotFoundError as error:
        raise ConcordWorkflowNotFoundError(
            "Grouping-signal CSV file is not available."
        ) from error
    except OSError as error:
        raise ConcordWorkflowValidationError(
            f"Grouping-signal CSV file could not be inspected: {error}"
        ) from error

    if not stat.S_ISREG(metadata.st_mode):
        raise ConcordWorkflowValidationError(
            "Grouping-signal CSV path must identify a regular file."
        )
    try:
        return path.read_bytes()
    except OSError as error:
        raise ConcordWorkflowValidationError(
            f"Grouping-signal CSV file could not be read: {error}"
        ) from error


def _parse_import_document(raw_csv: bytes) -> GroupingSignalCsvDocument:
    try:
        return parse_grouping_signal_csv(raw_csv)
    except GroupingSignalCsvError as error:
        raise ConcordWorkflowValidationError(
            f"Core grouping-signal CSV validation failed: {error}"
        ) from error


def _convert_import_document(
    request: ImportGroupingSignalCsvRequest,
    raw_csv: bytes,
) -> tuple[str, GroupingSignalSet]:
    document = _parse_import_document(raw_csv)

    has_new_id = request.new_signal_set_id is not None
    has_new_time = request.new_created_at is not None
    if document.requires_new_identity:
        if not has_new_id or not has_new_time:
            raise ConcordWorkflowValidationError(
                "A dimension_projection import requires both a new signal_set_id "
                "and a new created_at timestamp."
            )
    elif has_new_id or has_new_time:
        raise ConcordWorkflowValidationError(
            "A complete_signal import preserves its declared identity and does not "
            "accept projection identity overrides."
        )

    try:
        signal = grouping_signal_csv_to_signal_set(
            document,
            new_signal_set_id=request.new_signal_set_id,
            new_created_at=request.new_created_at,
        )
    except GroupingSignalCsvError as error:
        raise ConcordWorkflowValidationError(
            f"Core grouping-signal CSV conversion failed: {error}"
        ) from error
    return document.representation_scope, signal


def _require_import_diagnostics(
    diagnostics: GroupingSignalDiagnosticReport,
) -> None:
    if not diagnostics.has_errors:
        return
    codes = tuple(
        sorted(
            {
                finding.code
                for finding in diagnostics.findings
                if finding.severity == "error"
            }
        )
    )
    raise ConcordWorkflowValidationError(
        "Grouping-signal import has Core diagnostic error(s) and cannot be "
        "persisted: "
        + ", ".join(codes)
        + "."
    )


def inspect_grouping_signal_csv_file(
    csv_path: str | Path,
) -> GroupingSignalCsvSourceInspection:
    """Inspect one structurally valid Core CSV without converting or writing it."""

    document = _parse_import_document(_read_import_bytes(csv_path))
    return GroupingSignalCsvSourceInspection(
        representation_scope=document.representation_scope,
        requires_new_identity=document.requires_new_identity,
        signal_set_id=document.signal_set_id,
        class_id=document.class_id,
        created_at=document.created_at,
        source_kind=document.source.kind,
        source_module_id=document.source.module_id,
        dimension_id=document.dimension.dimension_id,
        band_count=document.dimension.band_count,
    )


def list_grouping_signals(
    class_id: str,
    *,
    workspace_root: str | Path | None = None,
) -> tuple[GroupingSignalSummary, ...]:
    """List exact immutable Core signals for one class without selecting one."""

    root = _required_root(workspace_root)
    require_core_class(root, class_id)
    try:
        signal_set_ids = list_grouping_signal_ids(root, class_id)
    except GroupingSignalStorageError as error:
        raise ConcordWorkflowValidationError(
            "Core grouping-signal storage failed strict integrity validation: "
            f"{error}"
        ) from error
    return tuple(
        _summary(_load_exact_signal(root, class_id, signal_set_id))
        for signal_set_id in signal_set_ids
    )


def inspect_grouping_signal(
    class_id: str,
    signal_set_id: str,
    *,
    workspace_root: str | Path | None = None,
) -> GroupingSignalInspection:
    """Load one exact Core signal and diagnose it against the current roster."""

    root = _required_root(workspace_root)
    require_core_class(root, class_id)
    stored = _load_exact_signal(root, class_id, signal_set_id)
    diagnostics = _diagnose(root, stored, class_id)
    return GroupingSignalInspection(
        summary=_summary(stored),
        stored=stored,
        diagnostics=diagnostics,
    )


def select_grouping_signal_dimension(
    class_id: str,
    signal_set_id: str,
    dimension_id: str,
    *,
    workspace_root: str | Path | None = None,
) -> GroupingSignalDimensionSelection:
    """Select one exact dimension, rejecting Core diagnostic errors only."""

    inspection = inspect_grouping_signal(
        class_id,
        signal_set_id,
        workspace_root=workspace_root,
    )
    dimension = next(
        (
            item
            for item in inspection.stored.signal.dimensions
            if item.dimension_id == dimension_id
        ),
        None,
    )
    if dimension is None:
        raise ConcordWorkflowValidationError(
            f"Grouping-signal dimension is not available: {dimension_id!r}."
        )
    if inspection.diagnostics.has_errors:
        codes = tuple(
            sorted(
                {
                    finding.code
                    for finding in inspection.diagnostics.findings
                    if finding.severity == "error"
                }
            )
        )
        raise ConcordWorkflowValidationError(
            "Grouping signal has Core diagnostic error(s) and cannot be used for "
            "planning: "
            + ", ".join(codes)
            + "."
        )
    dimension_diagnostics = next(
        item
        for item in inspection.diagnostics.dimensions
        if item.dimension_id == dimension_id
    )
    return GroupingSignalDimensionSelection(
        inspection=inspection,
        dimension=dimension,
        dimension_diagnostics=dimension_diagnostics,
    )


def prepare_grouping_signal_csv_import(
    request: ImportGroupingSignalCsvRequest,
    *,
    workspace_root: str | Path | None = None,
) -> GroupingSignalImportPreview:
    """Validate an explicit CSV completely without writing Core state."""

    if not isinstance(request, ImportGroupingSignalCsvRequest):
        raise ConcordWorkflowValidationError(
            "request must be an ImportGroupingSignalCsvRequest."
        )
    root = _required_root(workspace_root)
    require_core_class(root, request.class_id)
    raw_csv = _read_import_bytes(request.csv_path)
    representation_scope, signal = _convert_import_document(request, raw_csv)

    diagnostics = _diagnose_signal(root, signal, request.class_id)
    _require_import_diagnostics(diagnostics)
    if signal.class_id != request.class_id:
        raise ConcordWorkflowValidationError(
            "Grouping-signal CSV class_id does not match the requested Core class."
        )

    digest = calculate_grouping_signal_digest(signal)
    if (
        request.expected_signal_digest is not None
        and request.expected_signal_digest != digest
    ):
        raise ConcordWorkflowConflictError(
            "Grouping-signal CSV changed since preview; review it again before "
            "importing."
        )

    return GroupingSignalImportPreview(
        requested_class_id=request.class_id,
        representation_scope=representation_scope,
        signal=signal,
        digest_algorithm=GROUPING_SIGNAL_DIGEST_ALGORITHM,
        digest=digest,
        diagnostics=diagnostics,
    )


def import_grouping_signal_csv(
    request: ImportGroupingSignalCsvRequest,
    *,
    workspace_root: str | Path | None = None,
) -> GroupingSignalImportResult:
    """Validate and immutably persist one explicit Core grouping-signal CSV."""

    root = _required_root(workspace_root)
    preview = prepare_grouping_signal_csv_import(
        request,
        workspace_root=root,
    )
    try:
        written = write_grouping_signal(root, preview.signal)
    except GroupingSignalConflictError as error:
        raise ConcordWorkflowConflictError(
            f"Core grouping-signal immutable identity conflict: {error}"
        ) from error
    except GroupingSignalStorageError as error:
        raise ConcordWorkflowValidationError(
            f"Core grouping-signal storage write failed: {error}"
        ) from error

    return GroupingSignalImportResult(
        preview=preview,
        disposition=written.disposition,
        stored=written.stored,
    )
