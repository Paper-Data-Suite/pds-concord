"""Benchmark issue #93 canonical-read optimizations without setting thresholds."""

from __future__ import annotations

import argparse
import json
import statistics
import tempfile
import time
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, TypeVar

from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.workspace import ensure_workspace_root

from concord import storage
from concord.model_conversion import record_from_dict
from concord.model_validation import validate_record_graph
from concord.models import Activity, Session
from concord.storage import commit_record_batch
from concord.storage_errors import ConcordStorageIntegrityError
from concord.storage_models import ConcordLoadedRecordGraph
from concord.storage_paths import snapshots_path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = (
    ROOT / "tests" / "fixtures" / "native_records" / "evidence_only_activity.json"
)
T = TypeVar("T")


def _seed_history(
    workspace_root: Path,
    *,
    snapshots: int,
) -> tuple[Activity, Session]:
    root = ensure_workspace_root(workspace_root)
    metadata = create_class_metadata(
        "class-1",
        "2026-2027",
        created_at=datetime(2026, 8, 29, tzinfo=timezone.utc),
    )
    write_class_metadata_for_class(root, metadata)
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    activity = record_from_dict("activity", fixture["records"][0]["body"])
    session = record_from_dict("session", fixture["records"][1]["body"])
    if not isinstance(activity, Activity) or not isinstance(session, Session):
        raise RuntimeError("benchmark fixture did not produce Activity and Session")

    committed = commit_record_batch(
        root,
        activity.work_reference,
        (activity, session),
        expected_snapshot_revision=None,
    )
    for revision in range(2, snapshots + 1):
        committed = commit_record_batch(
            root,
            activity.work_reference,
            (replace(session, notes=f"Benchmark revision {revision}."),),
            expected_snapshot_revision=committed.snapshot_revision,
        )
    if committed.snapshot_revision != snapshots:
        raise RuntimeError("benchmark history did not reach requested revision")
    return activity, session


def _legacy_list_work_snapshots(
    workspace_root: Path,
    activity: Activity,
) -> tuple[int, ...]:
    revisions: list[int] = []
    for path in storage._visible(
        snapshots_path(workspace_root, activity.work_reference),
        "snapshots",
    ):
        if (
            path.is_symlink()
            or not path.is_file()
            or not path.name.endswith(".json")
            or not path.stem.isdigit()
            or path.stem.startswith("0")
        ):
            raise ConcordStorageIntegrityError(
                f"unexpected snapshot entry: {path}"
            )
        revision = int(path.stem)
        storage.load_work_snapshot(
            workspace_root,
            activity.work_reference,
            revision,
        )
        revisions.append(revision)
    return tuple(sorted(revisions))


def _legacy_load_current_record_graph(
    workspace_root: Path,
    activity: Activity,
) -> ConcordLoadedRecordGraph:
    storage.load_work_marker(workspace_root, activity.work_reference)
    current = storage.load_current_snapshot(workspace_root, activity.work_reference)
    snapshot, snapshot_bytes = storage._load_snapshot_chain(
        workspace_root,
        activity.work_reference,
        current.snapshot_revision,
    )
    snapshot_sha256 = storage._sha(snapshot_bytes)
    if snapshot_sha256 != current.snapshot_sha256:
        raise ConcordStorageIntegrityError(
            "current pointer snapshot digest mismatch."
        )
    graph = storage._validated_snapshot_graph(
        workspace_root,
        activity.work_reference,
        snapshot,
    )
    validate_record_graph(graph)
    return ConcordLoadedRecordGraph(
        graph,
        current.snapshot_revision,
        snapshot_sha256,
    )


def _legacy_record_history_pass(
    workspace_root: Path,
    activity: Activity,
) -> tuple[tuple[str, str], ...]:
    identities = storage.list_record_identities(
        workspace_root,
        activity.work_reference,
    )
    for record_kind, record_id in identities:
        storage.list_record_revisions(
            workspace_root,
            activity.work_reference,
            record_kind,
            record_id,
        )
    return identities


def _current_record_history_pass(
    workspace_root: Path,
    activity: Activity,
) -> tuple[tuple[str, str], ...]:
    history = storage._list_record_history(
        workspace_root,
        activity.work_reference,
    )
    return tuple(sorted(history))


def _time_call(
    function: Callable[[], T],
    *,
    repetitions: int,
) -> tuple[float, T]:
    elapsed: list[float] = []
    result: T | None = None
    for _ in range(repetitions):
        started = time.perf_counter()
        result = function()
        elapsed.append(time.perf_counter() - started)
    assert result is not None
    return statistics.median(elapsed), result


def _format_change(before: float, after: float) -> str:
    if before <= 0:
        return "n/a"
    reduction = (before - after) / before * 100
    return f"{reduction:.1f}% faster"


def benchmark(*, snapshots: int, repetitions: int) -> None:
    with tempfile.TemporaryDirectory(prefix="pds-concord-issue93-benchmark-") as raw:
        workspace = Path(raw) / "workspace"
        activity, _ = _seed_history(workspace, snapshots=snapshots)

        comparisons: tuple[
            tuple[str, Callable[[], object], Callable[[], object]], ...
        ] = (
            (
                "list_work_snapshots",
                lambda: _legacy_list_work_snapshots(workspace, activity),
                lambda: storage.list_work_snapshots(
                    workspace,
                    activity.work_reference,
                ),
            ),
            (
                "load_current_record_graph",
                lambda: _legacy_load_current_record_graph(workspace, activity),
                lambda: storage.load_current_record_graph(
                    workspace,
                    activity.work_reference,
                ),
            ),
            (
                "record-history enumeration",
                lambda: _legacy_record_history_pass(workspace, activity),
                lambda: _current_record_history_pass(workspace, activity),
            ),
        )

        print(
            f"Issue #93 storage benchmark: {snapshots} snapshots, "
            f"{repetitions} median repetitions"
        )
        for label, legacy, current in comparisons:
            before, legacy_result = _time_call(
                legacy,
                repetitions=repetitions,
            )
            after, current_result = _time_call(
                current,
                repetitions=repetitions,
            )
            if legacy_result != current_result:
                raise RuntimeError(f"{label} benchmark paths disagree")
            print(
                f"{label}: legacy={before:.6f}s "
                f"optimized={after:.6f}s "
                f"({_format_change(before, after)})"
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshots", type=int, default=12)
    parser.add_argument("--repetitions", type=int, default=5)
    args = parser.parse_args()
    if args.snapshots < 2:
        parser.error("--snapshots must be at least 2")
    if args.repetitions < 1:
        parser.error("--repetitions must be positive")
    benchmark(
        snapshots=args.snapshots,
        repetitions=args.repetitions,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
