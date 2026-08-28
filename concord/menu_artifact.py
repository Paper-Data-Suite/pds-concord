"""Teacher-facing Artifact, Page, assembly, Author, and Subject workflows."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from uuid import uuid4

from concord.menu_context import CancelMenuAction, MenuSessionContext
from concord.menu_navigation import (
    ConcordMenuChoice,
    NavigationChoice,
    QuitPDS,
    ReturnToMainMenu,
    navigation_hint_with_help,
    parse_menu_navigation,
)
from concord.menu_prompts import (
    choose_student,
    choose_students,
    confirm_write,
    handle_write_error,
    prompt_positive_int,
    prompt_text,
    select_one,
    show_result,
)
from concord.menu_ui import (
    clear_screen,
    pause_for_user,
    print_menu_header,
    print_navigation,
)
from concord.models import (
    ActorReference,
    ConcordRecordReference,
    CorePublicationReference,
    EvidenceReference,
    ParticipantReference,
    PrivacyPolicy,
    SubjectReference,
)
from concord.routing.rendering import (
    RenderArtifactPagesRequest,
    RenderPartialSuccessError,
    render_artifact_pages,
)
from concord.workflows import (
    ActivitySummary,
    AddArtifactAuthorRequest,
    AddArtifactSubjectRequest,
    ArtifactAuthorSummary,
    ArtifactSubjectSummary,
    ReplaceArtifactAuthorRequest,
    ReplaceArtifactSubjectRequest,
    UpdateArtifactAuthorRequest,
    UpdateArtifactSubjectRequest,
    add_artifact_author,
    add_artifact_subject,
    list_artifact_authors,
    list_artifact_subjects,
    list_artifacts,
    list_groups,
    list_sessions,
    replace_artifact_author,
    replace_artifact_subject,
    resolve_read_workspace_root,
    show_activity,
    show_artifact,
    show_artifact_author,
    show_artifact_subject,
    update_artifact_author,
    update_artifact_subject,
)
from concord.workflows.artifact import (
    ArtifactSummary,
    list_artifact_scan_occurrences,
)
from concord.workflows.artifact_assembly import (
    AssembleArtifactRequest,
    AssemblyPageSelection,
    assemble_returned_artifact,
)
from concord.workflows.artifact_page import (
    ArtifactPagePlan,
    ArtifactRoutePreparationPartialSuccessError,
    PrepareArtifactPagesRequest,
    list_artifact_pages,
    prepare_artifact_pages,
)
from concord.workflows.artifact_review import (
    AddArtifactReviewRequest,
    ArtifactReviewSummary,
    ReplaceArtifactReviewRequest,
    add_artifact_review,
    current_artifact_review,
    list_artifact_reviews,
    replace_artifact_review,
    show_artifact_review,
)
from concord.workflows.context import actor_reference
from concord.workflows.moderation import (
    AddModerationRecordRequest,
    ModerationSummary,
    ReplaceModerationRecordRequest,
    add_moderation_record,
    list_applicable_moderation_records,
    list_moderation_records,
    replace_moderation_record,
    show_moderation_record,
)


def _latest(activity: ActivitySummary) -> ActivitySummary:
    return show_activity(activity.class_id, activity.activity_id).summary


def _handle_error(
    activity: ActivitySummary,
    error: Exception,
    *,
    title: str = "Artifact Page Error",
) -> None:
    if isinstance(error, ArtifactRoutePreparationPartialSuccessError):
        result = error.result
        show_result(
            "Artifact Preparation Partial Success",
            (
                "Artifact/Page snapshot was published.",
                f"Snapshot: {result.commit.snapshot_revision}",
                f"Snapshot SHA-256: {result.commit.snapshot_sha256}",
                f"Routes verified: {result.routes_verified}/{result.routes_expected}",
                "Review canonical routes before retrying preparation.",
            ),
        )
        return
    if isinstance(error, RenderPartialSuccessError):
        show_result(
            "Artifact Render Partial Success",
            (
                "Rendered output is installed and durable.",
                f"Output: {error.output_path.name}",
                "Canonical lifecycle update is incomplete.",
                "Review canonical state before retrying rendering.",
            ),
        )
        return
    handle_write_error(
        error,
        reload=lambda: _latest(activity),
        error_title=title,
    )


def _prepare(activity: ActivitySummary, state: MenuSessionContext) -> None:
    artifact_id = prompt_text(
        "Prepare Artifact Pages",
        "Artifact Instance ID",
        help_text="Enter a durable synthetic identifier for this physical page set.",
    )
    template_id = prompt_text(
        "Prepare Artifact Pages",
        "Template version ID",
        help_text="Identify the template version used for this page set.",
    )
    count = prompt_positive_int(
        "Prepare Artifact Pages",
        "Physical page count",
        help_text="Each physical page receives its own durable route.",
        default=1,
    )
    assert artifact_id is not None and template_id is not None
    if not confirm_write(
        "Prepare Artifact Pages",
        "CREATE",
        (f"Activity: {activity.title}", f"Artifact: {artifact_id}", f"Pages: {count}"),
    ):
        return
    result = prepare_artifact_pages(
        PrepareArtifactPagesRequest(
            class_id=activity.class_id,
            activity_id=activity.activity_id,
            artifact_instance_id=artifact_id,
            template_version_id=template_id,
            artifact_category="student_work",
            expected_snapshot_revision=activity.snapshot_revision,
            actor=state.require_actor(),
            pages=tuple(
                ArtifactPagePlan(page_number=index) for index in range(1, count + 1)
            ),
            privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
        )
    )
    show_result(
        "Artifact Pages Prepared",
        (
            f"Artifact: {result.artifact_instance_id}",
            f"Routes verified: {result.routes_verified}/{result.routes_expected}",
            f"Snapshot: {result.commit.snapshot_revision}",
        ),
    )

def _list_pages(activity: ActivitySummary) -> None:
    pages = list_artifact_pages(activity.class_id, activity.activity_id)
    if not pages:
        show_result("Artifact Pages", ("No Artifact Pages have been prepared.",))
        return
    page = select_one(
        "Artifact Pages",
        pages,
        [
            f"{item.artifact_page_id}  page {item.page_number}  [{item.page_status}]"
            for item in pages
        ],
        help_text="Navigate every prepared page, then choose one for compact detail.",
    )
    show_result(
        "Artifact Page Detail",
        (
            f"Page: {page.artifact_page_id}",
            f"Artifact: {page.artifact_instance_id}",
            f"Physical page: {page.page_number}",
            f"Status: {page.page_status}",
            f"Route: {page.route_id or '-'}",
        ),
    )


def _list(activity: ActivitySummary) -> None:
    """Preserve the issue #27 private page-list helper contract."""
    _list_pages(activity)


def _render(activity: ActivitySummary, state: MenuSessionContext) -> None:
    artifact_id = prompt_text(
        "Render Artifact Pages",
        "Artifact Instance ID",
        help_text="Enter an already prepared Artifact Instance ID.",
    )
    assert artifact_id is not None
    if not confirm_write(
        "Render Artifact Pages",
        "RENDER",
        (f"Activity: {activity.title}", f"Artifact: {artifact_id}"),
    ):
        return
    result = render_artifact_pages(
        RenderArtifactPagesRequest(
            class_id=activity.class_id,
            activity_id=activity.activity_id,
            artifact_instance_id=artifact_id,
            expected_snapshot_revision=activity.snapshot_revision,
            actor=state.require_actor(),
        )
    )
    show_result(
        "Artifact Pages Rendered",
        (
            f"Artifact: {result.artifact_instance_id}",
            f"Pages: {result.page_count}",
            f"Output: {result.output_path.name}",
        ),
    )

def _choose_artifact(activity: ActivitySummary, *, title: str) -> ArtifactSummary:
    artifacts = list_artifacts(activity.class_id, activity.activity_id)
    return select_one(
        title,
        artifacts,
        [
            (
                f"{item.artifact_instance_id}  [{item.artifact_status}]  "
                f"returned {item.returned_required_page_count}/"
                f"{item.required_return_page_count}"
            )
            for item in artifacts
        ],
        help_text="Choose the Artifact Instance for this exact operation.",
    )


