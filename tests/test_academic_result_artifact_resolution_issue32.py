from __future__ import annotations

import base64
import hashlib
import json
import os
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.routing_models import ModuleRecordRef, ModuleWorkRef
from pds_core.standards import (
    StandardDefinition,
    StandardsLibrary,
    StandardsProfile,
)
from pds_core.workspace import ensure_workspace_root
from PIL import Image

import concord.academic_result_artifacts as artifacts_module
import concord.artifact_rendering as artifact_rendering_module
import concord.storage as storage_module
from concord.academic_result_artifacts import (
    AcademicResultArtifactAuthorizationDecision,
    ConcordAcademicResultArtifactAmbiguityError,
    ConcordAcademicResultArtifactAuthorizationError,
    ConcordAcademicResultArtifactIntegrityError,
    ConcordAcademicResultArtifactNotFoundError,
    ConcordAcademicResultArtifactUnavailableError,
    ConcordAcademicResultArtifactValidationError,
)
from concord.academic_result_manifest import (
    ACADEMIC_RESULT_MANIFEST_CONTRACT_VERSION,
    ACADEMIC_RESULT_MANIFEST_RECORD_TYPE,
    AcademicResultManifest,
    ActivityContextProjection,
    CriterionProjection,
    CriterionSetProjection,
    EvidenceReferenceProjection,
    ManifestProjection,
    ManifestRecordSet,
    PrivacyProjection,
    PublicActor,
    ScaleLevelProjection,
    ScoreEvidenceLinkProjection,
    ScoreProjection,
    ScoringScaleProjection,
    TargetReferenceProjection,
    with_semantic_projection_digest,
)
from concord.academic_result_manifest_generation import (
    GenerateAcademicResultManifestRequest,
    generate_academic_result_manifest,
)
from concord.academic_result_reader import lookup_academic_result_scale_level
from concord.academic_work_registration import register_concord_academic_work
from concord.model_conversion import record_from_dict, record_to_dict
from concord.model_validation import ConcordRecordGraph
from concord.models import (
    Activity,
    ActorReference,
    ArtifactAuthor,
    ArtifactInstance,
    ArtifactPage,
    ArtifactSubject,
    EvidenceReference,
    ParticipantReference,
    PrivacyPolicy,
    Provenance,
    ScanReference,
    ScoreEvidenceLink,
    ScoreRecord,
    ScoreTargetReference,
    Session,
    SubjectReference,
)
from concord.storage import (
    commit_record_batch,
    load_record_graph_at_snapshot,
)
from concord.storage_errors import ConcordStorageNotFoundError
from concord.storage_models import ConcordLoadedRecordGraph
from concord.storage_paths import record_revision_path
from concord.storage_serialization import serialize
from concord.workflows.models import WorkflowActor

STANDARDS_FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "native_records"
    / "standards_activity.json"
)
EVIDENCE_ONLY_FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "native_records"
    / "evidence_only_activity.json"
)
REPRESENTATIVE_SOURCE_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91JpzAAAAFklEQVR4nGPUCKhgYGBg"
    "YmBgYGBgAAALGgD0KRPd0QAAAABJRU5ErkJggg=="
)


def _timestamp() -> str:
    return "2026-08-15T09:00:00-04:00"


def _actor() -> ActorReference:
    return ActorReference(
        actor_kind="authorized_adult",
        actor_id="teacher-1",
        owning_system="core",
    )


def _provenance() -> Provenance:
    return Provenance(
        actor=_actor(),
        timestamp=_timestamp(),
        source_kind="manual",
    )


def _privacy() -> PrivacyPolicy:
    return PrivacyPolicy(
        classification="teacher_restricted",
    )


def _work() -> ModuleWorkRef:
    return ModuleWorkRef(
        module_id="concord",
        class_id="class-1",
        work_id="activity-1",
    )


def _native_evidence(kind: str = "artifact_instance") -> EvidenceReference:
    return EvidenceReference(
        evidence_kind=kind,
        owning_system="concord",
        record_id="artifact-1" if kind == "artifact_instance" else "page-1",
        moderation_requirement="not_required",
    )


def _native_graph(kind: str = "artifact_instance") -> ConcordRecordGraph:
    activity = Activity(
        activity_id="activity-1",
        class_reference=ModuleRecordRef(
            module_id="core",
            record_kind="class",
            record_id="class-1",
        ),
        title="Synthetic local Activity",
        activity_type="local:laboratory",
        scoring_orientation="local_criteria_only",
        status="active",
        created_provenance=_provenance(),
    )
    session = Session(
        session_id="session-1",
        activity_id="activity-1",
        sequence=1,
        status="active",
        created_provenance=_provenance(),
    )
    artifact = ArtifactInstance(
        artifact_instance_id="artifact-1",
        template_version_id="template-1",
        activity_id="activity-1",
        artifact_category="laboratory_record",
        generation_status="completed",
        expected_return_status="returned_expected",
        artifact_status="returned",
        privacy_policy=_privacy(),
        page_ids=("page-1", "page-2"),
        created_provenance=_provenance(),
        session_id="session-1",
        group_id="group-1",
    )
    pages = (
        ArtifactPage(
            artifact_page_id="page-1",
            artifact_instance_id="artifact-1",
            page_number=1,
            page_kind="primary",
            return_expected=True,
            route_required=False,
            page_status="returned",
            created_provenance=_provenance(),
        ),
        ArtifactPage(
            artifact_page_id="page-2",
            artifact_instance_id="artifact-1",
            page_number=2,
            page_kind="continuation",
            return_expected=True,
            route_required=False,
            page_status="returned",
            created_provenance=_provenance(),
            continuation_of_page_id="page-1",
        ),
    )
    author = ArtifactAuthor(
        artifact_author_id="author-1",
        artifact_instance_id="artifact-1",
        author_reference=ParticipantReference(
            participant_kind="core_student",
            participant_id="student-author",
            owning_system="core",
        ),
        authorship_mode="recorder_for_group",
        attribution_status="confirmed",
        attribution_source="teacher",
        created_provenance=_provenance(),
        represented_group_id="group-1",
        representation_status="recorder_summary",
    )
    subject = ArtifactSubject(
        artifact_subject_id="subject-1",
        artifact_instance_id="artifact-1",
        subject_reference=SubjectReference(
            subject_kind="core_student",
            subject_id="student-subject",
            owning_system="core",
        ),
        subject_role="observed_participant",
        confirmation_status="confirmed",
        assignment_source="teacher",
        created_provenance=_provenance(),
    )
    score = ScoreRecord(
        score_record_id="score-1",
        activity_id="activity-1",
        target_reference=ScoreTargetReference(
            target_kind="concord_artifact_instance",
            target_id="artifact-1",
            owning_system="concord",
        ),
        criterion_id="criterion-1",
        score_kind="local",
        scoring_scale_id="scale-1",
        disposition="scored",
        basis="linked_evidence",
        scorer=_actor(),
        scored_at=_timestamp(),
        moderation_complete=True,
        privacy_policy=_privacy(),
        value="met",
    )
    link = ScoreEvidenceLink(
        score_evidence_link_id="link-1",
        score_record_id="score-1",
        evidence_reference=_native_evidence(kind),
        relevance_description="Exact synthetic Artifact evidence.",
        status="active",
        created_provenance=_provenance(),
        significance="primary",
    )
    return ConcordRecordGraph(
        activities=(activity,),
        sessions=(session,),
        artifact_instances=(artifact,),
        artifact_pages=pages,
        artifact_authors=(author,),
        artifact_subjects=(subject,),
        score_records=(score,),
        score_evidence_links=(link,),
    )


