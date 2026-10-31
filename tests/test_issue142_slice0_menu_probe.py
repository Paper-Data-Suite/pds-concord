"""#142 Slice 0: disposable real-target Artifact menu Standards context probes.

These are pre-repair contract witnesses, NOT returned-evidence acceptance.
Every student, workspace, artifact, and menu decision here is synthetic.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from issue140_slice2_fixtures import (
    ACTIVITY_ID,
    ACTOR,
    SOURCE_CLASS,
    build_workspace,
)
from pds_core.routing_models import ModuleWorkRef
from pds_core.standards import write_workspace_standards_library

import concord.menu_artifact as menu
import concord.menu_artifact_write_context as authority
from concord.models import PrivacyPolicy
from concord.storage import list_work_snapshots, load_current_record_graph
from concord.workflows import (
    ArtifactPagePlan,
    PrepareArtifactPagesRequest,
    add_artifact_authors,
    prepare_artifact_pages,
    show_activity,
)

ARTIFACT_ID = "issue142-synthetic-planned-artifact"


def _work() -> ModuleWorkRef:
    return ModuleWorkRef("concord", SOURCE_CLASS, ACTIVITY_ID)


def _prepared_workspace(tmp_path: Path, orientation: str) -> Any:
    fixture = build_workspace(tmp_path, orientation=orientation)
    if orientation in {"standards_based", "mixed"}:
        # This is the REAL disposable Core workspace library, not a menu stub.
        write_workspace_standards_library(fixture.root, fixture.standards)
    initial = show_activity(
        SOURCE_CLASS, ACTIVITY_ID, workspace_root=fixture.root
    ).summary
    prepared = prepare_artifact_pages(
        PrepareArtifactPagesRequest(
            class_id=SOURCE_CLASS,
            activity_id=ACTIVITY_ID,
            artifact_instance_id=ARTIFACT_ID,
            template_version_id="issue142-synthetic-template",
            artifact_category="observation",
            expected_snapshot_revision=initial.snapshot_revision,
            actor=ACTOR,
            expected_return_status="return_not_expected",
            privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
            pages=(
                ArtifactPagePlan(
                    page_number=1,
                    page_kind="observation",
                    return_expected=False,
                    route_required=False,
                ),
            ),
        ),
        workspace_root=fixture.root,
        standards_library=(
            fixture.standards
            if orientation in {"mixed", "standards_based"}
            else None
        ),
    )
    assert prepared.artifact_instance_id == ARTIFACT_ID
    return fixture


def _exercise_menu(
    monkeypatch: pytest.MonkeyPatch,
    fixture: Any,
    *,
    approve: bool,
) -> tuple[list[Any], list[dict[str, object]]]:
    """Invoke actual teacher handler and the real service, pinning only test I/O.

    No mocked workflow/storage validation. Captured kwargs show precisely what
    the real menu forwarded BEFORE this fixture supplies the test workspace.
    """
    root = fixture.root
    current = show_activity(SOURCE_CLASS, ACTIVITY_ID, workspace_root=root).summary
    selected = SimpleNamespace(
        artifact_instance_id=ARTIFACT_ID,
        artifact_status="planned",
        snapshot_revision=current.snapshot_revision,
    )
    requests: list[Any] = []
    forwarded: list[dict[str, object]] = []

    monkeypatch.setattr(
        authority,
        "resolve_read_workspace_root",
        lambda explicit=None: root if explicit is None else Path(explicit),
    )
    monkeypatch.setattr(menu, "_latest", lambda _: current)
    monkeypatch.setattr(menu, "_choose_artifact", lambda *a, **kw: selected)
    monkeypatch.setattr(menu, "_require_workspace", lambda: root)
    monkeypatch.setattr(
        menu,
        "choose_students",
        lambda selected_root, class_id: (
            SimpleNamespace(student_id=fixture.source.students[0]),
            SimpleNamespace(student_id=fixture.source.students[1]),
        ),
    )
    monkeypatch.setattr(menu, "_routine_multi_author_mode", lambda: "individual_author")
    monkeypatch.setattr(menu, "_routine_add_status", lambda **kw: "proposed")
    monkeypatch.setattr(menu, "confirm_write", lambda *a, **kw: approve)
    monkeypatch.setattr(menu, "show_result", lambda *a, **kw: None)

    def real_write(request: Any, **kwargs: object) -> Any:
        requests.append(request)
        forwarded.append(dict(kwargs))
        kwargs.setdefault("workspace_root", root)
        return add_artifact_authors(request, **kwargs)

    monkeypatch.setattr(menu, "add_artifact_authors", real_write)
    menu._add_multiple_authors(current, menu.MenuSessionContext(actor=ACTOR))
    return requests, forwarded


@pytest.mark.parametrize("orientation", ("mixed", "standards_based"))
def test_repaired_menu_forwards_required_context_on_existing_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, orientation: str
) -> None:
    """Successor witness: same real synthetic menu now forwards canonical authority.

    The original pre-repair missing-Standards witness remains in the frozen
    Slice 0 source-only archive; no original source evidence was overwritten.
    """
    fixture = _prepared_workspace(tmp_path, orientation)
    before = list_work_snapshots(fixture.root, _work())
    requests, forwarded = _exercise_menu(monkeypatch, fixture, approve=True)
    assert len(requests) == 1
    assert len(forwarded) == 1
    assert forwarded[0] == {
        "workspace_root": fixture.root.resolve(),
        "standards_library": fixture.standards,
    }
    assert list_work_snapshots(fixture.root, _work()) == (
        *before,
        before[-1] + 1,
    )
    graph = load_current_record_graph(
        fixture.root, _work(), standards_library=fixture.standards
    ).graph
    assert len(graph.artifact_authors) == 2
    assert all(a.attribution_status == "proposed" for a in graph.artifact_authors)
    assert all(p.page_status == "planned" for p in graph.artifact_pages)


@pytest.mark.parametrize("orientation", ("evidence_only", "local_criteria_only"))
def test_neutral_existing_artifact_menu_does_not_need_core_standards(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, orientation: str
) -> None:
    fixture = _prepared_workspace(tmp_path, orientation)
    before = list_work_snapshots(fixture.root, _work())
    requests, forwarded = _exercise_menu(monkeypatch, fixture, approve=True)
    assert len(requests) == 1
    assert forwarded == [{"workspace_root": fixture.root.resolve()}]
    assert list_work_snapshots(fixture.root, _work()) == (*before, before[-1] + 1)
    graph = load_current_record_graph(fixture.root, _work()).graph
    assert len(graph.artifact_authors) == 2
    assert all(
        author.attribution_status == "proposed" for author in graph.artifact_authors
    )


@pytest.mark.parametrize("orientation", ("mixed", "evidence_only"))
def test_cancelled_menu_makes_no_write_or_service_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, orientation: str
) -> None:
    fixture = _prepared_workspace(tmp_path, orientation)
    before = list_work_snapshots(fixture.root, _work())
    requests, forwarded = _exercise_menu(monkeypatch, fixture, approve=False)
    assert requests == []
    assert forwarded == []
    assert list_work_snapshots(fixture.root, _work()) == before
