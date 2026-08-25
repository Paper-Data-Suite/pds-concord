"""Package-owned starter collaborative-learning Template catalog."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from importlib.resources import files

from concord.models import (
    PrivacyPolicy,
    Provenance,
    TemplateAuthorshipExpectation,
    TemplateCompatibility,
    TemplateDefinition,
    TemplatePageDefinition,
    TemplateRenderingInput,
    TemplateResponseRegion,
    TemplateSubjectExpectation,
    TemplateVersion,
)
from concord.starter_templates.layout import (
    STARTER_LAYOUT_SCHEMA,
    StarterLayoutDocument,
    StarterLayoutPage,
    StarterLayoutSection,
    starter_layout_from_json_bytes,
)

STARTER_TEMPLATE_COUNT = 30
STARTER_TEMPLATE_FAMILIES = (
    "discussion",
    "reading",
    "synthesis",
    "teamwork",
    "project",
    "peer_feedback",
    "science_stem",
    "problem_solving",
    "reflection",
)
_ROUTE_INPUTS = ("human_fallback", "pds2_route_payload")


class StarterTemplateCatalogError(ValueError):
    """The packaged starter Template catalog is invalid."""


class StarterTemplateNotFoundError(StarterTemplateCatalogError):
    """A requested packaged starter Template key is not available."""


@dataclass(frozen=True, slots=True, kw_only=True)
class StarterTemplateCatalogEntry:
    """Package-owned metadata for one ordinary reusable starter Template."""

    starter_key: str
    catalog_order: int
    family: str
    display_name: str
    purpose: str
    description: str
    template_id: str
    template_version_id: str
    rendering_specification_reference: str
    asset_name: str
    artifact_category: str
    page_count: int
    orientation: str
    suggested_audience_kinds: tuple[str, ...]
    suggested_activity_type_keys: tuple[str, ...] = ()
    default_privacy_classification: str = "group_and_teacher"
    default_authorship_mode: str = "collective_group_author"
    default_subject_kind: str = "concord_group"

    def __post_init__(self) -> None:
        for name in (
            "starter_key",
            "family",
            "display_name",
            "purpose",
            "description",
            "template_id",
            "template_version_id",
            "rendering_specification_reference",
            "asset_name",
            "artifact_category",
            "orientation",
            "default_privacy_classification",
            "default_authorship_mode",
            "default_subject_kind",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise StarterTemplateCatalogError(
                    f"{name} must be a non-empty string."
                )
        if (
            isinstance(self.catalog_order, bool)
            or not isinstance(self.catalog_order, int)
            or self.catalog_order <= 0
        ):
            raise StarterTemplateCatalogError(
                "catalog_order must be a positive integer."
            )
        if (
            isinstance(self.page_count, bool)
            or not isinstance(self.page_count, int)
            or self.page_count <= 0
        ):
            raise StarterTemplateCatalogError(
                "page_count must be a positive integer."
            )
        if self.family not in STARTER_TEMPLATE_FAMILIES:
            raise StarterTemplateCatalogError(
                f"unsupported starter family: {self.family}"
            )
        if self.orientation not in {"portrait", "landscape"}:
            raise StarterTemplateCatalogError(
                "orientation must be portrait or landscape."
            )
        if not self.asset_name.endswith(".json"):
            raise StarterTemplateCatalogError(
                "starter rendering asset must be JSON."
            )
        if not self.suggested_audience_kinds:
            raise StarterTemplateCatalogError(
                "suggested_audience_kinds must not be empty."
            )

    def rendering_specification_bytes(self) -> bytes:
        """Return the exact package-owned rendering bytes."""
        resource = files("concord.starter_templates.assets").joinpath(
            self.asset_name
        )
        try:
            data = resource.read_bytes()
        except OSError as error:
            raise StarterTemplateCatalogError(
                f"could not read packaged starter asset {self.asset_name}: "
                f"{error}"
            ) from error
        if not data:
            raise StarterTemplateCatalogError(
                f"packaged starter asset is empty: {self.asset_name}"
            )
        return data

    def rendering_sha256(self) -> str:
        """Return the exact SHA-256 of the packaged rendering bytes."""
        return hashlib.sha256(
            self.rendering_specification_bytes()
        ).hexdigest()

    def layout(self) -> StarterLayoutDocument:
        """Load and strictly validate the exact packaged layout."""
        return starter_layout_from_json_bytes(
            self.rendering_specification_bytes()
        )

    def build_template_records(
        self,
        *,
        created_provenance: Provenance,
        status: str = "active",
    ) -> tuple[TemplateDefinition, TemplateVersion]:
        """Build ordinary #57 Template records from one packaged starter."""
        if status not in {"draft", "active"}:
            raise StarterTemplateCatalogError(
                "starter installation status must be draft or active."
            )
        if not isinstance(created_provenance, Provenance):
            raise StarterTemplateCatalogError(
                "created_provenance must be Provenance."
            )
        layout = self.layout()
        page_manifest = tuple(
            _page_definition(page, index)
            for index, page in enumerate(layout.pages, start=1)
        )
        rendering_inputs = _rendering_inputs(layout)
        definition = TemplateDefinition(
            template_id=self.template_id,
            name=self.display_name,
            purpose=self.purpose,
            artifact_category=self.artifact_category,
            status=status,
            created_provenance=created_provenance,
            description=self.description,
            owner_reference=created_provenance.actor,
        )
        version = TemplateVersion(
            template_version_id=self.template_version_id,
            template_id=self.template_id,
            version_label="Starter v1",
            revision_sequence=1,
            rendering_contract_version=STARTER_LAYOUT_SCHEMA,
            rendering_specification_reference=(
                self.rendering_specification_reference
            ),
            rendering_specification_sha256=self.rendering_sha256(),
            artifact_category=self.artifact_category,
            page_manifest=page_manifest,
            rendering_inputs=rendering_inputs,
            default_expected_return_status="returned_expected",
            default_privacy_policy=PrivacyPolicy(
                classification=self.default_privacy_classification
            ),
            compatibility=TemplateCompatibility(
                audience_kinds=self.suggested_audience_kinds,
                activity_type_keys=self.suggested_activity_type_keys,
            ),
            created_provenance=created_provenance,
            status=status,
            default_authorship_expectation=(
                TemplateAuthorshipExpectation(
                    authorship_mode=self.default_authorship_mode,
                    required=True,
                    multiple_allowed=False,
                )
            ),
            default_subject_expectation=TemplateSubjectExpectation(
                subject_kind=self.default_subject_kind,
                required=True,
                multiple_allowed=False,
            ),
        )
        return definition, version


