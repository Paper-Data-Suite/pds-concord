# PDS2 Artifact Page Integration

## Ownership and identity

Core owns workspace resolution, `ModuleWorkRef`, PDS2 parsing and serialization,
immutable Route Registration storage, installed module discovery and dispatch,
retained-source storage, and version 2 routing-failure/resolution metadata.
Concord owns Artifact Instance/Page preparation, target validation, printable page
rendering, returned-page filing, and native `ScanReference` records.

Concord routes use:

```text
module_id = concord
class_id  = Activity.class_reference.record_id
work_id   = Activity.activity_id
route_id  = one non-semantic route per routable physical page
target    = concord:artifact_page:<artifact_page_id>@1
```

The PDS2 payload therefore identifies an expected physical page only. It never
contains a student, Author, Subject, Group, Criterion, Score, Review, Grade, or
logical page number.

## Preparation and immutable routes

`prepare_artifact_pages` validates a complete ordered plan, allocates native
Artifact Instance/Page identities and route IDs, and publishes the candidate
records through `commit_record_batch`. Only after the native snapshot is current
does it create or reconcile Core Route Registrations. One physical page has one
Artifact Page ID, route ID, registration, and serialized PDS2 locator.

Route files are immutable. Retry loads an existing registration and requires
exact semantic equality. It neither overwrites nor repoints a route. If route
creation stops after Concord publication, the service raises structured partial
success with the durable snapshot and verified-route count. Retry uses the route
IDs already stored on the canonical pages.

## Canonical-before-render

`render_artifact_pages` reloads the current Artifact Instance and pages, loads and
validates every required Core registration, and calls Core's PDS2 serializer.
Only then does it construct a minimal PDF. Output lives at
`rendered/<artifact_instance_id>.pdf` beneath the Core-qualified work root using
`safe_module_work_descendant`; caller-selected output is also required to remain
beneath that exact `rendered/` namespace. It cannot target `state/`, `routes/`,
another work, an absolute/drive/UNC path, or a traversal. Rendered data is
derived and nonauthoritative. A different existing output is not overwritten;
an identical deterministic output is reused. Installation is atomic, and a later
lifecycle-commit failure is reported as partial success without removing the
completed file.

This minimal renderer emits route-bearing pages only. A non-route page is not
placed in this PDF and therefore is not transitioned to `generated`; when such
a page remains, the enclosing Artifact also remains in its prior generation
state. This keeps canonical lifecycle claims aligned with the physical output.

Rendering uses Pillow and qrcode. Scan decoding uses zxing-cpp for raw QR text
and pypdfium2 for PDF rasterization. These mature wheel-based packages avoid
external executables and support the Python/Windows/Linux matrix. ScoreForm and
Quillan are not dependencies.

## Retain-first scan routing

Scan intake accepts PDF, PNG, JPEG, and TIFF sources. Each selected regular file
is retained exactly once through Core before decoding, and all later reads use
the retained copy. Because intake mutates retained-source state, it initializes
an absent resolved Core workspace through Core's public bootstrap API; review
reads and help remain non-mutating. PNG, JPEG, and TIFF image sources are physical
page 1; PDF sources enumerate physical pages 1 through N. The decoder returns raw
text, Core parses PDS2, and Core's module registry dispatches mixed-module batches
without sibling imports.

No payload, malformed PDS2, ambiguity, unavailable modules, inactive/missing
routes, and handler failures become immutable Core routing-failure v2 records.
One bad page does not discard later pages. Review uses append-only Core scan-
resolution v2 records. Automatic intake remains mixed-module. Concord's teacher
review correction is narrower: it accepts only an existing, active, validated
Concord `artifact_page` route. A failure already scoped to another module cannot
be reinterpreted as Concord evidence; an unscoped failure may be assigned to an
exact Concord route. Filing is re-dispatched through Core and the normal Concord
handler before a successful resolution is appended. No fuzzy, OCR, filename,
roster, or AI route inference is performed.

Review redispatch reconstructs the retained intake event from Core's canonical
UTC timestamp-bearing retained filename and date bucket, never from mutable file
metadata such as `mtime`. If dispatch succeeds but the append-only resolution
write fails, Concord reports structured partial success (dispatch/evidence yes,
resolution metadata no), leaves the filing intact and the failure unresolved,
and performs no silent retry.

## Returned occurrences

The Concord handler validates the resolved work, exact Artifact Page target,
canonical route ID, lifecycle, retained-source containment/digest, and positive
physical page number. It atomically commits a native `ScanReference` with the
page's returned transition under the snapshot it actually loaded.

A Scan Reference preserves the Artifact Page, route, Core source-scan identity,
one-based physical page number, workspace-relative retained path, SHA-256, and
system dispatch provenance. The occurrence key is retained source + physical
page + route. Exact replay is a no-op; a newly retained rescan is distinct.
Successful routing creates no Author or Subject, requires no student/roster, and
does not change when an Artifact is group-related or has zero, one, or several
Subject relationships.

## Follow-on boundary

This integration establishes prepared page -> immutable route -> rendered PDS2
page -> retained return -> dispatch -> Scan Reference. Issue #28 may assemble
returned Artifact content and manage Author/Subject relationships, but must
preserve these Artifact Page and Scan Reference identities.
