from __future__ import annotations

import hashlib
from datetime import date, datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.local_open import LocalOpenError
from pds_core.pds2 import parse_pds2_payload
from pds_core.route_registrations import resolve_route_registration
from pds_core.routing_models import ModuleWorkRef
from pds_core.scan_retention import RetainedSourceScan
from pds_core.workspace import ensure_workspace_root
from PIL import Image

from concord.models import PrivacyPolicy
from concord.storage import load_current_record_graph
from concord.workflows import (
    ArtifactAssemblyAmbiguityError,
    ArtifactAssemblyIntegrityError,
    ArtifactAssemblyNotFoundError,
    AssembleArtifactRequest,
    AssemblyPageSelection,
    ConcordWorkflowConflictError,
    ConcordWorkflowOpenError,
    CreateActivityContextRequest,
    ResolvedReturnedArtifactAssembly,
    WorkflowActor,
    assemble_returned_artifact,
    create_activity_context,
    open_returned_artifact_evidence,
    resolve_returned_artifact_assembly,
)
from concord.workflows.artifact_page import (
    ArtifactPagePlan,
    PrepareArtifactPagesRequest,
    handle_concord_route,
    prepare_artifact_pages,
)


def _clock() -> datetime:
    return datetime(2026, 9, 22, 23, 30, tzinfo=timezone.utc)


def _actor() -> WorkflowActor:
    return WorkflowActor(actor_id="teacher-1")


def _work() -> ModuleWorkRef:
    return ModuleWorkRef("concord", "class-1", "activity-1")


def _workspace(tmp_path: Path) -> Path:
    root = ensure_workspace_root(tmp_path / "workspace")
    write_class_metadata_for_class(
        root,
        create_class_metadata("class-1", "2026-2027", created_at=_clock()),
    )
    create_activity_context(
        CreateActivityContextRequest(
            class_id="class-1",
            activity_id="activity-1",
            title="Issue 105 Evidence Resolution",
            activity_type="project",
            scoring_orientation="evidence_only",
            session_id="session-1",
            actor=_actor(),
        ),
        workspace_root=root,
        clock=_clock,
    )
    return root


def _prepare(root: Path) -> Any:
    return prepare_artifact_pages(
        PrepareArtifactPagesRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            template_version_id="template-1",
            artifact_category="observation",
            expected_snapshot_revision=1,
            actor=_actor(),
            pages=(ArtifactPagePlan(page_number=1, artifact_page_id="page-1"),),
            privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
        ),
        workspace_root=root,
        clock=_clock,
    )


def _retained_image(
    root: Path,
    *,
    scan_id: str,
    filename: str,
    color: tuple[int, int, int],
) -> RetainedSourceScan:
    path = root / "scans" / "source" / "2026-09-22" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (80, 120), color).save(path)
    return RetainedSourceScan(
        source_scan_id=scan_id,
        source_filename=filename,
        source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        retained_source_path=path,
        retained_source_relative_path=path.relative_to(root).as_posix(),
        intake_timestamp=_clock(),
        intake_date=date(2026, 9, 22),
    )


def _return(root: Path, prepared: Any, retained: RetainedSourceScan) -> Any:
    payload = prepared.pages[0].pds2_payload
    assert payload is not None
    locator = parse_pds2_payload(payload)
    resolution = resolve_route_registration(root, locator)
    return handle_concord_route(resolution, retained, 1)


def _assemble(
    root: Path,
    *,
    selections: tuple[AssemblyPageSelection, ...] = (),
):
    loaded = load_current_record_graph(root, _work())
    return assemble_returned_artifact(
        AssembleArtifactRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            expected_snapshot_revision=loaded.snapshot_revision,
            actor=_actor(),
            selections=selections,
        ),
        workspace_root=root,
        clock=_clock,
    )


def _fingerprint(root: Path) -> tuple[tuple[str, str], ...]:
    rows: list[tuple[str, str]] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        if path.is_file():
            rows.append(
                (
                    path.relative_to(root).as_posix(),
                    hashlib.sha256(path.read_bytes()).hexdigest(),
                )
            )
    return tuple(rows)


