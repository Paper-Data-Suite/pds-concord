"""Direct Artifact Review and evidence Moderation commands."""

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
    CorePublicationReference,
    EvidenceReference,
    PrivacyPolicy,
    SubjectReference,
)
from concord.workflows import (
    AddArtifactReviewRequest,
    AddModerationRecordRequest,
    ReplaceArtifactReviewRequest,
    ReplaceModerationRecordRequest,
    add_artifact_review,
    add_moderation_record,
    list_artifact_reviews,
    list_moderation_records,
    replace_artifact_review,
    replace_moderation_record,
    show_artifact_review,
    show_moderation_record,
)


def _usage(args: argparse.Namespace, message: str) -> NoReturn:
    parser = getattr(args, "command_parser", None)
    if isinstance(parser, argparse.ArgumentParser):
        parser.error(message)
    raise ValueError(message)


def _privacy(value: str) -> PrivacyPolicy:
    return PrivacyPolicy(classification=value)


def _target_subject(
    value: str,
    args: argparse.Namespace,
) -> SubjectReference:
    parts = value.split(",")
    if len(parts) not in {3, 4} or any(not part for part in parts):
        _usage(
            args,
            "--target-subject must use KIND,OWNER,ID[,CONTRACT_VERSION].",
        )
    kind, owner, subject_id = parts[:3]
    contract_version = parts[3] if len(parts) == 4 else None
    return SubjectReference(
        subject_kind=kind,
        owning_system=owner,
        subject_id=subject_id,
        contract_version=contract_version,
    )


def _evidence_reference(args: argparse.Namespace) -> EvidenceReference:
    publication_id = getattr(args, "source_publication_id", None)
    schema_version = getattr(args, "source_publication_schema_version", None)
    if schema_version is not None and publication_id is None:
        _usage(
            args,
            "--source-publication-schema-version requires "
            "--source-publication-id.",
        )
    publication = (
        None
        if publication_id is None
        else CorePublicationReference(
            publication_id=publication_id,
            publication_schema_version=schema_version,
        )
    )
    return EvidenceReference(
        evidence_kind=args.evidence_kind,
        owning_system=args.evidence_owner,
        record_id=args.evidence_record_id,
        contract_version=args.evidence_contract_version,
        source_publication_reference=publication,
        immutable_source_version=args.immutable_source_version,
        moderation_requirement=args.evidence_moderation_requirement,
    )


def _subjects(args: argparse.Namespace) -> tuple[SubjectReference, ...]:
    return tuple(
        _target_subject(value, args) for value in (args.target_subject or ())
    )


