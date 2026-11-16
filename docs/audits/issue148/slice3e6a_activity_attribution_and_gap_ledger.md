# Concord #148 — Slice 3E6A Activity actor coverage

Starting commit: `046dbd94abffb3b8888e5ba02368b1c4721395fc`

## Qualified conversion scope

- `concord/menu_activity.py::_copy_activity`: retains `_confirm_copy` (the established exact `COPY` review) for legacy/no-provider sessions while routing provider-backed reviews through `confirm_actor_write`. The canonical `CopyActivityRequest.actor` receives the confirmed value; preexisting digest, privacy and Standards logic are unchanged.
- `concord/menu_activity.py::_update_activity_field`: defers actor selection until the `UPDATE` review; retains Activity snapshot/source workspace/Standards authority checks and forwards that actor into `UpdateActivityRequest`.
- Cancel/back yields no write, and the persisted default never changes from temporary review. Direct noninteractive CLI is untouched.

## Open source-census candidates — not final acceptance

The earlier 3E1 census was deliberately a **triage queue**, not a final signoff. A 2026-11-14 manual source inspection at starting branch `046dbd9` identified additional unresolved consequential or delegated paths. Do **not** infer `#148` is merge-ready solely from the previous percentage estimates.

| Source / function | Observed callsite | Next disposition |
|---|---|---|
| `menu_guided_activity.py::_create_fresh` | legacy confirmation + actor resolution + Activity creation | Convert with exact actor review |
| `menu_guided_activity.py::_create_from_activity` | legacy confirmation + actor resolution + Activity copy | Convert with exact actor/digest review |
| `menu_guided_activity.py::_start_packet_from_template` | legacy confirmation + actor resolution + packet commit | Convert digest-bound request/preview |
| `menu_packet_generation.py::_generate` | legacy confirmation + actor resolution + packet instantiation | Convert prepared packet actor/digest |
| `menu_packet_generation.py::_render_generation` | legacy confirmation + actor resolution + packet rendering | Review actor and render receipt |
| `menu_packet_generation.py::_render_instance` | legacy confirmation + actor resolution + packet rendering | Review actor and render receipt |
| `menu_group_plan_bulk.py::_review_batch` / `launch_cluster_bulk_editor` | actor resolution in delegated bulk path | Verify actual final reviewed actor forwarded to bulk commit; convert if needed |
| `menu_scan.py::_route` | legacy confirmation; no local actor resolution | Review scan routing service actor contract; don't invent an actor parameter |
| `menu_publication.py::_register`, `_update_registration`, `_withdraw`, `_rebuild_catalog` | legacy confirmation; no local actor resolution | Review published registration/catalog service actor contract; don't invent one |
| `menu_grouping_signal.py::_import_csv` | legacy confirmation; no local actor resolution | Review import service actor contract |
| `menu_artifact.py::_choose_author_semantics` | actor resolved in selection helper | Verify authorship semantics/read-only choice, no independent write |
| `menu_publication.py::_manifest_request` | actor resolved during request preparation | Verify caller is actor-reviewed, with exact forwarding |
| `menu_scoring.py::_score_components` | actor resolved in helper | Verify caller is actor-reviewed, with exact forwarding |
| `menu_saved_groupings.py::_saved`, `_collect_decisions` | browse/acknowledge | Keep as read-only and nonwrite acknowledgments |
| `menu_saved_grouping_revisions.py::_current`, `_show_history` | actor-scoped browse/history | Keep as read-only identity-scoped lookups |

Other menu modules still require exact function-by-function census reconciliation, and installed-wheel/source/consumer acceptance remain separate gates. The final census must be regenerated **after** converting all outstanding consequential actor writes, not inferred from this source-only inspection.
