from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace

import pytest

import concord.menu_activity as activity_module
from concord.menu_context import MenuSessionContext
from concord.workflows import ActivitySummary

CLEAR = "<<<CLEAR>>>"


def _inputs(monkeypatch: pytest.MonkeyPatch, values: list[str]) -> None:
    iterator: Iterator[str] = iter(values)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(iterator))


def _activity() -> ActivitySummary:
    return ActivitySummary(
        class_id="class-1",
        activity_id="activity-1",
        title="Macbeth Seminar",
        status="active",
        scoring_orientation="mixed",
        session_count=2,
        group_count=4,
        snapshot_revision=9,
    )


def _stable_activity(
    monkeypatch: pytest.MonkeyPatch,
    activity: ActivitySummary,
) -> None:
    monkeypatch.setattr(
        activity_module,
        "show_activity",
        lambda *_args, **_kwargs: SimpleNamespace(summary=activity),
    )


def _record_clear() -> None:
    print(CLEAR)


def test_open_activity_uses_six_teacher_tasks(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    activity = _activity()
    _stable_activity(monkeypatch, activity)
    _inputs(monkeypatch, ["b"])
    monkeypatch.setattr(activity_module, "clear_screen", lambda: None)

    activity_module.launch_activity_context_menu(activity)

    output = capsys.readouterr().out
    assert "Activity: Macbeth Seminar" in output
    assert "1. Plan" in output
    assert "2. Prepare" in output
    assert "3. Collect" in output
    assert "4. Review" in output
    assert "5. Score" in output
    assert "6. Share" in output
    assert "7. Advanced Activity tools" in output
    assert "Class: class-1" not in output
    assert "Status: active" not in output
    assert "View collaboration counts" not in output
    assert "Artifact Pages" not in output
    assert "Prepare / Generate Packet" not in output


def test_advanced_activity_tools_preserve_pre_issue66_exact_menu(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    activity = _activity()
    _stable_activity(monkeypatch, activity)
    _inputs(monkeypatch, ["7", "b", "b"])
    monkeypatch.setattr(activity_module, "clear_screen", lambda: None)

    activity_module.launch_activity_context_menu(activity)

    output = capsys.readouterr().out
    assert "Advanced Activity Tools" in output
    assert "1. View Activity summary" in output
    assert "2. View collaboration counts" in output
    assert "3. Sessions" in output
    assert "4. Groups and participants" in output
    assert "5. Roles" in output
    assert "6. Responsibilities" in output
    assert "7. Artifact Pages" in output
    assert "8. Scoring" in output
    assert "9. Publication" in output
    assert "10. Edit Activity" in output
    assert "11. Prepare / Generate Packet" in output
    assert "12. Continue Classroom Setup" in output


def test_plan_starts_with_existing_guided_setup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    activity = _activity()
    _stable_activity(monkeypatch, activity)
    calls: list[tuple[str, str]] = []
    monkeypatch.setattr(
        activity_module,
        "launch_guided_setup_for_activity",
        lambda selected, _state: calls.append(
            (selected.class_id, selected.activity_id)
        ),
    )
    _inputs(monkeypatch, ["1", "1", "b", "b"])
    monkeypatch.setattr(activity_module, "clear_screen", lambda: None)

    activity_module.launch_activity_context_menu(activity)

    assert calls == [("class-1", "activity-1")]


@pytest.mark.parametrize(
    ("task_choice", "target_name"),
    (
        ("2", "launch_classroom_materials_menu"),
        ("3", "launch_collect_work_menu"),
        ("4", "launch_review_work_menu"),
        ("5", "launch_score_menu"),
        ("6", "launch_share_results_menu"),
    ),
)
def test_initial_task_submenus_keep_existing_workflows_reachable(
    monkeypatch: pytest.MonkeyPatch,
    task_choice: str,
    target_name: str,
) -> None:
    activity = _activity()
    _stable_activity(monkeypatch, activity)
    calls: list[str] = []
    monkeypatch.setattr(
        activity_module,
        target_name,
        lambda selected, _state: calls.append(selected.activity_id),
    )
    _inputs(monkeypatch, [task_choice, "1", "b", "b"])
    monkeypatch.setattr(activity_module, "clear_screen", lambda: None)

    activity_module.launch_activity_context_menu(activity)

    assert calls == ["activity-1"]


def test_task_transition_redraws_only_current_action(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    activity = _activity()
    _stable_activity(monkeypatch, activity)
    _inputs(monkeypatch, ["1", "b", "b"])
    monkeypatch.setattr(activity_module, "clear_screen", _record_clear)

    activity_module.launch_activity_context_menu(activity)

    screens = [
        screen for screen in capsys.readouterr().out.split(CLEAR) if screen.strip()
    ]
    plan_screens = [
        screen
        for screen in screens
        if "1. Continue classroom setup" in screen
    ]
    assert len(plan_screens) == 1
    assert "Activity: Macbeth Seminar" in plan_screens[0]
    assert "2. Prepare" not in plan_screens[0]
    assert "6. Share" not in plan_screens[0]

def test_plan_exposes_classroom_planning_tasks_without_score_recording(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    activity = _activity()
    _stable_activity(monkeypatch, activity)
    _inputs(monkeypatch, ["1", "b", "b"])
    monkeypatch.setattr(activity_module, "clear_screen", lambda: None)

    activity_module.launch_activity_context_menu(activity)

    output = capsys.readouterr().out
    assert "1. Continue classroom setup" in output
    assert "2. Sessions" in output
    assert "3. Student groups" in output
    assert "4. Roles and responsibilities" in output
    assert "5. Assessment setup" in output
    assert "6. Edit Activity" in output
    assert "Record a Score" not in output


@pytest.mark.parametrize(
    ("choice", "target_name"),
    (
        ("2", "launch_session_menu"),
        ("3", "launch_group_menu"),
        ("5", "launch_assessment_setup_menu"),
    ),
)
def test_plan_routes_existing_services(
    monkeypatch: pytest.MonkeyPatch,
    choice: str,
    target_name: str,
) -> None:
    activity = _activity()
    _stable_activity(monkeypatch, activity)
    calls: list[str] = []
    monkeypatch.setattr(
        activity_module,
        target_name,
        lambda selected, _state: calls.append(selected.activity_id),
    )
    _inputs(monkeypatch, ["1", choice, "b", "b"])
    monkeypatch.setattr(activity_module, "clear_screen", lambda: None)

    activity_module.launch_activity_context_menu(activity)

    assert calls == ["activity-1"]


def test_plan_combines_roles_and_responsibilities_in_teacher_language(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    activity = _activity()
    _stable_activity(monkeypatch, activity)
    role_calls: list[str] = []
    responsibility_calls: list[str] = []
    monkeypatch.setattr(
        activity_module,
        "launch_role_menu",
        lambda selected, _state: role_calls.append(selected.activity_id),
    )
    monkeypatch.setattr(
        activity_module,
        "launch_responsibility_menu",
        lambda selected, _state: responsibility_calls.append(
            selected.activity_id
        ),
    )
    _inputs(monkeypatch, ["1", "4", "1", "2", "b", "b", "b"])
    monkeypatch.setattr(activity_module, "clear_screen", lambda: None)

    activity_module.launch_activity_context_menu(activity)

    output = capsys.readouterr().out
    assert "Who has which role?" in output
    assert "What does each person need to do?" in output
    assert role_calls == ["activity-1"]
    assert responsibility_calls == ["activity-1"]


def test_assessment_setup_contains_configuration_only(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    import concord.menu_scoring as scoring_module

    activity = _activity()
    monkeypatch.setattr(scoring_module, "_latest", lambda _activity: activity)
    _inputs(monkeypatch, ["b"])
    monkeypatch.setattr(scoring_module, "clear_screen", lambda: None)

    scoring_module.launch_assessment_setup_menu(activity)

    output = capsys.readouterr().out
    assert "Assessment Setup" in output
    assert "1. Use saved assessment setup" in output
    assert "2. Criteria" in output
    assert "3. Scoring scales" in output
    assert "Record a Score" not in output
    assert "Browse current Scores" not in output
    assert "Revise a Score" not in output

def test_prepare_exposes_low_density_material_tasks(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    activity = _activity()
    _stable_activity(monkeypatch, activity)
    _inputs(monkeypatch, ["2", "b", "b"])
    monkeypatch.setattr(activity_module, "clear_screen", lambda: None)

    activity_module.launch_activity_context_menu(activity)

    output = capsys.readouterr().out
    assert "1. Prepare classroom materials" in output
    assert "2. View prepared materials" in output
    assert "3. Manage saved materials" in output
    assert "Packet Instances" not in output
    assert "Artifact Pages" not in output
    assert "Review digest" not in output
    assert "Routes" not in output


@pytest.mark.parametrize(
    ("choice", "target_name"),
    (
        ("1", "launch_classroom_materials_menu"),
        ("2", "show_prepared_materials"),
    ),
)
def test_prepare_routes_activity_material_actions(
    monkeypatch: pytest.MonkeyPatch,
    choice: str,
    target_name: str,
) -> None:
    activity = _activity()
    _stable_activity(monkeypatch, activity)
    calls: list[str] = []
    monkeypatch.setattr(
        activity_module,
        target_name,
        lambda selected, *_args: calls.append(selected.activity_id),
    )
    _inputs(monkeypatch, ["2", choice, "b", "b"])
    monkeypatch.setattr(activity_module, "clear_screen", lambda: None)

    activity_module.launch_activity_context_menu(activity)

    assert calls == ["activity-1"]


def test_prepare_routes_saved_material_management(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    activity = _activity()
    _stable_activity(monkeypatch, activity)
    calls: list[object] = []
    monkeypatch.setattr(
        activity_module,
        "launch_manage_saved_materials_menu",
        lambda state: calls.append(state),
    )
    _inputs(monkeypatch, ["2", "3", "b", "b"])
    monkeypatch.setattr(activity_module, "clear_screen", lambda: None)

    activity_module.launch_activity_context_menu(activity)

    assert len(calls) == 1


def test_prepared_materials_summary_hides_instance_and_storage_internals(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import concord.menu_packet_generation as packet_generation

    activity = _activity()
    captured: list[tuple[str, tuple[str, ...]]] = []
    items = (
        SimpleNamespace(
            generation_status="generated",
            output_relative_path="generated/class-1/activity-1/student-a.pdf",
            packet_instance_id="packet-instance-secret",
            generation_id="generation-secret",
            target_key="participant:student-secret",
            output_sha256="hash-secret",
        ),
        SimpleNamespace(
            generation_status="routes_pending",
            output_relative_path=None,
            packet_instance_id="packet-instance-secret-2",
            generation_id="generation-secret-2",
            target_key="group:group-secret",
            output_sha256=None,
        ),
    )
    monkeypatch.setattr(
        packet_generation,
        "list_packet_instances",
        lambda _class_id, _activity_id: items,
    )
    monkeypatch.setattr(
        packet_generation,
        "show_result",
        lambda title, lines: captured.append((title, tuple(lines))),
    )

    packet_generation.show_prepared_materials(activity)

    assert len(captured) == 1
    title, lines = captured[0]
    rendered = "\\n".join(lines)
    assert title == "Prepared Materials"
    assert "Prepared sets: 2" in rendered
    assert "Ready to print: 1" in rendered
    assert "Need attention: 1" in rendered
    assert "student-a.pdf" in rendered
    assert "packet-instance-secret" not in rendered
    assert "generation-secret" not in rendered
    assert "student-secret" not in rendered
    assert "group-secret" not in rendered
    assert "hash-secret" not in rendered
    assert "generated/class-1/activity-1" not in rendered


def test_prepared_materials_summary_is_read_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import concord.menu_packet_generation as packet_generation

    activity = _activity()
    monkeypatch.setattr(
        packet_generation,
        "list_packet_instances",
        lambda _class_id, _activity_id: (),
    )
    monkeypatch.setattr(packet_generation, "show_result", lambda *_args: None)
    monkeypatch.setattr(
        packet_generation,
        "commit_packet_instantiation",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("read-only summary must not commit")
        ),
    )
    monkeypatch.setattr(
        packet_generation,
        "render_packet_instance",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("read-only summary must not render")
        ),
    )

    packet_generation.show_prepared_materials(activity)

def test_collect_screen_separates_returned_work_from_review(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    import concord.menu_artifact as artifact_module

    activity = _activity()
    _inputs(monkeypatch, ["b"])
    monkeypatch.setattr(artifact_module, "clear_screen", lambda: None)

    artifact_module.launch_collect_work_menu(activity, MenuSessionContext())

    output = capsys.readouterr().out
    assert "1. View returned work" in output
    assert "2. Assemble returned work" in output
    assert "3. Confirm who produced the work" in output
    assert "4. Confirm who or what the work is about" in output
    assert "Prepare Artifact Pages" not in output
    assert "Render prepared pages" not in output
    assert "Moderation" not in output
    assert "Record Review" not in output


@pytest.mark.parametrize(
    ("choice", "target_name"),
    (
        ("1", "_list_artifacts"),
        ("2", "_assemble"),
        ("3", "_launch_author_menu"),
        ("4", "_launch_subject_menu"),
    ),
)
def test_collect_routes_existing_artifact_services(
    monkeypatch: pytest.MonkeyPatch,
    choice: str,
    target_name: str,
) -> None:
    import concord.menu_artifact as artifact_module

    activity = _activity()
    calls: list[str] = []
    monkeypatch.setattr(
        artifact_module,
        target_name,
        lambda selected, *_args: calls.append(selected.activity_id),
    )
    _inputs(monkeypatch, [choice, "b"])
    monkeypatch.setattr(artifact_module, "clear_screen", lambda: None)

    artifact_module.launch_collect_work_menu(activity, MenuSessionContext())

    assert calls == ["activity-1"]


def test_review_screen_separates_review_and_moderation_from_collection(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    import concord.menu_artifact as artifact_module

    activity = _activity()
    _inputs(monkeypatch, ["b"])
    monkeypatch.setattr(artifact_module, "clear_screen", lambda: None)

    artifact_module.launch_review_work_menu(activity, MenuSessionContext())

    output = capsys.readouterr().out
    assert "1. Review collected work" in output
    assert "2. Moderation" in output
    assert "Assemble returned work" not in output
    assert "Confirm who produced the work" not in output
    assert "Confirm who or what the work is about" not in output
    assert "Record a Score" not in output


@pytest.mark.parametrize(
    ("choice", "target_name"),
    (
        ("1", "_launch_review_menu"),
        ("2", "_launch_moderation_menu"),
    ),
)
def test_review_routes_existing_review_services(
    monkeypatch: pytest.MonkeyPatch,
    choice: str,
    target_name: str,
) -> None:
    import concord.menu_artifact as artifact_module

    activity = _activity()
    calls: list[str] = []
    monkeypatch.setattr(
        artifact_module,
        target_name,
        lambda selected, *_args: calls.append(selected.activity_id),
    )
    _inputs(monkeypatch, [choice, "b"])
    monkeypatch.setattr(artifact_module, "clear_screen", lambda: None)

    artifact_module.launch_review_work_menu(activity, MenuSessionContext())

    assert calls == ["activity-1"]


@pytest.mark.parametrize(
    "menu_name",
    ("launch_collect_work_menu", "launch_review_work_menu"),
)
def test_collect_and_review_navigation_alone_do_not_write(
    monkeypatch: pytest.MonkeyPatch,
    menu_name: str,
) -> None:
    import concord.menu_artifact as artifact_module

    activity = _activity()

    def unexpected(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("navigation alone must not run a workflow action")

    for name in (
        "_list_artifacts",
        "_assemble",
        "_launch_author_menu",
        "_launch_subject_menu",
        "_launch_review_menu",
        "_launch_moderation_menu",
    ):
        monkeypatch.setattr(artifact_module, name, unexpected)

    _inputs(monkeypatch, ["b"])
    monkeypatch.setattr(artifact_module, "clear_screen", lambda: None)

    menu = getattr(artifact_module, menu_name)
    menu(activity, MenuSessionContext())

def test_score_screen_contains_judgment_actions_only(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    import concord.menu_scoring as scoring_module

    activity = _activity()
    monkeypatch.setattr(scoring_module, "_latest", lambda _activity: activity)
    _inputs(monkeypatch, ["b"])
    monkeypatch.setattr(scoring_module, "clear_screen", lambda: None)

    scoring_module.launch_score_menu(activity)

    output = capsys.readouterr().out
    assert "1. Record a Score" in output
    assert "2. View Scores" in output
    assert "3. Revise a Score" in output
    assert "Criterion Sets" not in output
    assert "Scoring Scales" not in output
    assert "Use Saved Scoring Setup" not in output
    assert "Orientation:" not in output


@pytest.mark.parametrize(
    ("choice", "target_name"),
    (
        ("1", "_record_score"),
        ("2", "_browse_scores"),
        ("3", "_revise_score"),
    ),
)
def test_score_routes_existing_score_services(
    monkeypatch: pytest.MonkeyPatch,
    choice: str,
    target_name: str,
) -> None:
    import concord.menu_scoring as scoring_module

    activity = _activity()
    calls: list[str] = []
    monkeypatch.setattr(scoring_module, "_latest", lambda _activity: activity)
    monkeypatch.setattr(
        scoring_module,
        target_name,
        lambda selected, *_args: calls.append(selected.activity_id),
    )
    _inputs(monkeypatch, [choice, "b"])
    monkeypatch.setattr(scoring_module, "clear_screen", lambda: None)

    scoring_module.launch_score_menu(activity, MenuSessionContext())

    assert calls == ["activity-1"]


def test_score_navigation_alone_does_not_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import concord.menu_scoring as scoring_module

    activity = _activity()
    monkeypatch.setattr(scoring_module, "_latest", lambda _activity: activity)

    def unexpected(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("opening Score must not record or revise anything")

    monkeypatch.setattr(scoring_module, "_record_score", unexpected)
    monkeypatch.setattr(scoring_module, "_revise_score", unexpected)
    _inputs(monkeypatch, ["b"])
    monkeypatch.setattr(scoring_module, "clear_screen", lambda: None)

    scoring_module.launch_score_menu(activity, MenuSessionContext())

def test_share_screen_uses_teacher_language_without_publication_internals(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    import concord.menu_publication as publication_module

    activity = _activity()
    _inputs(monkeypatch, ["b"])
    monkeypatch.setattr(publication_module, "clear_screen", lambda: None)

    publication_module.launch_share_results_menu(activity, MenuSessionContext())

    output = capsys.readouterr().out
    assert "1. Set up sharing" in output
    assert "2. Review what will be shared" in output
    assert "3. Share results" in output
    assert "4. View sharing history" in output
    assert "5. Stop sharing current results" in output
    assert "Generate immutable manifest" not in output
    assert "Catalog" not in output
    assert "Publication ID" not in output
    assert "SHA-256" not in output


def test_share_preview_hides_manifest_storage_and_identity_details(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import concord.menu_publication as publication_module

    activity = _activity()
    preview = SimpleNamespace()
    registration = SimpleNamespace(
        academic_intent="summative",
        lifecycle="active",
    )
    captured: list[tuple[str, tuple[str, ...]]] = []
    monkeypatch.setattr(
        publication_module,
        "_preview",
        lambda _activity, _state: (SimpleNamespace(), preview),
    )
    monkeypatch.setattr(
        publication_module,
        "load_current_concord_academic_work_registration",
        lambda *_args, **_kwargs: registration,
    )
    monkeypatch.setattr(publication_module, "_root", lambda: Path("."))
    monkeypatch.setattr(
        publication_module,
        "manifest_preview_summary",
        lambda _preview: {
            "score_count": 8,
            "current_score_count": 6,
            "historical_score_count": 2,
            "standard_backed_score_count": 5,
            "local_score_count": 3,
            "non_score_count": 1,
            "moderation_dependent_count": 2,
            "manifest_path": "secret/path/manifest.json",
            "manifest_sha256": "secret-hash",
            "record_set_id": "secret-record-set",
        },
    )
    monkeypatch.setattr(
        publication_module,
        "show_result",
        lambda title, lines: captured.append((title, tuple(lines))),
    )

    publication_module._show_share_preview(
        activity,
        MenuSessionContext(),
    )

    assert len(captured) == 1
    title, lines = captured[0]
    rendered = "\n".join(lines)
    assert title == "Review What Will Be Shared"
    assert "Scores included: 8" in rendered
    assert "Current / historical Scores: 6 / 2" in rendered
    assert "secret/path" not in rendered
    assert "secret-hash" not in rendered
    assert "secret-record-set" not in rendered


@pytest.mark.parametrize(
    ("has_head", "expected_superseding"),
    ((False, False), (True, True)),
)
def test_share_results_hides_first_vs_superseding_decision(
    monkeypatch: pytest.MonkeyPatch,
    has_head: bool,
    expected_superseding: bool,
) -> None:
    import concord.menu_publication as publication_module

    activity = _activity()
    calls: list[tuple[bool, bool]] = []
    state = SimpleNamespace(
        core_head=(SimpleNamespace(publication_id="pub-1") if has_head else None)
    )
    monkeypatch.setattr(publication_module, "_root", lambda: Path("."))
    monkeypatch.setattr(
        publication_module,
        "load_concord_publication_series_status",
        lambda *_args, **_kwargs: state,
    )
    monkeypatch.setattr(
        publication_module,
        "_publish",
        lambda _activity, _session, *, superseding, teacher_facing=False: (
            calls.append((superseding, teacher_facing))
        ),
    )

    publication_module._share_results(activity, MenuSessionContext())

    assert calls == [(expected_superseding, True)]


def test_share_navigation_alone_does_not_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import concord.menu_publication as publication_module

    activity = _activity()

    def unexpected(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("opening Share must not mutate publication state")

    for name in (
        "register_concord_academic_work",
        "update_academic_work_registration",
        "generate_academic_result_manifest",
        "publish_concord_academic_results",
        "supersede_concord_academic_results",
        "republish_concord_academic_results_after_withdrawal",
        "withdraw_concord_academic_result_publication",
        "rebuild_full_academic_catalog",
    ):
        monkeypatch.setattr(publication_module, name, unexpected)

    _inputs(monkeypatch, ["b"])
    monkeypatch.setattr(publication_module, "clear_screen", lambda: None)

    publication_module.launch_share_results_menu(activity, MenuSessionContext())

