"""#151 Slice 3B: distinguish and open verified saved assembly versions.

Isolated synthetic menu tests. Core owns the Windows viewer and source custody;
these witnesses never create a classroom workspace or open a real PDF.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import concord.menu_artifact as menu
from concord.menu_context import CancelMenuAction
from concord.workflows import ConcordWorkflowConflictError
from concord.workflows.artifact_assembly import (
    ArtifactAssemblyIntegrityError,
    AssemblyPageSelection,
)
from concord.workflows.errors import ConcordWorkflowOpenError
from concord.workflows.models import ActivitySummary
from concord.workflows.returned_assembly_versions import VerifiedAssemblyVersion


def _activity() -> ActivitySummary:
    return ActivitySummary(
        class_id="synthetic-class",
        activity_id="synthetic-activity",
        title="Synthetic Seminar",
        status="active",
        scoring_orientation="mixed",
        session_count=1,
        group_count=6,
        snapshot_revision=19,
    )


def _version(
    copy: str,
    when: str = "2026-11-20T14:06:00+00:00",
    *,
    evidence: str = "none",
) -> VerifiedAssemblyVersion:
    return VerifiedAssemblyVersion(
        assembly_id=f"assembly_{copy * 32}",
        assembled_at=when,
        page_count=2,
        selections=(
            AssemblyPageSelection(
                artifact_page_id="page-synthetic-1",
                scan_reference_id=f"scan-synthetic-{copy}",
            ),
        ),
        snapshot_revision=19,
        newer_evidence_status=evidence,
    )


@pytest.mark.parametrize(
    "when_b",
    (
        "2026-11-20T14:06:00+00:00",  # genuinely identical precise instant
        "2026-11-20T14:06:29+00:00",  # distinct time, same displayed minute
    ),
)
def test_indistinguishable_history_labels_get_stable_nonchronological_copy_numbers(
    when_b: str,
) -> None:
    versions = (_version("a"), _version("b", when_b))
    labels = menu._saved_assembly_version_labels(versions)
    assert len(labels) == 2
    assert labels[0] != labels[1]
    assert "saved copy 1 of 2" in labels[0]
    assert "saved copy 2 of 2" in labels[1]
    assert all("display order, not chronological" in label for label in labels)
    assert all(
        "assembly_" not in label and "scan-synthetic" not in label for label in labels
    )


def test_unique_saved_history_labels_remain_original_and_newer_evidence_visible() -> (
    None
):
    versions = (
        _version("a", evidence="newer"),
        _version("b", "2026-11-19T14:06:00+00:00"),
    )
    labels = menu._saved_assembly_version_labels(versions)
    assert "Newer routed evidence available" in labels[0]
    assert "saved copy" not in labels[0] + labels[1]
    assert labels[0] != labels[1]


def _arrange(
    monkeypatch: pytest.MonkeyPatch,
    versions: tuple[VerifiedAssemblyVersion, ...],
) -> tuple[
    list[tuple[tuple[object, ...], dict[str, object]]],
    list[tuple[str, tuple[str, ...]]],
]:
    opened: list[tuple[tuple[object, ...], dict[str, object]]] = []
    shown: list[tuple[str, tuple[str, ...]]] = []
    activity = _activity()
    choice = SimpleNamespace(
        label="Cluster 2 | Session 1",
        summary=SimpleNamespace(artifact_instance_id="work-b"),
    )
    monkeypatch.setattr(menu, "_latest", lambda _activity: activity)
    monkeypatch.setattr(menu, "_choose_artifact_choice", lambda *_a, **_kw: choice)

    def load(
        class_id: str, activity_id: str, artifact_id: str, **kw: object
    ) -> tuple[VerifiedAssemblyVersion, ...]:
        assert (class_id, activity_id, artifact_id) == (
            "synthetic-class",
            "synthetic-activity",
            "work-b",
        )
        assert kw == {"expected_snapshot_revision": 19}
        return versions

    monkeypatch.setattr(menu, "list_verified_assembly_versions", load)
    monkeypatch.setattr(
        menu,
        "open_returned_artifact_evidence",
        lambda *args, **kw: opened.append((args, kw)),
    )
    monkeypatch.setattr(
        menu,
        "show_result",
        lambda title, lines: shown.append((title, tuple(lines))),
    )
    monkeypatch.setattr(
        menu,
        "assemble_returned_artifact",
        lambda *_a, **_kw: pytest.fail("history must never assemble"),
    )
    return opened, shown


def test_ambiguous_display_opens_only_chosen_exact_saved_lineage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    versions = (_version("a"), _version("b"))
    opened, shown = _arrange(monkeypatch, versions)

    def choose(
        _title: str, items: object, labels: tuple[str, ...], **_kw: object
    ) -> object:
        assert items is versions
        assert "saved copy 1 of 2" in labels[0]
        assert "saved copy 2 of 2" in labels[1]
        return versions[1]

    monkeypatch.setattr(menu, "select_one", choose)
    menu.open_verified_assembly_version(_activity())
    assert len(opened) == 1
    args, kwargs = opened[0]
    assert args == ("synthetic-class", "synthetic-activity", "work-b")
    assert kwargs == {
        "selections": versions[1].selections,
        "expected_snapshot_revision": 19,
    }
    assert len(shown) == 1
    receipt = " ".join(shown[0][1])
    assert "saved copy 2 of 2" in receipt
    assert "viewer" in receipt.casefold()
    assert "display cannot be confirmed" in receipt.casefold()
    assert "not established" in receipt.casefold()
    assert "assembly_" not in receipt and "scan-synthetic" not in receipt


def test_untrusted_selection_cannot_reach_verified_opener(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    versions = (_version("a"),)
    opened, shown = _arrange(monkeypatch, versions)
    monkeypatch.setattr(menu, "select_one", lambda *_a, **_kw: _version("b"))
    menu.open_verified_assembly_version(_activity())
    assert not opened
    assert len(shown) == 1
    assert "changed" in " ".join(shown[0][1]).casefold()


def test_equivalent_but_reconstructed_selection_cannot_bypass_exact_menu_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    versions = (_version("a"),)
    opened, shown = _arrange(monkeypatch, versions)
    monkeypatch.setattr(menu, "select_one", lambda *_a, **_kw: _version("a"))
    menu.open_verified_assembly_version(_activity())
    assert opened == []
    assert "changed" in " ".join(shown[0][1]).casefold()


def test_no_saved_versions_reports_assembly_next_step_without_open(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    opened, shown = _arrange(monkeypatch, ())
    monkeypatch.setattr(
        menu, "select_one", lambda *_a, **_kw: pytest.fail("no chooser")
    )
    menu.open_verified_assembly_version(_activity())
    assert not opened
    assert len(shown) == 1
    assert "Assemble returned work" in " ".join(shown[0][1])


def test_canceling_history_choice_is_a_no_open_action(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    opened, shown = _arrange(monkeypatch, (_version("a"),))
    monkeypatch.setattr(
        menu, "select_one", lambda *_a, **_kw: (_ for _ in ()).throw(CancelMenuAction())
    )
    menu.open_verified_assembly_version(_activity())
    assert not opened
    assert not shown


@pytest.mark.parametrize(
    ("error", "expected"),
    (
        (
            ArtifactAssemblyIntegrityError("unsafe /secret/retained/scan-id"),
            "needs recovery",
        ),
        (ConcordWorkflowConflictError("old /secret/retained/scan-id"), "changed"),
    ),
)
def test_untrusted_history_or_stale_snapshot_never_launches_viewer(
    monkeypatch: pytest.MonkeyPatch,
    error: Exception,
    expected: str,
) -> None:
    opened, shown = _arrange(monkeypatch, (_version("a"),))
    monkeypatch.setattr(
        menu,
        "list_verified_assembly_versions",
        lambda *_a, **_kw: (_ for _ in ()).throw(error),
    )
    monkeypatch.setattr(
        menu, "select_one", lambda *_a, **_kw: pytest.fail("no chooser")
    )
    menu.open_verified_assembly_version(_activity())
    assert not opened
    assert len(shown) == 1
    rendered = " ".join(shown[0][1]).casefold()
    assert expected in rendered
    assert "/secret/" not in rendered and "scan-id" not in rendered


def test_core_viewer_failure_does_not_claim_pdf_display(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    versions = (_version("a"),)
    opened, shown = _arrange(monkeypatch, versions)
    monkeypatch.setattr(menu, "select_one", lambda _title, items, *_a, **_kw: items[0])
    monkeypatch.setattr(
        menu,
        "open_returned_artifact_evidence",
        lambda *_a, **_kw: (_ for _ in ()).throw(
            ConcordWorkflowOpenError("private /secret/file.pdf")
        ),
    )
    menu.open_verified_assembly_version(_activity())
    assert opened == []
    assert "default PDF application" in " ".join(shown[0][1])
    assert "/secret/" not in " ".join(shown[0][1])
