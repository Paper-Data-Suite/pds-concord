"""Retain-first physical scan decoding and Core PDS2 dispatch."""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from pds_core.module_dispatch import (
    RouteDispatchFailure,
    RouteDispatchRequest,
    RouteDispatchSuccess,
    dispatch_route,
)
from pds_core.module_profiles import ModuleRegistry, build_module_registry
from pds_core.pds2 import parse_pds2_payload
from pds_core.routing_models import RouteLocator
from pds_core.scan_failure_metadata import (
    ROUTING_FAILURE_SCHEMA_VERSION,
    RoutingFailureMetadata,
    routing_failure_metadata_from_dispatch_failure,
    write_routing_failure_metadata,
)
from pds_core.scan_retention import RetainedSourceScan, retain_source_scan

from concord.workflows.context import ensure_mutating_workspace_root

SUPPORTED_SCAN_EXTENSIONS = frozenset(
    {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}
)
RawPageDecoder = Callable[[Path], tuple[tuple[str, ...], ...]]


@dataclass(frozen=True, slots=True, kw_only=True)
class ScanPageOutcome:
    source_scan_id: str
    source_page_number: int
    status: str
    failure_id: str | None = None
    locator: RouteLocator | None = None
    module_result: object | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ScanSourceResult:
    source_path: Path
    retained_source: RetainedSourceScan | None
    pages: tuple[ScanPageOutcome, ...]
    source_error: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ScanBatchResult:
    sources: tuple[ScanSourceResult, ...]

    @property
    def dispatched_count(self) -> int:
        return sum(
            page.status == "dispatched"
            for source in self.sources
            for page in source.pages
        )

    @property
    def failure_count(self) -> int:
        return sum(
            page.status == "review" for source in self.sources for page in source.pages
        )


def _default_decode(path: Path) -> tuple[tuple[str, ...], ...]:
    try:
        import zxingcpp
        from PIL import Image
    except ImportError as error:  # pragma: no cover
        raise RuntimeError(
            "Pillow and zxing-cpp are required for scan decoding."
        ) from error

    def payloads(image: object) -> tuple[str, ...]:
        values = []
        for result in zxingcpp.read_barcodes(image):
            text = result.text
            if isinstance(text, str) and text not in values:
                values.append(text)
        return tuple(values)

    if path.suffix.lower() == ".pdf":
        try:
            import pypdfium2
        except ImportError as error:  # pragma: no cover
            raise RuntimeError("pypdfium2 is required for PDF scan intake.") from error
        document = pypdfium2.PdfDocument(path)
        try:
            return tuple(payloads(page.render(scale=2).to_pil()) for page in document)
        finally:
            document.close()
    with Image.open(path) as image:
        return (payloads(image.copy()),)


def _failure_id(
    retained: RetainedSourceScan, page: int, category: str, payload: str | None
) -> str:
    value = f"{retained.source_scan_id}|{page}|{category}|{payload or ''}".encode()
    return f"failure_{hashlib.sha256(value).hexdigest()[:32]}"


def _record_observation_failure(
    root: Path,
    retained: RetainedSourceScan,
    page: int,
    *,
    category: str,
    stage: str,
    message: str,
    payload: str | None = None,
    locator: RouteLocator | None = None,
) -> str:
    failure_id = _failure_id(retained, page, category, payload)
    metadata = RoutingFailureMetadata(
        schema_version=ROUTING_FAILURE_SCHEMA_VERSION,
        failure_id=failure_id,
        scope="page",
        stage=stage,
        created_at=datetime.now(timezone.utc).isoformat(),
        failure_category=category,
        failure_message=message,
        source_filename=retained.source_filename,
        source_scan_id=retained.source_scan_id,
        source_sha256=retained.source_sha256,
        retained_source_path=retained.retained_source_relative_path,
        review_copy_path=None,
        source_page_number=page,
        detected_payload=payload,
        route_locator=locator,
        target=None,
        module_details={"intake_module": "concord"},
    )
    try:
        write_routing_failure_metadata(root, metadata)
    except Exception as error:
        # Deterministic metadata IDs make a repeated operation safely inspectable.
        from pds_core.scan_failure_metadata import load_routing_failure_metadata

        existing = load_routing_failure_metadata(root, failure_id)
        if existing != metadata:
            raise error
    return failure_id


def _parse_page(
    raw_payloads: tuple[str, ...],
) -> tuple[RouteLocator | None, str | None, str | None]:
    candidates: list[tuple[str, RouteLocator]] = []
    malformed: list[str] = []
    for raw in dict.fromkeys(raw_payloads):
        try:
            locator = parse_pds2_payload(raw)
        except ValueError:
            if raw.startswith("PDS2"):
                malformed.append(raw)
            continue
        candidates.append((raw, locator))
    distinct = {locator for _, locator in candidates}
    if len(distinct) > 1:
        return None, None, "ambiguous"
    if len(distinct) == 1:
        locator = next(iter(distinct))
        raw = next(raw for raw, item in candidates if item == locator)
        return locator, raw, None
    if malformed:
        return None, malformed[0], "malformed"
    return None, None, "missing"


