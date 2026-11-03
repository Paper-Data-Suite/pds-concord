"""Pure, teacher-readable Criterion Set drafts; no workspace or mutation authority.

A draft is neither a native Criterion Set nor a reusable preset. Existing Concord
models and workflow services remain authoritative at the actual commit boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from pds_core.standards import (
    StandardsLibrary,
    find_standards_profile,
    validate_profile_standard_selection,
)

from concord.models import Criterion, CriterionSet, Provenance
from concord.workflows.criterion_sets import CriterionSpec


class GuidedCriterionInputError(ValueError):
    """An invalid teacher-facing draft or unavailable canonical context."""


@dataclass(frozen=True, slots=True)
class CriterionTargetChoice:
    value: str
    label: str
    explanation: str


TARGET_CHOICES: tuple[CriterionTargetChoice, ...] = (
    CriterionTargetChoice(
        "core_student", "Individual student", "A judgment about one Core student."
    ),
    CriterionTargetChoice(
        "concord_group", "Cluster Group", "A judgment about a Concord Group."
    ),
    CriterionTargetChoice(
        "concord_session", "Session", "A judgment about one Session."
    ),
    CriterionTargetChoice(
        "concord_activity", "Whole Activity", "A judgment about the Activity."
    ),
    CriterionTargetChoice(
        "concord_artifact_instance",
        "Specific Artifact",
        "A judgment about one Artifact instance.",
    ),
)
_TARGET_BY_VALUE = {choice.value: choice for choice in TARGET_CHOICES}


@dataclass(frozen=True, slots=True)
class FocusStandardChoice:
    standard_id: str
    code: str
    short_name: str
    description: str

    @property
    def label(self) -> str:
        return f"{self.code} — {self.short_name}"


def focus_standard_choices(
    library: StandardsLibrary,
    profile_id: str,
    focus_standard_ids: tuple[str, ...],
) -> tuple[FocusStandardChoice, ...]:
    """Read exact Activity Focus IDs in order; never invent a Core definition.

    Core enforces profile membership. Concord rejects inactive/deprecated choices
    as its existing graph validation already does for governing Standards.
    """
    try:
        selected = validate_profile_standard_selection(
            library,
            profile_id=profile_id,
            selected_standard_ids=focus_standard_ids,
        )
    except ValueError as error:
        raise GuidedCriterionInputError(
            f"Core Standards profile/Focus selection is unavailable: {error}"
        ) from error
    # The Core helper validates profile membership. Its return contains exact IDs.
    by_id = {item.standard_id: item for item in library.standards}
    choices: list[FocusStandardChoice] = []
    for standard_id in selected:
        definition = by_id[standard_id]
        if not definition.active or "deprecated" in definition.tags:
            raise GuidedCriterionInputError(
                f"Core Focus Standard is inactive or deprecated: {standard_id}"
            )
        choices.append(
            FocusStandardChoice(
                standard_id=standard_id,
                code=definition.code,
                short_name=definition.short_name,
                description=definition.description,
            )
        )
    return tuple(choices)


def target_choice(value: str) -> CriterionTargetChoice:
    """Present one canonical target without changing its stored value."""
    try:
        return _TARGET_BY_VALUE[value]
    except (KeyError, TypeError) as error:
        raise GuidedCriterionInputError(
            f"Unsupported Criterion target kind: {value!r}"
        ) from error


@dataclass(frozen=True, slots=True)
class CriterionDraft:
    key: str
    label: str
    definition: str
    criterion_kind: str
    supported_target_kinds: tuple[str, ...]
    standard_id: str | None = None
    alignment_standard_ids: tuple[str, ...] = ()
    default_scoring_scale_id: str | None = None
    status: str = "active"


@dataclass(frozen=True, slots=True)
class CriterionSetDraft:
    name: str
    purpose: str
    criterion_set_kind: str
    criteria: tuple[CriterionDraft, ...]
    scope: str = "activity_specific"


def add_criterion(draft: CriterionSetDraft, item: CriterionDraft) -> CriterionSetDraft:
    return replace(draft, criteria=(*draft.criteria, item))


def replace_criterion(
    draft: CriterionSetDraft, index: int, item: CriterionDraft
) -> CriterionSetDraft:
    _index(draft, index)
    updated = list(draft.criteria)
    updated[index] = item
    return replace(draft, criteria=tuple(updated))


def remove_criterion(draft: CriterionSetDraft, index: int) -> CriterionSetDraft:
    _index(draft, index)
    return replace(
        draft,
        criteria=tuple(
            item for position, item in enumerate(draft.criteria)
            if position != index
        ),
    )


def move_criterion(
    draft: CriterionSetDraft, source: int, destination: int
) -> CriterionSetDraft:
    _index(draft, source)
    _index(draft, destination)
    if source == destination:
        return draft
    updated = list(draft.criteria)
    item = updated.pop(source)
    updated.insert(destination, item)
    return replace(draft, criteria=tuple(updated))


def _index(draft: CriterionSetDraft, position: int) -> None:
    if type(position) is not int or position < 0 or position >= len(draft.criteria):
        raise GuidedCriterionInputError("Choose an existing Criterion position.")


def criterion_specs(
    draft: CriterionSetDraft, criterion_ids: tuple[str, ...]
) -> tuple[CriterionSpec, ...]:
    """Map approved, caller-issued native IDs into existing workflow input shape.

    This is a pure adapter. It does not generate IDs or authorize a write.
    The caller must validate the complete Activity/Standards context before use.
    """
    if not draft.criteria or len(criterion_ids) != len(draft.criteria):
        raise GuidedCriterionInputError(
            "Provide one new Criterion ID for each nonempty draft Criterion."
        )
    if len(set(criterion_ids)) != len(criterion_ids):
        raise GuidedCriterionInputError("Draft Criterion IDs must be unique.")
    return tuple(
        CriterionSpec(
            criterion_id=criterion_id,
            key=item.key,
            label=item.label,
            definition=item.definition,
            criterion_kind=item.criterion_kind,
            supported_target_kinds=item.supported_target_kinds,
            standard_id=item.standard_id,
            alignment_standard_ids=item.alignment_standard_ids,
            default_scoring_scale_id=item.default_scoring_scale_id,
            status=item.status,
        )
        for criterion_id, item in zip(criterion_ids, draft.criteria, strict=True)
    )


def validate_draft(
    draft: CriterionSetDraft,
    *,
    activity_scoring_orientation: str,
    standards_profile_id: str | None,
    focus_standard_ids: tuple[str, ...],
    standards_library: StandardsLibrary | None,
    created_provenance: Provenance,
) -> None:
    """Check model shape, permitted Activity orientation and canonical Standards.

    Not a replacement for the workflow's graph, snapshot, identity, Scale
    existence, Core roster or durable selected-Set validation at commit time.
    """
    if not draft.criteria:
        raise GuidedCriterionInputError("A rubric requires at least one Criterion.")
    keys = tuple(item.key for item in draft.criteria)
    if len(set(keys)) != len(keys):
        raise GuidedCriterionInputError("Criterion keys must be unique.")
    kinds = {item.criterion_kind for item in draft.criteria}
    if draft.criterion_set_kind == "standard_backed" and kinds != {"standard_backed"}:
        raise GuidedCriterionInputError(
            "A standards-backed rubric needs backed Criteria."
        )
    if draft.criterion_set_kind == "local" and kinds != {"local"}:
        raise GuidedCriterionInputError("A local rubric needs local Criteria.")
    if activity_scoring_orientation == "evidence_only":
        raise GuidedCriterionInputError("Evidence-only Activities cannot use rubrics.")
    if "standard_backed" in kinds and activity_scoring_orientation not in {
        "standards_based",
        "mixed",
    }:
        raise GuidedCriterionInputError(
            "This Activity does not permit standards-backed Criteria."
        )
    if "local" in kinds and activity_scoring_orientation not in {
        "local_criteria_only",
        "mixed",
    }:
        raise GuidedCriterionInputError("This Activity does not permit local Criteria.")

    protected = any(
        item.criterion_kind == "standard_backed" or item.alignment_standard_ids
        for item in draft.criteria
    )
    valid_focus: frozenset[str] = frozenset()
    profile_members: frozenset[str] = frozenset()
    if protected:
        if standards_library is None or standards_profile_id is None:
            raise GuidedCriterionInputError(
                "The Activity's canonical Core Standards Library/profile is required."
            )
        choices = focus_standard_choices(
            standards_library, standards_profile_id, focus_standard_ids
        )
        valid_focus = frozenset(item.standard_id for item in choices)
        profile = find_standards_profile(standards_library, standards_profile_id)
        assert profile is not None  # validated by focus_standard_choices
        profile_members = frozenset(profile.standards)
        definitions = {item.standard_id: item for item in standards_library.standards}
        for item in draft.criteria:
            if (
                item.criterion_kind == "standard_backed"
                and item.standard_id not in valid_focus
            ):
                raise GuidedCriterionInputError(
                    "A governing Standard must belong to the "
                    "Activity's Focus Standards."
                )
            for alignment in item.alignment_standard_ids:
                definition = definitions.get(alignment)
                if (
                    alignment not in profile_members
                    or definition is None
                    or not definition.active
                    or "deprecated" in definition.tags
                ):
                    raise GuidedCriterionInputError(
                        f"Alignment Standard unavailable in active profile: {alignment}"
                    )

    # Construct the actual immutable Concord models with synthetic preview-only
    # IDs. This checks canonical field/enum rules without committing any record.
    ids = tuple(
        f"criterion-preview-{index}"
        for index in range(1, len(draft.criteria) + 1)
    )
    specs = criterion_specs(draft, ids)
    for spec in specs:
        Criterion(
            criterion_id=spec.criterion_id,
            criterion_set_id="criterion-set-preview",
            key=spec.key,
            label=spec.label,
            definition=spec.definition,
            criterion_kind=spec.criterion_kind,
            supported_target_kinds=spec.supported_target_kinds,
            standard_id=spec.standard_id,
            alignment_standard_ids=spec.alignment_standard_ids,
            default_scoring_scale_id=spec.default_scoring_scale_id,
            status=spec.status,
            created_provenance=created_provenance,
        )
    CriterionSet(
        criterion_set_id="criterion-set-preview",
        lineage_id="criterion-set-preview-lineage",
        name=draft.name,
        purpose=draft.purpose,
        revision=1,
        scope=draft.scope,
        criterion_set_kind=draft.criterion_set_kind,
        criterion_ids=ids,
        status="active",
        created_provenance=created_provenance,
        standards_profile_id=(
            standards_profile_id
            if draft.criterion_set_kind in {"standard_backed", "mixed"}
            else None
        ),
    )


def describe_draft(
    draft: CriterionSetDraft,
    *,
    focus_choices: tuple[FocusStandardChoice, ...] = (),
) -> tuple[str, ...]:
    """Complete zero-write teacher preview; no invented Standard descriptions."""
    choices = {item.standard_id: item for item in focus_choices}
    lines: tuple[str, ...] = (
        f"Rubric: {draft.name}",
        f"Purpose: {draft.purpose}",
        f"Kind: {draft.criterion_set_kind}",
        f"Semantic scope: {draft.scope} (not a saved preset)",
        f"Ordered Criteria: {len(draft.criteria)}",
    )
    for index, item in enumerate(draft.criteria, 1):
        target_labels = ", ".join(
            target_choice(value).label for value in item.supported_target_kinds
        )
        standard = choices.get(item.standard_id or "")
        standard_label = (
            "Local — no governing Standard"
            if item.standard_id is None
            else (standard.label if standard else f"{item.standard_id} [unresolved]")
        )
        lines += (
            f"{index}. {item.label} ({item.key}) — {item.criterion_kind}",
            f"   Definition: {item.definition}",
            f"   Permitted targets: {target_labels}",
            f"   Governing Standard: {standard_label}",
            "   Alignment Standards: "
            + (", ".join(item.alignment_standard_ids) or "none"),
            "   Native default Scale ID: "
            + (item.default_scoring_scale_id or "none"),
        )
    return lines + (
        "Draft only: no Criterion Set, Activity selection or preset saved.",
        "No Scores, Grades, evidence, student/Group state or publication created.",
    )
