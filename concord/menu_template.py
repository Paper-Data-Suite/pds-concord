"""Workspace-level teacher menu for reusable Concord Templates."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from concord.menu_context import CancelMenuAction, MenuSessionContext
from concord.menu_navigation import (
    ConcordMenuChoice,
    NavigationChoice,
    navigation_hint_with_help,
    parse_menu_navigation,
)
from concord.menu_prompts import confirm_write, prompt_text, select_one, show_result
from concord.menu_ui import (
    clear_screen,
    pause_for_user,
    print_menu_header,
    print_navigation,
)
from concord.starter_templates.catalog import get_starter_template
from concord.template_storage import TemplateStoragePartialSuccessError
from concord.workflows.errors import ConcordWorkflowError
from concord.workflows.starter_template import (
    STARTER_INSTALLATION_ALREADY_INSTALLED,
    PrepareStarterTemplateInstallAllRequest,
    PrepareStarterTemplateInstallRequest,
    StarterTemplateInstallAllPartialSuccessError,
    StarterTemplateInstallAllResult,
    StarterTemplateInstallResult,
    StarterTemplateStatus,
    commit_starter_template_install,
    commit_starter_template_install_all,
    list_starter_template_statuses,
    prepare_starter_template_install,
    prepare_starter_template_install_all,
)
from concord.workflows.template import (
    PrepareTemplateActivationRequest,
    PrepareTemplateCreateRequest,
    PrepareTemplateRetireRequest,
    PrepareTemplateRetireVersionRequest,
    PrepareTemplateRevisionRequest,
    PrepareTemplateUpdateRequest,
    TemplateDetail,
    TemplateMutationResult,
    TemplateSummary,
    commit_template_activation,
    commit_template_create,
    commit_template_retire,
    commit_template_retire_version,
    commit_template_revision,
    commit_template_update,
    get_template,
    list_templates,
    prepare_template_activation,
    prepare_template_create,
    prepare_template_retire,
    prepare_template_retire_version,
    prepare_template_revision,
    prepare_template_update,
)


def _help() -> None:
    clear_screen()
    print_menu_header("Template Library Help")
    print("Templates are reusable across Activities and classes.")
    print("Template Versions are immutable printable revisions.")
    print("Creating or revising a Template does not create Artifacts or PDS2 routes.")
    print("Activation selects the exact Version for ordinary future use.")
    print("Retirement preserves historical Versions and rendering specifications.")
    print()
    pause_for_user()


def _summary_label(item: TemplateSummary) -> str:
    return (
        f"{item.name} ({item.template_id}) - {item.status}; "
        f"current={item.current_template_version_id or '-'}; "
        f"head={item.head_template_version_id}"
    )


def _choose_template(*, title: str) -> TemplateSummary:
    items = list_templates()
    if not items:
        raise ConcordWorkflowError("No reusable Concord Templates are available.")
    return select_one(
        title,
        items,
        tuple(_summary_label(item) for item in items),
        help_text="Choose the reusable Template for this workspace-level action.",
    )


def _detail_lines(detail: TemplateDetail) -> tuple[str, ...]:
    definition = detail.definition
    summary = detail.summary
    lines = [
        f"Template: {summary.template_id}",
        f"Name: {summary.name}",
        f"Purpose: {definition.purpose}",
        f"Status: {summary.status}",
        f"Artifact category: {summary.artifact_category}",
        f"Current Version: {summary.current_template_version_id or '-'}",
        f"Head Version: {summary.head_template_version_id}",
        f"Snapshot: {summary.snapshot_revision}",
        f"Versions: {len(detail.versions)}",
    ]
    if definition.description is not None:
        lines.append(f"Description: {definition.description}")
    return tuple(lines)


def _version_preview_lines(
    detail: TemplateDetail,
    version_id: str,
) -> tuple[str, ...]:
    version = next(
        (
            item
            for item in detail.versions
            if item.template_version_id == version_id
        ),
        None,
    )
    if version is None:
        raise ConcordWorkflowError(
            f"Template Version is not available: {version_id}"
        )
    return (
        f"Template: {detail.summary.template_id}",
        f"Name: {detail.summary.name}",
        f"Version: {version.template_version_id}",
        f"Version label: {version.version_label}",
        f"Revision sequence: {version.revision_sequence}",
        f"Status: {version.status}",
        f"Artifact category: {version.artifact_category}",
        f"Pages: {len(version.page_manifest)}",
        f"Expected return: {version.default_expected_return_status}",
        f"Privacy: {version.default_privacy_policy.classification}",
        f"Rendering contract: {version.rendering_contract_version}",
        f"Rendering reference: {version.rendering_specification_reference}",
        f"Rendering SHA-256: {version.rendering_specification_sha256}",
        f"Expected Template snapshot: {detail.summary.snapshot_revision}",
    )


def _mutation_lines(result: TemplateMutationResult) -> tuple[str, ...]:
    lines = [
        f"Template: {result.template_id}",
        f"Status: {result.status}",
        f"Snapshot: {result.snapshot_revision}",
        f"Current Version: {result.current_template_version_id or '-'}",
        f"Head Version: {result.head_template_version_id}",
    ]
    if result.workspace_created:
        lines.insert(0, "Created the Paper Data Suite workspace.")
    return tuple(lines)


def _show_partial_success(error: TemplateStoragePartialSuccessError) -> None:
    lines = [
        (
            "The Template current pointer was published, but follow-up "
            "verification or cleanup was incomplete."
            if error.pointer_published
            else "The Template current pointer was not published."
        )
    ]
    if error.snapshot_revision is not None:
        lines.append(f"Snapshot: {error.snapshot_revision}")
    if error.snapshot_sha256 is not None:
        lines.append(f"Snapshot SHA-256: {error.snapshot_sha256}")
    lines.append("Review canonical Template storage before retrying.")
    show_result("Template Partial Success", tuple(lines))


def _show_selected() -> None:
    selected = _choose_template(title="Choose a Template")
    detail = get_template(selected.template_id)
    show_result("Template Summary", _detail_lines(detail))


def _show_history() -> None:
    selected = _choose_template(title="Choose a Template")
    detail = get_template(selected.template_id)
    lines = list(_detail_lines(detail))
    lines.append("")
    lines.append("Version history:")
    for version in detail.versions:
        markers: list[str] = []
        if (
            version.template_version_id
            == detail.summary.current_template_version_id
        ):
            markers.append("current")
        if version.template_version_id == detail.summary.head_template_version_id:
            markers.append("head")
        marker = f" ({', '.join(markers)})" if markers else ""
        lines.append(
            f"{version.revision_sequence}. "
            f"{version.template_version_id} - "
            f"{version.version_label} [{version.status}]{marker}"
        )
    show_result("Template Version History", tuple(lines))


def _choose_activation() -> bool:
    return select_one(
        "Initial Template Status",
        (False, True),
        (
            "Draft - create without selecting a current Version",
            "Active - create and select the initial Version",
        ),
        help_text="Activation is explicit and can also be performed later.",
    )


def _create(state: MenuSessionContext) -> None:
    template_id = prompt_text(
        "Create Template",
        "Template ID",
        help_text="Enter the durable reusable Template identifier.",
    )
    assert template_id is not None
    version_id = prompt_text(
        "Create Template",
        "Initial Template Version ID",
        help_text="Enter a fresh immutable Template Version identifier.",
    )
    assert version_id is not None
    authoring = prompt_text(
        "Create Template",
        "Authoring JSON file",
        help_text="Enter the strict concord_template_authoring_v1 JSON file.",
    )
    assert authoring is not None
    rendering = prompt_text(
        "Create Template",
        "Rendering specification file",
        help_text="Enter the exact primary rendering specification file.",
    )
    assert rendering is not None
    activate = _choose_activation()
    prepared = prepare_template_create(
        PrepareTemplateCreateRequest(
            template_id=template_id,
            template_version_id=version_id,
            authoring_file=Path(authoring).expanduser(),
            rendering_specification=Path(rendering).expanduser(),
            actor=state.require_actor(),
            activate=activate,
        )
    )
    lines = (
        f"Template: {prepared.definition.template_id}",
        f"Name: {prepared.definition.name}",
        f"Version: {prepared.version.template_version_id}",
        f"Version label: {prepared.version.version_label}",
        f"Artifact category: {prepared.version.artifact_category}",
        f"Pages: {len(prepared.version.page_manifest)}",
        f"Expected return: {prepared.version.default_expected_return_status}",
        f"Privacy: {prepared.version.default_privacy_policy.classification}",
        f"Rendering contract: {prepared.version.rendering_contract_version}",
        (
            "Rendering reference: "
            f"{prepared.version.rendering_specification_reference}"
        ),
        f"Rendering SHA-256: {prepared.rendering_source.sha256}",
        f"Initial status: {prepared.version.status}",
    )
    if not confirm_write("Create Template", "CREATE", lines):
        return
    result = commit_template_create(prepared)
    show_result("Template Result", _mutation_lines(result))


def _revise(state: MenuSessionContext) -> None:
    selected = _choose_template(title="Choose Template to Revise")
    detail = get_template(selected.template_id)
    version_id = prompt_text(
        "Create Successor Template Version",
        "New Template Version ID",
        help_text="Enter a fresh immutable Version identifier.",
    )
    assert version_id is not None
    authoring = prompt_text(
        "Create Successor Template Version",
        "Authoring JSON file",
        help_text="Successor authoring must omit Definition metadata.",
    )
    assert authoring is not None
    rendering = prompt_text(
        "Create Successor Template Version",
        "Rendering specification file",
        help_text="Enter the exact successor rendering specification.",
    )
    assert rendering is not None
    prepared = prepare_template_revision(
        PrepareTemplateRevisionRequest(
            template_id=selected.template_id,
            template_version_id=version_id,
            authoring_file=Path(authoring).expanduser(),
            rendering_specification=Path(rendering).expanduser(),
            expected_snapshot_revision=detail.summary.snapshot_revision,
            actor=state.require_actor(),
        )
    )
    lines = (
        f"Template: {selected.template_id}",
        f"Name: {selected.name}",
        f"Current Version: {detail.summary.current_template_version_id or '-'}",
        f"Current head: {detail.summary.head_template_version_id}",
        f"New Version: {prepared.version.template_version_id}",
        f"Version label: {prepared.version.version_label}",
        f"Revision sequence: {prepared.version.revision_sequence}",
        f"Artifact category: {prepared.version.artifact_category}",
        f"Pages: {len(prepared.version.page_manifest)}",
        f"Expected return: {prepared.version.default_expected_return_status}",
        f"Privacy: {prepared.version.default_privacy_policy.classification}",
        f"Rendering contract: {prepared.version.rendering_contract_version}",
        (
            "Rendering reference: "
            f"{prepared.version.rendering_specification_reference}"
        ),
        f"Rendering SHA-256: {prepared.rendering_source.sha256}",
        f"Expected Template snapshot: {detail.summary.snapshot_revision}",
    )
    if not confirm_write("Create Successor Template Version", "REVISE", lines):
        return
    result = commit_template_revision(prepared)
    show_result("Template Result", _mutation_lines(result))


def _activate(state: MenuSessionContext) -> None:
    selected = _choose_template(title="Choose Template to Activate")
    detail = get_template(selected.template_id)
    head = detail.summary.head_template_version_id
    prepared = prepare_template_activation(
        PrepareTemplateActivationRequest(
            template_id=selected.template_id,
            template_version_id=head,
            expected_snapshot_revision=detail.summary.snapshot_revision,
            actor=state.require_actor(),
        )
    )
    lines = _version_preview_lines(detail, head)
    if not confirm_write("Activate Template Version", "ACTIVATE", lines):
        return
    result = commit_template_activation(prepared)
    show_result("Template Result", _mutation_lines(result))


def _description_update(detail: TemplateDetail) -> str | None:
    current = detail.definition.description
    action = select_one(
        "Template Description",
        ("keep", "change", "clear"),
        (
            "Keep current description",
            "Change description",
            "Clear description",
        ),
        help_text="Description is reusable Template metadata only.",
    )
    if action == "keep":
        return current
    if action == "clear":
        return None
    value = prompt_text(
        "Update Template",
        "Description",
        help_text="Enter the new reusable Template description.",
        optional=True,
    )
    return value


def _update(state: MenuSessionContext) -> None:
    selected = _choose_template(title="Choose Template to Update")
    detail = get_template(selected.template_id)
    name = prompt_text(
        "Update Template",
        "Name",
        help_text="Change only the teacher-facing reusable Template name.",
        default=detail.definition.name,
    )
    assert name is not None
    purpose = prompt_text(
        "Update Template",
        "Purpose",
        help_text="Change only the reusable Template purpose.",
        default=detail.definition.purpose,
    )
    assert purpose is not None
    description = _description_update(detail)
    prepared = prepare_template_update(
        PrepareTemplateUpdateRequest(
            template_id=selected.template_id,
            name=name,
            purpose=purpose,
            description=description,
            expected_snapshot_revision=detail.summary.snapshot_revision,
            actor=state.require_actor(),
        )
    )
    lines = (
        f"Template: {selected.template_id}",
        f"Name: {prepared.definition.name}",
        f"Purpose: {prepared.definition.purpose}",
        f"Description: {prepared.definition.description or '-'}",
        f"Artifact category: {prepared.definition.artifact_category}",
        f"Current Version: {detail.summary.current_template_version_id or '-'}",
        f"Head Version: {detail.summary.head_template_version_id}",
        f"Expected Template snapshot: {detail.summary.snapshot_revision}",
    )
    if not confirm_write("Update Template", "UPDATE", lines):
        return
    result = commit_template_update(prepared)
    show_result("Template Result", _mutation_lines(result))


def _retire_version(state: MenuSessionContext) -> None:
    selected = _choose_template(title="Choose Template")
    detail = get_template(selected.template_id)
    candidates = tuple(
        item
        for item in detail.versions
        if item.status == "draft"
        and item.template_version_id
        != detail.summary.current_template_version_id
    )
    if not candidates:
        raise ConcordWorkflowError(
            "No non-current draft Template Versions can be retired."
        )
    candidate = select_one(
        "Choose Draft Version to Retire",
        candidates,
        tuple(
            f"{item.revision_sequence}. {item.version_label} "
            f"({item.template_version_id})"
            for item in candidates
        ),
        help_text="Only non-current draft Versions may be retired independently.",
    )
    prepared = prepare_template_retire_version(
        PrepareTemplateRetireVersionRequest(
            template_id=selected.template_id,
            template_version_id=candidate.template_version_id,
            expected_snapshot_revision=detail.summary.snapshot_revision,
            actor=state.require_actor(),
        )
    )
    lines = _version_preview_lines(detail, candidate.template_version_id)
    if not confirm_write("Retire Template Version", "RETIRE", lines):
        return
    result = commit_template_retire_version(prepared)
    show_result("Template Result", _mutation_lines(result))


def _retire(state: MenuSessionContext) -> None:
    selected = _choose_template(title="Choose Template to Retire")
    detail = get_template(selected.template_id)
    prepared = prepare_template_retire(
        PrepareTemplateRetireRequest(
            template_id=selected.template_id,
            expected_snapshot_revision=detail.summary.snapshot_revision,
            actor=state.require_actor(),
        )
    )
    lines = _detail_lines(detail) + (
        "Retirement preserves all historical Versions and rendering specifications.",
        f"Expected Template snapshot: {detail.summary.snapshot_revision}",
    )
    if not confirm_write("Retire Template", "RETIRE", lines):
        return
    result = commit_template_retire(prepared)
    show_result("Template Result", _mutation_lines(result))




def _starter_status_label(item: StarterTemplateStatus) -> str:
    return (
        f"{item.display_name} ({item.starter_key}) - "
        f"{item.family}; {item.page_count} page(s) {item.orientation}; "
        f"{item.installation_state}"
    )


def _choose_starter(*, title: str) -> StarterTemplateStatus:
    items = list_starter_template_statuses()
    return select_one(
        title,
        items,
        tuple(_starter_status_label(item) for item in items),
        help_text=(
            "Choose one packaged synthetic starter. Browsing does not "
            "install or modify workspace state."
        ),
    )


def _starter_detail_lines(
    status: StarterTemplateStatus,
) -> tuple[str, ...]:
    entry = get_starter_template(status.starter_key)
    return (
        f"Starter: {entry.starter_key}",
        f"Name: {entry.display_name}",
        f"Family: {entry.family}",
        f"Purpose: {entry.purpose}",
        f"Description: {entry.description}",
        f"Template: {entry.template_id}",
        f"Initial Version: {entry.template_version_id}",
        f"Artifact category: {entry.artifact_category}",
        f"Pages: {entry.page_count}",
        f"Orientation: {entry.orientation}",
        "Expected return: returned_expected",
        f"Privacy: {entry.default_privacy_classification}",
        "Audience: " + ", ".join(entry.suggested_audience_kinds),
        (
            "Activity types: "
            + (
                ", ".join(entry.suggested_activity_type_keys)
                if entry.suggested_activity_type_keys
                else "-"
            )
        ),
        f"Authorship: {entry.default_authorship_mode}",
        f"Subject: {entry.default_subject_kind}",
        (
            "Rendering reference: "
            f"{entry.rendering_specification_reference}"
        ),
        f"Rendering SHA-256: {entry.rendering_sha256()}",
        f"Installation state: {status.installation_state}",
    )


def _starter_install_result_lines(
    result: StarterTemplateInstallResult,
) -> tuple[str, ...]:
    lines = [
        f"Starter: {result.starter_key}",
        f"Template: {result.template_id}",
        f"Version: {result.template_version_id}",
        f"Outcome: {result.outcome}",
        f"Snapshot: {result.snapshot_revision}",
    ]
    if result.workspace_created:
        lines.insert(0, "Created the Paper Data Suite workspace.")
    return tuple(lines)


def _show_starter_selected() -> None:
    selected = _choose_starter(title="Choose Starter Template")
    show_result(
        "Starter Template",
        _starter_detail_lines(selected),
    )


def _install_starter(state: MenuSessionContext) -> None:
    selected = _choose_starter(title="Choose Starter Template to Install")
    prepared = prepare_starter_template_install(
        PrepareStarterTemplateInstallRequest(
            starter_key=selected.starter_key,
            actor=state.require_actor(),
        )
    )
    if prepared.initial_state == STARTER_INSTALLATION_ALREADY_INSTALLED:
        show_result(
            "Starter Template",
            _starter_detail_lines(selected)
            + ("No canonical write is required.",),
        )
        return
    lines = _starter_detail_lines(selected) + (
        "Initial starter Version will be installed active/current.",
        "Future customization uses the ordinary successor workflow.",
    )
    if not confirm_write("Install Starter Template", "INSTALL", lines):
        return
    result = commit_starter_template_install(prepared)
    show_result(
        "Starter Installation Result",
        _starter_install_result_lines(result),
    )


def _starter_install_all_lines(
    result: StarterTemplateInstallAllResult,
) -> tuple[str, ...]:
    return (
        f"Installed: {result.installed_count}",
        f"Already installed: {result.already_installed_count}",
        f"Processed: {len(result.results)}",
    )


def _install_all_starters(state: MenuSessionContext) -> None:
    prepared = prepare_starter_template_install_all(
        PrepareStarterTemplateInstallAllRequest(
            actor=state.require_actor(),
        )
    )
    missing = sum(
        item.initial_state != STARTER_INSTALLATION_ALREADY_INSTALLED
        for item in prepared.items
    )
    already = len(prepared.items) - missing
    if missing == 0:
        show_result(
            "Starter Template Library",
            (
                "All 30 packaged starter Templates are already installed.",
                "No canonical write is required.",
            ),
        )
        return
    lines = (
        f"Missing starters to install: {missing}",
        f"Already installed: {already}",
        "Each missing starter becomes an ordinary active reusable Template.",
        "Existing exact starter lineages will not be rewritten.",
    )
    if not confirm_write("Install Starter Templates", "INSTALL", lines):
        return
    result = commit_starter_template_install_all(prepared)
    show_result(
        "Starter Installation Result",
        _starter_install_all_lines(result),
    )


def _starter_library_menu(state: MenuSessionContext) -> None:
    while True:
        clear_screen()
        print_menu_header("Starter Template Library")
        print("1. Browse / preview starter Templates")
        print("2. Install one starter Template")
        print("3. Install all missing starter Templates")
        print_navigation()
        print()
        raw = input("Select an option: ").strip()
        navigation = parse_menu_navigation(raw)
        if navigation is ConcordMenuChoice.HELP:
            clear_screen()
            print_menu_header("Starter Template Library Help")
            print("Starters are packaged synthetic reusable Templates.")
            print("Browsing is read-only; installation is always explicit.")
            print("Installed starters use the ordinary Template authority.")
            print("Teacher revisions are never reset by reinstalling.")
            print()
            pause_for_user()
            continue
        if navigation is NavigationChoice.BACK:
            return
        actions = {
            "1": _show_starter_selected,
            "2": lambda: _install_starter(state),
            "3": lambda: _install_all_starters(state),
        }
        action = actions.get(raw)
        if action is None:
            print(navigation_hint_with_help())
            pause_for_user()
            continue
        _run(action)



def _run(action: Callable[[], None]) -> None:
    try:
        action()
    except CancelMenuAction:
        return
    except TemplateStoragePartialSuccessError as error:
        _show_partial_success(error)
    except StarterTemplateInstallAllPartialSuccessError as error:
        show_result(
            "Starter Installation Partial Success",
            (
                f"Completed starter installs: {len(error.completed_results)}",
                f"Failed starter: {error.failed_starter_key}",
                "Rerun install-all to reconcile exact installed starters.",
            ),
        )
    except ConcordWorkflowError as error:
        show_result("Template Error", (str(error),))
    except (OSError, TypeError, ValueError) as error:
        show_result("Template Error", (str(error),))


def launch_template_library_menu(state: MenuSessionContext) -> None:
    """Run the low-density workspace-level reusable Template menu."""
    while True:
        clear_screen()
        print_menu_header("Template Library")
        print("1. List / select Templates")
        print("2. Create Template")
        print("3. View Template and version history")
        print("4. Create successor version")
        print("5. Activate current version")
        print("6. Update Template metadata")
        print("7. Retire version")
        print("8. Retire Template")
        print("9. Browse / install starter Templates")
        print_navigation()
        print()
        raw = input("Select an option: ").strip()
        navigation = parse_menu_navigation(raw)
        if navigation is ConcordMenuChoice.HELP:
            _help()
            continue
        if navigation is NavigationChoice.BACK:
            return
        actions = {
            "1": _show_selected,
            "2": lambda: _create(state),
            "3": _show_history,
            "4": lambda: _revise(state),
            "5": lambda: _activate(state),
            "6": lambda: _update(state),
            "7": lambda: _retire_version(state),
            "8": lambda: _retire(state),
            "9": lambda: _starter_library_menu(state),
        }
        action = actions.get(raw)
        if action is None:
            print(navigation_hint_with_help())
            pause_for_user()
            continue
        _run(action)
