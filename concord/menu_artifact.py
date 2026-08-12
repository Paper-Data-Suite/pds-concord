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
from concord.workflows.context import actor_reference


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


__all__ = ["launch_artifact_page_menu"]
