"""Bounded naming primitives for Concord-owned generated output."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Sequence
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
    "build_generated_output_filename",
    "build_generated_output_token",
    "validate_generated_output_filename",
    "validate_generated_output_token",
]
