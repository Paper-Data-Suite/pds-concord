# Concord #151 — Slice 3: Assembly readiness and viewer-continuity preflight

**Baseline:** `847d3ff41eed7b4c05edf9ca3092abbfd803ac46`, feature branch `151-authoritative-collect-returned-evidence`; `main` remains at `8443e9093e8f0ca14fc4c0c0abc20e0ede7eb0d5`.

**Issue owner:** #151 (Slice 3). **Related existing contracts:** Core #134 Windows viewer path alias, Concord #105 exact opening/assembly; #149 and #151 Slices 1–2 current evidence projections. This is a narrow teacher-journey correction, not a rewritten assembly engine.

## Reproduced source-level issue

`concord/menu_artifact.py::_assemble` currently asks the teacher to select competing scan occurrences and confirm an actor-attributed ASSEMBLE operation before checking whether the selected Artifact's return-expected paper is complete. An awaiting-return, partially returned, or non-return-expected Artifact gets as far as confirmation before the assembly writer raises an expected readiness error.

## Change

- After selecting the exact Artifact, call the read-only `inspect_teacher_collection_overview` with the current Activity snapshot revision. Choose by exact `artifact_instance_id`, never Group/Session labels.
- Permit canonical stages `ready_to_assemble`, `choose_occurrences`, `assembled`. The existing assembly owner still selects exact occurrences, validates source hashes, verifies/reuses the manifest/PDF and checks snapshot changes.
- For `awaiting_return`, `partially_returned`, `not_return_expected`, or `needs_recovery`, show a clear stage, count, safe next step and no-write receipt **before** any occurrence selection, actor confirmation or assembly attempt. No false physical print/distribution claim.
- Missing Artifact identity or stale snapshot fails closed. Cancellation remains no-write.
- After a verified assembly or exact reuse, teach the separate `O. Open returned work` action. Assembly never launches a viewer or claims Review/Score.

## Unchanged authority and safety

Core still owns PDS2 source retention and the Windows viewer alias. Concord's assembly writer still owns exact source selection, route/manifest/hash checks, crash-safe output and reuse; `open_returned_artifact_evidence` remains the only existing verified viewer handoff. The historical saved-version inspector retains its exact manifest-selected lineage and chronology. There is no new storage, no Notes implementation, and no Core/Suite navigation rewrite.

## Verification

Native candidate checks: strict pinned branch/remote, zip hashes and exact change scope; Python compile, Ruff, Mypy, documentation, new menu preflight tests, existing #105/#134/#149/#151 collection and viewer regressions. Two #151 attribution strict xfails are intentionally retained. Source-only synthetic fixtures cannot establish physical scan-return or Windows 296-character OneDrive viewer acceptance; those are separate Slice 6 gates.

## Known out-of-scope

- The actual double-validated, exact saved-version opening already exists; this slice preserves it and exercises regressions rather than rewriting custody logic.
- Source file integrity between preflight and commit must still be checked by the assembly writer, never inferred from the read-only stage.
- Attributions (#151 Slice 4), resume/recovery breadth (Slice 5), and native long-path viewer acceptance (Slice 6) remain outstanding.
