"""Install built wheels in isolation and smoke-test outside the checkout."""

from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
import textwrap
import venv
from pathlib import Path


def _run(
    command: list[str],
    cwd: Path,
    *,
    env: dict[str, str] | None = None,
    input_text: str | None = None,
) -> None:
    subprocess.run(
        command,
        cwd=cwd,
        check=True,
        input=input_text,
        text=True,
        env={
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
            **({} if env is None else env),
        },
    )


def _workflow_smoke_code() -> str:
    return textwrap.dedent(
        """
        from datetime import datetime, timezone
        from pathlib import Path
        import tempfile

        import concord
        from pds_core.class_metadata import (
            create_class_metadata,
            write_class_metadata_for_class,
        )
        from pds_core.classes import write_class_roster
        from pds_core.rosters import create_roster
        from pds_core.workspace import ensure_workspace_root

        from concord.models import EffectiveContext
        from concord.storage import (
            list_record_revisions,
            load_current_record_graph,
            load_work_snapshot,
        )
        from concord.storage_catalog import rebuild_catalog, query_catalog_records
        from concord.workflows import (
            AddMembershipsRequest,
            CreateActivityContextRequest,
            CreateGroupRequest,
            GroupMemberSpec,
            UpdateSessionRequest,
            WorkflowActor,
            add_memberships,
            create_activity_context,
            create_group,
            update_session,
        )

        package_root = Path(concord.__file__).resolve().parent
        package_files_before = {
            path.relative_to(package_root)
            for path in package_root.rglob("*")
            if path.is_file()
        }

        with tempfile.TemporaryDirectory(prefix="concord-installed-workflow-") as raw:
            root = ensure_workspace_root(Path(raw) / "workspace")
            metadata = create_class_metadata(
                "class-smoke",
                "2026-2027",
                created_at=datetime(2026, 8, 10, tzinfo=timezone.utc),
            )
            write_class_metadata_for_class(root, metadata)
            roster = create_roster(
                "class-smoke",
                (
                    {
                        "student_id": "student-1",
                        "last_name": "One",
                        "first_name": "Alex",
                        "period": "1",
                    },
                    {
                        "student_id": "student-2",
                        "last_name": "Two",
                        "first_name": "Blair",
                        "period": "1",
                    },
                ),
            )
            write_class_roster(root, roster)
            actor = WorkflowActor(actor_id="actor-smoke")
            created = create_activity_context(
                CreateActivityContextRequest(
                    class_id="class-smoke",
                    activity_id="activity-smoke",
                    title="Synthetic smoke activity",
                    activity_type="project",
                    scoring_orientation="evidence_only",
                    session_id="session-smoke",
                    actor=actor,
                    activity_status="active",
                    session_status="active",
                ),
                workspace_root=root,
            )
            group = create_group(
                CreateGroupRequest(
                    class_id="class-smoke",
                    activity_id="activity-smoke",
                    group_id="group-smoke",
                    label="Synthetic Group",
                    status="active",
                    expected_snapshot_revision=created.commit.snapshot_revision,
                    actor=actor,
                ),
                workspace_root=root,
            )
            context = EffectiveContext(
                activity_id="activity-smoke",
                session_ids=("session-smoke",),
            )
            memberships = add_memberships(
                AddMembershipsRequest(
                    class_id="class-smoke",
                    activity_id="activity-smoke",
                    group_id="group-smoke",
                    members=(
                        GroupMemberSpec(
                            membership_id="membership-1",
                            student_id="student-1",
                            effective_context=context,
                        ),
                        GroupMemberSpec(
                            membership_id="membership-2",
                            student_id="student-2",
                            effective_context=context,
                        ),
                    ),
                    expected_snapshot_revision=group.commit.snapshot_revision,
                    actor=actor,
                ),
                workspace_root=root,
            )
            revised = update_session(
                UpdateSessionRequest(
                    class_id="class-smoke",
                    activity_id="activity-smoke",
                    session_id="session-smoke",
                    expected_snapshot_revision=memberships.commit.snapshot_revision,
                    actor=actor,
                    notes="Synthetic installed-wheel revision.",
                ),
                workspace_root=root,
            )
            loaded = load_current_record_graph(root, created.commit.work)
            first_snapshot, _ = load_work_snapshot(root, created.commit.work, 1)
            assert loaded.snapshot_revision == revised.commit.snapshot_revision == 4
            assert len(loaded.graph.groups) == 1
            assert len(loaded.graph.memberships) == 2
            assert first_snapshot.snapshot_revision == 1
            assert list_record_revisions(
                root,
                created.commit.work,
                "session",
                "session-smoke",
            ) == (1, 2)
            rebuild_catalog(root, created.commit.work)
            current = query_catalog_records(
                root, created.commit.work, state="current"
            )
            historical = query_catalog_records(
                root, created.commit.work, snapshot_revision=1
            )
            assert len(current) == 5 and historical

        package_files_after = {
            path.relative_to(package_root)
            for path in package_root.rglob("*")
            if path.is_file()
        }
        assert package_files_after == package_files_before
        """
    )


def smoke_test(concord_wheel: Path, core_wheel: Path) -> None:
    """Install exact local wheels and exercise read-only, menu, and workflow paths."""
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

        absent_workspace = root / "read-only-workspace"
        read_only_env = {"PDS_WORKSPACE_ROOT": str(absent_workspace)}
        for command in (
            [str(concord), "--help"],
            [str(concord), "--version"],
            [str(python), "-m", "concord", "--help"],
            [str(python), "-m", "concord", "--version"],
        ):
            _run(command, outside, env=read_only_env)
        if absent_workspace.exists():
            raise RuntimeError("Read-only CLI smoke unexpectedly created a workspace.")

        for command in (
            [str(concord)],
            [str(concord), "menu"],
            [str(python), "-m", "concord"],
        ):
            _run(command, outside, env=read_only_env, input_text="q\n")
        if absent_workspace.exists():
            raise RuntimeError("Quit-only menu smoke unexpectedly created a workspace.")

        _run([str(python), "-c", _workflow_smoke_code()], outside)


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