def _list_artifacts(activity: ActivitySummary) -> None:
    artifact = _choose_artifact(activity, title="Artifacts")
    detail = show_artifact(
        activity.class_id,
        activity.activity_id,
        artifact.artifact_instance_id,
    )
    item = detail.summary
    show_result(
        "Artifact Detail",
        (
            f"Artifact: {item.artifact_instance_id}",
            f"Category: {item.artifact_category}",
            f"Status: {item.artifact_status}",
            (
                "Returned required pages: "
                f"{item.returned_required_page_count}/"
                f"{item.required_return_page_count}"
            ),
            f"Authors: {item.current_author_count}",
            f"Subjects: {item.current_subject_count}",
            f"Session: {detail.session_id or '-'}",
            f"Group: {detail.group_id or '-'}",
            f"Privacy: {detail.privacy_classification}",
        ),
    )


def _assembly_selections(
    activity: ActivitySummary,
    artifact: ArtifactSummary,
) -> tuple[AssemblyPageSelection, ...]:
    occurrences = list_artifact_scan_occurrences(
        activity.class_id,
        activity.activity_id,
        artifact.artifact_instance_id,
    )
    grouped = defaultdict(list)
    for item in occurrences:
        grouped[item.artifact_page_id].append(item)
    selections = []
    for page_id, candidates in grouped.items():
        if len(candidates) < 2:
            continue
        selected = select_one(
            f"Choose Returned Occurrence - Page {candidates[0].logical_page_number}",
            tuple(candidates),
            [
                (
                    f"Scan {item.source_scan_id}; source page "
                    f"{item.source_page_number}; ref {item.scan_reference_id}"
                )
                for item in candidates
            ],
            help_text=(
                "Several retained physical occurrences exist for this Artifact Page. "
                "Choose the exact occurrence for this assembly only."
            ),
        )
        selections.append(
            AssemblyPageSelection(
                artifact_page_id=page_id,
                scan_reference_id=selected.scan_reference_id,
            )
        )
    return tuple(selections)


def _assemble(activity: ActivitySummary, state: MenuSessionContext) -> None:
    current = _latest(activity)
    artifact = _choose_artifact(current, title="Assemble Returned Artifact")
    selections = _assembly_selections(current, artifact)
    if not confirm_write(
        "Assemble Returned Artifact",
        "ASSEMBLE",
        (
            f"Activity: {current.title}",
            f"Artifact: {artifact.artifact_instance_id}",
            f"Exact occurrence selections: {len(selections)}",
        ),
    ):
        return
    result = assemble_returned_artifact(
        AssembleArtifactRequest(
            class_id=current.class_id,
            activity_id=current.activity_id,
            artifact_instance_id=artifact.artifact_instance_id,
            expected_snapshot_revision=current.snapshot_revision,
            actor=state.require_actor(),
            selections=selections,
        )
    )
    show_result(
        "Returned Artifact Assembled",
        (
            f"Artifact: {result.artifact_instance_id}",
            f"Assembly: {result.assembly_id}",
            f"Pages: {result.page_count}",
            f"Output: {result.output_path.name}",
            f"Reused existing exact assembly: {'yes' if result.reused else 'no'}",
        ),
    )


def _require_workspace() -> Path:
    root = resolve_read_workspace_root()
    if root is None:
        raise ValueError("The Paper Data Suite workspace is unavailable.")
    return root


def _author_status() -> str:
    values = ("proposed", "confirmed", "disputed", "unknown")
    return select_one(
        "Author Attribution Status",
        values,
        tuple(item.replace("_", " ").title() for item in values),
        help_text="Choose the current state of this explicit authorship claim.",
    )


def _choose_student_author_mode() -> str:
    values = (
        "individual_author",
        "co_author",
        "observer",
        "recorder",
        "recorder_for_group",
    )
    return select_one(
        "Authorship Mode",
        values,
        tuple(item.replace("_", " ").title() for item in values),
        help_text="Authorship describes how this person produced or represented work.",
    )


def _representation_status() -> str:
    values = (
        "individual_view",
        "recorder_summary",
        "majority_position",
        "unanimous_position",
        "multiple_named_positions",
        "no_consensus",
        "not_applicable",
    )
    return select_one(
        "Representation Status",
        values,
        tuple(item.replace("_", " ").title() for item in values),
        help_text="Describe what the recorder's work represents for the Group.",
    )


def _choose_author_semantics(
    activity: ActivitySummary,
    state: MenuSessionContext,
) -> tuple[
    ParticipantReference | ActorReference | ConcordRecordReference | None,
    str,
    str,
    str,
    str | None,
    str | None,
    str | None,
]:
    kinds = (
        "student",
        "collective_group",
        "current_teacher",
        "authorized_adult",
        "unknown",
    )
    kind = select_one(
        "Who Completed or Produced This Artifact?",
        kinds,
        (
            "Student",
            "Collective Group",
            "Current teacher",
            "Other authorized adult",
            "Unknown",
        ),
        help_text=(
            "Choose explicit authorship. Routing, Group Membership, and Role "
            "Assignment do not establish authorship."
        ),
    )
    if kind == "unknown":
        return None, "unknown", "unknown", "unknown", None, None, None
    if kind == "current_teacher":
        return (
            actor_reference(state.require_actor()),
            "teacher_author",
            _author_status(),
            "teacher",
            None,
            None,
            None,
        )
    if kind == "authorized_adult":
        actor_id = prompt_text(
            "Authorized Adult Author",
            "Actor ID",
            help_text="Enter the durable authorized-adult Actor identifier.",
        )
        owner = prompt_text(
            "Authorized Adult Author",
            "Owning system",
            help_text="Enter the lowercase system that owns this Actor identity.",
            default="concord",
        )
        label = prompt_text(
            "Authorized Adult Author",
            "Display label",
            help_text="Optional display-label snapshot for teacher presentation.",
            optional=True,
        )
        assert actor_id is not None and owner is not None
        return (
            ActorReference(
                actor_kind="authorized_adult",
                actor_id=actor_id,
                owning_system=owner,
                display_label_snapshot=label,
            ),
            "authorized_adult_author",
            _author_status(),
            "teacher",
            None,
            None,
            None,
        )
    if kind == "collective_group":
        groups = list_groups(activity.class_id, activity.activity_id)
        group = select_one(
            "Collective Group Author",
            groups,
            [f"{item.label} ({item.group_id})" for item in groups],
            help_text="A Group Author remains a Group identity, never a fake student.",
        )
        return (
            ConcordRecordReference(record_kind="group", record_id=group.group_id),
            "collective_group_author",
            _author_status(),
            "teacher",
            None,
            None,
            None,
        )

    student = choose_student(_require_workspace(), activity.class_id)
    reference = ParticipantReference(
        participant_kind="core_student",
        participant_id=student.student_id,
        owning_system="core",
    )
    mode = _choose_student_author_mode()
    represented_group_id = None
    representation_status = None
    if mode == "recorder_for_group":
        groups = list_groups(activity.class_id, activity.activity_id)
        group = select_one(
            "Represented Group",
            groups,
            [f"{item.label} ({item.group_id})" for item in groups],
            help_text="The recorder and represented Group remain separate identities.",
        )
        represented_group_id = group.group_id
        representation_status = _representation_status()
    role_assignment_id = prompt_text(
        "Author Role Context",
        "Role Assignment ID",
        help_text=(
            "Optional existing Role Assignment providing context. "
            "The Role does not create or prove authorship."
        ),
        optional=True,
    )
    return (
        reference,
        mode,
        _author_status(),
        "teacher",
        represented_group_id,
        role_assignment_id,
        representation_status,
    )


def _author_label(item: ArtifactAuthorSummary) -> str:
    relation = item.reference_display_label or "Unknown"
    state = "current" if item.is_current else "historical"
    return (
        f"{relation} - {item.authorship_mode.replace('_', ' ')} - "
        f"{item.attribution_status} [{state}]"
    )


def _choose_author(
    activity: ActivitySummary,
    *,
    include_historical: bool = False,
    title: str,
) -> ArtifactAuthorSummary:
    items = list_artifact_authors(
        activity.class_id,
        activity.activity_id,
        include_historical=include_historical,
    )
    return select_one(
        title,
        items,
        [_author_label(item) for item in items],
        help_text=(
            "Choose the explicit Artifact Author association to inspect or change."
        ),
    )


