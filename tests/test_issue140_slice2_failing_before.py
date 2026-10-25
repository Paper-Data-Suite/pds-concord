"""Issue #140 Slice 2: C1 post-#141 fix and historical C2 baseline.

C1 retains its original test ID for frozen #140 traceability, but now proves
the successful canonical write. C2 remains a failing-before #143 witness.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from issue140_slice2_fixtures import (
    ACTIVITY_ID,
    ACTOR,
    PROFILE_ID,
    SOURCE_CLASS,
    STANDARD_ID,
    build_workspace,
)
from pds_core.routing_models import ModuleWorkRef

import concord.menu_activity as activity_menu
import concord.menu_scoring as scoring_menu
from concord.menu_context import MenuSessionContext
from concord.models import ScoringScaleLevel
from concord.reusable_preset_storage import load_current_preset
from concord.storage import list_work_snapshots, load_current_record_graph
from concord.workflows import (
    CreateCriterionSetRequest,
    CreateScoringScaleRequest,
    CriterionSpec,
    create_criterion_set,
    create_scoring_scale,
    list_criterion_sets,
    show_activity,
    show_criterion_set,
    update_activity,
)
from concord.workflows.reusable_presets import (
    prepare_criterion_set_preset_from_activity,
)


def _work() -> ModuleWorkRef:
    return ModuleWorkRef("concord", SOURCE_CLASS, ACTIVITY_ID)


def _graph(root: Path, standards: Any) -> Any:
    return load_current_record_graph(root, _work(), standards_library=standards).graph


def _patch_current_context(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep menu's structural read and real service on one synthetic workspace."""
    from concord.workflows.activity import _load_activity_context

    monkeypatch.setattr(
        activity_menu,
        "resolve_read_workspace_root",
        lambda: root,
    )
    monkeypatch.setattr(
        activity_menu,
        "_load_activity_context",
        lambda class_id, activity_id, *, workspace_root=None: _load_activity_context(
            class_id, activity_id, workspace_root=workspace_root
        ),
    )


def test_c1_status_edit_reproduces_missing_standards_at_real_menu_service_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = build_workspace(tmp_path, orientation="mixed")
    root, standards = fixture.root, fixture.standards
    before_graph = _graph(root, standards)
    before_snapshots = list_work_snapshots(root, _work())
    activity = show_activity(SOURCE_CLASS, ACTIVITY_ID, workspace_root=root).summary
    forwarded: list[object] = []
    errors: list[str] = []
    monkeypatch.setattr(
        activity_menu,
        "show_activity",
        lambda c, a, *, workspace_root=None: show_activity(
            c, a, workspace_root=workspace_root
        ),
    )
    _patch_current_context(root, monkeypatch)
    monkeypatch.setattr(activity_menu, "resolve_read_workspace_root", lambda: root)
    monkeypatch.setattr(activity_menu, "prompt_text", lambda *a, **k: "configured")
    monkeypatch.setattr(activity_menu, "confirm_write", lambda *a, **k: True)
    monkeypatch.setattr(activity_menu, "show_result", lambda *a, **k: None)
    monkeypatch.setattr(
        activity_menu, "load_menu_standards_library", lambda _root: standards
    )
    monkeypatch.setattr(
        activity_menu, "handle_write_error", lambda e, **k: errors.append(str(e))
    )

    def actual_service(
        request: Any,
        *,
        standards_library: Any = None,
        workspace_root: Path | None = None,
    ) -> Any:
        assert workspace_root == root
        forwarded.append(standards_library)
        return update_activity(
            request, workspace_root=workspace_root, standards_library=standards_library
        )

    monkeypatch.setattr(activity_menu, "update_activity", actual_service)
    activity_menu._update_activity_field(
        activity, MenuSessionContext(actor=ACTOR), "status"
    )
    # Historical C1 test ID is retained to anchor the original #140 witness;
    # the post-#141 assertions must now prove the successful guarded write.
    assert forwarded == [standards]
    assert not errors
    assert _graph(root, standards) != before_graph
    assert len(list_work_snapshots(root, _work())) == len(before_snapshots) + 1
    assert (
        show_activity(SOURCE_CLASS, ACTIVITY_ID, workspace_root=root).summary.status
        == "configured"
    )


