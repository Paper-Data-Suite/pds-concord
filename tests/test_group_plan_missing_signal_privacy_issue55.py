from __future__ import annotations

from dataclasses import fields
from pathlib import Path

from concord.models import GroupMembership

ROOT = Path(__file__).resolve().parents[1]

PRIVATE_PLAN_FIELDS = frozenset(
    {
        "missing_signal_disposition",
        "missing_signal_random_seed",
        "missing_signal_disposition_provenance",
        "source_signal_set_id",
        "source_signal_set_digest",
        "source_signal_dimension_id",
    }
)


def test_group_membership_has_no_missing_signal_or_signal_history_fields() -> None:
    membership_fields = {field.name for field in fields(GroupMembership)}
    assert PRIVATE_PLAN_FIELDS.isdisjoint(membership_fields)
    assert "band" not in membership_fields
    assert "seed" not in membership_fields


def test_nonplanning_publication_and_evidence_surfaces_do_not_reference_private_state(
) -> None:
    direct_files = (
        ROOT / "concord" / "academic_result_manifest.py",
        ROOT / "concord" / "academic_result_manifest_generation.py",
        ROOT / "concord" / "academic_result_publication.py",
        ROOT / "concord" / "pds_publication.py",
        ROOT / "concord" / "models" / "artifacts.py",
        ROOT / "concord" / "models" / "review.py",
        ROOT / "concord" / "models" / "scoring.py",
    )
    routing_files = tuple(sorted((ROOT / "concord" / "routing").rglob("*.py")))
    files_to_check = direct_files + routing_files

    for path in files_to_check:
        text = path.read_text(encoding="utf-8")
        for field_name in PRIVATE_PLAN_FIELDS:
            assert field_name not in text, (
                f"{field_name} leaked into nonplanning surface "
                f"{path.relative_to(ROOT)}"
            )


def test_group_plan_missing_signal_module_does_not_import_sibling_modules() -> None:
    text = (
        ROOT / "concord" / "workflows" / "group_plan_missing_signal.py"
    ).read_text(encoding="utf-8")
    for sibling in (
        "meridian",
        "scoreform",
        "quillan",
        "vitrine",
        "portia",
    ):
        assert f"import {sibling}" not in text
        assert f"from {sibling}" not in text
