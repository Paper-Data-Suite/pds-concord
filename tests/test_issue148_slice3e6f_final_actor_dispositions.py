"""#148 3E6F: exhaustive known menu AST candidate dispositions, synthetic only.

No current classroom workspace, local profile or student record is accessed.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from scripts.issue148_actor_callsite_census import inspect_text, inventory
from scripts.issue148_final_attribution_gate import (
    ACTOR_HELPER,
    DISPOSITIONS,
    LEGACY_ACTOR,
    MENU_MODULE_COUNT,
    MUST_REVIEW,
    OTHER_CONTRACT,
    REVIEWED,
    _function,
    _key,
    evaluate,
    render_report,
    validate_contracts,
    validate_rows,
)

ROOT = Path(__file__).resolve().parents[1]


def test_full_current_menu_census_is_explicitly_dispositioned() -> None:
    count, rows = evaluate(ROOT)
    assert count == MENU_MODULE_COUNT == 43
    assert rows == tuple(sorted(rows, key=lambda r: (r.path, r.line, r.function)))
    assert len(rows) >= 100
    assert all(row.classification != LEGACY_ACTOR for row in rows)
    assert {_key(row) for row in rows if row.classification != REVIEWED} == set(
        DISPOSITIONS
    )
    assert {row.classification for row in rows if row.classification != REVIEWED} == {
        ACTOR_HELPER,
        OTHER_CONTRACT,
    }


@pytest.mark.parametrize(("path", "name"), sorted(MUST_REVIEW))
def test_consequential_write_stays_reviewed(path: str, name: str) -> None:
    _count, rows = inventory(ROOT)
    matching = [row for row in rows if (row.path, row.function) == (path, name)]
    assert len(matching) == 1
    assert matching[0].classification == REVIEWED


def test_final_gate_rejects_a_new_legacy_actor_write() -> None:
    _count, rows = inventory(ROOT)
    synthetic = inspect_text(
        "concord/menu_new_synthetic.py",
        """
def dangerous(state):
    actor = state.require_actor()
    if not confirm_write('Commit', 'COMMIT', ()):
        return
    commit(SyntheticRequest(actor=actor))
""",
    )
    assert len(synthetic) == 1
    assert synthetic[0].classification == LEGACY_ACTOR
    with pytest.raises(ValueError, match="legacy_actor"):
        validate_rows((*rows, *synthetic))


def test_final_gate_rejects_unclassified_new_core_confirmation() -> None:
    _count, rows = inventory(ROOT)
    synthetic = inspect_text(
        "concord/menu_new_synthetic.py",
        """
def uncertain_service():
    if confirm_write('Save', 'SAVE', ()):
        update_core_state()
""",
    )
    assert synthetic[0].classification == OTHER_CONTRACT
    with pytest.raises(ValueError, match="unclassified"):
        validate_rows((*rows, *synthetic))


def test_final_gate_rejects_changed_disposition_and_missing_candidate() -> None:
    _count, rows = inventory(ROOT)
    first = next(row for row in rows if _key(row) in DISPOSITIONS)
    modified = tuple(
        replace(row, classification=REVIEWED) if row == first else row for row in rows
    )
    with pytest.raises(ValueError, match="reclassified"):
        validate_rows(modified)
    removed = tuple(row for row in rows if row != first)
    with pytest.raises(ValueError, match="missing_disposition"):
        validate_rows(removed)


def test_core_service_and_nested_score_contract_witnesses() -> None:
    validate_contracts(ROOT)
    for name in ("_record_score", "_revise_score"):
        assert _function(ROOT, "concord/menu_scoring.py", name).name == name


def test_census_report_is_transparent_about_remaining_acceptance() -> None:
    count, rows = evaluate(ROOT)
    report = render_report("0" * 40, count, rows)
    assert "zero" in report.lower() or "| `legacy-confirm-with-actor` | 0 |" in report
    assert "**Source HEAD:** `" + "0" * 40 + "`" in report
    assert "Core grouping-signal import" in report
    assert "nested non-score StatusReason" in report
    assert "full repository tests" in report
    assert "does **not** prove" in report


def test_absent_legacy_actor_does_not_imply_authentication() -> None:
    _count, rows = evaluate(ROOT)
    assert not [row for row in rows if row.classification == LEGACY_ACTOR]
    assert any(row.function == "_route" for row in rows)
    assert any(row.function == "_score_components" for row in rows)
