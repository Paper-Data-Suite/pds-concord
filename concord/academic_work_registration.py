"""Concord-owned Core Academic Work Registration workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn

from pds_core.academic_work_registration_storage import (
    AcademicWorkRegistrationConflictError as CoreStorageConflictError,
)
from pds_core.academic_work_registration_storage import (
    AcademicWorkRegistrationIntegrityError as CoreStorageIntegrityError,
)
from pds_core.academic_work_registration_storage import (
    AcademicWorkRegistrationNotFoundError as CoreStorageNotFoundError,
)
from pds_core.academic_work_registration_storage import (
    AcademicWorkRegistrationReadError as CoreStorageReadError,
)
from pds_core.academic_work_registration_storage import (
    AcademicWorkRegistrationWriteError as CoreStorageWriteError,
)
from pds_core.academic_work_registration_storage import (
    list_academic_work_registration_revisions,
    load_academic_work_registration_revision,
    load_current_academic_work_registration,
)
from pds_core.academic_work_registrations import (
    ACADEMIC_WORK_INTENTS,
    ACADEMIC_WORK_REGISTRATION_LIFECYCLES,
    AcademicWorkIntent,
    AcademicWorkRegistration,
    AcademicWorkRegistrationLifecycle,
)
from pds_core.academic_work_registrations import (
    AcademicWorkRegistrationValidationError as CoreStorageValidationError,
)
from pds_core.registry_services import (
    AcademicWorkRegistrationRequest,
    AcademicWorkRegistrationServiceResult,
    RegistryServiceConflictError,
    RegistryServiceIntegrityError,
    RegistryServiceNotFoundError,
    RegistryServicePartialState,
    RegistryServicePartialSuccessError,
    RegistryServiceValidationError,
    RegistryServiceWriteError,
    register_academic_work,
    update_academic_work_registration,
)
from pds_core.routing_models import ModuleRecordRef, ModuleWorkRef, RoutingModelError
from pds_core.workspace import WorkspaceRootError

from concord.models import Activity
from concord.pds_contract import (
    CONCORD_ACADEMIC_WORK_CONTRACT_VERSION,
    CONCORD_ACADEMIC_WORK_KIND,
    CONCORD_ACTIVITY_CONTRACT_VERSION,
    CONCORD_ACTIVITY_RECORD_KIND,
    CONCORD_MODULE_ID,
)
from concord.storage import load_current_record, load_current_snapshot
from concord.storage_errors import (
    ConcordStorageIntegrityError,
    ConcordStorageNotFoundError,
    ConcordStorageReadError,
    ConcordStorageValidationError,
)
from concord.workflows.context import require_core_class, resolve_read_workspace_root
from concord.workflows.errors import (
    ConcordWorkflowNotFoundError,
    ConcordWorkflowValidationError,
)

SUPPORTED_ACADEMIC_INTENTS: tuple[AcademicWorkIntent, ...] = (
    "formative",
    "summative",
    "diagnostic",
    "practice",
    "feedback_only",
    "reporting_only",
)
SUPPORTED_ACADEMIC_WORK_LIFECYCLES: tuple[
    AcademicWorkRegistrationLifecycle, ...
] = ("planned", "active", "closed", "cancelled")


class ConcordAcademicWorkRegistrationError(Exception):
    """Base error for Concord's Academic Work Registration boundary."""


class ConcordAcademicWorkRegistrationValidationError(
    ConcordAcademicWorkRegistrationError, ValueError
):
    """Caller input or the managed Concord Activity is invalid."""


class ConcordAcademicWorkRegistrationNotFoundError(
    ConcordAcademicWorkRegistrationError
):
    """The requested managed Activity or registration does not exist."""


class ConcordAcademicWorkRegistrationConflictError(
    ConcordAcademicWorkRegistrationError
):
    """Existing canonical state conflicts with the requested operation."""


class ConcordAcademicWorkRegistrationIntegrityError(
    ConcordAcademicWorkRegistrationError
):
    """Concord or Core registration state cannot be reconciled safely."""


