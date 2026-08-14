from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.routing_models import ModuleWorkRef
from pds_core.workspace import ensure_workspace_root

from concord.cli_app.main import EXIT_OK, main
from concord.storage import load_current_record_graph
from concord.workflows import (
    CreateActivityContextRequest,
    WorkflowActor,
    create_activity_context,
)


def _clock() -> datetime:
    return datetime(2026, 8, 13, 23, 0, tzinfo=timezone.utc)


def _work() -> ModuleWorkRef:
    return ModuleWorkRef(
        module_id="concord",
        class_id="class-1",
        work_id="activity-1",
    )


def _workspace(tmp_path: Path) -> tuple[Path, int]:
    root = ensure_workspace_root(tmp_path / "workspace")
    write_class_metadata_for_class(
        root,
        create_class_metadata("class-1", "2026-2027", created_at=_clock()),
    )
    created = create_activity_context(
        CreateActivityContextRequest(
            class_id="class-1",
            activity_id="activity-1",
            title="Issue 30 CLI",
            activity_type="project",
            scoring_orientation="local_criteria_only",
            session_id="session-1",
            actor=WorkflowActor(actor_id="teacher-1"),
        ),
        workspace_root=root,
        clock=_clock,
    )
    return root, created.commit.snapshot_revision


def _common(root: Path, expected: int) -> tuple[str, ...]:
    return (
        "--workspace-root",
        str(root),
        "--expected-snapshot",
        str(expected),
        "--actor-id",
        "teacher-1",
        "--actor-label",
        "Synthetic Teacher",
        "--class-id",
        "class-1",
        "--activity-id",
        "activity-1",
    )


def _write_json(path: Path, value: object) -> Path:
    path.write_text(
        json.dumps(value, indent=2),
        encoding="utf-8",
        newline="\n",
    )
    return path


def _scale_definition(revision: int) -> dict[str, object]:
    return {
        "name": "Three-level local scale",
        "revision": revision,
        "scale_type": "ordinal",
        "levels": [
            {
                "value": 1,
                "label": "Beginning",
                "meaning": "Beginning evidence",
                "position": 1,
            },
            {
                "value": 2,
                "label": "Developing",
                "meaning": "Developing evidence",
                "position": 2,
            },
            {
                "value": 3,
                "label": "Secure",
                "meaning": "Secure evidence",
                "position": 3,
            },
        ],
        "status": "active",
        "intended_use": "Synthetic local scoring.",
    }


def _criterion_definition(
    revision: int,
    criterion_id: str,
    scale_id: str,
) -> dict[str, object]:
    return {
        "name": "Local process criteria",
        "purpose": "Exercise direct Score CLI semantics.",
        "revision": revision,
        "scope": "activity_specific",
        "criterion_set_kind": "local",
        "status": "active",
        "criteria": [
            {
                "criterion_id": criterion_id,
                "key": "process",
                "label": "Process",
                "definition": "Uses an effective process.",
                "criterion_kind": "local",
                "supported_target_kinds": ["concord_activity"],
                "alignment_standard_ids": [],
                "default_scoring_scale_id": scale_id,
                "status": "active",
            }
        ],
    }


def _read_options(root: Path) -> tuple[str, ...]:
    return (
        "--workspace-root",
        str(root),
        "--class-id",
        "class-1",
        "--activity-id",
        "activity-1",
    )


