from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

import concord.menu_group_plan as plan_menu
import concord.menu_grouping_signal as signal_menu
from concord.menu_context import MenuSessionContext
from concord.workflows import (
    ActivitySummary,
    ConcordWorkflowValidationError,
    ImportGroupingSignalCsvRequest,
    WorkflowActor,
)


def _activity() -> ActivitySummary:
    return ActivitySummary(
        class_id="class-1",
        activity_id="activity-1",
        title="Planning Activity",
        status="draft",
        scoring_orientation="evidence_only",
        session_count=1,
        group_count=0,
        snapshot_revision=7,
    )


def _state() -> MenuSessionContext:
    return MenuSessionContext(actor=WorkflowActor(actor_id="teacher-1"))


def _summary(signal_id: str) -> SimpleNamespace:
    return SimpleNamespace(
        class_id="class-1",
        signal_set_id=signal_id,
        created_at=datetime(2026, 8, 20, tzinfo=timezone.utc),
        source_kind="teacher_authored",
        source_module_id=None,
        digest_algorithm="sha256",
        digest="a" * 64,
        dimension_ids=("dimension-a", "dimension-b"),
    )


def _inspection() -> SimpleNamespace:
    dimension_a = SimpleNamespace(dimension_id="dimension-a", band_count=3)
    dimension_b = SimpleNamespace(dimension_id="dimension-b", band_count=4)
    diagnostics = SimpleNamespace(
        findings=(),
        dimensions=(
            SimpleNamespace(
                dimension_id="dimension-a",
                band_count=3,
                roster_student_count=3,
                signal_entry_count=3,
                matched_student_count=3,
                missing_student_count=0,
                wrong_class_student_count=0,
                unknown_student_count=0,
                band_counts=((1, 1), (2, 1), (3, 1)),
            ),
            SimpleNamespace(
                dimension_id="dimension-b",
                band_count=4,
                roster_student_count=3,
                signal_entry_count=2,
                matched_student_count=2,
                missing_student_count=1,
                wrong_class_student_count=0,
                unknown_student_count=0,
                band_counts=((1, 0), (2, 1), (3, 1), (4, 0)),
            ),
        ),
    )
    return SimpleNamespace(
        summary=_summary("signal-b"),
        stored=SimpleNamespace(
            digest="a" * 64,
            signal=SimpleNamespace(
                signal_set_id="signal-b",
                class_id="class-1",
                created_at=datetime(2026, 8, 20, tzinfo=timezone.utc),
                source=SimpleNamespace(
                    kind="teacher_authored",
                    module_id=None,
                    snapshot_id=None,
                    snapshot_digest_algorithm=None,
                    snapshot_digest=None,
                ),
                dimensions=(dimension_a, dimension_b),
            ),
        ),
        diagnostics=diagnostics,
    )


