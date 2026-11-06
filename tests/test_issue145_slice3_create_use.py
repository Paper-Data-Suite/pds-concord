"""#145 Slice 3: exact selected-Set preservation, verified use and partial receipts."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import concord.menu_scoring as menu
from concord.criterion_guidance import CriterionDraft, CriterionSetDraft
from concord.workflows import ActivityCriterionSetSelectionSnapshot, WorkflowActor


def _activity() -> SimpleNamespace:
    return SimpleNamespace(
        class_id="class-synthetic", activity_id="activity-synthetic",
        scoring_orientation="local_criteria_only", title="Synthetic discussion",
        snapshot_revision=7,
    )


def _snapshot(rev: int, *ids: str) -> ActivityCriterionSetSelectionSnapshot:
    return ActivityCriterionSetSelectionSnapshot(
        criterion_set_ids=tuple(ids), snapshot_revision=rev
    )


def _actor() -> WorkflowActor:
    return WorkflowActor(actor_id="synthetic-teacher")


def _draft() -> CriterionSetDraft:
    return CriterionSetDraft(
        name="Cluster discussion", purpose="Evaluate collaborative analysis",
        criterion_set_kind="local",
        criteria=(CriterionDraft(
            key="collaboration", label="Cluster analysis",
            definition="Collaborative textual analysis", criterion_kind="local",
            supported_target_kinds=("concord_group",),
        ),),
    )


def test_create_and_use_preserves_existing_exact_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    activity = _activity()
    calls: list[str] = []
    reads = iter((
        _snapshot(7, "prior-z", "prior-a"),
        _snapshot(8, "prior-z", "prior-a"),
        _snapshot(9, "prior-z", "prior-a", "new-set"),
    ))
    monkeypatch.setattr(menu, "_latest", lambda _: activity)
    monkeypatch.setattr(menu, "show_activity", lambda *_: SimpleNamespace(
        standards_profile_id=None, focus_standard_ids=()
    ))
    monkeypatch.setattr(menu, "_library", lambda: None)
    monkeypatch.setattr(
        menu, "guide_native_criterion_set", lambda **_: (_draft(), ())
    )
    monkeypatch.setattr(menu, "uuid4", lambda: SimpleNamespace(hex="new"))
    monkeypatch.setattr(
        menu,
        "read_activity_criterion_set_selection",
        lambda *a, **k: next(reads),
    )
    previews: list[tuple[str, tuple[str, ...]]] = []

    def approve(title: str, code: str, lines: tuple[str, ...]) -> bool:
        calls.append("approve")
        previews.append((code, tuple(lines)))
        assert "CREATE & USE" == code
        assert "Existing selected Sets" in " ".join(lines)
        return True

    monkeypatch.setattr(menu, "confirm_write", approve)

    def create(req, **kwargs):
        calls.append("create")
        assert req.expected_snapshot_revision == 7
        return SimpleNamespace(
            criterion_set_id="new-set", commit=SimpleNamespace(snapshot_revision=8)
        )

    def select(req, **kwargs):
        calls.append("select")
        assert req.criterion_set_ids == ("prior-z", "prior-a", "new-set")
        assert req.expected_snapshot_revision == 8
        assert req.actor.actor_id == "synthetic-teacher"
        return SimpleNamespace(commit=SimpleNamespace(snapshot_revision=9))

    monkeypatch.setattr(menu, "create_criterion_set", create)
    monkeypatch.setattr(menu, "select_activity_criterion_sets", select)
    notices: list[tuple[str, tuple[str, ...]]] = []
    monkeypatch.setattr(menu, "show_result", lambda title, lines: notices.append(
        (title, tuple(lines))))
    monkeypatch.setattr(
        menu,
        "_handle_error",
        lambda *_: pytest.fail("unexpected error"),
    )
    state = SimpleNamespace(require_actor=_actor)
    menu._create_and_use_guided_criterion_set(activity, state)
    assert calls == ["approve", "create", "select"]
    assert notices[0][0] == "Rubric Created and Selected"
    assert "Existing selected Sets preserved: 2" in notices[0][1]


def test_failure_after_create_is_not_automatically_retried(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current = _activity()
    replies = iter((_snapshot(8, "prior"), _snapshot(8, "prior")))
    monkeypatch.setattr(
        menu,
        "read_activity_criterion_set_selection",
        lambda *a, **k: next(replies),
    )
    monkeypatch.setattr(menu, "_library", lambda: None)
    hits = []

    def failing_select(*args, **kwargs):
        hits.append(True)
        raise ValueError("synthetic concurrent write")

    monkeypatch.setattr(menu, "select_activity_criterion_sets", failing_select)
    seen = []
    monkeypatch.setattr(
        menu,
        "show_result",
        lambda title, lines: seen.append((title, tuple(lines))),
    )
    menu._complete_guided_criterion_selection(
        current, _actor(), "new-set", created_snapshot=8,
        original_selection=("prior",),
    )
    assert hits == [True]
    assert seen[0][0] == "Rubric Created — Selection Requires Review"
    assert "do not repeat creation" in " ".join(seen[0][1])


def test_postcreate_drift_refuses_to_overwrite_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(menu, "_library", lambda: None)
    monkeypatch.setattr(
        menu,
        "read_activity_criterion_set_selection",
        lambda *a, **k: _snapshot(9, "other"),
    )
    monkeypatch.setattr(
        menu,
        "select_activity_criterion_sets",
        lambda *a, **k: pytest.fail("stale selection write"),
    )
    outcomes = []
    monkeypatch.setattr(menu, "show_result", lambda name, lines: outcomes.append(name))
    menu._complete_guided_criterion_selection(
        _activity(), _actor(), "new-set", created_snapshot=8,
        original_selection=("prior",),
    )
    assert outcomes == ["Rubric Created — Selection Requires Review"]


def test_service_error_after_commit_can_be_reverified(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    replies = iter((_snapshot(8), _snapshot(9, "new-set")))
    monkeypatch.setattr(menu, "_library", lambda: None)
    monkeypatch.setattr(
        menu,
        "read_activity_criterion_set_selection",
        lambda *a, **k: next(replies),
    )
    monkeypatch.setattr(
        menu,
        "select_activity_criterion_sets",
        lambda *a, **k: (_ for _ in ()).throw(ValueError("response lost")),
    )
    outcomes = []
    monkeypatch.setattr(
        menu,
        "show_result",
        lambda title, lines: outcomes.append(title),
    )
    menu._complete_guided_criterion_selection(
        _activity(), _actor(), "new-set", created_snapshot=8,
        original_selection=(),
    )
    assert outcomes == ["Rubric Created — Selection Verified After Error"]


def test_unreadable_state_is_reported_as_unknown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(menu, "_library", lambda: None)
    monkeypatch.setattr(
        menu,
        "read_activity_criterion_set_selection",
        lambda *a, **k: (_ for _ in ()).throw(ValueError("unavailable")),
    )
    outcomes = []
    monkeypatch.setattr(
        menu,
        "show_result",
        lambda title, lines: outcomes.append((title,tuple(lines))),
    )
    menu._complete_guided_criterion_selection(
        _activity(), _actor(), "new-set", created_snapshot=8,
        original_selection=(),
    )
    assert outcomes[0][0] == "Rubric Created — Selection Outcome Unknown"
    assert any("Do not create another rubric" in line for line in outcomes[0][1])


def test_menu_routes_ordinary_create_and_separate_create_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actions = iter(("1", "7", "B"))
    seen = []
    monkeypatch.setattr("builtins.input", lambda _: next(actions))
    monkeypatch.setattr(menu, "clear_screen", lambda: None)
    monkeypatch.setattr(menu, "print_menu_header", lambda _: None)
    monkeypatch.setattr(menu, "print_navigation", lambda: None)
    monkeypatch.setattr(
        menu,
        "_create_and_use_guided_criterion_set",
        lambda *a: seen.append("use"),
    )
    monkeypatch.setattr(
        menu,
        "_create_guided_criterion_set",
        lambda *a: seen.append("only"),
    )
    menu._criterion_set_menu(_activity(), SimpleNamespace())
    assert seen == ["use", "only"]


def test_readonly_selection_snapshot_preserves_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import concord.workflows.criterion_sets as svc
    graph = SimpleNamespace(activities=())
    activity = SimpleNamespace(criterion_set_ids=("z", "b", "a"))
    monkeypatch.setattr(svc, "resolve_read_workspace_root", lambda *a: "workspace")
    monkeypatch.setattr(svc, "work_ref", lambda *a: "work")
    monkeypatch.setattr(svc, "load_graph", lambda *a: (graph, 17, None))
    monkeypatch.setattr(svc, "require_activity", lambda *a: activity)
    result = svc.read_activity_criterion_set_selection("class", "activity")
    assert result.criterion_set_ids == ("z", "b", "a")
    assert result.snapshot_revision == 17


def test_cancel_before_create_use_commits_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    activity = _activity()
    monkeypatch.setattr(menu, "_latest", lambda _: activity)
    monkeypatch.setattr(menu, "show_activity", lambda *_: SimpleNamespace(
        standards_profile_id=None, focus_standard_ids=()
    ))
    monkeypatch.setattr(menu, "_library", lambda: None)
    monkeypatch.setattr(menu, "guide_native_criterion_set", lambda **_: (_draft(), ()))
    monkeypatch.setattr(
        menu,
        "read_activity_criterion_set_selection",
        lambda *a, **k: _snapshot(7),
    )
    monkeypatch.setattr(menu, "confirm_write", lambda *a, **k: False)
    monkeypatch.setattr(
        menu,
        "create_criterion_set",
        lambda *a, **k: pytest.fail("unapproved create"),
    )
    monkeypatch.setattr(
        menu,
        "select_activity_criterion_sets",
        lambda *a, **k: pytest.fail("unapproved selection"),
    )
    monkeypatch.setattr(
        menu,
        "show_result",
        lambda *a, **k: pytest.fail("unapproved receipt"),
    )
    menu._create_and_use_guided_criterion_set(
        activity, SimpleNamespace(require_actor=_actor)
    )
