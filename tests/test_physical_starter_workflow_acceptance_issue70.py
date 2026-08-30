from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "v0.3.0-installed-physical-starter-workflow-acceptance.md"
DOC_INDEX = ROOT / "docs" / "README.md"


def _text() -> str:
    return DOC.read_text(encoding="utf-8")


def test_issue70_physical_acceptance_keeps_owner_gate_pending() -> None:
    text = _text()
    assert "Result before the owner performs the cases: `PENDING OWNER`" in text
    assert "physical acceptance: PENDING OWNER" in text
    assert "READY FOR #71: NO" in text
    assert "Automation must never replace `PENDING OWNER`" in text
    assert "issue #70 remains open" in text.casefold()


def test_issue70_document_covers_three_installed_workflows_and_privacy() -> None:
    text = _text()
    for starter_key in (
        "socratic_seminar",
        "project_plan",
        "peer_review_writing",
    ):
        assert starter_key in text
    for planning_path in (
        "manual signal-free GroupPlan",
        "similar_signal GroupPlan",
        "deterministic random signal-free GroupPlan",
    ):
        assert planning_path in text
    assert "Sentinel values" in text
    assert "planning-only" in text
    assert "Starter page counts are derived" in text


def test_issue70_physical_sample_requires_all_three_workflow_families() -> None:
    text = _text()
    required = (
        "six target packets",
        "one participant packet from canonical Group A",
        "both canonical Group-targeted packets",
        "peer review:",
        "Every page of those six selected packets",
        "Physically write `PDS70`",
        "production `route_scan_sources`",
        "physical seminar: PENDING OWNER",
        "physical group project: PENDING OWNER",
        "physical peer review: PENDING OWNER",
    )
    for fragment in required:
        assert fragment in text
    assert "The physical gate covers **all three required starter families**" in text


def test_issue70_physical_case_requires_exact_provenance_and_visual_gate() -> None:
    text = _text()
    required = (
        "same Concord/Core wheel bytes",
        "Concord wheel byte length",
        "printer make/model",
        "scanner make/model",
        "scan resolution (DPI)",
        "physical visual acceptance",
        "--visual-inspection-confirmed",
        "PASS WITH DOCUMENTED LIMITATION",
        "software-contract failure",
        "physical/environment dependency",
    )
    lowered = text.casefold()
    for fragment in required:
        assert fragment.casefold() in lowered
    assert (
        "98d7596ce0eed26e4d56a17bbbbd644db3014259b56a45783a173fe8237af5e5"
        in text
    )


def test_issue70_physical_acceptance_forbids_committing_raw_evidence() -> None:
    text = _text()
    forbidden_artifacts = (
        "raw scans",
        "generated acceptance PDFs",
        "marked paper images",
        "retained physical source files",
        "physical workspace copies",
        "virtual environments",
        "real student data",
    )
    for artifact in forbidden_artifacts:
        assert artifact in text
    index = DOC_INDEX.read_text(encoding="utf-8")
    assert "v0.3.0-installed-physical-starter-workflow-acceptance.md" in index