def handle_review_add(args: argparse.Namespace) -> int:
    result = add_artifact_review(
        AddArtifactReviewRequest(
            class_id=args.class_id,
            activity_id=args.activity_id,
            artifact_instance_id=args.artifact_instance_id,
            artifact_review_id=args.artifact_review_id,
            readability_judgment=args.readability_judgment,
            page_completeness_judgment=args.page_completeness_judgment,
            filing_judgment=args.filing_judgment,
            author_judgment=args.author_judgment,
            subject_judgment=args.subject_judgment,
            privacy_judgment=args.privacy_judgment,
            relevance_judgment=args.relevance_judgment,
            moderation_requirement=args.moderation_requirement,
            scoring_readiness=args.scoring_readiness,
            review_outcome=args.review_outcome,
            notes=args.notes,
            privacy_policy=_privacy(args.privacy_classification),
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
        ),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print_commit(result.commit)
    print(f"Artifact Review: {result.artifact_review_id}")
    return 0


def handle_review_list(args: argparse.Namespace) -> int:
    reviews = list_artifact_reviews(
        args.class_id,
        args.activity_id,
        artifact_instance_id=args.artifact_instance_id,
        include_historical=args.include_historical,
        workspace_root=workspace_arg(args),
    )
    for item in reviews:
        state = "current" if item.is_current else "historical"
        reviewer = item.reviewer_display_label or "-"
        print(
            f"{item.artifact_review_id}\t{item.artifact_instance_id}\t"
            f"{item.review_outcome}\t{item.scoring_readiness}\t"
            f"moderation={item.moderation_requirement}\t"
            f"reviewer={reviewer}\t{state}\t"
            f"snapshot={item.snapshot_revision}"
        )
    if not reviews:
        print("No Artifact Reviews found.")
    return 0


def handle_review_show(args: argparse.Namespace) -> int:
    item = show_artifact_review(
        args.class_id,
        args.activity_id,
        args.artifact_review_id,
        workspace_root=workspace_arg(args),
    )
    print(f"Artifact Review: {item.artifact_review_id}")
    print(f"Artifact: {item.artifact_instance_id}")
    print(f"Reviewer: {item.reviewer_display_label or '-'}")
    print(f"Reviewed at: {item.reviewed_at}")
    print(f"Readability: {item.readability_judgment}")
    print(f"Page completeness: {item.page_completeness_judgment}")
    print(f"Filing: {item.filing_judgment}")
    print(f"Author judgment: {item.author_judgment}")
    print(f"Subject judgment: {item.subject_judgment}")
    print(f"Privacy judgment: {item.privacy_judgment}")
    print(f"Relevance: {item.relevance_judgment}")
    print(f"Moderation requirement: {item.moderation_requirement}")
    print(f"Scoring readiness: {item.scoring_readiness}")
    print(f"Outcome: {item.review_outcome}")
    print(f"Notes: {item.notes or '-'}")
    print(f"Review privacy: {item.privacy_policy.classification}")
    print(f"Current: {'yes' if item.is_current else 'no'}")
    print(f"Snapshot revision: {item.snapshot_revision}")
    return 0


def handle_review_replace(args: argparse.Namespace) -> int:
    result = replace_artifact_review(
        ReplaceArtifactReviewRequest(
            class_id=args.class_id,
            activity_id=args.activity_id,
            artifact_review_id=args.artifact_review_id,
            replacement_artifact_review_id=args.replacement_artifact_review_id,
            correction_id=args.correction_id,
            reason=args.reason,
            readability_judgment=args.readability_judgment,
            page_completeness_judgment=args.page_completeness_judgment,
            filing_judgment=args.filing_judgment,
            author_judgment=args.author_judgment,
            subject_judgment=args.subject_judgment,
            privacy_judgment=args.privacy_judgment,
            relevance_judgment=args.relevance_judgment,
            moderation_requirement=args.moderation_requirement,
            scoring_readiness=args.scoring_readiness,
            review_outcome=args.review_outcome,
            notes=args.notes,
            privacy_policy=_privacy(args.privacy_classification),
            correction_privacy_policy=_privacy(
                args.correction_privacy_classification
            ),
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
        ),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print_commit(result.commit)
    print(f"Replacement Artifact Review: {result.artifact_review_id}")
    return 0


def handle_moderation_add(args: argparse.Namespace) -> int:
    result = add_moderation_record(
        AddModerationRecordRequest(
            class_id=args.class_id,
            activity_id=args.activity_id,
            moderation_record_id=args.moderation_record_id,
            target_evidence_reference=_evidence_reference(args),
            target_subject_references=_subjects(args),
            status=args.status,
            permitted_use=args.permitted_use,
            rationale=args.rationale,
            qualification=args.qualification,
            privacy_policy=_privacy(args.privacy_classification),
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
        ),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print_commit(result.commit)
    print(f"Moderation Record: {result.moderation_record_id}")
    return 0


def handle_moderation_list(args: argparse.Namespace) -> int:
    records = list_moderation_records(
        args.class_id,
        args.activity_id,
        include_historical=args.include_historical,
        workspace_root=workspace_arg(args),
    )
    for item in records:
        evidence = item.evidence_reference
        state = "current" if item.is_current else "historical"
        subjects = ",".join(
            f"{subject.subject_kind}:{subject.subject_id}"
            for subject in item.target_subject_references
        )
        print(
            f"{item.moderation_record_id}\t"
            f"{evidence.owning_system}:{evidence.evidence_kind}:"
            f"{evidence.record_id}\t"
            f"subjects={subjects or '-'}\t{item.status}\t"
            f"{item.permitted_use}\t{state}\t"
            f"snapshot={item.snapshot_revision}"
        )
    if not records:
        print("No Moderation Records found.")
    return 0


def handle_moderation_show(args: argparse.Namespace) -> int:
    detail = show_moderation_record(
        args.class_id,
        args.activity_id,
        args.moderation_record_id,
        workspace_root=workspace_arg(args),
    )
    item = detail.summary
    evidence = item.evidence_reference
    print(f"Moderation Record: {item.moderation_record_id}")
    print(
        "Evidence: "
        f"{evidence.owning_system}:{evidence.evidence_kind}:"
        f"{evidence.record_id}"
    )
    print(f"Evidence contract: {evidence.contract_version or '-'}")
    print(f"Immutable source version: {evidence.immutable_source_version or '-'}")
    publication = evidence.source_publication_reference
    print(
        "Source publication: "
        f"{publication.publication_id if publication is not None else '-'}"
    )
    print(f"Moderator: {item.moderator_display_label or '-'}")
    print(f"Moderated at: {item.moderated_at}")
    for subject in item.target_subject_references:
        print(
            "Target Subject: "
            f"{subject.subject_kind},{subject.owning_system},"
            f"{subject.subject_id}"
        )
    if not item.target_subject_references:
        print("Target Subjects: -")
    print(f"Status: {item.status}")
    print(f"Permitted use: {item.permitted_use}")
    print(f"Qualification: {item.qualification or '-'}")
    print(f"Rationale: {detail.rationale}")
    print(f"Moderation privacy: {item.privacy_policy.classification}")
    print(f"Current: {'yes' if item.is_current else 'no'}")
    print(f"Snapshot revision: {item.snapshot_revision}")
    return 0


def handle_moderation_replace(args: argparse.Namespace) -> int:
    result = replace_moderation_record(
        ReplaceModerationRecordRequest(
            class_id=args.class_id,
            activity_id=args.activity_id,
            moderation_record_id=args.moderation_record_id,
            replacement_moderation_record_id=args.replacement_moderation_record_id,
            correction_id=args.correction_id,
            reason=args.reason,
            target_evidence_reference=_evidence_reference(args),
            target_subject_references=_subjects(args),
            status=args.status,
            permitted_use=args.permitted_use,
            rationale=args.rationale,
            qualification=args.qualification,
            privacy_policy=_privacy(args.privacy_classification),
            correction_privacy_policy=_privacy(
                args.correction_privacy_classification
            ),
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
        ),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print_commit(result.commit)
    print(f"Replacement Moderation Record: {result.moderation_record_id}")
    return 0


__all__ = [
    "handle_moderation_add",
    "handle_moderation_list",
    "handle_moderation_replace",
    "handle_moderation_show",
    "handle_review_add",
    "handle_review_list",
    "handle_review_replace",
    "handle_review_show",
]
