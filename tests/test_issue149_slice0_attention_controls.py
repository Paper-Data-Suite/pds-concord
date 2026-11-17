"""#149 Slice 0: passing controls for legitimate current attention behavior.

All data is synthetic and no disk-backed academic records are opened.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import concord.workflows.activity_attention as attention


def _context(**graph_updates: object) -> SimpleNamespace:
    data: dict[str, object] = {
        "group_plans": (),
        "packet_instances": (),
        "artifact_instances": (),
        "artifact_authors": (),
        "artifact_subjects": (),
        "artifact_reviews": (),
        "moderation_records": (),
    }
    data.update(graph_updates)
    return SimpleNamespace(
        root=Path("synthetic-only"),
        work=SimpleNamespace(class_id="synthetic-class", work_id="synthetic-activity"),
        activity=SimpleNamespace(status="active", scoring_orientation="evidence_only"),
        graph=SimpleNamespace(**data),
    )


def test_draft_without_applied_plan_remains_a_real_plan_action() -> None:
    context = _context(
        group_plans=(
            SimpleNamespace(
                status="draft",
                strategy="manual",
                unresolved_student_ids=(),
                missing_signal_disposition=None,
            ),
        )
    )
    assert attention._plan_attention_counts_from_context(context) == {
        "concord_plan_prepare": 1,
    }


def test_applied_and_cancelled_plans_alone_do_not_create_attention() -> None:
    context = _context(
        group_plans=tuple(
            SimpleNamespace(
                status=status,
                strategy="manual",
                unresolved_student_ids=(),
                missing_signal_disposition=None,
            )
            for status in ("applied", "cancelled")
        )
    )
    assert attention._plan_attention_counts_from_context(context) == {}


def test_verified_assembled_evidence_retains_genuine_review_and_dispute_attention(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _context(
        artifact_instances=(
            SimpleNamespace(
                artifact_instance_id="returned-artifact",
                activity_id="synthetic-activity",
                artifact_status="returned",
            ),
        ),
        artifact_authors=(
            SimpleNamespace(
                artifact_author_id="author-current",
                artifact_instance_id="returned-artifact",
                attribution_status="disputed",
                supersedes_artifact_author_id=None,
            ),
        ),
        artifact_subjects=(
            SimpleNamespace(
                artifact_subject_id="subject-current",
                artifact_instance_id="returned-artifact",
                confirmation_status="unresolved",
                supersedes_artifact_subject_id=None,
            ),
        ),
    )
    monkeypatch.setattr(attention, "_assembly_state", lambda *_a, **_k: "assembled")
    monkeypatch.setattr(
        attention,
        "_share_attention_from_context",
        lambda _context: SimpleNamespace(status="inactive"),
    )
    counts = attention._attention_counts_from_context(context)
    assert counts == {
        "concord_collect_author_confirmation": 1,
        "concord_collect_subject_confirmation": 1,
        "concord_review_first": 1,
    }


def test_generated_packets_are_not_prepare_recovery_tasks() -> None:
    context = _context(
        packet_instances=tuple(
            SimpleNamespace(generation_status="generated") for _ in range(6)
        )
    )
    assert attention._prepare_attention_counts_from_context(context) == {}
