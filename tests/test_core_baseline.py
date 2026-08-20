from __future__ import annotations

import importlib.metadata
from pathlib import Path
from typing import get_args

import pytest
from packaging.version import Version
from pds_core.academic_work_registrations import (
    ACADEMIC_WORK_REGISTRATION_SCHEMA_VERSION,
)
from pds_core.module_profiles import CORE_ROUTING_CONTRACT_VERSION
from pds_core.publication_compatibility import (
    CORE_PUBLICATION_COMPATIBILITY_CONTRACT_VERSION,
)
from pds_core.publication_records import (
    PUBLICATION_RECORD_SCHEMA_VERSION,
    PUBLICATION_WITHDRAWAL_SCHEMA_VERSION,
    ManifestDigestAlgorithm,
)
from pds_core.routes import (
    ModuleWorkPathError,
    module_work_dir,
    safe_module_work_descendant,
)
from pds_core.routing_models import (
    PDS2_SCHEMA,
    ROUTE_REGISTRATION_SCHEMA_VERSION,
    ModuleRecordRef,
    ModuleWorkRef,
)
from pds_core.scan_failure_metadata import ROUTING_FAILURE_SCHEMA_VERSION
from pds_core.scan_resolution_metadata import SCAN_RESOLUTION_SCHEMA_VERSION

from concord.constants import CONCORD_MODULE_ID


def test_core_version_and_contract_values() -> None:
    version = Version(importlib.metadata.version("pds-core"))
    assert Version("0.6.1") <= version < Version("0.7")
    assert CORE_ROUTING_CONTRACT_VERSION == "1"
    assert PDS2_SCHEMA == "PDS2"
    assert ROUTE_REGISTRATION_SCHEMA_VERSION == "1"
    assert ROUTING_FAILURE_SCHEMA_VERSION == "2"
    assert SCAN_RESOLUTION_SCHEMA_VERSION == "2"
    assert ACADEMIC_WORK_REGISTRATION_SCHEMA_VERSION == "1"
    assert PUBLICATION_RECORD_SCHEMA_VERSION == "1"
    assert PUBLICATION_WITHDRAWAL_SCHEMA_VERSION == "1"
    assert CORE_PUBLICATION_COMPATIBILITY_CONTRACT_VERSION == "1"
    assert get_args(ManifestDigestAlgorithm) == ("sha256",)


def test_concord_core_identity_and_paths(
    baseline_context: dict[str, object], tmp_path: Path
) -> None:
    work = ModuleWorkRef(
        module_id=CONCORD_MODULE_ID,
        class_id=str(baseline_context["class_id"]),
        work_id=str(baseline_context["activity_id"]),
    )
    record = ModuleRecordRef(
        module_id=str(baseline_context["module_id"]),
        record_kind=str(baseline_context["record_kind"]),
        record_id=str(baseline_context["record_id"]),
        contract_version=str(baseline_context["contract_version"]),
    )
    expected = (
        tmp_path
        / "classes"
        / "synthetic_class_2026"
        / "modules"
        / "concord"
        / "work"
        / "synthetic_activity_alpha"
    )
    assert work.work_id == baseline_context["activity_id"]
    assert record.module_id == CONCORD_MODULE_ID
    assert module_work_dir(tmp_path, work) == expected
    descendant = safe_module_work_descendant(tmp_path, work, "records/activity.json")
    assert descendant == expected / "records" / "activity.json"
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize(
    "unsafe", ["../escape", "records/../../escape", "/absolute", "C:\\escape"]
)
def test_safe_descendant_rejects_escape(unsafe: str, tmp_path: Path) -> None:
    work = ModuleWorkRef(CONCORD_MODULE_ID, "synthetic_class_2026", "activity")
    with pytest.raises(ModuleWorkPathError):
        safe_module_work_descendant(tmp_path, work, unsafe)
