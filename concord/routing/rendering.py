"""Canonical-state rendering of minimal PDS2 Artifact Pages."""

from __future__ import annotations

import io
import os
import tempfile
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import cast

from pds_core.pds2 import serialize_pds2_payload
from pds_core.route_registrations import load_route_registration
from pds_core.routes import safe_module_work_descendant
from pds_core.routing_models import ModuleWorkRef

from concord.model_validation import ConcordRecordGraph
from concord.models import ArtifactPage
from concord.storage import commit_record_batch, load_current_record_graph
from concord.workflows.artifact_page import (
    _registration,
    _standards,
    validate_concord_route_registration,
)
from concord.workflows.context import ensure_mutating_workspace_root, require_core_class
from concord.workflows.errors import ConcordWorkflowNotFoundError
from concord.workflows.models import WorkflowActor, WorkflowCommitResult


@dataclass(frozen=True, slots=True, kw_only=True)
class RenderArtifactPagesRequest:
    class_id: str
    activity_id: str
    artifact_instance_id: str
    expected_snapshot_revision: int
    actor: WorkflowActor
    output_relative_path: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class RenderArtifactPagesResult:
    work: ModuleWorkRef
    artifact_instance_id: str
    output_path: Path
    page_count: int
    payloads: tuple[str, ...]
    commit: WorkflowCommitResult
    output_installed: bool


class RenderPartialSuccessError(RuntimeError):
    def __init__(self, output_path: Path, cause: Exception) -> None:
        super().__init__(
            "Rendered output is durable, but lifecycle state was not updated."
        )
        self.output_path = output_path
        self.__cause__ = cause


def _pdf_bytes(activity_id: str, pages: tuple[tuple[ArtifactPage, str], ...]) -> bytes:
    try:
        import qrcode
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as error:  # pragma: no cover - dependency installation guard
        raise RuntimeError("Pillow and qrcode are required for rendering.") from error
    sheets = []
    for page, payload in pages:
        sheet = Image.new("RGB", (1275, 1650), "white")
        draw = ImageDraw.Draw(sheet)
        font = ImageFont.load_default(size=28)
        small = ImageFont.load_default(size=20)
        draw.text((90, 90), "Concord Artifact Page", fill="black", font=font)
        draw.text((90, 145), f"Activity: {activity_id}", fill="black", font=small)
        draw.text(
            (90, 185), f"Physical page: {page.page_number}", fill="black", font=small
        )
        qr = qrcode.make(payload).convert("RGB").resize((430, 430))
        sheet.paste(qr, (755, 80))
        draw.text(
            (90, 1510), page.human_fallback or "Concord page", fill="black", font=small
        )
        draw.text((90, 1550), f"Route: {page.route_id}", fill="black", font=small)
        sheets.append(sheet)
    output = io.BytesIO()
    canonical_time = datetime.fromisoformat(
        pages[0][0].created_provenance.timestamp
    ).astimezone(timezone.utc).timetuple()
    sheets[0].save(
        output,
        "PDF",
        save_all=True,
        append_images=sheets[1:],
        resolution=150.0,
        creationDate=canonical_time,
        modDate=canonical_time,
    )
    return output.getvalue()


def _safe_install(target: Path, data: bytes) -> bool:
    for ancestor in (target, *target.parents):
        if ancestor.is_symlink():
            raise RuntimeError(f"render path traverses a symlink: {ancestor}")
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if not target.is_file() or target.read_bytes() != data:
            raise FileExistsError(
                f"different completed render already exists: {target}"
            )
        return False
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", delete=False, dir=target.parent, prefix=".render.", suffix=".tmp"
        ) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if target.exists():
            raise FileExistsError(f"render appeared concurrently: {target}")
        os.replace(temporary, target)
        temporary = None
        return True
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _render_target(root: Path, work: ModuleWorkRef, relative: str) -> Path:
    """Resolve final output while reserving every render beneath rendered/."""
    windows = PureWindowsPath(relative)
    posix = PurePosixPath(relative)
    parts = relative.replace("\\", "/").split("/")
    if (
        not relative
        or windows.is_absolute()
        or windows.drive
        or windows.root
        or posix.is_absolute()
        or "" in parts
        or "." in parts
        or ".." in parts
        or parts[0] != "rendered"
    ):
        raise ValueError("render output must be a safe path beneath rendered/.")
    rendered_root = safe_module_work_descendant(root, work, "rendered")
    target = safe_module_work_descendant(root, work, relative)
    try:
        target.resolve(strict=False).relative_to(rendered_root.resolve(strict=False))
    except (OSError, RuntimeError, ValueError) as error:
        raise ValueError("render output must remain beneath rendered/.") from error
    return target


