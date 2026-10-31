# Concord #142 — Slice 6C3B: historical #107 Quick Review unit tests

**Purpose:** reconcile six legacy Quick Review decision/dispatch tests with the
pinned-workspace, exact-snapshot and explicit Core Standards forwarding contract
introduced by #142. No production code or frozen #140 audit files are modified.

The legacy tests simulate a Class/Activity and an Artifact without a physical
Core workspace. A function-scoped, autouse fixture supplies *only for the six
named menu-decision cases* a synthetic pinned context (`root=Path('.')`,
Activity snapshot 12, digest `abc123`). The fixture does not create a workspace
or assert canonical Core validation; those properties remain covered by real
#142 synthetic integration tests. The tests continue to assert explicit
teacher decisions, cancellation/no-write, evidence open refusal, exact Artifact
selection, and privacy-aware routine Review preview.

The old Artifact and routine projection mocks now carry snapshot 12 consistent
with their Activity, and accept the new `workspace_root` and forward-write
keyword arguments. The preview assertion for snapshot 17 changes to 12, without
altering its asserted provenance digest `abc123` or other Review criteria.

**Scope:** `tests/test_menu_artifact_routine_review_issue107.py` and this note.
**Status:** Candidate pending Windows pytest, Ruff, mypy and whitespace gates.
**Prohibited:** production changes, blanket bypass, frozen #140 changes, staged
changes, automatic commit/push or real school workspace access.
