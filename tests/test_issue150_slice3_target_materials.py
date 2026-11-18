"""#150 Slice 3: target-only Packet checkpoints and guarded guided continuation."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import concord.menu_guided_activity as guided
import concord.menu_packet_generation as packet_menu
import concord.workflows.target_materials_preflight as preflight
from concord.menu_context import MenuSessionContext
from concord.workflows.errors import ConcordWorkflowConflictError
from concord.workflows.models import ActivitySummary
from concord.workflows.packet_generation import PacketGenerationSummary


def _activity(revision: int = 8) -> ActivitySummary:
    return ActivitySummary(
        class_id="class-target",
        activity_id="activity-new",
        title="Target Seminar",
        status="draft",
        scoring_orientation="evidence_only",
        session_count=1,
        group_count=0,
        snapshot_revision=revision,
    )


def _generation(
    *,
    name: str = "gen-one",
    pending: int = 0,
    generated: int = 1,
    class_id: str = "class-target",
    activity_id: str = "activity-new",
) -> PacketGenerationSummary:
    return PacketGenerationSummary(
        class_id=class_id,
        activity_id=activity_id,
        generation_id=name,
        packet_definition_id="saved-packet",
        packet_version_id="saved-version-1",
        packet_name="Seminar Packet",
        packet_version_label="1.0",
        session_id="target-session-1",
        session_label="Target Day 1",
        session_sequence=1,
        generation_date=None,
        created_at="2026-11-17T16:00:00+00:00",
        instance_count=pending + generated,
        artifact_count=pending + generated,
        page_count=pending + generated,
        route_count=pending + generated,
        planned_count=0,
        routes_pending_count=pending,
        rendering_count=0,
        generated_count=generated,
        failed_count=0,
        cancelled_count=0,
        snapshot_revision=8,
        snapshot_sha256="a" * 64,
    )


def _checkpoint(*rows: PacketGenerationSummary) -> preflight.TargetMaterialsCheckpoint:
    return preflight.TargetMaterialsCheckpoint(
        class_id="class-target",
        activity_id="activity-new",
        title="Target Seminar",
        snapshot_revision=8,
        generations=rows,
    )


def _inputs(monkeypatch: pytest.MonkeyPatch, *choices: str) -> None:
    answers = iter(choices)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    monkeypatch.setattr(guided, "clear_screen", lambda: None)


def test_inspection_reads_only_target_class_and_current_generation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reads: list[tuple[str, str]] = []
    monkeypatch.setattr(
        preflight, "resolve_read_workspace_root", lambda root=None: Path("synthetic")
    )
    monkeypatch.setattr(preflight, "require_core_class", lambda *_a: object())

    def activity_reader(class_id: str, activity_id: str, **_kwargs: object) -> object:
        reads.append((class_id, activity_id))
        return SimpleNamespace(summary=_activity())

    def generations_reader(
        class_id: str, activity_id: str, **_kwargs: object
    ) -> tuple[PacketGenerationSummary, ...]:
        reads.append((class_id, activity_id))
        return (_generation(),)

    monkeypatch.setattr(preflight, "show_activity", activity_reader)
    monkeypatch.setattr(preflight, "list_packet_generations", generations_reader)
    found = preflight.inspect_target_materials("class-target", "activity-new")
    assert reads == [("class-target", "activity-new")] * 2
    assert found.ready_to_print == 1
    assert not found.requires_recovery


@pytest.mark.parametrize(
    "incorrect",
    (
        _generation(class_id="class-source"),
        _generation(activity_id="activity-source"),
    ),
)
def test_cross_class_generation_is_rejected_without_writes(
    monkeypatch: pytest.MonkeyPatch, incorrect: PacketGenerationSummary
) -> None:
    monkeypatch.setattr(
        preflight, "resolve_read_workspace_root", lambda root=None: Path("synthetic")
    )
    monkeypatch.setattr(preflight, "require_core_class", lambda *_a: object())
    monkeypatch.setattr(
        preflight,
        "show_activity",
        lambda *_a, **_k: SimpleNamespace(summary=_activity()),
    )
    monkeypatch.setattr(
        preflight, "list_packet_generations", lambda *_a, **_k: (incorrect,)
    )
    with pytest.raises(ConcordWorkflowConflictError):
        preflight.inspect_target_materials("class-target", "activity-new")


def test_new_generation_diff_never_reuses_prior_id_or_cross_class() -> None:
    one = _generation()
    two = _generation(name="gen-two")
    delta = preflight.new_target_generations(_checkpoint(one), _checkpoint(one, two))
    assert delta == (two,)
    assert preflight.new_target_generations(_checkpoint(one), _checkpoint(one)) == ()
    with pytest.raises(ConcordWorkflowConflictError):
        preflight.new_target_generations(_checkpoint(one), _checkpoint(two))
    with pytest.raises(ConcordWorkflowConflictError):
        preflight.new_target_generations(
            _checkpoint(one),
            preflight.TargetMaterialsCheckpoint(
                class_id="class-source",
                activity_id="activity-old",
                title="Other",
                snapshot_revision=8,
                generations=(one,),
            ),
        )


def test_existing_pending_routes_offer_recovery_not_new_copy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observations: list[str] = []
    before = _checkpoint(_generation(pending=1, generated=0))
    monkeypatch.setattr(
        guided, "resolve_read_workspace_root", lambda: Path("synthetic")
    )
    monkeypatch.setattr(guided, "inspect_target_materials", lambda *_a, **_k: before)
    monkeypatch.setattr(
        guided, "show_activity", lambda *_a, **_k: SimpleNamespace(summary=_activity())
    )
    monkeypatch.setattr(
        guided,
        "launch_packet_generation_menu",
        lambda *_a: observations.append("recovery"),
    )
    monkeypatch.setattr(
        guided,
        "_launch_materials",
        lambda *_a: pytest.fail("Do not generate while pending"),
    )
    _inputs(monkeypatch, "1", "2")
    guided._launch_target_materials(_activity(), MenuSessionContext())
    assert observations == ["recovery"]


def test_existing_generated_requires_explicit_new_generation_choice(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    before = _checkpoint(_generation())
    monkeypatch.setattr(
        guided, "resolve_read_workspace_root", lambda: Path("synthetic")
    )
    monkeypatch.setattr(guided, "inspect_target_materials", lambda *_a, **_k: before)
    monkeypatch.setattr(
        guided, "_launch_materials", lambda *_a: pytest.fail("No automatic duplicate")
    )
    _inputs(monkeypatch, "3")
    guided._launch_target_materials(_activity(), MenuSessionContext())


def test_target_new_generation_reread_reports_only_canonical_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    before, after = _checkpoint(), _checkpoint(_generation())
    reads = iter((before, before, after, after))
    monkeypatch.setattr(
        guided, "resolve_read_workspace_root", lambda: Path("synthetic")
    )
    monkeypatch.setattr(
        guided, "inspect_target_materials", lambda *_a, **_k: next(reads)
    )
    monkeypatch.setattr(
        guided, "show_activity", lambda *_a, **_k: SimpleNamespace(summary=_activity())
    )
    created: list[ActivitySummary] = []
    monkeypatch.setattr(guided, "_launch_materials", lambda a, _s: created.append(a))
    lines: list[str] = []
    monkeypatch.setattr(guided, "show_result", lambda _name, shown: lines.extend(shown))
    _inputs(monkeypatch, "1", "3")
    guided._launch_target_materials(_activity(), MenuSessionContext())
    assert created == [_activity()]
    text = "\n".join(lines)
    assert "new target generation" in text.casefold()
    assert "Ready to print: 1" in text
    assert "Route-required pages: 1" in text
    assert "not proof of printing" in text.lower()
    assert "source" not in text.lower()


def test_cancelled_generation_does_not_infer_commit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    before = _checkpoint()
    monkeypatch.setattr(
        guided, "resolve_read_workspace_root", lambda: Path("synthetic")
    )
    monkeypatch.setattr(guided, "inspect_target_materials", lambda *_a, **_k: before)
    monkeypatch.setattr(
        guided, "show_activity", lambda *_a, **_k: SimpleNamespace(summary=_activity())
    )
    monkeypatch.setattr(guided, "_launch_materials", lambda *_a: None)
    lines: list[str] = []
    monkeypatch.setattr(guided, "show_result", lambda _name, shown: lines.extend(shown))
    _inputs(monkeypatch, "1", "2")
    guided._launch_target_materials(_activity(), MenuSessionContext())
    assert "No new target generation" in " ".join(lines)


def test_saved_packet_version_change_blocks_before_prepare(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    packet = SimpleNamespace(
        packet_definition_id="saved-packet",
        current_packet_version_id="old-version",
    )
    monkeypatch.setattr(
        packet_menu,
        "get_packet",
        lambda *_a: SimpleNamespace(
            summary=SimpleNamespace(current_packet_version_id="new-version")
        ),
    )
    errors: list[str] = []
    monkeypatch.setattr(
        packet_menu,
        "show_result",
        lambda _title, lines: errors.extend(lines),
    )
    monkeypatch.setattr(
        packet_menu,
        "prepare_packet_instantiation",
        lambda *_a, **_k: pytest.fail("Stale saved definition must not prepare"),
    )
    packet_menu.generate_saved_packet(_activity(), MenuSessionContext(), packet)
    assert "changed after selection" in " ".join(errors)