def _response_region(
    section: StarterLayoutSection,
) -> TemplateResponseRegion | None:
    if section.region_key is None or section.region_kind is None:
        return None
    return TemplateResponseRegion(
        region_key=section.region_key,
        label=section.label,
        region_kind=section.region_kind,
        required=section.required,
        description=section.instructions,
    )


def _page_definition(
    page: StarterLayoutPage,
    sequence: int,
) -> TemplatePageDefinition:
    regions = tuple(
        region
        for section in page.sections
        if (region := _response_region(section)) is not None
    )
    inputs = tuple(
        sorted(set(page.header_input_keys) | set(_ROUTE_INPUTS))
    )
    return TemplatePageDefinition(
        page_key=page.page_key,
        sequence=sequence,
        page_kind="primary" if sequence == 1 else "continuation",
        return_expected=True,
        route_required=True,
        rendering_input_keys=inputs,
        response_regions=regions,
        label=page.title,
        route_payload_input_key="pds2_route_payload",
        human_fallback_input_key="human_fallback",
    )


def _rendering_inputs(
    layout: StarterLayoutDocument,
) -> tuple[TemplateRenderingInput, ...]:
    keys = set(_ROUTE_INPUTS)
    for page in layout.pages:
        keys.update(page.header_input_keys)
    return tuple(_rendering_input(key) for key in sorted(keys))


def _rendering_input(key: str) -> TemplateRenderingInput:
    specs: dict[str, tuple[str, str, str, bool, int | None]] = {
        "activity_title": (
            "Activity",
            "activity_title",
            "text",
            True,
            120,
        ),
        "session_label": (
            "Session",
            "session_label",
            "text",
            False,
            120,
        ),
        "group_label": (
            "Group",
            "group_label",
            "text",
            True,
            120,
        ),
        "participant_display_label": (
            "Participant",
            "participant_display_label",
            "text",
            True,
            120,
        ),
        "current_date": (
            "Date",
            "current_date",
            "date",
            False,
            None,
        ),
        "teacher_prompt": (
            "Prompt / Topic",
            "teacher_text",
            "multiline_text",
            False,
            600,
        ),
        "pds2_route_payload": (
            "PDS2 route payload",
            "pds2_route_payload",
            "text",
            True,
            1000,
        ),
        "human_fallback": (
            "Human fallback",
            "human_fallback",
            "text",
            True,
            160,
        ),
    }
    try:
        label, source, value_kind, required, maximum = specs[key]
    except KeyError as error:
        raise StarterTemplateCatalogError(
            f"unsupported starter rendering input: {key}"
        ) from error
    return TemplateRenderingInput(
        input_key=key,
        label=label,
        source_kind=source,
        value_kind=value_kind,
        required=required,
        max_length=maximum,
    )


