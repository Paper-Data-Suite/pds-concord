"""#152 Slice 1K3: orientation and typed Score preparation boundaries."""

from __future__ import annotations

from pathlib import Path

import pytest
from pds_core.routing_models import ModuleWorkRef
from test_artifact_routine_scoring_preparation_issue108 import (
    _context,
    _criterion,
    _request,
    _scale,
    _target,
)
from test_issue142_slice6b_real_score_continuation import (
    ACTIVITY,
    ACTOR,
    ARTIFACT,
    CLASS,
    _setup_reviewed,
)

from concord.models import PrivacyPolicy
from concord.storage import list_work_snapshots, load_current_record_graph
from concord.workflows import AddScoreRequest, ScoreEvidenceLinkSpec, add_score
from concord.workflows.artifact_routine_scoring import inspect_artifact_routine_scoring
from concord.workflows.artifact_routine_scoring_preparation import (
    prepare_routine_score_preview,
)
from concord.workflows.artifact_routine_scoring_selection import (
    routine_criteria_for_target,
    routine_target_options,
)
from concord.workflows.errors import ConcordWorkflowValidationError


@pytest.mark.parametrize(
    ("orientation", "allowed"),
    (
        ("mixed", ("focus", "local")),
        ("standards_based", ("focus",)),
        ("local_criteria_only", ("local",)),
        ("evidence_only", ()),
    ),
)
def test_orientation_filters_explicit_score_preparation(
    orientation: str, allowed: tuple[str, ...]
) -> None:
    context = _context(
        criteria=(
            _criterion("focus"),
            _criterion("non-focus", standard_id="other-standard"),
            _criterion("local", kind="local", standard_id=None),
        )
    )
    context.scoring_orientation = orientation
    if not allowed:
        with pytest.raises(ConcordWorkflowValidationError):
            routine_target_options(context)
    else:
        assert (
            tuple(
                item.criterion_id
                for item in routine_criteria_for_target(context, _target())
            )
            == allowed
        )
    for criterion_id in ("focus", "non-focus", "local"):
        request = _request(criterion_id=criterion_id)
        if criterion_id not in allowed:
            with pytest.raises(ConcordWorkflowValidationError):
                prepare_routine_score_preview(context, request)
        else:
            preview = prepare_routine_score_preview(context, request)
            assert preview.criterion_id == criterion_id
            assert preview.standard_id == (
                "standard-1" if criterion_id == "focus" else None
            )


@pytest.mark.parametrize(
    ("level", "invalid"),
    (
        (1, True),
        (1, 1.0),
        (1, "1"),
        ("1", 1),
        (True, 1),
        ("meeting", "Meeting"),
        ("meeting", "exceeding"),
    ),
)
def test_exact_typed_scale_rejects_coercion(
    level: str | int | float | bool, invalid: str | int | float | bool
) -> None:
    context = _context(scales=(_scale(levels=((level, "Exact level"),)),))
    preview = prepare_routine_score_preview(context, _request(value=level))
    assert type(preview.value) is type(level)
    assert preview.value == level
    with pytest.raises(ConcordWorkflowValidationError, match="exact level"):
        prepare_routine_score_preview(context, _request(value=invalid))


def test_real_score_rejects_unrelated_moderation_identity_without_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, standards = _setup_reviewed(tmp_path, monkeypatch)
    work = ModuleWorkRef("concord", CLASS, ACTIVITY)
    context = inspect_artifact_routine_scoring(
        CLASS, ACTIVITY, ARTIFACT, workspace_root=root
    )
    before = list_work_snapshots(root, work)
    before_graph = load_current_record_graph(
        root, work, standards_library=standards
    ).graph
    request = AddScoreRequest(
        class_id=CLASS,
        activity_id=ACTIVITY,
        score_record_id="synthetic-rejected-score",
        target_reference=_target(),
        criterion_id="criterion-standard",
        scoring_scale_id="scale-1",
        disposition="scored",
        value=3,
        basis="linked_evidence",
        evidence_links=(
            ScoreEvidenceLinkSpec(
                score_evidence_link_id="synthetic-rejected-link",
                evidence_reference=context.evidence_reference,
                relevance_description="Synthetic observation.",
                moderation_record_id="unrelated-moderation",
            ),
        ),
        privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
        expected_snapshot_revision=context.snapshot_revision,
        actor=ACTOR,
    )
    with pytest.raises(
        ConcordWorkflowValidationError, match="Selected Moderation Record"
    ):
        add_score(request, workspace_root=root, standards_library=standards)
    assert list_work_snapshots(root, work) == before
    assert (
        load_current_record_graph(root, work, standards_library=standards).graph
        == before_graph
    )
