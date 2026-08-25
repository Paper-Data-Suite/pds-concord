"""Strict noncanonical authoring inputs for reusable Concord Templates."""

from __future__ import annotations

import hashlib
import os
import stat
from dataclasses import dataclass
from pathlib import Path

from concord.models import (
    PrivacyPolicy,
    TemplateAuthorshipExpectation,
    TemplateCompatibility,
    TemplatePageDefinition,
    TemplateRenderingInput,
    TemplateSubjectExpectation,
)
from concord.template_serialization import (
    TemplateSerializationError,
    dataclass_from_dict,
    strict_json_loads,
)

TEMPLATE_AUTHORING_SCHEMA = "concord_template_authoring_v1"


class TemplateAuthoringError(ValueError):
    """A Template authoring or rendering source is invalid."""


class TemplateAuthoringConflictError(TemplateAuthoringError):
    """A prepared source changed before commit."""


@dataclass(frozen=True, slots=True, kw_only=True)
class TemplateDefinitionAuthoring:
    name: str
    purpose: str
    description: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise TemplateAuthoringError("definition.name must be non-empty.")
        if not isinstance(self.purpose, str) or not self.purpose.strip():
            raise TemplateAuthoringError("definition.purpose must be non-empty.")
        if self.description is not None and (
            not isinstance(self.description, str)
            or not self.description.strip()
        ):
            raise TemplateAuthoringError(
                "definition.description must be non-empty when supplied."
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class TemplateVersionAuthoring:
    version_label: str
    rendering_contract_version: str
    rendering_specification_reference: str
    page_manifest: tuple[TemplatePageDefinition, ...]
    rendering_inputs: tuple[TemplateRenderingInput, ...]
    default_expected_return_status: str
    default_privacy_policy: PrivacyPolicy
    compatibility: TemplateCompatibility
    default_authorship_expectation: TemplateAuthorshipExpectation | None = None
    default_subject_expectation: TemplateSubjectExpectation | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.version_label, str) or not self.version_label.strip():
            raise TemplateAuthoringError("version.version_label must be non-empty.")
        if not isinstance(self.rendering_contract_version, str):
            raise TemplateAuthoringError(
                "version.rendering_contract_version must be a string."
            )
        if not isinstance(self.rendering_specification_reference, str):
            raise TemplateAuthoringError(
                "version.rendering_specification_reference must be a string."
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class TemplateAuthoringDocument:
    schema_version: str
    artifact_category: str
    version: TemplateVersionAuthoring
    definition: TemplateDefinitionAuthoring | None = None

    def __post_init__(self) -> None:
        if self.schema_version != TEMPLATE_AUTHORING_SCHEMA:
            raise TemplateAuthoringError(
                f"schema_version must be {TEMPLATE_AUTHORING_SCHEMA!r}."
            )
        if not isinstance(self.artifact_category, str):
            raise TemplateAuthoringError("artifact_category must be a string.")
        if not isinstance(self.version, TemplateVersionAuthoring):
            raise TemplateAuthoringError(
                "version must be TemplateVersionAuthoring."
            )
        if self.definition is not None and not isinstance(
            self.definition,
            TemplateDefinitionAuthoring,
        ):
            raise TemplateAuthoringError(
                "definition must be TemplateDefinitionAuthoring or null."
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class PreparedSourceFile:
    path: Path
    sha256: str
    size: int
    mtime_ns: int
    device: int
    inode: int
    data: bytes


def prepare_source_file(
    path: str | Path,
    *,
    description: str,
) -> PreparedSourceFile:
    """Read one exact ordinary source file and capture its stable fingerprint."""
    source = Path(path)
    before = _safe_source_stat(source, description)
    try:
        data = source.read_bytes()
    except OSError as error:
        raise TemplateAuthoringError(
            f"could not read {description} {source}: {error}"
        ) from error
    after = _safe_source_stat(source, description)
    before_fingerprint = _fingerprint(before)
    after_fingerprint = _fingerprint(after)
    if before_fingerprint != after_fingerprint or len(data) != after.st_size:
        raise TemplateAuthoringConflictError(
            f"{description} changed while it was being read: {source}"
        )
    return PreparedSourceFile(
        path=source,
        sha256=hashlib.sha256(data).hexdigest(),
        size=after.st_size,
        mtime_ns=after.st_mtime_ns,
        device=after.st_dev,
        inode=after.st_ino,
        data=data,
    )


def verify_prepared_source(
    prepared: PreparedSourceFile,
    *,
    description: str,
) -> bytes:
    """Re-read a prepared source and require the exact reviewed fingerprint."""
    current = prepare_source_file(prepared.path, description=description)
    if (
        current.sha256 != prepared.sha256
        or current.size != prepared.size
        or current.mtime_ns != prepared.mtime_ns
        or current.device != prepared.device
        or current.inode != prepared.inode
    ):
        raise TemplateAuthoringConflictError(
            f"{description} changed after preparation: {prepared.path}"
        )
    return current.data


def load_template_authoring_source(
    path: str | Path,
) -> tuple[TemplateAuthoringDocument, PreparedSourceFile]:
    """Parse one strict authoring transport document."""
    prepared = prepare_source_file(path, description="Template authoring file")
    try:
        parsed = strict_json_loads(
            prepared.data,
            description="Template authoring file",
        )
        document = dataclass_from_dict(TemplateAuthoringDocument, parsed)
    except (TemplateSerializationError, ValueError) as error:
        raise TemplateAuthoringError(
            f"invalid Template authoring file {prepared.path}: {error}"
        ) from error
    return document, prepared


def _safe_source_stat(path: Path, description: str) -> os.stat_result:
    _require_no_link_like_ancestors(path, description)
    try:
        info = path.stat()
    except FileNotFoundError as error:
        raise TemplateAuthoringError(
            f"{description} does not exist: {path}"
        ) from error
    except OSError as error:
        raise TemplateAuthoringError(
            f"could not inspect {description} {path}: {error}"
        ) from error
    if not stat.S_ISREG(info.st_mode):
        raise TemplateAuthoringError(
            f"{description} must be an ordinary regular file: {path}"
        )
    return info


def _require_no_link_like_ancestors(path: Path, description: str) -> None:
    candidate = path.absolute()
    for item in (candidate, *candidate.parents):
        try:
            if item.is_symlink():
                raise TemplateAuthoringError(
                    f"{description} path traverses a symlink: {item}"
                )
            info = item.lstat()
        except FileNotFoundError:
            if item == candidate:
                continue
            raise TemplateAuthoringError(
                f"{description} parent path does not exist: {item}"
            )
        except OSError as error:
            raise TemplateAuthoringError(
                f"could not inspect {description} path {item}: {error}"
            ) from error
        attributes = getattr(info, "st_file_attributes", 0)
        reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        if reparse and attributes & reparse:
            raise TemplateAuthoringError(
                f"{description} path traverses a reparse point: {item}"
            )


def _fingerprint(info: os.stat_result) -> tuple[int, int, int, int, int]:
    return (
        info.st_dev,
        info.st_ino,
        info.st_size,
        info.st_mtime_ns,
        info.st_mode,
    )


__all__ = [
    "PreparedSourceFile",
    "TEMPLATE_AUTHORING_SCHEMA",
    "TemplateAuthoringConflictError",
    "TemplateAuthoringDocument",
    "TemplateAuthoringError",
    "TemplateDefinitionAuthoring",
    "TemplateVersionAuthoring",
    "load_template_authoring_source",
    "prepare_source_file",
    "verify_prepared_source",
]
