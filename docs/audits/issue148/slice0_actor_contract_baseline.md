# Concord #148 — Slice 0: actor-attribution and cross-PDS baseline

Issue: https://github.com/Paper-Data-Suite/pds-concord/issues/148

Proposed branch: `148-persistent-reviewable-teacher-attribution`

## 1. Exact, observed planning source identities

Observed on 2026-11-08, before implementation. Re-verify these SHAs before applying any later slice.

| Authority | `main` or feature-branch baseline | Release/dependency status |
| --- | --- | --- |
| Concord `main` and checked-out #148 branch | `4f2767e9e927b42dc15441bd31df91e7e6899d76` | Published Concord v0.3.4; source has merged #147 |
| Core `main` | `a0d5e1a50580bbe025f0cad23c7e8524203a52ec` | Published **v0.6.6**; Concord requires `pds-core>=0.6.6,<0.7` |
| Suite `main` | `98649a5816485652a29b5c59e06f4704a7960626` | Published v0.1.0; independent launcher/home work ongoing |
| Meridian `main` | `fc05b248139ce0eb8b58aadddc0c04cc96677d07` | Published v0.4.2 predates source-merged #121 teacher profile |

`concord/menu_context.py` baseline Git blob: `0a35bbfb8c9d53e553a09556fc33ab915713f62a`. The main menu (`concord/menu.py`) blob is `f4423174930394e279a1f24ae7a4d9e72ceabb65`. **These are source facts, not claims that a binary is installed.**

The official `scripts/verify_core_wheel.py` in Concord checks the authenticated published Core 0.6.6 wheel hash `d6d21e426092b0329bcfd69b6fbee44c345edc46794a914d847d5ea73a2b7301`. Slice 0 does not modify or reinstall it.

## 2. Reproduction and evidence labels

| Question | Evidence | Disposition |
| --- | --- | --- |
| Is an Actor cached during one `MenuSessionContext`? | `require_actor()` returns its preexisting `WorkflowActor`; existing `test_menu_actor_is_collected_once_and_reused` verifies this. | **Code and existing-test verified; already implemented.** Do not label it a missing feature. |
| Does the normal top-level menu pass the same session to nested Activity and Scan entry points? | `launch_menu()` allocates one context and `_main_menu_once()` forwards it to both. | **Code-path verified.** Slice 0 adds a regression using the real top-level dispatcher with mocked downstream functions. |
| Can a standalone Activity/Scan submenu construct its own context? | `launch_activity_context_menu`, `launch_advanced_activity_tools_menu`, `launch_activity_management_menu`, and `launch_scan_routing_menu` have `state: MenuSessionContext | None` and allocate a new state if absent. Similar standalone scoring entry points exist. | **Code-path verified; legitimate compatibility path.** Keep callable entry points; supply an injectable provider later. |
| Does actor identity persist after a new Concord process/restart? | `MenuSessionContext.actor` is memory-only; `require_actor()` uses a raw `Actor ID:` prompt and has no local-store read. Two new contexts prompt separately. | **Code-path verified**, with a synthetic process-like characterization; **not a live Suite relaunch trial**. |
| Are reviewable Settings, a provider, a one-action override and user-local attribution storage implemented? | No Concord-local provider module or teacher-attribution Settings entry; no action-bound alternate actor API. | **Absent in inspected source; four strict XFAIL witnesses** until their owning slices. |
| Does a configured actor authenticate a user or grant private Notes ownership? | Concord `WorkflowActor` is caller-supplied immutable provenance; Core #236/#238 reserve Notes security to qualified local OS ownership. | **Contract boundary**; a profile must not be used as authentication. |

No claim of a teacher-observed live same-session failure is made here. The defect is the **absence of a deliberate restart-persistent preference and review/override UX**, while the process cache already works.

## 3. Actor callsite inventory (source-code census)

A literal source scan of Concord menu files at the pinned HEAD identified **120 direct `.require_actor()` callsites in 23 modules**. This is a *lexical inventory*, not proof that every path was interactively exercised or every indirect actor contributor is covered. Expand into an AST and semantic census before the final acceptance gate.

