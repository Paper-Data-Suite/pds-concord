# Concord #152 — Slice 1K acceptance reconciliation

Status: closeout candidate, not merge authorization. This ledger supplements
the teacher guide and historical Slice 1J ledger without rewriting them.

## Qualification provenance

- Baseline main: `7f59dc73abfdbfa877d47206518d27db22df524a` (#151).
- Branch: `152-score-preparation-label-integrity`; draft PR #176.
- Canonical local Windows repository qualification passed at
  `aa27264afe6a98620dac46d6378412c21b3eab09`. Reported elapsed
  1518.927 seconds, including pytest 868.440 seconds. Full validator
  `scripts/validate_repository.py --core-wheel <authenticated wheel>`
  covered source, static checks, build, packaging and installed-wheel
  smoke/reader acceptance. The successful transcript tail does not
  establish a total pytest case count.
- Official Core wheel: `pds_core-0.6.6-py3-none-any.whl`, SHA-256
  `d6d21e426092b0329bcfd69b6fbee44c345edc46794a914d847d5ea73a2b7301`.
  Isolated #136 acceptance Concord wheel SHA-256:
  `f057e453a6f96fbaed05f7026fcd05bd8092d57b6f7052a81e77af7c65d4888f`.
  This is a qualification artifact, not a release.
- Initial PR CI run 45301419727 failed on a historical label witness
  dependent on ambient Standards configuration. Test-only repair
  `b54c0e4e750d89cc912798550438c76732a50cb6` explicitly supplies
  the synthetic library, proves successful reads and injects the actual
  authoritative Scale-read failure. Run 45302575140 passed all eight jobs.
- Slice 1K1: `b8eaffe469f1daa758fd5d7f3d9585ddc8ddac9a`:
  15 targeted Windows tests passed (29.33 seconds); formatting-only
  repair `251cf322ab9acf975aeb0efbbedf804606eb7254` passed static
  and repository checks. CI run 45306148227 completed successfully.
- Slice 1K2: `18000c9be0b031dad37ef551c97d426cff9db1d9`:
  one two-class native persistence witness passed (42.94 seconds);
  formatting-only repair `d7398db9bbfb4d7a2e939b3cddabf2405387ed64`
  passed static and repository checks. CI run 45317162880 was not yet
  complete when last inspected.
- Slice 1K3: `c385060724f63ebdc0b6c6ec7d97c30086ad4078`:
  12 targeted tests passed (4.45 seconds), lint and commit integrity
  passed, Ruff requested one assertion-format correction. The closeout
  candidate includes that correction and one new durable replay test.
- Final closeout candidate: targeted static/behavior checks and its exact
  eight-job PR CI matrix are pending. Do not transfer older CI status
  or installed-wheel evidence to a new SHA without checking its gates.
  No production source change has been made after the canonical local run.

## Acceptance map

Paths in this table refer to files under tests/. Separate tests establish
separate boundaries; a projected unit test is not a physical paper test.

| Issue scenario | Witness / disposition |
| --- | --- |
| A, B, C | test_issue152_slice1a_score_label_reads.py, slice1b_essential_score_labels, slice1f_selection_labels: authoritative reads and essential-label refusal; historical #140 witness repaired above |
| D | test_issue152_slice1c_score_history_versions.py and test_issue152_slice1h_assessment_selection.py: revision labels, ambiguous labels, stale or absent default recovery |
| E | test_artifact_routine_scoring_issue108.py and test_menu_artifact_scoring_issue108.py: Review eligibility, ineligible context refusal; #151 return boundary preserved |
| F, G | test_issue152_slice1e_real_individual_cluster_scores.py: actual synthetic returned/assembled/reviewed Artifact, distinct native Scores and links; both original and exact dotted Focus Standard, group warning, cancellation |
| H | test_issue142_slice6b_real_score_continuation.py and test_issue142_slice5b2_score_continuation.py: real subsequent Criterion, duplicate prevention, pinned continuation authority |
| I | test_issue152_slice1g_workspace_pinning.py, test_issue152_slice1d_review_provenance.py, test_issue152_slice1k2_class_isolation.py, test_issue152_slice1k3_acceptance_matrix.py: mismatches, wrong class/target/assessment and unrelated Moderation ID; test_issue142_slice4b_successor_review_moderation.py covers immutable review/moderation successors and stale/concurrent refusal |
| J | test_menu_artifact_scoring_issue108.py and test_issue152_slice1e_real_individual_cluster_scores.py: cancellation, Back and continuation without write; established navigation regression suite retained |
| K | test_issue152_slice1k3_acceptance_matrix.py: four orientation projections, seven type-sensitive refusals; test_workflow_score_recording.py: canonical typed persistence |
| L | test_workflow_score_recording.py: native replacement, historical predecessor, fresh links, exceptional dispositions and moderation; test_issue152_slice1c_score_history_versions.py: current/historical teacher display |
| M | test_issue152_slice1k2_class_isolation.py: disjoint 29/30 Core rosters, 12 Groups, four native Scores and links, eight refused foreign student/Group/assessment writes, both graphs unchanged |

The two-class witness uses explicitly configured observation artifacts and
canonical Score services; the returned-paper-shaped routine menu witness is
separate. The orientation matrix is a preparation-layer synthetic projection,
not four independent classroom runs. Existing successor Review/Moderation
tests and stale context tests cover their respective boundaries; they are
not an end-to-end physical revoked-evidence exercise.

## Teacher flow and negative evidence

Source-derived before/after trace (not a measured human timing study):

- Before: select reviewed work and make explicit target, Criterion, Scale,
  level and contextual decisions; the Score history label helper could
  swallow a guarded Scale/Set lookup failure and display incomplete labels.
- After: retain the exact selected work and current context, show authoritative
  labels or an actionable refusal, keep consequential teacher choices explicit,
  preview the exact target and native Artifact evidence with Review provenance,
  confirm SCORE once, show a readable receipt, then re-inspect before continuing.
- Examples of bounded failure: missing Core Standards context requires repair
  and reopening the Activity; failed Scale reads report that labels could not
  be verified; incompatible or foreign targets and typed levels are refused;
  ambiguous write receipts direct the teacher to View Scores, not resubmission.

The exact immutable Score and Evidence Link relationships are exercised in
the mixed and two-class tests. The existing replacement witness
`test_score_revision_uses_fresh_links_and_can_correct_target_and_criterion`
retains the original linked source and creates a separate successor and
Correction. `test_issue152_slice1i_score_receipts.py` tests ambiguous
receipt wording with injected result objects. The new
`test_issue152_slice1k4_durable_score.py` adds actual storage CAS replay
rejection after a completed native Score. It is pending qualification and
does not simulate power loss or assert recovery from arbitrary partial writes.

## Boundaries and final gate

All fixtures use fabricated identities; no actual student records, physical
paper scores, Grades or Meridian publication were generated. Genuine
classroom and physical/downstream acceptance remains #159. Exact retained
scan/assembly versions are not invented from an Artifact Evidence Link.
No new package version, tag, release, dependency bump or merge is authorized.

Closeout requires a clean exact candidate, targeted replay and formatting
qualification, and successful final PR matrix. Record that final evidence in
the PR before requesting a reviewed squash merge; do not claim a human
acceptance gate from synthetic tests.
