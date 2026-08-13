from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from concord import menu_artifact
from concord.menu_context import MenuSessionContext
from concord.menu_navigation import QuitPDS, ReturnToMainMenu
from concord.models import (
    EvidenceReference,
    PrivacyPolicy,
    SubjectReference,
)
from concord.workflows import ActivitySummary, WorkflowActor


def _activity() -> ActivitySummary:
    return cast(
        ActivitySummary,
        SimpleNamespace(
            title="Issue 29 Menu",
            class_id="class-1",
            activity_id="activity-1",
            snapshot_revision=9,
        ),
    )


def _state() -> MenuSessionContext:
    return MenuSessionContext(actor=WorkflowActor(actor_id="teacher-1"))


def test_artifact_menu_adds_review_and_moderation_without_renumbering(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("builtins.input", lambda _prompt="": "B")
    menu_artifact.launch_artifact_page_menu(_activity(), _state())
    output = capsys.readouterr().out
    assert "1. Prepare Artifact Pages" in output
    assert "2. List / inspect Artifact Pages" in output
    assert "3. Render prepared pages" in output
    assert "4. List / inspect Artifacts" in output
    assert "5. Assemble returned Artifact" in output
    assert "6. Authors" in output
    assert "7. Subjects" in output
    assert "8. Review" in output
    assert "9. Moderation" in output


@pytest.mark.parametrize(
    ("surface", "key", "expected"),
    (
        ("8", "M", ReturnToMainMenu),
        ("8", "Q", QuitPDS),
        ("9", "M", ReturnToMainMenu),
        ("9", "Q", QuitPDS),
    ),
)
def test_issue29_nested_navigation_unwinds(
    surface: str,
    key: str,
    expected: type[BaseException],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    answers = iter((surface, key))
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    with pytest.raises(expected):
        menu_artifact.launch_artifact_page_menu(_activity(), _state())


def test_record_review_uses_explicit_context_and_review_confirmation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = SimpleNamespace(
        artifact_instance_id="artifact-1",
        artifact_status="partially_returned",
        returned_required_page_count=1,
        required_return_page_count=2,
        current_author_count=2,
        current_subject_count=1,
    )
    detail = SimpleNamespace(privacy_classification="teacher_restricted")
    captured: list[object] = []
    confirmations: list[str] = []
    result = SimpleNamespace(
        artifact_review_id="review-generated",
        commit=SimpleNamespace(snapshot_revision=10),
    )

    monkeypatch.setattr(menu_artifact, "_latest", lambda activity: activity)
    monkeypatch.setattr(
        menu_artifact,
        "_choose_artifact",
        lambda *_args, **_kwargs: artifact,
    )
    monkeypatch.setattr(
        menu_artifact,
        "show_artifact",
        lambda *_args, **_kwargs: detail,
    )
    monkeypatch.setattr(menu_artifact, "show_result", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        menu_artifact,
        "prompt_text",
        lambda *_args, **_kwargs: "review-generated",
    )
    monkeypatch.setattr(
        menu_artifact,
        "_review_values",
        lambda: (
            "readable",
            "partially_complete",
            "correct",
            "confirmed",
            "confirmed",
            "teacher_restricted",
            "relevant",
            "required",
            "not_ready",
            "moderation_required",
            "Explicit teacher judgment.",
            PrivacyPolicy(classification="teacher_restricted"),
        ),
    )

    def _confirm(_title: str, expected: str, _lines: object) -> bool:
        confirmations.append(expected)
        return True

    monkeypatch.setattr(menu_artifact, "confirm_write", _confirm)
    monkeypatch.setattr(
        menu_artifact,
        "add_artifact_review",
        lambda request: captured.append(request) or result,
    )

    menu_artifact._record_review(_activity(), _state())

    assert confirmations == ["REVIEW"]
    assert len(captured) == 1
    request = captured[0]
    assert request.artifact_instance_id == "artifact-1"
    assert request.page_completeness_judgment == "partially_complete"
    assert request.moderation_requirement == "required"
    assert request.scoring_readiness == "not_ready"
    assert request.review_outcome == "moderation_required"


def test_moderation_revision_preserves_exact_predecessor_scope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence = EvidenceReference(
        evidence_kind="artifact_instance",
        owning_system="concord",
        record_id="artifact-1",
        moderation_requirement="required",
    )
    subject = SubjectReference(
        subject_kind="core_student",
        owning_system="core",
        subject_id="student-1",
    )
    predecessor = SimpleNamespace(
        moderation_record_id="moderation-before",
        evidence_reference=evidence,
        target_subject_references=(subject,),
        status="disputed",
        permitted_use="corroborate_only",
        is_current=True,
    )
    prompts = iter(
        (
            "moderation-after",
            "correction-moderation-1",
            "Corroborating evidence resolved the dispute.",
        )
    )
    captured: list[object] = []
    confirmations: list[str] = []
    result = SimpleNamespace(
        moderation_record_id="moderation-after",
        commit=SimpleNamespace(snapshot_revision=10),
    )

    monkeypatch.setattr(menu_artifact, "_latest", lambda activity: activity)
    monkeypatch.setattr(
        menu_artifact,
        "list_moderation_records",
        lambda *_args, **_kwargs: (predecessor,),
    )
    monkeypatch.setattr(
        menu_artifact,
        "select_one",
        lambda *_args, **_kwargs: predecessor,
    )
    monkeypatch.setattr(
        menu_artifact,
        "prompt_text",
        lambda *_args, **_kwargs: next(prompts),
    )
    monkeypatch.setattr(
        menu_artifact,
        "_moderation_values",
        lambda: (
            "accepted",
            "support_named_subject",
            "Now sufficiently corroborated.",
            None,
            PrivacyPolicy(classification="teacher_restricted"),
        ),
    )

    def _confirm(_title: str, expected: str, _lines: object) -> bool:
        confirmations.append(expected)
        return True

    monkeypatch.setattr(menu_artifact, "confirm_write", _confirm)
    monkeypatch.setattr(
        menu_artifact,
        "replace_moderation_record",
        lambda request: captured.append(request) or result,
    )
    monkeypatch.setattr(menu_artifact, "show_result", lambda *_args, **_kwargs: None)

    menu_artifact._replace_moderation(_activity(), _state())

    assert confirmations == ["REVISE"]
    assert len(captured) == 1
    request = captured[0]
    assert request.target_evidence_reference is evidence
    assert request.target_subject_references == (subject,)
    assert request.replacement_moderation_record_id == "moderation-after"


def test_moderation_student_scope_supports_several_core_students(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    students = (
        SimpleNamespace(student_id="student-1"),
        SimpleNamespace(student_id="student-2"),
    )
    monkeypatch.setattr(
        menu_artifact,
        "select_one",
        lambda *_args, **_kwargs: "students",
    )
    monkeypatch.setattr(
        menu_artifact,
        "_require_workspace",
        lambda: Path("."),
    )
    monkeypatch.setattr(
        menu_artifact,
        "choose_students",
        lambda *_args, **_kwargs: students,
    )
    scope = menu_artifact._choose_moderation_subjects(_activity())
    assert [item.subject_kind for item in scope] == [
        "core_student",
        "core_student",
    ]
    assert [item.subject_id for item in scope] == ["student-1", "student-2"]
    assert all(item.owning_system == "core" for item in scope)


def test_moderation_general_scope_remains_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        menu_artifact,
        "select_one",
        lambda *_args, **_kwargs: "general",
    )
    assert menu_artifact._choose_moderation_subjects(_activity()) == ()


def test_review_history_uses_shared_pagination_after_ten(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    items = tuple(
        SimpleNamespace(
            artifact_review_id=f"review-{index}",
            artifact_instance_id="artifact-1",
            review_outcome="ready",
            scoring_readiness="ready",
            is_current=index == 11,
        )
        for index in range(1, 12)
    )
    selected_ids: list[str] = []
    answers = iter(("N", "1"))

    monkeypatch.setattr(
        menu_artifact,
        "list_artifact_reviews",
        lambda *_args, **_kwargs: items,
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))

    def _show(_class_id: str, _activity_id: str, review_id: str) -> object:
        selected_ids.append(review_id)
        return object()

    monkeypatch.setattr(menu_artifact, "show_artifact_review", _show)
    monkeypatch.setattr(menu_artifact, "_show_review_detail", lambda _item: None)

    menu_artifact._view_review_history(_activity())
    assert selected_ids == ["review-11"]


def test_applicable_moderation_returns_candidates_without_heuristic_choice(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence = EvidenceReference(
        evidence_kind="artifact_instance",
        owning_system="concord",
        record_id="artifact-1",
        moderation_requirement="not_required",
    )
    candidates = (
        SimpleNamespace(
            moderation_record_id="moderation-general",
            evidence_reference=evidence,
            target_subject_references=(),
            status="accepted",
            permitted_use="corroborate_only",
            qualification=None,
            is_current=True,
        ),
        SimpleNamespace(
            moderation_record_id="moderation-student",
            evidence_reference=evidence,
            target_subject_references=(
                SubjectReference(
                    subject_kind="core_student",
                    owning_system="core",
                    subject_id="student-1",
                ),
            ),
            status="accepted",
            permitted_use="support_named_subject",
            qualification=None,
            is_current=True,
        ),
    )
    selected_counts: list[int] = []

    monkeypatch.setattr(
        menu_artifact,
        "_choose_moderation_evidence",
        lambda _activity: evidence,
    )
    monkeypatch.setattr(
        menu_artifact,
        "_choose_moderation_subjects",
        lambda _activity: candidates[1].target_subject_references,
    )
    monkeypatch.setattr(
        menu_artifact,
        "list_applicable_moderation_records",
        lambda *_args, **_kwargs: candidates,
    )

    def _select(
        _title: str,
        items: object,
        _labels: object,
        **_kwargs: object,
    ) -> object:
        selected_counts.append(len(items))
        return candidates[1]

    monkeypatch.setattr(menu_artifact, "select_one", _select)
    monkeypatch.setattr(menu_artifact, "show_result", lambda *_args, **_kwargs: None)

    menu_artifact._view_applicable_moderation(_activity())
    assert selected_counts == [2]