def _public_evidence(kind: str = "artifact_instance") -> EvidenceReferenceProjection:
    return EvidenceReferenceProjection(
        evidence_kind=kind,
        owning_system="concord",
        record_id="artifact-1" if kind == "artifact_instance" else "page-1",
        contract_version=None,
        source_publication_reference=None,
        immutable_source_version=None,
        locator=None,
        subject_context=(),
        moderation_requirement="not_required",
    )


def _manifest(
    kind: str = "artifact_instance", revision: int = 7
) -> AcademicResultManifest:
    public_actor = PublicActor(
        actor_kind="authorized_adult",
        actor_id="teacher-1",
        owning_system="core",
    )
    work = _work()
    criterion_set = CriterionSetProjection(
        criterion_set_id="set-1",
        lineage_id="set-lineage",
        revision=1,
        criterion_set_kind="local",
        scope="activity_specific",
        criterion_ids=("criterion-1",),
        status="active",
        supersedes_criterion_set_id=None,
        standards_profile_id=None,
    )
    criterion = CriterionProjection(
        criterion_id="criterion-1",
        criterion_set_id="set-1",
        key="local_result",
        label="Local result",
        definition="Synthetic local result criterion.",
        criterion_kind="local",
        supported_target_kinds=("concord_artifact_instance",),
        status="active",
        standard_id=None,
        alignment_standard_ids=(),
        default_scoring_scale_id="scale-1",
    )
    scale = ScoringScaleProjection(
        scoring_scale_id="scale-1",
        lineage_id="scale-lineage",
        name="Synthetic result scale",
        revision=1,
        scale_type="teacher_defined",
        levels=(
            ScaleLevelProjection(
                value="met",
                label="Met",
                meaning="Criterion met.",
                position=None,
                description=None,
            ),
        ),
        status="active",
        supersedes_scoring_scale_id=None,
    )
    score = ScoreProjection(
        score_record_id="score-1",
        activity_id="activity-1",
        session_id=None,
        target_reference=TargetReferenceProjection(
            target_kind="concord_artifact_instance",
            target_id="artifact-1",
            owning_system="concord",
            contract_version=None,
        ),
        criterion_id="criterion-1",
        score_kind="local",
        standard_id=None,
        scoring_scale_id="scale-1",
        disposition="scored",
        value="met",
        basis="linked_evidence",
        scorer=public_actor,
        scored_at=datetime(2026, 8, 15, 13, 0, tzinfo=timezone.utc),
        moderation_complete=True,
        status_reason=None,
        supersedes_score_record_id=None,
        current_state="current",
    )
    link = ScoreEvidenceLinkProjection(
        score_evidence_link_id="link-1",
        score_record_id="score-1",
        evidence_reference=_public_evidence(kind),
        evidence_locator=None,
        subject_context=(),
        relevance_description="Exact synthetic Artifact evidence.",
        significance="primary",
        moderation_record_id=None,
        status="active",
        supersedes_score_evidence_link_id=None,
    )
    candidate = AcademicResultManifest(
        record_type=ACADEMIC_RESULT_MANIFEST_RECORD_TYPE,
        contract_version=ACADEMIC_RESULT_MANIFEST_CONTRACT_VERSION,
        producer_module_id="concord",
        generated_at=datetime(2026, 8, 15, 13, 5, tzinfo=timezone.utc),
        record_set=ManifestRecordSet("academic_results", 1),
        work=work,
        source_activity=ModuleRecordRef(
            module_id="concord",
            record_kind="activity",
            record_id="activity-1",
            contract_version="concord_activity_v1",
        ),
        projection=ManifestProjection(
            source_snapshot_revision=revision,
            projection_digest_algorithm="sha256",
            projection_digest="0" * 64,
            generated_by=public_actor,
            revision_reason="initial",
        ),
        activity_context=ActivityContextProjection(
            activity_id="activity-1",
            class_id="class-1",
            title="Synthetic local Activity",
            scoring_orientation="local_criteria_only",
            standards_profile_id=None,
            focus_standard_ids=(),
            criterion_set_ids=("set-1",),
        ),
        criterion_sets=(criterion_set,),
        criteria=(criterion,),
        scoring_scales=(scale,),
        scores=(score,),
        score_evidence_links=(link,),
        moderation_records=(),
        standards_result_projection=(),
        privacy=PrivacyProjection(
            classification="teacher_restricted",
            audience_references=(),
            policy_reference=None,
            inherited_from=None,
        ),
    )
    return with_semantic_projection_digest(candidate)


class _Gate:
    def __init__(self, status: str = "allowed") -> None:
        self.status = status
        self.requests = []

    def authorize(self, request):
        self.requests.append(request)
        return AcademicResultArtifactAuthorizationDecision(self.status)


def _loaded(
    kind: str = "artifact_instance", revision: int = 7
) -> ConcordLoadedRecordGraph:
    return ConcordLoadedRecordGraph(
        graph=_native_graph(kind),
        snapshot_revision=revision,
        snapshot_sha256="a" * 64,
    )


