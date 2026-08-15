"""Explicit Core publication workflows for Concord academic-result manifests.

Concord owns manifest generation, producer revision policy, and educational
semantics. Core owns canonical Publication Records, identifiers, timestamps,
registry persistence, and idempotency reconciliation. This module deliberately
writes no Core registry JSON and no catalog rows directly.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Final, Literal, NoReturn

from pds_core.academic_catalog import (
    AcademicCatalogBuildError,
    AcademicCatalogBuildResult,
    AcademicCatalogCompatibilityError,
    AcademicCatalogConflictError,
    AcademicCatalogError,
    AcademicCatalogIntegrityError,
    AcademicCatalogNotFoundError,
    AcademicCatalogReadError,
    AcademicCatalogSourceError,
    AcademicCatalogValidationError,
    CatalogPublication,
    PublicationCatalogQuery,
    PublicationCatalogState,
    load_academic_catalog_metadata,
    query_publication_catalog,
    rebuild_academic_catalog,
)
from pds_core.academic_work_registration_storage import (
    AcademicWorkRegistrationIntegrityError,
    AcademicWorkRegistrationNotFoundError,
    AcademicWorkRegistrationReadError,
    AcademicWorkRegistrationStorageError,
    load_academic_work_registration_revision,
)
from pds_core.academic_work_registrations import AcademicWorkRegistration
from pds_core.publication_compatibility import (
    PublicationCompatibilityError,
    PublicationCompatibilityResult,
    evaluate_publication_compatibility,
)
from pds_core.publication_records import (
    PublicationCapability,
    PublicationRecord,
    PublicationRecordError,
    PublicationWithdrawal,
    validate_publication_record_series,
)
from pds_core.publication_storage import (
    PublicationManifestError,
    PublicationManifestIntegrityError,
    PublicationManifestNotFoundError,
    PublicationStorageError,
    get_current_publication_record,
    list_publication_record_set,
    verify_publication_manifest,
)
from pds_core.registry_services import (
    PublicationManifestRequest,
    PublicationServiceResult,
    PublicationWithdrawalRequest,
    PublicationWithdrawalServiceResult,
    RegistryServiceConflictError,
    RegistryServiceError,
    RegistryServiceIntegrityError,
    RegistryServiceNotFoundError,
    RegistryServicePartialSuccessError,
    RegistryServiceValidationError,
    RegistryServiceWriteError,
    get_canonical_publication_record,
    get_canonical_publication_withdrawal,
    publish_manifest_revision,
    supersede_manifest_revision,
    withdraw_publication,
)
from pds_core.routing_models import ModuleRecordRef, ModuleWorkRef
from pds_core.standards import StandardsLibrary

from concord.academic_result_manifest import (
    ACADEMIC_RESULT_MANIFEST_CONTRACT_VERSION,
    AcademicResultManifest,
    derive_manifest_capabilities,
)
from concord.academic_result_manifest_generation import (
    AcademicResultManifestGenerationResult,
    ConcordManifestGenerationConflictError,
    ConcordManifestGenerationError,
    ConcordManifestGenerationIntegrityError,
    ConcordManifestGenerationNotFoundError,
    ConcordManifestGenerationPartialSuccessError,
    ConcordManifestGenerationValidationError,
    ConcordManifestGenerationWriteError,
    GenerateAcademicResultManifestRequest,
    ManifestGenerationPartialState,
    StoredAcademicResultManifest,
    academic_result_manifest_relative_path,
    generate_academic_result_manifest,
    list_academic_result_manifest_revisions,
    load_academic_result_manifest_revision,
)
from concord.academic_work_registration import (
    ConcordAcademicWorkRegistrationError,
    ConcordAcademicWorkRegistrationIntegrityError,
    ConcordAcademicWorkRegistrationNotFoundError,
    ConcordAcademicWorkRegistrationValidationError,
    load_current_concord_academic_work_registration,
)
from concord.pds_contract import (
    CONCORD_ACADEMIC_RESULT_RECORD_SET_ID,
    CONCORD_ACADEMIC_WORK_CONTRACT_VERSION,
    CONCORD_ACADEMIC_WORK_KIND,
    CONCORD_ACTIVITY_CONTRACT_VERSION,
    CONCORD_ACTIVITY_RECORD_KIND,
    CONCORD_MODULE_ID,
)
from concord.pds_publication import get_publication_producer_profile
from concord.workflows.context import resolve_read_workspace_root

CONCORD_ACADEMIC_RESULT_PUBLICATION_KIND: Final[Literal["academic_result_set"]] = (
    "academic_result_set"
)

PublicationDisposition = Literal["created", "existing"]
PublicationOperation = Literal[
    "publish",
    "supersede",
    "withdraw",
    "republish_after_withdrawal",
]
WithdrawalManifestVerification = Literal[
    "verified",
    "missing",
    "digest_mismatch_or_unsafe",
    "unreadable",
]
PublicationCanonicalState = Literal[
    "producer_only",
    "uncertain",
    "confirmed",
]


class ConcordAcademicResultPublicationError(Exception):
    """Base error for Concord's Core publication boundary."""


class ConcordAcademicResultPublicationValidationError(
    ConcordAcademicResultPublicationError, ValueError
):
    """The requested publication operation is malformed or inapplicable."""


class ConcordAcademicResultPublicationNotFoundError(
    ConcordAcademicResultPublicationError
):
    """Required producer or canonical state does not exist."""


class ConcordAcademicResultPublicationConflictError(
    ConcordAcademicResultPublicationError
):
    """Caller expectations conflict with current immutable state."""


class ConcordAcademicResultPublicationIntegrityError(
    ConcordAcademicResultPublicationError
):
    """Producer, registration, or canonical state is contradictory."""


class ConcordAcademicResultPublicationWriteError(
    ConcordAcademicResultPublicationError
):
    """Core publication state could not be completed or read safely."""


@dataclass(frozen=True, slots=True)
class PublicationPartialSuccessState:
    """Durable state known when publication completion becomes uncertain."""

    operation: PublicationOperation
    canonical_state: PublicationCanonicalState
    manifest_generation: AcademicResultManifestGenerationResult | None
    generation_partial_state: ManifestGenerationPartialState | None
    publication: PublicationRecord | None
    recommended_next_action: str
    withdrawal: PublicationWithdrawal | None = None
    catalog_rebuild_attempted: bool = False
    catalog_replacement_completed: bool = False
    catalog_verification_completed: bool = False
    catalog_build: AcademicCatalogBuildResult | None = None
    catalog_error: Exception | None = None
    withdrawal_manifest_verification: WithdrawalManifestVerification | None = None

    def __post_init__(self) -> None:
        if self.operation not in {
            "publish",
            "supersede",
            "withdraw",
            "republish_after_withdrawal",
        }:
            raise ValueError("operation is not a supported publication transition.")
        if self.canonical_state not in {
            "producer_only",
            "uncertain",
            "confirmed",
        }:
            raise ValueError("canonical_state is invalid.")
        if self.manifest_generation is not None and not isinstance(
            self.manifest_generation,
            AcademicResultManifestGenerationResult,
        ):
            raise TypeError(
                "manifest_generation must be an "
                "AcademicResultManifestGenerationResult or None."
            )
        if self.generation_partial_state is not None and not isinstance(
            self.generation_partial_state,
            ManifestGenerationPartialState,
        ):
            raise TypeError(
                "generation_partial_state must be a "
                "ManifestGenerationPartialState or None."
            )
        if self.publication is not None and not isinstance(
            self.publication, PublicationRecord
        ):
            raise TypeError("publication must be a PublicationRecord or None.")
        if self.withdrawal is not None and not isinstance(
            self.withdrawal, PublicationWithdrawal
        ):
            raise TypeError("withdrawal must be a PublicationWithdrawal or None.")
        if (
            not isinstance(self.recommended_next_action, str)
            or not self.recommended_next_action
        ):
            raise ValueError("recommended_next_action must be nonempty.")
        if self.canonical_state == "producer_only" and self.publication is not None:
            raise ValueError(
                "producer_only partial state must not claim a Core publication."
            )
        for name in (
            "catalog_rebuild_attempted",
            "catalog_replacement_completed",
            "catalog_verification_completed",
        ):
            if not isinstance(getattr(self, name), bool):
                raise TypeError(f"{name} must be Boolean.")
        if self.catalog_replacement_completed and not self.catalog_rebuild_attempted:
            raise ValueError("catalog replacement requires a rebuild attempt.")
        if (
            self.catalog_verification_completed
            and not self.catalog_replacement_completed
        ):
            raise ValueError("catalog verification requires replacement completion.")
        if self.catalog_replacement_completed and self.catalog_build is None:
            raise ValueError("completed catalog replacement requires its build result.")
        if self.catalog_build is not None and not isinstance(
            self.catalog_build, AcademicCatalogBuildResult
        ):
            raise TypeError("catalog_build must be AcademicCatalogBuildResult or None.")
        if self.catalog_error is not None and not isinstance(
            self.catalog_error, Exception
        ):
            raise TypeError("catalog_error must be an Exception or None.")
        if (
            self.withdrawal_manifest_verification is not None
            and self.withdrawal_manifest_verification
            not in {
                "verified",
                "missing",
                "digest_mismatch_or_unsafe",
                "unreadable",
            }
        ):
            raise ValueError("withdrawal_manifest_verification is invalid.")


