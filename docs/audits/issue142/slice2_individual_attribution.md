# Concord #142 — Slice 2: individual Artifact attribution and immutable correction

Source-only successor to Slice 0 (15 families / 16 call sites) and Slice 1 (Core operation-context resolver). This slice changes exactly six ordinary-menu handlers in `concord/menu_artifact.py` and does not change service signatures, graph validation, Core rosters or group identities, Core Standards records, physical scan state, or Score publication.

## Owned write boundaries

| Menu handler | Canonical mutator | #140 historical source line | Standards obligation |
|---|---|---:|---|
| `_add_author` | `add_artifact_author` | 882 | conditionally required |
| `_update_author` | `update_artifact_author` | 924 | conditionally required |
| `_correct_author` | `replace_artifact_author` | 985 | conditionally required |
| `_add_subject` | `add_artifact_subject` | 1284 | conditionally required |
| `_update_subject` | `update_artifact_subject` | 1321 | conditionally required |
| `_correct_subject` | `replace_artifact_subject` | 1376 | conditionally required |

Each handler calls the Slice 1 `begin_artifact_write_context` after its current Activity selection, before prompts. After the teacher confirms, it calls `revalidate_artifact_write_context` with that exact snapshot and forwards `artifact_write_kwargs` to the canonical service. These kwargs pin workspace root and forward the actual Core library only when orientation, persisted Criteria/Score history or an operation's proposed requirement necessitates it. The canonical service remains responsible for Core-student roster membership, Artifact/Group/Role/Session associations, immutable correction chains, request CAS and final validated commits.

The selected Artifact/Author/Subject controls in these handlers remain legacy ambient readers. Root drift is rejected before a write by revalidation, and the canonical service independently validates the selected identity in the pinned root. Refining auxiliary menu reads to carry the explicit root and eliminating ambiguous same-ID cross-workspace selections is an outstanding follow-up for Slice 2 qualification. Do not treat this slice as complete end-to-end release acceptance on that basis.

## Synthetic successor tests

`tests/test_issue142_slice2_individual_attribution.py` exercises real menu mutation entry points, passing-through to real guarded services. It creates disposable classes/rosters, Core Standards library where required and an explicit **planned** `return_not_expected` Artifact. Only **proposed** author/subject associations are created from this fixture: **no physical returned work, actual authorship, confirmed performance, or score is inferred**. Tests cover all four legal orientations, both Author/Subject positive additions, status updates, two audited corrections, cancel/no write, stale preview, duplicate Author and a wrong-class student and active workspace switch. Production sample/classroom workspaces are never opened.

## Historical and release gates

The original #140 tests remain frozen and intentionally assert the **pre-fix missing-Standards failure**. Those legacy expectations are now incompatible with a successful menu repair. Do not edit or secretly bypass the frozen tests. Preserve them as source-baseline evidence and account for the intentional predecessor-to-successor expectation change in #162 and the Slice 6 regression plan. Full-source pytest and installed wheel qualification remain outstanding, as do returned/assembled evidence semantics and both routine Scores.

Status on packaging: syntax/AST/manifest verified; **not yet run against the actual user Windows checkout**. Ruff/mypy/pytest remain mandatory before any commit/push. Report any positive-path fixture failures without manufacturing real returns.