def test_definition_cli_create_revise_select_list_show(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root, revision = _workspace(tmp_path)
    scale_v1 = _write_json(
        tmp_path / "scale-v1.json",
        _scale_definition(1),
    )
    scale_v2 = _write_json(
        tmp_path / "scale-v2.json",
        _scale_definition(2),
    )
    set_v1 = _write_json(
        tmp_path / "set-v1.json",
        _criterion_definition(1, "criterion-v1", "scale-1"),
    )
    set_v2 = _write_json(
        tmp_path / "set-v2.json",
        _criterion_definition(2, "criterion-v2", "scale-2"),
    )

    assert main(
        (
            "scale",
            "create",
            *_common(root, revision),
            "--scoring-scale-id",
            "scale-1",
            "--lineage-id",
            "scale-lineage",
            "--definition",
            str(scale_v1),
        )
    ) == EXIT_OK
    revision += 1

    assert main(
        (
            "criterion-set",
            "create",
            *_common(root, revision),
            "--criterion-set-id",
            "set-1",
            "--lineage-id",
            "set-lineage",
            "--definition",
            str(set_v1),
        )
    ) == EXIT_OK
    revision += 1

    assert main(
        (
            "criterion-set",
            "select",
            *_common(root, revision),
            "--criterion-set-id",
            "set-1",
        )
    ) == EXIT_OK
    revision += 1

    assert main(
        (
            "scale",
            "revise",
            *_common(root, revision),
            "--scoring-scale-id",
            "scale-1",
            "--replacement-scoring-scale-id",
            "scale-2",
            "--definition",
            str(scale_v2),
        )
    ) == EXIT_OK
    revision += 1

    assert main(
        (
            "criterion-set",
            "revise",
            *_common(root, revision),
            "--criterion-set-id",
            "set-1",
            "--replacement-criterion-set-id",
            "set-2",
            "--definition",
            str(set_v2),
        )
    ) == EXIT_OK
    revision += 1

    assert main(
        (
            "criterion-set",
            "select",
            *_common(root, revision),
            "--criterion-set-id",
            "set-2",
        )
    ) == EXIT_OK
    capsys.readouterr()

    assert main(
        (
            "scale",
            "list",
            *_read_options(root),
            "--current-only",
        )
    ) == EXIT_OK
    output = capsys.readouterr().out
    assert "scale-2" in output
    assert "scale-1" not in output

    assert main(
        (
            "criterion-set",
            "list",
            *_read_options(root),
            "--current-only",
        )
    ) == EXIT_OK
    output = capsys.readouterr().out
    assert "set-2" in output
    assert "set-1" not in output
    assert "selected" in output

    assert main(
        (
            "scale",
            "show",
            *_read_options(root),
            "--scoring-scale-id",
            "scale-2",
        )
    ) == EXIT_OK
    output = capsys.readouterr().out
    assert "Scoring Scale: scale-2" in output
    assert 'Level: value=3' in output

    assert main(
        (
            "criterion-set",
            "show",
            *_read_options(root),
            "--criterion-set-id",
            "set-2",
        )
    ) == EXIT_OK
    output = capsys.readouterr().out
    assert "Criterion Set: set-2" in output
    assert "criterion-v2" in output
    assert "default_scale=scale-2" in output


def test_score_cli_add_list_show_replace_and_non_score_reason(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root, revision = _workspace(tmp_path)
    scale = _write_json(
        tmp_path / "scale.json",
        _scale_definition(1),
    )
    criterion_set = _write_json(
        tmp_path / "set.json",
        _criterion_definition(1, "criterion-local", "scale-1"),
    )

    assert main(
        (
            "scale",
            "create",
            *_common(root, revision),
            "--scoring-scale-id",
            "scale-1",
            "--lineage-id",
            "scale-lineage",
            "--definition",
            str(scale),
        )
    ) == EXIT_OK
    revision += 1

    assert main(
        (
            "criterion-set",
            "create",
            *_common(root, revision),
            "--criterion-set-id",
            "set-1",
            "--lineage-id",
            "set-lineage",
            "--definition",
            str(criterion_set),
        )
    ) == EXIT_OK
    revision += 1

    assert main(
        (
            "criterion-set",
            "select",
            *_common(root, revision),
            "--criterion-set-id",
            "set-1",
        )
    ) == EXIT_OK
    revision += 1

    private_rationale = "Private professional-judgment rationale."
    semantic = (
        "--target-kind",
        "concord_activity",
        "--target-owner",
        "concord",
        "--target-id",
        "activity-1",
        "--criterion-id",
        "criterion-local",
        "--scoring-scale-id",
        "scale-1",
        "--disposition",
        "scored",
        "--basis",
        "professional_judgment",
    )
    assert main(
        (
            "score",
            "add",
            *_common(root, revision),
            "--score-record-id",
            "score-1",
            *semantic,
            "--value-json",
            "2",
            "--rationale",
            private_rationale,
        )
    ) == EXIT_OK
    revision += 1

    assert main(
        (
            "score",
            "list",
            *_read_options(root),
        )
    ) == EXIT_OK
    output = capsys.readouterr().out
    assert "score-1" in output
    assert "value=2" in output
    assert private_rationale not in output

    assert main(
        (
            "score",
            "show",
            *_read_options(root),
            "--score-record-id",
            "score-1",
        )
    ) == EXIT_OK
    output = capsys.readouterr().out
    assert "Score Record: score-1" in output
    assert private_rationale in output

    assert main(
        (
            "score",
            "replace",
            *_common(root, revision),
            "--score-record-id",
            "score-1",
            "--replacement-score-record-id",
            "score-2",
            "--correction-id",
            "correction-score-cli",
            "--reason",
            "Additional observation changed the judgment.",
            *semantic,
            "--value-json",
            "3",
            "--rationale",
            "Revised private rationale.",
        )
    ) == EXIT_OK
    revision += 1

    assert main(
        (
            "score",
            "list",
            *_read_options(root),
            "--current-only",
        )
    ) == EXIT_OK
    output = capsys.readouterr().out
    assert "score-2" in output
    assert "score-1" not in output

    non_score_semantic = (
        "--target-kind",
        "concord_activity",
        "--target-owner",
        "concord",
        "--target-id",
        "activity-1",
        "--criterion-id",
        "criterion-local",
        "--scoring-scale-id",
        "scale-1",
        "--disposition",
        "not_observed",
        "--basis",
        "professional_judgment",
        "--rationale",
        "No direct observation was available.",
        "--status-reason-note",
        "Synthetic non-score context.",
    )
    assert main(
        (
            "score",
            "add",
            *_common(root, revision),
            "--score-record-id",
            "score-nonscore",
            *non_score_semantic,
        )
    ) == EXIT_OK

    assert main(
        (
            "score",
            "show",
            *_read_options(root),
            "--score-record-id",
            "score-nonscore",
        )
    ) == EXIT_OK
    output = capsys.readouterr().out
    assert "Disposition: not_observed" in output
    assert "Value: -" in output
    assert "Status reason: not_observed" in output

    graph = load_current_record_graph(root, _work()).graph
    scores = {item.score_record_id: item for item in graph.score_records}
    assert scores["score-1"].value == 2
    assert scores["score-2"].value == 3
    assert scores["score-nonscore"].value is None
    assert len(graph.correction_records) == 1
    assert graph.correction_records[0].correction_type == "score_revision"
