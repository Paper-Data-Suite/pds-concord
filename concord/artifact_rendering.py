"""Neutral read-only retained Artifact rendering primitives."""

from __future__ import annotations

import hashlib
import io
import os
import stat as stat_module
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from concord.model_validation import ConcordRecordGraph
from concord.models import ArtifactInstance, ArtifactPage, ScanReference

_IMAGE_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".tif", ".tiff"})


class ReturnedArtifactRenderError(ValueError):
    """Base class for read-only returned-Artifact rendering failures."""


class ReturnedArtifactRenderUnavailableError(ReturnedArtifactRenderError):
    """Required returned Artifact evidence is unavailable."""


class ReturnedArtifactRenderAmbiguityError(ReturnedArtifactRenderError):
    """Returned Artifact evidence has more than one valid occurrence."""


class ReturnedArtifactRenderIntegrityError(ReturnedArtifactRenderError):
    """Retained-source integrity or bounded rendering failed."""


@dataclass(frozen=True, slots=True)
class VerifiedRetainedSource:
    """Exact retained-source bytes after containment and SHA-256 verification."""

    suffix: str
    content: bytes

    def __post_init__(self) -> None:
        if self.suffix not in _IMAGE_EXTENSIONS | {".pdf"}:
            raise ReturnedArtifactRenderIntegrityError(
                "verified retained source has an unsupported extension."
            )
        if type(self.content) is not bytes or not self.content:
            raise ReturnedArtifactRenderIntegrityError(
                "verified retained source must contain immutable bytes."
            )


def _is_link_like(path: Path) -> bool:
    if path.is_symlink():
        return True
    try:
        attributes = int(getattr(path.lstat(), "st_file_attributes", 0))
    except FileNotFoundError:
        return False
    except OSError as error:
        raise ReturnedArtifactRenderIntegrityError(
            "retained-source filesystem metadata could not be verified."
        ) from error
    reparse = int(getattr(stat_module, "FILE_ATTRIBUTE_REPARSE_POINT", 0))
    return bool(reparse and attributes & reparse)


def _assert_no_link_like_ancestors(path: Path, *, stop: Path) -> None:
    current = path
    while True:
        if os.path.lexists(current) and _is_link_like(current):
            raise ReturnedArtifactRenderIntegrityError(
                "retained-source path traverses a link-like filesystem object."
            )
        if current == stop:
            return
        if stop not in current.parents:
            raise ReturnedArtifactRenderIntegrityError(
                "retained-source path escaped the workspace root."
            )
        current = current.parent


def _retained_source_parts(scan: ScanReference) -> tuple[str, ...]:
    relative = PurePosixPath(scan.retained_source_relative_path)
    parts = tuple(relative.parts)
    if (
        relative.is_absolute()
        or not parts
        or any(part in {"", ".", ".."} for part in parts)
    ):
        raise ReturnedArtifactRenderIntegrityError(
            "retained-source path is not a safe relative path."
        )
    return parts


def _read_fd_bytes(descriptor: int) -> bytes:
    chunks: list[bytes] = []
    while True:
        chunk = os.read(descriptor, 1024 * 1024)
        if not chunk:
            break
        chunks.append(chunk)
    return b"".join(chunks)


def _open_posix_root_directory(root: Path) -> int:
    """Open every supplied root component without following links."""
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    directory = getattr(os, "O_DIRECTORY", 0)
    cloexec = getattr(os, "O_CLOEXEC", 0)
    if not nofollow or not directory:
        raise ReturnedArtifactRenderIntegrityError(
            "platform cannot enforce non-link retained-source traversal."
        )

    absolute = Path(os.path.abspath(os.fspath(root)))
    if not absolute.is_absolute() or not absolute.anchor:
        raise ReturnedArtifactRenderIntegrityError(
            "workspace root is not an absolute filesystem path."
        )

    current: int | None = None
    try:
        current = os.open(
            absolute.anchor,
            os.O_RDONLY | directory | nofollow | cloexec,
        )
        for part in absolute.parts[1:]:
            next_descriptor = os.open(
                part,
                os.O_RDONLY | directory | nofollow | cloexec,
                dir_fd=current,
            )
            try:
                if not stat_module.S_ISDIR(os.fstat(next_descriptor).st_mode):
                    raise ReturnedArtifactRenderIntegrityError(
                        "workspace root traverses a non-directory filesystem object."
                    )
            except BaseException:
                os.close(next_descriptor)
                raise
            os.close(current)
            current = next_descriptor
        if not stat_module.S_ISDIR(os.fstat(current).st_mode):
            raise ReturnedArtifactRenderIntegrityError(
                "workspace root must be an ordinary non-link directory."
            )
        result = current
        current = None
        return result
    except ReturnedArtifactRenderIntegrityError:
        raise
    except OSError as error:
        raise ReturnedArtifactRenderIntegrityError(
            "workspace root could not be safely opened."
        ) from error
    finally:
        if current is not None:
            try:
                os.close(current)
            except OSError:
                pass


