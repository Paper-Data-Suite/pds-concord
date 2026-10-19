"""#136 Slice 2: characterize real teacher-menu -> workflow context boundaries.

All identities and student data in these tests are synthetic.
"""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

import concord.menu_group as group_menu
import concord.menu_group_plan as plan_menu
import concord.menu_session as session_menu
import concord.menu_standards_context as context
from concord.menu_context import MenuSessionContext
from concord.workflows import ActivitySummary, GroupPlanDetail, WorkflowActor

ROOT = Path(__file__).resolve().parents[1]

# Each named public service is called from one normal teacher-menu boundary.
# These guards catch the precise omission class behind the classroom failure.
EXPECTED: dict[str, tuple[str, ...]] = {
    "concord/menu_group_plan.py": (
        "create_random_group_plan",
        "import_arrangement_group_plan",
        "add_planned_group",
        "edit_planned_group",
        "remove_planned_group",
        "place_student_in_plan",
        "unassign_student_from_plan",
        "refresh_group_plan_roster",
        "replace_group_plan_from_arrangement",
        "preview_group_plan",
        "approve_group_plan",
        "cancel_group_plan",
    ),
    "concord/menu_group_plan_signal.py": ("create_signal_group_plan",),
    "concord/menu_group_plan_missing_signal.py": ("set_missing_signal_disposition",),
    "concord/menu_group_plan_application.py": (
        "prepare_group_plan_application",
        "apply_group_plan",
    ),
    "concord/menu_group.py": (
        "create_group",
        "update_group",
        "add_memberships",
        "end_membership",
        "reassign_membership",
    ),
    "concord/menu_session.py": ("create_session", "update_session"),
    "concord/menu_role.py": (
        "assign_role",
        "end_role",
        "reassign_role",
        "prepare_role_preset_application",
        "apply_role_preset",
        "prepare_role_preset_from_assignment",
        "save_role_preset_from_assignment",
    ),
    "concord/menu_responsibility.py": (
        "assign_responsibility",
        "end_responsibility",
        "reassign_responsibility",
        "prepare_responsibility_preset_application",
        "apply_responsibility_preset",
        "prepare_responsibility_preset_from_assignment",
        "save_responsibility_preset_from_assignment",
    ),
}


@pytest.mark.parametrize(
    ("path", "service"),
    [(path, name) for path, names in EXPECTED.items() for name in names],
)
def test_teacher_boundary_forwards_context(path: str, service: str) -> None:
    module = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    calls = [
        node
        for node in ast.walk(module)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == service
    ]
    assert len(calls) == 1, f"{path}: {service} call disappeared or duplicated"
    call = calls[0]
    assert any(
        keyword.arg is None and isinstance(keyword.value, (ast.Call, ast.Name))
        for keyword in call.keywords
    ), f"{path}: {service} lost the canonical Standards context expansion"


def _activity(orientation: str) -> ActivitySummary:
    return ActivitySummary(
        class_id="class-synthetic",
        activity_id="activity-synthetic",
        title="Synthetic classroom activity",
        status="draft",
        scoring_orientation=orientation,
        session_count=1,
        group_count=0,
        snapshot_revision=11,
    )


def _state() -> MenuSessionContext:
    return MenuSessionContext(actor=WorkflowActor(actor_id="teacher-synthetic"))


@pytest.mark.parametrize("orientation", ["mixed", "standards_based"])
def test_standards_kwargs_select_exact_canonical_library(
    monkeypatch: pytest.MonkeyPatch,
    orientation: str,
) -> None:
    library = object()
    loads: list[int] = []

    def load() -> object:
        loads.append(1)
        return library

    monkeypatch.setattr(context, "load_menu_standards_library", load)
    assert context.standards_kwargs_for_activity(_activity(orientation)) == {
        "standards_library": library,
    }
    assert loads == [1]


@pytest.mark.parametrize("orientation", ["evidence_only", "local_criteria_only"])
def test_neutral_modes_do_not_load_core_library(
    monkeypatch: pytest.MonkeyPatch,
    orientation: str,
) -> None:
    monkeypatch.setattr(
        context,
        "load_menu_standards_library",
        lambda: pytest.fail("Neutral mode loaded the Core library"),
    )
    assert context.standards_kwargs_for_activity(_activity(orientation)) == {}


def test_plan_context_uses_live_activity_not_plan_strategy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    library = object()
    activity = _activity("mixed")
    loads: list[int] = []
    monkeypatch.setattr(
        context,
        "show_activity",
        lambda class_id, activity_id: (
            loads.append(1) or SimpleNamespace(summary=activity)
        ),
    )
    monkeypatch.setattr(context, "load_menu_standards_library", lambda: library)
    plan = cast(
        GroupPlanDetail,
        SimpleNamespace(
            summary=SimpleNamespace(
                class_id=activity.class_id,
                activity_id=activity.activity_id,
            ),
        ),
    )
    assert context.standards_kwargs_for_plan(plan) == {
        "standards_library": library,
    }
    assert loads == [1]


def test_missing_library_fails_before_teacher_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(context, "load_menu_standards_library", lambda: None)
    with pytest.raises(Exception, match="Core Standards Library is unavailable"):
        context.standards_kwargs_for_activity(_activity("mixed"))