def _show_author(activity: ActivitySummary, *, historical: bool) -> None:
    selected = _choose_author(
        activity,
        include_historical=historical,
        title="Artifact Authors" if not historical else "Artifact Author History",
    )
    item = show_artifact_author(
        activity.class_id,
        activity.activity_id,
        selected.artifact_author_id,
    )
    show_result(
        "Artifact Author Detail",
        (
            f"Artifact: {item.artifact_instance_id}",
            f"Completed by: {item.reference_display_label or 'Unknown'}",
            f"Authorship mode: {item.authorship_mode}",
            f"Attribution status: {item.attribution_status}",
            f"Represents: {item.represented_group_id or '-'}",
            f"Role context: {item.role_assignment_id or '-'}",
            f"Current: {'yes' if item.is_current else 'no'}",
        ),
    )


def _add_author(activity: ActivitySummary, state: MenuSessionContext) -> None:
    current = _latest(activity)
    artifact = _choose_artifact(current, title="Add Artifact Author")
    author_id = prompt_text(
        "Add Artifact Author",
        "Artifact Author ID",
        help_text="Use an opaque durable association identifier.",
        default=f"author_{uuid4().hex}",
    )
    assert author_id is not None
    (
        reference,
        mode,
        status,
        source,
        group_id,
        role_id,
        representation,
    ) = _choose_author_semantics(current, state)
    if not confirm_write(
        "Add Artifact Author",
        "ADD",
        (
            f"Artifact: {artifact.artifact_instance_id}",
            f"Authorship mode: {mode}",
            f"Attribution status: {status}",
        ),
    ):
        return
    result = add_artifact_author(
        AddArtifactAuthorRequest(
            class_id=current.class_id,
            activity_id=current.activity_id,
            artifact_instance_id=artifact.artifact_instance_id,
            artifact_author_id=author_id,
            author_reference=reference,
            authorship_mode=mode,
            attribution_status=status,
            attribution_source=source,
            expected_snapshot_revision=current.snapshot_revision,
            actor=state.require_actor(),
            represented_group_id=group_id,
            role_assignment_id=role_id,
            representation_status=representation,
        )
    )
    show_result(
        "Artifact Author Added",
        (
            f"Artifact Author: {result.association_id}",
            f"Snapshot: {result.commit.snapshot_revision}",
        ),
    )


def _update_author(activity: ActivitySummary, state: MenuSessionContext) -> None:
    current = _latest(activity)
    selected = _choose_author(current, title="Update Artifact Author")
    status = _author_status()
    if not confirm_write(
        "Update Artifact Author",
        "UPDATE",
        (
            f"Completed by: {selected.reference_display_label or 'Unknown'}",
            f"New attribution status: {status}",
        ),
    ):
        return
    result = update_artifact_author(
        UpdateArtifactAuthorRequest(
            class_id=current.class_id,
            activity_id=current.activity_id,
            artifact_author_id=selected.artifact_author_id,
            attribution_status=status,
            expected_snapshot_revision=current.snapshot_revision,
            actor=state.require_actor(),
        )
    )
    show_result(
        "Artifact Author Updated",
        (
            f"Artifact Author: {result.association_id}",
            f"Snapshot: {result.commit.snapshot_revision}",
        ),
    )


def _correct_author(activity: ActivitySummary, state: MenuSessionContext) -> None:
    current = _latest(activity)
    selected = _choose_author(current, title="Correct Artifact Author")
    replacement_id = prompt_text(
        "Correct Artifact Author",
        "Replacement Artifact Author ID",
        help_text="Create a new durable successor association.",
        default=f"author_{uuid4().hex}",
    )
    correction_id = prompt_text(
        "Correct Artifact Author",
        "Correction ID",
        help_text="Create an auditable correction identity.",
        default=f"correction_{uuid4().hex}",
    )
    reason = prompt_text(
        "Correct Artifact Author",
        "Reason",
        help_text="Briefly state why the predecessor attribution is being corrected.",
    )
    assert replacement_id is not None
    assert correction_id is not None
    assert reason is not None
    (
        reference,
        mode,
        status,
        source,
        group_id,
        role_id,
        representation,
    ) = _choose_author_semantics(current, state)
    if not confirm_write(
        "Correct Artifact Author",
        "CORRECT",
        (
            f"Predecessor: {selected.artifact_author_id}",
            f"Replacement: {replacement_id}",
            f"New authorship mode: {mode}",
        ),
    ):
        return
    result = replace_artifact_author(
        ReplaceArtifactAuthorRequest(
            class_id=current.class_id,
            activity_id=current.activity_id,
            artifact_author_id=selected.artifact_author_id,
            replacement_artifact_author_id=replacement_id,
            correction_id=correction_id,
            reason=reason,
            author_reference=reference,
            authorship_mode=mode,
            attribution_status=status,
            attribution_source=source,
            expected_snapshot_revision=current.snapshot_revision,
            actor=state.require_actor(),
            represented_group_id=group_id,
            role_assignment_id=role_id,
            representation_status=representation,
        )
    )
    show_result(
        "Artifact Author Corrected",
        (
            f"Successor: {result.association_id}",
            f"Correction: {correction_id}",
            f"Snapshot: {result.commit.snapshot_revision}",
        ),
    )


def _launch_author_menu(
    activity: ActivitySummary,
    state: MenuSessionContext,
) -> None:
    while True:
        clear_screen()
        print_menu_header("Artifact Authors")
        print("1. List / inspect current Authors")
        print("2. Add Author")
        print("3. Update attribution status")
        print("4. Correct / replace Author")
        print("5. View Author history")
        print_navigation()
        print()
        choice = input("Select an option: ").strip()
        navigation = parse_menu_navigation(choice)
        try:
            if navigation is ConcordMenuChoice.HELP:
                show_result(
                    "Artifact Author Help",
                    (
                        "Authors identify who produced, recorded, or represented work.",
                        (
                            "Routing, Membership, and Role context do not establish "
                            "authorship."
                        ),
                    ),
                )
            elif navigation is NavigationChoice.BACK:
                return
            elif choice == "1":
                _show_author(activity, historical=False)
            elif choice == "2":
                _add_author(activity, state)
            elif choice == "3":
                _update_author(activity, state)
            elif choice == "4":
                _correct_author(activity, state)
            elif choice == "5":
                _show_author(activity, historical=True)
            else:
                print(navigation_hint_with_help())
                pause_for_user()
        except CancelMenuAction:
            continue
        except (ReturnToMainMenu, QuitPDS, KeyboardInterrupt, EOFError):
            raise
        except Exception as error:
            _handle_error(activity, error, title="Artifact Author Error")


def _subject_status() -> str:
    values = ("proposed", "confirmed", "disputed", "unresolved")
    return select_one(
        "Subject Confirmation Status",
        values,
        tuple(item.replace("_", " ").title() for item in values),
        help_text="Choose the current state of this explicit Subject association.",
    )


def _choose_subject_semantics(
    activity: ActivitySummary,
) -> tuple[SubjectReference, str, str, str, str | None]:
    kinds = (
        "core_student",
        "concord_group",
        "concord_session",
        "concord_activity",
        "concord_artifact_instance",
        "external_record",
    )
    kind = select_one(
        "What Does This Artifact Concern?",
        kinds,
        (
            "Student",
            "Group",
            "Session",
            "Activity",
            "Another Artifact",
            "External record",
        ),
        help_text=(
            "Subject identity is independent from authorship, routing, and "
            "Score targets."
        ),
    )
    default_role = "general_subject"
    criterion_id = None
    if kind == "core_student":
        student = choose_student(_require_workspace(), activity.class_id)
        reference = SubjectReference(
            subject_kind=kind,
            subject_id=student.student_id,
            owning_system="core",
        )
        default_role = "observed_participant"
    elif kind == "concord_group":
        groups = list_groups(activity.class_id, activity.activity_id)
        group = select_one(
            "Artifact Concerns Group",
            groups,
            [f"{item.label} ({item.group_id})" for item in groups],
            help_text="Choose the exact Group this Artifact concerns.",
        )
        reference = SubjectReference(
            subject_kind=kind,
            subject_id=group.group_id,
            owning_system="concord",
        )
        default_role = "represented_group"
    elif kind == "concord_session":
        sessions = list_sessions(activity.class_id, activity.activity_id)
        session = select_one(
            "Artifact Concerns Session",
            sessions,
            [
                f"{item.label or item.session_id} ({item.session_id})"
                for item in sessions
            ],
            help_text="Choose the exact Session this Artifact concerns.",
        )
        reference = SubjectReference(
            subject_kind=kind,
            subject_id=session.session_id,
            owning_system="concord",
        )
        default_role = "session_context"
    elif kind == "concord_activity":
        reference = SubjectReference(
            subject_kind=kind,
            subject_id=activity.activity_id,
            owning_system="concord",
        )
        default_role = "activity_context"
    elif kind == "concord_artifact_instance":
        artifact = _choose_artifact(activity, title="Artifact Subject")
        reference = SubjectReference(
            subject_kind=kind,
            subject_id=artifact.artifact_instance_id,
            owning_system="concord",
        )
        default_role = "evaluated_artifact"
    else:
        subject_id = prompt_text(
            "External Artifact Subject",
            "External record ID",
            help_text="Enter the durable source-system record identifier.",
        )
        owner = prompt_text(
            "External Artifact Subject",
            "Owning system",
            help_text="Enter the lowercase source-system identifier.",
        )
        contract = prompt_text(
            "External Artifact Subject",
            "Contract version",
            help_text="Optional source-system contract/version identifier.",
            optional=True,
        )
        assert subject_id is not None and owner is not None
        reference = SubjectReference(
            subject_kind=kind,
            subject_id=subject_id,
            owning_system=owner,
            contract_version=contract,
        )
    role = prompt_text(
        "Artifact Subject Role",
        "Subject role",
        help_text=(
            "Use the built-in relationship or an approved namespace-qualified "
            "extension."
        ),
        default=default_role,
    )
    criterion_id = prompt_text(
        "Artifact Subject Criterion Context",
        "Criterion ID",
        help_text=(
            "Optional existing Criterion context only. This does not create a Score."
        ),
        optional=True,
    )
    assert role is not None
    return reference, role, _subject_status(), "teacher", criterion_id


