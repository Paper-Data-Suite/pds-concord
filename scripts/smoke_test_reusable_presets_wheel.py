"""Install Concord/Core wheels in isolation and smoke-test reusable presets."""

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
        from pds_core.routing_models import ModuleWorkRef
        from pds_core.workspace import ensure_workspace_root

        from concord.models import (
            EffectiveContext,
            ParticipantReference,
            PrivacyPolicy,
            ScoreTargetReference,
            ScoringScaleLevel,
        )
        from concord.reusable_preset_storage import preset_library_root
        from concord.reusable_presets import CriterionPresetSpec
        from concord.storage import load_current_record_graph, load_current_snapshot
        from concord.workflows import (
            AddScoreRequest,
            ApplyResponsibilityPresetRequest,
            ApplyRolePresetRequest,
            CreateActivityContextRequest,
            CreateCriterionSetPresetRequest,
            CreateResponsibilityPresetRequest,
            CreateRolePresetRequest,
            CreateScoringScalePresetRequest,
            CriterionTargetIdentity,
            MaterializeScoringSetupRequest,
            ReviseRolePresetRequest,
            ReviseScoringScalePresetRequest,
            WorkflowActor,
            add_score,
            apply_responsibility_preset,
            apply_role_preset,
            create_activity_context,
            create_criterion_set_preset,
            create_responsibility_preset,
            create_role_preset,
            create_scoring_scale_preset,
            get_preset,
            materialize_scoring_setup,
            prepare_responsibility_preset_application,
            prepare_role_preset_application,
            prepare_scoring_setup,
            revise_role_preset,
            revise_scoring_scale_preset,
        )

        assert metadata.version("pds-core") == "0.6.3"
        assert metadata.version("pds-concord") == "0.3.0.dev0"

        with tempfile.TemporaryDirectory(prefix="concord-presets-installed-") as raw:
            root = ensure_workspace_root(Path(raw) / "workspace")
            metadata_record = create_class_metadata(
                "class-1",
                "2026-2027",
                created_at=datetime(2026, 8, 27, tzinfo=timezone.utc),
            )
            write_class_metadata_for_class(root, metadata_record)
            actor = WorkflowActor(actor_id="teacher-preset-smoke")

            created = create_activity_context(
                CreateActivityContextRequest(
                    class_id="class-1",
                    activity_id="activity-1",
                    title="Preset Smoke Activity",
                    activity_type="project",
                    scoring_orientation="local_criteria_only",
                    session_id="session-1",
                    actor=actor,
                ),
                workspace_root=root,
            )
            work = ModuleWorkRef("concord", "class-1", "activity-1")
            session_context = EffectiveContext(
                activity_id="activity-1",
                session_ids=("session-1",),
            )
            participant = ParticipantReference(
                participant_kind="authorized_actor",
                participant_id="participant-1",
                owning_system="concord",
            )

            role_v1 = create_role_preset(
                CreateRolePresetRequest(
                    preset_id="discussion-leader",
                    preset_revision_id="discussion-leader-v1",
                    name="Discussion Leader",
                    role_key="facilitator",
                    role_label="Discussion Leader",
                    description="Keep the discussion moving.",
                    actor=actor,
                ),
                workspace_root=root,
            )
            revise_role_preset(
                ReviseRolePresetRequest(
                    preset_id="discussion-leader",
                    preset_revision_id="discussion-leader-v2",
                    expected_revision=role_v1.revision,
                    name="Discussion Leader",
                    role_key="facilitator",
                    role_label="Discussion Leader",
                    description="Keep discussion moving and invite participation.",
                    actor=actor,
                ),
                workspace_root=root,
            )
            role_request = ApplyRolePresetRequest(
                preset_id="discussion-leader",
                preset_revision_id="discussion-leader-v2",
                class_id="class-1",
                activity_id="activity-1",
                role_assignment_id="fresh-role-assignment",
                participant_reference=participant,
                effective_context=session_context,
                expected_snapshot_revision=created.commit.snapshot_revision,
                actor=actor,
            )
            before_role = load_current_snapshot(root, work)
            prepared_role = prepare_role_preset_application(
                role_request,
                workspace_root=root,
            )
            assert load_current_snapshot(root, work) == before_role
            role_result = apply_role_preset(
                role_request,
                review_digest=prepared_role.review_digest,
                workspace_root=root,
            )
            assert role_result.role_assignment_id == "fresh-role-assignment"

            responsibility = create_responsibility_preset(
                CreateResponsibilityPresetRequest(
                    preset_id="evidence-recorder",
                    preset_revision_id="evidence-recorder-v1",
                    name="Evidence Recorder",
                    description="Record the group's evidence.",
                    expected_output="Evidence notes",
                    actor=actor,
                ),
                workspace_root=root,
            )
            responsibility_request = ApplyResponsibilityPresetRequest(
                preset_id=responsibility.preset_id,
                preset_revision_id=responsibility.preset_revision_id,
                class_id="class-1",
                activity_id="activity-1",
                responsibility_assignment_id="fresh-responsibility",
                assignee_reference=participant,
                effective_context=session_context,
                expected_snapshot_revision=role_result.commit.snapshot_revision,
                actor=actor,
            )
            before_responsibility = load_current_snapshot(root, work)
            prepared_responsibility = prepare_responsibility_preset_application(
                responsibility_request,
                workspace_root=root,
            )
            assert load_current_snapshot(root, work) == before_responsibility
            responsibility_result = apply_responsibility_preset(
                responsibility_request,
                review_digest=prepared_responsibility.review_digest,
                workspace_root=root,
            )
            assert responsibility_result.responsibility_assignment_id == (
                "fresh-responsibility"
            )

            levels = (
                ScoringScaleLevel(
                    value="developing",
                    label="Developing",
                    meaning="Evidence is still developing.",
                    position=1,
                ),
                ScoringScaleLevel(
                    value="secure",
                    label="Secure",
                    meaning="Evidence is secure.",
                    position=2,
                ),
            )
            scale_v1 = create_scoring_scale_preset(
                CreateScoringScalePresetRequest(
                    preset_id="two-level",
                    preset_revision_id="two-level-v1",
                    name="Two-Level Proficiency",
                    scale_type="ordinal",
                    levels=levels,
                    intended_use="Quick local rubric",
                    actor=actor,
                ),
                workspace_root=root,
            )
            criterion = create_criterion_set_preset(
                CreateCriterionSetPresetRequest(
                    preset_id="discussion-rubric",
                    preset_revision_id="discussion-rubric-v1",
                    name="Discussion Rubric",
                    purpose="Assess discussion evidence.",
                    criterion_set_kind="local",
                    criteria=(
                        CriterionPresetSpec(
                            key="evidence",
                            label="Evidence",
                            definition="Uses relevant evidence.",
                            criterion_kind="local",
                            supported_target_kinds=("concord_activity",),
                            default_scoring_scale_preset_id="two-level",
                            default_scoring_scale_preset_revision_id="two-level-v1",
                        ),
                    ),
                    actor=actor,
                ),
                workspace_root=root,
            )
            scoring_request = MaterializeScoringSetupRequest(
                criterion_preset_id=criterion.preset_id,
                criterion_preset_revision_id=criterion.preset_revision_id,
                class_id="class-1",
                activity_id="activity-1",
                criterion_set_id="activity-rubric",
                criterion_set_lineage_id="activity-rubric-lineage",
                criterion_ids=(
                    CriterionTargetIdentity(
                        criterion_key="evidence",
                        criterion_id="activity-evidence-criterion",
                    ),
                ),
                scoring_scale_preset_id="two-level",
                scoring_scale_preset_revision_id="two-level-v1",
                scoring_scale_id="activity-scale",
                scoring_scale_lineage_id="activity-scale-lineage",
                expected_snapshot_revision=(
                    responsibility_result.commit.snapshot_revision
                ),
                actor=actor,
            )
            before_scoring = load_current_snapshot(root, work)
            prepared_scoring = prepare_scoring_setup(
                scoring_request,
                workspace_root=root,
            )
            assert load_current_snapshot(root, work) == before_scoring
            scoring_result = materialize_scoring_setup(
                scoring_request,
                review_digest=prepared_scoring.review_digest,
                workspace_root=root,
            )
            graph_after_setup = load_current_record_graph(root, work).graph
            assert len(graph_after_setup.scoring_scales) == 1
            assert len(graph_after_setup.criterion_sets) == 1
            assert len(graph_after_setup.criteria) == 1
            assert not graph_after_setup.score_records
            native_scale = graph_after_setup.scoring_scales[0]
            native_criterion = graph_after_setup.criteria[0]
            assert native_scale.scoring_scale_id == "activity-scale"
            assert native_criterion.default_scoring_scale_id == "activity-scale"

            score = add_score(
                AddScoreRequest(
                    class_id="class-1",
                    activity_id="activity-1",
                    score_record_id="score-1",
                    target_reference=ScoreTargetReference(
                        target_kind="concord_activity",
                        target_id="activity-1",
                        owning_system="concord",
                    ),
                    criterion_id="activity-evidence-criterion",
                    scoring_scale_id="activity-scale",
                    disposition="scored",
                    value="secure",
                    basis="professional_judgment",
                    rationale="Synthetic installed-wheel judgment.",
                    privacy_policy=PrivacyPolicy(
                        classification="teacher_restricted"
                    ),
                    expected_snapshot_revision=scoring_result.commit.snapshot_revision,
                    actor=actor,
                ),
                workspace_root=root,
            )
            graph_with_score = load_current_record_graph(root, work).graph
            assert len(graph_with_score.score_records) == 1
            assert graph_with_score.score_records[0].score_record_id == "score-1"

            revise_scoring_scale_preset(
                ReviseScoringScalePresetRequest(
                    preset_id="two-level",
                    preset_revision_id="two-level-v2",
                    expected_revision=scale_v1.revision,
                    name="Two-Level Proficiency Revised",
                    scale_type="ordinal",
                    levels=levels,
                    intended_use="Future use only",
                    actor=actor,
                ),
                workspace_root=root,
            )
            graph_after_preset_revision = load_current_record_graph(root, work).graph
            assert graph_after_preset_revision.scoring_scales[0] == native_scale
            assert graph_after_preset_revision.criteria[0] == native_criterion
            assert graph_after_preset_revision.score_records == (
                graph_with_score.score_records
            )
            assert (
                score.commit.snapshot_revision
                > scoring_result.commit.snapshot_revision
            )

            current_role = get_preset(
                "role",
                "discussion-leader",
                workspace_root=root,
            )
            assert current_role.preset_revision_id == "discussion-leader-v2"
            shared_root = preset_library_root(root)
            assert shared_root.is_dir()
            assert "shared" in shared_root.parts
            assert "activity-1" not in shared_root.parts

            final_graph = load_current_record_graph(root, work).graph
            assert final_graph.role_assignments[0].participant_reference == participant
            assert (
                final_graph.responsibility_assignments[0].assignee_reference
                == participant
            )
            assert len(final_graph.score_records) == 1
        """
    )


def smoke(concord_wheel: Path, core_wheel: Path) -> None:
    if not concord_wheel.is_file():
        raise FileNotFoundError(concord_wheel)
    if not core_wheel.is_file():
        raise FileNotFoundError(core_wheel)
    with tempfile.TemporaryDirectory(prefix="concord-presets-wheel-") as raw:
        work = Path(raw)
        env_root = work / "venv"
        venv.EnvBuilder(with_pip=True).create(env_root)
        python = _python(env_root)
        _run([str(python), "-m", "pip", "install", str(core_wheel.resolve())], work)
        _run([str(python), "-m", "pip", "install", str(concord_wheel.resolve())], work)
        smoke_path = work / "preset_smoke.py"
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
