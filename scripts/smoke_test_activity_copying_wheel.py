"""Install Concord/Core wheels in isolation and smoke-test Activity copying."""

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
        from pathlib import Path
        import tempfile

        from pds_core.class_metadata import (
            create_class_metadata,
            write_class_metadata_for_class,
        )
        from pds_core.routing_models import ModuleWorkRef
        from pds_core.workspace import ensure_workspace_root

        from concord.models import PrivacyPolicy
        from concord.storage import load_current_record_graph, load_current_snapshot
        from concord.workflows import (
            CopyActivityRequest,
            CreateActivityContextRequest,
            CreateGroupRequest,
            PrepareActivityCopyRequest,
            WorkflowActor,
            copy_activity,
            create_activity_context,
            create_group,
            prepare_activity_copy,
        )

        with tempfile.TemporaryDirectory(prefix="concord-copy-installed-") as raw:
            root = ensure_workspace_root(Path(raw) / "workspace")
            for class_id in ("source-class", "target-class"):
                metadata = create_class_metadata(
                    class_id,
                    "2026-2027",
                    created_at=datetime(2026, 8, 26, tzinfo=timezone.utc),
                )
                write_class_metadata_for_class(root, metadata)

            actor = WorkflowActor(actor_id="teacher-copy-smoke")
            created = create_activity_context(
                CreateActivityContextRequest(
                    class_id="source-class",
                    activity_id="seminar-1",
                    title="Synthetic Seminar",
                    description="Reusable seminar configuration.",
                    activity_type="socratic_seminar",
                    scoring_orientation="evidence_only",
                    activity_status="active",
                    session_id="source-session",
                    session_status="active",
                    privacy_policy=PrivacyPolicy(
                        classification="classroom_shared"
                    ),
                    actor=actor,
                ),
                workspace_root=root,
            )
            create_group(
                CreateGroupRequest(
                    class_id="source-class",
                    activity_id="seminar-1",
                    group_id="source-group",
                    label="Historical Group",
                    status="active",
                    expected_snapshot_revision=created.commit.snapshot_revision,
                    actor=actor,
                ),
                workspace_root=root,
            )

            source_work = ModuleWorkRef("concord", "source-class", "seminar-1")
            source_before = load_current_snapshot(root, source_work)
            prepared = prepare_activity_copy(
                PrepareActivityCopyRequest(
                    source_class_id="source-class",
                    source_activity_id="seminar-1",
                    target_class_id="target-class",
                    target_activity_id="seminar-1",
                    first_session_id="target-session",
                    first_session_label="Opening",
                ),
                workspace_root=root,
            )
            assert load_current_snapshot(root, source_work) == source_before
            assert prepared.source_status == "active"
            assert prepared.title == "Synthetic Seminar"
            assert prepared.privacy_policy is not None
            assert prepared.privacy_policy.classification == "classroom_shared"

            result = copy_activity(
                CopyActivityRequest(
                    source_class_id="source-class",
                    source_activity_id="seminar-1",
                    target_class_id="target-class",
                    target_activity_id="seminar-1",
                    first_session_id="target-session",
                    first_session_label="Opening",
                    actor=actor,
                    review_digest=prepared.review_digest,
                ),
                workspace_root=root,
            )
            assert result.commit.snapshot_revision == 1
            assert load_current_snapshot(root, source_work) == source_before

            target_work = ModuleWorkRef("concord", "target-class", "seminar-1")
            target = load_current_record_graph(root, target_work)
            assert target.snapshot_revision == 1
            assert len(target.graph.activities) == 1
            assert len(target.graph.sessions) == 1
            assert not target.graph.groups
            assert not target.graph.group_plans
            assert not target.graph.memberships
            assert not target.graph.packet_instances
            assert not target.graph.artifact_instances
            assert not target.graph.criterion_sets
            assert not target.graph.score_records
            activity = target.graph.activities[0]
            session = target.graph.sessions[0]
            assert activity.status == "draft"
            assert activity.title == "Synthetic Seminar"
            assert activity.description == "Reusable seminar configuration."
            assert activity.criterion_set_ids == ()
            assert activity.external_reference_ids == ()
            assert activity.created_provenance != (
                load_current_record_graph(root, source_work).graph.activities[0]
                .created_provenance
            )
            assert session.session_id == "target-session"
            assert session.sequence == 1
            assert session.status == "planned"
            assert session.label == "Opening"

            continued = create_group(
                CreateGroupRequest(
                    class_id="target-class",
                    activity_id="seminar-1",
                    group_id="target-group",
                    label="Fresh target Group",
                    expected_snapshot_revision=target.snapshot_revision,
                    actor=actor,
                ),
                workspace_root=root,
            )
            assert continued.commit.snapshot_revision == 2
            continued_target = load_current_record_graph(root, target_work)
            assert len(continued_target.graph.groups) == 1
            assert continued_target.graph.groups[0].group_id == "target-group"
            assert load_current_snapshot(root, source_work) == source_before
        """
    )


def smoke(concord_wheel: Path, core_wheel: Path) -> None:
    if not concord_wheel.is_file():
        raise FileNotFoundError(concord_wheel)
    if not core_wheel.is_file():
        raise FileNotFoundError(core_wheel)
    with tempfile.TemporaryDirectory(prefix="concord-copy-wheel-") as raw:
        work = Path(raw)
        env_root = work / "venv"
        venv.EnvBuilder(with_pip=True).create(env_root)
        python = _python(env_root)
        _run([str(python), "-m", "pip", "install", str(core_wheel.resolve())], work)
        _run([str(python), "-m", "pip", "install", str(concord_wheel.resolve())], work)
        smoke_path = work / "copy_smoke.py"
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
