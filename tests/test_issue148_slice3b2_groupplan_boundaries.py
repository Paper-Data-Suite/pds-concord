"""#148 Slice 3B2: actor-linked bulk digest and missing-signal confirmation.

Synthetic actors and disposable local profile configuration only. No student data.
"""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import concord.menu_group_plan_bulk as bulk
import concord.menu_group_plan_missing_signal as missing
from concord.menu_context import CancelMenuAction, MenuSessionContext
from concord.teacher_attribution import (
    ConcordTeacherAttributionProvider,
    ConcordTeacherAttributionStore,
    TeacherAttributionIdentity,
)
from concord.workflows import WorkflowActor
from concord.workflows.group_plan_manual import BulkPlannedGroupEditRequest

ROOT = Path(__file__).resolve().parents[1]
ALTERNATE = WorkflowActor(actor_id="adult-other", display_label="Other Adult")


def _provider_state(
    tmp_path: Path,
) -> tuple[MenuSessionContext, ConcordTeacherAttributionStore]:
    store = ConcordTeacherAttributionStore(config_directory=tmp_path)
    store.create("Default Adult", actor_id="adult-default")
    return MenuSessionContext(
        attribution_provider=ConcordTeacherAttributionProvider(store)
    ), store


def _preview(actor: WorkflowActor) -> SimpleNamespace:
    return SimpleNamespace(
        class_id="class-one",
        activity_id="activity-one",
        group_plan_id="plan-one",
        planned_group_key="cluster-one",
        original_status="draft",
        snapshot_revision=3,
        record_revision=1,
        roster_student_ids=("student-one",),
        selected_student_ids=("student-one",),
        changes=(
            SimpleNamespace(
                student_id="student-one",
                from_group_key=None,
                to_group_key="cluster-one",
            ),
        ),
        unchanged_count=0,
        unresolved_before=1,
        unresolved_after=0,
        before_sizes=(("cluster-one", 0),),
        after_sizes=(("cluster-one", 1),),
        review_digest="digest-" + actor.actor_id,
        no_op=False,
    )


def _bulk_inputs(monkeypatch: pytest.MonkeyPatch, choices: tuple[str, ...]) -> None:
    iterator = iter(choices)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(iterator))
    monkeypatch.setattr(bulk, "clear_screen", lambda: None)
    monkeypatch.setattr(bulk, "print_menu_header", lambda *_a: None)
    monkeypatch.setattr(bulk, "print_navigation", lambda **_kw: None)
    monkeypatch.setattr(bulk, "pause_for_user", lambda: None)


def _bulk_review(
    state: MenuSessionContext, monkeypatch: pytest.MonkeyPatch, choices: tuple[str, ...]
) -> tuple[Any, list[str], BulkPlannedGroupEditRequest]:
    _bulk_inputs(monkeypatch, choices)
    monkeypatch.setattr(
        bulk,
        "_choose_temporary_actor",
        lambda: TeacherAttributionIdentity("adult-other", "Other Adult", "temporary"),
    )
    names = {"student-one": "Synthetic Learner"}
    detail = SimpleNamespace(
        plan=SimpleNamespace(
            proposed_groups=(
                SimpleNamespace(planned_group_key="cluster-one", label="Cluster One"),
            ),
        ),
    )
    initial_actor = state.require_actor()
    request = BulkPlannedGroupEditRequest(
        class_id="class-one",
        activity_id="activity-one",
        group_plan_id="plan-one",
        planned_group_key="cluster-one",
        operation="place_or_move",
        student_ids=("student-one",),
        expected_snapshot_revision=3,
        expected_record_revision=1,
        actor=initial_actor,
    )
    seen: list[str] = []

    def prepare(candidate: BulkPlannedGroupEditRequest) -> SimpleNamespace:
        seen.append(candidate.actor.actor_id)
        return _preview(candidate.actor)

    result = bulk._review_batch(
        detail,
        _preview(initial_actor),
        names,
        state=state,
        request=request,
        prepare_review=prepare,
    )
    return result, seen, request