def _subject_label(item: ArtifactSubjectSummary) -> str:
    label = item.reference_display_label or item.subject_reference.subject_id
    state = "current" if item.is_current else "historical"
    return (
        f"{label} - {item.subject_role.replace('_', ' ')} - "
        f"{item.confirmation_status} [{state}]"
    )


def _choose_subject(
    activity: ActivitySummary,
    *,
    include_historical: bool = False,
    title: str,
) -> ArtifactSubjectSummary:
    items = list_artifact_subjects(
        activity.class_id,
        activity.activity_id,
        include_historical=include_historical,
    )
    return select_one(
        title,
        items,
        [_subject_label(item) for item in items],
        help_text=(
            "Choose the explicit Artifact Subject association to inspect or change."
        ),
    )


def _show_subject(activity: ActivitySummary, *, historical: bool) -> None:
    selected = _choose_subject(
        activity,
        include_historical=historical,
        title="Artifact Subjects" if not historical else "Artifact Subject History",
    )
    item = show_artifact_subject(
        activity.class_id,
        activity.activity_id,
        selected.artifact_subject_id,
    )
    show_result(
        "Artifact Subject Detail",
        (
            f"Artifact: {item.artifact_instance_id}",
            (
                "Artifact concerns: "
                f"{item.reference_display_label or item.subject_reference.subject_id}"
            ),
            f"Subject kind: {item.subject_reference.subject_kind}",
            f"Subject role: {item.subject_role}",
            f"Confirmation: {item.confirmation_status}",
            f"Criterion context: {item.criterion_id or '-'}",
            f"Current: {'yes' if item.is_current else 'no'}",
        ),
    )


def _add_subject(activity: ActivitySummary, state: MenuSessionContext) -> None:
    current = _latest(activity)
    artifact = _choose_artifact(current, title="Add Artifact Subject")
    subject_id = prompt_text(
        "Add Artifact Subject",
        "Artifact Subject ID",
        help_text="Use an opaque durable association identifier.",
        default=f"subject_{uuid4().hex}",
    )
    assert subject_id is not None
    reference, role, status, source, criterion_id = _choose_subject_semantics(
        current
    )
    if not confirm_write(
        "Add Artifact Subject",
        "ADD",
        (
            f"Artifact: {artifact.artifact_instance_id}",
            f"Subject kind: {reference.subject_kind}",
            f"Subject role: {role}",
            f"Confirmation: {status}",
        ),
    ):
        return
    result = add_artifact_subject(
        AddArtifactSubjectRequest(
            class_id=current.class_id,
            activity_id=current.activity_id,
            artifact_instance_id=artifact.artifact_instance_id,
            artifact_subject_id=subject_id,
            subject_reference=reference,
            subject_role=role,
            confirmation_status=status,
            assignment_source=source,
            expected_snapshot_revision=current.snapshot_revision,
            actor=state.require_actor(),
            criterion_id=criterion_id,
        )
    )
    show_result(
        "Artifact Subject Added",
        (
            f"Artifact Subject: {result.association_id}",
            f"Snapshot: {result.commit.snapshot_revision}",
        ),
    )


def _update_subject(activity: ActivitySummary, state: MenuSessionContext) -> None:
    current = _latest(activity)
    selected = _choose_subject(current, title="Update Artifact Subject")
    status = _subject_status()
    if not confirm_write(
        "Update Artifact Subject",
        "UPDATE",
        (
            f"Artifact Subject: {selected.artifact_subject_id}",
            f"New confirmation status: {status}",
        ),
    ):
        return
    result = update_artifact_subject(
        UpdateArtifactSubjectRequest(
            class_id=current.class_id,
            activity_id=current.activity_id,
            artifact_subject_id=selected.artifact_subject_id,
            confirmation_status=status,
            expected_snapshot_revision=current.snapshot_revision,
            actor=state.require_actor(),
        )
    )
    show_result(
        "Artifact Subject Updated",
        (
            f"Artifact Subject: {result.association_id}",
            f"Snapshot: {result.commit.snapshot_revision}",
        ),
    )


def _correct_subject(activity: ActivitySummary, state: MenuSessionContext) -> None:
    current = _latest(activity)
    selected = _choose_subject(current, title="Correct Artifact Subject")
    replacement_id = prompt_text(
        "Correct Artifact Subject",
        "Replacement Artifact Subject ID",
        help_text="Create a new durable successor association.",
        default=f"subject_{uuid4().hex}",
    )
    correction_id = prompt_text(
        "Correct Artifact Subject",
        "Correction ID",
        help_text="Create an auditable correction identity.",
        default=f"correction_{uuid4().hex}",
    )
    reason = prompt_text(
        "Correct Artifact Subject",
        "Reason",
        help_text="Briefly state why the predecessor Subject is being corrected.",
    )
    assert replacement_id is not None
    assert correction_id is not None
    assert reason is not None
    reference, role, status, source, criterion_id = _choose_subject_semantics(
        current
    )
    if not confirm_write(
        "Correct Artifact Subject",
        "CORRECT",
        (
            f"Predecessor: {selected.artifact_subject_id}",
            f"Replacement: {replacement_id}",
            f"New Subject kind: {reference.subject_kind}",
        ),
    ):
        return
    result = replace_artifact_subject(
        ReplaceArtifactSubjectRequest(
            class_id=current.class_id,
            activity_id=current.activity_id,
            artifact_subject_id=selected.artifact_subject_id,
            replacement_artifact_subject_id=replacement_id,
            correction_id=correction_id,
            reason=reason,
            subject_reference=reference,
            subject_role=role,
            confirmation_status=status,
            assignment_source=source,
            expected_snapshot_revision=current.snapshot_revision,
            actor=state.require_actor(),
            criterion_id=criterion_id,
        )
    )
    show_result(
        "Artifact Subject Corrected",
        (
            f"Successor: {result.association_id}",
            f"Correction: {correction_id}",
            f"Snapshot: {result.commit.snapshot_revision}",
        ),
    )


def _launch_subject_menu(
    activity: ActivitySummary,
    state: MenuSessionContext,
) -> None:
    while True:
        clear_screen()
        print_menu_header("Artifact Subjects")
        print("1. List / inspect current Subjects")
        print("2. Add Subject")
        print("3. Update confirmation status")
        print("4. Correct / replace Subject")
        print("5. View Subject history")
        print_navigation()
        print()
        choice = input("Select an option: ").strip()
        navigation = parse_menu_navigation(choice)
        try:
            if navigation is ConcordMenuChoice.HELP:
                show_result(
                    "Artifact Subject Help",
                    (
                        "Subjects identify whom or what the Artifact concerns.",
                        "Subjects do not establish authorship or a Score target.",
                    ),
                )
            elif navigation is NavigationChoice.BACK:
                return
            elif choice == "1":
                _show_subject(activity, historical=False)
            elif choice == "2":
                _add_subject(activity, state)
            elif choice == "3":
                _update_subject(activity, state)
            elif choice == "4":
                _correct_subject(activity, state)
            elif choice == "5":
                _show_subject(activity, historical=True)
            else:
                print(navigation_hint_with_help())
                pause_for_user()
        except CancelMenuAction:
            continue
        except (ReturnToMainMenu, QuitPDS, KeyboardInterrupt, EOFError):
            raise
        except Exception as error:
            _handle_error(activity, error, title="Artifact Subject Error")



