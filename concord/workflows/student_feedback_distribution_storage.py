
"""Staging and exact read-only verification for student feedback packages."""

from __future__ import annotations

import ctypes
import errno
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path, PurePath
from typing import Final

import pypdfium2 as pdfium

from concord.generated_paths import (
    ConcordGeneratedPathError,
    validate_human_readable_output_filename,
)
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowError,
    ConcordWorkflowValidationError,
)
from concord.workflows.student_feedback_distribution_package import (
    STUDENT_FEEDBACK_AUDIENCE_STAFF,
    STUDENT_FEEDBACK_AUDIENCE_STUDENT,
    STUDENT_FEEDBACK_INDEX_MEDIA_TYPE,
    STUDENT_FEEDBACK_MANIFEST_SCHEMA_VERSION,
    STUDENT_FEEDBACK_ORDERING_RULE,
    RenderedStudentFeedbackDistribution,
)
from concord.workflows.student_feedback_distribution_pdf import (
    STUDENT_FEEDBACK_PDF_MEDIA_TYPE,
)
from concord.workflows.student_feedback_distribution_plan import (
    FEEDBACK_INDEX_FILENAME,
    FEEDBACK_MANIFEST_FILENAME,
    FEEDBACK_PRINT_FILENAME,
    PreparedStudentFeedbackDistribution,
    verify_student_feedback_distribution_plan_digest,
)
from concord.workflows.student_feedback_distribution_rendering import (
    require_student_feedback_plan_current,
)

_SHA256_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[0-9a-f]{64}$")
_ENTRY_PATTERN: Final[re.Pattern[str]] = re.compile(r"^cfd_[0-9a-f]{24}$")
_TOP_LEVEL_KEYS: Final[frozenset[str]] = frozenset(
    {
        "schema_version",
        "created_at",
        "concord_version",
        "source",
        "selection_mode",
        "selected_count",
        "no_feedback_count",
        "unresolved_count",
        "ordering_rule",
        "reviewed_plan_digest",
        "entries",
        "combined_pdf",
        "feedback_index",
        "package_digest",
    }
)
_SOURCE_KEYS: Final[frozenset[str]] = frozenset(
    {
        "class_id",
        "activity_id",
        "activity_title",
        "snapshot_revision",
        "snapshot_sha256",
    }
)
_ENTRY_KEYS: Final[frozenset[str]] = frozenset(
    {
        "entry_identity",
        "student_display_name",
        "projection_sha256",
        "output_filename",
        "output_sha256",
        "page_count",
        "audience_scope",
    }
)
_COMBINED_KEYS: Final[frozenset[str]] = frozenset(
    {
        "filename",
        "media_type",
        "audience_scope",
        "sha256",
        "page_count",
    }
)
_INDEX_KEYS: Final[frozenset[str]] = frozenset(
    {
        "filename",
        "media_type",
        "audience_scope",
        "sha256",
    }
)


class StudentFeedbackDistributionStagingError(ConcordWorkflowError):
    """A staging write failed or could not be safely cleaned up."""

    def __init__(
        self,
        message: str,
        *,
        staging_directory: Path | None = None,
        cleanup_failed: bool = False,
    ) -> None:
        super().__init__(message)
        self.staging_directory = staging_directory
        self.cleanup_failed = cleanup_failed


@dataclass(frozen=True, slots=True, kw_only=True)
class VerifiedStudentFeedbackDistribution:
    """Exact read-only verification result for one bounded package directory."""

    directory: Path
    schema_version: str
    plan_digest: str
    package_digest: str
    selected_count: int
    managed_filenames: tuple[str, ...]
    combined_page_count: int


@dataclass(frozen=True, slots=True, kw_only=True)
class StagedStudentFeedbackDistribution:
    """Verified private staging directory ready for later final installation."""

    directory: Path
    verification: VerifiedStudentFeedbackDistribution


class _IndexParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []
        self.has_script = False
        self.resource_refs: list[str] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        lowered = tag.casefold()
        if lowered == "script":
            self.has_script = True
        for name, value in attrs:
            if value is None:
                continue
            key = name.casefold()
            if key == "href":
                self.hrefs.append(value)
            if key in {"href", "src"}:
                self.resource_refs.append(value)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json_bytes(payload: object) -> bytes:
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _require_exact_keys(
    payload: dict[str, object],
    expected: frozenset[str],
    label: str,
) -> None:
    if frozenset(payload) != expected:
        raise ConcordWorkflowValidationError(
            f"Student feedback {label} fields do not match the package contract."
        )


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ConcordWorkflowValidationError(
            f"Student feedback {label} must be nonempty text."
        )
    return value


