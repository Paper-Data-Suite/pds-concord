from __future__ import annotations

import re

import pytest

from concord.generated_paths import (
    GENERATED_OUTPUT_DOMAIN_MAX_LENGTH,
    GENERATED_OUTPUT_EXTENSION_MAX_LENGTH,
    GENERATED_OUTPUT_FILENAME_MAX_LENGTH,
    GENERATED_OUTPUT_TOKEN_LENGTH,
    ConcordGeneratedPathError,
    build_generated_output_filename,
    build_generated_output_token,
    validate_generated_output_filename,
    validate_generated_output_token,
)


def test_generated_output_token_is_exact_deterministic_and_bounded() -> None:
    token = build_generated_output_token(
        domain="activity-score-analysis",
        identity_parts=("class-1", "activity-1", "revision-7"),
    )

    assert token == "cgo_6634186e4b34ec833a159651"
    assert len(token) == GENERATED_OUTPUT_TOKEN_LENGTH == 28
    assert re.fullmatch(r"cgo_[0-9a-f]{24}", token)
    assert validate_generated_output_token(token) == token


def test_domain_separation_changes_the_token() -> None:
    identity = ("class-1", "activity-1")

    first = build_generated_output_token(
        domain="packet-render",
        identity_parts=identity,
    )
    second = build_generated_output_token(
        domain="activity-score-analysis",
        identity_parts=identity,
    )

    assert first != second


def test_length_prefixing_keeps_identity_tuples_unambiguous() -> None:
    first = build_generated_output_token(
        domain="packet-render",
        identity_parts=("ab", "c"),
    )
    second = build_generated_output_token(
        domain="packet-render",
        identity_parts=("a", "bc"),
    )

    assert first != second


def test_long_semantic_values_do_not_expand_generated_leaf() -> None:
    short = build_generated_output_filename(
        domain="packet-render",
        identity_parts=("packet-1",),
        extension=".pdf",
    )
    long = build_generated_output_filename(
        domain="packet-render",
        identity_parts=("packet-" + ("x" * 20_000),),
        extension=".pdf",
    )

    assert len(short) == len(long)
    assert len(long) <= GENERATED_OUTPUT_FILENAME_MAX_LENGTH
    assert long.endswith(".pdf")


def test_generated_filename_uses_fixed_token_and_bounded_extension() -> None:
    filename = build_generated_output_filename(
        domain="activity-score-analysis",
        identity_parts=("class-1", "activity-1", "snapshot-42"),
        extension=".json",
    )

    assert filename.startswith("cgo_")
    assert filename.endswith(".json")
    assert len(filename) <= GENERATED_OUTPUT_FILENAME_MAX_LENGTH
    assert validate_generated_output_filename(filename) == filename


@pytest.mark.parametrize(
    "domain",
    (
        "",
        "Packet",
        "packet.render",
        "../packet",
        "x" * (GENERATED_OUTPUT_DOMAIN_MAX_LENGTH + 1),
    ),
)
def test_invalid_domains_are_rejected(domain: str) -> None:
    with pytest.raises(ConcordGeneratedPathError, match="domain"):
        build_generated_output_token(
            domain=domain,
            identity_parts=("packet-1",),
        )


@pytest.mark.parametrize(
    "identity_parts",
    (
        (),
        ("",),
        ("good", ""),
        "not-a-sequence-of-parts",
        b"bytes-are-not-parts",
    ),
)
def test_invalid_identity_parts_are_rejected(identity_parts: object) -> None:
    with pytest.raises(ConcordGeneratedPathError, match="identity_parts"):
        build_generated_output_token(
            domain="packet-render",
            identity_parts=identity_parts,  # type: ignore[arg-type]
        )


def test_invalid_unicode_identity_part_is_rejected() -> None:
    with pytest.raises(ConcordGeneratedPathError, match="UTF-8"):
        build_generated_output_token(
            domain="packet-render",
            identity_parts=("\ud800",),
        )


@pytest.mark.parametrize(
    "extension",
    (
        "",
        "pdf",
        ".PDF",
        "../pdf",
        ".tar.gz",
        "." + ("x" * (GENERATED_OUTPUT_EXTENSION_MAX_LENGTH + 1)),
    ),
)
def test_invalid_extensions_are_rejected(extension: str) -> None:
    with pytest.raises(ConcordGeneratedPathError, match="extension"):
        build_generated_output_filename(
            domain="packet-render",
            identity_parts=("packet-1",),
            extension=extension,
        )


@pytest.mark.parametrize(
    "value",
    (
        "packet-1.pdf",
        "cgo_ABCDEF0123456789abcdef01.pdf",
        "cgo_1234.pdf",
        "cgo_0123456789abcdef01234567",
        "../cgo_0123456789abcdef01234567.pdf",
    ),
)
def test_noncontract_generated_filenames_are_rejected(value: str) -> None:
    with pytest.raises(ConcordGeneratedPathError):
        validate_generated_output_filename(value)


def test_filename_maximum_tracks_the_extension_budget() -> None:
    filename = build_generated_output_filename(
        domain="packet-render",
        identity_parts=("packet-1",),
        extension="." + ("x" * GENERATED_OUTPUT_EXTENSION_MAX_LENGTH),
    )

    assert len(filename) == GENERATED_OUTPUT_FILENAME_MAX_LENGTH