def test_historical_graph_loader_reads_exact_revision_without_current_pointer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = ensure_workspace_root(tmp_path / "workspace")
    metadata = create_class_metadata(
        "class-1",
        "2026-2027",
        created_at=datetime(2026, 8, 15, tzinfo=timezone.utc),
    )
    write_class_metadata_for_class(root, metadata)
    fixture = json.loads(EVIDENCE_ONLY_FIXTURE.read_text(encoding="utf-8"))
    activity = record_from_dict("activity", fixture["records"][0]["body"])
    session = record_from_dict("session", fixture["records"][1]["body"])
    assert isinstance(activity, Activity)
    assert isinstance(session, Session)

    commit_record_batch(
        root,
        activity.work_reference,
        (activity, session),
        expected_snapshot_revision=None,
    )
    changed = replace(session, notes="Synthetic snapshot two.")
    commit_record_batch(
        root,
        activity.work_reference,
        (changed,),
        expected_snapshot_revision=1,
    )

    def forbidden_current(*_args, **_kwargs):
        raise AssertionError("historical load must not consult current.json")

    monkeypatch.setattr(storage_module, "load_current_snapshot", forbidden_current)
    first = load_record_graph_at_snapshot(root, activity.work_reference, 1)
    second = load_record_graph_at_snapshot(root, activity.work_reference, 2)

    assert first.snapshot_revision == 1
    assert first.graph.sessions == (session,)
    assert second.snapshot_revision == 2
    assert second.graph.sessions == (changed,)


@pytest.mark.parametrize("status", ["denied", "unresolved"])
def test_denied_or_unresolved_authorization_performs_no_native_io(
    status: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden_loader(*_args, **_kwargs):
        raise AssertionError("native I/O occurred before authorization")

    monkeypatch.setattr(
        artifacts_module,
        "load_record_graph_at_snapshot",
        forbidden_loader,
    )
    gate = _Gate(status)
    with pytest.raises(ConcordAcademicResultArtifactAuthorizationError):
        artifacts_module._resolve_authorized_academic_result_artifact_context(
            "workspace-does-not-need-to-exist",
            _manifest(),
            "link-1",
            purpose="consumer review",
            authorization_gate=gate,
        )
    assert len(gate.requests) == 1
    assert gate.requests[0].source_snapshot_revision == 7


def test_gate_exception_fails_closed_before_native_io(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class BrokenGate:
        def authorize(self, request):
            raise RuntimeError("synthetic authorization outage")

    def forbidden_loader(*_args, **_kwargs):
        raise AssertionError("native I/O occurred after failed authorization")

    monkeypatch.setattr(
        artifacts_module,
        "load_record_graph_at_snapshot",
        forbidden_loader,
    )
    with pytest.raises(ConcordAcademicResultArtifactAuthorizationError):
        artifacts_module._resolve_authorized_academic_result_artifact_context(
            "workspace-does-not-need-to-exist",
            _manifest(),
            "link-1",
            purpose="consumer review",
            authorization_gate=BrokenGate(),
        )


def test_allowed_request_loads_only_manifest_historical_revision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = []

    def exact_loader(root, work, revision):
        calls.append((root, work, revision))
        return _loaded(revision=revision)

    monkeypatch.setattr(
        artifacts_module,
        "load_record_graph_at_snapshot",
        exact_loader,
    )
    gate = _Gate("allowed")
    context = artifacts_module._resolve_authorized_academic_result_artifact_context(
        "synthetic-root",
        _manifest(revision=7),
        "link-1",
        purpose="consumer review",
        authorization_gate=gate,
    )

    assert calls == [("synthetic-root", _work(), 7)]
    assert context.loaded.snapshot_revision == 7
    assert context.request.source_snapshot_revision == 7
    assert context.artifact.artifact_instance_id == "artifact-1"
    assert tuple(page.artifact_page_id for page in context.artifact.pages) == (
        "page-1",
        "page-2",
    )


def test_exact_historical_evidence_projection_must_match_manifest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    graph = _native_graph()
    changed_link = replace(
        graph.score_evidence_links[0],
        relevance_description="Different historical meaning.",
    )
    drifted = replace(graph, score_evidence_links=(changed_link,))
    monkeypatch.setattr(
        artifacts_module,
        "load_record_graph_at_snapshot",
        lambda *_args, **_kwargs: ConcordLoadedRecordGraph(
            drifted, 7, "b" * 64
        ),
    )
    with pytest.raises(
        ConcordAcademicResultArtifactIntegrityError,
        match="disagrees with the manifest projection",
    ):
        artifacts_module._resolve_authorized_academic_result_artifact_context(
            "synthetic-root",
            _manifest(),
            "link-1",
            purpose="consumer review",
            authorization_gate=_Gate(),
        )


def test_missing_historical_score_or_link_fails_exactly_after_authorization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    graph = _native_graph()
    without_score = replace(graph, score_records=())
    monkeypatch.setattr(
        artifacts_module,
        "load_record_graph_at_snapshot",
        lambda *_args, **_kwargs: ConcordLoadedRecordGraph(
            without_score, 7, "c" * 64
        ),
    )
    with pytest.raises(ConcordAcademicResultArtifactNotFoundError):
        artifacts_module._resolve_authorized_academic_result_artifact_context(
            "synthetic-root",
            _manifest(),
            "link-1",
            purpose="consumer review",
            authorization_gate=_Gate(),
        )

    without_link = replace(graph, score_evidence_links=())
    monkeypatch.setattr(
        artifacts_module,
        "load_record_graph_at_snapshot",
        lambda *_args, **_kwargs: ConcordLoadedRecordGraph(
            without_link, 7, "d" * 64
        ),
    )
    with pytest.raises(ConcordAcademicResultArtifactNotFoundError):
        artifacts_module._resolve_authorized_academic_result_artifact_context(
            "synthetic-root",
            _manifest(),
            "link-1",
            purpose="consumer review",
            authorization_gate=_Gate(),
        )


def test_artifact_page_evidence_resolves_exact_page_and_parent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        artifacts_module,
        "load_record_graph_at_snapshot",
        lambda *_args, **_kwargs: _loaded("artifact_page"),
    )
    context = artifacts_module._resolve_authorized_academic_result_artifact_context(
        "synthetic-root",
        _manifest("artifact_page"),
        "link-1",
        purpose="consumer review",
        authorization_gate=_Gate(),
    )
    assert context.evidence_page is not None
    assert context.evidence_page.artifact_page_id == "page-1"
    assert context.artifact_instance.artifact_instance_id == "artifact-1"


def test_author_and_subject_public_projections_remain_distinct(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        artifacts_module,
        "load_record_graph_at_snapshot",
        lambda *_args, **_kwargs: _loaded(),
    )
    context = artifacts_module._resolve_authorized_academic_result_artifact_context(
        "synthetic-root",
        _manifest(),
        "link-1",
        purpose="consumer review",
        authorization_gate=_Gate(),
    )
    author_reference = context.authors[0].author_reference
    assert author_reference is not None
    assert hasattr(author_reference, "participant_id")
    assert author_reference.participant_id == "student-author"
    assert context.subjects[0].subject_reference.subject_id == "student-subject"
    assert (
        author_reference.participant_id
        != context.subjects[0].subject_reference.subject_id
    )


def test_artifact_resolution_source_never_uses_current_snapshot_reader() -> None:
    source = Path(artifacts_module.__file__).read_text(encoding="utf-8")
    assert "load_current_snapshot" not in source
    assert "load_current_record_graph" not in source
    assert "registry_services" not in source
    assert "academic_catalog" not in source



def _routable_graph(kind: str = "artifact_instance") -> ConcordRecordGraph:
    graph = _native_graph(kind)
    pages = tuple(
        replace(
            page,
            route_required=True,
            route_id=f"route-{page.page_number}",
            human_fallback=f"Synthetic route {page.page_number}",
        )
        for page in graph.artifact_pages
    )
    return replace(graph, artifact_pages=pages)


def _retained_image_scan(
    root: Path,
    page: ArtifactPage,
    *,
    scan_reference_id: str,
    source_scan_id: str,
    filename: str,
    color: tuple[int, int, int],
) -> ScanReference:
    path = root / "scans" / "source" / "2026-08-15" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (60, 80), color).save(path)
    assert page.route_id is not None
    return ScanReference(
        scan_reference_id=scan_reference_id,
        activity_id="activity-1",
        artifact_page_id=page.artifact_page_id,
        route_id=page.route_id,
        source_scan_id=source_scan_id,
        source_page_number=1,
        retained_source_relative_path=path.relative_to(root).as_posix(),
        retained_source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        created_provenance=_provenance(),
    )


