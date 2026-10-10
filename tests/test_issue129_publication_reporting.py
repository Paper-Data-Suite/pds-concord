"""Issue #129 publication/reporting qualification with Core Standards identities."""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from pathlib import Path

from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.classes import write_class_roster
from pds_core.publication_compatibility import lookup_publication_reader_support
from pds_core.rosters import create_roster
from pds_core.routing_models import ModuleWorkRef
from pds_core.standards import (
    StandardDefinition,
    StandardsLibrary,
    StandardsProfile,
    write_workspace_standards_library,
)
from pds_core.workspace import ensure_workspace_root

import concord.workflows.activity_score_report_pdf as score_pdf
from concord.academic_result_manifest_generation import (
    GenerateAcademicResultManifestRequest,
)
from concord.academic_result_publication import publish_concord_academic_results
from concord.academic_result_reader import read_academic_result_manifest
from concord.academic_work_registration import register_concord_academic_work
from concord.models import (
    PrivacyPolicy,
    ScoreTargetReference,
    ScoringScaleLevel,
)
from concord.pds_contract import (
    ACADEMIC_RESULT_MANIFEST_CONTRACT_VERSION,
    CONCORD_ACADEMIC_RESULT_READER_CONTRACT_VERSION,
)
from concord.pds_publication import get_publication_producer_profile
from concord.workflows import (
    ActivityAnalysisReport,
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
    prepare_activity_analysis_report,
    render_score_analysis_report_csv,
    render_score_analysis_report_json,
    render_score_analysis_report_pdf,
    select_activity_criterion_sets,
)
from concord.workflows.activity_read import load_activity_read_context

PROFILE_ID = "njsls-ela:profile.2023:11-12"
PROFILE_TITLE = "NJSLS ELA Grades 11–12"
STANDARD_ID = "njsls-ela:2023:rl-ts-11-12-4"
STANDARD_CODE = "RL.TS.11-12.4"
STANDARD_SHORT_NAME = "Analyze Text Structure"


def _clock(hour: int) -> datetime:
    return datetime(2026, 10, 8, hour, 0, tzinfo=timezone.utc)


def _actor() -> WorkflowActor:
    return WorkflowActor(
        actor_id="teacher-1",
        display_label="Synthetic Teacher",
        role_label="teacher",
    )


def _library() -> StandardsLibrary:
    return StandardsLibrary(
        standards=(
            StandardDefinition(
                standard_id=STANDARD_ID,
                code=STANDARD_CODE,
                source="NJSLS ELA",
                short_name=STANDARD_SHORT_NAME,
                description="Analyze structural choices and their effects.",
                subject="English Language Arts",
                grade_band="11-12",
                available_modules=("concord",),
            ),
        ),
        profiles=(
            StandardsProfile(
                profile_id=PROFILE_ID,
                standards=(STANDARD_ID,),
                subject="English Language Arts",
                source="NJSLS ELA",
                title=PROFILE_TITLE,
            ),
        ),
    )


