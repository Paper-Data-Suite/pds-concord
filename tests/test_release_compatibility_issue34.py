from __future__ import annotations

from dataclasses import replace

import pytest

from scripts.verify_release_compatibility import (
    EXPECTED_CAPABILITIES,
    ProducerProfileValues,
    ReleaseCompatibilityError,
    ReleaseContractValues,
    validate_contract_values,
    validate_profile_values,
    validate_release_compatibility,
    validate_release_metadata,
)


def _project(*, core: str = "pds-core>=0.6.3,<0.7") -> dict[str, object]:
    return {
        "name": "pds-concord",
        "requires-python": ">=3.11",
        "dependencies": [core, "Pillow>=11,<13"],
    }


def _contracts() -> ReleaseContractValues:
    return ReleaseContractValues(
        "concord",
        "concord_academic_work_v1",
        "collaborative_activity",
        "activity",
        "concord_activity_v1",
        "concord_academic_result_manifest_v1",
        "concord_academic_result_manifest",
        "academic_results",
    )


def _profile() -> ProducerProfileValues:
    return ProducerProfileValues(
        "concord",
        frozenset({"1"}),
        frozenset({"concord_academic_work_v1"}),
        1,
        "academic_result_set",
        frozenset({"concord_academic_result_manifest_v1"}),
        EXPECTED_CAPABILITIES,
        "activity",
        frozenset({"concord_activity_v1"}),
        False,
        False,
    )


def test_live_release_compatibility_audit_passes() -> None:
    validate_release_compatibility()


@pytest.mark.parametrize(
    ("version", "core", "extra"),
    [
        ("0.2.0", "pds-core>=0.6.3,<0.7", None),
        ("0.3.0.dev0", "pds-core>=0.6.1,<0.7", None),
        ("0.3.0.dev0", "pds-core>=0.6.3,<0.7", "pds-meridian>=0.1"),
    ],
)
def test_release_metadata_rejects_version_core_and_sibling_drift(
    version: str, core: str, extra: str | None
) -> None:
    project = _project(core=core)
    if extra is not None:
        dependencies = project["dependencies"]
        assert isinstance(dependencies, list)
        dependencies.append(extra)
    with pytest.raises(ReleaseCompatibilityError):
        validate_release_metadata(project, version)


@pytest.mark.parametrize(
    "changed",
    [
        replace(_contracts(), work_contract="concord_academic_work_v2"),
        replace(_contracts(), record_set_id="results"),
    ],
)
def test_public_contract_rejects_identity_and_record_set_drift(
    changed: ReleaseContractValues,
) -> None:
    with pytest.raises(ReleaseCompatibilityError):
        validate_contract_values(changed)


@pytest.mark.parametrize(
    "changed",
    [
        replace(_profile(), capabilities=frozenset({"criterion_scores"})),
        replace(_profile(), source_record_kind="assignment"),
        replace(_profile(), source_contracts=frozenset({"concord_activity_v2"})),
        replace(_profile(), allows_missing_source_record=True),
    ],
)
def test_profile_rejects_capability_and_activity_source_drift(
    changed: ProducerProfileValues,
) -> None:
    with pytest.raises(ReleaseCompatibilityError):
        validate_profile_values(changed)
