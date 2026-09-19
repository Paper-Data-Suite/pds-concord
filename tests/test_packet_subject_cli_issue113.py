from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from concord.cli_app.handlers import packet_runtime
from concord.models import SubjectReference


def _artifact(
    *,
    authorship_mode: str,
    subject: SubjectReference,
    role: str,
) -> SimpleNamespace:
    return SimpleNamespace(
        packet_component_id="component-review",
        authorship_mode=authorship_mode,
        proposed_subject_reference=subject,
        proposed_subject_role=role,
    )


def test_peer_relationship_preview_is_human_readable_for_student(
    monkeypatch,
) -> None:
    prepared = SimpleNamespace(
        request=SimpleNamespace(
            class_id="class-1",
            activity_id="activity-1",
        ),
        activity=SimpleNamespace(
            activity_id="activity-1",
            title="Peer Review",
        ),
        session=SimpleNamespace(
            session_id="session-1",
            sequence=1,
            label="Session One",
        ),
    )
    roster = SimpleNamespace()
    monkeypatch.setattr(
        packet_runtime,
        "resolve_read_workspace_root",
        lambda path: Path(path) if path is not None else None,
    )
    monkeypatch.setattr(packet_runtime, "load_required_roster", lambda *_args: roster)
    monkeypatch.setattr(
        packet_runtime,
        "participant_print_label",
        lambda _roster, participant: (
            "Blair T." if participant.participant_id == "student-2" else None
        ),
    )
    line = packet_runtime._relationship_preview(
        prepared,
        _artifact(
            authorship_mode="individual_author",
            subject=SubjectReference(
                subject_kind="core_student",
                subject_id="student-2",
                owning_system="core",
            ),
            role="reviewed_subject",
        ),
        target_label="Alex O.",
        workspace_root=Path("workspace"),
    )
    assert line == "Reviewer: Alex O. | Reviewee: Blair T."


def test_group_relationship_preview_uses_group_label(monkeypatch) -> None:
    prepared = SimpleNamespace(
        request=SimpleNamespace(
            class_id="class-1",
            activity_id="activity-1",
        ),
        activity=SimpleNamespace(
            activity_id="activity-1",
            title="Peer Review",
        ),
        session=SimpleNamespace(
            session_id="session-1",
            sequence=1,
            label="Session One",
        ),
    )
    monkeypatch.setattr(
        packet_runtime,
        "show_group",
        lambda *_args, **_kwargs: SimpleNamespace(
            summary=SimpleNamespace(label="Group B")
        ),
    )
    line = packet_runtime._relationship_preview(
        prepared,
        _artifact(
            authorship_mode="individual_author",
            subject=SubjectReference(
                subject_kind="concord_group",
                subject_id="group-b",
                owning_system="concord",
            ),
            role="reviewed_subject",
        ),
        target_label="Alex O.",
        workspace_root=Path("workspace"),
    )
    assert line == "Reviewer: Alex O. | Reviewed: Group B"


def test_observer_relationship_preview_uses_session_label() -> None:
    prepared = SimpleNamespace(
        request=SimpleNamespace(
            class_id="class-1",
            activity_id="activity-1",
        ),
        activity=SimpleNamespace(
            activity_id="activity-1",
            title="Fishbowl",
        ),
        session=SimpleNamespace(
            session_id="session-1",
            sequence=1,
            label="Seminar Session 1",
        ),
    )
    line = packet_runtime._relationship_preview(
        prepared,
        _artifact(
            authorship_mode="observer",
            subject=SubjectReference(
                subject_kind="concord_session",
                subject_id="session-1",
                owning_system="concord",
            ),
            role="session_context",
        ),
        target_label="Alex O.",
        workspace_root=None,
    )
    assert line == "Observer: Alex O. | Observed: Seminar Session 1"
