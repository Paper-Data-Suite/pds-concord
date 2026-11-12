# Concord #148 — Slice 3E1 actor callsite census

**Baseline Git HEAD:** `6b2f17f25d59898be4ae273ff3c56eba8030e599`
**Menu Python modules scanned:** 43
**Functions with an actor-resolution or confirmation call:** 124

## Static classification totals

| Class | Function count |
|---|---:|
| `action-reviewed` | 63 |
| `legacy-confirm-with-actor` | 40 |
| `actor-resolved-no-local-review` | 10 |
| `confirm-without-local-actor-resolution` | 11 |

## Interpretation and limitations

- `action-reviewed`: an action-scoped actor confirmation helper is called inside this function; this alone does not prove every request or receipt forwards the reviewed actor.
- `legacy-confirm-with-actor`: an actor is resolved and a legacy confirmation appears in this function; inspect whether this is a consequential canonical write that needs the actor override.
- `actor-resolved-no-local-review`: includes orchestration helpers, authorship semantics, delegates, and potentially uncovered writes. It is a triage queue, not a blanket security-failure assertion.
- `confirm-without-local-actor-resolution`: may be a Core operation whose existing contract has no WorkflowActor; do not invent one.
- AST nesting and aliasing can hide indirect paths. This is a complete static enumeration of top-level `menu*.py` functions, **not** end-to-end proof of authorization or deployed acceptance.
- Direct noninteractive CLI retains explicit actor requirements. No real student data, user profiles, or OS config files were read.

## All candidate functions

