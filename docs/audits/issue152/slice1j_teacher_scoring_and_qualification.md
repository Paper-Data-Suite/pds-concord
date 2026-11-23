# Concord #152 — Teacher scoring guide and qualification ledger

**Candidate:** `152-score-preparation-label-integrity`, at
`525b8a98c0eb8f775ca0273eb111f8a7ce7cca8a` before this documentation
commit. **Issue:** #152, under #139. **Status:** scoped source changes
Windows-qualified through Slice 1I; full repository, installed-wheel and PR
CI qualification pending. No approved release or merge is implied.

## What the teacher does

1. In the Activity's **Review** or **Score** task, select the exact returned
   Artifact, inspect the returned/assembly and Review state, and open the
   returned work when needed. A printed, generated, routed or assembled page
   is **not** by itself a reviewed or scored Artifact. Unresolved authorship,
   subject attribution, Review or Moderation may block routine scoring.
2. Choose an **Individual student** or **Cluster Group** explicitly. A student
   is a Core roster identity; a Group is a Concord Group identity. If names
   cannot be verified against the current workspace, or if they collide
   without disambiguation, the selection is blocked or distinguished before
   the teacher authorizes a Score. An opaque ID is not an acceptable ordinary
   substitute for the student's name.
3. Choose one compatible **Criterion**, one current **Scoring Scale**, and an
   exact native value. A current default can be displayed first but does not
   select a value. Stale, missing or inactive assessment setup requires
   correction or an explicit valid alternate choice. `3`, `"3"` and
   `true` are different native values when their Scales distinguish them.
4. Inspect the preview: selected target, Criterion, Scale/value, disposition,
   linked Artifact evidence, Session and Subject context, Review provenance,
   and Moderation requirement. The preview is read-only; it does **not**
   establish an exact scan-file/assembly version that Score metadata does not
   record. Author/Subject attribution is not a Score target selection.
5. Type/confirm **SCORE** only for the exact intended judgment. Cancel/Back
   before authorization records **no placeholder Score**, does not mark work
   missing/overdue or complete, and does not publish anything to Meridian.
6. Read the post-commit receipt: target, Criterion, Scale and selected value,
   basis/disposition, native Artifact Evidence Link count and snapshot. A
   Group receipt explicitly says no student Scores were created. If an
   ambiguous/no-op or unexpected link result is returned, inspect **View
   Scores** before considering another attempt; never blindly retry.
7. To record another Criterion, use the offered continuation, which
   re-inspects current state and asks for a fresh Criterion/value. To inspect
   or correct a current Score, use **View Scores** or **Advanced Score** and
   its immutable revision path. Review readiness is not a missing-Score queue
   and is not proof that every possible Criterion has been completed.

### Distinct Individual and Group judgments

In a mixed lesson a teacher may separately record:

- An **Individual student** participation Score on a compatible
  `standard_backed` Criterion bound to an active Focus Standard.
- A **Cluster Group** collaborative-analysis Score on a local Criterion
  supporting `concord_group`, with its own explicitly selected Scale/value.

The Group Score is **one Group record**, not one Score per Group member.
Neither kind creates a Grade, infers proficiency for other students, or
triggers Meridian publication. Academic result sharing is a distinct
authorized workflow.

### Recoverable errors and safe exits

| Teacher sees | Consequential action |
| --- | --- |
| Core roster/student or Cluster label unavailable | Return to the Activity/workspace and verify the correct roster or Group; do not guess from an ID |
| Criterion/Scale labels unavailable or no current compatible definition | Return to Assessment Setup, inspect selected Criterion Sets, Scale revisions and defaults |
| Returned work/Review/Moderation not eligible | Return to Collect/Review/Moderation to resolve evidence; use Advanced Score only for supported exceptional evidence |
| Workspace, Activity, roster/assessment snapshot or evidence reference changed | Reopen the work and make a fresh selection/preview |
| Existing current Score for this target and Criterion | View the existing Score; use Advanced revision/correction rather than creating a parallel current Score |
| Ambiguous write receipt | Inspect the durable Score/links; do not retry automatically |
| Teacher changes their mind | Back/cancel before confirmation: no Score or Evidence Link recorded |

