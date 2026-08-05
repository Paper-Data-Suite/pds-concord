"""Exact JSON-native conversion for Concord record bodies."""

from __future__ import annotations

import math
import types
from dataclasses import MISSING, fields, is_dataclass
from typing import Any, cast, get_args, get_origin, get_type_hints

from concord.models import (
    Activity,
    ArtifactAuthor,
    ArtifactInstance,
    ArtifactPage,
    ArtifactReview,
    ArtifactSubject,
    ConcordModelError,
    CorrectionRecord,
    Criterion,
    CriterionSet,
    Group,
    GroupMembership,
    ModerationRecord,
    ResponsibilityAssignment,
    RoleAssignment,
    ScoreEvidenceLink,
    ScoreRecord,
    ScoringScale,
    Session,
)
from concord.record_registry import CONVERSION_KIND_ALIASES, RECORD_DESCRIPTORS

Record = (
    Activity
    | Session
    | Group
    | GroupMembership
    | RoleAssignment
    | ResponsibilityAssignment
    | ArtifactInstance
    | ArtifactPage
    | ArtifactAuthor
    | ArtifactSubject
    | ArtifactReview
    | ModerationRecord
    | CriterionSet
    | Criterion
    | ScoringScale
    | ScoreRecord
    | ScoreEvidenceLink
    | CorrectionRecord
)

RECORD_KIND_REGISTRY: dict[str, type[Record]] = {
    descriptor.kind: cast(type[Record], descriptor.model_type)
    for descriptor in RECORD_DESCRIPTORS
}
RECORD_KIND_REGISTRY.update(
    {
        alias: RECORD_KIND_REGISTRY[canonical]
        for alias, canonical in CONVERSION_KIND_ALIASES.items()
    }
)


def record_to_dict(record: Record) -> dict[str, Any]:
    """Convert one supported record to an independent JSON-native mapping."""
    if type(record) not in RECORD_KIND_REGISTRY.values():
        raise ConcordModelError("record is not a registered Concord record type.")
    result = _to_json(record)
    assert isinstance(result, dict)
    return result


def record_from_dict(record_kind: str, data: object) -> Record:
    """Construct one record from an exact mapping, rejecting schema drift."""
    if not isinstance(record_kind, str) or record_kind not in RECORD_KIND_REGISTRY:
        raise ConcordModelError(f"unsupported record_kind {record_kind!r}.")
    if not isinstance(data, dict) or any(not isinstance(key, str) for key in data):
        raise ConcordModelError("record data must be a mapping with string keys.")
    return cast(Record, _from_mapping(RECORD_KIND_REGISTRY[record_kind], data))


def _to_json(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ConcordModelError("serialized numeric values must be finite.")
        return value
    if isinstance(value, tuple):
        return [_to_json(item) for item in value]
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _to_json(getattr(value, field.name))
            for field in fields(value)
            if getattr(value, field.name) is not None
        }
    raise ConcordModelError(f"value of type {type(value).__name__} is not JSON-native.")


def _from_mapping(cls: type[Any], data: dict[str, Any]) -> Any:
    model_fields = {field.name: field for field in fields(cls)}
    unknown = sorted(set(data) - set(model_fields))
    if unknown:
        raise ConcordModelError(
            f"unknown field(s) for {cls.__name__}: {', '.join(unknown)}."
        )
    missing = sorted(
        name
        for name, field in model_fields.items()
        if field.default is MISSING
        and field.default_factory is MISSING
        and name not in data
    )
    if missing:
        raise ConcordModelError(
            f"missing required field(s) for {cls.__name__}: {', '.join(missing)}."
        )
    hints = get_type_hints(cls)
    kwargs = {name: _parse_value(data[name], hints[name], name) for name in data}
    try:
        return cls(**kwargs)
    except ConcordModelError:
        raise
    except (TypeError, ValueError) as error:
        raise ConcordModelError(str(error)) from error


def _parse_value(value: Any, annotation: Any, field_path: str) -> Any:
    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin is tuple:
        if not isinstance(value, list):
            raise ConcordModelError(f"{field_path} must be a JSON array.")
        item_type = args[0]
        return tuple(
            _parse_value(item, item_type, f"{field_path}[{index}]")
            for index, item in enumerate(value)
        )
    if origin in (types.UnionType, getattr(__import__("typing"), "Union")):
        if value is None and type(None) in args:
            return None
        candidates = tuple(
            candidate for candidate in args if candidate is not type(None)
        )
        if isinstance(value, dict):
            matching = [
                candidate
                for candidate in candidates
                if isinstance(candidate, type)
                and is_dataclass(candidate)
                and _keys_fit(candidate, value)
            ]
            if len(matching) == 1:
                return _from_mapping(matching[0], value)
        errors: list[Exception] = []
        for candidate in candidates:
            try:
                return _parse_value(value, candidate, field_path)
            except (ConcordModelError, TypeError, ValueError) as error:
                errors.append(error)
        raise ConcordModelError(f"{field_path} does not match any permitted type.")
    if annotation is Any:
        return value
    if annotation is bool:
        if type(value) is not bool:
            raise ConcordModelError(f"{field_path} must be a boolean.")
        return value
    if annotation is int:
        if type(value) is not int:
            raise ConcordModelError(f"{field_path} must be an integer.")
        return value
    if annotation is float:
        if type(value) is not float or not math.isfinite(value):
            raise ConcordModelError(f"{field_path} must be a finite float.")
        return value
    if annotation is str:
        if type(value) is not str:
            raise ConcordModelError(f"{field_path} must be a string.")
        return value
    if isinstance(annotation, type) and is_dataclass(annotation):
        if not isinstance(value, dict) or any(
            not isinstance(key, str) for key in value
        ):
            raise ConcordModelError(f"{field_path} must be an object.")
        return _from_mapping(annotation, value)
    raise ConcordModelError(f"unsupported conversion annotation for {field_path}.")


def _keys_fit(cls: type[Any], data: dict[str, Any]) -> bool:
    model_fields = {field.name: field for field in fields(cls)}
    required = {
        name
        for name, field in model_fields.items()
        if field.default is MISSING and field.default_factory is MISSING
    }
    return set(data) <= set(model_fields) and required <= set(data)


__all__ = ["RECORD_KIND_REGISTRY", "record_from_dict", "record_to_dict"]