def _review_choice(title: str, values: tuple[str, ...], help_text: str) -> str:
    return select_one(
        title,
        values,
        tuple(item.replace("_", " ").title() for item in values),
        help_text=help_text,
    )


def _review_values() -> tuple[
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str | None,
    PrivacyPolicy,
]:
    readability = _review_choice(
        "Review Readability",
        ("readable", "partially_readable", "unreadable", "not_reviewed"),
        "Record the human readability judgment; Concord does not infer it.",
    )
    completeness = _review_choice(
        "Review Page Completeness",
        ("complete", "partially_complete", "incomplete", "not_reviewed"),
        "Judge evidence completeness independently from Artifact return status.",
    )
    filing = _review_choice(
        "Review Filing",
        ("correct", "misfiled", "duplicate", "unresolved", "not_reviewed"),
        "Review may flag filing without rerouting or rewriting evidence.",
    )
    author = _review_choice(
        "Review Author Attribution",
        ("confirmed", "qualified", "disputed", "unknown", "not_reviewed"),
        "Review attribution without editing the explicit Author relationship.",
    )
    subject = _review_choice(
        "Review Subject Attribution",
        ("confirmed", "qualified", "disputed", "unresolved", "not_reviewed"),
        "Review Subject attribution without editing the Subject relationship.",
    )
    privacy = _review_choice(
        "Review Evidence Privacy",
        (
            "teacher_restricted",
            "teacher_and_subjects",
            "group_and_teacher",
            "classroom_shared",
        ),
        "Judge the evidence privacy classification explicitly.",
    )
    relevance = _review_choice(
        "Review Relevance",
        ("relevant", "partially_relevant", "not_relevant", "not_reviewed"),
        "Record whether the evidence is relevant to its intended use.",
    )
    moderation = _review_choice(
        "Review Moderation Requirement",
        ("required", "not_required", "completed"),
        "Review may require Moderation but does not create it automatically.",
    )
    readiness = _review_choice(
        "Review Scoring Readiness",
        ("ready", "ready_with_qualification", "not_ready"),
        "Readiness only permits later consideration; it does not create a Score.",
    )
    outcome = _review_choice(
        "Review Outcome",
        (
            "ready",
            "ready_with_qualification",
            "incomplete",
            "unreadable",
            "misrouted",
            "duplicate",
            "awaiting_correction",
            "awaiting_additional_evidence",
            "moderation_required",
            "not_suitable_for_scoring",
        ),
        "Choose the overall human Review outcome.",
    )
    notes = prompt_text(
        "Review Notes",
        "Notes",
        help_text="Record a concise Review explanation when useful.",
        optional=outcome != "ready_with_qualification",
    )
    review_privacy = _review_choice(
        "Review Record Privacy",
        (
            "teacher_restricted",
            "teacher_and_subjects",
            "group_and_teacher",
            "classroom_shared",
        ),
        "This protects the Review record itself, independently from the evidence.",
    )
    return (
        readability,
        completeness,
        filing,
        author,
        subject,
        privacy,
        relevance,
        moderation,
        readiness,
        outcome,
        notes,
        PrivacyPolicy(classification=review_privacy),
    )


def _review_label(item: ArtifactReviewSummary) -> str:
    state = "current" if item.is_current else "historical"
    return (
        f"{item.artifact_instance_id} - {item.review_outcome.replace('_', ' ')} - "
        f"{item.scoring_readiness.replace('_', ' ')} [{state}]"
    )


def _show_review_detail(item: ArtifactReviewSummary) -> None:
    show_result(
        "Artifact Review Detail",
        (
            f"Artifact: {item.artifact_instance_id}",
            f"Review: {item.artifact_review_id}",
            f"Reviewer: {item.reviewer_display_label or '-'}",
            f"Reviewed at: {item.reviewed_at}",
            f"Readability: {item.readability_judgment}",
            f"Page completeness: {item.page_completeness_judgment}",
            f"Filing: {item.filing_judgment}",
            f"Author judgment: {item.author_judgment}",
            f"Subject judgment: {item.subject_judgment}",
            f"Privacy judgment: {item.privacy_judgment}",
            f"Relevance: {item.relevance_judgment}",
            f"Moderation: {item.moderation_requirement}",
            f"Scoring readiness: {item.scoring_readiness}",
            f"Outcome: {item.review_outcome}",
            f"Notes: {item.notes or '-'}",
            f"Review privacy: {item.privacy_policy.classification}",
            f"Current: {'yes' if item.is_current else 'no'}",
        ),
    )


def _view_current_review(activity: ActivitySummary) -> None:
    artifact = _choose_artifact(activity, title="View Current Artifact Review")
    item = current_artifact_review(
        activity.class_id,
        activity.activity_id,
        artifact.artifact_instance_id,
    )
    if item is None:
        show_result(
            "Artifact Review",
            (f"Artifact {artifact.artifact_instance_id} has no current Review.",),
        )
        return
    _show_review_detail(item)


def _view_review_history(activity: ActivitySummary) -> None:
    items = list_artifact_reviews(
        activity.class_id,
        activity.activity_id,
        include_historical=True,
    )
    selected = select_one(
        "Artifact Review History",
        items,
        [_review_label(item) for item in items],
        help_text="Choose an exact preserved Review record to inspect.",
    )
    _show_review_detail(
        show_artifact_review(
            activity.class_id,
            activity.activity_id,
            selected.artifact_review_id,
        )
    )


def _record_review(activity: ActivitySummary, state: MenuSessionContext) -> None:
    current = _latest(activity)
    artifact = _choose_artifact(current, title="Record Artifact Review")
    detail = show_artifact(
        current.class_id,
        current.activity_id,
        artifact.artifact_instance_id,
    )
    show_result(
        "Artifact Review Context",
        (
            f"Artifact: {artifact.artifact_instance_id}",
            f"Status: {artifact.artifact_status}",
            (
                "Returned required pages: "
                f"{artifact.returned_required_page_count}/"
                f"{artifact.required_return_page_count}"
            ),
            f"Current Authors: {artifact.current_author_count}",
            f"Current Subjects: {artifact.current_subject_count}",
            f"Artifact privacy: {detail.privacy_classification}",
            "These facts are context only; Review judgments remain explicit.",
        ),
    )
    review_id = prompt_text(
        "Record Artifact Review",
        "Artifact Review ID",
        help_text="Use an opaque durable Review identifier.",
        default=f"review_{uuid4().hex}",
    )
    assert review_id is not None
    (
        readability,
        completeness,
        filing,
        author,
        subject,
        privacy,
        relevance,
        moderation,
        readiness,
        outcome,
        notes,
        review_privacy,
    ) = _review_values()
    if not confirm_write(
        "Record Artifact Review",
        "REVIEW",
        (
            f"Artifact: {artifact.artifact_instance_id}",
            f"Outcome: {outcome}",
            f"Scoring readiness: {readiness}",
            f"Moderation requirement: {moderation}",
        ),
    ):
        return
    result = add_artifact_review(
        AddArtifactReviewRequest(
            class_id=current.class_id,
            activity_id=current.activity_id,
            artifact_instance_id=artifact.artifact_instance_id,
            artifact_review_id=review_id,
            readability_judgment=readability,
            page_completeness_judgment=completeness,
            filing_judgment=filing,
            author_judgment=author,
            subject_judgment=subject,
            privacy_judgment=privacy,
            relevance_judgment=relevance,
            moderation_requirement=moderation,
            scoring_readiness=readiness,
            review_outcome=outcome,
            notes=notes,
            privacy_policy=review_privacy,
            expected_snapshot_revision=current.snapshot_revision,
            actor=state.require_actor(),
        )
    )
    show_result(
        "Artifact Review Recorded",
        (
            f"Review: {result.artifact_review_id}",
            f"Snapshot: {result.commit.snapshot_revision}",
        ),
    )


