# Concord #148 — Slice 3E6D: GroupPlan bulk-review disposition

- Branch: `148-persistent-reviewable-teacher-attribution`
- Pinned starting commit: `cbb38cb765247b751c53b46a8aed3c1d25415a8f`
- Classification: **already covered, custom action-scoped review** (from Concord #147, retained by #148).
- Production edits: **none**. The custom `SAVE BATCH` review already binds a selected actor, immutable request, preview digest, and guarded commit. Rewriting it would risk duplicating actor prompts and regressing the Cluster-first workflow.

## Source-backed disposition

1. `concord/menu_group_plan_bulk.py::_review_batch`: the original, paginated review shows proposed GroupPlan-only changes and the recorded actor. Its `A` path calls `_choose_temporary_actor`, makes a **new** request via `dataclasses.replace(request, actor=...)`, and re-runs `prepare_review`. Its `D` path restores the saved default and re-runs preparation. `B` returns no reviewed pair. `SAVE BATCH` calls `state.actor_for_action` again and aborts if the actor no longer matches `reviewed_request.actor`.
2. `concord/menu_group_plan_bulk.py::launch_cluster_bulk_editor`: creates an initial proposal from the exact roster, snapshot, record revision, and Standards context; delegates review to `_review_batch`; commits **only** its returned `reviewed_request` with `reviewed_preview.review_digest`. A cancelled review returns to selection; it does not reach the canonical commit. Canonical Groups and the Core roster are unaffected by a successful GroupPlan proposal edit.
3. `tests/test_issue147_slice2_cluster_bulk_menu.py` already covers selection, cancellation, one revision per batch, and six-Cluster distributions with synthetic rosters. Slice 3E6D adds focused #148 tests for temporary actor, default restoration, cancel, no-op, profile fingerprint change, and canonical request/digest pairing. No real classroom profile or workspace is accessed.

## Adjacent contract-specific rows (do not invent an actor field)

- `concord/menu_grouping_signal.py::_import_csv`: writes an immutable Core grouping-signal exchange via `ImportGroupingSignalCsvRequest`, whose current menu request has no `WorkflowActor`. It retains its `IMPORT` confirmation and digest check. This is **not** a Concord academic-record provenance write. A future Core-attributed import would require a separately qualified Core contract.
- `concord/menu_publication.py::_register` and `_update_registration`: use the Core academic-work registration services, not the native Concord `WorkflowActor` write interface. Preserve exact Core registration revision and intentional confirmation. Do not pass a fabricated actor parameter into Core.
- `concord/menu_saved_groupings.py::_saved`, `concord/menu_saved_grouping_revisions.py::_current` and `_show_history`: actor resolution scopes **read access** to existing saved arrangement ownership, not a new write requiring a second action review.
- `concord/menu_saved_groupings.py::_collect_decisions`: departed-student acknowledgment and placement selection are preparatory; the subsequent `use_saved_grouping` canonical draft creation received a reviewed actor in 3E5A.
- `concord/menu_artifact.py::_choose_author_semantics`: author identity selection is **not** the action recorder. Its enclosing canonical author-add/correct operations were converted in previous #148 slices.
- `concord/menu_packet_generation.py::_resume_generation`, `concord/menu_scan.py::_route`, and `concord/menu_publication.py::_withdraw` / `_rebuild_catalog` require **separate service-contract disposition** before final acceptance; actor-less repair, routing and catalog operations must not be relabeled as attributed writes without inspecting their exact APIs.

## Boundaries and remaining gates

This slice **does not** establish that the whole actor callsite census is complete. Remaining work includes source-pinned detailed disposition of all `legacy-confirm-with-actor`, `actor-resolved-no-local-review`, and `confirm-without-local-actor-resolution` candidates; verification of direct explicit-actor CLI; full Concord tests, Ruff/mypy, wheel/build/install/relaunch acceptance, and supported CI. The issue must remain open until those gates pass. Core 0.6.6 and Suite/Meridian ownership are unchanged.
