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


def score_lineage_chains(
    records: Iterable[ScoreRecord],
) -> tuple[tuple[ScoreRecord, ...], ...]:
    """Return deterministic root-to-head chains for explicit Score revisions."""
    values = tuple(records)
    by_id = {item.score_record_id: item for item in values}
    if len(by_id) != len(values):
        raise ValueError("Score lineage records must have unique identities.")

    successor_by_predecessor: dict[str, ScoreRecord] = {}
    for item in values:
        predecessor_id = item.supersedes_score_record_id
        if predecessor_id is None:
            continue
        if predecessor_id not in by_id:
            raise ValueError(
                "Score lineage successor references an unavailable predecessor: "
                f"{predecessor_id}"
            )
        if predecessor_id in successor_by_predecessor:
            raise ValueError(
                "Score lineage predecessor has multiple explicit successors: "
                f"{predecessor_id}"
            )
        successor_by_predecessor[predecessor_id] = item

    roots = tuple(
        sorted(
            (
                item
                for item in values
                if item.supersedes_score_record_id is None
            ),
            key=lambda item: item.score_record_id,
        )
    )
    visited: set[str] = set()
    chains: list[tuple[ScoreRecord, ...]] = []
    for root in roots:
        chain: list[ScoreRecord] = []
        current = root
        while True:
            if current.score_record_id in visited:
                raise ValueError(
                    "Score lineage contains a cycle or duplicate traversal."
                )
            visited.add(current.score_record_id)
            chain.append(current)
            successor = successor_by_predecessor.get(current.score_record_id)
            if successor is None:
                break
            current = successor
        chains.append(tuple(chain))

    if len(visited) != len(values):
        raise ValueError(
            "Score lineage contains a cycle without a reachable root."
        )
    return tuple(chains)


__all__ = ["current_score_lineage_heads", "score_lineage_chains"]
