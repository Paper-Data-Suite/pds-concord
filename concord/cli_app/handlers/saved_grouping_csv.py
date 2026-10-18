"""Direct, optional CSV portability for teacher-owned saved class groupings."""

from __future__ import annotations

import argparse

from concord.cli_app.common import workflow_actor, workspace_arg
from concord.workflows.class_group_arrangement_csv import (
    CsvExportRequest,
    CsvImportRequest,
    export_csv_grouping,
    import_csv_grouping,
    prepare_csv_export,
    prepare_csv_import,
)


def _import_request(args: argparse.Namespace) -> CsvImportRequest:
    return CsvImportRequest(
        class_id=args.class_id,
        arrangement_id=args.arrangement_id,
        name=args.name,
        csv_path=args.csv_path,
        actor=workflow_actor(args),
        acknowledge_unresolved=args.acknowledge_unresolved,
    )


def _export_request(args: argparse.Namespace) -> CsvExportRequest:
    return CsvExportRequest(
        class_id=args.class_id,
        arrangement_id=args.arrangement_id,
        expected_revision=args.expected_revision,
        expected_sha256=args.expected_sha256,
        actor=workflow_actor(args),
    )


def handle_import_preview(args: argparse.Namespace) -> int:
    preview = prepare_csv_import(
        _import_request(args), workspace_root=workspace_arg(args)
    )
    print(f"Grouping: {preview.name}")
    print(f"New grouping ID: {preview.arrangement_id}")
    print(f"Groups: {len(preview.groups)}")
    print(f"Assigned students: {preview.assigned_count}")
    print(f"Unresolved students: {len(preview.unresolved_student_ids)}")
    print("CSV group keys become group labels; empty groups are not represented.")
    if preview.unresolved_student_ids:
        print("Import requires --acknowledge-unresolved.")
    print(f"Review digest: {preview.review_digest}")
    print("Writes: none")
    return 0


def handle_import(args: argparse.Namespace) -> int:
    result = import_csv_grouping(
        _import_request(args),
        review_digest=args.review_digest,
        workspace_root=workspace_arg(args),
    )
    print(f"Saved grouping: {result.revision.name}")
    print(f"Revision: {result.revision.revision}")
    print("Source Activities and Groups changed: no")
    return 0


def handle_export_preview(args: argparse.Namespace) -> int:
    preview = prepare_csv_export(
        _export_request(args), workspace_root=workspace_arg(args)
    )
    print(f"Grouping ID: {preview.arrangement_id}")
    print(f"Revision: {preview.arrangement_revision}")
    print(f"Assigned students to export: {preview.assigned_count}")
    print(f"Group count: {preview.group_count}")
    print(f"Omitted unresolved: {preview.omitted_unresolved_count}")
    print(f"Omitted empty groups: {preview.omitted_empty_group_count}")
    print("Friendly group labels/descriptions are not in student_id,group CSV.")
    print(f"Review digest: {preview.review_digest}")
    print("Writes: none; student IDs not printed")
    return 0


def handle_export(args: argparse.Namespace) -> int:
    if not args.authorize_roster_export:
        from concord.workflows.errors import ConcordWorkflowValidationError

        raise ConcordWorkflowValidationError(
            "Explicit --authorize-roster-export is required to write student IDs."
        )
    output = export_csv_grouping(
        _export_request(args),
        output_path=args.output_path,
        review_digest=args.review_digest,
        workspace_root=workspace_arg(args),
    )
    print(f"CSV created: {output}")
    print("Existing files overwritten: no")
    print("Keep the exported student roster file private.")
    return 0


__all__ = [
    "handle_export",
    "handle_export_preview",
    "handle_import",
    "handle_import_preview",
]
