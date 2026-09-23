from __future__ import annotations

from types import SimpleNamespace

import pytest

import concord.menu_artifact as artifact_module
import concord.menu_scoring as scoring_module
from concord.menu_context import MenuSessionContext
from concord.workflows import ActivitySummary
from concord.workflows.artifact_assembly import (
    ArtifactAssemblyNotFoundError,
    AssemblyPageSelection,
)


def _activity() -> ActivitySummary:
    return ActivitySummary(
        class_id="class-1",
        activity_id="activity-1",
        title="Issue 105 Activity",
        status="active",
        scoring_orientation="mixed",
        session_count=1,
        group_count=1,
        snapshot_revision=9,
    )


def _inputs(monkeypatch: pytest.MonkeyPatch, values: tuple[str, ...]) -> None:
    answers = iter(values)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))


def test_shared_open_returned_work_uses_exact_selection_without_writes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    activity = _activity()
    artifact = SimpleNamespace(artifact_instance_id="artifact-1")
    selection = (
        AssemblyPageSelection(
            artifact_page_id="page-1",
            scan_reference_id="scan-ref-2",
        ),
    )
    opened: list[tuple[str, str, str, tuple[AssemblyPageSelection, ...]]] = []
    shown: list[tuple[str, tuple[str, ...]]] = []

    monkeypatch.setattr(artifact_module, "_latest", lambda selected: selected)
    monkeypatch.setattr(
        artifact_module,
        "_choose_artifact",
        lambda _activity, *, title: artifact,
    )
    monkeypatch.setattr(
        artifact_module,
        "_assembly_selections",
        lambda _activity, _artifact: selection,
    )

    def _open(
        class_id: str,
        activity_id: str,
        artifact_instance_id: str,
        *,
        selections: tuple[AssemblyPageSelection, ...] = (),
    ) -> object:
        opened.append((class_id, activity_id, artifact_instance_id, selections))
        return SimpleNamespace(
            artifact_instance_id=artifact_instance_id,
            page_count=1,
        )

    monkeypatch.setattr(
        artifact_module,
        "open_returned_artifact_evidence",
        _open,
    )
    monkeypatch.setattr(
        artifact_module,
        "assemble_returned_artifact",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("Open returned work must not assemble")
        ),
    )
    monkeypatch.setattr(
        artifact_module,
        "confirm_write",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("Open returned work must not confirm a write")
        ),
    )
    monkeypatch.setattr(
        artifact_module,
        "show_result",
        lambda title, lines: shown.append((title, tuple(lines))),
    )

    artifact_module.open_returned_work(activity)

    assert opened == [("class-1", "activity-1", "artifact-1", selection)]
    assert shown == [
        (
            "Returned Work Opened",
            (
                "Returned work opened in your default PDF viewer.",
                "Opening this evidence did not Review, Moderate, or Score the work.",
            ),
        )
    ]
    rendered = "\n".join(shown[0][1])
    assert "attachments/" not in rendered
    assert "manifest.json" not in rendered
    assert "SHA" not in rendered
    assert "scan-ref-2" not in rendered


def test_shared_open_returned_work_guides_missing_assembly_without_writing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    activity = _activity()
    artifact = SimpleNamespace(artifact_instance_id="artifact-1")
    shown: list[tuple[str, tuple[str, ...]]] = []

    monkeypatch.setattr(artifact_module, "_latest", lambda selected: selected)
    monkeypatch.setattr(
        artifact_module,
        "_choose_artifact",
        lambda _activity, *, title: artifact,
    )
    monkeypatch.setattr(
        artifact_module,
        "_assembly_selections",
        lambda *_args, **_kwargs: (),
    )
    monkeypatch.setattr(
        artifact_module,
        "open_returned_artifact_evidence",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            ArtifactAssemblyNotFoundError(
                "This exact returned work has not been assembled yet. "
                "Use Assemble returned work first."
            )
        ),
    )
    monkeypatch.setattr(
        artifact_module,
        "assemble_returned_artifact",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("Open must never assemble implicitly")
        ),
    )
    monkeypatch.setattr(
        artifact_module,
        "show_result",
        lambda title, lines: shown.append((title, tuple(lines))),
    )

    artifact_module.open_returned_work(activity)

    assert shown == [
        (
            "Open Returned Work",
            (
                "This exact returned work has not been assembled yet. "
                "Use Assemble returned work first.",
            ),
        )
    ]


