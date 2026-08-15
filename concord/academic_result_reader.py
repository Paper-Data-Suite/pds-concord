"""Consumer-neutral reader for Concord Academic Result Manifest v1."""

from __future__ import annotations

import math

from pds_core.identifiers import IdentifierValidationError, validate_identifier

from concord.academic_result_manifest import (
    AcademicResultManifest,
    ConcordAcademicResultManifestDecodeError,
    ConcordAcademicResultManifestValidationError,
    CriterionProjection,
    CriterionSetProjection,
    JsonScalar,
    ModerationProjection,
    ScaleLevelProjection,
    ScoreEvidenceLinkProjection,
    ScoreProjection,
    ScoringScaleProjection,
    TargetReferenceProjection,
    academic_result_manifest_from_bytes,
    academic_result_manifest_to_bytes,
)
from concord.academic_result_manifest import (
    validate_academic_result_manifest as validate_manifest,
)

_CANONICAL_DECODE_MESSAGES = frozenset(
    {
        "manifest must end with exactly one LF.",
        "manifest JSON is not canonical.",
    }
)


class ConcordAcademicResultReaderError(Exception):
    """Base failure for public Concord manifest reading and lookup."""


class ConcordAcademicResultReaderValidationError(
    ConcordAcademicResultReaderError, ValueError
):
    """Reader input violates the public consumer-neutral contract."""


class ConcordAcademicResultReaderDecodeError(
    ConcordAcademicResultReaderValidationError
):
    """Immutable bytes are not an exact valid Concord academic-result manifest."""


class ConcordAcademicResultReaderNotFoundError(
    ConcordAcademicResultReaderError, LookupError
):
    """An exact validated lookup is absent from the supplied manifest."""


