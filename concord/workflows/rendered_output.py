"""Read-only verification of existing rendered Packet PDF outputs."""

from __future__ import annotations

import hashlib
import stat
from dataclasses import dataclass
from pathlib import Path

from pds_core.routes import module_work_dir, safe_module_work_descendant
from pds_core.routing_models import ModuleWorkRef

from concord.workflows.context import resolve_read_workspace_root
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowNotFoundError,
    ConcordWorkflowValidationError,
)
from concord.workflows.packet_instance import show_packet_instance


@dataclass(frozen=True, slots=True, kw_only=True)
class ResolvedRenderedPacketOutput:
    """One exact existing Packet PDF verified against canonical Concord state."""

    work: ModuleWorkRef
    packet_instance_id: str
    generation_id: str
    output_path: Path
    output_sha256: str
    page_count: int
    route_count: int

    @property
    def output_directory(self) -> Path:
        """Return the verified Packet PDF's rendered-Packet directory."""
        return self.output_path.parent


def resolve_rendered_packet_output(
    class_id: str,
    activity_id: str,
    packet_instance_id: str,
    *,
    workspace_root: str | Path | None = None,
) -> ResolvedRenderedPacketOutput:
    """Resolve and integrity-check one already-rendered Packet PDF.

    This service is strictly read-only. It never renders, repairs, rewrites, or
    advances Packet lifecycle state.
    """
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError("Paper Data Suite workspace does not exist.")

    detail = show_packet_instance(
        class_id,
        activity_id,
        packet_instance_id,
        workspace_root=root,
    )
    summary = detail.summary
    if summary.activity_id != activity_id:
        raise ConcordWorkflowConflictError(
            "Packet Instance Activity identity contradicts the requested Activity."
        )
    if summary.generation_status != "generated":
        raise ConcordWorkflowValidationError(
            "This Packet is not ready to open yet. Use Render / reprint a Packet "
            "Instance."
        )
    if summary.output_relative_path is None or summary.output_sha256 is None:
        raise ConcordWorkflowConflictError(
            "Generated Packet output metadata is incomplete. Use Render / reprint "
            "to restore the exact Packet output."
        )

    work = ModuleWorkRef("concord", class_id, activity_id)
    output_path = _safe_rendered_packet_path(
        root,
        work,
        summary.output_relative_path,
    )
    _reject_link_like_descendants(root, work, output_path)

    if not output_path.exists():
        raise ConcordWorkflowNotFoundError(
            "This rendered Packet is missing. Use Render / reprint to recreate "
            "the exact output."
        )
    if not output_path.is_file():
        raise ConcordWorkflowConflictError(
            "The recorded rendered Packet output is not a regular file."
        )

    try:
        actual_sha256 = _file_sha256(output_path)
    except FileNotFoundError as error:
        raise ConcordWorkflowNotFoundError(
            "This rendered Packet is missing. Use Render / reprint to recreate "
            "the exact output."
        ) from error
    except OSError as error:
        raise ConcordWorkflowConflictError(
            "The recorded rendered Packet output could not be read safely."
        ) from error
    if actual_sha256 != summary.output_sha256:
        raise ConcordWorkflowConflictError(
            "This rendered Packet does not match Concord's recorded output. Use "
            "Render / reprint to restore the exact Packet output."
        )

    return ResolvedRenderedPacketOutput(
        work=work,
        packet_instance_id=summary.packet_instance_id,
        generation_id=summary.generation_id,
        output_path=output_path,
        output_sha256=summary.output_sha256,
        page_count=summary.page_count,
        route_count=summary.route_count,
    )


def _safe_rendered_packet_path(
    root: Path,
    work: ModuleWorkRef,
    relative_path: str,
) -> Path:
    try:
        work_root = module_work_dir(root, work)
        packet_root = safe_module_work_descendant(root, work, "rendered/packets")
        target = safe_module_work_descendant(root, work, relative_path)
    except (TypeError, ValueError) as error:
        raise ConcordWorkflowValidationError(
            "Recorded Packet output path is not a safe Concord work descendant."
        ) from error

    try:
        resolved_work = work_root.resolve(strict=False)
        resolved_packets = packet_root.resolve(strict=False)
        resolved_target = target.resolve(strict=False)
        resolved_packets.relative_to(resolved_work)
        resolved_target.relative_to(resolved_packets)
    except (OSError, RuntimeError, ValueError) as error:
        raise ConcordWorkflowValidationError(
            "Recorded Packet output must remain beneath rendered/packets/."
        ) from error

    if target.suffix.lower() != ".pdf":
        raise ConcordWorkflowValidationError("Recorded Packet output must be a PDF.")
    return target


def _reject_link_like_descendants(
    root: Path,
    work: ModuleWorkRef,
    target: Path,
) -> None:
    """Reject symlinks and Windows symlink/junction reparse points below work."""
    work_root = module_work_dir(root, work)
    try:
        relative = target.relative_to(work_root)
    except ValueError as error:
        raise ConcordWorkflowValidationError(
            "Recorded Packet output is outside the Concord Activity work root."
        ) from error

    current = work_root
    if current.is_symlink() or _is_windows_link_reparse_point(current):
        raise ConcordWorkflowValidationError(
            f"Concord Activity work root is a symbolic link or junction: {current}"
        )
    for part in relative.parts:
        current = current / part
        if current.is_symlink() or _is_windows_link_reparse_point(current):
            raise ConcordWorkflowValidationError(
                f"Rendered Packet path traverses a symbolic link or junction: {current}"
            )


def _is_windows_link_reparse_point(path: Path) -> bool:
    """Identify Windows symlink/junction tags without rejecting cloud placeholders."""
    try:
        info = path.lstat()
    except (FileNotFoundError, OSError):
        return False
    tag = getattr(info, "st_reparse_tag", 0)
    if not tag:
        return False
    symlink_tag = getattr(stat, "IO_REPARSE_TAG_SYMLINK", 0xA000000C)
    mount_point_tag = getattr(stat, "IO_REPARSE_TAG_MOUNT_POINT", 0xA0000003)
    return tag in {symlink_tag, mount_point_tag}


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


__all__ = [
    "ResolvedRenderedPacketOutput",
    "resolve_rendered_packet_output",
]
