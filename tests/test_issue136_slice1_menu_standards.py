"""Issue #136 Slice 1: real teacher-menu-to-service context contract.

No live workspace/student data is used. Services are substituted only at the
write boundary so the test catches missing menu keyword arguments directly.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from pds_core.routing_models import ModuleWorkRef

import concord.menu_group_plan as plan_menu
import concord.menu_standards_context as context_menu
from concord.menu_context import MenuSessionContext
from concord.workflows import ActivitySummary, WorkflowActor, WorkflowCommitResult


def _activity(orientation: str = "mixed", snapshot: int = 11) -> ActivitySummary:
    return ActivitySummary(
        class_id="class-1",
        activity_id="activity-1",
        title="Synthetic Focus Standards Discussion",
        status="draft",
        scoring_orientation=orientation,
        session_count=1,
        group_count=0,
        snapshot_revision=snapshot,
    )


def _commit() -> WorkflowCommitResult:
    return WorkflowCommitResult(
        work=ModuleWorkRef(
            module_id="concord", class_id="class-1", work_id="activity-1"
        ),
        snapshot_revision=12,
        snapshot_sha256="a" * 64,
        changed_records=(),
        no_op=False,
    )


def _setup(monkeypatch: pytest.MonkeyPatch, current: ActivitySummary) -> None:
    monkeypatch.setattr(plan_menu, "_latest", lambda _activity: current)
    monkeypatch.setattr(
        plan_menu,
        "prompt_text",
        lambda *args, **kwargs: "activity-1-group-plan",
    )
    monkeypatch.setattr(plan_menu, "show_result", lambda *args, **kwargs: None)


@pytest.mark.parametrize(
    ("orientation", "expect_library"),
    (
        ("mixed", True),
        ("standards_based", True),
        ("evidence_only", False),
        ("local_criteria_only", False),
    ),
)
def test_manual_menu_forwards_canonical_standards_context_once(
    monkeypatch: pytest.MonkeyPatch,
    orientation: str,
    expect_library: bool,
) -> None:
    current = _activity(orientation)
    _setup(monkeypatch, current)
    marker = object()
    loaded: list[str] = []
    calls: list[tuple[object, object]] = []
    shown: list[str] = []
    monkeypatch.setattr(
        context_menu,
        "load_menu_standards_library",
        lambda: loaded.append("library") or marker,
    )
    monkeypatch.setattr(plan_menu, "confirm_write", lambda *a, **k: True)
    monkeypatch.setattr(
        plan_menu,
        "show_result",
        lambda _title, lines: shown.extend(lines),
    )

    def fake_create(request: object, *, standards_library: object = None) -> object:
        calls.append((request, standards_library))
        return SimpleNamespace(
            commit=_commit(),
            group_plan_id="activity-1-group-plan",
            status="draft",
        )

    monkeypatch.setattr(plan_menu, "create_manual_group_plan", fake_create)
    monkeypatch.setattr(
        plan_menu,
        "_handle_error",
        lambda *_args: pytest.fail("Menu must not fail for a valid request"),
    )

    plan_menu._create_manual(
        current,
        MenuSessionContext(actor=WorkflowActor(actor_id="teacher-1")),
    )
    assert len(calls) == 1
    request, passed = calls[0]
    assert getattr(request, "class_id") == "class-1"
    assert getattr(request, "activity_id") == "activity-1"
    assert getattr(request, "group_plan_id") == "activity-1-group-plan"
    assert getattr(request, "expected_snapshot_revision") == 11
    assert getattr(request, "actor").actor_id == "teacher-1"
    assert passed is (marker if expect_library else None)
    assert loaded == (["library"] if expect_library else [])
    assert "Manual GroupPlan created." in shown
    assert "Canonical Groups created: no" in shown


@pytest.mark.parametrize("orientation", ("mixed", "standards_based"))
def test_missing_core_library_blocks_write_before_mutation(
    monkeypatch: pytest.MonkeyPatch,
    orientation: str,
) -> None:
    current = _activity(orientation)
    _setup(monkeypatch, current)
    monkeypatch.setattr(plan_menu, "confirm_write", lambda *a, **k: True)
    monkeypatch.setattr(context_menu, "load_menu_standards_library", lambda: None)
    errors: list[str] = []
    monkeypatch.setattr(
        plan_menu,
        "_handle_error",
        lambda _a, _t, error: errors.append(str(error)),
    )
    monkeypatch.setattr(
        plan_menu,
        "create_manual_group_plan",
        lambda *_a, **_k: pytest.fail("No write on missing library"),
    )
    plan_menu._create_manual(
        current,
        MenuSessionContext(actor=WorkflowActor(actor_id="teacher-1")),
    )
    assert len(errors) == 1
    assert "Core Standards Library" in errors[0]
    assert "No GroupPlan was created" in errors[0]


def test_cancel_does_not_load_library_or_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current = _activity()
    _setup(monkeypatch, current)
    monkeypatch.setattr(plan_menu, "confirm_write", lambda *a, **k: False)
    monkeypatch.setattr(
        context_menu,
        "load_menu_standards_library",
        lambda: pytest.fail("Cancellation must not load Standards"),
    )
    monkeypatch.setattr(
        plan_menu,
        "create_manual_group_plan",
        lambda *_a, **_k: pytest.fail("Cancellation must not write"),
    )
    plan_menu._create_manual(
        current,
        MenuSessionContext(actor=WorkflowActor(actor_id="teacher-1")),
    )