@pytest.mark.parametrize(
    ("menu_name", "module"),
    (
        ("launch_collect_work_menu", artifact_module),
        ("launch_review_work_menu", artifact_module),
        ("launch_score_menu", scoring_module),
    ),
)
def test_collect_review_and_score_expose_open_returned_work(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    menu_name: str,
    module: object,
) -> None:
    activity = _activity()
    if module is scoring_module:
        monkeypatch.setattr(scoring_module, "_latest", lambda selected: selected)
    _inputs(monkeypatch, ("b",))
    monkeypatch.setattr(module, "clear_screen", lambda: None)

    getattr(module, menu_name)(activity, MenuSessionContext())

    output = capsys.readouterr().out
    assert "O. Open returned work" in output


@pytest.mark.parametrize(
    ("surface", "module", "menu_name"),
    (
        ("collect", artifact_module, "launch_collect_work_menu"),
        ("review", artifact_module, "launch_review_work_menu"),
        ("score", scoring_module, "launch_score_menu"),
    ),
)
def test_open_returned_work_routes_through_one_shared_action(
    monkeypatch: pytest.MonkeyPatch,
    surface: str,
    module: object,
    menu_name: str,
) -> None:
    activity = _activity()
    calls: list[str] = []

    if module is scoring_module:
        monkeypatch.setattr(scoring_module, "_latest", lambda selected: selected)
        monkeypatch.setattr(
            scoring_module,
            "open_returned_work",
            lambda selected: calls.append(selected.activity_id),
        )
        monkeypatch.setattr(
            scoring_module,
            "_record_score",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                AssertionError("Open evidence must not record a Score")
            ),
        )
        monkeypatch.setattr(
            scoring_module,
            "_revise_score",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                AssertionError("Open evidence must not revise a Score")
            ),
        )
    else:
        monkeypatch.setattr(
            artifact_module,
            "open_returned_work",
            lambda selected: calls.append(selected.activity_id),
        )
        if surface == "review":
            monkeypatch.setattr(
                artifact_module,
                "_launch_review_menu",
                lambda *_args, **_kwargs: (_ for _ in ()).throw(
                    AssertionError("Open evidence must not create a Review")
                ),
            )
            monkeypatch.setattr(
                artifact_module,
                "_launch_moderation_menu",
                lambda *_args, **_kwargs: (_ for _ in ()).throw(
                    AssertionError("Open evidence must not create Moderation")
                ),
            )

    _inputs(monkeypatch, ("o", "b"))
    monkeypatch.setattr(module, "clear_screen", lambda: None)

    getattr(module, menu_name)(activity, MenuSessionContext())

    assert calls == ["activity-1"]


@pytest.mark.parametrize(
    ("menu_name", "module"),
    (
        ("launch_collect_work_menu", artifact_module),
        ("launch_review_work_menu", artifact_module),
        ("launch_score_menu", scoring_module),
    ),
)
def test_back_navigation_does_not_open_returned_work(
    monkeypatch: pytest.MonkeyPatch,
    menu_name: str,
    module: object,
) -> None:
    activity = _activity()

    if module is scoring_module:
        monkeypatch.setattr(scoring_module, "_latest", lambda selected: selected)
        monkeypatch.setattr(
            scoring_module,
            "open_returned_work",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                AssertionError("Back must not open evidence")
            ),
        )
    else:
        monkeypatch.setattr(
            artifact_module,
            "open_returned_work",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                AssertionError("Back must not open evidence")
            ),
        )

    _inputs(monkeypatch, ("b",))
    monkeypatch.setattr(module, "clear_screen", lambda: None)

    getattr(module, menu_name)(activity, MenuSessionContext())