def _entry(
    order: int,
    key: str,
    family: str,
    name: str,
    purpose: str,
    description: str,
    artifact_category: str,
    page_count: int,
    orientation: str,
    audience: str,
    *,
    activity_types: tuple[str, ...] = (),
    privacy: str | None = None,
) -> StarterTemplateCatalogEntry:
    participant = audience == "participant"
    return StarterTemplateCatalogEntry(
        starter_key=key,
        catalog_order=order,
        family=family,
        display_name=name,
        purpose=purpose,
        description=description,
        template_id="starter-" + key.replace("_", "-"),
        template_version_id=(
            "starter-" + key.replace("_", "-") + "-v1"
        ),
        rendering_specification_reference=(
            "starter-" + key.replace("_", "-") + "-layout-v1"
        ),
        asset_name=key + ".json",
        artifact_category=artifact_category,
        page_count=page_count,
        orientation=orientation,
        suggested_audience_kinds=(audience,),
        suggested_activity_type_keys=activity_types,
        default_privacy_classification=(
            privacy
            if privacy is not None
            else (
                "teacher_and_subjects"
                if participant
                else "group_and_teacher"
            )
        ),
        default_authorship_mode=(
            "individual_author"
            if participant
            else "collective_group_author"
        ),
        default_subject_kind=(
            "core_student" if participant else "concord_group"
        ),
    )


