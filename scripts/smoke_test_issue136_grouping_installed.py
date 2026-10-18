"""#136 isolated installed-wheel acceptance for real teacher grouping menu paths.

Run ONLY from a temporary outside-source directory, with an isolated Python -I.
All Core records, identifiers and teacher UI interactions are synthetic.
"""

from __future__ import annotations

import sys
import tempfile
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from unittest.mock import patch

import pds_core
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.classes import write_class_roster
from pds_core.rosters import create_roster
from pds_core.routing_models import ModuleWorkRef
from pds_core.standards import (
    StandardDefinition,
    StandardsLibrary,
    StandardsProfile,
    load_workspace_standards_library,
    write_workspace_standards_library,
)
from pds_core.workspace import ensure_workspace_root

import concord
import concord.menu_group_plan as plan_menu
import concord.menu_saved_groupings as saved_menu
import concord.menu_standards_context as standards_context
from concord.class_group_arrangement_storage import load_current_arrangement
from concord.menu_context import MenuSessionContext
from concord.models import EffectiveContext, PlannedGroup
from concord.storage import load_current_record_graph
from concord.workflows import (
    ActivitySummary,
    ApplyGroupPlanRequest,
    ApproveGroupPlanRequest,
    CreateActivityContextRequest,
    CreateManualGroupPlanRequest,
    PrepareGroupPlanApplicationRequest,
    PreviewGroupPlanRequest,
    WorkflowActor,
    apply_group_plan,
    approve_group_plan,
    create_activity_context,
    create_manual_group_plan,
    prepare_group_plan_application,
    preview_group_plan,
    show_activity,
    show_group_plan,
)
from concord.workflows.class_group_arrangements import (
    prepare_reuse_grouping,
    prepare_save_grouping,
    reuse_grouping,
    save_grouping,
)

CLASS = "six-table-synthetic-class"
SOURCE = "discussion-source"
TARGET = "discussion-target"
RESUME = "discussion-resume-existing"
ACTOR = WorkflowActor(actor_id="teacher-installed-136")
STATE = MenuSessionContext(actor=ACTOR)
STUDENTS = tuple(f"learner-{i:02}" for i in range(1, 30))
PROFILE = "synthetic:discussion-profile"
STANDARD = "synthetic:discussion-standard"
ARRANGEMENT = "six-table-arrangement"
PLAN = "fresh-target-plan"


def _clock() -> datetime:
    return datetime(2026, 10, 18, 16, 0, tzinfo=timezone.utc)


def _require_isolation(repo: Path) -> None:
    for distribution, module, version in (
        ("pds-core", pds_core, "0.6.6"),
        ("pds-concord", concord, "0.3.4"),
    ):
        assert metadata.version(distribution) == version
        origin = Path(str(module.__file__)).resolve()
        assert "site-packages" in {part.casefold() for part in origin.parts}
        assert not origin.is_relative_to(repo)
    roots = {name.split(".", 1)[0].casefold() for name in sys.modules}
    assert {"scoreform", "quillan", "portia", "meridian", "vitrine"}.isdisjoint(roots)
    for path in sys.path:
        if path:
            candidate = Path(path).resolve()
            assert candidate != repo and not candidate.is_relative_to(repo)


def _standards() -> StandardsLibrary:
    return StandardsLibrary(
        standards=(
            StandardDefinition(
                standard_id=STANDARD,
                code="SYN.ELA.1",
                source="synthetic",
                short_name="Synthetic discussion",
                description="Synthetic discussion observation only.",
                available_modules=("concord",),
            ),
        ),
        profiles=(
            StandardsProfile(
                profile_id=PROFILE,
                standards=(STANDARD,),
                title="Synthetic discussion profile",
            ),
        ),
    )


def _groups() -> tuple[PlannedGroup, ...]:
    return tuple(
        PlannedGroup(
            planned_group_key=f"table-{i}",
            label=f"Table {i}",
            description=f"Synthetic table {i}",
            student_ids=tuple(
                sid for index, sid in enumerate(STUDENTS) if index % 6 == i - 1
            ),
        )
        for i in range(1, 7)
    )


def _activity(root: Path, library: StandardsLibrary, activity_id: str) -> None:
    create_activity_context(
        CreateActivityContextRequest(
            class_id=CLASS,
            activity_id=activity_id,
            title=f"Synthetic {activity_id}",
            activity_type="project",
            scoring_orientation="mixed",
            standards_profile_id=PROFILE,
            focus_standard_ids=(STANDARD,),
            session_id=f"{activity_id}-session",
            actor=ACTOR,
        ),
        workspace_root=root,
        standards_library=library,
        clock=_clock,
    )


