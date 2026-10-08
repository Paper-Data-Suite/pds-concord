
"""In-memory aggregate artifacts for a reviewed student feedback distribution."""

from __future__ import annotations

import hashlib
import html
import io
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Final

import pypdfium2 as pdfium

from concord._version import __version__ as CONCORD_VERSION
from concord.workflows.errors import ConcordWorkflowValidationError
from concord.workflows.student_feedback import StudentFeedbackProjection
from concord.workflows.student_feedback_distribution_pdf import (
    STUDENT_FEEDBACK_PDF_MEDIA_TYPE,
    render_student_feedback_pdf,
)
from concord.workflows.student_feedback_distribution_plan import (
    FEEDBACK_INDEX_FILENAME,
    FEEDBACK_MANIFEST_FILENAME,
    FEEDBACK_PRINT_FILENAME,
    PreparedStudentFeedbackDistribution,
    verify_student_feedback_distribution_plan_digest,
)
from concord.workflows.student_feedback_distribution_rendering import (
    student_feedback_render_inputs_from_plan,
)

STUDENT_FEEDBACK_MANIFEST_SCHEMA_VERSION: Final[str] = (
    "concord_feedback_distribution_v1"
)
STUDENT_FEEDBACK_INDEX_MEDIA_TYPE: Final[str] = "text/html; charset=utf-8"
STUDENT_FEEDBACK_MANIFEST_MEDIA_TYPE: Final[str] = "application/json"
STUDENT_FEEDBACK_AUDIENCE_STUDENT: Final[str] = "student_scoped"
STUDENT_FEEDBACK_AUDIENCE_STAFF: Final[str] = "authorized_staff"
STUDENT_FEEDBACK_ORDERING_RULE: Final[str] = "current_core_roster_order"
_DISTRIBUTION_ENTRY_PREFIX: Final[str] = "cfd_"


@dataclass(frozen=True, slots=True, kw_only=True)
class RenderedStudentFeedbackDistributionFile:
    """One exact in-memory managed file for the bounded distribution package."""

    filename: str
    media_type: str
    audience_scope: str
    content: bytes
    sha256: str
    page_count: int | None


@dataclass(frozen=True, slots=True, kw_only=True)
class RenderedStudentFeedbackDistribution:
    """Complete in-memory package payload before any filesystem installation."""

    schema_version: str
    plan_digest: str
    package_digest: str
    files: tuple[RenderedStudentFeedbackDistributionFile, ...]


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


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_created_at(created_at: str) -> str:
    if not isinstance(created_at, str) or not created_at:
        raise ConcordWorkflowValidationError(
            "Student feedback package created_at must be an ISO datetime."
        )
    try:
        value = datetime.fromisoformat(created_at)
    except ValueError as error:
        raise ConcordWorkflowValidationError(
            "Student feedback package created_at must be an ISO datetime."
        ) from error
    if value.tzinfo is None or value.utcoffset() is None:
        raise ConcordWorkflowValidationError(
            "Student feedback package created_at requires an explicit UTC offset."
        )
    return value.astimezone(timezone.utc).isoformat()


def _projection_payload(
    projection: StudentFeedbackProjection,
) -> dict[str, object]:
    return {
        "student_display_name": projection.student_display_name,
        "activity_title": projection.activity_title,
        "class_label": projection.class_label,
        "boundary_statement": projection.boundary_statement,
        "results": [
            {
                "criterion_label": item.criterion_label,
                "scoring_scale_name": item.scoring_scale_name,
                "disposition": item.disposition,
                "value": item.value,
                "value_label": item.value_label,
            }
            for item in projection.results
        ],
    }


def student_feedback_projection_sha256(
    projection: StudentFeedbackProjection,
) -> str:
    """Digest the exact share-safe semantics represented to one student."""
    if not isinstance(projection, StudentFeedbackProjection):
        raise ConcordWorkflowValidationError(
            "Student feedback projection digest requires a feedback projection."
        )
    return _sha256(_canonical_json_bytes(_projection_payload(projection)))


def _entry_identity(filename: str, projection_sha256: str) -> str:
    payload = _canonical_json_bytes(
        {
            "filename": filename,
            "projection_sha256": projection_sha256,
        }
    )
    return _DISTRIBUTION_ENTRY_PREFIX + _sha256(payload)[:24]


