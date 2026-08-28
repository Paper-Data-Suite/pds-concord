from __future__ import annotations

import argparse
import inspect
from datetime import datetime, timezone
from pathlib import Path
from typing import cast

import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.classes import write_class_roster
from pds_core.rosters import create_roster
from pds_core.workspace import ensure_workspace_root

import concord.cli_app.handlers.publication as publication_handler
import concord.menu_activity as menu_activity
import concord.menu_publication as menu_publication
from concord.academic_result_manifest import RevisionReason
from concord.academic_result_manifest_generation import (
    GenerateAcademicResultManifestRequest,
    list_academic_result_manifest_revisions,
    manifest_preview_summary,
    preview_academic_result_manifest,
)
from concord.academic_result_publication import (
    ConcordAcademicResultPublicationConflictError,
    ConcordAcademicResultPublicationPartialSuccessError,
    PublicationPartialSuccessState,
)
from concord.academic_work_registration import register_concord_academic_work
from concord.cli import build_parser, main
from concord.menu_context import MenuSessionContext
from concord.models import PrivacyPolicy, ScoreTargetReference, ScoringScaleLevel
from concord.pds_contract import CONCORD_MODULE_ID
from concord.workflows import (
    ActivitySummary,
    AddScoreRequest,
    CreateActivityContextRequest,
    CreateCriterionSetRequest,
    CreateScoringScaleRequest,
    CriterionSpec,
    SelectActivityCriterionSetsRequest,
    WorkflowActor,
    add_score,
    create_activity_context,
    create_criterion_set,
    create_scoring_scale,
    select_activity_criterion_sets,
)


def _clock(hour: int) -> datetime:
    return datetime(2026, 8, 14, hour, 0, tzinfo=timezone.utc)


def _actor() -> WorkflowActor:
    return WorkflowActor(
        actor_id="teacher-1",
        display_label="Synthetic Teacher",
        role_label="teacher",
    )


