# Concord #150 — Slice 2: target-roster-only Cluster planning

**Scope:** Six *empty* planned Clusters as a teacher-authorized target-only GroupPlan. No source-class student identities, Memberships, saved arrangements or operational Group records.

**Source baseline:** `150-use-lesson-with-another-class` at `ff45a4199a27f1c54c96626e25cd99230e28d4ff`; Concord `main` at `59df22e07e7fa4e14677bf75cb0089fc0604f9fa`; pinned official Core 0.6.6; latest published Concord v0.3.4. These are source observations, **not** release claims. Slice 1 had 125 focused tests passed and three former witnesses green; runner Repair 1 qualified on Windows before this slice.

## Existing owners composed unchanged

- `concord/workflows/group_plan.py::create_group_plan` is the only canonical draft writer. It validates the *exact target Activity* and snapshot, requires current target Core roster and supports `expected_roster_student_ids`; it does not apply the plan or create Groups/Memberships.
- `concord/menu_group_plan.py` owns proposal editing, Cluster-first bulk placement, preview, approval, application, class-scoped saved arrangements, and guarded errors. Direct Group management remains available from the ordinary Student Groups area.
- `concord/workflows/participants.py::load_required_roster` retrieves the authoritative Core class roster. **Never** use source students or infer target students by display names or shared IDs.
- `concord/menu_standards_context.py::standards_for_activity` resolves the canonical Core Standards library for mixed/standards-based Activity writes; never pass `None` as a workaround.
- `concord/menu_guided_activity.py` is the existing guide. This slice changes only the post-copy **3. Plan target Clusters** entry to a concise target-only preflight; ordinary Create Fresh and general setup remain unchanged.

## Exact target state and safety matrix

| Input | Display/decision | Mutation/result |
| --- | --- | --- |
| 29 target students, no target GroupPlan or Groups | Verified target roster count; even-size **reference** `5 / 5 / 5 / 5 / 5 / 4` | **No student is assigned** by projection. Teacher may explicitly create six empty `draft` planned Clusters, then use existing bulk editor for actual placements. |
| 30 target students, no target plan | Verified target roster count; `5 / 5 / 5 / 5 / 5 / 5` *reference* | Same; individual placement counts may differ (e.g. teacher-selected `6/5/5/3/6/5`). The reference is **not a required capacity**, automatic assignment or assurance of balanced groups. |
| Existing target GroupPlan or canonical Groups | Clearly labeled current counts and route to existing target GroupPlan tools | **No new six-Cluster shape shortcut**. Avoid duplicate target planning; preserve any approved/applied and unrelated draft history. |
| Target Core roster missing/empty, class missing, Activity missing, inconsistent plan ownership | Bounded verification failure | No writes; use existing Core/Concord recovery. |
| Roster or Activity snapshot changes between read, confirmation and commit | Conflict and reread/review | No blind retry; `create_group_plan` enforces both snapshot and exact expected roster. |
| Target plan committed but read-back/receipt cannot be verified | Explicit uncertain outcome | Inspect authoritative target plans; no claim of rollback or automatic retry. |
| Teacher backs out, declines confirmation, chooses Decide later, or requests Help | Read-only projection | No actor prompt or new GroupPlan on simple inspection. |

All newly created plan-local `PlannedGroup` values have `student_ids=()` and have no individual or source context. The exact target roster is stored in the existing GroupPlan's roster/unresolved fields by Concord's canonical writer, **not** transferred from the source. Six planned Clusters are not six operational Groups. Preview/approve/apply remain separate explicit teacher decisions. No packets, PDS2 routes, Scores, Grades, review, publication, or private Notes are created.

### UI / Core / Suite contract

- Concord owns the task view, using existing `print_menu_header`, `print_navigation`, `clear_screen`, `MenuSessionContext`, and existing actor-confirmation helper. No new UI framework, global prompt interceptor or duplicate Core roster editor.
- The accepted Suite Teacher Experience v0.2 and Core Teacher-Experience v1 still govern app/title/context, green when a qualified installed Core renderer permits it, plain fallback, `B/M/Q/H`, concise Review→Confirm→Report→Continue, exact prompt-scoped `:notes` reservation, no raw source identifiers in normal screens, and no invented Notes/Admin availability. Broad adoption of new Core header/Notes remains Concord #153, not #150.
- The Suite Teacher Home retains launch/return authority. No Concord↔Suite or new Core library dependency.

## Qualification and handoff

Source test suite includes synthetic 29/30 target roster read authority, duplicate/foreign plan fail-close, six empty proposed Groups with exact target snapshot/roster pins, independent existing-plan management, no hidden write on Finish/Help, and verified post-commit receipt/recovery. Regress #63, #65, #136, #148, #149 and #150 Slices 0/1. Native installed Core 0.6.6, Ruff, mypy and documentation checks required; no full suite before final Slice 6. Physical student placement and final operational plan application remain teacher-directed via the existing qualified editors. Slice 3 will connect explicit saved Packet/Template selection with new target-only Packet Instances and PDS2 routes, maintaining separate receipts.
