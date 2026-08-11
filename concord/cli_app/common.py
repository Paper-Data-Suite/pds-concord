"""Shared parsing helpers for noninteractive Concord commands."""

from __future__ import annotations

import argparse
from pathlib import Path

from pds_core.standards import (
    StandardsLibrary,
    load_standards_library,
    standards_library_path,
)
from pds_core.workspace import resolve_workspace_root

from concord.models import (
    ConcordRecordReference,
    EffectiveContext,
    ParticipantReference,
)
from concord.workflows import WorkflowActor
from concord.workflows.participants import core_student_participant


def workflow_actor(args: argparse.Namespace) -> WorkflowActor:
    """Build explicit actor context from common mutating-command arguments."""
    return WorkflowActor(
        actor_id=args.actor_id,
        display_label=getattr(args, "actor_label", None),
        role_label=getattr(args, "actor_role", None),
    )


def effective_context(args: argparse.Namespace) -> EffectiveContext:
    """Build one explicit Effective Context from repeated Session arguments."""
    return EffectiveContext(
        activity_id=args.activity_id,
        session_ids=tuple(args.session_id),
        sequence_start=getattr(args, "sequence_start", None),
        sequence_end=getattr(args, "sequence_end", None),
        applies_to_remaining_activity=getattr(
            args, "applies_to_remaining_activity", False
        ),
    )


def load_command_standards_library(
    args: argparse.Namespace,
) -> StandardsLibrary | None:
    """Load an explicit or canonical Core standards library without creating it."""
    explicit_path = getattr(args, "standards_library", None)
    if explicit_path is not None:
        return load_standards_library(explicit_path)

    root = resolve_workspace_root(getattr(args, "workspace_root", None))
    canonical_path = standards_library_path(root)
    if canonical_path.is_file():
        return load_standards_library(canonical_path)
    return None


def student_participant(args: argparse.Namespace) -> ParticipantReference:
    """Resolve one Core-roster student for a direct Role/Responsibility command."""
    root = resolve_workspace_root(getattr(args, "workspace_root", None))
    return core_student_participant(root, args.class_id, args.student_id)


def group_assignee(group_id: str) -> ConcordRecordReference:
    """Build the native Concord Group reference used by Responsibilities."""
    return ConcordRecordReference(record_kind="group", record_id=group_id)


def workspace_arg(args: argparse.Namespace) -> str | Path | None:
    return getattr(args, "workspace_root", None)
