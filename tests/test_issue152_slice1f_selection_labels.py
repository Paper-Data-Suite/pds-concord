"""Concord #152 Slice 1F: exact, privacy-safe routine Score selection labels."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

import concord.menu_artifact_scoring as menu
from concord.models import ScoreTargetReference, SubjectReference
from concord.workflows import ActivitySummary, ConcordWorkflowValidationError
from concord.workflows.artifact_routine_scoring import (
    ArtifactRoutineScoringContext,
)
from concord.workflows.artifact_routine_scoring_selection import (
    RoutineScoreTargetCandidate,
    RoutineScoreTargetOptions,
)


def _activity() -> ActivitySummary:
    return cast(
        ActivitySummary,
        SimpleNamespace(
            class_id="synthetic-class",
            activity_id="synthetic-activity",
            title="Synthetic discussion",
        ),
    )


def _context(
    *,
    groups: tuple[object, ...] = (),
    sessions: tuple[object, ...] = (),
) -> ArtifactRoutineScoringContext:
    return cast(
        ArtifactRoutineScoringContext,
        SimpleNamespace(
            class_id="synthetic-class",
            activity_id="synthetic-activity",
            current_groups=groups,
            current_sessions=sessions,
            artifact=SimpleNamespace(artifact_instance_id="artifact-1"),
        ),
    )


def _student(student_id: str) -> ScoreTargetReference:
    return ScoreTargetReference(
        target_kind="core_student",
        target_id=student_id,
        owning_system="core",
    )


def _group(group_id: str) -> ScoreTargetReference:
    return ScoreTargetReference(
        target_kind="concord_group",
        target_id=group_id,
        owning_system="concord",
    )


def _options(*references: ScoreTargetReference) -> RoutineScoreTargetOptions:
    return RoutineScoreTargetOptions(
        candidates=tuple(
            RoutineScoreTargetCandidate(
                target_reference=reference,
                candidate_sources=("synthetic",),
                compatible_criterion_ids=("criterion-1",),
            )
            for reference in references
        ),
        supported_target_kinds=tuple(
            dict.fromkeys(reference.target_kind for reference in references)
        ),
    )


def test_missing_selected_workspace_never_displays_student_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(menu, "resolve_read_workspace_root", lambda: None)
    with pytest.raises(ConcordWorkflowValidationError) as caught:
        menu._target_label(_activity(), _context(), _student("private-student-7"))
    assert "Core student roster" in str(caught.value)
    assert "private-student-7" not in str(caught.value)
    assert "no Score was recorded" in str(caught.value)


def test_unavailable_roster_label_is_not_an_opaque_id_fallback(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        menu, "resolve_read_workspace_root", lambda: tmp_path
    )
    monkeypatch.setattr(menu, "participant_display_label", lambda *_a: None)
    with pytest.raises(ConcordWorkflowValidationError) as caught:
        menu._target_label(_activity(), _context(), _student("private-student-7"))
    assert "Core student label" in str(caught.value)
    assert "private-student-7" not in str(caught.value)


def test_unexpected_roster_failure_is_sanitized(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        menu, "resolve_read_workspace_root", lambda: tmp_path
    )

    def fail(*_args: object) -> None:
        raise RuntimeError("private filesystem path and raw roster identities")

    monkeypatch.setattr(menu, "participant_display_label", fail)
    with pytest.raises(ConcordWorkflowValidationError) as caught:
        menu._target_label(_activity(), _context(), _student("private-student-7"))
    assert "Core student labels could not be verified" in str(caught.value)
    assert "private filesystem" not in str(caught.value)
    assert "private-student-7" not in str(caught.value)


@pytest.mark.parametrize(
    "group",
    (
        None,
        SimpleNamespace(
            group_id="private-group-2",
            activity_id="unrelated-activity",
            label="Foreign Cluster",
        ),
        SimpleNamespace(
            group_id="private-group-2",
            activity_id="synthetic-activity",
            label="  ",
        ),
    ),
)
def test_missing_foreign_or_blank_cluster_label_blocks_target(
    group: object | None,
) -> None:
    groups = () if group is None else (group,)
    with pytest.raises(ConcordWorkflowValidationError) as caught:
        menu._target_label(
            _activity(),
            _context(groups=groups),
            _group("private-group-2"),
        )
    assert "Cluster Group" in str(caught.value)
    assert "private-group-2" not in str(caught.value)


def test_valid_group_label_retains_exact_target_identity() -> None:
    context = _context(
        groups=(
            SimpleNamespace(
                group_id="group-1",
                activity_id="synthetic-activity",
                label="Cluster One",
            ),
        ),
    )
    assert menu._target_label(_activity(), context, _group("group-1")) == (
        "Cluster One — group"
    )


def test_unlabeled_session_uses_verified_sequence_not_record_id() -> None:
    context = _context(
        sessions=(
            SimpleNamespace(
                session_id="private-session-2",
                activity_id="synthetic-activity",
                sequence=2,
                label=None,
            ),
        ),
    )
    assert menu._session_label(context, "private-session-2") == "Session 2"


def test_missing_session_refuses_to_guess_or_show_record_id() -> None:
    with pytest.raises(ConcordWorkflowValidationError) as caught:
        menu._session_label(_context(), "private-session-2")
    assert "Score Session" in str(caught.value)
    assert "private-session-2" not in str(caught.value)


def test_unrelated_artifact_target_does_not_leak_id() -> None:
    reference = ScoreTargetReference(
        target_kind="concord_artifact_instance",
        target_id="private-other-artifact",
        owning_system="concord",
    )
    with pytest.raises(ConcordWorkflowValidationError) as caught:
        menu._target_label(_activity(), _context(), reference)
    assert "Selected Artifact" in str(caught.value)
    assert "private-other-artifact" not in str(caught.value)


def test_missing_group_subject_label_cannot_enter_evidence_selection() -> None:
    subject = SubjectReference(
        subject_kind="concord_group",
        subject_id="private-group-2",
        owning_system="concord",
    )
    with pytest.raises(ConcordWorkflowValidationError) as caught:
        menu._subject_label(_activity(), _context(), subject)
    assert "Cluster Group" in str(caught.value)
    assert "private-group-2" not in str(caught.value)


def test_ambiguous_student_names_disambiguate_without_selecting_by_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    one, two = _student("student-1"), _student("student-2")
    monkeypatch.setattr(
        menu, "routine_target_options", lambda _context: _options(one, two)
    )
    monkeypatch.setattr(
        menu, "_student_label", lambda *_args: "Jordan Lee"
    )
    observed: dict[str, object] = {}

    def select(
        title: str,
        options: object,
        labels: tuple[str, ...],
        **_kwargs: object,
    ) -> RoutineScoreTargetCandidate:
        assert title == "Choose Score Target"
        observed["labels"] = labels
        return cast(tuple[RoutineScoreTargetCandidate, ...], options)[1]

    monkeypatch.setattr(menu, "select_one", select)
    chosen = menu._choose_target(_activity(), _context())
    assert chosen == two
    labels = cast(tuple[str, ...], observed["labels"])
    assert "1 of 2" in labels[0]
    assert "2 of 2" in labels[1]
    assert labels[0] != labels[1]
    assert labels[2].startswith("Other supported target")


def test_missing_student_label_blocks_before_target_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        menu, "routine_target_options",
        lambda _context: _options(_student("private-student-7")),
    )
    monkeypatch.setattr(menu, "resolve_read_workspace_root", lambda: None)

    def never_select(*_args: object, **_kwargs: object) -> None:
        pytest.fail("No Score target should be chosen without a verified label.")

    monkeypatch.setattr(menu, "select_one", never_select)
    with pytest.raises(ConcordWorkflowValidationError, match="Core student roster"):
        menu._choose_target(_activity(), _context())


def test_duplicate_evidence_subject_labels_are_distinguishable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    subjects = (
        SubjectReference(
            subject_kind="core_student",
            subject_id="student-1",
            owning_system="core",
        ),
        SubjectReference(
            subject_kind="core_student",
            subject_id="student-2",
            owning_system="core",
        ),
    )
    monkeypatch.setattr(
        menu, "routine_subject_context_options",
        lambda *_args: subjects,
    )
    monkeypatch.setattr(menu, "_student_label", lambda *_args: "Jordan Lee")
    monkeypatch.setattr(menu, "select_one", lambda *_args, **_kw: "select")
    labels_seen: list[tuple[str, ...]] = []

    def select_many(
        _title: str, items: tuple[SubjectReference, ...],
        labels: tuple[str, ...], **_kwargs: object,
    ) -> tuple[SubjectReference, ...]:
        assert items == subjects
        labels_seen.append(labels)
        return (items[1],)

    monkeypatch.setattr(menu, "select_many", select_many)
    chosen = menu._choose_subject_context(
        _activity(), _context(), _student("student-2"), "criterion-1"
    )
    assert chosen == (subjects[1],)
    assert len(labels_seen) == 1
    assert "1 of 2" in labels_seen[0][0]
    assert "2 of 2" in labels_seen[0][1]
