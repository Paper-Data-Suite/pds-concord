from __future__ import annotations

from types import SimpleNamespace

import pytest
from pds_core.routing_models import ModuleWorkRef

import concord.menu_activity as activity_menu
import concord.menu_group as group_menu
import concord.menu_responsibility as responsibility_menu
import concord.menu_role as role_menu
import concord.menu_session as session_menu
from concord.menu_context import MenuSessionContext
from concord.models import EffectiveContext
from concord.workflows import (
    ActivitySummary,
    ClassSummary,
    GroupSummary,
    SessionSummary,
    WorkflowActor,
    WorkflowCommitResult,
)


def _activity(snapshot: int = 7) -> ActivitySummary:
    return ActivitySummary(
        class_id="class-1",
        activity_id="seminar-1",
        title="Seminar One",
        status="draft",
        scoring_orientation="evidence_only",
        session_count=1,
        group_count=0,
        snapshot_revision=snapshot,
    )


def _commit(snapshot: int = 8) -> WorkflowCommitResult:
    return WorkflowCommitResult(
        work=ModuleWorkRef(
            module_id="concord",
            class_id="class-1",
            work_id="seminar-1",
        ),
        snapshot_revision=snapshot,
        snapshot_sha256="a" * 64,
        changed_records=(),
        no_op=False,
    )


def _state() -> MenuSessionContext:
    return MenuSessionContext(actor=WorkflowActor(actor_id="teacher-1"))


def test_menu_actor_is_collected_once_and_reused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        "builtins.input",
        lambda prompt="": calls.append(prompt) or "teacher-1",
    )
    state = MenuSessionContext()
    first = state.require_actor()
    second = state.require_actor()
    assert first is second
    assert first.actor_id == "teacher-1"
    assert len(calls) == 1


def test_activity_creation_calls_shared_atomic_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[object] = []
    state = _state()
    monkeypatch.setattr(
        activity_menu,
        "resolve_read_workspace_root",
        lambda: SimpleNamespace(),
    )
    monkeypatch.setattr(
        activity_menu,
        "list_available_classes",
        lambda _root: (ClassSummary(class_id="class-1", school_year="2026-2027"),),
    )
    monkeypatch.setattr(
        activity_menu,
        "choose_class",
        lambda _classes: ClassSummary(class_id="class-1", school_year="2026-2027"),
    )
    values = iter(
        [
            "Seminar One",
            "seminar-1",
            None,
            "seminar-1-session-1",
            "Day 1",
        ]
    )
    monkeypatch.setattr(activity_menu, "prompt_text", lambda *a, **k: next(values))
    monkeypatch.setattr(
        activity_menu, "_choose_activity_type", lambda: "socratic_seminar"
    )
    monkeypatch.setattr(
        activity_menu, "_choose_scoring_orientation", lambda: "evidence_only"
    )
    monkeypatch.setattr(
        activity_menu,
        "_standards_selection",
        lambda _orientation: (None, None, ()),
    )
    monkeypatch.setattr(activity_menu, "confirm_write", lambda *a, **k: True)
    monkeypatch.setattr(activity_menu, "show_result", lambda *a, **k: None)

    def fake_create(request: object, **kwargs: object) -> object:
        captured.append(request)
        return SimpleNamespace(
            commit=_commit(1),
            activity_id="seminar-1",
            first_session_id="seminar-1-session-1",
        )

    monkeypatch.setattr(activity_menu, "create_activity_context", fake_create)
    activity_menu._create_activity(state)
    assert len(captured) == 1
    request = captured[0]
    assert getattr(request, "activity_id") == "seminar-1"
    assert getattr(request, "session_id") == "seminar-1-session-1"
    assert getattr(request, "actor").actor_id == "teacher-1"


