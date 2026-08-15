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
    if "Released Core baseline:** `pds-core` 0.6.0" not in integration:
        failures.append("Integration requirements do not identify Core v0.6.0.")
    contracts = (
        ROOT / "docs" / "design" / "conceptual-data-contracts.md"
    ).read_text(encoding="utf-8")
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
