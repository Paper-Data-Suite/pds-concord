from __future__ import annotations

from types import SimpleNamespace

import pytest

from concord import menu_packet_generation
from concord.menu_context import MenuSessionContext
from concord.workflows.models import ActivitySummary, WorkflowActor
from concord.workflows.packet_generation import PacketGenerationSummary


def _activity() -> ActivitySummary:
    return ActivitySummary(
        class_id="class-1",
        activity_id="activity-1",
        title="Seminar Activity",
        status="active",
        scoring_orientation="evidence_only",
        session_count=1,
        group_count=1,
        snapshot_revision=17,
    )


def _state() -> MenuSessionContext:
    return MenuSessionContext(
        actor=WorkflowActor(actor_id="teacher-1"),
    )


def _summary(
    *,
    planned: int = 0,
    routes_pending: int = 0,
    rendering: int = 0,
    generated: int = 2,
    failed: int = 0,
    cancelled: int = 0,
) -> PacketGenerationSummary:
    total = planned + routes_pending + rendering + generated + failed + cancelled
    return PacketGenerationSummary(
        class_id="class-1",
        activity_id="activity-1",
        generation_id="generation-technical-1",
        packet_definition_id="packet-1",
        packet_version_id="packet-version-1",
        packet_name="Seminar Reflection",
        packet_version_label="v1",
        session_id="session-1",
        session_label="Seminar Session 1",
        session_sequence=1,
        generation_date="2026-10-05",
        created_at="2026-10-05T18:00:00+00:00",
        instance_count=total,
        artifact_count=total,
        page_count=total * 2,
        route_count=total * 2,
        planned_count=planned,
        routes_pending_count=routes_pending,
        rendering_count=rendering,
        generated_count=generated,
        failed_count=failed,
        cancelled_count=cancelled,
        snapshot_revision=17,
        snapshot_sha256="a" * 64,
    )


def test_generation_selection_is_teacher_readable_not_raw_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summary = _summary()
    captured: list[str] = []

    monkeypatch.setattr(
        menu_packet_generation,
        "list_packet_generations",
        lambda *_args, **_kwargs: (summary,),
    )

    def select(
        _title: str,
        items: tuple[PacketGenerationSummary, ...],
        labels: tuple[str, ...],
        *,
        help_text: str,
    ) -> PacketGenerationSummary:
        assert help_text
        captured.extend(labels)
        return items[0]

    monkeypatch.setattr(menu_packet_generation, "select_one", select)

    selected = menu_packet_generation._choose_generation(
        _activity(),
        title="Render / Reprint Complete Generation",
    )

    assert selected is summary
    assert len(captured) == 1
    assert "Seminar Reflection" in captured[0]
    assert "Seminar Session 1" in captured[0]
    assert "2 Packets" in captured[0]
    assert "4 pages" in captured[0]
    assert "Ready to reprint" in captured[0]
    assert summary.generation_id not in captured[0]


def test_all_generated_generation_requires_reprint_and_reviewed_snapshot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summary = _summary(generated=2)
    confirmations: list[tuple[str, str, tuple[str, ...]]] = []
    requests: list[object] = []
    shown: list[tuple[str, tuple[str, ...]]] = []

    monkeypatch.setattr(
        menu_packet_generation,
        "_choose_generation",
        lambda *_args, **_kwargs: summary,
    )

    def confirm(
        title: str,
        action: str,
        lines: tuple[str, ...],
    ) -> bool:
        confirmations.append((title, action, lines))
        return True

    monkeypatch.setattr(menu_packet_generation, "confirm_write", confirm)

    def render(request: object) -> object:
        requests.append(request)
        return SimpleNamespace(
            generation_id=summary.generation_id,
            packets=(object(), object()),
            page_count=4,
            route_count=4,
        )

    monkeypatch.setattr(menu_packet_generation, "render_packet_generation", render)
    monkeypatch.setattr(
        menu_packet_generation,
        "show_result",
        lambda title, lines: shown.append((title, tuple(lines))),
    )

    menu_packet_generation._render_generation(_activity(), _state())

    assert confirmations[0][0] == "Reprint Packet Generation"
    assert confirmations[0][1] == "REPRINT"
    assert summary.generation_id not in "\n".join(confirmations[0][2])
    request = requests[0]
    assert request.generation_id == summary.generation_id
    assert request.expected_snapshot_revision == 17
    assert shown[-1][0] == "Packet Generation Render Result"


