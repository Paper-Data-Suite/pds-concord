"""Side-effect-free Core routing profile for Concord."""

from pds_core.module_profiles import CORE_ROUTING_CONTRACT_VERSION, ModuleProfile
from pds_core.routing_models import PDS2_SCHEMA, ROUTE_REGISTRATION_SCHEMA_VERSION

from concord.workflows.artifact_page import (
    handle_concord_route,
    validate_concord_route_registration,
)


def get_module_profile() -> ModuleProfile:
    """Return Concord's released Core v0.6 routing profile."""
    return ModuleProfile(
        module_id="concord",
        display_name="Concord",
        supported_core_routing_contract_versions=frozenset(
            {CORE_ROUTING_CONTRACT_VERSION}
        ),
        supported_qr_schemas=frozenset({PDS2_SCHEMA}),
        supported_route_registration_schema_versions=frozenset(
            {ROUTE_REGISTRATION_SCHEMA_VERSION}
        ),
        dispatchable_route_statuses=frozenset({"active"}),
        route_handler=handle_concord_route,
        registration_validator=validate_concord_route_registration,
    )


__all__ = ["get_module_profile"]
