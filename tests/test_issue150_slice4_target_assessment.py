"""#150 Slice 4: target-only typed assessment checkpoints, zero Score reuse.

Tests use synthetic data and monkeypatched readers; no student, Score, or
workspace writes occur, and no source-class records may be inspected.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import concord.menu_guided_activity as guided
import concord.workflows.target_assessment_preflight as preflight
from concord.menu_context import MenuSessionContext
from concord.workflows.errors import ConcordWorkflowConflictError
from concord.workflows.models import ActivitySummary


def _activity(*, revision: int = 7, orientation: str = "mixed") -> ActivitySummary:
    return ActivitySummary(
        class_id="target-class",
        activity_id="target-activity",
        title="Target seminar",
        status="draft",
        scoring_orientation=orientation,
        session_count=1,
        group_count=0,
        snapshot_revision=revision,
    )


def _checkpoint(
    *,
    revision: int = 7,
    scales: tuple[str, ...] = (),
    sets: tuple[str, ...] = (),
    selected: tuple[str, ...] = (),
    scores: tuple[str, ...] = (),
    orientation: str = "mixed",
) -> preflight.TargetAssessmentCheckpoint:
    return preflight.TargetAssessmentCheckpoint(
        class_id="target-class",
        activity_id="target-activity",
        title="Target seminar",
        scoring_orientation=orientation,
        snapshot_revision=revision,
        scale_ids=scales,
        criterion_set_ids=sets,
        selected_criterion_set_ids=selected,
        score_record_ids=scores,
        criterion_count=len(sets) * 4,
    )


def _patch_reads(
    monkeypatch: pytest.MonkeyPatch, *, mismatch: str = ""
) -> list[tuple[str, str]]:
    seen: list[tuple[str, str]] = []
    root = Path("synthetic")
    monkeypatch.setattr(preflight, "resolve_read_workspace_root", lambda _root: root)
    monkeypatch.setattr(
        preflight, "require_core_class", lambda _root, cid: seen.append(("core", cid))
    )
    monkeypatch.setattr(
        preflight,
        "show_activity",
        lambda cid, aid, **_k: (
            seen.append((cid, aid)),
            SimpleNamespace(summary=_activity()),
        )[1],
    )

    def scales(cid: str, aid: str, **_kwargs: object) -> tuple[object, ...]:
        seen.append((cid, aid))
        return (
            SimpleNamespace(
                class_id="source-class" if mismatch == "class" else cid,
                activity_id=aid,
                snapshot_revision=6 if mismatch == "revision" else 7,
                scoring_scale_id="scale-target",
            ),
        )

    def criteria(cid: str, aid: str, **_kwargs: object) -> tuple[object, ...]:
        seen.append((cid, aid))
        return (
            SimpleNamespace(
                class_id=cid,
                activity_id=aid,
                snapshot_revision=7,
                criterion_set_id="set-target",
                criterion_count=4,
            ),
        )

    def scores(cid: str, aid: str, **_kwargs: object) -> tuple[object, ...]:
        seen.append((cid, aid))
        return ()

    monkeypatch.setattr(preflight, "list_scoring_scales", scales)
    monkeypatch.setattr(preflight, "list_criterion_sets", criteria)
    monkeypatch.setattr(preflight, "list_scores", scores)
    monkeypatch.setattr(
        preflight,
        "read_activity_criterion_set_selection",
        lambda cid, aid, **_k: (
            seen.append((cid, aid)),
            SimpleNamespace(snapshot_revision=7, criterion_set_ids=("set-target",)),
        )[1],
    )
    return seen


def test_reads_only_the_selected_target_and_exact_canonical_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen = _patch_reads(monkeypatch)
    result = preflight.inspect_target_assessment("target-class", "target-activity")
    assert result.scale_ids == ("scale-target",)
    assert result.criterion_set_ids == ("set-target",)
    assert result.selected_criterion_set_ids == ("set-target",)
    assert result.score_record_ids == ()
    assert seen[0] == ("core", "target-class")
    assert seen[1:] == [("target-class", "target-activity")] * 5


@pytest.mark.parametrize("mismatch", ("class", "revision"))
def test_cross_class_and_stale_reads_fail_closed(
    monkeypatch: pytest.MonkeyPatch, mismatch: str
) -> None:
    _patch_reads(monkeypatch, mismatch=mismatch)
    with pytest.raises(ConcordWorkflowConflictError):
        preflight.inspect_target_assessment("target-class", "target-activity")


def test_missing_selected_rubric_is_not_silently_accepted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_reads(monkeypatch)
    monkeypatch.setattr(
        preflight,
        "read_activity_criterion_set_selection",
        lambda *_a, **_k: SimpleNamespace(
            snapshot_revision=7, criterion_set_ids=("source-rubric",)
        ),
    )
    with pytest.raises(ConcordWorkflowConflictError, match="missing Criterion Set"):
        preflight.inspect_target_assessment("target-class", "target-activity")


def test_definition_delta_requires_unchanged_score_identities() -> None:
    before = _checkpoint()
    after = _checkpoint(
        revision=8,
        scales=("target-scale",),
        sets=("target-set",),
        selected=("target-set",),
    )
    result = preflight.verify_target_assessment_delta(before, after)
    assert (result.new_scales, result.new_criterion_sets) == (1, 1)
    assert result.selection_changed
    with pytest.raises(ConcordWorkflowConflictError, match="Score"):
        preflight.verify_target_assessment_delta(
            before, _checkpoint(revision=8, scores=("score-new",))
        )


def test_history_loss_or_cross_class_delta_is_not_a_receipt() -> None:
    before = _checkpoint(scales=("old-scale",), sets=("old-set",))
    with pytest.raises(ConcordWorkflowConflictError):
        preflight.verify_target_assessment_delta(before, _checkpoint(revision=8))
    wrong = _checkpoint(revision=8)
    wrong = preflight.TargetAssessmentCheckpoint(
        class_id="source-class",
        activity_id=wrong.activity_id,
        title=wrong.title,
        scoring_orientation=wrong.scoring_orientation,
        snapshot_revision=wrong.snapshot_revision,
        scale_ids=wrong.scale_ids,
        criterion_set_ids=wrong.criterion_set_ids,
        selected_criterion_set_ids=wrong.selected_criterion_set_ids,
        score_record_ids=wrong.score_record_ids,
        criterion_count=wrong.criterion_count,
    )
    with pytest.raises(ConcordWorkflowConflictError):
        preflight.verify_target_assessment_delta(_checkpoint(), wrong)


def test_finish_for_now_never_opens_a_scoring_writer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(guided, "clear_screen", lambda: None)
    monkeypatch.setattr(
        guided, "resolve_read_workspace_root", lambda: Path("synthetic")
    )
    monkeypatch.setattr(
        guided, "show_activity", lambda *_a, **_k: SimpleNamespace(summary=_activity())
    )
    monkeypatch.setattr(guided, "standards_for_activity", lambda *_a: None)
    monkeypatch.setattr(
        guided, "inspect_target_assessment", lambda *_a, **_k: _checkpoint()
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": "2")
    monkeypatch.setattr(
        guided,
        "launch_assessment_setup_menu",
        lambda *_a, **_k: pytest.fail("Finish must never invoke assessment writer"),
    )
    guided._launch_target_assessment(_activity(), MenuSessionContext())


def test_explicit_saved_setup_path_calls_only_no_score_menu_and_verifies_delta(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(guided, "clear_screen", lambda: None)
    monkeypatch.setattr(
        guided, "resolve_read_workspace_root", lambda: Path("synthetic")
    )
    monkeypatch.setattr(
        guided, "show_activity", lambda *_a, **_k: SimpleNamespace(summary=_activity())
    )
    monkeypatch.setattr(guided, "standards_for_activity", lambda *_a: None)
    rows = iter(
        (
            _checkpoint(),
            _checkpoint(revision=8, scales=("fresh-scale",), sets=("fresh-set",)),
        )
    )
    monkeypatch.setattr(
        guided, "inspect_target_assessment", lambda *_a, **_k: next(rows)
    )
    actions: list[object] = []
    monkeypatch.setattr(
        guided,
        "launch_assessment_setup_menu",
        lambda activity, _state: actions.append(activity),
    )
    result_lines: list[str] = []
    monkeypatch.setattr(
        guided,
        "show_result",
        lambda _title, lines: result_lines.extend(lines),
    )
    answers = iter(("1", "2"))
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    guided._launch_target_assessment(_activity(), MenuSessionContext())
    assert actions == [_activity()]
    assert any("1 fresh Scoring Scale" in line for line in result_lines)
    assert any("1 fresh Criterion Set" in line for line in result_lines)
    assert any("No Score records changed" in line for line in result_lines)


def test_changed_scores_after_owner_menu_do_not_claim_assessment_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(guided, "clear_screen", lambda: None)
    monkeypatch.setattr(
        guided, "resolve_read_workspace_root", lambda: Path("synthetic")
    )
    monkeypatch.setattr(
        guided, "show_activity", lambda *_a, **_k: SimpleNamespace(summary=_activity())
    )
    monkeypatch.setattr(guided, "standards_for_activity", lambda *_a: None)
    monkeypatch.setattr(
        guided,
        "inspect_target_assessment",
        lambda *_a, **_k: (_checkpoint(), _checkpoint(revision=8, scores=("new",)))[
            next(calls)
        ],
    )
    calls = iter((0, 1))
    monkeypatch.setattr(guided, "launch_assessment_setup_menu", lambda *_a: None)
    lines: list[str] = []
    monkeypatch.setattr(guided, "show_result", lambda _t, ls: lines.extend(ls))
    monkeypatch.setattr("builtins.input", lambda _p="": "1")
    guided._launch_target_assessment(_activity(), MenuSessionContext())
    assert any("unconfirmed" in item.lower() for item in lines)


def test_guided_setup_routes_to_configuration_not_score_capture(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called: list[object] = []
    monkeypatch.setattr(guided, "clear_screen", lambda: None)
    answers = iter(("1", "2"))
    monkeypatch.setattr("builtins.input", lambda _p="": next(answers))
    monkeypatch.setattr(
        guided,
        "launch_assessment_setup_menu",
        lambda a, state: called.append((a, state)),
    )
    state = MenuSessionContext()
    guided._launch_assessment(_activity(), state)
    assert called == [(_activity(), state)]
