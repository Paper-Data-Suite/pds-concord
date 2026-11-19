"""#150 installed-candidate lesson-reuse acceptance using official Core 0.6.6.

The wheel test uses isolated synthetic class rosters and writes only under a
temporary workspace. It never asserts real printing, scanning or distribution.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
import textwrap
import venv
from pathlib import Path


def _python(env_root: Path) -> Path:
    return (
        env_root / "Scripts" / "python.exe"
        if os.name == "nt"
        else env_root / "bin" / "python"
    )


def _run(command: list[str], *, cwd: Path) -> None:
    subprocess.run(
        command,
        cwd=cwd,
        check=True,
        env={
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": "",
        },
    )


def _smoke_code() -> str:
    """Use real public Core/Concord services with disjoint synthetic rosters."""
    return textwrap.dedent(
        """
        from datetime import datetime, timezone
        from importlib import metadata
        from pathlib import Path
        import tempfile

        from pds_core.class_metadata import (
            create_class_metadata, write_class_metadata_for_class,
        )
        from pds_core.classes import write_class_roster
        from pds_core.rosters import create_roster
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
            inspect_guided_activity_setup,
            prepare_activity_copy,
        )
        from concord.workflows.target_cluster_preflight import (
            create_target_six_cluster_draft,
            inspect_target_cluster_preflight,
        )
        from concord.workflows.target_materials_preflight import (
            inspect_target_materials,
        )
        from concord.workflows.target_assessment_preflight import (
            inspect_target_assessment,
        )
        from concord.menu_guided_activity import (
            launch_guided_activity_menu,
            launch_guided_continue_setup,
        )

        assert metadata.version("pds-core") == "0.6.6"
        assert metadata.version("pds-concord") == "0.3.4"
        assert callable(launch_guided_activity_menu)
        assert callable(launch_guided_continue_setup)

        with tempfile.TemporaryDirectory(prefix="concord150-installed-") as raw:
            root = ensure_workspace_root(Path(raw) / "workspace")
            for class_id, count, prefix in (
                ("source-class", 30, "source"),
                ("target-class", 29, "target"),
            ):
                write_class_metadata_for_class(
                    root,
                    create_class_metadata(
                        class_id,
                        "2026-2027",
                        created_at=datetime(2026, 8, 26, tzinfo=timezone.utc),
                    ),
                )
                roster = create_roster(
                    class_id,
                    tuple(
                        {
                            "student_id": f"{prefix}-{i:02d}",
                            "last_name": f"Synthetic{i:02d}",
                            "first_name": "Example",
                            "period": "1" if class_id == "source-class" else "4",
                        }
                        for i in range(1, count + 1)
                    ),
                )
                write_class_roster(root, roster)

            actor = WorkflowActor(actor_id="teacher150-wheel")
            created = create_activity_context(
                CreateActivityContextRequest(
                    class_id="source-class",
                    activity_id="lesson",
                    title="Synthetic Six-Cluster Seminar",
                    description="One reusable instructional design.",
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
                    activity_id="lesson",
                    group_id="source-group",
                    label="Source historical group",
                    status="active",
                    expected_snapshot_revision=created.commit.snapshot_revision,
                    actor=actor,
                ),
                workspace_root=root,
            )
            source_work = ModuleWorkRef("concord", "source-class", "lesson")
            source_before = load_current_snapshot(root, source_work)

            prepared = prepare_activity_copy(
                PrepareActivityCopyRequest(
                    source_class_id="source-class",
                    source_activity_id="lesson",
                    target_class_id="target-class",
                    target_activity_id="lesson",
                    first_session_id="target-first-session",
                    first_session_label="Day 1",
                ),
                workspace_root=root,
            )
            assert load_current_snapshot(root, source_work) == source_before
            result = copy_activity(
                CopyActivityRequest(
                    source_class_id="source-class",
                    source_activity_id="lesson",
                    target_class_id="target-class",
                    target_activity_id="lesson",
                    first_session_id="target-first-session",
                    first_session_label="Day 1",
                    actor=actor,
                    review_digest=prepared.review_digest,
                ),
                workspace_root=root,
            )
            assert result.commit.snapshot_revision == 1
            target_work = ModuleWorkRef("concord", "target-class", "lesson")
            target = load_current_record_graph(root, target_work)
            assert len(target.graph.activities) == 1
            assert len(target.graph.sessions) == 1
            assert target.graph.sessions[0].status == "planned"
            assert not target.graph.groups
            assert not target.graph.memberships
            assert not target.graph.group_plans
            assert not target.graph.packet_instances
            assert not target.graph.artifact_instances
            assert not target.graph.score_records
            assert not target.graph.criterion_sets
            assert load_current_snapshot(root, source_work) == source_before

            # All three independently owned target inspections must be read-only.
            cluster = inspect_target_cluster_preflight(
                "target-class", "lesson", workspace_root=root
            )
            assert cluster.roster_count == 29
            assert len(cluster.six_cluster_size_reference) == 6
            assert sum(cluster.six_cluster_size_reference) == 29
            assert cluster.can_create_new_shape
            materials = inspect_target_materials(
                "target-class", "lesson", workspace_root=root
            )
            assert not materials.generations
            assert materials.ready_to_print == 0
            assessment = inspect_target_assessment(
                "target-class", "lesson", workspace_root=root
            )
            assert not assessment.scale_ids
            assert not assessment.criterion_set_ids
            assert not assessment.score_record_ids
            setup_before = inspect_guided_activity_setup(
                "target-class", "lesson", workspace_root=root
            )
            assert setup_before.area("session").status == "ready"
            assert setup_before.area("groups").status == "not_set_up"
            assert setup_before.area("materials").status == "not_set_up"
            assert setup_before.area("assessment").status == "not_used"
            assert load_current_record_graph(root, target_work).snapshot_revision == 1

            # Only a reviewed target-specific write may create a plan; all
            # proposed Clusters are empty, never source student assignments.
            created_plan = create_target_six_cluster_draft(
                cluster,
                group_plan_id="target-plan",
                actor=actor,
                workspace_root=root,
            )
            assert created_plan.commit.snapshot_revision == 2
            after = load_current_record_graph(root, target_work)
            assert len(after.graph.group_plans) == 1
            assert not after.graph.memberships
            assert not after.graph.groups
            assert not after.graph.score_records
            assert not after.graph.packet_instances
            assert load_current_snapshot(root, source_work) == source_before
            resumed = inspect_guided_activity_setup(
                "target-class", "lesson", workspace_root=root
            )
            assert resumed.area("groups").status == "needs_attention"
            assert resumed.area("session").status == "ready"
            assert resumed.area("materials").status == "not_set_up"
            assert resumed.area("assessment").status == "not_used"
            assert inspect_target_cluster_preflight(
                "target-class", "lesson", workspace_root=root
            ).existing_plan_count == 1
            print("ISSUE150 INSTALLED WHEEL ACCEPTED: synthetic target-only copy, "
                  "29-student Cluster draft and canonical resume; "
                  "physical paper NOT tested")
        """
    )


def smoke(concord_wheel: Path, core_wheel: Path) -> None:
    if not concord_wheel.is_file() or not core_wheel.is_file():
        raise FileNotFoundError("Exact Core and Concord wheel paths are required")
    with tempfile.TemporaryDirectory(prefix="concord150-wheel-") as raw:
        work = Path(raw)
        env_root = work / "venv"
        venv.EnvBuilder(with_pip=True).create(env_root)
        python = _python(env_root)
        _run(
            [str(python), "-m", "pip", "install", str(core_wheel.resolve())],
            cwd=work,
        )
        _run(
            [str(python), "-m", "pip", "install", str(concord_wheel.resolve())],
            cwd=work,
        )
        _run([str(python), "-m", "pip", "check"], cwd=work)
        source = work / "issue150_installed.py"
        source.write_text(_smoke_code(), encoding="utf-8")
        _run([str(python), str(source)], cwd=work)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("concord_wheel", type=Path)
    parser.add_argument("core_wheel", type=Path)
    args = parser.parse_args()
    smoke(args.concord_wheel, args.core_wheel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
