"""Pure deterministic derivation for applying approved GroupPlans."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from uuid import UUID, uuid4

from pds_core.identifiers import IdentifierValidationError, validate_identifier

from concord.models import EffectiveContext, PlannedGroup
from concord.storage_serialization import canonical_json_bytes

GROUP_APPLICATION_DOMAIN = b"pds-concord:group-plan-application-group:v1\0"
MEMBERSHIP_APPLICATION_DOMAIN = (
    b"pds-concord:group-plan-application-membership:v1\0"
)
APPLICATION_PREVIEW_DOMAIN = b"pds-concord:group-plan-application-preview:v1\0"
APPLICATION_PREVIEW_RECORD_TYPE = "group_plan_application_preview_v1"


class GroupPlanApplicationError(ValueError):
    """Raised when pure GroupPlan application derivation is invalid."""


@dataclass(frozen=True, slots=True, kw_only=True)
class ApplicationGroupSpec:
    """One exact canonical Group proposed by an application preview."""

    planned_group_key: str
    group_id: str
    label: str
    description: str | None
    effective_context: EffectiveContext | None


@dataclass(frozen=True, slots=True, kw_only=True)
class ApplicationMembershipSpec:
    """One exact canonical Membership proposed by an application preview."""

    planned_group_key: str
    student_id: str
    membership_id: str
    group_id: str
    effective_context: EffectiveContext


def _identifier(value: str, field_name: str) -> str:
    try:
        return validate_identifier(value, field_name)
    except IdentifierValidationError as error:
        raise GroupPlanApplicationError(str(error)) from error


def new_application_id(
    *,
    uuid_factory: Callable[[], UUID] = uuid4,
) -> str:
    """Generate one fresh Core-valid application identity."""

    value = f"apply-{uuid_factory().hex}"
    _identifier(value, "application_id")
    return value


def derive_group_id(
    application_id: str,
    group_plan_id: str,
    planned_group_key: str,
) -> str:
    """Derive a fresh canonical Group ID in the application identity space."""

    application_id = _identifier(application_id, "application_id")
    group_plan_id = _identifier(group_plan_id, "group_plan_id")
    planned_group_key = _identifier(planned_group_key, "planned_group_key")
    payload = (
        GROUP_APPLICATION_DOMAIN
        + application_id.encode("utf-8")
        + b"\0"
        + group_plan_id.encode("utf-8")
        + b"\0"
        + planned_group_key.encode("utf-8")
    )
    value = "group-" + hashlib.sha256(payload).hexdigest()
    _identifier(value, "group_id")
    return value


def derive_membership_id(
    application_id: str,
    group_plan_id: str,
    planned_group_key: str,
    student_id: str,
) -> str:
    """Derive a fresh canonical Membership ID in the application identity space."""

    application_id = _identifier(application_id, "application_id")
    group_plan_id = _identifier(group_plan_id, "group_plan_id")
    planned_group_key = _identifier(planned_group_key, "planned_group_key")
    student_id = _identifier(student_id, "student_id")
    payload = (
        MEMBERSHIP_APPLICATION_DOMAIN
        + application_id.encode("utf-8")
        + b"\0"
        + group_plan_id.encode("utf-8")
        + b"\0"
        + planned_group_key.encode("utf-8")
        + b"\0"
        + student_id.encode("utf-8")
    )
    value = "membership-" + hashlib.sha256(payload).hexdigest()
    _identifier(value, "membership_id")
    return value


def derive_application_specs(
    *,
    application_id: str,
    group_plan_id: str,
    proposed_groups: tuple[PlannedGroup, ...],
    fallback_effective_context: EffectiveContext | None,
) -> tuple[tuple[ApplicationGroupSpec, ...], tuple[ApplicationMembershipSpec, ...]]:
    """Derive exact Group and Membership specs without performing I/O."""

    _identifier(application_id, "application_id")
    _identifier(group_plan_id, "group_plan_id")
    ordered = tuple(sorted(proposed_groups, key=lambda item: item.planned_group_key))
    keys = tuple(item.planned_group_key for item in ordered)
    if len(set(keys)) != len(keys):
        raise GroupPlanApplicationError(
            "proposed_groups must not duplicate planned_group_key."
        )
    needs_fallback = any(
        group.student_ids and group.effective_context is None for group in ordered
    )
    if needs_fallback and fallback_effective_context is None:
        raise GroupPlanApplicationError(
            "fallback_effective_context is required for a contextless nonempty "
            "PlannedGroup."
        )
    if not needs_fallback and fallback_effective_context is not None:
        raise GroupPlanApplicationError(
            "fallback_effective_context is not allowed when every nonempty "
            "PlannedGroup already has an Effective Context."
        )

    groups: list[ApplicationGroupSpec] = []
    memberships: list[ApplicationMembershipSpec] = []
    for group in ordered:
        group_id = derive_group_id(
            application_id,
            group_plan_id,
            group.planned_group_key,
        )
        groups.append(
            ApplicationGroupSpec(
                planned_group_key=group.planned_group_key,
                group_id=group_id,
                label=group.label,
                description=group.description,
                effective_context=group.effective_context,
            )
        )
        membership_context = group.effective_context or fallback_effective_context
        for student_id in sorted(group.student_ids):
            if membership_context is None:
                raise GroupPlanApplicationError(
                    "Membership Effective Context could not be resolved."
                )
            memberships.append(
                ApplicationMembershipSpec(
                    planned_group_key=group.planned_group_key,
                    student_id=student_id,
                    membership_id=derive_membership_id(
                        application_id,
                        group_plan_id,
                        group.planned_group_key,
                        student_id,
                    ),
                    group_id=group_id,
                    effective_context=membership_context,
                )
            )

    group_ids = tuple(item.group_id for item in groups)
    membership_ids = tuple(item.membership_id for item in memberships)
    if len(set(group_ids)) != len(group_ids):
        raise GroupPlanApplicationError("derived Group IDs must be unique.")
    if len(set(membership_ids)) != len(membership_ids):
        raise GroupPlanApplicationError("derived Membership IDs must be unique.")
    return tuple(groups), tuple(memberships)


def effective_context_to_dict(
    value: EffectiveContext | None,
) -> dict[str, object] | None:
    """Convert Effective Context into the exact JSON shape used by preview digests."""

    if value is None:
        return None
    return {
        "activity_id": value.activity_id,
        "session_ids": list(value.session_ids),
        "sequence_start": value.sequence_start,
        "sequence_end": value.sequence_end,
        "applies_to_remaining_activity": value.applies_to_remaining_activity,
    }


def build_application_manifest(
    *,
    application_id: str,
    class_id: str,
    activity_id: str,
    group_plan_id: str,
    group_plan_record_revision: int,
    expected_snapshot_revision: int,
    fallback_effective_context: EffectiveContext | None,
    groups: tuple[ApplicationGroupSpec, ...],
    memberships: tuple[ApplicationMembershipSpec, ...],
    unresolved_student_ids: tuple[str, ...],
) -> dict[str, object]:
    """Build one canonical JSON-native exact application manifest."""

    for identifier_value, field_name in (
        (application_id, "application_id"),
        (class_id, "class_id"),
        (activity_id, "activity_id"),
        (group_plan_id, "group_plan_id"),
    ):
        _identifier(identifier_value, field_name)
    for revision_value, field_name in (
        (group_plan_record_revision, "group_plan_record_revision"),
        (expected_snapshot_revision, "expected_snapshot_revision"),
    ):
        if type(revision_value) is not int or revision_value < 1:
            raise GroupPlanApplicationError(
                f"{field_name} must be a positive integer."
            )

    ordered_groups = tuple(sorted(groups, key=lambda item: item.planned_group_key))
    ordered_memberships = tuple(
        sorted(
            memberships,
            key=lambda item: (item.planned_group_key, item.student_id),
        )
    )
    return {
        "record_type": APPLICATION_PREVIEW_RECORD_TYPE,
        "application_id": application_id,
        "class_id": class_id,
        "activity_id": activity_id,
        "group_plan_id": group_plan_id,
        "group_plan_record_revision": group_plan_record_revision,
        "expected_snapshot_revision": expected_snapshot_revision,
        "fallback_effective_context": effective_context_to_dict(
            fallback_effective_context
        ),
        "resulting_group_plan_status": "applied",
        "unresolved_student_ids": sorted(unresolved_student_ids),
        "groups": [
            {
                "planned_group_key": item.planned_group_key,
                "group_id": item.group_id,
                "label": item.label,
                "status": "planned",
                "description": item.description,
                "effective_context": effective_context_to_dict(item.effective_context),
            }
            for item in ordered_groups
        ],
        "memberships": [
            {
                "planned_group_key": item.planned_group_key,
                "student_id": item.student_id,
                "membership_id": item.membership_id,
                "group_id": item.group_id,
                "status": "active",
                "effective_context": effective_context_to_dict(item.effective_context),
            }
            for item in ordered_memberships
        ],
    }


def application_digest(manifest: dict[str, object]) -> str:
    """Digest one exact application manifest under the frozen v1 domain."""

    return hashlib.sha256(
        APPLICATION_PREVIEW_DOMAIN + canonical_json_bytes(manifest)
    ).hexdigest()


__all__ = [
    "APPLICATION_PREVIEW_RECORD_TYPE",
    "ApplicationGroupSpec",
    "ApplicationMembershipSpec",
    "GroupPlanApplicationError",
    "application_digest",
    "build_application_manifest",
    "derive_application_specs",
    "derive_group_id",
    "derive_membership_id",
    "effective_context_to_dict",
    "new_application_id",
]
