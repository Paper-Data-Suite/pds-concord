"""Benchmark Issue #104 opened-Activity projection with 0/1/20 Artifacts."""

from __future__ import annotations

import argparse
import importlib.metadata
import platform
import statistics
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, TypeVar

from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.workspace import ensure_workspace_root

import concord.storage as storage_module
from concord.models import PrivacyPolicy
from concord.workflows import (
    ArtifactPagePlan,
    CreateActivityContextRequest,
    PrepareArtifactPagesRequest,
    UpdateActivityRequest,
    WorkflowActor,
    create_activity_context,
    prepare_artifact_pages,
    update_activity,
)
from concord.workflows.activity import _load_activity_context, show_activity
from concord.workflows.activity_attention import (
    _inspect_activity_attention_from_context,
    inspect_activity_attention,
)
from concord.workflows.activity_read import activity_summary_from_context

T = TypeVar("T")


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", *args],
        cwd=repo,
        text=True,
        encoding="utf-8",
    ).strip()


def _actor() -> WorkflowActor:
    return WorkflowActor(
        actor_id="teacher-1",
        display_label="Synthetic Teacher",
        role_label="teacher",
    )


def _clock(minute: int) -> datetime:
    return datetime(2026, 9, 22, 12, minute % 60, tzinfo=timezone.utc)


def _seed(
    workspace: Path,
    *,
    artifact_count: int,
    minimum_snapshots: int,
) -> int:
    root = ensure_workspace_root(workspace)
    metadata = create_class_metadata(
        "class-1",
        "2026-2027",
        created_at=_clock(0),
    )
    write_class_metadata_for_class(root, metadata)
    created = create_activity_context(
        CreateActivityContextRequest(
            class_id="class-1",
            activity_id="activity-1",
            title="Issue 104 Benchmark Activity",
            activity_type="project",
            scoring_orientation="evidence_only",
            session_id="session-1",
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(1),
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
                privacy_policy=PrivacyPolicy(
                    classification="teacher_restricted"
                ),
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
            clock=lambda: _clock(2),
        )
        revision = prepared.commit.snapshot_revision

    while revision < minimum_snapshots:
        updated = update_activity(
            UpdateActivityRequest(
                class_id="class-1",
                activity_id="activity-1",
                expected_snapshot_revision=revision,
                actor=_actor(),
                title=f"Issue 104 Benchmark Activity r{revision + 1}",
            ),
            workspace_root=root,
            clock=lambda: _clock(revision + 3),
        )
        revision = updated.commit.snapshot_revision

    return revision


def _measure(
    function: Callable[[], T],
    *,
    repetitions: int,
) -> tuple[float, dict[str, int]]:
    original_chain = storage_module._load_snapshot_chain
    original_graph = storage_module._validated_snapshot_graph
    original_validate = getattr(storage_module, "validate_record_graph")
    counts = {"chain": 0, "graph": 0, "validate": 0}

    def counted_chain(*args: Any, **kwargs: Any) -> Any:
        counts["chain"] += 1
        return original_chain(*args, **kwargs)

    def counted_graph(*args: Any, **kwargs: Any) -> Any:
        counts["graph"] += 1
        return original_graph(*args, **kwargs)

    def counted_validate(*args: Any, **kwargs: Any) -> Any:
        counts["validate"] += 1
        return original_validate(*args, **kwargs)

    storage_module._load_snapshot_chain = counted_chain
    storage_module._validated_snapshot_graph = counted_graph
    setattr(storage_module, "validate_record_graph", counted_validate)
    try:
        function()
        counts.update(chain=0, graph=0, validate=0)
        elapsed: list[float] = []
        per_call: list[dict[str, int]] = []
        for _ in range(repetitions):
            before = counts.copy()
            started = time.perf_counter()
            function()
            elapsed.append(time.perf_counter() - started)
            per_call.append(
                {key: counts[key] - before[key] for key in counts}
            )
        first = per_call[0]
        if any(item != first for item in per_call[1:]):
            raise RuntimeError("canonical-read counts varied across repetitions")
        return statistics.median(elapsed), first
    finally:
        storage_module._load_snapshot_chain = original_chain
        storage_module._validated_snapshot_graph = original_graph
        setattr(storage_module, "validate_record_graph", original_validate)


def _run_case(
    workspace: Path,
    *,
    artifacts: int,
    minimum_snapshots: int,
    repetitions: int,
) -> None:
    snapshots = _seed(
        workspace,
        artifact_count=artifacts,
        minimum_snapshots=minimum_snapshots,
    )

    def opened_projection() -> object:
        context = _load_activity_context(
            "class-1",
            "activity-1",
            workspace_root=workspace,
        )
        return (
            activity_summary_from_context(context),
            _inspect_activity_attention_from_context(context),
        )

    cases: tuple[tuple[str, Callable[[], object]], ...] = (
        (
            "show_activity",
            lambda: show_activity(
                "class-1",
                "activity-1",
                workspace_root=workspace,
            ),
        ),
        (
            "inspect_activity_attention",
            lambda: inspect_activity_attention(
                "class-1",
                "activity-1",
                workspace_root=workspace,
            ),
        ),
        ("opened_activity_local_projection", opened_projection),
    )

    print(f"Case: {snapshots} snapshots / {artifacts} Artifacts")
    for label, function in cases:
        median, counts = _measure(function, repetitions=repetitions)
        print(f"  {label}")
        print(f"    median_seconds: {median:.6f}")
        print(f"    snapshot_chain_loads: {counts['chain']}")
        print(f"    graph_materializations: {counts['graph']}")
        print(f"    graph_validations: {counts['validate']}")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--snapshots", type=int, default=12)
    parser.add_argument("--repetitions", type=int, default=5)
    args = parser.parse_args()
    repo = args.repo.resolve()

    if args.snapshots < 2:
        parser.error("--snapshots must be at least 2")
    if args.repetitions < 1:
        parser.error("--repetitions must be positive")

    print("Issue #104 opened-Activity benchmark")
    print(f"OS: {platform.platform()}")
    print(f"Python: {platform.python_version()}")
    print(f"pds-core: {importlib.metadata.version('pds-core')}")
    print(f"pds-concord: {importlib.metadata.version('pds-concord')}")
    print(f"Concord commit: {_git(repo, 'rev-parse', 'HEAD')}")
    print(f"Branch: {_git(repo, 'branch', '--show-current')}")
    print(f"Working tree dirty: {bool(_git(repo, 'status', '--porcelain'))}")
    print(f"Median repetitions: {args.repetitions}")
    print()

    for artifacts in (0, 1, 20):
        with tempfile.TemporaryDirectory(
            prefix=f"pds-concord-issue104-{artifacts}-"
        ) as raw:
            _run_case(
                Path(raw) / "workspace",
                artifacts=artifacts,
                minimum_snapshots=args.snapshots,
                repetitions=args.repetitions,
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
