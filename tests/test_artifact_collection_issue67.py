from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import concord.workflows.artifact_collection as collection
from concord.workflows.artifact_assembly import (
    ArtifactAssemblyAmbiguityError,
    ArtifactAssemblyIncompleteError,
    ArtifactAssemblyIntegrityError,
    AssemblyAmbiguity,
)


def _artifact() -> SimpleNamespace:
    return SimpleNamespace(
        artifact_instance_id="artifact-1",
        activity_id="activity-1",
    )


def _graph() -> SimpleNamespace:
    return SimpleNamespace(artifact_instances=(_artifact(),))


def test_assembly_state_waits_until_all_required_evidence_can_be_assembled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def incomplete(*_args: object, **_kwargs: object) -> object:
        raise ArtifactAssemblyIncompleteError(((2, "page-2"),))

    monkeypatch.setattr(collection, "_select_lineage", incomplete)
    assert collection._assembly_state(
        tmp_path,
        "class-1",
        "activity-1",
        _artifact(),  # type: ignore[arg-type]
        _graph(),  # type: ignore[arg-type]
    ) == "not_ready"


def test_assembly_state_marks_ambiguous_complete_returns_as_actionable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ambiguity = AssemblyAmbiguity(
        artifact_page_id="page-1",
        logical_page_number=1,
        scan_reference_ids=("scan-a", "scan-b"),
    )

    def ambiguous(*_args: object, **_kwargs: object) -> object:
        raise ArtifactAssemblyAmbiguityError((ambiguity,))

    monkeypatch.setattr(collection, "_select_lineage", ambiguous)
    assert collection._assembly_state(
        tmp_path,
        "class-1",
        "activity-1",
        _artifact(),  # type: ignore[arg-type]
        _graph(),  # type: ignore[arg-type]
    ) == "selection_required"


def test_assembly_state_distinguishes_ready_current_and_recovery(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lineage = (SimpleNamespace(),)
    output = tmp_path / "assemblies" / "assembly-1" / "artifact.pdf"
    manifest = output.with_name("manifest.json")
    monkeypatch.setattr(collection, "_select_lineage", lambda *_a, **_k: lineage)
    monkeypatch.setattr(collection, "_assembly_id", lambda *_a, **_k: "assembly-1")
    monkeypatch.setattr(
        collection,
        "_assembly_paths",
        lambda *_a, **_k: (output, manifest),
    )

    assert collection._assembly_state(
        tmp_path,
        "class-1",
        "activity-1",
        _artifact(),  # type: ignore[arg-type]
        _graph(),  # type: ignore[arg-type]
    ) == "ready"

    output.parent.mkdir(parents=True)
    monkeypatch.setattr(collection, "_verify_existing", lambda **_k: "a" * 64)
    assert collection._assembly_state(
        tmp_path,
        "class-1",
        "activity-1",
        _artifact(),  # type: ignore[arg-type]
        _graph(),  # type: ignore[arg-type]
    ) == "assembled"

    def invalid(**_kwargs: object) -> str:
        raise ArtifactAssemblyIntegrityError("invalid exact assembly")

    monkeypatch.setattr(collection, "_verify_existing", invalid)
    assert collection._assembly_state(
        tmp_path,
        "class-1",
        "activity-1",
        _artifact(),  # type: ignore[arg-type]
        _graph(),  # type: ignore[arg-type]
    ) == "needs_recovery"


def test_confirmation_attention_requires_explicit_current_pending_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        collection,
        "resolve_read_workspace_root",
        lambda _root: tmp_path,
    )
    monkeypatch.setattr(collection, "load_graph", lambda *_a, **_k: (_graph(), 1, "x"))
    monkeypatch.setattr(collection, "_assembly_state", lambda *_a, **_k: "assembled")
    monkeypatch.setattr(
        collection,
        "list_artifact_authors",
        lambda *_a, **_k: (
            SimpleNamespace(attribution_status="confirmed"),
            SimpleNamespace(attribution_status="unknown"),
        ),
    )
    monkeypatch.setattr(
        collection,
        "list_artifact_subjects",
        lambda *_a, **_k: (SimpleNamespace(confirmation_status="confirmed"),),
    )
    state = collection.inspect_artifact_collection_state(
        "class-1",
        "activity-1",
        "artifact-1",
        workspace_root=tmp_path,
    )
    assert not state.author_confirmation_pending
    assert not state.subject_confirmation_pending

    monkeypatch.setattr(
        collection,
        "list_artifact_authors",
        lambda *_a, **_k: (SimpleNamespace(attribution_status="proposed"),),
    )
    monkeypatch.setattr(
        collection,
        "list_artifact_subjects",
        lambda *_a, **_k: (SimpleNamespace(confirmation_status="unresolved"),),
    )
    state = collection.inspect_artifact_collection_state(
        "class-1",
        "activity-1",
        "artifact-1",
        workspace_root=tmp_path,
    )
    assert state.author_confirmation_pending
    assert state.subject_confirmation_pending


def test_zero_author_and_subject_records_do_not_manufacture_confirmation_attention(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        collection,
        "resolve_read_workspace_root",
        lambda _root: tmp_path,
    )
    monkeypatch.setattr(collection, "load_graph", lambda *_a, **_k: (_graph(), 1, "x"))
    monkeypatch.setattr(collection, "_assembly_state", lambda *_a, **_k: "not_ready")
    monkeypatch.setattr(collection, "list_artifact_authors", lambda *_a, **_k: ())
    monkeypatch.setattr(collection, "list_artifact_subjects", lambda *_a, **_k: ())
    state = collection.inspect_artifact_collection_state(
        "class-1",
        "activity-1",
        "artifact-1",
        workspace_root=tmp_path,
    )
    assert not state.author_confirmation_pending
    assert not state.subject_confirmation_pending
