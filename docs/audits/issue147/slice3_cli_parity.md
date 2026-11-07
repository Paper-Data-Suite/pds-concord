# Concord #147 — Slice 3 direct CLI and existing-workflow parity

Issue: https://github.com/Paper-Data-Suite/pds-concord/issues/147

## Source and authority boundary

- Base: clean `147-planned-cluster-bulk-roster-placement` at `4ec5f7439a97260487e033d69a8e7b0bdbc60200` after qualified Slice 2.
- Core authoritative class roster and Standards services remain unmodified. Concord 0.3.x development source retains `pds-core>=0.6.6,<0.7`. Suite's release and launch composition is out of scope.
- The only public change is two **new direct Concord commands** using Slice 1's existing typed `BulkPlannedGroupEditRequest` and `prepare_bulk_planned_group_edit` / `commit_bulk_planned_group_edit` service.
- No existing CLI command/argument/exit-code contract or GroupPlan model/strategy/schema is rewritten. No Core/Suite files, publishing metadata or wheel versions change.

## Scriptable commands

1. `concord group-plan batch-place-preview` is **read-only**. Accept optional explicit `--workspace-root` (otherwise use the configured workspace), and require `--class-id`, `--activity-id`, `--group-plan-id`, `--planned-group-key`, `--operation`, one or more repeated `--student-id`, `--expected-snapshot`, `--expected-record-revision`, and `--actor-id`; optional existing actor/Standards flags remain available. Print the complete per-student transition list, before/after sizes, unresolved counts and a deterministic `Review digest: <sha256>`.
2. `concord group-plan batch-place` requires the **same parameters** plus `--review-digest`. The canonical service recomputes the exact candidate and refuses drift. A successful changed batch writes exactly one Concord GroupPlan proposal revision; no-op writes nothing. Output an authoritative commit receipt plus record revision.
3. `--operation place_or_move` selects exact Core roster IDs into one **planned** Cluster, removing them from prior planned Clusters; `unassign_from_target` places current target members in the unresolved proposal set. Neither command creates operational Groups/Memberships or touches Core roster rows.
4. The review digest is an integrity binding, **not** a substitute for actor authorization, current snapshot, plan revision, Standards validation or explicit teacher review. Scripts must consciously supply the digest obtained from a prior preview. The exact provided student IDs and actor are included in the rechecked service request.
5. The established direct CLI exit contract remains: success 0, ordinary validation error 1, usage error 2, stale/digest conflict 3, partial/uncertain success 4. No interactive prompt is invoked by the two commands.

## Regression coverage and deferrals

- Slice 3 real service-backed tests: read-only/deterministic preview; preview→commit (one revision); stale replay; wrong digest/actor; duplicate student; unknown roster/changed Core roster; remove-to-unresolved; no-op; parser required arguments and help. The prior CLI XFAIL witness is converted to a normal passing test.
- Existing direct commands and important alternatives continue through focused tests: manual GroupPlan CLI, GroupPlan approval/application, CSV arrangement import/replacement, saved class groupings, and Slice 0–2 synthetic menu/service acceptance. Do **not** replace a full saved grouping from a bulk operation.
- Slice 4 owns the **single final full repository/strict mypy/Ruff/installed authenticated Core 0.6.6 wheel and PR CI gate**, plus any necessary repairs. No physical teacher/print/scan acceptance is claimed by Slice 3; Concord #155 covers that.