def test_mixed_generated_rendering_generation_requires_render(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summary = _summary(rendering=1, generated=1)
    actions: list[str] = []
    requests: list[object] = []

    monkeypatch.setattr(
        menu_packet_generation,
        "_choose_generation",
        lambda *_args, **_kwargs: summary,
    )
    monkeypatch.setattr(
        menu_packet_generation,
        "confirm_write",
        lambda _title, action, _lines: actions.append(action) or True,
    )
    monkeypatch.setattr(
        menu_packet_generation,
        "render_packet_generation",
        lambda request: requests.append(request)
        or SimpleNamespace(
            generation_id=summary.generation_id,
            packets=(object(), object()),
            page_count=4,
            route_count=4,
        ),
    )
    monkeypatch.setattr(
        menu_packet_generation,
        "show_result",
        lambda *_args, **_kwargs: None,
    )

    menu_packet_generation._render_generation(_activity(), _state())

    assert actions == ["RENDER"]
    assert len(requests) == 1


def test_routes_pending_generation_directs_teacher_to_recovery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summary = _summary(routes_pending=1, generated=1)
    confirmed: list[object] = []
    rendered: list[object] = []
    shown: list[tuple[str, tuple[str, ...]]] = []

    monkeypatch.setattr(
        menu_packet_generation,
        "_choose_generation",
        lambda *_args, **_kwargs: summary,
    )
    monkeypatch.setattr(
        menu_packet_generation,
        "confirm_write",
        lambda *_args, **_kwargs: confirmed.append(object()) or True,
    )
    monkeypatch.setattr(
        menu_packet_generation,
        "render_packet_generation",
        lambda *_args, **_kwargs: rendered.append(object()),
    )
    monkeypatch.setattr(
        menu_packet_generation,
        "show_result",
        lambda title, lines: shown.append((title, tuple(lines))),
    )

    menu_packet_generation._render_generation(_activity(), _state())

    assert confirmed == []
    assert rendered == []
    assert shown[-1][0] == "Packet Generation Requires Route Recovery"
    assert "Resume incomplete route preparation" in "\n".join(shown[-1][1])


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("planned", 1),
        ("failed", 1),
        ("cancelled", 1),
    ),
)
def test_nonrenderable_generation_is_not_silently_subset_rendered(
    field: str,
    value: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    counts = {
        "planned": 0,
        "routes_pending": 0,
        "rendering": 0,
        "generated": 1,
        "failed": 0,
        "cancelled": 0,
    }
    counts[field] = value
    summary = _summary(**counts)
    rendered: list[object] = []
    shown: list[tuple[str, tuple[str, ...]]] = []

    monkeypatch.setattr(
        menu_packet_generation,
        "_choose_generation",
        lambda *_args, **_kwargs: summary,
    )
    monkeypatch.setattr(
        menu_packet_generation,
        "render_packet_generation",
        lambda *_args, **_kwargs: rendered.append(object()),
    )
    monkeypatch.setattr(
        menu_packet_generation,
        "show_result",
        lambda title, lines: shown.append((title, tuple(lines))),
    )

    menu_packet_generation._render_generation(_activity(), _state())

    assert rendered == []
    assert shown[-1][0] == "Packet Generation Requires Attention"
    assert f"{field.capitalize()}: 1" in "\n".join(shown[-1][1])


def test_packet_generation_menu_exposes_complete_and_single_render_actions(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(menu_packet_generation, "clear_screen", lambda: None)
    monkeypatch.setattr(menu_packet_generation, "print_navigation", lambda: None)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "B")

    menu_packet_generation.launch_packet_generation_menu(
        _activity(),
        _state(),
    )

    output = capsys.readouterr().out
    assert "4. Render / reprint a complete generation" in output
    assert "5. Render / reprint one Packet Instance" in output
    assert "6. Resume incomplete route preparation" in output
