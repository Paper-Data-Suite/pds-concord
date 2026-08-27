from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import concord.menu_activity as menu_activity
import concord.menu_guided_activity as guided_menu
import concord.workflows.guided_activity_setup as guided_workflow
import concord.workflows.packet as packet_workflow
from concord.menu_context import MenuSessionContext
from concord.packet_storage import PacketStorageNotFoundError
from concord.workflows import ActivitySummary, ClassSummary, WorkflowActor

CLEAR = "<<<CLEAR>>>"


def _activity(*, scoring: str = "mixed") -> ActivitySummary:
    return ActivitySummary(
        class_id="class-1",
        activity_id="activity-1",
        title="Seminar",
        status="draft",
        scoring_orientation=scoring,
        session_count=1,
        group_count=0,
        snapshot_revision=1,
    )


def _detail(*, scoring: str = "mixed") -> SimpleNamespace:
    return SimpleNamespace(
        summary=_activity(scoring=scoring),
        activity_type="socratic_seminar",
    )


def _patch_setup_reads(
    monkeypatch: pytest.MonkeyPatch,
    *,
    scoring: str = "mixed",
    sessions: tuple[object, ...] = (object(),),
    groups: tuple[object, ...] = (),
    group_plans: tuple[object, ...] = (),
    roles: tuple[object, ...] = (),
    responsibilities: tuple[object, ...] = (),
    packets: tuple[object, ...] = (),
    criteria: tuple[object, ...] = (),
) -> None:
    monkeypatch.setattr(
        guided_workflow,
        "show_activity",
        lambda *_a, **_k: _detail(scoring=scoring),
    )
    monkeypatch.setattr(guided_workflow, "list_sessions", lambda *_a, **_k: sessions)
    monkeypatch.setattr(guided_workflow, "list_groups", lambda *_a, **_k: groups)
    monkeypatch.setattr(
        guided_workflow,
        "list_group_plans",
        lambda *_a, **_k: group_plans,
    )
    monkeypatch.setattr(guided_workflow, "list_roles", lambda *_a, **_k: roles)
    monkeypatch.setattr(
        guided_workflow,
        "list_responsibilities",
        lambda *_a, **_k: responsibilities,
    )
    monkeypatch.setattr(
        guided_workflow,
        "list_packet_instances",
        lambda *_a, **_k: packets,
    )
    monkeypatch.setattr(
        guided_workflow,
        "list_criterion_sets",
        lambda *_a, **_k: criteria,
    )