@pytest.mark.parametrize("orientation", ("evidence_only", "local_criteria_only"))
def test_c1_neutral_control_may_edit_without_core_standards(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, orientation: str
) -> None:
    fixture = build_workspace(tmp_path, orientation=orientation)
    root = fixture.root
    activity = show_activity(SOURCE_CLASS, ACTIVITY_ID, workspace_root=root).summary
    errors: list[str] = []
    monkeypatch.setattr(
        activity_menu,
        "load_menu_standards_library",
        lambda _root: pytest.fail("neutral mode loaded Core library"),
    )
    monkeypatch.setattr(
        activity_menu,
        "show_activity",
        lambda c, a, *, workspace_root=None: show_activity(
            c, a, workspace_root=workspace_root
        ),
    )
    _patch_current_context(root, monkeypatch)
    monkeypatch.setattr(activity_menu, "resolve_read_workspace_root", lambda: root)
    monkeypatch.setattr(activity_menu, "prompt_text", lambda *a, **k: "configured")
    monkeypatch.setattr(activity_menu, "confirm_write", lambda *a, **k: True)
    monkeypatch.setattr(activity_menu, "show_result", lambda *a, **k: None)
    monkeypatch.setattr(
        activity_menu, "handle_write_error", lambda e, **k: errors.append(str(e))
    )
    monkeypatch.setattr(
        activity_menu,
        "update_activity",
        lambda request, *, standards_library=None, workspace_root=None: update_activity(
            request, workspace_root=workspace_root, standards_library=standards_library
        ),
    )
    activity_menu._update_activity_field(
        activity, MenuSessionContext(actor=ACTOR), "status"
    )
    assert not errors
    assert (
        show_activity(SOURCE_CLASS, ACTIVITY_ID, workspace_root=root).summary.status
        == "configured"
    )


def test_c1_cancellation_must_not_reach_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = build_workspace(tmp_path)
    root = fixture.root
    before = list_work_snapshots(root, _work())
    activity = show_activity(SOURCE_CLASS, ACTIVITY_ID, workspace_root=root).summary
    monkeypatch.setattr(
        activity_menu,
        "show_activity",
        lambda c, a, *, workspace_root=None: show_activity(
            c, a, workspace_root=workspace_root
        ),
    )
    _patch_current_context(root, monkeypatch)
    monkeypatch.setattr(activity_menu, "resolve_read_workspace_root", lambda: root)
    monkeypatch.setattr(activity_menu, "prompt_text", lambda *a, **k: "configured")
    monkeypatch.setattr(activity_menu, "confirm_write", lambda *a, **k: False)
    monkeypatch.setattr(
        activity_menu,
        "update_activity",
        lambda *a, **k: pytest.fail("cancelled menu committed"),
    )
    activity_menu._update_activity_field(
        activity, MenuSessionContext(actor=ACTOR), "status"
    )
    assert list_work_snapshots(root, _work()) == before


