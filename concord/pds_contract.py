"""Stable public contract identities for Concord Core integration."""

from __future__ import annotations

from typing import Final

CONCORD_MODULE_ID: Final[str] = "concord"
CONCORD_DISPLAY_NAME: Final[str] = "Concord"

CONCORD_ACADEMIC_WORK_CONTRACT_VERSION: Final[str] = (
    "concord_academic_work_v1"
)
CONCORD_ACADEMIC_WORK_KIND: Final[str] = "collaborative_activity"

CONCORD_ACTIVITY_RECORD_KIND: Final[str] = "activity"
CONCORD_ACTIVITY_CONTRACT_VERSION: Final[str] = "concord_activity_v1"

ACADEMIC_RESULT_MANIFEST_CONTRACT_VERSION: Final[str] = (
    "concord_academic_result_manifest_v1"
)
ACADEMIC_RESULT_MANIFEST_RECORD_TYPE: Final[str] = (
    "concord_academic_result_manifest"
)
CONCORD_ACADEMIC_RESULT_RECORD_SET_ID: Final[str] = "academic_results"

__all__ = [
    "ACADEMIC_RESULT_MANIFEST_CONTRACT_VERSION",
    "ACADEMIC_RESULT_MANIFEST_RECORD_TYPE",
    "CONCORD_ACADEMIC_RESULT_RECORD_SET_ID",
    "CONCORD_ACADEMIC_WORK_CONTRACT_VERSION",
    "CONCORD_ACADEMIC_WORK_KIND",
    "CONCORD_ACTIVITY_CONTRACT_VERSION",
    "CONCORD_ACTIVITY_RECORD_KIND",
    "CONCORD_DISPLAY_NAME",
    "CONCORD_MODULE_ID",
]
