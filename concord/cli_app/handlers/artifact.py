"""Direct Artifact, assembly, Author, Subject, and Page commands."""

from __future__ import annotations

import argparse
from typing import NoReturn

from concord.cli_app.common import (
    load_command_standards_library,
    workflow_actor,
    workspace_arg,
)
from concord.cli_app.output import print_commit
from concord.models import (
    ActorReference,
    ConcordRecordReference,
    ParticipantReference,
    PrivacyPolicy,
    SubjectReference,
)
from concord.routing.rendering import RenderArtifactPagesRequest, render_artifact_pages
from concord.workflows import (
    AddArtifactAuthorRequest,
    AddArtifactSubjectRequest,
    AuthorWorkflowReference,
    ReplaceArtifactAuthorRequest,
    ReplaceArtifactSubjectRequest,
    UpdateArtifactAuthorRequest,
    UpdateArtifactSubjectRequest,
    add_artifact_author,
    add_artifact_subject,
    list_artifact_authors,
    list_artifact_subjects,
    replace_artifact_author,
    replace_artifact_subject,
    show_artifact_author,
    show_artifact_subject,
    update_artifact_author,
    update_artifact_subject,
)
from concord.workflows.artifact import list_artifacts, show_artifact
from concord.workflows.artifact_assembly import (
    AssembleArtifactRequest,
    AssemblyPageSelection,
    assemble_returned_artifact,
)
from concord.workflows.artifact_page import (
    ArtifactPagePlan,
    PrepareArtifactPagesRequest,
    list_artifact_pages,
    prepare_artifact_pages,
)
from concord.workflows.context import actor_reference


def _usage(args: argparse.Namespace, message: str) -> NoReturn:
    parser = getattr(args, "command_parser", None)
    if isinstance(parser, argparse.ArgumentParser):
        parser.error(message)
    raise ValueError(message)


def _privacy(value: str | None) -> PrivacyPolicy | None:
    if value is None:
        return None
    return PrivacyPolicy(classification=value)


def _author_reference(args: argparse.Namespace) -> AuthorWorkflowReference:
    kind = args.author_kind
    author_id = getattr(args, "author_id", None)
    owner = getattr(args, "author_owner", None)
    label = getattr(args, "author_label", None)
    if kind == "unknown":
        if author_id is not None:
            _usage(args, "--author-kind unknown must not include --author-id.")
        return None
    if kind == "current_actor":
        if author_id is not None:
            _usage(args, "--author-kind current_actor must not include --author-id.")
        return actor_reference(workflow_actor(args))
    if author_id is None:
        _usage(args, f"--author-kind {kind} requires --author-id.")
    if kind == "core_student":
        if owner not in (None, "core"):
            _usage(args, "core_student Authors must be owned by Core.")
        return ParticipantReference(
            participant_kind="core_student",
            participant_id=author_id,
            owning_system="core",
        )
    if kind == "concord_group":
        if owner not in (None, "concord"):
            _usage(args, "concord_group Authors must be owned by Concord.")
        return ConcordRecordReference(record_kind="group", record_id=author_id)
    if kind == "authorized_adult":
        return ActorReference(
            actor_kind="authorized_adult",
            actor_id=author_id,
            owning_system=owner or "core",
            display_label_snapshot=label,
        )
    _usage(args, f"unsupported --author-kind: {kind}")


def _subject_reference(args: argparse.Namespace) -> SubjectReference:
    kind = args.subject_kind
    owner = getattr(args, "subject_owner", None)
    expected_owner: str | None
    if kind == "core_student":
        expected_owner = "core"
    elif kind.startswith("concord_"):
        expected_owner = "concord"
    else:
        expected_owner = owner
    if kind == "external_record" and expected_owner is None:
        _usage(args, "external_record Subjects require --subject-owner.")
    if owner is not None and expected_owner is not None and owner != expected_owner:
        _usage(args, f"{kind} Subjects must be owned by {expected_owner}.")
    assert expected_owner is not None
    return SubjectReference(
        subject_kind=kind,
        subject_id=args.subject_id,
        owning_system=expected_owner,
        contract_version=getattr(args, "subject_contract_version", None),
    )


def _selection(value: str, args: argparse.Namespace) -> AssemblyPageSelection:
    page_id, separator, scan_id = value.partition("=")
    if not separator or not page_id or not scan_id or "=" in scan_id:
        _usage(args, "--select must use ARTIFACT_PAGE_ID=SCAN_REFERENCE_ID.")
    return AssemblyPageSelection(
        artifact_page_id=page_id,
        scan_reference_id=scan_id,
    )


