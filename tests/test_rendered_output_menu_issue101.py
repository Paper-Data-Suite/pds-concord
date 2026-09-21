from __future__ import annotations

from types import SimpleNamespace

import pytest

import concord.menu_packet_generation as menu_generation
from concord.menu_context import MenuSessionContext
from concord.workflows import ActivitySummary, WorkflowActor


def _activity() -> ActivitySummary:
    return ActivitySummary(
        class_id="class-1",
        activity_id="activity-1",
        title="Issue 101 Activity",
        status="active",
        scoring_orientation="evidence_only",
        session_count=1,
        group_count=1,
        snapshot_revision=7,
    )


def _generated() -> SimpleNamespace:
    return SimpleNamespace(
        generation_status="generated",
        output_relative_path=(
            "rendered/packets/packet-instance-secret.pdf"
        ),
        packet_instance_id="packet-instance-secret",
        generation_id="generation-secret",
        target_key="participant:student-secret",
        output_sha256="a" * 64,
    )


def test_prepared_materials_menu_opens_selected_pdf_through_shared_service(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    activity = _activity()
    item = _generated()
    opened: list[str] = []
    monkeypatch.setattr(
        menu_generation,
        "list_packet_instances",
        lambda *_args, **_kwargs: (item,),
    )
    monkeypatch.setattr(
        menu_generation,
        "_teacher_instance_labels",
        lambda _activity, _items: ("Alex One",),
    )
    monkeypatch.setattr(
        menu_generation,
        "open_rendered_packet_output",
        lambda _class_id, _activity_id, packet_id: opened.append(packet_id),
    )
    monkeypatch.setattr(
        menu_generation,
        "render_packet_instance",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("Open must not render")
        ),
    )
    monkeypatch.setattr(
        menu_generation,
        "confirm_write",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("Open must not request write confirmation")
        ),
    )
    monkeypatch.setattr(menu_generation, "clear_screen", lambda: None)
    monkeypatch.setattr(menu_generation, "show_result", lambda *_args: None)
    answers = iter(("1", "1", "b"))
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))

    menu_generation.launch_prepared_materials_menu(
        activity,
        MenuSessionContext(),
    )

    assert opened == ["packet-instance-secret"]
    output = capsys.readouterr().out
    assert "Alex One - Ready to print" in output
    assert "packet-instance-secret" not in output
    assert "generation-secret" not in output
    assert "student-secret" not in output
    assert "a" * 64 not in output


def test_prepared_materials_folder_open_is_read_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    activity = _activity()
    item = _generated()
    opened: list[str] = []
    monkeypatch.setattr(
        menu_generation,
        "list_packet_instances",
        lambda *_args, **_kwargs: (item,),
    )
    monkeypatch.setattr(
        menu_generation,
        "open_rendered_packet_output_directory",
        lambda _class_id, _activity_id, packet_id: opened.append(packet_id),
    )
    monkeypatch.setattr(
        menu_generation,
        "render_packet_instance",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("Folder Open must not render")
        ),
    )
    monkeypatch.setattr(
        menu_generation,
        "confirm_write",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("Folder Open must not confirm a write")
        ),
    )
    monkeypatch.setattr(menu_generation, "clear_screen", lambda: None)
    monkeypatch.setattr(menu_generation, "show_result", lambda *_args: None)
    answers = iter(("2", "b"))
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))

    menu_generation.launch_prepared_materials_menu(
        activity,
        MenuSessionContext(),
    )

    assert opened == ["packet-instance-secret"]


def test_advanced_packet_menu_keeps_open_separate_from_render_reprint(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    activity = _activity()
    calls: list[str] = []
    monkeypatch.setattr(
        menu_generation,
        "_open_ready_packet",
        lambda _activity: calls.append("pdf"),
    )
    monkeypatch.setattr(
        menu_generation,
        "_open_ready_folder",
        lambda _activity: calls.append("folder"),
    )
    monkeypatch.setattr(menu_generation, "clear_screen", lambda: None)
    answers = iter(("6", "7", "b"))
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))

    menu_generation.launch_packet_generation_menu(
        activity,
        MenuSessionContext(),
    )

    assert calls == ["pdf", "folder"]
    output = capsys.readouterr().out
    assert "4. Render / reprint a Packet Instance" in output
    assert "6. Open a rendered Packet" in output
    assert "7. Open rendered Packet folder" in output