_CATALOG = (
    _entry(
        1,
        "think_pair_share",
        "discussion",
        "Think–Pair–Share Quick Sheet",
        "Move from individual thinking to partner exchange and revision.",
        "A one-page THINK / PAIR / SHARE organizer for fast collaborative "
        "discussion.",
        "discussion_record",
        1,
        "portrait",
        "participant",
    ),
    _entry(
        2,
        "socratic_seminar",
        "discussion",
        "Socratic Seminar Preparation & Notes",
        "Prepare evidence and questions, track discussion, and reflect.",
        "Two-page seminar preparation, evidence, discussion-note, and "
        "reflection form.",
        "discussion_record",
        2,
        "portrait",
        "participant",
        activity_types=("socratic_seminar",),
    ),
    _entry(
        3,
        "fishbowl_observer",
        "discussion",
        "Fishbowl Observer Sheet",
        "Observe evidence use, listening moves, questions, and key ideas.",
        "A structured observer sheet for inner/outer-circle discussion.",
        "observation",
        1,
        "portrait",
        "participant",
        activity_types=("socratic_seminar",),
    ),
    _entry(
        4,
        "four_corners",
        "discussion",
        "Four Corners Position Tracker",
        "Record an initial position, contrary ideas, and revised reasoning.",
        "A before/after position-and-evidence tracker for Four Corners.",
        "discussion_record",
        1,
        "portrait",
        "participant",
    ),
    _entry(
        5,
        "structured_academic_controversy",
        "discussion",
        "Structured Academic Controversy",
        "Examine competing positions and develop qualified common ground.",
        "A two-page evidence-centered A/B deliberation and consensus form.",
        "discussion_record",
        2,
        "portrait",
        "group",
    ),
    _entry(
        6,
        "save_last_word",
        "discussion",
        "Save the Last Word",
        "Compare peer interpretations before revising a final response.",
        "A passage-centered written record of peer interpretations and "
        "the selector's final word.",
        "discussion_record",
        1,
        "portrait",
        "participant",
    ),
    _entry(
        7,
        "discussion_map",
        "discussion",
        "Discussion Map & Evidence Tracker",
        "Track claims, evidence, questions, connections, and unresolved ideas.",
        "A wide chronological discussion map with a final group synthesis.",
        "discussion_record",
        1,
        "landscape",
        "group",
    ),
    _entry(
        8,
        "talk_moves_observer",
        "discussion",
        "Discussion Observer / Talk-Moves Tracker",
        "Observe evidence use, questioning, paraphrasing, and participation.",
        "A collaboration-quality observation form with specific examples.",
        "observation",
        1,
        "portrait",
        "participant",
        activity_types=("socratic_seminar",),
    ),
    _entry(
        9,
        "jigsaw_expert",
        "reading",
        "Jigsaw Expert Sheet",
        "Become an expert on one source and prepare a concise teach-back.",
        "A source-analysis and home-group teach-back organizer.",
        "student_work",
        1,
        "portrait",
        "participant",
    ),
    _entry(
        10,
        "reciprocal_reading",
        "reading",
        "Reciprocal Reading Roles",
        "Record predicting, clarifying, questioning, and summarizing.",
        "A four-quadrant group reading organizer for reciprocal teaching.",
        "student_work",
        1,
        "portrait",
        "group",
    ),
    _entry(
        11,
        "collaborative_annotation",
        "reading",
        "Collaborative Annotation / Silent Conversation",
        "Notice, question, connect, support or challenge, and respond.",
        "A landscape annotation canvas for written peer conversation.",
        "student_work",
        1,
        "landscape",
        "group",
    ),
    _entry(
        12,
        "gallery_walk",
        "reading",
        "Gallery Walk Notes & Synthesis",
        "Record station observations and synthesize patterns across sources.",
        "A multi-station note catcher with a substantial synthesis area.",
        "student_work",
        1,
        "portrait",
        "participant",
    ),
    _entry(
        13,
        "see_think_wonder",
        "reading",
        "See–Think–Wonder Source Analysis",
        "Separate direct observation, interpretation, and questions.",
        "A three-column source-analysis organizer with evidence synthesis.",
        "student_work",
        1,
        "landscape",
        "participant",
    ),
    _entry(
        14,
        "group_kwl",
        "reading",
        "Group K–W–L / Inquiry Launch",
        "Organize prior knowledge, questions, new learning, and next inquiry.",
        "A group K–W–L chart with evidence and next-question space.",
        "student_work",
        1,
        "landscape",
        "group",
    ),
    _entry(
        15,
        "venn_comparison",
        "synthesis",
        "Venn Comparison",
        "Compare two subjects and explain the most important relationship.",
        "A two-circle Venn organizer with an analytical synthesis strip.",
        "student_work",
        1,
        "landscape",
        "group",
    ),
    _entry(
        16,
        "comparison_matrix",
        "synthesis",
        "Comparison Matrix",
        "Compare subjects across explicit criteria and explain significance.",
        "A dense landscape comparison table for evidence-based analysis.",
        "student_work",
        1,
        "landscape",
        "group",
    ),
    _entry(
        17,
        "concept_map",
        "synthesis",
        "Concept Map / Connection Web",
        "Map concepts, evidence, and labeled relationships.",
        "An open connection-web drawing area with written synthesis.",
        "student_work",
        1,
        "landscape",
        "group",
    ),
    _entry(
        18,
        "decision_matrix",
        "synthesis",
        "Consensus / Decision Matrix",
        "Compare options, tradeoffs, evidence, and remaining uncertainty.",
        "A group decision matrix with a prominent rationale area.",
        "student_work",
        1,
        "landscape",
        "group",
    ),
    _entry(
        19,
        "group_roles",
        "teamwork",
        "Group Roles & Responsibilities",
        "Assign task roles, responsibilities, products, and checkpoints.",
        "A group role/member/responsibility table using suggested role labels.",
        "project_record",
        1,
        "portrait",
        "group",
        activity_types=("project",),
    ),
    _entry(
        20,
        "team_contract",
        "teamwork",
        "Team Contract & Norms",
        "Agree on participation, communication, quality, and conflict norms.",
        "A concise team agreement with written commitments.",
        "project_record",
        2,
        "portrait",
        "group",
        activity_types=("project",),
    ),
    _entry(
        21,
        "project_plan",
        "project",
        "Project Plan & Task Tracker",
        "Plan objectives, milestones, task owners, dependencies, and status.",
        "A landscape project board for recurring collaborative work.",
        "project_record",
        1,
        "landscape",
        "group",
        activity_types=("project",),
    ),
    _entry(
        22,
        "project_check_in",
        "project",
        "Project Check-In / Meeting Record",
        "Record progress, decisions, blockers, owners, and next actions.",
        "A fast recurring meeting record for project groups.",
        "project_record",
        1,
        "portrait",
        "group",
        activity_types=("project",),
    ),
    _entry(
        23,
        "peer_review_writing",
        "peer_feedback",
        "Peer Review — Writing",
        "Give specific evidence-based feedback and record a revision plan.",
        "Reader feedback plus author response and revision planning.",
        "observation",
        2,
        "portrait",
        "participant",
    ),
    _entry(
        24,
        "peer_review_presentation",
        "peer_feedback",
        "Peer Review — Presentation / Product",
        "Give actionable feedback on clarity, evidence, organization, and design.",
        "A one-page structured review with creator response.",
        "observation",
        1,
        "portrait",
        "participant",
        activity_types=("project",),
    ),
    _entry(
        25,
        "peer_design_code_review",
        "peer_feedback",
        "Peer Design / Code Review",
        "Test intended behavior, document evidence, suggest change, and retest.",
        "A landscape engineering-style design/code review record.",
        "observation",
        1,
        "landscape",
        "participant",
        activity_types=("project",),
    ),
    _entry(
        26,
        "lab_investigation",
        "science_stem",
        "Laboratory Investigation Organizer",
        "Plan an investigation and record data, anomalies, and next questions.",
        "Two-page laboratory planning and evidence organizer.",
        "laboratory_record",
        2,
        "portrait",
        "group",
        activity_types=("laboratory",),
    ),
    _entry(
        27,
        "claim_evidence_reasoning",
        "science_stem",
        "Claim–Evidence–Reasoning Scientific Argument",
        "Develop and revise a claim using selected evidence and reasoning.",
        "A collaborative CER evidence, reasoning, challenge, and revision form.",
        "laboratory_record",
        1,
        "portrait",
        "group",
        activity_types=("laboratory",),
    ),
    _entry(
        28,
        "collaborative_problem_solving",
        "problem_solving",
        "Collaborative Problem-Solving Record",
        "Document knowns, strategies, tests, revisions, and verification.",
        "A landscape staged problem-solving record for STEM and computing.",
        "student_work",
        1,
        "landscape",
        "group",
    ),
    _entry(
        29,
        "collaborative_work_reflection",
        "reflection",
        "Collaborative Work Reflection",
        "Reflect on contribution, teamwork evidence, obstacles, and next steps.",
        "An individual post-collaboration reflection with written evidence.",
        "student_work",
        1,
        "portrait",
        "participant",
    ),
    _entry(
        30,
        "team_health_check",
        "reflection",
        "Team Health / Contribution Check",
        "Reflect confidentially on participation, follow-through, and concerns.",
        "A compact teacher-restricted collaboration health check.",
        "observation",
        1,
        "portrait",
        "participant",
        privacy="teacher_restricted",
    ),
)


