import pytest

from scripts.check_documentation import (
    CONTRACT_DRAFT_STATUS,
    CONTRACT_STATUS,
    EXAMPLE_DRAFT_STATUS,
    EXAMPLE_STATUS,
    PROPOSED_CHAIN,
    check_documentation,
    status_failures,
)


def test_documentation_integrity() -> None:
    check_documentation()


def test_completed_document_status_is_accepted() -> None:
    assert (
        status_failures(
            CONTRACT_STATUS,
            label="contracts",
            required=CONTRACT_STATUS,
            forbidden=(CONTRACT_DRAFT_STATUS,),
        )
        == []
    )


@pytest.mark.parametrize(
    ("text", "required", "forbidden", "expected"),
    [
        (
            CONTRACT_DRAFT_STATUS,
            CONTRACT_STATUS,
            (CONTRACT_DRAFT_STATUS,),
            "must contain completed status",
        ),
        (
            f"{CONTRACT_STATUS}\n{CONTRACT_DRAFT_STATUS}",
            CONTRACT_STATUS,
            (CONTRACT_DRAFT_STATUS,),
            "stale active wording",
        ),
        (
            EXAMPLE_DRAFT_STATUS,
            EXAMPLE_STATUS,
            (EXAMPLE_DRAFT_STATUS, PROPOSED_CHAIN),
            "must contain completed status",
        ),
        (
            f"{EXAMPLE_STATUS}\n{PROPOSED_CHAIN}",
            EXAMPLE_STATUS,
            (EXAMPLE_DRAFT_STATUS, PROPOSED_CHAIN),
            "stale active wording",
        ),
    ],
)
def test_stale_document_status_is_rejected(
    text: str, required: str, forbidden: tuple[str, ...], expected: str
) -> None:
    failures = status_failures(
        text,
        label="document",
        required=required,
        forbidden=forbidden,
    )
    assert any(expected in failure for failure in failures)
