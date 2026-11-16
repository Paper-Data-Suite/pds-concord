"""#148 Slice 3D3B: prepared routine Artifact Scores use the reviewed recorder.

In-memory synthetic fixtures only; no real student or academic data.
"""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from concord import menu_artifact_scoring as menu
from concord.menu_context import MenuSessionContext
from concord.workflows import WorkflowActor

ROOT = Path(__file__).resolve().parents[1]
CASES = (
    ("_record_selected_artifact_score", "Score this work"),
    ("_record_another_criterion", "Score another Criterion"),
)


def _calls(node: ast.AST, name: str) -> list[ast.Call]:
    return [
        item
        for item in ast.walk(node)
        if isinstance(item, ast.Call)
        and isinstance(item.func, ast.Name)
        and item.func.id == name
    ]


@pytest.mark.parametrize(("function_name", "title"), CASES)
def test_exact_reviewed_actor_reaches_one_routine_score_write(
    function_name: str, title: str
) -> None:
    source = (ROOT / "concord" / "menu_artifact_scoring.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    fn = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == function_name
    )
    reviews = _calls(fn, "confirm_actor_write")
    scores = _calls(fn, "record_prepared_routine_score")
    assert len(reviews) == len(scores) == 1
    assert reviews[0].lineno < scores[0].lineno
    assert not _calls(fn, "confirm_write")
    assert not any(
        isinstance(node, ast.Attribute) and node.attr == "require_actor"
        for node in ast.walk(fn)
    )
    assert isinstance(reviews[0].args[0], ast.Constant)
    assert reviews[0].args[0].value == title
    assert isinstance(reviews[0].args[1], ast.Constant)
    assert reviews[0].args[1].value == "SCORE"
    assert {kw.arg for kw in reviews[0].keywords} == {
        "state",
        "legacy_confirm",
    }
    actor_kw = [k.value for k in scores[0].keywords if k.arg == "actor"]
    assert len(actor_kw) == 1
    assert isinstance(actor_kw[0], ast.Name)
    assert actor_kw[0].id == "actor"
    cancelled = [
        item
        for item in ast.walk(fn)
        if isinstance(item, ast.If)
        and isinstance(item.test, ast.Compare)
        and isinstance(item.test.left, ast.Name)
        and item.test.left.id == "actor"
        and len(item.test.ops) == 1
        and isinstance(item.test.ops[0], ast.Is)
        and len(item.test.comparators) == 1
        and isinstance(item.test.comparators[0], ast.Constant)
        and item.test.comparators[0].value is None
    ]
    assert len(cancelled) == 1
    assert len(cancelled[0].body) == 1
    assert isinstance(cancelled[0].body[0], ast.Return)
    assert isinstance(cancelled[0].body[0].value, ast.Constant)
    assert cancelled[0].body[0].value.value is None


