"Teacher-facing Activity Packet generation, review, recovery, and reprint."

from __future__ import annotations

from concord.menu_context import CancelMenuAction, MenuSessionContext
from concord.menu_navigation import (
    ConcordMenuChoice,
    NavigationChoice,
    navigation_hint_with_help,
    parse_menu_navigation,
)
from concord.menu_prompts import (
    confirm_write,
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
from concord.models import PacketComponent, TemplateRenderingInput
from concord.workflows import ActivitySummary, SessionSummary, list_sessions
from concord.workflows.errors import ConcordWorkflowError
from concord.workflows.packet import PacketSummary, get_packet, list_packets
from concord.workflows.packet_instance import (
    PacketInstanceSummary,
    list_packet_instances,
    show_packet_instance,
)
from concord.workflows.packet_instantiation import (
    PacketComponentChoice,
    PacketRenderingBinding,
    PreparedPacketInstantiation,
    PreparePacketInstantiationRequest,
    prepare_packet_instantiation,
)
from concord.workflows.packet_instantiation_commit import (
    PacketInstantiationPartialSuccessError,
    commit_packet_instantiation,
    resume_packet_instantiation,
)
from concord.workflows.packet_rendering import (
    PacketGenerationRenderPartialSuccessError,
    PacketRenderPartialSuccessError,
    RenderPacketGenerationRequest,
    RenderPacketInstanceRequest,
    render_packet_generation,
    render_packet_instance,
)


def launch_packet_generation_menu(
    activity: ActivitySummary,
    state: MenuSessionContext,
) -> None:
    """Run the Activity-specific Packet generation and recovery menu."""
    while True:
        clear_screen()
        print_menu_header("Prepare / Generate Packet")
        print(f"Activity: {activity.title}")
        print()
        print("1. Preview and generate a Packet")
        print("2. List generated Packet Instances")
        print("3. Inspect a Packet Instance")
        print("4. Render / reprint a Packet Instance")
        print("5. Resume incomplete route preparation")
        print_navigation()
        print()
        choice = input("Select an option: ").strip()
        navigation = parse_menu_navigation(choice)
        if navigation is ConcordMenuChoice.HELP:
            _help()
        elif navigation is NavigationChoice.BACK:
            return
        elif choice == "1":
            _generate(activity, state)
        elif choice == "2":
            _list_instances(activity)
        elif choice == "3":
            _inspect_instance(activity)
        elif choice == "4":
            _render_instance(activity, state)
        elif choice == "5":
            _resume_generation(activity)
        else:
            print(navigation_hint_with_help())
            pause_for_user()


def _help() -> None:
    clear_screen()
    print_menu_header("Packet Generation Help")
    print("Choose one exact active Packet Version and one explicit Session.")
    print("Concord resolves audience targets before any generation state is written.")
    print("The preview shows exact counts, diagnostics, and a review digest.")
    print("Type GENERATE only after reviewing the resolved generation.")
    print("A retry reuses durable Packet, Artifact, Page, and route identities.")
    print("Reprint never allocates a replacement route for an existing Packet.")
    print()
    pause_for_user()


def _generate(
    activity: ActivitySummary,
    state: MenuSessionContext,
    selected_packet: PacketSummary | None = None,
) -> None:
    try:
        summary = (
            _choose_active_packet() if selected_packet is None else selected_packet
        )
        detail = get_packet(summary.packet_definition_id)
        current_version_id = detail.summary.current_packet_version_id
        if current_version_id is None:
            raise ConcordWorkflowError("Selected Packet has no active current Version.")
        version = next(
            (
                item
                for item in detail.versions
                if item.packet_version_id == current_version_id
            ),
            None,
        )
        if version is None:
            raise ConcordWorkflowError(
                "Selected Packet current Version is unavailable."
            )
        session = _choose_session(activity)
        choices = _component_choices(version.components)
        prepared = prepare_packet_instantiation(
            PreparePacketInstantiationRequest(
                class_id=activity.class_id,
                activity_id=activity.activity_id,
                session_id=session.session_id,
                packet_definition_id=summary.packet_definition_id,
                packet_version_id=version.packet_version_id,
                actor=state.require_actor(),
                component_choices=choices,
            )
        )
        bindings = _prompt_missing_bindings(prepared)
        if bindings:
            prepared = prepare_packet_instantiation(
                PreparePacketInstantiationRequest(
                    class_id=activity.class_id,
                    activity_id=activity.activity_id,
                    session_id=session.session_id,
                    packet_definition_id=summary.packet_definition_id,
                    packet_version_id=version.packet_version_id,
                    actor=state.require_actor(),
                    component_choices=choices,
                    rendering_bindings=bindings,
                )
            )
        lines = _preview_lines(prepared)
        if not prepared.ready_for_commit:
            show_result("Packet Preview", lines)
            return
        if not confirm_write("Generate Packet", "GENERATE", lines):
            return
        committed = commit_packet_instantiation(prepared)
        rendered = render_packet_generation(
            RenderPacketGenerationRequest(
                class_id=activity.class_id,
                activity_id=activity.activity_id,
                generation_id=committed.generation_id,
                actor=state.require_actor(),
            )
        )
        result_lines = [
            "Packet generation completed.",
            f"Generation: {committed.generation_id}",
            f"Packet Instances: {len(rendered.packets)}",
            f"Pages: {rendered.page_count}",
            f"Routes: {rendered.route_count}",
        ]
        result_lines.extend(
            f"Output: {item.output_path}" for item in rendered.packets
        )
        show_result("Packet Generation Result", tuple(result_lines))
    except CancelMenuAction:
        return
    except PacketInstantiationPartialSuccessError as error:
        show_result(
            "Packet Generation Partial Success",
            (
                str(error),
                f"Generation: {error.result.generation_id}",
                f"Stage: {error.stage}",
                (
                    f"Routes: {error.result.routes_verified}/"
                    f"{error.result.routes_expected}"
                ),
                "Use Resume incomplete route preparation before regenerating.",
            ),
        )
    except PacketGenerationRenderPartialSuccessError as error:
        show_result(
            "Packet Rendering Partial Success",
            (
                str(error),
                f"Generation: {error.generation_id}",
                f"Completed Packet outputs: {len(error.completed)}",
                "Use Render / reprint for any incomplete Packet Instance.",
            ),
        )
    except PacketRenderPartialSuccessError as error:
        show_result(
            "Packet Rendering Partial Success",
            (
                str(error),
                f"Output: {error.result.output_path}",
                "The PDF is durable; retrying will reconcile lifecycle state.",
            ),
        )
    except Exception as error:
        show_result("Packet Generation Error", (str(error),))


def generate_saved_packet(
    activity: ActivitySummary,
    state: MenuSessionContext,
    packet: PacketSummary,
) -> None:
    """Prepare one teacher-selected saved Packet through the normal review flow."""
    _generate(activity, state, selected_packet=packet)


def _choose_active_packet() -> PacketSummary:
    packets = tuple(
        item
        for item in list_packets()
        if item.status == "active" and item.current_packet_version_id is not None
    )
    if not packets:
        raise ConcordWorkflowError("No active reusable Packets are available.")
    return select_one(
        "Choose a Packet",
        packets,
        tuple(
            f"{item.name} ({item.packet_definition_id}) - "
            f"{item.current_packet_version_id}"
            for item in packets
        ),
        help_text="Choose the reusable Packet to instantiate for this Activity.",
    )


def _choose_session(activity: ActivitySummary) -> SessionSummary:
    sessions = tuple(
        item
        for item in list_sessions(activity.class_id, activity.activity_id)
        if item.status not in {"cancelled", "archived"}
    )
    if not sessions:
        raise ConcordWorkflowError("No usable Sessions are available.")
    return select_one(
        "Choose a Session",
        sessions,
        tuple(
            f"{item.sequence}. {item.label or item.session_id} [{item.status}]"
            for item in sessions
        ),
        help_text="Issue #62 requires one explicit Session for Packet generation.",
    )


def _component_choices(
    components: tuple[PacketComponent, ...],
) -> tuple[PacketComponentChoice, ...]:
    choices: list[PacketComponentChoice] = []
    for component in components:
        if (
            component.requirement_level == "conditional"
            and component.condition is not None
            and component.condition.condition_kind == "teacher_choice"
        ):
            include = select_one(
                "Conditional Packet Component",
                (True, False),
                (
                    f"Include {component.label or component.packet_component_id}",
                    f"Omit {component.label or component.packet_component_id}",
                ),
                help_text=(
                    "This Packet component explicitly requires a teacher yes/no "
                    "choice for this generation."
                ),
            )
            choices.append(
                PacketComponentChoice(
                    packet_component_id=component.packet_component_id,
                    include=include,
                )
            )
    return tuple(choices)


def _prompt_missing_bindings(
    prepared: PreparedPacketInstantiation,
) -> tuple[PacketRenderingBinding, ...]:
    missing = []
    seen: set[tuple[str, str]] = set()
    for diagnostic in prepared.diagnostics:
        if (
            diagnostic.code == "required_rendering_input_missing"
            and diagnostic.packet_component_id is not None
            and diagnostic.input_key is not None
        ):
            key = (diagnostic.packet_component_id, diagnostic.input_key)
            if key not in seen:
                seen.add(key)
                missing.append(key)
    if not missing:
        return ()

    definitions = _rendering_input_index(prepared)
    bindings: list[PacketRenderingBinding] = []
    for component_id, input_key in missing:
        definition = definitions.get((component_id, input_key))
        value_kind = "text" if definition is None else definition.value_kind
        raw = prompt_text(
            "Packet Rendering Input",
            input_key.replace("_", " ").title(),
            help_text=(
                f"Enter the teacher-controlled {value_kind} value for "
                f"component {component_id}."
            ),
        )
        assert raw is not None
        value: str | int | bool = raw
        if value_kind == "integer":
            try:
                value = int(raw)
            except ValueError as error:
                raise ConcordWorkflowError(
                    f"{input_key} requires an integer."
                ) from error
        elif value_kind == "boolean":
            normalized = raw.casefold()
            if normalized not in {"true", "false", "yes", "no"}:
                raise ConcordWorkflowError(
                    f"{input_key} requires true/false or yes/no."
                )
            value = normalized in {"true", "yes"}
        bindings.append(
            PacketRenderingBinding(
                packet_component_id=component_id,
                input_key=input_key,
                value=value,
            )
        )
    return tuple(bindings)


def _rendering_input_index(
    prepared: PreparedPacketInstantiation,
) -> dict[tuple[str, str], TemplateRenderingInput]:
    versions = {
        source.template_version_id: source.template_version
        for source in prepared.template_sources
    }
    result: dict[tuple[str, str], TemplateRenderingInput] = {}
    for component in prepared.packet_version.components:
        if component.template_version_id is None:
            continue
        version = versions.get(component.template_version_id)
        if version is None:
            continue
        for item in version.rendering_inputs:
            result[(component.packet_component_id, item.input_key)] = item
    return result


def _preview_lines(
    prepared: PreparedPacketInstantiation,
) -> tuple[str, ...]:
    lines = [
        f"Packet: {prepared.packet_definition.name}",
        f"Packet Version: {prepared.packet_version.packet_version_id}",
        f"Activity: {prepared.activity.activity_id}",
        f"Session: {prepared.session.label or prepared.session.session_id}",
        f"Generation date: {prepared.generation_date}",
        f"Packet Instances: {prepared.packet_instance_count}",
        f"Artifacts: {prepared.artifact_count}",
        f"Pages: {prepared.page_count}",
        f"Routes: {prepared.route_count}",
        f"Review digest: {prepared.review_digest}",
        "",
        "Components:",
    ]
    for component in prepared.component_previews:
        lines.append(
            f"{component.sequence}. {component.packet_component_id}: "
            f"{component.disposition}; targets "
            f"{component.included_target_count}/{component.eligible_target_count}; "
            f"artifacts {component.artifact_count}; pages {component.page_count}"
        )
    lines.append("")
    lines.append("Resolved targets:")
    lines.extend(
        f"{target.target_key}: {len(target.artifacts)} artifact(s)"
        for target in prepared.target_plans
    )
    if prepared.diagnostics:
        lines.append("")
        lines.append("Diagnostics:")
        lines.extend(
            (
                ("BLOCKING " if item.blocking else "NOTICE ")
                + f"{item.code}: {item.message}"
            )
            for item in prepared.diagnostics
        )
    return tuple(lines)


def _list_instances(activity: ActivitySummary) -> None:
    try:
        items = list_packet_instances(activity.class_id, activity.activity_id)
        lines = (
            tuple(
                f"{item.packet_instance_id}: {item.target_key}; "
                f"{item.generation_status}; generation={item.generation_id}; "
                f"pages={item.page_count}; output={item.output_relative_path or '-'}"
                for item in items
            )
            if items
            else ("No Packet Instances have been generated for this Activity.",)
        )
        show_result("Packet Instances", lines)
    except Exception as error:
        show_result("Packet Instance Error", (str(error),))


def _choose_instance(
    activity: ActivitySummary,
    *,
    title: str,
) -> PacketInstanceSummary:
    items = list_packet_instances(activity.class_id, activity.activity_id)
    if not items:
        raise ConcordWorkflowError("No Packet Instances are available.")
    return select_one(
        title,
        items,
        tuple(
            f"{item.target_key} - {item.generation_status} "
            f"({item.packet_instance_id})"
            for item in items
        ),
        help_text="Choose one Activity-specific Packet Instance.",
    )


def _inspect_instance(activity: ActivitySummary) -> None:
    try:
        selected = _choose_instance(activity, title="Choose Packet Instance")
        detail = show_packet_instance(
            activity.class_id,
            activity.activity_id,
            selected.packet_instance_id,
        )
        item = detail.summary
        lines = (
            f"Packet Instance: {item.packet_instance_id}",
            f"Generation: {item.generation_id}",
            f"Packet: {item.packet_definition_id}:{item.packet_version_id}",
            f"Session: {item.session_id}",
            f"Target: {item.target_key}",
            f"Status: {item.generation_status}",
            f"Artifacts: {item.artifact_count}",
            f"Pages: {item.page_count}",
            f"Routes: {item.route_count}",
            f"Output: {item.output_relative_path or '-'}",
            f"Output SHA-256: {item.output_sha256 or '-'}",
        )
        show_result("Packet Instance", lines)
    except CancelMenuAction:
        return
    except Exception as error:
        show_result("Packet Instance Error", (str(error),))


def _render_instance(
    activity: ActivitySummary,
    state: MenuSessionContext,
) -> None:
    try:
        selected = _choose_instance(activity, title="Render / Reprint Packet")
        action = "REPRINT" if selected.generation_status == "generated" else "RENDER"
        if not confirm_write(
            "Render / Reprint Packet",
            action,
            (
                f"Packet Instance: {selected.packet_instance_id}",
                f"Target: {selected.target_key}",
                f"Status: {selected.generation_status}",
                (
                    "Existing PDS2 route identities will be reused."
                    if selected.generation_status == "generated"
                    else "Prepared PDS2 route identities will be rendered."
                ),
            ),
        ):
            return
        result = render_packet_instance(
            RenderPacketInstanceRequest(
                class_id=activity.class_id,
                activity_id=activity.activity_id,
                packet_instance_id=selected.packet_instance_id,
                actor=state.require_actor(),
            )
        )
        show_result(
            "Packet Render Result",
            (
                f"Output: {result.output_path}",
                f"Output SHA-256: {result.output_sha256}",
                f"Pages: {result.page_count}",
                f"Routes: {result.route_count}",
                f"Reprint: {'yes' if result.replayed else 'no'}",
            ),
        )
    except CancelMenuAction:
        return
    except PacketRenderPartialSuccessError as error:
        show_result(
            "Packet Rendering Partial Success",
            (
                str(error),
                f"Output: {error.result.output_path}",
                "The PDF is durable; retry to reconcile lifecycle state.",
            ),
        )
    except Exception as error:
        show_result("Packet Rendering Error", (str(error),))


def _resume_generation(activity: ActivitySummary) -> None:
    try:
        items = list_packet_instances(activity.class_id, activity.activity_id)
        generation_ids = tuple(
            dict.fromkeys(
                item.generation_id
                for item in items
                if item.generation_status == "routes_pending"
            )
        )
        if not generation_ids:
            raise ConcordWorkflowError(
                "No Packet generations are waiting for route reconciliation."
            )
        generation_id = select_one(
            "Resume Packet Generation",
            generation_ids,
            generation_ids,
            help_text=(
                "Resume reconciles immutable Core PDS2 routes for already-durable "
                "Packet generation state."
            ),
        )
        result = resume_packet_instantiation(
            activity.class_id,
            activity.activity_id,
            generation_id,
        )
        show_result(
            "Packet Generation Recovery",
            (
                f"Generation: {result.generation_id}",
                f"Packet Instances: {len(result.packet_instance_ids)}",
                f"Routes: {result.routes_verified}/{result.routes_expected}",
                "Generation is ready for rendering.",
            ),
        )
    except CancelMenuAction:
        return
    except PacketInstantiationPartialSuccessError as error:
        show_result(
            "Packet Generation Partial Success",
            (
                str(error),
                f"Generation: {error.result.generation_id}",
                f"Stage: {error.stage}",
                (
                    f"Routes: {error.result.routes_verified}/"
                    f"{error.result.routes_expected}"
                ),
            ),
        )
    except Exception as error:
        show_result("Packet Generation Recovery Error", (str(error),))


__all__ = ["launch_packet_generation_menu"]
