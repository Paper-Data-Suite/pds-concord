"""#150 Slice 5: crash/restart, target identity and truthful copy receipts.

All identities are synthetic. No real Core roster or working files are used.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import concord.menu_guided_activity as guided
from concord.menu_context import MenuSessionContext
from concord.workflows import WorkflowActor
from concord.workflows.guided_activity_setup import GuidedActivitySetup, GuidedSetupArea
from concord.workflows.models import ActivitySummary, ClassSummary


def _activity(
    *,
    class_id: str = "target-class",
    activity_id: str = "target-new",
    revision: int = 3,
) -> ActivitySummary:
    return ActivitySummary(
        class_id=class_id,
        activity_id=activity_id,
        title="Synthetic target seminar",
        status="draft",
        scoring_orientation="mixed",
        session_count=1,
        group_count=0,
        snapshot_revision=revision,
    )


def _copy_inputs(monkeypatch: pytest.MonkeyPatch) -> list[object]:
    source = _activity(class_id="source-class", activity_id="original", revision=8)
    target = ClassSummary(class_id="target-class", school_year="2026-2027")
    monkeypatch.setattr(
        guided, "resolve_read_workspace_root", lambda: Path("synthetic")
    )
    monkeypatch.setattr(guided, "list_activities", lambda **_kwargs: (source,))
    monkeypatch.setattr(guided, "_guided_activity_choice", lambda *_a, **_k: source)
    monkeypatch.setattr(guided, "choose_class", lambda _classes: target)
    monkeypatch.setattr(
        guided, "prompt_text", lambda *_a, **kwargs: kwargs.get("default", "Day 1")
    )
    monkeypatch.setattr(guided, "_fresh_id", lambda prefix: f"target-{prefix}")
    monkeypatch.setattr(guided, "load_menu_standards_library", lambda: None)
    monkeypatch.setattr(
        guided,
        "prepare_activity_copy",
        lambda *_a, **_k: SimpleNamespace(review_digest="a" * 64),
    )
    monkeypatch.setattr(guided, "_cross_class_copy_review", lambda *_a: ("safe",))
    monkeypatch.setattr(
        guided,
        "confirm_actor_write",
        lambda *_a, **_k: WorkflowActor(actor_id="teacher"),
    )
    copies: list[object] = []
    monkeypatch.setattr(
        guided,
        "copy_activity",
        lambda request, **_kwargs: (
            copies.append(request),
            SimpleNamespace(activity_id="target-activity"),
        )[1],
    )
    return copies


def test_copy_readback_failure_requires_existing_target_inspection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    copies = _copy_inputs(monkeypatch)
    monkeypatch.setattr(
        guided,
        "show_activity",
        lambda *_a: (_ for _ in ()).throw(RuntimeError("private path")),
    )
    monkeypatch.setattr(
        guided, "_offer_after_creation", lambda *_a, **_k: pytest.fail("not verified")
    )
    outputs: list[str] = []
    monkeypatch.setattr(
        guided, "show_result", lambda title, lines: outputs.extend((title, *lines))
    )
    guided._create_from_activity(MenuSessionContext(), ())
    assert len(copies) == 1
    joined = " ".join(outputs).lower()
    assert "unconfirmed" in joined and "do not copy again" in joined
    assert "continue classroom setup" in joined
    assert "private path" not in joined


def test_copy_readback_wrong_class_never_opens_stage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    copies = _copy_inputs(monkeypatch)
    monkeypatch.setattr(
        guided,
        "show_activity",
        lambda *_a: SimpleNamespace(
            summary=_activity(class_id="source-class", activity_id="target-activity")
        ),
    )
    monkeypatch.setattr(
        guided, "_offer_after_creation", lambda *_a, **_k: pytest.fail("wrong class")
    )
    received: list[str] = []
    monkeypatch.setattr(
        guided, "show_result", lambda title, lines: received.extend((title, *lines))
    )
    guided._create_from_activity(MenuSessionContext(), ())
    assert len(copies) == 1
    assert "unconfirmed" in " ".join(received).lower()


def test_copy_commit_then_eof_does_not_restart_copy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    copies = _copy_inputs(monkeypatch)
    monkeypatch.setattr(
        guided,
        "show_activity",
        lambda *_a: SimpleNamespace(summary=_activity(activity_id="target-activity")),
    )
    monkeypatch.setattr(
        guided,
        "_offer_after_creation",
        lambda *_a, **_k: (_ for _ in ()).throw(EOFError()),
    )
    messages: list[str] = []
    monkeypatch.setattr(
        guided, "show_result", lambda title, lines: messages.extend((title, *lines))
    )
    guided._create_from_activity(MenuSessionContext(), ())
    assert len(copies) == 1
    assert "interrupted" in " ".join(messages).lower()
    assert "do not start a new copy" in " ".join(messages).lower()


def test_copy_confirmation_cancel_never_writes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _copy_inputs(monkeypatch)
    monkeypatch.setattr(guided, "confirm_actor_write", lambda *_a, **_k: None)
    monkeypatch.setattr(
        guided, "copy_activity", lambda *_a, **_k: pytest.fail("cancelled")
    )
    monkeypatch.setattr(guided, "show_activity", lambda *_a: pytest.fail("no readback"))
    guided._create_from_activity(MenuSessionContext(), ())


def test_post_copy_stage_stale_identity_blocks_owner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(guided, "clear_screen", lambda: None)
    monkeypatch.setattr("builtins.input", lambda _p="": "5")
    monkeypatch.setattr(
        guided,
        "show_activity",
        lambda *_a: SimpleNamespace(summary=_activity(class_id="other-class")),
    )
    monkeypatch.setattr(
        guided, "_launch_target_assessment", lambda *_a: pytest.fail("wrong target")
    )
    lines: list[str] = []
    monkeypatch.setattr(guided, "show_result", lambda _t, text: lines.extend(text))
    guided._offer_after_creation(_activity(), MenuSessionContext(), copied=True)
    assert any("no new stage" in line.lower() for line in lines)


def test_reopen_existing_target_does_not_invoke_copy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    chosen = _activity()
    monkeypatch.setattr(
        guided, "resolve_read_workspace_root", lambda: Path("synthetic")
    )
    monkeypatch.setattr(guided, "list_activities", lambda **_kwargs: (chosen,))
    monkeypatch.setattr(guided, "_guided_activity_choice", lambda *_a, **_k: chosen)
    monkeypatch.setattr(
        guided, "copy_activity", lambda *_a, **_k: pytest.fail("duplicate copy")
    )
    launched: list[ActivitySummary] = []
    monkeypatch.setattr(
        guided, "launch_guided_setup_for_activity", lambda a, _state: launched.append(a)
    )
    guided.launch_guided_continue_setup(MenuSessionContext())
    assert launched == [chosen]


def test_restart_rederives_after_owner_stage_without_duplicate_copy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reloaded: list[int] = []

    def read(_class: str, _activity_id: str) -> SimpleNamespace:
        revision = 3 if not reloaded else 4
        reloaded.append(revision)
        return SimpleNamespace(summary=_activity(revision=revision))

    monkeypatch.setattr(guided, "show_activity", read)
    monkeypatch.setattr(guided, "load_menu_standards_library", lambda: None)
    snapshots: list[int] = []

    def inspect(_class: str, _aid: str, **_k: object) -> GuidedActivitySetup:
        snapshots.append(reloaded[-1])
        area = GuidedSetupArea(
            key="groups",
            label="Groups",
            status="not_set_up" if len(snapshots) == 1 else "ready",
            detail="Independent target grouping",
        )
        return GuidedActivitySetup(
            class_id="target-class",
            activity_id="target-new",
            title="Synthetic",
            areas=(area,),
        )

    monkeypatch.setattr(guided, "inspect_guided_activity_setup", inspect)
    monkeypatch.setattr(guided, "clear_screen", lambda: None)
    monkeypatch.setattr(guided, "_print_setup", lambda *_a: None)
    monkeypatch.setattr(
        guided, "copy_activity", lambda *_a, **_k: pytest.fail("restart recopy")
    )
    stage: list[int] = []
    monkeypatch.setattr(
        guided,
        "_launch_setup_area",
        lambda _k, a, _state: stage.append(a.snapshot_revision),
    )
    answers = iter(("1", "3"))
    monkeypatch.setattr("builtins.input", lambda _p="": next(answers))
    guided.launch_guided_setup_for_activity(_activity(), MenuSessionContext())
    assert stage == [3]
    assert snapshots == [3, 4]


@pytest.mark.parametrize("kind", ("activity", "setup"))
def test_resume_wrong_identity_and_private_errors_are_sanitized(
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
) -> None:
    monkeypatch.setattr(
        guided,
        "show_activity",
        lambda *_a: SimpleNamespace(
            summary=(
                _activity(class_id="source-class")
                if kind == "activity"
                else _activity()
            )
        ),
    )
    monkeypatch.setattr(guided, "load_menu_standards_library", lambda: None)
    monkeypatch.setattr(
        guided,
        "inspect_guided_activity_setup",
        lambda *_a, **_k: (
            GuidedActivitySetup(
                class_id="source-class",
                activity_id="target-new",
                title="Synthetic",
                areas=(),
            )
            if kind == "setup"
            else (_ for _ in ()).throw(RuntimeError("secret/student.csv"))
        ),
    )
    monkeypatch.setattr(
        guided, "_launch_setup_area", lambda *_a: pytest.fail("wrong context")
    )
    lines: list[str] = []
    monkeypatch.setattr(
        guided, "show_result", lambda title, text: lines.extend((title, *text))
    )
    guided.launch_guided_setup_for_activity(_activity(), MenuSessionContext())
    joined = " ".join(lines).lower()
    assert "could not be verified" in joined
    assert "secret/student.csv" not in joined


def test_post_copy_finish_does_not_resolve_or_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(guided, "clear_screen", lambda: None)
    monkeypatch.setattr("builtins.input", lambda _p="": "2")
    monkeypatch.setattr(
        guided, "show_activity", lambda *_a: pytest.fail("finish reads")
    )
    monkeypatch.setattr(
        guided, "copy_activity", lambda *_a, **_k: pytest.fail("finish writes")
    )
    guided._offer_after_creation(_activity(), MenuSessionContext(), copied=True)
