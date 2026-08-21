"""Check local Markdown links and active project-status invariants."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
ADR_ROW = re.compile(r"^\| \[\d{4}\].*\| Accepted \|$", re.MULTILINE)
STALE_ACTIVE_PHRASES = (
    "thirteen accepted Architecture Decision Records",
    "ADR 0015 remains **Proposed**",
    "ADR 0015, while Proposed",
    "Released Core baseline:** `pds-core` 0.5.0",
    "Core registry and Academic Period integration remain pre-release",
)
CONTRACT_STATUS = (
    "**Status:** Accepted conceptual contracts; foundation review complete"
)
CONTRACT_DRAFT_STATUS = "**Status:** Draft for foundation review"
EXAMPLE_STATUS = (
    "**Status:** Accepted representative contract examples; validation complete"
)
EXAMPLE_DRAFT_STATUS = "**Status:** Draft for representative-contract validation"
PROPOSED_CHAIN = (
    "The examples also validate the proposed academic-result publication chain"
)
PUBLICATION_DOC = ROOT / "docs" / "implementation" / "academic-result-publication.md"
READER_DOC = ROOT / "docs" / "implementation" / "academic-result-reader.md"
ACCEPTANCE_DOC = ROOT / "docs" / "implementation" / "installed-end-to-end-acceptance.md"
RELEASE_DOCUMENTS = (
    ROOT / "docs" / "v0.2.0-release-audit.md",
    ROOT / "docs" / "v0.2.0-release-compatibility.md",
    ROOT / "docs" / "release_checklist.md",
)
FUTURE_PLAN = ROOT / "docs" / "pds-group-planning-interoperability-development-plan.md"
GROUPING_SIGNAL_DOC = (
    ROOT / "docs" / "v0.3.0-core-grouping-signal-integration.md"
)
GROUP_PLAN_DOC = ROOT / "docs" / "v0.3.0-group-plan-contract.md"
MANUAL_GROUP_PLAN_DOC = ROOT / "docs" / "v0.3.0-manual-group-planning.md"
RANDOM_GROUP_PLAN_DOC = ROOT / "docs" / "v0.3.0-random-group-planning.md"
GROUPING_SIGNAL_WORKFLOW_DOC = (
    ROOT / "docs" / "v0.3.0-grouping-signal-workflows.md"
)
REQUIRED_GROUP_PLAN_DOC_PHRASES = (
    "GroupPlan != Group",
    "record kind: group_plan",
    "draft -> previewed -> approved -> applied",
    "grouping_signal_set_v1",
    "teacher-restricted",
    "#56",
)
REQUIRED_MANUAL_GROUP_PLAN_DOC_PHRASES = (
    "student_id,group",
    "create_manual_group_plan",
    "refresh_group_plan_roster",
    "replace_group_plan_from_arrangement",
    "concord group-plan",
    "Plan groups",
    "GroupPlan approval != Group creation",
    "#56",
)
REQUIRED_RANDOM_GROUP_PLAN_DOC_PHRASES = (
    "create_random_group_plan",
    "pds-concord:group-plan-random:v1",
    "sha256",
    "ceil(N / S)",
    "random-1",
    "concord group-plan create-random",
    "Canonical Groups created: no",
    "Issue #53",
    "Issue #56",
)
REQUIRED_GROUPING_SIGNAL_WORKFLOW_DOC_PHRASES = (
    "grouping_signal_set_v1",
    "list_grouping_signals",
    "inspect_grouping_signal",
    "select_grouping_signal_dimension",
    "prepare_grouping_signal_csv_import",
    "import_grouping_signal_csv",
    "concord grouping-signal",
    "dimension_projection",
    "missing_student_signal",
    "expected_signal_digest",
    "Meridian",
    "Issue #54",
    "Issue #55",
    "Issue #56",
)
REQUIRED_GROUPING_SIGNAL_DOC_PHRASES = (
    "pds-core>=0.6.1,<0.7",
    "grouping_signal_set_v1",
    "pds_core.grouping_signal_storage",
    "pds_core.grouping_signal_diagnostics",
    "source.snapshot_digest",
    "dimension_projection",
    "Meridian",
    "Issue #53",
)
STALE_PUBLICATION_PHRASES = (
    "still does **not** publish academic results",
    "publication remains absent until issue #31",
    "Later issues add publication and consumer integration",
    "the publication entry point remains absent",
    "It does not add Concord publication",
    "Implemented through the v0.2.0 Criterion, Scale, and Score workflow in issue #30.",
)
REQUIRED_PUBLICATION_DOC_PHRASES = (
    "concord_academic_work_v1",
    "concord_activity_v1",
    "concord_academic_result_manifest_v1",
    "academic_results",
    "paper_data_suite.publication_producers",
    "Issue #32",
    "Issue #33",
    "Meridian",
)
REQUIRED_READER_DOC_PHRASES = (
    "concord.academic_result_reader",
    "concord.academic_result_artifacts",
    "read_academic_result_manifest",
    "AcademicResultArtifactAuthorizationGate",
    "source_snapshot_revision",
    "returned_artifact_pdf",
    "Issue #33",
    "Meridian",
    "Vitrine",
)
REQUIRED_ACCEPTANCE_DOC_PHRASES = (
    "pds_core-0.6.0-py3-none-any.whl",
    "be28c061b38463ef59ebc328ed1aa443767fe7f2c626babb769c2d8e5932f308",
    "scripts/verify_installed_producer_acceptance.py",
    "source_snapshot_revision",
    "audit_academic_registry",
    "manifest authorization != Artifact authorization",
    "issue #34",
)


class DocumentationError(ValueError):
    """Raised when repository documentation is internally inconsistent."""


def status_failures(
    text: str,
    *,
    label: str,
    required: str,
    forbidden: tuple[str, ...],
) -> list[str]:
    """Return targeted current-status failures for one active document."""
    failures: list[str] = []
    if required not in text:
        failures.append(f"{label} must contain completed status {required!r}.")
    for phrase in forbidden:
        if phrase in text:
            failures.append(f"{label} contains stale active wording {phrase!r}.")
    return failures


def _link_target(document: Path, raw_target: str) -> Path | None:
    target = raw_target.strip().split(maxsplit=1)[0].strip("<>")
    if target.startswith(("http://", "https://", "mailto:", "#")):
        return None
    path_text = target.split("#", 1)[0]
    if not path_text:
        return None
    return (document.parent / path_text).resolve()


def check_documentation() -> None:
    """Validate repository-relative links, ADR state, and current baseline prose."""
    if not (ROOT / "README.md").is_file():
        raise DocumentationError("Root package README.md is missing.")
    failures: list[str] = []
    for document in sorted(ROOT.rglob("*.md")):
        if any(part.startswith(".") for part in document.relative_to(ROOT).parts):
            continue
        text = document.read_text(encoding="utf-8")
        for match in LINK.finditer(text):
            target = _link_target(document, match.group(1))
            if target is not None and not target.exists():
                failures.append(
                    f"{document.relative_to(ROOT)}: unresolved link {match.group(1)!r}"
                )
    index_path = ROOT / "docs" / "decisions" / "README.md"
    index = index_path.read_text(encoding="utf-8")
    if len(ADR_ROW.findall(index)) != 15:
        failures.append("ADR index must contain exactly fifteen Accepted rows.")
    adr_15 = (
        ROOT
        / "docs"
        / "decisions"
        / (
            "0015-publish-versioned-concord-academic-result-manifests-through-the-core-registry.md"
        )
    )
    if "**Status:** Accepted" not in adr_15.read_text(encoding="utf-8"):
        failures.append("ADR 0015 source document must be Accepted.")
    active_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            ROOT / "docs" / "README.md",
            index_path,
            ROOT / "docs" / "design" / "pds-core-integration-requirements.md",
        )
    )
    for phrase in STALE_ACTIVE_PHRASES:
        if phrase in active_text:
            failures.append(f"Stale active-status phrase remains: {phrase!r}")
    docs_index = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    for release_document in RELEASE_DOCUMENTS:
        if not release_document.is_file():
            relative = release_document.relative_to(ROOT)
            failures.append(
                f"Required release document is missing: {relative}"
            )
        elif release_document.name not in docs_index:
            failures.append(
                f"Documentation index does not link {release_document.name}."
            )
    if not FUTURE_PLAN.is_file():
        failures.append("Future v0.3.0 Group Planning plan is missing.")
    else:
        future_text = FUTURE_PLAN.read_text(encoding="utf-8")
        if "v0.3.0" not in future_text or "future" not in future_text.lower():
            failures.append(
                "Group Planning interoperability plan must remain classified as "
                "future v0.3.0 work."
            )
        if FUTURE_PLAN.name not in docs_index:
            failures.append(
                "Documentation index does not retain the future v0.3.0 plan."
            )
    if not GROUPING_SIGNAL_DOC.is_file():
        failures.append(
            "Current v0.3.0 grouping-signal integration document is missing."
        )
    else:
        grouping_doc = GROUPING_SIGNAL_DOC.read_text(encoding="utf-8")
        for phrase in REQUIRED_GROUPING_SIGNAL_DOC_PHRASES:
            if phrase not in grouping_doc:
                failures.append(
                    "Grouping-signal integration document is missing required "
                    f"boundary wording {phrase!r}."
                )
        if GROUPING_SIGNAL_DOC.name not in docs_index:
            failures.append(
                "Documentation index does not link the grouping-signal "
                "integration document."
            )
    if not GROUP_PLAN_DOC.is_file():
        failures.append("Current v0.3.0 GroupPlan contract document is missing.")
    else:
        group_plan_doc = GROUP_PLAN_DOC.read_text(encoding="utf-8")
        for phrase in REQUIRED_GROUP_PLAN_DOC_PHRASES:
            if phrase not in group_plan_doc:
                failures.append(
                    "GroupPlan contract document is missing required boundary "
                    f"wording {phrase!r}."
                )
        if GROUP_PLAN_DOC.name not in docs_index:
            failures.append(
                "Documentation index does not link the GroupPlan contract document."
            )
    if not MANUAL_GROUP_PLAN_DOC.is_file():
        failures.append("Current v0.3.0 manual Group planning document is missing.")
    else:
        manual_group_plan_doc = MANUAL_GROUP_PLAN_DOC.read_text(encoding="utf-8")
        for phrase in REQUIRED_MANUAL_GROUP_PLAN_DOC_PHRASES:
            if phrase not in manual_group_plan_doc:
                failures.append(
                    "Manual Group planning document is missing required "
                    f"boundary wording {phrase!r}."
                )
        if MANUAL_GROUP_PLAN_DOC.name not in docs_index:
            failures.append(
                "Documentation index does not link the manual Group planning document."
            )
    if not RANDOM_GROUP_PLAN_DOC.is_file():
        failures.append(
            "Current v0.3.0 deterministic random Group planning document is missing."
        )
    else:
        random_group_plan_doc = RANDOM_GROUP_PLAN_DOC.read_text(encoding="utf-8")
        for phrase in REQUIRED_RANDOM_GROUP_PLAN_DOC_PHRASES:
            if phrase not in random_group_plan_doc:
                failures.append(
                    "Random Group planning document is missing required "
                    f"boundary wording {phrase!r}."
                )
        if RANDOM_GROUP_PLAN_DOC.name not in docs_index:
            failures.append(
                "Documentation index does not link the random Group planning document."
            )
    if not GROUPING_SIGNAL_WORKFLOW_DOC.is_file():
        failures.append(
            "Current v0.3.0 grouping-signal workflow document is missing."
        )
    else:
        signal_workflow_doc = GROUPING_SIGNAL_WORKFLOW_DOC.read_text(
            encoding="utf-8"
        )
        for phrase in REQUIRED_GROUPING_SIGNAL_WORKFLOW_DOC_PHRASES:
            if phrase not in signal_workflow_doc:
                failures.append(
                    "Grouping-signal workflow document is missing required "
                    f"boundary wording {phrase!r}."
                )
        if GROUPING_SIGNAL_WORKFLOW_DOC.name not in docs_index:
            failures.append(
                "Documentation index does not link the grouping-signal "
                "workflow document."
            )
    for active_path in (
        ROOT / "README.md",
        ROOT / "docs" / "cli-contract.md",
    ):
        active_group_plan_text = active_path.read_text(encoding="utf-8")
        if "concord group-plan" not in active_group_plan_text:
            failures.append(
                f"{active_path.relative_to(ROOT)} does not expose the GroupPlan CLI."
            )
        if "concord grouping-signal" not in active_group_plan_text:
            failures.append(
                f"{active_path.relative_to(ROOT)} does not expose the "
                "grouping-signal CLI."
            )
    for stale_phrase in (
        "lifecycle application services remain staged within #50",
        "does not make GroupPlan lifecycle/application services",
        "make the #51-#56 planning algorithms",
    ):
        if stale_phrase in docs_index:
            failures.append(
                "Documentation index contains stale GroupPlan wording "
                f"{stale_phrase!r}."
            )
    if not PUBLICATION_DOC.is_file():
        failures.append(
            "Academic result publication implementation document is missing."
        )
    else:
        publication_doc = PUBLICATION_DOC.read_text(encoding="utf-8")
        for phrase in REQUIRED_PUBLICATION_DOC_PHRASES:
            if phrase not in publication_doc:
                failures.append(
                    "Publication implementation document is missing required "
                    f"contract wording {phrase!r}."
                )
    if not READER_DOC.is_file():
        failures.append("Academic result consumer reader document is missing.")
    else:
        reader_doc = READER_DOC.read_text(encoding="utf-8")
        for phrase in REQUIRED_READER_DOC_PHRASES:
            if phrase not in reader_doc:
                failures.append(
                    "Consumer reader implementation document is missing required "
                    f"contract wording {phrase!r}."
                )
    if not ACCEPTANCE_DOC.is_file():
        failures.append("Installed end-to-end acceptance document is missing.")
    else:
        acceptance_doc = ACCEPTANCE_DOC.read_text(encoding="utf-8")
        for phrase in REQUIRED_ACCEPTANCE_DOC_PHRASES:
            if phrase not in acceptance_doc:
                failures.append(
                    "Installed acceptance document is missing required "
                    f"boundary wording {phrase!r}."
                )
    publication_active_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            ROOT / "README.md",
            ROOT / "docs" / "README.md",
            ROOT / "docs" / "cli-contract.md",
        )
    )
    for phrase in STALE_PUBLICATION_PHRASES:
        if phrase in publication_active_text:
            failures.append(f"Stale publication-status phrase remains: {phrase!r}")
    integration = (
        ROOT / "docs" / "design" / "pds-core-integration-requirements.md"
    ).read_text(encoding="utf-8")
    if "Current development Core baseline:** `pds-core` 0.6.1" not in integration:
        failures.append(
            "Integration requirements do not identify Core v0.6.1 "
            "for v0.3 development."
        )
    contracts = (ROOT / "docs" / "design" / "conceptual-data-contracts.md").read_text(
        encoding="utf-8"
    )
    failures.extend(
        status_failures(
            contracts,
            label="Conceptual data contracts",
            required=CONTRACT_STATUS,
            forbidden=(CONTRACT_DRAFT_STATUS,),
        )
    )
    examples = (ROOT / "docs" / "design" / "examples" / "README.md").read_text(
        encoding="utf-8"
    )
    failures.extend(
        status_failures(
            examples,
            label="Representative examples",
            required=EXAMPLE_STATUS,
            forbidden=(EXAMPLE_DRAFT_STATUS, PROPOSED_CHAIN),
        )
    )
    if failures:
        raise DocumentationError("\n".join(failures))


def main() -> int:
    """Run the documentation check."""
    check_documentation()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
