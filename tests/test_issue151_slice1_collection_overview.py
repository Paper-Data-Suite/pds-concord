"""#151 Slice 1: read-only, one-snapshot teacher collection overview.

Synthetic in-memory graph only; never scan real paper or alter teacher data.
The three Slice 0 strict xfails remain owned by later repair slices.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import concord.menu_artifact as artifact_menu
import concord.workflows.teacher_collection_overview as overview
from concord.menu_context import MenuSessionContext
from concord.workflows.artifact_assembly import ArtifactAssemblyIntegrityError
from concord.workflows.errors import ConcordWorkflowConflictError
from concord.workflows.models import ActivitySummary


def _graph(
    *,
    returned: tuple[str, ...] = (),
    nonreturn: bool = False,
    copies: int = 1,
    contradictory_route: bool = False,
    missing_page: bool = False,
) -> SimpleNamespace:
    artifacts = tuple(
        SimpleNamespace(
            artifact_instance_id=f"artifact-{index}",
            activity_id="activity-a",
            artifact_category="observation" if nonreturn else "student_work",
            generation_status="completed",
            expected_return_status=(
                "return_not_expected" if nonreturn else "returned_expected"
            ),
            artifact_status="generated",
            template_version_id="template-secret",
            group_id="cluster-a",
            session_id="session-a",
            page_ids=(f"page-{index}-1", f"page-{index}-2"),
        )
        for index in range(1, copies + 1)
    )
    pages = tuple(
        SimpleNamespace(
            artifact_page_id=f"page-{index}-{number}",
            artifact_instance_id=f"artifact-{index}",
            return_expected=not nonreturn,
            route_id=(None if nonreturn else f"route-{index}-{number}"),
            page_status="returned",  # Status is not proof of routing.
        )
        for index in range(1, copies + 1)
        for number in (1, 2)
        if not (missing_page and number == 2)
    )
    scans = tuple(
        SimpleNamespace(
            scan_reference_id=f"scan-secret-{index}",
            artifact_page_id=page_id,
            activity_id="activity-a",
            route_id=(
                "route-forged"
                if contradictory_route
                else page_id.replace("page", "route")
            ),
            retained_source_relative_path="private-scan-secret.pdf",
            source_sha256="a" * 64,
        )
        for index, page_id in enumerate(returned, start=1)
    )
    return SimpleNamespace(
        artifact_instances=artifacts,
        artifact_pages=pages,
        scan_references=scans,
        artifact_authors=(
            SimpleNamespace(
                artifact_author_id="author-secret",
                artifact_instance_id="artifact-1",
                attribution_status="proposed",
                supersedes_artifact_author_id=None,
            ),
        ),
        artifact_subjects=(
            SimpleNamespace(
                artifact_subject_id="subject-secret",
                artifact_instance_id="artifact-1",
                confirmation_status="disputed",
                supersedes_artifact_subject_id=None,
            ),
        ),
        groups=(SimpleNamespace(group_id="cluster-a", label="Cluster A"),),
        sessions=(SimpleNamespace(session_id="session-a", sequence=1, label="Debate"),),
    )


def _inspect(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    graph: SimpleNamespace,
    *,
    assembly: str = "ready",
    snapshot: int = 12,
    expected_snapshot: int | None = None,
) -> tuple[overview.TeacherCollectionOverview, dict[str, int]]:
    calls = {"load": 0, "assembly": 0, "class": 0}
    monkeypatch.setattr(overview, "resolve_read_workspace_root", lambda _r: tmp_path)

    def core_class(*_args: object) -> None:
        calls["class"] += 1

    def read(*_args: object) -> SimpleNamespace:
        calls["load"] += 1
        return SimpleNamespace(
            graph=graph, snapshot_revision=snapshot, snapshot_sha256="a" * 64
        )

    def assembly_state(*_args: object) -> str:
        calls["assembly"] += 1
        return assembly

    monkeypatch.setattr(overview, "require_core_class", core_class)
    monkeypatch.setattr(overview, "load_activity_read_context", read)
    monkeypatch.setattr(overview, "_assembly_state", assembly_state)
    projected = overview.inspect_teacher_collection_overview(
        "class-a",
        "activity-a",
        workspace_root=tmp_path,
        expected_snapshot_revision=expected_snapshot,
    )
    return projected, calls


def test_generated_page_status_is_not_a_routed_return(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    projected, calls = _inspect(monkeypatch, tmp_path, _graph())
    item = projected.items[0]
    assert projected.print_distribution_state == "not_tracked"
    assert item.stage == "awaiting_return"
    assert item.required_return_pages == 2
    assert item.routed_return_pages == 0
    assert item.routed_occurrences == 0
    assert item.pending_author_count == 1
    assert item.pending_subject_count == 1
    assert "no routed returned evidence" in item.attribution_note
    assert calls == {"load": 1, "assembly": 0, "class": 1}


def test_partial_return_counts_unique_pages_not_occurrence_count(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    projected, calls = _inspect(
        monkeypatch,
        tmp_path,
        _graph(returned=("page-1-1", "page-1-1")),
    )
    item = projected.items[0]
    assert item.stage == "partially_returned"
    assert item.routed_return_pages == 1
    assert item.routed_occurrences == 2
    assert "incomplete" in item.attribution_note
    assert calls["assembly"] == 0


@pytest.mark.parametrize(
    ("assembly", "expected"),
    (
        ("ready", "ready_to_assemble"),
        ("selection_required", "choose_occurrences"),
        ("assembled", "assembled"),
        ("needs_recovery", "needs_recovery"),
        ("not_ready", "needs_recovery"),
    ),
)
def test_complete_routed_pages_reuse_authoritative_assembly_state(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    assembly: str,
    expected: str,
) -> None:
    projected, calls = _inspect(
        monkeypatch,
        tmp_path,
        _graph(returned=("page-1-1", "page-1-2")),
        assembly=assembly,
    )
    assert projected.items[0].stage == expected
    assert projected.items[0].routed_return_pages == 2
    assert calls == {"load": 1, "assembly": 1, "class": 1}


def test_non_return_observation_is_not_forced_through_paper_scan(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    projected, calls = _inspect(monkeypatch, tmp_path, _graph(nonreturn=True))
    item = projected.items[0]
    assert item.stage == "not_return_expected"
    assert item.required_return_pages == 0
    assert item.pending_author_count == 1
    assert "no routed returned evidence" not in item.attribution_note
    assert calls["assembly"] == 0


def test_duplicate_cluster_and_session_labels_disambiguate_without_ids(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    projected, calls = _inspect(monkeypatch, tmp_path, _graph(copies=3))
    labels = tuple(item.label for item in projected.items)
    assert len(labels) == len(set(labels)) == 3
    assert "work 1 of 3" in labels[0]
    assert "work 3 of 3" in labels[-1]
    assert all("artifact-" not in label for label in labels)
    assert calls == {"load": 1, "assembly": 0, "class": 1}


def test_mismatched_canonical_route_fails_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    with pytest.raises(ArtifactAssemblyIntegrityError, match="contradicts"):
        _inspect(
            monkeypatch,
            tmp_path,
            _graph(returned=("page-1-1",), contradictory_route=True),
        )


def test_missing_canonical_artifact_page_fails_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    with pytest.raises(ArtifactAssemblyIntegrityError, match="identity"):
        _inspect(monkeypatch, tmp_path, _graph(missing_page=True))


def test_stale_snapshot_refuses_before_deriving_any_work(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    with pytest.raises(ConcordWorkflowConflictError, match="Refresh"):
        _inspect(monkeypatch, tmp_path, _graph(), expected_snapshot=11)


def test_empty_activity_is_readable_without_mutation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    graph = _graph()
    graph.artifact_instances = ()
    graph.artifact_authors = ()
    graph.artifact_subjects = ()
    projected, calls = _inspect(monkeypatch, tmp_path, graph)
    assert projected.items == ()
    assert calls == {"load": 1, "assembly": 0, "class": 1}


def test_collect_status_shortcut_uses_read_only_projection_and_back(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    activity = ActivitySummary(
        class_id="class-a",
        activity_id="activity-a",
        title="Synthetic Debate",
        status="active",
        scoring_orientation="mixed",
        session_count=1,
        group_count=1,
        snapshot_revision=12,
    )
    item = overview.CollectionWorkItem(
        artifact_instance_id="artifact-secret",
        label="Cluster A | Session 1 - Debate",
        group_label="Cluster A",
        session_label="Session 1 - Debate",
        stage="awaiting_return",
        required_return_pages=2,
        routed_return_pages=0,
        routed_occurrences=0,
        pending_author_count=1,
        pending_subject_count=0,
        confirmed_author_count=0,
        confirmed_subject_count=0,
    )
    captured: list[tuple[str, tuple[str, ...]]] = []
    selected: list[tuple[str, ...]] = []
    monkeypatch.setattr(artifact_menu, "clear_screen", lambda: None)
    monkeypatch.setattr(artifact_menu, "_latest", lambda a: a)
    monkeypatch.setattr(
        artifact_menu,
        "inspect_teacher_collection_overview",
        lambda *_a, **_k: SimpleNamespace(items=(item,)),
    )

    def choose(
        _title: str,
        _items: object,
        labels: tuple[str, ...],
        **_k: object,
    ) -> object:
        selected.append(labels)
        return item

    monkeypatch.setattr(artifact_menu, "select_one", choose)
    monkeypatch.setattr(
        artifact_menu,
        "show_result",
        lambda title, lines: captured.append((title, tuple(lines))),
    )
    monkeypatch.setattr(
        artifact_menu,
        "_assemble",
        lambda *_a: pytest.fail("A read-only choice must not assemble"),
    )
    answers = iter(("s", "b"))
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    artifact_menu.launch_collect_work_menu(activity, MenuSessionContext())
    assert len(selected) == 1
    assert len(captured) == 1
    rendered = " ".join(captured[0][1]).casefold()
    assert "not tracked" in rendered
    assert "routed" in rendered
    assert "no routed returned evidence" in rendered
    assert "artifact-secret" not in rendered
    assert "sha256" not in rendered
    assert "collection status" in capsys.readouterr().out.casefold()