def _create_native_mixed_criterion_set(root: Path, standards: Any) -> None:
    scale = create_scoring_scale(
        CreateScoringScaleRequest(
            class_id=SOURCE_CLASS,
            activity_id=ACTIVITY_ID,
            scoring_scale_id="issue140-scale",
            lineage_id="issue140-scale-lineage",
            name="Four Levels",
            revision=1,
            scale_type="ordinal",
            levels=tuple(
                ScoringScaleLevel(
                    value=index,
                    label=label,
                    meaning=f"Synthetic {label}",
                    position=index,
                )
                for index, label in enumerate(
                    ("Developing", "Approaching", "Meeting", "Exceeding"), start=1
                )
            ),
            status="active",
            expected_snapshot_revision=1,
            actor=ACTOR,
        ),
        workspace_root=root,
        standards_library=standards,
    )
    criteria = (
        CriterionSpec(
            criterion_id="issue140-criterion-individual",
            key="discussion_participation",
            label="Discussion Participation",
            definition="Synthetic individual evidence, no assumed Score.",
            criterion_kind="standard_backed",
            standard_id=STANDARD_ID,
            supported_target_kinds=("core_student",),
            default_scoring_scale_id="issue140-scale",
        ),
        CriterionSpec(
            criterion_id="issue140-criterion-group",
            key="collaborative_textual_analysis",
            label="Collaborative Textual Analysis",
            definition="Synthetic Group-level observation only.",
            criterion_kind="local",
            supported_target_kinds=("concord_group",),
            default_scoring_scale_id="issue140-scale",
        ),
    )
    create_criterion_set(
        CreateCriterionSetRequest(
            class_id=SOURCE_CLASS,
            activity_id=ACTIVITY_ID,
            criterion_set_id="issue140-native-set",
            lineage_id="issue140-native-lineage",
            name="Synthetic Mixed Discussion Criteria",
            purpose="Baseline dotted Standards ID regression",
            revision=1,
            scope="activity_specific",
            criterion_set_kind="mixed",
            criteria=criteria,
            status="active",
            standards_profile_id=PROFILE_ID,
            expected_snapshot_revision=scale.commit.snapshot_revision,
            actor=ACTOR,
        ),
        workspace_root=root,
        standards_library=standards,
    )


def test_c2_native_standards_identity_survives_but_menu_preset_save_rejects_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = build_workspace(tmp_path)
    root, standards = fixture.root, fixture.standards
    _create_native_mixed_criterion_set(root, standards)
    before_graph = _graph(root, standards)
    assert before_graph.score_records == ()
    assert any(c.standard_id == STANDARD_ID for c in before_graph.criteria)
    before_snapshots = list_work_snapshots(root, _work())
    current = show_activity(SOURCE_CLASS, ACTIVITY_ID, workspace_root=root).summary
    error_messages: list[str] = []
    entered_preview: list[bool] = []
    fake_uuid = "0" * 32
    monkeypatch.setattr(scoring_menu, "uuid4", lambda: SimpleNamespace(hex=fake_uuid))

    monkeypatch.setattr(scoring_menu, "_latest", lambda _activity: current)
    monkeypatch.setattr(scoring_menu, "_library", lambda: standards)
    monkeypatch.setattr(
        scoring_menu,
        "list_criterion_sets",
        lambda c, a, **k: list_criterion_sets(c, a, workspace_root=root, **k),
    )
    monkeypatch.setattr(
        scoring_menu,
        "show_criterion_set",
        lambda c, a, s, **k: show_criterion_set(c, a, s, workspace_root=root, **k),
    )
    monkeypatch.setattr(
        scoring_menu, "select_one", lambda _title, items, labels, **k: items[0]
    )
    monkeypatch.setattr(
        scoring_menu, "_recommended_scale_for_native_set", lambda _set: (None, None)
    )
    monkeypatch.setattr(
        scoring_menu,
        "_handle_error",
        lambda _activity, err: error_messages.append(str(err)),
    )
    monkeypatch.setattr(
        scoring_menu,
        "confirm_write",
        lambda *a, **k: pytest.fail("legacy preview unexpectedly succeeded"),
    )
    monkeypatch.setattr(
        scoring_menu,
        "save_criterion_set_preset_from_activity",
        lambda *a, **k: pytest.fail("save should never follow failed preview"),
    )

    def real_preview(request: Any, *, standards_library: Any = None) -> Any:
        entered_preview.append(True)
        return prepare_criterion_set_preset_from_activity(
            request, workspace_root=root, standards_library=standards_library
        )

    monkeypatch.setattr(
        scoring_menu, "prepare_criterion_set_preset_from_activity", real_preview
    )
    scoring_menu._save_criterion_set_as_preset(current, MenuSessionContext(actor=ACTOR))

    assert entered_preview == [True], (
        "Only the actual menu-to-preset contract is a witness"
    )
    assert len(error_messages) == 1
    assert error_messages[0] == (
        "standard_id must contain only letters, numbers, underscores, and hyphens."
    )
    assert _graph(root, standards) == before_graph
    assert list_work_snapshots(root, _work()) == before_snapshots
    with pytest.raises(Exception):
        load_current_preset(root, "criterion_set", f"criterion-preset-{fake_uuid}")
