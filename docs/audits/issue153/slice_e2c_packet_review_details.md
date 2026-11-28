# #153 E2c — Packet review and receipt technical details

E2b 76/76 tests passed (3.34 s), static checks passed, and the owner
confirmed clean local HEAD and tracking branch at formatting-only
`8372de2e5617cc563eec34110a4f3812d00fcf0d`. Reflog shows the exact
tree reconciliation already occurred. No second reset needed.

Packet preview and Generate Packet confirmation move only the review
digest into explicit T Technical Details. Exact Packet version, Activity,
Session, target relationships, counts and blocking diagnostics remain.
The single-instance render/reprint receipt retains the output location,
counts and replay outcome; the output SHA-256 is opt-in. Paths needed
to locate the completed output are intentional, not hidden identity.
Other partial/error paths remain as before; no blanket filtering.

The existing Concord local confirmation gains an opt-in details argument;
the existing prepared-actor helper binds optional details to the exact
prepared object and actor. Legacy callbacks without opt-in retain their
three-argument contract. The opted-in Packet caller supplies the existing
confirmation function supporting the explicit fourth argument. A provider
review redraws the same prepared preview after T, without reprepare;
actor changes still reprepare and final actor revalidation still occurs.
T is not an approval, data-entry command, or shared Core command.
B/Enter returns from details, M/Q propagate. No service, digest
calculation, actor identity, CAS, route or PDF validation changes.

14 added synthetic tests: legacy/provider disclosure and cancel/unwind,
alternate/default digest replacement, invalid confirmation inside details,
profile-change invalidation, ordinary Packet preview and render receipt.
The existing #148 Packet actor fixtures are extended to observe the
opt-in callback and post-render receipt without weakening existing actor
and request assertions. Local qualification pending. E2c covers these
specific surfaces, not every diagnostic or identifier across Concord.
B/F remain blocked until the consolidated released Core contract is
available; no Core implementation recreated.
