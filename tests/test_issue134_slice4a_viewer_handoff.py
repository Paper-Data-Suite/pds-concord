"""Slice 4A: an OS-accepted viewer request is not verified display."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import concord.menu_packet_generation as packet_menu
import concord.menu_student_feedback as feedback_menu


def _shown(monkeypatch: pytest.MonkeyPatch, module: object) -> list[tuple[str, ...]]:
    results: list[tuple[str, ...]] = []
    monkeypatch.setattr(
        module,
        "show_result",
        lambda _title, lines: results.append(tuple(lines)),
    )
    return results


def test_packet_open_only_reports_viewer_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    activity = SimpleNamespace(class_id="class-a", activity_id="activity-a")
    instance = SimpleNamespace(packet_instance_id="instance-a")
    opened: list[str] = []
    monkeypatch.setattr(
        packet_menu, "_choose_ready_instance", lambda *_a, **_k: instance
    )
    monkeypatch.setattr(
        packet_menu, "_teacher_instance_labels", lambda *_a: ("Group A",)
    )
    monkeypatch.setattr(
        packet_menu,
        "open_rendered_packet_output",
        lambda _class, _activity, identifier: opened.append(identifier),
    )
    shown = _shown(monkeypatch, packet_menu)
    packet_menu._open_ready_packet(activity)
    assert opened == ["instance-a"]
    text = " ".join(shown[0]).casefold()
    assert "requested" in text
    assert "does not prove" in text
    assert "opened:" not in text
    assert "instance-a" not in text


def test_packet_folder_open_is_not_display_confirmation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    activity = SimpleNamespace(class_id="class-a", activity_id="activity-a")
    instance = SimpleNamespace(packet_instance_id="instance-b")
    monkeypatch.setattr(
        packet_menu, "_ready_packet_instances", lambda *_a, **_k: (instance,)
    )
    selected: list[str] = []
    monkeypatch.setattr(
        packet_menu,
        "open_rendered_packet_output_directory",
        lambda _c, _a, identifier: selected.append(identifier),
    )
    shown = _shown(monkeypatch, packet_menu)
    packet_menu._open_ready_folder(activity)
    assert selected == ["instance-b"]
    assert "requested" in " ".join(shown[0]).casefold()
    assert "opened the verified" not in " ".join(shown[0]).casefold()


@pytest.mark.parametrize(
    ("action", "expected"),
    (("_open_existing_folder", "folder"), ("_open_existing_print_pdf", "pdf")),
)
def test_feedback_open_never_claims_viewer_display(
    monkeypatch: pytest.MonkeyPatch,
    action: str,
    expected: str,
) -> None:
    folder = Path("synthetic-feedback")
    monkeypatch.setattr(feedback_menu, "_existing_directory", lambda: folder)
    opened: list[tuple[str, Path]] = []
    verified = SimpleNamespace(selected_count=3, combined_page_count=4)
    monkeypatch.setattr(
        feedback_menu,
        "open_student_feedback_distribution_directory",
        lambda path: opened.append(("folder", Path(path))) or verified,
    )
    monkeypatch.setattr(
        feedback_menu,
        "open_student_feedback_distribution_print_pdf",
        lambda path: opened.append(("pdf", Path(path))) or verified,
    )
    shown = _shown(monkeypatch, feedback_menu)
    getattr(feedback_menu, action)()
    assert opened == [(expected, folder)]
    assert "requested" in " ".join(shown[0]).casefold()
    assert "opened." not in " ".join(shown[0]).casefold()


def test_all_three_verified_openers_continue_to_delegate_to_core() -> None:
    paths = (
        "concord/workflows/artifact_evidence_opening.py",
        "concord/workflows/rendered_output.py",
        "concord/workflows/student_feedback_distribution_opening.py",
    )
    for name in paths:
        text = Path(name).read_text(encoding="utf-8")
        assert "from pds_core.local_open import LocalOpenError, open_local_path" in text
        assert "open_local_path(" in text
        assert "os.startfile" not in text
        assert "xdg-open" not in text
