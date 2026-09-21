"""Prepare and classify Concord issue #113 relationship visual review."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.classes import write_class_roster
from pds_core.pds2 import parse_pds2_payload
from pds_core.rosters import create_roster
from pds_core.route_registrations import load_route_registration
from pds_core.routing_models import ModuleWorkRef
from pds_core.workspace import ensure_workspace_root

from concord.models import (
    EffectiveContext,
    PacketAudienceIntent,
    PacketComponent,
    PacketDefinition,
    PacketRenderingRules,
    PacketVersion,
    ParticipantReference,
    SubjectReference,
)
from concord.packet_storage import create_packet_library
from concord.starter_templates.catalog import get_starter_template
from concord.storage import load_current_record_graph
from concord.workflows import (
    CreateActivityContextRequest,
    CreateGroupWithMembersRequest,
    GroupMemberSpec,
    GroupRoleSpec,
    PacketSubjectBinding,
    PreparePacketInstantiationRequest,
    PrepareStarterTemplateInstallRequest,
    RenderPacketInstanceRequest,
    WorkflowActor,
    commit_packet_instantiation,
    commit_starter_template_install,
    core_student_participant,
    create_activity_context,
    create_group_with_members,
    prepare_packet_instantiation,
    prepare_starter_template_install,
    render_packet_instance,
)
from concord.workflows.context import provenance

ISSUE = 113
CLASS_ID = "english12-advanced-composition-period-2-2026"
SCHOOL_YEAR = "2026-2027"
REVIEWER_ID = "student-reviewer"
REVIEWEE_ID = "student-reviewee"
COLLABORATOR_ID = "student-collaborator"
REVIEWER_FIRST = "Alexandria"
REVIEWER_LAST = "Montgomery-Williams"
REVIEWEE_FIRST = "Christopher"
REVIEWEE_LAST = "Van-Der-Meer-Santiago"
COLLABORATOR_FIRST = "Marisol"
COLLABORATOR_LAST = "O'Connell-Ramirez"

SEMINAR_ACTIVITY_ID = "i113-seminar"
SEMINAR_SESSION_ID = "issue113-seminar-session"
SEMINAR_ROLE_ID = "issue113-seminar-observer-role"
SEMINAR_ROLE_KEY = "observer"
SEMINAR_SESSION_LABEL = (
    "Socratic Seminar — Evidence, Memory, Responsibility, and Competing Interpretations"
)
SEMINAR_ACTIVITY_TITLE = (
    "Seminar Relationship Review: Memory, Evidence, and Responsibility"
)

PROJECT_ACTIVITY_ID = "issue113-project-relationship-review"
PROJECT_ACTIVITY_TITLE = (
    "Project Relationship Review: Accessible Community Information System Prototype"
)
PROJECT_SESSION_LABEL = (
    "Prototype Critique — Accessibility, Evidence, Testing, and Revision"
)
PROJECT_SESSION_ID = "issue113-project-session"
PROJECT_ROLE_ID = "issue113-project-reviewer-role"
PROJECT_ROLE_KEY = "observer"
REVIEWED_GROUP_ID = "issue113-reviewed-product-group"
REVIEWED_GROUP_LABEL = "Community Accessibility Design Team — Prototype Alpha"

RUN_STATE = "visual-review-state.json"
MANIFEST = "manifest.json"
CHECKLIST = "visual-review-checklist.md"
COMMENT = "issue113-visual-review-comment.md"
EVIDENCE = "visual-review-evidence.json"
BUNDLE_ZIP = "issue113-visual-review-bundle.zip"
PDF_DIR = "pdfs"
PREVIEW_DIR = "previews"
OUTCOMES = ("PASS", "PASS_WITH_DOCUMENTED_LIMITATION", "FAIL")


@dataclass(frozen=True, slots=True)
class VisualCase:
    key: str
    starter_key: str
    display_label: str
    activity_id: str
    session_id: str
    role_id: str
    role_key: str
    subject_mode: str
    output_stem: str
    expected_orientation: str
    expected_page_count: int


CASES = (
    VisualCase(
        key="fishbowl",
        starter_key="fishbowl_observer",
        display_label="Fishbowl Observer v2",
        activity_id=SEMINAR_ACTIVITY_ID,
        session_id=SEMINAR_SESSION_ID,
        role_id=SEMINAR_ROLE_ID,
        role_key=SEMINAR_ROLE_KEY,
        subject_mode="session",
        output_stem="01-fishbowl-observer-v2",
        expected_orientation="portrait",
        expected_page_count=1,
    ),
    VisualCase(
        key="talk_moves",
        starter_key="talk_moves_observer",
        display_label="Talk-Moves Observer v2",
        activity_id=SEMINAR_ACTIVITY_ID,
        session_id=SEMINAR_SESSION_ID,
        role_id=SEMINAR_ROLE_ID,
        role_key=SEMINAR_ROLE_KEY,
        subject_mode="session",
        output_stem="02-talk-moves-observer-v2",
        expected_orientation="portrait",
        expected_page_count=1,
    ),
    VisualCase(
        key="writing",
        starter_key="peer_review_writing",
        display_label="Peer Review — Writing v2",
        activity_id=PROJECT_ACTIVITY_ID,
        session_id=PROJECT_SESSION_ID,
        role_id=PROJECT_ROLE_ID,
        role_key=PROJECT_ROLE_KEY,
        subject_mode="student",
        output_stem="03-peer-review-writing-v2-student",
        expected_orientation="portrait",
        expected_page_count=2,
    ),
    VisualCase(
        key="presentation",
        starter_key="peer_review_presentation",
        display_label="Peer Review — Presentation / Product v2",
        activity_id=PROJECT_ACTIVITY_ID,
        session_id=PROJECT_SESSION_ID,
        role_id=PROJECT_ROLE_ID,
        role_key=PROJECT_ROLE_KEY,
        subject_mode="group",
        output_stem="04-peer-review-presentation-v2-group",
        expected_orientation="portrait",
        expected_page_count=1,
    ),
    VisualCase(
        key="design_code",
        starter_key="peer_design_code_review",
        display_label="Peer Design / Code Review v2",
        activity_id=PROJECT_ACTIVITY_ID,
        session_id=PROJECT_SESSION_ID,
        role_id=PROJECT_ROLE_ID,
        role_key=PROJECT_ROLE_KEY,
        subject_mode="student",
        output_stem="05-peer-design-code-review-v2-student",
        expected_orientation="landscape",
        expected_page_count=1,
    ),
)


def _clock() -> datetime:
    return datetime(2026, 9, 20, 16, 0, tzinfo=timezone.utc)


def _actor() -> WorkflowActor:
    return WorkflowActor(
        actor_id="teacher-issue113-visual",
        display_label="Synthetic Visual Review Teacher",
        role_label="teacher",
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, value: dict[str, object]) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def _git_output(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def _source_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _git_head(root: Path) -> str:
    value = _git_output(root, "rev-parse", "HEAD").strip()
    if len(value) != 40:
        raise RuntimeError("could not determine exact source commit")
    return value


def _require_clean_checkout(root: Path) -> None:
    status = _git_output(root, "status", "--porcelain", "--untracked-files=all")
    if status:
        raise RuntimeError(
            "issue #113 visual review requires a clean checkout so the "
            "persistent bundle is attributable to one exact commit"
        )


def _require_fresh_run_root(run_root: Path) -> None:
    if run_root.exists():
        if any(run_root.iterdir()):
            raise RuntimeError(
                f"visual-review run directory is not empty: {run_root}"
            )
    else:
        run_root.mkdir(parents=True)


def _context(activity_id: str, session_id: str) -> EffectiveContext:
    return EffectiveContext(activity_id=activity_id, session_ids=(session_id,))


def _create_workspace(run_root: Path) -> Path:
    root = ensure_workspace_root(run_root / "workspace")
    write_class_metadata_for_class(
        root,
        create_class_metadata(CLASS_ID, SCHOOL_YEAR, created_at=_clock()),
    )
    write_class_roster(
        root,
        create_roster(
            CLASS_ID,
            (
                {
                    "student_id": REVIEWER_ID,
                    "last_name": REVIEWER_LAST,
                    "first_name": REVIEWER_FIRST,
                    "period": "2",
                },
                {
                    "student_id": REVIEWEE_ID,
                    "last_name": REVIEWEE_LAST,
                    "first_name": REVIEWEE_FIRST,
                    "period": "2",
                },
                {
                    "student_id": COLLABORATOR_ID,
                    "last_name": COLLABORATOR_LAST,
                    "first_name": COLLABORATOR_FIRST,
                    "period": "2",
                },
            ),
        ),
    )

    seminar = create_activity_context(
        CreateActivityContextRequest(
            class_id=CLASS_ID,
            activity_id=SEMINAR_ACTIVITY_ID,
            title=SEMINAR_ACTIVITY_TITLE,
            activity_type="socratic_seminar",
            scoring_orientation="evidence_only",
            session_id=SEMINAR_SESSION_ID,
            actor=_actor(),
            activity_status="active",
            session_status="active",
            session_label=SEMINAR_SESSION_LABEL,
        ),
        workspace_root=root,
        clock=_clock,
    )
    seminar_context = _context(SEMINAR_ACTIVITY_ID, SEMINAR_SESSION_ID)
    create_group_with_members(
        CreateGroupWithMembersRequest(
            class_id=CLASS_ID,
            activity_id=SEMINAR_ACTIVITY_ID,
            group_id="issue113-seminar-observers",
            label="Outer Circle — Evidence and Listening Observers",
            expected_snapshot_revision=seminar.commit.snapshot_revision,
            actor=_actor(),
            status="active",
            effective_context=seminar_context,
            members=(
                GroupMemberSpec(
                    membership_id="issue113-seminar-reviewer-membership",
                    student_id=REVIEWER_ID,
                    effective_context=seminar_context,
                ),
            ),
            roles=(
                GroupRoleSpec(
                    role_assignment_id=SEMINAR_ROLE_ID,
                    participant_reference=core_student_participant(
                        root, CLASS_ID, REVIEWER_ID
                    ),
                    role_key=SEMINAR_ROLE_KEY,
                    effective_context=seminar_context,
                    membership_id="issue113-seminar-reviewer-membership",
                ),
            ),
        ),
        workspace_root=root,
        clock=_clock,
    )

    project = create_activity_context(
        CreateActivityContextRequest(
            class_id=CLASS_ID,
            activity_id=PROJECT_ACTIVITY_ID,
            title=PROJECT_ACTIVITY_TITLE,
            activity_type="project",
            scoring_orientation="evidence_only",
            session_id=PROJECT_SESSION_ID,
            actor=_actor(),
            activity_status="active",
            session_status="active",
            session_label=PROJECT_SESSION_LABEL,
        ),
        workspace_root=root,
        clock=_clock,
    )
    project_context = _context(PROJECT_ACTIVITY_ID, PROJECT_SESSION_ID)
    reviewer_group = create_group_with_members(
        CreateGroupWithMembersRequest(
            class_id=CLASS_ID,
            activity_id=PROJECT_ACTIVITY_ID,
            group_id="issue113-project-reviewers",
            label="Peer Reviewers — Usability and Evidence Team",
            expected_snapshot_revision=project.commit.snapshot_revision,
            actor=_actor(),
            status="active",
            effective_context=project_context,
            members=(
                GroupMemberSpec(
                    membership_id="issue113-project-reviewer-membership",
                    student_id=REVIEWER_ID,
                    effective_context=project_context,
                ),
            ),
            roles=(
                GroupRoleSpec(
                    role_assignment_id=PROJECT_ROLE_ID,
                    participant_reference=core_student_participant(
                        root, CLASS_ID, REVIEWER_ID
                    ),
                    role_key=PROJECT_ROLE_KEY,
                    effective_context=project_context,
                    membership_id="issue113-project-reviewer-membership",
                ),
            ),
        ),
        workspace_root=root,
        clock=_clock,
    )
    create_group_with_members(
        CreateGroupWithMembersRequest(
            class_id=CLASS_ID,
            activity_id=PROJECT_ACTIVITY_ID,
            group_id=REVIEWED_GROUP_ID,
            label=REVIEWED_GROUP_LABEL,
            expected_snapshot_revision=reviewer_group.commit.snapshot_revision,
            actor=_actor(),
            status="active",
            effective_context=project_context,
            members=(
                GroupMemberSpec(
                    membership_id="issue113-project-reviewee-membership",
                    student_id=REVIEWEE_ID,
                    effective_context=project_context,
                ),
                GroupMemberSpec(
                    membership_id="issue113-project-collaborator-membership",
                    student_id=COLLABORATOR_ID,
                    effective_context=project_context,
                ),
            ),
        ),
        workspace_root=root,
        clock=_clock,
    )
    return root


def _subject_for_case(case: VisualCase) -> SubjectReference | None:
    if case.subject_mode == "session":
        return None
    if case.subject_mode == "student":
        return SubjectReference(
            subject_kind="core_student",
            subject_id=REVIEWEE_ID,
            owning_system="core",
        )
    if case.subject_mode == "group":
        return SubjectReference(
            subject_kind="concord_group",
            subject_id=REVIEWED_GROUP_ID,
            owning_system="concord",
        )
    raise RuntimeError(f"unsupported visual-review subject mode: {case.subject_mode}")


def _target_key(case: VisualCase) -> str:
    return f"role:{case.role_id}"


def _install_and_packet(root: Path, case: VisualCase) -> str:
    installed = commit_starter_template_install(
        prepare_starter_template_install(
            PrepareStarterTemplateInstallRequest(
                starter_key=case.starter_key,
                actor=_actor(),
            ),
            workspace_root=root,
            clock=_clock,
        ),
        workspace_root=root,
    )
    expected_v2 = f"{get_starter_template(case.starter_key).template_id}-v2"
    if installed.template_version_id != expected_v2:
        raise RuntimeError(
            f"{case.starter_key} did not resolve package-current v2: "
            f"{installed.template_version_id}"
        )

    created = provenance(_actor(), clock=_clock, source_kind="manual")
    packet_definition_id = f"issue113-visual-{case.key}-packet"
    packet_version_id = f"issue113-visual-{case.key}-packet-v1"
    packet_definition = PacketDefinition(
        packet_definition_id=packet_definition_id,
        name=f"Issue #113 Visual Review — {case.display_label}",
        purpose="Persistent synthetic relationship-aware visual qualification.",
        status="active",
        created_provenance=created,
    )
    packet_version = PacketVersion(
        packet_version_id=packet_version_id,
        packet_definition_id=packet_definition_id,
        version_label="Visual review v1",
        revision_sequence=1,
        components=(
            PacketComponent(
                packet_component_id=f"issue113-visual-{case.key}-component",
                sequence=1,
                component_kind="concord_template",
                template_id=installed.template_id,
                template_version_id=installed.template_version_id,
                copies_per_target=1,
                audience_intent=PacketAudienceIntent(
                    audience_kind="role",
                    role_keys=(case.role_key,),
                ),
                requirement_level="required",
            ),
        ),
        rendering_rules=PacketRenderingRules(),
        created_provenance=created,
        status="active",
    )
    create_packet_library(
        root,
        definition=packet_definition,
        initial_version=packet_version,
    )
    return installed.template_version_id


def _prepare_request(
    case: VisualCase,
    subject: SubjectReference | None,
) -> PreparePacketInstantiationRequest:
    bindings: tuple[PacketSubjectBinding, ...] = ()
    if subject is not None:
        bindings = (
            PacketSubjectBinding(
                packet_component_id=f"issue113-visual-{case.key}-component",
                target_key=_target_key(case),
                subject_reference=subject,
            ),
        )
    return PreparePacketInstantiationRequest(
        class_id=CLASS_ID,
        activity_id=case.activity_id,
        session_id=case.session_id,
        packet_definition_id=f"issue113-visual-{case.key}-packet",
        packet_version_id=f"issue113-visual-{case.key}-packet-v1",
        actor=_actor(),
        subject_bindings=bindings,
    )


def _verify_committed_relationship(
    root: Path,
    case: VisualCase,
    artifact_instance_id: str,
) -> tuple[str, str, str]:
    graph = load_current_record_graph(
        root,
        ModuleWorkRef("concord", CLASS_ID, case.activity_id),
    ).graph
    authors = tuple(
        item
        for item in graph.artifact_authors
        if item.artifact_instance_id == artifact_instance_id
    )
    subjects = tuple(
        item
        for item in graph.artifact_subjects
        if item.artifact_instance_id == artifact_instance_id
    )
    if len(authors) != 1 or len(subjects) != 1:
        raise RuntimeError(
            f"{case.key} must commit exactly one initial Author and Subject"
        )
    author = authors[0]
    subject = subjects[0]
    if not isinstance(author.author_reference, ParticipantReference):
        raise RuntimeError(f"{case.key} initial Author is not a participant")
    if author.author_reference.participant_id != REVIEWER_ID:
        raise RuntimeError(f"{case.key} initial Author is not the reviewer")
    if author.attribution_status != "proposed":
        raise RuntimeError(f"{case.key} initial Author is not proposed")

    expected_role = (
        "session_context" if case.subject_mode == "session" else "reviewed_subject"
    )
    if subject.subject_role != expected_role:
        raise RuntimeError(
            f"{case.key} Subject role mismatch: {subject.subject_role}"
        )
    if subject.confirmation_status != "proposed":
        raise RuntimeError(f"{case.key} Subject is not proposed")

    reference = subject.subject_reference
    if case.subject_mode == "session":
        if (
            reference.subject_kind != "concord_session"
            or reference.subject_id != SEMINAR_SESSION_ID
        ):
            raise RuntimeError(f"{case.key} did not resolve the selected Session")
    elif case.subject_mode == "student":
        if (
            reference.subject_kind != "core_student"
            or reference.subject_id != REVIEWEE_ID
        ):
            raise RuntimeError(f"{case.key} did not retain the reviewee student")
    elif case.subject_mode == "group":
        if (
            reference.subject_kind != "concord_group"
            or reference.subject_id != REVIEWED_GROUP_ID
        ):
            raise RuntimeError(f"{case.key} did not retain the reviewed Group")
    else:
        raise RuntimeError(f"unsupported subject mode: {case.subject_mode}")
    return author.authorship_mode, reference.subject_kind, subject.subject_role


def _render_previews_and_verify_qr(
    pdf_path: Path,
    preview_root: Path,
    case: VisualCase,
    payloads: tuple[str, ...],
) -> tuple[str, ...]:
    import pypdfium2
    import zxingcpp

    document = pypdfium2.PdfDocument(pdf_path)
    previews: list[str] = []
    try:
        page_count = len(document)
        if page_count != case.expected_page_count:
            raise RuntimeError(
                f"{case.key} rendered {page_count} pages, "
                f"expected {case.expected_page_count}"
            )
        if len(payloads) != page_count:
            raise RuntimeError(
                f"{case.key} payload count does not match rendered page count"
            )

        for index in range(page_count):
            page = document[index]
            image = page.render(scale=2).to_pil()
            width, height = image.size
            orientation = "portrait" if height > width else "landscape"
            if orientation != case.expected_orientation:
                raise RuntimeError(
                    f"{case.key} page {index + 1} orientation is "
                    f"{orientation}, expected {case.expected_orientation}"
                )
            detected = {
                result.text
                for result in zxingcpp.read_barcodes(image)
                if isinstance(result.text, str)
            }
            if payloads[index] not in detected:
                raise RuntimeError(
                    f"{case.key} page {index + 1} PDS2 QR did not decode "
                    "from the visual-review raster"
                )
            preview_name = f"{case.output_stem}-page-{index + 1}.png"
            preview_path = preview_root / preview_name
            image.save(preview_path, format="PNG")
            previews.append(f"{PREVIEW_DIR}/{preview_name}")
    finally:
        document.close()
    return tuple(previews)


def _generate_case(
    root: Path,
    run_root: Path,
    case: VisualCase,
) -> dict[str, object]:
    template_version_id = _install_and_packet(root, case)
    subject = _subject_for_case(case)
    prepared = prepare_packet_instantiation(
        _prepare_request(case, subject),
        workspace_root=root,
        clock=_clock,
    )
    if not prepared.ready_for_commit:
        messages = "; ".join(item.message for item in prepared.diagnostics)
        raise RuntimeError(f"{case.key} visual preview is blocked: {messages}")
    if len(prepared.target_plans) != 1:
        raise RuntimeError(f"{case.key} must resolve exactly one Packet target")
    if len(prepared.target_plans[0].artifacts) != 1:
        raise RuntimeError(f"{case.key} must resolve exactly one Artifact")
    if prepared.target_plans[0].artifacts[0].template_version_id != template_version_id:
        raise RuntimeError(f"{case.key} preview lost exact v2 Template identity")

    committed = commit_packet_instantiation(
        prepared,
        workspace_root=root,
        generation_id=f"generation-issue113-visual-{case.key}",
        clock=_clock,
    )
    if len(committed.packet_instance_ids) != 1:
        raise RuntimeError(f"{case.key} must commit exactly one Packet Instance")
    if len(committed.artifact_instance_ids) != 1:
        raise RuntimeError(f"{case.key} must commit exactly one Artifact")
    if len(committed.pages) != case.expected_page_count:
        raise RuntimeError(f"{case.key} committed unexpected page count")

    packet_instance_id = committed.packet_instance_ids[0]
    rendered = render_packet_instance(
        RenderPacketInstanceRequest(
            class_id=CLASS_ID,
            activity_id=case.activity_id,
            packet_instance_id=packet_instance_id,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    if rendered.page_count != case.expected_page_count:
        raise RuntimeError(f"{case.key} rendered unexpected page count")

    pdf_name = f"{case.output_stem}.pdf"
    pdf_path = run_root / PDF_DIR / pdf_name
    shutil.copyfile(rendered.output_path, pdf_path)
    if _sha256(pdf_path) != rendered.output_sha256:
        raise RuntimeError(f"{case.key} copied PDF digest changed")

    payloads = rendered.payloads
    if len(payloads) != case.expected_page_count:
        raise RuntimeError(f"{case.key} rendered unexpected route count")

    fallbacks: list[str] = []
    module_details: list[dict[str, object]] = []
    for committed_page, payload in zip(committed.pages, payloads, strict=True):
        if committed_page.pds2_payload != payload:
            raise RuntimeError(f"{case.key} rendered payload changed after commit")
        registration = load_route_registration(root, parse_pds2_payload(payload))
        if set(registration.module_details) != {
            "activity_id",
            "artifact_instance_id",
            "artifact_page_id",
            "page_number",
        }:
            raise RuntimeError(f"{case.key} route module_details contract changed")
        if registration.human_fallback is None:
            raise RuntimeError(f"{case.key} route human fallback is missing")
        fallback = registration.human_fallback
        if REVIEWER_ID in fallback or REVIEWEE_ID in fallback:
            raise RuntimeError(f"{case.key} physical fallback leaked student IDs")
        fallbacks.append(fallback)
        module_details.append(dict(registration.module_details))

    author_mode, subject_kind, subject_role = _verify_committed_relationship(
        root,
        case,
        committed.artifact_instance_ids[0],
    )
    previews = _render_previews_and_verify_qr(
        pdf_path,
        run_root / PREVIEW_DIR,
        case,
        payloads,
    )

    return {
        "case_key": case.key,
        "starter_key": case.starter_key,
        "display_label": case.display_label,
        "template_version_id": template_version_id,
        "activity_id": case.activity_id,
        "session_id": case.session_id,
        "packet_instance_id": packet_instance_id,
        "artifact_instance_id": committed.artifact_instance_ids[0],
        "orientation": case.expected_orientation,
        "expected_page_count": case.expected_page_count,
        "generated_page_count": rendered.page_count,
        "pdf_relative_path": f"{PDF_DIR}/{pdf_name}",
        "pdf_sha256": _sha256(pdf_path),
        "pdf_byte_length": pdf_path.stat().st_size,
        "preview_relative_paths": list(previews),
        "pds2_qr_decode_verified": True,
        "human_fallbacks": fallbacks,
        "route_module_details": module_details,
        "initial_author_student_id": REVIEWER_ID,
        "initial_authorship_mode": author_mode,
        "subject_kind": subject_kind,
        "subject_role": subject_role,
        "subject_mode": case.subject_mode,
    }


def _checklist_text() -> str:
    lines = [
        "# Issue #113 visual review checklist",
        "",
        "Inspect every PDF and its raster previews. Automation verifies page count,",
        "orientation, exact route metadata, and mechanical PDS2 QR decode, but it",
        "does not classify visual quality.",
        "",
        "## Required files",
        "",
    ]
    for case in CASES:
        lines.append(
            f"- `{PDF_DIR}/{case.output_stem}.pdf` — {case.display_label} "
            f"({case.expected_orientation}, {case.expected_page_count} page(s))"
        )
    lines.extend(
        [
            "",
            "## Human inspection criteria",
            "",
            "- role labels are unmistakable;",
            "- Reviewer and Reviewee/Reviewed are visually distinct;",
            "- Observer and Observed context are visually distinct;",
            "- headers remain readable with the long synthetic names;",
            "- the long class ID and privacy-minimized fallback remain readable;",
            "- footer/fallback text does not collide with QR or writable regions;",
            "- QR codes have clear quiet space and are not clipped;",
            "- writable response space remains useful;",
            "- the two-page Writing review has consistent identity/header treatment;",
            "- portrait pages remain portrait and Design/Code remains landscape;",
            "- the long Session and Group labels wrap without clipping or overlap;",
            "- no text, lines, tables, or page numbers clip at printable edges;",
            "- small text remains copier-friendly in grayscale;",
            "- no student IDs appear in ordinary physical identity text.",
            "",
            "Do not infer PASS from the generated artifacts. Record the owner/tester",
            "classification through the explicit `approve` command only after",
            "performing this inspection.",
            "",
        ]
    )
    return "\n".join(lines)


def _comment_pending(
    source_commit: str,
    bundle_sha256: str,
    bundle_byte_length: int,
) -> str:
    lines = [
        "Issue #113 visual-review completion record",
        "",
        f"source commit: {source_commit}",
        f"visual-review bundle: {BUNDLE_ZIP}",
        f"bundle byte length: {bundle_byte_length}",
        f"bundle SHA-256: {bundle_sha256}",
        f"class id: {CLASS_ID}",
        f"reviewer synthetic identity: {REVIEWER_FIRST} {REVIEWER_LAST}",
        f"reviewee synthetic identity: {REVIEWEE_FIRST} {REVIEWEE_LAST}",
        f"reviewed Group label: {REVIEWED_GROUP_LABEL}",
        f"observed Session label: {SEMINAR_SESSION_LABEL}",
        "Fishbowl Observer v2: OWNER CLASSIFICATION REQUIRED",
        "Talk-Moves Observer v2: OWNER CLASSIFICATION REQUIRED",
        "Peer Review — Writing v2: OWNER CLASSIFICATION REQUIRED",
        "Peer Review — Presentation / Product v2: OWNER CLASSIFICATION REQUIRED",
        "Peer Design / Code Review v2: OWNER CLASSIFICATION REQUIRED",
        "overall visual review: OWNER CLASSIFICATION REQUIRED",
        "installed-wheel acceptance: NOT YET RUN",
    ]
    return "\n".join(lines) + "\n"


def _zip_bundle(run_root: Path) -> Path:
    zip_path = run_root / BUNDLE_ZIP
    include = (
        run_root / PDF_DIR,
        run_root / PREVIEW_DIR,
        run_root / MANIFEST,
        run_root / CHECKLIST,
    )
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for item in include:
            if item.is_dir():
                for child in sorted(path for path in item.rglob("*") if path.is_file()):
                    archive.write(child, child.relative_to(run_root).as_posix())
            else:
                archive.write(item, item.relative_to(run_root).as_posix())
    return zip_path


def _prepare(run_root: Path) -> int:
    source_root = _source_root()
    _require_clean_checkout(source_root)
    source_commit = _git_head(source_root)
    _require_fresh_run_root(run_root)
    (run_root / PDF_DIR).mkdir()
    (run_root / PREVIEW_DIR).mkdir()

    workspace = _create_workspace(run_root)
    cases = [_generate_case(workspace, run_root, case) for case in CASES]
    manifest: dict[str, object] = {
        "schema_version": 1,
        "issue": ISSUE,
        "source_commit": source_commit,
        "class_id": CLASS_ID,
        "reviewer_display_name": f"{REVIEWER_FIRST} {REVIEWER_LAST}",
        "reviewee_display_name": f"{REVIEWEE_FIRST} {REVIEWEE_LAST}",
        "observed_session_label": SEMINAR_SESSION_LABEL,
        "reviewed_group_label": REVIEWED_GROUP_LABEL,
        "case_count": len(cases),
        "cases": cases,
        "mechanical_gate": {
            "all_pages_rasterized": True,
            "all_pds2_qr_codes_decoded": True,
            "all_route_module_details_exact": True,
            "student_ids_absent_from_human_fallbacks": True,
        },
        "owner_visual_classification": "OWNER CLASSIFICATION REQUIRED",
    }
    _write_json(run_root / MANIFEST, manifest)
    (run_root / CHECKLIST).write_text(_checklist_text(), encoding="utf-8")

    bundle = _zip_bundle(run_root)
    bundle_sha256 = _sha256(bundle)
    bundle_byte_length = bundle.stat().st_size
    state: dict[str, object] = {
        "schema_version": 1,
        "issue": ISSUE,
        "status": "prepared_pending_owner_visual_review",
        "source_commit": source_commit,
        "manifest_relative_path": MANIFEST,
        "checklist_relative_path": CHECKLIST,
        "bundle_relative_path": BUNDLE_ZIP,
        "bundle_sha256": bundle_sha256,
        "bundle_byte_length": bundle_byte_length,
        "pdf_count": len(CASES),
        "page_count": sum(case.expected_page_count for case in CASES),
        "owner_visual_classification": "OWNER CLASSIFICATION REQUIRED",
    }
    _write_json(run_root / RUN_STATE, state)
    (run_root / COMMENT).write_text(
        _comment_pending(
            source_commit,
            bundle_sha256,
            bundle_byte_length,
        ),
        encoding="utf-8",
    )

    print("Prepared Concord issue #113 visual-review bundle.")
    print(f"Source commit: {source_commit}")
    print(f"PDF directory: {run_root / PDF_DIR}")
    print(f"Preview directory: {run_root / PREVIEW_DIR}")
    print(f"Checklist: {run_root / CHECKLIST}")
    print(f"Bundle: {bundle}")
    print(f"Bundle SHA-256: {state['bundle_sha256']}")
    print("Owner visual classification: REQUIRED")
    return 0


def _outcome(value: str) -> str:
    if value not in OUTCOMES:
        raise RuntimeError(f"unsupported visual-review outcome: {value}")
    return value.replace("_", " ")


def _case_results(args: argparse.Namespace) -> dict[str, str]:
    return {
        "fishbowl": _outcome(args.fishbowl),
        "talk_moves": _outcome(args.talk_moves),
        "writing": _outcome(args.writing),
        "presentation": _outcome(args.presentation),
        "design_code": _outcome(args.design_code),
    }


def _approve(args: argparse.Namespace) -> int:
    run_root = Path(args.run_root).resolve()
    state = _load_json(run_root / RUN_STATE)
    if state.get("status") != "prepared_pending_owner_visual_review":
        raise RuntimeError(
            "visual-review run is not in the prepared pending-owner state"
        )
    if not args.visual_inspection_confirmed:
        raise RuntimeError(
            "--visual-inspection-confirmed is required after inspecting all five PDFs"
        )

    bundle = run_root / BUNDLE_ZIP
    expected_bundle_sha = state.get("bundle_sha256")
    if not isinstance(expected_bundle_sha, str):
        raise RuntimeError("visual-review state is missing bundle_sha256")
    if _sha256(bundle) != expected_bundle_sha:
        raise RuntimeError("visual-review bundle bytes changed after preparation")

    manifest = _load_json(run_root / MANIFEST)
    raw_cases = manifest.get("cases")
    if not isinstance(raw_cases, list) or len(raw_cases) != len(CASES):
        raise RuntimeError("visual-review manifest does not contain all five cases")
    for raw in raw_cases:
        if not isinstance(raw, dict):
            raise RuntimeError("visual-review manifest contains an invalid case")
        relative = raw.get("pdf_relative_path")
        digest = raw.get("pdf_sha256")
        if not isinstance(relative, str) or not isinstance(digest, str):
            raise RuntimeError("visual-review manifest case is missing PDF integrity")
        if _sha256(run_root / relative) != digest:
            raise RuntimeError(
                f"visual-review PDF changed after preparation: {relative}"
            )

    results = _case_results(args)
    overall = _outcome(args.overall)
    if overall == "PASS" and any(value != "PASS" for value in results.values()):
        raise RuntimeError(
            "overall PASS is invalid while any starter case is not PASS"
        )
    notes = args.notes.strip()
    if (
        overall != "PASS"
        or any(value != "PASS" for value in results.values())
    ) and not notes:
        raise RuntimeError(
            "--notes is required for FAIL or PASS WITH DOCUMENTED LIMITATION"
        )

    now = datetime.now().astimezone().isoformat()
    evidence: dict[str, object] = {
        "schema_version": 1,
        "issue": ISSUE,
        "source_commit": state["source_commit"],
        "bundle_sha256": expected_bundle_sha,
        "bundle_byte_length": state["bundle_byte_length"],
        "tester": args.tester,
        "date_local_time": now,
        "visual_inspection_confirmed": True,
        "inspection_scope": [
            "role labels",
            "header clarity",
            "footer clarity",
            "reviewer/reviewee distinction",
            "observer/observed distinction",
            "QR clearance",
            "writable-space preservation",
            "two-page consistency",
            "long realistic names",
            "long class ID",
            "long Session/Group labels",
            "no clipping",
            "copier-friendly small text",
        ],
        "case_results": results,
        "overall_result": overall,
        "notes": notes,
        "classification_source": "explicit owner/tester CLI input",
    }
    _write_json(run_root / EVIDENCE, evidence)

    lines = [
        "Issue #113 visual-review completion record",
        "",
        f"source commit: {state['source_commit']}",
        f"visual-review bundle: {BUNDLE_ZIP}",
        f"bundle byte length: {state['bundle_byte_length']}",
        f"bundle SHA-256: {expected_bundle_sha}",
        f"tester/date: {args.tester} / {now}",
        "visual inspection confirmed: YES",
    ]
    for case in CASES:
        lines.append(f"{case.display_label}: {results[case.key]}")
    lines.extend(
        [
            f"overall visual review: {overall}",
            f"notes: {notes or 'none'}",
            "installed-wheel acceptance: NOT YET RUN",
        ]
    )
    (run_root / COMMENT).write_text("\n".join(lines) + "\n", encoding="utf-8")

    state["status"] = "owner_visual_review_classified"
    state["evidence_relative_path"] = EVIDENCE
    state["owner_visual_classification"] = overall
    _write_json(run_root / RUN_STATE, state)

    print("Recorded explicit owner/tester visual-review classification.")
    print(f"Evidence: {run_root / EVIDENCE}")
    print(f"Issue-comment record: {run_root / COMMENT}")
    print(f"Overall visual review: {overall}")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare/classify issue #113 relationship visual review."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare")
    prepare.add_argument("run_root", type=Path)

    approve = subparsers.add_parser("approve")
    approve.add_argument("run_root", type=Path)
    approve.add_argument("--visual-inspection-confirmed", action="store_true")
    approve.add_argument("--tester", required=True)
    approve.add_argument("--fishbowl", choices=OUTCOMES, required=True)
    approve.add_argument("--talk-moves", choices=OUTCOMES, required=True)
    approve.add_argument("--writing", choices=OUTCOMES, required=True)
    approve.add_argument("--presentation", choices=OUTCOMES, required=True)
    approve.add_argument("--design-code", choices=OUTCOMES, required=True)
    approve.add_argument("--overall", choices=OUTCOMES, required=True)
    approve.add_argument("--notes", default="")
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.command == "prepare":
        return _prepare(Path(args.run_root).resolve())
    if args.command == "approve":
        return _approve(args)
    raise RuntimeError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