def _read_posix_contained_file(root: Path, parts: tuple[str, ...]) -> bytes:
    """Traverse from one no-follow root handle and read one exact file."""
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    directory = getattr(os, "O_DIRECTORY", 0)
    cloexec = getattr(os, "O_CLOEXEC", 0)
    if not nofollow or not directory:
        raise ReturnedArtifactRenderIntegrityError(
            "platform cannot enforce non-link retained-source traversal."
        )

    current: int | None = None
    opened_file: int | None = None
    try:
        current = _open_posix_root_directory(root)
        for part in parts[:-1]:
            next_descriptor = os.open(
                part,
                os.O_RDONLY | directory | nofollow | cloexec,
                dir_fd=current,
            )
            try:
                if not stat_module.S_ISDIR(os.fstat(next_descriptor).st_mode):
                    raise ReturnedArtifactRenderIntegrityError(
                        "retained-source ancestor is not an ordinary directory."
                    )
            except BaseException:
                os.close(next_descriptor)
                raise
            os.close(current)
            current = next_descriptor

        opened_file = os.open(
            parts[-1],
            os.O_RDONLY
            | nofollow
            | cloexec
            | getattr(os, "O_BINARY", 0),
            dir_fd=current,
        )
        if not stat_module.S_ISREG(os.fstat(opened_file).st_mode):
            raise ReturnedArtifactRenderIntegrityError(
                "retained source must be an ordinary non-link file."
            )
        return _read_fd_bytes(opened_file)
    except ReturnedArtifactRenderIntegrityError:
        raise
    except OSError as error:
        raise ReturnedArtifactRenderIntegrityError(
            "retained source could not be safely opened."
        ) from error
    finally:
        if opened_file is not None:
            try:
                os.close(opened_file)
            except OSError:
                pass
        if current is not None:
            try:
                os.close(current)
            except OSError:
                pass


def _windows_final_path(handle: int) -> Path:
    import ctypes

    kernel32 = getattr(ctypes, "WinDLL")("kernel32", use_last_error=True)
    get_final = kernel32.GetFinalPathNameByHandleW
    get_final.argtypes = [
        ctypes.c_void_p,
        ctypes.c_wchar_p,
        ctypes.c_ulong,
        ctypes.c_ulong,
    ]
    get_final.restype = ctypes.c_ulong

    size = get_final(ctypes.c_void_p(handle), None, 0, 0)
    if size == 0:
        raise ReturnedArtifactRenderIntegrityError(
            "retained-source handle path could not be verified."
        )
    buffer = ctypes.create_unicode_buffer(size + 1)
    written = get_final(
        ctypes.c_void_p(handle),
        buffer,
        len(buffer),
        0,
    )
    if written == 0 or written >= len(buffer):
        raise ReturnedArtifactRenderIntegrityError(
            "retained-source handle path could not be verified."
        )
    raw = buffer.value
    if raw.startswith("\\\\?\\UNC\\"):
        raw = "\\\\" + raw[8:]
    elif raw.startswith("\\\\?\\"):
        raw = raw[4:]
    return Path(raw)


def _windows_path_key(path: Path) -> str:
    return os.path.normcase(os.path.normpath(str(path)))


