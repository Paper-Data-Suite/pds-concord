from __future__ import annotations

from types import SimpleNamespace

import pytest
from pds_core.rosters import create_roster

from concord import menu_packet_generation
from concord.menu_context import MenuSessionContext
from concord.models import (
    ParticipantReference,
    SubjectReference,
    TemplateSubjectResolutionExpectation,
)
from concord.workflows.models import WorkflowActor
from concord.workflows.packet_instantiation import PacketSubjectBinding


def _roster():
    return create_roster(
        "english12-p2",
        (
            {
                "student_id": "student-1",
                "first_name": "Alex",
                "last_name": "One",
                "period": "2",
            },
            {
                "student_id": "student-2",
                "first_name": "Blair",
                "last_name": "Two",
                "period": "2",
            },
        ),
    )


def _prepared(
    expectation: TemplateSubjectResolutionExpectation,
) -> SimpleNamespace:
    target = SimpleNamespace(
        target_key="participant:student-1",
        participant_print_label="Alex O.",
        target_context=SimpleNamespace(
            participant_reference=ParticipantReference(
                participant_kind="core_student",
                participant_id="student-1",
                owning_system="core",
            ),
        ),
        artifacts=(),
    )
    return SimpleNamespace(
        request=SimpleNamespace(
            class_id="english12-p2",
            activity_id="activity-1",
        ),
        diagnostics=(
            SimpleNamespace(
                code="artifact_subject_binding_required",
                packet_component_id="component-review",
                target_key="participant:student-1",
            ),
        ),
        template_sources=(
            SimpleNamespace(
                template_version_id="template-v2",
                template_version=SimpleNamespace(
                    default_subject_expectation=expectation,
                ),
            ),
        ),
        packet_version=SimpleNamespace(
            components=(
                SimpleNamespace(
                    packet_component_id="component-review",
                    template_version_id="template-v2",
                ),
            ),
        ),
        target_plans=(target,),
    )


