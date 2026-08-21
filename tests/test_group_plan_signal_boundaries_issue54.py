from __future__ import annotations

from pathlib import Path

import concord.workflows as workflows
from scripts.verify_release_compatibility import validate_sibling_import_isolation


def test_issue54_signal_workflow_is_exported_from_public_workflow_surface() -> None:
    assert workflows.CreateSignalGroupPlanRequest.__module__ == (
        "concord.workflows.group_plan_signal"
    )
    assert workflows.SignalGroupPlanCreationResult.__module__ == (
        "concord.workflows.group_plan_signal"
    )
    assert workflows.create_signal_group_plan.__module__ == (
        "concord.workflows.group_plan_signal"
    )


def test_issue54_production_preserves_sibling_import_isolation() -> None:
    validate_sibling_import_isolation()

    root = Path(__file__).resolve().parents[1]
    issue54_sources = (
        root / "concord" / "group_plan_targets.py",
        root / "concord" / "group_plan_signal.py",
        root / "concord" / "workflows" / "group_plan_signal.py",
        root / "concord" / "cli_app" / "handlers" / "group_plan.py",
        root / "concord" / "menu_group_plan_signal.py",
        root / "concord" / "menu_group_plan.py",
    )
    forbidden = (
        "import meridian",
        "from meridian",
        "import scoreform",
        "from scoreform",
        "import quillan",
        "from quillan",
        "import vitrine",
        "from vitrine",
        "import portia",
        "from portia",
    )
    for source in issue54_sources:
        text = source.read_text(encoding="utf-8").casefold()
        assert not any(token in text for token in forbidden)


def test_issue54_uses_core_signal_digest_not_producer_snapshot_digest() -> None:
    root = Path(__file__).resolve().parents[1]
    source = (
        root / "concord" / "workflows" / "group_plan_signal.py"
    ).read_text(encoding="utf-8")

    assert "source_signal_set_digest=selection.digest" in source
    assert "source.snapshot_digest" not in source