def _summary(root: Path, activity_id: str) -> ActivitySummary:
    return show_activity(CLASS, activity_id, workspace_root=root).summary


def _run(root: Path, library: StandardsLibrary) -> None:
    # This is the actual production menu callback that failed for an existing
    # mixed-standards Activity. Only input/display and workspace routing are
    # substituted; the real workflow service performs the canonical write.
    errors: list[str] = []
    original_create = create_manual_group_plan
    with (
        patch.object(
            standards_context,
            "load_menu_standards_library",
            lambda: load_workspace_standards_library(root),
        ),
        patch.object(
            plan_menu, "_latest", lambda current: _summary(root, current.activity_id)
        ),
        patch.object(
            plan_menu, "prompt_text", lambda *_a, **_kw: "resumed-manual-plan"
        ),
        patch.object(plan_menu, "confirm_write", lambda *_a, **_kw: True),
        patch.object(plan_menu, "show_result", lambda *_a, **_kw: None),
        patch.object(
            plan_menu, "_handle_error", lambda _a, _t, exc: errors.append(str(exc))
        ),
        patch.object(
            plan_menu,
            "create_manual_group_plan",
            lambda request, **kw: original_create(request, workspace_root=root, **kw),
        ),
    ):
        plan_menu._create_manual(_summary(root, RESUME), STATE)
    assert errors == [], errors
    resumed = show_group_plan(CLASS, RESUME, "resumed-manual-plan", workspace_root=root)
    assert resumed.plan.status == "draft"
    assert resumed.summary.unresolved_student_count == 29
    print(
        "#136 installed grouping: original mixed-standards menu resume: PASS",
        flush=True,
    )

    # Source plan is a real six-table proposal, not a mock of grouping state.
    source = _summary(root, SOURCE)
    created = original_create(
        CreateManualGroupPlanRequest(
            class_id=CLASS,
            activity_id=SOURCE,
            group_plan_id="source-six-table-plan",
            proposed_groups=_groups(),
            expected_snapshot_revision=source.snapshot_revision,
            actor=ACTOR,
        ),
        workspace_root=root,
        standards_library=library,
    )
    source_revision = created.commit.snapshot_revision

    # Actual menu callbacks, including preview digest and confirmation, and
    # actual backing services. Never bypass author/revision rules.
    with (
        patch.object(
            saved_menu, "_latest", lambda current: _summary(root, current.activity_id)
        ),
        patch.object(
            saved_menu, "prompt_text", side_effect=["Six Table Groups", ARRANGEMENT]
        ),
        patch.object(saved_menu, "_show_placements", lambda *_a, **_kw: None),
        patch.object(saved_menu, "confirm_write", lambda *_a, **_kw: True),
        patch.object(saved_menu, "show_result", lambda *_a, **_kw: None),
        patch.object(
            saved_menu, "handle_write_error", lambda exc, **_kw: errors.append(str(exc))
        ),
        patch.object(
            saved_menu,
            "prepare_save_grouping",
            lambda req: prepare_save_grouping(req, workspace_root=root),
        ),
        patch.object(
            saved_menu,
            "save_grouping",
            lambda req, review_digest: save_grouping(
                req, review_digest=review_digest, workspace_root=root
            ),
        ),
    ):
        saved_menu.save_grouping_from_plan(
            _summary(root, SOURCE), STATE, group_plan_id="source-six-table-plan"
        )
    assert errors == [], errors
    saved = load_current_arrangement(
        root,
        class_id=CLASS,
        school_year="2026-2027",
        arrangement_id=ARRANGEMENT,
        actor_id=ACTOR.actor_id,
    )
    assert len(saved.revision.groups) == 6
    assert sum(len(g.student_ids) for g in saved.revision.groups) == 29
    assert _summary(root, SOURCE).snapshot_revision == source_revision
    print("#136 installed grouping: teacher-menu save six tables: PASS", flush=True)

    # Use the same stored class arrangement through the real target-menu action.
    # No roster reconciliation choices are required for an unchanged roster.
    with (
        patch.object(
            standards_context,
            "load_menu_standards_library",
            lambda: load_workspace_standards_library(root),
        ),
        patch.object(
            saved_menu, "_latest", lambda current: _summary(root, current.activity_id)
        ),
        patch.object(saved_menu, "_select_saved", lambda *_a: saved),
        patch.object(saved_menu, "_show_placements", lambda *_a, **_kw: None),
        patch.object(saved_menu, "_preview_reuse", lambda *_a, **_kw: None),
        patch.object(saved_menu, "_collect_decisions", lambda *_a: ((), ())),
        patch.object(saved_menu, "list_group_plans", lambda *_a, **_kw: ()),
        patch.object(saved_menu, "prompt_text", lambda *_a, **_kw: PLAN),
        patch.object(saved_menu, "confirm_write", lambda *_a, **_kw: True),
        patch.object(saved_menu, "show_result", lambda *_a, **_kw: None),
        patch.object(
            saved_menu, "handle_write_error", lambda exc, **_kw: errors.append(str(exc))
        ),
        patch.object(
            saved_menu,
            "prepare_reuse_grouping",
            lambda req: prepare_reuse_grouping(req, workspace_root=root),
        ),
        patch.object(
            saved_menu,
            "reuse_grouping",
            lambda req, review_digest, **kw: reuse_grouping(
                req, review_digest=review_digest, workspace_root=root, **kw
            ),
        ),
    ):
        saved_menu.use_saved_grouping(_summary(root, TARGET), STATE)
    assert errors == [], errors
    draft = show_group_plan(CLASS, TARGET, PLAN, workspace_root=root)
    assert draft.plan.status == "draft"
    target_graph = load_current_record_graph(
        root, ModuleWorkRef("concord", CLASS, TARGET), standards_library=library
    ).graph
    assert not target_graph.groups and not target_graph.memberships

    preview = preview_group_plan(
        PreviewGroupPlanRequest(
            class_id=CLASS,
            activity_id=TARGET,
            group_plan_id=PLAN,
            expected_snapshot_revision=draft.summary.snapshot_revision,
            actor=ACTOR,
        ),
        workspace_root=root,
        standards_library=library,
    )
    approved = approve_group_plan(
        ApproveGroupPlanRequest(
            class_id=CLASS,
            activity_id=TARGET,
            group_plan_id=PLAN,
            expected_snapshot_revision=preview.summary.snapshot_revision,
            actor=ACTOR,
        ),
        workspace_root=root,
        standards_library=library,
    )
    assert approved.status == "approved"
    context = EffectiveContext(activity_id=TARGET, session_ids=(f"{TARGET}-session",))
    application = prepare_group_plan_application(
        PrepareGroupPlanApplicationRequest(
            class_id=CLASS,
            activity_id=TARGET,
            group_plan_id=PLAN,
            application_id="six-table-application",
            fallback_effective_context=context,
        ),
        workspace_root=root,
        standards_library=library,
    )
    assert application.group_count == 6 and application.membership_count == 29
    applied = apply_group_plan(
        ApplyGroupPlanRequest(
            class_id=CLASS,
            activity_id=TARGET,
            group_plan_id=PLAN,
            application_id=application.application_id,
            application_digest=application.application_digest,
            expected_snapshot_revision=application.expected_snapshot_revision,
            actor=ACTOR,
            fallback_effective_context=context,
        ),
        workspace_root=root,
        standards_library=library,
    )
    assert applied.group_count == 6 and applied.membership_count == 29
    graph = load_current_record_graph(
        root, ModuleWorkRef("concord", CLASS, TARGET), standards_library=library
    ).graph
    assert len(graph.groups) == 6 and len(graph.memberships) == 29
    assert not graph.score_records and not graph.score_evidence_links
    assert _summary(root, SOURCE).snapshot_revision == source_revision
    assert (
        load_current_arrangement(
            root,
            class_id=CLASS,
            school_year="2026-2027",
            arrangement_id=ARRANGEMENT,
            actor_id=ACTOR.actor_id,
        )
        == saved
    )
    print(
        "#136 installed grouping: reviewed reuse and six-table apply: PASS", flush=True
    )


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(
            "Expected one source checkout path for provenance verification"
        )
    repo = Path(sys.argv[1]).resolve(strict=True)
    _require_isolation(repo)
    with tempfile.TemporaryDirectory(prefix="concord136-installed-six-tables-") as temp:
        root = ensure_workspace_root(Path(temp) / "workspace")
        write_class_metadata_for_class(
            root, create_class_metadata(CLASS, "2026-2027", created_at=_clock())
        )
        write_class_roster(
            root,
            create_roster(
                CLASS,
                tuple(
                    {
                        "student_id": student,
                        "last_name": f"Synthetic{i:02}",
                        "first_name": "Learner",
                        "period": "1",
                    }
                    for i, student in enumerate(STUDENTS, 1)
                ),
            ),
        )
        library = _standards()
        write_workspace_standards_library(root, library)
        for activity in (SOURCE, TARGET, RESUME):
            _activity(root, library, activity)
        _run(root, library)
    print("Issue #136 isolated installed teacher grouping acceptance: PASS", flush=True)


if __name__ == "__main__":
    main()
