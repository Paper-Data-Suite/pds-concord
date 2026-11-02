"""Run only outside checkout, with --target installed wheel and synthetic workspace."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--workspace", required=True, type=Path)
    args = parser.parse_args()
    target = args.target.resolve(strict=True)
    sys.path.insert(0, str(target))

    from pds_core.workspace import ensure_workspace_root

    import concord
    from concord.reusable_preset_storage import load_current_preset
    from concord.scale_guidance import (
        format_typed_value,
        four_level_proficiency,
        parse_typed_value,
    )
    from concord.workflows.models import WorkflowActor
    from concord.workflows.reusable_presets import (
        CreateScoringScalePresetRequest,
        create_scoring_scale_preset,
    )

    package = Path(concord.__file__).resolve()
    if not package.is_relative_to(target):
        raise RuntimeError(f"Concord is not imported from installed wheel: {package}")
    starter = four_level_proficiency()
    assert starter.scale_type == "ordinal"
    assert [item.value for item in starter.levels] == [1, 2, 3, 4]
    assert all(type(item.value) is int for item in starter.levels)
    assert "[boolean]" in format_typed_value(True)
    assert type(parse_typed_value("1.0", "decimal").value) is float
    root = ensure_workspace_root(args.workspace)
    result = create_scoring_scale_preset(
        CreateScoringScalePresetRequest(
            preset_id="installed-guided-starter",
            preset_revision_id="installed-guided-starter-v1",
            name="Installed synthetic four-level starter",
            scale_type=starter.scale_type,
            levels=starter.levels,
            actor=WorkflowActor(actor_id="synthetic-installed-teacher"),
        ),
        workspace_root=root,
    )
    assert result.revision == 1
    restored = load_current_preset(
        root, "scoring_scale", "installed-guided-starter"
    ).current
    assert restored.levels == starter.levels
    assert restored.scale_type == starter.scale_type
    assert restored.revision == 1
    print("ISSUE144_SLICE5_INSTALLED_WHEEL_SMOKE_PASSED")
    print(f"Concord installed package: {package}")


if __name__ == "__main__":
    main()
