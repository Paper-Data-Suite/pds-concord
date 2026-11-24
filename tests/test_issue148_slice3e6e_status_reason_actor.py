"""#148 3E6E: nested Score StatusReason must name the reviewed recorder.

Synthetic actors, immutable reasons and mocked canonical writes only. No
classroom workspace, actual teacher profile or student record is accessed.
"""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import concord.menu_scoring as menu
from concord.menu_context import MenuSessionContext
from concord.menu_score_teacher_labels import ScoreTeacherLabels
from concord.models import StatusReason
from concord.workflows import WorkflowActor
from concord.workflows.context import actor_reference
from scripts.issue148_actor_callsite_census import inventory

ROOT = Path(__file__).resolve().parents[1]


def test_score_status_reason_is_rebound_only_at_reviewed_write_boundary() -> None:
    tree = ast.parse((ROOT / "concord/menu_scoring.py").read_text(encoding="utf-8"))
    functions = {
        node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
    }
    helper = functions["_reviewed_score_status_reason"]
    replacement = [
        node
        for node in ast.walk(helper)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "replace"
    ]
    assert len(replacement) == 1
    kw = {item.arg: item.value for item in replacement[0].keywords}
    assert "recorded_by" in kw
    value = kw["recorded_by"]
    assert isinstance(value, ast.Call)
    assert isinstance(value.func, ast.Name) and value.func.id == "actor_reference"
    assert len(value.args) == 1
    assert isinstance(value.args[0], ast.Name) and value.args[0].id == "actor"
    for function_name, request_name in (
        ("_record_score", "AddScoreRequest"),
        ("_revise_score", "ReplaceScoreRequest"),
    ):
        fn = functions[function_name]
        calls = [
            node
            for node in ast.walk(fn)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == request_name
        ]
        assert len(calls) == 1
        reason = next(kw.value for kw in calls[0].keywords if kw.arg == "status_reason")
        assert isinstance(reason, ast.Call)
        assert isinstance(reason.func, ast.Name)
        assert reason.func.id == "_reviewed_score_status_reason"
        assert len(reason.args) == 2
        assert isinstance(reason.args[1], ast.Name) and reason.args[1].id == "actor"


def test_census_has_no_unreviewed_legacy_confirmation_with_local_actor() -> None:
    scanned, rows = inventory(ROOT)
    assert scanned >= 40
    assert not [
        (item.path, item.function)
        for item in rows
        if item.classification == "legacy-confirm-with-actor"
    ]
    by_key = {(item.path, item.function): item for item in rows}
    assert by_key[("concord/menu_scoring.py", "_score_components")].classification == (
        "actor-resolved-no-local-review"
    )
    assert by_key[("concord/menu_scoring.py", "_record_score")].classification == (
        "action-reviewed"
    )
    assert by_key[("concord/menu_scoring.py", "_revise_score")].classification == (
        "action-reviewed"
    )