def test_random_menu_forwards_library_and_current_snapshot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current = _activity("mixed")
    library = object()
    forwarded: list[tuple[object, object | None]] = []
    monkeypatch.setattr(plan_menu, "_latest", lambda _activity: current)
    monkeypatch.setattr(plan_menu, "prompt_text", lambda *a, **k: "plan-synthetic")
    monkeypatch.setattr(plan_menu, "prompt_exact_text", lambda *a, **k: "seed-1")
    monkeypatch.setattr(plan_menu, "select_one", lambda *a, **k: "count")
    monkeypatch.setattr(plan_menu, "prompt_positive_int", lambda *a, **k: 6)
    monkeypatch.setattr(plan_menu, "confirm_write", lambda *a, **k: True)
    monkeypatch.setattr(plan_menu, "show_result", lambda *a, **k: None)
    monkeypatch.setattr(context, "load_menu_standards_library", lambda: library)

    def fake_create(
        request: object, *, standards_library: object | None = None
    ) -> object:
        forwarded.append((request, standards_library))
        return SimpleNamespace(
            mutation=SimpleNamespace(
                commit=SimpleNamespace(snapshot_revision=12),
                group_plan_id="plan-synthetic",
                status="draft",
            ),
            group_count=6,
            assigned_student_count=29,
            group_sizes=(5, 5, 5, 5, 5, 4),
        )

    monkeypatch.setattr(plan_menu, "create_random_group_plan", fake_create)
    plan_menu._create_random(current, _state())
    assert len(forwarded) == 1
    request, passed = forwarded[0]
    assert passed is library
    assert getattr(request, "expected_snapshot_revision") == 11
    assert getattr(request, "target_group_count") == 6
    assert getattr(request, "actor").actor_id == "teacher-synthetic"


def test_direct_group_menu_forwards_library_after_confirmation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current = _activity("standards_based")
    library = object()
    forwarded: list[tuple[object, object | None]] = []
    monkeypatch.setattr(group_menu, "_latest", lambda _activity: current)
    monkeypatch.setattr(group_menu, "prompt_text", lambda *a, **k: "table-six")
    monkeypatch.setattr(group_menu, "confirm_write", lambda *a, **k: True)
    monkeypatch.setattr(group_menu, "show_result", lambda *a, **k: None)
    monkeypatch.setattr(context, "load_menu_standards_library", lambda: library)

    def fake_create(
        request: object, *, standards_library: object | None = None
    ) -> object:
        forwarded.append((request, standards_library))
        return SimpleNamespace(
            group_id="table-six",
            commit=SimpleNamespace(
                no_op=False,
                snapshot_revision=12,
            ),
        )

    monkeypatch.setattr(group_menu, "create_group", fake_create)
    group_menu._create_group(current, _state())
    assert len(forwarded) == 1
    assert forwarded[0][1] is library
    assert getattr(forwarded[0][0], "expected_snapshot_revision") == 11


def test_session_menu_forwards_library_without_snapshot_change(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current = _activity("mixed")
    library = object()
    forwarded: list[tuple[object, object | None]] = []
    monkeypatch.setattr(session_menu, "_latest", lambda _activity: current)
    monkeypatch.setattr(session_menu, "list_sessions", lambda *a, **k: ())
    monkeypatch.setattr(session_menu, "prompt_text", lambda *a, **k: "session-2")
    monkeypatch.setattr(session_menu, "prompt_positive_int", lambda *a, **k: 2)
    monkeypatch.setattr(session_menu, "confirm_write", lambda *a, **k: True)
    monkeypatch.setattr(session_menu, "show_result", lambda *a, **k: None)
    monkeypatch.setattr(context, "load_menu_standards_library", lambda: library)

    def fake_create(
        request: object, *, standards_library: object | None = None
    ) -> object:
        forwarded.append((request, standards_library))
        return SimpleNamespace(
            session_id="session-2",
            commit=SimpleNamespace(
                snapshot_revision=12,
                no_op=False,
            ),
        )

    monkeypatch.setattr(session_menu, "create_session", fake_create)
    session_menu._add(current, _state())
    assert len(forwarded) == 1
    assert forwarded[0][1] is library
    assert getattr(forwarded[0][0], "expected_snapshot_revision") == 11


def test_plan_preview_forwards_same_canonical_library(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    library = object()
    captured: list[tuple[object, object | None]] = []
    detail = cast(
        GroupPlanDetail,
        SimpleNamespace(
            summary=SimpleNamespace(
                class_id="class-synthetic",
                activity_id="activity-synthetic",
                group_plan_id="plan-synthetic",
                snapshot_revision=11,
                unresolved_student_count=0,
            ),
            plan=SimpleNamespace(group_plan_id="plan-synthetic"),
        ),
    )
    monkeypatch.setattr(
        plan_menu,
        "standards_kwargs_for_plan",
        lambda _detail: {"standards_library": library},
    )
    monkeypatch.setattr(plan_menu, "confirm_write", lambda *a, **k: True)
    monkeypatch.setattr(plan_menu, "show_result", lambda *a, **k: None)

    def fake_preview(
        request: object, *, standards_library: object | None = None
    ) -> object:
        captured.append((request, standards_library))
        return SimpleNamespace(
            plan=SimpleNamespace(status="previewed"),
            summary=SimpleNamespace(snapshot_revision=12),
        )

    monkeypatch.setattr(plan_menu, "preview_group_plan", fake_preview)
    plan_menu._preview(detail, _state())
    assert len(captured) == 1
    assert captured[0][1] is library
    assert getattr(captured[0][0], "expected_snapshot_revision") == 11