def _read_windows_contained_file(root: Path, parts: tuple[str, ...]) -> bytes:
    """Read beneath one retained, verified non-reparse Windows root handle."""
    import ctypes
    import importlib

    kernel32 = getattr(ctypes, "WinDLL")("kernel32", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = [
        ctypes.c_wchar_p,
        ctypes.c_ulong,
        ctypes.c_ulong,
        ctypes.c_void_p,
        ctypes.c_ulong,
        ctypes.c_ulong,
        ctypes.c_void_p,
    ]
    create_file.restype = ctypes.c_void_p
    get_info = kernel32.GetFileInformationByHandleEx
    get_info.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_void_p,
        ctypes.c_ulong,
    ]
    get_info.restype = ctypes.c_int
    close_handle = kernel32.CloseHandle
    close_handle.argtypes = [ctypes.c_void_p]
    close_handle.restype = ctypes.c_int

    class _FileAttributeTagInfo(ctypes.Structure):
        _fields_ = [
            ("file_attributes", ctypes.c_ulong),
            ("reparse_tag", ctypes.c_ulong),
        ]

    generic_read = 0x80000000
    file_read_attributes = 0x00000080
    share_read = 0x00000001
    open_existing = 3
    open_reparse_point = 0x00200000
    backup_semantics = 0x02000000
    sequential_scan = 0x08000000
    invalid_handle = ctypes.c_void_p(-1).value
    reparse_attribute = 0x00000400
    directory_attribute = 0x00000010
    file_attribute_tag_info = 9

    root_absolute = Path(os.path.abspath(os.fspath(root)))
    raw_root_handle = create_file(
        str(root_absolute),
        file_read_attributes,
        share_read,
        None,
        open_existing,
        open_reparse_point | backup_semantics,
        None,
    )
    root_handle = int(ctypes.cast(raw_root_handle, ctypes.c_void_p).value or 0)
    if not root_handle or root_handle == invalid_handle:
        raise ReturnedArtifactRenderIntegrityError(
            "workspace root could not be safely opened."
        )

    source_handle = 0
    descriptor: int | None = None
    try:
        root_info = _FileAttributeTagInfo()
        if not get_info(
            ctypes.c_void_p(root_handle),
            file_attribute_tag_info,
            ctypes.byref(root_info),
            ctypes.sizeof(root_info),
        ):
            raise ReturnedArtifactRenderIntegrityError(
                "workspace root handle attributes could not be verified."
            )
        if (
            root_info.file_attributes & reparse_attribute
            or not root_info.file_attributes & directory_attribute
        ):
            raise ReturnedArtifactRenderIntegrityError(
                "workspace root must be an ordinary non-link directory."
            )

        root_final = _windows_final_path(root_handle)
        if _windows_path_key(root_final) != _windows_path_key(root_absolute):
            raise ReturnedArtifactRenderIntegrityError(
                "workspace root handle did not identify the supplied root."
            )

        candidate = root_final.joinpath(*parts)
        raw_source_handle = create_file(
            str(candidate),
            generic_read,
            share_read,
            None,
            open_existing,
            open_reparse_point | sequential_scan,
            None,
        )
        source_handle = int(
            ctypes.cast(raw_source_handle, ctypes.c_void_p).value or 0
        )
        if not source_handle or source_handle == invalid_handle:
            raise ReturnedArtifactRenderIntegrityError(
                "retained source could not be safely opened."
            )

        source_info = _FileAttributeTagInfo()
        if not get_info(
            ctypes.c_void_p(source_handle),
            file_attribute_tag_info,
            ctypes.byref(source_info),
            ctypes.sizeof(source_info),
        ):
            raise ReturnedArtifactRenderIntegrityError(
                "retained-source handle attributes could not be verified."
            )
        if (
            source_info.file_attributes & reparse_attribute
            or source_info.file_attributes & directory_attribute
        ):
            raise ReturnedArtifactRenderIntegrityError(
                "retained source must be an ordinary non-link file."
            )

        final_path = _windows_final_path(source_handle)
        if _windows_path_key(final_path) != _windows_path_key(candidate):
            raise ReturnedArtifactRenderIntegrityError(
                "retained-source handle did not resolve to its canonical path."
            )
        try:
            final_path.relative_to(root_final)
        except ValueError as error:
            raise ReturnedArtifactRenderIntegrityError(
                "retained-source handle escaped the workspace root."
            ) from error

        _assert_no_link_like_ancestors(candidate, stop=root_final)
        msvcrt = importlib.import_module("msvcrt")
        open_osfhandle = getattr(msvcrt, "open_osfhandle")
        descriptor = open_osfhandle(
            source_handle,
            os.O_RDONLY | getattr(os, "O_BINARY", 0),
        )
        source_handle = 0
        if not stat_module.S_ISREG(os.fstat(descriptor).st_mode):
            raise ReturnedArtifactRenderIntegrityError(
                "retained source must be an ordinary non-link file."
            )
        return _read_fd_bytes(descriptor)
    except ReturnedArtifactRenderIntegrityError:
        raise
    except (OSError, ValueError) as error:
        raise ReturnedArtifactRenderIntegrityError(
            "retained source could not be safely read."
        ) from error
    finally:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass
        elif source_handle:
            close_handle(ctypes.c_void_p(source_handle))
        close_handle(ctypes.c_void_p(root_handle))


