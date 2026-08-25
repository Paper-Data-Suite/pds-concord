"""Strict canonical serialization for reusable Concord Template contracts."""

from __future__ import annotations

import json
import types
from dataclasses import MISSING, fields, is_dataclass
from typing import (
    Any,
    Literal,
    TypeVar,
    Union,
    cast,
    get_args,
    get_origin,
    get_type_hints,
)

from concord.models import TemplateDefinition, TemplateVersion

T = TypeVar("T")
TemplateRecord = TemplateDefinition | TemplateVersion


class TemplateSerializationError(ValueError):
    """Reusable Template data is not strict canonical JSON."""


def canonical_json_bytes(value: object) -> bytes:
    """Serialize one JSON-compatible value deterministically."""
    try:
        text = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise TemplateSerializationError(
            f"value is not canonical JSON data: {error}"
        ) from error
    return (text + "\n").encode("utf-8")


def strict_json_loads(data: bytes, *, description: str = "JSON") -> object:
    """Parse strict UTF-8 JSON and reject duplicate keys/non-JSON constants."""

    def pairs_hook(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise TemplateSerializationError(
                    f"{description} contains duplicate object key {key!r}."
                )
            result[key] = value
        return result

    def reject_constant(value: str) -> object:
        raise TemplateSerializationError(
            f"{description} contains invalid JSON constant {value!r}."
        )

    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise TemplateSerializationError(
            f"{description} is not valid UTF-8."
        ) from error
    try:
        return json.loads(
            text,
            object_pairs_hook=pairs_hook,
            parse_constant=reject_constant,
        )
    except TemplateSerializationError:
        raise
    except json.JSONDecodeError as error:
        raise TemplateSerializationError(
            f"{description} is not valid JSON: {error}"
        ) from error


def dataclass_to_dict(value: object) -> dict[str, object]:
    """Convert one typed dataclass instance to canonical JSON-native values."""
    if not is_dataclass(value) or isinstance(value, type):
        raise TemplateSerializationError("value must be a dataclass instance.")
    encoded = _encode(value)
    if not isinstance(encoded, dict):
        raise TemplateSerializationError("dataclass did not encode to an object.")
    return cast(dict[str, object], encoded)


def dataclass_from_dict(cls: type[T], value: object) -> T:
    """Strictly construct one typed dataclass from a JSON object."""
    if not is_dataclass(cls):
        raise TemplateSerializationError("cls must be a dataclass type.")
    return cast(T, _decode(cls, value, cls.__name__))


def template_to_dict(record: TemplateRecord) -> dict[str, object]:
    """Return the exact mapping for one reusable Template record."""
    if not isinstance(record, (TemplateDefinition, TemplateVersion)):
        raise TemplateSerializationError(
            "record must be TemplateDefinition or TemplateVersion."
        )
    return dataclass_to_dict(record)


def template_from_dict(record_kind: str, value: object) -> TemplateRecord:
    """Strictly parse one reusable Template record body."""
    if record_kind == "template_definition":
        return dataclass_from_dict(TemplateDefinition, value)
    if record_kind == "template_version":
        return dataclass_from_dict(TemplateVersion, value)
    raise TemplateSerializationError(
        f"unsupported reusable Template record kind {record_kind!r}."
    )


def template_to_json_bytes(record: TemplateRecord) -> bytes:
    """Return deterministic canonical Template body bytes."""
    return canonical_json_bytes(template_to_dict(record))


def template_from_json_bytes(
    record_kind: str,
    data: bytes,
    *,
    description: str | None = None,
) -> TemplateRecord:
    """Parse canonical Template body bytes and reject noncanonical encoding."""
    label = description or f"{record_kind} JSON"
    value = strict_json_loads(data, description=label)
    record = template_from_dict(record_kind, value)
    if template_to_json_bytes(record) != data:
        raise TemplateSerializationError(f"{label} is not canonical.")
    return record


def _encode(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _encode(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_encode(item) for item in value]
    if isinstance(value, list):
        return [_encode(item) for item in value]
    if isinstance(value, dict):
        result: dict[str, object] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TemplateSerializationError(
                    "canonical JSON object keys must be strings."
                )
            result[key] = _encode(item)
        return result
    if value is None or type(value) in {str, int, bool, float}:
        return value
    raise TemplateSerializationError(
        f"unsupported canonical value type {type(value).__name__}."
    )


def _decode(annotation: object, value: object, path: str) -> object:
    if annotation is Any or annotation is object:
        return _decode_any(value, path)

    origin = get_origin(annotation)
    args = get_args(annotation)

    if origin is Literal:
        if value not in args:
            raise TemplateSerializationError(
                f"{path} must be one of {args!r}."
            )
        return value

    if origin in {Union, types.UnionType}:
        if value is None and type(None) in args:
            return None
        errors: list[str] = []
        for option in (item for item in args if item is not type(None)):
            try:
                return _decode(option, value, path)
            except TemplateSerializationError as error:
                errors.append(str(error))
        raise TemplateSerializationError(
            f"{path} does not match its declared union type: "
            + "; ".join(errors)
        )

    if origin is tuple:
        if not isinstance(value, list):
            raise TemplateSerializationError(f"{path} must be a JSON array.")
        if len(args) == 2 and args[1] is Ellipsis:
            return tuple(
                _decode(args[0], item, f"{path}[{index}]")
                for index, item in enumerate(value)
            )
        if len(args) != len(value):
            raise TemplateSerializationError(
                f"{path} must contain exactly {len(args)} values."
            )
        return tuple(
            _decode(item_type, item, f"{path}[{index}]")
            for index, (item_type, item) in enumerate(zip(args, value))
        )

    if origin is list:
        if not isinstance(value, list):
            raise TemplateSerializationError(f"{path} must be a JSON array.")
        item_type = args[0] if args else Any
        return [
            _decode(item_type, item, f"{path}[{index}]")
            for index, item in enumerate(value)
        ]

    if origin is dict:
        if not isinstance(value, dict):
            raise TemplateSerializationError(f"{path} must be a JSON object.")
        key_type = args[0] if args else str
        item_type = args[1] if len(args) > 1 else Any
        if key_type is not str:
            raise TemplateSerializationError(
                f"{path} uses unsupported non-string mapping keys."
            )
        result: dict[str, object] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TemplateSerializationError(
                    f"{path} object keys must be strings."
                )
            result[key] = _decode(item_type, item, f"{path}.{key}")
        return result

    if annotation is str:
        if not isinstance(value, str):
            raise TemplateSerializationError(f"{path} must be a string.")
        return value
    if annotation is bool:
        if type(value) is not bool:
            raise TemplateSerializationError(f"{path} must be a boolean.")
        return value
    if annotation is int:
        if type(value) is not int:
            raise TemplateSerializationError(f"{path} must be an integer.")
        return value
    if annotation is float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TemplateSerializationError(f"{path} must be a number.")
        return float(value)
    if annotation is type(None):
        if value is not None:
            raise TemplateSerializationError(f"{path} must be null.")
        return None

    if isinstance(annotation, type) and is_dataclass(annotation):
        if not isinstance(value, dict):
            raise TemplateSerializationError(f"{path} must be a JSON object.")
        model_fields = {field.name: field for field in fields(annotation)}
        actual = set(value)
        unknown = sorted(actual - set(model_fields))
        if unknown:
            raise TemplateSerializationError(
                f"{path} contains unknown field(s): {', '.join(unknown)}."
            )
        missing = sorted(
            name
            for name, field in model_fields.items()
            if name not in actual
            and field.default is MISSING
            and field.default_factory is MISSING
        )
        if missing:
            raise TemplateSerializationError(
                f"{path} is missing required field(s): {', '.join(missing)}."
            )
        hints = get_type_hints(annotation)
        kwargs: dict[str, object] = {}
        for name, raw in value.items():
            kwargs[name] = _decode(
                hints.get(name, Any),
                raw,
                f"{path}.{name}",
            )
        try:
            return annotation(**kwargs)
        except (TypeError, ValueError) as error:
            raise TemplateSerializationError(f"invalid {path}: {error}") from error

    raise TemplateSerializationError(
        f"{path} uses unsupported declared type {annotation!r}."
    )


def _decode_any(value: object, path: str) -> object:
    if value is None or type(value) in {str, int, bool, float}:
        return value
    if isinstance(value, list):
        return [
            _decode_any(item, f"{path}[{index}]")
            for index, item in enumerate(value)
        ]
    if isinstance(value, dict):
        result: dict[str, object] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TemplateSerializationError(
                    f"{path} object keys must be strings."
                )
            result[key] = _decode_any(item, f"{path}.{key}")
        return result
    raise TemplateSerializationError(
        f"{path} contains unsupported JSON value type {type(value).__name__}."
    )


__all__ = [
    "TemplateRecord",
    "TemplateSerializationError",
    "canonical_json_bytes",
    "dataclass_from_dict",
    "dataclass_to_dict",
    "strict_json_loads",
    "template_from_dict",
    "template_from_json_bytes",
    "template_to_dict",
    "template_to_json_bytes",
]