class ConcordAcademicWorkRegistrationWriteError(
    ConcordAcademicWorkRegistrationError
):
    """Core could not durably complete the requested registration write."""


class ConcordAcademicWorkRegistrationPartialSuccessError(
    ConcordAcademicWorkRegistrationError
):
    """Core left durable registration state while completion remained uncertain."""

    def __init__(self, message: str, state: RegistryServicePartialState) -> None:
        super().__init__(message)
        self.state = state


@dataclass(frozen=True, slots=True)
class ManagedActivityRegistrationContext:
    """Validated minimal native Activity snapshot used for Core registration."""

    work: ModuleWorkRef
    source_record: ModuleRecordRef
    title: str
    snapshot_revision: int

    def __post_init__(self) -> None:
        if not isinstance(self.work, ModuleWorkRef):
            raise ConcordAcademicWorkRegistrationValidationError(
                "work must be a ModuleWorkRef."
            )
        if self.work.module_id != CONCORD_MODULE_ID:
            raise ConcordAcademicWorkRegistrationValidationError(
                'work.module_id must be exactly "concord".'
            )
        if not isinstance(self.source_record, ModuleRecordRef):
            raise ConcordAcademicWorkRegistrationValidationError(
                "source_record must be a ModuleRecordRef."
            )
        expected_source = _activity_source_record(self.work)
        if self.source_record != expected_source:
            raise ConcordAcademicWorkRegistrationValidationError(
                "source_record must identify the exact versioned Concord Activity."
            )
        if not isinstance(self.title, str) or not self.title.strip():
            raise ConcordAcademicWorkRegistrationValidationError(
                "title must be nonempty."
            )
        if self.title != self.title.strip():
            raise ConcordAcademicWorkRegistrationValidationError(
                "title must not contain leading or trailing whitespace."
            )
        if (
            isinstance(self.snapshot_revision, bool)
            or not isinstance(self.snapshot_revision, int)
            or self.snapshot_revision < 1
        ):
            raise ConcordAcademicWorkRegistrationValidationError(
                "snapshot_revision must be a positive integer."
            )


def _activity_work(class_id: str, activity_id: str) -> ModuleWorkRef:
    try:
        return ModuleWorkRef(
            module_id=CONCORD_MODULE_ID,
            class_id=class_id,
            work_id=activity_id,
        )
    except (RoutingModelError, TypeError, ValueError) as error:
        raise ConcordAcademicWorkRegistrationValidationError(str(error)) from error


def _activity_source_record(work: ModuleWorkRef) -> ModuleRecordRef:
    try:
        return ModuleRecordRef(
            module_id=CONCORD_MODULE_ID,
            record_kind=CONCORD_ACTIVITY_RECORD_KIND,
            record_id=work.work_id,
            contract_version=CONCORD_ACTIVITY_CONTRACT_VERSION,
        )
    except (RoutingModelError, TypeError, ValueError) as error:
        raise ConcordAcademicWorkRegistrationValidationError(str(error)) from error


def load_managed_activity_registration_context(
    workspace_root: str | Path,
    class_id: str,
    activity_id: str,
) -> ManagedActivityRegistrationContext:
    """Load one exact current native Activity without mutating the workspace."""
    try:
        root = resolve_read_workspace_root(workspace_root)
    except WorkspaceRootError as error:
        raise ConcordAcademicWorkRegistrationValidationError(str(error)) from error
    if root is None:
        raise ConcordAcademicWorkRegistrationNotFoundError(
            "Paper Data Suite workspace does not exist."
        )
    try:
        require_core_class(root, class_id)
    except ConcordWorkflowValidationError as error:
        raise ConcordAcademicWorkRegistrationValidationError(str(error)) from error
    except ConcordWorkflowNotFoundError as error:
        raise ConcordAcademicWorkRegistrationNotFoundError(str(error)) from error

    work = _activity_work(class_id, activity_id)
    try:
        current = load_current_snapshot(root, work)
        record, _ = load_current_record(
            root,
            work,
            CONCORD_ACTIVITY_RECORD_KIND,
            activity_id,
        )
    except ConcordStorageNotFoundError as error:
        raise ConcordAcademicWorkRegistrationNotFoundError(
            f"Concord Activity is not available: {activity_id}"
        ) from error
    except ConcordStorageValidationError as error:
        raise ConcordAcademicWorkRegistrationValidationError(str(error)) from error
    except (ConcordStorageIntegrityError, ConcordStorageReadError) as error:
        raise ConcordAcademicWorkRegistrationIntegrityError(str(error)) from error

    if not isinstance(record, Activity):
        raise ConcordAcademicWorkRegistrationIntegrityError(
            f"Current Activity record is invalid: {activity_id}"
        )
    if record.work_reference != work:
        raise ConcordAcademicWorkRegistrationIntegrityError(
            "Current Activity identity disagrees with its canonical work."
        )

    return ManagedActivityRegistrationContext(
        work=work,
        source_record=_activity_source_record(work),
        title=record.title,
        snapshot_revision=current.snapshot_revision,
    )