def _require_nonnegative_int(value: object, label: str) -> int:
    if type(value) is not int or value < 0:
        raise ConcordWorkflowValidationError(
            f"Student feedback {label} must be a nonnegative integer."
        )
    return value


def _require_positive_int(value: object, label: str) -> int:
    if type(value) is not int or value < 1:
        raise ConcordWorkflowValidationError(
            f"Student feedback {label} must be a positive integer."
        )
    return value


def _require_sha256(value: object, label: str) -> str:
    text = _require_text(value, label)
    if _SHA256_PATTERN.fullmatch(text) is None:
        raise ConcordWorkflowValidationError(
            f"Student feedback {label} must be a SHA-256 digest."
        )
    return text


def _safe_component(value: object, label: str) -> str:
    text = _require_text(value, label)
    path = PurePath(text)
    if (
        path.name != text
        or text in {".", ".."}
        or "/" in text
        or "\\" in text
        or "\x00" in text
    ):
        raise ConcordWorkflowValidationError(
            f"Student feedback {label} must be one safe filename component."
        )
    return text


def _path_is_redirecting(path: Path) -> bool:
    try:
        if path.is_symlink():
            return True
        is_junction = getattr(path, "is_junction", None)
        return bool(is_junction is not None and is_junction())
    except OSError as error:
        raise ConcordWorkflowValidationError(
            f"Could not inspect student feedback filesystem path: {path}"
        ) from error


def _require_no_redirecting_ancestors(path: Path) -> None:
    for candidate in (path, *path.parents):
        if _path_is_redirecting(candidate):
            raise ConcordWorkflowValidationError(
                "Student feedback path traverses a redirecting filesystem path: "
                f"{candidate}"
            )


def _resolved_path(path: Path, *, label: str) -> Path:
    try:
        return path.resolve(strict=False)
    except (OSError, RuntimeError) as error:
        raise ConcordWorkflowValidationError(
            f"Could not resolve student feedback {label} path."
        ) from error


def _paths_overlap(first: Path, second: Path) -> bool:
    first_text = os.path.normcase(os.fspath(first))
    second_text = os.path.normcase(os.fspath(second))
    try:
        common = os.path.commonpath((first_text, second_text))
    except ValueError:
        return False
    return common in {first_text, second_text}


def _read_regular_file(path: Path) -> bytes:
    if path.is_symlink():
        raise ConcordWorkflowValidationError(
            f"Student feedback package contains a symlink: {path.name}"
        )
    try:
        if not path.is_file():
            raise ConcordWorkflowValidationError(
                f"Student feedback package object is not a regular file: {path.name}"
            )
        return path.read_bytes()
    except OSError as error:
        raise ConcordWorkflowValidationError(
            f"Could not read student feedback package file: {path.name}"
        ) from error


def _pdf_page_count(content: bytes, label: str) -> int:
    if not content.startswith(b"%PDF"):
        raise ConcordWorkflowValidationError(
            f"Student feedback {label} is not a PDF."
        )
    try:
        document = pdfium.PdfDocument(content)
        try:
            count = len(document)
        finally:
            document.close()
    except Exception as error:
        raise ConcordWorkflowValidationError(
            f"Student feedback {label} could not be opened as a PDF."
        ) from error
    if count < 1:
        raise ConcordWorkflowValidationError(
            f"Student feedback {label} contains no PDF pages."
        )
    return count


def _manifest_object(content: bytes) -> dict[str, object]:
    try:
        parsed = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ConcordWorkflowValidationError(
            "Student feedback distribution manifest is invalid JSON."
        ) from error
    if not isinstance(parsed, dict):
        raise ConcordWorkflowValidationError(
            "Student feedback distribution manifest must be a JSON object."
        )
    payload = dict(parsed)
    _require_exact_keys(payload, _TOP_LEVEL_KEYS, "manifest")
    return payload


def _verify_package_digest(manifest: dict[str, object]) -> str:
    package_digest = _require_sha256(
        manifest["package_digest"],
        "manifest package_digest",
    )
    payload = dict(manifest)
    del payload["package_digest"]
    expected = _sha256(_canonical_json_bytes(payload))
    if package_digest != expected:
        raise ConcordWorkflowValidationError(
            "Student feedback distribution package digest does not match."
        )
    return package_digest


