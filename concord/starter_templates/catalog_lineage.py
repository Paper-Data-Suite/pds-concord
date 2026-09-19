"""Package-owned starter Template lineage adapter.

The ordinary starter catalog remains presentation metadata. This module maps
that metadata to the generic immutable lineage reconciliation engine so the
existing installer can become version-aware without changing the catalog's
teacher-facing shape.
"""

from __future__ import annotations

from concord.models import Provenance
from concord.starter_templates.catalog import StarterTemplateCatalogEntry
from concord.starter_templates.lineage import (
    PackagedStarterTemplateLineage,
    PackagedStarterTemplateVersion,
)


def build_starter_template_lineage(
    entry: StarterTemplateCatalogEntry,
    *,
    created_provenance: Provenance,
) -> PackagedStarterTemplateLineage:
    """Build the exact package-owned lineage for one catalog entry.

    Issue #113 intentionally begins with the current v1-only package. Later
    slices may append immutable package-owned successors here without changing
    the stable catalog key or rewriting v1.
    """
    definition, version = entry.build_template_records(
        created_provenance=created_provenance,
        status="active",
    )
    return PackagedStarterTemplateLineage(
        starter_key=entry.starter_key,
        definition=definition,
        versions=(
            PackagedStarterTemplateVersion(
                version=version,
                rendering_specification=entry.rendering_specification_bytes(),
            ),
        ),
    )


def current_packaged_template_version_id(
    entry: StarterTemplateCatalogEntry,
) -> str:
    """Return the package-current Version identity for one starter.

    All real starters are still v1 in this infrastructure slice. Keeping this
    helper separate lets later package successors advance the displayed current
    Version without redefining the stable catalog identity.
    """
    return entry.template_version_id


__all__ = [
    "build_starter_template_lineage",
    "current_packaged_template_version_id",
]
