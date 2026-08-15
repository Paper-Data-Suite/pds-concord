"""Direct Academic Publication commands for Concord Activities."""

from __future__ import annotations

import argparse
from pathlib import Path

from pds_core.academic_work_registrations import AcademicWorkRegistration
from pds_core.registry_services import (
    AcademicWorkRegistrationRequest,
    update_academic_work_registration,
)
from pds_core.routing_models import ModuleWorkRef

from concord.academic_result_manifest_generation import (
    GenerateAcademicResultManifestRequest,
    generate_academic_result_manifest,
    list_academic_result_manifest_revisions,
    load_academic_result_manifest_revision,
    manifest_generation_summary,
    manifest_preview_summary,
    preview_academic_result_manifest,
)
from concord.academic_result_publication import (
    load_concord_publication_series_status,
    publish_concord_academic_results,
    query_concord_publication_catalog,
    rebuild_concord_publication_catalog,
    rebuild_full_academic_catalog,
    republish_concord_academic_results_after_withdrawal,
    supersede_concord_academic_results,
    withdraw_concord_academic_result_publication,
)
from concord.academic_work_registration import (
    load_current_concord_academic_work_registration,
    register_concord_academic_work,
)
from concord.cli_app.common import (
    load_command_standards_library,
    workflow_actor,
    workspace_arg,
)
from concord.pds_contract import CONCORD_MODULE_ID
from concord.workflows import show_activity
from concord.workflows.context import resolve_read_workspace_root


def _root(args: argparse.Namespace) -> Path:
    resolved = resolve_read_workspace_root(workspace_arg(args))
    if resolved is None:
        raise FileNotFoundError("Paper Data Suite workspace does not exist.")
    return Path(resolved)


def _work(args: argparse.Namespace) -> ModuleWorkRef:
    return ModuleWorkRef(CONCORD_MODULE_ID, args.class_id, args.activity_id)


def _request(args: argparse.Namespace) -> GenerateAcademicResultManifestRequest:
    return GenerateAcademicResultManifestRequest(
        class_id=args.class_id,
        activity_id=args.activity_id,
        expected_snapshot_revision=args.expected_snapshot,
        actor=workflow_actor(args),
        revision_reason=args.revision_reason,
    )


def _print_registration(registration: AcademicWorkRegistration) -> None:
    print(f"Work: {registration.work.class_id}/{registration.work.work_id}")
    print(f"Registration revision: {registration.registration_revision}")
    print(f"Title: {registration.title}")
    print(f"Academic intent: {registration.academic_intent}")
    print(f"Lifecycle: {registration.lifecycle}")
    print(f"Producer contract: {registration.producer_contract_version}")


def _print_summary(summary: dict[str, object]) -> None:
    work = summary["work"]
    if isinstance(work, ModuleWorkRef):
        print(f"Work: {work.class_id}/{work.work_id}")
    for key, label in (
        ("disposition", "Disposition"),
        ("registration_revision", "Registration revision"),
        ("source_snapshot_revision", "Source snapshot revision"),
        ("record_set_id", "Record set"),
        ("record_set_revision", "Record-set revision"),
        ("manifest_contract_version", "Manifest contract"),
        ("score_count", "Scores"),
        ("current_score_count", "Current Scores"),
        ("historical_score_count", "Historical Scores"),
        ("standard_backed_score_count", "Standard-backed Scores"),
        ("local_score_count", "Local Scores"),
        ("non_score_count", "Non-score records"),
        ("moderation_dependent_count", "Moderation-dependent Scores"),
        ("manifest_path", "Manifest path"),
        ("manifest_sha256", "Manifest SHA-256"),
    ):
        if key in summary:
            print(f"{label}: {summary[key]}")
    capabilities = summary.get("capabilities")
    if capabilities is not None:
        print("Capabilities: " + ", ".join(capabilities))  # type: ignore[arg-type]


def handle_register(args: argparse.Namespace) -> int:
    result = register_concord_academic_work(
        _root(args),
        args.class_id,
        args.activity_id,
        academic_intent=args.academic_intent,
        lifecycle=args.lifecycle,
    )
    print(f"Disposition: {result.disposition}")
    _print_registration(result.registration)
    return 0


def handle_registration_show(args: argparse.Namespace) -> int:
    registration = load_current_concord_academic_work_registration(
        _root(args), args.class_id, args.activity_id
    )
    if registration is None:
        print("No current Academic Work Registration.")
        return 0
    _print_registration(registration)
    return 0


def handle_registration_update(args: argparse.Namespace) -> int:
    root = _root(args)
    current = load_current_concord_academic_work_registration(
        root, args.class_id, args.activity_id
    )
    if current is None:
        raise FileNotFoundError("Academic Work Registration does not exist.")
    detail = show_activity(
        args.class_id,
        args.activity_id,
        workspace_root=root,
    )
    request = AcademicWorkRegistrationRequest(
        work=current.work,
        producer_contract_version=current.producer_contract_version,
        title=detail.summary.title,
        work_kind=current.work_kind,
        academic_intent=args.academic_intent,
        lifecycle=args.lifecycle,
        source_records=current.source_records,
    )
    result = update_academic_work_registration(
        root,
        request,
        expected_current_revision=args.expected_registration_revision,
    )
    print(f"Disposition: {result.disposition}")
    _print_registration(result.registration)
    return 0