def _entry_metadata(
    value: object,
) -> tuple[str, str, int]:
    if not isinstance(value, dict):
        raise ConcordWorkflowValidationError(
            "Student feedback manifest entry must be an object."
        )
    entry = dict(value)
    _require_exact_keys(entry, _ENTRY_KEYS, "manifest entry")

    identity = _require_text(entry["entry_identity"], "entry identity")
    if _ENTRY_PATTERN.fullmatch(identity) is None:
        raise ConcordWorkflowValidationError(
            "Student feedback manifest entry identity is invalid."
        )
    _require_text(entry["student_display_name"], "student display name")
    _require_sha256(entry["projection_sha256"], "projection digest")
    filename = _safe_component(entry["output_filename"], "student filename")
    try:
        validate_human_readable_output_filename(filename)
    except ConcordGeneratedPathError as error:
        raise ConcordWorkflowValidationError(
            "Student feedback manifest contains a noncontract student filename."
        ) from error
    _require_sha256(entry["output_sha256"], "student output digest")
    page_count = _require_positive_int(entry["page_count"], "student page count")
    if entry["audience_scope"] != STUDENT_FEEDBACK_AUDIENCE_STUDENT:
        raise ConcordWorkflowValidationError(
            "Student feedback manifest student audience scope is invalid."
        )
    return filename, str(entry["output_sha256"]), page_count


def _aggregate_metadata(
    value: object,
    *,
    expected_keys: frozenset[str],
    expected_filename: str,
    expected_media_type: str,
    require_page_count: bool,
) -> tuple[str, int | None]:
    if not isinstance(value, dict):
        raise ConcordWorkflowValidationError(
            "Student feedback aggregate manifest entry must be an object."
        )
    item = dict(value)
    _require_exact_keys(item, expected_keys, "aggregate manifest entry")
    if item["filename"] != expected_filename:
        raise ConcordWorkflowValidationError(
            "Student feedback aggregate filename is invalid."
        )
    if item["media_type"] != expected_media_type:
        raise ConcordWorkflowValidationError(
            "Student feedback aggregate media type is invalid."
        )
    if item["audience_scope"] != STUDENT_FEEDBACK_AUDIENCE_STAFF:
        raise ConcordWorkflowValidationError(
            "Student feedback aggregate audience scope is invalid."
        )
    digest = _require_sha256(item["sha256"], "aggregate output digest")
    if require_page_count:
        pages = _require_positive_int(item["page_count"], "combined page count")
    else:
        pages = None
    return digest, pages


def _verify_index(
    content: bytes,
    expected_student_filenames: tuple[str, ...],
) -> None:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ConcordWorkflowValidationError(
            "Student feedback index must be valid UTF-8."
        ) from error

    lowered = text.casefold()
    for forbidden in ("http://", "https://", "javascript:", "file://"):
        if forbidden in lowered:
            raise ConcordWorkflowValidationError(
                "Student feedback index contains a nonlocal dependency."
            )

    parser = _IndexParser()
    try:
        parser.feed(text)
        parser.close()
    except Exception as error:
        raise ConcordWorkflowValidationError(
            "Student feedback index could not be parsed safely."
        ) from error
    if parser.has_script:
        raise ConcordWorkflowValidationError(
            "Student feedback index must not require JavaScript."
        )
    if tuple(parser.hrefs) != expected_student_filenames:
        raise ConcordWorkflowValidationError(
            "Student feedback index links do not match the selected package order."
        )
    for reference in parser.resource_refs:
        if reference not in expected_student_filenames:
            raise ConcordWorkflowValidationError(
                "Student feedback index references an unmanaged resource."
            )


