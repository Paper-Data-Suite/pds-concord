from __future__ import annotations

import re

import pytest

from concord.generated_paths import (
    GENERATED_OUTPUT_DOMAIN_MAX_LENGTH,
    GENERATED_OUTPUT_EXTENSION_MAX_LENGTH,
    GENERATED_OUTPUT_FILENAME_MAX_LENGTH,
    GENERATED_OUTPUT_TOKEN_LENGTH,
    HUMAN_READABLE_DISAMBIGUATOR_HEX_LENGTH,
    HUMAN_READABLE_FILENAME_MAX_BYTES,
    HUMAN_READABLE_VISIBLE_STEM_MAX_BYTES,
    ConcordGeneratedPathError,
    build_generated_output_filename,
    build_generated_output_token,
    build_human_readable_output_filename,
    validate_generated_output_filename,
    validate_generated_output_token,
    validate_human_readable_output_filename,
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


def test_human_readable_filename_is_deterministic_bounded_and_valid() -> None:
    filename = build_human_readable_output_filename(
        display_label="Jane O'Connor — Feedback",
        domain="student-feedback",
        identity_parts=("class-1", "student-17", "activity-3"),
        extension=".pdf",
    )

    assert filename.startswith("Jane-O-Connor-Feedback--")
    assert filename.endswith(".pdf")
    assert len(filename.encode("utf-8")) <= HUMAN_READABLE_FILENAME_MAX_BYTES
    assert re.search(
        rf"--[0-9a-f]{{{HUMAN_READABLE_DISAMBIGUATOR_HEX_LENGTH}}}\.pdf$",
        filename,
    )
    assert validate_human_readable_output_filename(filename) == filename
    assert (
        filename
        == build_human_readable_output_filename(
            display_label="Jane O'Connor — Feedback",
            domain="student-feedback",
            identity_parts=("class-1", "student-17", "activity-3"),
            extension=".pdf",
        )
    )


def test_duplicate_display_names_are_collision_safe_without_raw_ids() -> None:
    first = build_human_readable_output_filename(
        display_label="Alex Smith",
        domain="student-feedback",
        identity_parts=("class-1", "student-private-001"),
        extension=".pdf",
    )
    second = build_human_readable_output_filename(
        display_label="Alex Smith",
        domain="student-feedback",
        identity_parts=("class-1", "student-private-002"),
        extension=".pdf",
    )

    assert first != second
    assert first.startswith("Alex-Smith--")
    assert second.startswith("Alex-Smith--")
    assert "student-private-001" not in first
    assert "student-private-002" not in second


def test_human_readable_domain_separation_changes_disambiguator() -> None:
    identity = ("class-1", "student-1")

    first = build_human_readable_output_filename(
        display_label="Alex Smith",
        domain="student-feedback",
        identity_parts=identity,
        extension=".pdf",
    )
    second = build_human_readable_output_filename(
        display_label="Alex Smith",
        domain="target-detail-report",
        identity_parts=identity,
        extension=".pdf",
    )

    assert first != second


def test_long_human_label_is_bounded_by_utf8_bytes() -> None:
    filename = build_human_readable_output_filename(
        display_label=("Álgebra " * 500) + "Reflection",
        domain="target-detail-report",
        identity_parts=("class-1", "target-1"),
        extension=".pdf",
    )
    visible = filename.rsplit("--", 1)[0]

    assert len(visible.encode("utf-8")) <= HUMAN_READABLE_VISIBLE_STEM_MAX_BYTES
    assert len(filename.encode("utf-8")) <= HUMAN_READABLE_FILENAME_MAX_BYTES
    assert filename.endswith(".pdf")


def test_unicode_normalization_is_deterministic() -> None:
    composed = build_human_readable_output_filename(
        display_label="Café Reflection",
        domain="target-detail-report",
        identity_parts=("class-1", "target-1"),
        extension=".pdf",
    )
    decomposed = build_human_readable_output_filename(
        display_label="Cafe\u0301 Reflection",
        domain="target-detail-report",
        identity_parts=("class-1", "target-1"),
        extension=".pdf",
    )

    assert composed == decomposed


@pytest.mark.parametrize(
    "display_label",
    (
        "",
        "   ",
        ".",
        "..",
        "../Alex",
        r"..\Alex",
        r"C:\Users\Alex",
        "C:Alex",
        "Alex\x00Smith",
        "\nAlex",
        "!!!",
    ),
)
def test_unsafe_or_unreadable_human_labels_are_rejected(
    display_label: str,
) -> None:
    with pytest.raises(ConcordGeneratedPathError, match="display_label"):
        build_human_readable_output_filename(
            display_label=display_label,
            domain="student-feedback",
            identity_parts=("class-1", "student-1"),
            extension=".pdf",
        )


@pytest.mark.parametrize(
    "filename",
    (
        "Alex Smith--0123456789.pdf",
        "Alex-Smith.pdf",
        "Alex-Smith--ABCDEF0123.pdf",
        "../Alex-Smith--0123456789.pdf",
        "Alex-Smith--0123456789.PDF",
    ),
)
def test_noncontract_human_readable_filenames_are_rejected(
    filename: str,
) -> None:
    with pytest.raises(ConcordGeneratedPathError):
        validate_human_readable_output_filename(filename)


def test_human_filename_extension_still_uses_shared_extension_contract() -> None:
    with pytest.raises(ConcordGeneratedPathError, match="extension"):
        build_human_readable_output_filename(
            display_label="Alex Smith",
            domain="student-feedback",
            identity_parts=("class-1", "student-1"),
            extension=".tar.gz",
        )