def _retained_pdf_scan(
    root: Path,
    page: ArtifactPage,
    *,
    source_page_number: int,
) -> ScanReference:
    path = root / "scans" / "source" / "2026-08-15" / "multipage.pdf"
    path.parent.mkdir(parents=True, exist_ok=True)
    first = Image.new("RGB", (60, 80), (255, 0, 0))
    second = Image.new("RGB", (60, 80), (0, 255, 0))
    try:
        first.save(path, "PDF", save_all=True, append_images=[second])
    finally:
        first.close()
        second.close()
    assert page.route_id is not None
    return ScanReference(
        scan_reference_id="scan-ref-pdf",
        activity_id="activity-1",
        artifact_page_id=page.artifact_page_id,
        route_id=page.route_id,
        source_scan_id="source-pdf",
        source_page_number=source_page_number,
        retained_source_relative_path=path.relative_to(root).as_posix(),
        retained_source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        created_provenance=_provenance(),
    )


def _install_render_graph(
    monkeypatch: pytest.MonkeyPatch,
    graph: ConcordRecordGraph,
) -> None:
    monkeypatch.setattr(
        artifacts_module,
        "load_record_graph_at_snapshot",
        lambda *_args, **_kwargs: ConcordLoadedRecordGraph(
            graph=graph,
            snapshot_revision=7,
            snapshot_sha256="e" * 64,
        ),
    )


def _pdf_page_count(content: bytes) -> int:
    import pypdfium2

    document = pypdfium2.PdfDocument(content)
    try:
        return len(document)
    finally:
        document.close()