def test_bulk_alternate_reprepares_digest_before_one_confirmation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    state, store = _provider_state(tmp_path)
    reviewed, prepared, original = _bulk_review(state, monkeypatch, ("a", "SAVE BATCH"))
    assert reviewed is not None
    request, preview = reviewed
    assert request.actor == ALTERNATE
    assert original.actor.actor_id == "adult-default"
    assert preview.review_digest == "digest-adult-other"
    assert prepared == ["adult-other"]
    assert "digest-adult-other" in capsys.readouterr().out
    assert state.require_actor().actor_id == "adult-default"
    assert store.load() is not None


def test_bulk_restore_default_reprepares_digest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state, _store = _provider_state(tmp_path)
    reviewed, prepared, _request = _bulk_review(
        state, monkeypatch, ("a", "d", "SAVE BATCH")
    )
    assert reviewed is not None
    request, preview = reviewed
    assert request.actor.actor_id == "adult-default"
    assert preview.review_digest == "digest-adult-default"
    assert prepared == ["adult-other", "adult-default"]


def test_bulk_back_cancels_without_queuing_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state, _store = _provider_state(tmp_path)
    reviewed, prepared, _request = _bulk_review(state, monkeypatch, ("a", "b"))
    assert reviewed is None
    assert prepared == ["adult-other"]
    assert state.require_actor().actor_id == "adult-default"