def build_concord_academic_work_registration_request(
    context: ManagedActivityRegistrationContext,
    *,
    academic_intent: AcademicWorkIntent,
    lifecycle: AcademicWorkRegistrationLifecycle,
) -> AcademicWorkRegistrationRequest:
    """Map one validated current Activity snapshot to Core's stable request."""
    if not isinstance(context, ManagedActivityRegistrationContext):
        raise ConcordAcademicWorkRegistrationValidationError(
            "context must be a ManagedActivityRegistrationContext."
        )
    if academic_intent not in ACADEMIC_WORK_INTENTS:
        raise ConcordAcademicWorkRegistrationValidationError(
            "academic_intent must be one of: "
            + ", ".join(SUPPORTED_ACADEMIC_INTENTS)
            + "."
        )
    if lifecycle not in ACADEMIC_WORK_REGISTRATION_LIFECYCLES:
        raise ConcordAcademicWorkRegistrationValidationError(
            "lifecycle must be one of: "
            + ", ".join(SUPPORTED_ACADEMIC_WORK_LIFECYCLES)
            + "."
        )
    try:
        return AcademicWorkRegistrationRequest(
            work=context.work,
            producer_contract_version=CONCORD_ACADEMIC_WORK_CONTRACT_VERSION,
            title=context.title,
            work_kind=CONCORD_ACADEMIC_WORK_KIND,
            academic_intent=academic_intent,
            lifecycle=lifecycle,
            source_records=(context.source_record,),
        )
    except (RegistryServiceValidationError, TypeError, ValueError) as error:
        raise ConcordAcademicWorkRegistrationValidationError(str(error)) from error


def load_current_concord_academic_work_registration(
    workspace_root: str | Path,
    class_id: str,
    activity_id: str,
) -> AcademicWorkRegistration | None:
    """Load Core's explicit current registration for one managed Activity."""
    context = load_managed_activity_registration_context(
        workspace_root, class_id, activity_id
    )
    try:
        registration = load_current_academic_work_registration(
            workspace_root, context.work
        )
    except Exception as error:
        _raise_normalized_storage_error(error)
    if registration is not None:
        _verify_registration_identity(context, registration)
    return registration


def list_concord_academic_work_registration_revisions(
    workspace_root: str | Path,
    class_id: str,
    activity_id: str,
) -> tuple[int, ...]:
    """List exact immutable Core registration revisions for one Activity."""
    context = load_managed_activity_registration_context(
        workspace_root, class_id, activity_id
    )
    try:
        revisions = list_academic_work_registration_revisions(
            workspace_root, context.work
        )
    except Exception as error:
        _raise_normalized_storage_error(error)
    for revision in revisions:
        registration = load_concord_academic_work_registration_revision(
            workspace_root,
            class_id,
            activity_id,
            revision,
        )
        _verify_registration_identity(context, registration)
    return revisions