def test_open_folder_without_ready_output_guides_to_render_reprint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    activity = _activity()
    pending = SimpleNamespace(
        generation_status="routes_pending",
        packet_instance_id="pending-secret",
    )
    captured: list[tuple[str, tuple[str, ...]]] = []
    monkeypatch.setattr(
        menu_generation,
        "list_packet_instances",
        lambda *_args, **_kwargs: (pending,),
    )
    monkeypatch.setattr(
        menu_generation,
        "open_rendered_packet_output_directory",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("No viewer call is allowed without a ready output")
        ),
    )
    monkeypatch.setattr(
        menu_generation,
        "show_result",
        lambda title, lines: captured.append((title, tuple(lines))),
    )

    menu_generation._open_ready_folder(activity)

    assert len(captured) == 1
    assert "Render / reprint" in "\n".join(captured[0][1])


def test_teacher_instance_labels_use_names_without_raw_target_ids(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    activity = _activity()
    participant = _generated()
    group = SimpleNamespace(
        generation_status="generated",
        output_relative_path="rendered/packets/group-output.pdf",
        packet_instance_id="group-instance-secret",
        generation_id="generation-secret-2",
        target_key="group:group-secret",
        output_sha256="b" * 64,
    )
    roster = SimpleNamespace(
        students=(SimpleNamespace(student_id="student-secret", label="Alex One"),)
    )
    monkeypatch.setattr(menu_generation, "resolve_workspace_root", lambda: object())
    monkeypatch.setattr(menu_generation, "load_class_roster", lambda *_args: roster)
    monkeypatch.setattr(
        menu_generation,
        "student_display_name",
        lambda student: student.label,
    )
    monkeypatch.setattr(
        menu_generation,
        "list_groups",
        lambda *_args, **_kwargs: (
            SimpleNamespace(group_id="group-secret", label="Lab Team Blue"),
        ),
    )

    labels = menu_generation._teacher_instance_labels(
        activity,
        (participant, group),
    )

    assert labels == ("Alex One", "Lab Team Blue")
    assert "student-secret" not in " ".join(labels)
    assert "group-secret" not in " ".join(labels)


def test_post_generation_menu_scopes_open_actions_to_completed_generation(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    activity = _activity()
    new_one = SimpleNamespace(
        generation_status="generated",
        output_relative_path="rendered/packets/new-one.pdf",
        packet_instance_id="new-one",
        generation_id="generation-new",
        target_key="participant:student-one",
        output_sha256="c" * 64,
    )
    new_two = SimpleNamespace(
        generation_status="generated",
        output_relative_path="rendered/packets/new-two.pdf",
        packet_instance_id="new-two",
        generation_id="generation-new",
        target_key="participant:student-two",
        output_sha256="d" * 64,
    )
    old = SimpleNamespace(
        generation_status="generated",
        output_relative_path="rendered/packets/old.pdf",
        packet_instance_id="old-one",
        generation_id="generation-old",
        target_key="participant:student-old",
        output_sha256="e" * 64,
    )
    rendered = SimpleNamespace(
        generation_id="generation-new",
        packets=(
            SimpleNamespace(packet_instance_id="new-one"),
            SimpleNamespace(packet_instance_id="new-two"),
        ),
        page_count=4,
        route_count=4,
    )
    queried_generations: list[str | None] = []
    opened_pdf: list[str] = []
    opened_folder: list[str] = []

    def list_instances(
        _class_id: str,
        _activity_id: str,
        *,
        generation_id: str | None = None,
    ):
        queried_generations.append(generation_id)
        if generation_id == "generation-new":
            return (new_one, new_two)
        return (old, new_one, new_two)

    monkeypatch.setattr(menu_generation, "list_packet_instances", list_instances)
    monkeypatch.setattr(
        menu_generation,
        "_teacher_instance_labels",
        lambda _activity, items: tuple(
            {
                "new-one": "Alex One",
                "new-two": "Blair Two",
                "old-one": "Older Output",
            }[item.packet_instance_id]
            for item in items
        ),
    )
    monkeypatch.setattr(
        menu_generation,
        "open_rendered_packet_output",
        lambda _class_id, _activity_id, packet_id: opened_pdf.append(packet_id),
    )
    monkeypatch.setattr(
        menu_generation,
        "open_rendered_packet_output_directory",
        lambda _class_id, _activity_id, packet_id: opened_folder.append(packet_id),
    )
    monkeypatch.setattr(
        menu_generation,
        "render_packet_generation",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("post-generation Open must not render again")
        ),
    )
    monkeypatch.setattr(
        menu_generation,
        "render_packet_instance",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("post-generation Open must not reprint")
        ),
    )
    monkeypatch.setattr(
        menu_generation,
        "confirm_write",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("post-generation Open must not confirm a write")
        ),
    )
    monkeypatch.setattr(menu_generation, "clear_screen", lambda: None)
    monkeypatch.setattr(menu_generation, "show_result", lambda *_args: None)
    answers = iter(("1", "2", "2", "3"))
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))

    menu_generation._post_generation_open_menu(activity, rendered)

    assert opened_pdf == ["new-two"]
    assert opened_folder == ["new-two"]
    assert queried_generations
    assert set(queried_generations) == {"generation-new"}
    output = capsys.readouterr().out
    assert "Packet generation completed." in output
    assert "1. Open one rendered Packet" in output
    assert "2. Open rendered Packet folder" in output
    assert "old-one" not in output
    assert "generation-new" not in output
    assert "rendered/packets" not in output


