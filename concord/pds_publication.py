"""Installed Core publication compatibility metadata for Concord."""

from pds_core.publication_compatibility import (
    PublicationContractSupport,
    PublicationProducerProfile,
    SourceRecordContractSupport,
    validate_publication_producer_profile,
)
from pds_core.publication_records import PUBLICATION_RECORD_SCHEMA_VERSION

from concord.academic_result_manifest import (
    ACADEMIC_RESULT_MANIFEST_CONTRACT_VERSION,
)
from concord.pds_contract import (
    CONCORD_ACADEMIC_WORK_CONTRACT_VERSION,
    CONCORD_ACTIVITY_CONTRACT_VERSION,
    CONCORD_ACTIVITY_RECORD_KIND,
    CONCORD_DISPLAY_NAME,
    CONCORD_MODULE_ID,
)


def get_publication_producer_profile() -> PublicationProducerProfile:
    """Return Concord's validated metadata-only publication profile."""
    return validate_publication_producer_profile(
        PublicationProducerProfile(
            module_id=CONCORD_MODULE_ID,
            display_name=CONCORD_DISPLAY_NAME,
            supported_core_publication_schema_versions=frozenset(
                {PUBLICATION_RECORD_SCHEMA_VERSION}
            ),
            supported_academic_work_contract_versions=frozenset(
                {CONCORD_ACADEMIC_WORK_CONTRACT_VERSION}
            ),
            publication_contracts=(
                PublicationContractSupport(
                    publication_kind="academic_result_set",
                    manifest_contract_versions=frozenset(
                        {ACADEMIC_RESULT_MANIFEST_CONTRACT_VERSION}
                    ),
                    supported_capabilities=frozenset(
                        {
                            "criterion_scores",
                            "moderated_scores",
                            "standards_ratings",
                        }
                    ),
                    source_record_contracts=(
                        SourceRecordContractSupport(
                            record_kind=CONCORD_ACTIVITY_RECORD_KIND,
                            contract_versions=frozenset(
                                {CONCORD_ACTIVITY_CONTRACT_VERSION}
                            ),
                            allows_unversioned=False,
                        ),
                    ),
                    allows_missing_source_record=False,
                ),
            ),
        )
    )


__all__ = ["get_publication_producer_profile"]
