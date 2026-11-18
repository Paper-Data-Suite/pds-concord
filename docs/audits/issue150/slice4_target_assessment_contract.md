# Concord #150 Slice 4 — typed target Assessment setup and receipt

**Status:** bounded candidate, pending Windows and distribution qualification.
**Baseline:** feature branch `150-use-lesson-with-another-class`, parent commit `f4bfef79fb740b07b0110fcd9dc8cf953d436185`; installed official Core version 0.6.6.

## Scope and authority

- Source Activity copy remains create-only: no source Score, Criterion Set, Scale, rubric selection, Score analysis, moderation or student evidence is transferred.
- Target-only inspection consults Core class metadata, current Concord Activity, native Scoring Scale revisions, Criterion Set revisions and exact selected rubric order, and existing Score identities. Every native row must agree on the target class, target Activity and snapshot; disagreement fails closed.
- Teacher sees compact counts, not students, Score values or raw internal IDs. Existing target configuration is preserved. Repeating the guide never creates a rubric or Scale by inspection.
- The guided **Use saved rubric / assessment setup** branch delegates to `launch_assessment_setup_menu`, not `launch_scoring_menu`. This is the existing no-Score configuration surface, with independent saved preset selection, typed revision preview, actor authorization, native record materialization, readback and revision constraints. This slice does not replace the established saved-preset services or type converters.
- Saved Scale values retain their exact Python scalar types and meanings through the owned preset/materialization service; the guide never maps a numeric Scale value to a letter grade, invents weights, equates group/student Scores or writes to Meridian.
- After owner menu returns, target-only canonical readback compares native Scale and Criterion Set IDs, selected rubric order and Score record identities. Any unexpected Score change, missing old record, contradictory class/activity or unreadable state produces an unconfirmed outcome rather than a fabricated no-Score success. New Scale/Set counts are only reported from observed target records, not a menu return or guessed write.
- General guided Activity assessment setup now opens the config-only `launch_assessment_setup_menu`. Score entry remains in the separate authorized scoring surface. Evidence-only orientation still reports setup not required.
- No modifications to Core, Suite, official wheel pins, roster, PDS2, GroupPlan, packet, Score record writing, history or Notes service. #153 retains broader teacher header and `:notes` UI ownership.

## Explicit non-claims

This checkpoint does not verify typed Scale level equality itself, approve a saved preset, confirm user selection of a particular preset, certify criterion learning outcomes, certify no concurrent writers, publish Grades, or inspect physical paper. Those remain owned by the existing canonical setup and grading workflows. No Scores transferred is a contract of fresh Activity copy, not a claim that an Activity can never later have a teacher-entered Score.

## Qualification matrix

Synthetic regression: target-only reads; Cross-class and revision failures; missing selected rubric; exact Score identity unchanged on verified delta; cancellation/finish produces no assessment writer; explicit setup uses config-only owner; stale or conflicting result cannot report success. Existing #63/#65/#136/#148/#149/#150 and saved assessment configuration tests remain relevant. Windows runner must pin main and branch Git SHAs, use only reviewed files, run targeted Ruff/mypy/docs/tests, then commit and push on success.