def _replace_review(activity: ActivitySummary, state: MenuSessionContext) -> None:
    current = _latest(activity)
    items = list_artifact_reviews(
        current.class_id,
        current.activity_id,
        include_historical=False,
    )
    predecessor = select_one(
        "Revise Current Artifact Review",
        items,
        [_review_label(item) for item in items],
        help_text="Only a current Review head may receive a successor.",
    )
    replacement_id = prompt_text(
        "Revise Artifact Review",
        "Replacement Review ID",
        help_text="Create a new opaque durable Review successor identifier.",
        default=f"review_{uuid4().hex}",
    )
    correction_id = prompt_text(
        "Revise Artifact Review",
        "Correction ID",
        help_text="Create the audit record that connects predecessor and successor.",
        default=f"correction_{uuid4().hex}",
    )
    reason = prompt_text(
        "Revise Artifact Review",
        "Reason",
        help_text="State why a successor Review is being recorded.",
    )
    assert replacement_id is not None
    assert correction_id is not None
    assert reason is not None
    (
        readability,
        completeness,
        filing,
        author,
        subject,
        privacy,
        relevance,
        moderation,
        readiness,
        outcome,
        notes,
        review_privacy,
    ) = _review_values()
    if not confirm_write(
        "Revise Artifact Review",
        "REVISE",
        (
            f"Predecessor: {predecessor.artifact_review_id}",
            f"Successor: {replacement_id}",
            f"Outcome: {outcome}",
            f"Moderation requirement: {moderation}",
        ),
    ):
        return
    result = replace_artifact_review(
        ReplaceArtifactReviewRequest(
            class_id=current.class_id,
            activity_id=current.activity_id,
            artifact_review_id=predecessor.artifact_review_id,
            replacement_artifact_review_id=replacement_id,
            correction_id=correction_id,
            reason=reason,
            readability_judgment=readability,
            page_completeness_judgment=completeness,
            filing_judgment=filing,
            author_judgment=author,
            subject_judgment=subject,
            privacy_judgment=privacy,
            relevance_judgment=relevance,
            moderation_requirement=moderation,
            scoring_readiness=readiness,
            review_outcome=outcome,
            notes=notes,
            privacy_policy=review_privacy,
            correction_privacy_policy=PrivacyPolicy(
                classification="teacher_restricted"
            ),
            expected_snapshot_revision=current.snapshot_revision,
            actor=state.require_actor(),
        )
    )
    show_result(
        "Artifact Review Revised",
        (
            f"Successor: {result.artifact_review_id}",
            f"Correction: {correction_id}",
            f"Snapshot: {result.commit.snapshot_revision}",
        ),
    )


def _launch_review_menu(
    activity: ActivitySummary,
    state: MenuSessionContext,
) -> None:
    while True:
        clear_screen()
        print_menu_header("Artifact Review")
        print("1. View current Review")
        print("2. View Review history")
        print("3. Record Review")
        print("4. Record successor / corrected Review")
        print_navigation()
        print()
        choice = input("Select an option: ").strip()
        navigation = parse_menu_navigation(choice)
        try:
            if navigation is ConcordMenuChoice.HELP:
                show_result(
                    "Artifact Review Help",
                    (
                        "Review records explicit human evidence-readiness judgments.",
                        (
                            "Returned evidence is not automatically reviewed "
                            "or score-ready."
                        ),
                        (
                            "Review does not rewrite evidence, Authors, Subjects, "
                            "or Scores."
                        ),
                    ),
                )
            elif navigation is NavigationChoice.BACK:
                return
            elif choice == "1":
                _view_current_review(activity)
            elif choice == "2":
                _view_review_history(activity)
            elif choice == "3":
                _record_review(activity, state)
            elif choice == "4":
                _replace_review(activity, state)
            else:
                print(navigation_hint_with_help())
                pause_for_user()
        except CancelMenuAction:
            continue
        except (ReturnToMainMenu, QuitPDS, KeyboardInterrupt, EOFError):
            raise
        except Exception as error:
            _handle_error(activity, error, title="Artifact Review Error")


def _evidence_requirement() -> str:
    return select_one(
        "Evidence Moderation Requirement",
        ("not_required", "required"),
        ("Not required by the evidence reference", "Required"),
        help_text=(
            "This flag is explicit evidence metadata. Current Artifact Review "
            "requirements remain independently effective."
        ),
    )


def _choose_moderation_evidence(activity: ActivitySummary) -> EvidenceReference:
    kind = select_one(
        "Moderation Evidence",
        ("artifact", "page", "external"),
        ("Artifact Instance", "Artifact Page", "External evidence"),
        help_text="Choose the exact immutable evidence relationship to moderate.",
    )
    requirement = _evidence_requirement()
    if kind == "artifact":
        artifact = _choose_artifact(activity, title="Moderation Artifact Evidence")
        return EvidenceReference(
            evidence_kind="artifact_instance",
            owning_system="concord",
            record_id=artifact.artifact_instance_id,
            moderation_requirement=requirement,
        )
    if kind == "page":
        pages = list_artifact_pages(activity.class_id, activity.activity_id)
        page = select_one(
            "Moderation Artifact Page Evidence",
            pages,
            [
                f"{item.artifact_page_id} - page {item.page_number} "
                f"[{item.page_status}]"
                for item in pages
            ],
            help_text="Choose the exact Artifact Page evidence record.",
        )
        return EvidenceReference(
            evidence_kind="artifact_page",
            owning_system="concord",
            record_id=page.artifact_page_id,
            moderation_requirement=requirement,
        )

    evidence_kind = select_one(
        "External Evidence Type",
        ("scoreform_result", "quillan_response", "external_record"),
        ("ScoreForm result", "Quillan response", "External record"),
        help_text="Concord references external evidence without importing its package.",
    )
    owner = prompt_text(
        "External Moderation Evidence",
        "Owning system",
        help_text="Enter the lowercase source-system identifier.",
    )
    record_id = prompt_text(
        "External Moderation Evidence",
        "Record ID",
        help_text="Enter the exact source-system evidence record identifier.",
    )
    contract = prompt_text(
        "External Moderation Evidence",
        "Contract version",
        help_text="Optional immutable evidence contract/version identifier.",
        optional=True,
    )
    lineage_kind = select_one(
        "External Evidence Lineage",
        ("version", "publication"),
        ("Exact immutable source version", "Core Publication reference"),
        help_text="External evidence must preserve immutable source lineage.",
    )
    immutable_version = None
    publication = None
    if lineage_kind == "version":
        immutable_version = prompt_text(
            "External Evidence Lineage",
            "Immutable source version",
            help_text=(
                "Enter the exact immutable source revision, never latest/current."
            ),
        )
    else:
        publication_id = prompt_text(
            "External Evidence Lineage",
            "Core Publication ID",
            help_text="Enter the exact Core Publication Record identifier.",
        )
        schema_version = prompt_text(
            "External Evidence Lineage",
            "Publication schema version",
            help_text="Optional exact publication schema version.",
            optional=True,
        )
        assert publication_id is not None
        publication = CorePublicationReference(
            publication_id=publication_id,
            publication_schema_version=schema_version,
        )
    assert owner is not None and record_id is not None
    return EvidenceReference(
        evidence_kind=evidence_kind,
        owning_system=owner,
        record_id=record_id,
        contract_version=contract,
        source_publication_reference=publication,
        immutable_source_version=immutable_version,
        moderation_requirement=requirement,
    )