def verify_student_feedback_distribution_directory(
    directory: str | Path,
    *,
    expected_plan_digest: str | None = None,
    expected_package_digest: str | None = None,
) -> VerifiedStudentFeedbackDistribution:
    """Read-only exact verification for a staged or installed distribution."""
    root = Path(directory)
    if not root.is_absolute():
        raise ConcordWorkflowValidationError(
            "Student feedback distribution directory must be absolute."
        )
    if _path_is_redirecting(root) or not root.is_dir():
        raise ConcordWorkflowValidationError(
            "Student feedback distribution directory is not a safe directory."
        )

    manifest_path = root / FEEDBACK_MANIFEST_FILENAME
    manifest_content = _read_regular_file(manifest_path)
    manifest = _manifest_object(manifest_content)

    if manifest["schema_version"] != STUDENT_FEEDBACK_MANIFEST_SCHEMA_VERSION:
        raise ConcordWorkflowValidationError(
            "Student feedback distribution manifest schema is unsupported."
        )
    _require_text(manifest["created_at"], "manifest created_at")
    _require_text(manifest["concord_version"], "manifest Concord version")
    if manifest["ordering_rule"] != STUDENT_FEEDBACK_ORDERING_RULE:
        raise ConcordWorkflowValidationError(
            "Student feedback distribution ordering rule is unsupported."
        )

    source = manifest["source"]
    if not isinstance(source, dict):
        raise ConcordWorkflowValidationError(
            "Student feedback manifest source must be an object."
        )
    source_payload = dict(source)
    _require_exact_keys(source_payload, _SOURCE_KEYS, "manifest source")
    _require_text(source_payload["class_id"], "source class identity")
    _require_text(source_payload["activity_id"], "source Activity identity")
    _require_text(source_payload["activity_title"], "source Activity title")
    _require_positive_int(
        source_payload["snapshot_revision"],
        "source snapshot revision",
    )
    _require_sha256(
        source_payload["snapshot_sha256"],
        "source snapshot digest",
    )

    plan_digest = _require_sha256(
        manifest["reviewed_plan_digest"],
        "reviewed plan digest",
    )
    package_digest = _verify_package_digest(manifest)
    if expected_plan_digest is not None and plan_digest != expected_plan_digest:
        raise ConcordWorkflowValidationError(
            "Student feedback directory does not match the expected reviewed plan."
        )
    if (
        expected_package_digest is not None
        and package_digest != expected_package_digest
    ):
        raise ConcordWorkflowValidationError(
            "Student feedback directory does not match the expected package digest."
        )

    entries_value = manifest["entries"]
    if not isinstance(entries_value, list):
        raise ConcordWorkflowValidationError(
            "Student feedback manifest entries must be a list."
        )
    selected_count = _require_nonnegative_int(
        manifest["selected_count"],
        "selected count",
    )
    _require_nonnegative_int(manifest["no_feedback_count"], "no-feedback count")
    _require_nonnegative_int(manifest["unresolved_count"], "unresolved count")
    if selected_count != len(entries_value) or selected_count < 1:
        raise ConcordWorkflowValidationError(
            "Student feedback manifest selected count is inconsistent."
        )

    student_names: list[str] = []
    student_page_total = 0
    expected_digests: dict[str, str] = {}
    expected_pages: dict[str, int] = {}
    for entry in entries_value:
        filename, digest, pages = _entry_metadata(entry)
        student_names.append(filename)
        student_page_total += pages
        expected_digests[filename] = digest
        expected_pages[filename] = pages

    student_filenames = tuple(student_names)
    if len({name.casefold() for name in student_filenames}) != len(
        student_filenames
    ):
        raise ConcordWorkflowValidationError(
            "Student feedback manifest contains colliding student filenames."
        )

    combined_digest, combined_pages = _aggregate_metadata(
        manifest["combined_pdf"],
        expected_keys=_COMBINED_KEYS,
        expected_filename=FEEDBACK_PRINT_FILENAME,
        expected_media_type=STUDENT_FEEDBACK_PDF_MEDIA_TYPE,
        require_page_count=True,
    )
    if combined_pages != student_page_total:
        raise ConcordWorkflowValidationError(
            "Student feedback combined page count does not equal student pages."
        )
    index_digest, _ = _aggregate_metadata(
        manifest["feedback_index"],
        expected_keys=_INDEX_KEYS,
        expected_filename=FEEDBACK_INDEX_FILENAME,
        expected_media_type=STUDENT_FEEDBACK_INDEX_MEDIA_TYPE,
        require_page_count=False,
    )

    expected_digests[FEEDBACK_PRINT_FILENAME] = combined_digest
    expected_digests[FEEDBACK_INDEX_FILENAME] = index_digest
    expected_names = student_filenames + (
        FEEDBACK_PRINT_FILENAME,
        FEEDBACK_INDEX_FILENAME,
        FEEDBACK_MANIFEST_FILENAME,
    )
    if len({name.casefold() for name in expected_names}) != len(expected_names):
        raise ConcordWorkflowValidationError(
            "Student feedback package expected filenames collide."
        )

    try:
        actual_entries = tuple(root.iterdir())
    except OSError as error:
        raise ConcordWorkflowValidationError(
            "Could not enumerate student feedback distribution directory."
        ) from error
    actual_names = tuple(item.name for item in actual_entries)
    if len({name.casefold() for name in actual_names}) != len(actual_names):
        raise ConcordWorkflowValidationError(
            "Student feedback distribution contains case-colliding files."
        )
    if frozenset(actual_names) != frozenset(expected_names):
        raise ConcordWorkflowValidationError(
            "Student feedback distribution managed file set is not exact."
        )

    for filename in student_filenames:
        content = _read_regular_file(root / filename)
        if _sha256(content) != expected_digests[filename]:
            raise ConcordWorkflowValidationError(
                f"Student feedback file digest does not match: {filename}"
            )
        if _pdf_page_count(content, filename) != expected_pages[filename]:
            raise ConcordWorkflowValidationError(
                f"Student feedback PDF page count does not match: {filename}"
            )

    combined_content = _read_regular_file(root / FEEDBACK_PRINT_FILENAME)
    if _sha256(combined_content) != combined_digest:
        raise ConcordWorkflowValidationError(
            "Student feedback combined PDF digest does not match."
        )
    if _pdf_page_count(combined_content, FEEDBACK_PRINT_FILENAME) != combined_pages:
        raise ConcordWorkflowValidationError(
            "Student feedback combined PDF page count does not match."
        )

    index_content = _read_regular_file(root / FEEDBACK_INDEX_FILENAME)
    if _sha256(index_content) != index_digest:
        raise ConcordWorkflowValidationError(
            "Student feedback index digest does not match."
        )
    _verify_index(index_content, student_filenames)

    return VerifiedStudentFeedbackDistribution(
        directory=root,
        schema_version=STUDENT_FEEDBACK_MANIFEST_SCHEMA_VERSION,
        plan_digest=plan_digest,
        package_digest=package_digest,
        selected_count=selected_count,
        managed_filenames=expected_names,
        combined_page_count=combined_pages,
    )


