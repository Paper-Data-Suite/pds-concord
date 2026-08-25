"""Workspace-level teacher menu for reusable Concord Packets."""

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
from concord.models import PacketComponent, PacketVersion
from concord.packet_storage import PacketStoragePartialSuccessError
from concord.workflows.errors import ConcordWorkflowError
from concord.workflows.packet import (
    PacketDetail,
    PacketMutationResult,
    PacketSummary,
    PreparePacketActivationRequest,
    PreparePacketCreateRequest,
    PreparePacketRetireRequest,
    PreparePacketRetireVersionRequest,
    PreparePacketRevisionRequest,
    PreparePacketUpdateRequest,
    commit_packet_activation,
    commit_packet_create,
    commit_packet_retire,
    commit_packet_retire_version,
    commit_packet_revision,
    commit_packet_update,
    get_packet,
    list_packets,
    prepare_packet_activation,
    prepare_packet_create,
    prepare_packet_retire,
    prepare_packet_retire_version,
    prepare_packet_revision,
    prepare_packet_update,
)


def _help() -> None:
    clear_screen()
    print_menu_header("Packet Library Help")
    print("Packets are reusable across Activities and classes.")
    print("Packet Versions are immutable ordered compositions.")
    print("Template components pin exact Template Definition/Version identities.")
    print("External components preserve source-owned ModuleRecordRef identities.")
    print(
        "Creating or revising a Packet does not create "
        "Packet Instances or Artifacts."
    )
    print("Activation selects the exact Version for ordinary future use.")
    print("Retirement preserves historical Versions and component references.")
    print()
    pause_for_user()


def _summary_label(item: PacketSummary) -> str:
    return (
        f"{item.name} ({item.packet_definition_id}) - {item.status}; "
        f"current={item.current_packet_version_id or '-'}; "
        f"head={item.head_packet_version_id}"
    )


def _choose_packet(*, title: str) -> PacketSummary:
    items = list_packets()
    if not items:
        raise ConcordWorkflowError("No reusable Concord Packets are available.")
    return select_one(
        title,
        items,
        tuple(_summary_label(item) for item in items),
        help_text="Choose the reusable Packet for this workspace-level action.",
    )


def _component_line(component: PacketComponent) -> str:
    if component.component_kind == "concord_template":
        source = f"Template {component.template_id}:{component.template_version_id}"
    else:
        reference = component.external_reference
        assert reference is not None
        source = (
            f"External {reference.module_id}:"
            f"{reference.record_kind}:{reference.record_id}"
        )
        if reference.contract_version is not None:
            source += f"@{reference.contract_version}"
    audience = component.audience_intent.audience_kind
    if component.audience_intent.role_keys:
        audience += f"[{','.join(component.audience_intent.role_keys)}]"
    condition = (
        component.condition.condition_kind
        if component.condition is not None
        else "-"
    )
    return (
        f"{component.sequence}. {component.label or component.packet_component_id}: "
        f"{source}; copies={component.copies_per_target}; audience={audience}; "
        f"requirement={component.requirement_level}; condition={condition}"
    )


def _find_version(detail: PacketDetail, version_id: str) -> PacketVersion:
    match = next(
        (
            item
            for item in detail.versions
            if item.packet_version_id == version_id
        ),
        None,
    )
    if match is None:
        raise ConcordWorkflowError(
            f"Packet Version is not available: {version_id}"
        )
    return match


def _detail_lines(detail: PacketDetail) -> tuple[str, ...]:
    definition = detail.definition
    summary = detail.summary
    lines = [
        f"Packet: {summary.packet_definition_id}",
        f"Name: {summary.name}",
        f"Purpose: {definition.purpose}",
        f"Status: {summary.status}",
        f"Current Version: {summary.current_packet_version_id or '-'}",
        f"Head Version: {summary.head_packet_version_id}",
        f"Snapshot: {summary.snapshot_revision}",
        f"Versions: {len(detail.versions)}",
        f"Head components: {summary.component_count}",
    ]
    if definition.description is not None:
        lines.append(f"Description: {definition.description}")
    return tuple(lines)


