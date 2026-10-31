"""#142 Slice 4A: first detailed Review/Moderation with canonical Core context.

Fabricated observations only; a prepared Artifact is never described as returned,
assembled, reviewed evidence or a scored student performance. All writes are tmp_path.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from issue140_slice2_fixtures import (
    ACTIVITY_ID,
    ACTOR,
    SOURCE_CLASS,
    build_workspace,
)
from pds_core.routing_models import ModuleWorkRef
from pds_core.standards import (
    load_workspace_standards_library,
    write_workspace_standards_library,
)

import concord.menu_artifact as menu
import concord.menu_artifact_write_context as authority
from concord.models import PrivacyPolicy
from concord.storage import list_work_snapshots, load_current_record_graph
from concord.workflows import show_activity
from concord.workflows.artifact_page import (
    ArtifactPagePlan,
    PrepareArtifactPagesRequest,
    prepare_artifact_pages,
)

ARTIFACT_ID = "issue142-synthetic-unreturned-observation"
REVIEW_ID = "issue142-synthetic-administrative-review"
MODERATION_ID = "issue142-synthetic-not-for-scoring-moderation"


def _work() -> ModuleWorkRef:
    return ModuleWorkRef("concord", SOURCE_CLASS, ACTIVITY_ID)


def _standards(root: Path, orientation: str) -> Any:
    if orientation in {"mixed", "standards_based"}:
        return load_workspace_standards_library(root)
    return None


def _graph(root: Path, orientation: str) -> Any:
    return load_current_record_graph(
        root, _work(), standards_library=_standards(root, orientation)
    ).graph


def _activity(root: Path) -> Any:
    return show_activity(
        SOURCE_CLASS, ACTIVITY_ID, workspace_root=root
    ).summary


def _fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    orientation: str,
) -> Path:
    fixture = build_workspace(tmp_path, orientation=orientation)
    root = fixture.root
    if orientation in {"mixed", "standards_based"}:
        write_workspace_standards_library(root, fixture.standards)
    prepare_artifact_pages(
        PrepareArtifactPagesRequest(
            class_id=SOURCE_CLASS,
            activity_id=ACTIVITY_ID,
            artifact_instance_id=ARTIFACT_ID,
            template_version_id="issue142-synthetic-paper-template",
            artifact_category="observation",
            expected_snapshot_revision=_activity(root).snapshot_revision,
            actor=ACTOR,
            expected_return_status="return_not_expected",
            privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
            pages=(
                ArtifactPagePlan(
                    page_number=1,
                    return_expected=False,
                    route_required=False,
                ),
            ),
        ),
        workspace_root=root,
        standards_library=_standards(root, orientation),
    )
    monkeypatch.setattr(
        authority,
        "resolve_read_workspace_root",
        lambda explicit=None: root if explicit is None else Path(explicit),
    )
    monkeypatch.setattr(
        menu,
        "_latest",
        lambda activity: show_activity(
            activity.class_id,
            activity.activity_id,
            workspace_root=root,
        ).summary,
    )
    monkeypatch.setattr(menu, "select_one", lambda title, items, labels, **kw: items[0])
    monkeypatch.setattr(menu, "show_result", lambda *a, **kw: None)
    monkeypatch.setattr(menu, "confirm_write", lambda *a, **kw: True)
    monkeypatch.setattr(
        menu,
        "prompt_text",
        lambda title, label, **kw: {
            "Artifact Review ID": REVIEW_ID,
            "Moderation Record ID": MODERATION_ID,
        }.get(label, "Synthetic administrative observation"),
    )
    monkeypatch.setattr(
        menu,
        "_review_values",
        lambda: (
            "not_reviewed",
            "incomplete",
            "not_reviewed",
            "not_reviewed",
            "not_reviewed",
            "teacher_restricted",
            "not_reviewed",
            "not_required",
            "not_ready",
            "awaiting_additional_evidence",
            "Prepared observation, not returned student evidence",
            PrivacyPolicy(classification="teacher_restricted"),
        ),
    )
    monkeypatch.setattr(
        menu,
        "_moderation_values",
        lambda: (
            "not_used_for_scoring",
            "not_be_used_for_scoring",
            "Unreturned synthetic observation must not support scoring",
            None,
            PrivacyPolicy(classification="teacher_restricted"),
        ),
    )
    return root


def _invoke(kind: str, root: Path) -> None:
    handler = (
        menu._record_review if kind == "review" else menu._record_moderation
    )
    handler(_activity(root), menu.MenuSessionContext(actor=ACTOR))


@pytest.mark.parametrize("kind", ("review", "moderation"))
@pytest.mark.parametrize(
    "orientation", ("mixed", "standards_based", "evidence_only", "local_criteria_only")
)
def test_first_menu_write_records_only_explicit_administrative_judgment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
    orientation: str,
) -> None:
    root = _fixture(tmp_path, monkeypatch, orientation)
    before = list_work_snapshots(root, _work())
    _invoke(kind, root)
    assert len(list_work_snapshots(root, _work())) == len(before) + 1
    graph = _graph(root, orientation)
    assert graph.artifact_instances[0].expected_return_status == "return_not_expected"
    assert graph.scan_references == ()
    assert graph.score_records == ()
    assert graph.score_evidence_links == ()
    if kind == "review":
        assert len(graph.artifact_reviews) == 1
        assert graph.artifact_reviews[0].scoring_readiness == "not_ready"
        assert (
            graph.artifact_reviews[0].review_outcome == "awaiting_additional_evidence"
        )
        assert graph.moderation_records == ()
    else:
        assert len(graph.moderation_records) == 1
        assert graph.moderation_records[0].status == "not_used_for_scoring"
        assert graph.moderation_records[0].permitted_use == "not_be_used_for_scoring"
        assert graph.artifact_reviews == ()


@pytest.mark.parametrize("kind", ("review", "moderation"))
def test_teacher_cancellation_is_exact_no_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
) -> None:
    root = _fixture(tmp_path, monkeypatch, "mixed")
    before = list_work_snapshots(root, _work())
    monkeypatch.setattr(menu, "confirm_write", lambda *a, **kw: False)
    _invoke(kind, root)
    assert list_work_snapshots(root, _work()) == before


@pytest.mark.parametrize("kind", ("review", "moderation"))
def test_workspace_switch_after_confirmation_rejects_original_and_foreign(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
) -> None:
    root = _fixture(tmp_path, monkeypatch, "mixed")
    foreign = build_workspace(tmp_path / "foreign", orientation="mixed")
    original = list_work_snapshots(root, _work())
    foreign_before = list_work_snapshots(foreign.root, _work())

    def switch(*a: Any, **kw: Any) -> bool:
        monkeypatch.setattr(
            authority,
            "resolve_read_workspace_root",
            lambda explicit=None: (
                foreign.root if explicit is None else Path(explicit)
            ),
        )
        return True

    monkeypatch.setattr(menu, "confirm_write", switch)
    with pytest.raises(Exception, match="workspace has changed"):
        _invoke(kind, root)
    assert list_work_snapshots(root, _work()) == original
    assert list_work_snapshots(foreign.root, _work()) == foreign_before


@pytest.mark.parametrize("kind", ("review", "moderation"))
def test_repeated_identity_is_not_created_a_second_time(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
) -> None:
    root = _fixture(tmp_path, monkeypatch, "mixed")
    _invoke(kind, root)
    before = list_work_snapshots(root, _work())
    with pytest.raises(Exception):
        _invoke(kind, root)
    assert list_work_snapshots(root, _work()) == before
