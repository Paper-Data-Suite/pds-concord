from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "scripts" / "smoke_test_routine_artifact_scoring_wheel.py"
VALIDATOR = ROOT / "scripts" / "validate_repository.py"
PACKAGE_CHECK = ROOT / "scripts" / "check_package.py"
WORKFLOWS = ROOT / "concord" / "workflows" / "__init__.py"


def test_issue108_installed_smoke_is_present_and_isolated() -> None:
    text = SMOKE.read_text(encoding="utf-8")
    assert "EXPECTED_CORE_SHA256" in text
    assert (
        "98d7596ce0eed26e4d56a17bbbbd644db3014259b56a45783a173fe8237af5e5"
        in text
    )
    assert '"-m", "pip", "check"' in text
    assert '"-I"' in text
    assert "site-packages" in text
    assert "Activity local scoring setup with valid default Scale" in text
    assert 'scoring_orientation="local_criteria_only"' in text
    assert "StandardDefinition" not in text
    assert "two sequential explicit Scores with canonical reload" in text
    assert "deterministic navigation to another score-ready Artifact" in text
    assert "Advanced Score recording remains reachable" in text
    assert "Issue #108 isolated installed-wheel acceptance: PASS" in text


def test_issue108_smoke_is_wired_into_authoritative_repository_validation() -> None:
    text = VALIDATOR.read_text(encoding="utf-8")
    assert "scripts/smoke_test_routine_artifact_scoring_wheel.py" in text
    assert "installed-wheel smoke: issue #108 routine Artifact scoring" in text


def test_issue108_workflow_modules_are_required_package_content() -> None:
    text = PACKAGE_CHECK.read_text(encoding="utf-8")
    for path in (
        "concord/menu_artifact_scoring.py",
        "concord/workflows/artifact_routine_scoring.py",
        "concord/workflows/artifact_routine_scoring_selection.py",
        "concord/workflows/artifact_routine_scoring_preparation.py",
        "concord/workflows/artifact_routine_scoring_execution.py",
        "concord/workflows/artifact_routine_scoring_continuation.py",
        "concord/workflows/artifact_routine_scoring_next.py",
    ):
        assert path in text


def test_issue108_stable_workflow_surface_is_exported() -> None:
    text = WORKFLOWS.read_text(encoding="utf-8")
    for name in (
        "ArtifactRoutineScoringContext",
        "ArtifactRoutineScoringEligibility",
        "RoutineScoreTargetCandidate",
        "RoutineScoreTargetOptions",
        "RoutineScoringScaleOptions",
        "RoutineScorePreparationRequest",
        "RoutineScoreEvidencePreview",
        "RoutineScorePreview",
        "RoutineScoringContinuation",
        "ContinuedRoutineScorePreparationRequest",
        "ArtifactScoringNext",
        "inspect_artifact_routine_scoring",
        "native_artifact_evidence_reference",
        "routine_target_options",
        "routine_criteria_for_target",
        "routine_scale_options",
        "routine_subject_context_options",
        "prepare_routine_score_preview",
        "record_prepared_routine_score",
        "reload_routine_scoring_after_score",
        "prepare_next_routine_score_preview",
        "inspect_next_score_ready_artifact",
    ):
        assert name in text

def test_issue108_assembly_uses_public_api_shape() -> None:
    text = SMOKE.read_text(encoding="utf-8")
    start = text.index("assembled = assemble_returned_artifact(")
    end = text.index("assert assembled.output_path.is_file()", start)
    assembly_call = text[start:end]
    assert "standards_library=library" not in assembly_call
    assert "workspace_root=root" in assembly_call
    assert "clock=clock" in assembly_call