class ConcordAcademicResultPublicationPartialSuccessError(
    ConcordAcademicResultPublicationError
):
    """Producer/Core state is durable but the operation needs reconciliation."""

    def __init__(
        self,
        message: str,
        state: PublicationPartialSuccessState,
    ) -> None:
        super().__init__(message)
        self.state = state


@dataclass(frozen=True, slots=True)
class PublicationCatalogReconciliation:
    """One rebuilt Core catalog plus the exact reconciled Concord row."""

    build: AcademicCatalogBuildResult
    publication: CatalogPublication

    def __post_init__(self) -> None:
        if not isinstance(self.build, AcademicCatalogBuildResult):
            raise TypeError("build must be an AcademicCatalogBuildResult.")
        if not isinstance(self.publication, CatalogPublication):
            raise TypeError("publication must be a CatalogPublication.")


@dataclass(frozen=True, slots=True)
class AcademicResultPublicationResult:
    """Verified Core publication of one exact Concord manifest revision."""

    disposition: PublicationDisposition
    publication: PublicationRecord
    registration: AcademicWorkRegistration
    compatibility: PublicationCompatibilityResult
    catalog: PublicationCatalogReconciliation
    manifest_generation: AcademicResultManifestGenerationResult

    def __post_init__(self) -> None:
        if self.disposition not in {"created", "existing"}:
            raise ValueError("disposition must be created or existing.")
        if not isinstance(self.publication, PublicationRecord):
            raise TypeError("publication must be a PublicationRecord.")
        if not isinstance(self.registration, AcademicWorkRegistration):
            raise TypeError("registration must be an AcademicWorkRegistration.")
        if not isinstance(self.compatibility, PublicationCompatibilityResult):
            raise TypeError(
                "compatibility must be a PublicationCompatibilityResult."
            )
        if not isinstance(self.catalog, PublicationCatalogReconciliation):
            raise TypeError("catalog must be a PublicationCatalogReconciliation.")
        if not isinstance(
            self.manifest_generation,
            AcademicResultManifestGenerationResult,
        ):
            raise TypeError(
                "manifest_generation must be an "
                "AcademicResultManifestGenerationResult."
            )
        if self.publication.record_set_revision != self.manifest_generation.revision:
            raise ValueError(
                "publication and manifest_generation revisions must agree."
            )
        if self.catalog.publication.publication_id != self.publication.publication_id:
            raise ValueError("catalog row must belong to publication.")


@dataclass(frozen=True, slots=True)
class AcademicResultWithdrawalResult:
    """Verified explicit withdrawal of one Concord Core publication."""

    disposition: PublicationDisposition
    publication: PublicationRecord
    withdrawal: PublicationWithdrawal
    catalog: PublicationCatalogReconciliation
    manifest_verification: WithdrawalManifestVerification

    def __post_init__(self) -> None:
        if self.disposition not in {"created", "existing"}:
            raise ValueError("disposition must be created or existing.")
        if not isinstance(self.publication, PublicationRecord):
            raise TypeError("publication must be a PublicationRecord.")
        if not isinstance(self.withdrawal, PublicationWithdrawal):
            raise TypeError("withdrawal must be a PublicationWithdrawal.")
        if not isinstance(self.catalog, PublicationCatalogReconciliation):
            raise TypeError("catalog must be a PublicationCatalogReconciliation.")
        if self.withdrawal.publication_id != self.publication.publication_id:
            raise ValueError("withdrawal must belong to publication.")
        if self.catalog.publication.publication_id != self.publication.publication_id:
            raise ValueError("catalog row must belong to publication.")
        if self.manifest_verification not in {
            "verified",
            "missing",
            "digest_mismatch_or_unsafe",
            "unreadable",
        }:
            raise ValueError("manifest_verification is invalid.")


@dataclass(frozen=True, slots=True)
class ConcordPublicationSeriesState:
    """Presentation-neutral reconciliation of one Concord publication series."""

    work: ModuleWorkRef
    producer_revisions: tuple[int, ...]
    producer_head: StoredAcademicResultManifest | None
    publications: tuple[PublicationRecord, ...]
    withdrawals: tuple[PublicationWithdrawal, ...]
    core_head: PublicationRecord | None
    core_head_withdrawal: PublicationWithdrawal | None
    current_selectable_publication: PublicationRecord | None
    current_registration: AcademicWorkRegistration | None
    catalog_available: bool
    catalog_rows: tuple[CatalogPublication, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.work, ModuleWorkRef):
            raise TypeError("work must be a ModuleWorkRef.")
        object.__setattr__(self, "producer_revisions", tuple(self.producer_revisions))
        object.__setattr__(self, "publications", tuple(self.publications))
        object.__setattr__(self, "withdrawals", tuple(self.withdrawals))
        object.__setattr__(self, "catalog_rows", tuple(self.catalog_rows))
        if any(
            isinstance(item, bool) or not isinstance(item, int) or item < 1
            for item in self.producer_revisions
        ):
            raise TypeError("producer_revisions must contain positive integers.")
        if tuple(sorted(set(self.producer_revisions))) != self.producer_revisions:
            raise ValueError("producer_revisions must be unique and ascending.")
        if (self.producer_head is None) != (not self.producer_revisions):
            raise ValueError("producer_head presence must agree with revisions.")
        if (
            self.producer_head is not None
            and self.producer_head.revision != self.producer_revisions[-1]
        ):
            raise ValueError("producer_head must be the greatest producer revision.")
        if any(
            not isinstance(item, PublicationRecord) for item in self.publications
        ):
            raise TypeError("publications must contain PublicationRecord values.")
        if any(
            not isinstance(item, PublicationWithdrawal)
            for item in self.withdrawals
        ):
            raise TypeError("withdrawals must contain PublicationWithdrawal values.")
        if any(not isinstance(item, CatalogPublication) for item in self.catalog_rows):
            raise TypeError("catalog_rows must contain CatalogPublication values.")
        publication_ids = {item.publication_id for item in self.publications}
        withdrawal_ids = tuple(item.publication_id for item in self.withdrawals)
        if len(set(withdrawal_ids)) != len(withdrawal_ids):
            raise ValueError("withdrawals must not contain duplicate publication IDs.")
        if not set(withdrawal_ids).issubset(publication_ids):
            raise ValueError("withdrawals must belong to this publication series.")
        expected_head = _series_head(self.publications)
        if self.core_head != expected_head:
            raise ValueError("core_head disagrees with the supersession chain.")
        if self.core_head_withdrawal is not None and (
            self.core_head is None
            or self.core_head_withdrawal.publication_id
            != self.core_head.publication_id
        ):
            raise ValueError("core_head_withdrawal must belong to core_head.")
        expected_selectable = (
            self.core_head
            if self.core_head is not None and self.core_head_withdrawal is None
            else None
        )
        if self.current_selectable_publication != expected_selectable:
            raise ValueError("current selectable publication disagrees with Core.")
        if self.current_registration is not None and (
            not isinstance(self.current_registration, AcademicWorkRegistration)
            or self.current_registration.work != self.work
        ):
            raise ValueError("current_registration must belong to work.")
        if not isinstance(self.catalog_available, bool):
            raise TypeError("catalog_available must be Boolean.")
        if not self.catalog_available and self.catalog_rows:
            raise ValueError("catalog rows require an available catalog.")

    @property
    def current_registration_revision(self) -> int | None:
        return (
            None
            if self.current_registration is None
            else self.current_registration.registration_revision
        )

    @property
    def producer_head_revision(self) -> int | None:
        return None if self.producer_head is None else self.producer_head.revision

    @property
    def producer_head_projection_digest(self) -> str | None:
        return (
            None
            if self.producer_head is None
            else self.producer_head.manifest.projection.projection_digest
        )


def _clock_now() -> datetime:
    return datetime.now(timezone.utc)


def _work_identity(class_id: str, activity_id: str) -> ModuleWorkRef:
    try:
        return ModuleWorkRef(
            module_id=CONCORD_MODULE_ID,
            class_id=class_id,
            work_id=activity_id,
        )
    except Exception as error:
        raise ConcordAcademicResultPublicationValidationError(
            "Publication request does not identify safe Concord work."
        ) from error


def _work(request: GenerateAcademicResultManifestRequest) -> ModuleWorkRef:
    return _work_identity(request.class_id, request.activity_id)


def _source_record(work: ModuleWorkRef) -> ModuleRecordRef:
    try:
        return ModuleRecordRef(
            module_id=CONCORD_MODULE_ID,
            record_kind=CONCORD_ACTIVITY_RECORD_KIND,
            record_id=work.work_id,
            contract_version=CONCORD_ACTIVITY_CONTRACT_VERSION,
        )
    except Exception as error:
        raise ConcordAcademicResultPublicationIntegrityError(
            "Concord Activity source identity is invalid."
        ) from error