def load_concord_academic_work_registration_revision(
    workspace_root: str | Path,
    class_id: str,
    activity_id: str,
    registration_revision: int,
) -> AcademicWorkRegistration:
    """Load one exact immutable Core registration revision for an Activity."""
    if (
        isinstance(registration_revision, bool)
        or not isinstance(registration_revision, int)
        or registration_revision < 1
    ):
        raise ConcordAcademicWorkRegistrationValidationError(
            "registration_revision must be a positive integer."
        )
    context = load_managed_activity_registration_context(
        workspace_root, class_id, activity_id
    )
    try:
        registration = load_academic_work_registration_revision(
            workspace_root,
            context.work,
            registration_revision,
        )
    except Exception as error:
        _raise_normalized_storage_error(error)
    _verify_registration_identity(context, registration)
    return registration


def register_concord_academic_work(
    workspace_root: str | Path,
    class_id: str,
    activity_id: str,
    *,
    academic_intent: AcademicWorkIntent,
    lifecycle: AcademicWorkRegistrationLifecycle,
) -> AcademicWorkRegistrationServiceResult:
    """Create registration revision 1 or reconcile the exact existing value."""
    context = load_managed_activity_registration_context(
        workspace_root, class_id, activity_id
    )
    request = build_concord_academic_work_registration_request(
        context,
        academic_intent=academic_intent,
        lifecycle=lifecycle,
    )
    try:
        result = register_academic_work(workspace_root, request)
    except Exception as error:
        _raise_normalized_service_error(error)

    if result.disposition not in {"created", "existing"}:
        raise ConcordAcademicWorkRegistrationIntegrityError(
            "Core returned an unexpected registration disposition: "
            f"{result.disposition}."
        )
    if (
        result.disposition == "created"
        and result.registration.registration_revision != 1
    ):
        raise ConcordAcademicWorkRegistrationIntegrityError(
            "Initial registration did not create revision 1."
        )
    _verify_registration_matches_request(context, request, result.registration)
    _verify_current(workspace_root, context, result.registration)
    return result


def update_concord_academic_work_registration(
    workspace_root: str | Path,
    class_id: str,
    activity_id: str,
    *,
    academic_intent: AcademicWorkIntent,
    lifecycle: AcademicWorkRegistrationLifecycle,
    expected_current_revision: int,
) -> AcademicWorkRegistrationServiceResult:
    """Explicitly update Core registration metadata with optimistic concurrency."""
    if (
        isinstance(expected_current_revision, bool)
        or not isinstance(expected_current_revision, int)
        or expected_current_revision < 1
    ):
        raise ConcordAcademicWorkRegistrationValidationError(
            "expected_current_revision must be a positive integer."
        )
    context = load_managed_activity_registration_context(
        workspace_root, class_id, activity_id
    )
    request = build_concord_academic_work_registration_request(
        context,
        academic_intent=academic_intent,
        lifecycle=lifecycle,
    )
    try:
        result = update_academic_work_registration(
            workspace_root,
            request,
            expected_current_revision=expected_current_revision,
        )
    except Exception as error:
        _raise_normalized_service_error(error)

    if result.disposition not in {"updated", "existing"}:
        raise ConcordAcademicWorkRegistrationIntegrityError(
            "Core returned an unexpected update disposition: "
            f"{result.disposition}."
        )
    _verify_registration_matches_request(context, request, result.registration)
    _verify_current(workspace_root, context, result.registration)
    return result


def _verify_registration_identity(
    context: ManagedActivityRegistrationContext,
    registration: AcademicWorkRegistration,
) -> None:
    if not isinstance(registration, AcademicWorkRegistration):
        raise ConcordAcademicWorkRegistrationIntegrityError(
            "Core returned an invalid Academic Work Registration."
        )
    if registration.work != context.work:
        raise ConcordAcademicWorkRegistrationIntegrityError(
            "Registration work does not match the managed Concord Activity."
        )
    if (
        registration.producer_contract_version
        != CONCORD_ACADEMIC_WORK_CONTRACT_VERSION
    ):
        raise ConcordAcademicWorkRegistrationIntegrityError(
            "Registration producer contract is not Concord academic work v1."
        )
    if registration.work_kind != CONCORD_ACADEMIC_WORK_KIND:
        raise ConcordAcademicWorkRegistrationIntegrityError(
            "Registration work_kind is not Concord collaborative_activity."
        )
    if registration.source_records != (context.source_record,):
        raise ConcordAcademicWorkRegistrationIntegrityError(
            "Registration source_records do not identify the exact Concord Activity."
        )


