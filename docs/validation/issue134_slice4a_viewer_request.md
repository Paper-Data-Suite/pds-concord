# Concord #134 — Slice 4A: viewer handoff boundary

**Baseline:** `7e0cc88b91f31ce4d938d27bd0661583aa5fffb1`.

## Behavior

- Artifact, rendered Packet PDF/folder, and feedback PDF/folder openers continue to verify the selected canonical target **before** calling `pds_core.local_open.open_local_path`.
- The OS may accept a request without the asynchronous viewer actually displaying a PDF or folder. The ordinary menu therefore says **requested opening**, never “opened” as a factual claim.
- A failed launch remains an error and does not create or rewrite evidence. A successful launch request does not record Review, Moderation, Score, or delivery.
- The Core dependency and CI remain **unchanged in 4A** so that the historical 0.6.5 qualification gates stay coherent. Slice 4B will migrate the entire dependency/CI/release-gate chain to the **published Core 0.6.6** wheel, rather than raising only the runtime floor.

## Installed Windows physical acceptance utility

`python scripts/probe_issue134_core066_viewer.py --mode dispatch` in a Windows environment that has the **published** Core v0.6.6 installed creates a temporary synthetic PDF at a >296-WCHAR canonical path. It intercepts the shell launch, confirms Core's short lexical alias points to exactly the canonical file, and verifies that the original file hash is untouched. This is not real viewer acceptance.

`python scripts/probe_issue134_core066_viewer.py --mode physical` actually requests launch and explicitly asks the teacher to confirm that the external PDF viewer displayed the synthetic PDF. It refuses to assert physical acceptance without that confirmation. Both modes use only generated, non-student data. A physically verified **Concord artifact/Packet/feedback** open-through chain remains a separate installed acceptance in 4B/5.

Do not run the physical acceptance on a system with Core v0.6.5. Do not claim Core alias integration is complete until the exact 0.6.6 consumer environment is qualified.
