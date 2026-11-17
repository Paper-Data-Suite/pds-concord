"""#149 Slice 0: intentional RED witnesses for stage-aware Activity attention.

Strict xfails must be removed once #149 fixes the source behavior.
Run with --runxfail to reproduce actual failures on pinned Concord main.
All identities and graphs are synthetic; no teacher workspace is loaded.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import concord.workflows.activity_attention as attention


def _context(
    *,
    plans: tuple[object, ...] = (),
    packets: tuple[object, ...] = (),
    artifacts: tuple[object, ...] = (),
    authors: tuple[object, ...] = (),
    subjects: tuple[object, ...] = (),
    group_count: int = 0,
    student_count: int = 0,
) -> SimpleNamespace:
    return SimpleNamespace(
        root=Path("synthetic-workspace-not-opened"),
        work=SimpleNamespace(class_id="class-synthetic", work_id="activity-synthetic"),
        snapshot_revision=7,
        snapshot_sha256="a" * 64,
        activity=SimpleNamespace(
            activity_id="activity-synthetic",
            title="Six Cluster Seminar",
            status="active",
            scoring_orientation="evidence_only",
        ),
        graph=SimpleNamespace(
            sessions=(SimpleNamespace(session_id="session-1"),),
            groups=tuple(
                SimpleNamespace(group_id=f"cluster-{i}") for i in range(group_count)
            ),
            memberships=tuple(
                SimpleNamespace(student_id=f"student-{i}") for i in range(student_count)
            ),
            group_plans=plans,
            packet_instances=packets,
            artifact_instances=artifacts,
            artifact_authors=authors,
            artifact_subjects=subjects,
            artifact_reviews=(),
            moderation_records=(),
        ),
    )


def _plan(status: str, *, unresolved: tuple[str, ...] = ()) -> SimpleNamespace:
    return SimpleNamespace(
        group_plan_id=f"synthetic-{status}",
        status=status,
        strategy="manual",
        unresolved_student_ids=unresolved,
        missing_signal_disposition=None,
    )


@pytest.mark.parametrize("roster_size", (29, 30))
@pytest.mark.xfail(
    strict=True,
    reason=(
        "#149: applied operational Clusters still show unused drafts "
        "as blocking Plan attention"
    ),
)
def test_applied_six_cluster_plan_with_unused_draft_is_not_unready(
    roster_size: int,
) -> None:
    """An unrelated proposal must not erase current operational readiness."""
    context = _context(
        plans=(_plan("applied"), _plan("draft", unresolved=("draft-only",))),
        group_count=6,
        student_count=roster_size,
    )
    counts = attention._plan_attention_counts_from_context(context)
    assert not {
        code: value
        for code, value in counts.items()
        if code.startswith("concord_plan_")
    }, counts


@pytest.mark.xfail(
    strict=True,
    reason="#149: planned associations to blank packets are called returned evidence",
)
def test_six_generated_unreturned_blank_artifacts_have_no_returned_confirmation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No verified return exists even though packets have proposed associations."""
    context = _context(
        packets=tuple(SimpleNamespace(generation_status="generated") for _ in range(6)),
        artifacts=tuple(
            SimpleNamespace(
                artifact_instance_id=f"blank-{i}",
                activity_id="activity-synthetic",
                generation_status="completed",
                artifact_status="generated",  # NOT returned
                expected_return_status="returned_expected",
            )
            for i in range(6)
        ),
        authors=tuple(
            SimpleNamespace(
                artifact_author_id=f"planned-author-{i}",
                artifact_instance_id=f"blank-{i}",
                attribution_status="proposed",
                supersedes_artifact_author_id=None,
            )
            for i in range(6)
        ),
        subjects=tuple(
            SimpleNamespace(
                artifact_subject_id=f"planned-subject-{i}",
                artifact_instance_id=f"blank-{i}",
                confirmation_status="proposed",
                supersedes_artifact_subject_id=None,
            )
            for i in range(6)
        ),
    )
    monkeypatch.setattr(attention, "_assembly_state", lambda *_a, **_k: "not_ready")
    monkeypatch.setattr(
        attention,
        "_share_attention_from_context",
        lambda _context: SimpleNamespace(status="inactive"),
    )
    counts = attention._attention_counts_from_context(context)
    assert "concord_collect_author_confirmation" not in counts, counts
    assert "concord_collect_subject_confirmation" not in counts, counts