def validate_retained_source(
    root: Path,
    scan: ScanReference,
) -> VerifiedRetainedSource:
    """Read and verify one retained source from one no-follow root trust chain."""
    root_path = Path(os.path.abspath(os.fspath(root)))
    parts = _retained_source_parts(scan)
    try:
        if os.name == "nt":
            data = _read_windows_contained_file(root_path, parts)
        else:
            data = _read_posix_contained_file(root_path, parts)
    except ReturnedArtifactRenderIntegrityError:
        raise
    except Exception as error:
        raise ReturnedArtifactRenderIntegrityError(
            "retained source could not be safely read."
        ) from error

    if hashlib.sha256(data).hexdigest() != scan.retained_source_sha256:
        raise ReturnedArtifactRenderIntegrityError(
            "retained-source digest does not match the canonical Scan Reference."
        )
    return VerifiedRetainedSource(
        suffix=PurePosixPath(scan.retained_source_relative_path).suffix.lower(),
        content=data,
    )


def render_retained_source_page(
    source: VerifiedRetainedSource,
    source_page_number: int,
) -> Any:
    """Decode exactly one physical page from already-verified source bytes."""
    suffix = source.suffix
    try:
        from PIL import Image
    except ImportError as error:  # pragma: no cover - installation guard
        raise ReturnedArtifactRenderIntegrityError(
            "Pillow is required for returned-Artifact rendering."
        ) from error

    if suffix in _IMAGE_EXTENSIONS:
        if source_page_number != 1:
            raise ReturnedArtifactRenderIntegrityError(
                "image retained sources contain only physical page 1."
            )
        try:
            with Image.open(io.BytesIO(source.content)) as image:
                return image.convert("RGB").copy()
        except Exception as error:
            raise ReturnedArtifactRenderIntegrityError(
                "retained image could not be decoded."
            ) from error

    if suffix != ".pdf":
        raise ReturnedArtifactRenderIntegrityError(
            f"unsupported retained-source extension: {suffix}"
        )
    try:
        import pypdfium2
    except ImportError as error:  # pragma: no cover - installation guard
        raise ReturnedArtifactRenderIntegrityError(
            "pypdfium2 is required for PDF returned-Artifact rendering."
        ) from error
    try:
        document = pypdfium2.PdfDocument(source.content)
    except Exception as error:
        raise ReturnedArtifactRenderIntegrityError(
            "retained PDF could not be opened."
        ) from error
    try:
        page_count = len(document)
        if source_page_number < 1 or source_page_number > page_count:
            raise ReturnedArtifactRenderIntegrityError(
                "Scan Reference physical page is outside the retained PDF."
            )
        page = document[source_page_number - 1]
        return page.render(scale=2).to_pil().convert("RGB").copy()
    except ReturnedArtifactRenderIntegrityError:
        raise
    except Exception as error:
        raise ReturnedArtifactRenderIntegrityError(
            "retained PDF physical page could not be rendered."
        ) from error
    finally:
        document.close()