def _workspace(
    tmp_path: Path,
) -> tuple[Path, StandardsLibrary, int]:
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
    library = _library()
    write_workspace_standards_library(root, library)

    activity = create_activity_context(
        CreateActivityContextRequest(
            class_id="class-1",
            activity_id="activity-1",
            title="Standards Publication Activity",
            activity_type="project",
            scoring_orientation="standards_based",
            session_id="session-1",
            actor=_actor(),
            activity_status="active",
            session_status="active",
            standards_profile_id=PROFILE_ID,
            focus_standard_ids=(STANDARD_ID,),
            privacy_policy=PrivacyPolicy(
                classification="teacher_restricted"
            ),
        ),
        workspace_root=root,
        standards_library=library,
        clock=lambda: _clock(9),
    )
    scale = create_scoring_scale(
        CreateScoringScaleRequest(
            class_id="class-1",
            activity_id="activity-1",
            scoring_scale_id="scale-1",
            lineage_id="scale-lineage-1",
            name="Standards Scale",
            revision=1,
            scale_type="ordinal",
            levels=(
                ScoringScaleLevel(
                    value="developing",
                    label="Developing",
                    meaning="Evidence is developing.",
                    position=1,
                ),
                ScoringScaleLevel(
                    value="meeting",
                    label="Meeting",
                    meaning="Evidence meets the criterion.",
                    position=2,
                ),
            ),
            status="active",
            expected_snapshot_revision=activity.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        standards_library=library,
        clock=lambda: _clock(10),
    )
    criterion_set = create_criterion_set(
        CreateCriterionSetRequest(
            class_id="class-1",
            activity_id="activity-1",
            criterion_set_id="set-1",
            lineage_id="set-lineage-1",
            name="Text Structure",
            purpose="Qualify durable Standards identity publication.",
            revision=1,
            scope="activity_specific",
            criterion_set_kind="standard_backed",
            criteria=(
                CriterionSpec(
                    criterion_id="criterion-1",
                    key="text_structure",
                    label="Text Structure Analysis",
                    definition="Analyzes structural choices and effects.",
                    criterion_kind="standard_backed",
                    supported_target_kinds=("core_student",),
                    standard_id=STANDARD_ID,
                    default_scoring_scale_id="scale-1",
                ),
            ),
            status="active",
            expected_snapshot_revision=scale.commit.snapshot_revision,
            actor=_actor(),
            standards_profile_id=PROFILE_ID,
        ),
        workspace_root=root,
        standards_library=library,
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
        standards_library=library,
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
            value="meeting",
            basis="professional_judgment",
            rationale="Synthetic professional judgment for qualification.",
            privacy_policy=PrivacyPolicy(
                classification="teacher_restricted"
            ),
            expected_snapshot_revision=selected.commit.snapshot_revision,
            actor=_actor(),
            session_id="session-1",
        ),
        workspace_root=root,
        standards_library=library,
        clock=lambda: _clock(13),
    )
    register_concord_academic_work(
        root,
        "class-1",
        "activity-1",
        academic_intent="summative",
        lifecycle="active",
    )
    return root, library, scored.commit.snapshot_revision


def _request(revision: int) -> GenerateAcademicResultManifestRequest:
    return GenerateAcademicResultManifestRequest(
        class_id="class-1",
        activity_id="activity-1",
        expected_snapshot_revision=revision,
        actor=_actor(),
        revision_reason="initial",
    )


def test_issue129_persisted_standard_identity_reaches_core_publication_and_reader(
    tmp_path: Path,
) -> None:
    root, library, revision = _workspace(tmp_path)
    work = ModuleWorkRef("concord", "class-1", "activity-1")
    context = load_activity_read_context(root, work)

    assert context.activity.standards_profile_id == PROFILE_ID
    assert context.activity.focus_standard_ids == (STANDARD_ID,)
    assert context.graph.criterion_sets[0].standards_profile_id == PROFILE_ID
    assert context.graph.criteria[0].standard_id == STANDARD_ID
    assert context.graph.score_records[0].standard_id == STANDARD_ID

    published = publish_concord_academic_results(
        _request(revision),
        workspace_root=root,
        standards_library=library,
        clock=lambda: _clock(14),
    )

    assert published.compatibility.compatible
    assert published.compatibility.codes == ()
    assert published.publication.manifest_contract_version == (
        ACADEMIC_RESULT_MANIFEST_CONTRACT_VERSION
    )
    assert set(published.publication.capabilities) == {
        "criterion_scores",
        "standards_ratings",
    }

    content = published.manifest_generation.content
    manifest = read_academic_result_manifest(content)

    assert manifest.activity_context.standards_profile_id == PROFILE_ID
    assert manifest.activity_context.focus_standard_ids == (STANDARD_ID,)
    assert manifest.criterion_sets[0].standards_profile_id == PROFILE_ID
    assert manifest.criteria[0].standard_id == STANDARD_ID
    assert manifest.scores[0].standard_id == STANDARD_ID
    assert manifest.standards_result_projection[0].standard_id == STANDARD_ID

    support = lookup_publication_reader_support(
        get_publication_producer_profile(),
        published.publication.publication_kind,
        published.publication.manifest_contract_version,
    )
    assert support is not None
    assert support.reader_contract_version == (
        CONCORD_ACADEMIC_RESULT_READER_CONTRACT_VERSION
    )
    assert support.distribution_name == "pds-concord"


