from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from pds_core.routing_models import PDS2_SCHEMA, ModuleWorkRef, RouteLocator
from pds_core.scan_failure_metadata import RoutingFailureMetadata

import concord.menu_scan as menu_scan
from concord.routing.candidates import ConcordRouteCandidate
from concord.routing.review import RoutingFailureReview, RoutingFailureSummary
from concord.workflows.models import WorkflowActor


def _summary() -> RoutingFailureSummary:
    return RoutingFailureSummary(
        failure_id="failure_machine_1",
        category="payload_missing",
        stage="route_resolution",
        source_filename="seminar-period2.pdf",
        source_page_number=4,
        activity_id=None,
        latest_status=None,
    )


def _review(
    *,
    route_available: bool = True,
    latest_status: str | None = None,
    reason: str | None = None,
) -> RoutingFailureReview:
    failure = RoutingFailureMetadata(
        schema_version="2",
        failure_id="failure_machine_1",
        scope="page",
        stage="route_resolution",
        created_at="2026-10-05T01:00:00+00:00",
        failure_category="payload_missing",
        failure_message="No usable PDS2 route was detected.",
        source_filename="seminar-period2.pdf",
        source_scan_id="scan_source_1",
        source_sha256="a" * 64,
        retained_source_path="scans/retained/source.pdf",
        review_copy_path=None,
        source_page_number=4,
        detected_payload=None,
        route_locator=None,
        target=None,
        module_details={},
    )
    return RoutingFailureReview(
        failure=failure,
        latest_status=latest_status,
        activity_title=None,
        bound_work=None,
        retained_provenance_complete=True,
        route_action_available=route_available,
        route_action_unavailable_reason=reason,
        route_action_unavailable_detail=None,
    )


def _candidate() -> ConcordRouteCandidate:
    work = ModuleWorkRef("concord", "class-1", "activity-1")
    return ConcordRouteCandidate(
        locator=RouteLocator(PDS2_SCHEMA, work, "route-1"),
        activity_id="activity-1",
        activity_title="Seminar Reflection",
        artifact_instance_id="artifact-1",
        artifact_page_id="page-1",
        page_number=1,
        page_kind="response",
        artifact_category="reflection",
        human_fallback="Seminar Reflection page 1",
        session_id="session-1",
        session_label="Period 2",
        group_id=None,
        group_label=None,
        replayed_occurrence=False,
    )


def _state() -> SimpleNamespace:
    return SimpleNamespace(
        require_actor=lambda: WorkflowActor(actor_id="teacher-1")
    )