def test_setup_status_is_derived_from_canonical_records(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = SimpleNamespace(is_selected=True)
    _patch_setup_reads(
        monkeypatch,
        groups=(object(), object()),
        roles=(object(),),
        packets=(object(),),
        criteria=(selected,),
    )
    result = guided_workflow.inspect_guided_activity_setup("class-1", "activity-1")
    assert result.area("activity").status == "ready"
    assert result.area("session").status == "ready"
    assert result.area("materials").status == "ready"
    assert result.area("groups").status == "ready"
    assert result.area("assignments").status == "ready"
    assert result.area("assessment").status == "ready"


def test_evidence_only_activity_marks_assessment_not_used(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_setup_reads(monkeypatch, scoring="evidence_only")
    result = guided_workflow.inspect_guided_activity_setup("class-1", "activity-1")
    assert result.area("assessment").status == "not_used"
    assert "without Scores" in result.area("assessment").detail


def test_teacher_labels_do_not_expose_raw_enum_keys() -> None:
    assert (
        guided_workflow.activity_type_label("socratic_seminar")
        == "Discussion / seminar"
    )
    assert guided_workflow.scoring_orientation_label("standards_based") == (
        "Standards-based assessment"
    )
    assert "_" not in guided_workflow.activity_type_label("socratic_seminar")
    assert "_" not in guided_workflow.scoring_orientation_label("standards_based")


def test_activity_management_puts_guided_path_before_advanced_tools(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    answers = iter(["b"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    monkeypatch.setattr(menu_activity, "clear_screen", lambda: print(CLEAR))
    menu_activity.launch_activity_management_menu(MenuSessionContext())
    output = capsys.readouterr().out
    assert "1. Create Classroom Activity" in output
    assert "2. Continue setup for an Activity" in output
    assert "3. Advanced Activity tools" in output
    assert "Activity ID" not in output


def test_fresh_creation_cancel_before_confirmation_writes_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    classes = (ClassSummary(class_id="class-1", school_year="2026-2027"),)
    state = MenuSessionContext(actor=WorkflowActor(actor_id="teacher-1"))
    answers = iter(["1"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    monkeypatch.setattr(guided_menu, "_classes", lambda: classes)
    monkeypatch.setattr(guided_menu, "choose_class", lambda _items: classes[0])
    monkeypatch.setattr(
        guided_menu,
        "prompt_text",
        lambda _title, label, **_kwargs: {
            "Activity title": "Seminar",
            "Short description": None,
            "First session": "Day 1",
        }[label],
    )
    monkeypatch.setattr(
        guided_menu,
        "_choose_activity_type",
        lambda: "socratic_seminar",
    )
    monkeypatch.setattr(guided_menu, "_choose_assessment", lambda: "evidence_only")
    monkeypatch.setattr(guided_menu, "_standards_for", lambda _value: (None, None, ()))
    monkeypatch.setattr(guided_menu, "confirm_write", lambda *_a, **_k: False)
    monkeypatch.setattr(
        guided_menu,
        "create_activity_context",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("unexpected write")),
    )
    guided_menu.launch_guided_activity_menu(state)


def test_fresh_creation_generates_hidden_native_ids(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    classes = (ClassSummary(class_id="class-1", school_year="2026-2027"),)
    state = MenuSessionContext(actor=WorkflowActor(actor_id="teacher-1"))
    answers = iter(["1"])
    captured: list[object] = []
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    monkeypatch.setattr(guided_menu, "clear_screen", lambda: print(CLEAR))
    monkeypatch.setattr(guided_menu, "_classes", lambda: classes)
    monkeypatch.setattr(guided_menu, "choose_class", lambda _items: classes[0])
    monkeypatch.setattr(
        guided_menu,
        "prompt_text",
        lambda _title, label, **_kwargs: {
            "Activity title": "Seminar",
            "Short description": None,
            "First session": "Day 1",
        }[label],
    )
    monkeypatch.setattr(
        guided_menu,
        "_choose_activity_type",
        lambda: "socratic_seminar",
    )
    monkeypatch.setattr(guided_menu, "_choose_assessment", lambda: "evidence_only")
    monkeypatch.setattr(guided_menu, "_standards_for", lambda _value: (None, None, ()))
    monkeypatch.setattr(guided_menu, "confirm_write", lambda *_a, **_k: True)

    def create(request: object, **_kwargs: object) -> SimpleNamespace:
        captured.append(request)
        activity_id = getattr(request, "activity_id")
        return SimpleNamespace(activity_id=activity_id)

    monkeypatch.setattr(guided_menu, "create_activity_context", create)
    monkeypatch.setattr(
        guided_menu,
        "show_activity",
        lambda *_a, **_k: _detail(scoring="evidence_only"),
    )
    monkeypatch.setattr(guided_menu, "show_result", lambda *_a, **_k: None)
    monkeypatch.setattr(
        guided_menu,
        "_offer_after_creation",
        lambda *_a, **_k: None,
    )
    guided_menu.launch_guided_activity_menu(state)
    request = captured[0]
    assert request.activity_id.startswith("activity-")  # type: ignore[attr-defined]
    assert request.session_id.startswith("session-")  # type: ignore[attr-defined]
    output = capsys.readouterr().out
    assert "Activity ID" not in output
    assert "Session ID" not in output
    assert "snapshot" not in output.casefold()


def test_continue_setup_redraws_one_current_status_screen(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    state = MenuSessionContext(actor=WorkflowActor(actor_id="teacher-1"))
    setup = guided_workflow.GuidedActivitySetup(
        class_id="class-1",
        activity_id="activity-1",
        title="Seminar",
        areas=(
            guided_workflow.GuidedSetupArea(
                key="activity",
                label="Activity basics",
                status="ready",
                detail="Discussion / seminar",
            ),
            guided_workflow.GuidedSetupArea(
                key="session",
                label="Session",
                status="ready",
                detail="1 session available.",
            ),
            guided_workflow.GuidedSetupArea(
                key="materials",
                label="Classroom materials",
                status="not_set_up",
                detail="No classroom packet has been prepared yet.",
            ),
            guided_workflow.GuidedSetupArea(
                key="groups",
                label="Student groups",
                status="needs_attention",
                detail="A group plan is approved and ready to apply.",
            ),
            guided_workflow.GuidedSetupArea(
                key="assignments",
                label="Roles and responsibilities",
                status="not_set_up",
                detail="No assignments yet.",
            ),
            guided_workflow.GuidedSetupArea(
                key="assessment",
                label="Assessment",
                status="not_set_up",
                detail="Assessment criteria have not been selected yet.",
            ),
        ),
    )
    answers = iter(["4"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    monkeypatch.setattr(guided_menu, "clear_screen", lambda: print(CLEAR))
    monkeypatch.setattr(guided_menu, "show_activity", lambda *_a, **_k: _detail())
    monkeypatch.setattr(guided_menu, "load_menu_standards_library", lambda: None)
    monkeypatch.setattr(
        guided_menu,
        "inspect_guided_activity_setup",
        lambda *_a, **_k: setup,
    )
    guided_menu.launch_guided_setup_for_activity(_activity(), state)
    screens = [
        value for value in capsys.readouterr().out.split(CLEAR) if value.strip()
    ]
    assert len(screens) == 1
    assert "Ready: Session" in screens[0]
    assert "Needs attention: Student groups" in screens[0]
    assert "Not set up: Classroom materials" in screens[0]
    assert "Next: Student groups" in screens[0]
    assert "Continue with Student groups" in screens[0]
    assert "snapshot" not in screens[0].casefold()
    assert "revision" not in screens[0].casefold()
    assert "materializ" not in screens[0].casefold()


def test_group_plan_without_groups_is_derived_as_needs_attention(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = SimpleNamespace(status="approved")
    _patch_setup_reads(monkeypatch, group_plans=(plan,))
    result = guided_workflow.inspect_guided_activity_setup("class-1", "activity-1")
    groups = result.area("groups")
    assert groups.status == "needs_attention"
    assert groups.detail == "A group plan is approved and ready to apply."
    assert result.recommended_area() == groups


def test_recommended_area_prefers_group_attention_before_unprepared_materials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = SimpleNamespace(status="previewed")
    _patch_setup_reads(monkeypatch, group_plans=(plan,))
    result = guided_workflow.inspect_guided_activity_setup("class-1", "activity-1")
    assert result.area("materials").status == "not_set_up"
    assert result.recommended_area() is not None
    assert result.recommended_area().key == "groups"


def test_created_activity_can_finish_without_entering_more_setup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = MenuSessionContext(actor=WorkflowActor(actor_id="teacher-1"))
    activity = _activity()
    answers = iter(["2"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    monkeypatch.setattr(guided_menu, "clear_screen", lambda: None)
    monkeypatch.setattr(
        guided_menu,
        "launch_guided_setup_for_activity",
        lambda *_a, **_k: (_ for _ in ()).throw(
            AssertionError("setup should not be forced")
        ),
    )
    guided_menu._offer_after_creation(activity, state)


def test_group_choice_uses_teacher_language_and_keeps_plan_approval_explicit(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    state = MenuSessionContext(actor=WorkflowActor(actor_id="teacher-1"))
    answers = iter(["3"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    monkeypatch.setattr(guided_menu, "clear_screen", lambda: print(CLEAR))
    guided_menu._launch_groups(_activity(), state)
    output = capsys.readouterr().out
    assert "How would you like students to work?" in output
    assert "Create groups directly" in output
    assert "Make or review a group plan" in output
    assert "canonical" not in output.casefold()
    assert "groupplan" not in output.casefold()


def test_review_screen_keeps_prepare_materials_as_separate_action(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    state = MenuSessionContext(actor=WorkflowActor(actor_id="teacher-1"))
    setup = guided_workflow.GuidedActivitySetup(
        class_id="class-1",
        activity_id="activity-1",
        title="Seminar",
        areas=(
            guided_workflow.GuidedSetupArea(
                key="activity",
                label="Activity basics",
                status="ready",
                detail="Discussion / seminar",
            ),
        ),
    )
    answers = iter(["3"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    monkeypatch.setattr(guided_menu, "clear_screen", lambda: print(CLEAR))
    assert guided_menu._review_setup(setup, _activity(), state) is True
    output = capsys.readouterr().out
    assert "Prepare materials now" in output
    assert "Change a setup area" in output
    assert "Finish for now" in output
    assert "review digest" not in output.casefold()




def test_saved_packet_selection_hides_internal_packet_identities(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    packet = packet_workflow.PacketSummary(
        packet_definition_id="packet-secret-id",
        name="Seminar Materials",
        status="active",
        current_packet_version_id="version-secret-id",
        head_packet_version_id="version-secret-id",
        snapshot_revision=2,
        component_count=2,
    )
    state = MenuSessionContext(actor=WorkflowActor(actor_id="teacher-1"))
    captured_labels: list[str] = []
    generated: list[object] = []
    monkeypatch.setattr(guided_menu, "list_packets", lambda: (packet,))

    def choose(_title: str, items: object, labels: object, **_kwargs: object) -> object:
        captured_labels.extend(labels)  # type: ignore[arg-type]
        return tuple(items)[0]  # type: ignore[arg-type]

    monkeypatch.setattr(guided_menu, "select_one", choose)
    monkeypatch.setattr(
        guided_menu,
        "generate_saved_packet",
        lambda _activity, _state, selected: generated.append(selected),
    )
    guided_menu._use_saved_packet(_activity(), state)
    assert generated == [packet]
    assert captured_labels == ["Seminar Materials — 2 parts"]
    assert "packet-secret-id" not in captured_labels[0]
    assert "version-secret-id" not in captured_labels[0]


def test_packet_from_template_prepare_is_zero_write_and_exact(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    checked: list[object] = []
    monkeypatch.setattr(
        packet_workflow,
        "resolve_read_workspace_root",
        lambda _root=None: tmp_path,
    )
    monkeypatch.setattr(
        packet_workflow,
        "load_current_packet",
        lambda *_a, **_k: (_ for _ in ()).throw(
            PacketStorageNotFoundError("not found")
        ),
    )
    monkeypatch.setattr(
        packet_workflow,
        "_validate_dependencies",
        lambda _root, version, **_kwargs: checked.append(version),
    )
    monkeypatch.setattr(
        packet_workflow,
        "create_packet_library",
        lambda *_a, **_k: (_ for _ in ()).throw(
            AssertionError("prepare must not write Packet storage")
        ),
    )
    prepared = packet_workflow.prepare_packet_from_template(
        packet_workflow.PreparePacketFromTemplateRequest(
            packet_definition_id="packet-1",
            packet_version_id="packet-version-1",
            packet_component_id="component-1",
            name="Seminar Materials",
            purpose="Classroom materials",
            template_id="template-1",
            template_version_id="template-version-7",
            audience_kind="group",
            actor=WorkflowActor(actor_id="teacher-1"),
        )
    )
    assert checked == [prepared.version]
    assert prepared.definition.status == "active"
    assert prepared.version.status == "active"
    assert len(prepared.version.components) == 1
    component = prepared.version.components[0]
    assert component.template_id == "template-1"
    assert component.template_version_id == "template-version-7"
    assert component.audience_intent.audience_kind == "group"


def test_packet_from_template_commit_uses_normal_packet_storage(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    created: list[tuple[object, object]] = []
    prepared = SimpleNamespace(definition=object(), version=object())
    monkeypatch.setattr(
        packet_workflow,
        "ensure_mutating_workspace_root",
        lambda _root=None: SimpleNamespace(root=tmp_path, created=False),
    )

    def create(_root: Path, *, definition: object, initial_version: object) -> object:
        created.append((definition, initial_version))
        return object()

    sentinel = object()
    monkeypatch.setattr(packet_workflow, "create_packet_library", create)
    monkeypatch.setattr(
        packet_workflow,
        "_mutation_result",
        lambda _loaded, **_kwargs: sentinel,
    )
    result = packet_workflow.commit_packet_from_template(  # type: ignore[arg-type]
        prepared
    )
    assert result is sentinel
    assert created == [(prepared.definition, prepared.version)]


def test_materials_screen_uses_teacher_choices_not_storage_terms(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    state = MenuSessionContext(actor=WorkflowActor(actor_id="teacher-1"))
    answers = iter(["4"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    monkeypatch.setattr(guided_menu, "clear_screen", lambda: print(CLEAR))
    guided_menu._launch_materials(_activity(), state)
    output = capsys.readouterr().out
    assert "Use a saved Packet" in output
    assert "Start with a saved Template" in output
    assert "Manage saved materials" in output
    assert "packet_definition_id" not in output
    assert "template_version_id" not in output
    assert "snapshot" not in output.casefold()