def _raise_generation_error(
    error: ConcordManifestGenerationError,
    *,
    operation: PublicationOperation,
) -> NoReturn:
    if isinstance(error, ConcordManifestGenerationPartialSuccessError):
        raise ConcordAcademicResultPublicationPartialSuccessError(
            "Producer manifest state may be durable; reconcile manifest generation "
            "before retrying publication.",
            PublicationPartialSuccessState(
                operation=operation,
                canonical_state="producer_only",
                manifest_generation=None,
                generation_partial_state=error.state,
                publication=None,
                recommended_next_action=(
                    "Reconcile the immutable Concord manifest revision, then retry "
                    "the same publication request."
                ),
            ),
        ) from error
    if isinstance(error, ConcordManifestGenerationValidationError):
        raise ConcordAcademicResultPublicationValidationError(str(error)) from error
    if isinstance(error, ConcordManifestGenerationNotFoundError):
        raise ConcordAcademicResultPublicationNotFoundError(str(error)) from error
    if isinstance(error, ConcordManifestGenerationConflictError):
        raise ConcordAcademicResultPublicationConflictError(str(error)) from error
    if isinstance(error, ConcordManifestGenerationIntegrityError):
        raise ConcordAcademicResultPublicationIntegrityError(str(error)) from error
    if isinstance(error, ConcordManifestGenerationWriteError):
        raise ConcordAcademicResultPublicationWriteError(str(error)) from error
    raise ConcordAcademicResultPublicationIntegrityError(str(error)) from error


def _current_registration(
    root: Path,
    request: GenerateAcademicResultManifestRequest,
    generation: AcademicResultManifestGenerationResult,
) -> AcademicWorkRegistration:
    try:
        registration = load_current_concord_academic_work_registration(
            root,
            request.class_id,
            request.activity_id,
        )
    except ConcordAcademicWorkRegistrationNotFoundError as error:
        raise ConcordAcademicResultPublicationNotFoundError(str(error)) from error
    except ConcordAcademicWorkRegistrationValidationError as error:
        raise ConcordAcademicResultPublicationValidationError(str(error)) from error
    except ConcordAcademicWorkRegistrationIntegrityError as error:
        raise ConcordAcademicResultPublicationIntegrityError(str(error)) from error
    except ConcordAcademicWorkRegistrationError as error:
        raise ConcordAcademicResultPublicationIntegrityError(str(error)) from error
    if registration is None:
        raise ConcordAcademicResultPublicationIntegrityError(
            "The registration used by manifest generation disappeared before "
            "publication."
        )
    expected_source = _source_record(generation.manifest.work)
    if (
        registration.registration_revision != generation.registration_revision
        or registration.work != generation.manifest.work
        or registration.producer_contract_version
        != CONCORD_ACADEMIC_WORK_CONTRACT_VERSION
        or registration.work_kind != CONCORD_ACADEMIC_WORK_KIND
        or registration.source_records != (expected_source,)
        or registration.title != generation.manifest.activity_context.title
    ):
        raise ConcordAcademicResultPublicationConflictError(
            "Current Academic Work Registration changed after manifest generation; "
            "regenerate/reconcile before publication."
        )
    return registration


def _validate_manifest_identity(
    manifest: AcademicResultManifest,
    *,
    work: ModuleWorkRef,
    source_record: ModuleRecordRef,
) -> None:
    source = manifest.source_activity
    context = manifest.activity_context
    if (
        manifest.work != work
        or manifest.contract_version != ACADEMIC_RESULT_MANIFEST_CONTRACT_VERSION
        or manifest.record_set.record_set_id
        != CONCORD_ACADEMIC_RESULT_RECORD_SET_ID
        or source.module_id != source_record.module_id
        or source.record_kind != source_record.record_kind
        or source.record_id != source_record.record_id
        or source.contract_version != source_record.contract_version
        or context.activity_id != work.work_id
        or context.class_id != work.class_id
    ):
        raise ConcordAcademicResultPublicationIntegrityError(
            "Concord manifest identity does not agree across work, Activity source, "
            "and Activity context."
        )


def _manifest_request(
    generation: AcademicResultManifestGenerationResult,
    registration: AcademicWorkRegistration,
) -> PublicationManifestRequest:
    work = generation.manifest.work
    source_record = _source_record(work)
    _validate_manifest_identity(
        generation.manifest,
        work=work,
        source_record=source_record,
    )
    capabilities = derive_manifest_capabilities(generation.manifest)
    try:
        return PublicationManifestRequest(
            work=work,
            source_record=source_record,
            publication_kind=CONCORD_ACADEMIC_RESULT_PUBLICATION_KIND,
            capabilities=capabilities,
            record_set_id=CONCORD_ACADEMIC_RESULT_RECORD_SET_ID,
            record_set_revision=generation.revision,
            manifest_contract_version=ACADEMIC_RESULT_MANIFEST_CONTRACT_VERSION,
            manifest_path=generation.relative_path,
            academic_work_registration_revision=(
                registration.registration_revision
            ),
            expected_manifest_digest=generation.sha256,
        )
    except RegistryServiceValidationError as error:
        raise ConcordAcademicResultPublicationValidationError(str(error)) from error
    except Exception as error:
        raise ConcordAcademicResultPublicationIntegrityError(
            "Could not construct the exact Core Publication Manifest request."
        ) from error


def _raise_core_error(
    error: RegistryServiceError,
    generation: AcademicResultManifestGenerationResult,
    *,
    operation: PublicationOperation,
) -> NoReturn:
    if isinstance(error, RegistryServicePartialSuccessError):
        raise ConcordAcademicResultPublicationPartialSuccessError(
            "Core publication may be durable but canonical completion is uncertain.",
            PublicationPartialSuccessState(
                operation=operation,
                canonical_state="uncertain",
                manifest_generation=generation,
                generation_partial_state=None,
                publication=error.state.publication,
                recommended_next_action=(
                    "Reload Core canonical publication state and reconcile the same "
                    "logical producer revision before attempting a different action."
                ),
            ),
        ) from error
    if isinstance(error, RegistryServiceValidationError):
        raise ConcordAcademicResultPublicationValidationError(str(error)) from error
    if isinstance(error, RegistryServiceNotFoundError):
        raise ConcordAcademicResultPublicationNotFoundError(str(error)) from error
    if isinstance(error, RegistryServiceConflictError):
        raise ConcordAcademicResultPublicationConflictError(str(error)) from error
    if isinstance(error, RegistryServiceIntegrityError):
        raise ConcordAcademicResultPublicationIntegrityError(str(error)) from error
    if isinstance(error, RegistryServiceWriteError):
        raise ConcordAcademicResultPublicationWriteError(str(error)) from error
    raise ConcordAcademicResultPublicationWriteError(str(error)) from error


def _referenced_registration(
    root: Path,
    publication: PublicationRecord,
) -> AcademicWorkRegistration:
    revision = publication.academic_work_registration_revision
    if revision is None:
        raise ConcordAcademicResultPublicationIntegrityError(
            "Concord academic-result publication is missing its registration revision."
        )
    try:
        return load_academic_work_registration_revision(
            root,
            publication.work,
            revision,
        )
    except AcademicWorkRegistrationNotFoundError as error:
        raise ConcordAcademicResultPublicationIntegrityError(
            "Publication references a missing Academic Work Registration revision."
        ) from error
    except AcademicWorkRegistrationIntegrityError as error:
        raise ConcordAcademicResultPublicationIntegrityError(str(error)) from error
    except AcademicWorkRegistrationReadError as error:
        raise ConcordAcademicResultPublicationIntegrityError(str(error)) from error
    except AcademicWorkRegistrationStorageError as error:
        raise ConcordAcademicResultPublicationWriteError(str(error)) from error