def render_artifact_pages(
    request: RenderArtifactPagesRequest,
    *,
    workspace_root: str | Path | None = None,
) -> RenderArtifactPagesResult:
    root = ensure_mutating_workspace_root(workspace_root).root
    require_core_class(root, request.class_id)
    work = ModuleWorkRef("concord", request.class_id, request.activity_id)
    library = _standards(root)
    loaded = load_current_record_graph(root, work, standards_library=library)
    if loaded.snapshot_revision != request.expected_snapshot_revision:
        from concord.storage_errors import ConcordStorageConflictError

        raise ConcordStorageConflictError(
            f"expected snapshot {request.expected_snapshot_revision}, "
            f"found {loaded.snapshot_revision}."
        )
    graph = cast(ConcordRecordGraph, loaded.graph)
    artifact = next(
        (
            item
            for item in graph.artifact_instances
            if item.artifact_instance_id == request.artifact_instance_id
        ),
        None,
    )
    if artifact is None:
        raise ConcordWorkflowNotFoundError(
            f"Artifact Instance is unavailable: {request.artifact_instance_id}"
        )
    canonical_pages = tuple(
        sorted(
            (
                item
                for item in graph.artifact_pages
                if item.artifact_instance_id == artifact.artifact_instance_id
            ),
            key=lambda item: item.page_number,
        )
    )
    verified: list[tuple[ArtifactPage, str]] = []
    for page in canonical_pages:
        if not page.route_required:
            continue
        expected = _registration(work, page)
        actual = load_route_registration(root, expected.locator)
        validate_concord_route_registration(actual)
        if actual != expected:
            raise RuntimeError(
                f"route does not match canonical page: {page.artifact_page_id}"
            )
        verified.append((page, serialize_pds2_payload(actual.locator)))
    if not verified:
        raise ValueError("Artifact Instance has no route-bearing pages.")
    relative = (
        request.output_relative_path or f"rendered/{artifact.artifact_instance_id}.pdf"
    )
    target = _render_target(root, work, relative)
    data = _pdf_bytes(request.activity_id, tuple(verified))
    installed = _safe_install(target, data)
    rendered_page_ids = {page.artifact_page_id for page, _ in verified}
    revised_pages = tuple(
        replace(page, page_status="generated")
        if page.artifact_page_id in rendered_page_ids and page.page_status == "planned"
        else page
        for page in canonical_pages
    )
    all_pages_rendered = len(rendered_page_ids) == len(canonical_pages)
    revised_artifact = (
        replace(
            artifact,
            generation_status="completed",
            artifact_status="generated"
            if artifact.artifact_status == "planned"
            else artifact.artifact_status,
        )
        if all_pages_rendered
        else artifact
    )
    try:
        commit = commit_record_batch(
            root,
            work,
            (revised_artifact, *revised_pages),
            expected_snapshot_revision=loaded.snapshot_revision,
            standards_library=library,
        )
    except Exception as error:
        raise RenderPartialSuccessError(target, error) from error
    return RenderArtifactPagesResult(
        work=work,
        artifact_instance_id=artifact.artifact_instance_id,
        output_path=target,
        page_count=len(verified),
        payloads=tuple(payload for _, payload in verified),
        commit=WorkflowCommitResult.from_storage(commit),
        output_installed=installed,
    )


__all__ = [
    "RenderArtifactPagesRequest",
    "RenderArtifactPagesResult",
    "RenderPartialSuccessError",
    "render_artifact_pages",
]
