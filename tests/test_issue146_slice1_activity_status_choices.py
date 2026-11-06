"""#146 Slice 1: Activity status choices, source and real menu/service guards.

Only synthetic Core/Concord workspaces are constructed. No live teacher data.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from issue140_slice2_fixtures import (
    ACTIVITY_ID,
    ACTOR,
    SOURCE_CLASS,
    build_workspace,
)
from pds_core.routing_models import ModuleWorkRef

import concord.menu_activity as menu
import concord.menu_prompts as prompts
from concord.menu_context import CancelMenuAction, MenuSessionContext
from concord.storage import list_work_snapshots
from concord.workflows import show_activity

_STATUSES = (
    "draft", "configured", "active", "completed", "cancelled", "archived"
)


def _work() -> ModuleWorkRef:
    return ModuleWorkRef("concord", SOURCE_CLASS, ACTIVITY_ID)


def _summary() -> SimpleNamespace:
    return SimpleNamespace(
        class_id="class-test", activity_id="activity-test", title="Discussion",
        status="draft", snapshot_revision=7,
    )


def test_status_chooser_exposes_only_native_values_and_current_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[tuple[str, tuple[str, ...], tuple[str, ...], str]] = []

    def choose(
        title: str,
        items: tuple[str, ...],
        labels: tuple[str, ...],
        *,
        help_text: str,
    ) -> str:
        seen.append((title, items, labels, help_text))
        return "configured"

    monkeypatch.setattr(menu, "select_one", choose)
    assert menu._choose_activity_status(_summary()) == "configured"
    assert len(seen) == 1
    title, items, labels, help_text = seen[0]
    assert items == _STATUSES
    assert len(labels) == len(_STATUSES)
    assert all(item.replace("_", " ").lower() in label.lower()
               for item, label in zip(items, labels, strict=True))
    assert labels[0].endswith("[current]")
    assert all(not label.endswith("[current]") for label in labels[1:])
    for fragment in (
        "Discussion", "class-test", "activity-test", "draft", "Snapshot: 7"
    ):
        assert fragment in title
    assert "teacher decision" in help_text
    assert "not a new transition" in help_text


def test_real_numbered_picker_rejects_unlisted_input_and_supports_back(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    inputs = iter(("99", "2"))
    monkeypatch.setattr("builtins.input", lambda _prompt: next(inputs))
    monkeypatch.setattr(prompts, "clear_screen", lambda: None)
    monkeypatch.setattr(prompts, "pause_for_user", lambda: None)
    assert menu._choose_activity_status(_summary()) == "configured"
    output = capsys.readouterr().out
    assert "Current status: draft" in output
    assert "Snapshot: 7" in output
    assert "1. Draft" in output
    assert "2. Configured" in output


def _wire(
    monkeypatch: pytest.MonkeyPatch,
    root: Path,
    library: Any,
    *,
    selected: str = "configured",
    confirmed: bool = True,
) -> tuple[list[tuple[str, str, tuple[str, ...]]], list[tuple[Any, ...]], list[str]]:
    review: list[tuple[str, str, tuple[str, ...]]] = []
    receipts: list[tuple[Any, ...]] = []
    errors: list[str] = []
    monkeypatch.setattr(menu, "resolve_read_workspace_root", lambda: root)
    monkeypatch.setattr(menu, "load_menu_standards_library", lambda _root: library)
    monkeypatch.setattr(menu, "select_one", lambda *_args, **_kwargs: selected)

    def confirm(title: str, token: str, lines: tuple[str, ...]) -> bool:
        review.append((title, token, lines))
        return confirmed

    monkeypatch.setattr(menu, "confirm_write", confirm)
    monkeypatch.setattr(menu, "show_result", lambda *args: receipts.append(args))
    monkeypatch.setattr(
        menu,
        "handle_write_error",
        lambda error, **_kwargs: errors.append(str(error)),
    )
    return review, receipts, errors


@pytest.mark.parametrize("orientation", ("mixed", "standards_based", "evidence_only"))
def test_status_commit_through_real_menu_and_canonical_service(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    orientation: str,
) -> None:
    fixture = build_workspace(tmp_path, orientation=orientation)
    before = show_activity(SOURCE_CLASS, ACTIVITY_ID, workspace_root=fixture.root)
    snapshots = list_work_snapshots(fixture.root, _work())
    review, receipts, errors = _wire(
        monkeypatch, fixture.root, fixture.standards,
    )
    menu._update_activity_field(
        before.summary, MenuSessionContext(actor=ACTOR), "status"
    )
    assert not errors
    assert len(review) == len(receipts) == 1
    assert review[0][0:2] == ("Edit Activity", "UPDATE")
    review_text = "\n".join(review[0][2])
    assert "Current status: draft" in review_text
    assert "Requested status: configured" in review_text
    assert "Snapshot:" in review_text
    assert "No packets, returned evidence, Scores" in review_text
    after = show_activity(SOURCE_CLASS, ACTIVITY_ID, workspace_root=fixture.root)
    assert after.summary.status == "configured"
    assert after.summary.snapshot_revision == before.summary.snapshot_revision + 1
    assert len(list_work_snapshots(fixture.root, _work())) == len(snapshots) + 1
    assert "Status: draft -> configured" in str(receipts)
    assert after.standards_profile_id == before.standards_profile_id
    assert after.focus_standard_ids == before.focus_standard_ids


def test_selecting_current_status_is_zero_write_and_no_confirmation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = build_workspace(tmp_path, orientation="mixed")
    before = show_activity(SOURCE_CLASS, ACTIVITY_ID, workspace_root=fixture.root)
    snapshots = list_work_snapshots(fixture.root, _work())
    review, receipts, errors = _wire(
        monkeypatch, fixture.root, fixture.standards, selected="draft",
    )
    monkeypatch.setattr(
        menu, "update_activity", lambda *_args, **_kwargs: pytest.fail("No-op wrote")
    )
    monkeypatch.setattr(
        menu, "_load_activity_context", lambda *_args, **_kwargs: pytest.fail(
            "No-op loaded a write context"
        )
    )
    menu._update_activity_field(
        before.summary, MenuSessionContext(actor=ACTOR), "status"
    )
    assert not review and not errors
    assert "No changes were needed" in str(receipts)
    assert "Status remains: draft" in str(receipts)
    assert list_work_snapshots(fixture.root, _work()) == snapshots


def test_cancel_from_choice_or_confirmation_never_writes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = build_workspace(tmp_path, orientation="mixed")
    before = show_activity(SOURCE_CLASS, ACTIVITY_ID, workspace_root=fixture.root)
    snapshots = list_work_snapshots(fixture.root, _work())
    review, receipts, errors = _wire(
        monkeypatch, fixture.root, fixture.standards, confirmed=False,
    )
    monkeypatch.setattr(
        menu, "update_activity", lambda *_args, **_kwargs: pytest.fail("Canceled write")
    )
    menu._update_activity_field(
        before.summary, MenuSessionContext(actor=ACTOR), "status"
    )
    assert len(review) == 1 and not receipts and not errors
    assert list_work_snapshots(fixture.root, _work()) == snapshots



def test_back_from_status_picker_is_zero_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = build_workspace(tmp_path, orientation="mixed")
    before = show_activity(SOURCE_CLASS, ACTIVITY_ID, workspace_root=fixture.root)
    snapshots = list_work_snapshots(fixture.root, _work())
    review, receipts, errors = _wire(monkeypatch, fixture.root, fixture.standards)

    def back(*_args: object, **_kwargs: object) -> str:
        raise CancelMenuAction

    monkeypatch.setattr(menu, "select_one", back)
    monkeypatch.setattr(
        menu, "update_activity", lambda *_args, **_kwargs: pytest.fail("Back wrote")
    )
    menu._update_activity_field(
        before.summary, MenuSessionContext(actor=ACTOR), "status"
    )
    assert not review and not receipts and not errors
    assert list_work_snapshots(fixture.root, _work()) == snapshots


def test_missing_canonical_standards_aborts_before_activity_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = build_workspace(tmp_path, orientation="mixed")
    before = show_activity(SOURCE_CLASS, ACTIVITY_ID, workspace_root=fixture.root)
    snapshots = list_work_snapshots(fixture.root, _work())
    review, receipts, errors = _wire(monkeypatch, fixture.root, None)
    monkeypatch.setattr(
        menu, "update_activity", lambda *_args, **_kwargs: pytest.fail(
            "No canonical Standards must abort before write"
        ),
    )
    menu._update_activity_field(
        before.summary, MenuSessionContext(actor=ACTOR), "status"
    )
    assert len(review) == 1 and not receipts and errors
    assert "Core Standards Library" in errors[0]
    assert list_work_snapshots(fixture.root, _work()) == snapshots