def _version_preview_lines(
    detail: PacketDetail,
    version_id: str,
) -> tuple[str, ...]:
    version = _find_version(detail, version_id)
    lines = [
        f"Packet: {detail.summary.packet_definition_id}",
        f"Name: {detail.summary.name}",
        f"Version: {version.packet_version_id}",
        f"Version label: {version.version_label}",
        f"Revision sequence: {version.revision_sequence}",
        f"Status: {version.status}",
        f"Components: {len(version.components)}",
        f"Copy collation: {version.rendering_rules.copy_collation}",
        f"Target order: {version.rendering_rules.target_order}",
        (
            "Start each component on new page: "
            + (
                "yes"
                if version.rendering_rules.start_each_component_on_new_page
                else "no"
            )
        ),
        f"Expected Packet snapshot: {detail.summary.snapshot_revision}",
        "",
        "Ordered components:",
    ]
    lines.extend(_component_line(item) for item in version.components)
    return tuple(lines)


def _mutation_lines(result: PacketMutationResult) -> tuple[str, ...]:
    lines = [
        f"Packet: {result.packet_definition_id}",
        f"Status: {result.status}",
        f"Snapshot: {result.snapshot_revision}",
        f"Current Version: {result.current_packet_version_id or '-'}",
        f"Head Version: {result.head_packet_version_id}",
    ]
    if result.workspace_created:
        lines.insert(0, "Created the Paper Data Suite workspace.")
    return tuple(lines)


def _show_partial_success(error: PacketStoragePartialSuccessError) -> None:
    lines = [
        (
            "The Packet current pointer was published, but follow-up "
            "verification or cleanup was incomplete."
            if error.pointer_published
            else "The Packet current pointer was not published."
        )
    ]
    if error.snapshot_revision is not None:
        lines.append(f"Snapshot: {error.snapshot_revision}")
    if error.snapshot_sha256 is not None:
        lines.append(f"Snapshot SHA-256: {error.snapshot_sha256}")
    lines.append("Review canonical Packet storage before retrying.")
    show_result("Packet Partial Success", tuple(lines))


def _show_selected() -> None:
    selected = _choose_packet(title="Choose a Packet")
    detail = get_packet(selected.packet_definition_id)
    show_result("Packet Summary", _detail_lines(detail))


def _show_history() -> None:
    selected = _choose_packet(title="Choose a Packet")
    detail = get_packet(selected.packet_definition_id)
    lines = list(_detail_lines(detail))
    lines.append("")
    lines.append("Version history:")
    for version in detail.versions:
        markers: list[str] = []
        if version.packet_version_id == detail.summary.current_packet_version_id:
            markers.append("current")
        if version.packet_version_id == detail.summary.head_packet_version_id:
            markers.append("head")
        marker = f" ({', '.join(markers)})" if markers else ""
        lines.append(
            f"{version.revision_sequence}. {version.packet_version_id} - "
            f"{version.version_label} [{version.status}] "
            f"components={len(version.components)}{marker}"
        )
    show_result("Packet Version History", tuple(lines))


def _choose_activation() -> bool:
    return select_one(
        "Initial Packet Status",
        (False, True),
        (
            "Draft - create without selecting a current Version",
            "Active - validate dependencies and select the initial Version",
        ),
        help_text="Activation is explicit and can also be performed later.",
    )


def _create(state: MenuSessionContext) -> None:
    packet_id = prompt_text(
        "Create Packet",
        "Packet Definition ID",
        help_text="Enter the durable reusable Packet Definition identifier.",
    )
    assert packet_id is not None
    version_id = prompt_text(
        "Create Packet",
        "Initial Packet Version ID",
        help_text="Enter a fresh immutable Packet Version identifier.",
    )
    assert version_id is not None
    authoring = prompt_text(
        "Create Packet",
        "Authoring JSON file",
        help_text="Enter the strict concord_packet_authoring_v1 JSON file.",
    )
    assert authoring is not None
    activate = _choose_activation()
    prepared = prepare_packet_create(
        PreparePacketCreateRequest(
            packet_definition_id=packet_id,
            packet_version_id=version_id,
            authoring_file=Path(authoring).expanduser(),
            actor=state.require_actor(),
            activate=activate,
        )
    )
    lines = [
        f"Packet: {prepared.definition.packet_definition_id}",
        f"Name: {prepared.definition.name}",
        f"Version: {prepared.version.packet_version_id}",
        f"Version label: {prepared.version.version_label}",
        f"Components: {len(prepared.version.components)}",
        f"Initial status: {prepared.version.status}",
        "",
        "Ordered components:",
    ]
    lines.extend(_component_line(item) for item in prepared.version.components)
    if not confirm_write("Create Packet", "CREATE", tuple(lines)):
        return
    result = commit_packet_create(prepared)
    show_result("Packet Result", _mutation_lines(result))


