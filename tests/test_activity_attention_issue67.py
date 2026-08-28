from __future__ import annotations

from types import SimpleNamespace

import pytest

import concord.workflows.activity_attention as attention
from concord.academic_result_share_attention import AcademicResultShareAttentionState
from concord.workflows import ActivitySummary
from concord.workflows.artifact import ArtifactSummary
from concord.workflows.artifact_collection import ArtifactCollectionState
from concord.workflows.artifact_review_attention import ArtifactReviewAttentionState
from concord.workflows.artifact_scoring_attention import ArtifactScoringAttentionState
from concord.workflows.group_plan import GroupPlanSummary
from concord.workflows.packet_instance import PacketInstanceSummary


def _activity(
    activity_id: str = "activity-1",
    *,
    class_id: str = "class-1",
    title: str = "Seminar",
    status: str = "active",
    scoring_orientation: str = "evidence_only",
) -> ActivitySummary:
    return ActivitySummary(
        class_id=class_id,
        activity_id=activity_id,
        title=title,
        status=status,
        scoring_orientation=scoring_orientation,
        session_count=1,
        group_count=0,
        snapshot_revision=1,
    )


def _plan(
    group_plan_id: str,
    *,
    status: str,
    strategy: str = "manual",
    unresolved: int = 0,
) -> GroupPlanSummary:
    return GroupPlanSummary(
        class_id="class-1",
        activity_id="activity-1",
        group_plan_id=group_plan_id,
        strategy=strategy,
        status=status,
        proposed_group_count=1,
        assigned_student_count=3,
        unresolved_student_count=unresolved,
        target_group_size=None,
        target_group_count=None,
        snapshot_revision=1,
    )


def _packet(
    packet_instance_id: str,
    *,
    status: str,
    target_key: str = "activity:activity-1",
    output_relative_path: str | None = None,
    output_sha256: str | None = None,
) -> PacketInstanceSummary:
    return PacketInstanceSummary(
        packet_instance_id=packet_instance_id,
        generation_id=f"generation-{packet_instance_id}",
        packet_definition_id="packet-definition-1",
        packet_version_id="packet-version-1",
        activity_id="activity-1",
        session_id="session-1",
        audience_kind="activity",
        target_key=target_key,
        generation_status=status,
        artifact_count=1,
        page_count=2,
        route_count=1,
        output_relative_path=output_relative_path,
        output_sha256=output_sha256,
        created_at="2026-08-28T12:00:00+00:00",
    )


def _artifact(
    artifact_instance_id: str,
    *,
    status: str = "returned",
    returned: int = 1,
    required: int = 1,
    authors: int = 0,
    subjects: int = 0,
) -> ArtifactSummary:
    return ArtifactSummary(
        class_id="class-1",
        activity_id="activity-1",
        artifact_instance_id=artifact_instance_id,
        artifact_category="student_work",
        generation_status="completed",
        expected_return_status="returned_expected",
        artifact_status=status,
        required_return_page_count=required,
        returned_required_page_count=returned,
        current_author_count=authors,
        current_subject_count=subjects,
        snapshot_revision=1,
    )


def _collection_state(
    artifact_instance_id: str,
    *,
    assembly: str = "not_ready",
    author_pending: bool = False,
    subject_pending: bool = False,
) -> ArtifactCollectionState:
    return ArtifactCollectionState(
        class_id="class-1",
        activity_id="activity-1",
        artifact_instance_id=artifact_instance_id,
        assembly_state=assembly,  # type: ignore[arg-type]
        author_confirmation_pending=author_pending,
        subject_confirmation_pending=subject_pending,
    )


