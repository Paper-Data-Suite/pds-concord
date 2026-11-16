"""Concord #148 3D3A: actor-exact immutable manifest preview/write binding.

Synthetic in-memory activity/manifest objects only; no academic records are created.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from concord import menu_actor_action, menu_publication
from concord.menu_context import MenuSessionContext
from concord.teacher_attribution import TeacherAttributionIdentity
from concord.workflows import WorkflowActor

ROOT = Path(__file__).resolve().parents[1]


def _calls(node: ast.AST, name: str) -> list[ast.Call]:
    return [
        candidate
        for candidate in ast.walk(node)
        if isinstance(candidate, ast.Call)
        and isinstance(candidate.func, ast.Name)
        and candidate.func.id == name
    ]


@pytest.mark.parametrize("function_name", ["_generate", "_publish"])
def test_prepared_publication_action_uses_exact_reviewed_preview(
    function_name: str,
) -> None:
    tree = ast.parse(
        (ROOT / "concord" / "menu_publication.py").read_text(encoding="utf-8")
    )
    fn = next(
        candidate
        for candidate in tree.body
        if isinstance(candidate, ast.FunctionDef) and candidate.name == function_name
    )
    assert len(_calls(fn, "confirm_prepared_actor_write")) == 1
    assert not _calls(fn, "confirm_write")
    assert len(_calls(fn, "_preview_for_reviewed_actor")) == 1
    assert not _calls(fn, "_preview")
    assignments = [
        node
        for node in ast.walk(fn)
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Tuple)
        and [x.id for x in node.targets[0].elts if isinstance(x, ast.Name)]
        == ["request", "preview"]
        and isinstance(node.value, ast.Name)
        and node.value.id == "reviewed"
    ]
    assert len(assignments) == 1
    service_names = (
        ("generate_academic_result_manifest",)
        if function_name == "_generate"
        else (
            "publish_concord_academic_results",
            "supersede_concord_academic_results",
            "republish_concord_academic_results_after_withdrawal",
        )
    )
    for service_name in service_names:
        calls = _calls(fn, service_name)
        assert len(calls) == 1
        assert isinstance(calls[0].args[0], ast.Name)
        assert calls[0].args[0].id == "request"


def test_manifest_preview_replaces_actor_before_projection() -> None:
    tree = ast.parse(
        (ROOT / "concord" / "menu_publication.py").read_text(encoding="utf-8")
    )
    helper = next(
        item
        for item in tree.body
        if isinstance(item, ast.FunctionDef)
        and item.name == "_preview_for_reviewed_actor"
    )
    replacements = _calls(helper, "replace")
    assert len(replacements) == 1
    actor = next(k.value for k in replacements[0].keywords if k.arg == "actor")
    assert isinstance(actor, ast.Name) and actor.id == "actor"
    assert len(_calls(helper, "preview_academic_result_manifest")) == 1


@dataclass(frozen=True)
class _FakeManifestRequest:
    actor: WorkflowActor
    revision_reason: str = "initial"
    expected_snapshot_revision: int = 7


class _FakeReviewState:
    attribution_provider = object()

    def __init__(self) -> None:
        self.default = WorkflowActor(
            actor_id="adult-default", display_label="Default Adult"
        )

    def require_actor(self) -> WorkflowActor:
        return self.default

    def actor_for_action(
        self,
        *,
        action_label: str,
        alternate: TeacherAttributionIdentity | None = None,
    ) -> WorkflowActor:
        assert action_label in {
            "Generate Immutable Manifest",
            "Publish Academic Results",
            "Share Results",
        }
        return self.default if alternate is None else alternate.workflow_actor()


def _setup(
    monkeypatch: pytest.MonkeyPatch,
    actions: list[str],
    *,
    core_head: str | None = None,
) -> tuple[_FakeReviewState, list[str], list[tuple[str, str, str]]]:
    state = _FakeReviewState()
    inputs = iter(actions)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))
    monkeypatch.setattr(menu_actor_action, "clear_screen", lambda: None)
    monkeypatch.setattr(menu_actor_action, "print_menu_header", lambda _title: None)
    monkeypatch.setattr(menu_actor_action, "print_navigation", lambda: None)
    monkeypatch.setattr(
        menu_actor_action,
        "_choose_temporary_actor",
        lambda: TeacherAttributionIdentity("adult-other", "Other Adult", "temporary"),
    )
    monkeypatch.setattr(
        menu_publication,
        "_manifest_request",
        lambda *_args: _FakeManifestRequest(actor=state.default),
    )
    monkeypatch.setattr(menu_publication, "_root", lambda: Path("/unused"))
    monkeypatch.setattr(menu_publication, "load_menu_standards_library", lambda: None)
    monkeypatch.setattr(
        menu_publication,
        "load_current_concord_academic_work_registration",
        lambda *_args: SimpleNamespace(academic_intent="formative", lifecycle="active"),
    )
    projected: list[str] = []

    def projection(request: _FakeManifestRequest, **_kwargs: object) -> SimpleNamespace:
        projected.append(request.actor.actor_id)
        return SimpleNamespace(
            actor_id=request.actor.actor_id,
            manifest=SimpleNamespace(generated_at=f"instant-{request.actor.actor_id}"),
        )

    monkeypatch.setattr(
        menu_publication, "preview_academic_result_manifest", projection
    )
    monkeypatch.setattr(
        menu_publication,
        "_review_lines",
        lambda preview, **_kwargs: (f"Projected actor: {preview.actor_id}",),
    )
    monkeypatch.setattr(
        menu_publication,
        "_share_review_lines",
        lambda _activity, preview, **_kwargs: (
            f"Share projected actor: {preview.actor_id}",
        ),
    )
    monkeypatch.setattr(menu_publication, "show_result", lambda *_args: None)
    monkeypatch.setattr(
        menu_publication,
        "manifest_generation_summary",
        lambda _result: {
            "disposition": "created",
            "record_set_revision": 1,
            "manifest_path": "synthetic-manifest",
            "manifest_sha256": "0" * 64,
        },
    )
    monkeypatch.setattr(
        menu_publication,
        "load_concord_publication_series_status",
        lambda *_args, **_kwargs: SimpleNamespace(
            core_head=(
                None if core_head is None else SimpleNamespace(publication_id=core_head)
            ),
            core_head_withdrawal=None,
        ),
    )
    written: list[tuple[str, str, str]] = []

    def write(
        request: _FakeManifestRequest, *, clock: object, **_kwargs: object
    ) -> SimpleNamespace:
        assert callable(clock)
        written.append((request.actor.actor_id, request.revision_reason, clock()))
        return SimpleNamespace(
            disposition="created",
            publication=SimpleNamespace(
                publication_id="pub-synthetic", record_set_revision=1
            ),
        )

    monkeypatch.setattr(menu_publication, "generate_academic_result_manifest", write)
    monkeypatch.setattr(menu_publication, "publish_concord_academic_results", write)
    monkeypatch.setattr(menu_publication, "supersede_concord_academic_results", write)
    return state, projected, written


@pytest.mark.parametrize(
    ("actions", "expected"),
    [
        (["GENERATE"], ["adult-default"]),
        (["A", "GENERATE"], ["adult-default", "adult-other"]),
        (["A", "D", "GENERATE"], ["adult-default", "adult-other", "adult-default"]),
    ],
)
def test_generation_commits_actor_matching_fresh_review(
    actions: list[str],
    expected: list[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state, projected, written = _setup(monkeypatch, actions)
    menu_publication._generate(
        cast(object, SimpleNamespace(class_id="class-one", activity_id="work-one")),
        cast(MenuSessionContext, state),
    )
    assert projected == expected
    assert written == [(expected[-1], "initial", f"instant-{expected[-1]}")]


@pytest.mark.parametrize("actions", [[""], ["A", "B"]])
def test_cancelled_generation_does_not_write(
    actions: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    state, projected, written = _setup(monkeypatch, actions)
    menu_publication._generate(
        cast(object, SimpleNamespace(class_id="class-one", activity_id="work-one")),
        cast(MenuSessionContext, state),
    )
    assert projected
    assert written == []


@pytest.mark.parametrize("teacher_facing", [False, True])
def test_publication_and_sharing_commit_exact_reviewed_actor(
    teacher_facing: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    token = "SHARE" if teacher_facing else "PUBLISH"
    state, projected, written = _setup(monkeypatch, ["A", token])
    menu_publication._publish(
        cast(
            object,
            SimpleNamespace(
                class_id="class-one", activity_id="work-one", title="Synthetic Activity"
            ),
        ),
        cast(MenuSessionContext, state),
        superseding=False,
        teacher_facing=teacher_facing,
    )
    assert projected == ["adult-default", "adult-other"]
    assert written == [("adult-other", "initial", "instant-adult-other")]


def test_superseding_publication_keeps_selected_head_and_reviewed_actor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state, projected, written = _setup(
        monkeypatch, ["A", "PUBLISH"], core_head="head-before"
    )
    service_heads: list[str] = []

    def supersede(
        request: _FakeManifestRequest,
        *,
        expected_current_publication_id: str,
        clock: object,
        **_kwargs: object,
    ) -> SimpleNamespace:
        service_heads.append(expected_current_publication_id)
        assert callable(clock)
        written.append((request.actor.actor_id, request.revision_reason, clock()))
        return SimpleNamespace(
            disposition="created",
            publication=SimpleNamespace(
                publication_id="new-head", record_set_revision=2
            ),
        )

    monkeypatch.setattr(
        menu_publication, "supersede_concord_academic_results", supersede
    )
    menu_publication._publish(
        cast(
            object,
            SimpleNamespace(
                class_id="class-one", activity_id="work-one", title="Synthetic Activity"
            ),
        ),
        cast(MenuSessionContext, state),
        superseding=True,
    )
    assert projected == ["adult-default", "adult-other"]
    assert written == [("adult-other", "initial", "instant-adult-other")]
    assert service_heads == ["head-before"]
