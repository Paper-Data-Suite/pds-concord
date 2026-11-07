# Concord #147 — Slice 0 source-pinned baseline and implementation decisions

**Issue:** https://github.com/Paper-Data-Suite/pds-concord/issues/147

**Branch:** `147-planned-cluster-bulk-roster-placement`

**Frozen starting Concord HEAD and `main`:** `ce066b0f2f4e7f033b22bfe12fd6551ee9c850d8` (2026-11-07)

**Observed Core `main`:** `a0d5e1a50580bbe025f0cad23c7e8524203a52ec`

**Observed Suite `main`:** `98649a5816485652a29b5c59e06f4704a7960626`

**Published-compatible Core anchor:** authenticated `pds-core 0.6.6`, `pds-core>=0.6.6,<0.7`. These source SHAs do not prove a new installed release.

## Baseline teacher workflow and verified gap

Concord `menu_group_plan.py::_planned_group_menu` currently exposes *add, edit, remove a planned group*, but not roster placement. `_open_plan` provides student-first `Place or move a student` and `Unassign a student`; `_place_student` calls `choose_student` **before** `_select_planned_group` and then calls `place_student_in_plan` for **one** student and one proposal write. The teacher needs a planned-Cluster-first way to assign/move/remove multiple roster students with one reviewed proposal commit instead of 29 or 30 one-student commits.

The existing `menu_prompts.select_one` / `select_many` paginate ten rows, retain selected indexes across pages and respect B/M/Q/H plus N/P. In existing `select_many`, `A` selects **all items across pages**, not just the current page. Do not retroactively reinterpret that shared behavior. A new local planned-Cluster selector should explicitly offer *visible page* and *all eligible across all pages*, with noncolliding V/A/N/P/D/H/B/M/Q and accumulated counts.

## Canonical service/storage contract to preserve

- `workflows/group_plan_manual.py::_load_targeted_edit`: read rooted Class/Activity/GroupPlan, verify expected Activity snapshot, `draft`/`previewed` editability, and **exact current Core class roster** versus the plan roster. Reject drift before edits. This module owns the existing `place_student_in_plan` and `unassign_student_from_plan` semantics.
- `_replace_preserving_origin` delegates **once** to `workflows/group_plan.py::replace_group_plan_proposal`, with exact proposed groups, origin/strategy/seed/source metadata and `expected_snapshot_revision` via canonical storage. Model enforces unique students and plan-local group keys. A changed `previewed` proposal returns to `draft`; no-op has zero record revisions.
- `models/group_planning.py::PlannedGroup.student_ids` contains **Core `student_id`** values (not display names); a planned group key is not a canonical Concord Group ID. `GroupPlan.unresolved_student_ids` is derived from the validated exact class roster and proposed groups. Never fork Core roster identity or write to Core enrollment.
- `workflows/group_plan.py::preview_group_plan` and `approve_group_plan` are separate **durable GroupPlan lifecycle** actions. The new **zero-write batch impact preview** must never advance them. Canonical Group/Membership application requires the separate `workflows/group_plan_application.py` application preview/digest/commit. No operational Group writes in a batch.
- `menu_standards_context.py::standards_kwargs_for_plan` loads the live Activity and forwards authoritative Core Standards context for mixed/standards-backed writes; preserve #141/#142 repair and historic standards-backed graph guards. Preserve exact workspace identity, CAS, actor provenance, immutable history and storage partial-outcome handling.
- Existing `student_id,group` CSV import/replacement, class-scoped saved arrangements and direct CLI commands must remain functional; do not turn this interactive task into a full arrangement overwrite.

## Bounded decisions for implementation Slices 1–4

1. **Slice 1 — service:** adopt `prepare_bulk_planned_group_edit` and `commit_bulk_planned_group_edit` (typed request/preview/commit model) as a **Concord-local** service, reusable by menu and direct CLI. Prepare reads plan/roster and deterministically produces complete candidate groups, per-student deltas, counts and a digest, **without writing**. Commit re-reads and revalidates exact digest, snapshot/plan revision, class/workspace/roster/Standards and actor context, then performs **one** canonical proposal replacement; cannot atomically transact with the separate Core roster file. No-op, cancellation, stale or invalid request must not write.
2. **Slice 2 — menu:** planned Cluster selected **first**, then a `concord.menu_group_plan_bulk`-local paginated scoped selector and review/confirmation. Preserve student-first quick edit, all navigation and current plan lifecycle. Present source→destination moves and all affected group sizes, label/name collisions, class/workspace, status, snapshot, and explicitly warn that Core roster and operational Groups/Memberships are untouched.
3. **Slice 3 — direct CLI:** new distinct `group-plan batch-place-preview` and `group-plan batch-place` commands (including explicit operation, target key, selected IDs, expected revisions and reviewed digest on commit). Existing commands, JSON/CSV formats and return codes stay unchanged.
4. **Slice 4 — final gate:** synthetic 29-student `5/5/5/5/4/5` and 30-student `6/5/5/3/6/5` six-Cluster menu/service tests; extensive canceled/stale/roster/wrong-class/no-write and plan lifecycle scenarios; full repository tests once; Ruff/mypy, authenticated Core 0.6.6 isolated wheel acceptance and supported PR CI. Human classroom/physical print-return-scanning evidence belongs to #155, not this ticket.

## Related repositories and ownership

**Core:** #236/#237 establish versioned teacher-experience design/source capabilities; #238 workspace-private Notes store is still evolving and #241 roster mutation is separately owned. Do not import unpublished Core `teacher_ui`/`:notes`/Notes or require #238/#241. Core 0.6.6 public roster/Standards/workspace/navigation suffices. Future Core roster changes remain authoritative and must cause a stale planned proposal to refuse, not silent enrollment edits.

**Suite:** #49 evergreen launch/release provenance, closed #51/#16 teacher contract/provider inventory and open #52 teacher home own Suite launch and integration. The accepted teacher experience design favors Review→Confirm→Continue, but a Concord manual GroupPlan bulk **does not** change Suite CLI/provider, Core release identities or whole-suite qualification. Do not rewrite historical Suite release manifests.

**Concord:** #136 and merged #140–#146 protect real six-Cluster CSV/saved-plan experience, Class/Standards context and status behavior. #149 (attention), #153 (general navigation), #155 (full end-to-end acceptance), #162 (audit semantics) retain their distinct ownership.

## Slice 0 failing-before evidence and expected qualification

`tests/test_issue147_slice0_cluster_bulk_baseline.py` has **four deliberate strict XFAIL** witnesses until their owning slices replace them with positive tests:

1. real planned-group menu shows no `Manage students in this planned Cluster (bulk)` action;
2. no `prepare_bulk_planned_group_edit`/`commit_bulk_planned_group_edit` service pair;
3. no local `concord.menu_group_plan_bulk` selection surface;
4. no direct CLI batch preview/commit commands.

Four **passing** baseline witnesses confirm current student-first ordering, exact Core roster/snapshot checks, the canonical proposal replacement boundary and global meaning of current shared selector `A`. Focused existing #51 GroupPlan menu/manual/CSV tests are included with the runner. This is a **source baseline**, not proof the feature is implemented, installed-wheel qualified or teacher-tested. Convert the four XFAILs as corresponding slices are delivered, so final #147 CI has no unexplained expected failures.
