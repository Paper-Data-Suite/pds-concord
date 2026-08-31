from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_physical_starter_workflow_acceptance_issue70.py"
DOC = ROOT / "docs" / "v0.3.0-installed-physical-starter-workflow-acceptance.md"


def _source() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def test_operator_harness_compiles_and_has_two_public_stages() -> None:
    source = _source()
    ast.parse(source)
    assert 'subparsers.add_parser("prepare")' in source
    assert 'subparsers.add_parser("resume")' in source
    assert '"_installed-prepare"' in source
    assert '"_installed-resume"' in source
    assert '"-I"' in source
    assert '"pip", "check"' in source
    assert "site-packages" in source


def test_prepare_uses_all_three_groupplan_and_starter_paths() -> None:
    source = _source()
    required = (
        "create_manual_group_plan(",
        "create_signal_group_plan(",
        "create_random_group_plan(",
        "preview_group_plan(",
        "approve_group_plan(",
        "prepare_group_plan_application(",
        "apply_group_plan(",
        'get_starter_template("socratic_seminar")',
        'get_starter_template("project_plan")',
        'get_starter_template("peer_review_writing")',
        "prepare_packet_instantiation(",
        "commit_packet_instantiation(",
        "render_packet_instance(",
        "parse_pds2_payload(",
    )
    for token in required:
        assert token in source
    assert '"seminar": 2, "project": 2, "peer_review": 2' in source
    assert "issue #70 physical sample must contain exactly six packets" in source



def test_prepare_uses_fallback_context_only_for_generated_plans() -> None:
    source = _source()
    seminar_start = source.index('group_plan_id="plan-seminar-issue70-physical"')
    project_start = source.index('group_plan_id="plan-project-issue70-physical"')
    peer_start = source.index('group_plan_id="plan-peer-review-issue70-physical"')

    seminar_section = source[seminar_start:project_start]
    project_section = source[project_start:peer_start]
    peer_section = source[peer_start:]

    assert "fallback_effective_context=seminar_context" not in seminar_section
    assert project_section.count("fallback_effective_context=project_context") == 2
    assert peer_section.count("fallback_effective_context=peer_context") == 2


def test_prepare_preserves_project_privacy_sentinel() -> None:
    source = _source()
    assert "issue70-physical-private-signal-set" in source
    assert "issue70-physical-private-band" in source
    assert "private_canonical_digest" in source
    assert "leaked planning provenance into PDF" in source
    assert "leaked planning provenance into PDS2" in source
    assert "project planning provenance leaked downstream" in source


def test_resume_requires_real_changed_bytes_and_production_intake() -> None:
    source = _source()
    assert "--physical-mark-confirmed" in source
    assert "--visual-inspection-confirmed" in source
    assert "digest in print_hashes" in source
    assert "untouched generated PDF is not physical acceptance evidence" in source
    assert "route_scan_sources(scans, workspace_root=workspace)" in source
    assert "raw_page_decoder" not in source
    assert "scan intake inferred Artifact Review state" in source
    assert "scan intake inferred Score state" in source
    assert "assemble_returned_artifact(" in source
    assert "add_artifact_review(" in source
    assert "add_score(" in source
    assert "publish_concord_academic_results(" in source
    assert "read_academic_result_manifest(" in source


def test_resume_requires_exact_union_of_six_physical_packet_identities() -> None:
    source = _source()
    assert "route_to_case" in source
    assert "expected_pages_by_case" in source
    assert "expected_routes_by_case" in source
    assert "physical route set is incomplete" in source
    assert "physical ArtifactPage set is incomplete" in source
    assert "physical sample must contain two packets" in source


def test_harness_never_auto_declares_physical_pass() -> None:
    source = _source()
    assert "physical seminar: OWNER CLASSIFICATION REQUIRED" in source
    assert "physical group project: OWNER CLASSIFICATION REQUIRED" in source
    assert "physical peer review: OWNER CLASSIFICATION REQUIRED" in source
    assert "physical acceptance: OWNER CLASSIFICATION REQUIRED" in source
    assert "owner_physical_classification_required" in source
    assert "READY FOR #71: NO" in source
    assert "physical acceptance: PASS" not in source


def test_documentation_points_to_persistent_operator_harness() -> None:
    text = DOC.read_text(encoding="utf-8")
    assert "## Persistent operator harness" in text
    assert "run_physical_starter_workflow_acceptance_issue70.py prepare" in text
    assert "run_physical_starter_workflow_acceptance_issue70.py resume" in text
    assert "--physical-mark-confirmed" in text
    assert "--visual-inspection-confirmed" in text
    assert "OWNER CLASSIFICATION REQUIRED" in text
