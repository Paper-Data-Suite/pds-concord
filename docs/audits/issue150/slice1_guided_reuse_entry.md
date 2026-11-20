# Concord #150 — Slice 1: source-to-target teacher journey

**Starting Git head:** `f4e0f05d93cc88256410bad125bb6e7a51b28095` (`150-use-lesson-with-another-class`); parent source and all witnesses qualified as Slice 0. **No Core/Suite source changes.**

## Change boundary

The existing `Create Classroom Activity → Start from another Activity` becomes the recognizable **Use this lesson with another class** entry. `_create_from_activity` retains the canonical #63 `prepare_activity_copy` → review digest → actor-confirmed `copy_activity` sequence and fresh planned Session. `activity_copy.py` remains unchanged. The copy review is expanded into a legible *carry / new target / choose saved definitions later / never carry* list with target privacy and validated Focus Standards count. No source student data is read for this teacher preview.

Following a successful copy, the existing creation-result screen still offers **1 Continue setup now / 2 Finish for now**, plus four explicit *target-only* choices: Plan target Clusters; Choose saved classroom materials; Use saved rubric/assessment; Review target setup. Every choice reloads the target Activity and delegates to Concord's already guarded owned task menus. Nothing is automatically applied, generated, scored or published; the teacher decides separately. The fresh Activity route keeps its original two choices.

## Existing UI and authority preserved

- Concord's standard `print_menu_header`, compact redraw and `H/B/M/Q` navigation; no global `input()` interception, no unauthorized `:notes` service or invented Core/Suite home.
- Core's canonical class, roster, Standards and native navigation remain authoritative. No cross-class saved-arrangement association is created in this slice; target grouping and roster-reconciliation orchestration are Slice 2.
- Existing saved Packet/Template and Scale/Criterion selection flows own their writes in subsequent slices; this handoff only makes them discoverable. Do not interpret the header as qualified green Core `terminal.header.v1` on official Core 0.6.6. Broad Concord header adoption remains #153.
- #149 read-only `Before class`/`All attention` and its source-backed returned evidence remain unchanged. No physical printing, distribution or return claim.

## Proof and handoff

Retire the exact three `strict=True` XFAILs from Slice 0; all become normal GREEN regressions. Add target re-read, direct owner-menu selection, zero-hidden-work Finish, same-class fresh choice, navigation and preview boundary tests. Verify #63/#65/#149 regression families, Ruff, strict mypy and docs. Native Windows qualification remains required before a commit/push; no full-repository run for this bounded slice.

**Slice 2:** independent Core target roster and reviewed six-Cluster plan, making source class arrangements explicitly ineligible unless valid target-class arrangements are selected and reconciled. No new wizard persistence.