def test_bulk_stale_profile_refused_before_returning_request(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state, store = _provider_state(tmp_path)
    _bulk_inputs(monkeypatch, ())
    data = {"count": 0}

    def change(_prompt: str = "") -> str:
        data["count"] += 1
        entry = store.load()
        assert entry is not None
        store.update_display_name(entry, "Updated Adult")
        return "SAVE BATCH"

    monkeypatch.setattr("builtins.input", change)
    names = {"student-one": "Synthetic Learner"}
    detail = SimpleNamespace(
        plan=SimpleNamespace(
            proposed_groups=(
                SimpleNamespace(planned_group_key="cluster-one", label="Cluster One"),
            ),
        )
    )
    request = BulkPlannedGroupEditRequest(
        class_id="class-one",
        activity_id="activity-one",
        group_plan_id="plan-one",
        planned_group_key="cluster-one",
        operation="place_or_move",
        student_ids=("student-one",),
        expected_snapshot_revision=3,
        expected_record_revision=1,
        actor=state.require_actor(),
    )
    with pytest.raises(CancelMenuAction, match="changed"):
        bulk._review_batch(
            detail,
            _preview(request.actor),
            names,
            state=state,
            request=request,
            prepare_review=lambda candidate: _preview(candidate.actor),
        )
    assert data["count"] == 1


@pytest.mark.parametrize("disposition", ("manual", "random", "leave_unassigned"))
def test_missing_signal_service_receives_reviewed_temporary_actor(
    monkeypatch: pytest.MonkeyPatch, disposition: str
) -> None:
    inspection = SimpleNamespace(
        detail=SimpleNamespace(
            summary=SimpleNamespace(
                class_id="synthetic-class",
                activity_id="synthetic-activity",
                group_plan_id="synthetic-plan",
                snapshot_revision=3,
            ),
            plan=SimpleNamespace(group_plan_id="synthetic-plan"),
        ),
        missing_student_ids=("student-one",),
    )
    captured: list[object] = []
    monkeypatch.setattr(
        missing, "inspect_group_plan_missing_signal", lambda *a: inspection
    )
    monkeypatch.setattr(missing, "_show_context", lambda *_a: None)
    monkeypatch.setattr(missing, "_show_random_preview", lambda *a, **kw: None)
    monkeypatch.setattr(missing, "select_one", lambda *a, **kw: disposition)
    monkeypatch.setattr(missing, "prompt_exact_text", lambda *a, **kw: "seed-one")
    monkeypatch.setattr(missing, "confirm_actor_write", lambda *a, **kw: ALTERNATE)
    monkeypatch.setattr(missing, "standards_kwargs_for_plan", lambda *_a: {})
    monkeypatch.setattr(missing, "_result_lines", lambda *_a: ())
    monkeypatch.setattr(missing, "show_result", lambda *a: None)
    monkeypatch.setattr(
        missing,
        "set_missing_signal_disposition",
        lambda item, **kw: captured.append(item) or object(),
    )
    missing.resolve_missing_signal_from_menu(inspection.detail, SimpleNamespace())
    assert len(captured) == 1
    assert captured[0].actor == ALTERNATE
    assert captured[0].disposition == disposition


@pytest.mark.parametrize("disposition", ("manual", "random", "leave_unassigned"))
def test_cancelled_missing_signal_review_never_dispatches(
    monkeypatch: pytest.MonkeyPatch, disposition: str
) -> None:
    inspection = SimpleNamespace(
        detail=SimpleNamespace(
            summary=SimpleNamespace(
                class_id="synthetic-class",
                activity_id="synthetic-activity",
                group_plan_id="synthetic-plan",
                snapshot_revision=3,
            ),
            plan=SimpleNamespace(group_plan_id="synthetic-plan"),
        ),
        missing_student_ids=("student-one",),
    )
    monkeypatch.setattr(
        missing, "inspect_group_plan_missing_signal", lambda *a: inspection
    )
    monkeypatch.setattr(missing, "_show_context", lambda *_a: None)
    monkeypatch.setattr(missing, "_show_random_preview", lambda *a, **kw: None)
    monkeypatch.setattr(missing, "select_one", lambda *a, **kw: disposition)
    monkeypatch.setattr(missing, "prompt_exact_text", lambda *a, **kw: "seed-one")
    monkeypatch.setattr(missing, "confirm_actor_write", lambda *a, **kw: None)
    monkeypatch.setattr(
        missing,
        "set_missing_signal_disposition",
        lambda *a, **kw: pytest.fail("Cancelled review dispatched a write"),
    )
    missing.resolve_missing_signal_from_menu(inspection.detail, SimpleNamespace())


def test_bulk_commit_uses_same_request_and_digest_as_review() -> None:
    path = ROOT / "concord/menu_group_plan_bulk.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    entry = next(
        x
        for x in tree.body
        if isinstance(x, ast.FunctionDef) and x.name == "launch_cluster_bulk_editor"
    )
    commit = next(
        x
        for x in ast.walk(entry)
        if isinstance(x, ast.Call)
        and isinstance(x.func, ast.Name)
        and x.func.id == "commit_bulk_planned_group_edit"
    )
    assert isinstance(commit.args[0], ast.Name)
    assert commit.args[0].id == "reviewed_request"
    digest = next(x.value for x in commit.keywords if x.arg == "review_digest")
    assert isinstance(digest, ast.Attribute) and digest.attr == "review_digest"
    assert isinstance(digest.value, ast.Name)
    assert digest.value.id == "reviewed_preview"


def test_missing_signal_uses_same_actor_for_all_three_routes() -> None:
    path = ROOT / "concord/menu_group_plan_missing_signal.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    entry = next(
        x
        for x in tree.body
        if isinstance(x, ast.FunctionDef)
        and x.name == "resolve_missing_signal_from_menu"
    )
    confirmations = [
        x
        for x in ast.walk(entry)
        if isinstance(x, ast.Call)
        and isinstance(x.func, ast.Name)
        and x.func.id == "confirm_actor_write"
    ]
    assert len(confirmations) == 3
    requests = [
        x
        for x in ast.walk(entry)
        if isinstance(x, ast.Call)
        and isinstance(x.func, ast.Name)
        and x.func.id == "SetMissingSignalDispositionRequest"
    ]
    assert len(requests) == 1
    actor = next(x.value for x in requests[0].keywords if x.arg == "actor")
    assert isinstance(actor, ast.Name) and actor.id == "actor"
