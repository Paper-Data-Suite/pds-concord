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
SIGNAL_GROUP_PLAN_DOC = ROOT / "docs" / "v0.3.0-signal-group-planning.md"
MISSING_SIGNAL_DISPOSITION_DOC = (
    ROOT / "docs" / "v0.3.0-missing-signal-disposition.md"
)
GROUP_PLAN_APPLICATION_DOC = (
    ROOT / "docs" / "v0.3.0-group-plan-application.md"
)
TEMPLATE_DEFINITION_CONTRACT_DOC = (
    ROOT / "docs" / "v0.3.0-template-definition-contract.md"
)
TEMPLATE_STORAGE_WORKFLOW_DOC = (
    ROOT / "docs" / "v0.3.0-template-storage-revision-workflows.md"
)
PACKET_DEFINITION_CONTRACT_DOC = (
    ROOT / "docs" / "v0.3.0-packet-definition-contract.md"
)
PACKET_STORAGE_WORKFLOW_DOC = (
    ROOT / "docs" / "v0.3.0-packet-storage-revision-workflows.md"
)
STARTER_TEMPLATE_LIBRARY_DOC = (
    ROOT / "docs" / "v0.3.0-starter-template-library.md"
)
PACKET_INSTANTIATION_RENDERING_DOC = (
    ROOT / "docs" / "v0.3.0-packet-instantiation-rendering.md"
)
ACTIVITY_COPYING_DOC = ROOT / "docs" / "v0.3.0-activity-copying.md"
REUSABLE_PRESETS_DOC = (
    ROOT / "docs" / "v0.3.0-reusable-role-responsibility-scoring-presets.md"
)
GUIDED_ACTIVITY_WORKFLOW_DOC = (
    ROOT / "docs" / "v0.3.0-guided-create-classroom-activity.md"
)

TASK_ORIENTED_ACTIVITY_MENU_DOC = (
    ROOT / "docs" / "v0.3.0-task-oriented-activity-menus.md"
)
REQUIRED_PACKET_INSTANTIATION_RENDERING_PHRASES = (
    'PacketInstance',
    'PacketTargetContext',
    'generation_id',
    'review_digest',
    'prepare_packet_instantiation',
    'commit_packet_instantiation',
    'resume_packet_instantiation',
    'render_packet_generation',
    'render_packet_instance',
    'concord packet instantiate-preview',
    'concord packet instantiate',
    'concord packet instantiate-resume',
    'concord packet instance-list',
    'concord packet instance-show',
    'concord packet instance-render',
    'concord packet generation-render',
    'Prepare / Generate Packet',
    'concord_starter_layout_v1',
    'external_component',
    'teacher_restricted',
    'artifact_page',
    '35 rendered physical pages',
    '26146b994a273a0ab377846494f5498bf2f16017e6c95b779540d976722874e9',
    'Core 0.6.3',
    'Issue #63',
    'Issue #64',
)
REQUIRED_GUIDED_ACTIVITY_WORKFLOW_PHRASES = (
    "Create Classroom Activity",
    "Continue setup",
    "inspect_guided_activity_setup",
    "No persistent `WizardState`",
    "Information Density and screen-refresh contract",
    "Clearing/redrawing the screen is the default",
    "prepare_packet_from_template",
    "commit_packet_from_template",
    "GroupPlan != Group != GroupMembership",
    "Score != reusable configuration",
    "scripts/smoke_test_guided_activity_wheel.py",
    "pds-core>=0.6.3,<0.7",
)

