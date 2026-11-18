# Concord #150 — Slice 5: truthful copy handoff and durable resume

**Status:** Source candidate; Windows qualification pending.
**Branch:** `150-use-lesson-with-another-class`; base `a930f59821fbb2535cb8510532a0c3e504d1cd0d`.
**Scope:** Guided copy and canonical setup resume; no schema, migration, Core/Suite UI interface, new writer or release change.

## Failure and recovery contract

| Interruption boundary | Safe teacher result | Next operation |
| --- | --- | --- |
| Cancel before `copy_activity` | No new target write requested | Start again only after fresh review |
| Copy returned, target readback unavailable/wrong identity | **Unconfirmed**; target title/class shown; never infer rollback | Inspect exact target via Continue Classroom Setup; no automatic second copy |
| Copy and target verified, terminal EOF before continuation | Existing target retained; continuation interrupted | Reopen existing target; don't recopy |
| After GroupPlan save/approval | Existing target status reread; no wizard cursor | Inspect/continue original target GroupPlan tools |
| After Packet commit, routes/render pending | Existing generation remains; no duplicate generation | Use native packet recovery/reprint, confirm routes separately |
| After saved Scale/Criterion materialization | Reinspect native target definitions and selection | Use assessment-only setup; do not import again without explicit review |
| Target stage readback wrong class/Activity or unavailable | **Unconfirmed**; no stage launched by guide | Reselect exact target; protect other classes |
| Resume status read wrong identity or has opaque error | Sanitized verification failure | Reselect and inspect; no automatic mutation |
| Finish for now/Back/Help | No new write | Continue from target later |

`copy_activity` remains the sole create-only/digest-authorized copy writer, with a new planned first Session and no source student, Group, Grade, Score, scan or route transfer. This slice deliberately makes no false claim of physical printing, distribution, return, or full installed-wheel end-to-end teacher acceptance.

### Evidence tiers and remaining scope

- **Source candidate:** focused synthetic menu-level interruption tests, no real student records.
- **Native gate:** official Core 0.6.6, Ruff, mypy, docs, prior three witnesses, #63/#64/#65/#136/#145/#148/#149/#150 focused regressions.
- **Separate Slice 6:** single consolidated full-repo source validation, isolated candidate Concord wheel and CI, installed consumer/Windows fallback evidence; physical printer/scanner walkthrough explicitly **NOT YET PHYSICALLY QUALIFIED**.
- `NO_COLOR`/`TERM=dumb` and B/M/Q/H use established Concord menu helpers; no imaginary Core 0.6.6 header/Notes/admin API. Broader shared UI belongs to #153.
