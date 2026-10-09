"""Core 0.6.5 producer reader metadata for Concord Issue #129."""

from __future__ import annotations

import builtins
import tomllib
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest
from packaging.requirements import Requirement
from pds_core.academic_work_registrations import (
    ACADEMIC_WORK_REGISTRATION_RECORD_TYPE,
    ACADEMIC_WORK_REGISTRATION_SCHEMA_VERSION,
    AcademicWorkRegistration,
)
from pds_core.publication_compatibility import (
    PublicationProducerRegistry,
    PublicationReaderSupport,
    evaluate_publication_compatibility,
    lookup_publication_reader_support,
    validate_publication_producer_profile,
)
from pds_core.publication_records import (
    PUBLICATION_RECORD_SCHEMA_VERSION,
    PUBLICATION_RECORD_TYPE,
    PublicationRecord,
)
from pds_core.routing_models import ModuleRecordRef, ModuleWorkRef

from concord.pds_contract import (
    ACADEMIC_RESULT_MANIFEST_CONTRACT_VERSION,
    CONCORD_ACADEMIC_RESULT_READER_CONTRACT_VERSION,
    CONCORD_ACADEMIC_WORK_CONTRACT_VERSION,
    CONCORD_ACADEMIC_WORK_KIND,
    CONCORD_ACTIVITY_CONTRACT_VERSION,
    CONCORD_ACTIVITY_RECORD_KIND,
    CONCORD_DISTRIBUTION_NAME,
)
from concord.pds_publication import get_publication_producer_profile

EXPECTED_READER = PublicationReaderSupport(
    manifest_contract_version="concord_academic_result_manifest_v1",
    distribution_name="pds-concord",
    reader_contract_version="concord_academic_result_reader_v1",
)


def _work() -> ModuleWorkRef:
    return ModuleWorkRef(
        module_id="concord",
        class_id="class-1",
        work_id="activity-1",
    )


def _source() -> ModuleRecordRef:
    return ModuleRecordRef(
        module_id="concord",
        record_kind=CONCORD_ACTIVITY_RECORD_KIND,
        record_id="activity-1",
        contract_version=CONCORD_ACTIVITY_CONTRACT_VERSION,
    )


def _registration() -> AcademicWorkRegistration:
    moment = datetime(2026, 10, 8, 12, 0, tzinfo=timezone.utc)
    return AcademicWorkRegistration(
        schema_version=ACADEMIC_WORK_REGISTRATION_SCHEMA_VERSION,
        record_type=ACADEMIC_WORK_REGISTRATION_RECORD_TYPE,
        work=_work(),
        registration_revision=1,
        producer_contract_version=CONCORD_ACADEMIC_WORK_CONTRACT_VERSION,
        title="Synthetic Concord Activity",
        work_kind=CONCORD_ACADEMIC_WORK_KIND,
        academic_intent="formative",
        lifecycle="active",
        created_at=moment,
        updated_at=moment,
        source_records=(_source(),),
    )


def _publication() -> PublicationRecord:
    return PublicationRecord(
        schema_version=PUBLICATION_RECORD_SCHEMA_VERSION,
        record_type=PUBLICATION_RECORD_TYPE,
        publication_id="pub_" + ("a" * 32),
        work=_work(),
        source_record=_source(),
        publication_kind="academic_result_set",
        capabilities=("criterion_scores",),
        record_set_id="academic_results",
        record_set_revision=1,
        manifest_contract_version=ACADEMIC_RESULT_MANIFEST_CONTRACT_VERSION,
        manifest_path=(
            "classes/class-1/modules/concord/work/activity-1/"
            "exports/manifests/academic_results/1.json"
        ),
        manifest_digest_algorithm="sha256",
        manifest_digest="b" * 64,
        published_at=datetime(2026, 10, 8, 13, 0, tzinfo=timezone.utc),
        academic_work_registration_revision=1,
        supersedes_publication_id=None,
    )


def test_issue129_exact_reader_support_survives_core_validation_lookup_and_registry(
) -> None:
    profile = get_publication_producer_profile()

    assert ACADEMIC_RESULT_MANIFEST_CONTRACT_VERSION == (
        "concord_academic_result_manifest_v1"
    )
    assert CONCORD_ACADEMIC_RESULT_READER_CONTRACT_VERSION == (
        "concord_academic_result_reader_v1"
    )
    assert CONCORD_DISTRIBUTION_NAME == "pds-concord"

    support = profile.publication_contracts[0]
    assert support.reader_support == (EXPECTED_READER,)
    assert lookup_publication_reader_support(
        profile,
        "academic_result_set",
        ACADEMIC_RESULT_MANIFEST_CONTRACT_VERSION,
    ) == EXPECTED_READER

    validated = validate_publication_producer_profile(profile)
    assert validated == profile
    assert lookup_publication_reader_support(
        validated,
        "academic_result_set",
        ACADEMIC_RESULT_MANIFEST_CONTRACT_VERSION,
    ) == EXPECTED_READER

    registry = PublicationProducerRegistry((profile,))
    registered = registry.get("concord")
    assert registered is not None
    assert lookup_publication_reader_support(
        registered,
        "academic_result_set",
        ACADEMIC_RESULT_MANIFEST_CONTRACT_VERSION,
    ) == EXPECTED_READER


def test_issue129_reader_lookup_is_exact_and_has_no_implicit_fallback() -> None:
    profile = get_publication_producer_profile()

    assert lookup_publication_reader_support(
        profile,
        "academic_result_set",
        "future_manifest_v2",
    ) is None
    assert lookup_publication_reader_support(
        profile,
        "intervention_record_set",
        ACADEMIC_RESULT_MANIFEST_CONTRACT_VERSION,
    ) is None


def test_issue129_publication_compatibility_is_independent_of_reader_metadata(
) -> None:
    profile = get_publication_producer_profile()
    legacy_metadata = replace(
        profile,
        publication_contracts=(
            replace(
                profile.publication_contracts[0],
                reader_support=(),
            ),
        ),
    )
    publication = _publication()
    registration = _registration()

    with_reader = evaluate_publication_compatibility(
        publication,
        profile,
        registration,
    )
    without_reader = evaluate_publication_compatibility(
        publication,
        legacy_metadata,
        registration,
    )

    assert with_reader == without_reader
    assert with_reader.compatible
    assert with_reader.codes == ()


def test_issue129_profile_construction_does_not_import_public_reader(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_import = builtins.__import__

    def guarded_import(name: str, *args: Any, **kwargs: Any) -> Any:
        if name.startswith("concord.academic_result_reader"):
            raise AssertionError(
                "Publication metadata must not import or execute the reader."
            )
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    profile = get_publication_producer_profile()
    assert profile.publication_contracts[0].reader_support == (EXPECTED_READER,)
    assert lookup_publication_reader_support(
        profile,
        "academic_result_set",
        ACADEMIC_RESULT_MANIFEST_CONTRACT_VERSION,
    ) == EXPECTED_READER


def test_issue129_core_floor_is_065_without_downstream_runtime_coupling() -> None:
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))[
        "project"
    ]
    dependencies = [Requirement(value) for value in project["dependencies"]]

    core = [item for item in dependencies if item.name == "pds-core"]
    assert len(core) == 1
    assert str(core[0].specifier) in {
        ">=0.6.5,<0.7",
        "<0.7,>=0.6.5",
    }

    dependency_names = {item.name for item in dependencies}
    assert dependency_names.isdisjoint(
        {
            "pds-meridian",
            "meridian",
            "pds-vitrine",
            "vitrine",
        }
    )
