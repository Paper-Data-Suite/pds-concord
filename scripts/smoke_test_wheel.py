"""Install built wheels in isolation and smoke-test outside the checkout."""

from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
import textwrap
import venv
from pathlib import Path


def _run(command: list[str], cwd: Path) -> None:
    subprocess.run(
        command, cwd=cwd, check=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    )


def _storage_smoke_code() -> str:
    return textwrap.dedent(
        """
        from dataclasses import replace
        from datetime import datetime, timezone
        from pathlib import Path
        import tempfile
        from pds_core.class_metadata import (
            create_class_metadata,
            write_class_metadata_for_class,
        )
        from pds_core.workspace import ensure_workspace_root
        from concord.model_conversion import record_from_dict
        from concord.storage import (
            commit_record_batch,
            load_current_record_graph,
            load_record_revision,
        )
        from concord.storage_catalog import rebuild_catalog, query_catalog_records

        with tempfile.TemporaryDirectory(prefix="concord-installed-storage-") as raw:
            root = ensure_workspace_root(Path(raw) / "workspace")
            metadata = create_class_metadata(
                "class-smoke",
                "2026-2027",
                created_at=datetime(2026, 8, 5, tzinfo=timezone.utc),
            )
            write_class_metadata_for_class(root, metadata)
            provenance = {
                "actor": {
                    "actor_kind": "authorized_adult",
                    "actor_id": "actor-smoke",
                    "owning_system": "core",
                },
                "timestamp": "2026-08-05T12:00:00+00:00",
                "source_kind": "manual",
            }
            activity = record_from_dict(
                "activity",
                {
                    "activity_id": "activity-smoke",
                    "class_reference": {
                        "module_id": "core",
                        "record_kind": "class",
                        "record_id": "class-smoke",
                    },
                    "title": "Synthetic smoke activity",
                    "activity_type": "local:smoke",
                    "scoring_orientation": "evidence_only",
                    "status": "active",
                    "created_provenance": provenance,
                    "focus_standard_ids": [],
                    "criterion_set_ids": [],
                    "external_reference_ids": [],
                },
            )
            session = record_from_dict(
                "session",
                {
                    "session_id": "session-smoke",
                    "activity_id": "activity-smoke",
                    "sequence": 1,
                    "status": "active",
                    "created_provenance": provenance,
                },
            )
            first = commit_record_batch(
                root,
                activity.work_reference,
                (activity, session),
                expected_snapshot_revision=None,
            )
            changed = replace(session, notes="Synthetic installed-wheel revision.")
            second = commit_record_batch(
                root,
                activity.work_reference,
                (changed,),
                expected_snapshot_revision=first.snapshot_revision,
            )
            loaded = load_current_record_graph(root, activity.work_reference)
            old, _ = load_record_revision(
                root,
                activity.work_reference,
                "session",
                session.session_id,
                1,
            )
            assert loaded.snapshot_revision == second.snapshot_revision == 2
            assert old == session and loaded.graph.sessions == (changed,)
            rebuild_catalog(root, activity.work_reference)
            current = query_catalog_records(
                root, activity.work_reference, state="current"
            )
            historical = query_catalog_records(
                root, activity.work_reference, snapshot_revision=1
            )
            assert len(current) == 2 and historical
        """
    )


def smoke_test(concord_wheel: Path, core_wheel: Path) -> None:
    """Install exact local wheels without indexes and exercise import and CLI."""
    with tempfile.TemporaryDirectory(prefix="pds-concord-smoke-") as raw_temp:
        root = Path(raw_temp)
        environment = root / "venv"
        outside = root / "outside"
        outside.mkdir()
        venv.EnvBuilder(with_pip=True).create(environment)
        scripts = environment / ("Scripts" if os.name == "nt" else "bin")
        python = scripts / ("python.exe" if os.name == "nt" else "python")
        concord = scripts / ("concord.exe" if os.name == "nt" else "concord")
        _run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--no-index",
                "--no-deps",
                str(core_wheel.resolve()),
                str(concord_wheel.resolve()),
            ],
            outside,
        )
        _run(
            [
                str(python),
                "-c",
                (
                    "import importlib.metadata as m, concord, pds_core; "
                    "assert concord.__version__ == m.version('pds-concord'); "
                    "assert m.version('pds-core') == '0.6.0'"
                ),
            ],
            outside,
        )
        for command in (
            [str(concord)],
            [str(concord), "--help"],
            [str(concord), "--version"],
            [str(python), "-m", "concord"],
            [str(python), "-m", "concord", "--help"],
            [str(python), "-m", "concord", "--version"],
        ):
            _run(command, outside)
        _run([str(python), "-c", _storage_smoke_code()], outside)


def main() -> int:
    """Run an isolated smoke test for local Concord and Core wheels."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("concord_wheel", type=Path)
    parser.add_argument("core_wheel", type=Path)
    args = parser.parse_args()
    smoke_test(args.concord_wheel, args.core_wheel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
