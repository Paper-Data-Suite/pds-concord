"""Install wheels and smoke-test issues #66/#104 task-oriented Activity menus."""

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
        import hashlib
        from datetime import datetime, timezone
        from importlib import metadata
        from pathlib import Path
        from unittest.mock import patch
        import contextlib
        import io
        import tempfile

        import concord
        import concord.menu_activity as activity_menu
        import concord.menu_artifact as artifact_menu
        import concord.menu_publication as publication_menu
        import concord.menu_scoring as scoring_menu
        from pds_core.class_metadata import (
            create_class_metadata,
            write_class_metadata_for_class,
        )
        from pds_core.classes import write_class_roster
        from pds_core.rosters import create_roster
        from pds_core.workspace import ensure_workspace_root

        from concord.menu_context import MenuSessionContext
        from concord.models import PlannedGroup
        from concord.workflows import (
            CreateActivityContextRequest,
            WorkflowActor,
            create_activity_context,
            show_activity,
        )
        from concord.workflows.group_plan import (
            CreateGroupPlanRequest,
            create_group_plan,
        )

        assert metadata.version("pds-core") == "0.6.3"
        assert metadata.version("pds-concord") == "0.3.0"

        module_path = Path(concord.__file__).resolve().as_posix().lower()
        assert "site-packages" in module_path, module_path

        for distribution in (
            "pds-meridian",
            "scoreform",
            "quillan",
            "pds-vitrine",
            "pds-portia",
            "paper-data-suite",
        ):
            try:
                metadata.version(distribution)
            except metadata.PackageNotFoundError:
                pass
            else:
                raise AssertionError(
                    f"unexpected sibling distribution installed: {distribution}"
                )

        def fingerprint(root: Path) -> tuple[tuple[str, str], ...]:
            rows = []
            for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
                if path.is_file():
                    rows.append(
                        (
                            path.relative_to(root).as_posix(),
                            hashlib.sha256(path.read_bytes()).hexdigest(),
                        )
                    )
            return tuple(rows)

        with tempfile.TemporaryDirectory(prefix="concord-task-menu-installed-") as raw:
            root = ensure_workspace_root(Path(raw) / "workspace")
            write_class_metadata_for_class(
                root,
                create_class_metadata(
                    "class-1",
                    "2026-2027",
                    created_at=datetime(2026, 8, 27, tzinfo=timezone.utc),
                ),
            )
            write_class_roster(
                root,
                create_roster(
                    "class-1",
                    (
                        {
                            "student_id": "student-1",
                            "last_name": "One",
                            "first_name": "Alex",
                            "period": "1",
                        },
                    ),
                ),
            )
            actor = WorkflowActor(
                actor_id="teacher-task-menu-smoke",
                display_label="Synthetic Teacher",
                role_label="teacher",
            )
            created = create_activity_context(
                CreateActivityContextRequest(
                    class_id="class-1",
                    activity_id="activity-1",
                    title="Task Menu Smoke Activity",
                    activity_type="project",
                    scoring_orientation="evidence_only",
                    session_id="session-1",
                    session_label="Day 1",
                    actor=actor,
                ),
                workspace_root=root,
            )
            planned = create_group_plan(
                CreateGroupPlanRequest(
                    class_id="class-1",
                    activity_id="activity-1",
                    group_plan_id="plan-1",
                    strategy="manual",
                    expected_snapshot_revision=created.commit.snapshot_revision,
                    actor=actor,
                    proposed_groups=(
                        PlannedGroup(
                            planned_group_key="group-a",
                            label="Group A",
                            student_ids=("student-1",),
                        ),
                    ),
                ),
                workspace_root=root,
            )
            activity = show_activity(
                "class-1",
                "activity-1",
                workspace_root=root,
            ).summary
            before_revision = activity.snapshot_revision
            assert before_revision == planned.commit.snapshot_revision
            before = fingerprint(root)
            real_load_activity_context = activity_menu._load_activity_context

            responses = iter(
                (
                    "1", "b",
                    "2", "b",
                    "3", "b",
                    "4", "b",
                    "5", "b",
                    "6", "b",
                    "7", "b",
                    "b",
                )
            )
            output = io.StringIO()

            with (
                patch(
                    "builtins.input",
                    side_effect=lambda _prompt="": next(responses),
                ),
                patch.object(
                    activity_menu,
                    "_load_activity_context",
                    lambda class_id, activity_id: real_load_activity_context(
                        class_id,
                        activity_id,
                        workspace_root=root,
                    ),
                ),
                patch.object(activity_menu, "clear_screen", lambda: None),
                patch.object(artifact_menu, "clear_screen", lambda: None),
                patch.object(publication_menu, "clear_screen", lambda: None),
                patch.object(scoring_menu, "clear_screen", lambda: None),
                patch.object(scoring_menu, "_latest", lambda selected: selected),
                contextlib.redirect_stdout(output),
            ):
                activity_menu.launch_activity_context_menu(
                    activity,
                    MenuSessionContext(actor=actor),
                )

            rendered = output.getvalue()
            assert "Attention: unavailable" not in rendered
            for label in (
                "Attention",
                "Group plans still need preparation",
                "A. Open next action",
                "1. Plan",
                "2. Prepare",
                "3. Collect",
                "4. Review",
                "5. Score",
                "6. Share",
                "7. Advanced Activity tools",
                "1. Continue classroom setup",
                "1. Prepare classroom materials",
                "1. View returned work",
                "1. Review collected work",
                "1. Record a Score",
                "1. Set up sharing",
                "8. Scoring",
                "9. Publication",
            ):
                assert label in rendered, label

            after_revision = show_activity(
                "class-1",
                "activity-1",
                workspace_root=root,
            ).summary.snapshot_revision
            assert after_revision == before_revision
            assert fingerprint(root) == before
        """
    )


def smoke(concord_wheel: Path, core_wheel: Path) -> None:
    if not concord_wheel.is_file():
        raise FileNotFoundError(concord_wheel)
    if not core_wheel.is_file():
        raise FileNotFoundError(core_wheel)
    with tempfile.TemporaryDirectory(prefix="concord-task-menu-wheel-") as raw:
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
        smoke_path = work / "task_oriented_activity_menu_smoke.py"
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
