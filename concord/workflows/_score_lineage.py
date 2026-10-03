"""Pure Score lineage helpers shared by read-only and mutation workflows."""

from __future__ import annotations

from collections.abc import Iterable

from concord.models import ScoreRecord


def current_score_lineage_heads(
    records: Iterable[ScoreRecord],
) -> tuple[ScoreRecord, ...]:
    """Return explicit Score lineage heads without inferring required Scores."""
    values = tuple(records)
    superseded_ids = {
        item.supersedes_score_record_id
        for item in values
        if item.supersedes_score_record_id is not None
    }
    return tuple(
        item for item in values if item.score_record_id not in superseded_ids
    )


__all__ = ["current_score_lineage_heads"]