**Technical IDs** remain canonical for exact storage/service operations, not
ordinary teacher-friendly labels. These flows preserve the established menu
navigation rather than creating a second scoring/navigation service.

## Local acceptance evidence through Slice 1I

These numbers describe separate bounded Windows runs; they must not be summed
as unique full-suite test coverage.

| Slice | Last qualified feature behavior | Windows evidence |
| --- | --- | --- |
| 1A–1B | Authoritative label-read diagnostics, strict Score confirmation/revision labels | 56 targeted tests; Ruff and Mypy passed for 1B |
| 1C | Current/historical Score details and assessment version labels | 63 targeted tests; Ruff and Mypy passed |
| 1D | Reviewed Artifact provenance and exact native Evidence Link identity | 110 targeted tests; Ruff and Mypy passed |
| 1E | Real synthetic Individual and Group Scores remain separate | 2 integration + 55 regression tests passed |
| 1F | Student/Group target/subject names fail closed | 14 slice + 44 regression tests passed |
| 1G | Selected-workspace binding and Activity snapshot preflight | 7 slice + 58 regression tests passed |
| 1H | Compatible Criterion/Scale labels and recovery | 11 slice + 65 regression tests passed |
| 1I | Readable receipts and bounded ambiguous outcomes | 28 receipt/actor + 44 regression tests passed |

**Slice 1I qualified HEAD:** `525b8a98c0eb8f775ca0273eb111f8a7ce7cca8a`.
The Windows checks also verified source imports, correct branch and origin,
fast-forward-only history and a clean working tree. The synthetic tests use
disposable workspaces; they are **not** a real student or physical scanned-paper
Score acceptance.

## Required broader qualification — pending

Do not mark #152 complete solely from scoped source tests. The source of truth
for complete validation is `scripts/validate_repository.py`, invoked once
with `--core-wheel` pointing to the exact authenticated released Core 0.6.6
wheel. `scripts/verify_core_wheel.py` authenticates filename, ZIP/metadata,
installed distribution and SHA-256:

```text
pds_core-0.6.6-py3-none-any.whl
d6d21e426092b0329bcfd69b6fbee44c345edc46794a914d847d5ea73a2b7301
```

The full validator covers Core 0.6.6 and grouping-fixture authentication,
dependencies, one clean candidate build, full pytest/Ruff/Mypy/docs/release
checks, Twine/package checks, installed Concord wheel smokes and the installed
Core 0.6.6 reader-contract acceptance.

The current `.github/workflows/ci.yml` does **not** run on arbitrary feature
branch pushes; a draft pull request is needed for its eight-job GitHub Actions
matrix: Ubuntu/Windows with Python 3.11, 3.12, 3.13 and 3.14. Do not mark CI
green when no checks exist. Keep the PR unmerged until independent review.

**Remaining #152 acceptance checks to reconcile after complete validation:**
exact dotted `SL.PE.11-12.1` end-to-end Focus Standard in the mixed
Individual/Group fixture; two isolated class contexts with 29/30 distinct
rosters and six uneven Clusters; orientation matrix including
`standards_based`, `local_criteria_only` and `evidence_only`; typed
numeric/string/Boolean/categorical rejection; malformed/revoked assessment
or Review/Moderation identities; and verified post-write immutable history
with interrupted/conflicted outcomes. Existing test files may already cover
parts of this list: first inventory them and document the actual witnesses.
Do not invent a failing behavior or a passed gate.

**External boundary:** Genuine classroom/physical Score acceptance remains
#159. No merge, release, tag, dependency bump, automated Grade, or Meridian
publication is authorized by this document.