def _safe_identifier(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise ConcordAcademicResultReaderValidationError(
            f"{field_name} must be a safe identifier."
        )
    try:
        return validate_identifier(value, field_name)
    except (IdentifierValidationError, TypeError, ValueError) as error:
        raise ConcordAcademicResultReaderValidationError(
            f"{field_name} must be a safe identifier."
        ) from error


def _json_scalar(value: object) -> JsonScalar:
    if not isinstance(value, (str, int, float, bool)):
        raise ConcordAcademicResultReaderValidationError(
            "Scale value must be a non-null JSON scalar."
        )
    if isinstance(value, float) and not math.isfinite(value):
        raise ConcordAcademicResultReaderValidationError(
            "Scale value must be finite."
        )
    return value


def read_academic_result_manifest(value: bytes) -> AcademicResultManifest:
    """Decode, validate, and require exact canonical Concord manifest bytes."""
    if type(value) is not bytes:
        raise ConcordAcademicResultReaderValidationError(
            "Academic-result manifest input must be immutable bytes."
        )
    try:
        manifest = academic_result_manifest_from_bytes(value)
    except ConcordAcademicResultManifestDecodeError as error:
        if str(error) in _CANONICAL_DECODE_MESSAGES:
            raise ConcordAcademicResultReaderValidationError(
                "Academic-result manifest bytes are not canonical."
            ) from error
        raise ConcordAcademicResultReaderDecodeError(
            "Academic-result manifest bytes are invalid."
        ) from error
    except ConcordAcademicResultManifestValidationError as error:
        raise ConcordAcademicResultReaderDecodeError(
            "Academic-result manifest bytes are invalid."
        ) from error
    try:
        canonical = academic_result_manifest_to_bytes(manifest)
    except ConcordAcademicResultManifestValidationError as error:
        raise ConcordAcademicResultReaderValidationError(
            "Academic-result manifest could not be validated canonically."
        ) from error
    if canonical != value:
        raise ConcordAcademicResultReaderValidationError(
            "Academic-result manifest bytes are not canonical."
        )
    return manifest


def validate_academic_result_manifest(
    manifest: AcademicResultManifest,
) -> AcademicResultManifest:
    """Validate one existing immutable manifest model without I/O."""
    try:
        return validate_manifest(manifest)
    except ConcordAcademicResultManifestValidationError as error:
        raise ConcordAcademicResultReaderValidationError(
            "Academic-result manifest model is invalid."
        ) from error


def lookup_academic_result_criterion_set(
    manifest: AcademicResultManifest,
    criterion_set_id: str,
) -> CriterionSetProjection:
    """Return one exact represented Criterion Set."""
    checked = validate_academic_result_manifest(manifest)
    target = _safe_identifier(criterion_set_id, "criterion_set_id")
    for criterion_set in checked.criterion_sets:
        if criterion_set.criterion_set_id == target:
            return criterion_set
    raise ConcordAcademicResultReaderNotFoundError(
        "Requested Criterion Set is not represented in this manifest."
    )


def lookup_academic_result_criterion(
    manifest: AcademicResultManifest,
    criterion_id: str,
) -> CriterionProjection:
    """Return one exact represented Criterion."""
    checked = validate_academic_result_manifest(manifest)
    target = _safe_identifier(criterion_id, "criterion_id")
    for criterion in checked.criteria:
        if criterion.criterion_id == target:
            return criterion
    raise ConcordAcademicResultReaderNotFoundError(
        "Requested Criterion is not represented in this manifest."
    )


def lookup_academic_result_scoring_scale(
    manifest: AcademicResultManifest,
    scoring_scale_id: str,
) -> ScoringScaleProjection:
    """Return one exact represented Scoring Scale."""
    checked = validate_academic_result_manifest(manifest)
    target = _safe_identifier(scoring_scale_id, "scoring_scale_id")
    for scale in checked.scoring_scales:
        if scale.scoring_scale_id == target:
            return scale
    raise ConcordAcademicResultReaderNotFoundError(
        "Requested Scoring Scale is not represented in this manifest."
    )


def lookup_academic_result_scale_level(
    manifest: AcademicResultManifest,
    scoring_scale_id: str,
    value: JsonScalar,
) -> ScaleLevelProjection:
    """Return one exact type-sensitive Scale level without coercion."""
    scale = lookup_academic_result_scoring_scale(manifest, scoring_scale_id)
    target = _json_scalar(value)
    level = scale.level_for_value(target)
    if level is not None:
        return level
    raise ConcordAcademicResultReaderNotFoundError(
        "Requested Scale level is not represented in this manifest."
    )


def lookup_academic_result_score(
    manifest: AcademicResultManifest,
    score_record_id: str,
) -> ScoreProjection:
    """Return one exact represented producer Score revision."""
    checked = validate_academic_result_manifest(manifest)
    target = _safe_identifier(score_record_id, "score_record_id")
    for score in checked.scores:
        if score.score_record_id == target:
            return score
    raise ConcordAcademicResultReaderNotFoundError(
        "Requested Score is not represented in this manifest."
    )


def lookup_academic_result_score_evidence_link(
    manifest: AcademicResultManifest,
    score_evidence_link_id: str,
) -> ScoreEvidenceLinkProjection:
    """Return one exact represented Score Evidence Link."""
    checked = validate_academic_result_manifest(manifest)
    target = _safe_identifier(
        score_evidence_link_id,
        "score_evidence_link_id",
    )
    for link in checked.score_evidence_links:
        if link.score_evidence_link_id == target:
            return link
    raise ConcordAcademicResultReaderNotFoundError(
        "Requested Score Evidence Link is not represented in this manifest."
    )


def list_academic_result_score_evidence_links(
    manifest: AcademicResultManifest,
    score_record_id: str,
) -> tuple[ScoreEvidenceLinkProjection, ...]:
    """Return every represented Evidence Link for one exact Score in manifest order."""
    checked = validate_academic_result_manifest(manifest)
    score = lookup_academic_result_score(checked, score_record_id)
    return tuple(
        link
        for link in checked.score_evidence_links
        if link.score_record_id == score.score_record_id
    )


def lookup_academic_result_moderation(
    manifest: AcademicResultManifest,
    moderation_record_id: str,
) -> ModerationProjection:
    """Return one exact represented public Moderation revision."""
    checked = validate_academic_result_manifest(manifest)
    target = _safe_identifier(moderation_record_id, "moderation_record_id")
    for moderation in checked.moderation_records:
        if moderation.moderation_record_id == target:
            return moderation
    raise ConcordAcademicResultReaderNotFoundError(
        "Requested Moderation record is not represented in this manifest."
    )


def list_academic_result_scores_for_target(
    manifest: AcademicResultManifest,
    target: TargetReferenceProjection,
) -> tuple[ScoreProjection, ...]:
    """Return every represented Score for one exact target without selection."""
    checked = validate_academic_result_manifest(manifest)
    if not isinstance(target, TargetReferenceProjection):
        raise ConcordAcademicResultReaderValidationError(
            "target must be a TargetReferenceProjection."
        )
    return tuple(
        score for score in checked.scores if score.target_reference == target
    )


__all__ = (
    "AcademicResultManifest",
    "ConcordAcademicResultReaderDecodeError",
    "ConcordAcademicResultReaderError",
    "ConcordAcademicResultReaderNotFoundError",
    "ConcordAcademicResultReaderValidationError",
    "CriterionProjection",
    "CriterionSetProjection",
    "JsonScalar",
    "ModerationProjection",
    "ScaleLevelProjection",
    "ScoreEvidenceLinkProjection",
    "ScoreProjection",
    "ScoringScaleProjection",
    "TargetReferenceProjection",
    "list_academic_result_score_evidence_links",
    "list_academic_result_scores_for_target",
    "lookup_academic_result_criterion",
    "lookup_academic_result_criterion_set",
    "lookup_academic_result_moderation",
    "lookup_academic_result_scale_level",
    "lookup_academic_result_score",
    "lookup_academic_result_score_evidence_link",
    "lookup_academic_result_scoring_scale",
    "read_academic_result_manifest",
    "validate_academic_result_manifest",
)
