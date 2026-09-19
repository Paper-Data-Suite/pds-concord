"""Package-owned starter Template lineage adapter.

The ordinary starter catalog remains presentation metadata. This module maps
that metadata to the generic immutable lineage reconciliation engine and owns
the package-only successor metadata for relationship-aware starter revisions.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from importlib.resources import files

from concord.models import (
    Provenance,
    TemplateAuthorshipExpectation,
    TemplateSubjectResolutionExpectation,
)
from concord.starter_templates.catalog import (
    StarterTemplateCatalogEntry,
    StarterTemplateCatalogError,
)
from concord.starter_templates.layout import (
    starter_layout_from_json_bytes,
    starter_layout_to_json_bytes,
)
from concord.starter_templates.lineage import (
    PackagedStarterTemplateLineage,
    PackagedStarterTemplateVersion,
)

RELATIONSHIP_AWARE_STARTER_KEYS = (
    "fishbowl_observer",
    "talk_moves_observer",
    "peer_review_writing",
    "peer_review_presentation",
    "peer_design_code_review",
)


@dataclass(frozen=True, slots=True, kw_only=True)
class _RelationshipAwareV2Spec:
    asset_name: str
    authorship_mode: str
    authorship_multiple_allowed: bool
    subject_kinds: tuple[str, ...]
    resolution_mode: str
    subject_role: str
    subject_multiple_allowed: bool = False
    allow_target_subject_match: bool = True


_V2_SPECS = {
    "fishbowl_observer": _RelationshipAwareV2Spec(
        asset_name="fishbowl_observer_v2.json",
        authorship_mode="observer",
        authorship_multiple_allowed=False,
        subject_kinds=("concord_session",),
        resolution_mode="session",
        subject_role="session_context",
    ),
    "talk_moves_observer": _RelationshipAwareV2Spec(
        asset_name="talk_moves_observer_v2.json",
        authorship_mode="observer",
        authorship_multiple_allowed=False,
        subject_kinds=("concord_session",),
        resolution_mode="session",
        subject_role="session_context",
    ),
    "peer_review_writing": _RelationshipAwareV2Spec(
        asset_name="peer_review_writing_v2.json",
        authorship_mode="individual_author",
        authorship_multiple_allowed=True,
        subject_kinds=("core_student",),
        resolution_mode="explicit",
        subject_role="reviewed_subject",
        allow_target_subject_match=False,
    ),
    "peer_review_presentation": _RelationshipAwareV2Spec(
        asset_name="peer_review_presentation_v2.json",
        authorship_mode="individual_author",
        authorship_multiple_allowed=True,
        subject_kinds=("core_student", "concord_group"),
        resolution_mode="explicit",
        subject_role="reviewed_subject",
        allow_target_subject_match=False,
    ),
    "peer_design_code_review": _RelationshipAwareV2Spec(
        asset_name="peer_design_code_review_v2.json",
        authorship_mode="individual_author",
        authorship_multiple_allowed=False,
        subject_kinds=("core_student", "concord_group"),
        resolution_mode="explicit",
        subject_role="reviewed_subject",
        allow_target_subject_match=False,
    ),
}


def build_starter_template_lineage(
    entry: StarterTemplateCatalogEntry,
    *,
    created_provenance: Provenance,
) -> PackagedStarterTemplateLineage:
    """Build the exact package-owned lineage for one catalog entry."""
    definition, version_v1 = entry.build_template_records(
        created_provenance=created_provenance,
        status="active",
    )
    versions = [
        PackagedStarterTemplateVersion(
            version=version_v1,
            rendering_specification=entry.rendering_specification_bytes(),
        )
    ]

    spec = _V2_SPECS.get(entry.starter_key)
    if spec is not None:
        rendering_v2 = _relationship_v2_rendering(entry, spec)
        version_v2 = replace(
            version_v1,
            template_version_id=f"{entry.template_id}-v2",
            version_label="Starter v2",
            revision_sequence=2,
            rendering_specification_reference=(
                f"{entry.template_id}-layout-v2"
            ),
            rendering_specification_sha256=hashlib.sha256(
                rendering_v2
            ).hexdigest(),
            supersedes_template_version_id=version_v1.template_version_id,
            default_authorship_expectation=TemplateAuthorshipExpectation(
                authorship_mode=spec.authorship_mode,
                required=True,
                multiple_allowed=spec.authorship_multiple_allowed,
            ),
            default_subject_expectation=TemplateSubjectResolutionExpectation(
                subject_kinds=spec.subject_kinds,
                resolution_mode=spec.resolution_mode,
                subject_role=spec.subject_role,
                required=True,
                multiple_allowed=spec.subject_multiple_allowed,
                allow_target_subject_match=spec.allow_target_subject_match,
            ),
        )
        versions.append(
            PackagedStarterTemplateVersion(
                version=version_v2,
                rendering_specification=rendering_v2,
            )
        )

    return PackagedStarterTemplateLineage(
        starter_key=entry.starter_key,
        definition=definition,
        versions=tuple(versions),
    )


def current_packaged_template_version_id(
    entry: StarterTemplateCatalogEntry,
) -> str:
    """Return the package-current Version identity for one starter."""
    if entry.starter_key in _V2_SPECS:
        return f"{entry.template_id}-v2"
    return entry.template_version_id


def relationship_v2_asset_name(
    entry: StarterTemplateCatalogEntry,
) -> str | None:
    """Return the separate package asset for an affected starter successor."""
    spec = _V2_SPECS.get(entry.starter_key)
    return None if spec is None else spec.asset_name



def packaged_starter_asset_names(
    entries: tuple[StarterTemplateCatalogEntry, ...],
) -> tuple[str, ...]:
    """Return the exact JSON asset set required by packaged starter lineages."""
    names: list[str] = []
    for entry in entries:
        names.append(entry.asset_name)
        successor = relationship_v2_asset_name(entry)
        if successor is not None:
            names.append(successor)
    if len(set(names)) != len(names):
        raise StarterTemplateCatalogError(
            "packaged starter lineages must not reuse rendering asset names."
        )
    return tuple(names)


def _relationship_v2_rendering(
    entry: StarterTemplateCatalogEntry,
    spec: _RelationshipAwareV2Spec,
) -> bytes:
    resource = files("concord.starter_templates.assets").joinpath(
        spec.asset_name
    )
    try:
        data = resource.read_bytes()
    except OSError as error:
        raise StarterTemplateCatalogError(
            f"could not read packaged starter asset {spec.asset_name}: {error}"
        ) from error
    if not data:
        raise StarterTemplateCatalogError(
            f"packaged starter asset is empty: {spec.asset_name}"
        )

    try:
        layout = starter_layout_from_json_bytes(data)
    except ValueError as error:
        raise StarterTemplateCatalogError(
            f"invalid packaged starter asset {spec.asset_name}: {error}"
        ) from error
    if starter_layout_to_json_bytes(layout) != data:
        raise StarterTemplateCatalogError(
            f"packaged starter asset is not canonical JSON: {spec.asset_name}"
        )

    # Slice 5 changes immutable relationship semantics only. Keeping the exact
    # layout shape equal to v1 prevents the package from silently changing
    # printable regions before generation gains relationship-aware bindings.
    if layout != entry.layout():
        raise StarterTemplateCatalogError(
            f"{spec.asset_name} must preserve the v1 layout shape until "
            "relationship-aware rendering is implemented."
        )
    return data


__all__ = [
    "RELATIONSHIP_AWARE_STARTER_KEYS",
    "build_starter_template_lineage",
    "current_packaged_template_version_id",
    "packaged_starter_asset_names",
    "relationship_v2_asset_name",
]