def _patch_activity(
    monkeypatch: pytest.MonkeyPatch,
    *,
    status: str = "active",
    plans: tuple[GroupPlanSummary, ...] = (),
    packets: tuple[PacketInstanceSummary, ...] = (),
    artifacts: tuple[ArtifactSummary, ...] = (),
    collection_states: dict[str, ArtifactCollectionState] | None = None,
    review_states: dict[str, ArtifactReviewAttentionState] | None = None,
    scoring_states: dict[str, ArtifactScoringAttentionState] | None = None,
    scoring_orientation: str = "evidence_only",
    share_status: str = "inactive",
) -> None:
    monkeypatch.setattr(
        attention,
        "show_activity",
        lambda *_a, **_k: SimpleNamespace(
            summary=_activity(
                status=status,
                scoring_orientation=scoring_orientation,
            )
        ),
    )
    monkeypatch.setattr(
        attention,
        "list_group_plans",
        lambda *_a, **_k: plans,
    )
    monkeypatch.setattr(
        attention,
        "list_packet_instances",
        lambda *_a, **_k: packets,
    )
    monkeypatch.setattr(
        attention,
        "list_artifacts",
        lambda *_a, **_k: artifacts,
    )
    states = collection_states or {}
    monkeypatch.setattr(
        attention,
        "inspect_artifact_collection_state",
        lambda _class_id, _activity_id, artifact_id, **_k: states[artifact_id],
    )
    reviews = review_states or {}
    monkeypatch.setattr(
        attention,
        "inspect_artifact_review_attention_state",
        lambda _class_id, _activity_id, artifact_id, **_k: reviews.get(
            artifact_id,
            ArtifactReviewAttentionState(
                class_id="class-1",
                activity_id="activity-1",
                artifact_instance_id=artifact_id,
                first_review_pending=False,
                review_attention_pending=False,
                moderation_pending=False,
                post_moderation_review_pending=False,
            ),
        ),
    )
    scoring = scoring_states or {}
    monkeypatch.setattr(
        attention,
        "inspect_artifact_scoring_attention_state",
        lambda _class_id, _activity_id, artifact_id, **_k: scoring.get(
            artifact_id,
            ArtifactScoringAttentionState(
                class_id="class-1",
                activity_id="activity-1",
                artifact_instance_id=artifact_id,
                scoring_ready=False,
            ),
        ),
    )
    monkeypatch.setattr(
        attention,
        "inspect_academic_result_share_attention_state",
        lambda _class_id, _activity_id, **_k: AcademicResultShareAttentionState(
            class_id="class-1",
            activity_id="activity-1",
            status=share_status,  # type: ignore[arg-type]
        ),
    )