def _verify_publication(
    root: Path,
    service: PublicationServiceResult,
    generation: AcademicResultManifestGenerationResult,
    *,
    expected_supersedes_publication_id: str | None,
) -> tuple[
    PublicationRecord,
    AcademicWorkRegistration,
    PublicationCompatibilityResult,
]:
    publication = service.publication
    if service.withdrawal is not None:
        raise ConcordAcademicResultPublicationIntegrityError(
            "Core publication unexpectedly returned a withdrawal."
        )
    try:
        canonical = get_canonical_publication_record(
            root, publication.publication_id
        )
    except RegistryServiceError as error:
        raise ConcordAcademicResultPublicationIntegrityError(
            "Core publication exists but could not be reloaded canonically."
        ) from error
    if canonical != publication:
        raise ConcordAcademicResultPublicationIntegrityError(
            "Core canonical Publication Record differs from the service result."
        )

    expected_source = _source_record(generation.manifest.work)
    expected_capabilities = derive_manifest_capabilities(generation.manifest)
    _validate_manifest_identity(
        generation.manifest,
        work=canonical.work,
        source_record=expected_source,
    )
    if (
        canonical.work != generation.manifest.work
        or canonical.source_record != expected_source
        or canonical.publication_kind
        != CONCORD_ACADEMIC_RESULT_PUBLICATION_KIND
        or canonical.capabilities != expected_capabilities
        or canonical.record_set_id != CONCORD_ACADEMIC_RESULT_RECORD_SET_ID
        or canonical.record_set_revision != generation.revision
        or canonical.manifest_contract_version
        != ACADEMIC_RESULT_MANIFEST_CONTRACT_VERSION
        or canonical.manifest_path != generation.relative_path
        or canonical.manifest_digest_algorithm != "sha256"
        or canonical.manifest_digest != generation.sha256
        or canonical.academic_work_registration_revision
        != generation.registration_revision
        or canonical.supersedes_publication_id
        != expected_supersedes_publication_id
    ):
        raise ConcordAcademicResultPublicationIntegrityError(
            "Core Publication Record does not exactly bind the Concord producer "
            "manifest and Activity registration."
        )

    try:
        verify_publication_manifest(root, canonical)
    except PublicationManifestNotFoundError as error:
        raise ConcordAcademicResultPublicationIntegrityError(
            "Published Concord manifest disappeared after Core publication."
        ) from error
    except PublicationManifestIntegrityError as error:
        raise ConcordAcademicResultPublicationIntegrityError(str(error)) from error
    except PublicationManifestError as error:
        raise ConcordAcademicResultPublicationWriteError(str(error)) from error

    registration = _referenced_registration(root, canonical)
    if (
        registration.registration_revision != generation.registration_revision
        or registration.work != canonical.work
        or registration.producer_contract_version
        != CONCORD_ACADEMIC_WORK_CONTRACT_VERSION
        or registration.work_kind != CONCORD_ACADEMIC_WORK_KIND
        or registration.source_records != (expected_source,)
        or registration.title != generation.manifest.activity_context.title
    ):
        raise ConcordAcademicResultPublicationIntegrityError(
            "Referenced Academic Work Registration does not match the exact "
            "Concord publication contract."
        )

    try:
        compatibility = evaluate_publication_compatibility(
            canonical,
            get_publication_producer_profile(),
            registration,
        )
    except PublicationCompatibilityError as error:
        raise ConcordAcademicResultPublicationIntegrityError(str(error)) from error
    if not compatibility.compatible:
        raise ConcordAcademicResultPublicationIntegrityError(
            "Core reports the Concord publication as "
            "contract-incompatible: " + ", ".join(compatibility.codes)
        )
    return canonical, registration, compatibility


def _post_core_partial(
    error: ConcordAcademicResultPublicationError,
    generation: AcademicResultManifestGenerationResult,
    publication: PublicationRecord,
    *,
    operation: PublicationOperation,
) -> NoReturn:
    raise ConcordAcademicResultPublicationPartialSuccessError(
        "Core publication is durable but Concord post-write verification failed.",
        PublicationPartialSuccessState(
            operation=operation,
            canonical_state="confirmed",
            manifest_generation=generation,
            generation_partial_state=None,
            publication=publication,
            recommended_next_action=(
                "Reconcile this exact Core publication and producer manifest before "
                "creating, superseding, or withdrawing another publication."
            ),
        ),
    ) from error


def _validate_canonical_publication_record(
    publication: PublicationRecord,
    *,
    expected_work: ModuleWorkRef,
) -> PublicationRecord:
    if not isinstance(publication, PublicationRecord):
        raise ConcordAcademicResultPublicationIntegrityError(
            "Canonical publication has the wrong model type."
        )
    source_record = _source_record(expected_work)
    try:
        expected_path = academic_result_manifest_relative_path(
            expected_work,
            publication.record_set_revision,
        )
    except ConcordManifestGenerationError as error:
        raise ConcordAcademicResultPublicationIntegrityError(
            "Canonical publication has an invalid producer revision."
        ) from error
    if (
        publication.work != expected_work
        or publication.source_record != source_record
        or publication.publication_kind
        != CONCORD_ACADEMIC_RESULT_PUBLICATION_KIND
        or publication.record_set_id != CONCORD_ACADEMIC_RESULT_RECORD_SET_ID
        or publication.manifest_contract_version
        != ACADEMIC_RESULT_MANIFEST_CONTRACT_VERSION
        or publication.manifest_path != expected_path
    ):
        raise ConcordAcademicResultPublicationIntegrityError(
            "Canonical publication contradicts Concord's exact producer contract."
        )
    supported = get_publication_producer_profile().publication_contracts[0]
    if not set(publication.capabilities).issubset(
        supported.supported_capabilities
    ):
        raise ConcordAcademicResultPublicationIntegrityError(
            "Canonical publication advertises a capability outside Concord's profile."
        )
    return publication


def _load_series(
    root: Path,
    work: ModuleWorkRef,
) -> tuple[PublicationRecord, ...]:
    try:
        records = list_publication_record_set(
            root,
            work,
            CONCORD_ACADEMIC_RESULT_PUBLICATION_KIND,
            CONCORD_ACADEMIC_RESULT_RECORD_SET_ID,
        )
    except PublicationStorageError as error:
        raise ConcordAcademicResultPublicationIntegrityError(str(error)) from error
    for publication in records:
        _validate_canonical_publication_record(
            publication,
            expected_work=work,
        )
    try:
        return validate_publication_record_series(records)
    except PublicationRecordError as error:
        raise ConcordAcademicResultPublicationIntegrityError(str(error)) from error


def _series_head(
    records: tuple[PublicationRecord, ...],
) -> PublicationRecord | None:
    if not records:
        return None
    superseded = {
        item.supersedes_publication_id
        for item in records
        if item.supersedes_publication_id is not None
    }
    heads = tuple(
        item for item in records if item.publication_id not in superseded
    )
    if len(heads) != 1:
        raise ConcordAcademicResultPublicationIntegrityError(
            "Canonical Concord publication series does not have exactly one head."
        )
    return heads[0]


class _CatalogReconciliationFailure(Exception):
    def __init__(
        self,
        error: Exception,
        *,
        build: AcademicCatalogBuildResult | None,
    ) -> None:
        super().__init__(str(error))
        self.error = error
        self.build = build


def _catalog_query(
    work: ModuleWorkRef,
    *,
    required_capabilities: tuple[PublicationCapability, ...] = (),
    state: PublicationCatalogState = "all",
) -> PublicationCatalogQuery:
    try:
        return PublicationCatalogQuery(
            class_id=work.class_id,
            module_id=work.module_id,
            work_id=work.work_id,
            publication_kind=CONCORD_ACADEMIC_RESULT_PUBLICATION_KIND,
            required_capabilities=required_capabilities,
            record_set_id=CONCORD_ACADEMIC_RESULT_RECORD_SET_ID,
            state=state,
        )
    except AcademicCatalogValidationError as error:
        raise ConcordAcademicResultPublicationValidationError(str(error)) from error


def _raise_catalog_error(error: AcademicCatalogError) -> NoReturn:
    if isinstance(error, AcademicCatalogValidationError):
        raise ConcordAcademicResultPublicationValidationError(str(error)) from error
    if isinstance(error, AcademicCatalogNotFoundError):
        raise ConcordAcademicResultPublicationNotFoundError(str(error)) from error
    if isinstance(error, AcademicCatalogConflictError):
        raise ConcordAcademicResultPublicationConflictError(str(error)) from error
    if isinstance(
        error,
        (
            AcademicCatalogSourceError,
            AcademicCatalogIntegrityError,
            AcademicCatalogCompatibilityError,
            AcademicCatalogReadError,
        ),
    ):
        raise ConcordAcademicResultPublicationIntegrityError(str(error)) from error
    if isinstance(error, AcademicCatalogBuildError):
        raise ConcordAcademicResultPublicationWriteError(str(error)) from error
    raise ConcordAcademicResultPublicationWriteError(str(error)) from error


def _status_current_registration(
    root: Path,
    work: ModuleWorkRef,
) -> AcademicWorkRegistration | None:
    try:
        registration = load_current_concord_academic_work_registration(
            root,
            work.class_id,
            work.work_id,
        )
    except ConcordAcademicWorkRegistrationNotFoundError:
        return None
    except ConcordAcademicWorkRegistrationValidationError as error:
        raise ConcordAcademicResultPublicationValidationError(str(error)) from error
    except ConcordAcademicWorkRegistrationIntegrityError as error:
        raise ConcordAcademicResultPublicationIntegrityError(str(error)) from error
    except ConcordAcademicWorkRegistrationError as error:
        raise ConcordAcademicResultPublicationIntegrityError(str(error)) from error
    if registration is None:
        return None
    expected_source = _source_record(work)
    if (
        registration.work != work
        or registration.producer_contract_version
        != CONCORD_ACADEMIC_WORK_CONTRACT_VERSION
        or registration.work_kind != CONCORD_ACADEMIC_WORK_KIND
        or registration.source_records != (expected_source,)
    ):
        raise ConcordAcademicResultPublicationIntegrityError(
            "Current Academic Work Registration contradicts Concord's contract."
        )
    return registration


