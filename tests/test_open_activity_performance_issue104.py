from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.standards import (
    StandardDefinition,
    StandardsLibrary,
    StandardsProfile,
)
from pds_core.workspace import ensure_workspace_root

import concord.menu_activity as menu_activity
import concord.storage as storage_module
from concord.models import PrivacyPolicy
from concord.storage_errors import ConcordStorageIntegrityError
from concord.storage_paths import snapshot_path
from concord.workflows import (
    ActivitySummary,
    ArtifactPagePlan,
    CreateActivityContextRequest,
    PrepareArtifactPagesRequest,
    UpdateActivityRequest,
    WorkflowActor,
    create_activity_context,
    prepare_artifact_pages,
    update_activity,
)
from concord.workflows.activity import show_activity
from concord.workflows.activity_attention import inspect_activity_attention


def _clock(hour: int) -> datetime:
    return datetime(2026, 9, 22, hour, 0, tzinfo=timezone.utc)


def _actor() -> WorkflowActor:
    return WorkflowActor(
        actor_id="teacher-1",
        display_label="Synthetic Teacher",
        role_label="teacher",
    )


def _privacy() -> PrivacyPolicy:
    return PrivacyPolicy(classification="teacher_restricted")


def _workspace(
    tmp_path: Path,
    *,
    artifact_count: int = 0,
    scoring_orientation: str = "evidence_only",
    standards_library: StandardsLibrary | None = None,
) -> tuple[Path, int]:
    root = ensure_workspace_root(tmp_path / "workspace")
    metadata = create_class_metadata(
        "class-1",
        "2026-2027",
        created_at=_clock(8),
    )
    write_class_metadata_for_class(root, metadata)
    created = create_activity_context(
        CreateActivityContextRequest(
            class_id="class-1",
            activity_id="activity-1",
            title="Issue 104 Performance Activity",
            activity_type="project",
            scoring_orientation=scoring_orientation,  # type: ignore[arg-type]
            session_id="session-1",
            actor=_actor(),
            standards_profile_id=(
                "profile-1"
                if scoring_orientation in {"standards_based", "mixed"}
                else None
            ),
            focus_standard_ids=(
                ("standard-1",)
                if scoring_orientation in {"standards_based", "mixed"}
                else ()
            ),
        ),
        workspace_root=root,
        standards_library=standards_library,
        clock=lambda: _clock(9),
    )
    revision = created.commit.snapshot_revision
    for index in range(artifact_count):
        prepared = prepare_artifact_pages(
            PrepareArtifactPagesRequest(
                class_id="class-1",
                activity_id="activity-1",
                artifact_instance_id=f"artifact-{index:03d}",
                template_version_id="template-v1",
                artifact_category="observation",
                expected_snapshot_revision=revision,
                actor=_actor(),
                expected_return_status="return_not_expected",
                privacy_policy=_privacy(),
                session_id="session-1",
                pages=(
                    ArtifactPagePlan(
                        page_number=1,
                        page_kind="observation",
                        return_expected=False,
                        route_required=False,
                    ),
                ),
            ),
            workspace_root=root,
            clock=lambda: _clock(10),
        )
        revision = prepared.commit.snapshot_revision
    return root, revision


def _standards_library() -> StandardsLibrary:
    return StandardsLibrary(
        standards=(
            StandardDefinition(
                standard_id="standard-1",
                code="S1",
                source="synthetic",
                short_name="Standard 1",
                description="Synthetic standard one.",
            ),
        ),
        profiles=(
            StandardsProfile(
                profile_id="profile-1",
                standards=("standard-1",),
                source="synthetic",
                title="Synthetic profile",
            ),
        ),
    )


def _fingerprint(root: Path) -> tuple[tuple[str, int, str], ...]:
    rows: list[tuple[str, int, str]] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        data = path.read_bytes()
        rows.append(
            (
                path.relative_to(root).as_posix(),
                len(data),
                hashlib.sha256(data).hexdigest(),
            )
        )
    return tuple(rows)