@pytest.mark.parametrize("approved", [True, False])
@pytest.mark.parametrize(
    "operation", ["_record_selected_artifact_score", "_record_another_criterion"]
)
def test_scoring_review_keeps_preview_target_and_reviewer(
    monkeypatch: pytest.MonkeyPatch, approved: bool, operation: str
) -> None:
    activity = SimpleNamespace(
        class_id="class-synthetic",
        activity_id="activity-synthetic",
        title="Synthetic Activity",
        snapshot_revision=7,
    )
    default = WorkflowActor(actor_id="teacher-default", display_label="Default")
    alternate = WorkflowActor(actor_id="teacher-other", display_label="Other Adult")
    state = MenuSessionContext(actor=default)
    target = SimpleNamespace(target_kind="core_student")
    context = SimpleNamespace(
        class_id=activity.class_id,
        activity_id=activity.activity_id,
        snapshot_revision=7,
        snapshot_sha256="sha-synthetic",
        artifact=SimpleNamespace(artifact_instance_id="artifact-synthetic"),
        eligibility=SimpleNamespace(routine_scoring_eligible=True),
    )
    authority = SimpleNamespace(
        root=Path("synthetic-only"),
        active_workspace_binding=False,
        class_id=activity.class_id,
        activity_id=activity.activity_id,
        snapshot_revision=7,
        snapshot_sha256="sha-synthetic",
    )
    preview = SimpleNamespace(
        existing_current_score_ids=(),
        snapshot_revision=7,
        snapshot_sha256="sha-synthetic",
        artifact_instance_id="artifact-synthetic",
    )
    criterion = SimpleNamespace(
        criterion_id="criterion-2", criterion_kind="local", label="Craft"
    )
    scale = SimpleNamespace(scoring_scale_id="scale-1")
    selected: list[WorkflowActor] = []
    captured: list[tuple[Any, WorkflowActor]] = []
    revalidated: list[str] = []

    patch = monkeypatch.setattr
    patch(menu, "_current_activity", lambda *_args: activity)
    patch(menu, "begin_artifact_write_context", lambda *_args, **_kwargs: authority)
    patch(
        menu,
        "_refresh_score_continuation_authority",
        lambda *_args, **_kwargs: authority,
    )
    patch(menu, "inspect_artifact_routine_scoring", lambda *_args, **_kwargs: context)
    patch(menu, "_choose_target", lambda *_args: target)
    patch(menu, "_choose_criterion", lambda *_args: criterion)
    patch(menu, "_continuation_criteria", lambda *_args: (criterion,))
    patch(menu, "select_one", lambda *_args, **_kwargs: criterion)
    patch(menu, "_choose_scale", lambda *_args: scale)
    patch(menu, "_choose_level", lambda *_args: SimpleNamespace(value=3))
    patch(menu, "_choose_session", lambda *_args: None)
    patch(menu, "_choose_subject_context", lambda *_args: ())
    patch(menu, "_choose_relevance", lambda: "synthetic relevance")
    patch(
        menu,
        "RoutineScorePreparationRequest",
        lambda **kwargs: SimpleNamespace(**kwargs),
    )
    patch(
        menu,
        "ContinuedRoutineScorePreparationRequest",
        lambda **kwargs: SimpleNamespace(**kwargs),
    )
    patch(menu, "prepare_routine_score_preview", lambda *_args: preview)
    patch(menu, "prepare_next_routine_score_preview", lambda *_args: preview)
    patch(menu, "_preview_lines", lambda *_args: ("Synthetic score preview",))
    patch(menu, "show_result", lambda *_args: None)
    patch(menu, "artifact_write_kwargs", lambda *_args: {})
    patch(
        menu,
        "revalidate_artifact_write_context",
        lambda *_args, **kwargs: revalidated.append(kwargs["operation"]) or authority,
    )
    patch(
        menu,
        "confirm_write",
        lambda *_args: pytest.fail("legacy direct confirmation used"),
    )

    def reviewed(
        title: str, token: str, lines: Any, **kwargs: Any
    ) -> WorkflowActor | None:
        assert title in {"Score this work", "Score another Criterion"}
        assert token == "SCORE"
        assert lines == ("Synthetic score preview",)
        assert kwargs["state"] is state
        assert kwargs["legacy_confirm"] is menu.confirm_write
        selected.append(alternate)
        return alternate if approved else None

    patch(menu, "confirm_actor_write", reviewed)
    mutation = SimpleNamespace(commit=SimpleNamespace(snapshot_revision=8))
    patch(
        menu,
        "record_prepared_routine_score",
        lambda provided, *, actor, **_kwargs: (
            captured.append((provided, actor)) or mutation
        ),
    )
    if operation == "_record_selected_artifact_score":
        result = menu._record_selected_artifact_score(
            activity, "artifact-synthetic", state
        )
    else:
        continuation = SimpleNamespace(
            context=context,
            retained_target_reference=target,
            session_context_retained=True,
        )
        result = menu._record_another_criterion(
            activity, continuation, state, origin_context=authority
        )
    assert len(selected) == 1
    assert len(captured) == (1 if approved else 0)
    assert len(revalidated) == (1 if approved else 0)
    if approved:
        assert captured == [(preview, alternate)]
        assert result is not None and result.preview is preview
        assert result.mutation is mutation
        assert result.write_context is authority
    else:
        assert result is None
    assert state.actor == default
