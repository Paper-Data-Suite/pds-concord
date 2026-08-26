from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace

import pytest

from concord.cli_app.handlers import packet_runtime
from concord.cli_app.parser import build_parser
from concord.menu_activity import launch_activity_context_menu
from concord.menu_context import MenuSessionContext
from concord.workflows import ActivitySummary
from concord.workflows.errors import ConcordWorkflowValidationError
from concord.workflows.packet_instantiation import (
    PacketComponentChoice,
    PacketRenderingBinding,
)


def test_packet_runtime_commands_are_exposed_by_parser() -> None:
    parser = build_parser()

    preview = parser.parse_args(
        [
            "packet",
            "instantiate-preview",
            "--class-id",
            "class-1",
            "--activity-id",
            "activity-1",
            "--session-id",
            "session-1",
            "--packet-definition-id",
            "packet-1",
            "--packet-version-id",
            "packet-version-1",
            "--actor-id",
            "teacher-1",
        ]
    )
    assert preview.handler is packet_runtime.handle_instantiate_preview

    commit = parser.parse_args(
        [
            "packet",
            "instantiate",
            "--class-id",
            "class-1",
            "--activity-id",
            "activity-1",
            "--session-id",
            "session-1",
            "--packet-definition-id",
            "packet-1",
            "--packet-version-id",
            "packet-version-1",
            "--review-digest",
            "a" * 64,
            "--actor-id",
            "teacher-1",
        ]
    )
    assert commit.handler is packet_runtime.handle_instantiate

    resume = parser.parse_args(
        [
            "packet",
            "instantiate-resume",
            "--class-id",
            "class-1",
            "--activity-id",
            "activity-1",
            "--generation-id",
            "generation-1",
        ]
    )
    assert resume.handler is packet_runtime.handle_instantiate_resume

    instance_list = parser.parse_args(
        [
            "packet",
            "instance-list",
            "--class-id",
            "class-1",
            "--activity-id",
            "activity-1",
        ]
    )
    assert instance_list.handler is packet_runtime.handle_instance_list

    instance_show = parser.parse_args(
        [
            "packet",
            "instance-show",
            "--class-id",
            "class-1",
            "--activity-id",
            "activity-1",
            "--packet-instance-id",
            "packet-instance-1",
        ]
    )
    assert instance_show.handler is packet_runtime.handle_instance_show

    instance_render = parser.parse_args(
        [
            "packet",
            "instance-render",
            "--class-id",
            "class-1",
            "--activity-id",
            "activity-1",
            "--packet-instance-id",
            "packet-instance-1",
            "--actor-id",
            "teacher-1",
        ]
    )
    assert instance_render.handler is packet_runtime.handle_instance_render

    generation_render = parser.parse_args(
        [
            "packet",
            "generation-render",
            "--class-id",
            "class-1",
            "--activity-id",
            "activity-1",
            "--generation-id",
            "generation-1",
            "--actor-id",
            "teacher-1",
        ]
    )
    assert generation_render.handler is packet_runtime.handle_generation_render


def test_options_file_parses_explicit_choices_and_typed_bindings(
    tmp_path: Path,
) -> None:
    path = tmp_path / "packet-options.json"
    path.write_text(
        json.dumps(
            {
                "component_choices": [
                    {
                        "packet_component_id": "component-1",
                        "include": False,
                    }
                ],
                "rendering_bindings": [
                    {
                        "packet_component_id": "component-2",
                        "input_key": "teacher_prompt",
                        "value": "Discuss the evidence.",
                    },
                    {
                        "packet_component_id": "component-2",
                        "input_key": "criterion_label",
                        "value": 3,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    choices, bindings = packet_runtime._load_options(str(path))
    assert choices == (
        PacketComponentChoice(
            packet_component_id="component-1",
            include=False,
        ),
    )
    assert bindings == (
        PacketRenderingBinding(
            packet_component_id="component-2",
            input_key="teacher_prompt",
            value="Discuss the evidence.",
        ),
        PacketRenderingBinding(
            packet_component_id="component-2",
            input_key="criterion_label",
            value=3,
        ),
    )


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {"unknown": []},
        {"component_choices": {}},
        {"rendering_bindings": {}},
        {
            "component_choices": [
                {"packet_component_id": "component-1", "include": "yes"}
            ]
        },
    ],
)
def test_options_file_rejects_noncanonical_shapes(
    tmp_path: Path,
    payload: object,
) -> None:
    path = tmp_path / "bad-options.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ConcordWorkflowValidationError):
        packet_runtime._load_options(str(path))


def test_instance_render_expected_snapshot_is_optional() -> None:
    parser = build_parser()
    args: Namespace = parser.parse_args(
        [
            "packet",
            "instance-render",
            "--class-id",
            "class-1",
            "--activity-id",
            "activity-1",
            "--packet-instance-id",
            "packet-instance-1",
            "--actor-id",
            "teacher-1",
        ]
    )
    assert args.expected_snapshot is None


def test_open_activity_menu_dispatches_packet_generation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    activity = ActivitySummary(
        class_id="class-1",
        activity_id="activity-1",
        title="Synthetic Activity",
        status="active",
        scoring_orientation="evidence_only",
        session_count=1,
        group_count=1,
        snapshot_revision=4,
    )
    import concord.menu_activity as menu_activity

    monkeypatch.setattr(
        menu_activity,
        "show_activity",
        lambda *_args, **_kwargs: SimpleNamespace(summary=activity),
    )
    monkeypatch.setattr(menu_activity, "clear_screen", lambda: None)
    monkeypatch.setattr(menu_activity, "print_menu_header", lambda *_args: None)
    monkeypatch.setattr(menu_activity, "print_navigation", lambda: None)
    monkeypatch.setattr(menu_activity, "pause_for_user", lambda: None)

    dispatched: list[str] = []

    def fake_packet_menu(
        selected: ActivitySummary,
        _state: MenuSessionContext,
    ) -> None:
        dispatched.append(selected.activity_id)

    monkeypatch.setattr(
        menu_activity,
        "launch_packet_generation_menu",
        fake_packet_menu,
    )
    responses = iter(("11", "b"))
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(responses))

    launch_activity_context_menu(activity, MenuSessionContext())
    assert dispatched == ["activity-1"]