def _validate_in_memory_package(
    plan: PreparedStudentFeedbackDistribution,
    package: RenderedStudentFeedbackDistribution,
) -> None:
    verify_student_feedback_distribution_plan_digest(plan)
    if package.schema_version != STUDENT_FEEDBACK_MANIFEST_SCHEMA_VERSION:
        raise ConcordWorkflowValidationError(
            "Rendered student feedback package schema is unsupported."
        )
    if package.plan_digest != plan.plan_digest:
        raise ConcordWorkflowValidationError(
            "Rendered student feedback package does not match the reviewed plan."
        )
    filenames = tuple(item.filename for item in package.files)
    if filenames != plan.output_filenames:
        raise ConcordWorkflowValidationError(
            "Rendered student feedback package output set is inconsistent."
        )
    for item in package.files:
        if _sha256(item.content) != item.sha256:
            raise ConcordWorkflowValidationError(
                "Rendered student feedback file digest is inconsistent: "
                f"{item.filename}"
            )


def _require_staging_parent(plan: PreparedStudentFeedbackDistribution) -> Path:
    parent = plan.destination.parent
    if not parent.is_absolute():
        raise ConcordWorkflowValidationError(
            "Student feedback destination parent must be absolute."
        )
    _require_no_redirecting_ancestors(parent)
    if not parent.is_dir():
        raise ConcordWorkflowValidationError(
            "Student feedback destination parent must be an existing safe directory."
        )
    return parent


def _require_distribution_destination_safe(
    plan: PreparedStudentFeedbackDistribution,
    *,
    workspace_root: str | Path,
) -> Path:
    parent = _require_staging_parent(plan)
    if plan.destination.exists() and (
        _path_is_redirecting(plan.destination) or not plan.destination.is_dir()
    ):
        raise ConcordWorkflowValidationError(
            "Student feedback destination exists but is not a safe directory."
        )
    destination = _resolved_path(
        plan.destination,
        label="destination",
    )
    workspace = _resolved_path(
        Path(workspace_root),
        label="workspace",
    )
    if _paths_overlap(destination, workspace):
        raise ConcordWorkflowValidationError(
            "Student feedback destination must not overlap the "
            "Paper Data Suite workspace."
        )
    return parent