REQUIRED_TASK_ORIENTED_ACTIVITY_MENU_PHRASES = (
    "Plan",
    "Prepare",
    "Collect",
    "Review",
    "Score",
    "Share",
    "assessment setup != Score",
    "Advanced Activity tools",
    "GroupPlan != Group != GroupMembership",
    "Clearing/redrawing the screen is the default",
    "Where does the teacher go to do a task?",
    "What currently needs the teacher's attention?",
    "publication != downstream ingestion",
    "presentation routing != domain mutation logic",
    "scripts/smoke_test_task_oriented_activity_menu_wheel.py",
    "pds-core>=0.6.3,<0.7",
)
REQUIRED_REUSABLE_PRESETS_PHRASES = (
    "concord_reusable_preset_library_v1",
    "shared/concord/reusable-presets/",
    "Role preset != RoleAssignment",
    "Responsibility preset != ResponsibilityAssignment",
    "Score != reusable configuration",
    "prepare_scoring_setup",
    "materialize_scoring_setup",
    "save_role_preset_from_assignment",
    "concord role-preset",
    "Reusable Presets",
    "pds-core>=0.6.3,<0.7",
    "scripts/smoke_test_reusable_presets_wheel.py",
)
REQUIRED_ACTIVITY_COPYING_PHRASES = (
    "copy Activity configuration != clone Activity state",
    "prepare_activity_copy",
    "copy_activity",
    "review_digest",
    "criterion_set_ids = ()",
    "external_reference_ids = ()",
    "teacher_restricted",
    "concord activity copy-preview",
    "concord activity copy",
    "COPY",
    "pds-core>=0.6.3,<0.7",
    "pds_core-0.6.3-py3-none-any.whl",
)
REQUIRED_STARTER_TEMPLATE_LIBRARY_PHRASES = (
    "30",
    "concord_starter_layout_v1",
    "concord template starter-list",
    "concord template starter-show",
    "concord template starter-install",
    "concord template starter-install-all",
    "StarterTemplateInstallAllPartialSuccessError",
    "shared/concord/templates/",
    "already_installed",
    "teacher_restricted",
    "Think–Pair–Share Quick Sheet",
    "Structured Academic Controversy",
    "Collaborative Annotation / Silent Conversation",
    "Peer Design / Code Review",
    "Claim–Evidence–Reasoning Scientific Argument",
    "Team Health / Contribution Check",
    "#62",
    "#64",
)
REQUIRED_PACKET_STORAGE_WORKFLOW_PHRASES = (
    "concord_packet_library_storage_v1",
    "shared/concord/packets/",
    "concord_packet_authoring_v1",
    "create_packet_library",
    "create_successor_packet_version",
    "activate_packet_version",
    "current_packet_version_id",
    "head_packet_version_id",
    "expected_snapshot_revision",
    "PacketVersion.revision_sequence",
    "record_revision",
    "PacketStoragePartialSuccessError",
    "concord packet create",
    "Packet Library",
    "ModuleRecordRef",
    "#62",
)
REQUIRED_PACKET_DEFINITION_CONTRACT_PHRASES = (
    "PacketDefinition",
    "PacketVersion",
    "PacketComponent",
    "PacketAudienceIntent",
    "PacketCondition",
    "PacketRenderingRules",
    "copies_per_target",
    "ModuleRecordRef",
    "concord_template",
    "external_component",
    "ROLE_KEYS",
    "PacketDefinition != PacketVersion",
    "PacketVersion != PacketInstance",
    "grouping-signal",
    "#60",
    "#62",
    "#64",
)
REQUIRED_TEMPLATE_STORAGE_WORKFLOW_PHRASES = (
    "concord_template_library_storage_v1",
    "shared/concord/templates/",
    "concord_template_authoring_v1",
    "create_template_library",
    "create_successor_template_version",
    "activate_template_version",
    "current_template_version_id",
    "head_template_version_id",
    "expected_snapshot_revision",
    "rendering-specifications/",
    "Template Version != storage record revision",
    "concord template create",
    "Template Library",
    "Issue #59",
    "Issue #62",
)
REQUIRED_TEMPLATE_DEFINITION_CONTRACT_PHRASES = (
    "TemplateDefinition",
    "TemplateVersion",
    "TemplatePageDefinition",
    "TemplateRenderingInput",
    "TemplateResponseRegion",
    "TemplateCompatibility",
    "rendering_specification_sha256",
    "pds2_route_payload",
    "human_fallback",
    "supported_criterion_ids",
    "grouping_signal_set_v1",
    "TemplateVersion != ArtifactInstance",
    "TemplatePageDefinition != ArtifactPage",
    "Issue #58 now",
    "Issue #57 did not implement",
)
REQUIRED_GROUP_PLAN_APPLICATION_DOC_PHRASES = (
    "group_plan_application_preview_v1",
    "pds-concord:group-plan-application-preview:v1",
    "pds-concord:group-plan-application-group:v1",
    "pds-concord:group-plan-application-membership:v1",
    "prepare_group_plan_application",
    "apply_group_plan",
    "applied_application_id",
    "applied_application_digest",
    "commit_record_batch",
    "concord group-plan application-preview",
    "concord group-plan apply",
    "leave_unassigned",
    "APPLY",
    "Meridian",
)
REQUIRED_MISSING_SIGNAL_DISPOSITION_DOC_PHRASES = (
    "missing_signal_disposition",
    "missing_signal_random_seed",
    "missing_signal_disposition_provenance",
    "missing_student_signal",
    "select_grouping_signal_dimension",
    "pds-concord:group-plan-missing-signal-random:v1",
    "leave_unassigned",
    "concord group-plan confirm-missing-manual",
    "concord group-plan distribute-missing-random",
    "concord group-plan leave-missing-unassigned",
    "Canonical Groups created: no",
    "Issue #56",
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
REQUIRED_SIGNAL_GROUP_PLAN_DOC_PHRASES = (
    "create_signal_group_plan",
    "generate_similar_signal_group_plan_proposal",
    "generate_mixed_signal_group_plan_proposal",
    "ceil(N / S)",
    "similar-1",
    "mixed-1",
    "source_signal_set_digest",
    "concord group-plan create-similar-signal",
    "concord group-plan create-mixed-signal",
    "Canonical Groups created: no",
    "missing signal != lowest band",
    "Meridian",
    "Issue #55",
    "Issue #56",
)
REQUIRED_GROUPING_SIGNAL_DOC_PHRASES = (
    "pds-core>=0.6.3,<0.7",
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
    if not SIGNAL_GROUP_PLAN_DOC.is_file():
        failures.append(
            "Current v0.3.0 signal-backed Group planning document is missing."
        )
    else:
        signal_group_plan_doc = SIGNAL_GROUP_PLAN_DOC.read_text(encoding="utf-8")
        for phrase in REQUIRED_SIGNAL_GROUP_PLAN_DOC_PHRASES:
            if phrase not in signal_group_plan_doc:
                failures.append(
                    "Signal-backed Group planning document is missing required "
                    f"boundary wording {phrase!r}."
                )
        if SIGNAL_GROUP_PLAN_DOC.name not in docs_index:
            failures.append(
                "Documentation index does not link the signal-backed Group "
                "planning document."
            )
    if not MISSING_SIGNAL_DISPOSITION_DOC.is_file():
        failures.append(
            "Current v0.3.0 missing-signal disposition document is missing."
        )
    else:
        missing_signal_doc = MISSING_SIGNAL_DISPOSITION_DOC.read_text(
            encoding="utf-8"
        )
        for phrase in REQUIRED_MISSING_SIGNAL_DISPOSITION_DOC_PHRASES:
            if phrase not in missing_signal_doc:
                failures.append(
                    "Missing-signal disposition document is missing required "
                    f"boundary wording {phrase!r}."
                )
        if MISSING_SIGNAL_DISPOSITION_DOC.name not in docs_index:
            failures.append(
                "Documentation index does not link the missing-signal "
                "disposition document."
            )
    if not GROUP_PLAN_APPLICATION_DOC.is_file():
        failures.append(
            "Current v0.3.0 GroupPlan application document is missing."
        )
    else:
        application_doc = GROUP_PLAN_APPLICATION_DOC.read_text(encoding="utf-8")
        for phrase in REQUIRED_GROUP_PLAN_APPLICATION_DOC_PHRASES:
            if phrase not in application_doc:
                failures.append(
                    "GroupPlan application document is missing required "
                    f"boundary wording {phrase!r}."
                )
        if GROUP_PLAN_APPLICATION_DOC.name not in docs_index:
            failures.append(
                "Documentation index does not link the GroupPlan application document."
            )
    if not TEMPLATE_DEFINITION_CONTRACT_DOC.is_file():
        failures.append(
            "Current v0.3.0 Template Definition contract document is missing."
        )
    else:
        template_contract_doc = TEMPLATE_DEFINITION_CONTRACT_DOC.read_text(
            encoding="utf-8"
        )
        for phrase in REQUIRED_TEMPLATE_DEFINITION_CONTRACT_PHRASES:
            if phrase not in template_contract_doc:
                failures.append(
                    "Template Definition contract document is missing required "
                    f"boundary wording {phrase!r}."
                )
        if TEMPLATE_DEFINITION_CONTRACT_DOC.name not in docs_index:
            failures.append(
                "Documentation index does not link the Template Definition "
                "contract document."
            )
    if not TEMPLATE_STORAGE_WORKFLOW_DOC.is_file():
        failures.append(
            "Current v0.3.0 Template storage/revision workflow document is missing."
        )
    else:
        template_storage_doc = TEMPLATE_STORAGE_WORKFLOW_DOC.read_text(
            encoding="utf-8"
        )
        for phrase in REQUIRED_TEMPLATE_STORAGE_WORKFLOW_PHRASES:
            if phrase not in template_storage_doc:
                failures.append(
                    "Template storage/revision document is missing required "
                    f"boundary wording {phrase!r}."
                )
        if TEMPLATE_STORAGE_WORKFLOW_DOC.name not in docs_index:
            failures.append(
                "Documentation index does not link the Template storage/revision "
                "workflow document."
            )
    if not PACKET_DEFINITION_CONTRACT_DOC.is_file():
        failures.append(
            "Current v0.3.0 Packet Definition contract document is missing."
        )
    else:
        packet_contract_doc = PACKET_DEFINITION_CONTRACT_DOC.read_text(
            encoding="utf-8"
        )
        for phrase in REQUIRED_PACKET_DEFINITION_CONTRACT_PHRASES:
            if phrase not in packet_contract_doc:
                failures.append(
                    "Packet Definition contract document is missing required "
                    f"boundary wording {phrase!r}."
                )
        if PACKET_DEFINITION_CONTRACT_DOC.name not in docs_index:
            failures.append(
                "Documentation index does not link the Packet Definition "
                "contract document."
            )
    if not PACKET_STORAGE_WORKFLOW_DOC.is_file():
        failures.append(
            "Current v0.3.0 Packet storage/revision workflow document is missing."
        )
    else:
        packet_storage_doc = PACKET_STORAGE_WORKFLOW_DOC.read_text(
            encoding="utf-8"
        )
        for phrase in REQUIRED_PACKET_STORAGE_WORKFLOW_PHRASES:
            if phrase not in packet_storage_doc:
                failures.append(
                    "Packet storage/revision document is missing required "
                    f"boundary wording {phrase!r}."
                )
        if PACKET_STORAGE_WORKFLOW_DOC.name not in docs_index:
            failures.append(
                "Documentation index does not link the Packet storage/revision "
                "workflow document."
            )
    if not STARTER_TEMPLATE_LIBRARY_DOC.is_file():
        failures.append(
            "Current v0.3.0 starter Template library document is missing."
        )
    else:
        starter_doc = STARTER_TEMPLATE_LIBRARY_DOC.read_text(encoding="utf-8")
        for phrase in REQUIRED_STARTER_TEMPLATE_LIBRARY_PHRASES:
            if phrase not in starter_doc:
                failures.append(
                    "Starter Template library document is missing required "
                    f"boundary wording {phrase!r}."
                )
        if STARTER_TEMPLATE_LIBRARY_DOC.name not in docs_index:
            failures.append(
                "Documentation index does not link the starter Template "
                "library document."
            )
    if not PACKET_INSTANTIATION_RENDERING_DOC.is_file():
        failures.append(
            "Current v0.3.0 Packet instantiation/rendering document is missing."
        )
    else:
        packet_generation_doc = PACKET_INSTANTIATION_RENDERING_DOC.read_text(
            encoding="utf-8"
        )
        for phrase in REQUIRED_PACKET_INSTANTIATION_RENDERING_PHRASES:
            if phrase not in packet_generation_doc:
                failures.append(
                    "Packet instantiation/rendering document is missing required "
                    f"boundary wording {phrase!r}."
                )
        if PACKET_INSTANTIATION_RENDERING_DOC.name not in docs_index:
            failures.append(
                "Documentation index does not link the Packet "
                "instantiation/rendering document."
            )
    if not ACTIVITY_COPYING_DOC.is_file():
        failures.append("Current v0.3.0 Activity-copying document is missing.")
    else:
        activity_copy_doc = ACTIVITY_COPYING_DOC.read_text(encoding="utf-8")
        for phrase in REQUIRED_ACTIVITY_COPYING_PHRASES:
            if phrase not in activity_copy_doc:
                failures.append(
                    "Activity-copying document is missing required boundary "
                    f"wording {phrase!r}."
                )
        if ACTIVITY_COPYING_DOC.name not in docs_index:
            failures.append(
                "Documentation index does not link the Activity-copying document."
            )
    if not REUSABLE_PRESETS_DOC.is_file():
        failures.append("Current v0.3.0 reusable-preset document is missing.")
    else:
        reusable_presets_doc = REUSABLE_PRESETS_DOC.read_text(encoding="utf-8")
        for phrase in REQUIRED_REUSABLE_PRESETS_PHRASES:
            if phrase not in reusable_presets_doc:
                failures.append(
                    "Reusable-preset document is missing required boundary "
                    f"wording {phrase!r}."
                )
        if REUSABLE_PRESETS_DOC.name not in docs_index:
            failures.append(
                "Documentation index does not link the reusable-preset document."
            )
    if not GUIDED_ACTIVITY_WORKFLOW_DOC.is_file():
        failures.append(
            "Current v0.3.0 guided Activity workflow document is missing."
        )
    else:
        guided_activity_doc = GUIDED_ACTIVITY_WORKFLOW_DOC.read_text(
            encoding="utf-8"
        )
        for phrase in REQUIRED_GUIDED_ACTIVITY_WORKFLOW_PHRASES:
            if phrase not in guided_activity_doc:
                failures.append(
                    "Guided Activity workflow document is missing required "
                    f"boundary wording {phrase!r}."
                )
        if GUIDED_ACTIVITY_WORKFLOW_DOC.name not in docs_index:
            failures.append(
                "Documentation index does not link the guided Activity document."
            )

    if not TASK_ORIENTED_ACTIVITY_MENU_DOC.is_file():
        failures.append(
            "Current v0.3.0 task-oriented Activity menu document is missing."
        )
    else:
        task_menu_doc = TASK_ORIENTED_ACTIVITY_MENU_DOC.read_text(
            encoding="utf-8"
        )
        for phrase in REQUIRED_TASK_ORIENTED_ACTIVITY_MENU_PHRASES:
            if phrase not in task_menu_doc:
                failures.append(
                    "Task-oriented Activity menu document is missing required "
                    f"boundary wording {phrase!r}."
                )
        if TASK_ORIENTED_ACTIVITY_MENU_DOC.name not in docs_index:
            failures.append(
                "Documentation index does not link the task-oriented Activity "
                "menu document."
            )

    for active_path in (
        ROOT / "README.md",
        ROOT / "docs" / "cli-contract.md",
    ):
        active_group_plan_text = active_path.read_text(encoding="utf-8")
        if "Create Classroom Activity" not in active_group_plan_text:
            failures.append(
                f"{active_path.relative_to(ROOT)} does not expose guided "
                "Activity setup."
            )
        if "concord group-plan" not in active_group_plan_text:
            failures.append(
                f"{active_path.relative_to(ROOT)} does not expose the GroupPlan CLI."
            )
        if "concord grouping-signal" not in active_group_plan_text:
            failures.append(
                f"{active_path.relative_to(ROOT)} does not expose the "
                "grouping-signal CLI."
            )
        if "concord group-plan application-preview" not in active_group_plan_text:
            failures.append(
                f"{active_path.relative_to(ROOT)} does not expose GroupPlan "
                "application preview."
            )
        if "concord group-plan apply" not in active_group_plan_text:
            failures.append(
                f"{active_path.relative_to(ROOT)} does not expose GroupPlan apply."
            )
        if "concord activity copy-preview" not in active_group_plan_text:
            failures.append(
                f"{active_path.relative_to(ROOT)} does not expose Activity "
                "copy preview."
            )
        if "concord role-preset" not in active_group_plan_text:
            failures.append(
                f"{active_path.relative_to(ROOT)} does not expose reusable presets."
            )
        if "concord activity copy" not in active_group_plan_text:
            failures.append(
                f"{active_path.relative_to(ROOT)} does not expose Activity copy."
            )
        if "concord template create" not in active_group_plan_text:
            failures.append(
                f"{active_path.relative_to(ROOT)} does not expose the Template CLI."
            )
        if "concord packet create" not in active_group_plan_text:
            failures.append(
                f"{active_path.relative_to(ROOT)} does not expose the Packet CLI."
            )
        if "concord template starter-list" not in active_group_plan_text:
            failures.append(
                f"{active_path.relative_to(ROOT)} does not expose the "
                "starter Template CLI."
            )
    for stale_phrase in (
        "lifecycle application services remain staged within #50",
        "does not make GroupPlan lifecycle/application services",
        "make the #51-#56 planning algorithms",
        "Missing-signal disposition remains reserved for #55",
        "#48-#54 foundations",
        "#48-#55 foundations",
        "#48-#56 foundations",
        "#48-#57 foundations",
        "#48-#58 foundations",
        "#48-#59 foundations",
        "#48-#60 foundations",
        "#48-#61 foundations",
        "#48-#62 foundations",
        "#48-#63 foundations",
        "canonical plan application remains reserved for #56",
        "canonical Template storage and revision workflows remain #58",
        "Template Definition / Template Version remain wholly undefined",
        "there is no `group-plan\napply` command",
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
    if "Current development Core baseline:** `pds-core` 0.6.3" not in integration:
        failures.append(
            "Integration requirements do not identify Core v0.6.3 "
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