def _managed_file(
    *,
    filename: str,
    media_type: str,
    audience_scope: str,
    content: bytes,
    page_count: int | None = None,
) -> RenderedStudentFeedbackDistributionFile:
    if not content:
        raise ConcordWorkflowValidationError(
            f"Student feedback package file is empty: {filename}"
        )
    return RenderedStudentFeedbackDistributionFile(
        filename=filename,
        media_type=media_type,
        audience_scope=audience_scope,
        content=content,
        sha256=_sha256(content),
        page_count=page_count,
    )


def _merge_student_pdfs(
    files: tuple[RenderedStudentFeedbackDistributionFile, ...],
) -> tuple[bytes, int]:
    if not files:
        raise ConcordWorkflowValidationError(
            "Combined student feedback PDF requires at least one student PDF."
        )

    combined = pdfium.PdfDocument.new()
    expected_pages = 0
    try:
        for item in files:
            if item.media_type != STUDENT_FEEDBACK_PDF_MEDIA_TYPE:
                raise ConcordWorkflowValidationError(
                    "Combined feedback received a non-PDF student artifact."
                )
            source = pdfium.PdfDocument(item.content)
            try:
                source_pages = len(source)
                if item.page_count != source_pages:
                    raise ConcordWorkflowValidationError(
                        "Student feedback PDF page count is inconsistent."
                    )
                combined.import_pages(source)
                expected_pages += source_pages
            finally:
                source.close()

        if len(combined) != expected_pages:
            raise ConcordWorkflowValidationError(
                "Combined feedback PDF page count is inconsistent."
            )
        stream = io.BytesIO()
        combined.save(stream)
        content = stream.getvalue()
    except ConcordWorkflowValidationError:
        raise
    except Exception as error:
        raise ConcordWorkflowValidationError(
            f"Could not combine student feedback PDFs: {error}"
        ) from error
    finally:
        combined.close()

    if not content.startswith(b"%PDF"):
        raise ConcordWorkflowValidationError(
            "Combined student feedback renderer did not produce PDF bytes."
        )
    return content, expected_pages


def _index_bytes(
    plan: PreparedStudentFeedbackDistribution,
    student_files: tuple[RenderedStudentFeedbackDistributionFile, ...],
) -> bytes:
    rows = []
    for planned, rendered in zip(plan.students, student_files, strict=True):
        if planned.filename != rendered.filename:
            raise ConcordWorkflowValidationError(
                "Student feedback index order disagrees with the reviewed plan."
            )
        name = html.escape(planned.student_display_name)
        href = html.escape(rendered.filename, quote=True)
        rows.append(
            f'<li><span>{name}</span> '
            f'<a href="{href}">Open feedback</a></li>'
        )

    title = html.escape(f"{plan.activity_title} Feedback")
    body = "\n".join(rows)
    document = (
        "<!doctype html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        f"<title>{title}</title>\n"
        "</head>\n"
        "<body>\n"
        f"<h1>{title}</h1>\n"
        f"<p>{len(student_files)} feedback files</p>\n"
        "<p>Authorized teacher/support-staff class-set index.</p>\n"
        "<ul>\n"
        f"{body}\n"
        "</ul>\n"
        "</body>\n"
        "</html>\n"
    )
    return document.encode("utf-8")


def _file_manifest_payload(
    item: RenderedStudentFeedbackDistributionFile,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "filename": item.filename,
        "media_type": item.media_type,
        "audience_scope": item.audience_scope,
        "sha256": item.sha256,
    }
    if item.page_count is not None:
        payload["page_count"] = item.page_count
    return payload


def _package_digest(
    payload: dict[str, object],
) -> str:
    return _sha256(_canonical_json_bytes(payload))