def _pdf_center_pixel(content: bytes) -> tuple[int, int, int]:
    import pypdfium2

    document = pypdfium2.PdfDocument(content)
    try:
        page = document[0]
        try:
            image = page.render(scale=1).to_pil().convert("RGB")
            try:
                return image.getpixel((image.width // 2, image.height // 2))
            finally:
                image.close()
        finally:
            page.close()
    finally:
        document.close()


def test_authorized_artifact_instance_returns_deterministic_read_only_pdf(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    graph = _routable_graph()
    page_one, page_two = graph.artifact_pages
    scans = (
        _retained_image_scan(
            root,
            page_one,
            scan_reference_id="scan-ref-one",
            source_scan_id="source-one",
            filename="one.png",
            color=(255, 0, 0),
        ),
        _retained_image_scan(
            root,
            page_two,
            scan_reference_id="scan-ref-two",
            source_scan_id="source-two",
            filename="two.png",
            color=(0, 255, 0),
        ),
    )
    graph = replace(graph, scan_references=scans)
    _install_render_graph(monkeypatch, graph)
    before = tuple(sorted(path.relative_to(root) for path in root.rglob("*")))

    first = artifacts_module.read_authorized_academic_result_artifact(
        root,
        _manifest(),
        "link-1",
        purpose="consumer review",
        authorization_gate=_Gate(),
    )
    second = artifacts_module.read_authorized_academic_result_artifact(
        root,
        _manifest(),
        "link-1",
        purpose="consumer review",
        authorization_gate=_Gate(),
    )
    after = tuple(sorted(path.relative_to(root) for path in root.rglob("*")))

    assert first.content.startswith(b"%PDF")
    assert first.media_type == "application/pdf"
    assert first.sha256 == hashlib.sha256(first.content).hexdigest()
    assert first.byte_size == len(first.content)
    assert first.content == second.content
    assert first.sha256 == second.sha256
    assert _pdf_page_count(first.content) == 2
    assert after == before
    assert not any("assemblies" in path.parts for path in after)


def test_artifact_page_reads_only_exact_physical_pdf_page(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    graph = _routable_graph("artifact_page")
    evidence_page = graph.artifact_pages[0]
    scan = _retained_pdf_scan(root, evidence_page, source_page_number=2)
    graph = replace(graph, scan_references=(scan,))
    _install_render_graph(monkeypatch, graph)

    result = artifacts_module.read_authorized_academic_result_artifact(
        root,
        _manifest("artifact_page"),
        "link-1",
        purpose="consumer review",
        authorization_gate=_Gate(),
    )

    assert _pdf_page_count(result.content) == 1
    red, green, blue = _pdf_center_pixel(result.content)
    assert green > red + 100
    assert green > blue + 100


def test_artifact_instance_missing_returned_page_is_unavailable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    graph = _routable_graph()
    page_one = graph.artifact_pages[0]
    scan = _retained_image_scan(
        root,
        page_one,
        scan_reference_id="scan-ref-one",
        source_scan_id="source-one",
        filename="one.png",
        color=(255, 0, 0),
    )
    graph = replace(graph, scan_references=(scan,))
    _install_render_graph(monkeypatch, graph)

    with pytest.raises(ConcordAcademicResultArtifactUnavailableError):
        artifacts_module.read_authorized_academic_result_artifact(
            root,
            _manifest(),
            "link-1",
            purpose="consumer review",
            authorization_gate=_Gate(),
        )


def test_multiple_returned_occurrences_fail_closed_without_scan_selector(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    graph = _routable_graph("artifact_page")
    page = graph.artifact_pages[0]
    scans = (
        _retained_image_scan(
            root,
            page,
            scan_reference_id="scan-ref-one",
            source_scan_id="source-one",
            filename="one.png",
            color=(255, 0, 0),
        ),
        _retained_image_scan(
            root,
            page,
            scan_reference_id="scan-ref-two",
            source_scan_id="source-two",
            filename="two.png",
            color=(0, 255, 0),
        ),
    )
    graph = replace(graph, scan_references=scans)
    _install_render_graph(monkeypatch, graph)

    with pytest.raises(ConcordAcademicResultArtifactAmbiguityError) as caught:
        artifacts_module.read_authorized_academic_result_artifact(
            root,
            _manifest("artifact_page"),
            "link-1",
            purpose="consumer review",
            authorization_gate=_Gate(),
        )
    message = str(caught.value)
    assert "scan-ref-one" not in message
    assert "scan-ref-two" not in message


def test_retained_source_digest_failure_maps_to_privacy_safe_integrity_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    graph = _routable_graph("artifact_page")
    page = graph.artifact_pages[0]
    scan = _retained_image_scan(
        root,
        page,
        scan_reference_id="scan-ref-one",
        source_scan_id="source-one",
        filename="private-source.png",
        color=(10, 20, 30),
    )
    path = root / scan.retained_source_relative_path
    path.write_bytes(b"tampered")
    graph = replace(graph, scan_references=(scan,))
    _install_render_graph(monkeypatch, graph)

    with pytest.raises(ConcordAcademicResultArtifactIntegrityError) as caught:
        artifacts_module.read_authorized_academic_result_artifact(
            root,
            _manifest("artifact_page"),
            "link-1",
            purpose="consumer review",
            authorization_gate=_Gate(),
        )
    message = str(caught.value)
    assert "private-source.png" not in message
    assert str(root) not in message


def test_non_return_expected_artifact_page_is_not_added_to_instance_pdf(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    graph = _routable_graph()
    page_one, page_two = graph.artifact_pages
    page_two = replace(page_two, return_expected=False)
    scans = (
        _retained_image_scan(
            root,
            page_one,
            scan_reference_id="scan-ref-one",
            source_scan_id="source-one",
            filename="one.png",
            color=(255, 0, 0),
        ),
        _retained_image_scan(
            root,
            page_two,
            scan_reference_id="scan-ref-two",
            source_scan_id="source-two",
            filename="two.png",
            color=(0, 255, 0),
        ),
    )
    graph = replace(
        graph,
        artifact_pages=(page_one, page_two),
        scan_references=scans,
    )
    _install_render_graph(monkeypatch, graph)

    result = artifacts_module.read_authorized_academic_result_artifact(
        root,
        _manifest(),
        "link-1",
        purpose="consumer review",
        authorization_gate=_Gate(),
    )
    assert _pdf_page_count(result.content) == 1


def _external_evidence_manifest() -> AcademicResultManifest:
    base = _manifest()
    external_evidence = EvidenceReferenceProjection(
        evidence_kind="scoreform_result",
        owning_system="scoreform",
        record_id="external-result-1",
        contract_version="scoreform_result_v1",
        source_publication_reference=None,
        immutable_source_version="attempt-1",
        locator=None,
        subject_context=(),
        moderation_requirement="not_required",
    )
    external_link = replace(
        base.score_evidence_links[0],
        evidence_reference=external_evidence,
    )
    candidate = replace(
        base,
        score_evidence_links=(external_link,),
        projection=replace(
            base.projection,
            projection_digest="0" * 64,
        ),
    )
    return with_semantic_projection_digest(candidate)


def test_external_evidence_is_rejected_before_gate_or_native_io(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ForbiddenGate:
        def authorize(self, request):
            raise AssertionError("external evidence must not reach authorization")

    def forbidden_loader(*_args, **_kwargs):
        raise AssertionError("external evidence must not reach native I/O")

    monkeypatch.setattr(
        artifacts_module,
        "load_record_graph_at_snapshot",
        forbidden_loader,
    )
    with pytest.raises(ConcordAcademicResultArtifactValidationError):
        artifacts_module.read_authorized_academic_result_artifact(
            "workspace-does-not-need-to-exist",
            _external_evidence_manifest(),
            "link-1",
            purpose="consumer review",
            authorization_gate=ForbiddenGate(),
        )


def test_public_projection_excludes_superseded_and_unrelated_attribution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    graph = _native_graph()
    predecessor_author = graph.artifact_authors[0]
    current_author = replace(
        predecessor_author,
        artifact_author_id="author-2",
        author_reference=ParticipantReference(
            participant_kind="core_student",
            participant_id="student-current-author",
            owning_system="core",
        ),
        supersedes_artifact_author_id=predecessor_author.artifact_author_id,
    )
    unrelated_author = replace(
        predecessor_author,
        artifact_author_id="author-unrelated",
        artifact_instance_id="artifact-unrelated",
        author_reference=ParticipantReference(
            participant_kind="core_student",
            participant_id="student-unrelated-author",
            owning_system="core",
        ),
    )
    predecessor_subject = graph.artifact_subjects[0]
    current_subject = replace(
        predecessor_subject,
        artifact_subject_id="subject-2",
        subject_reference=SubjectReference(
            subject_kind="core_student",
            subject_id="student-current-subject",
            owning_system="core",
        ),
        supersedes_artifact_subject_id=predecessor_subject.artifact_subject_id,
    )
    unrelated_subject = replace(
        predecessor_subject,
        artifact_subject_id="subject-unrelated",
        artifact_instance_id="artifact-unrelated",
        subject_reference=SubjectReference(
            subject_kind="core_student",
            subject_id="student-unrelated-subject",
            owning_system="core",
        ),
    )
    graph = replace(
        graph,
        artifact_authors=(
            predecessor_author,
            current_author,
            unrelated_author,
        ),
        artifact_subjects=(
            predecessor_subject,
            current_subject,
            unrelated_subject,
        ),
    )
    monkeypatch.setattr(
        artifacts_module,
        "load_record_graph_at_snapshot",
        lambda *_args, **_kwargs: ConcordLoadedRecordGraph(
            graph=graph,
            snapshot_revision=7,
            snapshot_sha256="f" * 64,
        ),
    )

    context = artifacts_module._resolve_authorized_academic_result_artifact_context(
        "synthetic-root",
        _manifest(),
        "link-1",
        purpose="consumer review",
        authorization_gate=_Gate(),
    )

    assert tuple(item.artifact_author_id for item in context.authors) == ("author-2",)
    assert tuple(
        item.artifact_subject_id for item in context.subjects
    ) == ("subject-2",)
    author_reference = context.authors[0].author_reference
    assert author_reference is not None
    assert hasattr(author_reference, "participant_id")
    assert author_reference.participant_id == "student-current-author"
    assert context.subjects[0].subject_reference.subject_id == "student-current-subject"
    assert context.authors[0].authorship_mode == "recorder_for_group"
    assert context.authors[0].represented_group_id == "group-1"


def _file_bytes_snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_authorized_read_leaves_every_existing_workspace_file_byte_identical(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    graph = _routable_graph()
    scans = tuple(
        _retained_image_scan(
            root,
            page,
            scan_reference_id=f"scan-ref-{page.page_number}",
            source_scan_id=f"source-{page.page_number}",
            filename=f"page-{page.page_number}.png",
            color=(100 * page.page_number, 10, 20),
        )
        for page in graph.artifact_pages
    )
    graph = replace(graph, scan_references=scans)
    _install_render_graph(monkeypatch, graph)
    before = _file_bytes_snapshot(root)

    artifacts_module.read_authorized_academic_result_artifact(
        root,
        _manifest(),
        "link-1",
        purpose="consumer review",
        authorization_gate=_Gate(),
    )

    assert _file_bytes_snapshot(root) == before


def test_verified_retained_bytes_are_the_exact_bytes_passed_to_renderer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    graph = _routable_graph("artifact_page")
    page = graph.artifact_pages[0]
    scan = _retained_image_scan(
        root,
        page,
        scan_reference_id="scan-ref-one",
        source_scan_id="source-one",
        filename="verified.png",
        color=(255, 0, 0),
    )
    graph = replace(graph, scan_references=(scan,))
    _install_render_graph(monkeypatch, graph)
    source_path = root / scan.retained_source_relative_path
    expected_source_bytes = source_path.read_bytes()

    rendered_source_bytes: list[bytes] = []
    original_render = artifact_rendering_module.render_retained_source_page

    def record_rendered_source(source, source_page_number):
        rendered_source_bytes.append(source.content)
        return original_render(source, source_page_number)

    monkeypatch.setattr(
        artifact_rendering_module,
        "render_retained_source_page",
        record_rendered_source,
    )

    original_read_bytes = Path.read_bytes

    def forbid_retained_path_reread(path: Path) -> bytes:
        if path == source_path:
            raise AssertionError(
                "retained source must not be reopened through Path.read_bytes"
            )
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", forbid_retained_path_reread)

    result = artifacts_module.read_authorized_academic_result_artifact(
        root,
        _manifest("artifact_page"),
        "link-1",
        purpose="consumer review",
        authorization_gate=_Gate(),
    )

    assert rendered_source_bytes == [expected_source_bytes]
    red, green, blue = _pdf_center_pixel(result.content)
    assert red > green + 100
    assert red > blue + 100


def test_missing_historical_storage_error_does_not_expose_internal_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def secret_loader(*_args, **_kwargs):
        raise ConcordStorageNotFoundError(
            r"canonical object not found: C:\private\concord\state\7.json"
        )

    monkeypatch.setattr(
        artifacts_module,
        "load_record_graph_at_snapshot",
        secret_loader,
    )
    with pytest.raises(ConcordAcademicResultArtifactNotFoundError) as caught:
        artifacts_module._resolve_authorized_academic_result_artifact_context(
            "synthetic-root",
            _manifest(),
            "link-1",
            purpose="consumer review",
            authorization_gate=_Gate(),
        )

    assert "private" not in str(caught.value).lower()
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None


def test_missing_retained_source_public_error_has_no_private_exception_chain(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    graph = _routable_graph("artifact_page")
    page = graph.artifact_pages[0]
    scan = _retained_image_scan(
        root,
        page,
        scan_reference_id="scan-ref-one",
        source_scan_id="source-one",
        filename="private-missing.png",
        color=(10, 20, 30),
    )
    source_path = root / scan.retained_source_relative_path
    source_path.unlink()
    graph = replace(graph, scan_references=(scan,))
    _install_render_graph(monkeypatch, graph)

    with pytest.raises(ConcordAcademicResultArtifactIntegrityError) as caught:
        artifacts_module.read_authorized_academic_result_artifact(
            root,
            _manifest("artifact_page"),
            "link-1",
            purpose="consumer review",
            authorization_gate=_Gate(),
        )

    assert "private-missing.png" not in str(caught.value)
    assert str(root) not in str(caught.value)
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None


def test_artifact_page_source_page_out_of_bounds_is_integrity_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    graph = _routable_graph("artifact_page")
    page = graph.artifact_pages[0]
    scan = _retained_pdf_scan(root, page, source_page_number=3)
    graph = replace(graph, scan_references=(scan,))
    _install_render_graph(monkeypatch, graph)

    with pytest.raises(ConcordAcademicResultArtifactIntegrityError):
        artifacts_module.read_authorized_academic_result_artifact(
            root,
            _manifest("artifact_page"),
            "link-1",
            purpose="consumer review",
            authorization_gate=_Gate(),
        )


def test_retained_source_symlink_is_rejected_without_path_disclosure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    graph = _routable_graph("artifact_page")
    page = graph.artifact_pages[0]

    outside = tmp_path / "outside.png"
    Image.new("RGB", (60, 80), (20, 30, 40)).save(outside)
    link = root / "scans" / "source" / "2026-08-15" / "linked.png"
    link.parent.mkdir(parents=True, exist_ok=True)
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError) as error:
        pytest.skip(f"filesystem cannot create source symlink: {error}")

    assert page.route_id is not None
    scan = ScanReference(
        scan_reference_id="scan-ref-link",
        activity_id="activity-1",
        artifact_page_id=page.artifact_page_id,
        route_id=page.route_id,
        source_scan_id="source-link",
        source_page_number=1,
        retained_source_relative_path=link.relative_to(root).as_posix(),
        retained_source_sha256=hashlib.sha256(outside.read_bytes()).hexdigest(),
        created_provenance=_provenance(),
    )
    graph = replace(graph, scan_references=(scan,))
    _install_render_graph(monkeypatch, graph)

    with pytest.raises(ConcordAcademicResultArtifactIntegrityError) as caught:
        artifacts_module.read_authorized_academic_result_artifact(
            root,
            _manifest("artifact_page"),
            "link-1",
            purpose="consumer review",
            authorization_gate=_Gate(),
        )

    assert "linked.png" not in str(caught.value)
    assert str(outside) not in str(caught.value)
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None


def test_gate_exception_does_not_escape_deployment_policy_details(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class SecretGate:
        def authorize(self, request):
            raise RuntimeError("secret role-matrix detail")

    monkeypatch.setattr(
        artifacts_module,
        "load_record_graph_at_snapshot",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("native I/O must not occur")
        ),
    )
    with pytest.raises(ConcordAcademicResultArtifactAuthorizationError) as caught:
        artifacts_module.read_authorized_academic_result_artifact(
            "workspace-does-not-need-to-exist",
            _manifest(),
            "link-1",
            purpose="consumer review",
            authorization_gate=SecretGate(),
        )

    assert "secret role-matrix detail" not in str(caught.value)
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None


def _issue32_standards_library() -> StandardsLibrary:
    return StandardsLibrary(
        standards=(
            StandardDefinition(
                standard_id="standard-1",
                code="SYN.1",
                source="synthetic",
                short_name="Synthetic standard",
                description="Privacy-safe standard used only by tests.",
                available_modules=("concord",),
            ),
        ),
        profiles=(
            StandardsProfile(
                profile_id="profile-1",
                standards=("standard-1",),
                title="Synthetic standards profile",
            ),
        ),
    )


def _workspace_file_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_historical_graph_parses_the_exact_digest_verified_record_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = ensure_workspace_root(tmp_path / "workspace")
    metadata = create_class_metadata(
        "class-1",
        "2026-2027",
        created_at=datetime(2026, 8, 15, tzinfo=timezone.utc),
    )
    write_class_metadata_for_class(root, metadata)
    fixture = json.loads(EVIDENCE_ONLY_FIXTURE.read_text(encoding="utf-8"))
    activity = record_from_dict("activity", fixture["records"][0]["body"])
    session = record_from_dict("session", fixture["records"][1]["body"])
    assert isinstance(activity, Activity)
    assert isinstance(session, Session)
    commit_record_batch(
        root,
        activity.work_reference,
        (activity, session),
        expected_snapshot_revision=None,
    )

    target = record_revision_path(
        root,
        activity.work_reference,
        "session",
        session.session_id,
        1,
    )
    _, envelope = storage_module.load_record_revision(
        root,
        activity.work_reference,
        "session",
        session.session_id,
        1,
    )
    replacement = replace(session, notes="Unbound replacement record.")
    replacement_bytes = serialize(
        replace(envelope, body=record_to_dict(replacement))
    )
    original_reader = storage_module.read_canonical_bytes
    swapped = False

    def interposed_reader(path: Path, *, missing: bool = False) -> bytes:
        nonlocal swapped
        data = original_reader(path, missing=missing)
        if Path(path) == target and not swapped:
            swapped = True
            target.write_bytes(replacement_bytes)
        return data

    monkeypatch.setattr(
        storage_module,
        "read_canonical_bytes",
        interposed_reader,
    )
    loaded = load_record_graph_at_snapshot(root, activity.work_reference, 1)

    assert swapped
    assert loaded.snapshot_revision == 1
    assert loaded.graph.sessions == (session,)
    assert loaded.graph.sessions != (replacement,)


@pytest.mark.skipif(os.name == "nt", reason="POSIX openat race regression")
def test_retained_source_swap_to_symlink_immediately_before_open_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    graph = _routable_graph("artifact_page")
    page = graph.artifact_pages[0]
    scan = _retained_image_scan(
        root,
        page,
        scan_reference_id="scan-ref-race",
        source_scan_id="source-race",
        filename="race.png",
        color=(20, 30, 40),
    )
    source = root / scan.retained_source_relative_path
    outside = tmp_path / "outside.png"
    outside.write_bytes(source.read_bytes())
    graph = replace(graph, scan_references=(scan,))
    _install_render_graph(monkeypatch, graph)

    original_open = artifact_rendering_module.os.open
    swapped = False

    def interposed_open(path, flags, mode=0o777, *, dir_fd=None):
        nonlocal swapped
        if (
            not swapped
            and dir_fd is not None
            and path == source.name
            and flags & getattr(os, "O_NOFOLLOW", 0)
        ):
            source.unlink()
            try:
                source.symlink_to(outside)
            except (OSError, NotImplementedError) as error:
                pytest.skip(f"filesystem cannot create race symlink: {error}")
            swapped = True
        if dir_fd is None:
            return original_open(path, flags, mode)
        return original_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(artifact_rendering_module.os, "open", interposed_open)
    with pytest.raises(ConcordAcademicResultArtifactIntegrityError) as caught:
        artifacts_module.read_authorized_academic_result_artifact(
            root,
            _manifest("artifact_page"),
            "link-1",
            purpose="consumer review",
            authorization_gate=_Gate(),
        )

    assert swapped
    assert source.name not in str(caught.value)
    assert str(outside) not in str(caught.value)
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None


@pytest.mark.skipif(os.name == "nt", reason="POSIX root no-follow race regression")
def test_retained_workspace_root_swap_to_symlink_before_root_open_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    graph = _routable_graph("artifact_page")
    page = graph.artifact_pages[0]
    scan = _retained_image_scan(
        root,
        page,
        scan_reference_id="scan-ref-root-race",
        source_scan_id="source-root-race",
        filename="root-race.png",
        color=(20, 30, 40),
    )
    graph = replace(graph, scan_references=(scan,))
    _install_render_graph(monkeypatch, graph)

    moved_root = tmp_path / "workspace-original"
    original_open = artifact_rendering_module.os.open
    root_component = Path(os.path.abspath(root)).name
    swapped = False

    def interposed_open(path, flags, mode=0o777, *, dir_fd=None):
        nonlocal swapped
        if (
            not swapped
            and dir_fd is not None
            and path == root_component
            and flags & getattr(os, "O_DIRECTORY", 0)
            and flags & getattr(os, "O_NOFOLLOW", 0)
        ):
            root.rename(moved_root)
            try:
                root.symlink_to(moved_root, target_is_directory=True)
            except (OSError, NotImplementedError) as error:
                moved_root.rename(root)
                pytest.skip(f"filesystem cannot create root race symlink: {error}")
            swapped = True
        if dir_fd is None:
            return original_open(path, flags, mode)
        return original_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(artifact_rendering_module.os, "open", interposed_open)
    with pytest.raises(ConcordAcademicResultArtifactIntegrityError) as caught:
        artifacts_module.read_authorized_academic_result_artifact(
            root,
            _manifest("artifact_page"),
            "link-1",
            purpose="consumer review",
            authorization_gate=_Gate(),
        )

    assert swapped
    assert str(root) not in str(caught.value)
    assert str(moved_root) not in str(caught.value)
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None


@pytest.mark.skipif(os.name != "nt", reason="Windows root reparse regression")
def test_retained_workspace_root_junction_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import subprocess

    real_root = tmp_path / "workspace-real"
    real_root.mkdir()
    graph = _routable_graph("artifact_page")
    page = graph.artifact_pages[0]
    scan = _retained_image_scan(
        real_root,
        page,
        scan_reference_id="scan-ref-root-junction",
        source_scan_id="source-root-junction",
        filename="root-junction.png",
        color=(20, 30, 40),
    )
    graph = replace(graph, scan_references=(scan,))
    _install_render_graph(monkeypatch, graph)

    junction = tmp_path / "workspace"
    created = subprocess.run(
        ["cmd", "/d", "/c", "mklink", "/J", str(junction), str(real_root)],
        capture_output=True,
        text=True,
        check=False,
    )
    if created.returncode != 0:
        pytest.skip("filesystem cannot create a Windows directory junction")
    try:
        with pytest.raises(ConcordAcademicResultArtifactIntegrityError) as caught:
            artifacts_module.read_authorized_academic_result_artifact(
                junction,
                _manifest("artifact_page"),
                "link-1",
                purpose="consumer review",
                authorization_gate=_Gate(),
            )
    finally:
        subprocess.run(
            ["cmd", "/d", "/c", "rmdir", str(junction)],
            capture_output=True,
            text=True,
            check=False,
        )

    assert str(junction) not in str(caught.value)
    assert str(real_root) not in str(caught.value)
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None


def test_pillow_decompression_bomb_is_sanitized_as_public_integrity_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    graph = _routable_graph("artifact_page")
    page = graph.artifact_pages[0]
    scan = _retained_image_scan(
        root,
        page,
        scan_reference_id="scan-ref-bomb",
        source_scan_id="source-bomb",
        filename="bomb.png",
        color=(20, 30, 40),
    )
    graph = replace(graph, scan_references=(scan,))
    _install_render_graph(monkeypatch, graph)

    def bomb(*_args, **_kwargs):
        raise Image.DecompressionBombError("private decoder dimensions")

    monkeypatch.setattr(Image, "open", bomb)
    with pytest.raises(ConcordAcademicResultArtifactIntegrityError) as caught:
        artifacts_module.read_authorized_academic_result_artifact(
            root,
            _manifest("artifact_page"),
            "link-1",
            purpose="consumer review",
            authorization_gate=_Gate(),
        )

    assert "private decoder dimensions" not in str(caught.value)
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None


def test_representative_fixture_generates_and_reads_bounded_artifact_evidence(
    tmp_path: Path,
) -> None:
    root = ensure_workspace_root(tmp_path / "workspace")
    write_class_metadata_for_class(
        root,
        create_class_metadata(
            "class-1",
            "2026-2027",
            created_at=datetime(2026, 8, 15, tzinfo=timezone.utc),
        ),
    )
    fixture = json.loads(STANDARDS_FIXTURE.read_text(encoding="utf-8"))
    records = tuple(
        record_from_dict(item["record_kind"], item["body"])
        for item in fixture["records"]
    )
    activity = next(item for item in records if isinstance(item, Activity))
    assert activity.activity_id == "standards-activity"

    proof = fixture["artifact_reader_proof"]
    assert isinstance(proof, dict)
    retained = root.joinpath(*proof["retained_source_relative_path"].split("/"))
    retained.parent.mkdir(parents=True, exist_ok=True)
    retained_bytes = base64.b64decode(REPRESENTATIVE_SOURCE_BASE64)
    retained.write_bytes(retained_bytes)
    assert hashlib.sha256(retained_bytes).hexdigest() == proof["retained_source_sha256"]

    standards_library = _issue32_standards_library()
    committed = commit_record_batch(
        root,
        activity.work_reference,
        records,
        expected_snapshot_revision=None,
        standards_library=standards_library,
    )
    assert committed.snapshot_revision == 1
    register_concord_academic_work(
        root,
        "class-1",
        "standards-activity",
        academic_intent="summative",
        lifecycle="active",
    )
    generated = generate_academic_result_manifest(
        GenerateAcademicResultManifestRequest(
            class_id="class-1",
            activity_id="standards-activity",
            expected_snapshot_revision=1,
            actor=WorkflowActor(actor_id="actor-1"),
            revision_reason="initial",
        ),
        workspace_root=root,
        standards_library=standards_library,
        clock=lambda: datetime(2026, 8, 15, 18, 0, tzinfo=timezone.utc),
    )
    manifest = generated.manifest
    assert manifest.projection.source_snapshot_revision == 1
    assert {
        item.evidence_reference.owning_system
        for item in manifest.score_evidence_links
    } >= {"concord", "scoreform", "quillan"}
    typed_scale_id = proof["type_sensitive_scale_id"]
    for value, value_type in (
        (1, int),
        (1.0, float),
        ("1", str),
        (True, bool),
    ):
        level = lookup_academic_result_scale_level(
            manifest,
            typed_scale_id,
            value,
        )
        assert type(level.value) is value_type

    session = next(item for item in records if isinstance(item, Session))
    changed_session = replace(session, notes="Synthetic current snapshot two.")
    advanced = commit_record_batch(
        root,
        activity.work_reference,
        (changed_session,),
        expected_snapshot_revision=1,
        standards_library=standards_library,
    )
    assert advanced.snapshot_revision == 2
    before = _workspace_file_bytes(root)

    instance_result = artifacts_module.read_authorized_academic_result_artifact(
        root,
        manifest,
        proof["artifact_instance_link_id"],
        purpose="consumer review",
        authorization_gate=_Gate(),
    )
    page_result = artifacts_module.read_authorized_academic_result_artifact(
        root,
        manifest,
        proof["artifact_page_link_id"],
        purpose="consumer review",
        authorization_gate=_Gate(),
    )

    assert instance_result.source_snapshot_revision == 1
    assert page_result.source_snapshot_revision == 1
    assert instance_result.content.startswith(b"%PDF")
    assert page_result.content.startswith(b"%PDF")
    assert instance_result.content != retained_bytes
    assert page_result.content != retained_bytes
    assert _pdf_page_count(instance_result.content) == 1
    assert _pdf_page_count(page_result.content) == 1
    assert instance_result.artifact.artifact_instance_id == "artifact-1"
    assert page_result.artifact.artifact_instance_id == "artifact-1"
    assert instance_result.authors[0].author_reference is not None
    assert (
        instance_result.authors[0].author_reference.participant_id
        == fixture["semantic_proof"]["author_id"]
    )
    assert instance_result.subjects[0].subject_reference.subject_id == (
        fixture["semantic_proof"]["subject_id"]
    )
    assert (
        instance_result.authors[0].author_reference.participant_id
        != instance_result.subjects[0].subject_reference.subject_id
    )
    assert instance_result.artifact.group_id == "group-1"
    assert not hasattr(instance_result.artifact, "retained_source_relative_path")
    assert not hasattr(instance_result.artifact, "retained_source_sha256")
    assert _workspace_file_bytes(root) == before