| Menu module (prefix `concord/`) | Direct callsites |
| --- | ---: |
| `menu_activity.py` | 3 |
| `menu_artifact.py` | 18 |
| `menu_artifact_scoring.py` | 2 |
| `menu_group.py` | 5 |
| `menu_group_plan.py` | 13 |
| `menu_group_plan_application.py` | 1 |
| `menu_group_plan_bulk.py` | 1 |
| `menu_group_plan_missing_signal.py` | 1 |
| `menu_group_plan_signal.py` | 1 |
| `menu_guided_activity.py` | 3 |
| `menu_packet.py` | 6 |
| `menu_packet_generation.py` | 6 |
| `menu_presets.py` | 13 |
| `menu_publication.py` | 1 |
| `menu_responsibility.py` | 4 |
| `menu_role.py` | 4 |
| `menu_saved_groupings.py` | 3 |
| `menu_saved_grouping_revisions.py` | 3 |
| `menu_saved_operational_grouping.py` | 1 |
| `menu_scan.py` | 2 |
| `menu_scoring.py` | 19 |
| `menu_session.py` | 2 |
| `menu_template.py` | 8 |
| **Total** | **120** |

The inspected menu modules contained **one raw** `input("Actor ID: ")` in `menu_context.py`; the direct noninteractive CLI instead constructs an explicit `WorkflowActor` from required `--actor-id` in `concord/cli_app/common.py`. A raw string search cannot exclude other indirect or dynamic actor sources. Freeze any newly found sources in Slice 0 follow-up evidence; do not silently reclassify them as tested.

Process-local context constructors include `concord/menu.py` (one), `concord/menu_activity.py` (three), `concord/menu_scan.py` (one), and `concord/menu_scoring.py` (three). Audit actual invocation context before calling any of these redundant prompts. The list reflects construction sites, not eight *live failures*.

## 4. Source/release/ownership matrix

| System | Current source | Usable from published qualified artifact? | #148 implication |
| --- | --- | --- | --- |
| Core | Workspace config helpers and Core-valid identifiers are already public; Core #237 teacher header/command parser exists on `main`. | Workspace/identifier APIs **yes** in v0.6.6; new teacher UI **not** in v0.6.6. | Use only published public config/identifier APIs; do not import source-only teacher UI or `:notes`. |
| Core Notes #238–#240 | Private Notes binding, storage, owner/record/menu remain under development. | No. | Self-declared actor ID must **never** act as a private Notes owner or OS login. |
| Meridian #121 | `meridian/teacher_profile.py` and Settings are source-merged; schema is Meridian-local. | No cross-module profile contract; v0.4.2 predates this work. | Mirror *field meanings and safety principles* only. Never import or read Meridian's private profile file. |
| Suite #49/#52 | Source-first evergreen launcher/teacher-home planning and integration status. | No published authenticated cross-module actor profile. | No Suite code/launcher/config changes; Suite launches foreground Concord process. |
| Concord | Source process-cache; existing CLI explicit actor; published dependency Core>=0.6.6,<0.7. | No durable Concord preference. | Add an isolated `get_workspace_config_path().parent / concord` preference with guarded injection; preserve actor provenance. |

**Proposed storage decision (for Slice 1 to validate):** Concord-private `teacher-attribution-v1.json` in a dedicated user-local `concord` configuration child, not the workspace or shared Core `config.json`, and not `meridian/teacher-profile-v1.json`. Treat it as an attribution preference **not** a shared identity registry, user authentication, Notes owner or cross-module contract. All writes require explicit teacher confirmation and safe CAS/private-path checks. A future Core shared attribution service must be separately designed, released and migrated by explicit decision.

## 5. Ownership of next slices and validation cadence

- **Slice 1:** bounded durable Concord-local store and injectable provider, no main-menu changes, historical record writes or Core/Suite mutations. Convert provider XFAIL only after real persistence/unsafe-path/CAS tests pass.
- **Slice 2:** teacher-facing first-use and Settings, provider-aware shared/standalone sessions, relaunch and workspace freshness; retire Settings/provider-injection XFAILs with behavioral tests.
- **Slice 3:** action-bound alternate actor with Reviewed By/Recorded By context and explicit consumption; preserve B/M/Q, cancel/retry, actor snapshots and direct CLI; retire the remaining override XFAIL.
- **Slice 4:** full repository test/lint/type/build/official-Core-0.6.6 installed-wheel qualification, source-pinned Core/Suite boundary and supported CI; separately disclose non-qualified real classroom/device trial.

The four XFAILs are deliberate **feature witnesses**. XPASS is a failure until the witness is converted to a stronger positive test in its owning slice. All tests use synthetic identities, avoid real user data and do not create or inspect the user's actual profile or classroom workspace. Run focused tests per slice; reserve full-repository validation for Slice 4.