def test_menu_assigns_student_subject_by_name_without_inferring_pairing(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepared = _prepared(
        TemplateSubjectResolutionExpectation(
            subject_kinds=("core_student",),
            resolution_mode="explicit",
            subject_role="reviewed_subject",
            allow_target_subject_match=False,
        )
    )
    roster = _roster()
    selected_labels: list[tuple[str, ...]] = []
    selected_help: list[str] = []

    monkeypatch.setattr(
        menu_packet_generation,
        "resolve_workspace_root",
        lambda: tmp_path,
    )
    monkeypatch.setattr(
        menu_packet_generation,
        "load_class_roster",
        lambda _root, _class_id: roster,
    )
    monkeypatch.setattr(
        menu_packet_generation,
        "list_groups",
        lambda *_args, **_kwargs: (),
    )

    def choose(
        _title,
        items,
        labels,
        *,
        help_text: str,
    ):
        selected_labels.append(tuple(labels))
        selected_help.append(help_text)
        return next(item for item in items if item.student_id == "student-2")

    monkeypatch.setattr(menu_packet_generation, "select_one", choose)

    bindings = menu_packet_generation._prompt_missing_subject_bindings(prepared)

    assert bindings == (
        PacketSubjectBinding(
            packet_component_id="component-review",
            target_key="participant:student-1",
            subject_reference=SubjectReference(
                subject_kind="core_student",
                subject_id="student-2",
                owning_system="core",
            ),
        ),
    )
    assert selected_labels == [("Blair Two",)]
    assert "student-1" not in selected_labels[0]
    assert "student-2" not in selected_labels[0]
    assert "Alex O." in selected_help[0]


def test_menu_can_explicitly_choose_group_subject_without_member_inference(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepared = _prepared(
        TemplateSubjectResolutionExpectation(
            subject_kinds=("core_student", "concord_group"),
            resolution_mode="explicit",
            subject_role="reviewed_subject",
            allow_target_subject_match=False,
        )
    )
    roster = _roster()
    group = SimpleNamespace(
        group_id="group-b",
        label="Group B",
        status="active",
    )
    calls: list[tuple[str, tuple[str, ...]]] = []

    monkeypatch.setattr(
        menu_packet_generation,
        "resolve_workspace_root",
        lambda: tmp_path,
    )
    monkeypatch.setattr(
        menu_packet_generation,
        "load_class_roster",
        lambda _root, _class_id: roster,
    )
    monkeypatch.setattr(
        menu_packet_generation,
        "list_groups",
        lambda *_args, **_kwargs: (group,),
    )

    def choose(
        title,
        items,
        labels,
        *,
        help_text: str,
    ):
        _ = help_text
        calls.append((title, tuple(labels)))
        if title == "Choose Reviewed Subject Type":
            return "concord_group"
        return items[0]

    monkeypatch.setattr(menu_packet_generation, "select_one", choose)

    bindings = menu_packet_generation._prompt_missing_subject_bindings(prepared)

    assert bindings[0].subject_reference == SubjectReference(
        subject_kind="concord_group",
        subject_id="group-b",
        owning_system="concord",
    )
    assert calls == [
        ("Choose Reviewed Subject Type", ("Student", "Group")),
        ("Assign Review Subject", ("Group B [active]",)),
    ]
    assert all("group-b" not in label for _, labels in calls for label in labels)


def test_generate_reprepares_with_explicit_subject_bindings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actor = WorkflowActor(actor_id="teacher-1")
    state = MenuSessionContext(actor=actor)
    activity = SimpleNamespace(
        class_id="english12-p2",
        activity_id="activity-1",
        title="Peer Review",
    )
    packet = SimpleNamespace(packet_definition_id="packet-1")
    version = SimpleNamespace(
        packet_version_id="packet-version-1",
        components=(),
    )
    detail = SimpleNamespace(
        summary=SimpleNamespace(
            current_packet_version_id="packet-version-1",
        ),
        versions=(version,),
    )
    session = SimpleNamespace(session_id="session-1")
    initial = SimpleNamespace(ready_for_commit=False)
    final = SimpleNamespace(ready_for_commit=True)
    requests = []
    binding = PacketSubjectBinding(
        packet_component_id="component-review",
        target_key="participant:student-1",
        subject_reference=SubjectReference(
            subject_kind="core_student",
            subject_id="student-2",
            owning_system="core",
        ),
    )

    monkeypatch.setattr(menu_packet_generation, "get_packet", lambda _id: detail)
    monkeypatch.setattr(
        menu_packet_generation,
        "_choose_session",
        lambda _activity: session,
    )
    monkeypatch.setattr(
        menu_packet_generation,
        "_component_choices",
        lambda _components: (),
    )

    def prepare(request):
        requests.append(request)
        return initial if len(requests) == 1 else final

    monkeypatch.setattr(
        menu_packet_generation,
        "prepare_packet_instantiation",
        prepare,
    )
    monkeypatch.setattr(
        menu_packet_generation,
        "_prompt_missing_bindings",
        lambda _prepared: (),
    )
    monkeypatch.setattr(
        menu_packet_generation,
        "_prompt_missing_subject_bindings",
        lambda _prepared: (binding,),
    )
    monkeypatch.setattr(
        menu_packet_generation,
        "_preview_lines",
        lambda _prepared: ("review",),
    )
    monkeypatch.setattr(
        menu_packet_generation,
        "confirm_write",
        lambda *_args, **_kwargs: False,
    )

    menu_packet_generation._generate(
        activity,
        state,
        selected_packet=packet,
    )

    assert len(requests) == 2
    assert requests[0].subject_bindings == ()
    assert requests[1].subject_bindings == (binding,)


def test_preview_includes_human_readable_review_pairing() -> None:
    artifact = SimpleNamespace(
        proposed_subject_role="reviewed_subject",
        subject_print_label="Blair T.",
        authorship_mode="individual_author",
        proposed_subject_reference=SubjectReference(
            subject_kind="core_student",
            subject_id="student-2",
            owning_system="core",
        ),
        rendering_inputs=(
            SimpleNamespace(input_key="reviewee_display_label"),
        ),
    )
    prepared = SimpleNamespace(
        target_plans=(
            SimpleNamespace(
                participant_print_label="Alex O.",
                artifacts=(artifact,),
            ),
        ),
    )

    assert menu_packet_generation._relationship_preview_lines(prepared) == (
        "Reviewer: Alex O. | Reviewee: Blair T.",
    )