def _patch_result_ui(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(menu_scan, "clear_screen", lambda: None)
    monkeypatch.setattr(menu_scan, "pause_for_user", lambda *args, **kwargs: None)
    monkeypatch.setattr(menu_scan, "print_menu_header", lambda *_args: None)
    monkeypatch.setattr(menu_scan, "print_navigation", lambda **_kwargs: None)


def test_failure_list_uses_teacher_readable_label_not_failure_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summary = _summary()
    captured: dict[str, Any] = {}
    monkeypatch.setattr(menu_scan, "list_routing_failures", lambda: (summary,))

    def choose(
        title: str,
        items: Any,
        labels: Any,
        *,
        help_text: str,
    ) -> Any:
        captured["labels"] = tuple(labels)
        raise menu_scan.CancelMenuAction

    monkeypatch.setattr(menu_scan, "select_one", choose)

    menu_scan._review(_state())

    assert captured["labels"] == (
        "seminar-period2.pdf — page 4 — QR/PDS2 route missing — unresolved",
    )
    assert "failure_machine_1" not in captured["labels"][0]


def test_action_screen_shows_teacher_context_and_only_safe_actions(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    review = _review(
        route_available=False,
        reason="retained_provenance_incomplete",
    )
    _patch_result_ui(monkeypatch)
    values = iter(["1"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(values))

    action = menu_scan._choose_routing_review_action(review)

    output = capsys.readouterr().out
    assert action == "defer"
    assert "Source: seminar-period2.pdf" in output
    assert "Physical page: 4" in output
    assert "Problem: QR/PDS2 route missing" in output
    assert "Activity: Not determined" in output
    assert "Route to an existing Concord page" not in output
    assert "1. Defer for later" in output
    assert "2. Technical details" in output
    assert "provenance is incomplete" in output


def test_resolved_failure_offers_only_technical_details(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    review = _review(
        route_available=False,
        latest_status="resolved",
        reason="already_resolved",
    )
    _patch_result_ui(monkeypatch)
    monkeypatch.setattr(menu_scan, "_show_routing_technical_details", lambda _r: None)
    values = iter(["1", "b"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(values))

    with pytest.raises(menu_scan.CancelMenuAction):
        menu_scan._choose_routing_review_action(review)

    output = capsys.readouterr().out
    assert "1. Technical details" in output
    assert "Defer for later" not in output
    assert "Route to an existing Concord page" not in output


def test_technical_details_contains_machine_identity_without_mutation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    review = _review()
    shown: list[tuple[str, tuple[str, ...]]] = []
    monkeypatch.setattr(
        menu_scan,
        "show_result",
        lambda title, lines: shown.append((title, tuple(lines))),
    )

    menu_scan._show_routing_technical_details(review)

    assert shown[0][0] == "Routing Review — Technical Details"
    text = "\n".join(shown[0][1])
    assert "Failure ID: failure_machine_1" in text
    assert "Source scan ID: scan_source_1" in text
    assert "Source SHA-256:" in text
    assert "Recorded route: none" in text


def test_defer_uses_default_note_and_requires_defer_confirmation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summary = _summary()
    review = _review(route_available=False, reason="known_other_module")
    observed: dict[str, Any] = {}
    monkeypatch.setattr(menu_scan, "list_routing_failures", lambda: (summary,))
    monkeypatch.setattr(menu_scan, "select_one", lambda *a, **k: summary)
    monkeypatch.setattr(menu_scan, "review_routing_failure", lambda _id: review)
    monkeypatch.setattr(menu_scan, "_choose_routing_review_action", lambda _r: "defer")

    def prompt(*args: Any, **kwargs: Any) -> str:
        observed["default"] = kwargs.get("default")
        return str(kwargs["default"])

    monkeypatch.setattr(menu_scan, "prompt_text", prompt)

    def confirm(title: str, expected: str, lines: Any) -> bool:
        observed["confirm"] = (title, expected, tuple(lines))
        return True

    monkeypatch.setattr(menu_scan, "confirm_write", confirm)

    def defer(failure_id: str, *, message: str, reviewer: Any) -> Any:
        observed["defer"] = (failure_id, message, reviewer.actor_id)
        return SimpleNamespace(resolution_status="deferred")

    monkeypatch.setattr(menu_scan, "defer_routing_failure", defer)
    monkeypatch.setattr(menu_scan, "show_result", lambda *a, **k: None)

    menu_scan._review(_state())

    assert observed["default"] == "Deferred for later teacher review."
    assert observed["confirm"][1] == "DEFER"
    confirm_text = "\n".join(observed["confirm"][2])
    assert "failure_machine_1" not in confirm_text
    assert observed["defer"] == (
        "failure_machine_1",
        "Deferred for later teacher review.",
        "teacher-1",
    )


def test_cancelled_defer_confirmation_performs_no_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summary = _summary()
    review = _review()
    monkeypatch.setattr(menu_scan, "list_routing_failures", lambda: (summary,))
    calls = 0

    def choose(*args: Any, **kwargs: Any) -> Any:
        nonlocal calls
        calls += 1
        if calls == 1:
            return summary
        raise menu_scan.CancelMenuAction

    monkeypatch.setattr(menu_scan, "select_one", choose)
    monkeypatch.setattr(menu_scan, "review_routing_failure", lambda _id: review)
    action_calls = 0

    def action(_review: RoutingFailureReview) -> str:
        nonlocal action_calls
        action_calls += 1
        if action_calls == 1:
            return "defer"
        raise menu_scan.CancelMenuAction

    monkeypatch.setattr(menu_scan, "_choose_routing_review_action", action)
    monkeypatch.setattr(menu_scan, "prompt_text", lambda *a, **k: "Teacher note")
    monkeypatch.setattr(menu_scan, "confirm_write", lambda *a, **k: False)
    monkeypatch.setattr(
        menu_scan,
        "defer_routing_failure",
        lambda *a, **k: pytest.fail("defer write must not occur"),
    )

    menu_scan._review(_state())


def test_route_confirmation_uses_exact_candidate_and_no_machine_route_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summary = _summary()
    review = _review()
    candidate = _candidate()
    observed: dict[str, Any] = {}
    monkeypatch.setattr(menu_scan, "list_routing_failures", lambda: (summary,))
    monkeypatch.setattr(menu_scan, "select_one", lambda *a, **k: summary)
    monkeypatch.setattr(menu_scan, "review_routing_failure", lambda _id: review)
    monkeypatch.setattr(menu_scan, "_choose_routing_review_action", lambda _r: "route")
    monkeypatch.setattr(
        menu_scan,
        "_select_routing_destination_candidate",
        lambda _review: candidate,
    )

    def prompt(title: str, label: str, **kwargs: Any) -> str:
        observed["prompt"] = (title, label, kwargs.get("default"))
        assert label == "Resolution note"
        return "Confirmed destination after paper review."

    monkeypatch.setattr(menu_scan, "prompt_text", prompt)

    def confirm(title: str, expected: str, lines: Any) -> bool:
        observed["confirm"] = (title, expected, tuple(lines))
        return True

    monkeypatch.setattr(menu_scan, "confirm_write", confirm)

    def resolve(
        failure_id: str,
        locator: RouteLocator,
        *,
        message: str,
        reviewer: Any,
    ) -> Any:
        observed["resolve"] = (failure_id, locator, message, reviewer.actor_id)
        return SimpleNamespace(resolution_action="route_selected")

    monkeypatch.setattr(menu_scan, "resolve_routing_failure_with_route", resolve)
    monkeypatch.setattr(menu_scan, "show_result", lambda *a, **k: None)

    menu_scan._review(_state())

    assert observed["confirm"][1] == "RESOLVE"
    confirm_text = "\n".join(observed["confirm"][2])
    assert "Destination: Period 2 — reflection — page 1" in confirm_text
    assert "route-1" not in confirm_text
    assert "artifact-1" not in confirm_text
    assert observed["resolve"] == (
        "failure_machine_1",
        candidate.locator,
        "Confirmed destination after paper review.",
        "teacher-1",
    )


def test_cancelled_route_confirmation_does_not_dispatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summary = _summary()
    review = _review()
    candidate = _candidate()
    select_calls = 0
    monkeypatch.setattr(menu_scan, "list_routing_failures", lambda: (summary,))

    def choose(*args: Any, **kwargs: Any) -> Any:
        nonlocal select_calls
        select_calls += 1
        if select_calls == 1:
            return summary
        raise menu_scan.CancelMenuAction

    monkeypatch.setattr(menu_scan, "select_one", choose)
    monkeypatch.setattr(menu_scan, "review_routing_failure", lambda _id: review)
    action_calls = 0

    def action(_review: RoutingFailureReview) -> str:
        nonlocal action_calls
        action_calls += 1
        if action_calls == 1:
            return "route"
        raise menu_scan.CancelMenuAction

    monkeypatch.setattr(menu_scan, "_choose_routing_review_action", action)
    monkeypatch.setattr(
        menu_scan,
        "_select_routing_destination_candidate",
        lambda _review: candidate,
    )
    monkeypatch.setattr(menu_scan, "prompt_text", lambda *a, **k: "Teacher note")
    monkeypatch.setattr(menu_scan, "confirm_write", lambda *a, **k: False)
    monkeypatch.setattr(
        menu_scan,
        "resolve_routing_failure_with_route",
        lambda *a, **k: pytest.fail("dispatch must not occur before RESOLVE"),
    )

    menu_scan._review(_state())


def test_destination_selector_preserves_exact_candidate_object(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    review = _review()
    candidate = _candidate()
    projection = SimpleNamespace(candidates=(candidate,), diagnostics=())
    selected_items: list[Any] = []
    monkeypatch.setattr(
        menu_scan,
        "list_routing_destination_classes",
        lambda _review: (SimpleNamespace(class_id="class-1", school_year="2026-2027"),),
    )
    monkeypatch.setattr(
        menu_scan,
        "routing_destination_class_label",
        lambda _item: "2026-2027 — class-1",
    )
    monkeypatch.setattr(
        menu_scan,
        "list_routing_destination_activities",
        lambda _review, _class_id: (
            SimpleNamespace(activity_id="activity-1", title="Seminar Reflection"),
        ),
    )
    monkeypatch.setattr(
        menu_scan,
        "routing_destination_activity_label",
        lambda _item: "Seminar Reflection — active",
    )
    monkeypatch.setattr(
        menu_scan,
        "project_routing_destination_candidates",
        lambda _review, _work: projection,
    )

    def choose(title: str, items: Any, labels: Any, *, help_text: str) -> Any:
        values = tuple(items)
        selected_items.append(values)
        return values[0]

    monkeypatch.setattr(menu_scan, "select_one", choose)

    selected = menu_scan._select_routing_destination_candidate(review)

    assert selected is candidate
    assert selected_items[-1][0] is candidate
    assert menu_scan._select_routing_destination(review) == candidate.locator
