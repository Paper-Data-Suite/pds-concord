"""Bounded naming primitives for Concord-owned generated output."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections.abc import Sequence
from pathlib import PureWindowsPath
from typing import Final

GENERATED_OUTPUT_CONTRACT_VERSION: Final = "concord-generated-output-v1"
GENERATED_OUTPUT_TOKEN_PREFIX: Final = "cgo_"
GENERATED_OUTPUT_TOKEN_HEX_LENGTH: Final = 24
GENERATED_OUTPUT_TOKEN_LENGTH: Final = (
    len(GENERATED_OUTPUT_TOKEN_PREFIX) + GENERATED_OUTPUT_TOKEN_HEX_LENGTH
)
GENERATED_OUTPUT_EXTENSION_MAX_LENGTH: Final = 10
GENERATED_OUTPUT_FILENAME_MAX_LENGTH: Final = (
    GENERATED_OUTPUT_TOKEN_LENGTH + 1 + GENERATED_OUTPUT_EXTENSION_MAX_LENGTH
)
GENERATED_OUTPUT_DOMAIN_MAX_LENGTH: Final = 48

HUMAN_READABLE_OUTPUT_CONTRACT_VERSION: Final = (
    "concord-human-readable-output-v1"
)
HUMAN_READABLE_VISIBLE_STEM_MAX_BYTES: Final = 56
HUMAN_READABLE_DISAMBIGUATOR_HEX_LENGTH: Final = 10
HUMAN_READABLE_DISAMBIGUATOR_SEPARATOR: Final = "--"
HUMAN_READABLE_FILENAME_MAX_BYTES: Final = (
    HUMAN_READABLE_VISIBLE_STEM_MAX_BYTES
    + len(HUMAN_READABLE_DISAMBIGUATOR_SEPARATOR)
    + HUMAN_READABLE_DISAMBIGUATOR_HEX_LENGTH
    + 1
    + GENERATED_OUTPUT_EXTENSION_MAX_LENGTH
)

_DOMAIN_PATTERN: Final[re.Pattern[str]] = re.compile(
    rf"^[a-z][a-z0-9_-]{{0,{GENERATED_OUTPUT_DOMAIN_MAX_LENGTH - 1}}}$"
)
_EXTENSION_PATTERN: Final[re.Pattern[str]] = re.compile(
    rf"^\.[a-z0-9]{{1,{GENERATED_OUTPUT_EXTENSION_MAX_LENGTH}}}$"
)
_TOKEN_PATTERN: Final[re.Pattern[str]] = re.compile(
    rf"^{GENERATED_OUTPUT_TOKEN_PREFIX}"
    rf"[0-9a-f]{{{GENERATED_OUTPUT_TOKEN_HEX_LENGTH}}}$"
)
_FILENAME_PATTERN: Final[re.Pattern[str]] = re.compile(
    rf"^{GENERATED_OUTPUT_TOKEN_PREFIX}"
    rf"[0-9a-f]{{{GENERATED_OUTPUT_TOKEN_HEX_LENGTH}}}"
    rf"\.[a-z0-9]{{1,{GENERATED_OUTPUT_EXTENSION_MAX_LENGTH}}}$"
)
_HUMAN_DISAMBIGUATOR_PATTERN: Final[re.Pattern[str]] = re.compile(
    rf"^[0-9a-f]{{{HUMAN_READABLE_DISAMBIGUATOR_HEX_LENGTH}}}$"
)


class ConcordGeneratedPathError(ValueError):
    """A Concord-generated output name violates the bounded naming contract."""


def build_generated_output_token(
    *,
    domain: str,
    identity_parts: Sequence[str],
) -> str:
    """Return one deterministic, privacy-minimized, fixed-length output token."""
    checked_domain = _validate_domain(domain)
    checked_parts = _validate_identity_parts(identity_parts)

    digest = hashlib.sha256()
    _update_digest_component(digest, GENERATED_OUTPUT_CONTRACT_VERSION)
    _update_digest_component(digest, checked_domain)
    for part in checked_parts:
        _update_digest_component(digest, part)

    token = (
        GENERATED_OUTPUT_TOKEN_PREFIX
        + digest.hexdigest()[:GENERATED_OUTPUT_TOKEN_HEX_LENGTH]
    )
    if len(token) != GENERATED_OUTPUT_TOKEN_LENGTH:
        raise AssertionError("generated output token exceeded its fixed budget")
    return token


def build_generated_output_filename(
    *,
    domain: str,
    identity_parts: Sequence[str],
    extension: str,
) -> str:
    """Return one bounded opaque output filename with a validated extension."""
    checked_extension = _validate_extension(extension)
    filename = (
        build_generated_output_token(
            domain=domain,
            identity_parts=identity_parts,
        )
        + checked_extension
    )
    if len(filename) > GENERATED_OUTPUT_FILENAME_MAX_LENGTH:
        raise AssertionError("generated output filename exceeded its fixed budget")
    return filename


def build_human_readable_output_filename(
    *,
    display_label: str,
    domain: str,
    identity_parts: Sequence[str],
    extension: str,
) -> str:
    """Return a bounded readable filename with opaque identity disambiguation."""
    checked_label = _validate_human_display_label(display_label)
    checked_domain = _validate_domain(domain)
    checked_parts = _validate_identity_parts(identity_parts)
    checked_extension = _validate_extension(extension)

    visible = _sanitize_human_visible_stem(checked_label)
    visible = _truncate_utf8(
        visible,
        HUMAN_READABLE_VISIBLE_STEM_MAX_BYTES,
    ).rstrip("-")
    if not visible:
        raise ConcordGeneratedPathError(
            "display_label must contain at least one readable letter or number."
        )

    digest = hashlib.sha256()
    _update_digest_component(digest, HUMAN_READABLE_OUTPUT_CONTRACT_VERSION)
    _update_digest_component(digest, checked_domain)
    for part in checked_parts:
        _update_digest_component(digest, part)
    disambiguator = digest.hexdigest()[
        :HUMAN_READABLE_DISAMBIGUATOR_HEX_LENGTH
    ]

    filename = (
        visible
        + HUMAN_READABLE_DISAMBIGUATOR_SEPARATOR
        + disambiguator
        + checked_extension
    )
    if len(filename.encode("utf-8")) > HUMAN_READABLE_FILENAME_MAX_BYTES:
        raise AssertionError(
            "human-readable output filename exceeded its fixed byte budget"
        )
    return filename


def validate_generated_output_token(token: str) -> str:
    """Validate one exact token created by this naming contract."""
    if not isinstance(token, str) or _TOKEN_PATTERN.fullmatch(token) is None:
        raise ConcordGeneratedPathError(
            "generated output token does not match the bounded contract."
        )
    return token


def validate_generated_output_filename(filename: str) -> str:
    """Validate one exact opaque filename created by this naming contract."""
    if (
        not isinstance(filename, str)
        or _FILENAME_PATTERN.fullmatch(filename) is None
    ):
        raise ConcordGeneratedPathError(
            "generated output filename does not match the bounded contract."
        )
    if len(filename) > GENERATED_OUTPUT_FILENAME_MAX_LENGTH:
        raise ConcordGeneratedPathError(
            "generated output filename exceeds the fixed budget."
        )
    return filename


def validate_human_readable_output_filename(filename: str) -> str:
    """Validate one bounded human-readable filename from this contract."""
    if not isinstance(filename, str) or not filename:
        raise ConcordGeneratedPathError(
            "human-readable output filename must be nonempty text."
        )
    if (
        "/" in filename
        or "\\" in filename
        or "\x00" in filename
        or PureWindowsPath(filename).drive
    ):
        raise ConcordGeneratedPathError(
            "human-readable output filename must be one safe component."
        )
    try:
        encoded = filename.encode("utf-8")
    except UnicodeEncodeError as error:
        raise ConcordGeneratedPathError(
            "human-readable output filename must contain valid UTF-8 text."
        ) from error
    if len(encoded) > HUMAN_READABLE_FILENAME_MAX_BYTES:
        raise ConcordGeneratedPathError(
            "human-readable output filename exceeds the fixed byte budget."
        )

    stem, dot, suffix = filename.rpartition(".")
    if not dot:
        raise ConcordGeneratedPathError(
            "human-readable output filename requires a validated extension."
        )
    _validate_extension("." + suffix)

    visible, separator, disambiguator = stem.rpartition(
        HUMAN_READABLE_DISAMBIGUATOR_SEPARATOR
    )
    if (
        not separator
        or not visible
        or _HUMAN_DISAMBIGUATOR_PATTERN.fullmatch(disambiguator) is None
    ):
        raise ConcordGeneratedPathError(
            "human-readable output filename lacks bounded disambiguation."
        )
    if len(visible.encode("utf-8")) > HUMAN_READABLE_VISIBLE_STEM_MAX_BYTES:
        raise ConcordGeneratedPathError(
            "human-readable output visible stem exceeds the fixed byte budget."
        )
    if visible.startswith("-") or visible.endswith("-"):
        raise ConcordGeneratedPathError(
            "human-readable output visible stem has unsafe edge punctuation."
        )
    if any(not (character.isalnum() or character == "-") for character in visible):
        raise ConcordGeneratedPathError(
            "human-readable output visible stem contains unsafe characters."
        )
    return filename


def _validate_human_display_label(display_label: object) -> str:
    if not isinstance(display_label, str):
        raise ConcordGeneratedPathError("display_label must be text.")
    if any(
        unicodedata.category(character) in {"Cc", "Cf", "Cs", "Zl", "Zp"}
        for character in display_label
    ):
        raise ConcordGeneratedPathError(
            "display_label must not contain control or separator characters."
        )
    try:
        normalized = unicodedata.normalize("NFKC", display_label).strip()
        normalized.encode("utf-8")
    except (TypeError, UnicodeEncodeError) as error:
        raise ConcordGeneratedPathError(
            "display_label must contain valid UTF-8 text."
        ) from error
    if not normalized:
        raise ConcordGeneratedPathError("display_label must not be empty.")
    if (
        "/" in normalized
        or "\\" in normalized
        or "\x00" in normalized
        or PureWindowsPath(normalized).drive
        or normalized in {".", ".."}
    ):
        raise ConcordGeneratedPathError(
            "display_label must not be a path, traversal, or drive-qualified value."
        )
    return normalized


def _sanitize_human_visible_stem(display_label: str) -> str:
    pieces: list[str] = []
    last_was_separator = False
    for character in display_label:
        if character.isalnum():
            pieces.append(character)
            last_was_separator = False
            continue
        if not last_was_separator:
            pieces.append("-")
            last_was_separator = True
    return "".join(pieces).strip("-")


def _truncate_utf8(value: str, maximum_bytes: int) -> str:
    if len(value.encode("utf-8")) <= maximum_bytes:
        return value
    parts: list[str] = []
    used = 0
    for character in value:
        encoded = character.encode("utf-8")
        if used + len(encoded) > maximum_bytes:
            break
        parts.append(character)
        used += len(encoded)
    return "".join(parts)


def _validate_domain(domain: object) -> str:
    if not isinstance(domain, str) or _DOMAIN_PATTERN.fullmatch(domain) is None:
        raise ConcordGeneratedPathError(
            "domain must be a lowercase bounded generated-output namespace."
        )
    return domain


def _validate_identity_parts(identity_parts: object) -> tuple[str, ...]:
    if isinstance(identity_parts, (str, bytes)) or not isinstance(
        identity_parts,
        Sequence,
    ):
        raise ConcordGeneratedPathError(
            "identity_parts must be a nonempty sequence of strings."
        )
    checked = tuple(identity_parts)
    if not checked:
        raise ConcordGeneratedPathError(
            "identity_parts must contain at least one canonical value."
        )
    for part in checked:
        if not isinstance(part, str) or not part:
            raise ConcordGeneratedPathError(
                "identity_parts must contain nonempty strings."
            )
        try:
            part.encode("utf-8")
        except UnicodeEncodeError as error:
            raise ConcordGeneratedPathError(
                "identity_parts must contain valid UTF-8 text."
            ) from error
    return checked


def _validate_extension(extension: object) -> str:
    if (
        not isinstance(extension, str)
        or _EXTENSION_PATTERN.fullmatch(extension) is None
    ):
        raise ConcordGeneratedPathError(
            "extension must be a lowercase dot-prefixed alphanumeric suffix "
            "within the fixed budget."
        )
    return extension


def _update_digest_component(digest: object, value: str) -> None:
    encoded = value.encode("utf-8")
    length = len(encoded).to_bytes(8, "big")
    update = getattr(digest, "update")
    update(length)
    update(encoded)


__all__ = [
    "ConcordGeneratedPathError",
    "GENERATED_OUTPUT_CONTRACT_VERSION",
    "GENERATED_OUTPUT_DOMAIN_MAX_LENGTH",
    "GENERATED_OUTPUT_EXTENSION_MAX_LENGTH",
    "GENERATED_OUTPUT_FILENAME_MAX_LENGTH",
    "GENERATED_OUTPUT_TOKEN_HEX_LENGTH",
    "GENERATED_OUTPUT_TOKEN_LENGTH",
    "GENERATED_OUTPUT_TOKEN_PREFIX",
    "HUMAN_READABLE_DISAMBIGUATOR_HEX_LENGTH",
    "HUMAN_READABLE_DISAMBIGUATOR_SEPARATOR",
    "HUMAN_READABLE_FILENAME_MAX_BYTES",
    "HUMAN_READABLE_OUTPUT_CONTRACT_VERSION",
    "HUMAN_READABLE_VISIBLE_STEM_MAX_BYTES",
    "build_generated_output_filename",
    "build_generated_output_token",
    "build_human_readable_output_filename",
    "validate_generated_output_filename",
    "validate_generated_output_token",
    "validate_human_readable_output_filename",
]