def _load_withdrawals(
    root: Path,
    records: tuple[PublicationRecord, ...],
) -> tuple[PublicationWithdrawal, ...]:
    withdrawals: list[PublicationWithdrawal] = []
    for publication in records:
        try:
            withdrawal = get_canonical_publication_withdrawal(
                root,
                publication.publication_id,
            )
        except RegistryServiceError as error:
            raise ConcordAcademicResultPublicationIntegrityError(
                "Could not load canonical Concord withdrawal state."
            ) from error
        if withdrawal is not None:
            withdrawals.append(withdrawal)
    return tuple(withdrawals)


def _catalog_record_values(row: CatalogPublication) -> tuple[object, ...]:
    return (
        row.work,
        row.source_record,
        row.publication_kind,
        row.capabilities,
        row.record_set_id,
        row.record_set_revision,
        row.manifest_contract_version,
        row.manifest_path,
        row.manifest_digest_algorithm,
        row.manifest_digest,
        row.published_at,
        row.academic_work_registration_revision,
        row.supersedes_publication_id,
    )


def _canonical_record_values(publication: PublicationRecord) -> tuple[object, ...]:
    return (
        publication.work,
        publication.source_record,
        publication.publication_kind,
        publication.capabilities,
        publication.record_set_id,
        publication.record_set_revision,
        publication.manifest_contract_version,
        publication.manifest_path,
        publication.manifest_digest_algorithm,
        publication.manifest_digest,
        publication.published_at,
        publication.academic_work_registration_revision,
        publication.supersedes_publication_id,
    )


def _validate_catalog_rows_against_canonical(
    root: Path,
    records: tuple[PublicationRecord, ...],
    withdrawals: tuple[PublicationWithdrawal, ...],
    rows: tuple[CatalogPublication, ...],
    current_registration: AcademicWorkRegistration | None,
) -> None:
    publication_by_id = {item.publication_id: item for item in records}
    row_by_id = {item.publication_id: item for item in rows}
    if len(row_by_id) != len(rows):
        raise ConcordAcademicResultPublicationIntegrityError(
            "Core academic catalog contains duplicate Concord publication rows."
        )
    if set(row_by_id) != set(publication_by_id):
        raise ConcordAcademicResultPublicationIntegrityError(
            "Core academic catalog does not cover the exact canonical Concord series."
        )
    withdrawal_by_id = {item.publication_id: item for item in withdrawals}
    head = _series_head(records)
    for publication_id, publication in publication_by_id.items():
        row = row_by_id[publication_id]
        withdrawal = withdrawal_by_id.get(publication_id)
        referenced_registration = _referenced_registration(root, publication)
        expected_head = head is not None and head.publication_id == publication_id
        expected_withdrawn = withdrawal is not None
        expected_current_revision = (
            None
            if current_registration is None
            else current_registration.registration_revision
        )
        expected_current_lifecycle = (
            None if current_registration is None else current_registration.lifecycle
        )
        if (
            _catalog_record_values(row) != _canonical_record_values(publication)
            or row.referenced_registration_lifecycle
            != referenced_registration.lifecycle
            or row.current_registration_revision != expected_current_revision
            or row.current_registration_lifecycle != expected_current_lifecycle
            or row.is_series_head != expected_head
            or row.is_withdrawn != expected_withdrawn
            or row.withdrawn_at
            != (None if withdrawal is None else withdrawal.withdrawn_at)
            or row.is_current_selectable
            != (expected_head and not expected_withdrawn)
        ):
            raise ConcordAcademicResultPublicationIntegrityError(
                "Core academic catalog row disagrees with canonical Concord state."
            )


def _reconcile_publication_catalog(
    root: Path,
    work: ModuleWorkRef,
    publication: PublicationRecord,
) -> PublicationCatalogReconciliation:
    try:
        build = rebuild_academic_catalog(root)
    except AcademicCatalogError as error:
        raise _CatalogReconciliationFailure(error, build=None) from error
    try:
        rows = query_publication_catalog(root, _catalog_query(work, state="all"))
        records = _load_series(root, work)
        withdrawals = _load_withdrawals(root, records)
        current_registration = _status_current_registration(root, work)
        _validate_catalog_rows_against_canonical(
            root,
            records,
            withdrawals,
            rows,
            current_registration,
        )
        matches = tuple(
            row for row in rows if row.publication_id == publication.publication_id
        )
        if len(matches) != 1:
            raise ConcordAcademicResultPublicationIntegrityError(
                "Rebuilt catalog does not contain exactly one target publication row."
            )
        return PublicationCatalogReconciliation(
            build=build,
            publication=matches[0],
        )
    except Exception as error:
        raise _CatalogReconciliationFailure(error, build=build) from error


def _raise_catalog_partial(
    failure: _CatalogReconciliationFailure,
    *,
    operation: PublicationOperation,
    generation: AcademicResultManifestGenerationResult | None,
    publication: PublicationRecord,
    withdrawal: PublicationWithdrawal | None = None,
    withdrawal_manifest_verification: WithdrawalManifestVerification | None = None,
) -> NoReturn:
    raise ConcordAcademicResultPublicationPartialSuccessError(
        "Canonical Core state is durable but catalog reconciliation failed.",
        PublicationPartialSuccessState(
            operation=operation,
            canonical_state="confirmed",
            manifest_generation=generation,
            generation_partial_state=None,
            publication=publication,
            withdrawal=withdrawal,
            recommended_next_action=(
                "Replay the exact operation or rebuild the Core academic catalog; "
                "do not create a duplicate publication."
            ),
            catalog_rebuild_attempted=True,
            catalog_replacement_completed=failure.build is not None,
            catalog_verification_completed=False,
            catalog_build=failure.build,
            catalog_error=failure.error,
            withdrawal_manifest_verification=(
                withdrawal_manifest_verification
            ),
        ),
    ) from failure.error


def _stored_manifest_for_publication(
    root: Path,
    publication: PublicationRecord,
) -> StoredAcademicResultManifest:
    try:
        stored = load_academic_result_manifest_revision(
            root,
            publication.work,
            publication.record_set_revision,
        )
    except ConcordManifestGenerationNotFoundError as error:
        raise ConcordAcademicResultPublicationIntegrityError(
            "Canonical publication references a missing Concord manifest revision."
        ) from error
    except ConcordManifestGenerationError as error:
        raise ConcordAcademicResultPublicationIntegrityError(str(error)) from error
    source_record = _source_record(publication.work)
    _validate_manifest_identity(
        stored.manifest,
        work=publication.work,
        source_record=source_record,
    )
    if (
        publication.source_record != source_record
        or publication.capabilities
        != derive_manifest_capabilities(stored.manifest)
        or publication.record_set_revision != stored.revision
        or publication.manifest_path != stored.relative_path
        or publication.manifest_digest != stored.sha256
        or publication.manifest_digest_algorithm != "sha256"
    ):
        raise ConcordAcademicResultPublicationIntegrityError(
            "Canonical publication does not exactly bind its Concord manifest."
        )
    try:
        resolved = verify_publication_manifest(root, publication)
        expected = stored.path.resolve(strict=True)
    except PublicationManifestNotFoundError as error:
        raise ConcordAcademicResultPublicationIntegrityError(
            "Canonical publication's Concord manifest is missing."
        ) from error
    except PublicationManifestIntegrityError as error:
        raise ConcordAcademicResultPublicationIntegrityError(str(error)) from error
    except PublicationManifestError as error:
        raise ConcordAcademicResultPublicationWriteError(str(error)) from error
    except OSError as error:
        raise ConcordAcademicResultPublicationWriteError(
            "Could not resolve the immutable Concord manifest path."
        ) from error
    if resolved != expected:
        raise ConcordAcademicResultPublicationIntegrityError(
            "Core resolved a different Concord manifest path than producer history."
        )
    registration = _referenced_registration(root, publication)
    if (
        registration.work != publication.work
        or registration.producer_contract_version
        != CONCORD_ACADEMIC_WORK_CONTRACT_VERSION
        or registration.work_kind != CONCORD_ACADEMIC_WORK_KIND
        or registration.source_records != (source_record,)
        or registration.title != stored.manifest.activity_context.title
    ):
        raise ConcordAcademicResultPublicationIntegrityError(
            "Canonical publication's referenced registration contradicts its "
            "Concord manifest."
        )
    try:
        compatibility = evaluate_publication_compatibility(
            publication,
            get_publication_producer_profile(),
            registration,
        )
    except PublicationCompatibilityError as error:
        raise ConcordAcademicResultPublicationIntegrityError(str(error)) from error
    if not compatibility.compatible:
        raise ConcordAcademicResultPublicationIntegrityError(
            "Canonical predecessor is incompatible with Concord's producer profile: "
            + ", ".join(compatibility.codes)
        )
    return stored


