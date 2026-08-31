"""Install Concord/Core wheels in isolation and smoke-test guided setup."""

from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
import textwrap
import venv
from pathlib import Path


def _python(venv_root: Path) -> Path:
    return (
        venv_root / "Scripts" / "python.exe"
        if os.name == "nt"
        else venv_root / "bin" / "python"
    )


def _run(command: list[str], cwd: Path) -> None:
    subprocess.run(
        command,
        cwd=cwd,
        check=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )


def _smoke_code() -> str:
    return textwrap.dedent(
        """
        from datetime import datetime, timezone
        from importlib import metadata
        from pathlib import Path
        import tempfile

        from pds_core.class_metadata import (
            create_class_metadata,
            write_class_metadata_for_class,
        )
        from pds_core.classes import write_class_roster
        from pds_core.rosters import create_roster
        from pds_core.workspace import ensure_workspace_root

        from concord.menu_guided_activity import (
            launch_guided_activity_menu,
            launch_guided_continue_setup,
        )
        from concord.models import EffectiveContext
        from concord.storage import load_current_record_graph
        from concord.workflows import (
            CreateActivityContextRequest,
            CreateGroupWithMembersRequest,
            GroupMemberSpec,
            GroupResponsibilitySpec,
            GroupRoleSpec,
            WorkflowActor,
            core_student_participant,
            create_activity_context,
            create_group_with_members,
            group_record_reference,
            inspect_guided_activity_setup,
        )

        assert metadata.version("pds-core") == "0.6.3"
        assert metadata.version("pds-concord") == "0.3.0"
        assert callable(launch_guided_activity_menu)
        assert callable(launch_guided_continue_setup)

        with tempfile.TemporaryDirectory(prefix="concord-guided-installed-") as raw:
            root = ensure_workspace_root(Path(raw) / "workspace")
            class_metadata = create_class_metadata(
                "class-1",
                "2026-2027",
                created_at=datetime(2026, 8, 27, tzinfo=timezone.utc),
            )
            write_class_metadata_for_class(root, class_metadata)
            roster = create_roster(
                "class-1",
                (
                    {
                        "student_id": "student-1",
                        "last_name": "One",
                        "first_name": "Alex",
                        "period": "1",
                    },
                ),
            )
            write_class_roster(root, roster)
            actor = WorkflowActor(
                actor_id="teacher-guided-smoke",
                display_label="Synthetic Teacher",
                role_label="teacher",
            )
            created = create_activity_context(
                CreateActivityContextRequest(
                    class_id="class-1",
                    activity_id="activity-1",
                    title="Guided Smoke Activity",
                    activity_type="project",
                    scoring_orientation="evidence_only",
                    session_id="session-1",
                    session_label="Day 1",
                    actor=actor,
                ),
                workspace_root=root,
            )

            first = inspect_guided_activity_setup(
                "class-1",
                "activity-1",
                workspace_root=root,
            )
            assert first.area("activity").status == "ready"
            assert first.area("session").status == "ready"
            assert first.area("materials").status == "not_set_up"
            assert first.area("groups").status == "not_set_up"
            assert first.area("assignments").status == "not_set_up"
            assert first.area("assessment").status == "not_used"
            assert first.area("assessment").detail == (
                "This Activity collects evidence without Scores."
            )

            second = inspect_guided_activity_setup(
                "class-1",
                "activity-1",
                workspace_root=root,
            )
            assert second == first

            participant = core_student_participant(root, "class-1", "student-1")
            context = EffectiveContext(
                activity_id="activity-1",
                session_ids=("session-1",),
            )
            group_result = create_group_with_members(
                CreateGroupWithMembersRequest(
                    class_id="class-1",
                    activity_id="activity-1",
                    group_id="group-1",
                    label="Group 1",
                    expected_snapshot_revision=created.commit.snapshot_revision,
                    actor=actor,
                    status="active",
                    effective_context=context,
                    members=(
                        GroupMemberSpec(
                            membership_id="membership-1",
                            student_id="student-1",
                            effective_context=context,
                        ),
                    ),
                    roles=(
                        GroupRoleSpec(
                            role_assignment_id="role-1",
                            participant_reference=participant,
                            role_key="recorder",
                            effective_context=context,
                            membership_id="membership-1",
                        ),
                    ),
                    responsibilities=(
                        GroupResponsibilitySpec(
                            responsibility_assignment_id="responsibility-1",
                            assignee_reference=group_record_reference("group-1"),
                            description="Record evidence",
                            effective_context=context,
                        ),
                    ),
                ),
                workspace_root=root,
            )
            resumed = inspect_guided_activity_setup(
                "class-1",
                "activity-1",
                workspace_root=root,
            )
            assert resumed.area("groups").status == "ready"
            assert resumed.area("assignments").status == "ready"
            assert resumed.area("materials").status == "not_set_up"
            assert resumed.area("assessment").status == "not_used"
            assert resumed.recommended_area() == resumed.area("materials")

            graph = load_current_record_graph(
                root,
                group_result.commit.work,
            ).graph
            assert len(graph.groups) == 1
            assert len(graph.memberships) == 1
            assert len(graph.role_assignments) == 1
            assert len(graph.responsibility_assignments) == 1
            assert not graph.score_records
        """
    )


def smoke(concord_wheel: Path, core_wheel: Path) -> None:
    if not concord_wheel.is_file():
        raise FileNotFoundError(concord_wheel)
    if not core_wheel.is_file():
        raise FileNotFoundError(core_wheel)
    with tempfile.TemporaryDirectory(prefix="concord-guided-wheel-") as raw:
        work = Path(raw)
        env_root = work / "venv"
        venv.EnvBuilder(with_pip=True).create(env_root)
        python = _python(env_root)
        _run(
            [str(python), "-m", "pip", "install", str(core_wheel.resolve())],
            work,
        )
        _run(
            [str(python), "-m", "pip", "install", str(concord_wheel.resolve())],
            work,
        )
        smoke_path = work / "guided_activity_smoke.py"
        smoke_path.write_text(_smoke_code(), encoding="utf-8")
        _run([str(python), str(smoke_path)], work)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("concord_wheel", type=Path)
    parser.add_argument("core_wheel", type=Path)
    args = parser.parse_args()
    smoke(args.concord_wheel, args.core_wheel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
