# Issue #134 — Slice 1: Shared teacher Artifact choices

**Reviewed base:** `7301ba01673f87cb04547abb03ddeed4b4912adc` (Slice 0, branch `134-reliable-long-path-opening-and-teacher-artifact-navigation`).

## Behavior in this slice

- One new read-only service, `list_teacher_artifact_choices`, constructs Group, Session, returned-page-count, and state labels from **one** current Concord graph. It reuses exact immutable Artifact IDs in the selected `ArtifactSummary` and uses no filenames, scan IDs, or hashes to generate labels.
- `menu_artifact` uses the same projection for ordinary Collect, Assemble, Open, Review, attribution, and scoring shortcuts passing through its Artifact picker; the View Artifact detail and Review-next branches use it too.
- `menu_scoring` uses that projection for the direct Artifact Score target picker.
- Identical Group names are disambiguated by a stable ordinal within the current graph; identical work descriptions receive `work copy x of y`. **These are not dates, revisions, or most-recent markers.** A duplicate label never changes the exact canonical selection identity.
- Unknown Session or Group associations are not guessed; absent and dangling associations use different truthful fallbacks.
- The returned-work viewer UI acknowledges an OS opening *request* rather than claiming the PDF displayed. The existing Core opener contract and canonical manifest verification remain unchanged in this slice.
- The Slice 0 JSON inventory is a **frozen historical snapshot** of the preimplementation source. The Slice 0 regression test now validates the frozen JSON schema/identity instead of incorrectly comparing it with intentionally modified menu source. The inventory is not regenerated.

## Deliberate limits

- The Core class record has a canonical `class_id` and school year but no mandatory display-friendly course/period title; Activity's title remains the primary heading. We do not invent class names or periods.
- Author and participant names are **not inferred from GroupMembership or rosters** in this slice. Exact author and subject identities carry separate privacy and confirmation rules. Only verified, authorized participant naming may be added after an explicit authorization/display contract is reviewed.
- Returned scan routing times, repeated occurrence choices, verified historical assembly selection, Review/Score evidence-version binding, and assembly chronology remain **Slice 2**.
- Other raw IDs in packet generation, templates, historical Score presentation, publication, page and other routine status/detail screens are the documented **Slice 3** follow-up. This slice is not a claim that every Slice 0 audit candidate has been fixed.
- Viewer-safe installed-Core 0.6.6 adoption and real long-path physical acceptance remain **Slice 4**. This slice does not raise Concord's dependency floor or alter any release asset.

## Guardrails and qualification

- No canonical storage/model/manifest/record revisions, dispatch policies, publication contracts, student evidence files, or generated PDFs are changed.
- Test the new snapshot projection against the existing `ArtifactSummary` service on synthetic records, including 40 indistinguishable work copies, duplicate Group names, unknown associations, and stale snapshot requests.
- Qualification is focused pytest for the new and changed baseline tests plus relevant existing Artifact/Score menu tests, Ruff, MyPy, and Git diff whitespace. The full clean CI/installed acceptance remains a final release gate, not a redundant per-slice action.
