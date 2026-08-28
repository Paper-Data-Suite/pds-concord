from __future__ import annotations

from pathlib import Path

from pds_core.module_profiles import validate_module_profile

from concord.cli import main
from concord.pds_module import get_module_profile


def test_console_script_remains_the_concord_cli_entry_point() -> None:
    text = Path("pyproject.toml").read_text(encoding="utf-8")
    scripts = text.split("[project.scripts]", 1)[1].split(
        "[project.entry-points.", 1
    )[0]

    assert 'concord = "concord.cli:main"' in scripts
    assert scripts.count('concord = "concord.cli:main"') == 1
    assert callable(main)


def test_routing_profile_remains_independent_from_operations_profile() -> None:
    profile = get_module_profile()

    assert validate_module_profile(profile) is profile
    assert profile.module_id == "concord"
    assert profile.route_handler.__module__ == "concord.workflows.artifact_page"
    assert profile.route_handler.__name__ == "handle_concord_route"
    assert profile.registration_validator is not None
    assert (
        profile.registration_validator.__module__
        == "concord.workflows.artifact_page"
    )
    assert (
        profile.registration_validator.__name__
        == "validate_concord_route_registration"
    )