def test_plan_groups_menu_exposes_grouping_signals(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    values = iter(["5", "b"])

    monkeypatch.setattr(
        "builtins.input",
        lambda _prompt="": next(values),
    )
    monkeypatch.setattr(plan_menu, "clear_screen", lambda: None)
    monkeypatch.setattr(
        plan_menu,
        "print_menu_header",
        lambda *_a, **_k: None,
    )
    monkeypatch.setattr(
        plan_menu,
        "print_navigation",
        lambda *_a, **_k: None,
    )
    monkeypatch.setattr(plan_menu, "_latest", lambda activity: activity)
    monkeypatch.setattr(
        plan_menu,
        "launch_grouping_signal_menu",
        lambda _activity: calls.append("signals"),
    )

    plan_menu.launch_group_plan_menu(_activity(), _state())
    assert calls == ["signals"]


def test_inspection_requires_explicit_signal_and_dimension_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summaries = (_summary("signal-a"), _summary("signal-b"))
    inspection = _inspection()
    selections: list[str] = []
    inspected: list[tuple[str, str]] = []
    shown: list[str] = []

    monkeypatch.setattr(
        signal_menu,
        "list_grouping_signals",
        lambda class_id: summaries,
    )

    def fake_select(
        title: str,
        items: object,
        labels: object,
        *,
        help_text: str,
    ) -> object:
        del items, labels, help_text
        selections.append(title)
        if len(selections) == 1:
            return summaries[1]
        return inspection.stored.signal.dimensions[1]

    monkeypatch.setattr(signal_menu, "select_one", fake_select)
    monkeypatch.setattr(
        signal_menu,
        "inspect_grouping_signal",
        lambda class_id, signal_id: (
            inspected.append((class_id, signal_id)) or inspection
        ),
    )
    monkeypatch.setattr(
        signal_menu,
        "_show_signal_inspection",
        lambda _inspection: shown.append("signal"),
    )
    monkeypatch.setattr(
        signal_menu,
        "_show_dimension_diagnostics",
        lambda _inspection, dimension_id: shown.append(dimension_id),
    )

    signal_menu._inspect_signal(_activity())

    assert selections == [
        "Choose a Grouping Signal",
        "Choose a Signal Dimension",
    ]
    assert inspected == [("class-1", "signal-b")]
    assert shown == ["signal", "dimension-b"]


def test_invalid_import_never_reaches_confirmation_or_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    confirmed: list[bool] = []
    written: list[bool] = []

    monkeypatch.setattr(
        signal_menu,
        "prompt_text",
        lambda *a, **k: "invalid.csv",
    )
    monkeypatch.setattr(
        signal_menu,
        "inspect_grouping_signal_csv_file",
        lambda _path: SimpleNamespace(requires_new_identity=False),
    )
    monkeypatch.setattr(
        signal_menu,
        "prepare_grouping_signal_csv_import",
        lambda _request: (_ for _ in ()).throw(
            ConcordWorkflowValidationError("unknown_student")
        ),
    )
    monkeypatch.setattr(
        signal_menu,
        "confirm_write",
        lambda *a, **k: confirmed.append(True) or True,
    )
    monkeypatch.setattr(
        signal_menu,
        "import_grouping_signal_csv",
        lambda _request: written.append(True),
    )

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="unknown_student",
    ):
        signal_menu._import_csv(_activity())

    assert confirmed == []
    assert written == []