def _verify_registration_matches_request(
    context: ManagedActivityRegistrationContext,
    request: AcademicWorkRegistrationRequest,
    registration: AcademicWorkRegistration,
) -> None:
    _verify_registration_identity(context, registration)
    if (
        registration.title != request.title
        or registration.academic_intent != request.academic_intent
        or registration.lifecycle != request.lifecycle
    ):
        raise ConcordAcademicWorkRegistrationIntegrityError(
            "Core registration does not match the requested Activity metadata."
        )


def _verify_current(
    workspace_root: str | Path,
    context: ManagedActivityRegistrationContext,
    expected: AcademicWorkRegistration,
) -> None:
    try:
        current = load_current_academic_work_registration(
            workspace_root, context.work
        )
    except Exception as error:
        _raise_normalized_storage_error(error)
    if current != expected:
        raise ConcordAcademicWorkRegistrationIntegrityError(
            "Core's current registration does not equal the service result."
        )


def _raise_normalized_service_error(error: Exception) -> NoReturn:
    if isinstance(error, RegistryServicePartialSuccessError):
        raise ConcordAcademicWorkRegistrationPartialSuccessError(
            str(error), error.state
        ) from error
    mappings = (
        (
            RegistryServiceValidationError,
            ConcordAcademicWorkRegistrationValidationError,
        ),
        (
            RegistryServiceNotFoundError,
            ConcordAcademicWorkRegistrationNotFoundError,
        ),
        (
            RegistryServiceConflictError,
            ConcordAcademicWorkRegistrationConflictError,
        ),
        (
            RegistryServiceIntegrityError,
            ConcordAcademicWorkRegistrationIntegrityError,
        ),
        (
            RegistryServiceWriteError,
            ConcordAcademicWorkRegistrationWriteError,
        ),
    )
    for core_type, concord_type in mappings:
        if isinstance(error, core_type):
            raise concord_type(str(error)) from error
    raise error


def _raise_normalized_storage_error(error: Exception) -> NoReturn:
    mappings = (
        (
            CoreStorageValidationError,
            ConcordAcademicWorkRegistrationValidationError,
        ),
        (
            CoreStorageNotFoundError,
            ConcordAcademicWorkRegistrationNotFoundError,
        ),
        (
            CoreStorageConflictError,
            ConcordAcademicWorkRegistrationConflictError,
        ),
        (
            CoreStorageIntegrityError,
            ConcordAcademicWorkRegistrationIntegrityError,
        ),
        (
            CoreStorageWriteError,
            ConcordAcademicWorkRegistrationWriteError,
        ),
        (
            CoreStorageReadError,
            ConcordAcademicWorkRegistrationIntegrityError,
        ),
    )
    for core_type, concord_type in mappings:
        if isinstance(error, core_type):
            raise concord_type(str(error)) from error
    raise error


__all__ = [
    "ConcordAcademicWorkRegistrationConflictError",
    "ConcordAcademicWorkRegistrationError",
    "ConcordAcademicWorkRegistrationIntegrityError",
    "ConcordAcademicWorkRegistrationNotFoundError",
    "ConcordAcademicWorkRegistrationPartialSuccessError",
    "ConcordAcademicWorkRegistrationValidationError",
    "ConcordAcademicWorkRegistrationWriteError",
    "ManagedActivityRegistrationContext",
    "SUPPORTED_ACADEMIC_INTENTS",
    "SUPPORTED_ACADEMIC_WORK_LIFECYCLES",
    "build_concord_academic_work_registration_request",
    "list_concord_academic_work_registration_revisions",
    "load_concord_academic_work_registration_revision",
    "load_current_concord_academic_work_registration",
    "load_managed_activity_registration_context",
    "register_concord_academic_work",
    "update_concord_academic_work_registration",
]