def render_student_feedback_distribution_package(
    plan: PreparedStudentFeedbackDistribution,
    *,
    created_at: str,
) -> RenderedStudentFeedbackDistribution:
    """Render a complete bounded distribution entirely in memory."""
    verify_student_feedback_distribution_plan_digest(plan)
    canonical_created_at = _canonical_created_at(created_at)
    prepared = student_feedback_render_inputs_from_plan(plan)

    student_files: list[RenderedStudentFeedbackDistributionFile] = []
    entries: list[dict[str, object]] = []
    for planned, render_input in zip(
        plan.students,
        prepared.students,
        strict=True,
    ):
        if planned.filename != render_input.filename:
            raise ConcordWorkflowValidationError(
                "Student feedback rendering order disagrees with the reviewed plan."
            )
        projection_sha256 = student_feedback_projection_sha256(
            render_input.projection
        )
        rendered = render_student_feedback_pdf(render_input)
        managed = _managed_file(
            filename=rendered.filename,
            media_type=rendered.media_type,
            audience_scope=STUDENT_FEEDBACK_AUDIENCE_STUDENT,
            content=rendered.content,
            page_count=rendered.page_count,
        )
        student_files.append(managed)
        entries.append(
            {
                "entry_identity": _entry_identity(
                    managed.filename,
                    projection_sha256,
                ),
                "student_display_name": planned.student_display_name,
                "projection_sha256": projection_sha256,
                "output_filename": managed.filename,
                "output_sha256": managed.sha256,
                "page_count": managed.page_count,
                "audience_scope": managed.audience_scope,
            }
        )

    students = tuple(student_files)
    combined_content, combined_pages = _merge_student_pdfs(students)
    combined = _managed_file(
        filename=FEEDBACK_PRINT_FILENAME,
        media_type=STUDENT_FEEDBACK_PDF_MEDIA_TYPE,
        audience_scope=STUDENT_FEEDBACK_AUDIENCE_STAFF,
        content=combined_content,
        page_count=combined_pages,
    )
    index = _managed_file(
        filename=FEEDBACK_INDEX_FILENAME,
        media_type=STUDENT_FEEDBACK_INDEX_MEDIA_TYPE,
        audience_scope=STUDENT_FEEDBACK_AUDIENCE_STAFF,
        content=_index_bytes(plan, students),
    )

    digest_payload: dict[str, object] = {
        "schema_version": STUDENT_FEEDBACK_MANIFEST_SCHEMA_VERSION,
        "created_at": canonical_created_at,
        "concord_version": CONCORD_VERSION,
        "source": {
            "class_id": plan.class_id,
            "activity_id": plan.activity_id,
            "activity_title": plan.activity_title,
            "snapshot_revision": plan.expected_snapshot_revision,
            "snapshot_sha256": plan.expected_snapshot_sha256,
        },
        "selection_mode": plan.selection_mode,
        "selected_count": len(students),
        "no_feedback_count": len(plan.no_feedback_student_ids),
        "unresolved_count": len(plan.unresolved_student_ids),
        "ordering_rule": STUDENT_FEEDBACK_ORDERING_RULE,
        "reviewed_plan_digest": plan.plan_digest,
        "entries": entries,
        "combined_pdf": _file_manifest_payload(combined),
        "feedback_index": _file_manifest_payload(index),
    }
    package_digest = _package_digest(digest_payload)
    manifest_payload = dict(digest_payload)
    manifest_payload["package_digest"] = package_digest
    manifest = _managed_file(
        filename=FEEDBACK_MANIFEST_FILENAME,
        media_type=STUDENT_FEEDBACK_MANIFEST_MEDIA_TYPE,
        audience_scope=STUDENT_FEEDBACK_AUDIENCE_STAFF,
        content=_canonical_json_bytes(manifest_payload),
    )

    files = students + (combined, index, manifest)
    filenames = tuple(item.filename for item in files)
    if filenames != plan.output_filenames:
        raise ConcordWorkflowValidationError(
            "Rendered feedback package does not match the reviewed output set."
        )
    if len({name.casefold() for name in filenames}) != len(filenames):
        raise ConcordWorkflowValidationError(
            "Rendered feedback package contains colliding filenames."
        )

    return RenderedStudentFeedbackDistribution(
        schema_version=STUDENT_FEEDBACK_MANIFEST_SCHEMA_VERSION,
        plan_digest=plan.plan_digest,
        package_digest=package_digest,
        files=files,
    )


__all__ = [
    "STUDENT_FEEDBACK_AUDIENCE_STAFF",
    "STUDENT_FEEDBACK_AUDIENCE_STUDENT",
    "STUDENT_FEEDBACK_INDEX_MEDIA_TYPE",
    "STUDENT_FEEDBACK_MANIFEST_MEDIA_TYPE",
    "STUDENT_FEEDBACK_MANIFEST_SCHEMA_VERSION",
    "STUDENT_FEEDBACK_ORDERING_RULE",
    "RenderedStudentFeedbackDistribution",
    "RenderedStudentFeedbackDistributionFile",
    "render_student_feedback_distribution_package",
    "student_feedback_projection_sha256",
]
