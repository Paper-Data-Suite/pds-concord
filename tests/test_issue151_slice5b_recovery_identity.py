"""#151 Slice 5B: exact, private attribution labels and recoverable navigation.

Synthetic tests: no Core scanner, source evidence, academic write, or PDF open.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import concord.menu_artifact as menu
import concord.workflows.artifact_attribution_review as review_service
from concord.menu_context import MenuSessionContext
from concord.workflows.models import ActivitySummary


def _activity() -> ActivitySummary:
    return ActivitySummary(
        class_id="class-151-synthetic",
        activity_id="activity-151-synthetic",
        title="Synthetic Seminar",
        status="active",
        scoring_orientation="mixed",
        session_count=2,
        group_count=6,
        snapshot_revision=11,
    )


def _author(author_id: str) -> SimpleNamespace:
    return SimpleNamespace(
        artifact_author_id=author_id,
        reference_display_label="Student Example",
        authorship_mode="individual_author",
        attribution_status="proposed",
        represented_group_id="opaque-group-membership-42",
        disposition="candidate",
        exception_code=None,
    )


def _subject(subject_id: str) -> SimpleNamespace:
    return SimpleNamespace(
        artifact_subject_id=subject_id,
        reference_display_label="Lesson Example",
        subject_role="general_subject",
        confirmation_status="proposed",
        disposition="candidate",
        exception_code=None,
    )


def _review(
    labels: tuple[str | None, ...] = ("Team A | Session 1",),
) -> SimpleNamespace:
    groups = tuple(
        SimpleNamespace(
            artifact_instance_id=f"opaque-artifact-{index}",
            teacher_work_label=label,
            authors=(_author(f"opaque-author-{index}"),),
            subjects=(_subject(f"opaque-subject-{index}"),),
        )
        for index, label in enumerate(labels, 1)
    )
    return SimpleNamespace(
        candidate_author_ids=tuple(
            author.artifact_author_id for group in groups for author in group.authors
        ),
        candidate_subject_ids=tuple(
            subject.artifact_subject_id
            for group in groups
            for subject in group.subjects
        ),
        candidate_count=2 * len(groups),
        exception_count=0,
        confirmed_relationship_count=0,
        artifacts=groups,
    )


def _keys(monkeypatch: pytest.MonkeyPatch, *values: str) -> None:
    choices = iter(values)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(choices))
    monkeypatch.setattr(menu, "clear_screen", lambda: None)


def test_screen_uses_group_and_session_without_opaque_ids(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(menu, "clear_screen", lambda: None)
    menu._print_attribution_review(_activity(), _review())
    out = capsys.readouterr().out
    assert "Work: Team A | Session 1" in out
    assert "Represents an explicit Group" in out
    assert "R. Route or review scans" in out
    assert "T. Collection status" in out
    for secret in (
        "opaque-artifact",
        "opaque-group",
        "opaque-author",
        "opaque-subject",
    ):
        assert secret not in out


@pytest.mark.parametrize("labels", (("Same | Session 1",) * 2, (None,) * 3))
def test_same_named_work_receives_explicit_nonchronological_copy_labels(
    labels: tuple[str | None, ...],
) -> None:
    review = _review(labels)
    work_labels = menu._attribution_teacher_labels(review)
    assert len(work_labels) == len(labels)
    assert len(set(work_labels)) == len(labels)
    assert all("display order, not chronological" in label for label in work_labels)
    assert all("opaque-" not in label for label in work_labels)


def test_distinct_labels_remain_compact_and_exact() -> None:
    review = _review(("Group One | Session 1", "Group Two | Session 1"))
    assert menu._attribution_teacher_labels(review) == (
        "Group One | Session 1",
        "Group Two | Session 1",
    )
    choices = menu._attribution_proposal_choices(review)
    assert len(choices) == 4
    assert choices[0].association_id == "opaque-author-1"
    assert choices[1].association_id == "opaque-subject-1"
    assert choices[2].association_id == "opaque-author-2"
    assert choices[3].association_id == "opaque-subject-2"
    assert "Group One" in choices[0].display_label
    assert "Group Two" in choices[2].display_label
    assert all("opaque-" not in item.display_label for item in choices)


def test_duplicate_work_candidates_remain_canonically_distinct() -> None:
    choices = menu._attribution_proposal_choices(
        _review(("Group | Session 2", "Group | Session 2"))
    )
    assert "work 1 of 2" in choices[0].display_label
    assert "work 2 of 2" in choices[2].display_label
    assert choices[0].association_id != choices[2].association_id


def test_legacy_review_fixture_without_label_never_leaks_artifact_id(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    original = _review()
    legacy = SimpleNamespace(
        artifact_instance_id="opaque-secret-artifact-10",
        authors=original.artifacts[0].authors,
        subjects=original.artifacts[0].subjects,
    )
    original.artifacts = (legacy,)
    monkeypatch.setattr(menu, "clear_screen", lambda: None)
    menu._print_attribution_review(_activity(), original)
    out = capsys.readouterr().out
    assert "Work: Work requiring attribution" in out
    assert "opaque-secret-artifact" not in out


def test_routing_then_status_recovers_with_new_review_projection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = MenuSessionContext()
    reviews = []
    actions: list[str] = []

    def inspect(*_args: object) -> SimpleNamespace:
        reviews.append(len(reviews) + 1)
        return _review()

    monkeypatch.setattr(menu, "inspect_artifact_attribution_review", inspect)
    monkeypatch.setattr(menu, "_print_attribution_review", lambda *_a: None)

    def routing(session: MenuSessionContext) -> None:
        assert session is state
        actions.append("route")

    monkeypatch.setattr(menu, "launch_scan_routing_menu", routing)

    def status(activity: ActivitySummary) -> None:
        assert activity.activity_id == _activity().activity_id
        actions.append("status")

    monkeypatch.setattr(menu, "_show_collection_status", status)
    monkeypatch.setattr(
        menu,
        "batch_confirm_artifact_attribution",
        lambda *_a, **_kw: pytest.fail("no automatic confirm"),
    )
    _keys(monkeypatch, "r", "t", "b")
    menu._launch_attribution_review_menu(_activity(), state)
    assert actions == ["route", "status"]
    assert len(reviews) == 3


def test_select_s_is_not_repurposed_as_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actions: list[str] = []
    monkeypatch.setattr(
        menu, "inspect_artifact_attribution_review", lambda *_a: _review()
    )
    monkeypatch.setattr(menu, "_print_attribution_review", lambda *_a: None)
    monkeypatch.setattr(
        menu,
        "_confirm_selected_straightforward_attribution",
        lambda *_a: actions.append("select"),
    )
    monkeypatch.setattr(
        menu,
        "_show_collection_status",
        lambda *_a: pytest.fail("S means select, not status"),
    )
    _keys(monkeypatch, "s", "b")
    menu._launch_attribution_review_menu(_activity(), MenuSessionContext())
    assert actions == ["select"]


def test_back_exits_without_routing_status_or_confirmation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        menu, "inspect_artifact_attribution_review", lambda *_a: _review()
    )
    monkeypatch.setattr(menu, "_print_attribution_review", lambda *_a: None)
    monkeypatch.setattr(
        menu,
        "launch_scan_routing_menu",
        lambda *_a: pytest.fail("unexpected route"),
    )
    monkeypatch.setattr(
        menu,
        "_show_collection_status",
        lambda *_a: pytest.fail("unexpected status"),
    )
    monkeypatch.setattr(
        menu,
        "batch_confirm_artifact_attribution",
        lambda *_a, **_kw: pytest.fail("unexpected confirmation"),
    )
    _keys(monkeypatch, "b")
    menu._launch_attribution_review_menu(_activity(), MenuSessionContext())


def test_help_describes_read_only_recovery_not_confirmation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lines: list[str] = []
    monkeypatch.setattr(
        menu, "inspect_artifact_attribution_review", lambda *_a: _review()
    )
    monkeypatch.setattr(menu, "_print_attribution_review", lambda *_a: None)
    monkeypatch.setattr(menu, "show_result", lambda _t, ls: lines.extend(ls))
    _keys(monkeypatch, "h", "b")
    menu._launch_attribution_review_menu(_activity(), MenuSessionContext())
    result = " ".join(lines)
    assert "R opens Scan Routing" in result
    assert "neither action confirms attribution" in result


def test_projection_preserves_snapshot_identity_and_single_read(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: object,
) -> None:
    graph = SimpleNamespace(
        artifact_instances=(
            SimpleNamespace(
                artifact_instance_id="a1",
                activity_id="activity-151-synthetic",
                template_version_id="template-a",
                artifact_category="student_work",
                group_id="group-1",
                session_id="session-1",
            ),
        ),
        artifact_authors=(
            SimpleNamespace(
                artifact_instance_id="a1",
                artifact_author_id="author-1",
                attribution_status="proposed",
                supersedes_artifact_author_id=None,
            ),
        ),
        artifact_subjects=(),
        artifact_pages=(),
        groups=(),
        sessions=(),
    )
    calls: list[str] = []
    monkeypatch.setattr(
        review_service, "resolve_read_workspace_root", lambda _r: tmp_path
    )
    monkeypatch.setattr(review_service, "require_core_class", lambda *_a: None)
    monkeypatch.setattr(
        review_service,
        "load_activity_read_context",
        lambda *_a: (
            calls.append("load")
            or SimpleNamespace(
                graph=graph,
                snapshot_revision=22,
                snapshot_sha256="a" * 64,
            )
        ),
    )
    monkeypatch.setattr(
        review_service,
        "build_teacher_artifact_choices",
        lambda _g, **kw: (
            (
                SimpleNamespace(
                    summary=SimpleNamespace(artifact_instance_id="a1"),
                    group_label="Team A",
                    session_label="Session 2",
                ),
            )
            if kw["snapshot_revision"] == 22
            else pytest.fail("stale labels")
        ),
    )
    monkeypatch.setattr(
        review_service,
        "_author_review_item",
        lambda *_a: SimpleNamespace(
            artifact_author_id="author-1",
            disposition="candidate",
        ),
    )
    result = review_service.inspect_artifact_attribution_review(
        "class-151-synthetic", "activity-151-synthetic", workspace_root=tmp_path
    )
    assert calls == ["load"]
    assert result.artifacts[0].teacher_work_label == "Team A | Session 2"
    assert result.artifacts[0].artifact_instance_id == "a1"


def test_projection_can_handle_partial_legacy_synthetic_graph(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: object,
) -> None:
    graph = SimpleNamespace(
        artifact_instances=(
            SimpleNamespace(
                artifact_instance_id="a1",
                template_version_id="template",
                artifact_category="observation",
                group_id=None,
                session_id=None,
            ),
        ),
        artifact_authors=(
            SimpleNamespace(
                artifact_instance_id="a1",
                artifact_author_id="author-1",
                attribution_status="proposed",
                supersedes_artifact_author_id=None,
            ),
        ),
        artifact_subjects=(),
    )
    monkeypatch.setattr(
        review_service, "resolve_read_workspace_root", lambda _r: tmp_path
    )
    monkeypatch.setattr(review_service, "require_core_class", lambda *_a: None)
    monkeypatch.setattr(
        review_service,
        "load_activity_read_context",
        lambda *_a: SimpleNamespace(
            graph=graph,
            snapshot_revision=1,
            snapshot_sha256="a" * 64,
        ),
    )
    monkeypatch.setattr(
        review_service,
        "_author_review_item",
        lambda *_a: SimpleNamespace(
            artifact_author_id="author-1", disposition="candidate"
        ),
    )
    monkeypatch.setattr(
        review_service,
        "build_teacher_artifact_choices",
        lambda *_a, **_kw: pytest.fail("partial must not project"),
    )
    result = review_service.inspect_artifact_attribution_review(
        "class-151-synthetic", "activity-151-synthetic", workspace_root=tmp_path
    )
    assert result.artifacts[0].teacher_work_label is None