def _choose_moderation_subjects(
    activity: ActivitySummary,
) -> tuple[SubjectReference, ...]:
    kind = select_one(
        "Moderation Subject Scope",
        (
            "general",
            "students",
            "group",
            "session",
            "activity",
            "artifact",
            "external",
        ),
        (
            "General evidence decision - no Subject scope",
            "One or more students",
            "Group",
            "Session",
            "Activity",
            "Artifact",
            "External record",
        ),
        help_text=(
            "Subject scope is explicit and is never inferred from Authors, "
            "Artifact Subjects, or Group Membership."
        ),
    )
    if kind == "general":
        return ()
    if kind == "students":
        students = choose_students(_require_workspace(), activity.class_id)
        return tuple(
            SubjectReference(
                subject_kind="core_student",
                subject_id=student.student_id,
                owning_system="core",
            )
            for student in students
        )
    if kind == "group":
        groups = list_groups(activity.class_id, activity.activity_id)
        group = select_one(
            "Moderation Group Scope",
            groups,
            [f"{item.label} ({item.group_id})" for item in groups],
            help_text="Choose the exact Concord Group scope.",
        )
        return (
            SubjectReference(
                subject_kind="concord_group",
                subject_id=group.group_id,
                owning_system="concord",
            ),
        )
    if kind == "session":
        sessions = list_sessions(activity.class_id, activity.activity_id)
        session = select_one(
            "Moderation Session Scope",
            sessions,
            [
                f"{item.label or item.session_id} ({item.session_id})"
                for item in sessions
            ],
            help_text="Choose the exact Concord Session scope.",
        )
        return (
            SubjectReference(
                subject_kind="concord_session",
                subject_id=session.session_id,
                owning_system="concord",
            ),
        )
    if kind == "activity":
        return (
            SubjectReference(
                subject_kind="concord_activity",
                subject_id=activity.activity_id,
                owning_system="concord",
            ),
        )
    if kind == "artifact":
        artifact = _choose_artifact(activity, title="Moderation Artifact Subject Scope")
        return (
            SubjectReference(
                subject_kind="concord_artifact_instance",
                subject_id=artifact.artifact_instance_id,
                owning_system="concord",
            ),
        )
    subject_id = prompt_text(
        "External Moderation Subject",
        "External record ID",
        help_text="Enter the exact external Subject identifier.",
    )
    owner = prompt_text(
        "External Moderation Subject",
        "Owning system",
        help_text="Enter the lowercase external owning system.",
    )
    contract = prompt_text(
        "External Moderation Subject",
        "Contract version",
        help_text="Optional external Subject contract/version.",
        optional=True,
    )
    assert subject_id is not None and owner is not None
    return (
        SubjectReference(
            subject_kind="external_record",
            subject_id=subject_id,
            owning_system=owner,
            contract_version=contract,
        ),
    )


def _moderation_values() -> tuple[str, str, str, str | None, PrivacyPolicy]:
    status = select_one(
        "Moderation Status",
        (
            "accepted",
            "accepted_with_qualification",
            "insufficient",
            "disputed",
            "rejected",
            "not_used_for_scoring",
        ),
        (
            "Accepted",
            "Accepted with qualification",
            "Insufficient",
            "Disputed",
            "Rejected",
            "Not used for scoring",
        ),
        help_text="Record the human reliability/fairness decision.",
    )
    permitted_use = select_one(
        "Moderation Permitted Use",
        (
            "support_group_score",
            "support_named_subject",
            "corroborate_only",
            "formative_only",
            "not_independently_determine_score",
            "not_be_used_for_scoring",
        ),
        (
            "Support Group Score",
            "Support named Subject",
            "Corroborate only",
            "Formative only",
            "May not independently determine Score",
            "Must not be used for scoring",
        ),
        help_text="Permission limits later evidence use; it does not create a Score.",
    )
    rationale = prompt_text(
        "Moderation Rationale",
        "Rationale",
        help_text="Record the explicit human reason for this Moderation decision.",
    )
    qualification = prompt_text(
        "Moderation Qualification",
        "Qualification",
        help_text="Required for accepted-with-qualification; optional otherwise.",
        optional=status != "accepted_with_qualification",
    )
    privacy = select_one(
        "Moderation Record Privacy",
        (
            "teacher_restricted",
            "teacher_and_subjects",
            "group_and_teacher",
            "classroom_shared",
        ),
        (
            "Teacher restricted",
            "Teacher and Subjects",
            "Group and teacher",
            "Classroom shared",
        ),
        help_text="Moderation privacy is independent from the evidence privacy.",
    )
    assert rationale is not None
    return status, permitted_use, rationale, qualification, PrivacyPolicy(
        classification=privacy
    )


def _moderation_label(item: ModerationSummary) -> str:
    evidence = item.evidence_reference
    scope = ", ".join(
        f"{subject.subject_kind}:{subject.subject_id}"
        for subject in item.target_subject_references
    )
    state = "current" if item.is_current else "historical"
    return (
        f"{evidence.owning_system}:{evidence.evidence_kind}:{evidence.record_id} - "
        f"{scope or 'general'} - {item.status} - {item.permitted_use} [{state}]"
    )


def _show_moderation(activity: ActivitySummary) -> None:
    items = list_moderation_records(
        activity.class_id,
        activity.activity_id,
        include_historical=True,
    )
    selected = select_one(
        "Moderation Decisions",
        items,
        [_moderation_label(item) for item in items],
        help_text="Choose one exact Moderation decision to inspect.",
    )
    detail = show_moderation_record(
        activity.class_id,
        activity.activity_id,
        selected.moderation_record_id,
    )
    item = detail.summary
    evidence = item.evidence_reference
    show_result(
        "Moderation Detail",
        (
            f"Moderation: {item.moderation_record_id}",
            (
                "Evidence: "
                f"{evidence.owning_system}:{evidence.evidence_kind}:"
                f"{evidence.record_id}"
            ),
            (
                "Subject scope: "
                + (
                    ", ".join(
                        f"{subject.subject_kind}:{subject.subject_id}"
                        for subject in item.target_subject_references
                    )
                    or "general"
                )
            ),
            f"Status: {item.status}",
            f"Permitted use: {item.permitted_use}",
            f"Qualification: {item.qualification or '-'}",
            f"Rationale: {detail.rationale}",
            f"Privacy: {item.privacy_policy.classification}",
            f"Current: {'yes' if item.is_current else 'no'}",
        ),
    )


def _record_moderation(
    activity: ActivitySummary,
    state: MenuSessionContext,
) -> None:
    current = _latest(activity)
    evidence = _choose_moderation_evidence(current)
    subjects = _choose_moderation_subjects(current)
    moderation_id = prompt_text(
        "Record Moderation",
        "Moderation Record ID",
        help_text="Use an opaque durable Moderation identifier.",
        default=f"moderation_{uuid4().hex}",
    )
    assert moderation_id is not None
    status, permitted_use, rationale, qualification, privacy = _moderation_values()
    if not confirm_write(
        "Record Moderation",
        "MODERATE",
        (
            (
                "Evidence: "
                f"{evidence.owning_system}:{evidence.evidence_kind}:"
                f"{evidence.record_id}"
            ),
            f"Subject scope count: {len(subjects)}",
            f"Status: {status}",
            f"Permitted use: {permitted_use}",
        ),
    ):
        return
    result = add_moderation_record(
        AddModerationRecordRequest(
            class_id=current.class_id,
            activity_id=current.activity_id,
            moderation_record_id=moderation_id,
            target_evidence_reference=evidence,
            target_subject_references=subjects,
            status=status,
            permitted_use=permitted_use,
            rationale=rationale,
            qualification=qualification,
            privacy_policy=privacy,
            expected_snapshot_revision=current.snapshot_revision,
            actor=state.require_actor(),
        )
    )
    show_result(
        "Moderation Recorded",
        (
            f"Moderation: {result.moderation_record_id}",
            f"Snapshot: {result.commit.snapshot_revision}",
        ),
    )


def _replace_moderation(
    activity: ActivitySummary,
    state: MenuSessionContext,
) -> None:
    current = _latest(activity)
    items = list_moderation_records(
        current.class_id,
        current.activity_id,
        include_historical=False,
    )
    predecessor = select_one(
        "Revise Current Moderation",
        items,
        [_moderation_label(item) for item in items],
        help_text=(
            "Revision preserves the predecessor's exact evidence and Subject scope."
        ),
    )
    replacement_id = prompt_text(
        "Revise Moderation",
        "Replacement Moderation ID",
        help_text="Create a new opaque durable successor identifier.",
        default=f"moderation_{uuid4().hex}",
    )
    correction_id = prompt_text(
        "Revise Moderation",
        "Correction ID",
        help_text="Create the audit record connecting predecessor and successor.",
        default=f"correction_{uuid4().hex}",
    )
    reason = prompt_text(
        "Revise Moderation",
        "Reason",
        help_text="State why the Moderation decision is being revised.",
    )
    assert replacement_id is not None
    assert correction_id is not None
    assert reason is not None
    status, permitted_use, rationale, qualification, privacy = _moderation_values()
    if not confirm_write(
        "Revise Moderation",
        "REVISE",
        (
            f"Predecessor: {predecessor.moderation_record_id}",
            f"Successor: {replacement_id}",
            "Evidence and Subject scope: preserved exactly",
            f"New status: {status}",
            f"New permitted use: {permitted_use}",
        ),
    ):
        return
    result = replace_moderation_record(
        ReplaceModerationRecordRequest(
            class_id=current.class_id,
            activity_id=current.activity_id,
            moderation_record_id=predecessor.moderation_record_id,
            replacement_moderation_record_id=replacement_id,
            correction_id=correction_id,
            reason=reason,
            target_evidence_reference=predecessor.evidence_reference,
            target_subject_references=predecessor.target_subject_references,
            status=status,
            permitted_use=permitted_use,
            rationale=rationale,
            qualification=qualification,
            privacy_policy=privacy,
            correction_privacy_policy=PrivacyPolicy(
                classification="teacher_restricted"
            ),
            expected_snapshot_revision=current.snapshot_revision,
            actor=state.require_actor(),
        )
    )
    show_result(
        "Moderation Revised",
        (
            f"Successor: {result.moderation_record_id}",
            f"Correction: {correction_id}",
            f"Snapshot: {result.commit.snapshot_revision}",
        ),
    )