def test_resolve_existing_exact_assembly_is_typed_and_read_only(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    prepared = _prepare(root)
    _return(
        root,
        prepared,
        _retained_image(
            root,
            scan_id="scan-1",
            filename="returned.png",
            color=(20, 30, 40),
        ),
    )
    assembled = _assemble(root)
    current = load_current_record_graph(root, _work())
    before = _fingerprint(root)

    resolved = resolve_returned_artifact_assembly(
        "class-1",
        "activity-1",
        "artifact-1",
        workspace_root=root,
    )

    assert isinstance(resolved, ResolvedReturnedArtifactAssembly)
    assert resolved.work == _work()
    assert resolved.artifact_instance_id == "artifact-1"
    assert resolved.assembly_id == assembled.assembly_id
    assert resolved.output_path == assembled.output_path
    assert resolved.manifest_path == assembled.manifest_path
    assert resolved.page_count == 1
    assert resolved.output_sha256 == assembled.output_sha256
    assert resolved.snapshot_revision == current.snapshot_revision
    assert resolved.snapshot_sha256 == current.snapshot_sha256
    assert _fingerprint(root) == before


def test_resolve_missing_exact_assembly_never_creates_output(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    prepared = _prepare(root)
    _return(
        root,
        prepared,
        _retained_image(
            root,
            scan_id="scan-1",
            filename="returned.png",
            color=(20, 30, 40),
        ),
    )
    before = _fingerprint(root)

    with pytest.raises(
        ArtifactAssemblyNotFoundError,
        match="has not been assembled.*Assemble returned work",
    ):
        resolve_returned_artifact_assembly(
            "class-1",
            "activity-1",
            "artifact-1",
            workspace_root=root,
        )

    assembly_root = (
        root
        / "classes"
        / "class-1"
        / "modules"
        / "concord"
        / "work"
        / "activity-1"
        / "attachments"
        / "artifacts"
        / "artifact-1"
        / "assemblies"
    )
    assert not assembly_root.exists()
    assert _fingerprint(root) == before


def test_resolve_duplicate_return_requires_exact_selection(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    prepared = _prepare(root)
    first = _return(
        root,
        prepared,
        _retained_image(
            root,
            scan_id="scan-first",
            filename="first.png",
            color=(1, 2, 3),
        ),
    )
    second = _return(
        root,
        prepared,
        _retained_image(
            root,
            scan_id="scan-second",
            filename="second.png",
            color=(4, 5, 6),
        ),
    )

    with pytest.raises(ArtifactAssemblyAmbiguityError):
        resolve_returned_artifact_assembly(
            "class-1",
            "activity-1",
            "artifact-1",
            workspace_root=root,
        )

    selected = (
        AssemblyPageSelection(
            artifact_page_id="page-1",
            scan_reference_id=second.scan_reference_id,
        ),
    )
    assembled = _assemble(root, selections=selected)
    resolved = resolve_returned_artifact_assembly(
        "class-1",
        "activity-1",
        "artifact-1",
        selections=selected,
        workspace_root=root,
    )
    assert resolved.assembly_id == assembled.assembly_id
    assert resolved.output_path == assembled.output_path

    other = (
        AssemblyPageSelection(
            artifact_page_id="page-1",
            scan_reference_id=first.scan_reference_id,
        ),
    )
    with pytest.raises(ArtifactAssemblyNotFoundError):
        resolve_returned_artifact_assembly(
            "class-1",
            "activity-1",
            "artifact-1",
            selections=other,
            workspace_root=root,
        )


def test_resolve_rejects_tampered_existing_pdf(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    prepared = _prepare(root)
    _return(
        root,
        prepared,
        _retained_image(
            root,
            scan_id="scan-1",
            filename="returned.png",
            color=(20, 30, 40),
        ),
    )
    assembled = _assemble(root)
    assembled.output_path.write_bytes(b"tampered returned Artifact PDF")

    with pytest.raises(
        ArtifactAssemblyIntegrityError,
        match="digest does not match",
    ):
        resolve_returned_artifact_assembly(
            "class-1",
            "activity-1",
            "artifact-1",
            workspace_root=root,
        )


def test_resolve_rejects_tampered_retained_source_custody(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    prepared = _prepare(root)
    retained = _retained_image(
        root,
        scan_id="scan-1",
        filename="returned.png",
        color=(20, 30, 40),
    )
    _return(root, prepared, retained)
    _assemble(root)
    retained.retained_source_path.write_bytes(b"tampered retained source")

    with pytest.raises(ArtifactAssemblyIntegrityError):
        resolve_returned_artifact_assembly(
            "class-1",
            "activity-1",
            "artifact-1",
            workspace_root=root,
        )

def test_open_returned_artifact_evidence_delegates_only_after_verification(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _workspace(tmp_path)
    prepared = _prepare(root)
    _return(
        root,
        prepared,
        _retained_image(
            root,
            scan_id="scan-open",
            filename="open.png",
            color=(20, 30, 40),
        ),
    )
    assembled = _assemble(root)
    before = _fingerprint(root)
    opened: list[Path] = []

    def _open(path: str | Path) -> Path:
        resolved = Path(path).resolve(strict=False)
        opened.append(resolved)
        return resolved

    monkeypatch.setattr(
        "concord.workflows.artifact_evidence_opening.open_local_path",
        _open,
    )

    resolved = open_returned_artifact_evidence(
        "class-1",
        "activity-1",
        "artifact-1",
        workspace_root=root,
    )

    assert resolved.output_path == assembled.output_path
    assert opened == [assembled.output_path.resolve(strict=False)]
    assert _fingerprint(root) == before


def test_open_returned_artifact_evidence_translates_core_open_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _workspace(tmp_path)
    prepared = _prepare(root)
    _return(
        root,
        prepared,
        _retained_image(
            root,
            scan_id="scan-open-fail",
            filename="open-fail.png",
            color=(20, 30, 40),
        ),
    )
    _assemble(root)
    before = _fingerprint(root)

    def _fail_open(path: str | Path) -> Path:
        del path
        raise LocalOpenError("synthetic local viewer failure")

    monkeypatch.setattr(
        "concord.workflows.artifact_evidence_opening.open_local_path",
        _fail_open,
    )

    with pytest.raises(
        ConcordWorkflowOpenError,
        match="verified the returned Artifact PDF.*default application",
    ) as caught:
        open_returned_artifact_evidence(
            "class-1",
            "activity-1",
            "artifact-1",
            workspace_root=root,
        )

    assert isinstance(caught.value.__cause__, LocalOpenError)
    assert _fingerprint(root) == before


def test_open_returned_artifact_evidence_never_opens_missing_assembly(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _workspace(tmp_path)
    prepared = _prepare(root)
    _return(
        root,
        prepared,
        _retained_image(
            root,
            scan_id="scan-not-assembled",
            filename="not-assembled.png",
            color=(20, 30, 40),
        ),
    )
    opened: list[Path] = []

    def _open(path: str | Path) -> Path:
        resolved = Path(path).resolve(strict=False)
        opened.append(resolved)
        return resolved

    monkeypatch.setattr(
        "concord.workflows.artifact_evidence_opening.open_local_path",
        _open,
    )

    with pytest.raises(ArtifactAssemblyNotFoundError):
        open_returned_artifact_evidence(
            "class-1",
            "activity-1",
            "artifact-1",
            workspace_root=root,
        )

    assert opened == []


def test_open_returned_artifact_evidence_never_opens_tampered_pdf(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _workspace(tmp_path)
    prepared = _prepare(root)
    _return(
        root,
        prepared,
        _retained_image(
            root,
            scan_id="scan-tampered-open",
            filename="tampered-open.png",
            color=(20, 30, 40),
        ),
    )
    assembled = _assemble(root)
    assembled.output_path.write_bytes(b"tampered immediately before open")
    opened: list[Path] = []

    def _open(path: str | Path) -> Path:
        resolved = Path(path).resolve(strict=False)
        opened.append(resolved)
        return resolved

    monkeypatch.setattr(
        "concord.workflows.artifact_evidence_opening.open_local_path",
        _open,
    )

    with pytest.raises(ArtifactAssemblyIntegrityError):
        open_returned_artifact_evidence(
            "class-1",
            "activity-1",
            "artifact-1",
            workspace_root=root,
        )

    assert opened == []


def test_open_returned_artifact_evidence_forwards_exact_occurrence_selection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _workspace(tmp_path)
    prepared = _prepare(root)
    _return(
        root,
        prepared,
        _retained_image(
            root,
            scan_id="scan-open-first",
            filename="open-first.png",
            color=(1, 2, 3),
        ),
    )
    second = _return(
        root,
        prepared,
        _retained_image(
            root,
            scan_id="scan-open-second",
            filename="open-second.png",
            color=(4, 5, 6),
        ),
    )
    selection = (
        AssemblyPageSelection(
            artifact_page_id="page-1",
            scan_reference_id=second.scan_reference_id,
        ),
    )
    assembled = _assemble(root, selections=selection)
    opened: list[Path] = []

    def _open(path: str | Path) -> Path:
        resolved = Path(path).resolve(strict=False)
        opened.append(resolved)
        return resolved

    monkeypatch.setattr(
        "concord.workflows.artifact_evidence_opening.open_local_path",
        _open,
    )

    resolved = open_returned_artifact_evidence(
        "class-1",
        "activity-1",
        "artifact-1",
        selections=selection,
        workspace_root=root,
    )

    assert resolved.assembly_id == assembled.assembly_id
    assert opened == [assembled.output_path.resolve(strict=False)]

def test_resolve_rejects_canonical_state_change_during_verification(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _workspace(tmp_path)
    prepared = _prepare(root)
    _return(
        root,
        prepared,
        _retained_image(
            root,
            scan_id="scan-currentness",
            filename="currentness.png",
            color=(20, 30, 40),
        ),
    )
    _assemble(root)
    current = load_current_record_graph(root, _work())
    before = _fingerprint(root)

    monkeypatch.setattr(
        "concord.workflows.artifact_assembly.load_current_snapshot",
        lambda *_args, **_kwargs: SimpleNamespace(
            snapshot_revision=current.snapshot_revision + 1,
            snapshot_sha256="f" * 64,
        ),
    )

    with pytest.raises(
        ConcordWorkflowConflictError,
        match="state changed.*Try opening the returned work again",
    ):
        resolve_returned_artifact_assembly(
            "class-1",
            "activity-1",
            "artifact-1",
            workspace_root=root,
        )

    assert _fingerprint(root) == before


def test_open_never_delegates_when_canonical_state_changes_during_resolution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _workspace(tmp_path)
    prepared = _prepare(root)
    _return(
        root,
        prepared,
        _retained_image(
            root,
            scan_id="scan-open-currentness",
            filename="open-currentness.png",
            color=(20, 30, 40),
        ),
    )
    _assemble(root)
    current = load_current_record_graph(root, _work())
    opened: list[Path] = []

    monkeypatch.setattr(
        "concord.workflows.artifact_assembly.load_current_snapshot",
        lambda *_args, **_kwargs: SimpleNamespace(
            snapshot_revision=current.snapshot_revision,
            snapshot_sha256="e" * 64,
        ),
    )

    def _open(path: str | Path) -> Path:
        resolved = Path(path).resolve(strict=False)
        opened.append(resolved)
        return resolved

    monkeypatch.setattr(
        "concord.workflows.artifact_evidence_opening.open_local_path",
        _open,
    )

    with pytest.raises(
        ConcordWorkflowConflictError,
        match="state changed.*Try opening the returned work again",
    ):
        open_returned_artifact_evidence(
            "class-1",
            "activity-1",
            "artifact-1",
            workspace_root=root,
        )

    assert opened == []
