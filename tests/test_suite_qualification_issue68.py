from __future__ import annotations

from pathlib import Path


def test_package_checker_requires_readiness_provider() -> None:
    text = Path("scripts/check_package.py").read_text(encoding="utf-8")
    assert '"concord/readiness_provider.py"' in text
    assert '"paper-data-suite"' in text


def test_installed_smoke_qualifies_both_operations_capabilities() -> None:
    text = Path("scripts/smoke_test_attention_provider_wheel.py").read_text(
        encoding="utf-8"
    )
    assert "profile.attention_provider is not None" in text
    assert "profile.readiness_provider is not None" in text
    assert '"concord_readiness_unavailable"' in text
    assert '"concord_class_not_ready"' in text
    assert 'concord_console_entries[0].value == "concord.cli:main"' in text
    assert "_run_with_input([str(concord)], work" in text
    assert '"paper-data-suite"' in text
    assert '"0.6.3"' in text


def test_normative_interoperability_doc_records_required_boundaries() -> None:
    text = Path("docs/v0.3.0-suite-interoperability.md").read_text(
        encoding="utf-8"
    )
    for phrase in (
        "readiness != attention",
        "readiness_provider = present",
        "attention_provider = present",
        "concord_readiness_unavailable",
        "concord_class_not_ready",
        "module_operations.provider_failed",
        "module_operations.result_invalid",
        "concord = concord.cli:main",
        "handle_concord_route",
        "dispatch_routes",
        "Paper Data Suite v0.1.0",
        "pds-core>=0.6.3,<0.7",
    ):
        assert phrase in text


def test_active_docs_expose_issue68_without_moving_suite_ownership() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    cli = Path("docs/cli-contract.md").read_text(encoding="utf-8")
    attention = Path(
        "docs/v0.3.0-activity-attention-next-actions.md"
    ).read_text(encoding="utf-8")

    assert "Suite interoperability and structural readiness" in readme
    assert "v0.3.0-suite-interoperability.md" in readme
    assert "issue #68" in cli.lower()
    assert "readiness != attention" in cli
    assert "readiness_provider = present" in attention
    assert "Issue #67 originally left `readiness_provider = None`" in attention


def test_documentation_validator_requires_issue68_doc() -> None:
    text = Path("scripts/check_documentation.py").read_text(encoding="utf-8")
    assert "SUITE_INTEROPERABILITY_DOC" in text
    assert "REQUIRED_SUITE_INTEROPERABILITY_PHRASES" in text
    assert "v0.3.0-suite-interoperability.md" in text


def test_repository_validator_reuses_installed_operations_smoke() -> None:
    text = Path("scripts/validate_repository.py").read_text(encoding="utf-8")
    assert "scripts/smoke_test_attention_provider_wheel.py" in text


def test_docs_index_and_changelog_record_issue68() -> None:
    docs_index = Path("docs/README.md").read_text(encoding="utf-8")
    changelog = Path("CHANGELOG.md").read_text(encoding="utf-8")

    assert "v0.3.0-suite-interoperability.md" in docs_index
    assert "structural readiness" in changelog
    assert "Issue #68" in changelog