def _validate_supersession_pair(
    predecessor: StoredAcademicResultManifest,
    successor: AcademicResultManifestGenerationResult,
) -> None:
    if (
        predecessor.manifest.work != successor.manifest.work
        or predecessor.manifest.record_set.record_set_id
        != CONCORD_ACADEMIC_RESULT_RECORD_SET_ID
        or successor.manifest.record_set.record_set_id
        != CONCORD_ACADEMIC_RESULT_RECORD_SET_ID
    ):
        raise ConcordAcademicResultPublicationIntegrityError(
            "Producer manifests do not share one Concord publication series."
        )
    if successor.revision <= predecessor.revision:
        raise ConcordAcademicResultPublicationConflictError(
            "Successor producer revision must be greater than the predecessor revision."
        )
    if (
        successor.manifest.projection.projection_digest
        == predecessor.manifest.projection.projection_digest
    ):
        raise ConcordAcademicResultPublicationConflictError(
            "Concord's semantic public projection did not materially change."
        )


def query_concord_publication_catalog(
    class_id: str,
    activity_id: str,
    *,
    required_capabilities: tuple[PublicationCapability, ...] = (),
    state: PublicationCatalogState = "current",
    workspace_root: str | Path | None = None,
) -> tuple[CatalogPublication, ...]:
    """Query Core's derived catalog for one exact Concord Activity series."""
    try:
        resolved = resolve_read_workspace_root(workspace_root)
    except Exception as error:
        raise ConcordAcademicResultPublicationValidationError(str(error)) from error
    if resolved is None:
        raise ConcordAcademicResultPublicationNotFoundError(
            "Paper Data Suite workspace does not exist."
        )
    work = _work_identity(class_id, activity_id)
    query = _catalog_query(
        work,
        required_capabilities=required_capabilities,
        state=state,
    )
    try:
        return query_publication_catalog(Path(resolved), query)
    except AcademicCatalogError as error:
        _raise_catalog_error(error)


def load_concord_publication_series_status(
    class_id: str,
    activity_id: str,
    *,
    workspace_root: str | Path | None = None,
) -> ConcordPublicationSeriesState:
    """Reconcile producer, canonical Core, registration, and optional catalog state."""
    try:
        resolved = resolve_read_workspace_root(workspace_root)
    except Exception as error:
        raise ConcordAcademicResultPublicationValidationError(str(error)) from error
    if resolved is None:
        raise ConcordAcademicResultPublicationNotFoundError(
            "Paper Data Suite workspace does not exist."
        )
    root = Path(resolved)
    work = _work_identity(class_id, activity_id)
    try:
        history = list_academic_result_manifest_revisions(root, work)
    except ConcordManifestGenerationValidationError as error:
        raise ConcordAcademicResultPublicationValidationError(str(error)) from error
    except ConcordManifestGenerationNotFoundError as error:
        raise ConcordAcademicResultPublicationNotFoundError(str(error)) from error
    except ConcordManifestGenerationError as error:
        raise ConcordAcademicResultPublicationIntegrityError(str(error)) from error

    records = _load_series(root, work)
    for publication in records:
        _stored_manifest_for_publication(root, publication)
    withdrawals = _load_withdrawals(root, records)
    head = _series_head(records)
    withdrawal_by_id = {item.publication_id: item for item in withdrawals}
    head_withdrawal = (
        None if head is None else withdrawal_by_id.get(head.publication_id)
    )
    expected_selectable = (
        head if head is not None and head_withdrawal is None else None
    )
    try:
        selectable = get_current_publication_record(
            root,
            work,
            CONCORD_ACADEMIC_RESULT_PUBLICATION_KIND,
            CONCORD_ACADEMIC_RESULT_RECORD_SET_ID,
        )
    except PublicationStorageError as error:
        raise ConcordAcademicResultPublicationIntegrityError(str(error)) from error
    if selectable != expected_selectable:
        raise ConcordAcademicResultPublicationIntegrityError(
            "Core current-selectable publication disagrees with structural head state."
        )
    current_registration = _status_current_registration(root, work)

    catalog_available = False
    rows: tuple[CatalogPublication, ...] = ()
    try:
        load_academic_catalog_metadata(root)
    except AcademicCatalogNotFoundError:
        pass
    except AcademicCatalogError as error:
        _raise_catalog_error(error)
    else:
        try:
            rows = query_publication_catalog(root, _catalog_query(work, state="all"))
        except AcademicCatalogError as error:
            _raise_catalog_error(error)
        _validate_catalog_rows_against_canonical(
            root,
            records,
            withdrawals,
            rows,
            current_registration,
        )
        catalog_available = True

    return ConcordPublicationSeriesState(
        work=work,
        producer_revisions=tuple(item.revision for item in history),
        producer_head=history[-1] if history else None,
        publications=records,
        withdrawals=withdrawals,
        core_head=head,
        core_head_withdrawal=head_withdrawal,
        current_selectable_publication=selectable,
        current_registration=current_registration,
        catalog_available=catalog_available,
        catalog_rows=rows,
    )


def rebuild_concord_publication_catalog(
    class_id: str,
    activity_id: str,
    *,
    publication_id: str,
    workspace_root: str | Path | None = None,
) -> PublicationCatalogReconciliation:
    """Rebuild Core's full catalog and reconcile one exact Concord publication."""
    try:
        resolved = resolve_read_workspace_root(workspace_root)
    except Exception as error:
        raise ConcordAcademicResultPublicationValidationError(str(error)) from error
    if resolved is None:
        raise ConcordAcademicResultPublicationNotFoundError(
            "Paper Data Suite workspace does not exist."
        )
    root = Path(resolved)
    work = _work_identity(class_id, activity_id)
    records = _load_series(root, work)
    publication = next(
        (item for item in records if item.publication_id == publication_id),
        None,
    )
    if publication is None:
        raise ConcordAcademicResultPublicationNotFoundError(
            "Publication ID was not found in the exact Concord series."
        )
    try:
        return _reconcile_publication_catalog(root, work, publication)
    except _CatalogReconciliationFailure as failure:
        if isinstance(failure.error, AcademicCatalogError):
            _raise_catalog_error(failure.error)
        if isinstance(failure.error, ConcordAcademicResultPublicationError):
            raise failure.error from failure
        raise ConcordAcademicResultPublicationIntegrityError(
            "Catalog reconciliation failed after Core rebuilt the catalog."
        ) from failure.error


def rebuild_full_academic_catalog(
    workspace_root: str | Path,
) -> AcademicCatalogBuildResult:
    """Explicitly rebuild Core's complete disposable academic catalog."""
    try:
        return rebuild_academic_catalog(workspace_root)
    except AcademicCatalogError as error:
        _raise_catalog_error(error)


def _withdrawal_manifest_verification(
    root: Path,
    publication: PublicationRecord,
) -> WithdrawalManifestVerification:
    try:
        verify_publication_manifest(root, publication)
    except PublicationManifestNotFoundError:
        return "missing"
    except PublicationManifestIntegrityError:
        return "digest_mismatch_or_unsafe"
    except (PublicationManifestError, OSError):
        return "unreadable"
    return "verified"


def _raise_withdrawal_core_error(
    error: RegistryServiceError,
    *,
    publication: PublicationRecord | None,
) -> NoReturn:
    if isinstance(error, RegistryServicePartialSuccessError):
        raise ConcordAcademicResultPublicationPartialSuccessError(
            "Core withdrawal may be durable but canonical completion is uncertain.",
            PublicationPartialSuccessState(
                operation="withdraw",
                canonical_state="uncertain",
                manifest_generation=None,
                generation_partial_state=None,
                publication=error.state.publication or publication,
                withdrawal=error.state.withdrawal,
                recommended_next_action=(
                    "Reload the exact Core publication and withdrawal before "
                    "retrying or publishing a successor."
                ),
            ),
        ) from error
    if isinstance(error, RegistryServiceValidationError):
        raise ConcordAcademicResultPublicationValidationError(str(error)) from error
    if isinstance(error, RegistryServiceNotFoundError):
        raise ConcordAcademicResultPublicationNotFoundError(str(error)) from error
    if isinstance(error, RegistryServiceConflictError):
        raise ConcordAcademicResultPublicationConflictError(str(error)) from error
    if isinstance(error, RegistryServiceIntegrityError):
        raise ConcordAcademicResultPublicationIntegrityError(str(error)) from error
    if isinstance(error, RegistryServiceWriteError):
        raise ConcordAcademicResultPublicationWriteError(str(error)) from error
    raise ConcordAcademicResultPublicationWriteError(str(error)) from error


