"""Read-only Concord readiness provider for Core module-operations v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final, Literal

from pds_core.class_metadata import (
    ClassMetadataReadError,
    ClassMetadataValidationError,
    load_class_metadata_for_class,
)
from pds_core.classes import ClassFolder, class_folder
from pds_core.identifiers import IdentifierValidationError
from pds_core.module_operations import (
    ModuleOperationsNotice,
    ModuleOperationsRequest,
    ModuleReadinessReport,
    validate_module_readiness_report,
)
from pds_core.routing_models import RoutingModelError
from pds_core.workspace import WorkspaceRootError

from concord.pds_contract import CONCORD_MODULE_ID
from concord.storage import list_activity_work_refs
from concord.storage_errors import (
    ConcordStorageIntegrityError,
    ConcordStorageReadError,
)
from concord.workflows.context import resolve_read_workspace_root

_UNAVAILABLE_NOTICE_CODE: Final = "concord_readiness_unavailable"
_CLASS_NOT_READY_NOTICE_CODE: Final = "concord_class_not_ready"

_PathState = Literal["present", "missing", "wrong_type", "unsafe"]


def evaluate_concord_readiness(
    request: ModuleOperationsRequest,
    /,
) -> ModuleReadinessReport:
    """Evaluate structural Concord readiness without mutating workspace state."""
    if not isinstance(request, ModuleOperationsRequest):
        raise TypeError("request must be a ModuleOperationsRequest.")

    if request.workspace_root is None:
        return _unavailable_report(
            "Concord readiness requires an explicit workspace."
        )

    try:
        root = resolve_read_workspace_root(request.workspace_root)
    except (OSError, WorkspaceRootError):
        return _unavailable_report(
            "The supplied workspace cannot be inspected safely for Concord readiness."
        )
    if root is None:
        return _unavailable_report(
            "The supplied workspace is not available for Concord readiness."
        )

    # Core v1 does not identify a requested Concord operation. A valid workspace
    # is therefore structurally usable even when no class is selected yet.
    if request.class_id is None:
        return _ready_report()

    return _evaluate_class_readiness(root, request.class_id)


def _evaluate_class_readiness(root: Path, class_id: str) -> ModuleReadinessReport:
    try:
        folder = class_folder(root, class_id)
    except IdentifierValidationError:
        return _unavailable_report(
            "The requested Concord class identity cannot be inspected safely."
        )

    class_state = _inspect_path(folder.class_dir, expected_kind="directory")
    if class_state == "unsafe":
        return _unavailable_report(
            "The requested Concord class path cannot be inspected safely."
        )
    if class_state != "present":
        return _class_not_ready_report()

    metadata_state = _inspect_path(folder.metadata_path, expected_kind="file")
    if metadata_state == "unsafe":
        return _unavailable_report(
            "The requested Concord class metadata cannot be inspected safely."
        )
    if metadata_state != "present":
        return _class_not_ready_report()

    metadata_result = _inspect_class_metadata(root, folder)
    if metadata_result is not None:
        return metadata_result

    try:
        list_activity_work_refs(root, class_id)
    except (ConcordStorageIntegrityError, RoutingModelError):
        return _class_not_ready_report()
    except (ConcordStorageReadError, OSError):
        return _unavailable_report(
            "The requested Concord class structure cannot be inspected safely."
        )

    # No Concord Activities is a valid starting state. Roster- and
    # operation-specific prerequisites remain enforced by their owning services.
    return _ready_report()


def _inspect_class_metadata(
    root: Path,
    folder: ClassFolder,
) -> ModuleReadinessReport | None:
    try:
        metadata = load_class_metadata_for_class(root, folder.class_id)
    except ClassMetadataValidationError:
        return _class_not_ready_report()
    except ClassMetadataReadError as error:
        cause = error.__cause__
        if isinstance(cause, (json.JSONDecodeError, UnicodeError)):
            return _class_not_ready_report()
        return _unavailable_report(
            "The requested Concord class metadata cannot be inspected safely."
        )

    if metadata.class_id != folder.class_id:
        return _class_not_ready_report()
    return None


def _inspect_path(
    path: Path,
    *,
    expected_kind: Literal["directory", "file"],
) -> _PathState:
    try:
        if path.is_symlink():
            return "unsafe"
        if not path.exists():
            return "missing"
        if expected_kind == "directory":
            return "present" if path.is_dir() else "wrong_type"
        return "present" if path.is_file() else "wrong_type"
    except OSError:
        return "unsafe"


def _ready_report() -> ModuleReadinessReport:
    return validate_module_readiness_report(
        ModuleReadinessReport(
            evaluation="evaluated",
            ready=True,
            notices=(),
        ),
        expected_module_id=CONCORD_MODULE_ID,
    )


def _class_not_ready_report() -> ModuleReadinessReport:
    return validate_module_readiness_report(
        ModuleReadinessReport(
            evaluation="evaluated",
            ready=False,
            notices=(
                ModuleOperationsNotice(
                    code=_CLASS_NOT_READY_NOTICE_CODE,
                    summary=(
                        "The requested Concord class is missing or structurally "
                        "unusable."
                    ),
                ),
            ),
        ),
        expected_module_id=CONCORD_MODULE_ID,
    )


def _unavailable_report(summary: str) -> ModuleReadinessReport:
    return validate_module_readiness_report(
        ModuleReadinessReport(
            evaluation="unavailable",
            ready=None,
            notices=(
                ModuleOperationsNotice(
                    code=_UNAVAILABLE_NOTICE_CODE,
                    summary=summary,
                ),
            ),
        ),
        expected_module_id=CONCORD_MODULE_ID,
    )


__all__ = ["evaluate_concord_readiness"]
