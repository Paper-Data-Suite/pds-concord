# Concord #148 — Slice 3: operation-scoped actor confirmation (first integration set)

**Baseline:** `3f80a131352eba7ead28278661648b08878026ec`, after qualified Slice 2. **Core installed contract:** officially released `pds-core==0.6.6`. **Implementation remains Concord-owned.**

## Contract

`MenuSessionContext.actor_for_action(action_label=..., alternate=...)` always revalidates the local saved attribution and its fingerprint before returning an actor. It returns the saved default unless a `TeacherAttributionIdentity(source="temporary")` is explicitly supplied **for the immediate call**. It does not store pending overrides, change the default, or modify the academic workspace. Profile change/reset while a review is open aborts through existing `CancelMenuAction` behavior.

`menu_actor_action.confirm_actor_write` is opt-in on a **consequential confirmation screen**, never a global key handler. It presents the teacher-readable actor, exact ID, original action context and substantive confirmation. `A` permits choosing an alternate ID/name for this operation, `D` restores the default, B/Enter cancel, and the original confirmation verb performs one reviewed save through the existing guarded service. No second generic actor confirmation is inserted. This actor is not login, Core Notes owner, or evidence permission.

For old explicit `MenuSessionContext(actor=...)` test/caller sessions, the existing `confirm_write` callback remains in control and the actor remains explicitly supplied. Direct CLI `--actor-id`, `--actor-label`, and all `WorkflowActor` native fields are unchanged.

## Included real-menu integrations

- Activity creation: exact class/title/first-Session review returns actor before immutable Activity+Session creation.
- Manual GroupPlan creation: unchanged proposal/roster/snapshot semantics and canonical service, but actor is reviewed at same `CREATE` confirmation.
- Retained-scan Routing Review: `DEFER` and `RESOLVE` confirm the intended retained page, exact destination/note and actor, then use the owner service; no implicit student authorship or route approval.

**Deliberately outstanding before #148 release:** the rest of the literal 120 actor callsites (including other GroupPlan mutations, Artifacts, Score, Criteria, bulk placement and publication) have not yet been individually migrated to the actor-selectable review. They retain the verified saved-default actor from Slice 2. A follow-on Slice 3B / qualification audit must explicitly inspect and migrate the remaining relevant consequential review routes before claiming universal alternate actor coverage. Do not close #148 based on this first integration set.

## Safety and qualification

Synthetic cases cover default one-confirmation, alternate use/consumption, cancel, restore default, concurrent profile edit/refusal, wrong source, invalid action label, legacy caller compatibility, a real GroupPlan service request and source-level Activity/Scan handoff guards. Test files use disposable local config roots and never touch classroom/student data. Revalidate with installed Core 0.6.6, Ruff, strict mypy, Windows-focused pytest; full tests in final qualification. Profile stored only in Concord's local OS-user settings, not Core, Meridian or Suite.
