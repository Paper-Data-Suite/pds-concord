"""Zero-write native-to-preset Scale mapping guidance for Concord teachers.

This is a presentation/decision adapter, not a preset or storage authority.
The existing reviewed preset-save services own persistence and replay guards.
"""

from __future__ import annotations

from dataclasses import dataclass

from concord.models import Criterion
from concord.models.common import scalar_key
from concord.models.scoring import ScoringScaleLevel
from concord.reusable_presets import ScoringScalePresetRevision
from concord.workflows.scoring_scales import ScoringScaleDetail


@dataclass(frozen=True, slots=True)
class NativeScaleMappingAssessment:
    """One exact native default, or an explicit omission reason."""

    default_ids: tuple[str, ...]
    native_scale_id: str | None
    notice: str


def assess_native_defaults(
    criteria: tuple[Criterion, ...],
) -> NativeScaleMappingAssessment:
    """Preserve first-seen native defaults; never arbitrarily pick one of many."""
    distinct: list[str] = []
    for criterion in criteria:
        default_id = criterion.default_scoring_scale_id
        if default_id is not None and default_id not in distinct:
            distinct.append(default_id)
    defaults = tuple(distinct)
    if not defaults:
        return NativeScaleMappingAssessment(
            default_ids=(),
            native_scale_id=None,
            notice=(
                "No native default Scoring Scale is defined; "
                "no Scale preset recommendation is needed."
            ),
        )
    if len(defaults) > 1:
        return NativeScaleMappingAssessment(
            default_ids=defaults,
            native_scale_id=None,
            notice=(
                "Multiple distinct native default Scales are in this rubric. "
                "The existing preset service supports only one recommended Scale; "
                "native Scale links will be excluded from the saved definition."
            ),
        )
    return NativeScaleMappingAssessment(
        default_ids=defaults,
        native_scale_id=defaults[0],
        notice=(
            "One native default Scale is present. Only an exact, typed, "
            "existing Scale-preset revision may be recommended."
        ),
    )


def _typed_level(level: ScoringScaleLevel) -> tuple[object, ...]:
    """Values are typed: 1, 1.0, '1' and True remain distinct."""
    value = level.value
    return (
        scalar_key(value),
        level.label,
        level.meaning,
        level.position,
        level.description,
    )


def matches_native_scale(
    native: ScoringScaleDetail,
    preset: ScoringScalePresetRevision,
) -> bool:
    """Conservative exact definition match; never infer an equivalent Scale.

    Identity/name/provenance can differ because the preset is reusable. All
    scoring semantics, ordered typed levels, and guidance must agree exactly.
    """
    return (
        preset.status == "active"
        and native.summary.scale_type == preset.scale_type
        and native.summary.intended_use == preset.intended_use
        and native.aggregation_guidance == preset.aggregation_guidance
        and tuple(map(_typed_level, native.levels))
        == tuple(map(_typed_level, preset.levels))
    )


def scale_mapping_receipt(
    assessment: NativeScaleMappingAssessment,
    *,
    preset_id: str | None,
    preset_revision_id: str | None,
) -> tuple[str, ...]:
    """Truthful review lines for recommendation vs excluded native references."""
    if (preset_id is None) != (preset_revision_id is None):
        raise ValueError("A Scale recommendation requires both exact preset IDs.")
    if preset_id is not None and assessment.native_scale_id is None:
        raise ValueError("No single native Scale exists to support this mapping.")
    lines = (assessment.notice,)
    if preset_id is not None:
        return lines + (
            f"Native default Scale: {assessment.native_scale_id}",
            f"Exact matched preset: {preset_id} / {preset_revision_id}",
            "The typed Scale definition matches; the native ID is NOT copied.",
        )
    if assessment.default_ids:
        return lines + (
            "Omitted native default Scale IDs: " + ", ".join(assessment.default_ids),
            "Target classes must choose/save an appropriate Scale separately.",
        )
    return lines + ("No Scoring Scale preset is recommended.",)
