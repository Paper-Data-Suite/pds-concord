"""#140 Slice 3B: genuine Artifact menu/service Standards guards, no writes.

This retrospective baseline tests repaired and pending context boundaries.
No actual teacher judgments, attribution, Score, or paper scans are created.
"""

from __future__ import annotations

from functools import partial
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from issue140_slice2_fixtures import ACTIVITY_ID, ACTOR, SOURCE_CLASS, build_workspace
from pds_core.routing_models import ModuleWorkRef
from pds_core.standards import write_workspace_standards_library

import concord.menu_artifact as menu
import concord.menu_artifact_write_context as authority
from concord.models import EvidenceReference, PrivacyPolicy, SubjectReference
from concord.storage import list_work_snapshots, load_current_record_graph
from concord.workflows import (
    add_artifact_author,
    add_artifact_subject,
    show_activity,
)
from concord.workflows.artifact_review import add_artifact_review
from concord.workflows.moderation import add_moderation_record

ARTIFACT_ID = "issue140-nonexistent-evidence"


def _work() -> ModuleWorkRef:
    return ModuleWorkRef("concord", SOURCE_CLASS, ACTIVITY_ID)


def _menu_scaffold(monkeypatch: pytest.MonkeyPatch, *, current: Any) -> SimpleNamespace:
    """Replace only menu prompting/choice; never replace guarded services."""
    artifact = SimpleNamespace(
        artifact_instance_id=ARTIFACT_ID,
        snapshot_revision=current.snapshot_revision,
        artifact_status="planned",
        returned_required_page_count=0,
        required_return_page_count=1,
        current_author_count=0,
        current_subject_count=0,
    )
    monkeypatch.setattr(menu, "_latest", lambda _activity: current)
    monkeypatch.setattr(menu, "_choose_artifact", lambda *a, **k: artifact)
    monkeypatch.setattr(menu, "prompt_text", lambda *a, **k: "issue140-probe-id")
    monkeypatch.setattr(menu, "confirm_write", lambda *a, **k: True)
    monkeypatch.setattr(menu, "show_result", lambda *a, **k: None)
    return artifact


def _exercise(
    kind: str,
    activity: Any,
    root: Path,
    monkeypatch: pytest.MonkeyPatch,
    captured: list[Any],
) -> None:
    """Invoke the existing handler; adapt only its workspace-root boundary."""
    monkeypatch.setattr(
        authority,
        "resolve_read_workspace_root",
        lambda explicit_root=None: (
            root if explicit_root is None else Path(explicit_root)
        ),
    )
    artifact = _menu_scaffold(monkeypatch, current=activity)
    state = menu.MenuSessionContext(actor=ACTOR)
    if kind == "author":
        monkeypatch.setattr(
            menu,
            "_choose_author_semantics",
            lambda *a, **k: (
                None,
                "teacher_author",
                "proposed",
                "manual",
                None,
                None,
                None,
            ),
        )
        real = add_artifact_author
        menu_name = "add_artifact_author"
        handler = partial(menu._add_author, activity, state)
    elif kind == "subject":
        reference = SubjectReference(
            subject_kind="core_student",
            owning_system="core",
            subject_id="issue140-synthetic-student-01",
        )
        monkeypatch.setattr(
            menu,
            "_choose_subject_semantics",
            lambda *a, **k: (
                reference,
                "observed_participant",
                "proposed",
                "manual",
                None,
            ),
        )
        real = add_artifact_subject
        menu_name = "add_artifact_subject"
        handler = partial(menu._add_subject, activity, state)
    elif kind == "review":
        monkeypatch.setattr(
            menu,
            "show_artifact",
            lambda *a, **k: SimpleNamespace(
                privacy_classification="teacher_restricted"
            ),
        )
        monkeypatch.setattr(
            menu,
            "_review_values",
            lambda: (
                "readable",
                "complete",
                "correctly_filed",
                "undetermined",
                "undetermined",
                "appropriate",
                "relevant",
                "not_required",
                "not_ready",
                "needs_attention",
                "synthetic context-only probe",
                PrivacyPolicy(classification="teacher_restricted"),
            ),
        )
        real = add_artifact_review
        menu_name = "add_artifact_review"
        handler = partial(menu._record_review_selected, activity, artifact, state)
    elif kind == "moderation":
        monkeypatch.setattr(
            menu,
            "_choose_moderation_evidence",
            lambda *a, **k: EvidenceReference(
                evidence_kind="artifact_instance",
                owning_system="concord",
                record_id=ARTIFACT_ID,
            ),
        )
        monkeypatch.setattr(
            menu,
            "_choose_moderation_subjects",
            lambda *a, **k: (),
        )
        monkeypatch.setattr(
            menu,
            "_moderation_values",
            lambda: (
                "pending",
                "context_only",
                "synthetic context-only probe",
                None,
                PrivacyPolicy(classification="teacher_restricted"),
            ),
        )
        real = add_moderation_record
        menu_name = "add_moderation_record"
        handler = partial(menu._record_moderation, activity, state)
    else:
        raise AssertionError("Unsupported witness")

    def actual_service(request: Any, **kwargs: Any) -> Any:
        captured.append(request)
        if (
            "workspace_root" in kwargs
            and Path(kwargs["workspace_root"]).resolve() != root.resolve()
        ):
            raise AssertionError("Menu passed a different Core workspace")
        kwargs.setdefault("workspace_root", root)
        return real(request, **kwargs)

    monkeypatch.setattr(menu, menu_name, actual_service)
    handler()