def test_successful_generate_enters_post_generation_open_affordance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    activity = _activity()
    state = MenuSessionContext(actor=WorkflowActor(actor_id="teacher-1"))
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
    prepared = SimpleNamespace(ready_for_commit=True)
    committed = SimpleNamespace(generation_id="generation-new")
    rendered = SimpleNamespace(
        generation_id="generation-new",
        packets=(SimpleNamespace(packet_instance_id="packet-new"),),
        page_count=1,
        route_count=1,
    )
    post_generation: list[object] = []

    monkeypatch.setattr(menu_generation, "get_packet", lambda _id: detail)
    monkeypatch.setattr(
        menu_generation,
        "_choose_session",
        lambda _activity: session,
    )
    monkeypatch.setattr(
        menu_generation,
        "_component_choices",
        lambda _components: (),
    )
    monkeypatch.setattr(
        menu_generation,
        "prepare_packet_instantiation",
        lambda _request: prepared,
    )
    monkeypatch.setattr(
        menu_generation,
        "_prompt_missing_bindings",
        lambda _prepared: (),
    )
    monkeypatch.setattr(
        menu_generation,
        "_prompt_missing_subject_bindings",
        lambda _prepared: (),
    )
    monkeypatch.setattr(
        menu_generation,
        "_preview_lines",
        lambda _prepared: ("review",),
    )
    monkeypatch.setattr(
        menu_generation,
        "confirm_write",
        lambda *_args, **_kwargs: True,
    )
    monkeypatch.setattr(
        menu_generation,
        "commit_packet_instantiation",
        lambda _prepared: committed,
    )
    render_calls: list[str] = []

    def render_generation(request):
        render_calls.append(request.generation_id)
        return rendered

    monkeypatch.setattr(
        menu_generation,
        "render_packet_generation",
        render_generation,
    )
    monkeypatch.setattr(
        menu_generation,
        "_post_generation_open_menu",
        lambda selected_activity, result: post_generation.append(
            (selected_activity.activity_id, result)
        ),
    )
    monkeypatch.setattr(
        menu_generation,
        "show_result",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError(
                "successful generation should hand off to the Open affordance"
            )
        ),
    )

    menu_generation._generate(
        activity,
        state,
        selected_packet=packet,
    )

    assert render_calls == ["generation-new"]
    assert post_generation == [("activity-1", rendered)]