| Source:line | Function | Classification | Actor resolutions | Actor reviews | Legacy reviews | `actor=` args |
|---|---|---|---:|---:|---:|---:|
| `concord/menu_activity.py:331` | `_create_activity` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_activity.py:600` | `_copy_activity` | `actor-resolved-no-local-review` | 1 | 0 | 0 | 1 |
| `concord/menu_activity.py:709` | `_update_activity_field` | `legacy-confirm-with-actor` | 1 | 0 | 1 | 0 |
| `concord/menu_actor_action.py:54` | `confirm_actor_write` | `actor-resolved-no-local-review` | 5 | 0 | 0 | 0 |
| `concord/menu_actor_action.py:138` | `confirm_prepared_actor_write` | `action-reviewed` | 0 | 1 | 0 | 0 |
| `concord/menu_artifact.py:205` | `_prepare` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_artifact.py:291` | `_render` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_artifact.py:596` | `_assemble` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_artifact.py:690` | `_choose_author_semantics` | `actor-resolved-no-local-review` | 1 | 0 | 0 | 0 |
| `concord/menu_artifact.py:909` | `_add_author` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_artifact.py:979` | `_update_author` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_artifact.py:1028` | `_correct_author` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_artifact.py:1370` | `_add_subject` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_artifact.py:1430` | `_update_subject` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_artifact.py:1476` | `_correct_subject` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_artifact.py:1881` | `_quick_review_selected` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_artifact.py:2004` | `_record_review_selected` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_artifact.py:2234` | `_replace_review` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_artifact.py:2803` | `_record_moderation` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_artifact.py:2868` | `_replace_moderation` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_artifact.py:3127` | `_commit_attribution_confirmation` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_artifact.py:3279` | `_add_multiple_authors` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_artifact.py:3337` | `_add_multiple_subjects` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_artifact_scoring.py:462` | `_record_selected_artifact_score` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_artifact_scoring.py:596` | `_record_another_criterion` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_group.py:168` | `_create_group` | `legacy-confirm-with-actor` | 1 | 0 | 1 | 1 |
| `concord/menu_group.py:290` | `_edit_group` | `legacy-confirm-with-actor` | 1 | 0 | 1 | 0 |
| `concord/menu_group.py:461` | `_add_member` | `legacy-confirm-with-actor` | 1 | 0 | 1 | 1 |
| `concord/menu_group.py:514` | `_end_member` | `legacy-confirm-with-actor` | 1 | 0 | 1 | 1 |
| `concord/menu_group.py:589` | `_reassign_member` | `legacy-confirm-with-actor` | 1 | 0 | 1 | 1 |
| `concord/menu_group_plan.py:199` | `_create_manual` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_group_plan.py:250` | `_create_random` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_group_plan.py:358` | `_import_arrangement` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_group_plan.py:417` | `_add_group` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_group_plan.py:472` | `_edit_group` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_group_plan.py:525` | `_remove_group` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_group_plan.py:618` | `_place_student` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_group_plan.py:657` | `_unassign_student` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_group_plan.py:693` | `_refresh_roster` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_group_plan.py:727` | `_replace_arrangement` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_group_plan.py:770` | `_preview` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_group_plan.py:804` | `_approve` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_group_plan.py:843` | `_cancel` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_group_plan_application.py:85` | `apply_approved_group_plan_from_menu` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_group_plan_bulk.py:130` | `_review_batch` | `actor-resolved-no-local-review` | 4 | 0 | 0 | 2 |
| `concord/menu_group_plan_bulk.py:278` | `launch_cluster_bulk_editor` | `actor-resolved-no-local-review` | 1 | 0 | 0 | 1 |
| `concord/menu_group_plan_missing_signal.py:103` | `resolve_missing_signal_from_menu` | `action-reviewed` | 0 | 3 | 0 | 1 |
| `concord/menu_group_plan_signal.py:268` | `create_signal_group_plan_from_menu` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_grouping_signal.py:296` | `_import_csv` | `confirm-without-local-actor-resolution` | 0 | 0 | 1 | 0 |
| `concord/menu_guided_activity.py:169` | `_create_fresh` | `legacy-confirm-with-actor` | 1 | 0 | 1 | 1 |
| `concord/menu_guided_activity.py:225` | `_create_from_activity` | `legacy-confirm-with-actor` | 1 | 0 | 1 | 1 |
| `concord/menu_guided_activity.py:532` | `_start_packet_from_template` | `legacy-confirm-with-actor` | 1 | 0 | 1 | 1 |
| `concord/menu_packet.py:275` | `_create` | `legacy-confirm-with-actor` | 1 | 0 | 1 | 1 |
| `concord/menu_packet.py:321` | `_revise` | `legacy-confirm-with-actor` | 1 | 0 | 1 | 1 |
| `concord/menu_packet.py:369` | `_activate` | `legacy-confirm-with-actor` | 1 | 0 | 1 | 1 |
| `concord/menu_packet.py:412` | `_update` | `legacy-confirm-with-actor` | 1 | 0 | 1 | 1 |
| `concord/menu_packet.py:455` | `_retire_version` | `legacy-confirm-with-actor` | 1 | 0 | 1 | 1 |
| `concord/menu_packet.py:493` | `_retire` | `legacy-confirm-with-actor` | 1 | 0 | 1 | 1 |
| `concord/menu_packet_generation.py:150` | `_generate` | `legacy-confirm-with-actor` | 4 | 0 | 1 | 4 |
| `concord/menu_packet_generation.py:1054` | `_render_generation` | `legacy-confirm-with-actor` | 1 | 0 | 1 | 1 |
| `concord/menu_packet_generation.py:1240` | `_render_instance` | `legacy-confirm-with-actor` | 1 | 0 | 1 | 1 |
| `concord/menu_presets.py:312` | `_create_role` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_presets.py:340` | `_create_responsibility` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_presets.py:380` | `_create_scale` | `action-reviewed` | 2 | 1 | 0 | 1 |
| `concord/menu_presets.py:570` | `_create_criterion` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_presets.py:635` | `_edit_role` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_presets.py:678` | `_edit_responsibility` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_presets.py:763` | `_edit_scale` | `action-reviewed` | 2 | 1 | 0 | 1 |
| `concord/menu_presets.py:856` | `_edit_criterion` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_presets.py:934` | `_retire` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_publication.py:141` | `_register` | `confirm-without-local-actor-resolution` | 0 | 0 | 1 | 0 |
| `concord/menu_publication.py:170` | `_update_registration` | `confirm-without-local-actor-resolution` | 0 | 0 | 1 | 0 |
| `concord/menu_publication.py:230` | `_manifest_request` | `actor-resolved-no-local-review` | 1 | 0 | 0 | 1 |
| `concord/menu_publication.py:322` | `_generate` | `action-reviewed` | 0 | 1 | 0 | 0 |
| `concord/menu_publication.py:420` | `_publish` | `action-reviewed` | 0 | 1 | 0 | 0 |
| `concord/menu_publication.py:532` | `_withdraw` | `confirm-without-local-actor-resolution` | 0 | 0 | 2 | 0 |
| `concord/menu_publication.py:651` | `_rebuild_catalog` | `confirm-without-local-actor-resolution` | 0 | 0 | 1 | 0 |
| `concord/menu_responsibility.py:200` | `_assign` | `legacy-confirm-with-actor` | 1 | 0 | 2 | 2 |
| `concord/menu_responsibility.py:297` | `_save_responsibility_as_preset` | `legacy-confirm-with-actor` | 1 | 0 | 1 | 1 |
| `concord/menu_responsibility.py:353` | `_end` | `legacy-confirm-with-actor` | 1 | 0 | 1 | 1 |
| `concord/menu_responsibility.py:423` | `_reassign` | `legacy-confirm-with-actor` | 1 | 0 | 1 | 1 |
| `concord/menu_role.py:226` | `_assign` | `legacy-confirm-with-actor` | 1 | 0 | 2 | 2 |
| `concord/menu_role.py:313` | `_save_role_as_preset` | `legacy-confirm-with-actor` | 1 | 0 | 1 | 1 |
| `concord/menu_role.py:374` | `_end` | `legacy-confirm-with-actor` | 1 | 0 | 1 | 1 |
| `concord/menu_role.py:445` | `_reassign` | `legacy-confirm-with-actor` | 1 | 0 | 1 | 1 |
| `concord/menu_saved_grouping_revisions.py:45` | `_current` | `actor-resolved-no-local-review` | 1 | 0 | 0 | 0 |
| `concord/menu_saved_grouping_revisions.py:61` | `_change` | `legacy-confirm-with-actor` | 1 | 0 | 1 | 0 |
| `concord/menu_saved_grouping_revisions.py:161` | `_show_history` | `actor-resolved-no-local-review` | 1 | 0 | 0 | 0 |
| `concord/menu_saved_groupings.py:62` | `_saved` | `actor-resolved-no-local-review` | 1 | 0 | 0 | 0 |
| `concord/menu_saved_groupings.py:135` | `save_grouping_from_plan` | `legacy-confirm-with-actor` | 1 | 0 | 1 | 1 |
| `concord/menu_saved_groupings.py:227` | `_collect_decisions` | `confirm-without-local-actor-resolution` | 0 | 0 | 1 | 0 |
| `concord/menu_saved_groupings.py:287` | `use_saved_grouping` | `legacy-confirm-with-actor` | 1 | 0 | 2 | 1 |
| `concord/menu_saved_operational_grouping.py:55` | `save_grouping_from_existing_groups` | `legacy-confirm-with-actor` | 1 | 0 | 2 | 2 |
| `concord/menu_scan.py:258` | `_route` | `confirm-without-local-actor-resolution` | 0 | 0 | 1 | 0 |
| `concord/menu_scan.py:496` | `_review` | `action-reviewed` | 0 | 2 | 0 | 0 |
| `concord/menu_scoring.py:300` | `_create_scale` | `action-reviewed` | 2 | 1 | 0 | 1 |
| `concord/menu_scoring.py:395` | `_revise_scale` | `action-reviewed` | 2 | 1 | 0 | 1 |
| `concord/menu_scoring.py:593` | `_import_saved_scale` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_scoring.py:879` | `_create_criterion_set` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_scoring.py:974` | `_create_guided_criterion_set` | `action-reviewed` | 1 | 1 | 0 | 1 |
| `concord/menu_scoring.py:1231` | `_revise_criterion_set_advanced` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_scoring.py:1339` | `_select_criterion_sets_advanced` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_scoring.py:1865` | `_score_components` | `actor-resolved-no-local-review` | 1 | 0 | 0 | 0 |
| `concord/menu_scoring.py:1972` | `_record_score` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_scoring.py:2111` | `_revise_score` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_scoring.py:2221` | `_save_scale_id_as_preset` | `action-reviewed` | 1 | 1 | 0 | 2 |
| `concord/menu_scoring.py:2379` | `_save_criterion_set_as_preset` | `action-reviewed` | 1 | 1 | 0 | 2 |
| `concord/menu_scoring.py:2614` | `_use_existing_criterion_set` | `action-reviewed` | 0 | 1 | 0 | 1 |
| `concord/menu_scoring.py:2826` | `_revise_criterion_set` | `action-reviewed` | 1 | 1 | 0 | 1 |
| `concord/menu_scoring.py:3243` | `_use_saved_scoring_setup` | `action-reviewed` | 1 | 1 | 0 | 2 |
| `concord/menu_session.py:134` | `_add` | `legacy-confirm-with-actor` | 1 | 0 | 1 | 1 |
| `concord/menu_session.py:202` | `_edit_field` | `legacy-confirm-with-actor` | 1 | 0 | 1 | 0 |
| `concord/menu_teacher_settings.py:129` | `_setup` | `confirm-without-local-actor-resolution` | 0 | 0 | 1 | 0 |
| `concord/menu_teacher_settings.py:164` | `_rename` | `confirm-without-local-actor-resolution` | 0 | 0 | 1 | 0 |
| `concord/menu_teacher_settings.py:199` | `_replace` | `confirm-without-local-actor-resolution` | 0 | 0 | 1 | 0 |
| `concord/menu_teacher_settings.py:240` | `_reset` | `confirm-without-local-actor-resolution` | 0 | 0 | 1 | 0 |
| `concord/menu_template.py:248` | `_create` | `legacy-confirm-with-actor` | 1 | 0 | 1 | 1 |
| `concord/menu_template.py:307` | `_revise` | `legacy-confirm-with-actor` | 1 | 0 | 1 | 1 |
| `concord/menu_template.py:364` | `_activate` | `legacy-confirm-with-actor` | 1 | 0 | 1 | 1 |
| `concord/menu_template.py:408` | `_update` | `legacy-confirm-with-actor` | 1 | 0 | 1 | 1 |
| `concord/menu_template.py:452` | `_retire_version` | `legacy-confirm-with-actor` | 1 | 0 | 1 | 1 |
| `concord/menu_template.py:491` | `_retire` | `legacy-confirm-with-actor` | 1 | 0 | 1 | 1 |
| `concord/menu_template.py:595` | `_install_starter` | `legacy-confirm-with-actor` | 1 | 0 | 1 | 1 |
| `concord/menu_template.py:645` | `_install_all_starters` | `legacy-confirm-with-actor` | 1 | 0 | 1 | 1 |

## Follow-on acceptance gate

1. Manually disposition each `legacy-confirm-with-actor` and `actor-resolved-no-local-review` function as an actor-attributed write needing action review, an already-covered delegated write, a non-mutating helper, or a different service contract.
2. Convert uncovered consequential writes in bounded slices, retaining exact review/actor forwarding, CAS, privacy, and no-write cancellation safeguards.
3. Re-run this source-pinned census, the full Concord suite, strict typing, packaging, installed-wheel acceptance, and CI **before** marking #148 merge-ready.