def _write_staging_file(path: Path, content: bytes) -> None:
    try:
        with path.open("xb") as target:
            target.write(content)
            target.flush()
            os.fsync(target.fileno())
    except OSError as error:
        raise StudentFeedbackDistributionStagingError(
            f"Could not write staged student feedback file: {path.name}"
        ) from error


def _cleanup_staging(path: Path) -> bool:
    try:
        shutil.rmtree(path)
    except OSError:
        return False
    return True


def stage_student_feedback_distribution(
    plan: PreparedStudentFeedbackDistribution,
    package: RenderedStudentFeedbackDistribution,
    *,
    workspace_root: str | Path,
) -> StagedStudentFeedbackDistribution:
    """Write and verify a private sibling staging package, never the final path."""
    _validate_in_memory_package(plan, package)
    parent = _require_distribution_destination_safe(
        plan,
        workspace_root=workspace_root,
    )

    # This is deliberately the final source-state read before durable output mutation.
    require_student_feedback_plan_current(
        plan,
        workspace_root=workspace_root,
    )

    staging: Path | None = None
    try:
        staging = Path(
            tempfile.mkdtemp(
                prefix=".concord-feedback-staging-",
                dir=parent,
            )
        )
        for item in package.files:
            _write_staging_file(staging / item.filename, item.content)

        verification = verify_student_feedback_distribution_directory(
            staging,
            expected_plan_digest=plan.plan_digest,
            expected_package_digest=package.package_digest,
        )
        return StagedStudentFeedbackDistribution(
            directory=staging,
            verification=verification,
        )
    except Exception as error:
        if staging is None:
            raise
        cleaned = _cleanup_staging(staging)
        if not cleaned:
            raise StudentFeedbackDistributionStagingError(
                "Student feedback staging failed and staging cleanup also failed.",
                staging_directory=staging,
                cleanup_failed=True,
            ) from error
        if isinstance(error, StudentFeedbackDistributionStagingError):
            raise
        raise StudentFeedbackDistributionStagingError(
            "Student feedback staging failed before final installation."
        ) from error



STUDENT_FEEDBACK_INSTALL_ACTION_INSTALLED: Final[str] = "installed"
STUDENT_FEEDBACK_INSTALL_ACTION_REUSED: Final[str] = "reused"


class StudentFeedbackDistributionInstallError(ConcordWorkflowError):
    """Final installation failed or completed only partially."""

    def __init__(
        self,
        message: str,
        *,
        destination: Path,
        staging_directory: Path | None = None,
        destination_durable: bool = False,
        cleanup_failed: bool = False,
    ) -> None:
        super().__init__(message)
        self.destination = destination
        self.staging_directory = staging_directory
        self.destination_durable = destination_durable
        self.cleanup_failed = cleanup_failed


@dataclass(frozen=True, slots=True, kw_only=True)
class InstalledStudentFeedbackDistribution:
    """Verified final distribution, newly installed or safely reused."""

    directory: Path
    action: str
    verification: VerifiedStudentFeedbackDistribution


def _fsync_directory_if_supported(path: Path) -> None:
    if os.name == "nt":
        return
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _require_stage_matches_plan(
    plan: PreparedStudentFeedbackDistribution,
    staged: StagedStudentFeedbackDistribution,
) -> VerifiedStudentFeedbackDistribution:
    verify_student_feedback_distribution_plan_digest(plan)
    if staged.directory == plan.destination:
        raise ConcordWorkflowValidationError(
            "Student feedback staging directory must differ from final destination."
        )
    if staged.directory.parent != plan.destination.parent:
        raise ConcordWorkflowValidationError(
            "Student feedback staging directory must be a destination sibling."
        )
    if not staged.directory.name.startswith(".concord-feedback-staging-"):
        raise ConcordWorkflowValidationError(
            "Student feedback staging directory is not a recognized private stage."
        )

    verified = verify_student_feedback_distribution_directory(
        staged.directory,
        expected_plan_digest=plan.plan_digest,
        expected_package_digest=staged.verification.package_digest,
    )
    if verified != staged.verification:
        raise ConcordWorkflowValidationError(
            "Student feedback staging verification changed before installation."
        )
    if verified.managed_filenames != plan.output_filenames:
        raise ConcordWorkflowValidationError(
            "Student feedback staging output set differs from the reviewed plan."
        )
    return verified