def _count_canonical_reads(
    monkeypatch: pytest.MonkeyPatch,
    function: Callable[[], object],
) -> dict[str, int]:
    original_chain = storage_module._load_snapshot_chain
    original_graph = storage_module._validated_snapshot_graph
    original_validate = storage_module.validate_record_graph
    calls = {"chain": 0, "graph": 0, "validate": 0}

    def counted_chain(*args: Any, **kwargs: Any) -> Any:
        calls["chain"] += 1
        return original_chain(*args, **kwargs)

    def counted_graph(*args: Any, **kwargs: Any) -> Any:
        calls["graph"] += 1
        return original_graph(*args, **kwargs)

    def counted_validate(*args: Any, **kwargs: Any) -> Any:
        calls["validate"] += 1
        return original_validate(*args, **kwargs)

    monkeypatch.setattr(storage_module, "_load_snapshot_chain", counted_chain)
    monkeypatch.setattr(storage_module, "_validated_snapshot_graph", counted_graph)
    monkeypatch.setattr(storage_module, "validate_record_graph", counted_validate)
    function()
    return calls


@pytest.mark.parametrize("artifact_count", (1, 20))
def test_attention_graph_loads_remain_constant_with_real_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    artifact_count: int,
) -> None:
    root, _ = _workspace(tmp_path, artifact_count=artifact_count)

    calls = _count_canonical_reads(
        monkeypatch,
        lambda: inspect_activity_attention(
            "class-1",
            "activity-1",
            workspace_root=root,
        ),
    )

    assert calls == {"chain": 1, "graph": 1, "validate": 1}


@pytest.mark.parametrize("orientation", ("standards_based", "mixed"))
def test_attention_does_not_add_missing_standards_library_requirement(
    tmp_path: Path,
    orientation: str,
) -> None:
    root, _ = _workspace(
        tmp_path,
        scoring_orientation=orientation,
        standards_library=_standards_library(),
    )

    result = inspect_activity_attention(
        "class-1",
        "activity-1",
        workspace_root=root,
    )

    assert result.class_id == "class-1"
    assert result.activity_id == "activity-1"


def test_attention_is_read_only_with_real_artifacts(tmp_path: Path) -> None:
    root, _ = _workspace(tmp_path, artifact_count=3)
    before = _fingerprint(root)

    inspect_activity_attention(
        "class-1",
        "activity-1",
        workspace_root=root,
    )

    assert _fingerprint(root) == before


def test_open_activity_then_back_is_read_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, _ = _workspace(tmp_path, artifact_count=2)
    summary = show_activity(
        "class-1",
        "activity-1",
        workspace_root=root,
    ).summary
    before = _fingerprint(root)
    real_load = menu_activity._load_activity_context

    monkeypatch.setattr(
        menu_activity,
        "_load_activity_context",
        lambda class_id, activity_id: real_load(
            class_id,
            activity_id,
            workspace_root=root,
        ),
    )
    monkeypatch.setattr(menu_activity, "clear_screen", lambda: None)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "B")

    menu_activity.launch_activity_context_menu(
        ActivitySummary(
            class_id=summary.class_id,
            activity_id=summary.activity_id,
            title=summary.title,
            status=summary.status,
            scoring_orientation=summary.scoring_orientation,
            session_count=summary.session_count,
            group_count=summary.group_count,
            snapshot_revision=summary.snapshot_revision,
        )
    )

    assert _fingerprint(root) == before


def test_attention_fails_closed_on_predecessor_corruption(tmp_path: Path) -> None:
    root, revision = _workspace(tmp_path)
    second = update_activity(
        UpdateActivityRequest(
            class_id="class-1",
            activity_id="activity-1",
            expected_snapshot_revision=revision,
            actor=_actor(),
            title="Issue 104 Performance Activity Revision 2",
        ),
        workspace_root=root,
        clock=lambda: _clock(11),
    )
    update_activity(
        UpdateActivityRequest(
            class_id="class-1",
            activity_id="activity-1",
            expected_snapshot_revision=second.commit.snapshot_revision,
            actor=_actor(),
            title="Issue 104 Performance Activity Revision 3",
        ),
        workspace_root=root,
        clock=lambda: _clock(12),
    )

    predecessor = snapshot_path(root, second.commit.work, 1)
    predecessor.write_bytes(predecessor.read_bytes() + b"\n")

    with pytest.raises(ConcordStorageIntegrityError):
        inspect_activity_attention(
            "class-1",
            "activity-1",
            workspace_root=root,
        )