@pytest.mark.parametrize("kind", ("author", "subject", "review", "moderation"))
def test_mixed_teacher_menu_reaches_real_guard_before_missing_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    fixture = build_workspace(tmp_path, orientation="mixed")
    write_workspace_standards_library(fixture.root, fixture.standards)
    activity = show_activity(
        SOURCE_CLASS, ACTIVITY_ID, workspace_root=fixture.root
    ).summary
    before = load_current_record_graph(
        fixture.root, _work(), standards_library=fixture.standards
    ).graph
    snapshots = list_work_snapshots(fixture.root, _work())
    captured: list[Any] = []
    # The handler is invoked with a real selected Activity and the real service;
    # its selected Artifact is absent to verify valid context reaches identity refusal.
    # All four reviewed menu operations now forward canonical authority.
    expected_failure = "Artifact is not available:"
    with pytest.raises(Exception, match=expected_failure):
        _exercise(kind, activity, fixture.root, monkeypatch, captured)
    assert len(captured) == 1
    service = {
        "author": add_artifact_author,
        "subject": add_artifact_subject,
        "review": add_artifact_review,
        "moderation": add_moderation_record,
    }[kind]
    # Same valid Core activity and request cross the guard when the actual
    # Standards library is forwarded, then fail on the deliberately absent
    # artifact/evidence target. Distinguishes source failure from a bad fixture.
    with pytest.raises(Exception) as with_context:
        service(
            captured[0],
            workspace_root=fixture.root,
            standards_library=fixture.standards,
        )
    assert "standards_library" not in str(with_context.value)
    # The authoritative Activity graph remains valid and no fabricated Artifact
    # or score is introduced to force the menu operation through validation.
    assert list_work_snapshots(fixture.root, _work()) == snapshots
    assert (
        load_current_record_graph(
            fixture.root, _work(), standards_library=fixture.standards
        ).graph
        == before
    )


def test_neutral_activity_missing_artifact_fails_for_identity_not_standards(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = build_workspace(tmp_path, orientation="evidence_only")
    write_workspace_standards_library(fixture.root, fixture.standards)
    activity = show_activity(
        SOURCE_CLASS, ACTIVITY_ID, workspace_root=fixture.root
    ).summary
    snapshots = list_work_snapshots(fixture.root, _work())
    captured: list[Any] = []
    with pytest.raises(Exception) as err:
        _exercise("author", activity, fixture.root, monkeypatch, captured)
    assert len(captured) == 1
    assert "standards_library" not in str(err.value)
    assert "Artifact" in str(err.value)
    assert list_work_snapshots(fixture.root, _work()) == snapshots


@pytest.mark.parametrize("orientation", ("mixed", "evidence_only"))
def test_routine_review_read_does_not_require_standards_to_report_absent_artifact(
    tmp_path: Path, orientation: str
) -> None:
    from concord.workflows.artifact_routine_review import (
        inspect_artifact_routine_review,
    )

    fixture = build_workspace(tmp_path, orientation=orientation)
    write_workspace_standards_library(fixture.root, fixture.standards)
    before = list_work_snapshots(fixture.root, _work())
    with pytest.raises(Exception) as error:
        inspect_artifact_routine_review(
            SOURCE_CLASS,
            ACTIVITY_ID,
            ARTIFACT_ID,
            workspace_root=fixture.root,
        )
    assert "standards_library" not in str(error.value)
    assert list_work_snapshots(fixture.root, _work()) == before