def encode_returned_artifact_pdf(images: tuple[Any, ...], created_at: str) -> bytes:
    """Encode ordered RGB images as deterministic returned-Artifact PDF bytes."""
    if not images:
        raise ReturnedArtifactRenderIntegrityError(
            "returned-Artifact rendering requires at least one page."
        )
    try:
        canonical_time = datetime.fromisoformat(
            created_at.replace("Z", "+00:00")
        ).astimezone(timezone.utc).timetuple()
    except ValueError as error:
        raise ReturnedArtifactRenderIntegrityError(
            "Artifact creation provenance has an invalid timestamp."
        ) from error
    output = io.BytesIO()
    try:
        images[0].save(
            output,
            "PDF",
            save_all=True,
            append_images=list(images[1:]),
            resolution=150.0,
            creationDate=canonical_time,
            modDate=canonical_time,
        )
    except Exception as error:
        raise ReturnedArtifactRenderIntegrityError(
            "returned Artifact PDF could not be encoded."
        ) from error
    data = output.getvalue()
    if not data.startswith(b"%PDF"):
        raise ReturnedArtifactRenderIntegrityError(
            "returned Artifact encoder did not produce PDF bytes."
        )
    return data


def _artifact_pages(
    artifact: ArtifactInstance,
    graph: ConcordRecordGraph,
) -> dict[str, ArtifactPage]:
    pages = {item.artifact_page_id: item for item in graph.artifact_pages}
    for page_id in artifact.page_ids:
        page = pages.get(page_id)
        if page is None or page.artifact_instance_id != artifact.artifact_instance_id:
            raise ReturnedArtifactRenderIntegrityError(
                "Artifact declared page structure is inconsistent."
            )
    return pages


def _single_scan(
    artifact: ArtifactInstance,
    page: ArtifactPage,
    graph: ConcordRecordGraph,
) -> ScanReference:
    candidates = tuple(
        sorted(
            (
                item
                for item in graph.scan_references
                if item.artifact_page_id == page.artifact_page_id
            ),
            key=lambda item: item.scan_reference_id,
        )
    )
    if not candidates:
        raise ReturnedArtifactRenderUnavailableError(
            "required returned Artifact page is unavailable."
        )
    if len(candidates) > 1:
        raise ReturnedArtifactRenderAmbiguityError(
            "returned Artifact page has multiple canonical scan occurrences."
        )
    scan = candidates[0]
    if (
        scan.activity_id != artifact.activity_id
        or scan.artifact_page_id != page.artifact_page_id
        or scan.route_id != page.route_id
    ):
        raise ReturnedArtifactRenderIntegrityError(
            "Scan Reference contradicts the canonical Artifact Page."
        )
    return scan


def _selected_scans(
    artifact: ArtifactInstance,
    graph: ConcordRecordGraph,
    evidence_page: ArtifactPage | None,
) -> tuple[ScanReference, ...]:
    pages = _artifact_pages(artifact, graph)
    if evidence_page is not None:
        if (
            evidence_page.artifact_instance_id != artifact.artifact_instance_id
            or evidence_page.artifact_page_id not in artifact.page_ids
        ):
            raise ReturnedArtifactRenderIntegrityError(
                "Artifact Page is inconsistent with its Artifact Instance."
            )
        canonical_page = pages.get(evidence_page.artifact_page_id)
        if canonical_page != evidence_page:
            raise ReturnedArtifactRenderIntegrityError(
                "Artifact Page is not the exact historical page selected by the graph."
            )
        return (_single_scan(artifact, evidence_page, graph),)

    required = tuple(
        pages[page_id]
        for page_id in artifact.page_ids
        if pages[page_id].return_expected
    )
    if not required:
        raise ReturnedArtifactRenderUnavailableError(
            "Artifact has no return-expected pages to render."
        )
    return tuple(_single_scan(artifact, page, graph) for page in required)


def render_returned_artifact_pdf(
    workspace_root: str | Path,
    graph: ConcordRecordGraph,
    artifact: ArtifactInstance,
    *,
    evidence_page: ArtifactPage | None = None,
) -> bytes:
    """Render exact historical returned Artifact evidence without durable writes."""
    root = Path(workspace_root)
    scans = _selected_scans(artifact, graph, evidence_page)
    images: list[Any] = []
    try:
        for scan in scans:
            source = validate_retained_source(root, scan)
            images.append(
                render_retained_source_page(source, scan.source_page_number)
            )
        return encode_returned_artifact_pdf(
            tuple(images), artifact.created_provenance.timestamp
        )
    finally:
        for image in images:
            close = getattr(image, "close", None)
            if callable(close):
                close()