def handle_artifact_list(args: argparse.Namespace) -> int:
    artifacts = list_artifacts(
        args.class_id,
        args.activity_id,
        workspace_root=workspace_arg(args),
    )
    for item in artifacts:
        print(
            f"{item.artifact_instance_id}\t{item.artifact_category}\t"
            f"{item.artifact_status}\t"
            f"returned={item.returned_required_page_count}/"
            f"{item.required_return_page_count}\t"
            f"authors={item.current_author_count}\t"
            f"subjects={item.current_subject_count}\t"
            f"snapshot={item.snapshot_revision}"
        )
    if not artifacts:
        print("No Artifacts found.")
    return 0


def handle_artifact_show(args: argparse.Namespace) -> int:
    detail = show_artifact(
        args.class_id,
        args.activity_id,
        args.artifact_instance_id,
        workspace_root=workspace_arg(args),
    )
    item = detail.summary
    print(f"Artifact: {item.artifact_instance_id}")
    print(f"Category: {item.artifact_category}")
    print(f"Status: {item.artifact_status}")
    print(f"Generation: {item.generation_status}")
    print(f"Expected return: {item.expected_return_status}")
    print(
        "Returned required pages: "
        f"{item.returned_required_page_count}/{item.required_return_page_count}"
    )
    print(f"Authors: {item.current_author_count}")
    print(f"Subjects: {item.current_subject_count}")
    print(f"Template version: {detail.template_version_id}")
    print(f"Session: {detail.session_id or '-'}")
    print(f"Group: {detail.group_id or '-'}")
    print(f"Privacy: {detail.privacy_classification}")
    print(f"Snapshot revision: {item.snapshot_revision}")
    return 0


def handle_assemble(args: argparse.Namespace) -> int:
    selections = tuple(_selection(value, args) for value in (args.select or ()))
    result = assemble_returned_artifact(
        AssembleArtifactRequest(
            class_id=args.class_id,
            activity_id=args.activity_id,
            artifact_instance_id=args.artifact_instance_id,
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
            selections=selections,
        ),
        workspace_root=workspace_arg(args),
    )
    print(f"Artifact: {result.artifact_instance_id}")
    print(f"Assembly: {result.assembly_id}")
    print(f"Pages: {result.page_count}")
    print(f"Output: {result.output_path}")
    print(f"Output SHA-256: {result.output_sha256}")
    print(f"Reused: {'yes' if result.reused else 'no'}")
    return 0