def test_issue129_reports_keep_durable_id_separate_from_teacher_depiction(
    tmp_path: Path,
    monkeypatch,
) -> None:
    root, library, _ = _workspace(tmp_path)
    context = load_activity_read_context(
        root,
        ModuleWorkRef("concord", "class-1", "activity-1"),
    )

    prepared_json = prepare_activity_analysis_report(
        context,
        report_format="json",
        standards_library=library,
        clock=lambda: _clock(14),
    )
    payload = prepared_json.payload
    assert isinstance(payload, ActivityAnalysisReport)
    standard = payload.standard_analyses[0]
    assert standard.standard_id == STANDARD_ID
    assert standard.standard_label == STANDARD_CODE
    assert standard.standard_code == STANDARD_CODE
    assert standard.standard_short_name == STANDARD_SHORT_NAME
    assert standard.standard_id != standard.standard_code

    rendered_json = render_score_analysis_report_json(prepared_json)
    data = json.loads(rendered_json.artifacts[0].content)
    standard_json = data["standards_criterion_view"][0]
    assert standard_json["standard_id"] == STANDARD_ID
    assert standard_json["standard_label"] == STANDARD_CODE
    assert standard_json["standard_code"] == STANDARD_CODE
    assert standard_json["standard_short_name"] == STANDARD_SHORT_NAME
    assert data["criterion_analysis"][0]["standard_id"] == STANDARD_ID

    prepared_csv = prepare_activity_analysis_report(
        context,
        report_format="csv",
        standards_library=library,
        clock=lambda: _clock(14),
    )
    rendered_csv = render_score_analysis_report_csv(prepared_csv)
    standards_csv = next(
        item
        for item in rendered_csv.artifacts
        if item.filename == "standards_criteria.csv"
    )
    rows = tuple(
        csv.DictReader(io.StringIO(standards_csv.content.decode("utf-8")))
    )
    assert rows[0]["standard_id"] == STANDARD_ID
    assert rows[0]["standard_label"] == STANDARD_CODE

    paragraphs: list[str] = []
    tables: list[tuple[tuple[str, ...], tuple[tuple[str, ...], ...]]] = []
    original_paragraph = score_pdf._ReportPainter.paragraph
    original_table = score_pdf._ReportPainter.table

    def capture_paragraph(
        self: object,
        text: str,
        *args: object,
        **kwargs: object,
    ) -> None:
        paragraphs.append(text)
        original_paragraph(self, text, *args, **kwargs)

    def capture_table(
        self: object,
        headers: object,
        rows: object,
        widths: object,
    ) -> None:
        header_tuple = tuple(headers)
        row_tuple = tuple(tuple(row) for row in rows)
        tables.append((header_tuple, row_tuple))
        original_table(self, header_tuple, row_tuple, widths)

    monkeypatch.setattr(score_pdf._ReportPainter, "paragraph", capture_paragraph)
    monkeypatch.setattr(score_pdf._ReportPainter, "table", capture_table)

    prepared_pdf = prepare_activity_analysis_report(
        context,
        report_format="pdf",
        standards_library=library,
        clock=lambda: _clock(14),
    )
    rendered_pdf = render_score_analysis_report_pdf(prepared_pdf)
    assert rendered_pdf.artifacts[0].content.startswith(b"%PDF")

    teacher_label = f"{STANDARD_CODE} — {STANDARD_SHORT_NAME}"
    assert f"Standard: {teacher_label}" in paragraphs
    assert not any(text.startswith("Standard ID:") for text in paragraphs)

    standards_tables = [
        rows
        for headers, rows in tables
        if headers and headers[0] == "Standard"
    ]
    assert standards_tables
    assert standards_tables[0][0][0] == teacher_label
