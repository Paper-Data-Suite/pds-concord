# Concord #150 Slice 3 — exact target materials checkpoint and duplicate-safe guide

**Status:** Slice 3 source candidate. Native Windows and installed distribution qualification **pending**.
**Baseline:** `150-use-lesson-with-another-class` `513bbafedd9422b821c83165367307aa685526c5`, parent `ff45a4199a27f1c54c96626e25cd99230e28d4ff`, main `59df22e07e7fa4e14677bf75cb0089fc0604f9fa`.
**Core published baseline:** official v0.6.6. Never infer Core source-only green header, `:notes` execution or shared administration availability.
**UI:** Suite teacher experience design specification v0.2 / Core teacher-experience v1 govern labels, Back/Main/Quit/Help, review/confirm/report/continue and capability-qualified headers. Concord #153 owns the broad UI adoption.

## Owner and operation table

| Operation | Source of truth | Slice 3 action |
| --- | --- | --- |
| Read active target | Core class and current Concord Activity | Exact class-qualified activity only; zero writes |
| Read target preparation | `concord.workflows.packet_generation.list_packet_generations` | Exact snapshot-backed generation projection; no source class reads |
| Choose saved materials | Existing saved Packet / Template selectors | Existing teacher-readable, opt-in choices; no inferred source Packet |
| Create target Packet/Artifacts/Pages/PDS2 routes | Existing packet instantiation and render services | No alternate writer or route registry |
| Incomplete route/render work | Existing Packet generation recovery menu | Present recovery/inspection before new target generation |
| Add copies deliberately | Existing `generate_saved_packet` review/confirm | Requires explicit *additional copies* choice if target has prior generations |
| Report new target generation | Read `list_packet_generations` again | Compare exact generation IDs and report counts/status, not printing |
| Reuse old student or route records | **Forbidden** | No source class, Group, Membership, scan, generated PDF, score or route cloning |

## Checkpoint truth and no implicit retries

`TargetMaterialsCheckpoint` has exact class, Activity, Activity snapshot and zero or more native generation summaries. It will refuse mismatched class/Activity identities, duplicate generation IDs and inconsistent revisions. No lookup by title, no fuzzy selection, no write from inspection. The count of `route_count` means **recorded route-required pages**; it is **not** an independent authenticated PDS2 route-registry or physical-custody attestation. The established instantiation writer remains responsible for route registration, partial-success receipts and recovery.

On entry, if any existing target generation has routes pending, failed/cancelled/planned or rendering state, the guide offers existing recovery/inspection rather than directly presenting an additional-generation action. A fully generated target set can be inspected/reprinted, or the teacher may explicitly choose **Prepare ADDITIONAL target copies (a new generation)**. No matching Packet, saved Template, Session or target is inferred. Existing ownership and generated Instance/Artifact uniqueness checks stay in the writer.

The guide rereads workspace, exact target snapshot and observed generation IDs immediately before handing off to the existing materials chooser. A changed workspace/generation set/snapshot fails closed and requests fresh review. After the existing menu exits, it rereads the canonical target and compares observed generation IDs: zero new = no verified generation, exactly one new = list recorded packets/pages/ready status/route-required pages, multiple new = inspect individual generation history, failed reinspection = **possibly committed; no blind retry**. A cancelled stage may have saved no generation; creating a saved reusable Packet definition is an independent durable operation and is never mislabeled as a generated set. No action in this guide silently produces a second generation.

The selected saved Packet's current Version is checked again by `_generate` before even previewing packet instantiation; a changed version requires explicit re-selection and review. The existing prepare/commit stage retains its own exact dependency, routing and snapshot checks. No new Core/Suite APIs, data schema, release/version or private source authority are added.

## Failing/negative and positive test scenarios

1. Target-only Core class/Activity and native generation reader, with synthetic data and no source-class reads.
2. Cross-class or cross-Activity generation reference rejected before action.
3. Two snapshots with exact new generation ID difference; disappearance/conflict fails closed.
4. Routes-pending/failed generation directs to existing recovery, never hidden new generation.
5. Already generated preparation remains read-only until an explicit *additional copies* selection.
6. First-generation path uses only existing saved chooser/commit owner and independently re-reads target.
7. No new generation after cancel creates no fictional success; unseen/uncertain post-commit outcome requires inspection.
8. Changed saved Packet current Version blocks before instantiation preview/write.
9. Existing #63/#65/#136/#149/#150 cross-class, grouping, version and attention boundaries preserved; direct CLI unaffected.
10. Non-color Concord headers, B/M/Q/H and Core/Suite prompt scope retained; `:notes` remains inert without qualified public Core service.

## Not part of this bounded slice

Independent Core PDS2 registry custody/returned scan verification; printer/scanner/physical classroom tests; user-to-user copy/export; new Packet/Template authoring; Scales/Criterion reuse (#150 Slice 4); broad UI adoption (#153); group/roster writes; automatic provenance links; published wheel qualification. Later Slice 5/6 exercise installed composition and complete restart/partial durability. Claims must continue to distinguish observed source state from installed and physical acceptance.