def handle_author_add(args: argparse.Namespace) -> int:
    result = add_artifact_author(
        AddArtifactAuthorRequest(
            class_id=args.class_id,
            activity_id=args.activity_id,
            artifact_instance_id=args.artifact_instance_id,
            artifact_author_id=args.artifact_author_id,
            author_reference=_author_reference(args),
            authorship_mode=args.authorship_mode,
            attribution_status=args.attribution_status,
            attribution_source=args.attribution_source,
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
            represented_group_id=args.represented_group_id,
            role_assignment_id=args.role_assignment_id,
            representation_status=args.representation_status,
            privacy_policy=_privacy(args.privacy_classification),
        ),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print_commit(result.commit)
    print(f"Artifact Author: {result.association_id}")
    return 0


def handle_author_list(args: argparse.Namespace) -> int:
    authors = list_artifact_authors(
        args.class_id,
        args.activity_id,
        artifact_instance_id=args.artifact_instance_id,
        include_historical=args.include_historical,
        workspace_root=workspace_arg(args),
    )
    for item in authors:
        label = item.reference_display_label or "Unknown"
        state = "current" if item.is_current else "historical"
        print(
            f"{item.artifact_author_id}\t{item.artifact_instance_id}\t"
            f"{label}\t{item.authorship_mode}\t{item.attribution_status}\t"
            f"{state}\tsnapshot={item.snapshot_revision}"
        )
    if not authors:
        print("No Artifact Authors found.")
    return 0


def handle_author_show(args: argparse.Namespace) -> int:
    item = show_artifact_author(
        args.class_id,
        args.activity_id,
        args.artifact_author_id,
        workspace_root=workspace_arg(args),
    )
    print(f"Artifact Author: {item.artifact_author_id}")
    print(f"Artifact: {item.artifact_instance_id}")
    print(f"Completed by: {item.reference_display_label or 'Unknown'}")
    print(f"Authorship mode: {item.authorship_mode}")
    print(f"Attribution status: {item.attribution_status}")
    print(f"Attribution source: {item.attribution_source}")
    print(f"Represents Group: {item.represented_group_id or '-'}")
    print(f"Role Assignment: {item.role_assignment_id or '-'}")
    print(f"Representation: {item.representation_status or '-'}")
    print(f"Current: {'yes' if item.is_current else 'no'}")
    print(f"Snapshot revision: {item.snapshot_revision}")
    return 0


def handle_author_update(args: argparse.Namespace) -> int:
    result = update_artifact_author(
        UpdateArtifactAuthorRequest(
            class_id=args.class_id,
            activity_id=args.activity_id,
            artifact_author_id=args.artifact_author_id,
            attribution_status=args.attribution_status,
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
        ),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print_commit(result.commit)
    print(f"Artifact Author: {result.association_id}")
    return 0


def handle_author_replace(args: argparse.Namespace) -> int:
    result = replace_artifact_author(
        ReplaceArtifactAuthorRequest(
            class_id=args.class_id,
            activity_id=args.activity_id,
            artifact_author_id=args.artifact_author_id,
            replacement_artifact_author_id=args.replacement_artifact_author_id,
            correction_id=args.correction_id,
            reason=args.reason,
            author_reference=_author_reference(args),
            authorship_mode=args.authorship_mode,
            attribution_status=args.attribution_status,
            attribution_source=args.attribution_source,
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
            represented_group_id=args.represented_group_id,
            role_assignment_id=args.role_assignment_id,
            representation_status=args.representation_status,
            privacy_policy=_privacy(args.privacy_classification),
            correction_privacy_policy=_privacy(
                args.correction_privacy_classification
            ),
        ),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print_commit(result.commit)
    print(f"Replacement Artifact Author: {result.association_id}")
    return 0


def handle_subject_add(args: argparse.Namespace) -> int:
    result = add_artifact_subject(
        AddArtifactSubjectRequest(
            class_id=args.class_id,
            activity_id=args.activity_id,
            artifact_instance_id=args.artifact_instance_id,
            artifact_subject_id=args.artifact_subject_id,
            subject_reference=_subject_reference(args),
            subject_role=args.subject_role,
            confirmation_status=args.confirmation_status,
            assignment_source=args.assignment_source,
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
            criterion_id=args.criterion_id,
            privacy_policy=_privacy(args.privacy_classification),
        ),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print_commit(result.commit)
    print(f"Artifact Subject: {result.association_id}")
    return 0


def handle_subject_list(args: argparse.Namespace) -> int:
    subjects = list_artifact_subjects(
        args.class_id,
        args.activity_id,
        artifact_instance_id=args.artifact_instance_id,
        include_historical=args.include_historical,
        workspace_root=workspace_arg(args),
    )
    for item in subjects:
        label = item.reference_display_label or item.subject_reference.subject_id
        state = "current" if item.is_current else "historical"
        print(
            f"{item.artifact_subject_id}\t{item.artifact_instance_id}\t"
            f"{label}\t{item.subject_role}\t{item.confirmation_status}\t"
            f"{state}\tsnapshot={item.snapshot_revision}"
        )
    if not subjects:
        print("No Artifact Subjects found.")
    return 0


def handle_subject_show(args: argparse.Namespace) -> int:
    item = show_artifact_subject(
        args.class_id,
        args.activity_id,
        args.artifact_subject_id,
        workspace_root=workspace_arg(args),
    )
    print(f"Artifact Subject: {item.artifact_subject_id}")
    print(f"Artifact: {item.artifact_instance_id}")
    print(
        "Artifact concerns: "
        f"{item.reference_display_label or item.subject_reference.subject_id}"
    )
    print(f"Subject kind: {item.subject_reference.subject_kind}")
    print(f"Subject role: {item.subject_role}")
    print(f"Confirmation: {item.confirmation_status}")
    print(f"Assignment source: {item.assignment_source}")
    print(f"Criterion: {item.criterion_id or '-'}")
    print(f"Current: {'yes' if item.is_current else 'no'}")
    print(f"Snapshot revision: {item.snapshot_revision}")
    return 0


def handle_subject_update(args: argparse.Namespace) -> int:
    result = update_artifact_subject(
        UpdateArtifactSubjectRequest(
            class_id=args.class_id,
            activity_id=args.activity_id,
            artifact_subject_id=args.artifact_subject_id,
            confirmation_status=args.confirmation_status,
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
        ),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print_commit(result.commit)
    print(f"Artifact Subject: {result.association_id}")
    return 0


def handle_subject_replace(args: argparse.Namespace) -> int:
    result = replace_artifact_subject(
        ReplaceArtifactSubjectRequest(
            class_id=args.class_id,
            activity_id=args.activity_id,
            artifact_subject_id=args.artifact_subject_id,
            replacement_artifact_subject_id=args.replacement_artifact_subject_id,
            correction_id=args.correction_id,
            reason=args.reason,
            subject_reference=_subject_reference(args),
            subject_role=args.subject_role,
            confirmation_status=args.confirmation_status,
            assignment_source=args.assignment_source,
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
            criterion_id=args.criterion_id,
            privacy_policy=_privacy(args.privacy_classification),
            correction_privacy_policy=_privacy(
                args.correction_privacy_classification
            ),
        ),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print_commit(result.commit)
    print(f"Replacement Artifact Subject: {result.association_id}")
    return 0


def handle_prepare(args: argparse.Namespace) -> int:
    page_ids = tuple(args.page_id or ())
    if page_ids and len(page_ids) != args.page_count:
        raise ValueError("--page-id count must equal --page-count.")
    pages = tuple(
        ArtifactPagePlan(
            page_number=index,
            artifact_page_id=page_ids[index - 1] if page_ids else None,
            page_kind="primary" if index == 1 else "continuation",
        )
        for index in range(1, args.page_count + 1)
    )
    result = prepare_artifact_pages(
        PrepareArtifactPagesRequest(
            class_id=args.class_id,
            activity_id=args.activity_id,
            artifact_instance_id=args.artifact_instance_id,
            template_version_id=args.template_version_id,
            artifact_category=args.artifact_category,
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
            pages=pages,
            expected_return_status=args.expected_return_status,
            privacy_policy=PrivacyPolicy(classification=args.privacy_classification),
            session_id=args.session_id,
            group_id=args.group_id,
        ),
        workspace_root=workspace_arg(args),
    )
    print_commit(result.commit)
    print(f"Artifact Instance: {result.artifact_instance_id}")
    print(f"Routes verified: {result.routes_verified}/{result.routes_expected}")
    for page in result.pages:
        print(
            f"{page.page_number}\t{page.artifact_page_id}\troute={page.route_id or '-'}"
        )
    return 0


def handle_list(args: argparse.Namespace) -> int:
    pages = list_artifact_pages(
        args.class_id, args.activity_id, workspace_root=workspace_arg(args)
    )
    if args.artifact_instance_id is not None:
        pages = tuple(
            page
            for page in pages
            if page.artifact_instance_id == args.artifact_instance_id
        )
    for page in pages:
        print(
            f"{page.artifact_instance_id}\t{page.page_number}\t"
            f"{page.artifact_page_id}\t{page.page_status}\t"
            f"route={page.route_id or '-'}\tsnapshot={page.snapshot_revision}"
        )
    if not pages:
        print("No Artifact Pages found.")
    return 0


def handle_show(args: argparse.Namespace) -> int:
    pages = list_artifact_pages(
        args.class_id, args.activity_id, workspace_root=workspace_arg(args)
    )
    page = next(
        (item for item in pages if item.artifact_page_id == args.artifact_page_id),
        None,
    )
    if page is None:
        raise ValueError(f"Artifact Page is unavailable: {args.artifact_page_id}")
    print(f"Artifact Instance: {page.artifact_instance_id}")
    print(f"Artifact Page: {page.artifact_page_id}")
    print(f"Page number: {page.page_number}")
    print(f"Kind: {page.page_kind}")
    print(f"Status: {page.page_status}")
    print(f"Route: {page.route_id or '-'}")
    print(f"Snapshot revision: {page.snapshot_revision}")
    return 0


def handle_render(args: argparse.Namespace) -> int:
    result = render_artifact_pages(
        RenderArtifactPagesRequest(
            class_id=args.class_id,
            activity_id=args.activity_id,
            artifact_instance_id=args.artifact_instance_id,
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
            output_relative_path=args.output,
        ),
        workspace_root=workspace_arg(args),
    )
    print_commit(result.commit)
    print(f"Rendered pages: {result.page_count}")
    print(f"Output: {result.output_path}")
    return 0


__all__ = [
    "handle_artifact_list",
    "handle_artifact_show",
    "handle_assemble",
    "handle_author_add",
    "handle_author_list",
    "handle_author_replace",
    "handle_author_show",
    "handle_author_update",
    "handle_list",
    "handle_prepare",
    "handle_render",
    "handle_show",
    "handle_subject_add",
    "handle_subject_list",
    "handle_subject_replace",
    "handle_subject_show",
    "handle_subject_update",
]
