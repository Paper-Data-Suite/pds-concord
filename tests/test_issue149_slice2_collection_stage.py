"""#149 Slice 2: evidence-backed returned-work/attribution stage projections.

Synthetic provenance references only; no actual teacher files or returned scans.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import concord.workflows.activity_attention as attention
import concord.workflows.artifact_collection as collection
from concord.workflows.artifact_assembly import ArtifactAssemblyIntegrityError


def _artifact(
    status: str = "generated", *, page_ids: tuple[str, ...] = ("page-1", "page-2")
) -> SimpleNamespace:
    return SimpleNamespace(
        artifact_instance_id="artifact-synthetic",
        activity_id="activity-synthetic",
        artifact_status=status,
        generation_status="completed",
        expected_return_status="returned_expected",
        page_ids=page_ids,
    )


def _page(
    page_id: str, *, route: str = "route-synthetic", returned: bool = False
) -> SimpleNamespace:
    return SimpleNamespace(
        artifact_page_id=page_id,
        artifact_instance_id="artifact-synthetic",
        route_id=route,
        return_expected=True,
        page_status="returned" if returned else "generated",
    )


def _scan(
    *,
    route: str = "route-synthetic",
    activity: str = "activity-synthetic",
    page: str = "page-1",
) -> SimpleNamespace:
    return SimpleNamespace(
        scan_reference_id="scan-reference-synthetic",
        activity_id=activity,
        artifact_page_id=page,
        route_id=route,
        retained_source_relative_path="scans/source/2026-11-16/example.pdf",
        retained_source_sha256="a" * 64,
    )


def _graph(
    artifact: SimpleNamespace,
    *,
    scans: tuple[object, ...] = (),
    pages: tuple[object, ...] | None = None,
    authors: tuple[object, ...] | None = None,
    subjects: tuple[object, ...] | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        artifact_instances=(artifact,),
        artifact_pages=pages
        if pages is not None
        else (_page("page-1"), _page("page-2")),
        scan_references=scans,
        artifact_authors=authors if authors is not None else (_author(),),
        artifact_subjects=subjects if subjects is not None else (_subject(),),
        artifact_reviews=(),
        group_plans=(),
        packet_instances=(),
        moderation_records=(),
    )


def _author(
    *,
    status: str = "proposed",
    identifier: str = "author-current",
    supersedes: str | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        artifact_author_id=identifier,
        artifact_instance_id="artifact-synthetic",
        attribution_status=status,
        supersedes_artifact_author_id=supersedes,
    )


def _subject(
    *,
    status: str = "disputed",
    identifier: str = "subject-current",
    supersedes: str | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        artifact_subject_id=identifier,
        artifact_instance_id="artifact-synthetic",
        confirmation_status=status,
        supersedes_artifact_subject_id=supersedes,
    )


def _context(graph: SimpleNamespace, root: Path) -> SimpleNamespace:
    return SimpleNamespace(
        root=root,
        work=SimpleNamespace(class_id="class-synthetic", work_id="activity-synthetic"),
        graph=graph,
        activity=SimpleNamespace(
            activity_id="activity-synthetic",
            status="active",
            scoring_orientation="evidence_only",
        ),
    )


def _inspect_both(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    graph: SimpleNamespace,
    *,
    assembly_state: str,
) -> tuple[collection.ArtifactCollectionState, collection.ArtifactCollectionState]:
    monkeypatch.setattr(collection, "resolve_read_workspace_root", lambda _p: tmp_path)
    monkeypatch.setattr(
        collection, "load_graph", lambda *_a, **_k: (graph, 7, "a" * 64)
    )
    monkeypatch.setattr(
        collection, "list_artifact_authors", lambda *_a, **_k: graph.artifact_authors
    )
    monkeypatch.setattr(
        collection, "list_artifact_subjects", lambda *_a, **_k: graph.artifact_subjects
    )
    monkeypatch.setattr(collection, "_assembly_state", lambda *_a, **_k: assembly_state)
    monkeypatch.setattr(attention, "_assembly_state", lambda *_a, **_k: assembly_state)
    public = collection.inspect_artifact_collection_state(
        "class-synthetic",
        "activity-synthetic",
        "artifact-synthetic",
        workspace_root=tmp_path,
    )
    ctx = _context(graph, tmp_path)
    optimized = attention._collection_state_from_context(
        ctx, attention._build_attention_index(ctx), "artifact-synthetic"
    )
    return public, optimized


@pytest.mark.parametrize(
    "status",
    ("generated", "distributed", "returned", "partially_returned", "completed"),
)
def test_status_without_retained_return_never_proves_association_attention(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, status: str
) -> None:
    """Even a status claiming return cannot replace routed source evidence."""
    graph = _graph(_artifact(status))
    public, optimized = _inspect_both(
        monkeypatch, tmp_path, graph, assembly_state="not_ready"
    )
    assert not public.author_confirmation_pending
    assert not public.subject_confirmation_pending
    assert public == optimized


@pytest.mark.parametrize(
    "stage", ("ready", "selection_required", "assembled", "needs_recovery")
)
def test_verified_assembly_stage_retains_real_confirmation_attention(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, stage: str
) -> None:
    graph = _graph(_artifact("returned"))
    public, optimized = _inspect_both(
        monkeypatch, tmp_path, graph, assembly_state=stage
    )
    assert public.author_confirmation_pending
    assert public.subject_confirmation_pending
    assert public == optimized


def test_partially_routed_return_is_actionable_without_full_assembly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    graph = _graph(
        _artifact("partially_returned"),
        scans=(_scan(),),
        pages=(_page("page-1", returned=True), _page("page-2")),
    )
    public, optimized = _inspect_both(
        monkeypatch, tmp_path, graph, assembly_state="not_ready"
    )
    assert public.author_confirmation_pending
    assert public.subject_confirmation_pending
    assert public.assembly_state == "not_ready"
    assert public == optimized


@pytest.mark.parametrize("mismatch", ("route", "activity"))
def test_contradictory_routed_source_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mismatch: str
) -> None:
    scan = (
        _scan(route="wrong-route")
        if mismatch == "route"
        else _scan(activity="wrong-activity")
    )
    graph = _graph(_artifact(), scans=(scan,))
    with pytest.raises(ArtifactAssemblyIntegrityError, match="contradicts"):
        _inspect_both(monkeypatch, tmp_path, graph, assembly_state="not_ready")


def test_unrelated_scan_or_no_required_return_does_not_create_attention(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    unrelated = _scan(page="other-artifact-page")
    graph = _graph(_artifact(), scans=(unrelated,))
    public, optimized = _inspect_both(
        monkeypatch, tmp_path, graph, assembly_state="not_ready"
    )
    assert not public.author_confirmation_pending
    assert not public.subject_confirmation_pending
    assert public == optimized

    graph = _graph(_artifact(), scans=(_scan(),))
    public, optimized = _inspect_both(
        monkeypatch, tmp_path, graph, assembly_state="not_applicable"
    )
    assert not public.author_confirmation_pending
    assert not public.subject_confirmation_pending
    assert public == optimized


def test_superseded_pending_proposals_do_not_reappear_after_return(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    graph = _graph(
        _artifact("returned"),
        scans=(_scan(),),
        authors=(
            _author(),
            _author(
                status="confirmed", identifier="author-new", supersedes="author-current"
            ),
        ),
        subjects=(
            _subject(),
            _subject(
                status="confirmed",
                identifier="subject-new",
                supersedes="subject-current",
            ),
        ),
    )
    monkeypatch.setattr(attention, "_assembly_state", lambda *_a, **_k: "not_ready")
    context = _context(graph, tmp_path)
    indexed = attention._build_attention_index(context)
    optimized = attention._collection_state_from_context(
        context, indexed, "artifact-synthetic"
    )
    assert not optimized.author_confirmation_pending
    assert not optimized.subject_confirmation_pending


def test_source_ref_does_not_leak_into_attention_summary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    graph = _graph(_artifact("partially_returned"), scans=(_scan(),))
    ctx = _context(graph, tmp_path)
    monkeypatch.setattr(attention, "_assembly_state", lambda *_a, **_k: "not_ready")
    monkeypatch.setattr(
        attention,
        "_share_attention_from_context",
        lambda _ctx: SimpleNamespace(status="inactive"),
    )
    counts = attention._attention_counts_from_context(ctx)
    assert counts == {
        "concord_collect_author_confirmation": 1,
        "concord_collect_subject_confirmation": 1,
    }
    result = attention._items_from_counts(counts)
    assert "scan-reference-synthetic" not in repr(result)
    assert "scans/source" not in repr(result)
    assert "artifact-synthetic" not in repr(result)