@pytest.mark.parametrize("operation", ("record", "revise"))
@pytest.mark.parametrize("choice", ("default", "alternate", "cancel"))
@pytest.mark.parametrize("non_score", (True, False))
def test_final_reviewed_actor_owns_status_reason_or_cancel_is_no_write(
    monkeypatch: pytest.MonkeyPatch,
    operation: str,
    choice: str,
    non_score: bool,
) -> None:
    default = WorkflowActor(actor_id="adult-default", display_label="Default Adult")
    alternate = WorkflowActor(actor_id="adult-other", display_label="Other Adult")
    state = MenuSessionContext(actor=default)
    original = (
        StatusReason(
            reason_code="absent",
            recorded_by=actor_reference(default),
            recorded_at="2026-11-14T12:34:56+00:00",
            note="Synthetic, no evidence available",
        )
        if non_score
        else None
    )
    draft = SimpleNamespace(
        target=SimpleNamespace(target_kind="core_student", target_id="student-fake"),
        criterion=SimpleNamespace(criterion_id="criterion-fake"),
        scale=SimpleNamespace(scoring_scale_id="scale-fake"),
        session_id=None,
        disposition="absent" if non_score else "scored",
        value=None if non_score else "meeting",
        basis="professional_judgment",
        links=(),
        rationale="Synthetic rationale",
        status_reason=original,
    )
    current = SimpleNamespace(
        class_id="class-fake",
        activity_id="activity-fake",
        title="Synthetic",
        snapshot_revision=7,
        scoring_orientation="local_criteria_only",
    )
    recorded: list[Any] = []
    errors: list[Exception] = []
    approved = (
        default if choice == "default" else alternate if choice == "alternate" else None
    )
    monkeypatch.setattr(menu, "_latest", lambda *_a: current)
    monkeypatch.setattr(menu, "_score_components", lambda *_a: draft)
    monkeypatch.setattr(menu, "_identifier", lambda *_a: "synthetic-id")
    monkeypatch.setattr(
        menu, "_score_confirmation_lines", lambda *_a: ("Synthetic review",)
    )
    monkeypatch.setattr(menu, "_library", lambda: None)
    monkeypatch.setattr(menu, "show_result", lambda *_a, **_k: None)
    monkeypatch.setattr(
        menu, "_handle_error", lambda _activity, exc: errors.append(exc)
    )

    def reviewed(_title: str, _expected: str, _lines: Any, **kwargs: Any) -> Any:
        assert kwargs["state"] is state
        assert kwargs["legacy_confirm"] is menu.confirm_write
        return approved

    monkeypatch.setattr(menu, "confirm_actor_write", reviewed)
    if operation == "record":
        monkeypatch.setattr(menu, "AddScoreRequest", lambda **kw: SimpleNamespace(**kw))
        monkeypatch.setattr(
            menu,
            "add_score",
            lambda request, **_kw: (
                recorded.append(request) or SimpleNamespace(score_evidence_link_ids=())
            ),
        )
        menu._record_score(current, state)
    else:
        predecessor = SimpleNamespace(
            score_record_id="prior-score",
            target_reference=SimpleNamespace(
                target_kind="core_student", target_id="student-fake"
            ),
            criterion_id="criterion-fake",
            scoring_scale_id="scale-fake",
            session_id=None,
            scored_at="2026-11-14T12:34:56+00:00",
            disposition="scored",
            value="meeting",
            is_current=True,
        )
        labels = ScoreTeacherLabels(
            targets={("core_student", "student-fake"): "Synthetic student"},
            criteria={"criterion-fake": "Synthetic criterion"},
            scales={"scale-fake": "Synthetic scale"},
        )
        monkeypatch.setattr(
            menu, "list_current_score_heads", lambda *_a, **_kw: (predecessor,)
        )
        monkeypatch.setattr(
            menu, "build_score_teacher_labels", lambda *_a, **_kw: labels
        )
        monkeypatch.setattr(menu, "select_one", lambda *_a, **_kw: predecessor)
        monkeypatch.setattr(menu, "_score_label", lambda *_a, **_kw: "Previous score")
        monkeypatch.setattr(menu, "prompt_text", lambda *_a, **_kw: "Correction reason")
        monkeypatch.setattr(
            menu, "ReplaceScoreRequest", lambda **kw: SimpleNamespace(**kw)
        )
        monkeypatch.setattr(
            menu,
            "replace_score",
            lambda request, **_kw: (
                recorded.append(request) or SimpleNamespace(score_evidence_link_ids=())
            ),
        )
        menu._revise_score(current, state)
    assert not errors, errors
    assert len(recorded) == int(approved is not None)
    if approved is not None:
        saved = recorded[0]
        assert saved.actor == approved
        if non_score:
            assert saved.status_reason is not original
            assert saved.status_reason.recorded_by == actor_reference(approved)
            assert saved.status_reason.reason_code == original.reason_code
            assert saved.status_reason.recorded_at == original.recorded_at
            assert saved.status_reason.note == original.note
            assert original.recorded_by == actor_reference(default)
        else:
            assert saved.status_reason is None
    assert state.actor is default