def _workspace(tmp_path: Path) -> tuple[Path, int]:
    root = ensure_workspace_root(tmp_path / "workspace")
    write_class_metadata_for_class(
        root,
        create_class_metadata(
            "class-1",
            "2026-2027",
            created_at=_clock(8),
        ),
    )
    write_class_roster(
        root,
        create_roster(
            "class-1",
            (
                {
                    "student_id": "student-1",
                    "last_name": "One",
                    "first_name": "Alex",
                    "period": "1",
                },
            ),
        ),
    )
    activity = create_activity_context(
        CreateActivityContextRequest(
            class_id="class-1",
            activity_id="activity-1",
            title="Synthetic Publication Activity",
            activity_type="project",
            scoring_orientation="local_criteria_only",
            session_id="session-1",
            actor=_actor(),
            activity_status="active",
            session_status="active",
            privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
        ),
        workspace_root=root,
        clock=lambda: _clock(9),
    )
    scale = create_scoring_scale(
        CreateScoringScaleRequest(
            class_id="class-1",
            activity_id="activity-1",
            scoring_scale_id="scale-1",
            lineage_id="scale-lineage",
            name="Local scale",
            revision=1,
            scale_type="teacher_defined",
            levels=(
                ScoringScaleLevel(
                    value=1,
                    label="One",
                    meaning="First exact level.",
                ),
                ScoringScaleLevel(
                    value=2,
                    label="Two",
                    meaning="Second exact level.",
                ),
            ),
            status="active",
            expected_snapshot_revision=activity.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(10),
    )
    criterion_set = create_criterion_set(
        CreateCriterionSetRequest(
            class_id="class-1",
            activity_id="activity-1",
            criterion_set_id="set-1",
            lineage_id="set-lineage",
            name="Local criteria",
            purpose="Synthetic publication validation.",
            revision=1,
            scope="activity_specific",
            criterion_set_kind="local",
            criteria=(
                CriterionSpec(
                    criterion_id="criterion-1",
                    key="collaboration",
                    label="Collaboration",
                    definition="Demonstrates collaborative practice.",
                    criterion_kind="local",
                    supported_target_kinds=("core_student",),
                    default_scoring_scale_id="scale-1",
                ),
            ),
            status="active",
            expected_snapshot_revision=scale.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(11),
    )
    selected = select_activity_criterion_sets(
        SelectActivityCriterionSetsRequest(
            class_id="class-1",
            activity_id="activity-1",
            criterion_set_ids=("set-1",),
            expected_snapshot_revision=criterion_set.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(12),
    )
    scored = add_score(
        AddScoreRequest(
            class_id="class-1",
            activity_id="activity-1",
            score_record_id="score-1",
            target_reference=ScoreTargetReference(
                target_kind="core_student",
                target_id="student-1",
                owning_system="core",
            ),
            criterion_id="criterion-1",
            scoring_scale_id="scale-1",
            disposition="scored",
            value=1,
            basis="professional_judgment",
            rationale="Private publication rationale.",
            privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
            expected_snapshot_revision=selected.commit.snapshot_revision,
            actor=_actor(),
            session_id="session-1",
        ),
        workspace_root=root,
        clock=lambda: _clock(13),
    )
    register_concord_academic_work(
        root,
        "class-1",
        "activity-1",
        academic_intent="summative",
        lifecycle="active",
    )
    return root, scored.commit.snapshot_revision


def _request(
    revision: int,
    *,
    reason: RevisionReason = "initial",
) -> GenerateAcademicResultManifestRequest:
    return GenerateAcademicResultManifestRequest(
        class_id="class-1",
        activity_id="activity-1",
        expected_snapshot_revision=revision,
        actor=_actor(),
        revision_reason=reason,
    )

def _publication_actions(parser: argparse.ArgumentParser) -> set[str]:
    top = next(
        action
        for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
    )
    publication = top.choices["publication"]
    nested = next(
        action
        for action in publication._actions
        if isinstance(action, argparse._SubParsersAction)
    )
    return set(nested.choices)


def test_parser_exposes_complete_publication_command_family() -> None:
    actions = _publication_actions(build_parser())
    assert {
        "register",
        "registration-show",
        "registration-update",
        "manifest-generate",
        "manifest-list",
        "manifest-show",
        "publish",
        "supersede",
        "withdraw",
        "series-show",
        "catalog-list",
        "catalog-rebuild",
    } <= actions


def test_read_only_manifest_preview_does_not_create_manifest(tmp_path: Path) -> None:
    root, revision = _workspace(tmp_path)
    preview = preview_academic_result_manifest(
        _request(revision),
        workspace_root=root,
    )
    summary = manifest_preview_summary(preview)
    assert preview.disposition == "would_create"
    assert summary["registration_revision"] == 1
    assert summary["source_snapshot_revision"] == revision
    assert summary["score_count"] == 1
    assert summary["current_score_count"] == 1
    assert summary["historical_score_count"] == 0
    assert summary["local_score_count"] == 1
    assert summary["non_score_count"] == 0
    assert summary["manifest_sha256"] == preview.sha256
    assert not preview.path.exists()
    history = list_academic_result_manifest_revisions(
        root, preview.manifest.work
    )
    assert history == ()


def test_direct_manifest_commands_are_compact_and_safe(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root, revision = _workspace(tmp_path)
    common = [
        "publication",
        "manifest-generate",
        "--workspace-root",
        str(root),
        "--class-id",
        "class-1",
        "--activity-id",
        "activity-1",
        "--expected-snapshot",
        str(revision),
        "--actor-id",
        "teacher-1",
        "--revision-reason",
        "initial",
    ]
    assert main(common) == 0
    generated = capsys.readouterr().out
    assert "Record-set revision: 1" in generated
    assert "Private publication rationale" not in generated

    assert main(
        [
            "publication",
            "manifest-list",
            "--workspace-root",
            str(root),
            "--class-id",
            "class-1",
            "--activity-id",
            "activity-1",
        ]
    ) == 0
    listed = capsys.readouterr().out
    assert "1\t" in listed
    assert "Private publication rationale" not in listed

    assert main(
        [
            "publication",
            "manifest-show",
            "--workspace-root",
            str(root),
            "--class-id",
            "class-1",
            "--activity-id",
            "activity-1",
            "--revision",
            "1",
        ]
    ) == 0
    shown = capsys.readouterr().out
    assert '"record_type":"concord_academic_result_manifest"' in shown
    assert "Private publication rationale" not in shown


def test_publication_errors_preserve_cli_exit_contract(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def conflict(_args: argparse.Namespace) -> int:
        raise ConcordAcademicResultPublicationConflictError("stale head")

    monkeypatch.setattr(publication_handler, "handle_series_show", conflict)
    code = main(
        [
            "publication",
            "series-show",
            "--class-id",
            "class-1",
            "--activity-id",
            "activity-1",
        ]
    )
    assert code == 3
    assert "Conflict: stale head" in capsys.readouterr().err

    state = PublicationPartialSuccessState(
        operation="publish",
        canonical_state="confirmed",
        manifest_generation=None,
        generation_partial_state=None,
        publication=None,
        recommended_next_action="rebuild catalog",
    )

    def partial(_args: argparse.Namespace) -> int:
        raise ConcordAcademicResultPublicationPartialSuccessError(
            "catalog stale", state
        )

    monkeypatch.setattr(publication_handler, "handle_series_show", partial)
    code = main(
        [
            "publication",
            "series-show",
            "--class-id",
            "class-1",
            "--activity-id",
            "activity-1",
        ]
    )
    assert code == 4
    error = capsys.readouterr().err
    assert "Partial success: catalog stale" in error
    assert "rebuild catalog" in error


def test_activity_menu_places_share_after_score_and_preserves_advanced_order() -> None:
    routine = inspect.getsource(menu_activity.launch_activity_context_menu)
    assert routine.index('print("5. Score")') < routine.index('print("6. Share")')
    assert routine.index('print("6. Share")') < routine.index(
        'print("7. Advanced Activity tools")'
    )

    advanced = inspect.getsource(
        menu_activity.launch_advanced_open_activity_tools_menu
    )
    assert advanced.index('print("8. Scoring")') < advanced.index(
        'print("9. Publication")'
    )
    assert advanced.index('print("9. Publication")') < advanced.index(
        'print("10. Edit Activity")'
    )


def test_entering_publication_menu_then_back_has_no_write_side_effect(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    forbidden_names = (
        "register_concord_academic_work",
        "update_academic_work_registration",
        "generate_academic_result_manifest",
        "publish_concord_academic_results",
        "supersede_concord_academic_results",
        "republish_concord_academic_results_after_withdrawal",
        "withdraw_concord_academic_result_publication",
        "rebuild_full_academic_catalog",
    )

    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("publication menu entry must not mutate state")

    for name in forbidden_names:
        monkeypatch.setattr(menu_publication, name, forbidden)
    answers = iter(("b",))
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    activity = cast(
        ActivitySummary,
        type(
            "SyntheticActivity",
            (),
            {
                "title": "Synthetic",
                "class_id": "class-1",
                "activity_id": "activity-1",
                "snapshot_revision": 1,
            },
        )(),
    )
    menu_publication.launch_publication_menu(activity, MenuSessionContext())


def test_publication_handler_uses_concord_work_identity() -> None:
    args = argparse.Namespace(class_id="class-1", activity_id="activity-1")
    work = publication_handler._work(args)
    assert work.module_id == CONCORD_MODULE_ID
    assert work.class_id == "class-1"
    assert work.work_id == "activity-1"