def _verify_withdrawal_result(
    root: Path,
    work: ModuleWorkRef,
    service: PublicationWithdrawalServiceResult,
) -> tuple[PublicationRecord, PublicationWithdrawal, WithdrawalManifestVerification]:
    try:
        publication = get_canonical_publication_record(
            root,
            service.publication.publication_id,
        )
        withdrawal = get_canonical_publication_withdrawal(
            root,
            service.publication.publication_id,
        )
    except RegistryServiceError as error:
        raise ConcordAcademicResultPublicationIntegrityError(
            "Core withdrawal exists but could not be reloaded canonically."
        ) from error
    if publication != service.publication or withdrawal != service.withdrawal:
        raise ConcordAcademicResultPublicationIntegrityError(
            "Canonical withdrawal state differs from Core's service result."
        )
    _validate_canonical_publication_record(publication, expected_work=work)
    series = _load_series(root, work)
    head = _series_head(series)
    if head is None or head.publication_id != publication.publication_id:
        raise ConcordAcademicResultPublicationIntegrityError(
            "Withdrawal target is no longer the structural Concord series head."
        )
    try:
        selectable = get_current_publication_record(
            root,
            work,
            CONCORD_ACADEMIC_RESULT_PUBLICATION_KIND,
            CONCORD_ACADEMIC_RESULT_RECORD_SET_ID,
        )
    except PublicationStorageError as error:
        raise ConcordAcademicResultPublicationIntegrityError(str(error)) from error
    if selectable is not None:
        raise ConcordAcademicResultPublicationIntegrityError(
            "Withdrawing the Concord head unexpectedly selected a predecessor."
        )
    return (
        publication,
        service.withdrawal,
        _withdrawal_manifest_verification(root, publication),
    )


def _post_withdrawal_partial(
    error: ConcordAcademicResultPublicationError,
    service: PublicationWithdrawalServiceResult,
) -> NoReturn:
    raise ConcordAcademicResultPublicationPartialSuccessError(
        "Core withdrawal is durable but Concord post-write verification failed.",
        PublicationPartialSuccessState(
            operation="withdraw",
            canonical_state="confirmed",
            manifest_generation=None,
            generation_partial_state=None,
            publication=service.publication,
            withdrawal=service.withdrawal,
            recommended_next_action=(
                "Reload this exact Core publication and withdrawal before "
                "publishing any successor."
            ),
        ),
    ) from error


def withdraw_concord_academic_result_publication(
    class_id: str,
    activity_id: str,
    *,
    publication_id: str,
    reason: str,
    workspace_root: str | Path | None = None,
) -> AcademicResultWithdrawalResult:
    """Explicitly withdraw the unique structural head of one Concord series."""
    try:
        resolved = resolve_read_workspace_root(workspace_root)
    except Exception as error:
        raise ConcordAcademicResultPublicationValidationError(str(error)) from error
    if resolved is None:
        raise ConcordAcademicResultPublicationNotFoundError(
            "Paper Data Suite workspace does not exist."
        )
    root = Path(resolved)
    work = _work_identity(class_id, activity_id)
    records = _load_series(root, work)
    if not records:
        raise ConcordAcademicResultPublicationNotFoundError(
            "Concord publication series does not exist."
        )
    publication = next(
        (item for item in records if item.publication_id == publication_id),
        None,
    )
    if publication is None:
        raise ConcordAcademicResultPublicationConflictError(
            "Publication ID does not belong to the exact Concord series."
        )
    head = _series_head(records)
    if head is None or head.publication_id != publication.publication_id:
        raise ConcordAcademicResultPublicationConflictError(
            "Only the structural Concord series head may be withdrawn here."
        )
    try:
        request = PublicationWithdrawalRequest(
            publication_id=publication.publication_id,
            reason=reason,
        )
    except (RegistryServiceValidationError, TypeError, ValueError) as error:
        raise ConcordAcademicResultPublicationValidationError(str(error)) from error
    try:
        service = withdraw_publication(root, request)
    except RegistryServiceError as error:
        _raise_withdrawal_core_error(error, publication=publication)
    try:
        publication, withdrawal, manifest_verification = _verify_withdrawal_result(
            root, work, service
        )
    except ConcordAcademicResultPublicationError as error:
        _post_withdrawal_partial(error, service)
    try:
        catalog = _reconcile_publication_catalog(root, work, publication)
    except _CatalogReconciliationFailure as failure:
        _raise_catalog_partial(
            failure,
            operation="withdraw",
            generation=None,
            publication=publication,
            withdrawal=withdrawal,
            withdrawal_manifest_verification=manifest_verification,
        )
    return AcademicResultWithdrawalResult(
        disposition=service.disposition,
        publication=publication,
        withdrawal=withdrawal,
        catalog=catalog,
        manifest_verification=manifest_verification,
    )


def republish_concord_academic_results_after_withdrawal(
    request: GenerateAcademicResultManifestRequest,
    *,
    expected_withdrawn_head_publication_id: str,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Callable[[], datetime] = _clock_now,
) -> AcademicResultPublicationResult:
    """Publish a corrected successor that explicitly supersedes a withdrawn head."""
    if not isinstance(request, GenerateAcademicResultManifestRequest):
        raise ConcordAcademicResultPublicationValidationError(
            "request must be GenerateAcademicResultManifestRequest."
        )
    if (
        not isinstance(expected_withdrawn_head_publication_id, str)
        or not expected_withdrawn_head_publication_id
    ):
        raise ConcordAcademicResultPublicationValidationError(
            "expected_withdrawn_head_publication_id must be a nonempty string."
        )
    try:
        resolved = resolve_read_workspace_root(workspace_root)
    except Exception as error:
        raise ConcordAcademicResultPublicationValidationError(str(error)) from error
    if resolved is None:
        raise ConcordAcademicResultPublicationNotFoundError(
            "Paper Data Suite workspace does not exist."
        )
    root = Path(resolved)
    work = _work(request)
    records = _load_series(root, work)
    if not records:
        raise ConcordAcademicResultPublicationNotFoundError(
            "Concord publication series does not exist."
        )
    withdrawn_record = next(
        (
            item
            for item in records
            if item.publication_id == expected_withdrawn_head_publication_id
        ),
        None,
    )
    if withdrawn_record is None:
        raise ConcordAcademicResultPublicationConflictError(
            "Expected withdrawn publication does not belong to the Concord series."
        )
    try:
        withdrawal = get_canonical_publication_withdrawal(
            root,
            withdrawn_record.publication_id,
        )
    except RegistryServiceError as error:
        _raise_withdrawal_core_error(error, publication=withdrawn_record)
    if withdrawal is None:
        raise ConcordAcademicResultPublicationConflictError(
            "Expected Concord publication is not withdrawn."
        )
    head = _series_head(records)
    if head is None:
        raise ConcordAcademicResultPublicationNotFoundError(
            "Concord publication series does not have a structural head."
        )
    exact_replay = (
        head.publication_id != withdrawn_record.publication_id
        and head.supersedes_publication_id == withdrawn_record.publication_id
    )
    if head.publication_id != withdrawn_record.publication_id and not exact_replay:
        raise ConcordAcademicResultPublicationConflictError(
            "Expected withdrawn publication is not the current structural head "
            "or the predecessor of an exact republication replay."
        )
    if head.publication_id == withdrawn_record.publication_id:
        try:
            selectable = get_current_publication_record(
                root,
                work,
                CONCORD_ACADEMIC_RESULT_PUBLICATION_KIND,
                CONCORD_ACADEMIC_RESULT_RECORD_SET_ID,
            )
        except PublicationStorageError as error:
            raise ConcordAcademicResultPublicationIntegrityError(str(error)) from error
        if selectable is not None:
            raise ConcordAcademicResultPublicationIntegrityError(
                "Withdrawn Concord structural head is unexpectedly selectable."
            )
    try:
        result = supersede_concord_academic_results(
            request,
            expected_current_publication_id=withdrawn_record.publication_id,
            workspace_root=root,
            standards_library=standards_library,
            clock=clock,
        )
    except ConcordAcademicResultPublicationPartialSuccessError as error:
        state = error.state
        raise ConcordAcademicResultPublicationPartialSuccessError(
            "Corrected republication after withdrawal needs reconciliation.",
            PublicationPartialSuccessState(
                operation="republish_after_withdrawal",
                canonical_state=state.canonical_state,
                manifest_generation=state.manifest_generation,
                generation_partial_state=state.generation_partial_state,
                publication=state.publication,
                withdrawal=withdrawal,
                recommended_next_action=state.recommended_next_action,
                catalog_rebuild_attempted=state.catalog_rebuild_attempted,
                catalog_replacement_completed=(
                    state.catalog_replacement_completed
                ),
                catalog_verification_completed=(
                    state.catalog_verification_completed
                ),
                catalog_build=state.catalog_build,
                catalog_error=state.catalog_error,
                withdrawal_manifest_verification=(
                    state.withdrawal_manifest_verification
                ),
            ),
        ) from error
    if (
        result.publication.record_set_revision
        <= withdrawn_record.record_set_revision
        or result.publication.supersedes_publication_id
        != withdrawn_record.publication_id
    ):
        raise ConcordAcademicResultPublicationIntegrityError(
            "Corrected republication did not advance and supersede the withdrawn head."
        )
    try:
        persisted_withdrawal = get_canonical_publication_withdrawal(
            root,
            withdrawn_record.publication_id,
        )
        selectable = get_current_publication_record(
            root,
            work,
            CONCORD_ACADEMIC_RESULT_PUBLICATION_KIND,
            CONCORD_ACADEMIC_RESULT_RECORD_SET_ID,
        )
    except RegistryServiceError as error:
        raise ConcordAcademicResultPublicationIntegrityError(str(error)) from error
    except PublicationStorageError as error:
        raise ConcordAcademicResultPublicationIntegrityError(str(error)) from error
    if persisted_withdrawal != withdrawal:
        raise ConcordAcademicResultPublicationIntegrityError(
            "Republication altered the predecessor's immutable withdrawal."
        )
    if selectable != result.publication:
        raise ConcordAcademicResultPublicationIntegrityError(
            "Corrected Concord republication is not the current selectable head."
        )
    return result


