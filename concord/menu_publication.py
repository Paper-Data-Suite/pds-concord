"""Teacher-facing Academic Publication workflow for one Concord Activity."""

from __future__ import annotations

from pathlib import Path

from pds_core.academic_work_registrations import (
    AcademicWorkIntent,
    AcademicWorkRegistrationLifecycle,
)
from pds_core.registry_services import (
    AcademicWorkRegistrationRequest,
    RegistryServiceConflictError,
    RegistryServicePartialSuccessError,
    update_academic_work_registration,
)

from concord.academic_result_manifest import RevisionReason
from concord.academic_result_manifest_generation import (
    AcademicResultManifestPreview,
    ConcordManifestGenerationConflictError,
    ConcordManifestGenerationPartialSuccessError,
    GenerateAcademicResultManifestRequest,
    generate_academic_result_manifest,
    manifest_generation_summary,
    manifest_preview_summary,
    preview_academic_result_manifest,
)
from concord.academic_result_publication import (
    ConcordAcademicResultPublicationConflictError,
    ConcordAcademicResultPublicationPartialSuccessError,
    load_concord_publication_series_status,
    publish_concord_academic_results,
    query_concord_publication_catalog,
    rebuild_full_academic_catalog,
    republish_concord_academic_results_after_withdrawal,
    supersede_concord_academic_results,
    withdraw_concord_academic_result_publication,
)
from concord.academic_work_registration import (
    load_current_concord_academic_work_registration,
    register_concord_academic_work,
)
from concord.menu_context import CancelMenuAction, MenuSessionContext
from concord.menu_navigation import (
    ConcordMenuChoice,
    NavigationChoice,
    navigation_hint_with_help,
    parse_menu_navigation,
)
from concord.menu_prompts import (
    confirm_write,
    load_menu_standards_library,
    prompt_conflict_reload,
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
from concord.workflows import ActivitySummary, show_activity
from concord.workflows.context import resolve_read_workspace_root

_ACADEMIC_INTENTS: tuple[AcademicWorkIntent, ...] = (
    "formative",
    "summative",
    "diagnostic",
    "practice",
    "feedback_only",
    "reporting_only",
)
_REGISTRATION_LIFECYCLES: tuple[
    AcademicWorkRegistrationLifecycle, ...
] = ("planned", "active", "closed", "cancelled")
_REVISION_REASONS: tuple[RevisionReason, ...] = (
    "native_state_change",
    "evidence_lineage_change",
    "moderation_change",
    "projection_correction",
    "privacy_correction",
    "contract_migration",
)


def _root() -> Path:
    resolved = resolve_read_workspace_root()
    if resolved is None:
        raise FileNotFoundError("Paper Data Suite workspace does not exist.")
    return Path(resolved)


def _registration_status(activity: ActivitySummary) -> None:
    registration = load_current_concord_academic_work_registration(
        _root(), activity.class_id, activity.activity_id
    )
    lines = [f"Activity: {activity.title}", f"Work: {activity.activity_id}"]
    if registration is None:
        lines.append("Registration: none")
    else:
        lines.extend(
            (
                f"Registration revision: {registration.registration_revision}",
                f"Academic intent: {registration.academic_intent}",
                f"Lifecycle: {registration.lifecycle}",
                f"Registered title: {registration.title}",
            )
        )
    show_result("Registration Status", tuple(lines))


def _choose_registration_values() -> tuple[
    AcademicWorkIntent, AcademicWorkRegistrationLifecycle
]:
    intent = select_one(
        "Academic Intent",
        _ACADEMIC_INTENTS,
        tuple(item.replace("_", " ").title() for item in _ACADEMIC_INTENTS),
        help_text="Choose the explicit Core academic intent for this Activity.",
    )
    lifecycle = select_one(
        "Registration Lifecycle",
        _REGISTRATION_LIFECYCLES,
        tuple(item.title() for item in _REGISTRATION_LIFECYCLES),
        help_text="Choose the explicit Core lifecycle for this registration.",
    )
    return intent, lifecycle


def _register(activity: ActivitySummary) -> None:
    intent, lifecycle = _choose_registration_values()
    if not confirm_write(
        "Register Activity",
        "REGISTER",
        (
            f"Activity: {activity.title}",
            f"Work: {activity.class_id}/{activity.activity_id}",
            f"Academic intent: {intent}",
            f"Lifecycle: {lifecycle}",
        ),
    ):
        return
    result = register_concord_academic_work(
        _root(),
        activity.class_id,
        activity.activity_id,
        academic_intent=intent,
        lifecycle=lifecycle,
    )
    show_result(
        "Registration Result",
        (
            f"Disposition: {result.disposition}",
            f"Registration revision: {result.registration.registration_revision}",
        ),
    )


def _update_registration(activity: ActivitySummary) -> None:
    root = _root()
    current = load_current_concord_academic_work_registration(
        root, activity.class_id, activity.activity_id
    )
    if current is None:
        show_result("Registration Update", ("Register the Activity first.",))
        return
    intent, lifecycle = _choose_registration_values()
    detail = show_activity(
        activity.class_id, activity.activity_id, workspace_root=root
    )
    if not confirm_write(
        "Update Registration",
        "REGISTER",
        (
            f"Activity: {detail.summary.title}",
            f"Current registration revision: {current.registration_revision}",
            f"Academic intent: {intent}",
            f"Lifecycle: {lifecycle}",
        ),
    ):
        return
    request = AcademicWorkRegistrationRequest(
        work=current.work,
        producer_contract_version=current.producer_contract_version,
        title=detail.summary.title,
        work_kind=current.work_kind,
        academic_intent=intent,
        lifecycle=lifecycle,
        source_records=current.source_records,
    )
    result = update_academic_work_registration(
        root,
        request,
        expected_current_revision=current.registration_revision,
    )
    show_result(
        "Registration Result",
        (
            f"Disposition: {result.disposition}",
            f"Registration revision: {result.registration.registration_revision}",
        ),
    )


def _revision_reason(activity: ActivitySummary) -> RevisionReason:
    state = load_concord_publication_series_status(
        activity.class_id, activity.activity_id, workspace_root=_root()
    )
    if not state.producer_revisions:
        return "initial"
    return select_one(
        "Manifest Revision Reason",
        _REVISION_REASONS,
        tuple(item.replace("_", " ").title() for item in _REVISION_REASONS),
        help_text=(
            "Choose the controlled non-sensitive reason for this public projection."
        ),
    )


def _manifest_request(
    activity: ActivitySummary,
    session: MenuSessionContext,
) -> GenerateAcademicResultManifestRequest:
    return GenerateAcademicResultManifestRequest(
        class_id=activity.class_id,
        activity_id=activity.activity_id,
        expected_snapshot_revision=activity.snapshot_revision,
        actor=session.require_actor(),
        revision_reason=_revision_reason(activity),
    )


def _preview(
    activity: ActivitySummary,
    session: MenuSessionContext,
) -> tuple[GenerateAcademicResultManifestRequest, AcademicResultManifestPreview]:
    request = _manifest_request(activity, session)
    preview = preview_academic_result_manifest(
        request,
        workspace_root=_root(),
        standards_library=load_menu_standards_library(),
    )
    return request, preview


def _review_lines(
    preview: AcademicResultManifestPreview,
    *,
    academic_intent: str,
    lifecycle: str,
) -> tuple[str, ...]:
    summary = manifest_preview_summary(preview)
    work = preview.manifest.work
    capabilities = ", ".join(summary["capabilities"])  # type: ignore[arg-type]
    return (
        f"Activity/work: {work.class_id}/{work.work_id}",
        f"Registration revision: {summary['registration_revision']}",
        f"Academic intent: {academic_intent}",
        f"Registration lifecycle: {lifecycle}",
        f"Concord source snapshot revision: {summary['source_snapshot_revision']}",
        f"Record set: {summary['record_set_id']} @ {summary['record_set_revision']}",
        f"Manifest contract: {summary['manifest_contract_version']}",
        f"Scores: {summary['score_count']}",
        (
            "Current / historical Scores: "
            f"{summary['current_score_count']} / {summary['historical_score_count']}"
        ),
        (
            "Standard-backed / local Scores: "
            f"{summary['standard_backed_score_count']} / "
            f"{summary['local_score_count']}"
        ),
        f"Non-score records: {summary['non_score_count']}",
        f"Moderation-dependent Scores: {summary['moderation_dependent_count']}",
        f"Derived capabilities: {capabilities or '-'}",
        f"Manifest path: {summary['manifest_path']}",
        f"Manifest SHA-256: {summary['manifest_sha256']}",
        f"Generation disposition: {summary['disposition']}",
    )


def _show_preview(activity: ActivitySummary, session: MenuSessionContext) -> None:
    _request_value, preview = _preview(activity, session)
    registration = load_current_concord_academic_work_registration(
        _root(), activity.class_id, activity.activity_id
    )
    assert registration is not None
    show_result(
        "Publication Readiness / Preview",
        _review_lines(
            preview,
            academic_intent=registration.academic_intent,
            lifecycle=registration.lifecycle,
        ),
    )


def _generate(activity: ActivitySummary, session: MenuSessionContext) -> None:
    request, preview = _preview(activity, session)
    registration = load_current_concord_academic_work_registration(
        _root(), activity.class_id, activity.activity_id
    )
    assert registration is not None
    review = _review_lines(
        preview,
        academic_intent=registration.academic_intent,
        lifecycle=registration.lifecycle,
    )
    if not confirm_write("Generate Immutable Manifest", "GENERATE", review):
        return
    result = generate_academic_result_manifest(
        request,
        workspace_root=_root(),
        standards_library=load_menu_standards_library(),
        clock=lambda: preview.manifest.generated_at,
    )
    summary = manifest_generation_summary(result)
    show_result(
        "Manifest Result",
        (
            f"Disposition: {summary['disposition']}",
            f"Record-set revision: {summary['record_set_revision']}",
            f"Manifest path: {summary['manifest_path']}",
            f"Manifest SHA-256: {summary['manifest_sha256']}",
        ),
    )


def _publication_status(activity: ActivitySummary) -> None:
    state = load_concord_publication_series_status(
        activity.class_id, activity.activity_id, workspace_root=_root()
    )
    lines = [
        (
            "Producer manifest head: "
            + (str(state.producer_head.revision) if state.producer_head else "none")
        ),
        (
            "Core structural head: "
            + (state.core_head.publication_id if state.core_head else "none")
        ),
        f"Core head withdrawn: {'yes' if state.core_head_withdrawal else 'no'}",
        (
            "Current selectable publication: "
            + (
                state.current_selectable_publication.publication_id
                if state.current_selectable_publication
                else "none"
            )
        ),
        (
            "Current registration revision: "
            + (
                str(state.current_registration_revision)
                if state.current_registration_revision is not None
                else "none"
            )
        ),
        f"Catalog available: {'yes' if state.catalog_available else 'no'}",
        f"Catalog rows: {len(state.catalog_rows)}",
    ]
    for publication in state.publications:
        withdrawn = any(
            item.publication_id == publication.publication_id
            for item in state.withdrawals
        )
        lines.append(
            f"Revision {publication.record_set_revision}: "
            f"{publication.publication_id} "
            f"({'withdrawn' if withdrawn else 'active history'})"
        )
    show_result("Publication History / Status", tuple(lines))


def _publish(
    activity: ActivitySummary,
    session: MenuSessionContext,
    *,
    superseding: bool,
    teacher_facing: bool = False,
) -> None:
    state = load_concord_publication_series_status(
        activity.class_id, activity.activity_id, workspace_root=_root()
    )
    if superseding and state.core_head is None:
        show_result("Publish", ("There is no Core publication to supersede.",))
        return
    if not superseding and state.core_head is not None:
        show_result(
            "Publish",
            ("A Core publication series already exists; use superseding publication.",),
        )
        return
    request, preview = _preview(activity, session)
    registration = load_current_concord_academic_work_registration(
        _root(), activity.class_id, activity.activity_id
    )
    assert registration is not None
    if teacher_facing:
        review = list(
            _share_review_lines(
                activity,
                preview,
                academic_intent=registration.academic_intent,
                lifecycle=registration.lifecycle,
            )
        )
    else:
        review = list(
            _review_lines(
                preview,
                academic_intent=registration.academic_intent,
                lifecycle=registration.lifecycle,
            )
        )
        if state.core_head is not None:
            review.append(f"Expected Core head: {state.core_head.publication_id}")
            withdrawn_label = "yes" if state.core_head_withdrawal else "no"
            review.append(f"Expected Core head withdrawn: {withdrawn_label}")
    confirmation_title = (
        "Share Results" if teacher_facing else "Publish Academic Results"
    )
    confirmation_word = "SHARE" if teacher_facing else "PUBLISH"
    if not confirm_write(
        confirmation_title,
        confirmation_word,
        tuple(review),
    ):
        return
    if not superseding:
        result = publish_concord_academic_results(
            request,
            workspace_root=_root(),
            standards_library=load_menu_standards_library(),
            clock=lambda: preview.manifest.generated_at,
        )
    else:
        assert state.core_head is not None
        if state.core_head_withdrawal is not None:
            result = republish_concord_academic_results_after_withdrawal(
                request,
                expected_withdrawn_head_publication_id=state.core_head.publication_id,
                workspace_root=_root(),
                standards_library=load_menu_standards_library(),
                clock=lambda: preview.manifest.generated_at,
            )
        else:
            result = supersede_concord_academic_results(
                request,
                expected_current_publication_id=state.core_head.publication_id,
                workspace_root=_root(),
                standards_library=load_menu_standards_library(),
                clock=lambda: preview.manifest.generated_at,
            )
    if teacher_facing:
        show_result(
            "Results Shared",
            (
                "The Activity results are now shared through Paper Data Suite.",
                f"Shared revision: {result.publication.record_set_revision}",
            ),
        )
    else:
        show_result(
            "Publication Result",
            (
                f"Disposition: {result.disposition}",
                f"Publication: {result.publication.publication_id}",
                f"Record-set revision: {result.publication.record_set_revision}",
            ),
        )


def _withdraw(
    activity: ActivitySummary,
    *,
    teacher_facing: bool = False,
) -> None:
    state = load_concord_publication_series_status(
        activity.class_id, activity.activity_id, workspace_root=_root()
    )
    publication_id: str
    if teacher_facing:
        current = state.current_selectable_publication
        if current is None:
            show_result(
                "Stop Sharing",
                ("There are no currently shared results to stop sharing.",),
            )
            return
        current_publication_id = current.publication_id
        if current_publication_id is None:
            raise ValueError(
                "Current shared results have no publication identifier."
            )
        publication_id = current_publication_id
        reason = prompt_text(
            "Stop Sharing",
            "Reason",
            help_text=(
                "Use a short operational reason. Do not include student "
                "or moderation narrative."
            ),
        )
        assert reason is not None
        if not confirm_write(
            "Stop Sharing",
            "STOP",
            (
                f"Activity: {activity.title}",
                f"Current shared revision: {current.record_set_revision}",
                f"Reason: {reason}",
            ),
        ):
            return
    else:
        if not state.publications:
            show_result("Withdraw Publication", ("No Core publications exist.",))
            return
        publication_id_value = prompt_text(
            "Withdraw Publication",
            "Publication ID",
            help_text="Enter the exact Core Publication Record ID to withdraw.",
            default=(state.core_head.publication_id if state.core_head else None),
        )
        assert publication_id_value is not None
        publication_id = publication_id_value
        reason = prompt_text(
            "Withdraw Publication",
            "Publication-safe reason",
            help_text=(
                "Use deliberate operational text only; do not paste student or "
                "moderation narrative."
            ),
        )
        assert reason is not None
        if not confirm_write(
            "Withdraw Publication",
            "WITHDRAW",
            (
                f"Activity: {activity.title}",
                f"Publication: {publication_id}",
                f"Reason: {reason}",
            ),
        ):
            return
    result = withdraw_concord_academic_result_publication(
        activity.class_id,
        activity.activity_id,
        publication_id=publication_id,
        reason=reason,
        workspace_root=_root(),
    )
    if teacher_facing:
        show_result(
            "Sharing Stopped",
            ("The current shared results are no longer selectable.",),
        )
    else:
        show_result(
            "Withdrawal Result",
            (
                f"Disposition: {result.disposition}",
                f"Publication: {result.publication.publication_id}",
                f"Manifest verification: {result.manifest_verification}",
            ),
        )


def _catalog_status(activity: ActivitySummary) -> None:
    state = load_concord_publication_series_status(
        activity.class_id, activity.activity_id, workspace_root=_root()
    )
    lines = [
        f"Catalog available: {'yes' if state.catalog_available else 'no'}",
        f"Catalog rows for Activity: {len(state.catalog_rows)}",
    ]
    if state.catalog_available:
        rows = query_concord_publication_catalog(
            activity.class_id,
            activity.activity_id,
            state="all",
            workspace_root=_root(),
        )
        for row in rows:
            lines.append(
                f"Revision {row.record_set_revision}: {row.publication_id}; "
                f"head={'yes' if row.is_series_head else 'no'}; "
                f"withdrawn={'yes' if row.is_withdrawn else 'no'}; "
                f"current={'yes' if row.is_current_selectable else 'no'}"
            )
    show_result("Catalog Discovery / Status", tuple(lines))


def _rebuild_catalog(activity: ActivitySummary) -> None:
    if not confirm_write(
        "Rebuild Core Academic Catalog",
        "REBUILD",
        (
            "Core academic catalog is disposable derived state.",
            f"Activity context: {activity.class_id}/{activity.activity_id}",
            "Canonical registrations/publications/withdrawals are not rewritten.",
        ),
    ):
        return
    result = rebuild_full_academic_catalog(_root())
    show_result(
        "Catalog Result",
        (
            "Catalog rebuilt and verified.",
            f"Publications: {result.metadata.publication_count}",
            f"Withdrawals: {result.metadata.withdrawal_count}",
            f"Source snapshot SHA-256: {result.metadata.source_snapshot_sha256}",
        ),
    )


def _handle_error(error: Exception) -> None:
    if isinstance(
        error,
        (
            ConcordManifestGenerationConflictError,
            ConcordAcademicResultPublicationConflictError,
            RegistryServiceConflictError,
        ),
    ) or error.__class__.__name__.endswith("ConflictError"):
        prompt_conflict_reload()
        return
    if isinstance(error, ConcordManifestGenerationPartialSuccessError):
        show_result(
            "Partial Success",
            (
                str(error),
                f"Durable manifest revision: {error.state.revision}",
                "Review canonical producer state before retrying.",
            ),
        )
        return
    if isinstance(error, ConcordAcademicResultPublicationPartialSuccessError):
        state = error.state
        show_result(
            "Partial Success",
            (
                str(error),
                f"Canonical state: {state.canonical_state}",
                state.recommended_next_action,
            ),
        )
        return
    if isinstance(error, RegistryServicePartialSuccessError):
        show_result(
            "Partial Success",
            (str(error), "Review canonical Core registry state before retrying."),
        )
        return
    show_result("Publication Error", (str(error),))


def _publication_help() -> None:
    show_result(
        "Publication Help",
        (
            "Publication is explicit teacher intent and never occurs on menu entry.",
            "Concord publishes immutable academic-result manifests through Core.",
            "Publication does not calculate Grades, proficiency, or reporting policy.",
        ),
    )


def _sharing_setup_status(activity: ActivitySummary) -> None:
    registration = load_current_concord_academic_work_registration(
        _root(), activity.class_id, activity.activity_id
    )
    lines = [f"Activity: {activity.title}"]
    if registration is None:
        lines.append("Sharing setup: not configured")
    else:
        lines.extend(
            (
                "Sharing setup: configured",
                (
                    "Academic intent: "
                    + registration.academic_intent.replace("_", " ").title()
                ),
                f"Activity status: {registration.lifecycle.title()}",
            )
        )
    show_result("Sharing Setup", tuple(lines))


def _launch_sharing_setup_menu(activity: ActivitySummary) -> None:
    while True:
        clear_screen()
        print_menu_header("Set Up Sharing")
        print(f"Activity: {activity.title}")
        print()
        print("1. View sharing setup")
        print("2. Set up this Activity for sharing")
        print("3. Update sharing setup")
        print_navigation()
        print()
        choice = input("Select an option: ").strip()
        navigation = parse_menu_navigation(choice)
        if navigation is ConcordMenuChoice.HELP:
            show_result(
                "Sharing Setup Help",
                (
                    "Set the Activity's academic intent and lifecycle.",
                    "This does not share results by itself.",
                ),
            )
        elif navigation is NavigationChoice.BACK:
            return
        elif choice == "1":
            _sharing_setup_status(activity)
        elif choice == "2":
            _register(activity)
        elif choice == "3":
            _update_registration(activity)
        else:
            print(navigation_hint_with_help())
            pause_for_user()


def _share_review_lines(
    activity: ActivitySummary,
    preview: AcademicResultManifestPreview,
    *,
    academic_intent: str,
    lifecycle: str,
) -> tuple[str, ...]:
    summary = manifest_preview_summary(preview)
    return (
        f"Activity: {activity.title}",
        f"Academic intent: {academic_intent.replace('_', ' ').title()}",
        f"Activity status: {lifecycle.title()}",
        f"Scores included: {summary['score_count']}",
        (
            "Current / historical Scores: "
            f"{summary['current_score_count']} / {summary['historical_score_count']}"
        ),
        (
            "Standards-backed / Activity-specific Scores: "
            f"{summary['standard_backed_score_count']} / "
            f"{summary['local_score_count']}"
        ),
        f"Non-score records included: {summary['non_score_count']}",
        (
            "Scores requiring moderation: "
            f"{summary['moderation_dependent_count']}"
        ),
    )


def _show_share_preview(
    activity: ActivitySummary,
    session: MenuSessionContext,
) -> None:
    _request_value, preview = _preview(activity, session)
    registration = load_current_concord_academic_work_registration(
        _root(), activity.class_id, activity.activity_id
    )
    assert registration is not None
    show_result(
        "Review What Will Be Shared",
        _share_review_lines(
            activity,
            preview,
            academic_intent=registration.academic_intent,
            lifecycle=registration.lifecycle,
        ),
    )


def _share_results(
    activity: ActivitySummary,
    session: MenuSessionContext,
) -> None:
    state = load_concord_publication_series_status(
        activity.class_id,
        activity.activity_id,
        workspace_root=_root(),
    )
    _publish(
        activity,
        session,
        superseding=state.core_head is not None,
        teacher_facing=True,
    )


def _share_history(activity: ActivitySummary) -> None:
    state = load_concord_publication_series_status(
        activity.class_id,
        activity.activity_id,
        workspace_root=_root(),
    )
    lines = [f"Shared revisions: {len(state.publications)}"]
    if state.current_selectable_publication is None:
        lines.append("Currently shared: no")
    else:
        lines.extend(
            (
                "Currently shared: yes",
                (
                    "Current shared revision: "
                    f"{state.current_selectable_publication.record_set_revision}"
                ),
            )
        )
    for publication in state.publications:
        withdrawn = any(
            item.publication_id == publication.publication_id
            for item in state.withdrawals
        )
        current = (
            state.current_selectable_publication is not None
            and state.current_selectable_publication.publication_id
            == publication.publication_id
        )
        if current:
            status = "current"
        elif withdrawn:
            status = "withdrawn"
        else:
            status = "earlier"
        lines.append(f"Revision {publication.record_set_revision}: {status}")
    show_result("Sharing History", tuple(lines))


def launch_share_results_menu(
    activity: ActivitySummary,
    state: MenuSessionContext,
) -> None:
    """Open the focused teacher-facing result-sharing surface."""
    while True:
        clear_screen()
        print_menu_header("Share")
        print(f"Activity: {activity.title}")
        print()
        print("1. Set up sharing")
        print("2. Review what will be shared")
        print("3. Share results")
        print("4. View sharing history")
        print("5. Stop sharing current results")
        print_navigation()
        print()
        choice = input("Select an option: ").strip()
        navigation = parse_menu_navigation(choice)
        if navigation is ConcordMenuChoice.HELP:
            show_result(
                "Share Help",
                (
                    "Share deliberate Activity results through Paper Data Suite.",
                    "Review the result set before sharing it.",
                    "Sharing does not calculate Grades or reporting policy.",
                ),
            )
            continue
        if navigation is NavigationChoice.BACK:
            return
        try:
            activity = show_activity(
                activity.class_id,
                activity.activity_id,
                workspace_root=_root(),
            ).summary
            if choice == "1":
                _launch_sharing_setup_menu(activity)
            elif choice == "2":
                _show_share_preview(activity, state)
            elif choice == "3":
                _share_results(activity, state)
            elif choice == "4":
                _share_history(activity)
            elif choice == "5":
                _withdraw(activity, teacher_facing=True)
            else:
                print(navigation_hint_with_help())
                pause_for_user()
        except CancelMenuAction:
            continue
        except Exception as error:
            _handle_error(error)


def launch_publication_menu(
    activity: ActivitySummary,
    state: MenuSessionContext,
) -> None:
    """Open the deliberate Activity-scoped Academic Publication surface."""
    while True:
        clear_screen()
        print_menu_header("Academic Publication")
        print(f"Activity: {activity.title}")
        print(f"Class: {activity.class_id}")
        print()
        print("1. Registration status")
        print("2. Register Activity")
        print("3. Update registration")
        print("4. Publication readiness / preview")
        print("5. Generate immutable manifest")
        print("6. Publication history / status")
        print("7. Publish first revision")
        print("8. Publish superseding revision")
        print("9. Withdraw exact publication")
        print("10. Catalog discovery / status")
        print("11. Rebuild catalog")
        print_navigation()
        print()
        choice = input("Select an option: ").strip()
        navigation = parse_menu_navigation(choice)
        if navigation is ConcordMenuChoice.HELP:
            _publication_help()
            continue
        if navigation is NavigationChoice.BACK:
            return
        try:
            activity = show_activity(
                activity.class_id,
                activity.activity_id,
                workspace_root=_root(),
            ).summary
            if choice == "1":
                _registration_status(activity)
            elif choice == "2":
                _register(activity)
            elif choice == "3":
                _update_registration(activity)
            elif choice == "4":
                _show_preview(activity, state)
            elif choice == "5":
                _generate(activity, state)
            elif choice == "6":
                _publication_status(activity)
            elif choice == "7":
                _publish(activity, state, superseding=False)
            elif choice == "8":
                _publish(activity, state, superseding=True)
            elif choice == "9":
                _withdraw(activity)
            elif choice == "10":
                _catalog_status(activity)
            elif choice == "11":
                _rebuild_catalog(activity)
            else:
                print(navigation_hint_with_help())
                pause_for_user()
        except CancelMenuAction:
            continue
        except Exception as error:
            _handle_error(error)
