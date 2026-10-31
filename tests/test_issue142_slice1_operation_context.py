"""#142 Slice 1: Core-owned operation context, not synthetic student return proof."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from issue140_slice2_fixtures import (
    ACTIVITY_ID,
    ACTOR,
    SOURCE_CLASS,
    TARGET_CLASS,
    build_workspace,
)
from pds_core.routing_models import ModuleWorkRef
from pds_core.standards import (
    StandardsLibrary,
    write_workspace_standards_library,
)

import concord.menu_artifact_write_context as subject
from concord.storage import list_work_snapshots
from concord.workflows import UpdateActivityRequest, show_activity, update_activity


def _work() -> ModuleWorkRef:
    return ModuleWorkRef("concord", SOURCE_CLASS, ACTIVITY_ID)


def _setup(tmp_path: Path, orientation: str) -> tuple[Path, Any, Any]:
    fixture = build_workspace(tmp_path, orientation=orientation)
    selection = show_activity(
        SOURCE_CLASS, ACTIVITY_ID, workspace_root=fixture.root
    ).summary
    return fixture.root, selection, fixture


def _begin(selection: Any, root: Path, **kwargs: Any) -> subject.ArtifactWriteContext:
    return subject.begin_artifact_write_context(
        selection, workspace_root=root, operation="Artifact Author", **kwargs
    )


@pytest.mark.parametrize("orientation", ("evidence_only", "local_criteria_only"))
def test_neutral_graph_needs_no_core_standards(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, orientation: str
) -> None:
    root, selection, _ = _setup(tmp_path, orientation)
    before = list_work_snapshots(root, _work())
    monkeypatch.setattr(
        subject,
        "load_menu_standards_library",
        lambda *a, **k: pytest.fail("Neutral operation consulted Standards"),
    )
    preview = _begin(selection, root)
    assert not preview.standards_required
    assert preview.standards_library is None
    checked = subject.revalidate_artifact_write_context(
        preview,
        operation="Artifact Author",
        expected_snapshot_revision=selection.snapshot_revision,
    )
    assert subject.artifact_write_kwargs(checked) == {"workspace_root": root.resolve()}
    assert list_work_snapshots(root, _work()) == before


@pytest.mark.parametrize("orientation", ("mixed", "standards_based"))
def test_required_core_library_is_pinned_and_forwarded(
    tmp_path: Path, orientation: str
) -> None:
    root, selection, fixture = _setup(tmp_path, orientation)
    write_workspace_standards_library(root, fixture.standards)
    before = list_work_snapshots(root, _work())
    preview = _begin(selection, root)
    assert preview.standards_required
    assert preview.standards_library == fixture.standards
    checked = subject.revalidate_artifact_write_context(
        preview,
        operation="Artifact Author",
        expected_snapshot_revision=preview.snapshot_revision,
    )
    assert subject.artifact_write_kwargs(checked) == {
        "workspace_root": root.resolve(),
        "standards_library": fixture.standards,
    }
    assert list_work_snapshots(root, _work()) == before


def test_missing_core_library_fails_without_concord_mutation(tmp_path: Path) -> None:
    root, selection, _ = _setup(tmp_path, "mixed")
    before = list_work_snapshots(root, _work())
    with pytest.raises(Exception, match="Core Standards Library is missing"):
        _begin(selection, root)
    assert list_work_snapshots(root, _work()) == before


def test_wrong_selected_class_is_rejected_without_mutation(tmp_path: Path) -> None:
    root, selection, fixture = _setup(tmp_path, "mixed")
    write_workspace_standards_library(root, fixture.standards)
    before = list_work_snapshots(root, _work())
    with pytest.raises(Exception, match="Class|Activity|snapshot"):
        _begin(replace(selection, class_id=TARGET_CLASS), root)
    assert list_work_snapshots(root, _work()) == before


def test_stale_selection_is_rejected_without_mutation(tmp_path: Path) -> None:
    root, selection, fixture = _setup(tmp_path, "mixed")
    write_workspace_standards_library(root, fixture.standards)
    before = list_work_snapshots(root, _work())
    with pytest.raises(Exception, match="snapshot has changed"):
        _begin(
            replace(selection, snapshot_revision=selection.snapshot_revision + 1), root
        )
    assert list_work_snapshots(root, _work()) == before


def test_request_revision_must_match_preview(tmp_path: Path) -> None:
    root, selection, fixture = _setup(tmp_path, "mixed")
    write_workspace_standards_library(root, fixture.standards)
    preview = _begin(selection, root)
    before = list_work_snapshots(root, _work())
    with pytest.raises(Exception, match="different revision"):
        subject.revalidate_artifact_write_context(
            preview,
            operation="Artifact Subject",
            expected_snapshot_revision=preview.snapshot_revision + 1,
        )
    assert list_work_snapshots(root, _work()) == before


def test_active_workspace_switch_after_preview_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, selection, fixture = _setup(tmp_path / "source", "mixed")
    other, _, _ = _setup(tmp_path / "other", "evidence_only")
    write_workspace_standards_library(root, fixture.standards)
    selected_active = {"root": root}

    def active_root(explicit_root: Path | None = None) -> Path:
        return selected_active["root"] if explicit_root is None else explicit_root

    monkeypatch.setattr(subject, "resolve_read_workspace_root", active_root)
    preview = subject.begin_artifact_write_context(
        selection, operation="Artifact Review"
    )
    before = list_work_snapshots(root, _work())
    selected_active["root"] = other
    with pytest.raises(Exception, match="active Core workspace has changed"):
        subject.revalidate_artifact_write_context(
            preview,
            operation="Artifact Review",
            expected_snapshot_revision=preview.snapshot_revision,
        )
    assert list_work_snapshots(root, _work()) == before


def test_invalid_profile_since_preview_refused_with_no_concord_write(
    tmp_path: Path,
) -> None:
    root, selection, fixture = _setup(tmp_path, "mixed")
    write_workspace_standards_library(root, fixture.standards)
    preview = _begin(selection, root)
    before = list_work_snapshots(root, _work())
    write_workspace_standards_library(
        root,
        StandardsLibrary(standards=fixture.standards.standards, profiles=()),
        overwrite=True,
    )
    with pytest.raises(
        Exception, match="Core Standards profile or Focus IDs are invalid"
    ):
        subject.revalidate_artifact_write_context(
            preview,
            operation="Artifact Author",
            expected_snapshot_revision=preview.snapshot_revision,
        )
    assert list_work_snapshots(root, _work()) == before


def test_inactive_focus_is_refused_without_concord_write(tmp_path: Path) -> None:
    root, selection, fixture = _setup(tmp_path, "mixed")
    write_workspace_standards_library(
        root,
        StandardsLibrary(
            standards=(replace(fixture.standards.standards[0], active=False),),
            profiles=fixture.standards.profiles,
        ),
    )
    before = list_work_snapshots(root, _work())
    with pytest.raises(
        Exception, match="Core Standards profile or Focus IDs are invalid"
    ):
        _begin(selection, root)
    assert list_work_snapshots(root, _work()) == before


def test_standard_backed_candidate_requires_focus_even_in_neutral_mode(
    tmp_path: Path,
) -> None:
    root, selection, fixture = _setup(tmp_path, "evidence_only")
    write_workspace_standards_library(root, fixture.standards)
    before = list_work_snapshots(root, _work())
    with pytest.raises(Exception, match="lacks an Activity profile or Focus Standards"):
        _begin(selection, root, candidate_standard_backed=True)
    assert list_work_snapshots(root, _work()) == before


def test_history_requirement_classifies_beyond_orientation(
    tmp_path: Path
) -> None:
    """Classification-only unit test; DOES NOT claim neutral-backed graph is valid."""
    root, selection, fixture = _setup(tmp_path, "evidence_only")
    context = subject.load_activity_read_context(
        root, ModuleWorkRef("concord", SOURCE_CLASS, ACTIVITY_ID)
    )
    # The real graph is legally neutral. This projection-only stub verifies the
    # boolean classifier; it is never fed to storage or treated as evidence.
    graph = SimpleNamespace(
        criteria=(SimpleNamespace(criterion_kind="standard_backed"),),
        score_records=(),
    )
    simulated = SimpleNamespace(activity=context.activity, graph=graph)
    assert subject._needs_standards(
        simulated, candidate_standard_backed=False  # type: ignore[arg-type]
    )
    assert list_work_snapshots(root, _work())


def test_canonical_standards_load_exception_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, selection, _ = _setup(tmp_path, "mixed")
    before = list_work_snapshots(root, _work())

    def unavailable(_root: Path) -> None:
        raise OSError("synthetic read failure")

    monkeypatch.setattr(subject, "load_menu_standards_library", unavailable)
    with pytest.raises(Exception, match="cannot be read"):
        _begin(selection, root)
    assert list_work_snapshots(root, _work()) == before


def test_actual_changed_snapshot_after_preview_is_rejected(tmp_path: Path) -> None:
    root, selection, fixture = _setup(tmp_path, "mixed")
    write_workspace_standards_library(root, fixture.standards)
    preview = _begin(selection, root)
    mutation = update_activity(
        UpdateActivityRequest(
            class_id=SOURCE_CLASS,
            activity_id=ACTIVITY_ID,
            expected_snapshot_revision=selection.snapshot_revision,
            actor=ACTOR,
            status="configured",
        ),
        workspace_root=root,
        standards_library=fixture.standards,
    )
    before = list_work_snapshots(root, _work())
    assert mutation.commit.snapshot_revision > preview.snapshot_revision
    with pytest.raises(Exception, match="snapshot changed after preview"):
        subject.revalidate_artifact_write_context(
            preview,
            operation="Artifact Author",
            expected_snapshot_revision=preview.snapshot_revision,
        )
    assert list_work_snapshots(root, _work()) == before


def test_group_plan_only_error_suffix_not_leaked_to_other_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import concord.menu_standards_context as legacy

    _root, selection, _ = _setup(tmp_path, "mixed")
    monkeypatch.setattr(legacy, "load_menu_standards_library", lambda: None)
    with pytest.raises(Exception) as caught:
        legacy.standards_for_activity(selection)
    assert "No GroupPlan" not in str(caught.value)
    assert "No changes were saved" in str(caught.value)