def handle_manifest_preview(args: argparse.Namespace) -> int:
    preview = preview_academic_result_manifest(
        _request(args),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    _print_summary(manifest_preview_summary(preview))
    return 0


def handle_manifest_generate(args: argparse.Namespace) -> int:
    result = generate_academic_result_manifest(
        _request(args),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    _print_summary(manifest_generation_summary(result))
    return 0


def handle_manifest_list(args: argparse.Namespace) -> int:
    items = list_academic_result_manifest_revisions(_root(args), _work(args))
    if not items:
        print("No Concord academic-result manifest revisions.")
        return 0
    for item in items:
        print(
            f"{item.revision}\t{item.sha256}\t"
            f"{item.manifest.projection.projection_digest}\t{item.relative_path}"
        )
    return 0


def handle_manifest_show(args: argparse.Namespace) -> int:
    stored = load_academic_result_manifest_revision(
        _root(args), _work(args), args.revision
    )
    text = stored.content.decode("utf-8")
    print(text, end="" if text.endswith("\n") else "\n")
    return 0


def handle_publish(args: argparse.Namespace) -> int:
    result = publish_concord_academic_results(
        _request(args),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print(f"Disposition: {result.disposition}")
    print(f"Publication: {result.publication.publication_id}")
    print(f"Record-set revision: {result.publication.record_set_revision}")
    print(f"Manifest SHA-256: {result.publication.manifest_digest}")
    return 0


def handle_supersede(args: argparse.Namespace) -> int:
    state = load_concord_publication_series_status(
        args.class_id,
        args.activity_id,
        workspace_root=workspace_arg(args),
    )
    if (
        state.core_head_withdrawal is not None
        and state.core_head is not None
        and state.core_head.publication_id == args.expected_current_publication_id
    ):
        result = republish_concord_academic_results_after_withdrawal(
            _request(args),
            expected_withdrawn_head_publication_id=(
                args.expected_current_publication_id
            ),
            workspace_root=workspace_arg(args),
            standards_library=load_command_standards_library(args),
        )
    else:
        result = supersede_concord_academic_results(
            _request(args),
            expected_current_publication_id=args.expected_current_publication_id,
            workspace_root=workspace_arg(args),
            standards_library=load_command_standards_library(args),
        )
    print(f"Disposition: {result.disposition}")
    print(f"Publication: {result.publication.publication_id}")
    print(f"Supersedes: {result.publication.supersedes_publication_id}")
    print(f"Record-set revision: {result.publication.record_set_revision}")
    return 0


def handle_withdraw(args: argparse.Namespace) -> int:
    result = withdraw_concord_academic_result_publication(
        args.class_id,
        args.activity_id,
        publication_id=args.publication_id,
        reason=args.reason,
        workspace_root=workspace_arg(args),
    )
    print(f"Disposition: {result.disposition}")
    print(f"Publication: {result.publication.publication_id}")
    print(f"Withdrawn at: {result.withdrawal.withdrawn_at.isoformat()}")
    print(f"Manifest verification: {result.manifest_verification}")
    return 0


def handle_series_show(args: argparse.Namespace) -> int:
    state = load_concord_publication_series_status(
        args.class_id,
        args.activity_id,
        workspace_root=workspace_arg(args),
    )
    print(f"Work: {state.work.class_id}/{state.work.work_id}")
    print(
        "Producer head: "
        + (str(state.producer_head.revision) if state.producer_head else "none")
    )
    print(
        "Core structural head: "
        + (state.core_head.publication_id if state.core_head else "none")
    )
    print(
        "Core head withdrawn: "
        + ("yes" if state.core_head_withdrawal is not None else "no")
    )
    print(
        "Current selectable publication: "
        + (
            state.current_selectable_publication.publication_id
            if state.current_selectable_publication is not None
            else "none"
        )
    )
    print(
        "Current registration revision: "
        + (
            str(state.current_registration_revision)
            if state.current_registration_revision is not None
            else "none"
        )
    )
    print(f"Catalog available: {'yes' if state.catalog_available else 'no'}")
    print(f"Catalog rows: {len(state.catalog_rows)}")
    for publication in state.publications:
        withdrawal = next(
            (
                item
                for item in state.withdrawals
                if item.publication_id == publication.publication_id
            ),
            None,
        )
        print(
            f"{publication.record_set_revision}\t{publication.publication_id}\t"
            f"supersedes={publication.supersedes_publication_id or '-'}\t"
            f"withdrawn={'yes' if withdrawal is not None else 'no'}"
        )
    return 0


def handle_catalog_list(args: argparse.Namespace) -> int:
    rows = query_concord_publication_catalog(
        args.class_id,
        args.activity_id,
        required_capabilities=tuple(args.required_capability or ()),
        state=args.state,
        workspace_root=workspace_arg(args),
    )
    if not rows:
        print("No matching Concord publication catalog rows.")
        return 0
    for row in rows:
        print(
            f"{row.record_set_revision}\t{row.publication_id}\t"
            f"head={'yes' if row.is_series_head else 'no'}\t"
            f"withdrawn={'yes' if row.is_withdrawn else 'no'}\t"
            f"current={'yes' if row.is_current_selectable else 'no'}"
        )
    return 0


def handle_catalog_rebuild(args: argparse.Namespace) -> int:
    if args.publication_id is None:
        result = rebuild_full_academic_catalog(_root(args))
        print(f"Catalog: {result.catalog_path}")
        print(
            "Source snapshot SHA-256: "
            f"{result.metadata.source_snapshot_sha256}"
        )
        print(f"Publications: {result.metadata.publication_count}")
        return 0
    reconciliation = rebuild_concord_publication_catalog(
        args.class_id,
        args.activity_id,
        publication_id=args.publication_id,
        workspace_root=workspace_arg(args),
    )
    print(f"Publication: {reconciliation.publication.publication_id}")
    print("Catalog reconciliation: verified")
    return 0