def publish_concord_academic_results(
    request: GenerateAcademicResultManifestRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Callable[[], datetime] = _clock_now,
) -> AcademicResultPublicationResult:
    """Generate/reuse the current producer manifest and publish it first in Core.

    This service intentionally implements only the initial publication transition.
    A nonempty Core series that requires a successor is a conflict; callers must
    use supersede_concord_academic_results with the exact expected Core head.
    """
    if not isinstance(request, GenerateAcademicResultManifestRequest):
        raise ConcordAcademicResultPublicationValidationError(
            "request must be GenerateAcademicResultManifestRequest."
        )
    if not callable(clock):
        raise ConcordAcademicResultPublicationValidationError(
            "clock must be callable."
        )
    try:
        resolved = resolve_read_workspace_root(workspace_root)
    except Exception as error:
        raise ConcordAcademicResultPublicationValidationError(str(error)) from error
    if resolved is None:
        raise ConcordAcademicResultPublicationNotFoundError(
            "Paper Data Suite workspace does not exist."
        )
    root = Path(resolved)
    work = _work(request)

    try:
        generation = generate_academic_result_manifest(
            request,
            workspace_root=root,
            standards_library=standards_library,
            clock=clock,
        )
    except ConcordManifestGenerationError as error:
        _raise_generation_error(error, operation="publish")

    if generation.manifest.work != work:
        raise ConcordAcademicResultPublicationIntegrityError(
            "Manifest generation returned a different Concord work identity."
        )
    registration = _current_registration(root, request, generation)
    manifest_request = _manifest_request(generation, registration)

    try:
        service = publish_manifest_revision(root, manifest_request)
    except RegistryServiceError as error:
        _raise_core_error(error, generation, operation="publish")

    try:
        canonical, referenced_registration, compatibility = _verify_publication(
            root,
            service,
            generation,
            expected_supersedes_publication_id=None,
        )
    except ConcordAcademicResultPublicationError as error:
        _post_core_partial(
            error,
            generation,
            service.publication,
            operation="publish",
        )

    try:
        catalog = _reconcile_publication_catalog(root, work, canonical)
    except _CatalogReconciliationFailure as failure:
        _raise_catalog_partial(
            failure,
            operation="publish",
            generation=generation,
            publication=canonical,
        )

    return AcademicResultPublicationResult(
        disposition=service.disposition,
        publication=canonical,
        registration=referenced_registration,
        compatibility=compatibility,
        catalog=catalog,
        manifest_generation=generation,
    )


def supersede_concord_academic_results(
    request: GenerateAcademicResultManifestRequest,
    *,
    expected_current_publication_id: str,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Callable[[], datetime] = _clock_now,
) -> AcademicResultPublicationResult:
    """Explicitly supersede one expected canonical Concord series head.

    The caller must name the exact predecessor Publication Record. An exact replay
    of a previously completed successor is reconciled idempotently; otherwise a
    stale or non-head predecessor is rejected before Core is asked to write.
    """
    if not isinstance(request, GenerateAcademicResultManifestRequest):
        raise ConcordAcademicResultPublicationValidationError(
            "request must be GenerateAcademicResultManifestRequest."
        )
    if (
        not isinstance(expected_current_publication_id, str)
        or not expected_current_publication_id
    ):
        raise ConcordAcademicResultPublicationValidationError(
            "expected_current_publication_id must be a nonempty string."
        )
    if not callable(clock):
        raise ConcordAcademicResultPublicationValidationError(
            "clock must be callable."
        )
    try:
        resolved = resolve_read_workspace_root(workspace_root)
    except Exception as error:
        raise ConcordAcademicResultPublicationValidationError(str(error)) from error
    if resolved is None:
        raise ConcordAcademicResultPublicationNotFoundError(
            "Paper Data Suite workspace does not exist."
        )
    root = Path(resolved)
    work = _work(request)

    try:
        generation = generate_academic_result_manifest(
            request,
            workspace_root=root,
            standards_library=standards_library,
            clock=clock,
        )
    except ConcordManifestGenerationError as error:
        _raise_generation_error(error, operation="supersede")
    if generation.manifest.work != work:
        raise ConcordAcademicResultPublicationIntegrityError(
            "Manifest generation returned a different Concord work identity."
        )
    registration = _current_registration(root, request, generation)

    records = _load_series(root, work)
    if not records:
        raise ConcordAcademicResultPublicationNotFoundError(
            "Publication series does not exist; use first publication."
        )
    predecessor_record = next(
        (
            item
            for item in records
            if item.publication_id == expected_current_publication_id
        ),
        None,
    )
    if predecessor_record is None:
        raise ConcordAcademicResultPublicationConflictError(
            "Expected publication ID does not belong to the Concord series."
        )

    logical = tuple(
        item
        for item in records
        if item.record_set_revision == generation.revision
    )
    if len(logical) > 1:
        raise ConcordAcademicResultPublicationIntegrityError(
            "Canonical Concord logical publication revision is duplicated."
        )
    if generation.revision <= predecessor_record.record_set_revision:
        raise ConcordAcademicResultPublicationConflictError(
            "Concord has no later material producer revision to supersede the "
            "expected publication."
        )
    if logical:
        replay = logical[0]
        if replay.supersedes_publication_id != expected_current_publication_id:
            raise ConcordAcademicResultPublicationIntegrityError(
                "Existing logical Concord revision has a contradictory predecessor."
            )
    else:
        head = _series_head(records)
        if head is None:
            raise ConcordAcademicResultPublicationNotFoundError(
                "Publication series does not have a canonical head."
            )
        if head.publication_id != expected_current_publication_id:
            raise ConcordAcademicResultPublicationConflictError(
                "Expected publication ID is not the canonical Concord series head."
            )

    predecessor = _stored_manifest_for_publication(root, predecessor_record)
    _validate_supersession_pair(predecessor, generation)
    manifest_request = _manifest_request(generation, registration)

    try:
        service = supersede_manifest_revision(
            root,
            manifest_request,
            expected_current_publication_id=expected_current_publication_id,
        )
    except RegistryServiceError as error:
        _raise_core_error(error, generation, operation="supersede")

    try:
        canonical, referenced_registration, compatibility = _verify_publication(
            root,
            service,
            generation,
            expected_supersedes_publication_id=(
                expected_current_publication_id
            ),
        )
        series = _load_series(root, work)
        if canonical not in series:
            raise ConcordAcademicResultPublicationIntegrityError(
                "Superseding publication is absent from its revalidated Core series."
            )
    except ConcordAcademicResultPublicationError as error:
        _post_core_partial(
            error,
            generation,
            service.publication,
            operation="supersede",
        )

    try:
        catalog = _reconcile_publication_catalog(root, work, canonical)
    except _CatalogReconciliationFailure as failure:
        _raise_catalog_partial(
            failure,
            operation="supersede",
            generation=generation,
            publication=canonical,
        )

    return AcademicResultPublicationResult(
        disposition=service.disposition,
        publication=canonical,
        registration=referenced_registration,
        compatibility=compatibility,
        catalog=catalog,
        manifest_generation=generation,
    )


__all__ = [
    "AcademicResultPublicationResult",
    "AcademicResultWithdrawalResult",
    "CONCORD_ACADEMIC_RESULT_PUBLICATION_KIND",
    "ConcordAcademicResultPublicationConflictError",
    "ConcordAcademicResultPublicationError",
    "ConcordAcademicResultPublicationIntegrityError",
    "ConcordAcademicResultPublicationNotFoundError",
    "ConcordAcademicResultPublicationPartialSuccessError",
    "ConcordAcademicResultPublicationValidationError",
    "ConcordAcademicResultPublicationWriteError",
    "ConcordPublicationSeriesState",
    "PublicationCanonicalState",
    "PublicationCatalogReconciliation",
    "PublicationDisposition",
    "PublicationOperation",
    "PublicationPartialSuccessState",
    "WithdrawalManifestVerification",
    "load_concord_publication_series_status",
    "publish_concord_academic_results",
    "query_concord_publication_catalog",
    "rebuild_concord_publication_catalog",
    "rebuild_full_academic_catalog",
    "republish_concord_academic_results_after_withdrawal",
    "supersede_concord_academic_results",
    "withdraw_concord_academic_result_publication",
]
