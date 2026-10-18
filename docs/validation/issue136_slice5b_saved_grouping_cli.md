# Issue #136 — Slice 5B: saved-grouping direct CLI

**Baseline:** `753c0bc79774a2ccdede1e2c3388e2ca761134d` (Slice 5A).
**Target release:** Concord v0.3.4 (unchanged in this slice).
**Core contract:** PDS Core v0.6.6; no new dependency.

## Public command surface

`concord saved-grouping` provides `list`, `show`, `roster-diff`, `save-preview`, `save`, `reuse-preview`, and `reuse`. These are direct, noninteractive wrappers around the Slice 3–4 immutable class-arrangement library and reviewed GroupPlan services. No alternate plan materialization or group assignment engine is introduced.

All commands require `--class-id` and `--actor-id`, plus `--workspace-root` when not relying on canonical workspace configuration. Source and target Activity commands also require `--activity-id`, `--expected-snapshot` and the relevant IDs. The existing `--standards-library` optional override is preserved for standards-backed **reuse commits**; otherwise the canonical Core workspace library is used.

For example, with an already edited source GroupPlan:

```powershell
$concord = 'python -m concord'
# Run the commands below as: python -m concord ...
python -m concord saved-grouping save-preview --class-id class-1 --activity-id source-1 --group-plan-id plan-1 --arrangement-id six-tables --name 'Six tables' --expected-snapshot 6 --actor-id teacher-1
python -m concord saved-grouping save --class-id class-1 --activity-id source-1 --group-plan-id plan-1 --arrangement-id six-tables --name 'Six tables' --expected-snapshot 6 --actor-id teacher-1 --review-digest <digest-from-preview>
python -m concord saved-grouping list --class-id class-1 --actor-id teacher-1
python -m concord saved-grouping show --class-id class-1 --arrangement-id six-tables --actor-id teacher-1
python -m concord saved-grouping roster-diff --class-id class-1 --arrangement-id six-tables --actor-id teacher-1
python -m concord saved-grouping reuse-preview --class-id class-1 --activity-id target-2 --arrangement-id six-tables --new-group-plan-id reused-six-tables --expected-snapshot 3 --actor-id teacher-1
python -m concord saved-grouping reuse --class-id class-1 --activity-id target-2 --arrangement-id six-tables --new-group-plan-id reused-six-tables --expected-snapshot 3 --actor-id teacher-1 --review-digest <digest-from-preview>
```

These examples use synthetic identities. `roster-diff` reveals which exact students need decisions before `reuse-preview` can succeed. Reuse on a changed roster additionally requires exact `--place STUDENT_ID=GROUP_KEY`, `--leave-unresolved STUDENT_ID`, and/or `--acknowledge-departed STUDENT_ID` flags, repeated as needed. Existing target GroupPlans require `--acknowledge-existing-plans`. Placement decisions must be unique. Follow the CLI preview and service validation; never silently assign by student names.

## Safety and parity guarantees

- `list` exposes name, revision, status and counts but **no student IDs**. `show` prints counts and labels; individual Core IDs require `--show-members`. `roster-diff` is an explicitly requested read-only check which displays affected exact student IDs; it works before placement decisions are entered. `reuse-preview --show-placements` opt-in displays all intended placements for precise audit. The caller must present the owning teacher's actor ID, and storage enforces exact class/year/owner scope.
- `save-preview` and `reuse-preview` call read-only service methods and never write. The corresponding writes require `--review-digest` produced from the same request parameters. Services re-prepare and compare the source revision, current Activity snapshot, target roster and saved revision/digest before mutation.
- Saving captures reusable configuration only. Reuse creates **a draft GroupPlan**, not canonical Groups/Memberships, Scoring, Feedback, routing or publication records. Existing preview → approve → apply remains mandatory before canonical Groups and Memberships.
- No implicit revision, retire, operational Group save, or CSV interchange is added here. Those are later #136 slices.
- The CLI maps arrangement concurrency/ownership conflicts to established exit **3**, storage/integrity errors to exit **1**, and argparse usage errors to exit **2**. No stack trace on expected errors.
- Focused boundary tests cover parser/help, required actor/review digest, count-only list/show, opt-in exact member/placement details, read-only roster differences, exact request/digest/standards forwarding, no-commit preview, malformed and duplicate placement decisions, and stable conflict/error codes. Existing menu and GroupPlan CLI tests are also included in the gate.

## Release notes / follow-ups

Do not release or install from this branch. Complete storage revision/retirement and unambiguous operational-Group saving; run synthetic six-group/29-student integration and cross-mode scoring/publication acceptance; then perform candidate wheel/CI/release gates for v0.3.4.