def _cleanup_stage_or_raise(
    staging: Path,
    *,
    destination: Path,
    message: str,
    cause: Exception,
    destination_durable: bool,
) -> None:
    if _cleanup_staging(staging):
        return
    raise StudentFeedbackDistributionInstallError(
        message,
        destination=destination,
        staging_directory=staging,
        destination_durable=destination_durable,
        cleanup_failed=True,
    ) from cause


def _existing_destination_verification(
    plan: PreparedStudentFeedbackDistribution,
    staged: StagedStudentFeedbackDistribution,
) -> VerifiedStudentFeedbackDistribution:
    try:
        existing = verify_student_feedback_distribution_directory(
            plan.destination,
            expected_plan_digest=plan.plan_digest,
        )
        if existing.managed_filenames != plan.output_filenames:
            raise ConcordWorkflowValidationError(
                "Existing student feedback output set differs from the "
                "reviewed plan."
            )
        return existing
    except ConcordWorkflowValidationError as error:
        _cleanup_stage_or_raise(
            staged.directory,
            destination=plan.destination,
            message=(
                "Student feedback destination conflicts and staging cleanup failed."
            ),
            cause=error,
            destination_durable=True,
        )
        raise ConcordWorkflowConflictError(
            "Student feedback destination already exists with different "
            "or unverifiable content."
        ) from error


def reuse_existing_student_feedback_distribution(
    plan: PreparedStudentFeedbackDistribution,
    *,
    workspace_root: str | Path,
) -> InstalledStudentFeedbackDistribution | None:
    """Reuse one exact self-verified package without consulting current source state."""
    verify_student_feedback_distribution_plan_digest(plan)
    _require_distribution_destination_safe(
        plan,
        workspace_root=workspace_root,
    )
    destination = plan.destination
    if not destination.exists():
        return None

    try:
        verified = verify_student_feedback_distribution_directory(
            destination,
            expected_plan_digest=plan.plan_digest,
        )
        if verified.managed_filenames != plan.output_filenames:
            raise ConcordWorkflowValidationError(
                "Existing student feedback output set differs from the "
                "reviewed plan."
            )
    except ConcordWorkflowValidationError as error:
        raise ConcordWorkflowConflictError(
            "Student feedback destination already exists with different "
            "or unverifiable content."
        ) from error

    return InstalledStudentFeedbackDistribution(
        directory=destination,
        action=STUDENT_FEEDBACK_INSTALL_ACTION_REUSED,
        verification=verified,
    )


_AT_FDCWD: Final[int] = -100
_RENAME_NOREPLACE: Final[int] = 1
_RENAME_EXCL: Final[int] = 0x00000004


def _raise_rename_error(error_number: int, destination: Path) -> None:
    raise OSError(
        error_number,
        os.strerror(error_number),
        os.fspath(destination),
    )


def _linux_rename_noreplace(staging: Path, destination: Path) -> None:
    library = ctypes.CDLL(None, use_errno=True)
    renameat2 = getattr(library, "renameat2", None)
    if renameat2 is None:
        raise OSError(
            errno.ENOTSUP,
            "atomic no-replace rename is unavailable on this Linux runtime",
        )

    ctypes.set_errno(0)
    result = renameat2(
        _AT_FDCWD,
        os.fsencode(staging),
        _AT_FDCWD,
        os.fsencode(destination),
        _RENAME_NOREPLACE,
    )
    if result != 0:
        _raise_rename_error(ctypes.get_errno(), destination)


def _darwin_rename_noreplace(staging: Path, destination: Path) -> None:
    library = ctypes.CDLL(None, use_errno=True)
    renamex_np = getattr(library, "renamex_np", None)
    if renamex_np is None:
        raise OSError(
            errno.ENOTSUP,
            "atomic no-replace rename is unavailable on this Darwin runtime",
        )

    ctypes.set_errno(0)
    result = renamex_np(
        os.fsencode(staging),
        os.fsencode(destination),
        _RENAME_EXCL,
    )
    if result != 0:
        _raise_rename_error(ctypes.get_errno(), destination)


def _promote_staging_directory(staging: Path, destination: Path) -> None:
    """Atomically install one verified stage without replacing any destination."""
    if os.name == "nt":
        os.rename(staging, destination)
        return
    if sys.platform.startswith("linux"):
        _linux_rename_noreplace(staging, destination)
        return
    if sys.platform == "darwin":
        _darwin_rename_noreplace(staging, destination)
        return
    raise OSError(
        errno.ENOTSUP,
        "atomic no-replace rename is unavailable on this platform",
    )


