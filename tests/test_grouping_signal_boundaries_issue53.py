from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.classes import write_class_roster
from pds_core.grouping_signal_storage import write_grouping_signal
from pds_core.grouping_signals import grouping_signal_set_from_json
from pds_core.rosters import create_roster
from pds_core.workspace import ensure_workspace_root

from concord.workflows import (
    ImportGroupingSignalCsvRequest,
    import_grouping_signal_csv,
    list_grouping_signals,
    select_grouping_signal_dimension,
)
from scripts.verify_release_compatibility import validate_sibling_import_isolation

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "core_grouping_signals" / "v1"


def _fixture(name: str) -> bytes:
    return (FIXTURE_ROOT / name).read_bytes()


def _workspace(tmp_path: Path) -> Path:
    root = ensure_workspace_root(tmp_path / "workspace")
    write_class_metadata_for_class(
        root,
        create_class_metadata(
            "english10_p2",
            "2026-2027",
            created_at=datetime(2026, 8, 20, tzinfo=timezone.utc),
        ),
    )
    write_class_roster(
        root,
        create_roster(
            "english10_p2",
            (
                {
                    "student_id": "student_001",
                    "last_name": "Sample",
                    "first_name": "Ava",
                    "period": "2",
                },
                {
                    "student_id": "student_002",
                    "last_name": "Example",
                    "first_name": "Ben",
                    "period": "2",
                },
                {
                    "student_id": "student_003",
                    "last_name": "Demo",
                    "first_name": "Cora",
                    "period": "2",
                },
            ),
        ),
    )
    return root


def _digests(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file()
    }


def test_exact_signal_selection_is_read_only_without_activity_state(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    signal = grouping_signal_set_from_json(_fixture("teacher_complete.json"))
    stored = write_grouping_signal(root, signal).stored
    before = _digests(root)

    summaries = list_grouping_signals("english10_p2", workspace_root=root)
    selection = select_grouping_signal_dimension(
        "english10_p2",
        "teacher_complete_001",
        "discussion_support",
        workspace_root=root,
    )

    assert tuple(item.signal_set_id for item in summaries) == (
        "teacher_complete_001",
    )
    assert selection.signal_set_id == "teacher_complete_001"
    assert selection.dimension_id == "discussion_support"
    assert selection.digest == stored.digest
    assert selection.inspection.stored == stored
    assert selection.inspection.diagnostics.is_clean
    assert _digests(root) == before
    assert not (
        root / "classes" / "english10_p2" / "modules" / "concord"
    ).exists()


def test_signal_csv_import_persists_only_core_exchange_state(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    before = _digests(root)
    csv_path = tmp_path / "teacher-complete.csv"
    csv_path.write_bytes(_fixture("teacher_complete.csv"))

    result = import_grouping_signal_csv(
        ImportGroupingSignalCsvRequest(
            class_id="english10_p2",
            csv_path=csv_path,
        ),
        workspace_root=root,
    )

    after = _digests(root)
    added = set(after) - set(before)
    assert result.disposition == "created"
    assert added == {
        "exchange/grouping-signals/english10_p2/teacher_complete_001.json",
        (
            "exchange/grouping-signals/english10_p2/"
            "teacher_complete_001.json.sha256"
        ),
    }
    assert not (
        root / "classes" / "english10_p2" / "modules" / "concord"
    ).exists()
    assert not (root / "pds2").exists()


def test_issue53_production_preserves_sibling_import_isolation() -> None:
    validate_sibling_import_isolation()

    root = Path(__file__).resolve().parents[1]
    issue53_sources = (
        root / "concord" / "workflows" / "grouping_signal.py",
        root / "concord" / "cli_app" / "handlers" / "grouping_signal.py",
        root / "concord" / "menu_grouping_signal.py",
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
    for source in issue53_sources:
        text = source.read_text(encoding="utf-8").casefold()
        assert not any(token in text for token in forbidden)
