# Concord #142 — Slice 4A: First detailed Review and first Moderation

## Scope

This is a **sub-slice** of planned Slice 4, not signoff for all Review/Moderation paths.

- Resolve and pin the selected Class, Activity, current snapshot, workspace, and conditional Core Standards library **before** starting the first detailed Review or first Moderation entry.
- In detailed Review, pin the Artifact choice and use the exact same Core Standards library for the Artifact detail reader and subsequent `add_artifact_review` write. Revalidate the active workspace and snapshot after the teacher confirms; the service retains native graph and CAS validation.
- In first Moderation, pin the Artifact/Page/Subject selection workspace and forward the exact root and canonical Standards context to `add_moderation_record`. Revalidate after confirmation. Moderation never determines a Score.
- Add optional `standards_library` to the narrow `show_artifact` and `list_artifact_reviews` read services, without changing default callers. The Review list extension is preparatory for Slice 4B successor Review.
- Preserve the previously accepted nine Attribution writer paths and frozen #140 audit records.

## Positive and refusal evidence

`tests/test_issue142_slice4a_first_review_moderation.py` runs the *real* first-write menu handlers and services on disposable two-class Core workspaces and a genuine, synthetically prepared Concord Artifact. The test Artifact has **no returned scans**, **no expected return**, and no observed student evidence. The explicitly entered Review outcome is `awaiting_additional_evidence` with `not_ready` scoring readiness; Moderation says `not_used_for_scoring` with `not_be_used_for_scoring` permitted use. The tests verify one atomic snapshot append, no Score or evidence link, clean cancellation, workspace drift refusal, and duplicate write rejection. All tested data is fabricated, isolated in pytest `tmp_path`.

This is **not** evidence of successful returned/assembled paper Review or scoring. A future Slice 4B validation gate must use genuine synthetic returned/assembled evidence where the record graph supports it. Do not misrepresent prepared pages as received evidence.

## Explicitly deferred

- `replace_artifact_review` and `replace_moderation_record`, current-head selection, immutable correction/provenance, complete historical #140 Slice 3B/3D expectation reconciliation.
- Review-next, quick Review, routine Score menus (planned Slice 5); broad menu reading and navigation not needed for these first-write paths.
- Full pytest suite, installed-wheel verification, real scanner/returned-evidence end-to-end and frozen #140 audit remeasurement.

## Safety

Source-only package. Runner checks exact original branch/HEAD, origin, no staged changes, *whole* status inventory, reconstructs expected post-Slice-3 Artifact menu, validates reader baselines, hashes and parses the payload. Defaults to no-write preflight; explicit `--apply` writes only three existing sources and two additive files, with rollback on failure. No automatic git stage/commit/push, no real Core workspace access, no #140 frozen data edits.
