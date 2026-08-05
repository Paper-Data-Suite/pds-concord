"""Public exception taxonomy for Concord canonical storage."""

from concord.validation_diagnostics import ValidationIssue


class ConcordStorageError(RuntimeError):
    pass


class ConcordStorageValidationError(ConcordStorageError, ValueError):
    pass


class ConcordStorageReadError(ConcordStorageError):
    pass


class ConcordStorageNotFoundError(ConcordStorageReadError):
    pass


class ConcordStorageWriteError(ConcordStorageError):
    pass


class ConcordStorageConflictError(ConcordStorageWriteError):
    pass


class ConcordStoragePartialSuccessError(ConcordStorageWriteError):
    def __init__(
        self,
        message: str,
        *,
        durable_paths: tuple[str, ...],
        pointer_published: bool,
        snapshot_revision: int | None,
        snapshot_sha256: str | None,
    ) -> None:
        self.durable_paths = durable_paths
        self.pointer_published = pointer_published
        self.snapshot_revision = snapshot_revision
        self.snapshot_sha256 = snapshot_sha256
        super().__init__(message)


class ConcordStorageIntegrityError(ConcordStorageError):
    pass


class ConcordStorageGraphIntegrityError(ConcordStorageIntegrityError):
    def __init__(
        self,
        message: str,
        *,
        issues: tuple[ValidationIssue, ...],
    ) -> None:
        self.issues = issues
        super().__init__(message)


class ConcordCatalogError(ConcordStorageError):
    pass


class ConcordCatalogNotFoundError(ConcordCatalogError):
    pass


class ConcordCatalogConflictError(ConcordCatalogError):
    pass


class ConcordCatalogSourceError(ConcordCatalogError):
    pass


class ConcordCatalogIntegrityError(ConcordCatalogError):
    pass


class ConcordCatalogCompatibilityError(ConcordCatalogError):
    pass


class ConcordCatalogBuildError(ConcordCatalogError):
    pass