def test_missing_only_import_is_reviewed_and_digest_bound(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    missing = SimpleNamespace(
        code="missing_student_signal",
        severity="warning",
        student_id="student-3",
        dimension_id="discussion",
    )
    diagnostics = SimpleNamespace(
        findings=(missing,),
        dimensions=(
            SimpleNamespace(
                dimension_id="discussion",
                band_count=3,
                matched_student_count=2,
                missing_student_count=1,
            ),
        ),
    )
    signal = SimpleNamespace(
        class_id="class-1",
        signal_set_id="signal-1",
        source=SimpleNamespace(
            kind="teacher_authored",
            module_id=None,
            snapshot_id=None,
            snapshot_digest_algorithm=None,
            snapshot_digest=None,
        ),
    )
    preview = SimpleNamespace(
        signal=signal,
        representation_scope="complete_signal",
        digest="d" * 64,
        diagnostics=diagnostics,
        dimension=SimpleNamespace(dimension_id="discussion"),
    )
    import_result = SimpleNamespace(
        disposition="created",
        preview=preview,
        stored=SimpleNamespace(
            signal=signal,
            digest="d" * 64,
        ),
    )
    confirmed_lines: list[tuple[str, ...]] = []
    requests: list[ImportGroupingSignalCsvRequest] = []
    shown: list[tuple[str, tuple[str, ...]]] = []

    monkeypatch.setattr(
        signal_menu,
        "prompt_text",
        lambda *a, **k: "signal.csv",
    )
    monkeypatch.setattr(
        signal_menu,
        "inspect_grouping_signal_csv_file",
        lambda _path: SimpleNamespace(requires_new_identity=False),
    )
    monkeypatch.setattr(
        signal_menu,
        "prepare_grouping_signal_csv_import",
        lambda request: preview,
    )
    monkeypatch.setattr(
        signal_menu,
        "confirm_write",
        lambda title, expected, lines: (
            confirmed_lines.append(tuple(lines)) or True
        ),
    )

    def fake_import(request: ImportGroupingSignalCsvRequest) -> object:
        requests.append(request)
        return import_result

    monkeypatch.setattr(
        signal_menu,
        "import_grouping_signal_csv",
        fake_import,
    )
    monkeypatch.setattr(
        signal_menu,
        "show_result",
        lambda title, lines: shown.append((title, tuple(lines))),
    )

    signal_menu._import_csv(_activity())

    assert len(confirmed_lines) == 1
    assert "Missing students: 1" in confirmed_lines[0]
    assert "Missing student IDs: student-3" in confirmed_lines[0]
    assert "Missing coverage is not a lowest-band value." in confirmed_lines[0]
    assert requests[0].expected_signal_digest == "d" * 64
    assert shown[0][0] == "Grouping Signal Import Result"


def test_projection_identity_and_time_are_explicit_before_confirmation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses = iter(
        [
            "projection.csv",
            "projection-new-1",
            "2026-08-20T21:30:00+00:00",
        ]
    )
    request_seen: list[ImportGroupingSignalCsvRequest] = []
    confirm_lines: list[tuple[str, ...]] = []
    diagnostics = SimpleNamespace(
        findings=(),
        dimensions=(
            SimpleNamespace(
                dimension_id="reading",
                band_count=4,
                matched_student_count=3,
                missing_student_count=0,
            ),
        ),
    )
    signal = SimpleNamespace(
        class_id="class-1",
        signal_set_id="projection-new-1",
        source=SimpleNamespace(
            kind="module_generated",
            module_id="synthetic_module",
            snapshot_id="source-1",
            snapshot_digest_algorithm="sha256",
            snapshot_digest="b" * 64,
        ),
    )
    preview = SimpleNamespace(
        signal=signal,
        representation_scope="dimension_projection",
        digest="c" * 64,
        diagnostics=diagnostics,
        dimension=SimpleNamespace(dimension_id="reading"),
    )
    result = SimpleNamespace(
        disposition="created",
        preview=preview,
        stored=SimpleNamespace(signal=signal, digest="c" * 64),
    )

    monkeypatch.setattr(
        signal_menu,
        "prompt_text",
        lambda *a, **k: next(responses),
    )
    monkeypatch.setattr(
        signal_menu,
        "inspect_grouping_signal_csv_file",
        lambda _path: SimpleNamespace(requires_new_identity=True),
    )

    def fake_prepare(request: ImportGroupingSignalCsvRequest) -> object:
        request_seen.append(request)
        return preview

    monkeypatch.setattr(
        signal_menu,
        "prepare_grouping_signal_csv_import",
        fake_prepare,
    )
    monkeypatch.setattr(
        signal_menu,
        "confirm_write",
        lambda title, expected, lines: (
            confirm_lines.append(tuple(lines)) or True
        ),
    )
    monkeypatch.setattr(
        signal_menu,
        "import_grouping_signal_csv",
        lambda request: result,
    )
    monkeypatch.setattr(signal_menu, "show_result", lambda *a, **k: None)

    signal_menu._import_csv(_activity())

    prepared = request_seen[0]
    assert prepared.new_signal_set_id == "projection-new-1"
    assert prepared.new_created_at == datetime(
        2026,
        8,
        20,
        21,
        30,
        tzinfo=timezone.utc,
    )
    assert "Signal set: projection-new-1" in confirm_lines[0]
    assert "Representation: dimension_projection" in confirm_lines[0]
    assert "Source module: synthetic_module" in confirm_lines[0]
