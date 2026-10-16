"""Exact, provenance-driven chronology and assembly history, #134 Slice 2."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from concord.workflows import ConcordWorkflowConflictError
from concord.workflows.artifact import ArtifactScanOccurrenceSummary
from concord.workflows.artifact_assembly import (
    ArtifactAssemblyIntegrityError,
    AssemblyPageSelection,
)
from concord.workflows.returned_assembly_versions import (
    _exact_manifest_selections,
    _recorded_datetime,
    list_verified_assembly_versions,
)
from concord.workflows.teacher_evidence_chronology import (
    display_recorded_time,
    instant,
    occurrence_labels,
    ordered_occurrences,
)


def _scan(
    scan_id: str, when: str | None, page_number: int = 1
) -> ArtifactScanOccurrenceSummary:
    return ArtifactScanOccurrenceSummary(
        artifact_page_id="page-1",
        logical_page_number=1,
        scan_reference_id=scan_id,
        source_scan_id=f"scan-{scan_id}",
        source_page_number=page_number,
        snapshot_revision=7,
        routed_at=when,
    )


def test_routed_occurrences_sort_by_aware_instant_not_id_or_offset() -> None:
    older = _scan("scan-z", "2026-10-12T19:58:00-04:00")
    newer = _scan("scan-a", "2026-10-15T01:00:00+00:00")
    assert ordered_occurrences((older, newer)) == (newer, older)
    labels = occurrence_labels((older, newer))
    assert "most recently routed" in labels[0]
    assert "earlier retained occurrence" in labels[1]
    assert "scan-a" not in labels[0]
    assert "scan-z" not in labels[1]


def test_exact_tie_does_not_claim_one_routed_scan_newest() -> None:
    moment = "2026-10-14T14:12:00+00:00"
    labels = occurrence_labels((_scan("z", moment), _scan("a", moment)))
    assert len(labels) == 2
    assert all("order uncertain" in text for text in labels)
    assert all("most recently" not in text for text in labels)


def test_unrecorded_time_is_not_inferred_from_scan_identifier() -> None:
    labels = occurrence_labels((_scan("aaa", None), _scan("zzz", None)))
    assert all("chronology uncertain" in text for text in labels)
    assert all("time not recorded" in text for text in labels)
    assert instant("2026-10-14T12:00:00") is None
    assert instant("not-a-date") is None


def test_offset_equivalence_is_one_instant() -> None:
    first = instant("2026-10-12T19:58:00-04:00")
    second = instant("2026-10-12T23:58:00+00:00")
    assert first == second
    assert first is not None and first.tzinfo is not None
    assert "2026" in display_recorded_time("2026-10-12T23:58:00+00:00")


def test_manifest_history_fails_closed_for_malformed_pages() -> None:
    with pytest.raises(ArtifactAssemblyIntegrityError):
        _exact_manifest_selections({"ordered_pages": []})
    with pytest.raises(ArtifactAssemblyIntegrityError):
        _exact_manifest_selections({"ordered_pages": [{"artifact_page_id": 4}]})
    assert _exact_manifest_selections(
        {
            "ordered_pages": [
                {"artifact_page_id": "page1", "scan_reference_id": "ref2"}
            ]
        }
    ) == (AssemblyPageSelection(artifact_page_id="page1", scan_reference_id="ref2"),)


def test_assembly_creation_time_requires_aware_timestamp() -> None:
    with pytest.raises(ArtifactAssemblyIntegrityError):
        _recorded_datetime("2026-10-14T14:12:00")
    with pytest.raises(ArtifactAssemblyIntegrityError):
        _recorded_datetime("invalid")
    assert _recorded_datetime("2026-10-14T10:12:00-04:00") == datetime.fromisoformat(
        "2026-10-14T14:12:00+00:00"
    )


def test_history_rejects_stale_snapshot_without_enumerating_files(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import concord.workflows.returned_assembly_versions as history

    monkeypatch.setattr(history, "resolve_read_workspace_root", lambda _: tmp_path)
    monkeypatch.setattr(history, "require_core_class", lambda *_args: None)
    monkeypatch.setattr(history, "_standards", lambda *_args: None)
    monkeypatch.setattr(
        history,
        "load_current_record_graph",
        lambda *_args, **_kwargs: SimpleNamespace(snapshot_revision=8),
    )
    monkeypatch.setattr(
        history,
        "_existing_versions",
        lambda *_args: pytest.fail("Must not inspect versions on stale snapshot"),
    )
    with pytest.raises(ConcordWorkflowConflictError):
        list_verified_assembly_versions(
            "class1", "activity1", "artifact1",
            expected_snapshot_revision=7, workspace_root=tmp_path
        )


def test_history_requires_exact_current_artifact(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import concord.workflows.returned_assembly_versions as history
    from concord.workflows.errors import ConcordWorkflowNotFoundError

    monkeypatch.setattr(history, "resolve_read_workspace_root", lambda _: tmp_path)
    monkeypatch.setattr(history, "require_core_class", lambda *_args: None)
    monkeypatch.setattr(history, "_standards", lambda *_args: None)
    graph = SimpleNamespace(
        artifact_instances=(
            SimpleNamespace(artifact_instance_id="artifactX", activity_id="other"),
        )
    )
    monkeypatch.setattr(
        history,
        "load_current_record_graph",
        lambda *_args, **_kwargs: SimpleNamespace(
            graph=graph, snapshot_revision=7, snapshot_sha256="sha"
        ),
    )
    with pytest.raises(ConcordWorkflowNotFoundError):
        list_verified_assembly_versions(
            "class1", "activity1", "artifactX",
            expected_snapshot_revision=7, workspace_root=tmp_path
        )


def test_history_read_does_not_assume_review_or_score_version() -> None:
    from concord.workflows.returned_assembly_versions import VerifiedAssemblyVersion

    version = VerifiedAssemblyVersion(
        assembly_id="assembly_example",
        assembled_at="2026-10-15T14:18:00+00:00",
        page_count=2,
        selections=(AssemblyPageSelection(
            artifact_page_id="page1", scan_reference_id="scan1"
        ),),
        snapshot_revision=7,
        newer_evidence_status="additional_uncertain",
    )
    assert version.newer_evidence_status == "additional_uncertain"
    assert not hasattr(version, "reviewed_version")
    assert not hasattr(version, "scored_version")


def test_version_menu_opens_exact_selected_saved_lineage_without_writing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import concord.menu_artifact as menu
    from concord.workflows.returned_assembly_versions import VerifiedAssemblyVersion

    version = VerifiedAssemblyVersion(
        assembly_id="assembly_123",
        assembled_at="2026-10-12T23:58:00+00:00",
        page_count=2,
        selections=(AssemblyPageSelection(
            artifact_page_id="page1", scan_reference_id="older-scan"
        ),),
        snapshot_revision=11,
        newer_evidence_status="newer",
    )
    activity = SimpleNamespace(
        class_id="class1", activity_id="activity1", snapshot_revision=11
    )
    artifact = SimpleNamespace(artifact_instance_id="artifact1")
    choice = SimpleNamespace(summary=artifact, label="Group 1 | Session 1")
    calls: list[object] = []
    shown: list[tuple[str, tuple[str, ...]]] = []
    monkeypatch.setattr(menu, "_latest", lambda _: activity)
    monkeypatch.setattr(menu, "_choose_artifact_choice", lambda *_a, **_kw: choice)
    monkeypatch.setattr(
        menu, "list_verified_assembly_versions", lambda *_a, **_kw: (version,)
    )

    def choose(_title: str, items: object, labels: object, **_kw: object) -> object:
        assert "Newer routed evidence available" in str(labels)
        return version

    monkeypatch.setattr(menu, "select_one", choose)
    monkeypatch.setattr(
        menu, "open_returned_artifact_evidence",
        lambda *a, **kw: calls.append((a, kw)),
    )
    monkeypatch.setattr(
        menu, "show_result",
        lambda title, lines: shown.append((title, tuple(lines))),
    )
    monkeypatch.setattr(
        menu, "assemble_returned_artifact",
        lambda *_a, **_kw: pytest.fail("History must not assemble"),
    )
    menu.open_verified_assembly_version(activity)
    assert len(calls) == 1
    _, kwargs = calls[0]
    assert kwargs["selections"] == version.selections
    assert kwargs["expected_snapshot_revision"] == 11
    assert "Viewer Requested" in shown[0][0]
    assert all("assembly_123" not in line for line in shown[0][1])


def test_verified_history_compares_newer_routing_with_saved_exact_lineage(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import concord.workflows.returned_assembly_versions as history

    name = "assembly_" + "a" * 32
    base = tmp_path / "assemblies"
    (base / name).mkdir(parents=True)
    artifact = SimpleNamespace(artifact_instance_id="artifact1")
    selected = SimpleNamespace(
        scan_reference_id="older",
        artifact_page_id="page1",
    )
    older = SimpleNamespace(
        scan_reference_id="older", artifact_page_id="page1",
        created_provenance=SimpleNamespace(
            timestamp="2026-10-12T14:00:00+00:00"
        ),
    )
    newer = SimpleNamespace(
        scan_reference_id="newer", artifact_page_id="page1",
        created_provenance=SimpleNamespace(
            timestamp="2026-10-14T14:00:00+00:00"
        ),
    )
    graph = SimpleNamespace(scan_references=(older, newer))
    monkeypatch.setattr(
        history, "safe_module_work_descendant", lambda *_a: base
    )
    monkeypatch.setattr(
        history, "_assert_no_link_like_ancestors", lambda *_a, **_kw: None
    )
    monkeypatch.setattr(history, "work_root", lambda *_a: tmp_path)
    monkeypatch.setattr(history, "_select_lineage", lambda *_a: (selected,))
    monkeypatch.setattr(history, "_assembly_id", lambda *_a: name)
    monkeypatch.setattr(history, "_assembly_paths", lambda *_a: (
        base / name / "artifact.pdf", base / name / "manifest.json"
    ))
    monkeypatch.setattr(history, "_load_manifest", lambda *_a: {
        "ordered_pages": [
            {"artifact_page_id": "page1", "scan_reference_id": "older"}
        ],
        "created_provenance": {"timestamp": "2026-10-12T14:15:00+00:00"},
    })
    monkeypatch.setattr(history, "_validate_retained_source", lambda *_a: None)
    monkeypatch.setattr(history, "_verify_existing", lambda **_kw: "validdigest")

    versions = history._existing_versions(
        tmp_path, SimpleNamespace(), artifact, graph, 7
    )
    assert len(versions) == 1
    assert versions[0].selections == (
        AssemblyPageSelection(
            artifact_page_id="page1", scan_reference_id="older"
        ),
    )
    assert versions[0].newer_evidence_status == "newer"


def test_unverified_assembly_entry_is_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import concord.workflows.returned_assembly_versions as history

    base = tmp_path / "assemblies"
    (base / "untrusted-thing").mkdir(parents=True)
    monkeypatch.setattr(
        history, "safe_module_work_descendant", lambda *_a: base
    )
    monkeypatch.setattr(
        history, "_assert_no_link_like_ancestors", lambda *_a, **_kw: None
    )
    monkeypatch.setattr(history, "work_root", lambda *_a: tmp_path)
    with pytest.raises(ArtifactAssemblyIntegrityError):
        history._existing_versions(
            tmp_path, SimpleNamespace(),
            SimpleNamespace(artifact_instance_id="artifact1"),
            SimpleNamespace(scan_references=()), 7
        )