def list_starter_templates() -> tuple[StarterTemplateCatalogEntry, ...]:
    """Return all packaged starters in deterministic catalog order."""
    return _CATALOG


def get_starter_template(
    starter_key: str,
) -> StarterTemplateCatalogEntry:
    """Return one exact packaged starter by stable key."""
    match = next(
        (item for item in _CATALOG if item.starter_key == starter_key),
        None,
    )
    if match is None:
        raise StarterTemplateNotFoundError(
            f"starter Template is not available: {starter_key}"
        )
    return match


def validate_starter_catalog() -> None:
    """Fail closed on packaged starter metadata or asset drift."""
    if len(_CATALOG) != STARTER_TEMPLATE_COUNT:
        raise StarterTemplateCatalogError(
            f"starter catalog must contain {STARTER_TEMPLATE_COUNT} entries."
        )
    fields = {
        "starter_key": tuple(item.starter_key for item in _CATALOG),
        "catalog_order": tuple(item.catalog_order for item in _CATALOG),
        "template_id": tuple(item.template_id for item in _CATALOG),
        "template_version_id": tuple(
            item.template_version_id for item in _CATALOG
        ),
        "rendering_specification_reference": tuple(
            item.rendering_specification_reference for item in _CATALOG
        ),
        "asset_name": tuple(item.asset_name for item in _CATALOG),
    }
    for field_name, values in fields.items():
        if len(set(values)) != len(values):
            raise StarterTemplateCatalogError(
                f"starter catalog duplicates {field_name}."
            )
    if fields["catalog_order"] != tuple(
        range(1, STARTER_TEMPLATE_COUNT + 1)
    ):
        raise StarterTemplateCatalogError(
            "starter catalog order must be contiguous 1..30."
        )
    for entry in _CATALOG:
        layout = entry.layout()
        if len(layout.pages) != entry.page_count:
            raise StarterTemplateCatalogError(
                f"{entry.starter_key} page_count disagrees with its asset."
            )
        orientations = {page.orientation for page in layout.pages}
        if orientations != {entry.orientation}:
            raise StarterTemplateCatalogError(
                f"{entry.starter_key} orientation disagrees with its asset."
            )


validate_starter_catalog()


__all__ = [
    "STARTER_TEMPLATE_COUNT",
    "STARTER_TEMPLATE_FAMILIES",
    "StarterTemplateCatalogEntry",
    "StarterTemplateCatalogError",
    "StarterTemplateNotFoundError",
    "get_starter_template",
    "list_starter_templates",
    "validate_starter_catalog",
]
