# Concord #148 — Slice 3E3B: packaged Starter Template actor review

Starting commit: `b8b67c201f9a8b577b4c37646d10db9f93c93a05`.

## Scope and precise behavior

Converts the two remaining packaged Starter Template operations in `concord/menu_template.py`: **Install / Update Starter Template** and **Install / Update Starter Templates**. These operations use typed `PrepareStarterTemplateInstallRequest` and `PrepareStarterTemplateInstallAllRequest` values. A prepared Starter Template includes canonical provenance and must be recomputed for the actor whose ID and label are displayed at confirmation. The canonical `commit_starter_template_install` / `commit_starter_template_install_all` continues to receive the exact actor-reviewed prepared value, without reconstructing it afterward.

A read-only initial preparation decides whether **no canonical write is needed**. If the selected Starter is already installed, or all packaged Starters are already current, the original informational receipt returns without a new confirmation and without a write. For pending installation, `_prepare_for_actor` reruns the canonical preparation for the currently selected actor on each review. It checks initial installed/upgrade status (and, for bulk, each exact ordered Starter key and state) against the initial no-write determination. A changed disposition fails closed and requires reopening the action. The canonical storage service retains final currentness/identity/CAS and safe replay authority.

No alternate actor persists across an operation or into the next Template write. `confirm_prepared_actor_write` handles defaults, temporary actor selection, restoration, cancellation, and the previously verified mid-review actor revalidation. Both operations remain distinct from regular Template lifecycle and Packet lifecycle, which were addressed in 3E3A. The original source census document remains an unmodified historical report; its regression test now requires these two functions to be `action-reviewed`. The existing starter-menu test is updated to expect the intentional read-only inspection plus exact reviewed preparation before commit, with the same actor and prepared-object identity.

## Boundaries and evidence

No Core, Meridian, Suite, canonical storage, roster, student data, or direct CLI modifications. This is self-declared attribution, **not authentication or permission**. The initial inspection and action-specific re-preparation run through preexisting read-only preparation functions. The synthetic regression suite checks both operations' exact request-to-commit forwarding; no-write cases; actor selection, switching, restoration, and cancellation; and failure on changed Starter status. Every synthetic identity, key, and output is fictitious.

The guarded runner checks the pinned starting commit and ten exact Git blobs, source archive SHA-256/manifest, no worktree changes, and all affected source paths. It projects the patch in temporary storage and runs Ruff and strict mypy with a source shadow before modifying the checkout. Installed-Core verification and scoped pytest run after applying. Commit/push occur only after successful qualification and a checked remote HEAD. Full Concord suite, installed-wheel relaunch, and supported CI remain separate final issue #148 acceptance gates.
