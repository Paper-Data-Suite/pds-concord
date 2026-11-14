# Concord #148 — Slice 3E6E: nested Score provenance and indirect callsites

**Pinned starting branch:** `148-persistent-reviewable-teacher-attribution`
**Pinned HEAD:** `b880a6c147a5ef4cb374f75d6b7c22491e1e510b`

## Confirmed consequential discrepancy

`concord/menu_scoring.py::_score_components` creates a non-scored
`StatusReason(recorded_by=actor_reference(state.require_actor()), ...)`
**before** the final action-scoped Score review. `_record_score` and
`_revise_score` then select their final `WorkflowActor` using
`confirm_actor_write`; before this slice, they sent the original nested
`draft.status_reason` to `AddScoreRequest` / `ReplaceScoreRequest` even
when the final reviewed actor differed. The canonical Score's action actor
and its nested status reason therefore could disagree.

Slice 3E6E adds `_reviewed_score_status_reason(reason, actor)` and uses it at
**both** canonical write boundaries. It immutably replaces only
`StatusReason.recorded_by` with `actor_reference(actor)`, preserving the
selected reason code, timestamp, note and related record. For a normal
scored value, `None` remains `None`. Cancelling the final review reaches
neither canonical write. The local teacher default is not updated or
persisted by this helper. All tests use invented adults and mock write
services; no real teacher profile or classroom workspace is opened.

## Remaining attribution callsite dispositions

The 3E1 AST inventory scans all `concord/menu*.py` top-level functions.
Slice 3E6E adds a gate requiring zero functions in
`legacy-confirm-with-actor`; this is **not**, by itself, a complete
transitive dataflow/authorization proof. In particular:

| Source function(s) | Disposition | Boundary |
|---|---|---|
| `menu_artifact::_choose_author_semantics` | Preparatory authorship identity, not the action recorder | Canonical author-add/correct operations already review their recorder; an explicitly chosen author must not be silently replaced |
| `menu_scoring::_score_components` | Preparatory Score draft; **nested provenance repaired here** | The final reviewed Score actor now also owns any nested `StatusReason` |
| `menu_group_plan_bulk::_review_batch`, `launch_cluster_bulk_editor` | Already covered custom paginated SAVE BATCH actor/digest review | 3E6D qualified temporary/default switching and precommit fingerprint check without production edits |
| `menu_saved_groupings::_saved`; `menu_saved_grouping_revisions::_current`, `_show_history` | Read-only owner-scoped loading | Not new mutations; owner actor is used to select accessible saved library state |
| `menu_saved_groupings::_collect_decisions` | Preparatory roster/placement acknowledgment | Final reuse writer uses reviewed actor and digest (3E5A) |
| `menu_publication::_manifest_request` | Preparation helper for actor-bound public projection | `_generate` / `_publish` reprepare using the reviewed actor (3D3A) |
| `menu_teacher_settings::_setup`, `_rename`, `_replace`, `_reset` | Explicit local profile settings mutation with separate confirmation and CAS | Not academic provenance, Core Notes owner, or action-scoped temporary actor |
| `menu_grouping_signal::_import_csv` | Core immutable grouping-signal exchange | Existing `ImportGroupingSignalCsvRequest` has no actor; retains `IMPORT` confirmation and digest check |
| `menu_scan::_route` | Core PDS2 retained-scan intake/dispatch | `route_scan_sources` accepts sources, root, registry, decoder; no WorkflowActor argument; routing resolution/defer already uses reviewed `reviewer` |
| `menu_publication::_register`, `_update_registration` | Core Academic Work Registration | Core request/registry contract is actor-less; preserve revision/currentness and confirmation |
| `menu_publication::_withdraw` | Core Publication Withdrawal | `withdraw_concord_academic_result_publication` has no WorkflowActor parameter; existing `STOP` / `WITHDRAW` checks are retained |
| `menu_publication::_rebuild_catalog` | Core derived catalog rebuild | Does not rewrite canonical publications/registrations; `REBUILD` confirmation remains |
| `menu_packet_generation::_resume_generation` | Recovery of already-durable Packet generation/route lifecycle | `resume_packet_instantiation` takes exact class/activity/generation IDs, not a new actor; no new Packet generation choice |

The Core-owned, actor-less services are **not** changed to accept invented
actor fields. If auditability of scan intake, Core registration, withdrawal,
or recovery must include an adult actor, that needs a separately published
Core/Concord service contract and qualification, not a fabricated provenance
record under #148.

## Evidence and subsequent acceptance

- Python parse, exact AST/source transformation and duplicate-application
  refusal are checked locally against synthetic source fragments.
- The guarded Windows runner authenticates the source ZIP and eleven pinned
  baseline Git blobs; it then runs Ruff, strict mypy, official installed Core
  verification and focused Score/census regressions before any commit.
- Final issue acceptance remains **open**: rerun the complete executable
  census, validate all indirect paths against canonical contracts, full
  Concord pytest/Ruff/mypy, build/install/relaunch tests, Windows/Linux CI,
  and supported Suite-foreground launch smoke evidence on synthetic data.
  No release bump or cross-module identity authority is introduced here.