def _revise(state: MenuSessionContext) -> None:
    selected = _choose_packet(title="Choose Packet to Revise")
    detail = get_packet(selected.packet_definition_id)
    version_id = prompt_text(
        "Create Successor Packet Version",
        "New Packet Version ID",
        help_text="Enter a fresh immutable Packet Version identifier.",
    )
    assert version_id is not None
    authoring = prompt_text(
        "Create Successor Packet Version",
        "Authoring JSON file",
        help_text="Successor authoring must omit Definition metadata.",
    )
    assert authoring is not None
    prepared = prepare_packet_revision(
        PreparePacketRevisionRequest(
            packet_definition_id=selected.packet_definition_id,
            packet_version_id=version_id,
            authoring_file=Path(authoring).expanduser(),
            expected_snapshot_revision=detail.summary.snapshot_revision,
            actor=state.require_actor(),
        )
    )
    lines = [
        f"Packet: {selected.packet_definition_id}",
        f"Name: {selected.name}",
        f"Current Version: {detail.summary.current_packet_version_id or '-'}",
        f"Current head: {detail.summary.head_packet_version_id}",
        f"New Version: {prepared.version.packet_version_id}",
        f"Version label: {prepared.version.version_label}",
        f"Revision sequence: {prepared.version.revision_sequence}",
        f"Components: {len(prepared.version.components)}",
        f"Expected Packet snapshot: {detail.summary.snapshot_revision}",
        "",
        "Ordered components:",
    ]
    lines.extend(_component_line(item) for item in prepared.version.components)
    if not confirm_write(
        "Create Successor Packet Version",
        "REVISE",
        tuple(lines),
    ):
        return
    result = commit_packet_revision(prepared)
    show_result("Packet Result", _mutation_lines(result))


def _activate(state: MenuSessionContext) -> None:
    selected = _choose_packet(title="Choose Packet to Activate")
    detail = get_packet(selected.packet_definition_id)
    head = detail.summary.head_packet_version_id
    prepared = prepare_packet_activation(
        PreparePacketActivationRequest(
            packet_definition_id=selected.packet_definition_id,
            packet_version_id=head,
            expected_snapshot_revision=detail.summary.snapshot_revision,
            actor=state.require_actor(),
        )
    )
    lines = _version_preview_lines(detail, head)
    if not confirm_write("Activate Packet Version", "ACTIVATE", lines):
        return
    result = commit_packet_activation(prepared)
    show_result("Packet Result", _mutation_lines(result))


def _description_update(detail: PacketDetail) -> str | None:
    current = detail.definition.description
    action = select_one(
        "Packet Description",
        ("keep", "change", "clear"),
        (
            "Keep current description",
            "Change description",
            "Clear description",
        ),
        help_text="Description is reusable Packet metadata only.",
    )
    if action == "keep":
        return current
    if action == "clear":
        return None
    return prompt_text(
        "Update Packet",
        "Description",
        help_text="Enter the new reusable Packet description.",
        optional=True,
    )