def test_no_group_plan_does_not_manufacture_attention(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_activity(monkeypatch)
    result = attention.inspect_activity_attention("class-1", "activity-1")
    assert result.items == ()
    assert result.next_item is None


def test_group_plan_lifecycle_maps_to_stable_plan_attention(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_activity(
        monkeypatch,
        plans=(
            _plan("plan-draft", status="draft"),
            _plan("plan-preview", status="previewed"),
            _plan("plan-approved", status="approved"),
            _plan("plan-applied", status="applied"),
            _plan("plan-cancelled", status="cancelled"),
        ),
    )
    result = attention.inspect_activity_attention("class-1", "activity-1")
    assert [(item.code, item.count) for item in result.items] == [
        ("concord_plan_prepare", 1),
        ("concord_plan_approve", 1),
        ("concord_plan_apply", 1),
    ]
    assert result.next_item == result.items[0]
    assert all(item.task == "plan" for item in result.items)
    assert all(item.action_id == "open_activity_plan" for item in result.items)


def test_unresolved_placement_attention_counts_plans_not_students(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_activity(
        monkeypatch,
        plans=(
            _plan("plan-a", status="draft", unresolved=7),
            _plan("plan-b", status="previewed", unresolved=4),
        ),
    )
    result = attention.inspect_activity_attention("class-1", "activity-1")
    unresolved = next(
        item
        for item in result.items
        if item.code == "concord_plan_unresolved_placements"
    )
    assert unresolved.count == 2
    assert [item.code for item in result.items] == [
        "concord_plan_prepare",
        "concord_plan_unresolved_placements",
        "concord_plan_approve",
    ]


def test_explicit_leave_unassigned_signal_disposition_is_not_false_attention(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan(
        "plan-signal",
        status="previewed",
        strategy="similar_signal",
        unresolved=5,
    )
    _patch_activity(monkeypatch, plans=(plan,))
    monkeypatch.setattr(
        attention,
        "show_group_plan",
        lambda *_a, **_k: SimpleNamespace(
            plan=SimpleNamespace(
                missing_signal_disposition="leave_unassigned",
                source_signal_set_digest="f" * 64,
                unresolved_student_ids=("student-secret",),
            )
        ),
    )
    result = attention.inspect_activity_attention("class-1", "activity-1")
    assert [item.code for item in result.items] == ["concord_plan_approve"]
    rendered = repr(result)
    assert "student-secret" not in rendered
    assert "f" * 64 not in rendered


def test_signal_plan_without_leave_unassigned_keeps_unresolved_attention(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan(
        "plan-signal",
        status="draft",
        strategy="mixed_signal",
        unresolved=2,
    )
    _patch_activity(monkeypatch, plans=(plan,))
    monkeypatch.setattr(
        attention,
        "show_group_plan",
        lambda *_a, **_k: SimpleNamespace(
            plan=SimpleNamespace(missing_signal_disposition="manual")
        ),
    )
    result = attention.inspect_activity_attention("class-1", "activity-1")
    assert [item.code for item in result.items] == [
        "concord_plan_prepare",
        "concord_plan_unresolved_placements",
    ]


def test_completed_cancelled_and_archived_activities_do_not_emit_plan_attention(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for status in ("completed", "cancelled", "archived"):
        _patch_activity(
            monkeypatch,
            status=status,
            plans=(_plan("plan-approved", status="approved"),),
        )
        result = attention.inspect_activity_attention("class-1", "activity-1")
        assert result.items == ()


def test_activity_attention_list_uses_class_title_identity_display_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    activities = (
        _activity("activity-z", class_id="class-2", title="Alpha"),
        _activity("activity-b", class_id="class-1", title="beta"),
        _activity("activity-a", class_id="class-1", title="Alpha"),
    )
    monkeypatch.setattr(attention, "list_activities", lambda **_k: activities)

    def inspect(class_id: str, activity_id: str, **_kwargs: object):
        activity = next(item for item in activities if item.activity_id == activity_id)
        return attention.ActivityAttentionSummary(
            class_id=class_id,
            activity_id=activity_id,
            title=activity.title,
        )

    monkeypatch.setattr(attention, "inspect_activity_attention", inspect)
    result = attention.list_activity_attention()
    assert [(item.class_id, item.title, item.activity_id) for item in result] == [
        ("class-1", "Alpha", "activity-a"),
        ("class-1", "beta", "activity-b"),
        ("class-2", "Alpha", "activity-z"),
    ]


def test_attention_item_rejects_nonpositive_counts() -> None:
    with pytest.raises(ValueError, match="positive integer"):
        attention.ActivityAttentionItem(
            code="concord_plan_prepare",
            label="Group plans still need preparation",
            task="plan",
            count=0,
            action_id="open_activity_plan",
        )


def test_packet_lifecycle_maps_only_actionable_prepare_states(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_activity(
        monkeypatch,
        packets=(
            _packet("packet-planned", status="planned"),
            _packet("packet-rendering", status="rendering"),
            _packet("packet-routes", status="routes_pending"),
            _packet("packet-failed", status="failed"),
            _packet(
                "packet-generated",
                status="generated",
                output_relative_path="rendered/packets/private.pdf",
                output_sha256="a" * 64,
            ),
            _packet("packet-cancelled", status="cancelled"),
        ),
    )
    result = attention.inspect_activity_attention("class-1", "activity-1")
    assert [(item.code, item.count) for item in result.items] == [
        ("concord_prepare_materials", 2),
        ("concord_prepare_routes_pending", 1),
        ("concord_prepare_recovery", 1),
    ]
    assert all(item.task == "prepare" for item in result.items)
    assert all(item.action_id == "open_activity_prepare" for item in result.items)


def test_generated_and_cancelled_packets_create_no_prepare_attention(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_activity(
        monkeypatch,
        packets=(
            _packet(
                "packet-generated",
                status="generated",
                output_relative_path="rendered/packets/final.pdf",
                output_sha256="b" * 64,
            ),
            _packet("packet-cancelled", status="cancelled"),
        ),
    )
    result = attention.inspect_activity_attention("class-1", "activity-1")
    assert result.items == ()


def test_prepare_attention_does_not_leak_packet_target_or_output_details(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sensitive_target = "participant:student-secret"
    sensitive_path = "rendered/packets/private-secret.pdf"
    sensitive_hash = "c" * 64
    _patch_activity(
        monkeypatch,
        packets=(
            _packet(
                "packet-secret",
                status="failed",
                target_key=sensitive_target,
            ),
            _packet(
                "packet-generated-secret",
                status="generated",
                target_key=sensitive_target,
                output_relative_path=sensitive_path,
                output_sha256=sensitive_hash,
            ),
        ),
    )
    result = attention.inspect_activity_attention("class-1", "activity-1")
    rendered = repr(result)
    assert sensitive_target not in rendered
    assert sensitive_path not in rendered
    assert sensitive_hash not in rendered
    assert "packet-secret" not in rendered
    assert "generation-packet-secret" not in rendered


def test_plan_attention_precedes_prepare_attention_for_next_action(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_activity(
        monkeypatch,
        plans=(_plan("plan-draft", status="draft"),),
        packets=(_packet("packet-failed", status="failed"),),
    )
    result = attention.inspect_activity_attention("class-1", "activity-1")
    assert [item.task for item in result.items] == ["plan", "prepare"]
    assert result.next_item is not None
    assert result.next_item.code == "concord_plan_prepare"



def test_collect_attention_requires_explicit_actionable_collection_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifacts = (
        _artifact("artifact-waiting", status="distributed", returned=0, required=2),
        _artifact("artifact-ready"),
        _artifact("artifact-assembled"),
    )
    _patch_activity(
        monkeypatch,
        artifacts=artifacts,
        collection_states={
            "artifact-waiting": _collection_state(
                "artifact-waiting", assembly="not_ready"
            ),
            "artifact-ready": _collection_state(
                "artifact-ready", assembly="ready"
            ),
            "artifact-assembled": _collection_state(
                "artifact-assembled", assembly="assembled"
            ),
        },
    )
    result = attention.inspect_activity_attention("class-1", "activity-1")
    assert [(item.code, item.count) for item in result.items] == [
        ("concord_collect_assembly", 1)
    ]


def test_collect_confirmation_attention_uses_explicit_association_state_not_absence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifacts = (
        _artifact("artifact-empty", authors=0, subjects=0),
        _artifact("artifact-pending", authors=1, subjects=1),
    )
    _patch_activity(
        monkeypatch,
        artifacts=artifacts,
        collection_states={
            "artifact-empty": _collection_state(
                "artifact-empty", assembly="assembled"
            ),
            "artifact-pending": _collection_state(
                "artifact-pending",
                assembly="assembled",
                author_pending=True,
                subject_pending=True,
            ),
        },
    )
    result = attention.inspect_activity_attention("class-1", "activity-1")
    assert [(item.code, item.count) for item in result.items] == [
        ("concord_collect_author_confirmation", 1),
        ("concord_collect_subject_confirmation", 1),
    ]
    assert all(item.count == 1 for item in result.items)
    assert all(item.action_id == "open_activity_collect" for item in result.items)


def test_collect_assembly_selection_or_recovery_are_actionable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifacts = (
        _artifact("artifact-selection"),
        _artifact("artifact-recovery"),
    )
    _patch_activity(
        monkeypatch,
        artifacts=artifacts,
        collection_states={
            "artifact-selection": _collection_state(
                "artifact-selection", assembly="selection_required"
            ),
            "artifact-recovery": _collection_state(
                "artifact-recovery", assembly="needs_recovery"
            ),
        },
    )
    result = attention.inspect_activity_attention("class-1", "activity-1")
    assert [(item.code, item.count) for item in result.items] == [
        ("concord_collect_assembly", 2)
    ]


def test_collect_attention_does_not_leak_artifact_or_identity_details(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret_artifact = "artifact-secret-student-42"
    _patch_activity(
        monkeypatch,
        artifacts=(_artifact(secret_artifact, authors=1, subjects=1),),
        collection_states={
            secret_artifact: _collection_state(
                secret_artifact,
                assembly="ready",
                author_pending=True,
                subject_pending=True,
            )
        },
    )
    result = attention.inspect_activity_attention("class-1", "activity-1")
    rendered = repr(result)
    assert secret_artifact not in rendered
    assert [item.code for item in result.items] == [
        "concord_collect_assembly",
        "concord_collect_author_confirmation",
        "concord_collect_subject_confirmation",
    ]


def test_prepare_attention_precedes_collect_attention_for_next_action(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_activity(
        monkeypatch,
        packets=(_packet("packet-failed", status="failed"),),
        artifacts=(_artifact("artifact-ready"),),
        collection_states={
            "artifact-ready": _collection_state("artifact-ready", assembly="ready")
        },
    )
    result = attention.inspect_activity_attention("class-1", "activity-1")
    assert [item.task for item in result.items] == ["prepare", "collect"]
    assert result.next_item is not None
    assert result.next_item.code == "concord_prepare_recovery"


def test_review_and_moderation_attention_use_stable_review_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = _artifact("artifact-review")
    _patch_activity(
        monkeypatch,
        artifacts=(artifact,),
        collection_states={
            "artifact-review": _collection_state(
                "artifact-review", assembly="assembled"
            )
        },
        review_states={
            "artifact-review": ArtifactReviewAttentionState(
                class_id="class-1",
                activity_id="activity-1",
                artifact_instance_id="artifact-review",
                first_review_pending=True,
                review_attention_pending=True,
                moderation_pending=True,
                post_moderation_review_pending=True,
            )
        },
    )
    result = attention.inspect_activity_attention("class-1", "activity-1")
    review_items = tuple(item for item in result.items if item.task == "review")
    assert [(item.code, item.count) for item in review_items] == [
        ("concord_review_first", 1),
        ("concord_review_attention", 1),
        ("concord_review_moderation", 1),
        ("concord_review_post_moderation", 1),
    ]
    assert all(item.action_id == "open_activity_review" for item in review_items)


def test_collect_attention_precedes_review_attention_for_next_action(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = _artifact("artifact-review")
    _patch_activity(
        monkeypatch,
        artifacts=(artifact,),
        collection_states={
            "artifact-review": _collection_state(
                "artifact-review",
                assembly="assembled",
                author_pending=True,
            )
        },
        review_states={
            "artifact-review": ArtifactReviewAttentionState(
                class_id="class-1",
                activity_id="activity-1",
                artifact_instance_id="artifact-review",
                first_review_pending=True,
                review_attention_pending=False,
                moderation_pending=False,
                post_moderation_review_pending=False,
            )
        },
    )
    result = attention.inspect_activity_attention("class-1", "activity-1")
    assert [item.code for item in result.items] == [
        "concord_collect_author_confirmation",
        "concord_review_first",
    ]
    assert result.next_item is not None
    assert result.next_item.task == "collect"


def test_scoring_ready_attention_counts_reviewed_evidence_items(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifacts = (_artifact("artifact-a"), _artifact("artifact-b"))
    _patch_activity(
        monkeypatch,
        scoring_orientation="local_criteria_only",
        artifacts=artifacts,
        collection_states={
            item.artifact_instance_id: _collection_state(
                item.artifact_instance_id, assembly="assembled"
            )
            for item in artifacts
        },
        scoring_states={
            item.artifact_instance_id: ArtifactScoringAttentionState(
                class_id="class-1",
                activity_id="activity-1",
                artifact_instance_id=item.artifact_instance_id,
                scoring_ready=True,
            )
            for item in artifacts
        },
    )
    result = attention.inspect_activity_attention("class-1", "activity-1")
    assert [(item.code, item.count) for item in result.items] == [
        ("concord_score_ready", 2)
    ]
    assert result.items[0].task == "score"
    assert result.items[0].action_id == "open_activity_score"


def test_review_attention_precedes_score_attention_for_next_action(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = _artifact("artifact-score")
    _patch_activity(
        monkeypatch,
        scoring_orientation="mixed",
        artifacts=(artifact,),
        collection_states={
            "artifact-score": _collection_state(
                "artifact-score", assembly="assembled"
            )
        },
        review_states={
            "artifact-score": ArtifactReviewAttentionState(
                class_id="class-1",
                activity_id="activity-1",
                artifact_instance_id="artifact-score",
                first_review_pending=False,
                review_attention_pending=True,
                moderation_pending=False,
                post_moderation_review_pending=False,
            )
        },
        scoring_states={
            "artifact-score": ArtifactScoringAttentionState(
                class_id="class-1",
                activity_id="activity-1",
                artifact_instance_id="artifact-score",
                scoring_ready=True,
            )
        },
    )
    result = attention.inspect_activity_attention("class-1", "activity-1")
    assert [item.task for item in result.items] == ["review", "score"]
    assert result.next_item is not None
    assert result.next_item.code == "concord_review_attention"


@pytest.mark.parametrize(
    ("share_status", "expected_code"),
    (
        ("inactive", None),
        ("current", None),
        ("manifest_needed", "concord_share_manifest"),
        ("publish_ready", "concord_share_publish"),
        ("supersede_ready", "concord_share_supersede"),
        ("withdrawn", "concord_share_withdrawn"),
        ("needs_inspection", "concord_share_inspect"),
    ),
)
def test_share_attention_requires_explicit_share_state(
    monkeypatch: pytest.MonkeyPatch,
    share_status: str,
    expected_code: str | None,
) -> None:
    _patch_activity(monkeypatch, share_status=share_status)
    result = attention.inspect_activity_attention("class-1", "activity-1")
    assert [item.code for item in result.items] == (
        [] if expected_code is None else [expected_code]
    )
    if result.items:
        assert result.items[0].count == 1
        assert result.items[0].task == "share"
        assert result.items[0].action_id == "open_activity_share"


def test_score_precedes_share_in_navigation_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = _artifact("artifact-ready")
    _patch_activity(
        monkeypatch,
        artifacts=(artifact,),
        collection_states={"artifact-ready": _collection_state("artifact-ready")},
        scoring_states={
            "artifact-ready": ArtifactScoringAttentionState(
                class_id="class-1",
                activity_id="activity-1",
                artifact_instance_id="artifact-ready",
                scoring_ready=True,
            )
        },
        scoring_orientation="standards_based",
        share_status="publish_ready",
    )
    result = attention.inspect_activity_attention("class-1", "activity-1")
    assert [item.code for item in result.items] == [
        "concord_score_ready",
        "concord_share_publish",
    ]
    assert result.next_item == result.items[0]