def install_staged_student_feedback_distribution(
    plan: PreparedStudentFeedbackDistribution,
    staged: StagedStudentFeedbackDistribution,
) -> InstalledStudentFeedbackDistribution:
    """Install a verified stage once, or reuse an exact existing package."""
    verified_stage = _require_stage_matches_plan(plan, staged)
    destination = plan.destination
    parent = _require_staging_parent(plan)

    if destination.exists() or destination.is_symlink():
        existing = _existing_destination_verification(plan, staged)
        try:
            cleaned = _cleanup_staging(staged.directory)
        except Exception as error:
            raise StudentFeedbackDistributionInstallError(
                "Exact destination was reusable but staging cleanup failed.",
                destination=destination,
                staging_directory=staged.directory,
                destination_durable=True,
                cleanup_failed=True,
            ) from error
        if not cleaned:
            raise StudentFeedbackDistributionInstallError(
                "Exact destination was reusable but staging cleanup failed.",
                destination=destination,
                staging_directory=staged.directory,
                destination_durable=True,
                cleanup_failed=True,
            )
        return InstalledStudentFeedbackDistribution(
            directory=destination,
            action=STUDENT_FEEDBACK_INSTALL_ACTION_REUSED,
            verification=existing,
        )

    try:
        _fsync_directory_if_supported(staged.directory)
        _promote_staging_directory(staged.directory, destination)
        _fsync_directory_if_supported(parent)
    except FileExistsError as error:
        if destination.exists() or destination.is_symlink():
            existing = _existing_destination_verification(plan, staged)
            if not _cleanup_staging(staged.directory):
                raise StudentFeedbackDistributionInstallError(
                    "Exact destination was reusable but staging cleanup failed.",
                    destination=destination,
                    staging_directory=staged.directory,
                    destination_durable=True,
                    cleanup_failed=True,
                ) from error
            return InstalledStudentFeedbackDistribution(
                directory=destination,
                action=STUDENT_FEEDBACK_INSTALL_ACTION_REUSED,
                verification=existing,
            )
        _cleanup_stage_or_raise(
            staged.directory,
            destination=destination,
            message="Student feedback installation failed and cleanup failed.",
            cause=error,
            destination_durable=False,
        )
        raise StudentFeedbackDistributionInstallError(
            "Student feedback staging directory could not be promoted.",
            destination=destination,
            staging_directory=None,
            destination_durable=False,
        ) from error
    except OSError as error:
        staging_still_exists = staged.directory.exists()
        if staging_still_exists:
            _cleanup_stage_or_raise(
                staged.directory,
                destination=destination,
                message="Student feedback installation failed and cleanup failed.",
                cause=error,
                destination_durable=False,
            )
        raise StudentFeedbackDistributionInstallError(
            "Student feedback staging directory could not be promoted.",
            destination=destination,
            staging_directory=None,
            destination_durable=destination.exists(),
        ) from error

    try:
        final_verification = verify_student_feedback_distribution_directory(
            destination,
            expected_plan_digest=plan.plan_digest,
            expected_package_digest=verified_stage.package_digest,
        )
    except Exception as error:
        raise StudentFeedbackDistributionInstallError(
            "Student feedback destination became durable but final "
            "verification failed.",
            destination=destination,
            staging_directory=None,
            destination_durable=True,
        ) from error

    return InstalledStudentFeedbackDistribution(
        directory=destination,
        action=STUDENT_FEEDBACK_INSTALL_ACTION_INSTALLED,
        verification=final_verification,
    )


__all__ = [
    "STUDENT_FEEDBACK_INSTALL_ACTION_INSTALLED",
    "STUDENT_FEEDBACK_INSTALL_ACTION_REUSED",
    "InstalledStudentFeedbackDistribution",
    "StagedStudentFeedbackDistribution",
    "StudentFeedbackDistributionInstallError",
    "StudentFeedbackDistributionStagingError",
    "VerifiedStudentFeedbackDistribution",
    "install_staged_student_feedback_distribution",
    "reuse_existing_student_feedback_distribution",
    "stage_student_feedback_distribution",
    "verify_student_feedback_distribution_directory",
]