def test_session_add_uses_latest_snapshot(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[object] = []
    current = _activity(11)
    monkeypatch.setattr(session_menu, "_latest", lambda _activity: current)
    monkeypatch.setattr(
        session_menu,
        "list_sessions",
        lambda *_a: (
            SessionSummary(
                class_id="class-1",
                activity_id="seminar-1",
                session_id="s1",
                sequence=1,
                label="Day 1",
                status="planned",
                scheduled_start=None,
                snapshot_revision=11,
            ),
        ),
    )
    text_values = iter(["Day 2", "seminar-1-session-2"])
    monkeypatch.setattr(session_menu, "prompt_text", lambda *a, **k: next(text_values))
    monkeypatch.setattr(session_menu, "prompt_positive_int", lambda *a, **k: 2)
    monkeypatch.setattr(session_menu, "confirm_write", lambda *a, **k: True)
    monkeypatch.setattr(session_menu, "show_result", lambda *a, **k: None)

    def fake_create(request: object) -> object:
        captured.append(request)
        return SimpleNamespace(commit=_commit(12), session_id="seminar-1-session-2")

    monkeypatch.setattr(session_menu, "create_session", fake_create)
    session_menu._add(current, _state())
    request = captured[0]
    assert getattr(request, "expected_snapshot_revision") == 11
    assert getattr(request, "sequence") == 2


def test_membership_add_uses_roster_identity_and_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[object] = []
    current = _activity(12)
    group = GroupSummary(
        class_id="class-1",
        activity_id="seminar-1",
        group_id="group-a",
        label="Group A",
        status="active",
        member_count=0,
        parent_group_id=None,
        effective_session_count=0,
        snapshot_revision=12,
    )
    session = SessionSummary(
        class_id="class-1",
        activity_id="seminar-1",
        session_id="s1",
        sequence=1,
        label="Day 1",
        status="active",
        scheduled_start=None,
        snapshot_revision=12,
    )
    student = SimpleNamespace(
        student_id="student-1", first_name="Ada", last_name="Lovelace"
    )
    context = EffectiveContext(activity_id="seminar-1", session_ids=("s1",))
    monkeypatch.setattr(group_menu, "_latest", lambda _activity: current)
    monkeypatch.setattr(group_menu, "list_groups", lambda *_a: (group,))
    monkeypatch.setattr(group_menu, "choose_group", lambda *_a, **_k: group)
    monkeypatch.setattr(group_menu, "list_sessions", lambda *_a: (session,))
    monkeypatch.setattr(group_menu, "choose_effective_context", lambda *_a: context)
    monkeypatch.setattr(group_menu, "resolve_workspace_root", lambda: SimpleNamespace())
    monkeypatch.setattr(group_menu, "choose_students", lambda *_a: (student,))
    monkeypatch.setattr(group_menu, "confirm_write", lambda *a, **k: True)
    monkeypatch.setattr(group_menu, "show_result", lambda *a, **k: None)

    def fake_add(request: object) -> object:
        captured.append(request)
        return SimpleNamespace(
            commit=_commit(13),
            membership_ids=("membership-new",),
        )

    monkeypatch.setattr(group_menu, "add_memberships", fake_add)
    group_menu._add_member(current, _state())
    request = captured[0]
    assert getattr(request, "group_id") == "group-a"
    members = getattr(request, "members")
    assert len(members) == 1
    assert members[0].student_id == "student-1"
    assert members[0].effective_context == context
    assert getattr(request, "expected_snapshot_revision") == 12


def test_role_assign_uses_shared_service(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[object] = []
    current = _activity(4)
    student = SimpleNamespace(
        student_id="student-1", first_name="Ada", last_name="Lovelace"
    )
    context = EffectiveContext(activity_id="seminar-1", session_ids=("s1",))
    participant = SimpleNamespace(participant_id="student-1")
    monkeypatch.setattr(role_menu, "_latest", lambda _activity: current)
    monkeypatch.setattr(role_menu, "resolve_workspace_root", lambda: SimpleNamespace())
    monkeypatch.setattr(role_menu, "choose_student", lambda *_a: student)
    monkeypatch.setattr(role_menu, "_choose_role_key", lambda: "facilitator")
    monkeypatch.setattr(role_menu, "_choose_optional_group", lambda _a: None)
    monkeypatch.setattr(role_menu, "list_sessions", lambda *_a: (SimpleNamespace(),))
    monkeypatch.setattr(role_menu, "choose_effective_context", lambda *_a: context)
    monkeypatch.setattr(role_menu, "confirm_write", lambda *a, **k: True)
    monkeypatch.setattr(role_menu, "show_result", lambda *a, **k: None)
    monkeypatch.setattr(role_menu, "core_student_participant", lambda *_a: participant)

    def fake_assign(request: object) -> object:
        captured.append(request)
        return SimpleNamespace(commit=_commit(5), role_assignment_id="role-new")

    monkeypatch.setattr(role_menu, "assign_role", fake_assign)
    role_menu._assign(current, _state())
    request = captured[0]
    assert getattr(request, "role_key") == "facilitator"
    assert getattr(request, "expected_snapshot_revision") == 4


def test_responsibility_group_assignee_stays_group(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[object] = []
    current = _activity(6)
    assignee = SimpleNamespace(record_kind="group", record_id="group-a")
    context = EffectiveContext(activity_id="seminar-1", session_ids=("s1",))
    monkeypatch.setattr(responsibility_menu, "_latest", lambda _activity: current)
    monkeypatch.setattr(
        responsibility_menu,
        "_choose_assignee",
        lambda _activity: (assignee, "group-a", "Group A"),
    )
    monkeypatch.setattr(
        responsibility_menu,
        "prompt_text",
        lambda *a, **k: "Record observations" if "Responsibility" in a[0] else None,
    )
    monkeypatch.setattr(
        responsibility_menu,
        "list_sessions",
        lambda *_a: (SimpleNamespace(),),
    )
    monkeypatch.setattr(
        responsibility_menu,
        "choose_effective_context",
        lambda *_a: context,
    )
    monkeypatch.setattr(responsibility_menu, "confirm_write", lambda *a, **k: True)
    monkeypatch.setattr(responsibility_menu, "show_result", lambda *a, **k: None)

    def fake_assign(request: object) -> object:
        captured.append(request)
        return SimpleNamespace(
            commit=_commit(7),
            responsibility_assignment_id="responsibility-new",
        )

    monkeypatch.setattr(responsibility_menu, "assign_responsibility", fake_assign)
    responsibility_menu._assign(current, _state())
    request = captured[0]
    assert getattr(request, "group_id") == "group-a"
    assert getattr(request, "assignee_reference").record_kind == "group"


def test_activity_context_delegates_to_session_menu_with_same_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    activity = _activity()
    state = _state()
    called: list[object] = []
    inputs = iter(["1", "2", "b", "b"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))
    monkeypatch.setattr(activity_menu, "clear_screen", lambda: None)
    monkeypatch.setattr(
        activity_menu,
        "show_activity",
        lambda *_a: SimpleNamespace(summary=activity),
    )
    monkeypatch.setattr(
        activity_menu,
        "launch_session_menu",
        lambda _activity, received: called.append(received),
    )
    activity_menu.launch_activity_context_menu(activity, state)
    assert called == [state]
