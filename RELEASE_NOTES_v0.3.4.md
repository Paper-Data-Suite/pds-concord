# Concord v0.3.4 — standards-backed grouping and saved classroom arrangements

**Release status: candidate; not yet published.**

## Fixed — teacher workflows (#136)

- Corrected standards-context propagation through teacher-driven GroupPlan, Group/Membership, Session, Role/Responsibility and related setup workflows. Standards-backed and mixed Activities continue using the canonical Core Standards Library; standards validation is not relaxed.
- The pre-existing Activity can be resumed after updating Concord; existing GroupPlans and prior recorded evidence are not silently changed or recreated.

## Added — class-scoped saved groupings (#136)

- Save a six-table (or other) arrangement from an editable Activity GroupPlan or from actual current Groups/Memberships for an explicitly selected Session.
- Browse, review, rename, replace with a reviewed plan, retire and inspect immutable revisions of teacher-owned, class/year-scoped arrangements.
- Reuse a saved grouping in another Activity as a **fresh editable GroupPlan**, with exact Core-student identity, roster reconciliation, explicit teacher placement decisions and normal preview → approve → apply lifecycle.
- Optional direct CLI and `student_id,group` CSV interchange with privacy-sensitive previews, restricted export and no-overwrite enforcement.
- No Activity Groups, Memberships, Scores, evidence, grades or publication state are copied by saving or reusing an arrangement.

## Compatibility and grading integrity

- Maintains `pds-core>=0.6.6,<0.7`, including Core v0.6.6 Windows viewer-safe local-opening support and Concord's existing byte-integrity checks.
- Preserves independent student standard-backed Score targets and Group local-criterion Score targets, with no automatic proficiency fan-out.
- Preserves `concord_academic_result_manifest_v1`, Core academic-work publication and the neutral manifest-reader boundary.

## Qualification required before release

This candidate must pass final full CI, official Core 0.6.6 installed-wheel acceptance, outstanding Packet/PDS2 and real Windows long-path viewer acceptance, exact-main build, checksum verification and fresh-download installed validation. See `docs/v0.3.4-release-checklist.md`.