def _update(state: MenuSessionContext) -> None:
    selected = _choose_packet(title="Choose Packet to Update")
    detail = get_packet(selected.packet_definition_id)
    name = prompt_text(
        "Update Packet",
        "Name",
        help_text="Change only the teacher-facing reusable Packet name.",
        default=detail.definition.name,
    )
    assert name is not None
    purpose = prompt_text(
        "Update Packet",
        "Purpose",
        help_text="Change only the reusable Packet purpose.",
        default=detail.definition.purpose,
    )
    assert purpose is not None
    description = _description_update(detail)
    prepared = prepare_packet_update(
        PreparePacketUpdateRequest(
            packet_definition_id=selected.packet_definition_id,
            name=name,
            purpose=purpose,
            description=description,
            expected_snapshot_revision=detail.summary.snapshot_revision,
            actor=state.require_actor(),
        )
    )
    lines = (
        f"Packet: {selected.packet_definition_id}",
        f"Name: {prepared.definition.name}",
        f"Purpose: {prepared.definition.purpose}",
        f"Description: {prepared.definition.description or '-'}",
        f"Current Version: {detail.summary.current_packet_version_id or '-'}",
        f"Head Version: {detail.summary.head_packet_version_id}",
        f"Expected Packet snapshot: {detail.summary.snapshot_revision}",
    )
    if not confirm_write("Update Packet", "UPDATE", lines):
        return
    result = commit_packet_update(prepared)
    show_result("Packet Result", _mutation_lines(result))


def _retire_version(state: MenuSessionContext) -> None:
    selected = _choose_packet(title="Choose Packet")
    detail = get_packet(selected.packet_definition_id)
    candidates = tuple(
        item
        for item in detail.versions
        if item.status == "draft"
        and item.packet_version_id != detail.summary.current_packet_version_id
    )
    if not candidates:
        raise ConcordWorkflowError(
            "No non-current draft Packet Versions can be retired."
        )
    candidate = select_one(
        "Choose Draft Version to Retire",
        candidates,
        tuple(
            f"{item.revision_sequence}. {item.version_label} "
            f"({item.packet_version_id})"
            for item in candidates
        ),
        help_text="Only non-current draft Versions may be retired independently.",
    )
    prepared = prepare_packet_retire_version(
        PreparePacketRetireVersionRequest(
            packet_definition_id=selected.packet_definition_id,
            packet_version_id=candidate.packet_version_id,
            expected_snapshot_revision=detail.summary.snapshot_revision,
            actor=state.require_actor(),
        )
    )
    lines = _version_preview_lines(detail, candidate.packet_version_id)
    if not confirm_write("Retire Packet Version", "RETIRE", lines):
        return
    result = commit_packet_retire_version(prepared)
    show_result("Packet Result", _mutation_lines(result))


def _retire(state: MenuSessionContext) -> None:
    selected = _choose_packet(title="Choose Packet to Retire")
    detail = get_packet(selected.packet_definition_id)
    prepared = prepare_packet_retire(
        PreparePacketRetireRequest(
            packet_definition_id=selected.packet_definition_id,
            expected_snapshot_revision=detail.summary.snapshot_revision,
            actor=state.require_actor(),
        )
    )
    lines = _detail_lines(detail) + (
        "Retirement preserves all historical Versions and component references.",
        f"Expected Packet snapshot: {detail.summary.snapshot_revision}",
    )
    if not confirm_write("Retire Packet", "RETIRE", lines):
        return
    result = commit_packet_retire(prepared)
    show_result("Packet Result", _mutation_lines(result))


def _run(action: Callable[[], None]) -> None:
    try:
        action()
    except CancelMenuAction:
        return
    except PacketStoragePartialSuccessError as error:
        _show_partial_success(error)
    except ConcordWorkflowError as error:
        show_result("Packet Error", (str(error),))
    except (OSError, TypeError, ValueError) as error:
        show_result("Packet Error", (str(error),))


def launch_packet_library_menu(state: MenuSessionContext) -> None:
    """Run the low-density workspace-level reusable Packet menu."""
    while True:
        clear_screen()
        print_menu_header("Packet Library")
        print("1. List / select Packets")
        print("2. Create Packet")
        print("3. View Packet and version history")
        print("4. Create successor version")
        print("5. Activate current version")
        print("6. Update Packet metadata")
        print("7. Retire version")
        print("8. Retire Packet")
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
        }
        action = actions.get(raw)
        if action is None:
            print(navigation_hint_with_help())
            pause_for_user()
            continue
        _run(action)
