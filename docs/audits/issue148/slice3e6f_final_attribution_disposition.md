# Concord #148 — Slice 3E6F: final source-level actor-disposition gate

Starting branch: `148-persistent-reviewable-teacher-attribution`
Starting commit: `0e96aea2ed29f5aafb1a4698d0276a4594cba19b`
Scope: source-only menu inventory, synthetic regression, and a review gate. No Core, Suite, Meridian, academic workspace, or actor-profile mutation.

## Exact scope and audit method

This slice adds `scripts/issue148_final_attribution_gate.py` and a synthetic test module. No production files are changed. The gate imports the existing `scripts/issue148_actor_callsite_census.py` scanner, enumerates all **43** `concord/menu*.py` modules, and requires an explicit disposition for every top-level function whose AST exposes actor resolution or a write confirmation. It fails closed on new/unclassified candidates, missing reviewed write witnesses, newly introduced `legacy-confirm-with-actor` cases, and regressions in selected nested Score and GroupPlan digest contracts.

The gate distinguishes a self-declared recorded actor from authorization and does not infer real-world use, installed-wheel behavior, or complete coverage of dynamically dispatched functions from AST alone. A nonactor confirmation is not automatically safe; each residual has been mapped to an explicit service or intermediate menu boundary.

## Residual actor-resolution candidates

| Source | Function | Reviewed disposition |
|---|---|---|
| `menu_actor_action.py` | `confirm_actor_write` | Shared action-reviewed implementation, not an academic service write |
| `menu_artifact.py` | `_choose_author_semantics` | Author identity is selected separately from the reviewed recorder; #148 3D2B |
| `menu_group_plan_bulk.py` | `_review_batch` | Custom review with exact actor/digest and currentness; #148 3E6D |
| `menu_group_plan_bulk.py` | `launch_cluster_bulk_editor` | Commits `_review_batch`'s request and paired digest; #147/#148 3E6D |
| `menu_publication.py` | `_manifest_request` | Prepares request used by later actor-specific publication preview; #148 3D3A |
| `menu_saved_grouping_revisions.py` | `_current`, `_show_history` | Actor-scoped lookup and display, not a mutator; #148 3E5C |
| `menu_saved_groupings.py` | `_saved` | Read-only actor-scoped arrangement lookup; #148 3E5A |
| `menu_scoring.py` | `_score_components` | Draft-only; non-score `StatusReason` rebinding occurs at reviewed write; #148 3E6E |

## Other-confirmation candidates (no Concord actor field)

| Source | Function(s) | Disposition |
|---|---|---|
| `menu_grouping_signal.py` | `_import_csv` | Core grouping-signal exchange and source digest; request has no actor field |
| `menu_publication.py` | `_register`, `_update_registration` | Core academic-work registration contract has no `WorkflowActor` |
| `menu_publication.py` | `_withdraw` | Core publication withdrawal records a reason under its current service contract, not a Concord actor |
| `menu_publication.py` | `_rebuild_catalog` | Regenerates disposable derived Core catalog; not canonical academic actor history |
| `menu_saved_groupings.py` | `_collect_decisions` | Explicit `ACKNOWLEDGE` before the separate action-attributed grouping creation review |
| `menu_scan.py` | `_route` | Initial retained-scan intake delegates to actor-less Core routing. Teacher routing-failure defer/resolve is actor-reviewed separately |
| `menu_teacher_settings.py` | `_setup`, `_rename`, `_replace`, `_reset` | Explicit local Concord preference lifecycle; no academic writes or new identity authority |

These are service-contract dispositions, not a claim that Core should acquire an actor parameter. If cross-module attribution becomes a requirement, it needs a separately published and qualified Core contract; neither Meridian private profiles nor Core Notes ownership should be repurposed.

## Qualification and exit gate

1. Pin the source ZIP, the exact starting HEAD, and eleven Git blobs. Require no staged, changed or untracked files before applying.
2. Ruff-check and format the new script and tests in a temporary projection; verify the installed official Core wheel; run the new census script to a **temporary non-repository report**.
3. Run focused #148 source/actor/GroupPlan/Score/Packet, Settings and navigation tests. Commit and push only after all gates, staged whitespace validation, and remote-head match.
4. **Still required, not claimed by this slice:** one final full Concord suite, Ruff and strict typing for the repo, build/package and installed-wheel setup→relaunch→author acceptance, Windows/Linux CI, consumer launch evidence, and PR review. These must be recorded separately; successful static analysis alone is not merge acceptance.

Existing direct CLI explicit `--actor-id` behavior, scoped workspace access and historical record immutability are unchanged by this slice.
