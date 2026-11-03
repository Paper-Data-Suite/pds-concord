# #145 Slice 3 — Create & Use, exact selection read, partial-success recovery

Starting guard: Concord #145 qualified Slice 2 cumulative Git tree `37dc94def248e947c8809687e23fe3d061ba9a8a`, base `5aeb1ae3f98a4bac1439dcd46a802241ab3a9dc8`. The candidate tree is reconstructed from the **qualified files already in the teacher's checkout** and compared to the exact Slice 2 tree, not guessed from filenames or new archives. No commit is created.

## Ownership and cross-repository noncollision

- **Core #235, #238–#244:** no Core files, roster/Standards services, shared terminal commands, Notes private storage, or callable Workspace & Classroom Management menus are modified. The new read-only selection accessor is a Concord workflow and uses the existing Core-canonical guarded graph loader, not a Core data-model modification.
- **Suite #49/#51:** no Suite manifest, launcher, installed-release attestation, teacher-home implementation, or shared UI service is created. The sequence respects the accepted **choose → review → confirm → report → continue** and UX-04 principles using existing Concord menu helpers, while leaving producer adoption/compatibility certification to Suite.
- **Meridian #124/#127/#128:** no Grade Item, proficiency aggregation, Grade, or policy is created; native rubric selection is exclusively Concord authority.
- **Concord #143/#144/#150/#152/#162:** native revisions, typed Scales, existing preset materialization, cross-class lesson copying, score recording and broader semantic inventory remain owned by those scopes. Slice 3 has no preset write, Score, or student/Group mutation.

## Qualified design

1. Native Create only remains option 7 and retains the formerly tested `_create_guided_criterion_set` default behavior. Advanced native creation stays option 6.
2. Ordinary option 1 becomes **Create and use a rubric**. After a single affirmative `CREATE & USE` review, it invokes existing native `create_criterion_set` and then existing `select_activity_criterion_sets`, with **no additional teacher approval** for the same reviewed intent.
3. New read-only `read_activity_criterion_set_selection` exposes the canonical Activity's exact **ordered** `criterion_set_ids` and snapshot. `list_criterion_sets` sorts by lineage and must not be used to reconstruct authoritative selection order.
4. The path reads selection before review, verifies the unchanged snapshot; after the native create it re-reads selection and requires exact original order and the exact newly committed snapshot before writing. It appends only the new Set ID, preserving existing selections; the selection workflow still guards validity and historical-score usage.
5. After selection, it re-reads and verifies the exact selected tuple and returned snapshot. A successful receipt states the verified state only. The two writes remain **separate, durable operations**, not a claimed atomic transaction.
6. If selection fails or the second result is uncertain, the already-created native Set is **never automatically recreated**. A canonical read distinguishes `Verified After Error`, `Selection Requires Review`, and `Selection Outcome Unknown`, with a safe route to explicitly select the **existing** Set.
7. The existing Slice 2 ordinary-menu routing test is intentionally updated from the old Create-only behavior. No original test assertion is deleted; it now asserts the new wrapper dispatch. New tests exercise cancellation, selection order, successful verification, stale/read failures, and post-commit error recovery.

## Qualification boundaries

Guard original `main` + branch + remote, empty index, exact Slice 2 staged reconstructed tree, exact touched file inventory, source SHA-256 manifest, verified published Core wheel and the frozen #140 audit. Run import-only Ruff fixes confined to changed Python files, prove AST equivalence before/after, then Ruff, strict mypy and targeted pytest for #145, #144 and existing Criterion workflows. Capture logs and exact candidate tree. Mirror new/modified source only after full qualification; never commit, push, create PR or publish from this slice.