def route_scan_sources(
    sources: Iterable[str | Path],
    *,
    workspace_root: str | Path | None = None,
    registry: ModuleRegistry | None = None,
    decoder: RawPageDecoder | None = None,
) -> ScanBatchResult:
    """Retain each source once and classify every retained physical page."""
    root = ensure_mutating_workspace_root(workspace_root).root
    module_registry = registry or build_module_registry()
    decode = decoder or _default_decode
    expanded: list[Path] = []
    for item in sources:
        path = Path(item)
        if path.is_dir() and not path.is_symlink():
            expanded.extend(
                child
                for child in path.iterdir()
                if child.is_file() and not child.is_symlink()
            )
        else:
            expanded.append(path)
    ordered = tuple(sorted(expanded, key=lambda path: str(path).casefold()))
    results: list[ScanSourceResult] = []
    for source in ordered:
        try:
            if source.suffix.lower() not in SUPPORTED_SCAN_EXTENSIONS:
                raise ValueError(f"unsupported scan source type: {source.suffix}")
            if source.is_symlink() or not source.is_file():
                raise ValueError("scan source must be a regular non-symlink file")
            retained = retain_source_scan(root, source)
        except Exception as error:
            results.append(
                ScanSourceResult(
                    source_path=source,
                    retained_source=None,
                    pages=(),
                    source_error=str(error),
                )
            )
            continue
        page_outcomes: list[ScanPageOutcome] = []
        try:
            decoded_pages = decode(retained.retained_source_path)
        except Exception as error:
            failure_id = _record_observation_failure(
                root,
                retained,
                1,
                category="payload_unreadable",
                stage="payload_detection",
                message=str(error),
            )
            decoded_pages = ()
            page_outcomes.append(
                ScanPageOutcome(
                    source_scan_id=retained.source_scan_id,
                    source_page_number=1,
                    status="review",
                    failure_id=failure_id,
                )
            )
        if not decoded_pages and not page_outcomes:
            failure_id = _record_observation_failure(
                root,
                retained,
                1,
                category="payload_unreadable",
                stage="payload_detection",
                message="Retained source contains no readable physical pages.",
            )
            page_outcomes.append(
                ScanPageOutcome(
                    source_scan_id=retained.source_scan_id,
                    source_page_number=1,
                    status="review",
                    failure_id=failure_id,
                )
            )
        for number, raw_payloads in enumerate(decoded_pages, start=1):
            locator, raw, parse_state = _parse_page(raw_payloads)
            if parse_state is not None:
                category = {
                    "missing": "payload_missing",
                    "malformed": "payload_invalid",
                    "ambiguous": "route_ambiguous",
                }[parse_state]
                failure_id = _record_observation_failure(
                    root,
                    retained,
                    number,
                    category=category,
                    stage="payload_parsing",
                    message={
                        "missing": "No usable PDS2 payload was detected.",
                        "malformed": "A PDS2-looking payload is malformed.",
                        "ambiguous": "Several distinct PDS2 routes were detected.",
                    }[parse_state],
                    payload=raw,
                )
                page_outcomes.append(
                    ScanPageOutcome(
                        source_scan_id=retained.source_scan_id,
                        source_page_number=number,
                        status="review",
                        failure_id=failure_id,
                    )
                )
                continue
            assert locator is not None
            request = RouteDispatchRequest(locator, retained, number)
            try:
                dispatched = dispatch_route(root, module_registry, request)
            except Exception as error:
                failure = RouteDispatchFailure(request=request, error=error)
                failure_id = _failure_id(retained, number, "dispatch", raw)
                metadata = routing_failure_metadata_from_dispatch_failure(
                    failure,
                    failure_id=failure_id,
                    created_at=datetime.now(timezone.utc).isoformat(),
                    detected_payload=raw,
                    module_details={"intake_module": "concord"},
                )
                write_routing_failure_metadata(root, metadata)
                page_outcomes.append(
                    ScanPageOutcome(
                        source_scan_id=retained.source_scan_id,
                        source_page_number=number,
                        status="review",
                        failure_id=failure_id,
                        locator=locator,
                    )
                )
            else:
                assert isinstance(dispatched, RouteDispatchSuccess)
                page_outcomes.append(
                    ScanPageOutcome(
                        source_scan_id=retained.source_scan_id,
                        source_page_number=number,
                        status="dispatched",
                        locator=locator,
                        module_result=dispatched.module_result,
                    )
                )
        results.append(
            ScanSourceResult(
                source_path=source, retained_source=retained, pages=tuple(page_outcomes)
            )
        )
    return ScanBatchResult(sources=tuple(results))


def route_scan_folder(folder: str | Path, **kwargs: object) -> ScanBatchResult:
    root = Path(folder)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("scan folder must be a regular non-symlink directory.")
    return route_scan_sources((root,), **kwargs)  # type: ignore[arg-type]


__all__ = [
    "SUPPORTED_SCAN_EXTENSIONS",
    "ScanBatchResult",
    "ScanPageOutcome",
    "ScanSourceResult",
    "route_scan_folder",
    "route_scan_sources",
]