def _view_applicable_moderation(activity: ActivitySummary) -> None:
    evidence = _choose_moderation_evidence(activity)
    subjects = _choose_moderation_subjects(activity)
    items = list_applicable_moderation_records(
        activity.class_id,
        activity.activity_id,
        evidence,
        subject_context=subjects,
    )
    if not items:
        show_result(
            "Applicable Moderation",
            ("No current Moderation decisions apply to this exact evidence/scope.",),
        )
        return
    selected = select_one(
        "Applicable Moderation",
        items,
        [_moderation_label(item) for item in items],
        help_text=(
            "All applicable current decisions are returned; Concord does not "
            "choose one by timestamp or ID."
        ),
    )
    show_result(
        "Applicable Moderation Decision",
        (
            f"Moderation: {selected.moderation_record_id}",
            f"Status: {selected.status}",
            f"Permitted use: {selected.permitted_use}",
            f"Qualification: {selected.qualification or '-'}",
            "Rationale is available only through explicit Moderation detail.",
        ),
    )


def _launch_moderation_menu(
    activity: ActivitySummary,
    state: MenuSessionContext,
) -> None:
    while True:
        clear_screen()
        print_menu_header("Evidence Moderation")
        print("1. List / inspect Moderation decisions")
        print("2. Record Moderation")
        print("3. Record successor / revised Moderation")
        print("4. Find decisions applicable to evidence")
        print_navigation()
        print()
        choice = input("Select an option: ").strip()
        navigation = parse_menu_navigation(choice)
        try:
            if navigation is ConcordMenuChoice.HELP:
                show_result(
                    "Moderation Help",
                    (
                        "Moderation judges reliability, fairness, and permitted use.",
                        (
                            "It does not choose a Criterion, Score target, Score, "
                            "or Grade."
                        ),
                        "Subject scope is explicit and never inferred from Authors.",
                    ),
                )
            elif navigation is NavigationChoice.BACK:
                return
            elif choice == "1":
                _show_moderation(activity)
            elif choice == "2":
                _record_moderation(activity, state)
            elif choice == "3":
                _replace_moderation(activity, state)
            elif choice == "4":
                _view_applicable_moderation(activity)
            else:
                print(navigation_hint_with_help())
                pause_for_user()
        except CancelMenuAction:
            continue
        except (ReturnToMainMenu, QuitPDS, KeyboardInterrupt, EOFError):
            raise
        except Exception as error:
            _handle_error(activity, error, title="Moderation Error")


def launch_collect_work_menu(
    activity: ActivitySummary,
    state: MenuSessionContext,
) -> None:
    """Work with returned evidence without entering Review or scoring."""
    while True:
        clear_screen()
        print_menu_header("Collect")
        print(f"Activity: {activity.title}")
        print()
        print("1. View returned work")
        print("2. Assemble returned work")
        print("3. Confirm who produced the work")
        print("4. Confirm who or what the work is about")
        print_navigation()
        print()
        choice = input("Select an option: ").strip()
        navigation = parse_menu_navigation(choice)
        try:
            if navigation is ConcordMenuChoice.HELP:
                clear_screen()
                print_menu_header("Collect Help")
                print("Use Collect for work that has come back from students.")
                print("Assembly joins returned pages into the intended work.")
                print("Who produced the work and what it concerns stay separate.")
                print("Collect does not Review, Moderate, or Score the work.")
                print()
                pause_for_user()
            elif navigation is NavigationChoice.BACK:
                return
            elif choice == "1":
                _list_artifacts(activity)
            elif choice == "2":
                _assemble(activity, state)
            elif choice == "3":
                _launch_author_menu(activity, state)
            elif choice == "4":
                _launch_subject_menu(activity, state)
            else:
                print(navigation_hint_with_help())
                pause_for_user()
        except CancelMenuAction:
            continue
        except (ReturnToMainMenu, QuitPDS, KeyboardInterrupt, EOFError):
            raise
        except Exception as error:
            _handle_error(activity, error, title="Collect Error")


def launch_review_work_menu(
    activity: ActivitySummary,
    state: MenuSessionContext,
) -> None:
    """Review collected evidence without recording Scores."""
    while True:
        clear_screen()
        print_menu_header("Review")
        print(f"Activity: {activity.title}")
        print()
        print("1. Review collected work")
        print("2. Moderation")
        print_navigation()
        print()
        choice = input("Select an option: ").strip()
        navigation = parse_menu_navigation(choice)
        try:
            if navigation is ConcordMenuChoice.HELP:
                clear_screen()
                print_menu_header("Review Help")
                print("Review records explicit human evidence-readiness judgments.")
                print(
                    "Moderation is a separate reliability and "
                    "permitted-use decision."
                )
                print("Neither Review nor Moderation creates a Score.")
                print()
                pause_for_user()
            elif navigation is NavigationChoice.BACK:
                return
            elif choice == "1":
                _launch_review_menu(activity, state)
            elif choice == "2":
                _launch_moderation_menu(activity, state)
            else:
                print(navigation_hint_with_help())
                pause_for_user()
        except CancelMenuAction:
            continue
        except (ReturnToMainMenu, QuitPDS, KeyboardInterrupt, EOFError):
            raise
        except Exception as error:
            _handle_error(activity, error, title="Review Error")


def launch_artifact_page_menu(
    activity: ActivitySummary, state: MenuSessionContext
) -> None:
    while True:
        clear_screen()
        print_menu_header("Artifact Pages")
        print(f"Activity: {activity.title}")
        print()
        print("1. Prepare Artifact Pages")
        print("2. List / inspect Artifact Pages")
        print("3. Render prepared pages")
        print("4. List / inspect Artifacts")
        print("5. Assemble returned Artifact")
        print("6. Authors")
        print("7. Subjects")
        print("8. Review")
        print("9. Moderation")
        print_navigation()
        print()
        choice = input("Select an option: ").strip()
        navigation = parse_menu_navigation(choice)
        try:
            if navigation is ConcordMenuChoice.HELP:
                show_result(
                    "Artifact Help",
                    (
                        "Pages carry routes; Artifacts collect physical page evidence.",
                        (
                            "Authors and Subjects remain explicit independent "
                            "relationships."
                        ),
                    ),
                )
            elif navigation is NavigationChoice.BACK:
                return
            elif choice == "1":
                _prepare(activity, state)
                return
            elif choice == "2":
                _list_pages(activity)
            elif choice == "3":
                _render(activity, state)
                return
            elif choice == "4":
                _list_artifacts(activity)
            elif choice == "5":
                _assemble(activity, state)
                return
            elif choice == "6":
                _launch_author_menu(activity, state)
            elif choice == "7":
                _launch_subject_menu(activity, state)
            elif choice == "8":
                _launch_review_menu(activity, state)
            elif choice == "9":
                _launch_moderation_menu(activity, state)
            else:
                print(navigation_hint_with_help())
                pause_for_user()
        except CancelMenuAction:
            return
        except (ReturnToMainMenu, QuitPDS, KeyboardInterrupt, EOFError):
            raise
        except Exception as error:
            _handle_error(activity, error)
            return


__all__ = [
    "launch_artifact_page_menu",
    "launch_collect_work_menu",
    "launch_review_work_menu",
]
