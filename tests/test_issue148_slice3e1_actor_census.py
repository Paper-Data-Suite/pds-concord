"""#148 3E1: source-pinned inventory of action-scoped review adoption.

Synthetic AST examples and source-only tests; no PDS workspace or profile I/O.
"""

from __future__ import annotations

from pathlib import Path

from scripts.issue148_actor_callsite_census import (
    inspect_text,
    inventory,
    render_report,
)

ROOT = Path(__file__).resolve().parents[1]


def test_ast_census_distinguishes_review_classifications() -> None:
    rows = inspect_text(
        "concord/menu_synthetic.py",
        """
def reviewed(state):
    actor = confirm_actor_write("Save", "SAVE", (), state=state)
    save(Request(actor=actor))

def legacy(state):
    actor = state.require_actor()
    if not confirm_write("Save", "SAVE", ()):
        return
    save(Request(actor=actor))

def delegated(state):
    return state.require_actor()

def core_without_actor():
    if confirm_write("Rebuild", "REBUILD", ()):
        rebuild_catalog()
""",
    )
    assert [x.classification for x in rows] == [
        "action-reviewed",
        "legacy-confirm-with-actor",
        "actor-resolved-no-local-review",
        "confirm-without-local-actor-resolution",
    ]
    assert rows[0].explicit_actor == 1
    assert rows[1].legacy_review == 1


def test_inventory_is_deterministic_and_reports_known_coverage_and_gaps() -> None:
    file_count, rows = inventory(ROOT)
    assert file_count >= 35
    by_key = {(row.path, row.function): row for row in rows}
    covered = (
        ("concord/menu_artifact_scoring.py", "_record_selected_artifact_score"),
        ("concord/menu_artifact_scoring.py", "_record_another_criterion"),
        ("concord/menu_publication.py", "_generate"),
        ("concord/menu_publication.py", "_publish"),
        ("concord/menu_artifact.py", "_add_author"),
    )
    for key in covered:
        assert by_key[key].classification == "action-reviewed", key
    promoted = (
        ("concord/menu_group.py", "_create_group"),
        ("concord/menu_session.py", "_add"),
        ("concord/menu_template.py", "_create"),
        ("concord/menu_packet.py", "_create"),
    )
    for key in promoted:
        assert by_key[key].classification == "action-reviewed", key
    assert rows == tuple(sorted(rows, key=lambda r: (r.path, r.line, r.function)))
    report = render_report("0123456789abcdef", file_count, rows)
    assert "`concord/menu_group.py:" in report
    assert "`actor-resolved-no-local-review`" in report
    assert "not a final acceptance verdict" not in report
    assert "## Follow-on acceptance gate" in report
